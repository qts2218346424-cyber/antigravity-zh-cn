use base64::{engine::general_purpose::STANDARD_NO_PAD, Engine as _};
use regex::Regex;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};

use super::atomic_write_text;
use super::skin_manager::{
    compile_skin, compiled_dir, load_studio_config, save_studio_config, CompiledSkin,
};

pub const IDE_SKIN_START: &str = "/* [AGZH_IDE_SKIN_START] */";
pub const IDE_SKIN_END: &str = "/* [AGZH_IDE_SKIN_END] */";

/// 计算 VS Code `product.json` checksums 规范哈希：SHA-256 -> Base64 (无尾部 `=` 填充)
pub fn vscode_checksum(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    STANDARD_NO_PAD.encode(hasher.finalize())
}

/// 生成注入 Antigravity Agent 主进程的皮肤热加载钩子（兼容 `BaseWindow` + `WebContentsView` + 目录安全监听）
pub fn build_agent_main_hook() -> String {
    let cdir = compiled_dir();
    let css_path_json =
        serde_json::to_string(&cdir.join("skin.css").to_string_lossy().to_string())
            .unwrap_or_else(|_| "\"\"".to_string());
    let runtime_path_json = serde_json::to_string(
        &cdir
            .join("skin-runtime.json")
            .to_string_lossy()
            .to_string(),
    )
    .unwrap_or_else(|_| "\"\"".to_string());
    let config_path_json = serde_json::to_string(
        &super::skin_manager::studio_config_path()
            .to_string_lossy()
            .to_string(),
    )
    .unwrap_or_else(|_| "\"\"".to_string());

    format!(
        r#"
// === [AGZH_SKIN_HOOK_START] ===
;(function() {{
  try {{
    if (globalThis.__agzhSkin && globalThis.__agzhSkin.__initialized) return;
    const fs = require('fs');
    const path = require('path');
    const {{ app, BaseWindow, BrowserWindow, ipcMain, webContents }} = require('electron');
    const SKIN_CSS_PATH = {css_path};
    const SKIN_RUNTIME_PATH = {runtime_path};
    const STUDIO_CFG_PATH = {cfg_path};
    const keyMap = new WeakMap();
    const genMap = new WeakMap();
    const attachedContents = new WeakSet();

    function readConfig() {{
      try {{
        if (!fs.existsSync(STUDIO_CFG_PATH)) return {{ skin_enabled: false }};
        return JSON.parse(fs.readFileSync(STUDIO_CFG_PATH, 'utf8'));
      }} catch (_e) {{
        return {{ skin_enabled: false }};
      }}
    }}

    function readCompiledCss() {{
      try {{
        const cfg = readConfig();
        if (!cfg || !cfg.skin_enabled) return '';
        if (!fs.existsSync(SKIN_CSS_PATH)) return '';
        return fs.readFileSync(SKIN_CSS_PATH, 'utf8') || '';
      }} catch (_e) {{
        return '';
      }}
    }}

    function readRuntimePayload() {{
      try {{
        const cfg = readConfig();
        if (!cfg || !cfg.skin_enabled) return null;
        if (!fs.existsSync(SKIN_RUNTIME_PATH)) return null;
        return JSON.parse(fs.readFileSync(SKIN_RUNTIME_PATH, 'utf8') || 'null');
      }} catch (_e) {{
        return null;
      }}
    }}

    function isSkippableUrl(url) {{
      if (!url || typeof url !== 'string') return false;
      if (url.startsWith('devtools://') || url.startsWith('chrome-devtools://')) return true;
      if (url.startsWith('data:text/html,<!doctype html><html style="margin:0;width:100%;height:100%;overflow:hidden;background:transparent')) return true;
      if (url === 'about:blank') return true;
      return false;
    }}

    function isTargetWebContents(wc) {{
      try {{
        if (!wc || typeof wc.isDestroyed !== 'function' || wc.isDestroyed()) return false;
        const t = typeof wc.getType === 'function' ? wc.getType() : '';
        if (t === 'remote' || t === 'backgroundPage') return false;
        const url = typeof wc.getURL === 'function' ? wc.getURL() : '';
        if (isSkippableUrl(url)) return false;
        if (url.startsWith('https://') || url.startsWith('http://')) {{
          return url.startsWith('https://127.0.0.1') || url.startsWith('http://127.0.0.1')
            || url.startsWith('https://localhost') || url.startsWith('http://localhost');
        }}
        return true;
      }} catch (_e) {{
        return false;
      }}
    }}

    async function applyToWebContents(wc) {{
      if (!isTargetWebContents(wc)) return;
      const gen = (genMap.get(wc) || 0) + 1;
      genMap.set(wc, gen);
      const prevKey = keyMap.get(wc);
      if (prevKey) {{
        keyMap.delete(wc);
        try {{ await wc.removeInsertedCSS(prevKey); }} catch (_e) {{}}
      }}
      if (genMap.get(wc) !== gen) return;
      const css = readCompiledCss();
      if (css && css.trim()) {{
        try {{
          const key = await wc.insertCSS(css, {{ cssOrigin: 'author' }});
          if (genMap.get(wc) !== gen) {{
            try {{ await wc.removeInsertedCSS(key); }} catch (_e) {{}}
            return;
          }}
          keyMap.set(wc, key);
        }} catch (_e) {{}}
      }}
      try {{
        wc.send('agzh:skin-updated', readRuntimePayload());
      }} catch (_e) {{}}
    }}

    async function applyToWindow(target) {{
      if (!target) return;
      if (typeof target.insertCSS === 'function') {{
        await applyToWebContents(target);
        return;
      }}
      if (target.webContents && typeof target.webContents.insertCSS === 'function') {{
        await applyToWebContents(target.webContents);
      }}
    }}

    function updateNativeWindowChrome() {{
      try {{
        const payload = readRuntimePayload();
        const colors = payload && payload.colors;
        const bg = colors && typeof colors.background === 'string' && /^#[0-9a-fA-F]{{6}}$/.test(colors.background.trim())
          ? colors.background.trim()
          : null;
        const fg = colors && typeof colors.foreground === 'string' && /^#[0-9a-fA-F]{{6}}$/.test(colors.foreground.trim())
          ? colors.foreground.trim()
          : null;
        if (!bg) return;

        const wins = [
          ...(BaseWindow && typeof BaseWindow.getAllWindows === 'function' ? BaseWindow.getAllWindows() : []),
          ...(BrowserWindow && typeof BrowserWindow.getAllWindows === 'function' ? BrowserWindow.getAllWindows() : []),
        ];
        const seen = new Set();
        for (const win of wins) {{
          if (!win || seen.has(win) || (win.isDestroyed && win.isDestroyed())) continue;
          seen.add(win);
          try {{
            if (typeof win.setBackgroundColor === 'function') win.setBackgroundColor(bg);
          }} catch (_e) {{}}
          try {{
            if (process.platform !== 'darwin' && typeof win.setTitleBarOverlay === 'function') {{
              win.setTitleBarOverlay({{ color: bg, symbolColor: fg || '#FAFAFA', height: 30 }});
            }}
          }} catch (_e) {{}}
        }}
      }} catch (_e) {{}}
    }}

    function applyToAllWindows() {{
      try {{
        const list = webContents && typeof webContents.getAllWebContents === 'function'
          ? webContents.getAllWebContents()
          : [];
        for (const wc of list) {{
          void applyToWebContents(wc);
        }}
        updateNativeWindowChrome();
      }} catch (_e) {{}}
    }}

    function attachWebContents(wc) {{
      if (!wc || attachedContents.has(wc)) return;
      attachedContents.add(wc);
      const trigger = () => {{ void applyToWebContents(wc); }};
      try {{
        wc.on('did-finish-load', trigger);
        wc.on('did-navigate-in-page', trigger);
        wc.on('dom-ready', trigger);
      }} catch (_e) {{}}
    }}

    let watchTimer = null;
    const scheduleRefresh = () => {{
      clearTimeout(watchTimer);
      watchTimer = setTimeout(applyToAllWindows, 140);
    }};

    // 通过监听父目录 + 必须绑定 'error' 事件，彻底避免 Windows 下原子重命名替换文件引发 EPERM 未捕获异常崩溃
    function setupDirWatch(filePath, targetNames) {{
      try {{
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {{
          try {{ fs.mkdirSync(dir, {{ recursive: true }}); }} catch (_e) {{}}
        }}
        if (!fs.existsSync(dir)) return;
        const nameSet = new Set(targetNames);
        const watcher = fs.watch(dir, {{ persistent: false }}, (_eventType, filename) => {{
          if (!filename || nameSet.has(String(filename))) {{
            scheduleRefresh();
          }}
        }});
        watcher.on('error', () => {{
          try {{ watcher.close(); }} catch (_e) {{}}
        }});
      }} catch (_e) {{}}
    }}

    function getStamp(p) {{
      try {{
        if (!fs.existsSync(p)) return '';
        const st = fs.statSync(p);
        return st.mtimeMs + ':' + st.size;
      }} catch (_e) {{
        return '';
      }}
    }}

    let lastCssStamp = getStamp(SKIN_CSS_PATH);
    let lastCfgStamp = getStamp(STUDIO_CFG_PATH);

    if (ipcMain && typeof ipcMain.listenerCount === 'function' && !ipcMain.listenerCount('agzh:get-skin-runtime')) {{
      ipcMain.handle('agzh:get-skin-runtime', () => readRuntimePayload());
    }}

    globalThis.__agzhSkin = {{
      __initialized: true,
      applyToWindow,
      applyToWebContents,
      applyToAllWindows,
      attachWebContents,
      readCompiledCss,
      readRuntimePayload,
    }};

    if (app && typeof app.on === 'function') {{
      app.on('web-contents-created', (_ev, wc) => attachWebContents(wc));
    }}
    try {{
      const existing = webContents && typeof webContents.getAllWebContents === 'function'
        ? webContents.getAllWebContents()
        : [];
      for (const wc of existing) {{
        attachWebContents(wc);
        void applyToWebContents(wc);
      }}
    }} catch (_e) {{}}

    setupDirWatch(SKIN_CSS_PATH, ['skin.css', 'skin-runtime.json']);
    setupDirWatch(STUDIO_CFG_PATH, ['studio.json']);

    // 轻量兜底时间戳比对（仅在文件确实变化时重刷，解决首次运行时尚未创建配置文件/目录事件丢失）
    const pollTimer = setInterval(() => {{
      const s1 = getStamp(SKIN_CSS_PATH);
      const s2 = getStamp(STUDIO_CFG_PATH);
      if (s1 !== lastCssStamp || s2 !== lastCfgStamp) {{
        lastCssStamp = s1;
        lastCfgStamp = s2;
        scheduleRefresh();
      }}
    }}, 1200);
    if (pollTimer && typeof pollTimer.unref === 'function') pollTimer.unref();
  }} catch (_err) {{}}
}})();
// === [AGZH_SKIN_HOOK_END] ===
"#,
        css_path = css_path_json,
        runtime_path = runtime_path_json,
        cfg_path = config_path_json
    )
}

