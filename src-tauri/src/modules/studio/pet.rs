use base64::{engine::general_purpose::STANDARD as BASE64_STANDARD, Engine as _};
use serde_json::Value;
use std::sync::{Mutex, OnceLock};
use tauri::{Emitter, LogicalSize, Manager, PhysicalPosition, Size};

use super::skin_manager::{load_studio_config, save_studio_config};
use super::{resources_dir, MediaStatus, PetAssets};

#[derive(Default)]
struct LyricCache {
    key: String,
    lrc: String,
}

static LYRIC_CACHE: OnceLock<Mutex<LyricCache>> = OnceLock::new();

fn lyric_cache() -> &'static Mutex<LyricCache> {
    LYRIC_CACHE.get_or_init(|| Mutex::new(LyricCache::default()))
}

fn read_media_data_uri(stem: &str) -> Option<String> {
    let mdir = resources_dir().join("media");
    for (ext, mime) in [("webp", "image/webp"), ("png", "image/png")] {
        let p = mdir.join(format!("{}.{}", stem, ext));
        if p.is_file() {
            if let Ok(bytes) = std::fs::read(&p) {
                return Some(format!(
                    "data:{};base64,{}",
                    mime,
                    BASE64_STANDARD.encode(&bytes)
                ));
            }
        }
    }
    None
}

/// 打包加载桌宠全部 WebP/PNG 动态材质，封装为 Data URI 返回给透明桌宠窗口
pub fn get_pet_assets() -> PetAssets {
    PetAssets {
        nezuko_chibi: read_media_data_uri("nezuko_chibi_pet"),
        nezuko_basket: read_media_data_uri("nezuko_basket"),
        nezuko_spin_sheet: read_media_data_uri("nezuko_box_spin_sheet"),
        shockwave: read_media_data_uri("box_impact_shockwave"),
        little_prince: read_media_data_uri("little_prince_pet"),
        prince_fox: read_media_data_uri("prince_action_fox"),
        prince_rose: read_media_data_uri("prince_asset_rose"),
        prince_stars: read_media_data_uri("prince_asset_stars"),
        prince_sunset: read_media_data_uri("prince_asset_sunset"),
    }
}

pub fn is_pet_open(app: &tauri::AppHandle) -> bool {
    app.get_webview_window("pet")
        .and_then(|w| w.is_visible().ok())
        .unwrap_or(false)
}

fn position_bottom_right(win: &tauri::WebviewWindow) {
    if let Ok(Some(monitor)) = win.current_monitor() {
        let area = monitor.work_area();
        let win_size = win
            .outer_size()
            .unwrap_or(tauri::PhysicalSize::new(360, 440));
        let margin = 20i32;
        let x = area.position.x + area.size.width as i32 - win_size.width as i32 - margin;
        let y = area.position.y + area.size.height as i32 - win_size.height as i32 - margin;
        let _ = win.set_position(PhysicalPosition::new(x.max(area.position.x), y.max(area.position.y)));
    }
}

pub fn launch_pet_window(
    app: &tauri::AppHandle,
    character: Option<&str>,
) -> Result<bool, String> {
    if let Some(ch) = character.map(str::trim).filter(|s| !s.is_empty()) {
        let mut cfg = load_studio_config();
        cfg.pet_character = ch.to_string();
        let _ = save_studio_config(&cfg);
    }

    let win = if let Some(w) = app.get_webview_window("pet") {
        w
    } else {
        let built = tauri::WebviewWindowBuilder::new(
            app,
            "pet",
            tauri::WebviewUrl::App("index.html?pet=1".into()),
        )
        .title("Antigravity 桌宠伴侣")
        .inner_size(360.0, 460.0)
        .transparent(true)
        .decorations(false)
        .always_on_top(true)
        .skip_taskbar(true)
        .resizable(false)
        .shadow(false)
        .build()
        .map_err(|e| format!("创建独立桌宠窗口失败: {}", e))?;
        position_bottom_right(&built);
        built
    };

    if !win.is_visible().unwrap_or(false) {
        position_bottom_right(&win);
    }
    let _ = win.set_always_on_top(true);
    win.show()
        .map_err(|e| format!("显示独立桌宠窗口失败: {}", e))?;
    let _ = win.set_focus();

    if let Some(ch) = character.map(str::trim).filter(|s| !s.is_empty()) {
        let _ = app.emit_to("pet", "pet:character-changed", ch);
    }

    Ok(true)
}

pub fn close_pet_window(app: &tauri::AppHandle) -> Result<bool, String> {
    if let Some(win) = app.get_webview_window("pet") {
        win.hide()
            .map_err(|e| format!("隐藏独立桌宠窗口失败: {}", e))?;
    }
    Ok(false)
}

pub fn reset_pet_position(app: &tauri::AppHandle) -> Result<(), String> {
    if let Some(win) = app.get_webview_window("pet") {
        position_bottom_right(&win);
        let _ = win.show();
    }
    Ok(())
}

