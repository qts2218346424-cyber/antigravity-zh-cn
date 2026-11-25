use crate::modules::logger;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

const GITHUB_API_URL: &str =
    "https://api.github.com/repos/qts2218346424-cyber/antigravity-zh-cn/releases/latest";
const GITHUB_RELEASES_API_URL: &str =
    "https://api.github.com/repos/qts2218346424-cyber/antigravity-zh-cn/releases?per_page=15";
const CURRENT_VERSION: &str = env!("CARGO_PKG_VERSION");
const DEFAULT_CHECK_INTERVAL_HOURS: u64 = 24;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum UpdateChannel {
    Stable,
    Beta,
}

impl Default for UpdateChannel {
    fn default() -> Self {
        UpdateChannel::Stable
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateInfo {
    pub current_version: String,
    pub latest_version: String,
    pub has_update: bool,
    pub download_url: String, // previously release_url
    pub release_notes: String,
    pub published_at: String,
    #[serde(default)]
    pub source: Option<String>,
    #[serde(default)]
    pub proxy_url: Option<String>,
    #[serde(default)]
    pub channel: Option<UpdateChannel>,
    #[serde(default)]
    pub updater_json_url: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateSettings {
    pub auto_check: bool,
    pub last_check_time: u64,
    #[serde(default = "default_check_interval")]
    pub check_interval_hours: u64,
    #[serde(default)]
    pub update_channel: UpdateChannel,
}

fn default_check_interval() -> u64 {
    DEFAULT_CHECK_INTERVAL_HOURS
}

impl Default for UpdateSettings {
    fn default() -> Self {
        Self {
            auto_check: true,
            last_check_time: 0,
            check_interval_hours: DEFAULT_CHECK_INTERVAL_HOURS,
            update_channel: UpdateChannel::default(),
        }
    }
}

/// 更新设置的局部补丁：仅覆盖显式提供的字段，未提供的字段保留磁盘上的现有值。
///
/// 该结构同时服务于 Web (Axum) 与桌面 (Tauri) 两条链路：
/// - Web 前端 `invoke('save_update_settings', { settings: { ... } })` 经 HTTP 原样透传；
/// - 桌面端由 Tauri 按参数名 `settings` 自动解包。
///
/// 直接用完整结构体落盘会带来两个历史问题：前端硬编码的 `last_check_time: 0`
/// 会清空最近检查时间并触发立即检查；部分调用点省略的 `update_channel` 会因
/// `#[serde(default)]` 被静默重置为构建默认通道。
#[derive(Debug, Clone, Default, Deserialize)]
pub struct UpdateSettingsPatch {
    pub auto_check: Option<bool>,
    pub last_check_time: Option<u64>,
    pub check_interval_hours: Option<u64>,
    pub update_channel: Option<UpdateChannel>,
}

impl UpdateSettingsPatch {
    /// 补丁未携带任何字段时视为无效请求，避免静默返回成功。
    pub fn is_empty(&self) -> bool {
        self.auto_check.is_none()
            && self.last_check_time.is_none()
            && self.check_interval_hours.is_none()
            && self.update_channel.is_none()
    }
}

impl UpdateSettings {
    /// 将补丁字段合并进当前设置，未提供的字段保持不变。
    pub fn apply_patch(&mut self, patch: UpdateSettingsPatch) {
        if let Some(auto_check) = patch.auto_check {
            self.auto_check = auto_check;
        }
        if let Some(last_check_time) = patch.last_check_time {
            self.last_check_time = last_check_time;
        }
        if let Some(check_interval_hours) = patch.check_interval_hours {
            self.check_interval_hours = check_interval_hours;
        }
        if let Some(update_channel) = patch.update_channel {
            self.update_channel = update_channel;
        }
    }
}

#[derive(Debug, Deserialize)]
struct GitHubRelease {
    tag_name: String,
    html_url: String,
    body: Option<String>,
    published_at: Option<String>,
    #[serde(default)]
    prerelease: bool,
    #[serde(default)]
    assets: Vec<GitHubReleaseAsset>,
}

#[derive(Debug, Deserialize)]
struct GitHubReleaseAsset {
    name: String,
    browser_download_url: String,
}

pub const STABLE_LATEST_JSON_URL: &str =
    "https://github.com/qts2218346424-cyber/antigravity-zh-cn/releases/latest/download/latest.json";
pub const STABLE_UPDATER_JSON_URL: &str =
    "https://github.com/qts2218346424-cyber/antigravity-zh-cn/releases/latest/download/updater.json";
pub const PREVIEW_LATEST_JSON_URL: &str =
    "https://github.com/qts2218346424-cyber/antigravity-zh-cn/releases/download/preview/latest.json";
pub const PREVIEW_UPDATER_JSON_URL: &str =
    "https://github.com/qts2218346424-cyber/antigravity-zh-cn/releases/download/preview/updater.json";

pub fn get_upstream_proxy_url() -> Option<String> {
    if let Ok(config) = crate::modules::config::load_app_config() {
        if config.proxy.upstream_proxy.enabled && !config.proxy.upstream_proxy.url.trim().is_empty()
        {
            let url = config.proxy.upstream_proxy.url.trim();
            let normalized = if !url.contains("://") {
                format!("http://{}", url)
            } else {
                url.to_string()
            };
            return Some(normalized);
        }
    }

    // 兜底：若未显式配置上游代理，尝试从系统环境变量获取代理 (HTTPS_PROXY / HTTP_PROXY / ALL_PROXY)
    for env_var in &[
        "HTTPS_PROXY",
        "https_proxy",
        "ALL_PROXY",
        "all_proxy",
        "HTTP_PROXY",
        "http_proxy",
    ] {
        if let Ok(val) = std::env::var(env_var) {
            let trimmed = val.trim();
            if !trimmed.is_empty() {
                let normalized = if !trimmed.contains("://") {
                    format!("http://{}", trimmed)
                } else {
                    trimmed.to_string()
                };
                return Some(normalized);
            }
        }
    }

    None
}

/// Check for updates with improved strategy:
/// 1. Check updater.json (Source of Truth for Auto-Update)
/// 2. Fallback to GitHub API (Informational)
/// Check for updates with improved strategy:
/// 1. Check updater.json based on selected channel (Stable vs Beta)
/// 2. Fallback to GitHub API (Release or Pre-release)
pub async fn check_for_updates() -> Result<UpdateInfo, String> {
    // 统一仅检查正式版通道，避免历史配置残留 beta 导致无法切回正式版
    check_for_updates_with_channel(UpdateChannel::Stable).await
}

/// 按指定通道检查更新（中文 Studio 版统一收敛至正式 OTA 通道）
pub async fn check_for_updates_with_channel(_channel: UpdateChannel) -> Result<UpdateInfo, String> {
    let channel = UpdateChannel::Stable;
    let mut info = check_for_updates_internal(channel).await?;
    info.proxy_url = get_upstream_proxy_url();
    info.channel = Some(channel);
    Ok(info)
}

async fn check_for_updates_internal(channel: UpdateChannel) -> Result<UpdateInfo, String> {
    // 1. 优先通过签名 OTA 清单 (latest.json / updater.json) 检查可用更新
    match check_updater_json_channel(channel).await {
        Ok(info) => return Ok(info),
        Err(e) => {
            logger::log_warn(&format!(
                "{:?} OTA manifest check failed: {}. Trying GitHub Releases API...",
                channel, e
            ));
        }
    }

    // 2. 降级至 GitHub Releases API（仅当对应系统安装包已就绪时提示更新，避免构建半途抢跑报错）
    match check_github_api_channel(channel).await {
        Ok(info) => return Ok(info),
        Err(e) => {
            logger::log_warn(&format!("GitHub API ({:?}) check failed: {}", channel, e));
        }
    }

    Err(format!(
        "Failed to fetch updates for {:?} channel. Please check network/proxy settings.",
        channel
    ))
}

#[derive(Debug, Deserialize)]
struct UpdaterJson {
    version: String,
    notes: Option<String>,
    pub_date: Option<String>,
    #[serde(default)]
    platforms: HashMap<String, serde_json::Value>,
}

fn is_platform_ready_for_os(platforms: &HashMap<String, serde_json::Value>, os: &str) -> bool {
    if platforms.is_empty() {
        return false;
    }
    match os {
        "windows" => [
            "windows-x86_64",
            "windows-x86_64-nsis",
            "windows-x86_64-msi",
            "windows-aarch64",
        ]
        .iter()
        .any(|k| platforms.contains_key(*k)),
        "macos" => [
            "darwin-universal",
            "darwin-universal-app",
            "darwin-aarch64",
            "darwin-x86_64",
        ]
        .iter()
        .any(|k| platforms.contains_key(*k)),
        "linux" => ["linux-x86_64", "linux-x86_64-appimage"]
            .iter()
            .any(|k| platforms.contains_key(*k)),
        _ => true,
    }
}

fn has_release_installer_for_os(assets: &[GitHubReleaseAsset], os: &str) -> bool {
    assets.iter().any(|a| {
        let lower = a.name.to_ascii_lowercase();
        if lower.ends_with(".sig") || lower.ends_with(".json") {
            return false;
        }
        match os {
            "windows" => lower.ends_with(".exe") || lower.ends_with(".msi"),
            "macos" => lower.ends_with(".dmg") || lower.ends_with(".app.tar.gz"),
            "linux" => {
                lower.ends_with(".appimage") || lower.ends_with(".deb") || lower.ends_with(".rpm")
            }
            _ => true,
        }
    })
}

async fn create_client() -> Result<reqwest::Client, String> {
    let mut builder = reqwest::Client::builder()
        .user_agent("Antigravity-Manager")
        .timeout(std::time::Duration::from_secs(10));

    // Load config to check for upstream proxy
    if let Some(proxy_url) = get_upstream_proxy_url() {
        logger::log_info(&format!(
            "Update checker using upstream proxy: {}",
            proxy_url
        ));
        match reqwest::Proxy::all(&proxy_url) {
            Ok(proxy) => {
                builder = builder.proxy(proxy);
            }
            Err(e) => {
                logger::log_warn(&format!("Failed to parse proxy URL '{}': {}", proxy_url, e));
            }
        }
    }

    builder
        .build()
        .map_err(|e| format!("Failed to create HTTP client: {}", e))
}

async fn check_updater_json_channel(channel: UpdateChannel) -> Result<UpdateInfo, String> {
    let client = create_client().await?;
    let candidate_urls: &[&str] = match channel {
        UpdateChannel::Stable => &[STABLE_LATEST_JSON_URL, STABLE_UPDATER_JSON_URL],
        UpdateChannel::Beta => &[PREVIEW_LATEST_JSON_URL, PREVIEW_UPDATER_JSON_URL],
    };

    let mut chosen: Option<(reqwest::Response, String)> = None;
    let mut last_err = String::new();

    for &url in candidate_urls {
        logger::log_info(&format!(
            "Checking for updates via {:?} manifest ({})...",
            channel, url
        ));
        match client.get(url).send().await {
            Ok(res) if res.status().is_success() => {
                chosen = Some((res, url.to_string()));
                break;
            }
            Ok(res) => {
                last_err = format!("{} returned status {}", url, res.status());
            }
            Err(e) => {
                last_err = format!("{} error: {}", url, e);
            }
        }
    }

    let (response, actual_url) = match chosen {
        Some(pair) => pair,
        None => {
            if channel == UpdateChannel::Beta {
                logger::log_info("Preview manifest endpoint unavailable, checking latest prerelease assets from GitHub API...");
                if let Ok(asset_url) = fetch_prerelease_updater_json_url(&client).await {
                    let res = client
                        .get(&asset_url)
                        .send()
                        .await
                        .map_err(|e| format!("Request failed: {}", e))?;
                    if !res.status().is_success() {
                        return Err(format!("Prerelease manifest returned status {}", res.status()));
                    }
                    (res, asset_url)
                } else {
                    return Err(format!("Manifest unavailable ({})", last_err));
                }
            } else {
                return Err(format!("Manifest unavailable ({})", last_err));
            }
        }
    };

    let updater_info: UpdaterJson = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse OTA manifest: {}", e))?;

    let latest_version = updater_info.version.trim_start_matches('v').to_string();
    let current_version = CURRENT_VERSION.to_string();
    let version_is_newer = compare_versions(&latest_version, &current_version);
    let platform_ready = is_platform_ready_for_os(&updater_info.platforms, std::env::consts::OS);
    let has_update = version_is_newer && platform_ready;

    if version_is_newer && !platform_ready {
        logger::log_info(&format!(
            "New version {} detected in manifest, but {} platform artifact is still building; deferring prompt.",
            latest_version,
            std::env::consts::OS
        ));
    } else if has_update {
        logger::log_info(&format!(
            "New version found ({:?} manifest): {} (Current: {})",
            channel, latest_version, current_version
        ));
    } else {
        logger::log_info(&format!(
            "Up to date ({:?} manifest): {} (Matches {})",
            channel, current_version, latest_version
        ));
    }

    let download_url = format!(
        "https://github.com/qts2218346424-cyber/antigravity-zh-cn/releases/tag/v{}",
        latest_version
    );

    Ok(UpdateInfo {
        current_version,
        latest_version,
        has_update,
        download_url,
        release_notes: updater_info
            .notes
            .unwrap_or_else(|| "Release notes available on GitHub.".to_string()),
        published_at: updater_info
            .pub_date
            .unwrap_or_else(|| Utc::now().to_rfc3339()),
        source: Some(format!("{:?} OTA manifest", channel)),
        proxy_url: None,
        channel: Some(channel),
        updater_json_url: if platform_ready {
            Some(actual_url)
        } else {
            None
        },
    })
}

async fn fetch_prerelease_updater_json_url(client: &reqwest::Client) -> Result<String, String> {
    let response = client
        .get(GITHUB_RELEASES_API_URL)
        .send()
        .await
        .map_err(|e| format!("Failed to query releases: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "Releases API returned status {}",
            response.status()
        ));
    }

    let releases: Vec<GitHubRelease> = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse releases: {}", e))?;

    for release in releases {
        if release.prerelease {
            if let Some(asset) = release.assets.iter().find(|a| {
                a.name.eq_ignore_ascii_case("latest.json")
                    || a.name.eq_ignore_ascii_case("updater.json")
            }) {
                return Ok(asset.browser_download_url.clone());
            }
        }
    }

    Err("No latest.json/updater.json found in latest pre-releases".to_string())
}

async fn check_github_api_channel(channel: UpdateChannel) -> Result<UpdateInfo, String> {
    let client = create_client().await?;
    logger::log_info(&format!(
        "Checking for updates via GitHub API ({:?} channel)...",
        channel
    ));

    let release = match channel {
        UpdateChannel::Stable => {
            let response = client
                .get(GITHUB_API_URL)
                .send()
                .await
                .map_err(|e| format!("Request failed: {}", e))?;

            if !response.status().is_success() {
                return Err(format!("GitHub API returned status: {}", response.status()));
            }

            response
                .json::<GitHubRelease>()
                .await
                .map_err(|e| format!("Failed to parse release info: {}", e))?
        }
        UpdateChannel::Beta => {
            let response = client
                .get(GITHUB_RELEASES_API_URL)
                .send()
                .await
                .map_err(|e| format!("Request failed: {}", e))?;

            if !response.status().is_success() {
                return Err(format!("GitHub API returned status: {}", response.status()));
            }

            let releases: Vec<GitHubRelease> = response
                .json()
                .await
                .map_err(|e| format!("Failed to parse releases: {}", e))?;

            releases
                .into_iter()
                .find(|r| r.prerelease)
                .ok_or_else(|| "No pre-release found on GitHub".to_string())?
        }
    };

    let latest_version = release.tag_name.trim_start_matches('v').to_string();
    let current_version = CURRENT_VERSION.to_string();
    let version_is_newer = compare_versions(&latest_version, &current_version);

    let manifest_asset_url = release
        .assets
        .iter()
        .find(|a| a.name.eq_ignore_ascii_case("latest.json"))
        .or_else(|| {
            release
                .assets
                .iter()
                .find(|a| a.name.eq_ignore_ascii_case("updater.json"))
        })
        .map(|a| a.browser_download_url.clone());

    let installer_ready = has_release_installer_for_os(&release.assets, std::env::consts::OS);
    let has_update = version_is_newer && (manifest_asset_url.is_some() || installer_ready);

    if version_is_newer && !has_update {
        logger::log_info(&format!(
            "Release {} exists on GitHub, but artifacts for {} are not uploaded yet; deferring update prompt.",
            latest_version,
            std::env::consts::OS
        ));
    } else if has_update {
        logger::log_info(&format!(
            "New version found (API {:?}): {} (Current: {})",
            channel, latest_version, current_version
        ));
    } else {
        logger::log_info(&format!(
            "Up to date (API {:?}): {} (Matches {})",
            channel, current_version, latest_version
        ));
    }

    Ok(UpdateInfo {
        current_version,
        latest_version,
        has_update,
        download_url: release.html_url,
        release_notes: release.body.unwrap_or_default(),
        published_at: release
            .published_at
            .unwrap_or_else(|| Utc::now().to_rfc3339()),
        source: Some(format!("GitHub API ({:?})", channel)),
        proxy_url: None,
        channel: Some(channel),
        updater_json_url: manifest_asset_url,
    })
}

/// Compare two semantic versions (supports pre-release tags like "4.8.1-beta.2" vs "4.8.1-beta.1")
pub fn compare_versions(latest: &str, current: &str) -> bool {
    let parse_semver = |v: &str| -> (Vec<u32>, Option<(String, u32)>) {
        let clean = v.trim().trim_start_matches('v');
        if let Some((main_part, pre_part)) = clean.split_once('-') {
            let nums: Vec<u32> = main_part
                .split('.')
                .filter_map(|s| s.parse::<u32>().ok())
                .collect();
            // 解析预发布段，如 beta.2 -> ("beta", 2)
            let pre_info = if let Some((tag, num_str)) = pre_part.split_once('.') {
                Some((tag.to_lowercase(), num_str.parse::<u32>().unwrap_or(0)))
            } else {
                Some((pre_part.to_lowercase(), 0))
            };
            (nums, pre_info)
        } else {
            let nums: Vec<u32> = clean
                .split('.')
                .filter_map(|s| s.parse::<u32>().ok())
                .collect();
            (nums, None)
        }
    };

    let (latest_nums, latest_pre) = parse_semver(latest);
    let (current_nums, current_pre) = parse_semver(current);

    // 1. 先比较主版本号 [major, minor, patch]
    for i in 0..latest_nums.len().max(current_nums.len()) {
        let l = latest_nums.get(i).copied().unwrap_or(0);
        let c = current_nums.get(i).copied().unwrap_or(0);
        if l > c {
            return true;
        } else if l < c {
            return false;
        }
    }

    // 2. 主版本号完全相同时，检查 pre-release (标准 SemVer 规则：无 pre-release > 有 pre-release)
    match (latest_pre, current_pre) {
        (None, Some(_)) => true,  // e.g. latest 4.8.1 正式版 > current 4.8.1-beta.2
        (Some(_), None) => false, // e.g. latest 4.8.1-beta.2 < current 4.8.1 正式版
        (Some((l_tag, l_num)), Some((c_tag, c_num))) => {
            if l_tag != c_tag {
                l_tag > c_tag
            } else {
                l_num > c_num // e.g. beta.2 > beta.1
            }
        }
        (None, None) => false, // 完全相同版本
    }
}

/// Check if enough time has passed since last check
pub fn should_check_for_updates(settings: &UpdateSettings) -> bool {
    if !settings.auto_check {
        return false;
    }

    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();

    let elapsed_hours = (now - settings.last_check_time) / 3600;
    let interval = if settings.check_interval_hours > 0 {
        settings.check_interval_hours
    } else {
        DEFAULT_CHECK_INTERVAL_HOURS
    };
    elapsed_hours >= interval
}

/// Load update settings from config file
pub fn load_update_settings() -> Result<UpdateSettings, String> {
    let data_dir = crate::modules::account::get_data_dir()
        .map_err(|e| format!("Failed to get data dir: {}", e))?;
    let settings_path = data_dir.join("update_settings.json");

    if !settings_path.exists() {
        return Ok(UpdateSettings::default());
    }

    let content = std::fs::read_to_string(&settings_path)
        .map_err(|e| format!("Failed to read settings file: {}", e))?;

    let mut settings: UpdateSettings =
        serde_json::from_str(&content).map_err(|e| format!("Failed to parse settings: {}", e))?;
    settings.update_channel = UpdateChannel::Stable;
    Ok(settings)
}

/// Save update settings to config file
pub fn save_update_settings(settings: &UpdateSettings) -> Result<(), String> {
    let data_dir = crate::modules::account::get_data_dir()
        .map_err(|e| format!("Failed to get data dir: {}", e))?;
    let settings_path = data_dir.join("update_settings.json");

    let content = serde_json::to_string_pretty(settings)
        .map_err(|e| format!("Failed to serialize settings: {}", e))?;

    std::fs::write(&settings_path, content)
        .map_err(|e| format!("Failed to write settings file: {}", e))
}

/// 读取现有设置、应用补丁后落盘，返回合并后的完整设置。
///
/// 配置文件尚不存在时 `load_update_settings` 会返回按构建版本推导的默认值，
/// 因此首次保存同样能产出完整、合法的配置。空补丁一律拒绝，避免两条传输链路
/// （Web / Tauri）出现“字段名拼错但静默成功”的假象。
pub fn patch_update_settings(patch: UpdateSettingsPatch) -> Result<UpdateSettings, String> {
    if patch.is_empty() {
        return Err(
            "Empty update settings patch: expected at least one field to update".to_string(),
        );
    }

    let mut settings = load_update_settings()?;
    settings.apply_patch(patch);
    save_update_settings(&settings)?;
    Ok(settings)
}

/// Update last check time
pub fn update_last_check_time() -> Result<(), String> {
    let mut settings = load_update_settings()?;
    settings.last_check_time = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    save_update_settings(&settings)
}

/// Detect if the app was installed via Homebrew Cask (macOS only)
pub fn is_homebrew_installed() -> bool {
    #[cfg(target_os = "macos")]
    {
        let caskroom_paths = [
            "/opt/homebrew/Caskroom/antigravity-tools",
            "/usr/local/Caskroom/antigravity-tools",
        ];

        for path in &caskroom_paths {
            if std::path::Path::new(path).exists() {
                logger::log_info(&format!("Detected Homebrew Cask installation at: {}", path));
                return true;
            }
        }
    }

    false
}

/// Detect if the app is currently running as an AppImage (Linux only).
///
/// The AppImage runtime always sets the `APPIMAGE` environment variable to the
/// absolute path of the source `.AppImage` file before mounting and executing the
/// bundled application. This is the canonical way to detect an AppImage execution
/// context without inspecting the filesystem.
///
/// This is used to gate Tauri's native auto-updater on Linux: Tauri's updater plugin
/// only supports AppImage bundles on Linux. Attempting to use it on RPM/DEB-installed
/// binaries results in an `ENOEXEC` error because the downloaded artifact is an
/// AppImage that cannot be executed without FUSE support (or proper permissions).
pub fn is_appimage_running() -> bool {
    #[cfg(target_os = "linux")]
    {
        std::env::var("APPIMAGE").is_ok()
    }
    #[cfg(not(target_os = "linux"))]
    {
        false
    }
}

/// Execute `brew upgrade --cask antigravity-tools` with timeout (macOS only)
#[cfg(not(target_os = "macos"))]
pub async fn brew_upgrade_cask() -> Result<String, String> {
    Err("brew_not_supported".to_string())
}

#[cfg(target_os = "macos")]
pub async fn brew_upgrade_cask() -> Result<String, String> {
    logger::log_info("Starting Homebrew Cask upgrade for antigravity-tools...");

    // Find brew binary
    let brew_path = if std::path::Path::new("/opt/homebrew/bin/brew").exists() {
        "/opt/homebrew/bin/brew"
    } else if std::path::Path::new("/usr/local/bin/brew").exists() {
        "/usr/local/bin/brew"
    } else {
        return Err("brew_not_found".to_string());
    };

    // 3 min timeout to prevent hanging
    let result = tokio::time::timeout(
        std::time::Duration::from_secs(180),
        tokio::process::Command::new(brew_path)
            .args(["upgrade", "--cask", "antigravity-tools"])
            .output(),
    )
    .await;

    let output = match result {
        Ok(Ok(output)) => output,
        Ok(Err(e)) => {
            logger::log_error(&format!("Failed to execute brew upgrade: {}", e));
            return Err("brew_exec_failed".to_string());
        }
        Err(_) => {
            logger::log_error("Homebrew upgrade timed out after 3 minutes");
            return Err("brew_timeout".to_string());
        }
    };

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if output.status.success() {
        logger::log_info(&format!("Homebrew upgrade succeeded: {}", stdout));
        Ok(stdout)
    } else {
        logger::log_error(&format!(
            "brew upgrade failed - stdout: {} stderr: {}",
            stdout, stderr
        ));
        // Return structured error key for frontend i18n
        if stderr.contains("already installed") || stdout.contains("already installed") {
            Err("brew_already_latest".to_string())
        } else {
            Err("brew_upgrade_failed".to_string())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compare_versions() {
        assert!(compare_versions("3.3.36", "3.3.35"));
        assert!(compare_versions("3.4.0", "3.3.35"));
        assert!(compare_versions("4.0.3", "3.3.35"));
        assert!(!compare_versions("3.3.34", "3.3.35"));
        assert!(!compare_versions("3.3.35", "3.3.35"));

        // Pre-release tests
        assert!(compare_versions("4.8.1-beta.2", "4.8.1-beta.1"));
        assert!(!compare_versions("4.8.1-beta.1", "4.8.1-beta.2"));
        assert!(compare_versions("4.8.1", "4.8.1-beta.2")); // 正式版 > 预发布版
        assert!(!compare_versions("4.8.1-beta.2", "4.8.1"));
        assert!(compare_versions("4.8.2-beta.1", "4.8.1"));
    }

    #[test]
    fn test_apply_patch_preserves_unspecified_fields() {
        let mut settings = UpdateSettings {
            auto_check: true,
            last_check_time: 1_700_000_000,
            check_interval_hours: 6,
            update_channel: UpdateChannel::Beta,
        };

        settings.apply_patch(UpdateSettingsPatch {
            auto_check: Some(false),
            ..Default::default()
        });

        assert!(!settings.auto_check);
        assert_eq!(settings.last_check_time, 1_700_000_000);
        assert_eq!(settings.check_interval_hours, 6);
        assert_eq!(settings.update_channel, UpdateChannel::Beta);
    }

    #[test]
    fn test_update_settings_patch_only_contains_provided_fields() {
        let patch: UpdateSettingsPatch = serde_json::from_value(serde_json::json!({
            "update_channel": "beta"
        }))
        .expect("partial patch should deserialize");

        assert!(!patch.is_empty());
        assert_eq!(patch.auto_check, None);
        assert_eq!(patch.last_check_time, None);
        assert_eq!(patch.update_channel, Some(UpdateChannel::Beta));

        let empty: UpdateSettingsPatch = serde_json::from_value(serde_json::json!({})).unwrap();
        assert!(empty.is_empty());
    }

    #[test]
    fn test_patch_update_settings_rejects_empty_patch() {
        // 空补丁在触达磁盘前即被拒绝，不依赖数据目录环境
        assert!(patch_update_settings(UpdateSettingsPatch::default()).is_err());
    }

    #[test]
    fn test_should_check_for_updates() {
        let mut settings = UpdateSettings::default();
        assert!(should_check_for_updates(&settings));

        settings.last_check_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        assert!(!should_check_for_updates(&settings));

        settings.auto_check = false;
        assert!(!should_check_for_updates(&settings));
    }

    #[test]
    fn test_platform_and_installer_readiness_guards() {
        let mut platforms = HashMap::new();
        assert!(!is_platform_ready_for_os(&platforms, "windows"));

        platforms.insert("darwin-universal".to_string(), serde_json::json!({}));
        assert!(is_platform_ready_for_os(&platforms, "macos"));
        assert!(!is_platform_ready_for_os(&platforms, "windows"));

        platforms.insert("windows-x86_64".to_string(), serde_json::json!({}));
        assert!(is_platform_ready_for_os(&platforms, "windows"));

        let partial_assets = vec![GitHubReleaseAsset {
            name: "Antigravity.Studio_5.7.0_universal.dmg".to_string(),
            browser_download_url: "https://example.com/a.dmg".to_string(),
        }];
        assert!(has_release_installer_for_os(&partial_assets, "macos"));
        assert!(!has_release_installer_for_os(&partial_assets, "windows"));
    }
}