/// 探测本机 Antigravity IDE 安装路径（含 `product.json` 与 `out/vs/workbench/workbench.desktop.main.css`）
pub fn find_ide_app_root(explicit: Option<&str>) -> Option<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();

    if let Some(p) = explicit.map(str::trim).filter(|s| !s.is_empty()) {
        let pb = PathBuf::from(p);
        candidates.push(pb.clone());
        candidates.push(pb.join("resources").join("app"));
        candidates.push(pb.join("Contents").join("Resources").join("app"));
    }

    let cfg = load_studio_config();
    if let Some(saved) = cfg.ide_install_dir.as_deref() {
        let pb = PathBuf::from(saved);
        candidates.push(pb.clone());
        candidates.push(pb.join("resources").join("app"));
    }

    #[cfg(target_os = "windows")]
    {
        if let Ok(local) = std::env::var("LOCALAPPDATA") {
            let programs = PathBuf::from(&local).join("Programs");
            for dir_name in ["Antigravity IDE", "Antigravity", "AntigravityIDE"] {
                candidates.push(programs.join(dir_name).join("resources").join("app"));
            }
        }
        if let Ok(pf) = std::env::var("ProgramFiles") {
            for dir_name in ["Antigravity IDE", "Antigravity", "AntigravityIDE"] {
                candidates.push(
                    PathBuf::from(&pf)
                        .join(dir_name)
                        .join("resources")
                        .join("app"),
                );
            }
        }
        candidates.push(PathBuf::from(
            r"C:\Program Files\Antigravity IDE\resources\app",
        ));
        candidates.push(PathBuf::from(
            r"C:\Program Files\Antigravity\resources\app",
        ));
    }

    #[cfg(target_os = "macos")]
    {
        candidates.push(PathBuf::from(
            "/Applications/Antigravity.app/Contents/Resources/app",
        ));
        candidates.push(PathBuf::from(
            "/Applications/Antigravity IDE.app/Contents/Resources/app",
        ));
        if let Some(home) = dirs::home_dir() {
            candidates.push(home.join("Applications/Antigravity.app/Contents/Resources/app"));
            candidates.push(home.join("Applications/Antigravity IDE.app/Contents/Resources/app"));
        }
    }

    #[cfg(all(not(target_os = "windows"), not(target_os = "macos")))]
    {
        candidates.push(PathBuf::from("/usr/share/antigravity/resources/app"));
        candidates.push(PathBuf::from("/opt/Antigravity/resources/app"));
        candidates.push(PathBuf::from("/usr/lib/antigravity/resources/app"));
    }

    for cand in candidates {
        let css = ide_workbench_css_path(&cand);
        let prod = cand.join("product.json");
        if css.is_file() && prod.is_file() {
            return Some(cand);
        }
    }

    None
}

