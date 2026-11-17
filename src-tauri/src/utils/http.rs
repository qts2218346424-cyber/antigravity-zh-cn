use crate::modules::config::load_app_config;
use once_cell::sync::Lazy;
use rquest::{Client, Proxy};
use rquest_util::Emulation;
use std::collections::HashMap;
use std::sync::RwLock;

/// 共享客户端的身份：决定超时长度与是否启用 JA3/TLS 仿真。
///
/// 每个组合只构建一次并长期复用（`Client` 自带连接池，clone 很轻且共享同一个池）。
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct ClientKey {
    timeout_secs: u64,
    emulated: bool,
}

impl ClientKey {
    const fn new(timeout_secs: u64, emulated: bool) -> Self {
        Self {
            timeout_secs,
            emulated,
        }
    }
}

struct SharedClients {
    built: HashMap<ClientKey, Client>,
    proxy_snapshot: Option<String>,
}

impl SharedClients {
    fn new() -> Self {
        Self {
            built: HashMap::new(),
            proxy_snapshot: None,
        }
    }

    fn get(&mut self, key: ClientKey) -> Client {
        let current_proxy = resolve_effective_proxy_url();
        if !self.built.is_empty() && self.proxy_snapshot != current_proxy {
            tracing::info!(
                old_proxy = ?self.proxy_snapshot,
                new_proxy = ?current_proxy,
                "Detected effective proxy change (AppConfig or System Proxy); rebuilding shared HTTP clients"
            );
            self.built.clear();
        }
        if let Some(client) = self.built.get(&key) {
            return client.clone();
        }
        self.proxy_snapshot = current_proxy.clone();
        let client = if key.emulated {
            create_base_client(key.timeout_secs, current_proxy.as_deref())
        } else {
            create_standard_client(key.timeout_secs, current_proxy.as_deref())
        };
        self.built.insert(key, client.clone());
        client
    }
}

static SHARED_CLIENTS: Lazy<RwLock<SharedClients>> =
    Lazy::new(|| RwLock::new(SharedClients::new()));

fn acquire(key: ClientKey) -> Client {
    let mut guard = SHARED_CLIENTS
        .write()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    guard.get(key)
}

/// 丢弃所有已构建的共享客户端，令其在下次访问时按当前配置重建。
///
/// **为什么必须存在**：`create_base_client` / `create_standard_client` 只在**构建时**
/// 读取一次 `load_app_config().proxy.upstream_proxy`。这些客户端此前是 `Lazy` 静态值 ——
/// 首次使用即定型、永不重建，于是用户在运行期间改动上游代理后，
/// 主请求路径已热更新（`UpstreamClient::rebuild_default_client`），
/// 但这些共享客户端仍带着**旧代理**继续跑：表现为「改完代理，聊天正常，
/// 但 token 刷新 / 配额刷新 / 项目解析（loadCodeAssist）一直失败」，
/// 必须重启应用才能恢复。
///
/// 调用点：`AxumServer::update_proxy`（上游代理热更新）。
/// 采用惰性重建 —— 若之后无人使用，不付出任何构建成本。
pub fn invalidate_shared_clients() {
    let mut guard = SHARED_CLIENTS
        .write()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let dropped = guard.built.len();
    guard.built.clear();
    guard.proxy_snapshot = None;
    if dropped > 0 {
        tracing::info!(
            dropped,
            "Discarded shared HTTP clients after upstream proxy change; rebuild on next use"
        );
    }
}

/// 测试用：列出当前已构建的客户端 key。
#[cfg(test)]
fn shared_client_keys() -> Vec<ClientKey> {
    let guard = SHARED_CLIENTS
        .read()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    guard.built.keys().copied().collect()
}

/// 统一的 HTTP 客户端（15s 超时，带 JA3 仿真）
pub fn get_client() -> Client {
    acquire(ClientKey::new(15, true))
}

/// 标准 HTTP 客户端（15s 超时，**不带** JA3 仿真）
pub fn get_standard_client() -> Client {
    acquire(ClientKey::new(15, false))
}

