use base64::{engine::general_purpose::STANDARD as BASE64_STANDARD, Engine as _};
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};
use std::collections::HashSet;
use std::io::{Read, Write};
use std::path::{Component, Path, PathBuf};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipArchive, ZipWriter};

use super::{atomic_write_bytes, atomic_write_text, config_dir, resources_dir, SkinInfo};

pub const SCHEMA_VERSION: u32 = 1;
pub const MAX_IMAGE_BYTES: usize = 8 * 1024 * 1024;
pub const MAX_FONT_BYTES: usize = 16 * 1024 * 1024;
pub const MAX_CSS_CHARS: usize = 200_000;
pub const MAX_ZIP_TOTAL_BYTES: u64 = 64 * 1024 * 1024;
pub const MAX_ZIP_FILES: usize = 500;

/// 标准材质包颜色变量字典（专为 Google Antigravity 独立桌面应用 AGY Hub 设计）
pub const COLOR_VARIABLES: &[(&str, &str)] = &[
    ("background", "主画布背景"),
    ("foreground", "主前景色 / 正文"),
    ("accent", "品牌主强调色 / 发送按钮"),
    ("accentForeground", "强调色按钮文字"),
    ("sidebar", "左侧会话与工作区导航栏"),
    ("titleBar", "顶部窗口标题栏"),
    ("panel", "深度思考卡与伴生工件舱"),
    ("border", "卡片与面板极细分割线"),
    ("selection", "会话选中与悬停高亮"),
    ("input", "底部指令输入舱背景"),
    ("muted", "次级说明与占位文字"),
];

pub const BACKGROUND_TARGETS: &[(&str, &str)] = &[
    (
        "window",
        "body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))) .agy-sheet [data-main-content-body], body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))):not(:has([data-main-content-body]))",
    ),
    (
        "app",
        "body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))) .agy-sheet [data-main-content-body], body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))):not(:has([data-main-content-body]))",
    ),
    (
        "conversation",
        "body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))) .agy-sheet [data-main-content-body], body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))):not(:has([data-main-content-body]))",
    ),
    (
        "chat",
        "body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))) .agy-sheet [data-main-content-body], body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))):not(:has([data-main-content-body]))",
    ),
    (
        "editor",
        "body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))) .agy-sheet [data-main-content-body], body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))):not(:has([data-main-content-body]))",
    ),
    (
        "sidebar",
        "aside, [data-sidebar='sidebar'], .agy-inset-shell [data-peek-surface], [data-testid='in-tab-sidebar-overlay']",
    ),
    (
        "composer",
        ".surface-composer > .surface-composer-card, form:has(textarea)",
    ),
    (
        "panel",
        "[data-side-panel-body], aside, [role='complementary']",
    ),
    ("modal", "[role='dialog'], .agy-dialog"),
    ("titlebar", ".agy-titlebar, header"),
];

