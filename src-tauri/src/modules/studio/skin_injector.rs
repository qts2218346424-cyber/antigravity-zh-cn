use base64::{engine::general_purpose::STANDARD_NO_PAD, Engine as _};
use regex::Regex;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};

use super::atomic_write_text;
use super::skin_manager::{compiled_dir, load_studio_config, save_studio_config};

pub const LEGACY_IDE_SKIN_START: &str = "/* [AGZH_IDE_SKIN_START] */";
pub const LEGACY_IDE_SKIN_END: &str = "/* [AGZH_IDE_SKIN_END] */";
pub const SKIN_HOOK_REV: &str = "AGZH_SKIN_HOOK_V4";

/// 生成注入 Google Antigravity 独立桌面应用（AGY Hub）主进程的光学皮肤热重载钩子：
/// - 精准对接官方 `dist/utils.js` (`getHubWindows` / `getHubWebContents` / `setHubCurtainColor`)
/// - 严格仅向应用自身 Hub 视图注入样式，绝不污染内置浏览器 (`browserWcv`)、捕获层 (`catcherWcv`) 与幕布层 (`curtainView`)
/// - 实时联动原生窗口底色、三层栈幕布色与 Windows 标题栏控制按钮覆盖色，停用皮肤时无损还原原生深浅配色
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
    let runtime_js_path_json = serde_json::to_string(
        &cdir
            .join("skin-runtime.js")
            .to_string_lossy()
            .to_string(),
    )
    .unwrap_or_else(|_| "\"\"".to_string());

    format!(
        r#"
// === [AGZH_SKIN_HOOK_START:{hook_rev}] ===
;(function() {{
  try {{
    if (globalThis.__agzhSkin && globalThis.__agzhSkin.__initialized) return;
    const fs = require('fs');
    const path = require('path');
    const {{ app, BaseWindow, BrowserWindow, ipcMain, nativeTheme, webContents }} = require('electron');
    let agyUtils = null;
    try {{ agyUtils = require('./utils'); }} catch (_e) {{}}

    const SKIN_CSS_PATH = {css_path};
    const SKIN_RUNTIME_PATH = {runtime_path};
    const SKIN_RUNTIME_JS_PATH = {runtime_js_path};
    const STUDIO_CFG_PATH = {cfg_path};
    const keyMap = new WeakMap();
    const genMap = new WeakMap();
    const runtimeSigMap = new WeakMap();
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

    function collectHubWebContentsSet() {{
      const set = new Set();
      try {{
        if (agyUtils && typeof agyUtils.getHubWindows === 'function' && typeof agyUtils.getHubWebContents === 'function') {{
          for (const win of agyUtils.getHubWindows()) {{
            const wc = agyUtils.getHubWebContents(win);
            if (wc && !wc.isDestroyed?.()) set.add(wc);
          }}
        }}
      }} catch (_e) {{}}
      return set;
    }}

    function isSkippableUrl(url) {{
      if (!url || typeof url !== 'string') return false;
      if (url.startsWith('devtools://') || url.startsWith('chrome-devtools://')) return true;
      if (url.startsWith('data:')) return true;
      if (url === 'about:blank' || url.includes('ag_clannad_splash_')) return true;
      return false;
    }}

    function isTargetAppWebContents(wc) {{
      try {{
        if (!wc || typeof wc.isDestroyed !== 'function' || wc.isDestroyed()) return false;
        const hubSet = collectHubWebContentsSet();
        if (hubSet.size > 0) {{
          return hubSet.has(wc);
        }}
        const t = typeof wc.getType === 'function' ? wc.getType() : '';
        if (t === 'remote' || t === 'backgroundPage' || t === 'webview') return false;
        const url = typeof wc.getURL === 'function' ? wc.getURL() : '';
        if (isSkippableUrl(url)) return false;
        if (url.startsWith('https://') || url.startsWith('http://')) {{
          return url.startsWith('https://127.0.0.1:') || url.startsWith('http://127.0.0.1:');
        }}
        return true;
      }} catch (_e) {{
        return false;
      }}
    }}

    async function syncRuntimeScript(wc) {{
      try {{
        if (!wc || wc.isDestroyed?.() || typeof wc.executeJavaScript !== 'function') return;
        if (!fs.existsSync(SKIN_RUNTIME_JS_PATH)) return;
        const st = fs.statSync(SKIN_RUNTIME_JS_PATH);
        const sig = st.mtimeMs + ':' + st.size;
        if (runtimeSigMap.get(wc) === sig) return;
        const code = fs.readFileSync(SKIN_RUNTIME_JS_PATH, 'utf8');
        if (!code || !code.trim()) return;
        const payloadJson = JSON.stringify(readRuntimePayload());
        const sigJson = JSON.stringify(sig);
        const script =
          '(function(){{try{{if(window.__AGZH_RUNTIME_SIG__===' + sigJson + ')return;' +
          'if(typeof window.__AGZH_SKIN_DISPOSE__==="function")try{{window.__AGZH_SKIN_DISPOSE__();}}catch(_){{}}' +
          'window.__AGZH_SKIN__=' + payloadJson + ';' +
          'window.__AGZH_RUNTIME_SIG__=' + sigJson + ';' +
          code +
          '}}catch(_e){{}}}})();';
        await wc.executeJavaScript(script, true);
        runtimeSigMap.set(wc, sig);
      }} catch (_e) {{}}
    }}

    async function applyToWebContents(wc) {{
      if (!isTargetAppWebContents(wc)) return;
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
      await syncRuntimeScript(wc);
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
      if (agyUtils && typeof agyUtils.getHubWebContents === 'function') {{
        const hubWc = agyUtils.getHubWebContents(target);
        if (hubWc) {{
          await applyToWebContents(hubWc);
          return;
        }}
      }}
      if (target.webContents && typeof target.webContents.insertCSS === 'function') {{
        await applyToWebContents(target.webContents);
      }}
    }}

    function normalizeHex6(val) {{
      return typeof val === 'string' && /^#[0-9a-fA-F]{{6}}$/.test(val.trim())
        ? val.trim()
        : null;
    }}

    function updateNativeWindowChrome() {{
      try {{
        const payload = readRuntimePayload();
        const colors = payload && payload.colors;
        const isLightFallback = agyUtils && typeof agyUtils.isLightTheme === 'function'
          ? Boolean(agyUtils.isLightTheme())
          : Boolean(nativeTheme && !nativeTheme.shouldUseDarkColors);

        const defaultBg = isLightFallback ? '#FAFAFA' : '#131313';
        const defaultFg = isLightFallback ? '#383A42' : '#FAFAFA';

        const bg = colors ? (normalizeHex6(colors.background) || defaultBg) : defaultBg;
        const shellBg = colors ? (normalizeHex6(colors.sidebar) || bg) : defaultBg;
        const titleBg = colors ? (normalizeHex6(colors.titleBar) || shellBg) : defaultBg;
        const fg = colors ? (normalizeHex6(colors.foreground) || defaultFg) : defaultFg;

        const wins = [
          ...(agyUtils && typeof agyUtils.getHubWindows === 'function' ? agyUtils.getHubWindows() : []),
          ...(BaseWindow && typeof BaseWindow.getAllWindows === 'function' ? BaseWindow.getAllWindows() : []),
          ...(BrowserWindow && typeof BrowserWindow.getAllWindows === 'function' ? BrowserWindow.getAllWindows() : []),
        ];
        const seen = new Set();
        for (const win of wins) {{
          if (!win || seen.has(win) || (win.isDestroyed && win.isDestroyed())) continue;
          if (win.__isWebviewPopupWindow) continue;
          seen.add(win);
          try {{
            if (agyUtils && typeof agyUtils.setHubCurtainColor === 'function') {{
              agyUtils.setHubCurtainColor(win, shellBg);
            }} else if (typeof win.setBackgroundColor === 'function') {{
              win.setBackgroundColor(shellBg);
            }}
          }} catch (_e) {{}}
          try {{
            if (process.platform !== 'darwin' && typeof win.setTitleBarOverlay === 'function') {{
              win.setTitleBarOverlay({{ color: titleBg, symbolColor: fg, height: 30 }});
            }}
          }} catch (_e) {{}}
        }}
      }} catch (_e) {{}}
    }}

    function applyToAllWindows() {{
      try {{
        const hubSet = collectHubWebContentsSet();
        if (hubSet.size > 0) {{
          for (const wc of hubSet) {{
            void applyToWebContents(wc);
          }}
        }} else {{
          const list = webContents && typeof webContents.getAllWebContents === 'function'
            ? webContents.getAllWebContents()
            : [];
          for (const wc of list) {{
            void applyToWebContents(wc);
          }}
        }}
        updateNativeWindowChrome();
      }} catch (_e) {{}}
    }}

    function attachWebContents(wc) {{
      if (!wc || attachedContents.has(wc)) return;
      attachedContents.add(wc);
      const trigger = () => {{
        void applyToWebContents(wc);
        updateNativeWindowChrome();
      }};
      try {{
        wc.on('did-finish-load', trigger);
        wc.on('did-navigate-in-page', trigger);
        wc.on('dom-ready', trigger);
      }} catch (_e) {{}}
    }}

    let watchTimer = null;
    const scheduleRefresh = () => {{
      clearTimeout(watchTimer);
      watchTimer = setTimeout(applyToAllWindows, 120);
    }};

    // 通过监听父目录并绑定 'error' 事件，杜绝 Windows 原子替换文件引发 EPERM 未捕获异常
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
    let lastJsStamp = getStamp(SKIN_RUNTIME_JS_PATH);
    let lastCfgStamp = getStamp(STUDIO_CFG_PATH);

    if (ipcMain && typeof ipcMain.listenerCount === 'function') {{
      if (!ipcMain.listenerCount('agzh:get-skin-runtime')) {{
        ipcMain.handle('agzh:get-skin-runtime', () => readRuntimePayload());
      }}
      if (!ipcMain.listenerCount('agzh:get-skin-runtime-sync')) {{
        ipcMain.on('agzh:get-skin-runtime-sync', (ev) => {{
          ev.returnValue = readRuntimePayload();
        }});
      }}
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
      updateNativeWindowChrome();
    }} catch (_e) {{}}

    setupDirWatch(SKIN_CSS_PATH, ['skin.css', 'skin-runtime.json', 'skin-runtime.js']);
    setupDirWatch(STUDIO_CFG_PATH, ['studio.json']);

    // 轻量兜底时间戳比对（解决首次运行时尚未创建配置文件或目录事件丢失）
    const pollTimer = setInterval(() => {{
      const s1 = getStamp(SKIN_CSS_PATH);
      const s2 = getStamp(STUDIO_CFG_PATH);
      const s3 = getStamp(SKIN_RUNTIME_JS_PATH);
      if (s1 !== lastCssStamp || s2 !== lastCfgStamp || s3 !== lastJsStamp) {{
        lastCssStamp = s1;
        lastCfgStamp = s2;
        lastJsStamp = s3;
        scheduleRefresh();
      }}
    }}, 1200);
    if (pollTimer && typeof pollTimer.unref === 'function') pollTimer.unref();
  }} catch (_err) {{}}
}})();
// === [AGZH_SKIN_HOOK_END] ===
"#,
        hook_rev = SKIN_HOOK_REV,
        css_path = css_path_json,
        runtime_path = runtime_path_json,
        runtime_js_path = runtime_js_path_json,
        cfg_path = config_path_json
    )
}

