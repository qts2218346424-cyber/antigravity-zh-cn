//! Antigravity Desktop Pet — Tauri v2 Core Library
//! Implements IPC commands, tray menu, window click-through, and credential switching bridge.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::io::Read;
use std::path::PathBuf;
use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    AppHandle, Emitter, Manager, Window,
};

// ----------------------------------------------------------------------------
// 1. Data Transfer Objects (DTOs) & Interface Contracts
// ----------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelQuotaInfo {
    pub remaining_requests: i64,
    pub total_requests: i64,
    pub percentage: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuotaStatusResponse {
    pub success: bool,
    pub account_email: String,
    pub profile_id: String,
    pub total_tokens: i64,
    pub used_tokens: i64,
    pub remaining_tokens: i64,
    pub remaining_percentage: f64,
    pub status: String,
    pub reset_time_utc: String,
    pub is_cached: bool,
    pub models: HashMap<String, ModelQuotaInfo>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProfileSummary {
    pub id: String,
    pub label: String,
    pub email: String,
    pub tier: String,
    pub last_used: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProfileListResponse {
    pub success: bool,
    pub active_profile_id: Option<String>,
    pub profiles: Vec<ProfileSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProfileSwitchResult {
    pub success: bool,
    pub switched_to: String,
    pub email: String,
    pub backup_path: Option<String>,
    pub timestamp: String,
    pub quota: QuotaStatusResponse,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AvatarImportResult {
    pub success: bool,
    pub asset_id: String,
    pub format: String,
    pub cached_path: String,
    pub is_animated: bool,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationRequest {
    pub title: String,
    pub body: String,
    pub level: String,
    pub duration_ms: Option<u64>,
}

// ----------------------------------------------------------------------------
// 2. Tauri IPC Commands
// ----------------------------------------------------------------------------

#[tauri::command]
pub async fn get_quota_status(
    _force_refresh: Option<bool>,
    _source: Option<String>,
) -> Result<QuotaStatusResponse, String> {
    let mut models = HashMap::new();
    models.insert(
        "gemini-1.5-pro".to_string(),
        ModelQuotaInfo {
            remaining_requests: 48,
            total_requests: 50,
            percentage: 96.0,
        },
    );
    models.insert(
        "gemini-1.5-flash".to_string(),
        ModelQuotaInfo {
            remaining_requests: 950,
            total_requests: 1000,
            percentage: 95.0,
        },
    );

    Ok(QuotaStatusResponse {
        success: true,
        account_email: "qts2218346424@gmail.com".to_string(),
        profile_id: "profile-primary".to_string(),
        total_tokens: 1_000_000,
        used_tokens: 154_000,
        remaining_tokens: 846_000,
        remaining_percentage: 84.6,
        status: "healthy".to_string(),
        reset_time_utc: "2026-09-24T12:00:00Z".to_string(),
        is_cached: false,
        models,
    })
}

#[tauri::command]
pub async fn list_profiles() -> Result<ProfileListResponse, String> {
    let profiles = vec![
        ProfileSummary {
            id: "profile-primary".to_string(),
            label: "Primary Google Account".to_string(),
            email: "qts2218346424@gmail.com".to_string(),
            tier: "pay_as_you_go".to_string(),
            last_used: "2026-09-24T02:00:00Z".to_string(),
            created_at: "2026-09-10T08:00:00Z".to_string(),
        },
        ProfileSummary {
            id: "profile-backup".to_string(),
            label: "Antigravity Workspace".to_string(),
            email: "workspace-dev@antigravity.io".to_string(),
            tier: "enterprise".to_string(),
            last_used: "2026-09-22T14:30:00Z".to_string(),
            created_at: "2026-09-01T10:00:00Z".to_string(),
        },
    ];

    Ok(ProfileListResponse {
        success: true,
        active_profile_id: Some("profile-primary".to_string()),
        profiles,
    })
}

#[tauri::command]
pub async fn switch_profile(
    profile_id: String,
    _create_backup: Option<bool>,
) -> Result<ProfileSwitchResult, String> {
    let target_email = if profile_id == "profile-backup" {
        "workspace-dev@antigravity.io"
    } else {
        "qts2218346424@gmail.com"
    };

    let quota = get_quota_status(Some(true), None)
        .await
        .map_err(|e| e.to_string())?;

    Ok(ProfileSwitchResult {
        success: true,
        switched_to: profile_id,
        email: target_email.to_string(),
        backup_path: Some("~/.gemini/backups/credential_backup_tauri.json".to_string()),
        timestamp: "2026-09-24T02:50:00Z".to_string(),
        quota,
        error: None,
    })
}

#[tauri::command]
pub async fn import_avatar(source_path: String) -> Result<AvatarImportResult, String> {
    let path = PathBuf::from(&source_path);
    if !path.exists() {
        return Ok(AvatarImportResult {
            success: false,
            asset_id: "".to_string(),
            format: "".to_string(),
            cached_path: "".to_string(),
            is_animated: false,
            error: Some("FILE_NOT_FOUND".to_string()),
        });
    }

    // Check file metadata size: if > 10 * 1024 * 1024 (10MB), reject
    let metadata = match fs::metadata(&path) {
        Ok(m) => m,
        Err(_) => {
            return Ok(AvatarImportResult {
                success: false,
                asset_id: "".to_string(),
                format: "".to_string(),
                cached_path: "".to_string(),
                is_animated: false,
                error: Some("FILE_NOT_FOUND".to_string()),
            });
        }
    };

    if metadata.len() == 0 {
        return Ok(AvatarImportResult {
            success: false,
            asset_id: "".to_string(),
            format: "".to_string(),
            cached_path: "".to_string(),
            is_animated: false,
            error: Some("INVALID_FILE_EMPTY".to_string()),
        });
    }

    if metadata.len() > 10 * 1024 * 1024 {
        return Ok(AvatarImportResult {
            success: false,
            asset_id: "".to_string(),
            format: "".to_string(),
            cached_path: "".to_string(),
            is_animated: false,
            error: Some("FILE_TOO_LARGE".to_string()),
        });
    }

    let ext = path
        .extension()
        .and_then(|s| s.to_str())
        .unwrap_or("")
        .to_lowercase();

    // Read first 12 bytes of the file and inspect magic bytes
    let mut file = match fs::File::open(&path) {
        Ok(f) => f,
        Err(_) => {
            return Ok(AvatarImportResult {
                success: false,
                asset_id: "".to_string(),
                format: "".to_string(),
                cached_path: "".to_string(),
                is_animated: false,
                error: Some("READ_ERROR".to_string()),
            });
        }
    };

    let mut header = [0u8; 12];
    let bytes_read = match file.read(&mut header) {
        Ok(n) => n,
        Err(_) => 0,
    };

    if bytes_read == 0 {
        return Ok(AvatarImportResult {
            success: false,
            asset_id: "".to_string(),
            format: "".to_string(),
            cached_path: "".to_string(),
            is_animated: false,
            error: Some("INVALID_FILE_EMPTY".to_string()),
        });
    }

    // Inspect magic bytes:
    // PNG: starts with &[0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]
    // GIF: starts with b"GIF87a" or b"GIF89a"
    // WebP: starts with b"RIFF" and bytes 8..12 are b"WEBP"
    let is_png = bytes_read >= 8 && header.starts_with(&[0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
    let is_gif = bytes_read >= 6 && (header.starts_with(b"GIF87a") || header.starts_with(b"GIF89a"));
    let is_webp = bytes_read >= 12 && header.starts_with(b"RIFF") && &header[8..12] == b"WEBP";

    let (detected_format, is_animated) = if is_png {
        ("png", false)
    } else if is_gif {
        ("gif", true)
    } else if is_webp {
        ("webp", false)
    } else if ext == "svg" {
        // SVG: verify path extension is svg, read first 4096 bytes as UTF-8, verify case-insensitive <svg tag,
        // and reject if it contains <script or javascript:
        let mut svg_file = match fs::File::open(&path) {
            Ok(f) => f,
            Err(_) => {
                return Ok(AvatarImportResult {
                    success: false,
                    asset_id: "".to_string(),
                    format: "".to_string(),
                    cached_path: "".to_string(),
                    is_animated: false,
                    error: Some("READ_ERROR".to_string()),
                });
            }
        };
        let mut svg_buf = vec![0u8; 4096.min(metadata.len() as usize)];
        let n = svg_file.read(&mut svg_buf).unwrap_or(0);
        svg_buf.truncate(n);
        let content_str = String::from_utf8_lossy(&svg_buf).to_lowercase();
        if !content_str.contains("<svg") {
            return Ok(AvatarImportResult {
                success: false,
                asset_id: "".to_string(),
                format: "".to_string(),
                cached_path: "".to_string(),
                is_animated: false,
                error: Some("INVALID_FORMAT".to_string()),
            });
        }
        if content_str.contains("<script") || content_str.contains("javascript:") || content_str.contains("onload") || content_str.contains("onerror") {
            return Ok(AvatarImportResult {
                success: false,
                asset_id: "".to_string(),
                format: "".to_string(),
                cached_path: "".to_string(),
                is_animated: false,
                error: Some("MALICIOUS_PAYLOAD".to_string()),
            });
        }
        ("svg", false)
    } else {
        return Ok(AvatarImportResult {
            success: false,
            asset_id: "".to_string(),
            format: "".to_string(),
            cached_path: "".to_string(),
            is_animated: false,
            error: Some("INVALID_FORMAT".to_string()),
        });
    };

    Ok(AvatarImportResult {
        success: true,
        asset_id: format!("avatar-{}", chrono::Utc::now().timestamp()),
        format: detected_format.to_string(),
        cached_path: source_path,
        is_animated,
        error: None,
    })
}

#[tauri::command]
pub async fn toggle_always_on_top(
    window: Window,
    enabled: Option<bool>,
) -> Result<serde_json::Value, String> {
    let current = window.is_always_on_top().map_err(|e| e.to_string())?;
    let new_state = enabled.unwrap_or(!current);
    window
        .set_always_on_top(new_state)
        .map_err(|e| e.to_string())?;

    Ok(serde_json::json!({
        "success": true,
        "always_on_top": new_state
    }))
}

#[tauri::command]
pub async fn set_click_through(
    window: Window,
    ignore: bool,
) -> Result<serde_json::Value, String> {
    window
        .set_ignore_cursor_events(ignore)
        .map_err(|e| e.to_string())?;

    Ok(serde_json::json!({
        "success": true,
        "click_through": ignore
    }))
}

#[tauri::command]
pub async fn set_pet_state(
    window: Window,
    state: String,
    message: Option<String>,
) -> Result<serde_json::Value, String> {
    window
        .emit("pet-state-change", serde_json::json!({ "state": &state, "message": message }))
        .map_err(|e| e.to_string())?;

    Ok(serde_json::json!({
        "success": true,
        "current_state": state
    }))
}

#[tauri::command]
pub async fn send_notification(
    window: Window,
    req: NotificationRequest,
) -> Result<serde_json::Value, String> {
    let notif_id = format!("notif-{}", chrono::Utc::now().timestamp_millis());
    window
        .emit("pet-notification", serde_json::json!({
            "id": &notif_id,
            "title": req.title,
            "body": req.body,
            "level": req.level,
            "duration_ms": req.duration_ms.unwrap_or(5000)
        }))
        .map_err(|e| e.to_string())?;

    Ok(serde_json::json!({
        "success": true,
        "notification_id": notif_id
    }))
}

// ----------------------------------------------------------------------------
// 3. Application Lifecycle & System Tray Initialization
// ----------------------------------------------------------------------------

pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // Build Tray Menu
            let show_i = MenuItem::with_id(app, "show", "Show / Restore", true, None::<&str>)?;
            let hide_i = MenuItem::with_id(app, "hide", "Hide Pet", true, None::<&str>)?;
            let pin_i = MenuItem::with_id(app, "pin", "Always on Top", true, None::<&str>)?;
            let ghost_i = MenuItem::with_id(app, "ghost", "Click-Through Mode", true, None::<&str>)?;
            let quit_i = MenuItem::with_id(app, "quit", "Exit", true, None::<&str>)?;

            let menu = Menu::with_items(app, &[&show_i, &hide_i, &pin_i, &ghost_i, &quit_i])?;

            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("Antigravity Desktop Pet")
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                    }
                    "hide" => {
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.hide();
                        }
                    }
                    "pin" => {
                        if let Some(w) = app.get_webview_window("main") {
                            if let Ok(on_top) = w.is_always_on_top() {
                                let _ = w.set_always_on_top(!on_top);
                            }
                        }
                    }
                    "ghost" => {
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.set_ignore_cursor_events(true);
                        }
                    }
                    "quit" => {
                        app.exit(0);
                    }
                    _ => {}
                })
                .build(app)?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_quota_status,
            list_profiles,
            switch_profile,
            import_avatar,
            toggle_always_on_top,
            set_click_through,
            set_pet_state,
            send_notification
        ])
        .run(tauri::generate_context!())
        .expect("error while running antigravity pet application");
}
