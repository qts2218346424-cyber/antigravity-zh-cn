use tauri::{AppHandle, Emitter};

use crate::modules::studio::optimizer::{
    self, CleanResult, JunkCategoryItem, LargeFileScanResult, MemoryBoostResult,
    OptimizerActionResult, OptimizerOverview, ProcessGroupItem, ServiceItem, WhitelistSnapshot,
};

async fn run_blocking<F, T>(f: F) -> Result<T, String>
where
    F: FnOnce() -> Result<T, String> + Send + 'static,
    T: Send + 'static,
{
    tokio::task::spawn_blocking(f)
        .await
        .map_err(|e| format!("后台执行优化任务异常: {}", e))?
}

#[tauri::command]
pub async fn optimizer_get_overview() -> Result<OptimizerOverview, String> {
    run_blocking(|| Ok(optimizer::get_overview())).await
}

#[tauri::command]
pub async fn optimizer_toggle_ruthless(enable: bool) -> Result<OptimizerOverview, String> {
    run_blocking(move || optimizer::toggle_ruthless_mode(enable)).await
}

#[tauri::command]
pub async fn optimizer_boost_memory() -> Result<MemoryBoostResult, String> {
    run_blocking(|| Ok(optimizer::boost_memory())).await
}

#[tauri::command]
pub async fn optimizer_list_processes() -> Result<Vec<ProcessGroupItem>, String> {
    run_blocking(|| Ok(optimizer::list_process_groups())).await
}

#[tauri::command]
pub async fn optimizer_process_action(
    process_name: String,
    action: String,
) -> Result<OptimizerActionResult, String> {
    run_blocking(move || Ok(optimizer::control_process_group(&process_name, &action))).await
}

#[tauri::command]
pub async fn optimizer_unfreeze_all() -> Result<OptimizerActionResult, String> {
    run_blocking(|| Ok(optimizer::unfreeze_all_processes())).await
}

#[tauri::command]
pub async fn optimizer_list_services() -> Result<Vec<ServiceItem>, String> {
    run_blocking(|| Ok(optimizer::list_heavy_services())).await
}

#[tauri::command]
pub async fn optimizer_service_action(name: String, action: String) -> Result<String, String> {
    run_blocking(move || optimizer::control_heavy_service(&name, &action)).await
}

#[tauri::command]
pub async fn optimizer_scan_junk() -> Result<Vec<JunkCategoryItem>, String> {
    run_blocking(|| Ok(optimizer::scan_junk_categories())).await
}

#[tauri::command]
pub async fn optimizer_clean_junk(category_ids: Vec<String>) -> Result<CleanResult, String> {
    run_blocking(move || Ok(optimizer::clean_junk_categories(category_ids))).await
}

#[tauri::command]
pub async fn optimizer_scan_large_files(
    root_path: Option<String>,
    min_file_mb: Option<f64>,
) -> Result<LargeFileScanResult, String> {
    run_blocking(move || optimizer::scan_large_files(root_path, min_file_mb)).await
}

#[tauri::command]
pub async fn optimizer_file_action(path: String, action: String) -> Result<String, String> {
    run_blocking(move || optimizer::handle_file_action(&path, &action)).await
}

#[tauri::command]
pub async fn optimizer_get_whitelist() -> Result<WhitelistSnapshot, String> {
    run_blocking(|| Ok(optimizer::get_whitelist_snapshot())).await
}

#[tauri::command]
pub async fn optimizer_update_whitelist(items: Vec<String>) -> Result<WhitelistSnapshot, String> {
    run_blocking(move || optimizer::update_custom_whitelist(items)).await
}

#[tauri::command]
pub async fn optimizer_relaunch_as_admin(_app: AppHandle) -> Result<bool, String> {
    let launched = run_blocking(optimizer::relaunch_as_admin).await?;
    if launched {
        optimizer::shutdown_and_restore();
        // 彻底退出旧进程，释放 Named Pipe 与单实例 Mutex 锁（绕过 ExitRequested 中的 api.prevent_exit）
        crate::proxy::signature_cache::flush_on_exit();
        std::process::exit(0);
    }
    Ok(launched)
}

#[tauri::command]
pub async fn optimizer_open_full_panel(app: AppHandle) -> Result<(), String> {
    let app_handle = app.clone();
    let _ = app.run_on_main_thread(move || {
        if let Ok(window) = crate::modules::lightweight::exit_lightweight_mode(&app_handle) {
            let _ = window.show();
            let _ = window.unminimize();
            let _ = window.set_focus();
        }
        let _ = app_handle.emit("studio:open-tab", "optimizer");
    });
    Ok(())
}