pub fn set_pet_size(app: &tauri::AppHandle, width: u32, height: u32) -> Result<(), String> {
    if let Some(win) = app.get_webview_window("pet") {
        let w = width.clamp(220, 720) as f64;
        let h = height.clamp(220, 780) as f64;
        win.set_size(Size::Logical(LogicalSize::new(w, h)))
            .map_err(|e| format!("调整桌宠窗口大小失败: {}", e))?;
    }
    Ok(())
}

pub fn set_pet_always_on_top(app: &tauri::AppHandle, always_on_top: bool) -> Result<(), String> {
    if let Some(win) = app.get_webview_window("pet") {
        win.set_always_on_top(always_on_top)
            .map_err(|e| format!("设置桌宠置顶失败: {}", e))?;
    }
    Ok(())
}

#[cfg(target_os = "windows")]
mod win32_media {
    use std::ffi::OsStr;
    use std::os::windows::ffi::OsStrExt;

    #[link(name = "user32")]
    extern "system" {
        fn FindWindowW(lp_class_name: *const u16, lp_window_name: *const u16) -> isize;
        fn GetWindowTextLengthW(h_wnd: isize) -> i32;
        fn GetWindowTextW(h_wnd: isize, lp_string: *mut u16, n_max_count: i32) -> i32;
        fn GetClassNameW(h_wnd: isize, lp_class_name: *mut u16, n_max_count: i32) -> i32;
        fn EnumWindows(
            lp_enum_func: unsafe extern "system" fn(isize, isize) -> i32,
            l_param: isize,
        ) -> i32;
        fn keybd_event(b_vk: u8, b_scan: u8, dw_flags: u32, dw_extra_info: usize);
    }

    fn to_wide(s: &str) -> Vec<u16> {
        OsStr::new(s)
            .encode_wide()
            .chain(std::iter::once(0))
            .collect()
    }

    fn read_window_title(hwnd: isize) -> String {
        if hwnd == 0 {
            return String::new();
        }
        unsafe {
            let len = GetWindowTextLengthW(hwnd);
            if len <= 0 || len > 512 {
                return String::new();
            }
            let mut buf = vec![0u16; (len + 1) as usize];
            let copied = GetWindowTextW(hwnd, buf.as_mut_ptr(), buf.len() as i32);
            if copied <= 0 {
                return String::new();
            }
            String::from_utf16_lossy(&buf[..copied as usize])
                .trim()
                .to_string()
        }
    }

    fn read_class_name(hwnd: isize) -> String {
        unsafe {
            let mut buf = [0u16; 128];
            let copied = GetClassNameW(hwnd, buf.as_mut_ptr(), buf.len() as i32);
            if copied <= 0 {
                return String::new();
            }
            String::from_utf16_lossy(&buf[..copied as usize])
        }
    }

    struct EnumState {
        found_title: String,
        found_source: String,
    }

    unsafe extern "system" fn enum_cb(hwnd: isize, lparam: isize) -> i32 {
        let state = &mut *(lparam as *mut EnumState);
        let cls = read_class_name(hwnd);
        if cls.contains("QQMusic") || cls == "OrpheusBrowserHost" || cls.contains("CloudMusic") {
            let title = read_window_title(hwnd);
            if title.contains(" - ") && title != "QQ音乐" && title != "网易云音乐" {
                state.found_title = title;
                state.found_source = if cls.contains("QQMusic") {
                    "QQ音乐".to_string()
                } else {
                    "网易云音乐".to_string()
                };
                return 0;
            }
        }
        1
    }

    pub fn detect_player_title() -> Option<(String, String)> {
        let qq_cls = to_wide("QQMusic_Daemon_Wnd");
        let hwnd = unsafe { FindWindowW(qq_cls.as_ptr(), std::ptr::null()) };
        if hwnd != 0 {
            let title = read_window_title(hwnd);
            if !title.is_empty() && title != "QQ音乐" && title != "QQMusic" {
                return Some((title, "QQ音乐".to_string()));
            }
        }

        let mut state = EnumState {
            found_title: String::new(),
            found_source: String::new(),
        };
        unsafe {
            EnumWindows(enum_cb, &mut state as *mut EnumState as isize);
        }
        if !state.found_title.is_empty() {
            return Some((state.found_title, state.found_source));
        }
        None
    }

    pub fn trigger_media_vk(vk: u8) {
        const KEYEVENTF_EXTENDEDKEY: u32 = 0x0001;
        const KEYEVENTF_KEYUP: u32 = 0x0002;
        unsafe {
            keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY, 0);
            keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0);
        }
    }
}

fn parse_track_artist(raw_title: &str) -> (String, String) {
    if let Some((left, right)) = raw_title.split_once(" - ") {
        (left.trim().to_string(), right.trim().to_string())
    } else if let Some((left, right)) = raw_title.split_once(" — ") {
        (left.trim().to_string(), right.trim().to_string())
    } else {
        (raw_title.trim().to_string(), String::new())
    }
}