pub const PET_CHARACTERS: &[&str] = &[
    "nezuko",
    "prince",
    "little-prince",
    "ushio",
    "clannad",
    "tanjiro",
    "zenitsu",
    "inosuke",
    "giyu",
    "shinobu",
    "none",
    "custom",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct StudioConfig {
    pub active_skin: Option<String>,
    pub skin_enabled: bool,
    pub ide_enabled: bool,
    pub install_dir: Option<String>,
    pub ide_install_dir: Option<String>,
    pub auto_reapply: bool,
    pub lang: String,
    pub splash_character: String,
    pub enable_pet: bool,
    pub enable_skin: bool,
    pub pet_character: String,
    pub pet_roaming: bool,
    pub pet_always_on_top: bool,
    pub pet_scale_idx: usize,
    pub pet_muted: bool,
    pub custom_pet_avatar: Option<String>,
    pub pet_size: u32,
    pub reapply_logs: Vec<String>,
}

impl Default for StudioConfig {
    fn default() -> Self {
        Self {
            active_skin: None,
            skin_enabled: false,
            ide_enabled: false,
            install_dir: None,
            ide_install_dir: None,
            auto_reapply: true,
            lang: "zh-cn".to_string(),
            splash_character: "none".to_string(),
            enable_pet: false,
            enable_skin: true,
            pet_character: "nezuko".to_string(),
            pet_roaming: true,
            pet_always_on_top: true,
            pet_scale_idx: 1,
            pet_muted: false,
            custom_pet_avatar: None,
            pet_size: 132,
            reapply_logs: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompiledSkin {
    pub skin_id: String,
    pub css: String,
    pub runtime_json: Value,
    pub compiled_css_path: String,
    pub compiled_runtime_path: String,
}

pub fn user_skins_dir() -> PathBuf {
    config_dir().join("skins")
}

pub fn builtin_skins_dir() -> PathBuf {
    resources_dir().join("skins")
}

pub fn overrides_dir() -> PathBuf {
    config_dir().join("skin-overrides")
}

pub fn global_override_path() -> PathBuf {
    overrides_dir().join("global.json")
}

pub fn skin_override_path(skin_id: &str) -> PathBuf {
    overrides_dir().join("skins").join(format!("{}.json", skin_id))
}

pub fn compiled_dir() -> PathBuf {
    config_dir().join("skin-compiled")
}

pub fn studio_config_path() -> PathBuf {
    config_dir().join("studio.json")
}

pub fn load_studio_config() -> StudioConfig {
    let path = studio_config_path();
    if let Ok(raw) = std::fs::read_to_string(&path) {
        if let Ok(cfg) = serde_json::from_str::<StudioConfig>(&raw) {
            return cfg;
        }
    }
    StudioConfig::default()
}

pub fn save_studio_config(cfg: &StudioConfig) -> Result<(), String> {
    let text = serde_json::to_string_pretty(cfg)
        .map_err(|e| format!("序列化 Studio 配置失败: {}", e))?;
    atomic_write_text(&studio_config_path(), &text)
}

static STUDIO_CONFIG_LOCK: std::sync::OnceLock<std::sync::Mutex<()>> = std::sync::OnceLock::new();

pub fn mutate_studio_config<F>(mutator: F) -> Result<StudioConfig, String>
where
    F: FnOnce(&mut StudioConfig),
{
    let lock = STUDIO_CONFIG_LOCK.get_or_init(|| std::sync::Mutex::new(()));
    let _guard = lock.lock().unwrap_or_else(|e| e.into_inner());
    let mut cfg = load_studio_config();
    mutator(&mut cfg);
    save_studio_config(&cfg)?;
    Ok(cfg)
}

pub fn append_reapply_log(msg: &str) {
    let mut cfg = load_studio_config();
    let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    cfg.reapply_logs.push(format!("[{}] {}", ts, msg));
    if cfg.reapply_logs.len() > 120 {
        let excess = cfg.reapply_logs.len() - 120;
        cfg.reapply_logs.drain(0..excess);
    }
    let _ = save_studio_config(&cfg);
}

/// 校验并安全解析皮肤包内部相对路径，严禁绝对路径或 `..` 目录穿越
pub fn safe_resolve_under(base_dir: &Path, rel_path: &str) -> Result<PathBuf, String> {
    let trimmed = rel_path.trim();
    if trimmed.is_empty() {
        return Err("路径不能为空".to_string());
    }
    let rel = Path::new(trimmed);
    if rel.is_absolute() {
        return Err(format!("禁止使用绝对路径: {}", rel_path));
    }
    for comp in rel.components() {
        match comp {
            Component::ParentDir | Component::RootDir | Component::Prefix(_) => {
                return Err(format!("检测到非法路径穿越字符: {}", rel_path));
            }
            Component::CurDir | Component::Normal(_) => {}
        }
    }
    let joined = base_dir.join(rel);
    if base_dir.exists() && joined.exists() {
        let canon_base = std::fs::canonicalize(base_dir)
            .map_err(|e| format!("解析基目录失败: {}", e))?;
        let canon_target = std::fs::canonicalize(&joined)
            .map_err(|e| format!("解析目标文件失败: {}", e))?;
        if !canon_target.starts_with(&canon_base) {
            return Err(format!("路径越界（超出皮肤包根目录）: {}", rel_path));
        }
    }
    Ok(joined)
}

pub fn validate_skin_id(id: &str) -> Result<(), String> {
    let re = Regex::new(r"^[a-z0-9][a-z0-9-_]{1,62}$").unwrap();
    if !re.is_match(id) {
        return Err(format!(
            "材质包 ID '{}' 不合法，仅支持 2-63 位小写字母、数字、'-' 或 '_'",
            id
        ));
    }
    Ok(())
}

/// 递归合并两份 JSON 对象（`over` 覆盖 `base`）
pub fn deep_merge(base: &Value, over: &Value) -> Value {
    match (base, over) {
        (Value::Object(b_map), Value::Object(o_map)) => {
            let mut merged = b_map.clone();
            for (k, v) in o_map {
                if v.is_null() {
                    merged.remove(k);
                } else if let Some(existing) = merged.get(k) {
                    merged.insert(k.clone(), deep_merge(existing, v));
                } else {
                    merged.insert(k.clone(), v.clone());
                }
            }
            Value::Object(merged)
        }
        (_, over_val) => over_val.clone(),
    }
}

fn check_css_safety(css: &str) -> Result<(), String> {
    if css.chars().count() > MAX_CSS_CHARS {
        return Err(format!(
            "CSS 内容超长（{} 字符），上限为 {} 字符",
            css.chars().count(),
            MAX_CSS_CHARS
        ));
    }
    let dangerous =
        Regex::new(r"(?i)(@import\s+url\s*\(\s*['\x22]?https?:|expression\s*\(|javascript:)")
            .unwrap();
    if dangerous.is_match(css) {
        return Err("CSS 包含不安全的远程 @import、expression() 或 javascript: 表达式".to_string());
    }
    Ok(())
}

fn mime_for_ext(ext: &str) -> &'static str {
    match ext.to_ascii_lowercase().as_str() {
        "png" => "image/png",
        "webp" => "image/webp",
        "jpg" | "jpeg" => "image/jpeg",
        "gif" => "image/gif",
        "svg" => "image/svg+xml",
        "avif" => "image/avif",
        "woff2" => "font/woff2",
        "woff" => "font/woff",
        "ttf" => "font/ttf",
        "otf" => "font/otf",
        _ => "application/octet-stream",
    }
}

fn encode_asset_data_uri(path: &Path, max_bytes: usize) -> Result<String, String> {
    let meta = std::fs::metadata(path)
        .map_err(|e| format!("读取资产文件元数据失败 {}: {}", path.display(), e))?;
    if meta.len() as usize > max_bytes {
        return Err(format!(
            "资产文件过大 ({} 字节，上限 {} 字节): {}",
            meta.len(),
            max_bytes,
            path.display()
        ));
    }
    let bytes = std::fs::read(path)
        .map_err(|e| format!("读取资产文件失败 {}: {}", path.display(), e))?;
    let ext = path.extension().and_then(|s| s.to_str()).unwrap_or("");
    let mime = mime_for_ext(ext);
    Ok(format!(
        "data:{};base64,{}",
        mime,
        BASE64_STANDARD.encode(&bytes)
    ))
}

fn resolve_asset_uri_or_inline(
    skin_dir: Option<&Path>,
    raw: &str,
    max_bytes: usize,
) -> Result<String, String> {
    let trimmed = raw.trim();
    if trimmed.is_empty() {
        return Ok(String::new());
    }
    if trimmed.starts_with("data:") {
        if trimmed.len() > max_bytes * 2 {
            return Err("内联 Data URI 体积超出安全阈值".to_string());
        }
        return Ok(trimmed.to_string());
    }
    if trimmed.starts_with("http://") || trimmed.starts_with("https://") {
        return Err("材质包禁止引用外部 HTTP(S) 资源，请使用本地相对路径或 Data URI".to_string());
    }
    let dir = skin_dir
        .ok_or_else(|| format!("无法解析相对路径资产（未知皮肤目录）: {}", trimmed))?;
    let resolved = safe_resolve_under(dir, trimmed)?;
    if !resolved.is_file() {
        return Err(format!("皮肤资产文件不存在: {}", trimmed));
    }
    encode_asset_data_uri(&resolved, max_bytes)
}

/// 校验 `skin.json` 清单合法性（同时兼容 `"schema"` 与 `"schema_version"`）
pub fn validate_manifest(manifest: &Value, skin_dir: Option<&Path>) -> Result<(), String> {
    let obj = manifest
        .as_object()
        .ok_or_else(|| "skin.json 根节点必须是 JSON 对象".to_string())?;

    let sv = obj
        .get("schema")
        .or_else(|| obj.get("schema_version"))
        .and_then(|v| v.as_u64())
        .unwrap_or(0);
    if sv != SCHEMA_VERSION as u64 {
        return Err(format!(
            "不支持的 schema 版本: {}（当前仅支持 {}）",
            sv, SCHEMA_VERSION
        ));
    }

    let id = obj
        .get("id")
        .and_then(|v| v.as_str())
        .ok_or_else(|| "skin.json 缺少合法字符串字段 'id'".to_string())?;
    validate_skin_id(id)?;

    let name = obj
        .get("name")
        .and_then(|v| v.as_str())
        .map(str::trim)
        .unwrap_or("");
    if name.is_empty() || name.chars().count() > 80 {
        return Err("skin.json 的 'name' 必须为 1-80 字符的非空字符串".to_string());
    }

    if let Some(css) = obj
        .get("css")
        .or_else(|| obj.get("custom_css"))
        .and_then(|v| v.as_str())
    {
        check_css_safety(css)?;
    }

    if let Some(css_file) = obj
        .get("cssFile")
        .or_else(|| obj.get("css_file"))
        .and_then(|v| v.as_str())
    {
        if let Some(dir) = skin_dir {
            let p = safe_resolve_under(dir, css_file)?;
            if !p.is_file() {
                return Err(format!("指定的样式文件不存在: {}", css_file));
            }
            let content = std::fs::read_to_string(&p)
                .map_err(|e| format!("读取样式文件失败: {}", e))?;
            check_css_safety(&content)?;
        }
    }

    if let Some(pet) = obj.get("pet").and_then(|v| v.as_object()) {
        if let Some(ch) = pet.get("character").and_then(|v| v.as_str()) {
            if !PET_CHARACTERS.contains(&ch) {
                return Err(format!("不支持的桌宠角色 '{}'", ch));
            }
        }
    }

    Ok(())
}

/// 定位皮肤包根目录（用户目录优先于内置目录）
pub fn find_skin_dir(skin_id: &str) -> Option<(PathBuf, bool)> {
    let user_dir = user_skins_dir().join(skin_id);
    if user_dir.join("skin.json").is_file() {
        return Some((user_dir, false));
    }
    let builtin_dir = builtin_skins_dir().join(skin_id);
    if builtin_dir.join("skin.json").is_file() {
        return Some((builtin_dir, true));
    }
    None
}

fn load_raw_manifest(dir: &Path) -> Result<Value, String> {
    let manifest_path = dir.join("skin.json");
    let raw = std::fs::read_to_string(&manifest_path)
        .map_err(|e| format!("读取 {} 失败: {}", manifest_path.display(), e))?;
    serde_json::from_str(&raw).map_err(|e| format!("解析 {} 失败: {}", manifest_path.display(), e))
}

/// 读取基础包及其继承链，并叠加全局覆盖与单包覆盖层
pub fn load_effective_manifest(skin_id: &str) -> Result<(PathBuf, bool, Value), String> {
    let (dir, builtin) =
        find_skin_dir(skin_id).ok_or_else(|| format!("未找到材质包 '{}'", skin_id))?;
    let mut visited = HashSet::new();
    visited.insert(skin_id.to_string());

    let manifest = load_raw_manifest(&dir)?;
    let mut chain = vec![(dir.clone(), manifest.clone())];

    let mut cur_manifest = manifest;
    while let Some(base_id) = cur_manifest
        .get("base")
        .and_then(|v| v.as_str())
        .map(str::trim)
        .filter(|s| !s.is_empty() && *s != "dark" && *s != "light")
    {
        if !visited.insert(base_id.to_string()) {
            return Err(format!("检测到材质包循环继承: {}", base_id));
        }
        if let Some((base_dir, _)) = find_skin_dir(base_id) {
            let base_manifest = load_raw_manifest(&base_dir)?;
            cur_manifest = base_manifest.clone();
            chain.push((base_dir, base_manifest));
        } else {
            break;
        }
    }

    chain.reverse();
    let mut merged = json!({});
    for (_, part) in &chain {
        merged = deep_merge(&merged, part);
    }

    if let Ok(raw) = std::fs::read_to_string(global_override_path()) {
        if let Ok(over) = serde_json::from_str::<Value>(&raw) {
            merged = deep_merge(&merged, &over);
        }
    }

    if let Ok(raw) = std::fs::read_to_string(skin_override_path(skin_id)) {
        if let Ok(over) = serde_json::from_str::<Value>(&raw) {
            merged = deep_merge(&merged, &over);
        }
    }

    Ok((dir, builtin, merged))
}

fn find_preview_uri(skin_dir: &Path, manifest: &Value) -> Option<String> {
    if let Some(rel) = manifest.get("preview").and_then(|v| v.as_str()) {
        if let Ok(uri) = resolve_asset_uri_or_inline(Some(skin_dir), rel, MAX_IMAGE_BYTES) {
            if !uri.is_empty() {
                return Some(uri);
            }
        }
    }
    for name in ["preview.png", "preview.webp", "preview.jpg", "preview.svg"] {
        let p = skin_dir.join(name);
        if p.is_file() {
            if let Ok(uri) = encode_asset_data_uri(&p, MAX_IMAGE_BYTES) {
                return Some(uri);
            }
        }
    }
    None
}

fn extract_skin_icon_preview(skin_dir: &Path, manifest: &Value) -> (Vec<String>, Option<String>) {
    let mut pack = Vec::new();
    let mut charm_uri = None;
    if let Some(icons) = manifest.get("icons").and_then(|v| v.as_object()) {
        if let Some(sem) = icons.get("semantic").and_then(|v| v.as_object()) {
            for key in [
                "app_logo",
                "new_chat",
                "automations",
                "customizations",
                "settings",
                "thinking",
            ] {
                if pack.len() >= 5 {
                    break;
                }
                if let Some(rel) = sem.get(key).and_then(|v| v.as_str()) {
                    if let Ok(uri) = resolve_asset_uri_or_inline(Some(skin_dir), rel, MAX_IMAGE_BYTES)
                    {
                        if !uri.is_empty() {
                            pack.push(uri);
                        }
                    }
                }
            }
        }
        if let Some(charm_rel) = icons.get("composer_charm").and_then(|v| v.as_str()) {
            if let Ok(uri) = resolve_asset_uri_or_inline(Some(skin_dir), charm_rel, MAX_IMAGE_BYTES)
            {
                if !uri.is_empty() {
                    charm_uri = Some(uri);
                }
            }
        }
    }
    (pack, charm_uri)
}

/// 枚举所有可用材质包（用户目录优先于同 ID 内置材质包）
pub fn list_skins() -> Vec<SkinInfo> {
    let cfg = load_studio_config();
    let active_id = cfg.active_skin.clone().unwrap_or_default();
    let mut seen = HashSet::new();
    let mut out = Vec::new();

    let scan_dir = |root: PathBuf,
                    builtin: bool,
                    seen: &mut HashSet<String>,
                    out: &mut Vec<SkinInfo>| {
        let Ok(entries) = std::fs::read_dir(&root) else {
            return;
        };
        let mut dirs: Vec<PathBuf> = entries
            .filter_map(|e| e.ok().map(|de| de.path()))
            .filter(|p| p.is_dir() && p.join("skin.json").is_file())
            .collect();
        dirs.sort();

        for dir in dirs {
            let Ok(raw) = load_raw_manifest(&dir) else {
                continue;
            };
            let id = raw
                .get("id")
                .and_then(|v| v.as_str())
                .map(|s| s.to_string())
                .unwrap_or_else(|| {
                    dir.file_name()
                        .and_then(|n| n.to_str())
                        .unwrap_or("unknown")
                        .to_string()
                });
            if !seen.insert(id.clone()) {
                continue;
            }
            let preview_data_uri = find_preview_uri(&dir, &raw);
            let (icon_pack, composer_charm_uri) = extract_skin_icon_preview(&dir, &raw);
            let colors = raw.get("colors").cloned().unwrap_or_else(|| json!({}));
            out.push(SkinInfo {
                id: id.clone(),
                name: raw
                    .get("name")
                    .and_then(|v| v.as_str())
                    .unwrap_or(&id)
                    .to_string(),
                version: raw
                    .get("version")
                    .and_then(|v| v.as_str())
                    .unwrap_or("1.0.0")
                    .to_string(),
                author: raw
                    .get("author")
                    .and_then(|v| v.as_str())
                    .unwrap_or("未知")
                    .to_string(),
                description: raw
                    .get("description")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string(),
                base: raw
                    .get("base")
                    .and_then(|v| v.as_str())
                    .unwrap_or("dark")
                    .to_string(),
                path: dir.to_string_lossy().to_string(),
                builtin,
                preview_data_uri,
                icon_pack,
                composer_charm_uri,
                colors,
                active: cfg.skin_enabled && id == active_id,
            });
        }
    };

    scan_dir(user_skins_dir(), false, &mut seen, &mut out);
    scan_dir(builtin_skins_dir(), true, &mut seen, &mut out);

    out.sort_by(|a, b| {
        b.active
            .cmp(&a.active)
            .then_with(|| a.builtin.cmp(&b.builtin).reverse())
            .then_with(|| a.id.cmp(&b.id))
    });
    out
}

fn background_selector(target: &str, custom_selector: Option<&str>) -> String {
    if let Some(sel) = custom_selector.map(str::trim).filter(|s| !s.is_empty()) {
        return sel.to_string();
    }
    for &(name, default_sel) in BACKGROUND_TARGETS {
        if name == target {
            return default_sel.to_string();
        }
    }
    "body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))) .agy-sheet [data-main-content-body], body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false']))):not(:has([data-main-content-body]))".to_string()
}

#[allow(dead_code)]
fn append_pseudo_to_selectors(selector_list: &str, pseudo: &str) -> String {
    selector_list
        .split(',')
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(|s| format!("{}::{}", s, pseudo))
        .collect::<Vec<_>>()
        .join(", ")
}

fn camel_to_kebab(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 4);
    for (i, ch) in s.chars().enumerate() {
        if ch.is_ascii_uppercase() {
            if i > 0 {
                out.push('-');
            }
            out.push(ch.to_ascii_lowercase());
        } else if ch == '_' {
            out.push('-');
        } else {
            out.push(ch);
        }
    }
    out
}

/// 将最终合并后的皮肤清单编译成针对 Google Antigravity 桌面应用（AGY Hub）的原生光学 CSS 与运行时 JSON
pub fn compile_skin(skin_id: &str) -> Result<CompiledSkin, String> {
    let (skin_dir, _builtin, manifest) = load_effective_manifest(skin_id)?;
    validate_manifest(&manifest, Some(&skin_dir))?;

    let is_light = manifest
        .get("base")
        .and_then(|v| v.as_str())
        .map(|s| s.trim().eq_ignore_ascii_case("light"))
        .unwrap_or(false);
    let color_scheme = if is_light { "light" } else { "dark" };

    let surfaces_obj = manifest.get("surfaces").and_then(|v| v.as_object());
    let prism_facets = surfaces_obj
        .and_then(|v| v.get("prism_facets"))
        .and_then(|v| v.as_bool())
        .unwrap_or(true);
    let rim_glow = surfaces_obj
        .and_then(|v| v.get("rim_glow"))
        .and_then(|v| v.as_bool())
        .unwrap_or(true);
    let code_enhance = surfaces_obj
        .and_then(|v| v.get("code_enhance"))
        .and_then(|v| v.as_bool())
        .unwrap_or(true);
    let ambient_aura = surfaces_obj
        .and_then(|v| v.get("ambient_aura"))
        .and_then(|v| v.as_bool())
        .unwrap_or(true);
    let backdrop_mode = surfaces_obj
        .and_then(|v| v.get("backdrop_mode"))
        .and_then(|v| v.as_str())
        .map(str::trim)
        .filter(|s| matches!(*s, "auto" | "light" | "off"))
        .unwrap_or("auto");
    let card_opacity = surfaces_obj
        .and_then(|v| v.get("card_opacity"))
        .and_then(|v| v.as_f64())
        .map(|v| v.clamp(0.25, 1.0));
    let border_glow_raw = surfaces_obj
        .and_then(|v| v.get("border_glow"))
        .and_then(|v| v.as_str())
        .map(str::trim)
        .filter(|s| !s.is_empty());
    let shadow_elevation_raw = surfaces_obj
        .and_then(|v| v.get("shadow_elevation"))
        .and_then(|v| v.as_str())
        .map(str::trim)
        .filter(|s| !s.is_empty());

    let no_hole_html = "html:not(:has(body[data-has-browser-hole='true'])):not(:has([data-browser-hole]:not([data-browser-hole='false'])))";
    let no_hole_body = "body:not([data-has-browser-hole='true']):not(:has([data-browser-hole]:not([data-browser-hole='false'])))";

    let mut css_parts: Vec<String> = Vec::new();
    css_parts.push(format!("/* [AGZH_SKIN_START:{}] */", skin_id));

    // 1. 颜色 CSS 变量 + Google Antigravity 桌面应用（AGY Hub Onyx + Tailwind v4）全量原生设计令牌映射
    let mut root_vars = Vec::new();
    root_vars.push(format!("  color-scheme: {} !important;", color_scheme));

    if let Some(colors) = manifest.get("colors").and_then(|v| v.as_object()) {
        for (k, v) in colors {
            if let Some(val) = v.as_str() {
                let val_trimmed = val.trim();
                let var_name = if k.starts_with("--") {
                    k.clone()
                } else {
                    format!("--agzh-{}", camel_to_kebab(k))
                };
                root_vars.push(format!("  {}: {} !important;", var_name, val_trimmed));
            }
        }

        let bg = colors
            .get("background")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(if is_light { "#fff8fb" } else { "#0b101b" });
        let fg = colors
            .get("foreground")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(if is_light { "#27272a" } else { "#edf2fb" });
        let acc = colors
            .get("accent")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(if is_light { "#2563eb" } else { "#38bdf8" });
        let acc_fg = colors
            .get("accentForeground")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(if is_light { "#ffffff" } else { "#06131f" });
        let default_sb = if is_light {
            format!("color-mix(in srgb, {} 94%, #000000)", bg)
        } else {
            format!("color-mix(in srgb, #000000 28%, {})", bg)
        };
        let sb = colors
            .get("sidebar")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(&default_sb);
        let tb = colors
            .get("titleBar")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(sb);
        let default_pn = if is_light {
            "#ffffff".to_string()
        } else {
            format!("color-mix(in srgb, {} 7.5%, {})", fg, bg)
        };
        let pn = colors
            .get("panel")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(&default_pn);
        let default_bd = if is_light {
            "rgba(15, 23, 42, 0.10)"
        } else {
            "rgba(255, 255, 255, 0.12)"
        };
        let bd = colors
            .get("border")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(default_bd);
        let default_sel = format!("color-mix(in srgb, {} 22%, transparent)", acc);
        let sel = colors
            .get("selection")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(&default_sel);
        let inp = colors
            .get("input")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(pn);
        let default_mt = format!("color-mix(in srgb, {} 58%, {})", fg, bg);
        let mt = colors
            .get("muted")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .unwrap_or(&default_mt);

        // 阶梯式光学表面计算：防止暗色皮肤卡片与黑底糊成一团，并彻底消除浅色宿主残留纯白块
        let elevated_card = if is_light {
            pn.to_string()
        } else {
            format!("color-mix(in srgb, {} 93%, {} 7%)", pn, fg)
        };
        let glass_surface = if let Some(op) = card_opacity {
            if op < 0.99 {
                format!(
                    "color-mix(in srgb, {} {:.0}%, transparent)",
                    elevated_card,
                    (op * 100.0).clamp(35.0, 100.0)
                )
            } else {
                elevated_card.clone()
            }
        } else {
            elevated_card.clone()
        };

        let secondary_surface = if is_light {
            format!("color-mix(in srgb, {} 6.5%, {})", fg, bg)
        } else {
            format!("color-mix(in srgb, {} 10%, {})", fg, bg)
        };
        let secondary_fg = format!("color-mix(in srgb, {} 84%, {})", fg, mt);
        let muted_surface = if is_light {
            format!("color-mix(in srgb, {} 4%, {})", fg, bg)
        } else {
            format!("color-mix(in srgb, {} 5.6%, {})", fg, bg)
        };
        let placeholder_fg = format!("color-mix(in srgb, {} 82%, {})", mt, bg);
        let sidebar_secondary = if is_light {
            format!("color-mix(in srgb, {} 7%, {})", fg, sb)
        } else {
            format!("color-mix(in srgb, {} 10.5%, {})", fg, sb)
        };
        let sidebar_muted = if is_light {
            format!("color-mix(in srgb, {} 4.5%, {})", fg, sb)
        } else {
            format!("color-mix(in srgb, {} 6.2%, {})", fg, sb)
        };
        let effective_border = if is_light {
            bd.to_string()
        } else {
            format!("color-mix(in srgb, {} 78%, rgba(255, 255, 255, 0.15))", bd)
        };
        let effective_card_border = if is_light {
            bd.to_string()
        } else {
            format!("color-mix(in srgb, {} 72%, rgba(255, 255, 255, 0.20))", bd)
        };
        let glass_highlight = border_glow_raw
            .map(|s| s.to_string())
            .unwrap_or_else(|| {
                if is_light {
                    "rgba(255, 255, 255, 0.88)".to_string()
                } else {
                    "rgba(255, 255, 255, 0.12)".to_string()
                }
            });
        let glass_shadow = shadow_elevation_raw
            .map(|s| s.to_string())
            .unwrap_or_else(|| {
                if is_light {
                    "0 14px 34px -10px rgba(15, 23, 42, 0.08), 0 2px 6px -1px rgba(15, 23, 42, 0.03)".to_string()
                } else {
                    "0 20px 46px -12px rgba(0, 0, 0, 0.62), 0 3px 10px -2px rgba(0, 0, 0, 0.36)".to_string()
                }
            });
        let card_edge = if is_light {
            format!("color-mix(in srgb, {} 75%, rgba(0, 0, 0, 0.08))", bd)
        } else {
            format!("color-mix(in srgb, {} 20%, rgba(255, 255, 255, 0.14))", acc)
        };
        let sash_line = if is_light {
            "rgba(15, 23, 42, 0.12)".to_string()
        } else {
            format!("color-mix(in srgb, {} 42%, rgba(255, 255, 255, 0.24))", acc)
        };
        let onyx_frame = if is_light {
            format!("color-mix(in srgb, {} 60%, {})", sb, bg)
        } else {
            format!("color-mix(in srgb, {} 72%, {})", sb, bg)
        };
        let onyx_well = if is_light {
            format!("color-mix(in srgb, {} 5.5%, {})", fg, bg)
        } else {
            format!("color-mix(in srgb, #000000 34%, {})", bg)
        };
        let onyx_raised = if is_light {
            inp.to_string()
        } else {
            format!("color-mix(in srgb, {} 92%, {} 8%)", inp, fg)
        };
        let onyx_key = if is_light {
            "#ffffff".to_string()
        } else {
            format!("color-mix(in srgb, {} 80%, {} 15%)", inp, fg)
        };
        let code_fg = if is_light {
            format!("color-mix(in srgb, {} 64%, {})", fg, acc)
        } else {
            format!("color-mix(in srgb, {} 72%, {})", fg, acc)
        };
        let code_block_bg = if is_light {
            format!("color-mix(in srgb, {} 4.5%, {})", fg, bg)
        } else {
            format!("color-mix(in srgb, {} 80%, #000000)", pn)
        };
        let home_glow = format!("color-mix(in srgb, {} 13%, transparent)", acc);
        let scrim = if is_light {
            "rgb(15 23 42 / 0.28)"
        } else {
            "rgb(0 0 0 / 0.66)"
        };
        let facet_top = if is_light {
            "rgba(255, 255, 255, 0.92)".to_string()
        } else {
            format!("color-mix(in srgb, {} 14%, rgba(255, 255, 255, 0.12))", acc)
        };
        let facet_edge = if is_light {
            format!("color-mix(in srgb, {} 82%, rgba(15, 23, 42, 0.08))", bd)
        } else {
            format!("color-mix(in srgb, {} 18%, {})", acc, effective_card_border)
        };
        let well_bg = if is_light {
            format!("color-mix(in srgb, {} 6.5%, {})", fg, bg)
        } else {
            format!("color-mix(in srgb, #000000 42%, {})", bg)
        };
        let kbd_bg = if is_light {
            format!("color-mix(in srgb, #ffffff 88%, {})", bg)
        } else {
            format!("color-mix(in srgb, {} 11%, {})", fg, onyx_key)
        };
        let kbd_shadow = if is_light {
            "0 1px 0 rgba(15, 23, 42, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.95)".to_string()
        } else {
            "0 1px 0 rgba(0, 0, 0, 0.58), inset 0 1px 0 rgba(255, 255, 255, 0.12)".to_string()
        };
        let chip_bg = if is_light {
            format!("color-mix(in srgb, {} 9%, {})", acc, pn)
        } else {
            format!("color-mix(in srgb, {} 11%, {})", acc, pn)
        };
        let chip_border = format!("color-mix(in srgb, {} 28%, {})", acc, effective_border);

        let token_pairs: Vec<(&str, String)> = vec![
            ("--agzh-bg", bg.to_string()),
            ("--background", bg.to_string()),
            ("--content", bg.to_string()),
            ("--sw-bg", bg.to_string()),
            ("--color-background-primary", bg.to_string()),
            ("--agzh-fg", fg.to_string()),
            ("--foreground", fg.to_string()),
            ("--card-foreground", fg.to_string()),
            ("--popover-foreground", fg.to_string()),
            ("--accent-foreground", fg.to_string()),
            ("--sidebar-foreground", fg.to_string()),
            ("--sidebar-accent-foreground", fg.to_string()),
            ("--sw-fg", fg.to_string()),
            ("--color-text-primary", fg.to_string()),
            ("--agzh-accent", acc.to_string()),
            ("--primary", acc.to_string()),
            ("--cta", acc.to_string()),
            ("--link", acc.to_string()),
            ("--ring", acc.to_string()),
            ("--sidebar-primary", acc.to_string()),
            ("--sidebar-ring", acc.to_string()),
            ("--sw-primary", acc.to_string()),
            ("--sw-ring", acc.to_string()),
            ("--color-ring-primary", acc.to_string()),
            ("--agzh-accent-fg", acc_fg.to_string()),
            ("--primary-foreground", acc_fg.to_string()),
            ("--cta-foreground", acc_fg.to_string()),
            ("--sidebar-primary-foreground", acc_fg.to_string()),
            ("--sw-primary-fg", acc_fg.to_string()),
            ("--agzh-sidebar", sb.to_string()),
            ("--sidebar", sb.to_string()),
            ("--sidebar-background", sb.to_string()),
            ("--shell", sb.to_string()),
            ("--shell-canvas", sb.to_string()),
            ("--sidebar-secondary", sidebar_secondary),
            ("--sidebar-muted", sidebar_muted),
            ("--color-background-secondary", sb.to_string()),
            ("--agzh-titlebar", tb.to_string()),
            ("--header-background", tb.to_string()),
            ("--agzh-panel", pn.to_string()),
            ("--agzh-card-surface", glass_surface.clone()),
            ("--card", elevated_card.clone()),
            ("--popover", elevated_card.clone()),
            ("--sw-card", elevated_card),
            ("--glass", glass_surface.clone()),
            ("--color-background-tertiary", glass_surface),
            ("--secondary", secondary_surface.clone()),
            ("--sw-secondary", secondary_surface),
            ("--secondary-foreground", secondary_fg),
            ("--muted", muted_surface.clone()),
            ("--sw-muted", muted_surface),
            ("--agzh-muted", mt.to_string()),
            ("--muted-foreground", mt.to_string()),
            ("--placeholder", placeholder_fg),
            ("--sw-fg-muted", mt.to_string()),
            ("--sw-fg-2", mt.to_string()),
            ("--sw-fg-faint", mt.to_string()),
            ("--color-text-secondary", mt.to_string()),
            ("--color-text-tertiary", mt.to_string()),
            ("--agzh-border", effective_border.clone()),
            ("--border", effective_border.clone()),
            ("--sidebar-border", effective_border.clone()),
            ("--sw-border", effective_border.clone()),
            ("--color-border-primary", effective_border),
            ("--card-border", effective_card_border.clone()),
            ("--sw-card-border", effective_card_border.clone()),
            ("--glass-border", effective_card_border),
            ("--glass-highlight", glass_highlight),
            ("--glass-shadow", glass_shadow),
            ("--card-edge", card_edge),
            ("--sash-line", sash_line),
            ("--agzh-selection", sel.to_string()),
            ("--accent", sel.to_string()),
            ("--sidebar-accent", sel.to_string()),
            ("--sw-fill", sel.to_string()),
            ("--onyx-selected", sel.to_string()),
            ("--agzh-input", onyx_raised.clone()),
            ("--input", onyx_raised.clone()),
            ("--sw-field", onyx_raised.clone()),
            ("--onyx-frame", onyx_frame),
            ("--onyx-well", onyx_well),
            ("--onyx-raised", onyx_raised),
            ("--onyx-key", onyx_key),
            ("--code-foreground", code_fg),
            ("--editor-code-block-background", code_block_bg),
            ("--editor-line-number-foreground", mt.to_string()),
            ("--editor-selection-background", sel.to_string()),
            ("--home-glow", home_glow),
            ("--scrim", scrim.to_string()),
            ("--agzh-facet-top", facet_top),
            ("--agzh-facet-edge", facet_edge),
            ("--agzh-well-bg", well_bg),
            ("--agzh-kbd-bg", kbd_bg),
            ("--agzh-kbd-shadow", kbd_shadow),
            ("--agzh-chip-bg", chip_bg),
            ("--agzh-chip-border", chip_border),
            ("--agzh-spring", "cubic-bezier(0.22, 1, 0.36, 1)".to_string()),
        ];

        let mut hub_overrides = Vec::with_capacity(token_pairs.len() + 1);
        hub_overrides.push(format!("  color-scheme: {} !important;", color_scheme));
        for (k, v) in token_pairs {
            hub_overrides.push(format!("  {}: {} !important;", k, v));
        }

        css_parts.push(format!(
            ":root, :root[data-theme], :root[data-theme='dark'], :root[data-theme='light'], html, body, body[data-agy-theme], body[data-agy-theme].dark, .agy-inset-shell, .dark .agy-inset-shell, .dark, .light {{\n{}\n}}",
            hub_overrides.join("\n")
        ));

        let mut base_rules = Vec::new();
        // 严格避让激活态浏览器透视孔，确保内置浏览器 WebContentsView 透视视口不被背景遮挡
        base_rules.push(format!(
            "{html_sel}, {body_sel} {{\n  background-color: {bg} !important;\n  color: {fg} !important;\n}}",
            html_sel = no_hole_html,
            body_sel = no_hole_body,
            bg = bg,
            fg = fg
        ));

        base_rules.push(format!(
            "aside, [data-sidebar='sidebar'], [data-testid='in-tab-sidebar-overlay'] {{ background-color: {} !important; border-color: var(--border) !important; }}",
            sb
        ));
        base_rules.push(format!(
            "header[data-testid*='titlebar'], [data-agzh-region='titlebar'] {{ background-color: {} !important; }}",
            tb
        ));
        base_rules.push(format!("::selection {{ background: {} !important; }}", sel));
        base_rules.push(format!(
            "::-webkit-scrollbar-thumb {{ background-color: color-mix(in srgb, {} 38%, transparent) !important; border-radius: 9999px; }}\n::-webkit-scrollbar-thumb:hover {{ background-color: color-mix(in srgb, {} 58%, transparent) !important; }}",
            acc, acc
        ));

        // 暗色材质深度加固：即便官方宿主原处于浅色模式 (.theme-light)，也强制统一高可读暗色代码高亮与 Onyx 组件光影
        if !is_light {
            base_rules.push(
                r#"body, .theme-light, .theme-dark {
  --syntax-default-fg: #eef3fb !important;
  --syntax-comment: #7f91ad !important;
  --syntax-punctuation: #cbd5e1 !important;
  --syntax-property: #fda4af !important;
  --syntax-deleted: #fb7185 !important;
  --syntax-inserted: #86efac !important;
  --syntax-tag: #fda4af !important;
  --syntax-constant: #f9a8d4 !important;
  --syntax-number: #d8b4fe !important;
  --syntax-string: #86efac !important;
  --syntax-attr-name: #6ee7b7 !important;
  --syntax-builtin: #67e8f9 !important;
  --syntax-operator: #cbd5e1 !important;
  --syntax-variable: #f1f5f9 !important;
  --syntax-attr-value: #fde047 !important;
  --syntax-keyword: #7dd3fc !important;
  --syntax-function: #fde047 !important;
  --syntax-class-name: #fcd34d !important;
  --syntax-regex: #fdba74 !important;
  --bg-selection: color-mix(in srgb, var(--primary) 32%, transparent) !important;
  --bg-selection-overlay: color-mix(in srgb, var(--primary) 24%, transparent) !important;
  --bg-cursor-line: rgba(255, 255, 255, 0.05) !important;
  --fg-cursor: #e2e8f0 !important;
}
.theme-light code[class*='language-'],
.theme-light pre[class*='language-'],
.theme-dark code[class*='language-'],
.theme-dark pre[class*='language-'] {
  color: var(--syntax-default-fg) !important;
  text-shadow: none !important;
}
.theme-light pre[class*='language-'],
.theme-dark pre[class*='language-'] {
  background: var(--editor-code-block-background) !important;
  border: 1px solid color-mix(in srgb, var(--border) 82%, transparent);
  border-radius: 10px;
}
.theme-light :not(pre) > code[class*='language-'],
.theme-dark :not(pre) > code[class*='language-'] {
  background: var(--secondary) !important;
  color: var(--code-foreground) !important;
  text-shadow: none !important;
}
body[data-agy-theme] .surface-composer {
  background-color: var(--onyx-frame) !important;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.35), 0 0 0 4px var(--onyx-frame), 0 0 0 5px color-mix(in srgb, var(--border) 75%, transparent), 0 18px 42px -12px rgba(0, 0, 0, 0.52) !important;
}
body[data-agy-theme] .surface-composer > .surface-composer-card {
  background-color: var(--onyx-raised) !important;
  box-shadow: inset 0 1px 0 var(--glass-highlight), 0 0 0 1px var(--glass-border), 0 4px 14px -2px rgba(0, 0, 0, 0.36) !important;
}
body[data-agy-theme] .surface-composer:focus-within > .surface-composer-card {
  box-shadow: inset 0 1px 0 var(--glass-highlight), 0 0 0 1px color-mix(in srgb, var(--primary) 42%, var(--glass-border)), 0 8px 24px -4px rgba(0, 0, 0, 0.45) !important;
}
body[data-agy-theme] [data-slot='toggle-group'] {
  background-color: var(--onyx-well) !important;
  border-color: var(--border) !important;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}
body[data-agy-theme] [data-slot='toggle-group'] > button[data-pressed] {
  background-color: var(--onyx-key) !important;
  color: var(--foreground) !important;
  box-shadow: inset 0 1px 0 var(--glass-highlight), 0 1px 3px rgba(0, 0, 0, 0.35) !important;
}
body[data-agy-theme] .agy-sidebar-row[data-selected='true'] {
  background-color: var(--onyx-selected) !important;
  --row-bg: var(--onyx-selected) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), inset 0 0 0 1px color-mix(in srgb, var(--primary) 26%, transparent) !important;
}
body[data-agy-theme] .artifact-card,
body[data-agy-theme] .agy-card,
body[data-agy-theme] .agy-callout {
  background-color: var(--glass) !important;
  border-color: var(--card-border) !important;
  box-shadow: inset 0 1px 0 var(--glass-highlight), 0 8px 24px -8px rgba(0, 0, 0, 0.36);
}"#
                .to_string(),
            );
        }

        css_parts.push(base_rules.join("\n"));
    }

    // 2. 自定义 variables 对象
    if let Some(vars) = manifest.get("variables").and_then(|v| v.as_object()) {
        for (k, v) in vars {
            if let Some(val) = v.as_str() {
                let var_name = if k.starts_with("--") {
                    k.clone()
                } else {
                    format!("--{}", k)
                };
                root_vars.push(format!("  {}: {} !important;", var_name, val.trim()));
            }
        }
    }

    // 3. 物理表面质感 & 字体（精准绑定官方 Onyx 类名，绝不注入全屏顶层摩尔纹白雾遮罩）
    if let Some(surfaces) = surfaces_obj {
        if let Some(radius) = surfaces.get("radius").and_then(|v| v.as_str()) {
            root_vars.push(format!("  --agzh-radius: {} !important;", radius));
            root_vars.push(format!("  --radius: {} !important;", radius));
            root_vars.push(format!("  --card-radius: {} !important;", radius));
            root_vars.push(format!("  --nux-radius-lg: {} !important;", radius));
            css_parts.push(format!(
                "[role='dialog'], [role='menu'], [role='listbox'], .surface-composer > .surface-composer-card, form:has(textarea) {{ border-radius: {}; }}",
                radius
            ));
        }
        if let Some(blur) = surfaces.get("glass_blur").and_then(|v| v.as_u64()) {
            let effective_blur = match backdrop_mode {
                "off" => 0,
                "light" => (blur / 2).max(4),
                _ => blur,
            };
            root_vars.push(format!("  --agzh-glass-blur: {}px !important;", effective_blur));
            if effective_blur > 0 {
                css_parts.push(format!(
                    ".surface-glass, .agy-takeover-card, .agy-fastpick, .surface-composer > .surface-composer-card, [role='dialog'], [role='menu'], [role='listbox'] {{ backdrop-filter: blur({}px) saturate(1.35) !important; -webkit-backdrop-filter: blur({}px) saturate(1.35) !important; }}",
                    effective_blur, effective_blur
                ));
            }
        }
        if let Some(opacity) = surfaces.get("card_opacity").and_then(|v| v.as_f64()) {
            root_vars.push(format!(
                "  --agzh-card-opacity: {:.3} !important;",
                opacity.clamp(0.25, 1.0)
            ));
        }
        if let Some(glow) = surfaces.get("border_glow").and_then(|v| v.as_str()) {
            root_vars.push(format!("  --agzh-border-glow: {} !important;", glow));
            css_parts.push(format!(
                "[role='dialog'], [role='menu'], [role='listbox'] {{ box-shadow: inset 0 1px 0 {}, var(--agzh-shadow-elevation, 0 20px 50px rgba(0,0,0,0.45)) !important; }}",
                glow
            ));
        }
        if let Some(grain) = surfaces.get("noise_grain").and_then(|v| v.as_f64()) {
            let clamped_grain = grain.clamp(0.0, 0.12);
            root_vars.push(format!("  --agzh-noise-grain: {:.3} !important;", clamped_grain));
        }
        if let Some(shadow) = surfaces.get("shadow_elevation").and_then(|v| v.as_str()) {
            root_vars.push(format!("  --agzh-shadow-elevation: {} !important;", shadow));
        }
    }

    let font_obj = manifest
        .get("font")
        .or_else(|| manifest.get("typography"))
        .and_then(|v| v.as_object());
    if let Some(typo) = font_obj {
        if let Some(font_family) = typo
            .get("family")
            .or_else(|| typo.get("font_family"))
            .and_then(|v| v.as_str())
        {
            root_vars.push(format!("  --agzh-font-sans: {} !important;", font_family));
            root_vars.push(format!("  --font-family: {} !important;", font_family));
            root_vars.push(format!("  --font-sans: {} !important;", font_family));
            root_vars.push(format!("  --default-font-family: {} !important;", font_family));
            css_parts.push(format!(
                "body, body[data-agy-font], #root {{ font-family: {} !important; }}",
                font_family
            ));
        }
        if let Some(mono_family) = typo
            .get("monoFamily")
            .or_else(|| typo.get("mono_family"))
            .and_then(|v| v.as_str())
        {
            root_vars.push(format!("  --agzh-font-mono: {} !important;", mono_family));
            root_vars.push(format!("  --editor-font-family: {} !important;", mono_family));
            root_vars.push(format!("  --font-mono: {} !important;", mono_family));
            root_vars.push(format!(
                "  --default-mono-font-family: {} !important;",
                mono_family
            ));
            css_parts.push(format!(
                "code, pre, kbd, samp, .code-block {{ font-family: {} !important; }}",
                mono_family
            ));
        }
        if let Some(size) = typo.get("size").and_then(|v| v.as_u64()) {
            let clamped = size.clamp(11, 22);
            root_vars.push(format!("  --agzh-font-size: {}px !important;", clamped));
            // 仅当用户显式将字号调离默认 13/14px 时按比例微调全局字号倍率，不破坏 --text-sm 原生梯度
            if clamped != 13 && clamped != 14 {
                let scale = (clamped as f64 / 14.0).clamp(0.82, 1.35);
                root_vars.push(format!("  --app-font-scale: {:.3} !important;", scale));
            }
        }
        if let Some(font_file) = typo
            .get("file")
            .or_else(|| typo.get("font_file"))
            .and_then(|v| v.as_str())
        {
            if let Ok(uri) = resolve_asset_uri_or_inline(Some(&skin_dir), font_file, MAX_FONT_BYTES)
            {
                if !uri.is_empty() {
                    let custom_name = typo
                        .get("font_name")
                        .and_then(|v| v.as_str())
                        .unwrap_or("AgzhCustomFont");
                    css_parts.push(format!(
                        "@font-face {{\n  font-family: '{}';\n  src: url('{}');\n  font-display: swap;\n}}",
                        custom_name, uri
                    ));
                    root_vars.push(format!(
                        "  --agzh-font-sans: '{}', system-ui, sans-serif !important;",
                        custom_name
                    ));
                    root_vars.push(format!(
                        "  --font-family: '{}', system-ui, sans-serif !important;",
                        custom_name
                    ));
                }
            }
        }
    }

    if !root_vars.is_empty() {
        css_parts.push(format!(":root {{\n{}\n}}", root_vars.join("\n")));
    }

    // 3.5 棱镜光学切面、近场指针高光、代码块与控制台凹槽增强（完全消费各材质自身颜色令牌，自适应深浅）
    if prism_facets {
        let facets_css = r#"
__BODY__ .agy-user-bubble,
__BODY__ [data-testid*="user-message"] {
  background-image: linear-gradient(180deg, color-mix(in srgb, var(--agzh-accent, var(--primary)) 10%, transparent) 0%, transparent 100%) !important;
  border-color: var(--agzh-facet-edge, var(--card-border)) !important;
  box-shadow: inset 0 1px 0 var(--agzh-facet-top), 0 6px 18px -8px rgba(0, 0, 0, 0.24) !important;
}
__BODY__ .artifact-card,
__BODY__ .agy-card,
__BODY__ .agy-callout,
__BODY__ [data-testid*="diff-card"] {
  border-color: var(--agzh-facet-edge, var(--card-border)) !important;
  box-shadow: inset 0 1px 0 var(--agzh-facet-top), 0 8px 24px -10px rgba(0, 0, 0, 0.22);
}
__BODY__ kbd {
  font-family: var(--agzh-font-mono, monospace);
  font-size: 0.85em;
  line-height: 1.25;
  padding: 1px 6px 2px;
  border-radius: 6px;
  background-color: var(--agzh-kbd-bg) !important;
  color: var(--foreground) !important;
  border: 1px solid var(--agzh-facet-edge, var(--border)) !important;
  border-bottom-width: 2px !important;
  box-shadow: var(--agzh-kbd-shadow) !important;
}
__BODY__ a[data-file-path],
__BODY__ [data-testid*="file-chip"],
__BODY__ .file-pill {
  background-color: var(--agzh-chip-bg) !important;
  border: 1px solid var(--agzh-chip-border) !important;
  border-radius: 9999px !important;
  padding: 1px 8px !important;
  box-shadow: none !important;
  transition: background-color 0.18s var(--agzh-spring), border-color 0.18s var(--agzh-spring);
}
__BODY__ a[data-file-path]:hover,
__BODY__ [data-testid*="file-chip"]:hover,
__BODY__ .file-pill:hover {
  background-color: color-mix(in srgb, var(--agzh-accent, var(--primary)) 20%, var(--panel, var(--card))) !important;
  border-color: color-mix(in srgb, var(--agzh-accent, var(--primary)) 50%, var(--border)) !important;
}
__BODY__ [data-testid*="terminal"],
__BODY__ [data-testid*="command-output"],
__BODY__ [data-testid*="background-task"],
__BODY__ .terminal-container,
__BODY__ pre:has(> code.language-bash),
__BODY__ pre:has(> code.language-sh),
__BODY__ pre:has(> code.language-powershell) {
  background-color: var(--agzh-well-bg) !important;
  border: 1px solid color-mix(in srgb, var(--border) 88%, transparent) !important;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.22), inset 0 0 0 1px rgba(0, 0, 0, 0.06) !important;
}"#
        .replace("__BODY__", no_hole_body);
        css_parts.push(facets_css);
    }

    if rim_glow {
        let rim_css = r#"
__BODY__ [data-agzh-rim-active="1"] {
  background-image: radial-gradient(240px circle at var(--agzh-mx, -999px) var(--agzh-my, -999px), color-mix(in srgb, var(--agzh-accent, var(--primary)) 16%, transparent) 0%, transparent 72%) !important;
  border-color: color-mix(in srgb, var(--agzh-accent, var(--primary)) 46%, var(--border)) !important;
  box-shadow: inset 0 1px 0 var(--agzh-facet-top), 0 0 0 1px color-mix(in srgb, var(--agzh-accent, var(--primary)) 22%, transparent), 0 10px 26px -10px color-mix(in srgb, var(--agzh-accent, var(--primary)) 28%, transparent) !important;
}"#
        .replace("__BODY__", no_hole_body);
        css_parts.push(rim_css);
    }

    if code_enhance {
        let code_css = r#"
__BODY__ pre {
  position: relative;
}
__BODY__ pre > div:first-child:has(button),
__BODY__ [data-testid*="code-block-header"] {
  position: sticky;
  top: 0;
  z-index: 4;
  background-color: color-mix(in srgb, var(--editor-code-block-background, var(--panel)) 92%, transparent);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid color-mix(in srgb, var(--border) 72%, transparent);
}
__BODY__ .agzh-code-fold-btn {
  position: absolute;
  top: 8px;
  right: 10px;
  z-index: 6;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.5;
  cursor: pointer;
  color: var(--foreground);
  background: color-mix(in srgb, var(--agzh-accent, var(--primary)) 16%, var(--panel, var(--card)));
  border: 1px solid color-mix(in srgb, var(--agzh-accent, var(--primary)) 38%, var(--border));
  transition: transform 0.16s var(--agzh-spring), background-color 0.16s var(--agzh-spring);
}
__BODY__ .agzh-code-fold-btn:hover {
  transform: translateY(-1px);
  background: color-mix(in srgb, var(--agzh-accent, var(--primary)) 26%, var(--panel, var(--card)));
}
__BODY__ pre[data-agzh-code-folded="1"] {
  max-height: 220px !important;
  overflow: hidden !important;
  mask-image: linear-gradient(180deg, #000 68%, transparent 100%);
  -webkit-mask-image: linear-gradient(180deg, #000 68%, transparent 100%);
}
__BODY__ .agzh-rail-hud {
  position: fixed;
  right: 18px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 55;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 6px 4px;
  border-radius: 9999px;
  background: color-mix(in srgb, var(--panel, var(--card)) 88%, transparent);
  border: 1px solid var(--agzh-facet-edge, var(--border));
  box-shadow: inset 0 1px 0 var(--agzh-facet-top), 0 10px 26px -8px rgba(0, 0, 0, 0.34);
  backdrop-filter: blur(10px);
}
__BODY__ .agzh-rail-btn {
  width: 24px;
  height: 24px;
  border-radius: 9999px;
  border: none;
  background: transparent;
  color: var(--foreground);
  font-size: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s var(--agzh-spring), color 0.15s var(--agzh-spring);
}
__BODY__ .agzh-rail-btn:hover {
  background: color-mix(in srgb, var(--agzh-accent, var(--primary)) 22%, transparent);
  color: var(--agzh-accent, var(--primary));
}
__BODY__ .agzh-rail-count {
  font-size: 10px;
  font-family: var(--agzh-font-mono, monospace);
  color: var(--muted-foreground);
  padding: 1px 3px;
  user-select: none;
}
__BODY__ .agzh-rail-popover {
  display: none;
  position: absolute;
  right: calc(100% + 10px);
  top: 50%;
  transform: translateY(-50%);
  width: 230px;
  max-height: 280px;
  overflow-y: auto;
  padding: 6px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--panel, var(--card)) 94%, transparent);
  border: 1px solid var(--agzh-facet-edge, var(--border));
  box-shadow: inset 0 1px 0 var(--agzh-facet-top), 0 16px 36px -10px rgba(0, 0, 0, 0.42);
  backdrop-filter: blur(12px);
}
__BODY__ .agzh-rail-hud:hover .agzh-rail-popover {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
__BODY__ .agzh-rail-item {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  color: var(--foreground);
  font-size: 11px;
  padding: 5px 8px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
__BODY__ .agzh-rail-item:hover,
__BODY__ .agzh-rail-item.is-active {
  background: color-mix(in srgb, var(--agzh-accent, var(--primary)) 20%, transparent);
  color: var(--agzh-accent, var(--primary));
}"#
        .replace("__BODY__", no_hole_body);
        css_parts.push(code_css);
    }

    if ambient_aura {
        let aura_css = r#"
__BODY__ #agzh-aura-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  pointer-events: none;
  z-index: 60;
  opacity: 0;
  transition: opacity 0.28s var(--agzh-spring), background 0.28s var(--agzh-spring);
}
html[data-agzh-aura="thinking"] __BODY__ #agzh-aura-bar {
  opacity: 0.92;
  background: linear-gradient(90deg, transparent 0%, var(--agzh-accent, var(--primary)) 50%, transparent 100%);
  box-shadow: 0 0 14px color-mix(in srgb, var(--agzh-accent, var(--primary)) 65%, transparent);
}
html[data-agzh-aura="attention"] __BODY__ #agzh-aura-bar {
  opacity: 0.96;
  background: linear-gradient(90deg, transparent 0%, #f59e0b 50%, transparent 100%);
  box-shadow: 0 0 16px rgba(245, 158, 11, 0.65);
}
__BODY__ button,
__BODY__ [role="button"],
__BODY__ .artifact-card,
__BODY__ .agy-card {
  transition: transform 0.18s var(--agzh-spring), border-color 0.18s var(--agzh-spring), box-shadow 0.18s var(--agzh-spring), background-color 0.18s var(--agzh-spring);
}
@media (prefers-reduced-motion: reduce) {
  __BODY__ *,
  __BODY__ #agzh-aura-bar {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}"#
        .replace("__BODY__", no_hole_body);
        css_parts.push(aura_css);
    }

    // 4. 底层画布背景插画与环境极光合成（严格置于容器 background 层，绝不盖在文字与卡片上方）
    let mut bg_items: Vec<(String, Map<String, Value>)> = Vec::new();
    if let Some(bg_val) = manifest.get("background").or_else(|| manifest.get("backgrounds")) {
        if let Some(arr) = bg_val.as_array() {
            for item in arr {
                if let Some(obj) = item.as_object() {
                    let target = obj
                        .get("target")
                        .and_then(|v| v.as_str())
                        .unwrap_or("conversation")
                        .to_string();
                    bg_items.push((target, obj.clone()));
                }
            }
        } else if let Some(obj) = bg_val.as_object() {
            if obj.contains_key("image") || obj.contains_key("file") {
                let target = obj
                    .get("target")
                    .and_then(|v| v.as_str())
                    .unwrap_or("conversation")
                    .to_string();
                bg_items.push((target, obj.clone()));
            } else {
                for (target, sub) in obj {
                    if let Some(sub_obj) = sub.as_object() {
                        bg_items.push((target.clone(), sub_obj.clone()));
                    }
                }
            }
        }
    }

    let mut resolved_backgrounds = Vec::new();
    let mut has_main_canvas_bg = false;
    let main_canvas_selector = format!(
        "{body} .agy-sheet:not([data-split-panes] *) [data-main-content-body], {body}:not(:has([data-main-content-body]))",
        body = no_hole_body
    );

    for (idx, (target, cfg)) in bg_items.iter().enumerate() {
        if cfg.get("enabled").and_then(|v| v.as_bool()) == Some(false) {
            continue;
        }
        let image_raw = cfg
            .get("image")
            .or_else(|| cfg.get("file"))
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let uri = resolve_asset_uri_or_inline(Some(&skin_dir), image_raw, MAX_IMAGE_BYTES)?;
        if uri.is_empty() {
            continue;
        }
        let custom_sel = cfg.get("selector").and_then(|v| v.as_str());
        let is_viewport_layer = custom_sel.is_none()
            && matches!(
                target.as_str(),
                "window" | "app" | "conversation" | "chat" | "editor"
            );

        let selector = if is_viewport_layer {
            has_main_canvas_bg = true;
            main_canvas_selector.clone()
        } else {
            background_selector(target, custom_sel)
        };

        let opacity = cfg
            .get("opacity")
            .and_then(|v| v.as_f64())
            .unwrap_or(0.16)
            .clamp(0.0, 0.85);
        let blur = cfg.get("blur").and_then(|v| v.as_u64()).unwrap_or(0);
        let size = cfg
            .get("size")
            .and_then(|v| v.as_str())
            .unwrap_or("cover");
        let position = cfg
            .get("position")
            .and_then(|v| v.as_str())
            .unwrap_or("center center");
        let repeat = cfg
            .get("repeat")
            .and_then(|v| v.as_str())
            .unwrap_or("no-repeat");

        let base_var = if target == "sidebar" {
            "var(--sidebar)"
        } else {
            "var(--background)"
        };
        let veil_pct = ((1.0 - opacity) * 100.0).clamp(15.0, 100.0);

        if is_viewport_layer {
            let ambient_pct = if is_light { 7 } else { 9 };
            css_parts.push(format!(
                "{sel} /* bg-{idx} */ {{\n  background-color: {base} !important;\n  background-image: radial-gradient(82% 44% at 50% 0%, color-mix(in srgb, var(--agzh-accent, var(--primary)) {amb}%, transparent) 0%, transparent 74%), linear-gradient(color-mix(in srgb, {base} {veil:.1}%, transparent), color-mix(in srgb, {base} {veil:.1}%, transparent)), url('{uri}') !important;\n  background-size: 100% 100%, 100% 100%, {size} !important;\n  background-position: top center, center center, {pos} !important;\n  background-repeat: no-repeat, no-repeat, {repeat} !important;\n}}",
                sel = selector,
                idx = idx,
                base = base_var,
                amb = ambient_pct,
                veil = veil_pct,
                uri = uri,
                size = size,
                pos = position,
                repeat = repeat
            ));
        } else {
            css_parts.push(format!(
                "{sel} /* bg-{idx} */ {{\n  background-color: {base} !important;\n  background-image: linear-gradient(color-mix(in srgb, {base} {veil:.1}%, transparent), color-mix(in srgb, {base} {veil:.1}%, transparent)), url('{uri}') !important;\n  background-size: 100% 100%, {size} !important;\n  background-position: center center, {pos} !important;\n  background-repeat: no-repeat, {repeat} !important;\n}}",
                sel = selector,
                idx = idx,
                base = base_var,
                veil = veil_pct,
                uri = uri,
                size = size,
                pos = position,
                repeat = repeat
            ));
        }

        resolved_backgrounds.push(json!({
            "target": target,
            "selector": selector,
            "opacity": opacity,
            "blur": blur,
            "size": size,
            "position": position,
            "repeat": repeat,
            "data_uri": uri,
        }));
    }

    // 对于未携带插画贴图的暗色材质（如黑曜石、朱漆、北境极光），注入柔和双焦点环境天光，消除纯色死黑平板感
    if !has_main_canvas_bg && !is_light {
        css_parts.push(format!(
            "{sel} {{\n  background-color: var(--background) !important;\n  background-image: radial-gradient(78% 42% at 50% 0%, color-mix(in srgb, var(--agzh-accent, var(--primary)) 9%, transparent) 0%, transparent 72%), radial-gradient(56% 40% at 88% 96%, color-mix(in srgb, var(--agzh-accent, var(--primary)) 5%, transparent) 0%, transparent 70%) !important;\n  background-repeat: no-repeat !important;\n}}",
            sel = main_canvas_selector
        ));
    }

    // 5. 应用内矢量图标色调与专属动漫角色/团子图标映射（支持 semantic、composer_charm 与 codicons）
    let mut resolved_icons = Map::new();
    let mut icon_root_vars = Vec::new();
    let mut has_semantic_icons = false;
    let mut has_composer_charm = false;

    if let Some(icons) = manifest.get("icons").and_then(|v| v.as_object()) {
        if let Some(filter) = icons.get("filter").and_then(|v| v.as_str()) {
            css_parts.push(format!("aside svg {{ filter: {}; }}", filter));
        }
        if let Some(color) = icons.get("color").and_then(|v| v.as_str()) {
            icon_root_vars.push(format!("  --agzh-icon-accent: {};", color));
        }
        if let Some(semantic) = icons.get("semantic").and_then(|v| v.as_object()) {
            for (icon_key, raw_path) in semantic {
                if let Some(rel) = raw_path.as_str() {
                    if let Ok(uri) =
                        resolve_asset_uri_or_inline(Some(&skin_dir), rel, MAX_IMAGE_BYTES)
                    {
                        if !uri.is_empty() {
                            let kebab = camel_to_kebab(icon_key);
                            icon_root_vars
                                .push(format!("  --agzh-icon-{}: url('{}');", kebab, uri));
                            resolved_icons.insert(icon_key.clone(), Value::String(uri));
                            has_semantic_icons = true;
                        }
                    }
                }
            }
        }
        if let Some(charm_rel) = icons.get("composer_charm").and_then(|v| v.as_str()) {
            if let Ok(uri) =
                resolve_asset_uri_or_inline(Some(&skin_dir), charm_rel, MAX_IMAGE_BYTES)
            {
                if !uri.is_empty() {
                    icon_root_vars.push(format!("  --agzh-composer-charm: url('{}');", uri));
                    resolved_icons
                        .insert("composer_charm".to_string(), Value::String(uri));
                    has_composer_charm = true;
                }
            }
        }
        if let Some(codicons) = icons.get("codicons").and_then(|v| v.as_object()) {
            for (icon_key, raw_path) in codicons {
                if let Some(rel) = raw_path.as_str() {
                    if let Ok(uri) =
                        resolve_asset_uri_or_inline(Some(&skin_dir), rel, MAX_IMAGE_BYTES)
                    {
                        if !uri.is_empty() {
                            resolved_icons.insert(icon_key.clone(), Value::String(uri));
                        }
                    }
                }
            }
        }
    }

    // 6. 外部样式文件与自定义 CSS
    let mut external_css_loaded = false;
    if let Some(css_file) = manifest
        .get("cssFile")
        .or_else(|| manifest.get("css_file"))
        .and_then(|v| v.as_str())
    {
        let p = safe_resolve_under(&skin_dir, css_file)?;
        let content =
            std::fs::read_to_string(&p).map_err(|e| format!("读取样式文件失败: {}", e))?;
        check_css_safety(&content)?;
        external_css_loaded = content.contains("--agzh-icon-");
        css_parts.push(content);
    }

    if !icon_root_vars.is_empty() && !external_css_loaded {
        css_parts.push(format!(":root {{\n{}\n}}", icon_root_vars.join("\n")));
        if has_semantic_icons {
            css_parts.push(format!(
                r#"{body} [data-testid="app-icon-new-conversation-button"] svg,
{body} [data-testid="sidebar-header-logo"] svg,
{body} [data-testid="suggested-action-antigravity-icon"] svg {{
  background: var(--agzh-icon-app-logo) center / contain no-repeat !important;
}}
{body} [data-testid="app-icon-new-conversation-button"] svg > *,
{body} [data-testid="sidebar-header-logo"] svg > *,
{body} [data-testid="suggested-action-antigravity-icon"] svg > * {{
  opacity: 0 !important;
}}"#,
                body = no_hole_body
            ));
        }
        if has_composer_charm {
            css_parts.push(format!(
                r#"{body} .surface-composer,
{body} .surface-composer-card {{ overflow: visible !important; position: relative !important; }}
{body} .surface-composer-card::after {{
  content: ''; position: absolute; right: 18px; top: -21px; width: 68px; height: 24px;
  pointer-events: none; z-index: 12; background: var(--agzh-composer-charm) right bottom / contain no-repeat; opacity: 0.9;
}}"#,
                body = no_hole_body
            ));
        }
    }
    if let Some(custom_css) = manifest
        .get("css")
        .or_else(|| manifest.get("custom_css"))
        .and_then(|v| v.as_str())
    {
        if !custom_css.trim().is_empty() {
            check_css_safety(custom_css)?;
            css_parts.push(custom_css.to_string());
        }
    }

    css_parts.push("/* [AGZH_SKIN_END] */".to_string());
    let final_css = css_parts.join("\n\n");

    let mut pet_runtime = manifest.get("pet").cloned().unwrap_or_else(|| json!({}));
    if let Some(pet_obj) = pet_runtime.as_object_mut() {
        if let Some(raw_avatar) = pet_obj
            .get("image")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string())
        {
            if let Ok(uri) =
                resolve_asset_uri_or_inline(Some(&skin_dir), &raw_avatar, MAX_IMAGE_BYTES)
            {
                if !uri.is_empty() {
                    pet_obj.insert("image_data_uri".to_string(), Value::String(uri));
                }
            }
        }
    }

    let runtime_json = json!({
        "skin_id": skin_id,
        "name": manifest.get("name").cloned().unwrap_or_else(|| json!(skin_id)),
        "base": manifest.get("base").cloned().unwrap_or_else(|| json!("dark")),
        "colors": manifest.get("colors").cloned().unwrap_or_else(|| json!({})),
        "surfaces": manifest.get("surfaces").cloned().unwrap_or_else(|| json!({})),
        "prism": {
            "facets": prism_facets,
            "rim_glow": rim_glow,
            "code_enhance": code_enhance,
            "ambient_aura": ambient_aura,
            "backdrop_mode": backdrop_mode,
        },
        "backgrounds": resolved_backgrounds,
        "icons": resolved_icons,
        "pet": pet_runtime,
        "splash": manifest.get("splash").cloned().unwrap_or_else(|| json!({})),
        "css": final_css,
    });

    let cdir = compiled_dir();
    let css_path = cdir.join("skin.css");
    let runtime_path = cdir.join("skin-runtime.json");
    atomic_write_text(&css_path, &final_css)?;
    atomic_write_text(
        &runtime_path,
        &serde_json::to_string_pretty(&runtime_json).unwrap_or_default(),
    )?;

    Ok(CompiledSkin {
        skin_id: skin_id.to_string(),
        css: final_css,
        runtime_json,
        compiled_css_path: css_path.to_string_lossy().to_string(),
        compiled_runtime_path: runtime_path.to_string_lossy().to_string(),
    })
}