fn vscode_checksum(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    STANDARD_NO_PAD.encode(hasher.finalize())
}

fn strip_legacy_ide_skin_block(css_content: &str) -> String {
    let re_new = Regex::new(
        r"(?s)\s*/\*\s*\[AGZH_IDE_SKIN_START\]\s*\*/.*?/\*\s*\[AGZH_IDE_SKIN_END\]\s*\*/\s*",
    )
    .unwrap();
    let step1 = re_new.replace_all(css_content, "");
    let re_legacy = Regex::new(
        r"(?s)\s*/\*\s*__AGZH_SKIN_BEGIN__.*?\*/.*?/\*\s*__AGZH_SKIN_END__\s*\*/\s*",
    )
    .unwrap();
    re_legacy.replace_all(&step1, "").to_string()
}

fn find_legacy_ide_root(explicit: Option<&str>) -> Option<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();
    if let Some(p) = explicit.map(str::trim).filter(|s| !s.is_empty()) {
        let pb = PathBuf::from(p);
        candidates.push(pb.clone());
        candidates.push(pb.join("resources").join("app"));
    }

    #[cfg(target_os = "windows")]
    {
        if let Ok(local) = std::env::var("LOCALAPPDATA") {
            let programs = PathBuf::from(&local).join("Programs");
            for dir_name in ["Antigravity IDE", "AntigravityIDE"] {
                candidates.push(programs.join(dir_name).join("resources").join("app"));
            }
        }
        if let Ok(pf) = std::env::var("ProgramFiles") {
            for dir_name in ["Antigravity IDE", "AntigravityIDE"] {
                candidates.push(PathBuf::from(&pf).join(dir_name).join("resources").join("app"));
            }
        }
    }

    #[cfg(target_os = "macos")]
    {
        candidates.push(PathBuf::from(
            "/Applications/Antigravity IDE.app/Contents/Resources/app",
        ));
    }

    for cand in candidates {
        let css = cand
            .join("out")
            .join("vs")
            .join("workbench")
            .join("workbench.desktop.main.css");
        let prod = cand.join("product.json");
        if css.is_file() && prod.is_file() {
            return Some(cand);
        }
    }
    None
}

