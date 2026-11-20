use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Mutex, OnceLock};
use sysinfo::System;

use super::{atomic_write_text, config_dir};

const CONFIG_FILE_NAME: &str = "optimizer_config.json";

/// Windows 核心底层进程（严禁压制、隔离、冻结或结束，防止系统崩溃）
pub const SYSTEM_CRITICAL_PROCESSES: &[&str] = &[
    "system",
    "system idle process",
    "registry",
    "smss",
    "csrss",
    "wininit",
    "services",
    "lsass",
    "winlogon",
    "dwm",
    "explorer",
    "spoolsv",
    "svchost",
    "fontdrvhost",
    "sihost",
    "taskhostw",
    "ctfmon",
    "textinputhost",
    "securityhealthservice",
    "msmpeng",
    "nissrv",
    "memory compression",
    "audiodg",
    "conhost",
    "searchindexer",
    "shellexperiencehost",
    "startmenuexperiencehost",
    "runtimebroker",
    "dllhost",
    "applicationframehost",
    "wudfhost",
];

/// 代理网络与异地组网白名单（100% 免疫，保证梯子与隧道零断连、零延迟抖动）
pub const PROXY_WHITELIST: &[&str] = &[
    "flclash",
    "flclashcore",
    "flclashhelperservice",
    "clash",
    "clash-win64",
    "clash-meta",
    "clash-verge",
    "clashverge",
    "mihomo",
    "v2ray",
    "wv2ray",
    "xray",
    "sing-box",
    "singbox",
    "nekoray",
    "nekobox",
    "tailscale",
    "tailscaled",
    "shadowsocks",
    "hiddify",
    "shadowrocket",
    "mihomo-party",
];

/// Antigravity 生态核心白名单（连同其直系子进程树自动继承免疫）
pub const ANTIGRAVITY_WHITELIST: &[&str] = &[
    "antigravity",
    "antigravity-tools",
    "language_server",
    "sidecar-web-server",
    "antigravity studio",
];

/// 常见可安全压制/识别说明的后台消费大户关键字（仅用于分类标注与推荐策略，实际压榨对白名单外全部第三方后台一视同仁）
const HEAVY_SERVICE_CATALOG: &[(&str, &str, &str, u64, bool, &str)] = &[
    (
        "MSSQLSERVER",
        "SQL Server 主数据库引擎",
        "database",
        640,
        true,
        "本地不开发数据库时常驻锁定 600MB+ 内存，停止后立即释放巨额 Commit 压力，可随时一键恢复。",
    ),
    (
        "MSSQL$SQLEXPRESS",
        "SQL Server Express 实例",
        "database",
        320,
        true,
        "Express 实例常驻后台占用内存与磁盘 I/O，不跑本地 SQL 项目时建议暂时停止。",
    ),
    (
        "SQLTELEMETRY",
        "SQL Server 遥测收集",
        "database",
        40,
        true,
        "微软 SQL 遥测上报服务，停止后无任何副作用。",
    ),
    (
        "SQLWriter",
        "SQL Server VSS 卷影服务",
        "database",
        24,
        true,
        "SQL 备份卷影辅助服务，停用数据库期间可同步停止。",
    ),
    (
        "SysMain",
        "SysMain (Superfetch 预读服务)",
        "windows",
        180,
        true,
        "SSD 固态硬盘上长期预读会推高后台磁盘排队与 Standby 缓存占用，停用后游戏与桌面切换更跟手。",
    ),
    (
        "WSearch",
        "Windows Search 文件索引",
        "windows",
        120,
        false,
        "后台周期性全盘建索引消耗 I/O 与 CPU；若常用系统搜索则保留，极客游戏期间可暂止。",
    ),
    (
        "DiagTrack",
        "Windows 诊断遥测体验服务",
        "windows",
        45,
        true,
        "系统后台诊断日志上传服务，安全可停。",
    ),
    (
        "ArmouryCrateService",
        "华硕奥创主服务",
        "asus",
        140,
        false,
        "负责奥创中心硬件配置与灯效；停止后可显著减少后台唤醒，但可能影响奥创面板实时调档。",
    ),
    (
        "ArmouryCrateControlInterface",
        "华硕奥创控制接口",
        "asus",
        65,
        false,
        "奥创控制通道接口服务。",
    ),
    (
        "ROG Live Service",
        "ROG Live 灯效与同步服务",
        "asus",
        85,
        true,
        "ROG 外设灯光与同步守护，关闭后可降低后台 CPU 轮询，不影响显卡与风扇底噪控制。",
    ),
    (
        "AsusAppService",
        "ASUS 应用辅助服务",
        "asus",
        55,
        true,
        "华硕应用管家伴生服务，平时可安全停止。",
    ),
    (
        "ASUSSystemAnalysis",
        "ASUS 系统诊断分析",
        "asus",
        45,
        true,
        "华硕自检遥测分析，安全可停。",
    ),
    (
        "ASUSSystemDiagnosis",
        "ASUS 系统故障诊断",
        "asus",
        40,
        true,
        "华硕硬件诊断报告收集，安全可停。",
    ),
];

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default, rename_all = "camelCase")]
pub struct OptimizerConfig {
    pub ruthless_enabled: bool,
    pub custom_whitelist: Vec<String>,
    pub aggressive_core_isolation: bool,
    pub timer_05ms_enabled: bool,
    pub auto_zero_menu_delay: bool,
}