pub fn ide_workbench_css_path(app_root: &Path) -> PathBuf {
    app_root
        .join("out")
        .join("vs")
        .join("workbench")
        .join("workbench.desktop.main.css")
}

pub fn ide_jetski_css_path(app_root: &Path) -> PathBuf {
    app_root.join("out").join("jetskiMain.tailwind.css")
}

fn strip_ide_skin_block(css_content: &str) -> String {
    let re_new = Regex::new(
        r"(?s)\s*/\*\s*\[AGZH_IDE_SKIN_START\]\s*\*/.*?/\*\s*\[AGZH_IDE_SKIN_END\]\s*\*/\s*",
    )
    .unwrap();
    let step1 = re_new.replace_all(css_content, "");
    // 兼容剥离旧工具残留的 /* __AGZH_SKIN_BEGIN__ ... */ ... /* __AGZH_SKIN_END__ */ 注入块
    let re_legacy = Regex::new(
        r"(?s)\s*/\*\s*__AGZH_SKIN_BEGIN__.*?\*/.*?/\*\s*__AGZH_SKIN_END__\s*\*/\s*",
    )
    .unwrap();
    re_legacy.replace_all(&step1, "").to_string()
}

fn update_product_checksums(app_root: &Path, entries: &[(&str, &[u8])]) -> Result<(), String> {
    let prod_path = app_root.join("product.json");
    let bak_path = app_root.join("product.json.agzh-bak");
    let legacy_bak = app_root.join("product.json.agzh.bak");
    let raw = std::fs::read_to_string(&prod_path)
        .map_err(|e| format!("读取 product.json 失败: {}", e))?;

    if !bak_path.exists() {
        let bak_src = if legacy_bak.is_file() {
            std::fs::read_to_string(&legacy_bak).unwrap_or_else(|_| raw.clone())
        } else {
            raw.clone()
        };
        let _ = atomic_write_text(&bak_path, &bak_src);
    }

    let mut prod: Value =
        serde_json::from_str(&raw).map_err(|e| format!("解析 product.json 失败: {}", e))?;

    if let Some(checksums) = prod.get_mut("checksums").and_then(|v| v.as_object_mut()) {
        for &(rel_key, bytes) in entries {
            if checksums.contains_key(rel_key) {
                checksums.insert(rel_key.to_string(), json!(vscode_checksum(bytes)));
            }
        }
    }

    let updated = serde_json::to_string_pretty(&prod)
        .map_err(|e| format!("序列化 product.json 失败: {}", e))?;
    atomic_write_text(&prod_path, &updated)?;
    Ok(())
}