fn restore_legacy_ide_css_if_dirty(css_path: &Path) -> Option<Vec<u8>> {
    let cur = std::fs::read_to_string(css_path).ok()?;
    let bak_path = css_path.with_extension("css.agzh-bak");
    let legacy_bak = css_path.with_extension("css.agzh.bak");

    let has_dirty_marker =
        cur.contains(LEGACY_IDE_SKIN_START) || cur.contains("__AGZH_SKIN_BEGIN__");
    if !has_dirty_marker && !bak_path.is_file() && !legacy_bak.is_file() {
        return None;
    }

    let clean_css = if bak_path.is_file() {
        std::fs::read_to_string(&bak_path)
            .map(|r| strip_legacy_ide_skin_block(&r))
            .unwrap_or_else(|_| strip_legacy_ide_skin_block(&cur))
    } else if legacy_bak.is_file() {
        std::fs::read_to_string(&legacy_bak)
            .map(|r| strip_legacy_ide_skin_block(&r))
            .unwrap_or_else(|_| strip_legacy_ide_skin_block(&cur))
    } else {
        strip_legacy_ide_skin_block(&cur)
    };

    if has_dirty_marker {
        let _ = atomic_write_text(css_path, &clean_css);
    }
    let _ = std::fs::remove_file(&bak_path);
    let _ = std::fs::remove_file(&legacy_bak);
    Some(clean_css.into_bytes())
}

