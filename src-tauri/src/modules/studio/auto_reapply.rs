use std::sync::atomic::{AtomicBool, Ordering};
use sysinfo::{Pid, System};
use tauri::Emitter;
use tauri_plugin_autostart::ManagerExt;

use super::asar::read_asar_file_content;
use super::l10n::{
    apply_l10n_patch, detect_install_dir, locate_app_asar, localize_all_skills,
};
use super::skin_injector::cleanup_legacy_ide_injection;
use super::skin_manager::{
    append_reapply_log, compile_skin, compiled_dir, load_studio_config, save_studio_config,
    StudioConfig,
};
use super::{ReapplyCheckResult, PATCH_MARKER};

static WATCHDOG_STARTED: AtomicBool = AtomicBool::new(false);
static CHECK_RUNNING: AtomicBool = AtomicBool::new(false);

struct RunningGuard;
impl Drop for RunningGuard {
    fn drop(&mut self) {
        CHECK_RUNNING.store(false, Ordering::SeqCst);
    }
}

/// 查询 Google Antigravity 桌面应用注入状态：`"not_found"` / `"clean"` / `"patched"`
pub fn agent_status(explicit_dir: Option<&str>) -> String {
    let Some(install_dir) = detect_install_dir(explicit_dir) else {
        return "not_found".to_string();
    };
    let Some(asar_path) = locate_app_asar(&install_dir) else {
        return "not_found".to_string();
    };
    let Ok(bytes) = std::fs::read(&asar_path) else {
        return "not_found".to_string();
    };
    match read_asar_file_content(&bytes, "dist/main.js") {
        Ok(main_js) => {
            if String::from_utf8_lossy(&main_js).contains(PATCH_MARKER) {
                "patched".to_string()
            } else {
                "clean".to_string()
            }
        }
        Err(_) => "clean".to_string(),
    }
}

/// 检测 Antigravity 客户端 app.asar 渲染层是否仍残留旧版脚本注入的老宠物代码
pub fn has_legacy_pet_in_agent(explicit_dir: Option<&str>) -> bool {
    let Some(install_dir) = detect_install_dir(explicit_dir) else {
        return false;
    };
    let Some(asar_path) = locate_app_asar(&install_dir) else {
        return false;
    };
    let Ok(bytes) = std::fs::read(&asar_path) else {
        return false;
    };
    for target in ["dist/preload.js", "dist/utils.js"] {
        if let Ok(content) = read_asar_file_content(&bytes, target) {
            let text = String::from_utf8_lossy(&content);
            if text.contains("__AGY_NEZUKO_PET_INITIALIZED__") || text.contains("nezuko-pet") {
                return true;
            }
        }
    }
    false
}

/// 检测官方 Antigravity 桌面应用进程是否正在运行（严格排除本管理器与旧版 IDE）
pub fn is_antigravity_running() -> bool {
    let self_pid = Pid::from_u32(std::process::id());
    let mut sys = System::new_all();
    sys.refresh_processes(sysinfo::ProcessesToUpdate::All);

    for (pid, proc_) in sys.processes() {
        if *pid == self_pid {
            continue;
        }
        let name = proc_.name().to_string_lossy().to_ascii_lowercase();
        let exe = proc_
            .exe()
            .map(|p| p.to_string_lossy().to_ascii_lowercase())
            .unwrap_or_default();

        if name.contains("manager")
            || name.contains("tools")
            || name.contains("studio")
            || exe.contains("antigravity-cn")
            || exe.contains("antigravity ide")
            || exe.contains("antigravityide")
        {
            continue;
        }
        if name == "antigravity.exe"
            || name == "antigravity"
            || exe.ends_with("\\antigravity.exe")
            || exe.ends_with("/antigravity")
        {
            return true;
        }
    }
    false
}

