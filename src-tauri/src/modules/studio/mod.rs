pub mod asar;
pub mod auto_reapply;
pub mod l10n;
pub mod pet;
pub mod skin_injector;
pub mod skin_manager;

use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

pub const APP_DIR_NAME: &str = "antigravity-zh-cn";
pub const PATCH_MARKER: &str = "/* __ANTIGRAVITY_ZH_CN_PATCHED__ */";

/// 定位用户配置根目录：
/// - 优先环境变量 `AGZH_CONFIG_DIR`
/// - Windows: `%APPDATA%\antigravity-zh-cn`
/// - macOS: `~/Library/Application Support/antigravity-zh-cn`
/// - Linux: `$XDG_CONFIG_HOME/antigravity-zh-cn` 或 `~/.config/antigravity-zh-cn`
pub fn config_dir() -> PathBuf {
    if let Ok(env_dir) = std::env::var("AGZH_CONFIG_DIR") {
        let trimmed = env_dir.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }

    #[cfg(target_os = "windows")]
    {
        if let Ok(appdata) = std::env::var("APPDATA") {
            if !appdata.trim().is_empty() {
                return PathBuf::from(appdata).join(APP_DIR_NAME);
            }
        }
        return dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join("AppData")
            .join("Roaming")
            .join(APP_DIR_NAME);
    }

    #[cfg(target_os = "macos")]
    {
        return dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join("Library")
            .join("Application Support")
            .join(APP_DIR_NAME);
    }

    #[cfg(all(not(target_os = "windows"), not(target_os = "macos")))]
    {
        if let Ok(xdg) = std::env::var("XDG_CONFIG_HOME") {
            if !xdg.trim().is_empty() {
                return PathBuf::from(xdg).join(APP_DIR_NAME);
            }
        }
        dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join(".config")
            .join(APP_DIR_NAME)
    }
}

/// 定位项目/打包资源根目录（其下包含 `resources/`）。
pub fn resource_root() -> PathBuf {
    if let Ok(env_root) = std::env::var("AGZH_REPO_ROOT") {
        let p = PathBuf::from(env_root.trim());
        if p.join("resources").is_dir() {
            return p;
        }
    }

    if let Ok(exe) = std::env::current_exe() {
        let mut cur = exe.parent();
        for _ in 0..5 {
            if let Some(dir) = cur {
                if dir.join("resources").join("antigravity-zh-CN.json").is_file() {
                    return dir.to_path_buf();
                }
                if dir.join("agzh-resources").join("antigravity-zh-CN.json").is_file() {
                    return dir.to_path_buf();
                }
                cur = dir.parent();
            } else {
                break;
            }
        }
    }

    if let Ok(cwd) = std::env::current_dir() {
        let mut cur = Some(cwd.as_path());
        for _ in 0..4 {
            if let Some(dir) = cur {
                if dir.join("resources").join("antigravity-zh-CN.json").is_file() {
                    return dir.to_path_buf();
                }
                cur = dir.parent();
            } else {
                break;
            }
        }
    }

    // 编译时回退至仓库根目录（src-tauri 的父目录）
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    if let Some(parent) = manifest_dir.parent() {
        if parent.join("resources").is_dir() {
            return parent.to_path_buf();
        }
    }

    manifest_dir
}

pub fn resources_dir() -> PathBuf {
    let root = resource_root();
    let direct = root.join("resources");
    if direct.join("antigravity-zh-CN.json").is_file() {
        return direct;
    }
    let bundled = root.join("agzh-resources");
    if bundled.join("antigravity-zh-CN.json").is_file() {
        return bundled;
    }
    direct
}

/// 跨平台原子写入文本/字节，带 Windows 共享冲突重试机制
pub fn atomic_write_bytes(path: &Path, bytes: &[u8]) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|e| format!("创建目录失败 {}: {}", parent.display(), e))?;
    }

    let pid = std::process::id();
    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let file_name = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("tmp");
    let tmp_path = path.with_file_name(format!("{}.{}.{}.tmp", file_name, pid, nonce));

    std::fs::write(&tmp_path, bytes)
        .map_err(|e| format!("写入临时文件失败 {}: {}", tmp_path.display(), e))?;

    let mut last_err = String::new();
    for attempt in 0..20 {
        match std::fs::rename(&tmp_path, path) {
            Ok(()) => return Ok(()),
            Err(e) => {
                last_err = e.to_string();
                // Windows 下覆盖已存在文件有时需要先短暂重试
                if path.exists() {
                    let _ = std::fs::copy(&tmp_path, path).map(|_| {
                        let _ = std::fs::remove_file(&tmp_path);
                    });
                    if path.exists() && attempt >= 1 {
                        // 验证 copy 是否成功
                        if let Ok(meta) = std::fs::metadata(path) {
                            if meta.len() == bytes.len() as u64 {
                                let _ = std::fs::remove_file(&tmp_path);
                                return Ok(());
                            }
                        }
                    }
                }
                std::thread::sleep(std::time::Duration::from_millis(50 * (attempt + 1) as u64));
            }
        }
    }

    let _ = std::fs::remove_file(&tmp_path);
    Err(format!("原子替换文件失败 {}: {}", path.display(), last_err))
}

pub fn atomic_write_text(path: &Path, text: &str) -> Result<(), String> {
    atomic_write_bytes(path, text.as_bytes())
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkinInfo {
    pub id: String,
    pub name: String,
    pub version: String,
    pub author: String,
    pub description: String,
    pub base: String,
    pub path: String,
    pub builtin: bool,
    pub preview_data_uri: Option<String>,
    pub colors: serde_json::Value,
    pub active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StudioStatus {
    pub install_dir: Option<String>,
    pub ide_root: Option<String>,
    pub agent_status: String,
    pub ide_status: String,
    pub active_skin: Option<String>,
    pub skin_enabled: bool,
    pub ide_enabled: bool,
    pub auto_reapply: bool,
    pub autostart_enabled: bool,
    pub updates_disabled: bool,
    pub splash_character: String,
    pub lang: String,
    pub enable_pet: bool,
    pub enable_skin: bool,
    pub pet_window_open: bool,
    pub config_dir: String,
    pub resource_dir: String,
    pub reapply_logs: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct L10nPatchResult {
    pub success: bool,
    pub message: String,
    pub install_dir: String,
    pub lang: String,
    pub character: String,
    pub patched_files: Vec<String>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillLocalizeResult {
    pub scanned: usize,
    pub updated: usize,
    pub skipped: usize,
    pub details: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReapplyCheckResult {
    pub agent: String,
    pub ide: String,
    pub actions: Vec<String>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MediaStatus {
    pub is_playing: bool,
    pub title: String,
    pub artist: String,
    pub raw_title: String,
    pub source: String,
    pub lrc: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PetAssets {
    pub nezuko_chibi: Option<String>,
    pub nezuko_basket: Option<String>,
    pub nezuko_spin_sheet: Option<String>,
    pub shockwave: Option<String>,
    pub little_prince: Option<String>,
    pub prince_fox: Option<String>,
    pub prince_rose: Option<String>,
    pub prince_stars: Option<String>,
    pub prince_sunset: Option<String>,
}