fn inject_single_ide_css(css_path: &Path, compiled_css: &str) -> Result<Vec<u8>, String> {
    let bak_path = css_path.with_extension("css.agzh-bak");
    let legacy_bak = css_path.with_extension("css.agzh.bak");
    let original_raw = std::fs::read_to_string(css_path)
        .map_err(|e| format!("读取 {} 失败: {}", css_path.display(), e))?;

    if !bak_path.exists() {
        let base_for_bak = if legacy_bak.is_file() {
            let lraw = std::fs::read_to_string(&legacy_bak).unwrap_or_else(|_| original_raw.clone());
            strip_ide_skin_block(&lraw)
        } else {
            strip_ide_skin_block(&original_raw)
        };
        let _ = atomic_write_text(&bak_path, &base_for_bak);
    }

    let base_css = strip_ide_skin_block(&original_raw);
    let new_css = format!(
        "{}\n\n{}\n{}\n{}\n",
        base_css.trim_end(),
        IDE_SKIN_START,
        compiled_css.trim(),
        IDE_SKIN_END
    );
    atomic_write_text(css_path, &new_css)?;
    Ok(new_css.into_bytes())
}

fn restore_single_ide_css(css_path: &Path) -> Result<Vec<u8>, String> {
    let bak_path = css_path.with_extension("css.agzh-bak");
    let legacy_bak = css_path.with_extension("css.agzh.bak");

    let clean_css = if bak_path.is_file() {
        let raw = std::fs::read_to_string(&bak_path)
            .map_err(|e| format!("读取备份 CSS 失败: {}", e))?;
        strip_ide_skin_block(&raw)
    } else if legacy_bak.is_file() {
        let raw = std::fs::read_to_string(&legacy_bak)
            .map_err(|e| format!("读取旧版备份 CSS 失败: {}", e))?;
        strip_ide_skin_block(&raw)
    } else {
        let cur = std::fs::read_to_string(css_path)
            .map_err(|e| format!("读取 IDE CSS 失败: {}", e))?;
        strip_ide_skin_block(&cur)
    };

    atomic_write_text(css_path, &clean_css)?;
    Ok(clean_css.into_bytes())
}