pub fn save_override(scope: &str, skin_id: Option<&str>, patch: Value) -> Result<(), String> {
    if !patch.is_object() {
        return Err("覆盖层数据必须是 JSON 对象".to_string());
    }
    let target_path = match scope {
        "global" => global_override_path(),
        "skin" => {
            let sid = skin_id
                .map(str::trim)
                .filter(|s| !s.is_empty())
                .ok_or_else(|| "保存单包覆盖时必须指定 skin_id".to_string())?;
            validate_skin_id(sid)?;
            skin_override_path(sid)
        }
        other => return Err(format!("不支持的覆盖作用域 '{}'", other)),
    };

    let current = if let Ok(raw) = std::fs::read_to_string(&target_path) {
        serde_json::from_str::<Value>(&raw).unwrap_or_else(|_| json!({}))
    } else {
        json!({})
    };

    let merged = deep_merge(&current, &patch);
    let formatted = serde_json::to_string_pretty(&merged)
        .map_err(|e| format!("序列化覆盖配置失败: {}", e))?;
    atomic_write_text(&target_path, &formatted)?;

    let cfg = load_studio_config();
    if cfg.skin_enabled {
        if let Some(active) = cfg.active_skin.as_deref() {
            let _ = compile_skin(active);
        }
    }
    super::skin_injector::cleanup_legacy_ide_injection();
    Ok(())
}