impl Default for OptimizerConfig {
    fn default() -> Self {
        Self {
            ruthless_enabled: false,
            custom_whitelist: Vec::new(),
            aggressive_core_isolation: true,
            timer_05ms_enabled: true,
            auto_zero_menu_delay: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct OptimizerOverview {
    pub cpu_percent: f32,
    pub mem_total_mb: u64,
    pub mem_used_mb: u64,
    pub mem_available_mb: u64,
    pub mem_percent: f32,
    pub commit_total_mb: u64,
    pub commit_used_mb: u64,
    pub commit_percent: f32,
    pub timer_resolution_ms: f32,
    pub menu_show_delay_ms: u32,
    pub is_elevated: bool,
    pub is_windows: bool,
    pub logical_cpus: usize,
    pub exile_cores_label: String,
    pub ruthless_enabled: bool,
    pub foreground_process: Option<String>,
    pub foreground_pid: Option<u32>,
    pub throttled_count: usize,
    pub frozen_count: usize,
    pub protected_count: usize,
    pub access_denied_count: usize,
    pub running_heavy_services: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProcessGroupItem {
    pub name: String,
    pub count: usize,
    pub pids: Vec<u32>,
    pub working_set_mb: f64,
    pub private_mb: f64,
    pub cpu_percent: f32,
    pub protection: String,
    pub protection_label: String,
    pub state: String,
    pub is_frozen: bool,
    pub can_control: bool,
    pub exe_path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct OptimizerActionResult {
    pub success: bool,
    pub message: String,
    pub affected: usize,
    pub denied: usize,
    pub needs_elevation: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MemoryBoostResult {
    pub success: bool,
    pub standby_purged: bool,
    pub trimmed_processes: usize,
    pub freed_mb: f64,
    pub before_avail_mb: u64,
    pub after_avail_mb: u64,
    pub needs_elevation: bool,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ServiceItem {
    pub name: String,
    pub display_name: String,
    pub category: String,
    pub status: String,
    pub start_type: String,
    pub est_memory_mb: u64,
    pub risk_note: String,
    pub recommended_stop: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct JunkCategoryItem {
    pub id: String,
    pub name: String,
    pub group: String,
    pub path: String,
    pub size_mb: f64,
    pub file_count: usize,
    pub default_checked: bool,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CleanResult {
    pub success: bool,
    pub deleted_files: usize,
    pub skipped_files: usize,
    pub freed_mb: f64,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LargeFileEntry {
    pub path: String,
    pub name: String,
    pub size_mb: f64,
    pub ext: String,
    pub modified_ts: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LargeDirEntry {
    pub path: String,
    pub name: String,
    pub size_mb: f64,
    pub percent: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LargeFileScanResult {
    pub root_path: String,
    pub total_scanned_mb: f64,
    pub directories: Vec<LargeDirEntry>,
    pub files: Vec<LargeFileEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WhitelistSnapshot {
    pub system: Vec<String>,
    pub proxy: Vec<String>,
    pub antigravity: Vec<String>,
    pub custom: Vec<String>,
    pub dynamic_tree_count: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProtectionKind {
    System,
    Proxy,
    Antigravity,
    AntigravityTree,
    Custom,
    None,
}

impl ProtectionKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            ProtectionKind::System => "system",
            ProtectionKind::Proxy => "proxy",
            ProtectionKind::Antigravity => "antigravity",
            ProtectionKind::AntigravityTree => "antigravity_tree",
            ProtectionKind::Custom => "custom",
            ProtectionKind::None => "none",
        }
    }

    pub fn label(&self) -> &'static str {
        match self {
            ProtectionKind::System => "系统内核免疫",
            ProtectionKind::Proxy => "代理隧道免杀",
            ProtectionKind::Antigravity => "Antigravity 核心",
            ProtectionKind::AntigravityTree => "Antigravity 子进程树",
            ProtectionKind::Custom => "自定义白名单",
            ProtectionKind::None => "可压榨后台",
        }
    }

    pub fn is_protected(&self) -> bool {
        !matches!(self, ProtectionKind::None)
    }
}

// -------------------------------------------------------------
// 全局运行时状态与安全追踪表（支持退出全量恢复，杜绝孤儿卡死）
// -------------------------------------------------------------
static RUTHLESS_ACTIVE: AtomicBool = AtomicBool::new(false);
static DAEMON_STARTED: AtomicBool = AtomicBool::new(false);
static LAST_FG_PID: AtomicUsize = AtomicUsize::new(0);
static LAST_FG_NAME: OnceLock<Mutex<Option<String>>> = OnceLock::new();
static FROZEN_PIDS: OnceLock<Mutex<HashSet<u32>>> = OnceLock::new();
static ISOLATED_PIDS: OnceLock<Mutex<HashSet<u32>>> = OnceLock::new();
static DENIED_PIDS: OnceLock<Mutex<HashSet<u32>>> = OnceLock::new();
static CONFIG_LOCK: OnceLock<Mutex<()>> = OnceLock::new();
static SYS_PROBE: OnceLock<Mutex<System>> = OnceLock::new();
static HEAVY_SVC_CACHE: OnceLock<Mutex<Option<(std::time::Instant, usize)>>> = OnceLock::new();

fn frozen_pids() -> &'static Mutex<HashSet<u32>> {
    FROZEN_PIDS.get_or_init(|| Mutex::new(HashSet::new()))
}

fn isolated_pids() -> &'static Mutex<HashSet<u32>> {
    ISOLATED_PIDS.get_or_init(|| Mutex::new(HashSet::new()))
}

fn denied_pids() -> &'static Mutex<HashSet<u32>> {
    DENIED_PIDS.get_or_init(|| Mutex::new(HashSet::new()))
}

fn last_fg_name() -> &'static Mutex<Option<String>> {
    LAST_FG_NAME.get_or_init(|| Mutex::new(None))
}

fn config_lock() -> &'static Mutex<()> {
    CONFIG_LOCK.get_or_init(|| Mutex::new(()))
}

fn sys_probe() -> &'static Mutex<System> {
    SYS_PROBE.get_or_init(|| {
        let mut s = System::new_all();
        s.refresh_cpu_usage();
        Mutex::new(s)
    })
}

fn heavy_svc_cache() -> &'static Mutex<Option<(std::time::Instant, usize)>> {
    HEAVY_SVC_CACHE.get_or_init(|| Mutex::new(None))
}

fn invalidate_heavy_svc_cache() {
    if let Ok(mut guard) = heavy_svc_cache().lock() {
        *guard = None;
    }
}

fn get_running_heavy_service_count_cached() -> usize {
    if !cfg!(target_os = "windows") {
        return 0;
    }
    let now = std::time::Instant::now();
    if let Ok(guard) = heavy_svc_cache().lock() {
        if let Some((ts, cnt)) = *guard {
            if now.duration_since(ts) < std::time::Duration::from_secs(15) {
                return cnt;
            }
        }
    }
    let count = HEAVY_SERVICE_CATALOG
        .iter()
        .filter(|(svc, _, _, _, _, _)| win_native::is_service_running(svc))
        .count();
    if let Ok(mut guard) = heavy_svc_cache().lock() {
        *guard = Some((std::time::Instant::now(), count));
    }
    count
}

fn config_path() -> PathBuf {
    config_dir().join(CONFIG_FILE_NAME)
}

pub fn load_optimizer_config() -> OptimizerConfig {
    let _g = config_lock().lock().ok();
    let p = config_path();
    if let Ok(raw) = std::fs::read_to_string(&p) {
        if let Ok(cfg) = serde_json::from_str::<OptimizerConfig>(&raw) {
            return cfg;
        }
    }
    OptimizerConfig::default()
}

pub fn save_optimizer_config(cfg: &OptimizerConfig) -> Result<(), String> {
    let _g = config_lock().lock().ok();
    let raw = serde_json::to_string_pretty(cfg)
        .map_err(|e| format!("序列化优化器配置失败: {}", e))?;
    atomic_write_text(&config_path(), &raw)
}

/// 标准化进程名：小写并去除末尾 `.exe`
pub fn normalize_proc_name(name: &str) -> String {
    let trimmed = name.trim().to_ascii_lowercase();
    trimmed.strip_suffix(".exe").unwrap_or(&trimmed).to_string()
}

/// 计算后台驱逐与前台全核亲和度掩码
/// 对 8 核 16 线程（logical_cpus = 16）返回：
/// - full_mask = 0xFFFF (CPU 0~15)
/// - exile_mask = 0xC000 (仅 CPU 14, 15)
pub fn compute_affinity_masks(logical_cpus: usize) -> (usize, usize, String) {
    let max_bits = usize::BITS as usize;
    let n = logical_cpus.clamp(1, max_bits);
    let full_mask = if n >= max_bits {
        usize::MAX
    } else {
        (1usize << n) - 1
    };

    if n >= 8 {
        let exile_mask = (1usize << (n - 1)) | (1usize << (n - 2));
        let label = format!("CPU {}-{} (腾空 CPU 0-{})", n - 2, n - 1, n - 3);
        (full_mask, exile_mask, label)
    } else if n >= 4 {
        let exile_mask = 1usize << (n - 1);
        let label = format!("CPU {} (腾空 CPU 0-{})", n - 1, n - 2);
        (full_mask, exile_mask, label)
    } else {
        let exile_mask = 1usize << (n - 1);
        (full_mask, exile_mask, format!("CPU {}", n - 1))
    }
}

fn match_list(norm_name: &str, list: &[&str]) -> bool {
    list.iter().any(|entry| {
        let e = normalize_proc_name(entry);
        norm_name == e
    })
}

fn match_custom_list(norm_name: &str, custom: &[String]) -> bool {
    custom.iter().any(|entry| {
        let e = normalize_proc_name(entry);
        !e.is_empty() && norm_name == e
    })
}

/// 基于进程映射表进行最高 6 层祖先追踪的白名单判定
pub fn classify_process_protection(
    pid: u32,
    proc_map: &HashMap<u32, (Option<u32>, String)>,
    custom_whitelist: &[String],
    self_pid: u32,
) -> ProtectionKind {
    if pid <= 4 {
        return ProtectionKind::System;
    }
    if pid == self_pid {
        return ProtectionKind::Antigravity;
    }

    let Some((_, raw_name)) = proc_map.get(&pid) else {
        return ProtectionKind::None;
    };
    let norm = normalize_proc_name(raw_name);

    if match_list(&norm, PROXY_WHITELIST) {
        return ProtectionKind::Proxy;
    }
    if match_list(&norm, ANTIGRAVITY_WHITELIST) {
        return ProtectionKind::Antigravity;
    }
    if match_list(&norm, SYSTEM_CRITICAL_PROCESSES) {
        return ProtectionKind::System;
    }
    if match_custom_list(&norm, custom_whitelist) {
        return ProtectionKind::Custom;
    }

    // 向上追踪最多 6 层父进程：仅由 Antigravity / 代理 / 本身拉起的子进程（如专属 msedgewebview2 / node）才自动继承免杀！
    // SearchHost.exe 等系统壳拉起的 msedgewebview2 绝不会被错误豁免！
    let mut cur_parent = proc_map.get(&pid).and_then(|(ppid, _)| *ppid);
    for _ in 0..6 {
        let Some(ppid) = cur_parent else {
            break;
        };
        if ppid == 0 || ppid == pid {
            break;
        }
        if ppid == self_pid {
            return ProtectionKind::AntigravityTree;
        }
        if let Some((next_ppid, p_name)) = proc_map.get(&ppid) {
            let p_norm = normalize_proc_name(p_name);
            if match_list(&p_norm, PROXY_WHITELIST) {
                return ProtectionKind::Proxy;
            }
            if match_list(&p_norm, ANTIGRAVITY_WHITELIST) {
                return ProtectionKind::AntigravityTree;
            }
            if match_custom_list(&p_norm, custom_whitelist) {
                return ProtectionKind::Custom;
            }
            cur_parent = *next_ppid;
        } else {
            break;
        }
    }

    ProtectionKind::None
}

/// 危险系统目录与核心软件目录删除护栏（禁止任何删除/清理/回收操作）
pub fn is_dangerous_delete_path(path: &Path) -> bool {
    let raw = path.to_string_lossy().replace('/', "\\");
    let trimmed = raw.trim().trim_end_matches('\\').to_ascii_lowercase();
    if trimmed.is_empty() || trimmed.len() <= 3 {
        // 拒绝盘符根目录如 C: / C:\ / /
        return true;
    }

    let dangerous_prefixes = [
        "c:\\windows",
        "c:\\program files",
        "c:\\program files (x86)",
        "c:\\programdata",
        "c:\\users\\all users",
        "c:\\$recycle.bin",
        "c:\\system volume information",
    ];
    for prefix in dangerous_prefixes {
        if trimmed == prefix || trimmed.starts_with(&format!("{}\\", prefix)) {
            // 仅允许 C:\Windows\Temp 和 CrashDumps 类明确缓存子目录，否则拦截
            if trimmed != "c:\\windows\\temp" {
                return true;
            }
        }
    }

    // 保护 Antigravity 与 FlClash 自身程序/数据目录
    if trimmed.contains("\\antigravity\\")
        || trimmed.ends_with("\\antigravity")
        || trimmed.contains("\\antigravity-cn")
        || trimmed.contains("\\antigravity studio")
        || trimmed.contains("\\antigravity-zh-cn")
        || trimmed.contains("\\flclash")
        || trimmed.contains("\\.gemini\\google_accounts")
    {
        return true;
    }

    false
}

// -------------------------------------------------------------
// Windows 原生 FFI 底层引擎
// -------------------------------------------------------------
#[cfg(target_os = "windows")]
mod win_native {
    use std::ffi::{c_void, OsStr};
    use std::os::windows::ffi::OsStrExt;
    use std::os::windows::process::CommandExt;
    use std::path::Path;
    use std::process::Command;
    use std::sync::OnceLock;

    const CREATE_NO_WINDOW: u32 = 0x0800_0000;
    const PROCESS_QUERY_INFORMATION: u32 = 0x0400;
    const PROCESS_QUERY_LIMITED_INFORMATION: u32 = 0x1000;
    const PROCESS_SET_INFORMATION: u32 = 0x0200;
    const PROCESS_SET_QUOTA: u32 = 0x0100;
    const PROCESS_SUSPEND_RESUME: u32 = 0x0800;
    const PROCESS_TERMINATE: u32 = 0x0001;

    const HIGH_PRIORITY_CLASS: u32 = 0x0000_0080;
    const NORMAL_PRIORITY_CLASS: u32 = 0x0000_0020;
    const IDLE_PRIORITY_CLASS: u32 = 0x0000_0040;

    const PROCESS_MEMORY_PRIORITY: u32 = 0;
    const PROCESS_POWER_THROTTLING: u32 = 4;
    const PROCESS_IO_PRIORITY: u32 = 33;

    const MEMORY_PRIORITY_VERY_LOW: u32 = 1;
    const MEMORY_PRIORITY_NORMAL: u32 = 5;
    const IO_PRIORITY_VERY_LOW: u32 = 0;
    const IO_PRIORITY_NORMAL: u32 = 2;

    const TOKEN_QUERY: u32 = 0x0008;
    const TOKEN_ADJUST_PRIVILEGES: u32 = 0x0020;
    const TOKEN_ELEVATION_INFO_CLASS: u32 = 20;
    const SE_PRIVILEGE_ENABLED: u32 = 0x0000_0002;

    const HKEY_CURRENT_USER: isize = (0x8000_0001u32 as i32) as isize;
    const KEY_READ: u32 = 0x20019;
    const KEY_SET_VALUE: u32 = 0x0002;
    const REG_SZ: u32 = 1;

    #[repr(C)]
    struct MemoryStatusEx {
        dw_length: u32,
        dw_memory_load: u32,
        ull_total_phys: u64,
        ull_avail_phys: u64,
        ull_total_page_file: u64,
        ull_avail_page_file: u64,
        ull_total_virtual: u64,
        ull_avail_virtual: u64,
        ull_avail_extended_virtual: u64,
    }

    #[repr(C)]
    struct MemoryPriorityInfo {
        memory_priority: u32,
    }

    #[repr(C)]
    struct ProcessPowerThrottlingState {
        version: u32,
        control_mask: u32,
        state_mask: u32,
    }

    #[repr(C)]
    struct TokenElevation {
        token_is_elevated: u32,
    }

    #[repr(C)]
    #[derive(Clone, Copy)]
    struct Luid {
        low_part: u32,
        high_part: i32,
    }

    #[repr(C)]
    struct LuidAndAttributes {
        luid: Luid,
        attributes: u32,
    }

    #[repr(C)]
    struct TokenPrivileges {
        privilege_count: u32,
        privileges: [LuidAndAttributes; 1],
    }

    #[cfg_attr(target_pointer_width = "32", repr(C, packed(1)))]
    #[cfg_attr(target_pointer_width = "64", repr(C))]
    struct ShFileOpStructW {
        hwnd: isize,
        w_func: u32,
        p_from: *const u16,
        p_to: *const u16,
        f_flags: u16,
        f_any_operations_aborted: i32,
        h_name_mappings: isize,
        lpsz_progress_title: *const u16,
    }

    #[link(name = "kernel32")]
    extern "system" {
        fn GetCurrentProcess() -> isize;
        fn OpenProcess(dw_desired_access: u32, b_inherit_handle: i32, dw_process_id: u32) -> isize;
        fn CloseHandle(h_object: isize) -> i32;
        fn SetPriorityClass(h_process: isize, dw_priority_class: u32) -> i32;
        fn SetProcessAffinityMask(h_process: isize, dw_process_affinity_mask: usize) -> i32;
        fn SetProcessInformation(
            h_process: isize,
            process_information_class: u32,
            process_information: *const c_void,
            process_information_size: u32,
        ) -> i32;
        fn TerminateProcess(h_process: isize, u_exit_code: u32) -> i32;
        fn GlobalMemoryStatusEx(lp_buffer: *mut MemoryStatusEx) -> i32;
        fn GetModuleHandleW(lp_module_name: *const u16) -> isize;
        fn GetProcAddress(h_module: isize, lp_proc_name: *const u8) -> *const c_void;
        fn WaitForSingleObject(h_handle: isize, dw_milliseconds: u32) -> u32;
    }

    #[link(name = "user32")]
    extern "system" {
        fn GetForegroundWindow() -> isize;
        fn GetWindowThreadProcessId(hwnd: isize, lpdw_process_id: *mut u32) -> u32;
        fn SystemParametersInfoW(
            ui_action: u32,
            ui_param: u32,
            pv_param: *mut c_void,
            f_win_ini: u32,
        ) -> i32;
    }

    type FnNtSetTimerResolution = unsafe extern "system" fn(u32, u8, *mut u32) -> i32;
    type FnNtQueryTimerResolution = unsafe extern "system" fn(*mut u32, *mut u32, *mut u32) -> i32;
    type FnNtSetInformationProcess =
        unsafe extern "system" fn(isize, u32, *const c_void, u32) -> i32;
    type FnNtSetSystemInformation = unsafe extern "system" fn(u32, *const c_void, u32) -> i32;
    type FnNtSuspendProcess = unsafe extern "system" fn(isize) -> i32;
    type FnNtResumeProcess = unsafe extern "system" fn(isize) -> i32;

    struct NtdllApi {
        set_timer_res: Option<FnNtSetTimerResolution>,
        query_timer_res: Option<FnNtQueryTimerResolution>,
        set_info_proc: Option<FnNtSetInformationProcess>,
        set_sys_info: Option<FnNtSetSystemInformation>,
        suspend_proc: Option<FnNtSuspendProcess>,
        resume_proc: Option<FnNtResumeProcess>,
    }

    static NTDLL_API: OnceLock<NtdllApi> = OnceLock::new();

    fn ntdll() -> &'static NtdllApi {
        NTDLL_API.get_or_init(|| unsafe {
            let w_mod = to_wide_null("ntdll.dll");
            let h_mod = GetModuleHandleW(w_mod.as_ptr());
            if h_mod == 0 {
                return NtdllApi {
                    set_timer_res: None,
                    query_timer_res: None,
                    set_info_proc: None,
                    set_sys_info: None,
                    suspend_proc: None,
                    resume_proc: None,
                };
            }
            macro_rules! load_sym {
                ($name:literal, $ty:ty) => {{
                    let ptr = GetProcAddress(h_mod, $name.as_ptr());
                    if ptr.is_null() {
                        None
                    } else {
                        Some(std::mem::transmute::<*const c_void, $ty>(ptr))
                    }
                }};
            }
            NtdllApi {
                set_timer_res: load_sym!(b"NtSetTimerResolution\0", FnNtSetTimerResolution),
                query_timer_res: load_sym!(b"NtQueryTimerResolution\0", FnNtQueryTimerResolution),
                set_info_proc: load_sym!(b"NtSetInformationProcess\0", FnNtSetInformationProcess),
                set_sys_info: load_sym!(b"NtSetSystemInformation\0", FnNtSetSystemInformation),
                suspend_proc: load_sym!(b"NtSuspendProcess\0", FnNtSuspendProcess),
                resume_proc: load_sym!(b"NtResumeProcess\0", FnNtResumeProcess),
            }
        })
    }

    #[link(name = "psapi")]
    extern "system" {
        fn EmptyWorkingSet(h_process: isize) -> i32;
    }

    #[link(name = "advapi32")]
    extern "system" {
        fn OpenProcessToken(
            process_handle: isize,
            desired_access: u32,
            token_handle: *mut isize,
        ) -> i32;
        fn GetTokenInformation(
            token_handle: isize,
            token_information_class: u32,
            token_information: *mut c_void,
            token_information_length: u32,
            return_length: *mut u32,
        ) -> i32;
        fn LookupPrivilegeValueW(
            lp_system_name: *const u16,
            lp_name: *const u16,
            lp_luid: *mut Luid,
        ) -> i32;
        fn AdjustTokenPrivileges(
            token_handle: isize,
            disable_all_privileges: i32,
            new_state: *const TokenPrivileges,
            buffer_length: u32,
            previous_state: *mut c_void,
            return_length: *mut u32,
        ) -> i32;
        fn RegOpenKeyExW(
            h_key: isize,
            lp_sub_key: *const u16,
            ul_options: u32,
            sam_desired: u32,
            phk_result: *mut isize,
        ) -> i32;
        fn RegQueryValueExW(
            h_key: isize,
            lp_value_name: *const u16,
            lp_reserved: *mut u32,
            lp_type: *mut u32,
            lp_data: *mut u8,
            lpcb_data: *mut u32,
        ) -> i32;
        fn RegSetValueExW(
            h_key: isize,
            lp_value_name: *const u16,
            reserved: u32,
            dw_type: u32,
            lp_data: *const u8,
            cb_data: u32,
        ) -> i32;
        fn RegCloseKey(h_key: isize) -> i32;
    }

    #[link(name = "shell32")]
    extern "system" {
        fn ShellExecuteW(
            hwnd: isize,
            lp_operation: *const u16,
            lp_file: *const u16,
            lp_parameters: *const u16,
            lp_directory: *const u16,
            n_show_cmd: i32,
        ) -> isize;
        fn SHFileOperationW(lp_file_op: *mut ShFileOpStructW) -> i32;
    }

    fn to_wide_null(s: &str) -> Vec<u16> {
        OsStr::new(s).encode_wide().chain(std::iter::once(0)).collect()
    }

    fn to_wide_double_null(s: &str) -> Vec<u16> {
        OsStr::new(s)
            .encode_wide()
            .chain([0u16, 0u16])
            .collect()
    }

    pub fn is_elevated() -> bool {
        unsafe {
            let mut token: isize = 0;
            if OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &mut token) == 0 || token == 0 {
                return false;
            }
            let mut elev = TokenElevation {
                token_is_elevated: 0,
            };
            let mut ret_len: u32 = 0;
            let ok = GetTokenInformation(
                token,
                TOKEN_ELEVATION_INFO_CLASS,
                &mut elev as *mut _ as *mut c_void,
                std::mem::size_of::<TokenElevation>() as u32,
                &mut ret_len,
            );
            CloseHandle(token);
            ok != 0 && elev.token_is_elevated != 0
        }
    }

    pub fn enable_privilege(priv_name: &str) -> bool {
        unsafe {
            let mut token: isize = 0;
            if OpenProcessToken(
                GetCurrentProcess(),
                TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
                &mut token,
            ) == 0
                || token == 0
            {
                return false;
            }
            let mut luid = Luid {
                low_part: 0,
                high_part: 0,
            };
            let wname = to_wide_null(priv_name);
            let lookup_ok = LookupPrivilegeValueW(std::ptr::null(), wname.as_ptr(), &mut luid) != 0;
            if !lookup_ok {
                CloseHandle(token);
                return false;
            }
            let tp = TokenPrivileges {
                privilege_count: 1,
                privileges: [LuidAndAttributes {
                    luid,
                    attributes: SE_PRIVILEGE_ENABLED,
                }],
            };
            let adj_ok = AdjustTokenPrivileges(
                token,
                0,
                &tp,
                std::mem::size_of::<TokenPrivileges>() as u32,
                std::ptr::null_mut(),
                std::ptr::null_mut(),
            ) != 0;
            CloseHandle(token);
            adj_ok
        }
    }

    pub fn init_privileges() {
        let _ = enable_privilege("SeDebugPrivilege");
        let _ = enable_privilege("SeProfileSingleProcessPrivilege");
    }

    pub fn get_memory_commit_mb() -> (u64, u64, u64, u64) {
        unsafe {
            let mut ms = MemoryStatusEx {
                dw_length: std::mem::size_of::<MemoryStatusEx>() as u32,
                dw_memory_load: 0,
                ull_total_phys: 0,
                ull_avail_phys: 0,
                ull_total_page_file: 0,
                ull_avail_page_file: 0,
                ull_total_virtual: 0,
                ull_avail_virtual: 0,
                ull_avail_extended_virtual: 0,
            };
            if GlobalMemoryStatusEx(&mut ms) != 0 {
                let phys_tot = ms.ull_total_phys / (1024 * 1024);
                let phys_avail = ms.ull_avail_phys / (1024 * 1024);
                let commit_tot = ms.ull_total_page_file / (1024 * 1024);
                let commit_avail = ms.ull_avail_page_file / (1024 * 1024);
                (phys_tot, phys_avail, commit_tot, commit_avail)
            } else {
                (0, 0, 0, 0)
            }
        }
    }

    pub fn get_foreground_pid() -> Option<u32> {
        unsafe {
            let hwnd = GetForegroundWindow();
            if hwnd == 0 {
                return None;
            }
            let mut pid: u32 = 0;
            GetWindowThreadProcessId(hwnd, &mut pid);
            if pid > 4 {
                Some(pid)
            } else {
                None
            }
        }
    }

    pub fn set_timer_resolution(enable_05ms: bool) -> f32 {
        unsafe {
            let mut cur: u32 = 0;
            if let Some(f) = ntdll().set_timer_res {
                if enable_05ms {
                    let _ = f(5000, 1, &mut cur);
                } else {
                    let _ = f(156_250, 0, &mut cur);
                }
            }
            if cur > 0 {
                (cur as f32) / 10_000.0
            } else {
                get_timer_resolution_ms()
            }
        }
    }

    pub fn get_timer_resolution_ms() -> f32 {
        unsafe {
            let (mut min_r, mut max_r, mut cur) = (0u32, 0u32, 0u32);
            if let Some(f) = ntdll().query_timer_res {
                if f(&mut min_r, &mut max_r, &mut cur) == 0 && cur > 0 {
                    return (cur as f32) / 10_000.0;
                }
            }
            15.625
        }
    }

    pub fn get_menu_show_delay_ms() -> u32 {
        unsafe {
            let sub = to_wide_null("Control Panel\\Desktop");
            let val_name = to_wide_null("MenuShowDelay");
            let mut hkey: isize = 0;
            if RegOpenKeyExW(HKEY_CURRENT_USER, sub.as_ptr(), 0, KEY_READ, &mut hkey) != 0 {
                return 400;
            }
            let mut buf = [0u8; 64];
            let mut buf_len: u32 = buf.len() as u32;
            let mut reg_type: u32 = 0;
            let rc = RegQueryValueExW(
                hkey,
                val_name.as_ptr(),
                std::ptr::null_mut(),
                &mut reg_type,
                buf.as_mut_ptr(),
                &mut buf_len,
            );
            RegCloseKey(hkey);
            if rc == 0 && buf_len >= 2 {
                let u16_slice: &[u16] =
                    std::slice::from_raw_parts(buf.as_ptr() as *const u16, (buf_len as usize) / 2);
                let s = String::from_utf16_lossy(u16_slice)
                    .trim_end_matches('\0')
                    .trim()
                    .to_string();
                return s.parse::<u32>().unwrap_or(400);
            }
            400
        }
    }

    pub fn set_menu_show_delay_ms(delay_ms: u32) -> Result<(), String> {
        unsafe {
            let sub = to_wide_null("Control Panel\\Desktop");
            let val_name = to_wide_null("MenuShowDelay");
            let val_str = to_wide_null(&delay_ms.to_string());
            let mut hkey: isize = 0;
            if RegOpenKeyExW(HKEY_CURRENT_USER, sub.as_ptr(), 0, KEY_SET_VALUE, &mut hkey) != 0 {
                return Err("打开 Desktop 注册表项失败".to_string());
            }
            let byte_len = (val_str.len() * 2) as u32;
            let rc = RegSetValueExW(
                hkey,
                val_name.as_ptr(),
                0,
                REG_SZ,
                val_str.as_ptr() as *const u8,
                byte_len,
            );
            RegCloseKey(hkey);
            if rc != 0 {
                return Err(format!("写入 MenuShowDelay 失败 (错误码 {})", rc));
            }
            // SPI_SETMENUSHOWDELAY = 0x006B
            let _ = SystemParametersInfoW(0x006B, delay_ms, std::ptr::null_mut(), 0x0002 | 0x0001);
            Ok(())
        }
    }

    /// 对目标进程施加四重自私压榨隔离（失败返回 false 代表权限不足）
    pub fn isolate_background_process(pid: u32, exile_mask: usize) -> bool {
        unsafe {
            let h = OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION, 0, pid);
            if h == 0 {
                return false;
            }
            let p_ok = SetPriorityClass(h, IDLE_PRIORITY_CLASS) != 0;
            let a_ok = SetProcessAffinityMask(h, exile_mask) != 0;

            let throttle = ProcessPowerThrottlingState {
                version: 1,
                control_mask: 1,
                state_mask: 1,
            };
            let _ = SetProcessInformation(
                h,
                PROCESS_POWER_THROTTLING,
                &throttle as *const _ as *const c_void,
                std::mem::size_of::<ProcessPowerThrottlingState>() as u32,
            );

            let mem_prio = MemoryPriorityInfo {
                memory_priority: MEMORY_PRIORITY_VERY_LOW,
            };
            let _ = SetProcessInformation(
                h,
                PROCESS_MEMORY_PRIORITY,
                &mem_prio as *const _ as *const c_void,
                std::mem::size_of::<MemoryPriorityInfo>() as u32,
            );

            let io_prio = IO_PRIORITY_VERY_LOW;
            if let Some(f) = ntdll().set_info_proc {
                let _ = f(
                    h,
                    PROCESS_IO_PRIORITY,
                    &io_prio as *const _ as *const c_void,
                    std::mem::size_of::<u32>() as u32,
                );
            }

            CloseHandle(h);
            p_ok || a_ok
        }
    }

