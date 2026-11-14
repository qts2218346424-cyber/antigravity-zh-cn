use serde_json::Value;
use std::path::PathBuf;

use crate::modules::studio::{
    auto_reapply, config_dir, l10n, pet, resources_dir, skin_injector, skin_manager,
    L10nPatchResult, MediaStatus, PetAssets, ReapplyCheckResult, SkillLocalizeResult, SkinInfo,
    StudioStatus,
};

async fn run_blocking<F, T>(f: F) -> Result<T, String>
where
    F: FnOnce() -> Result<T, String> + Send + 'static,
    T: Send + 'static,
{
    tokio::task::spawn_blocking(f)
        .await
        .map_err(|e| format!("后台执行任务异常: {}", e))?
}

fn build_studio_status(app: &tauri::AppHandle) -> StudioStatus {
    let cfg = skin_manager::load_studio_config();
    let detected_agent = l10n::detect_install_dir(cfg.install_dir.as_deref());
    let detected_ide = skin_injector::find_ide_app_root(cfg.ide_install_dir.as_deref());

    let install_str = detected_agent
        .as_ref()
        .map(|p| p.to_string_lossy().to_string())
        .or_else(|| cfg.install_dir.clone());
    let ide_str = detected_ide
        .as_ref()
        .map(|p| p.to_string_lossy().to_string())
        .or_else(|| cfg.ide_install_dir.clone());

    StudioStatus {
        install_dir: install_str.clone(),
        ide_root: ide_str.clone(),
        agent_status: auto_reapply::agent_status(install_str.as_deref()),
        ide_status: skin_injector::ide_status(ide_str.as_deref()),
        active_skin: cfg.active_skin,
        skin_enabled: cfg.skin_enabled,
        ide_enabled: cfg.ide_enabled,
        auto_reapply: cfg.auto_reapply,
        autostart_enabled: auto_reapply::is_autostart_enabled(app),
        updates_disabled: l10n::is_updates_disabled(install_str.as_deref()),
        splash_character: cfg.splash_character,
        lang: cfg.lang,
        enable_pet: cfg.enable_pet,
        enable_skin: cfg.enable_skin,
        pet_window_open: pet::is_pet_open(app),
        config_dir: config_dir().to_string_lossy().to_string(),
        resource_dir: resources_dir().to_string_lossy().to_string(),
        reapply_logs: cfg.reapply_logs,
    }
}

#[tauri::command]
pub async fn studio_get_status(app: tauri::AppHandle) -> Result<StudioStatus, String> {
    let app_clone = app.clone();
    tokio::task::spawn_blocking(move || build_studio_status(&app_clone))
        .await
        .map_err(|e| format!("读取 Studio 状态失败: {}", e))
}

#[tauri::command]
pub async fn studio_update_paths(
    app: tauri::AppHandle,
    install_dir: Option<String>,
    ide_dir: Option<String>,
) -> Result<StudioStatus, String> {
    let app_clone = app.clone();
    run_blocking(move || {
        let mut cfg = skin_manager::load_studio_config();
        if let Some(d) = install_dir {
            let t = d.trim().to_string();
            cfg.install_dir = if t.is_empty() { None } else { Some(t) };
        }
        if let Some(d) = ide_dir {
            let t = d.trim().to_string();
            cfg.ide_install_dir = if t.is_empty() { None } else { Some(t) };
        }
        skin_manager::save_studio_config(&cfg)?;
        Ok(build_studio_status(&app_clone))
    })
    .await
}

#[tauri::command]
pub async fn studio_apply_l10n(
    install_dir: Option<String>,
    lang: String,
    character: String,
    enable_pet: bool,
    enable_skin: bool,
) -> Result<L10nPatchResult, String> {
    run_blocking(move || {
        l10n::apply_l10n_patch(
            install_dir.as_deref(),
            &lang,
            &character,
            enable_pet,
            enable_skin,
        )
    })
    .await
}

#[tauri::command]
pub async fn studio_restore_l10n(install_dir: Option<String>) -> Result<String, String> {
    run_blocking(move || l10n::restore_l10n_backup(install_dir.as_deref())).await
}

#[tauri::command]
pub async fn studio_toggle_updates(
    install_dir: Option<String>,
    disable: bool,
) -> Result<bool, String> {
    run_blocking(move || l10n::toggle_auto_updates(install_dir.as_deref(), disable)).await
}

#[tauri::command]
pub async fn studio_localize_skills() -> Result<SkillLocalizeResult, String> {
    run_blocking(|| Ok(l10n::localize_all_skills())).await
}

#[tauri::command]
pub async fn studio_ensure_protocol() -> Result<bool, String> {
    run_blocking(l10n::ensure_chinese_thinking_protocol).await
}