pub fn reset_override(scope: &str, skin_id: Option<&str>) -> Result<(), String> {
    let target_path = match scope {
        "global" => global_override_path(),
        "skin" => {
            let sid = skin_id
                .map(str::trim)
                .filter(|s| !s.is_empty())
                .ok_or_else(|| "重置单包覆盖时必须指定 skin_id".to_string())?;
            validate_skin_id(sid)?;
            skin_override_path(sid)
        }
        other => return Err(format!("不支持的覆盖作用域 '{}'", other)),
    };
    if target_path.exists() {
        std::fs::remove_file(&target_path)
            .map_err(|e| format!("删除覆盖文件失败: {}", e))?;
    }
    let cfg = load_studio_config();
    if cfg.skin_enabled {
        if let Some(active) = cfg.active_skin.as_deref() {
            let _ = compile_skin(active);
        }
    }
    super::skin_injector::cleanup_legacy_ide_injection();
    Ok(())
}

pub fn activate_skin(skin_id: &str) -> Result<CompiledSkin, String> {
    let compiled = compile_skin(skin_id)?;
    let mut cfg = load_studio_config();
    cfg.active_skin = Some(skin_id.to_string());
    cfg.skin_enabled = true;
    cfg.enable_skin = true;
    save_studio_config(&cfg)?;

    // 若早期版本曾在旧版 IDE 中遗留过皮肤块，自动无损剥离还原
    super::skin_injector::cleanup_legacy_ide_injection();

    // 若官方 Antigravity 桌面应用当前空闲且尚未挂载热重载钩子，自动无损打入钩子
    let cur_agent = super::auto_reapply::agent_status(cfg.install_dir.as_deref());
    if cur_agent == "clean" && !super::auto_reapply::is_antigravity_running() {
        let _ = super::l10n::apply_l10n_patch(
            cfg.install_dir.as_deref(),
            &cfg.lang,
            &cfg.splash_character,
            cfg.enable_pet,
            true,
        );
    }

    Ok(compiled)
}