/// 检查并在需要时自动维护 Antigravity 桌面应用汉化补丁与光学材质编译产物
pub fn check_and_reapply(force: bool) -> ReapplyCheckResult {
    if CHECK_RUNNING
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return ReapplyCheckResult {
            agent: agent_status(None),
            actions: vec!["巡检正在执行中，已跳过并发重复调用".to_string()],
            error: None,
        };
    }
    let _guard = RunningGuard;

    cleanup_legacy_ide_injection();

    let cfg: StudioConfig = load_studio_config();
    let cur_agent = agent_status(cfg.install_dir.as_deref());

    let mut actions = Vec::new();
    let mut errors = Vec::new();

    if !cfg.auto_reapply && !force {
        return ReapplyCheckResult {
            agent: cur_agent,
            actions,
            error: None,
        };
    }

    // 若已开启皮肤但编译文件缺失（或用户点击强制重刷），重新编译当前皮肤至客户端热加载目录
    if cfg.skin_enabled {
        if let Some(active_id) = cfg.active_skin.as_deref() {
            let css_missing = !compiled_dir().join("skin.css").is_file();
            if force || css_missing {
                match compile_skin(active_id) {
                    Ok(_) => {
                        let msg = format!("已重新编译 Antigravity 应用光学材质 '{}'", active_id);
                        actions.push(msg.clone());
                        append_reapply_log(&msg);
                    }
                    Err(e) => {
                        let err_msg = format!("编译光学材质 '{}' 失败: {}", active_id, e);
                        errors.push(err_msg.clone());
                        append_reapply_log(&err_msg);
                    }
                }
            }
        }
    }

    // 检查是否曾打过补丁或已启用皮肤（存在配置 install_dir、开启了皮肤或已有 .bak）
    let had_agent_patch = cfg.install_dir.is_some()
        || cfg.skin_enabled
        || detect_install_dir(None)
            .and_then(|d| locate_app_asar(&d))
            .map(|p| p.with_extension("asar.bak").is_file())
            .unwrap_or(false);

    if (force && cur_agent != "not_found") || (cur_agent == "clean" && had_agent_patch) {
        if is_antigravity_running() && !force {
            let msg = "检测到 Antigravity 应用待挂载补丁/钩子，等待应用退出后自动静默重注";
            actions.push(msg.to_string());
            append_reapply_log(msg);
        } else {
            match apply_l10n_patch(
                cfg.install_dir.as_deref(),
                &cfg.lang,
                &cfg.splash_character,
                cfg.enable_pet,
                cfg.enable_skin || cfg.skin_enabled,
            ) {
                Ok(res) => {
                    let msg = format!(
                        "{} Antigravity 应用中文与皮肤钩子成功（共 {} 个模块）",
                        if force { "强制重刷" } else { "自动重注" },
                        res.patched_files.len()
                    );
                    actions.push(msg.clone());
                    append_reapply_log(&msg);
                    let sk = localize_all_skills();
                    if sk.updated > 0 {
                        let s_msg = format!("同步汉化了 {} 个 Skill 描述", sk.updated);
                        actions.push(s_msg.clone());
                        append_reapply_log(&s_msg);
                    }
                }
                Err(e) => {
                    errors.push(format!("重注 Antigravity 应用补丁失败: {}", e));
                    append_reapply_log(&format!("重注 Antigravity 应用补丁失败: {}", e));
                }
            }
        }
    }

    let final_agent = agent_status(cfg.install_dir.as_deref());

    ReapplyCheckResult {
        agent: final_agent,
        actions,
        error: if errors.is_empty() {
            None
        } else {
            Some(errors.join("；"))
        },
    }
}

pub fn set_auto_reapply(enabled: bool) -> Result<bool, String> {
    let mut cfg = load_studio_config();
    cfg.auto_reapply = enabled;
    save_studio_config(&cfg)?;
    append_reapply_log(if enabled {
        "已开启自动维护看门狗巡检"
    } else {
        "已暂停自动维护看门狗巡检"
    });
    Ok(enabled)
}

pub fn is_autostart_enabled(app: &tauri::AppHandle) -> bool {
    app.autolaunch().is_enabled().unwrap_or(false)
}

/// 启动随 Tauri 宿主常驻的 Tokio 自动维护看门狗（每 120 秒巡检一次）
pub fn start_background_watchdog(app: tauri::AppHandle) {
    if WATCHDOG_STARTED
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return;
    }

    tauri::async_runtime::spawn(async move {
        tokio::time::sleep(std::time::Duration::from_secs(15)).await;
        loop {
            let cfg = load_studio_config();
            if cfg.auto_reapply {
                let res = tokio::task::spawn_blocking(|| check_and_reapply(false)).await;
                if let Ok(report) = res {
                    if !report.actions.is_empty() || report.error.is_some() {
                        let _ = app.emit("studio:reapplied", report);
                    }
                }
            }
            tokio::time::sleep(std::time::Duration::from_secs(120)).await;
        }
    });
}