    /// 赋予前台 VIP / 受保护进程全核算力 + 关闭节流 + 高优先级
    pub fn boost_process(pid: u32, full_mask: usize, high_prio: bool) -> bool {
        unsafe {
            let h = OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION, 0, pid);
            if h == 0 {
                return false;
            }
            let prio = if high_prio {
                HIGH_PRIORITY_CLASS
            } else {
                NORMAL_PRIORITY_CLASS
            };
            let p_ok = SetPriorityClass(h, prio) != 0;
            let a_ok = SetProcessAffinityMask(h, full_mask) != 0;

            // 显式关闭 EcoQoS 节流：ControlMask = 1, StateMask = 0
            let throttle = ProcessPowerThrottlingState {
                version: 1,
                control_mask: 1,
                state_mask: 0,
            };
            let _ = SetProcessInformation(
                h,
                PROCESS_POWER_THROTTLING,
                &throttle as *const _ as *const c_void,
                std::mem::size_of::<ProcessPowerThrottlingState>() as u32,
            );

            let mem_prio = MemoryPriorityInfo {
                memory_priority: MEMORY_PRIORITY_NORMAL,
            };
            let _ = SetProcessInformation(
                h,
                PROCESS_MEMORY_PRIORITY,
                &mem_prio as *const _ as *const c_void,
                std::mem::size_of::<MemoryPriorityInfo>() as u32,
            );

            let io_prio = IO_PRIORITY_NORMAL;
            if let Some(f) = ntdll().set_info_proc {
                let _ = f(
                    h,
                    PROCESS_IO_PRIORITY,
                    &io_prio as *const _ as *const c_void,
                    std::mem::size_of::<u32>() as u32,
                );
            }

            CloseHandle(h);
            p_ok || a_ok
        }
    }

    pub fn restore_process_defaults(pid: u32, full_mask: usize) -> bool {
        unsafe {
            let h = OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION, 0, pid);
            if h == 0 {
                return false;
            }
            let ok = SetPriorityClass(h, NORMAL_PRIORITY_CLASS) != 0;
            let _ = SetProcessAffinityMask(h, full_mask);

            let throttle = ProcessPowerThrottlingState {
                version: 1,
                control_mask: 0,
                state_mask: 0,
            };
            let _ = SetProcessInformation(
                h,
                PROCESS_POWER_THROTTLING,
                &throttle as *const _ as *const c_void,
                std::mem::size_of::<ProcessPowerThrottlingState>() as u32,
            );

            let mem_prio = MemoryPriorityInfo {
                memory_priority: MEMORY_PRIORITY_NORMAL,
            };
            let _ = SetProcessInformation(
                h,
                PROCESS_MEMORY_PRIORITY,
                &mem_prio as *const _ as *const c_void,
                std::mem::size_of::<MemoryPriorityInfo>() as u32,
            );

            let io_prio = IO_PRIORITY_NORMAL;
            if let Some(f) = ntdll().set_info_proc {
                let _ = f(
                    h,
                    PROCESS_IO_PRIORITY,
                    &io_prio as *const _ as *const c_void,
                    std::mem::size_of::<u32>() as u32,
                );
            }

            CloseHandle(h);
            ok
        }
    }

    pub fn suspend_process(pid: u32) -> bool {
        let Some(f) = ntdll().suspend_proc else {
            return false;
        };
        unsafe {
            let h = OpenProcess(PROCESS_SUSPEND_RESUME, 0, pid);
            if h == 0 {
                return false;
            }
            let st = f(h);
            CloseHandle(h);
            st == 0
        }
    }

    pub fn resume_process(pid: u32) -> bool {
        let Some(f) = ntdll().resume_proc else {
            return false;
        };
        unsafe {
            let h = OpenProcess(PROCESS_SUSPEND_RESUME, 0, pid);
            if h == 0 {
                return false;
            }
            let st = f(h);
            CloseHandle(h);
            st == 0
        }
    }

    pub fn kill_process_win(pid: u32) -> bool {
        unsafe {
            let h = OpenProcess(PROCESS_TERMINATE, 0, pid);
            if h == 0 {
                return false;
            }
            let ok = TerminateProcess(h, 1) != 0;
            CloseHandle(h);
            ok
        }
    }

    pub fn trim_process_working_set(pid: u32) -> bool {
        unsafe {
            let h = OpenProcess(PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION, 0, pid);
            if h == 0 {
                return false;
            }
            let ok = EmptyWorkingSet(h) != 0;
            CloseHandle(h);
            ok
        }
    }

    pub fn purge_standby_list() -> bool {
        let Some(f) = ntdll().set_sys_info else {
            return false;
        };
        let _ = enable_privilege("SeProfileSingleProcessPrivilege");
        unsafe {
            let cmd: u32 = 4; // MemoryPurgeStandbyList
            f(
                80, // SystemMemoryListInformation
                &cmd as *const _ as *const c_void,
                std::mem::size_of::<u32>() as u32,
            ) == 0
        }
    }

    pub fn set_core_parking(disable_parking: bool) {
        if !is_elevated() {
            return;
        }
        let val = if disable_parking { "100" } else { "10" };
        let _ = Command::new("powercfg.exe")
            .args([
                "-setacvalueindex",
                "scheme_current",
                "sub_processor",
                "CPMINCORES",
                val,
            ])
            .creation_flags(CREATE_NO_WINDOW)
            .output();
        let _ = Command::new("powercfg.exe")
            .args(["-setactive", "scheme_current"])
            .creation_flags(CREATE_NO_WINDOW)
            .output();
    }

    pub fn is_service_running(name: &str) -> bool {
        let Ok(q_out) = Command::new("sc.exe")
            .args(["query", name])
            .creation_flags(CREATE_NO_WINDOW)
            .output()
        else {
            return false;
        };
        if !q_out.status.success() {
            return false;
        }
        String::from_utf8_lossy(&q_out.stdout)
            .to_ascii_uppercase()
            .contains("RUNNING")
    }

    pub fn query_service_status(name: &str) -> Option<(String, String)> {
        let q_out = Command::new("sc.exe")
            .args(["query", name])
            .creation_flags(CREATE_NO_WINDOW)
            .output()
            .ok()?;
        if !q_out.status.success() {
            return None;
        }
        let q_txt = String::from_utf8_lossy(&q_out.stdout).to_ascii_uppercase();
        let status = if q_txt.contains("RUNNING") {
            "running"
        } else if q_txt.contains("STOPPED") {
            "stopped"
        } else {
            "pending"
        };

        let qc_out = Command::new("sc.exe")
            .args(["qc", name])
            .creation_flags(CREATE_NO_WINDOW)
            .output()
            .ok();
        let start_type = if let Some(out) = qc_out {
            let qc_txt = String::from_utf8_lossy(&out.stdout).to_ascii_uppercase();
            if qc_txt.contains("AUTO_START") {
                "auto"
            } else if qc_txt.contains("DEMAND_START") {
                "manual"
            } else if qc_txt.contains("DISABLED") {
                "disabled"
            } else {
                "unknown"
            }
        } else {
            "unknown"
        };

        Some((status.to_string(), start_type.to_string()))
    }

    pub fn control_service(name: &str, action: &str) -> Result<String, String> {
        let args: Vec<&str> = match action {
            "stop" => vec!["stop", name],
            "start" => vec!["start", name],
            "manual" => vec!["config", name, "start=", "demand"],
            "auto" => vec!["config", name, "start=", "auto"],
            _ => return Err(format!("不支持的服务动作: {}", action)),
        };

        let out = Command::new("sc.exe")
            .args(&args)
            .creation_flags(CREATE_NO_WINDOW)
            .output()
            .map_err(|e| format!("调用 sc.exe 失败: {}", e))?;

        if out.status.success() {
            Ok(format!("服务 {} 操作 [{}] 已执行", name, action))
        } else {
            let msg = String::from_utf8_lossy(&out.stdout).trim().to_string();
            let err = String::from_utf8_lossy(&out.stderr).trim().to_string();
            let detail = if !err.is_empty() { err } else { msg };
            if detail.contains("5") || detail.to_ascii_lowercase().contains("access") {
                Err("权限不足：操作 Windows 服务需要以管理员身份（UAC 提权）运行".to_string())
            } else {
                Err(format!("服务控制失败: {}", detail))
            }
        }
    }

    pub fn move_to_recycle_bin(path: &Path) -> Result<(), String> {
        let abs = path.to_string_lossy().replace('/', "\\");
        let wide_from = to_wide_double_null(&abs);
        unsafe {
            // FOF_ALLOWUNDO (0x40) | FOF_NOCONFIRMATION (0x10) | FOF_SILENT (0x04) | FOF_NOERRORUI (0x0400)
            let mut op = ShFileOpStructW {
                hwnd: 0,
                w_func: 3, // FO_DELETE
                p_from: wide_from.as_ptr(),
                p_to: std::ptr::null(),
                f_flags: 0x0040 | 0x0010 | 0x0004 | 0x0400,
                f_any_operations_aborted: 0,
                h_name_mappings: 0,
                lpsz_progress_title: std::ptr::null(),
            };
            let rc = SHFileOperationW(&mut op);
            if rc == 0 && op.f_any_operations_aborted == 0 {
                Ok(())
            } else {
                Err(format!("移入回收站失败（文件可能正在被占用或需要管理员权限，错误码 {}）", rc))
            }
        }
    }

    pub fn reveal_in_explorer(path: &Path) -> Result<(), String> {
        let abs = path.to_string_lossy().replace('/', "\\");
        let arg = if path.is_file() {
            format!("/select,\"{}\"", abs)
        } else {
            format!("\"{}\"", abs)
        };
        Command::new("explorer.exe")
            .raw_arg(&arg)
            .creation_flags(CREATE_NO_WINDOW)
            .spawn()
            .map_err(|e| format!("打开资源管理器失败: {}", e))?;
        Ok(())
    }

    pub fn wait_for_pid_exit(pid: u32, timeout_ms: u32) {
        const SYNCHRONIZE: u32 = 0x0010_0000;
        unsafe {
            let h = OpenProcess(SYNCHRONIZE, 0, pid);
            if h != 0 {
                let _ = WaitForSingleObject(h, timeout_ms);
                CloseHandle(h);
            }
        }
    }

    pub fn relaunch_as_admin() -> Result<bool, String> {
        let exe = std::env::current_exe()
            .map_err(|e| format!("获取当前程序路径失败: {}", e))?;
        let self_pid = std::process::id();
        let verb = to_wide_null("runas");
        let file = to_wide_null(&exe.to_string_lossy());
        let params_str = format!("--wait-pid {}", self_pid);
        let params = to_wide_null(&params_str);
        let dir = exe
            .parent()
            .map(|p| to_wide_null(&p.to_string_lossy()));
        let rc = unsafe {
            ShellExecuteW(
                0,
                verb.as_ptr(),
                file.as_ptr(),
                params.as_ptr(),
                dir.as_ref().map(|d| d.as_ptr()).unwrap_or(std::ptr::null()),
                1, // SW_SHOWNORMAL
            )
        };
        if rc > 32 {
            Ok(true)
        } else {
            Err("用户取消了管理员 UAC 授权或提权启动失败".to_string())
        }
    }
}

