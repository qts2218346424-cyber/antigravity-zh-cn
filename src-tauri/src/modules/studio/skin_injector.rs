use base64::{engine::general_purpose::STANDARD_NO_PAD, Engine as _};
use regex::Regex;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};

use super::atomic_write_text;
use super::skin_manager::{
    compile_skin, compiled_dir, load_studio_config, save_studio_config,
};

pub const IDE_SKIN_START: &str = "/* [AGZH_IDE_SKIN_START] */";
pub const IDE_SKIN_END: &str = "/* [AGZH_IDE_SKIN_END] */";

/// 计算 VS Code `product.json` checksums 规范哈希：SHA-256 -> Base64 (无尾部 `=` 填充)
pub fn vscode_checksum(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    STANDARD_NO_PAD.encode(hasher.finalize())
}

/// 生成注入 Antigravity Agent 主进程的皮肤热加载钩子（读取用户配置目录下的编译产物）
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
    const {{ BrowserWindow, ipcMain }} = require('electron');
    const SKIN_CSS_PATH = {css_path};
    const SKIN_RUNTIME_PATH = {runtime_path};
    const STUDIO_CFG_PATH = {cfg_path};
    const keyMap = new WeakMap();

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

    async function applyToWindow(win) {{
      if (!win || win.isDestroyed() || !win.webContents) return;
      const wc = win.webContents;
      const prevKey = keyMap.get(wc);
      if (prevKey) {{
        try {{ await wc.removeInsertedCSS(prevKey); }} catch (_e) {{}}
        keyMap.delete(wc);
      }}
      const css = readCompiledCss();
      if (css && css.trim()) {{
        try {{
          const key = await wc.insertCSS(css, {{ cssOrigin: 'author' }});
          keyMap.set(wc, key);
        }} catch (_e) {{}}
      }}
      try {{
        if (fs.existsSync(SKIN_RUNTIME_PATH)) {{
          const raw = fs.readFileSync(SKIN_RUNTIME_PATH, 'utf8');
          wc.send('agzh:skin-updated', JSON.parse(raw || '{{}}'));
        }}
      }} catch (_e) {{}}
    }}

    function applyToAllWindows() {{
      for (const win of BrowserWindow.getAllWindows()) {{
        applyToWindow(win);
      }}
    }}

    let watchTimer = null;
    function setupWatch(filePath) {{
      try {{
        if (!fs.existsSync(filePath)) return;
        fs.watch(filePath, {{ persistent: false }}, () => {{
          clearTimeout(watchTimer);
          watchTimer = setTimeout(applyToAllWindows, 120);
        }});
      }} catch (_e) {{}}
    }}

    if (ipcMain && !ipcMain.listenerCount('agzh:get-skin-runtime')) {{
      ipcMain.handle('agzh:get-skin-runtime', () => {{
        try {{
          const cfg = readConfig();
          if (!cfg || !cfg.skin_enabled) return null;
          if (!fs.existsSync(SKIN_RUNTIME_PATH)) return null;
          return JSON.parse(fs.readFileSync(SKIN_RUNTIME_PATH, 'utf8'));
        }} catch (_e) {{
          return null;
        }}
      }});
    }}

    globalThis.__agzhSkin = {{
      __initialized: true,
      applyToWindow,
      applyToAllWindows,
      readCompiledCss,
    }};

    setupWatch(SKIN_CSS_PATH);
    setupWatch(STUDIO_CFG_PATH);
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
            candidates.push(
                PathBuf::from(&local)
                    .join("Programs")
                    .join("Antigravity")
                    .join("resources")
                    .join("app"),
            );
            candidates.push(
                PathBuf::from(&local)
                    .join("Programs")
                    .join("AntigravityIDE")
                    .join("resources")
                    .join("app"),
            );
        }
        candidates.push(PathBuf::from(
            r"C:\Program Files\Antigravity\resources\app",
        ));
    }

    #[cfg(target_os = "macos")]
    {
        candidates.push(PathBuf::from(
            "/Applications/Antigravity.app/Contents/Resources/app",
        ));
        if let Some(home) = dirs::home_dir() {
            candidates.push(home.join("Applications/Antigravity.app/Contents/Resources/app"));
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

fn strip_ide_skin_block(css_content: &str) -> String {
    let re = Regex::new(
        r"(?s)\s*/\*\s*\[AGZH_IDE_SKIN_START\]\s*\*/.*?/\*\s*\[AGZH_IDE_SKIN_END\]\s*\*/\s*",
    )
    .unwrap();
    re.replace_all(css_content, "").to_string()
}

fn update_product_checksum(app_root: &Path, css_bytes: &[u8]) -> Result<(), String> {
    let prod_path = app_root.join("product.json");
    let bak_path = app_root.join("product.json.agzh-bak");
    let raw = std::fs::read_to_string(&prod_path)
        .map_err(|e| format!("读取 product.json 失败: {}", e))?;

    if !bak_path.exists() {
        let _ = atomic_write_text(&bak_path, &raw);
    }

    let mut prod: Value =
        serde_json::from_str(&raw).map_err(|e| format!("解析 product.json 失败: {}", e))?;
    let digest = vscode_checksum(css_bytes);

    if let Some(checksums) = prod.get_mut("checksums").and_then(|v| v.as_object_mut()) {
        checksums.insert(
            "vs/workbench/workbench.desktop.main.css".to_string(),
            json!(digest),
        );
    }

    let updated = serde_json::to_string_pretty(&prod)
        .map_err(|e| format!("序列化 product.json 失败: {}", e))?;
    atomic_write_text(&prod_path, &updated)?;
    Ok(())
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

/// 向 Antigravity IDE 注入材质包样式，并同步修正 `product.json` 的 SHA-256 校验和防止“安装似乎已损坏”警告
pub fn inject_ide(skin_id: Option<&str>, explicit_root: Option<&str>) -> Result<String, String> {
    let app_root = find_ide_app_root(explicit_root)
        .ok_or_else(|| "未检测到 Antigravity IDE 安装目录，请确认路径中包含 product.json 与 workbench.desktop.main.css".to_string())?;

    let target_skin = skin_id
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(|s| s.to_string())
        .or_else(|| load_studio_config().active_skin)
        .ok_or_else(|| "尚未指定或启用任何材质包，无法注入 IDE".to_string())?;

    let compiled = compile_skin(&target_skin)?;
    let css_path = ide_workbench_css_path(&app_root);
    let bak_path = css_path.with_extension("css.agzh-bak");

    let original_raw = std::fs::read_to_string(&css_path)
        .map_err(|e| format!("读取 workbench.desktop.main.css 失败: {}", e))?;

    if !bak_path.exists() {
        let clean_for_bak = strip_ide_skin_block(&original_raw);
        let _ = atomic_write_text(&bak_path, &clean_for_bak);
    }

    let base_css = strip_ide_skin_block(&original_raw);
    let new_css = format!(
        "{}\n\n{}\n{}\n{}\n",
        base_css.trim_end(),
        IDE_SKIN_START,
        compiled.css.trim(),
        IDE_SKIN_END
    );

    atomic_write_text(&css_path, &new_css)?;
    update_product_checksum(&app_root, new_css.as_bytes())?;

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
    cfg.active_skin = Some(target_skin.clone());
    cfg.skin_enabled = true;
    save_studio_config(&cfg)?;

    Ok(format!(
        "已成功向 Antigravity IDE 注入材质包 '{}' 并修复 SHA-256 校验和",
        target_skin
    ))
}

/// 从 Antigravity IDE 移除材质包注入并重新校准 `product.json` 校验和
pub fn remove_ide(explicit_root: Option<&str>) -> Result<String, String> {
    let app_root = find_ide_app_root(explicit_root)
        .ok_or_else(|| "未检测到 Antigravity IDE 安装目录".to_string())?;
    let css_path = ide_workbench_css_path(&app_root);
    let bak_path = css_path.with_extension("css.agzh-bak");

    let clean_css = if bak_path.is_file() {
        std::fs::read_to_string(&bak_path)
            .map_err(|e| format!("读取备份 CSS 失败: {}", e))?
    } else {
        let cur = std::fs::read_to_string(&css_path)
            .map_err(|e| format!("读取 IDE CSS 失败: {}", e))?;
        strip_ide_skin_block(&cur)
    };

    atomic_write_text(&css_path, &clean_css)?;
    update_product_checksum(&app_root, clean_css.as_bytes())?;

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
            "body{{color:#000}}\n{}\n:root{{--a:1}}\n{}\n",
            IDE_SKIN_START, IDE_SKIN_END
        );
        let cleaned = strip_ide_skin_block(&src);
        assert_eq!(cleaned.trim(), "body{color:#000}");
    }
}
