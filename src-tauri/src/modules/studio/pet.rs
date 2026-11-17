use base64::{engine::general_purpose::STANDARD as BASE64_STANDARD, Engine as _};
use serde_json::{json, Value};
use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};
use tauri::{Emitter, LogicalSize, Manager, PhysicalPosition, Size};

use super::skin_manager::{load_studio_config, mutate_studio_config, MAX_IMAGE_BYTES};
use super::{atomic_write_bytes, config_dir, resources_dir, MediaStatus, PetAssets};

#[derive(Default)]
struct LyricCache {
    key: String,
    lrc: String,
}

static LYRIC_CACHE: OnceLock<Mutex<LyricCache>> = OnceLock::new();
static BUILTIN_PET_ASSETS_CACHE: OnceLock<PetAssets> = OnceLock::new();

fn lyric_cache() -> &'static Mutex<LyricCache> {
    LYRIC_CACHE.get_or_init(|| Mutex::new(LyricCache::default()))
}

fn custom_pet_dir() -> PathBuf {
    config_dir().join("custom-pet")
}

fn mime_for_image_ext(ext: &str) -> Option<&'static str> {
    match ext.to_ascii_lowercase().as_str() {
        "png" => Some("image/png"),
        "webp" => Some("image/webp"),
        "gif" => Some("image/gif"),
        "svg" => Some("image/svg+xml"),
        "jpg" | "jpeg" => Some("image/jpeg"),
        "avif" => Some("image/avif"),
        _ => None,
    }
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

fn read_voice_data_uris() -> std::collections::HashMap<String, String> {
    let mut map = std::collections::HashMap::new();
    let vdir = resources_dir().join("media").join("voices");
    let Ok(entries) = std::fs::read_dir(&vdir) else {
        return map;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let ext = path
            .extension()
            .and_then(|e| e.to_str())
            .unwrap_or("")
            .to_ascii_lowercase();
        let mime = match ext.as_str() {
            "mp3" => "audio/mpeg",
            "ogg" => "audio/ogg",
            "wav" => "audio/wav",
            _ => continue,
        };
        let Some(stem) = path.file_stem().and_then(|s| s.to_str()) else {
            continue;
        };
        if let Ok(bytes) = std::fs::read(&path) {
            map.insert(
                stem.to_string(),
                format!("data:{};base64,{}", mime, BASE64_STANDARD.encode(&bytes)),
            );
        }
    }
    map
}

fn read_custom_avatar_data_uri() -> Option<String> {
    let cfg = load_studio_config();
    if let Some(ref saved_path) = cfg.custom_pet_avatar {
        let p = PathBuf::from(saved_path);
        if p.is_file() {
            let ext = p.extension().and_then(|e| e.to_str()).unwrap_or("");
            if let Some(mime) = mime_for_image_ext(ext) {
                if let Ok(bytes) = std::fs::read(&p) {
                    if bytes.len() <= MAX_IMAGE_BYTES {
                        return Some(format!(
                            "data:{};base64,{}",
                            mime,
                            BASE64_STANDARD.encode(&bytes)
                        ));
                    }
                }
            }
        }
    }
    let dir = custom_pet_dir();
    for ext in ["webp", "png", "gif", "svg", "jpg", "jpeg"] {
        let p = dir.join(format!("avatar.{}", ext));
        if p.is_file() {
            if let Some(mime) = mime_for_image_ext(ext) {
                if let Ok(bytes) = std::fs::read(&p) {
                    if bytes.len() <= MAX_IMAGE_BYTES {
                        return Some(format!(
                            "data:{};base64,{}",
                            mime,
                            BASE64_STANDARD.encode(&bytes)
                        ));
                    }
                }
            }
        }
    }
    None
}

