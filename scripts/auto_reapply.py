#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 更新后自动重新注入 (auto_reapply.py)

面向普通用户（与面向维护者、会自动 git push 的 auto_maintainer.py 区分）：
- 每次补丁成功后在用户配置目录 state.json 中记录目标文件指纹（大小 + mtime + sha256）；
- 检测：指纹变化 → 读取文件确认补丁标记是否还在 → 标记丢失即判定“被官方更新覆盖”；
- 重新注入：Antigravity 正在运行时延后（不强杀用户进程），退出后自动重打汉化补丁、
  重新写入 IDE 皮肤块，并在 macOS 上重新 ad-hoc 签名；
- 用户主动“还原原版”后会记录 agent.enabled=false，不会被自动重新打回；
- 开机自启：Windows 注册表 HKCU\\...\\Run、macOS LaunchAgent、Linux XDG autostart，
  全部为当前用户级别，无需管理员权限。
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skin_manager as sm  # noqa: E402
import skin_injector as si  # noqa: E402

PATCH_MARKER = b"/* __ANTIGRAVITY_ZH_CN_PATCHED__ */"
AUTOSTART_NAME = "AntigravityZhCnAutoReapply"
MAC_LABEL = "com.antigravity-zh-cn.autoreapply"
PROCESS_NAMES = ("Antigravity", "antigravity", "Antigravity.exe", "antigravity.exe")
# 官方更新安装器替换 app.asar 期间文件处于“半写入”状态：最近 SETTLE_SECONDS 秒内被修改过的
# 文件先不动，等更新器写完再重新注入，避免在不完整的 asar 上打补丁。
SETTLE_SECONDS = 90
# 正在运行时识别的官方更新/安装程序进程名（小写），存在时同样延后
UPDATER_PROCESS_NAMES = ("antigravity setup.exe", "antigravitysetup.exe", "update.exe", "squirrel.exe")

# 指纹变化后需要全文扫描补丁标记（app.asar 约 100~200 MB）。同一指纹只扫描一次。
_MARKER_CACHE: dict[tuple, bool] = {}


def _reapply_lock():
    """重新注入 app.asar 的跨进程锁（界面“立即检测”与开机后台守护可能同时触发）。"""
    return sm.FileLock(sm.config_dir() / ".reapply.lock", timeout=0.5, stale=600)