#[cfg(not(target_os = "windows"))]
mod win_native {
    use std::path::Path;

    pub fn is_elevated() -> bool {
        false
    }
    pub fn init_privileges() {}
    pub fn get_memory_commit_mb() -> (u64, u64, u64, u64) {
        (0, 0, 0, 0)
    }
    pub fn get_foreground_pid() -> Option<u32> {
        None
    }
    pub fn set_timer_resolution(_enable_05ms: bool) -> f32 {
        15.625
    }
    pub fn get_timer_resolution_ms() -> f32 {
        15.625
    }
    pub fn get_menu_show_delay_ms() -> u32 {
        400
    }
    pub fn set_menu_show_delay_ms(_delay_ms: u32) -> Result<(), String> {
        Ok(())
    }
    pub fn isolate_background_process(_pid: u32, _exile_mask: usize) -> bool {
        false
    }
    pub fn boost_process(_pid: u32, _full_mask: usize, _high_prio: bool) -> bool {
        false
    }
    pub fn restore_process_defaults(_pid: u32, _full_mask: usize) -> bool {
        false
    }
    pub fn suspend_process(_pid: u32) -> bool {
        false
    }
    pub fn resume_process(_pid: u32) -> bool {
        false
    }
    pub fn kill_process_win(_pid: u32) -> bool {
        false
    }
    pub fn trim_process_working_set(_pid: u32) -> bool {
        false
    }
    pub fn purge_standby_list() -> bool {
        false
    }
    pub fn set_core_parking(_disable_parking: bool) {}
    pub fn is_service_running(_name: &str) -> bool {
        false
    }
    pub fn query_service_status(_name: &str) -> Option<(String, String)> {
        None
    }
    pub fn control_service(_name: &str, _action: &str) -> Result<String, String> {
        Err("仅支持 Windows 平台控制服务".to_string())
    }
    pub fn move_to_recycle_bin(_path: &Path) -> Result<(), String> {
        Err("仅支持 Windows 平台回收站安全删除".to_string())
    }
    pub fn reveal_in_explorer(_path: &Path) -> Result<(), String> {
        Err("仅支持 Windows 平台资源管理器定位".to_string())
    }
    pub fn relaunch_as_admin() -> Result<bool, String> {
        Err("当前操作系统不支持 Windows UAC 提权".to_string())
    }
    pub fn wait_for_pid_exit(_pid: u32, _timeout_ms: u32) {}
}