/// 打包加载桌宠全部 WebP/PNG/SVG 动态材质（内置资产进程级缓存 + 用户自定义立绘热加载）
pub fn get_pet_assets() -> PetAssets {
    let base = BUILTIN_PET_ASSETS_CACHE
        .get_or_init(|| PetAssets {
            nezuko_chibi: read_media_data_uri("nezuko_chibi_pet"),
            nezuko_blink: read_media_data_uri("nezuko_chibi_blink"),
            nezuko_happy: read_media_data_uri("nezuko_action_happy"),
            nezuko_run: read_media_data_uri("nezuko_action_run"),
            nezuko_stomp: read_media_data_uri("nezuko_action_stomp"),
            nezuko_blood: read_media_data_uri("nezuko_action_blood"),
            nezuko_basket: read_media_data_uri("nezuko_basket"),
            nezuko_spin_sheet: read_media_data_uri("nezuko_box_spin_sheet"),
            shockwave: read_media_data_uri("box_impact_shockwave"),
            nezuko_peeker: read_media_data_uri("nezuko_peeker_head"),
            little_prince: read_media_data_uri("little_prince_pet"),
            prince_blink: read_media_data_uri("little_prince_blink"),
            prince_walk: read_media_data_uri("prince_action_walk"),
            prince_fox: read_media_data_uri("prince_action_fox"),
            prince_rose_pose: read_media_data_uri("prince_action_rose"),
            prince_sleep: read_media_data_uri("prince_action_sleep"),
            ushio_chibi: read_media_data_uri("ushio_chibi_pet"),
            ushio_blink: read_media_data_uri("ushio_chibi_blink"),
            ushio_happy: read_media_data_uri("ushio_action_happy"),
            ushio_walk: read_media_data_uri("ushio_action_walk"),
            ushio_sunflower: read_media_data_uri("ushio_action_sunflower"),
            ushio_sleep: read_media_data_uri("ushio_action_sleep"),
            tanjiro_water: read_media_data_uri("tanjiro_water"),
            zenitsu_thunder: read_media_data_uri("zenitsu_thunder"),
            inosuke_beast: read_media_data_uri("inosuke_beast"),
            custom_avatar: None,
            voices: read_voice_data_uris(),
        })
        .clone();

    PetAssets {
        custom_avatar: read_custom_avatar_data_uri(),
        ..base
    }
}

/// 导入用户自定义桌宠形象资产（支持 PNG / WebP / GIF / SVG / JPG）并即时同步至伴侣视窗
pub fn import_custom_pet_avatar(app: &tauri::AppHandle, src_path: &Path) -> Result<String, String> {
    if !src_path.is_file() {
        return Err(format!("未找到所选形象文件: {}", src_path.display()));
    }
    let ext = src_path
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_ascii_lowercase();
    let mime = mime_for_image_ext(&ext)
        .ok_or_else(|| "仅支持导入 PNG、WebP、GIF、SVG 或 JPG 格式的立绘资产".to_string())?;

    let meta = std::fs::metadata(src_path)
        .map_err(|e| format!("读取文件信息失败: {}", e))?;
    if meta.len() == 0 {
        return Err("所选图片文件为空".to_string());
    }
    if meta.len() as usize > MAX_IMAGE_BYTES {
        return Err("自定义立绘文件不能超过 8MB".to_string());
    }

    let bytes = std::fs::read(src_path)
        .map_err(|e| format!("读取自定义立绘失败: {}", e))?;
    let dir = custom_pet_dir();
    std::fs::create_dir_all(&dir)
        .map_err(|e| format!("创建自定义伴侣目录失败: {}", e))?;

    // 清理旧扩展名头像残留
    for old_ext in ["webp", "png", "gif", "svg", "jpg", "jpeg"] {
        if old_ext != ext {
            let old_file = dir.join(format!("avatar.{}", old_ext));
            if old_file.exists() {
                let _ = std::fs::remove_file(old_file);
            }
        }
    }

    let dst = dir.join(format!("avatar.{}", ext));
    atomic_write_bytes(&dst, &bytes)?;
    let dst_str = dst.to_string_lossy().to_string();

    mutate_studio_config(|cfg| {
        cfg.custom_pet_avatar = Some(dst_str.clone());
        cfg.pet_character = "custom".to_string();
    })?;

    let data_uri = format!("data:{};base64,{}", mime, BASE64_STANDARD.encode(&bytes));
    let _ = app.emit("pet:assets-updated", ());
    let _ = app.emit("pet:character-changed", "custom");
    let _ = app.emit(
        "studio:pet-state-changed",
        json!({ "open": is_pet_open(app), "character": "custom" }),
    );
    Ok(data_uri)
}

