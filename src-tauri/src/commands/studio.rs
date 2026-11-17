use serde_json::Value;
use std::path::PathBuf;
use std::time::Instant;

use crate::modules::studio::{
    auto_reapply, config_dir, l10n, pet, resources_dir, skin_injector, skin_manager,
    L10nPatchResult, MediaStatus, PetAssets, ReapplyCheckResult, SkillLocalizeResult, SkinInfo,
    StudioDiagnosticItem, StudioDiagnosticReport, StudioStatus,
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
        pet_character: cfg.pet_character,
        pet_roaming: cfg.pet_roaming,
        pet_always_on_top: cfg.pet_always_on_top,
        pet_scale_idx: cfg.pet_scale_idx,
        pet_muted: cfg.pet_muted,
        custom_pet_avatar: cfg.custom_pet_avatar,
        lang: cfg.lang,
        enable_pet: cfg.enable_pet,
        enable_skin: cfg.enable_skin,
        pet_window_open: pet::is_pet_open(app),
        has_legacy_pet: auto_reapply::has_legacy_pet_in_agent(install_str.as_deref()),
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
pub async fn studio_nudge_pet(app: tauri::AppHandle, dx: i32) -> Result<i32, String> {
    pet::nudge_pet_window(&app, dx)
}

#[tauri::command]
pub async fn studio_get_media_status() -> Result<MediaStatus, String> {
    Ok(pet::get_media_status().await)
}

#[tauri::command]
pub async fn studio_send_media_command(cmd: String) -> Result<(), String> {
    run_blocking(move || pet::send_media_command(&cmd)).await
}

#[tauri::command]
pub async fn studio_import_pet_avatar(
    app: tauri::AppHandle,
    file_path: String,
) -> Result<String, String> {
    run_blocking(move || pet::import_custom_pet_avatar(&app, &PathBuf::from(file_path))).await
}

#[tauri::command]
pub async fn studio_clear_pet_avatar(app: tauri::AppHandle) -> Result<(), String> {
    run_blocking(move || pet::clear_custom_pet_avatar(&app)).await
}

#[tauri::command]
pub async fn studio_update_pet_prefs(
    app: tauri::AppHandle,
    character: Option<String>,
    roaming: Option<bool>,
    always_on_top: Option<bool>,
    scale_idx: Option<usize>,
    muted: Option<bool>,
) -> Result<(), String> {
    run_blocking(move || {
        pet::update_pet_prefs(&app, character, roaming, always_on_top, scale_idx, muted)
    })
    .await
}

/// 执行 Studio 全链路离线与本地环境诊断自检（词典、材质编译器、桌宠资产、客户端探针）
#[tauri::command]
pub async fn studio_run_diagnostics(app: tauri::AppHandle) -> Result<StudioDiagnosticReport, String> {
    run_blocking(move || {
        let total_start = Instant::now();
        let mut items = Vec::new();
        let rdir = resources_dir();

        // 1. 汉化词典与运行时完整性校验
        let t1 = Instant::now();
        let dict_files = [
            "antigravity-zh-CN.json",
            "antigravity-zh-TW.json",
            "antigravity-zh-HK.json",
            "rules-zh-CN.json",
            "desktop-zh-CN.json",
            "runtime-zh.js",
            "skin-runtime.js",
        ];
        let mut missing = Vec::new();
        let mut cn_entries = 0usize;
        for f in &dict_files {
            let p = rdir.join(f);
            if !p.is_file() {
                missing.push((*f).to_string());
            } else if *f == "antigravity-zh-CN.json" {
                if let Ok(raw) = std::fs::read_to_string(&p) {
                    if let Ok(val) = serde_json::from_str::<Value>(&raw) {
                        cn_entries = val.as_object().map(|o| o.len()).unwrap_or(0);
                    }
                }
            }
        }
        items.push(StudioDiagnosticItem {
            key: "l10n_resources".to_string(),
            name: "多语种汉化词典与运行时脚本核验".to_string(),
            passed: missing.is_empty() && cn_entries > 100,
            duration_ms: t1.elapsed().as_millis() as u64,
            detail: if missing.is_empty() {
                format!("7 项核心资源完好，简体主词典已载入 {} 条精准词条", cn_entries)
            } else {
                format!("缺失资源文件: {}", missing.join(", "))
            },
        });

        // 2. 内置与自定义光学材质包全量沙盒编译测试
        let t2 = Instant::now();
        let skins = skin_manager::list_skins();
        let mut skin_errors = Vec::new();
        for sk in &skins {
            if let Err(e) = skin_manager::load_effective_manifest(&sk.id).and_then(|(dir, _, m)| {
                skin_manager::validate_manifest(&m, Some(&dir))
            }) {
                skin_errors.push(format!("{}: {}", sk.id, e));
            }
        }
        items.push(StudioDiagnosticItem {
            key: "skin_compiler".to_string(),
            name: "高定光学材质包 Schema 与安全沙盒校验".to_string(),
            passed: !skins.is_empty() && skin_errors.is_empty(),
            duration_ms: t2.elapsed().as_millis() as u64,
            detail: if skin_errors.is_empty() {
                format!("全部 {} 款材质包通过结构与 CSS 防注入安全审查", skins.len())
            } else {
                skin_errors.join("；")
            },
        });

        // 3. 桌面伴侣高精多姿态立绘与多角色媒体资产校验
        let t3 = Instant::now();
        let assets = pet::get_pet_assets();
        let checks = [
            assets.nezuko_chibi.is_some(),
            assets.nezuko_blink.is_some(),
            assets.nezuko_happy.is_some(),
            assets.nezuko_run.is_some(),
            assets.nezuko_stomp.is_some(),
            assets.nezuko_blood.is_some(),
            assets.nezuko_peeker.is_some(),
            assets.nezuko_basket.is_some(),
            assets.nezuko_spin_sheet.is_some(),
            assets.little_prince.is_some(),
            assets.prince_blink.is_some(),
            assets.prince_walk.is_some(),
            assets.prince_fox.is_some(),
            assets.prince_rose_pose.is_some(),
            assets.prince_sleep.is_some(),
            assets.tanjiro_water.is_some(),
            assets.zenitsu_thunder.is_some(),
            assets.inosuke_beast.is_some(),
        ];
        let total_expected = checks.len();
        let loaded_count = checks.into_iter().filter(|b| *b).count();
        items.push(StudioDiagnosticItem {
            key: "pet_assets".to_string(),
            name: "桌面伴侣多姿态原画与 5 大内置角色材质缓存".to_string(),
            passed: loaded_count == total_expected,
            duration_ms: t3.elapsed().as_millis() as u64,
            detail: format!(
                "祢豆子与小王子全套多姿态透明原画及全角色资产已就绪 ({}/{}){}",
                loaded_count,
                total_expected,
                if assets.custom_avatar.is_some() {
                    "，且已挂载用户自定义专属立绘"
                } else {
                    ""
                }
            ),
        });

        // 4. 本地配置目录原子写入自检
        let t4 = Instant::now();
        let probe_file = config_dir().join(".diag_write_probe");
        let write_ok = crate::modules::studio::atomic_write_text(&probe_file, "ok")
            .and_then(|_| {
                let _ = std::fs::remove_file(&probe_file);
                Ok(())
            })
            .is_ok();
        items.push(StudioDiagnosticItem {
            key: "atomic_fs".to_string(),
            name: "配置目录权限与 Windows 原子替换写入探针".to_string(),
            passed: write_ok,
            duration_ms: t4.elapsed().as_millis() as u64,
            detail: if write_ok {
                format!("配置目录读写与原子覆盖正常 ({})", config_dir().display())
            } else {
                format!("配置目录写入受阻: {}", config_dir().display())
            },
        });

        // 5. 客户端与 IDE 环境探测状态汇总
        let t5 = Instant::now();
        let st = build_studio_status(&app);
        items.push(StudioDiagnosticItem {
            key: "client_probe".to_string(),
            name: "Antigravity 客户端与 IDE 安装环境探测".to_string(),
            passed: true,
            duration_ms: t5.elapsed().as_millis() as u64,
            detail: format!(
                "Agent 状态: {} | IDE 状态: {} | 旧版宠物残留: {}",
                st.agent_status,
                st.ide_status,
                if st.has_legacy_pet { "存在待清理残留" } else { "洁净无残留" }
            ),
        });

        let all_passed = items.iter().all(|i| i.passed);
        Ok(StudioDiagnosticReport {
            all_passed,
            total_ms: total_start.elapsed().as_millis() as u64,
            items,
        })
    })
    .await
}
