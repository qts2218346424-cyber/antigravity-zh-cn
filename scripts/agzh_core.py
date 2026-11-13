#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 汉化 + 材质包 一体化核心门面 (agzh_core.py)

命令行 (scripts/agzh.py) 与图形界面 (app/agzh_app.py) 都只调用这里的函数，
保证两种入口行为完全一致。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skin_manager as sm  # noqa: E402
import skin_injector as si  # noqa: E402
import auto_reapply as ar  # noqa: E402


def bootstrap() -> None:
    """首次运行：准备配置目录、同步内置材质包、为打包版设置资源环境变量。"""
    root = sm.resource_root()
    os.environ.setdefault("AGZH_REPO_ROOT", str(root))
    # 启动动画角色选择保存到用户配置目录，避免写进安装/解包目录
    os.environ.setdefault("AGZH_SPLASH_CONFIG", str(sm.config_dir() / "splash_config.json"))
    sm.config_dir().mkdir(parents=True, exist_ok=True)
    try:
        sm.sync_builtin_packs()
    except Exception as e:
        print(f"[!] 同步内置材质包失败: {e}")


# ---------------------------------------------------------------------------
# 材质包
# ---------------------------------------------------------------------------
def list_skins() -> list[dict]:
    st = sm.load_state()
    active = st.get("active_skin") if st.get("skin_enabled", True) else None
    out = []
    for p in sm.list_packs():
        info = p.to_info()
        info["active"] = p.id == active
        out.append(info)
    return out


def use_skin(skin_id: str, *, apply_ide: bool | None = None, ide_dir: str | None = None) -> dict:
    """切换材质包：写入运行时载荷（Agent 桌面端实时生效）并同步到 IDE 工作台。"""
    payload = sm.activate(skin_id)
    result = {"id": skin_id, "hash": payload["hash"], "ide": None}
    result["ide"] = sync_ide(apply_ide=apply_ide, ide_dir=ide_dir)
    return result


def skin_off(*, ide_dir: str | None = None) -> dict:
    sm.deactivate()
    root = si.find_ide_app_root(ide_dir)
    ide = None
    if root is not None and (sm.load_state().get("ide") or {}).get("enabled"):
        si.inject_ide(root)  # 写入 disabled 载荷 = 剥离样式块，但保留 IDE 注入开关
        ide = "cleared"
    return {"disabled": True, "ide": ide}


def sync_ide(*, apply_ide: bool | None = None, ide_dir: str | None = None) -> str | None:
    """apply_ide=None 时遵循用户上次的选择（未选择过且检测到 IDE 时默认启用）。"""
    root = si.find_ide_app_root(ide_dir)
    if root is None:
        return "not_found"
    enabled = (sm.load_state().get("ide") or {}).get("enabled")
    want = apply_ide if apply_ide is not None else (enabled is not False)
    if not want:
        if enabled:
            si.remove_ide(root)
        return "disabled"
    try:
        r = si.inject_ide(root)
        return "applied" if r["changed"] else "unchanged"
    except PermissionError:
        return "permission_denied"


def save_customization(skin_id: str | None, data: dict) -> dict | None:
    """保存用户覆盖层并在其属于当前材质包时立即重新编译生效。"""
    sm.save_override(skin_id, data)
    st = sm.load_state()
    if st.get("active_skin") and st.get("skin_enabled", True) and (skin_id in (None, st.get("active_skin"))):
        return use_skin(st["active_skin"])
    return None


# ---------------------------------------------------------------------------
# 汉化补丁
# ---------------------------------------------------------------------------
def detect_install_dir(explicit: str | None = None) -> Path | None:
    import patch_antigravity as pa
    if explicit:
        p = Path(explicit)
        return p if p.is_dir() else None
    saved = (sm.load_state().get("agent") or {}).get("install_dir")
    if saved and pa.get_asar_path(Path(saved)).is_file():
        return Path(saved)
    return pa.get_default_install_path()


def install_localization(install_dir: Path, lang: str = "zh-CN", character: str | None = None,
                         enable_pet: bool = True, enable_skin: bool = True, stop_processes: bool = True) -> None:
    import patch_antigravity as pa
    pa.apply_patch(install_dir, lang, sm.resource_root(), character=character, enable_pet=enable_pet,
                   enable_skin=enable_skin, stop_processes=stop_processes)
    if sys.platform == "darwin":
        subprocess.run(["codesign", "--force", "--deep", "-s", "-", str(install_dir)], capture_output=True)


def restore_localization(install_dir: Path, *, also_ide: bool = True) -> bool:
    import patch_antigravity as pa
    ok = pa.restore_backup(install_dir)
    if also_ide:
        root = si.find_ide_app_root()
        if root is not None:
            si.remove_ide(root)
    return ok


def toggle_updates(install_dir: Path, disable: bool) -> None:
    import patch_antigravity as pa
    pa.toggle_auto_updates(install_dir, disable=disable, remember=True)


# ---------------------------------------------------------------------------
# 桌宠
# ---------------------------------------------------------------------------
def launch_pet() -> subprocess.Popen | None:
    """启动独立桌面桌宠（目前仅 Windows：依赖 pywebview + pywin32 + pystray）。"""
    if sys.platform != "win32":
        raise RuntimeError("独立桌面桌宠目前仅支持 Windows；macOS/Linux 请使用 Antigravity 内置桌宠。")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    env = dict(os.environ, AGZH_REPO_ROOT=str(sm.resource_root()))
    if getattr(sys, "frozen", False):
        return subprocess.Popen([sys.executable, "--pet"], creationflags=flags, env=env)
    py = Path(sys.executable)
    pyw = py.with_name("pythonw.exe")
    exe = str(pyw if pyw.is_file() else py)
    return subprocess.Popen([exe, str(sm.resource_root() / "scripts" / "desktop_pet_app.py")],
                            creationflags=flags, env=env, cwd=str(sm.resource_root()))


# ---------------------------------------------------------------------------
# 状态汇总
# ---------------------------------------------------------------------------
def status() -> dict:
    st = sm.load_state()
    install = detect_install_dir()
    ide_root = si.find_ide_app_root()
    asar = None
    if install:
        import patch_antigravity as pa
        asar = pa.get_asar_path(install)
    return {
        "config_dir": str(sm.config_dir()),
        "install_dir": str(install) if install else None,
        "agent": ar.agent_status(asar) if asar else "missing",
        "ide_root": str(ide_root) if ide_root else None,
        "ide": si.ide_status(ide_root),
        "active_skin": st.get("active_skin"),
        "skin_enabled": st.get("skin_enabled", True),
        "auto_reapply": bool(st.get("auto_reapply")),
        "autostart": ar.autostart_enabled(),
    }