/// 清除用户自定义立绘并回退至灶门祢豆子
pub fn clear_custom_pet_avatar(app: &tauri::AppHandle) -> Result<(), String> {
    let dir = custom_pet_dir();
    if dir.is_dir() {
        let _ = std::fs::remove_dir_all(&dir);
    }
    mutate_studio_config(|cfg| {
        cfg.custom_pet_avatar = None;
        if cfg.pet_character == "custom" {
            cfg.pet_character = "nezuko".to_string();
        }
    })?;
    let next_ch = load_studio_config().pet_character;
    let _ = app.emit("pet:assets-updated", ());
    let _ = app.emit("pet:character-changed", next_ch.clone());
    let _ = app.emit(
        "studio:pet-state-changed",
        json!({ "open": is_pet_open(app), "character": next_ch }),
    );
    Ok(())
}

/// 持久化更新桌宠交互偏好并在主窗口与伴侣窗口间实时同步
pub fn update_pet_prefs(
    app: &tauri::AppHandle,
    character: Option<String>,
    roaming: Option<bool>,
    always_on_top: Option<bool>,
    scale_idx: Option<usize>,
    muted: Option<bool>,
) -> Result<(), String> {
    let updated = mutate_studio_config(|cfg| {
        if let Some(ref ch) = character {
            let t = ch.trim();
            if !t.is_empty() {
                cfg.pet_character = t.to_string();
            }
        }
        if let Some(r) = roaming {
            cfg.pet_roaming = r;
        }
        if let Some(top) = always_on_top {
            cfg.pet_always_on_top = top;
        }
        if let Some(s) = scale_idx {
            cfg.pet_scale_idx = s.min(2);
        }
        if let Some(m) = muted {
            cfg.pet_muted = m;
        }
    })?;

    if let Some(top) = always_on_top {
        let _ = set_pet_always_on_top(app, top);
    }
    if let Some(ch) = character {
        let t = ch.trim();
        if !t.is_empty() {
            let _ = app.emit("pet:character-changed", t);
        }
    }
    let _ = app.emit(
        "studio:pet-state-changed",
        json!({
            "open": is_pet_open(app),
            "character": updated.pet_character,
            "roaming": updated.pet_roaming,
            "always_on_top": updated.pet_always_on_top,
            "scale_idx": updated.pet_scale_idx,
            "muted": updated.pet_muted,
        }),
    );
    Ok(())
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
            .unwrap_or(tauri::PhysicalSize::new(386, 420));
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
    let cfg = mutate_studio_config(|c| {
        if let Some(ch) = character.map(str::trim).filter(|s| !s.is_empty()) {
            c.pet_character = ch.to_string();
        }
        c.enable_pet = true;
    })?;

    let win = if let Some(w) = app.get_webview_window("pet") {
        w
    } else {
        let built = tauri::WebviewWindowBuilder::new(
            app,
            "pet",
            tauri::WebviewUrl::App("index.html?pet=1".into()),
        )
        .title("Antigravity 独立桌面伴侣")
        .inner_size(386.0, 420.0)
        .transparent(true)
        .decorations(false)
        .always_on_top(cfg.pet_always_on_top)
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
    let _ = win.set_always_on_top(cfg.pet_always_on_top);
    win.show()
        .map_err(|e| format!("显示独立桌宠窗口失败: {}", e))?;
    let _ = win.set_focus();

    let active_ch = cfg.pet_character.clone();
    let _ = app.emit("pet:character-changed", active_ch.as_str());
    let _ = app.emit(
        "studio:pet-state-changed",
        json!({
            "open": true,
            "character": active_ch,
            "always_on_top": cfg.pet_always_on_top,
        }),
    );

    Ok(true)
}

pub fn close_pet_window(app: &tauri::AppHandle) -> Result<bool, String> {
    if let Some(win) = app.get_webview_window("pet") {
        win.hide()
            .map_err(|e| format!("隐藏独立桌宠窗口失败: {}", e))?;
    }
    let cfg = mutate_studio_config(|c| {
        c.enable_pet = false;
    })
    .unwrap_or_default();
    let _ = app.emit(
        "studio:pet-state-changed",
        json!({
            "open": false,
            "character": cfg.pet_character,
            "always_on_top": cfg.pet_always_on_top,
        }),
    );
    Ok(false)
}

pub fn reset_pet_position(app: &tauri::AppHandle) -> Result<(), String> {
    if let Some(win) = app.get_webview_window("pet") {
        position_bottom_right(&win);
        let _ = win.show();
    }
    Ok(())
}

/// 调整桌宠窗口逻辑尺寸，同时锚定窗口底边位置并夹取在屏幕工作区内（彻底消除展开遥测面板穿出任务栏的 Bug）
pub fn set_pet_size(app: &tauri::AppHandle, width: u32, height: u32) -> Result<(), String> {
    if let Some(win) = app.get_webview_window("pet") {
        let w = width.clamp(220, 720) as f64;
        let h = height.clamp(220, 780) as f64;

        let old_pos = win.outer_position().ok();
        let old_size = win.outer_size().ok();
        let monitor = win.current_monitor().ok().flatten();
        let scale = monitor
            .as_ref()
            .map(|m| m.scale_factor())
            .or_else(|| win.scale_factor().ok())
            .unwrap_or(1.0);

        win.set_size(Size::Logical(LogicalSize::new(w, h)))
            .map_err(|e| format!("调整桌宠窗口大小失败: {}", e))?;

        if let (Some(pos), Some(old_sz)) = (old_pos, old_size) {
            let new_phys_w = (w * scale).round() as i32;
            let new_phys_h = (h * scale).round() as i32;
            let bottom_anchor = pos.y + old_sz.height as i32;
            let mut next_x = pos.x;
            let mut next_y = bottom_anchor - new_phys_h;

            if let Some(mon) = monitor {
                let area = mon.work_area();
                let min_x = area.position.x + 8;
                let max_x = (area.position.x + area.size.width as i32 - new_phys_w - 8).max(min_x);
                let min_y = area.position.y + 8;
                let max_y = (area.position.y + area.size.height as i32 - new_phys_h - 8).max(min_y);
                next_x = next_x.clamp(min_x, max_x);
                next_y = next_y.clamp(min_y, max_y);
            }
            let _ = win.set_position(PhysicalPosition::new(next_x, next_y));
        }
    }
    Ok(())
}

pub fn set_pet_always_on_top(app: &tauri::AppHandle, always_on_top: bool) -> Result<(), String> {
    let _ = mutate_studio_config(|c| {
        c.pet_always_on_top = always_on_top;
    });
    if let Some(win) = app.get_webview_window("pet") {
        win.set_always_on_top(always_on_top)
            .map_err(|e| format!("设置桌宠置顶失败: {}", e))?;
    }
    let _ = app.emit(
        "studio:pet-state-changed",
        json!({
            "open": is_pet_open(app),
            "always_on_top": always_on_top,
        }),
    );
    Ok(())
}

/// 沿屏幕工作区底边平滑步进移动桌宠窗口；到达边缘时返回反向信号 (`1` 向右 / `-1` 向左 / `0` 未碰边)
pub fn nudge_pet_window(app: &tauri::AppHandle, dx: i32) -> Result<i32, String> {
    let Some(win) = app.get_webview_window("pet") else {
        return Ok(0);
    };
    let Ok(Some(monitor)) = win.current_monitor() else {
        return Ok(0);
    };
    let area = monitor.work_area();
    let pos = win
        .outer_position()
        .unwrap_or(PhysicalPosition::new(area.position.x, area.position.y));
    let win_size = win
        .outer_size()
        .unwrap_or(tauri::PhysicalSize::new(360, 440));
    let margin = 12i32;
    let min_x = area.position.x + margin;
    let max_x = (area.position.x + area.size.width as i32 - win_size.width as i32 - margin).max(min_x);
    let next_raw = pos.x + dx;
    let clamped_x = next_raw.clamp(min_x, max_x);
    let _ = win.set_position(PhysicalPosition::new(clamped_x, pos.y));
    if next_raw <= min_x {
        Ok(1)
    } else if next_raw >= max_x {
        Ok(-1)
    } else {
        Ok(0)
    }
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