pub fn disable_skin() -> Result<(), String> {
    let mut cfg = load_studio_config();
    cfg.skin_enabled = false;
    save_studio_config(&cfg)?;
    let css_path = compiled_dir().join("skin.css");
    if css_path.exists() {
        let _ = atomic_write_text(&css_path, "");
    }
    let runtime_path = compiled_dir().join("skin-runtime.json");
    if runtime_path.exists() {
        let _ = atomic_write_text(&runtime_path, "{}");
    }
    super::skin_injector::cleanup_legacy_ide_injection();
    Ok(())
}

fn copy_dir_recursive(src: &Path, dst: &Path) -> Result<(), String> {
    std::fs::create_dir_all(dst)
        .map_err(|e| format!("创建目录失败 {}: {}", dst.display(), e))?;
    let entries = std::fs::read_dir(src)
        .map_err(|e| format!("读取目录失败 {}: {}", src.display(), e))?;
    for entry in entries.flatten() {
        let p = entry.path();
        let target = dst.join(entry.file_name());
        if p.is_dir() {
            copy_dir_recursive(&p, &target)?;
        } else if p.is_file() {
            std::fs::copy(&p, &target)
                .map_err(|e| format!("复制文件失败 {}: {}", p.display(), e))?;
        }
    }
    Ok(())
}