/// 若检测到早期版本曾在旧版 `Antigravity IDE` 中注入过皮肤样式，静默将其无损还原为原版并清除遗留配置
pub fn cleanup_legacy_ide_injection() {
    let cfg = load_studio_config();
    let app_root = find_legacy_ide_root(cfg.ide_install_dir.as_deref());

    if let Some(root) = app_root {
        let wb_css = root
            .join("out")
            .join("vs")
            .join("workbench")
            .join("workbench.desktop.main.css");
        let jetski_css = root.join("out").join("jetskiMain.tailwind.css");

        let wb_restored = restore_legacy_ide_css_if_dirty(&wb_css);
        let jetski_restored = if jetski_css.is_file() {
            restore_legacy_ide_css_if_dirty(&jetski_css)
        } else {
            None
        };

        if wb_restored.is_some() || jetski_restored.is_some() {
            let prod_path = root.join("product.json");
            if let Ok(raw) = std::fs::read_to_string(&prod_path) {
                if let Ok(mut prod) = serde_json::from_str::<Value>(&raw) {
                    if let Some(checksums) = prod.get_mut("checksums").and_then(|v| v.as_object_mut())
                    {
                        if let Some(ref b) = wb_restored {
                            if checksums.contains_key("vs/workbench/workbench.desktop.main.css") {
                                checksums.insert(
                                    "vs/workbench/workbench.desktop.main.css".to_string(),
                                    json!(vscode_checksum(b)),
                                );
                            }
                        }
                        if let Some(ref b) = jetski_restored {
                            if checksums.contains_key("jetskiMain.tailwind.css") {
                                checksums.insert(
                                    "jetskiMain.tailwind.css".to_string(),
                                    json!(vscode_checksum(b)),
                                );
                            }
                        }
                    }
                    if let Ok(updated) = serde_json::to_string_pretty(&prod) {
                        let _ = atomic_write_text(&prod_path, &updated);
                    }
                }
            }
            let _ = std::fs::remove_file(root.join("product.json.agzh-bak"));
            let _ = std::fs::remove_file(root.join("product.json.agzh.bak"));
        }
    }

    if cfg.ide_enabled || cfg.ide_install_dir.is_some() {
        let mut next = cfg;
        next.ide_enabled = false;
        next.ide_install_dir = None;
        let _ = save_studio_config(&next);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_agent_hook_uses_hub_utils_and_curtain_sync() {
        let hook = build_agent_main_hook();
        assert!(hook.contains(SKIN_HOOK_REV));
        assert!(hook.contains("getHubWindows"));
        assert!(hook.contains("getHubWebContents"));
        assert!(hook.contains("setHubCurtainColor"));
        assert!(hook.contains("agzh:skin-updated"));
        assert!(hook.contains("skin-runtime.js"));
        assert!(hook.contains("syncRuntimeScript"));
    }

    #[test]
    fn test_strip_legacy_ide_skin_block_is_idempotent() {
        let src = format!(
            "body{{color:#000}}\n{}\n:root{{--a:1}}\n{}\n/* __AGZH_SKIN_BEGIN__ id=old */\n:root{{--x:2}}\n/* __AGZH_SKIN_END__ */\n",
            LEGACY_IDE_SKIN_START, LEGACY_IDE_SKIN_END
        );
        let cleaned = strip_legacy_ide_skin_block(&src);
        assert_eq!(cleaned.trim(), "body{color:#000}");
    }
}