// -------------------------------------------------------------
// 后台守护线程与核心调度逻辑
// -------------------------------------------------------------
fn build_proc_tree_map(sys: &System) -> HashMap<u32, (Option<u32>, String)> {
    let mut map = HashMap::with_capacity(sys.processes().len());
    for (pid, p) in sys.processes() {
        let ppid = p.parent().map(|parent| parent.as_u32());
        let name = p.name().to_string_lossy().to_string();
        map.insert(pid.as_u32(), (ppid, name));
    }
    map
}

fn execute_ruthless_sweep(sys: &System, cfg: &OptimizerConfig) {
    let n_cpus = sys.cpus().len().max(1);
    let (full_mask, exile_mask, _) = compute_affinity_masks(n_cpus);
    let proc_map = build_proc_tree_map(sys);
    let self_pid = std::process::id();
    let fg_pid = win_native::get_foreground_pid();

    if let Some(fp) = fg_pid {
        LAST_FG_PID.store(fp as usize, Ordering::Relaxed);
        if let Some((_, pname)) = proc_map.get(&fp) {
            if let Ok(mut guard) = last_fg_name().lock() {
                *guard = Some(pname.clone());
            }
        }
    }

    let mut new_isolated = HashSet::new();
    let mut new_denied = HashSet::new();

    for (&pid, (_ppid, _name)) in &proc_map {
        let prot = classify_process_protection(pid, &proc_map, &cfg.custom_whitelist, self_pid);
        if prot == ProtectionKind::System {
            continue;
        }
        if prot.is_protected() {
            // 代理与 Antigravity 核心家族：赋予全核心无节流高响应保障（不压制！）
            let _ = win_native::boost_process(pid, full_mask, true);
            continue;
        }
        if Some(pid) == fg_pid {
            // 当前前台活动窗口：拉升为全核最高优先级 VIP
            let _ = win_native::boost_process(pid, full_mask, true);
            continue;
        }
        if cfg.aggressive_core_isolation {
            if win_native::isolate_background_process(pid, exile_mask) {
                new_isolated.insert(pid);
            } else {
                new_denied.insert(pid);
            }
        }
    }

    if let Ok(mut guard) = isolated_pids().lock() {
        *guard = new_isolated;
    }
    if let Ok(mut guard) = denied_pids().lock() {
        *guard = new_denied;
    }
}

fn spawn_ruthless_daemon_if_needed() {
    if DAEMON_STARTED.swap(true, Ordering::SeqCst) {
        return;
    }
    std::thread::spawn(|| {
        let mut tick: u64 = 0;
        let mut prev_fg: Option<u32> = None;
        loop {
            std::thread::sleep(std::time::Duration::from_millis(350));
            if !RUTHLESS_ACTIVE.load(Ordering::Relaxed) {
                tick = 0;
                prev_fg = None;
                continue;
            }
            let cfg = load_optimizer_config();
            if cfg.timer_05ms_enabled {
                let _ = win_native::set_timer_resolution(true);
            }

            let cur_fg = win_native::get_foreground_pid();
            let fg_changed = cur_fg != prev_fg;
            if fg_changed {
                if let Some(fp) = cur_fg {
                    let n_cpus = std::thread::available_parallelism()
                        .map(|n| n.get())
                        .unwrap_or(16);
                    let (full_mask, exile_mask, _) = compute_affinity_masks(n_cpus);
                    let _ = win_native::boost_process(fp, full_mask, true);
                    LAST_FG_PID.store(fp as usize, Ordering::Relaxed);
                    // 前任前台窗口若不是白名单且已被切走，重新压入孤立区
                    if let Some(old_fp) = prev_fg {
                        if let Ok(mut sys) = sys_probe().lock() {
                            sys.refresh_processes(sysinfo::ProcessesToUpdate::All);
                            let proc_map = build_proc_tree_map(&sys);
                            if let Some((_, cur_name)) = proc_map.get(&fp) {
                                if let Ok(mut g) = last_fg_name().lock() {
                                    *g = Some(cur_name.clone());
                                }
                            }
                            let prot = classify_process_protection(
                                old_fp,
                                &proc_map,
                                &cfg.custom_whitelist,
                                std::process::id(),
                            );
                            if !prot.is_protected() && cfg.aggressive_core_isolation {
                                let _ = win_native::isolate_background_process(old_fp, exile_mask);
                            }
                        }
                    }
                }
                prev_fg = cur_fg;
            }

            // 每 10 次心跳（约 3.5 秒）扫描一次新出现的第三方后台并执行核心隔离
            if tick % 10 == 0 {
                if let Ok(mut sys) = sys_probe().lock() {
                    sys.refresh_processes(sysinfo::ProcessesToUpdate::All);
                    execute_ruthless_sweep(&sys, &cfg);
                }
            }
            tick = tick.wrapping_add(1);
        }
    });
}

/// 应用启动时调用：若配置开启极客霸权模式则自动恢复守护
pub fn init_optimizer_on_startup() {
    win_native::init_privileges();
    let cfg = load_optimizer_config();
    if cfg.ruthless_enabled {
        let _ = toggle_ruthless_mode(true);
    }
}

/// 应用退出时兜底清理：解冻全部被挂起进程、恢复时钟与全核心隔离状态
pub fn shutdown_and_restore() {
    RUTHLESS_ACTIVE.store(false, Ordering::SeqCst);
    let _ = win_native::set_timer_resolution(false);
    win_native::set_core_parking(false);

    if let Ok(mut frozen) = frozen_pids().lock() {
        for pid in frozen.drain() {
            let _ = win_native::resume_process(pid);
        }
    }

    let n_cpus = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(16);
    let (full_mask, _, _) = compute_affinity_masks(n_cpus);
    if let Ok(mut isolated) = isolated_pids().lock() {
        for pid in isolated.drain() {
            let _ = win_native::restore_process_defaults(pid, full_mask);
        }
    }
}