def _log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        p = sm.config_dir() / "logs" / "auto-reapply.log"
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.is_file() and p.stat().st_size > 512 * 1024:
            p.replace(p.with_suffix(".log.1"))
        with open(p, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 1. 指纹与状态
# ---------------------------------------------------------------------------
def file_fingerprint(path: Path, with_hash: bool = False) -> dict:
    st = path.stat()
    fp = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    if with_hash:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        fp["sha256"] = h.hexdigest()
    return fp


def _contains_marker(path: Path, marker: bytes = PATCH_MARKER) -> bool:
    overlap = len(marker)
    tail = b""
    with open(path, "rb") as f:
        while True:
            chunk = f.read(4 * 1024 * 1024)
            if not chunk:
                return False
            if marker in tail + chunk:
                return True
            tail = chunk[-overlap:]


def record_agent_patch(install_dir: Path, asar_path: Path, *, lang: str, character: str | None,
                       enable_pet: bool, enable_skin: bool = True, version: str | None = None) -> dict:
    """apply_patch 成功后调用：记录补丁参数与目标文件指纹。"""
    info = {
        "enabled": True,
        "install_dir": str(install_dir),
        "asar_path": str(asar_path),
        "lang": lang,
        "character": character,
        "enable_pet": enable_pet,
        "enable_skin": enable_skin,
        "fingerprint": file_fingerprint(asar_path, with_hash=True),
        "version": version,
        "patched_at": int(time.time()),
    }
    sm.update_state(agent=info)
    return info


def mark_agent_restored(install_dir: Path) -> None:
    sm.update_state(agent={"enabled": False, "install_dir": str(install_dir)})


def agent_status(asar_path: Path | None = None) -> str:
    """Agent 桌面端汉化状态：

    - missing        未找到 app.asar
    - never          从未通过本工具打过补丁
    - disabled       用户已主动还原，不自动重打
    - patched        补丁仍在（指纹未变或标记存在）
    - needs_reapply  曾经打过补丁但标记已丢失（官方更新覆盖）
    """
    st = sm.load_state().get("agent") or {}
    if asar_path is None and st.get("asar_path"):
        asar_path = Path(st["asar_path"])
    if asar_path is None or not Path(asar_path).is_file():
        return "missing"
    asar_path = Path(asar_path)
    if not st:
        return "patched" if _contains_marker_cached(asar_path) else "never"
    if st.get("enabled") is False:
        return "disabled"
    fp = st.get("fingerprint") or {}
    cur = file_fingerprint(asar_path)
    if fp.get("size") == cur["size"] and fp.get("mtime_ns") == cur["mtime_ns"]:
        return "patched"
    # 指纹变化：可能是官方更新，也可能是其他工具重新打包，读取内容确认
    if _contains_marker_cached(asar_path, cur):
        return "patched"
    return "needs_reapply"


def _contains_marker_cached(path: Path, fp: dict | None = None) -> bool:
    fp = fp or file_fingerprint(path)
    key = (str(path), fp["size"], fp["mtime_ns"])
    if key not in _MARKER_CACHE:
        if len(_MARKER_CACHE) > 16:
            _MARKER_CACHE.clear()
        _MARKER_CACHE[key] = _contains_marker(path)
    return _MARKER_CACHE[key]


def recently_modified(path: Path, seconds: float | None = None) -> bool:
    """文件是否在最近 seconds 秒内被修改（官方更新器可能仍在写入）。mtime 在未来（时钟偏差）时不阻塞。"""
    seconds = SETTLE_SECONDS if seconds is None else seconds
    try:
        age = time.time() - Path(path).stat().st_mtime
    except OSError:
        return True
    return 0 <= age < seconds


# ---------------------------------------------------------------------------
# 2. 进程检测（精确匹配进程名，避免 pkill -f 误杀本工具自身）
# ---------------------------------------------------------------------------
def is_antigravity_running() -> bool:
    try:
        names = _process_names()
        if sys.platform == "win32":
            return "antigravity.exe" in names
        return any(n in names for n in (p.lower() for p in PROCESS_NAMES))
    except Exception:
        return False


def is_updater_running() -> bool:
    try:
        names = _process_names()
    except Exception:
        return False
    return any(n in names for n in UPDATER_PROCESS_NAMES)


def _process_names() -> set[str]:
    """当前用户可见的进程名（小写）。tasklist 在中文系统上输出 GBK，按 utf-8 宽松解码只用于匹配 ASCII 名称。"""
    if sys.platform == "win32":
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=10,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout or ""
        return {line.split(",")[0].strip('"').lower() for line in out.splitlines() if line}
    out = subprocess.run(["ps", "-A", "-o", "comm="], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=10).stdout or ""
    return {os.path.basename(line.strip()).lower() for line in out.splitlines() if line.strip()}


# ---------------------------------------------------------------------------
# 3. 检测 + 重新注入
# ---------------------------------------------------------------------------
def check(apply: bool = False, *, allow_when_running: bool = False, repo_root: Path | None = None) -> dict:
    """检测一次；apply=True 时对需要的目标重新注入。返回各目标的状态字典。"""
    result: dict = {"agent": None, "ide": None, "actions": []}
    st = sm.load_state()
    agent = st.get("agent") or {}

    # 皮肤载荷缺失（例如清理过配置目录）时按当前选择重新编译
    if st.get("active_skin") and st.get("skin_enabled", True) and sm.read_compiled() is None:
        if apply:
            try:
                sm.recompile_active()
                result["actions"].append("recompiled_skin")
            except Exception as e:
                _log(f"重新编译材质包失败: {e}")

    a_status = agent_status()
    result["agent"] = a_status
    if a_status == "needs_reapply" and apply:
        asar = Path(agent.get("asar_path") or "")
        if is_antigravity_running() and not allow_when_running:
            result["agent"] = "deferred_running"
            _log("检测到 Antigravity 已被更新覆盖，但程序正在运行，等待其退出后再重新注入。")
        elif not allow_when_running and (recently_modified(asar) or is_updater_running()):
            # 更新器刚替换完（或仍在替换）app.asar：等文件稳定后下一轮再处理
            result["agent"] = "deferred_settling"
            _log("检测到 Antigravity 正在更新，等待更新完成后再重新注入。")
        else:
            lock = _reapply_lock()
            if not lock.acquire():
                result["agent"] = "deferred_locked"
                _log("另一个进程正在重新注入，本次跳过。")
            else:
                try:
                    # 拿到锁后再确认一次：可能另一进程刚刚完成了注入
                    if agent_status() != "needs_reapply":
                        result["agent"] = agent_status()
                    else:
                        _log("检测到 Antigravity 已被更新覆盖，开始自动重新注入汉化与皮肤加载器...")
                        reapply_agent(agent, repo_root=repo_root)
                        result["agent"] = "reapplied"
                        result["actions"].append("reapplied_agent")
                        _log("Agent 桌面端重新注入完成。")
                except Exception as e:
                    result["agent"] = "error"
                    result["error"] = str(e)
                    _log(f"重新注入失败: {e}")
                finally:
                    lock.release()

    ide_root = si.find_ide_app_root()
    i_status = si.ide_status(ide_root)
    result["ide"] = i_status
    if apply and ide_root is not None and i_status in ("needs_reapply", "stale"):
        try:
            si.inject_ide(ide_root)
            result["ide"] = "reapplied"
            result["actions"].append("reapplied_ide")
            _log(f"IDE 工作台皮肤已重新写入: {ide_root}")
        except Exception as e:
            result["ide"] = "error"
            _log(f"IDE 皮肤写入失败: {e}")
    return result


def reapply_agent(agent: dict, repo_root: Path | None = None) -> None:
    import patch_antigravity as pa  # 延迟导入，避免循环
    install_dir = Path(agent["install_dir"])
    pa.apply_patch(
        install_dir,
        agent.get("lang") or "zh-CN",
        repo_root or sm.resource_root(),
        character=agent.get("character"),
        enable_pet=agent.get("enable_pet", True),
        enable_skin=agent.get("enable_skin", True),
        stop_processes=False,
    )
    if sys.platform == "darwin":
        try:
            subprocess.run(["codesign", "--force", "--deep", "-s", "-", str(install_dir)],
                           capture_output=True, timeout=120)
        except Exception:
            pass


def watch(interval: int = 120, once: bool = False) -> None:
    """后台守护：空闲时只做 stat，开销极低。"""
    if not _acquire_single_instance():
        _log("已有一个后台检测实例在运行，本实例退出。")
        return
    _log(f"后台自动重注入守护已启动，每 {interval} 秒检测一次。")
    try:
        while True:
            st = sm.load_state()
            if not st.get("auto_reapply", False):
                # 用户已关闭自动重注入：守护进程直接退出，而不是永远空转
                _log("自动重注入已关闭，后台守护退出。")
                return
            try:
                check(apply=True)
            except Exception as e:
                _log(f"检测异常: {e}")
            if once:
                return
            time.sleep(max(30, interval))
    finally:
        _release_single_instance()


def _pid_alive(pid: int) -> bool:
    return sm._pid_alive(pid)


_INSTANCE_LOCK: "sm.FileLock | None" = None


def _acquire_single_instance() -> bool:
    """后台守护单实例：O_EXCL 锁文件 + 进程存活检测（旧实现先读后写，两个实例同时启动会都通过）。"""
    global _INSTANCE_LOCK
    lock = sm.FileLock(sm.config_dir() / "background.pid", timeout=0, stale=10 ** 9)
    if lock.acquire():
        _INSTANCE_LOCK = lock
        return True
    return False


def _release_single_instance() -> None:
    global _INSTANCE_LOCK
    if _INSTANCE_LOCK is not None:
        _INSTANCE_LOCK.release()
        _INSTANCE_LOCK = None


# ---------------------------------------------------------------------------
# 4. 开机自启（当前用户级）
# ---------------------------------------------------------------------------
def background_command() -> list[str]:
    """后台检测命令：打包版为 exe --background；源码版为 pythonw app/agzh_app.py --background。"""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--background"]
    py = sys.executable
    if sys.platform == "win32":
        cand = Path(py).with_name("pythonw.exe")
        if cand.is_file():
            py = str(cand)
    return [py, str(sm.resource_root() / "app" / "agzh_app.py"), "--background"]


def _mac_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{MAC_LABEL}.plist"


def _linux_desktop_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "autostart" / "antigravity-zh-cn-autoreapply.desktop"


def enable_autostart(cmd: list[str] | None = None) -> str:
    cmd = cmd or background_command()
    sm.update_state(auto_reapply=True)
    if sys.platform == "win32":
        import winreg
        quoted = subprocess.list2cmdline(cmd)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, AUTOSTART_NAME, 0, winreg.REG_SZ, quoted)
        return "已写入 HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    if sys.platform == "darwin":
        # launchd 每 10 分钟拉起一次单次检测，无需常驻进程
        once_cmd = [c for c in cmd if c != "--background"] + ["--check-once"]
        args = "".join(f"\n    <string>{_xml_escape(c)}</string>" for c in once_cmd)
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{MAC_LABEL}</string>
  <key>ProgramArguments</key>
  <array>{args}
  </array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>600</integer>