/// 长超时的标准客户端（60s，**不带** JA3 仿真）
pub fn get_long_standard_client() -> Client {
    acquire(ClientKey::new(60, false))
}

/// 解析 WinINET 注册表 `ProxyServer` 字符串为标准代理 URL。
///
/// 支持两种常见格式：
/// 1. 单一代理：`"127.0.0.1:7890"` 或 `"http://127.0.0.1:7890"`
/// 2. 分协议代理：`"http=127.0.0.1:7890;https=127.0.0.1:7890;socks=127.0.0.1:7891"`
pub fn parse_wininet_proxy_server(raw: &str) -> Option<String> {
    let trimmed = raw.trim();
    if trimmed.is_empty() {
        return None;
    }

    let normalize_addr = |addr: &str, default_scheme: &str| -> Option<String> {
        let a = addr.trim();
        if a.is_empty() {
            return None;
        }
        if a.contains("://") {
            Some(a.to_string())
        } else {
            Some(format!("{}://{}", default_scheme, a))
        }
    };

    if !trimmed.contains('=') && !trimmed.contains(';') {
        return normalize_addr(trimmed, "http");
    }

    let mut https_entry: Option<&str> = None;
    let mut http_entry: Option<&str> = None;
    let mut socks_entry: Option<&str> = None;
    let mut fallback_entry: Option<&str> = None;

    for part in trimmed.split(';') {
        let p = part.trim();
        if p.is_empty() {
            continue;
        }
        if let Some((k, v)) = p.split_once('=') {
            match k.trim().to_ascii_lowercase().as_str() {
                "https" => https_entry = Some(v.trim()),
                "http" => http_entry = Some(v.trim()),
                "socks" | "socks5" => socks_entry = Some(v.trim()),
                _ => {}
            }
        } else if fallback_entry.is_none() {
            fallback_entry = Some(p);
        }
    }

    // 注意：WinINET 中 `https=127.0.0.1:7890` 代表转发 HTTPS 流量的本地 HTTP CONNECT 代理，默认协议头为 http://
    if let Some(v) = https_entry.or(http_entry).or(fallback_entry) {
        return normalize_addr(v, "http");
    }
    if let Some(v) = socks_entry {
        return normalize_addr(v, "socks5");
    }
    None
}

fn is_self_loop_proxy(proxy_url: &str, self_port: Option<u16>) -> bool {
    let Some(port) = self_port else {
        return false;
    };
    if let Ok(parsed) = url::Url::parse(proxy_url) {
        let is_local = matches!(
            parsed.host_str(),
            Some("127.0.0.1") | Some("localhost") | Some("::1") | Some("0.0.0.0")
        );
        if is_local && parsed.port() == Some(port) {
            return true;
        }
    }
    false
}