pub fn toggle_ruthless_mode(enable: bool) -> Result<OptimizerOverview, String> {
    win_native::init_privileges();
    let mut cfg = load_optimizer_config();
    cfg.ruthless_enabled = enable;
    let _ = save_optimizer_config(&cfg);

    if enable {
        RUTHLESS_ACTIVE.store(true, Ordering::SeqCst);
        if cfg.timer_05ms_enabled {
            let _ = win_native::set_timer_resolution(true);
        }
        if cfg.auto_zero_menu_delay {
            let _ = win_native::set_menu_show_delay_ms(0);
        }
        win_native::set_core_parking(true);

        if let Ok(mut sys) = sys_probe().lock() {
            sys.refresh_processes(sysinfo::ProcessesToUpdate::All);
            execute_ruthless_sweep(&sys, &cfg);
        }
        spawn_ruthless_daemon_if_needed();
    } else {
        RUTHLESS_ACTIVE.store(false, Ordering::SeqCst);
        let _ = win_native::set_timer_resolution(false);
        win_native::set_core_parking(false);

        let n_cpus = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(16);
        let (full_mask, _, _) = compute_affinity_masks(n_cpus);
        if let Ok(mut isolated) = isolated_pids().lock() {
            for pid in isolated.drain() {
                let _ = win_native::restore_process_defaults(pid, full_mask);
            }
        }
        if let Ok(mut denied) = denied_pids().lock() {
            denied.clear();
        }
    }

    Ok(get_overview())
}

pub fn get_overview() -> OptimizerOverview {
    let cfg = load_optimizer_config();
    let elevated = win_native::is_elevated();
    let (cpu_percent, mem_tot, mem_avail, logical_cpus, protected_count) = {
        let mut sys = sys_probe().lock().unwrap_or_else(|e| e.into_inner());
        sys.refresh_memory();
        sys.refresh_cpu_usage();
        sys.refresh_processes(sysinfo::ProcessesToUpdate::All);
        let cpu = sys.global_cpu_usage();
        let m_tot = sys.total_memory() / (1024 * 1024);
        let m_avail = sys.available_memory() / (1024 * 1024);
        let cpus = sys.cpus().len().max(1);
        let proc_map = build_proc_tree_map(&sys);
        let self_pid = std::process::id();
        let prot_cnt = proc_map
            .keys()
            .filter(|&&pid| {
                classify_process_protection(pid, &proc_map, &cfg.custom_whitelist, self_pid)
                    .is_protected()
            })
            .count();
        (cpu, m_tot, m_avail, cpus, prot_cnt)
    };

    let (win_phys_tot, win_phys_avail, commit_tot, commit_avail) =
        win_native::get_memory_commit_mb();
    let final_tot = if win_phys_tot > 0 { win_phys_tot } else { mem_tot };
    let final_avail = if win_phys_avail > 0 {
        win_phys_avail
    } else {
        mem_avail
    };
    let final_used = final_tot.saturating_sub(final_avail);
    let mem_percent = if final_tot > 0 {
        ((final_used as f32) / (final_tot as f32)) * 100.0
    } else {
        0.0
    };

    let commit_used = commit_tot.saturating_sub(commit_avail);
    let commit_percent = if commit_tot > 0 {
        ((commit_used as f32) / (commit_tot as f32)) * 100.0
    } else {
        0.0
    };

    let (_, _, exile_cores_label) = compute_affinity_masks(logical_cpus);
    let throttled_count = isolated_pids().lock().map(|g| g.len()).unwrap_or(0);
    let frozen_count = frozen_pids().lock().map(|g| g.len()).unwrap_or(0);
    let access_denied_count = denied_pids().lock().map(|g| g.len()).unwrap_or(0);
    let fg_pid = win_native::get_foreground_pid().or_else(|| {
        let cached = LAST_FG_PID.load(Ordering::Relaxed);
        if cached > 4 {
            Some(cached as u32)
        } else {
            None
        }
    });
    let fg_name = last_fg_name().lock().ok().and_then(|g| g.clone());

    let running_heavy_services = get_running_heavy_service_count_cached();

    OptimizerOverview {
        cpu_percent: (cpu_percent * 10.0).round() / 10.0,
        mem_total_mb: final_tot,
        mem_used_mb: final_used,
        mem_available_mb: final_avail,
        mem_percent: (mem_percent * 10.0).round() / 10.0,
        commit_total_mb: commit_tot,
        commit_used_mb: commit_used,
        commit_percent: (commit_percent * 10.0).round() / 10.0,
        timer_resolution_ms: win_native::get_timer_resolution_ms(),
        menu_show_delay_ms: win_native::get_menu_show_delay_ms(),
        is_elevated: elevated,
        is_windows: cfg!(target_os = "windows"),
        logical_cpus,
        exile_cores_label,
        ruthless_enabled: RUTHLESS_ACTIVE.load(Ordering::Relaxed),
        foreground_process: fg_name,
        foreground_pid: fg_pid,
        throttled_count,
        frozen_count,
        protected_count,
        access_denied_count,
        running_heavy_services,
    }
}

pub fn boost_memory() -> MemoryBoostResult {
    win_native::init_privileges();
    let cfg = load_optimizer_config();
    let (_, win_before, _, _) = win_native::get_memory_commit_mb();
    let before_avail = if win_before > 0 {
        win_before
    } else {
        get_overview().mem_available_mb
    };
    let standby_purged = win_native::purge_standby_list();

    let fg_pid = win_native::get_foreground_pid();
    let self_pid = std::process::id();
    let mut trimmed = 0usize;

    if let Ok(mut sys) = sys_probe().lock() {
        sys.refresh_processes(sysinfo::ProcessesToUpdate::All);
        let proc_map = build_proc_tree_map(&sys);
        for (&pid, _) in &proc_map {
            if Some(pid) == fg_pid {
                continue;
            }
            let prot = classify_process_protection(pid, &proc_map, &cfg.custom_whitelist, self_pid);
            // 严禁修剪系统内核、代理网络、Antigravity 核心树或当前前台（杜绝硬缺页卡顿）
            if prot.is_protected() {
                continue;
            }
            if win_native::trim_process_working_set(pid) {
                trimmed += 1;
            }
        }
    }

    std::thread::sleep(std::time::Duration::from_millis(180));
    let (_, win_after, _, _) = win_native::get_memory_commit_mb();
    let after_avail = if win_after > 0 {
        win_after
    } else {
        get_overview().mem_available_mb
    };
    let freed_mb = after_avail.saturating_sub(before_avail) as f64;
    let elevated = win_native::is_elevated();

    let message = if standby_purged {
        format!(
            "已清空系统 Standby 缓存死锁并修剪 {} 个非白名单后台，物理可用内存净增 {:.0} MB",
            trimmed, freed_mb
        )
    } else if !elevated {
        format!(
            "已安全修剪 {} 个后台进程（净增 {:.0} MB）；点击右上角「UAC 提权」后可解锁真正清空系统 Standby 备用内存锁",
            trimmed, freed_mb
        )
    } else {
        format!("已修剪 {} 个后台进程，物理可用内存增加 {:.0} MB", trimmed, freed_mb)
    };

    MemoryBoostResult {
        success: true,
        standby_purged,
        trimmed_processes: trimmed,
        freed_mb,
        before_avail_mb: before_avail,
        after_avail_mb: after_avail,
        needs_elevation: !standby_purged && !elevated,
        message,
    }
}