/// 查询 Antigravity IDE 样式注入状态：`"not_found"` / `"clean"` / `"injected"` / `"stale"`
pub fn ide_status(explicit_root: Option<&str>) -> String {
    let Some(app_root) = find_ide_app_root(explicit_root) else {
        return "not_found".to_string();
    };
    let css_path = ide_workbench_css_path(&app_root);
    let Ok(content) = std::fs::read_to_string(&css_path) else {
        return "not_found".to_string();
    };

    if !content.contains(IDE_SKIN_START) {
        return "clean".to_string();
    }

    // 校验当前注入片段是否与已启用的皮肤编译产物一致
    let cfg = load_studio_config();
    if cfg.skin_enabled {
        let compiled_css_path = compiled_dir().join("skin.css");
        if let Ok(expected_css) = std::fs::read_to_string(&compiled_css_path) {
            if !expected_css.trim().is_empty() && !content.contains(expected_css.trim()) {
                return "stale".to_string();
            }
        }
    }

    "injected".to_string()
}

/// 使用已经编译好的皮肤产物写入 IDE（同时覆写工作台主样式与 Jetski 代理面板样式并校验 SHA-256）
pub fn inject_ide_compiled(
    compiled: &CompiledSkin,
    explicit_root: Option<&str>,
) -> Result<String, String> {
    let app_root = find_ide_app_root(explicit_root)
        .ok_or_else(|| "未检测到 Antigravity IDE 安装目录，请确认路径中包含 product.json 与 workbench.desktop.main.css".to_string())?;

    let wb_css_path = ide_workbench_css_path(&app_root);
    let wb_bytes = inject_single_ide_css(&wb_css_path, &compiled.css)?;

    let jetski_css_path = ide_jetski_css_path(&app_root);
    let jetski_bytes = if jetski_css_path.is_file() {
        Some(inject_single_ide_css(&jetski_css_path, &compiled.css)?)
    } else {
        None
    };

    let mut checksum_entries: Vec<(&str, &[u8])> =
        vec![("vs/workbench/workbench.desktop.main.css", &wb_bytes)];
    if let Some(ref jb) = jetski_bytes {
        checksum_entries.push(("jetskiMain.tailwind.css", jb));
    }
    update_product_checksums(&app_root, &checksum_entries)?;

    #[cfg(target_os = "macos")]
    {
        if let Some(app_bundle) = app_root.parent().and_then(|p| p.parent()).and_then(|p| p.parent()) {
            if app_bundle.extension().and_then(|e| e.to_str()) == Some("app") {
                let _ = std::process::Command::new("codesign")
                    .args(["--force", "--deep", "--sign", "-"])
                    .arg(app_bundle)
                    .output();
            }
        }
    }

    let mut cfg = load_studio_config();
    cfg.ide_enabled = true;
    cfg.ide_install_dir = Some(app_root.to_string_lossy().to_string());
    cfg.active_skin = Some(compiled.skin_id.clone());
    cfg.skin_enabled = true;
    save_studio_config(&cfg)?;

    Ok(format!(
        "已成功向 Antigravity IDE 注入材质包 '{}' 并修复 SHA-256 校验和",
        compiled.skin_id
    ))
}