#[cfg(target_os = "windows")]
fn read_windows_wininet_proxy() -> Option<String> {
    use std::ffi::OsStr;
    use std::os::windows::ffi::OsStrExt;

    type Hkey = isize;
    const HKEY_CURRENT_USER: Hkey = -2147483647i32 as isize; // 0x80000001
    const KEY_READ: u32 = 0x20019;
    const ERROR_SUCCESS: i32 = 0;

    #[link(name = "Advapi32")]
    extern "system" {
        fn RegOpenKeyExW(
            hkey: Hkey,
            lp_sub_key: *const u16,
            ul_options: u32,
            sam_desired: u32,
            phk_result: *mut Hkey,
        ) -> i32;
        fn RegQueryValueExW(
            hkey: Hkey,
            lp_value_name: *const u16,
            lp_reserved: *const u32,
            lp_type: *mut u32,
            lp_data: *mut u8,
            lpcb_data: *mut u32,
        ) -> i32;
        fn RegCloseKey(hkey: Hkey) -> i32;
    }

    let to_wide = |s: &str| -> Vec<u16> {
        OsStr::new(s).encode_wide().chain(std::iter::once(0)).collect()
    };

    unsafe {
        let subkey = to_wide("Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings");
        let mut hkey: Hkey = 0;
        if RegOpenKeyExW(HKEY_CURRENT_USER, subkey.as_ptr(), 0, KEY_READ, &mut hkey)
            != ERROR_SUCCESS
        {
            return None;
        }

        let enable_name = to_wide("ProxyEnable");
        let mut enable_val: u32 = 0;
        let mut enable_len: u32 = std::mem::size_of::<u32>() as u32;
        let mut reg_type: u32 = 0;
        let rc_enable = RegQueryValueExW(
            hkey,
            enable_name.as_ptr(),
            std::ptr::null(),
            &mut reg_type,
            &mut enable_val as *mut u32 as *mut u8,
            &mut enable_len,
        );
        if rc_enable != ERROR_SUCCESS || enable_val == 0 {
            let _ = RegCloseKey(hkey);
            return None;
        }

        let server_name = to_wide("ProxyServer");
        let mut buf = [0u16; 512];
        let mut buf_bytes: u32 = (buf.len() * std::mem::size_of::<u16>()) as u32;
        let rc_server = RegQueryValueExW(
            hkey,
            server_name.as_ptr(),
            std::ptr::null(),
            &mut reg_type,
            buf.as_mut_ptr() as *mut u8,
            &mut buf_bytes,
        );
        let _ = RegCloseKey(hkey);

        if rc_server != ERROR_SUCCESS || buf_bytes < 2 {
            return None;
        }

        let u16_len = (buf_bytes as usize) / 2;
        let slice = &buf[..u16_len];
        let end = slice.iter().position(|&c| c == 0).unwrap_or(slice.len());
        let raw_str = String::from_utf16_lossy(&slice[..end]);
        parse_wininet_proxy_server(&raw_str)
    }
}

/// 自动探测环境变量或操作系统级代理（如 Windows 注册表 WinINET 系统代理），并排除本地反代自环端口。
pub fn detect_system_proxy_url(self_port: Option<u16>) -> Option<String> {
    for env_key in [
        "HTTPS_PROXY",
        "https_proxy",
        "HTTP_PROXY",
        "http_proxy",
        "ALL_PROXY",
        "all_proxy",
    ] {
        if let Ok(val) = std::env::var(env_key) {
            if let Some(normalized) = parse_wininet_proxy_server(&val) {
                if !is_self_loop_proxy(&normalized, self_port) {
                    return Some(normalized);
                }
            }
        }
    }

    #[cfg(target_os = "windows")]
    {
        if let Some(win_proxy) = read_windows_wininet_proxy() {
            if !is_self_loop_proxy(&win_proxy, self_port) {
                return Some(win_proxy);
            }
        }
    }

    None
}

/// 解析当前应生效的出站代理 URL（优先软件内显式配置的 `upstream_proxy`，未启用时自动回退系统代理）。
pub fn resolve_effective_proxy_url() -> Option<String> {
    let mut self_port: Option<u16> = None;
    if let Ok(config) = load_app_config() {
        self_port = Some(config.proxy.port);
        let proxy_config = config.proxy.upstream_proxy;
        if proxy_config.enabled && !proxy_config.url.trim().is_empty() {
            let normalized = crate::proxy::config::normalize_proxy_url(&proxy_config.url);
            if !is_self_loop_proxy(&normalized, self_port) {
                return Some(normalized);
            }
        }
    }
    detect_system_proxy_url(self_port)
}

/// 应用生效代理 URL 到 builder 上。
fn apply_proxy_url(
    builder: rquest::ClientBuilder,
    proxy_url: Option<&str>,
    label: &str,
) -> rquest::ClientBuilder {
    if let Some(url) = proxy_url.filter(|u| !u.trim().is_empty()) {
        match Proxy::all(url) {
            Ok(proxy) => {
                tracing::info!("{} enabled outbound proxy: {}", label, url);
                return builder.proxy(proxy);
            }
            Err(e) => {
                tracing::error!("invalid_proxy_url: {}, error: {}", url, e);
            }
        }
    }
    builder
}