#[tauri::command]
pub async fn studio_list_skins() -> Result<Vec<SkinInfo>, String> {
    run_blocking(|| Ok(skin_manager::list_skins())).await
}

#[tauri::command]
pub async fn studio_get_skin_manifest(skin_id: String) -> Result<Value, String> {
    run_blocking(move || {
        let (_, _, manifest) = skin_manager::load_effective_manifest(&skin_id)?;
        Ok(manifest)
    })
    .await
}

#[tauri::command]
pub async fn studio_activate_skin(skin_id: String) -> Result<skin_manager::CompiledSkin, String> {
    run_blocking(move || skin_manager::activate_skin(&skin_id)).await
}

#[tauri::command]
pub async fn studio_disable_skin() -> Result<(), String> {
    run_blocking(skin_manager::disable_skin).await
}

#[tauri::command]
pub async fn studio_save_override(
    scope: String,
    skin_id: Option<String>,
    patch: Value,
) -> Result<(), String> {
    run_blocking(move || skin_manager::save_override(&scope, skin_id.as_deref(), patch)).await
}

#[tauri::command]
pub async fn studio_reset_override(scope: String, skin_id: Option<String>) -> Result<(), String> {
    run_blocking(move || skin_manager::reset_override(&scope, skin_id.as_deref())).await
}

#[tauri::command]
pub async fn studio_duplicate_skin(
    source_id: String,
    new_id: String,
    new_name: String,
) -> Result<SkinInfo, String> {
    run_blocking(move || skin_manager::duplicate_skin(&source_id, &new_id, &new_name)).await
}

#[tauri::command]
pub async fn studio_delete_skin(skin_id: String) -> Result<(), String> {
    run_blocking(move || skin_manager::delete_skin(&skin_id)).await
}

#[tauri::command]
pub async fn studio_import_skin_zip(zip_path: String, overwrite: bool) -> Result<SkinInfo, String> {
    run_blocking(move || skin_manager::import_skin_zip(&PathBuf::from(zip_path), overwrite)).await
}

#[tauri::command]
pub async fn studio_export_skin_zip(
    skin_id: String,
    out_zip_path: String,
    include_overrides: bool,
) -> Result<String, String> {
    run_blocking(move || {
        skin_manager::export_skin_zip(&skin_id, &PathBuf::from(out_zip_path), include_overrides)
    })
    .await
}

#[tauri::command]
pub async fn studio_inject_ide(
    skin_id: Option<String>,
    ide_root: Option<String>,
) -> Result<String, String> {
    run_blocking(move || skin_injector::inject_ide(skin_id.as_deref(), ide_root.as_deref())).await
}

#[tauri::command]
pub async fn studio_remove_ide(ide_root: Option<String>) -> Result<String, String> {
    run_blocking(move || skin_injector::remove_ide(ide_root.as_deref())).await
}

#[tauri::command]
pub async fn studio_reapply_check(force: bool) -> Result<ReapplyCheckResult, String> {
    run_blocking(move || Ok(auto_reapply::check_and_reapply(force))).await
}

#[tauri::command]
pub async fn studio_set_auto_reapply(enabled: bool) -> Result<bool, String> {
    run_blocking(move || auto_reapply::set_auto_reapply(enabled)).await
}

#[tauri::command]
pub async fn studio_get_pet_assets() -> Result<PetAssets, String> {
    run_blocking(|| Ok(pet::get_pet_assets())).await
}

#[tauri::command]
pub async fn studio_launch_pet(
    app: tauri::AppHandle,
    character: Option<String>,
) -> Result<bool, String> {
    pet::launch_pet_window(&app, character.as_deref())
}

#[tauri::command]
pub async fn studio_close_pet(app: tauri::AppHandle) -> Result<bool, String> {
    pet::close_pet_window(&app)
}

#[tauri::command]
pub async fn studio_reset_pet_position(app: tauri::AppHandle) -> Result<(), String> {
    pet::reset_pet_position(&app)
}

#[tauri::command]
pub async fn studio_set_pet_size(
    app: tauri::AppHandle,
    width: u32,
    height: u32,
) -> Result<(), String> {
    pet::set_pet_size(&app, width, height)
}

#[tauri::command]
pub async fn studio_set_pet_always_on_top(
    app: tauri::AppHandle,
    always_on_top: bool,
) -> Result<(), String> {
    pet::set_pet_always_on_top(&app, always_on_top)
}

#[tauri::command]
pub async fn studio_get_media_status() -> Result<MediaStatus, String> {
    Ok(pet::get_media_status().await)
}

#[tauri::command]
pub async fn studio_send_media_command(cmd: String) -> Result<(), String> {
    run_blocking(move || pet::send_media_command(&cmd)).await
}