/// 向 Antigravity IDE 注入材质包样式，并同步修正 `product.json` 的 SHA-256 校验和防止“安装似乎已损坏”警告
pub fn inject_ide(skin_id: Option<&str>, explicit_root: Option<&str>) -> Result<String, String> {
    let target_skin = skin_id
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(|s| s.to_string())
        .or_else(|| load_studio_config().active_skin)
        .ok_or_else(|| "尚未指定或启用任何材质包，无法注入 IDE".to_string())?;

    let compiled = compile_skin(&target_skin)?;
    inject_ide_compiled(&compiled, explicit_root)
}

/// 从 Antigravity IDE 移除材质包注入并重新校准 `product.json` 校验和
pub fn remove_ide(explicit_root: Option<&str>) -> Result<String, String> {
    let app_root = find_ide_app_root(explicit_root)
        .ok_or_else(|| "未检测到 Antigravity IDE 安装目录".to_string())?;

    let wb_bytes = restore_single_ide_css(&ide_workbench_css_path(&app_root))?;
    let jetski_css_path = ide_jetski_css_path(&app_root);
    let jetski_bytes = if jetski_css_path.is_file() {
        Some(restore_single_ide_css(&jetski_css_path)?)
    } else {
        None
    };

    let mut checksum_entries: Vec<(&str, &[u8])> =
        vec![("vs/workbench/workbench.desktop.main.css", &wb_bytes)];
    if let Some(ref jb) = jetski_bytes {
        checksum_entries.push(("jetskiMain.tailwind.css", jb));
    }
    update_product_checksums(&app_root, &checksum_entries)?;

    let mut cfg = load_studio_config();
    cfg.ide_enabled = false;
    save_studio_config(&cfg)?;

    Ok("已从 Antigravity IDE 移除材质包样式并恢复校验和".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vscode_checksum_format() {
        // 标准 SHA-256 -> Base64 去填充
        let digest = vscode_checksum(b"hello world");
        assert!(!digest.contains('='));
        assert_eq!(digest, "uU0nuZNNPgilLlLX2n2r+sSE7+N6U4DukIj3rOLvzek");
    }

    #[test]
    fn test_strip_ide_skin_block_is_idempotent() {
        let src = format!(
            "body{{color:#000}}\n{}\n:root{{--a:1}}\n{}\n/* __AGZH_SKIN_BEGIN__ id=old */\n:root{{--x:2}}\n/* __AGZH_SKIN_END__ */\n",
            IDE_SKIN_START, IDE_SKIN_END
        );
        let cleaned = strip_ide_skin_block(&src);
        assert_eq!(cleaned.trim(), "body{color:#000}");
    }
}