async fn fetch_kugou_lrc(keyword: &str) -> String {
    {
        if let Ok(cache) = lyric_cache().lock() {
            if cache.key == keyword {
                return cache.lrc.clone();
            }
        }
    }

    let client = match reqwest::Client::builder()
        .timeout(std::time::Duration::from_millis(2500))
        .user_agent("Antigravity-Studio/5.0")
        .build()
    {
        Ok(c) => c,
        Err(_) => return String::new(),
    };

    let search_res = client
        .get("https://krcs.kugou.com/search")
        .query(&[
            ("ver", "1"),
            ("man", "yes"),
            ("client", "mobi"),
            ("keyword", keyword),
            ("duration", "-1"),
            ("hash", ""),
        ])
        .send()
        .await;

    let Ok(resp) = search_res else {
        return String::new();
    };
    let Ok(json_val) = resp.json::<Value>().await else {
        return String::new();
    };
    let Some(first) = json_val
        .get("candidates")
        .and_then(|v| v.as_array())
        .and_then(|a| a.first())
    else {
        return String::new();
    };

    let id = first
        .get("id")
        .and_then(|v| v.as_str().map(|s| s.to_string()).or_else(|| v.as_u64().map(|n| n.to_string())))
        .unwrap_or_default();
    let accesskey = first
        .get("accesskey")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();
    if id.is_empty() || accesskey.is_empty() {
        return String::new();
    }

    let dl_res = client
        .get("https://lyrics.kugou.com/download")
        .query(&[
            ("ver", "1"),
            ("client", "pc"),
            ("id", id.as_str()),
            ("accesskey", accesskey.as_str()),
            ("fmt", "lrc"),
            ("charset", "utf8"),
        ])
        .send()
        .await;

    let Ok(dl_resp) = dl_res else {
        return String::new();
    };
    let Ok(dl_json) = dl_resp.json::<Value>().await else {
        return String::new();
    };
    let b64 = dl_json
        .get("content")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    let lrc = BASE64_STANDARD
        .decode(b64.as_bytes())
        .ok()
        .and_then(|bytes| String::from_utf8(bytes).ok())
        .unwrap_or_default();

    if let Ok(mut cache) = lyric_cache().lock() {
        cache.key = keyword.to_string();
        cache.lrc = lrc.clone();
    }
    lrc
}

/// 读取当前本机音乐播放器状态及匹配歌词
pub async fn get_media_status() -> MediaStatus {
    #[cfg(target_os = "windows")]
    let detected = tokio::task::spawn_blocking(win32_media::detect_player_title)
        .await
        .ok()
        .flatten();

    #[cfg(not(target_os = "windows"))]
    let detected: Option<(String, String)> = None;

    let Some((raw_title, source)) = detected else {
        return MediaStatus {
            is_playing: false,
            title: String::new(),
            artist: String::new(),
            raw_title: String::new(),
            source: String::new(),
            lrc: String::new(),
        };
    };

    let (title, artist) = parse_track_artist(&raw_title);
    let lrc = fetch_kugou_lrc(&raw_title).await;

    MediaStatus {
        is_playing: true,
        title,
        artist,
        raw_title,
        source,
        lrc,
    }
}

/// 发送跨平台媒体控制按键（上一曲/下一曲/播放暂停/音量调节）
pub fn send_media_command(cmd: &str) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        let vk = match cmd {
            "play_pause" => 0xB3u8, // VK_MEDIA_PLAY_PAUSE
            "next" => 0xB0u8,       // VK_MEDIA_NEXT_TRACK
            "prev" => 0xB1u8,       // VK_MEDIA_PREV_TRACK
            "vol_up" => 0xAFu8,     // VK_VOLUME_UP
            "vol_down" => 0xAEu8,   // VK_VOLUME_DOWN
            other => return Err(format!("不支持的媒体指令 '{}'", other)),
        };
        win32_media::trigger_media_vk(vk);
        return Ok(());
    }

    #[cfg(not(target_os = "windows"))]
    {
        #[cfg(target_os = "macos")]
        {
            let script = match cmd {
                "play_pause" => "tell application \"Music\" to playpause",
                "next" => "tell application \"Music\" to next track",
                "prev" => "tell application \"Music\" to previous track",
                _ => return Ok(()),
            };
            let _ = std::process::Command::new("osascript")
                .args(["-e", script])
                .output();
            return Ok(());
        }
        #[cfg(all(not(target_os = "windows"), not(target_os = "macos")))]
        {
            let arg = match cmd {
                "play_pause" => "play-pause",
                "next" => "next",
                "prev" => "previous",
                _ => return Ok(()),
            };
            let _ = std::process::Command::new("playerctl").arg(arg).output();
            return Ok(());
        }
    }
}