</dict>
</plist>
"""
        p = _mac_plist_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(plist, encoding="utf-8")
        subprocess.run(["launchctl", "unload", str(p)], capture_output=True)
        subprocess.run(["launchctl", "load", str(p)], capture_output=True)
        return f"已安装 LaunchAgent: {p}"
    p = _linux_desktop_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    exec_line = " ".join(_shell_quote(c) for c in cmd)
    p.write_text("[Desktop Entry]\nType=Application\nName=Antigravity 汉化/皮肤自动重注入\n"
                 f"Exec={exec_line}\nX-GNOME-Autostart-enabled=true\nNoDisplay=true\n", encoding="utf-8")
    return f"已写入 XDG 自启动项: {p}"


def disable_autostart() -> str:
    sm.update_state(auto_reapply=False)
    if sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                                winreg.KEY_SET_VALUE) as k:
                winreg.DeleteValue(k, AUTOSTART_NAME)
        except FileNotFoundError:
            pass
        return "已移除开机自启项"
    if sys.platform == "darwin":
        p = _mac_plist_path()
        if p.exists():
            subprocess.run(["launchctl", "unload", str(p)], capture_output=True)
            p.unlink()
        return "已移除 LaunchAgent"
    p = _linux_desktop_path()
    if p.exists():
        p.unlink()
    return "已移除 XDG 自启动项"


def autostart_enabled() -> bool:
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
                winreg.QueryValueEx(k, AUTOSTART_NAME)
            return True
        except Exception:
            return False
    if sys.platform == "darwin":
        return _mac_plist_path().is_file()
    return _linux_desktop_path().is_file()


def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _shell_quote(s: str) -> str:
    return s if s and all(c.isalnum() or c in "/._-=" for c in s) else '"' + s.replace('"', '\\"') + '"'


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Antigravity 更新后自动重新注入")
    ap.add_argument("--apply", action="store_true", help="发现被覆盖时立即重新注入")
    ap.add_argument("--watch", action="store_true", help="常驻后台检测")
    ap.add_argument("--interval", type=int, default=120)
    a = ap.parse_args()
    if a.watch:
        watch(a.interval)
    else:
        print(json.dumps(check(apply=a.apply), ensure_ascii=False, indent=2))