pub fn duplicate_skin(source_id: &str, new_id: &str, new_name: &str) -> Result<SkinInfo, String> {
    validate_skin_id(new_id)?;
    let (src_dir, _) =
        find_skin_dir(source_id).ok_or_else(|| format!("源材质包 '{}' 不存在", source_id))?;
    let dst_dir = user_skins_dir().join(new_id);
    if dst_dir.exists() {
        return Err(format!("目标材质包 ID '{}' 已存在", new_id));
    }

    copy_dir_recursive(&src_dir, &dst_dir)?;
    let mut manifest = load_raw_manifest(&dst_dir)?;
    if let Some(obj) = manifest.as_object_mut() {
        obj.insert("id".to_string(), json!(new_id));
        obj.insert(
            "name".to_string(),
            json!(if new_name.trim().is_empty() {
                new_id
            } else {
                new_name.trim()
            }),
        );
    }
    atomic_write_text(
        &dst_dir.join("skin.json"),
        &serde_json::to_string_pretty(&manifest).unwrap_or_default(),
    )?;

    list_skins()
        .into_iter()
        .find(|s| s.id == new_id)
        .ok_or_else(|| "复制材质包后未能在列表中定位".to_string())
}

pub fn delete_skin(skin_id: &str) -> Result<(), String> {
    validate_skin_id(skin_id)?;
    let user_dir = user_skins_dir().join(skin_id);
    if !user_dir.exists() {
        return Err("仅允许删除用户自定义材质包（内置材质包不可删除）".to_string());
    }
    let cfg = load_studio_config();
    if cfg.active_skin.as_deref() == Some(skin_id) {
        let _ = disable_skin();
    }
    std::fs::remove_dir_all(&user_dir)
        .map_err(|e| format!("删除材质包目录失败 {}: {}", user_dir.display(), e))?;
    let over = skin_override_path(skin_id);
    if over.exists() {
        let _ = std::fs::remove_file(over);
    }
    Ok(())
}