pub fn list_process_groups() -> Vec<ProcessGroupItem> {
    let cfg = load_optimizer_config();
    let fg_pid = win_native::get_foreground_pid();
    let self_pid = std::process::id();
    let frozen_set = frozen_pids().lock().map(|g| g.clone()).unwrap_or_default();
    let isolated_set = isolated_pids().lock().map(|g| g.clone()).unwrap_or_default();

    let mut sys = sys_probe().lock().unwrap_or_else(|e| e.into_inner());
    sys.refresh_processes(sysinfo::ProcessesToUpdate::All);
    let proc_map = build_proc_tree_map(&sys);

    struct GroupAcc {
        display_name: String,
        pids: Vec<u32>,
        ws_bytes: u64,
        virt_bytes: u64,
        cpu_sum: f32,
        best_prot: ProtectionKind,
        has_fg: bool,
        any_frozen: bool,
        any_isolated: bool,
        exe_path: Option<String>,
    }

    let mut groups: HashMap<String, GroupAcc> = HashMap::new();
    for (pid_obj, proc_) in sys.processes() {
        let pid = pid_obj.as_u32();
        if pid <= 4 {
            continue;
        }
        let raw_name = proc_.name().to_string_lossy().to_string();
        let key = raw_name.to_ascii_lowercase();
        let prot = classify_process_protection(pid, &proc_map, &cfg.custom_whitelist, self_pid);
        let is_fg = Some(pid) == fg_pid;
        let is_frozen = frozen_set.contains(&pid);
        let is_isolated = isolated_set.contains(&pid);
        let exe_path = proc_.exe().map(|p| p.to_string_lossy().to_string());

        let entry = groups.entry(key).or_insert_with(|| GroupAcc {
            display_name: raw_name,
            pids: Vec::new(),
            ws_bytes: 0,
            virt_bytes: 0,
            cpu_sum: 0.0,
            best_prot: prot,
            has_fg: false,
            any_frozen: false,
            any_isolated: false,
            exe_path,
        });

        entry.pids.push(pid);
        entry.ws_bytes = entry.ws_bytes.saturating_add(proc_.memory());
        entry.virt_bytes = entry.virt_bytes.saturating_add(proc_.virtual_memory());
        entry.cpu_sum += proc_.cpu_usage();
        if prot.is_protected() && !entry.best_prot.is_protected() {
            entry.best_prot = prot;
        }
        if is_fg {
            entry.has_fg = true;
        }
        if is_frozen {
            entry.any_frozen = true;
        }
        if is_isolated {
            entry.any_isolated = true;
        }
    }

    let mut result: Vec<ProcessGroupItem> = groups
        .into_values()
        .map(|g| {
            let ws_mb = ((g.ws_bytes as f64) / (1024.0 * 1024.0) * 10.0).round() / 10.0;
            let priv_mb = (((g.virt_bytes.min(g.ws_bytes * 2)) as f64) / (1024.0 * 1024.0) * 10.0).round() / 10.0;
            let state = if g.any_frozen {
                "frozen"
            } else if g.has_fg {
                "foreground_vip"
            } else if g.best_prot.is_protected() {
                "protected"
            } else if g.any_isolated {
                "isolated"
            } else {
                "normal"
            };
            let protection = if g.has_fg && !g.best_prot.is_protected() {
                "foreground"
            } else {
                g.best_prot.as_str()
            };
            let protection_label = if g.has_fg && !g.best_prot.is_protected() {
                "当前前台 VIP"
            } else {
                g.best_prot.label()
            };

            ProcessGroupItem {
                name: g.display_name,
                count: g.pids.len(),
                pids: g.pids,
                working_set_mb: ws_mb,
                private_mb: priv_mb,
                cpu_percent: (g.cpu_sum * 10.0).round() / 10.0,
                protection: protection.to_string(),
                protection_label: protection_label.to_string(),
                state: state.to_string(),
                is_frozen: g.any_frozen,
                can_control: !g.best_prot.is_protected(),
                exe_path: g.exe_path,
            }
        })
        .collect();

    result.sort_by(|a, b| {
        b.working_set_mb
            .partial_cmp(&a.working_set_mb)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    result
}

pub fn control_process_group(process_name: &str, action: &str) -> OptimizerActionResult {
    win_native::init_privileges();
    let cfg = load_optimizer_config();
    let target_norm = normalize_proc_name(process_name);
    let self_pid = std::process::id();

    let (pids, n_cpus, protected_hit) = {
        let mut sys = sys_probe().lock().unwrap_or_else(|e| e.into_inner());
        sys.refresh_processes(sysinfo::ProcessesToUpdate::All);
        let proc_map = build_proc_tree_map(&sys);
        let mut matched = Vec::new();
        let mut prot_block = false;
        for (&pid, (_ppid, raw_name)) in &proc_map {
            if normalize_proc_name(raw_name) == target_norm {
                let prot =
                    classify_process_protection(pid, &proc_map, &cfg.custom_whitelist, self_pid);
                if prot.is_protected() {
                    prot_block = true;
                } else {
                    matched.push(pid);
                }
            }
        }
        (matched, sys.cpus().len().max(1), prot_block)
    };

    if pids.is_empty() {
        return OptimizerActionResult {
            success: false,
            message: if protected_hit {
                format!("「{}」位于神圣白名单保护中，已严格拦截操作", process_name)
            } else {
                format!("当前未找到运行中的「{}」进程", process_name)
            },
            affected: 0,
            denied: 0,
            needs_elevation: false,
        };
    }

    let (full_mask, exile_mask, _) = compute_affinity_masks(n_cpus);
    let mut affected = 0usize;
    let mut denied = 0usize;

    for pid in pids {
        let ok = match action {
            "freeze" => {
                let _ = win_native::isolate_background_process(pid, exile_mask);
                if win_native::suspend_process(pid) {
                    if let Ok(mut f) = frozen_pids().lock() {
                        f.insert(pid);
                    }
                    true
                } else {
                    false
                }
            }
            "unfreeze" => {
                if win_native::resume_process(pid) {
                    if let Ok(mut f) = frozen_pids().lock() {
                        f.remove(&pid);
                    }
                    true
                } else {
                    false
                }
            }
            "isolate" => {
                if win_native::isolate_background_process(pid, exile_mask) {
                    if let Ok(mut iso) = isolated_pids().lock() {
                        iso.insert(pid);
                    }
                    true
                } else {
                    false
                }
            }
            "restore" => {
                let _ = win_native::resume_process(pid);
                if let Ok(mut f) = frozen_pids().lock() {
                    f.remove(&pid);
                }
                if let Ok(mut iso) = isolated_pids().lock() {
                    iso.remove(&pid);
                }
                win_native::restore_process_defaults(pid, full_mask)
            }
            "kill" => {
                if let Ok(mut f) = frozen_pids().lock() {
                    f.remove(&pid);
                }
                win_native::kill_process_win(pid)
            }
            _ => false,
        };
        if ok {
            affected += 1;
        } else {
            denied += 1;
        }
    }

    let needs_elevation = affected == 0 && denied > 0 && !win_native::is_elevated();
    let act_cn = match action {
        "freeze" => "冻结挂起（CPU 归零）",
        "unfreeze" => "解冻恢复",
        "isolate" => "核心隔离压制",
        "restore" => "恢复正常调度",
        "kill" => "结束进程",
        _ => action,
    };

    OptimizerActionResult {
        success: affected > 0,
        message: if needs_elevation {
            format!(
                "「{}」需要管理员权限才能执行{}，请点击顶部「UAC 提权」后重试",
                process_name, act_cn
            )
        } else {
            format!("已对「{}」共 {} 个实例执行{}", process_name, affected, act_cn)
        },
        affected,
        denied,
        needs_elevation,
    }
}

pub fn unfreeze_all_processes() -> OptimizerActionResult {
    let mut affected = 0usize;
    if let Ok(mut frozen) = frozen_pids().lock() {
        for pid in frozen.drain() {
            if win_native::resume_process(pid) {
                affected += 1;
            }
        }
    }
    OptimizerActionResult {
        success: true,
        message: format!("已解冻恢复 {} 个挂起进程", affected),
        affected,
        denied: 0,
        needs_elevation: false,
    }
}

pub fn list_heavy_services() -> Vec<ServiceItem> {
    let mut items = Vec::new();
    for &(name, display, cat, est_mb, rec_stop, note) in HEAVY_SERVICE_CATALOG {
        if let Some((status, start_type)) = win_native::query_service_status(name) {
            items.push(ServiceItem {
                name: name.to_string(),
                display_name: display.to_string(),
                category: cat.to_string(),
                status,
                start_type,
                est_memory_mb: est_mb,
                risk_note: note.to_string(),
                recommended_stop: rec_stop,
            });
        }
    }
    items
}

pub fn control_heavy_service(name: &str, action: &str) -> Result<String, String> {
    if !HEAVY_SERVICE_CATALOG.iter().any(|(svc, _, _, _, _, _)| *svc == name) {
        return Err(format!("安全拦截：不允许通过此面板操作未登记的系统服务 {}", name));
    }
    let res = win_native::control_service(name, action)?;
    invalidate_heavy_svc_cache();
    Ok(res)
}

fn calc_dir_stats(path: &Path, max_depth: usize) -> (u64, usize) {
    let mut total_bytes: u64 = 0;
    let mut file_count: usize = 0;
    let mut stack = vec![(path.to_path_buf(), 0usize)];
    while let Some((dir, depth)) = stack.pop() {
        let Ok(rd) = std::fs::read_dir(&dir) else {
            continue;
        };
        for entry in rd.flatten() {
            let Ok(ft) = entry.file_type() else {
                continue;
            };
            if ft.is_symlink() {
                continue;
            }
            if ft.is_file() {
                if let Ok(meta) = entry.metadata() {
                    total_bytes = total_bytes.saturating_add(meta.len());
                    file_count += 1;
                }
            } else if ft.is_dir() && depth < max_depth {
                stack.push((entry.path(), depth + 1));
            }
        }
    }
    (total_bytes, file_count)
}

pub fn scan_junk_categories() -> Vec<JunkCategoryItem> {
    let mut candidates: Vec<(&str, &str, &str, PathBuf, bool, &str)> = Vec::new();

    if let Ok(temp) = std::env::var("TEMP") {
        candidates.push((
            "user_temp",
            "用户临时文件夹 (TEMP)",
            "safe",
            PathBuf::from(temp),
            true,
            "安装包残余与程序运行临时文件，被占用文件将自动安全跳过。",
        ));
    }
    #[cfg(target_os = "windows")]
    candidates.push((
        "win_temp",
        "Windows 系统临时目录",
        "safe",
        PathBuf::from(r"C:\Windows\Temp"),
        true,
        "系统更新与安装服务遗留的临时解压文件。",
    ));

    if let Ok(local_app) = std::env::var("LOCALAPPDATA") {
        let la = PathBuf::from(&local_app);
        candidates.push((
            "crash_dumps",
            "程序崩溃转储 (CrashDumps)",
            "safe",
            la.join("CrashDumps"),
            true,
            "应用闪退生成的内存转储 .dmp 文件，通常体积较大且日常无用。",
        ));
        candidates.push((
            "chrome_cache",
            "Chrome 网页媒体缓存 (仅 Cache)",
            "browser",
            la.join(r"Google\Chrome\User Data\Default\Cache"),
            false,
            "仅清理网页图片与脚本缓存，绝对不触碰 Cookie、密码、书签与登录态。",
        ));
        candidates.push((
            "edge_cache",
            "Edge 网页媒体缓存 (仅 Cache)",
            "browser",
            la.join(r"Microsoft\Edge\User Data\Default\Cache"),
            false,
            "仅清理 Edge 网页缓存，保留所有账号与扩展数据。",
        ));
        candidates.push((
            "tabbit_cache",
            "Tabbit 浏览器缓存 (仅 Cache)",
            "browser",
            la.join(r"Tabbit\User Data\Default\Cache"),
            false,
            "仅清理 Tabbit 浏览器缓存，不触碰登录态与页面历史。",
        ));
    }

    if let Some(home) = dirs::home_dir() {
        let dot_cache = home.join(".cache");
        for (id, name, folder, desc) in [
            (
                "cache_codex",
                "开发缓存 · codex-runtimes",
                "codex-runtimes",
                "多版本 Codex 运行时缓存（如不再切回旧版本可释放约 2GB+）。",
            ),
            (
                "cache_puppeteer",
                "开发缓存 · puppeteer / 浏览器镜像",
                "puppeteer",
                "自动化测试下载的无头浏览器镜像缓存。",
            ),
            (
                "cache_hyperframes",
                "开发缓存 · hyperframes",
                "hyperframes",
                "视频渲染工具组件与缓存文件。",
            ),
            (
                "cache_chrome_mcp",
                "开发缓存 · chrome-devtools-mcp",
                "chrome-devtools-mcp",
                "Chrome MCP 调试工具缓存。",
            ),
        ] {
            let p = dot_cache.join(folder);
            if p.is_dir() {
                candidates.push((id, name, "dev_cache", p, false, desc));
            }
        }
    }

    candidates
        .into_iter()
        .filter(|(_, _, _, p, _, _)| p.is_dir())
        .map(|(id, name, group, path, default_checked, desc)| {
            let (bytes, count) = calc_dir_stats(&path, 8);
            let mb = ((bytes as f64) / (1024.0 * 1024.0) * 100.0).round() / 100.0;
            JunkCategoryItem {
                id: id.to_string(),
                name: name.to_string(),
                group: group.to_string(),
                path: path.to_string_lossy().to_string(),
                size_mb: mb,
                file_count: count,
                default_checked,
                description: desc.to_string(),
            }
        })
        .collect()
}

pub fn clean_junk_categories(category_ids: Vec<String>) -> CleanResult {
    let available = scan_junk_categories();
    let id_set: HashSet<String> = category_ids.into_iter().collect();
    let mut deleted_files = 0usize;
    let mut skipped_files = 0usize;
    let mut freed_bytes: u64 = 0;

    for item in available {
        if !id_set.contains(&item.id) {
            continue;
        }
        let target = PathBuf::from(&item.path);
        if is_dangerous_delete_path(&target) || !target.is_dir() {
            continue;
        }

        let mut dirs_to_prune = Vec::new();
        let mut stack = vec![target.clone()];
        while let Some(cur) = stack.pop() {
            let Ok(rd) = std::fs::read_dir(&cur) else {
                continue;
            };
            for entry in rd.flatten() {
                let Ok(ft) = entry.file_type() else {
                    continue;
                };
                if ft.is_symlink() {
                    continue;
                }
                let p = entry.path();
                if ft.is_file() {
                    let sz = entry.metadata().map(|m| m.len()).unwrap_or(0);
                    if std::fs::remove_file(&p).is_ok() {
                        deleted_files += 1;
                        freed_bytes = freed_bytes.saturating_add(sz);
                    } else {
                        skipped_files += 1;
                    }
                } else if ft.is_dir() {
                    dirs_to_prune.push(p.clone());
                    stack.push(p);
                }
            }
        }
        // 自底向上清理空目录
        for d in dirs_to_prune.into_iter().rev() {
            let _ = std::fs::remove_dir(d);
        }
    }

    let freed_mb = ((freed_bytes as f64) / (1024.0 * 1024.0) * 10.0).round() / 10.0;
    CleanResult {
        success: true,
        deleted_files,
        skipped_files,
        freed_mb,
        message: format!(
            "清理完成：删除 {} 个文件，释放 {:.1} MB（已自动跳过 {} 个占用中文件）",
            deleted_files, freed_mb, skipped_files
        ),
    }
}

pub fn scan_large_files(root_path: Option<String>, min_file_mb: Option<f64>) -> Result<LargeFileScanResult, String> {
    let root = match root_path.map(|s| s.trim().to_string()).filter(|s| !s.is_empty()) {
        Some(p) => PathBuf::from(p),
        None => dirs::home_dir().unwrap_or_else(|| PathBuf::from("C:\\")),
    };
    if !root.is_dir() {
        return Err(format!("扫描目录不存在: {}", root.display()));
    }

    let min_bytes = ((min_file_mb.unwrap_or(50.0)).max(5.0) * 1024.0 * 1024.0) as u64;
    let mut dirs_acc: Vec<(PathBuf, String, u64)> = Vec::new();
    let mut big_files: Vec<LargeFileEntry> = Vec::new();
    let mut total_bytes: u64 = 0;

    let rd = std::fs::read_dir(&root)
        .map_err(|e| format!("读取目录失败 {}: {}", root.display(), e))?;

    for entry in rd.flatten() {
        let Ok(ft) = entry.file_type() else {
            continue;
        };
        if ft.is_symlink() {
            continue;
        }
        let p = entry.path();
        let name = entry.file_name().to_string_lossy().to_string();
        if ft.is_file() {
            if let Ok(meta) = entry.metadata() {
                let sz = meta.len();
                total_bytes = total_bytes.saturating_add(sz);
                if sz >= min_bytes {
                    let mod_ts = meta
                        .modified()
                        .ok()
                        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                        .map(|d| d.as_secs())
                        .unwrap_or(0);
                    big_files.push(LargeFileEntry {
                        path: p.to_string_lossy().to_string(),
                        name: name.clone(),
                        size_mb: ((sz as f64) / (1024.0 * 1024.0) * 10.0).round() / 10.0,
                        ext: p
                            .extension()
                            .and_then(|e| e.to_str())
                            .unwrap_or("")
                            .to_ascii_uppercase(),
                        modified_ts: mod_ts,
                    });
                }
            }
        } else if ft.is_dir() {
            let lower = name.to_ascii_lowercase();
            if matches!(
                lower.as_str(),
                "windows" | "$recycle.bin" | "system volume information" | "winsxs"
            ) {
                continue;
            }
            let dir_bytes = scan_dir_with_large_files(&p, min_bytes, 5, &mut big_files);
            total_bytes = total_bytes.saturating_add(dir_bytes);
            if dir_bytes >= 20 * 1024 * 1024 {
                dirs_acc.push((p, name, dir_bytes));
            }
        }
    }

    dirs_acc.sort_by(|a, b| b.2.cmp(&a.2));
    dirs_acc.truncate(12);

    big_files.sort_by(|a, b| {
        b.size_mb
            .partial_cmp(&a.size_mb)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    big_files.truncate(30);

    let total_mb = ((total_bytes as f64) / (1024.0 * 1024.0) * 10.0).round() / 10.0;
    let directories = dirs_acc
        .into_iter()
        .map(|(p, name, bytes)| {
            let mb = ((bytes as f64) / (1024.0 * 1024.0) * 10.0).round() / 10.0;
            let pct = if total_bytes > 0 {
                ((bytes as f64 / total_bytes as f64) * 1000.0).round() as f32 / 10.0
            } else {
                0.0
            };
            LargeDirEntry {
                path: p.to_string_lossy().to_string(),
                name,
                size_mb: mb,
                percent: pct,
            }
        })
        .collect();

    Ok(LargeFileScanResult {
        root_path: root.to_string_lossy().to_string(),
        total_scanned_mb: total_mb,
        directories,
        files: big_files,
    })
}

fn scan_dir_with_large_files(
    dir: &Path,
    min_bytes: u64,
    max_depth: usize,
    out_files: &mut Vec<LargeFileEntry>,
) -> u64 {
    let mut total_bytes: u64 = 0;
    let mut stack = vec![(dir.to_path_buf(), 0usize)];
    while let Some((cur, depth)) = stack.pop() {
        let Ok(rd) = std::fs::read_dir(&cur) else {
            continue;
        };
        for entry in rd.flatten() {
            let Ok(ft) = entry.file_type() else {
                continue;
            };
            if ft.is_symlink() {
                continue;
            }
            let p = entry.path();
            if ft.is_file() {
                if let Ok(meta) = entry.metadata() {
                    let sz = meta.len();
                    total_bytes = total_bytes.saturating_add(sz);
                    if sz >= min_bytes {
                        let mod_ts = meta
                            .modified()
                            .ok()
                            .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                            .map(|d| d.as_secs())
                            .unwrap_or(0);
                        out_files.push(LargeFileEntry {
                            path: p.to_string_lossy().to_string(),
                            name: entry.file_name().to_string_lossy().to_string(),
                            size_mb: ((sz as f64) / (1024.0 * 1024.0) * 10.0).round() / 10.0,
                            ext: p
                                .extension()
                                .and_then(|e| e.to_str())
                                .unwrap_or("")
                                .to_ascii_uppercase(),
                            modified_ts: mod_ts,
                        });
                    }
                }
            } else if ft.is_dir() && depth < max_depth {
                stack.push((p, depth + 1));
            }
        }
    }
    total_bytes
}

pub fn handle_file_action(path_str: &str, action: &str) -> Result<String, String> {
    let path = PathBuf::from(path_str.trim());
    if !path.exists() {
        return Err("目标路径不存在".to_string());
    }
    match action {
        "reveal" => {
            win_native::reveal_in_explorer(&path)?;
            Ok("已在资源管理器中定位目标".to_string())
        }
        "trash" => {
            if is_dangerous_delete_path(&path) {
                return Err("安全拦截：禁止删除系统核心目录、软件安装目录或账号配置目录！".to_string());
            }
            win_native::move_to_recycle_bin(&path)?;
            Ok(format!("已安全移入回收站: {}", path.display()))
        }
        _ => Err(format!("不支持的文件操作: {}", action)),
    }
}

pub fn get_whitelist_snapshot() -> WhitelistSnapshot {
    let cfg = load_optimizer_config();
    let dynamic_tree_count = {
        let mut sys = sys_probe().lock().unwrap_or_else(|e| e.into_inner());
        sys.refresh_processes(sysinfo::ProcessesToUpdate::All);
        let proc_map = build_proc_tree_map(&sys);
        let self_pid = std::process::id();
        proc_map
            .keys()
            .filter(|&&pid| {
                classify_process_protection(pid, &proc_map, &cfg.custom_whitelist, self_pid)
                    == ProtectionKind::AntigravityTree
            })
            .count()
    };

    WhitelistSnapshot {
        system: SYSTEM_CRITICAL_PROCESSES
            .iter()
            .map(|s| s.to_string())
            .collect(),
        proxy: PROXY_WHITELIST.iter().map(|s| s.to_string()).collect(),
        antigravity: ANTIGRAVITY_WHITELIST
            .iter()
            .map(|s| s.to_string())
            .collect(),
        custom: cfg.custom_whitelist,
        dynamic_tree_count,
    }
}

pub fn update_custom_whitelist(items: Vec<String>) -> Result<WhitelistSnapshot, String> {
    let mut cfg = load_optimizer_config();
    let mut seen = HashSet::new();
    let mut cleaned = Vec::new();
    for raw in items {
        let norm = normalize_proc_name(&raw);
        if !norm.is_empty() && seen.insert(norm.clone()) {
            cleaned.push(norm);
        }
    }
    cfg.custom_whitelist = cleaned;
    save_optimizer_config(&cfg)?;

    if RUTHLESS_ACTIVE.load(Ordering::Relaxed) {
        if let Ok(mut sys) = sys_probe().lock() {
            sys.refresh_processes(sysinfo::ProcessesToUpdate::All);
            execute_ruthless_sweep(&sys, &cfg);
        }
    }

    Ok(get_whitelist_snapshot())
}

pub fn relaunch_as_admin() -> Result<bool, String> {
    win_native::relaunch_as_admin()
}

pub fn wait_for_pid_exit(pid: u32, timeout_ms: u32) {
    win_native::wait_for_pid_exit(pid, timeout_ms);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compute_affinity_masks_16_threads() {
        let (full, exile, label) = compute_affinity_masks(16);
        assert_eq!(full, 0xFFFF);
        assert_eq!(exile, 0xC000);
        assert!(label.contains("14-15"));
        assert!(label.contains("0-13"));
    }

    #[test]
    fn test_whitelist_process_tree_inheritance() {
        let mut map = HashMap::new();
        map.insert(100u32, (None, "explorer.exe".to_string()));
        map.insert(200u32, (Some(100), "Antigravity.exe".to_string()));
        map.insert(201u32, (Some(200), "msedgewebview2.exe".to_string()));
        map.insert(300u32, (Some(100), "SearchHost.exe".to_string()));
        map.insert(301u32, (Some(300), "msedgewebview2.exe".to_string()));
        map.insert(400u32, (Some(100), "FlClash.exe".to_string()));
        map.insert(401u32, (Some(400), "FlClashCore.exe".to_string()));
        map.insert(500u32, (Some(100), "Tabbit Browser.exe".to_string()));
        map.insert(501u32, (Some(100), "MyGame.exe".to_string()));

        let custom = vec!["mygame".to_string()];
        let self_pid = 99999;

        assert_eq!(
            classify_process_protection(200, &map, &custom, self_pid),
            ProtectionKind::Antigravity
        );
        // Antigravity 子树内的 WebView2 自动继承免杀
        assert_eq!(
            classify_process_protection(201, &map, &custom, self_pid),
            ProtectionKind::AntigravityTree
        );
        // SearchHost 拉起的 WebView2 不在白名单树中，可压榨
        assert_eq!(
            classify_process_protection(301, &map, &custom, self_pid),
            ProtectionKind::None
        );
        // FlClash 家族免杀
        assert_eq!(
            classify_process_protection(400, &map, &custom, self_pid),
            ProtectionKind::Proxy
        );
        assert_eq!(
            classify_process_protection(401, &map, &custom, self_pid),
            ProtectionKind::Proxy
        );
        // Tabbit 可压榨
        assert_eq!(
            classify_process_protection(500, &map, &custom, self_pid),
            ProtectionKind::None
        );
        // 自定义白名单生效
        assert_eq!(
            classify_process_protection(501, &map, &custom, self_pid),
            ProtectionKind::Custom
        );
    }

    #[test]
    fn test_dangerous_delete_path_guard() {
        assert!(is_dangerous_delete_path(Path::new(r"C:\")));
        assert!(is_dangerous_delete_path(Path::new(r"C:\Windows\System32")));
        assert!(is_dangerous_delete_path(Path::new(r"C:\Program Files\FlClash")));
        assert!(is_dangerous_delete_path(Path::new(r"E:\antigravity-cn\src")));
        assert!(!is_dangerous_delete_path(Path::new(r"C:\Windows\Temp")));
        assert!(!is_dangerous_delete_path(Path::new(r"C:\Users\Test\Downloads\big.iso")));
    }
}
