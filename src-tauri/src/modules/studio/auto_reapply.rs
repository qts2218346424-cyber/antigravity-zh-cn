use std::sync::atomic::{AtomicBool, Ordering};
use sysinfo::{Pid, System};
use tauri::Emitter;
use tauri_plugin_autostart::ManagerExt;

use super::asar::read_asar_file_content;
use super::l10n::{
    apply_l10n_patch, detect_install_dir, locate_app_asar, localize_all_skills,
};
use super::skin_injector::{ide_status, inject_ide};
use super::skin_manager::{
    append_reapply_log, load_studio_config, save_studio_config, StudioConfig,
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

/// 查询 Antigravity 客户端（Agent）汉化注入状态：`"not_found"` / `"clean"` / `"patched"`
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

/// 检测官方 Antigravity 客户端进程是否正在运行（严格排除本管理器）
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

/// 检查并在需要时自动重打 Agent 汉化补丁与 IDE 材质包注入
pub fn check_and_reapply(force: bool) -> ReapplyCheckResult {
    if CHECK_RUNNING
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return ReapplyCheckResult {
            agent: agent_status(None),
            ide: ide_status(None),
            actions: vec!["巡检正在执行中，已跳过并发重复调用".to_string()],
            error: None,
        };
    }
    let _guard = RunningGuard;

    let cfg: StudioConfig = load_studio_config();
    let cur_agent = agent_status(cfg.install_dir.as_deref());
    let cur_ide = ide_status(cfg.ide_install_dir.as_deref());

    let mut actions = Vec::new();
    let mut errors = Vec::new();

    if !cfg.auto_reapply && !force {
        return ReapplyCheckResult {
            agent: cur_agent,
            ide: cur_ide,
            actions,
            error: None,
        };
    }

    // 检查是否曾打过补丁（存在配置 install_dir 或已有 .bak）
    let had_agent_patch = cfg.install_dir.is_some()
        || detect_install_dir(None)
            .and_then(|d| locate_app_asar(&d))
            .map(|p| p.with_extension("asar.bak").is_file())
            .unwrap_or(false);

    if cur_agent == "clean" && (force || had_agent_patch) {
        if is_antigravity_running() && !force {
            let msg = "检测到 Antigravity 客户端有更新覆盖，等待客户端退出后再自动重打补丁";
            actions.push(msg.to_string());
            append_reapply_log(msg);
        } else {
            match apply_l10n_patch(
                cfg.install_dir.as_deref(),
                &cfg.lang,
                &cfg.splash_character,
                cfg.enable_pet,
                cfg.enable_skin,
            ) {
                Ok(res) => {
                    let msg = format!("自动重打 Agent 中文补丁成功（{}）", res.character);
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
                    errors.push(format!("重打 Agent 补丁失败: {}", e));
                    append_reapply_log(&format!("重打 Agent 补丁失败: {}", e));
                }
            }
        }
    }

    if (cur_ide == "clean" || cur_ide == "stale")
        && cfg.ide_enabled
        && cfg.skin_enabled
        && cfg.active_skin.is_some()
    {
        match inject_ide(cfg.active_skin.as_deref(), cfg.ide_install_dir.as_deref()) {
            Ok(msg) => {
                actions.push(msg.clone());
                append_reapply_log(&msg);
            }
            Err(e) => {
                errors.push(format!("自动修复 IDE 材质包失败: {}", e));
                append_reapply_log(&format!("自动修复 IDE 材质包失败: {}", e));
            }
        }
    }

    let final_agent = agent_status(cfg.install_dir.as_deref());
    let final_ide = ide_status(cfg.ide_install_dir.as_deref());

    ReapplyCheckResult {
        agent: final_agent,
        ide: final_ide,
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