/// 从 `.zip` 导入材质包（包含 Zip-Slip、文件数上限与 64MB 压缩炸弹多层拦截）
pub fn import_skin_zip(zip_path: &Path, overwrite: bool) -> Result<SkinInfo, String> {
    let file = std::fs::File::open(zip_path)
        .map_err(|e| format!("打开 ZIP 文件失败 {}: {}", zip_path.display(), e))?;
    let mut archive =
        ZipArchive::new(file).map_err(|e| format!("无效的 ZIP 归档文件: {}", e))?;

    if archive.len() > MAX_ZIP_FILES {
        return Err(format!(
            "ZIP 内文件数量过多 ({} > {})，疑似异常包",
            archive.len(),
            MAX_ZIP_FILES
        ));
    }

    let mut raw_names = Vec::new();
    let mut declared_total: u64 = 0;
    for i in 0..archive.len() {
        let entry = archive
            .by_index(i)
            .map_err(|e| format!("读取 ZIP 条目失败: {}", e))?;
        let name = entry.name().replace('\\', "/");
        if name.starts_with('/') || name.contains("..") || name.contains(':') {
            return Err(format!("拦截到不安全 ZIP 路径 (Zip-Slip): {}", entry.name()));
        }
        if !entry.is_dir() {
            declared_total = declared_total.saturating_add(entry.size());
            if declared_total > MAX_ZIP_TOTAL_BYTES {
                return Err("ZIP 解压总大小超过 64MB 上限，拒绝导入".to_string());
            }
            raw_names.push(name);
        }
    }

    if raw_names.is_empty() {
        return Err("ZIP 归档中没有可用文件".to_string());
    }

    let first_segments: HashSet<String> = raw_names
        .iter()
        .filter_map(|n| n.split('/').next().map(|s| s.to_string()))
        .collect();
    let strip_prefix =
        if first_segments.len() == 1 && raw_names.iter().all(|n| n.contains('/')) {
            first_segments.into_iter().next()
        } else {
            None
        };

    let staging_dir = config_dir()
        .join("tmp")
        .join(format!("import_{}", std::process::id()));
    if staging_dir.exists() {
        let _ = std::fs::remove_dir_all(&staging_dir);
    }
    std::fs::create_dir_all(&staging_dir)
        .map_err(|e| format!("创建临时解压目录失败: {}", e))?;

    let cleanup = || {
        let _ = std::fs::remove_dir_all(&staging_dir);
    };

    let mut actual_total: u64 = 0;
    let mut buf = Vec::new();
    for i in 0..archive.len() {
        let mut entry = archive
            .by_index(i)
            .map_err(|e| format!("读取 ZIP 条目失败: {}", e))?;
        if entry.is_dir() {
            continue;
        }
        let norm = entry.name().replace('\\', "/");
        let rel = if let Some(ref prefix) = strip_prefix {
            norm.strip_prefix(&format!("{}/", prefix))
                .unwrap_or(&norm)
                .to_string()
        } else {
            norm
        };
        let target = match safe_resolve_under(&staging_dir, &rel) {
            Ok(p) => p,
            Err(e) => {
                cleanup();
                return Err(e);
            }
        };

        buf.clear();
        let mut limited = (&mut entry).take(MAX_ZIP_TOTAL_BYTES - actual_total + 1);
        if let Err(e) = limited.read_to_end(&mut buf) {
            cleanup();
            return Err(format!("解压 ZIP 条目 {} 失败: {}", rel, e));
        }
        actual_total = actual_total.saturating_add(buf.len() as u64);
        if actual_total > MAX_ZIP_TOTAL_BYTES {
            cleanup();
            return Err("ZIP 实际解压字节超出 64MB 安全限制".to_string());
        }
        if let Err(e) = atomic_write_bytes(&target, &buf) {
            cleanup();
            return Err(e);
        }
    }

    let manifest = match load_raw_manifest(&staging_dir) {
        Ok(m) => m,
        Err(e) => {
            cleanup();
            return Err(format!("ZIP 缺少合法 skin.json: {}", e));
        }
    };
    if let Err(e) = validate_manifest(&manifest, Some(&staging_dir)) {
        cleanup();
        return Err(e);
    }

    let skin_id = manifest["id"].as_str().unwrap().to_string();
    let dest_dir = user_skins_dir().join(&skin_id);
    if dest_dir.exists() {
        if !overwrite {
            cleanup();
            return Err(format!("材质包 '{}' 已存在，请勾选覆盖导入", skin_id));
        }
        std::fs::remove_dir_all(&dest_dir)
            .map_err(|e| format!("清理旧材质包目录失败: {}", e))?;
    }

    std::fs::create_dir_all(user_skins_dir())
        .map_err(|e| format!("创建用户材质包目录失败: {}", e))?;
    if let Err(e) = copy_dir_recursive(&staging_dir, &dest_dir) {
        cleanup();
        return Err(e);
    }
    cleanup();

    list_skins()
        .into_iter()
        .find(|s| s.id == skin_id)
        .ok_or_else(|| "导入后未找到材质包记录".to_string())
}