/// Base client creation logic with JA3 Emulation
fn create_base_client(timeout_secs: u64, proxy_url: Option<&str>) -> Client {
    let builder = Client::builder()
        .emulation(Emulation::Chrome123)
        .connect_timeout(std::time::Duration::from_secs(5))
        .pool_idle_timeout(std::time::Duration::from_secs(45))
        .timeout(std::time::Duration::from_secs(timeout_secs));
    let builder = apply_proxy_url(builder, proxy_url, "HTTP shared client");

    tracing::info!("Initialized JA3/TLS Impersonation (Chrome123)");
    builder.build().unwrap_or_else(|_| Client::new())
}

/// Base client creation logic strictly WITHOUT JA3 Emulation (Pure Native)
fn create_standard_client(timeout_secs: u64, proxy_url: Option<&str>) -> Client {
    // No .emulation(Emulation::Chrome123) here!
    let builder = Client::builder()
        .connect_timeout(std::time::Duration::from_secs(5))
        .pool_idle_timeout(std::time::Duration::from_secs(45))
        .timeout(std::time::Duration::from_secs(timeout_secs));
    let builder = apply_proxy_url(builder, proxy_url, "HTTP standard client");

    tracing::info!("Initialized Pure Native Standard Client");
    builder.build().unwrap_or_else(|_| Client::new())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn emulated_15_key() -> ClientKey {
        ClientKey::new(15, true)
    }

    #[test]
    fn shared_client_is_cached_until_invalidated() {
        let _guard = crate::proxy::config::TEST_CONFIG_LOCK
            .lock()
            .unwrap_or_else(|p| p.into_inner());
        invalidate_shared_clients();

        let _ = get_client();
        assert!(
            shared_client_keys().contains(&emulated_15_key()),
            "get_client 应产出对应 key 的客户端"
        );

        // 同一 key 只应存在一份（HashMap 语义），重复获取不得新建实例。
        let _ = get_client();
        let count = shared_client_keys()
            .iter()
            .filter(|k| **k == emulated_15_key())
            .count();
        assert_eq!(count, 1, "重复获取同一 key 不应产生第二个实例");
    }

    /// 这是本次修复的核心语义：上游代理热更新后，已构建的共享客户端必须被丢弃，
    /// 否则它们会带着**旧代理**继续跑（token 刷新 / 配额刷新 / 项目解析）。
    #[test]
    fn invalidate_drops_clients_so_they_rebuild_with_current_proxy() {
        let _guard = crate::proxy::config::TEST_CONFIG_LOCK
            .lock()
            .unwrap_or_else(|p| p.into_inner());

        let _ = get_client();
        assert!(shared_client_keys().contains(&emulated_15_key()));

        invalidate_shared_clients();
        assert!(
            !shared_client_keys().contains(&emulated_15_key()),
            "invalidate 必须丢弃已构建的客户端，否则改代理后仍走旧代理直到重启"
        );

        // 下次访问按当前配置重建
        let _ = get_client();
        assert!(
            shared_client_keys().contains(&emulated_15_key()),
            "失效后应重新构建"
        );

        invalidate_shared_clients();
    }

    #[test]
    fn wininet_proxy_parser_handles_common_formats_and_self_loop() {
        assert_eq!(
            parse_wininet_proxy_server("127.0.0.1:7890"),
            Some("http://127.0.0.1:7890".to_string())
        );
        assert_eq!(
            parse_wininet_proxy_server("http=127.0.0.1:7890;https=127.0.0.1:7891"),
            Some("http://127.0.0.1:7891".to_string())
        );
        assert_eq!(
            parse_wininet_proxy_server("socks=127.0.0.1:1080"),
            Some("socks5://127.0.0.1:1080".to_string())
        );
        assert!(is_self_loop_proxy("http://127.0.0.1:8045", Some(8045)));
        assert!(!is_self_loop_proxy("http://127.0.0.1:7890", Some(8045)));
    }
}