fn collect_files_for_zip(root: &Path, cur: &Path, out: &mut Vec<(String, PathBuf)>) {
    let Ok(entries) = std::fs::read_dir(cur) else {
        return;
    };
    for entry in entries.flatten() {
        let p = entry.path();
        if p.is_dir() {
            collect_files_for_zip(root, &p, out);
        } else if p.is_file() {
            if let Ok(rel) = p.strip_prefix(root) {
                out.push((rel.to_string_lossy().replace('\\', "/"), p));
            }
        }
    }
}

pub fn export_skin_zip(
    skin_id: &str,
    out_zip_path: &Path,
    include_overrides: bool,
) -> Result<String, String> {
    let (skin_dir, _, effective) = load_effective_manifest(skin_id)?;
    if let Some(parent) = out_zip_path.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|e| format!("创建导出目录失败 {}: {}", parent.display(), e))?;
    }

    let tmp_zip = out_zip_path.with_extension("zip.tmp");
    let file = std::fs::File::create(&tmp_zip)
        .map_err(|e| format!("创建导出 ZIP 文件失败: {}", e))?;
    let mut writer = ZipWriter::new(file);
    let options = SimpleFileOptions::default()
        .compression_method(CompressionMethod::Deflated)
        .unix_permissions(0o644);

    let mut files = Vec::new();
    collect_files_for_zip(&skin_dir, &skin_dir, &mut files);

    for (rel, abs) in files {
        let zip_entry_name = format!("{}/{}", skin_id, rel);
        writer
            .start_file(&zip_entry_name, options)
            .map_err(|e| format!("写入 ZIP 头失败: {}", e))?;
        if rel == "skin.json" && include_overrides {
            let text = serde_json::to_string_pretty(&effective).unwrap_or_default();
            writer
                .write_all(text.as_bytes())
                .map_err(|e| format!("写入 skin.json 失败: {}", e))?;
        } else {
            let bytes = std::fs::read(&abs)
                .map_err(|e| format!("读取资产文件 {} 失败: {}", rel, e))?;
            writer
                .write_all(&bytes)
                .map_err(|e| format!("写入资产 {} 失败: {}", rel, e))?;
        }
    }

    writer
        .finish()
        .map_err(|e| format!("完成 ZIP 归档失败: {}", e))?;

    if out_zip_path.exists() {
        let _ = std::fs::remove_file(out_zip_path);
    }
    std::fs::rename(&tmp_zip, out_zip_path)
        .map_err(|e| format!("保存导出文件失败: {}", e))?;

    Ok(out_zip_path.to_string_lossy().to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_deep_merge_and_null_removal() {
        let base = json!({
            "colors": {"accent": "#ff0000", "background": "#000000"},
            "pet": {"character": "nezuko", "scale": 1.0}
        });
        let over = json!({
            "colors": {"accent": "#e94560", "background": null},
            "pet": {"character": "prince"}
        });
        let merged = deep_merge(&base, &over);
        assert_eq!(merged["colors"]["accent"], "#e94560");
        assert!(merged["colors"].get("background").is_none());
        assert_eq!(merged["pet"]["scale"], 1.0);
        assert_eq!(merged["pet"]["character"], "prince");
    }

    #[test]
    fn test_safe_resolve_blocks_traversal() {
        let base = PathBuf::from("/tmp/skin-test");
        assert!(safe_resolve_under(&base, "../etc/passwd").is_err());
        assert!(safe_resolve_under(&base, "/abs/path.png").is_err());
        assert!(safe_resolve_under(&base, "icons/sakura.svg").is_ok());
    }

    #[test]
    fn test_css_safety_blocks_remote_import() {
        assert!(check_css_safety("@import url('https://evil.com/a.css');").is_err());
        assert!(check_css_safety("body { width: expression(alert(1)); }").is_err());
        assert!(check_css_safety(":root { --agzh-accent: #ff6699; }").is_ok());
    }

    #[test]
    fn test_manifest_supports_schema_v1_formats() {
        let m = json!({
            "schema": 1,
            "id": "nezuko-bamboo",
            "name": "祢豆子 · 竹筒与麻叶",
            "pet": {"character": "prince"}
        });
        assert!(validate_manifest(&m, None).is_ok());
    }

    #[test]
    fn test_append_pseudo_to_selectors_handles_multiple() {
        assert_eq!(
            append_pseudo_to_selectors("aside, [data-sidebar='sidebar']", "before"),
            "aside::before, [data-sidebar='sidebar']::before"
        );
    }

    #[test]
    fn test_dark_skins_compile_onyx_tokens_without_foreground_haze() {
        let dark_ids = [
            "obsidian-glass",
            "midnight-dark",
            "vermilion-lacquer",
            "nordic-aurora",
            "nezuko-bamboo",
            "clannad-illusionary-orbs",
            "clannad-starfish-library",
        ];
        for id in dark_ids {
            let compiled = compile_skin(id).unwrap_or_else(|e| panic!("编译 {} 失败: {}", id, e));
            let css = &compiled.css;
            for required in [
                "--onyx-frame:",
                "--onyx-raised:",
                "--onyx-well:",
                "--onyx-selected:",
                "--onyx-key:",
                "--shell:",
                "--shell-canvas:",
                "--glass:",
                "--glass-border:",
                "--glass-highlight:",
                "--editor-code-block-background:",
                "--syntax-default-fg:",
            ] {
                assert!(
                    css.contains(required),
                    "暗色皮肤 {} 编译产物缺少关键令牌 {}",
                    id,
                    required
                );
            }
            assert!(
                !css.contains("z-index: 9980") && !css.contains("z-index: 9985"),
                "暗色皮肤 {} 不应注入遮挡正文的顶层噪点或插画伪元素",
                id
            );
            assert!(
                !css.contains("--text-sm:"),
                "皮肤 {} 不应强行覆盖 Tailwind --text-sm 字号梯度",
                id
            );
        }
    }

    #[test]
    fn test_prism_facets_tokens_compiled_for_all_builtin_skins() {
        let all_ids = [
            "obsidian-glass",
            "midnight-dark",
            "vermilion-lacquer",
            "nordic-aurora",
            "nezuko-bamboo",
            "sakura-light",
            "clannad-sakura-hill",
            "clannad-illusionary-orbs",
            "clannad-after-sunflower",
            "clannad-starfish-library",
        ];
        for id in all_ids {
            let compiled = compile_skin(id).unwrap_or_else(|e| panic!("编译 {} 失败: {}", id, e));
            let css = &compiled.css;
            for required in [
                "--agzh-facet-top:",
                "--agzh-facet-edge:",
                "--agzh-well-bg:",
                "--agzh-kbd-bg:",
                "--agzh-chip-bg:",
                "--agzh-spring:",
                "data-agzh-rim-active",
                ".agzh-code-fold-btn",
                "#agzh-aura-bar",
            ] {
                assert!(
                    css.contains(required),
                    "皮肤 {} 编译产物缺少棱镜光学令牌或规则 {}",
                    id,
                    required
                );
            }
            assert_eq!(compiled.runtime_json["prism"]["facets"], true);
            assert_eq!(compiled.runtime_json["prism"]["rim_glow"], true);
            assert!(
                !css.contains("z-index: 9980")
                    && !css.contains("z-index: 9985")
                    && !css.contains("--text-sm:"),
                "皮肤 {} 不应注入禁止的顶层遮罩或破坏字号梯度",
                id
            );
        }
    }
}
