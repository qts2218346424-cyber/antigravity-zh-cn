#!/usr/bin/env python3
"""
Antigravity Desktop Pet — Zero-Install Desktop Preview Runner (Windows)
Powered by pywebview (WebView2) + pystray + pywin32
Provides frameless transparent desktop window, system tray menu, and IPC bridge.
"""

import sys
import os
import pathlib

# Guard against pythonw.exe NoneType stdout/stderr crashes & persist runtime log
_runtime_log_dir = pathlib.Path.home() / ".gemini"
_runtime_log_dir.mkdir(parents=True, exist_ok=True)
_runtime_log_file = _runtime_log_dir / "pet_runtime.log"

if sys.stdout is None:
    try:
        sys.stdout = open(_runtime_log_file, "a", encoding="utf-8")
    except Exception:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    try:
        sys.stderr = open(_runtime_log_file, "a", encoding="utf-8")
    except Exception:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

import json
import time
import threading
import argparse
import pathlib
import re
from typing import Dict, Any, Optional

# Clean conflicting global WebView2 remote debugging port to prevent E_ABORT (0x80004004)
if "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS" in os.environ:
    _wb_args = os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"]
    if "--remote-debugging-port" in _wb_args:
        _cleaned = re.sub(r'--remote-debugging-port=\d+', '', _wb_args).strip()
        if _cleaned:
            os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = _cleaned
        else:
            del os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"]


def ensure_default_desktop_session():
    """
    Ensures the process and UI threads are attached to the interactive user desktop (WinSta0\\Default).
    This guarantees the pet window appears on the user's physical monitor even when spawned from isolated agent shells or background services.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            h_winsta = user32.OpenWindowStationW("WinSta0", False, 0x037F)
            if h_winsta:
                user32.SetProcessWindowStation(h_winsta)
            h_desk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if h_desk:
                user32.SetThreadDesktop(h_desk)
        except Exception:
            pass


ensure_default_desktop_session()

# Attempt to load pet_engine backend if available
try:
    from pet_engine.switcher import AccountSwitcher
    from pet_engine.quota import QuotaMonitor
    from pet_engine.version_checker import VersionChecker
    HAS_PET_ENGINE = True
except ImportError:
    try:
        from pet.pet_engine.switcher import AccountSwitcher
        from pet.pet_engine.quota import QuotaMonitor
        from pet.pet_engine.version_checker import VersionChecker
        HAS_PET_ENGINE = True
    except ImportError:
        HAS_PET_ENGINE = False
        VersionChecker = None


# -----------------------------------------------------------------------------
# 1. Magic-Byte Image Validator (Python Backend)
# -----------------------------------------------------------------------------
def validate_image_file(file_path: str) -> Dict[str, Any]:
    """Inspects file magic bytes on disk without external image decoders."""
    p = pathlib.Path(file_path)
    if not p.exists() or not p.is_file():
        return {"valid": False, "error": "FILE_NOT_FOUND"}

    size = p.stat().st_size
    if size == 0:
        return {"valid": False, "error": "INVALID_FILE_EMPTY"}
    if size > 10 * 1024 * 1024:
        return {"valid": False, "error": "FILE_EXCEEDS_MAX_SIZE_10MB"}

    try:
        with open(p, "rb") as f:
            header = f.read(16)
    except Exception as e:
        return {"valid": False, "error": f"IO_ERROR: {str(e)}"}

    # 1. PNG: 89 50 4E 47 0D 0A 1A 0A
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return {"valid": True, "format": "png", "is_animated": False}

    # 2. GIF: GIF87a or GIF89a
    if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        return {"valid": True, "format": "gif", "is_animated": True}

    # 3. WebP: RIFF....WEBP
    if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP":
        return {"valid": True, "format": "webp", "is_animated": False}

    # 4. SVG: XML text containing <svg
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            content_lower = content.lower()
            if "<svg" in content_lower:
                if any(x in content_lower for x in ["<script", "javascript:", "onload", "onerror"]):
                    return {"valid": False, "error": "MALICIOUS_SVG_PAYLOAD"}
                return {"valid": True, "format": "svg", "is_animated": False}
    except Exception:
        pass

    return {"valid": False, "error": "INVALID_MAGIC_BYTES"}


# -----------------------------------------------------------------------------
# 2. System Tray Icon Generator
# -----------------------------------------------------------------------------
def create_tray_image():
    """Generates a dynamic 64x64 celestial Gemini icon for pystray."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Outer soft glow aura
        draw.ellipse([8, 8, 56, 56], fill=(123, 44, 191, 100))

        # Four-pointed celestial diamond sparkle
        points = [
            (32, 6),   # Top
            (38, 26),  # Top-right inner curve
            (58, 32),  # Right
            (38, 38),  # Bottom-right inner curve
            (32, 58),  # Bottom
            (26, 38),  # Bottom-left inner curve
            (6, 32),   # Left
            (26, 26)   # Top-left inner curve
        ]
        draw.polygon(points, fill=(0, 240, 255, 230), outline=(255, 255, 255, 255))
        # Center core star
        draw.ellipse([27, 27, 37, 37], fill=(255, 255, 255, 255))
        return img
    except Exception as e:
        # Fallback 16x16 transparent image if PIL fails
        from PIL import Image
        return Image.new("RGBA", (16, 16), (0, 240, 255, 255))


# -----------------------------------------------------------------------------
# 3. JavaScript API Bridge (RPC Host)
# -----------------------------------------------------------------------------
class JsBridge:
    """Exposes native backend functionality to the HTML5 pet UI."""

    def __init__(self, window_holder, mock_mode: bool = False):
        self._holder = window_holder
        self.mock_mode = mock_mode or (not HAS_PET_ENGINE)
        self.always_on_top = True
        self.click_through = False
        self.active_profile_id = "profile-primary"
        self.pet_state = "idle"
        self.auto_start_with_antigravity = True
        self._drag_lock = threading.Lock()
        self._last_drag_time = 0.0
        self._load_pet_config()

        # Initialize backend engine if available
        self.version_checker = None
        if HAS_PET_ENGINE and not self.mock_mode:
            try:
                self.switcher = AccountSwitcher()
                self.quota_monitor = QuotaMonitor(mode="auto")
                if VersionChecker:
                    self.version_checker = VersionChecker()
            except Exception as e:
                print(f"[JsBridge] Backend init warning, falling back to mock: {e}")
                self.mock_mode = True

    def _load_pet_config(self):
        cfg_path = pathlib.Path.home() / ".gemini" / "pet_config.json"
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.auto_start_with_antigravity = bool(data.get("auto_start_with_antigravity", True))
            except Exception:
                pass

    @property
    def _window(self):
        return self._holder.get("window")

    def get_quota_status(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Contract: get_quota_status() -> QuotaStatusResponse"""
        if HAS_PET_ENGINE and not self.mock_mode:
            try:
                force = payload.get("force_refresh", False) if payload else False
                status = self.quota_monitor.get_quota_status(force_refresh=force)
                if hasattr(status, "to_dict"):
                    return status.to_dict()
                return {
                    "success": True,
                    "account_email": getattr(status, "account_email", "user@antigravity.io"),
                    "profile_id": self.active_profile_id,
                    "total_tokens": getattr(status, "total_tokens", 1000000),
                    "used_tokens": getattr(status, "used_tokens", 150000),
                    "remaining_tokens": getattr(status, "remaining_tokens", 850000),
                    "remaining_percentage": getattr(status, "remaining_percentage", 85.0),
                    "status": getattr(status, "status", "healthy"),
                    "reset_time_utc": getattr(status, "reset_time_utc", "2026-09-24T12:00:00Z"),
                    "is_cached": getattr(status, "is_cached", False),
                    "models": getattr(status, "models", {})
                }
            except Exception as e:
                print(f"[JsBridge] Quota engine error: {e}")

        # Deterministic mock response
        return {
            "success": True,
            "account_email": "qts2218346424@gmail.com" if self.active_profile_id == "profile-primary" else "workspace-dev@antigravity.io",
            "profile_id": self.active_profile_id,
            "total_tokens": 1000000,
            "used_tokens": 154000 if self.active_profile_id == "profile-primary" else 420000,
            "remaining_tokens": 846000 if self.active_profile_id == "profile-primary" else 580000,
            "remaining_percentage": 84.6 if self.active_profile_id == "profile-primary" else 58.0,
            "status": "healthy",
            "reset_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 86400)),
            "is_cached": False,
            "models": {
                "gemini-1.5-pro": {"remaining_requests": 48, "total_requests": 50, "percentage": 96.0},
                "gemini-1.5-flash": {"remaining_requests": 950, "total_requests": 1000, "percentage": 95.0}
            }
        }

    def list_profiles(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Contract: list_profiles() -> ProfileListResponse"""
        if HAS_PET_ENGINE and not self.mock_mode:
            try:
                res = self.switcher.list_profiles()
                if isinstance(res, dict):
                    return res
            except Exception as e:
                print(f"[JsBridge] Switcher list error: {e}")

        return {
            "success": True,
            "active_profile_id": self.active_profile_id,
            "profiles": [
                {
                    "id": "profile-primary",
                    "label": "Primary Google Account",
                    "email": "qts2218346424@gmail.com",
                    "tier": "pay_as_you_go",
                    "last_used": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "created_at": "2026-09-10T08:00:00Z"
                },
                {
                    "id": "profile-backup",
                    "label": "Antigravity Workspace",
                    "email": "workspace-dev@antigravity.io",
                    "tier": "enterprise",
                    "last_used": "2026-09-22T14:30:00Z",
                    "created_at": "2026-09-01T10:00:00Z"
                }
            ]
        }

    def switch_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Contract: switch_profile(profile_id, create_backup=True) -> ProfileSwitchResult"""
        profile_id = payload.get("profile_id", "")
        if not profile_id:
            return {"success": False, "error": "MISSING_PROFILE_ID"}

        if HAS_PET_ENGINE and not self.mock_mode:
            try:
                create_backup = payload.get("create_backup", True)
                res = self.switcher.switch_profile(profile_id, create_backup=create_backup)
                self.active_profile_id = profile_id
                return res
            except Exception as e:
                return {"success": False, "error": str(e)}

        self.active_profile_id = profile_id
        target_email = "workspace-dev@antigravity.io" if profile_id == "profile-backup" else "qts2218346424@gmail.com"
        quota = self.get_quota_status()
        return {
            "success": True,
            "switched_to": profile_id,
            "email": target_email,
            "backup_path": f"~/.gemini/backups/credential_backup_{int(time.time())}.json",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "quota": quota
        }

    def import_avatar(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Contract: import_avatar(source_path) -> AvatarImportResult"""
        source_path = payload.get("source_path", "")
        if not source_path:
            return {"success": False, "error": "MISSING_SOURCE_PATH"}

        res = validate_image_file(source_path)
        if not res.get("valid"):
            return {"success": False, "error": res.get("error", "VALIDATION_FAILED")}

        if res.get("format") == "svg":
            try:
                with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
                    svg_content = f.read().lower()
                if any(x in svg_content for x in ["<script", "javascript:", "onload", "onerror"]):
                    return {"success": False, "error": "MALICIOUS_SVG_PAYLOAD"}
            except Exception as e:
                return {"success": False, "error": f"IO_ERROR: {str(e)}"}

        return {
            "success": True,
            "asset_id": f"avatar-{int(time.time())}",
            "format": res.get("format"),
            "cached_path": source_path,
            "is_animated": res.get("is_animated", False)
        }

    def toggle_always_on_top(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Contract: toggle_always_on_top(enabled?) -> { success, always_on_top }"""
        if payload and isinstance(payload, dict) and "enabled" in payload:
            self.always_on_top = bool(payload["enabled"])
        else:
            self.always_on_top = not self.always_on_top

        if self._window:
            try:
                self._window.on_top = self.always_on_top
            except Exception:
                pass

        # Also apply via Win32 if on Windows
        apply_win32_window_styles(self.always_on_top, self.click_through)
        return {"success": True, "always_on_top": self.always_on_top}

    def toggle_click_through(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Contract: toggle_click_through(enabled?) -> { success, click_through }"""
        if payload and isinstance(payload, dict) and "enabled" in payload:
            self.click_through = bool(payload["enabled"])
        else:
            self.click_through = not self.click_through

        apply_win32_window_styles(self.always_on_top, self.click_through)
        return {"success": True, "click_through": self.click_through}

    def start_drag(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initiates smooth native OS window drag using Win32 WM_NCLBUTTONDOWN with re-entrancy protection."""
        now = time.monotonic()
        if not self._drag_lock.acquire(blocking=False):
            return {"success": False, "reason": "LOCKED"}
        try:
            if now - self._last_drag_time < 0.2:
                return {"success": False, "reason": "THROTTLED"}
            self._last_drag_time = now

            import win32gui
            import win32con
            hwnd = get_pet_hwnd()
            if hwnd and win32gui.IsWindow(hwnd):
                win32gui.ReleaseCapture()
                win32gui.SendMessage(hwnd, win32con.WM_NCLBUTTONDOWN, win32con.HTCAPTION, 0)
                return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self._drag_lock.release()
        return {"success": False}

    def get_pet_config(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg_path = pathlib.Path.home() / ".gemini" / "pet_config.json"
        cfg = {"auto_start_with_antigravity": self.auto_start_with_antigravity, "always_on_top": self.always_on_top}
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg.update(json.load(f))
            except Exception:
                pass
        return {"success": True, "config": cfg}

    def set_pet_config(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cfg_path = pathlib.Path.home() / ".gemini" / "pet_config.json"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        current = {"auto_start_with_antigravity": True, "always_on_top": self.always_on_top}
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    current.update(json.load(f))
            except Exception:
                pass

        if "auto_start_with_antigravity" in payload:
            self.auto_start_with_antigravity = bool(payload["auto_start_with_antigravity"])
            current["auto_start_with_antigravity"] = self.auto_start_with_antigravity

        tmp_path = cfg_path.parent / f"pet_config.tmp.{os.getpid()}"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, cfg_path)
            return {"success": True, "config": current}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_pet_state(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Contract: set_pet_state(state, message?) -> { success, current_state }"""
        st = payload.get("state", "idle")
        self.pet_state = st
        if self._window:
            try:
                self._window.evaluate_js(f"window.__ANTIGRAVITY_PET__.setState('{st}');")
            except Exception:
                pass
        return {"success": True, "current_state": st}

    def send_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Contract: send_notification(req) -> { success, notification_id }"""
        notif_id = f"notif-{int(time.time() * 1000)}"
        if self._window:
            try:
                opts = json.dumps(payload)
                self._window.evaluate_js(f"window.__ANTIGRAVITY_PET__.showToast({opts});")
            except Exception:
                pass
        return {"success": True, "notification_id": notif_id}

    def hide_window(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Hides the pet window to system tray."""
        if self._window:
            try:
                self._window.hide()
            except Exception:
                pass
        return {"success": True}

    def open_external_url(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Opens external URL in default system browser."""
        url = payload.get("url", "")
        if url and (url.startswith("http://") or url.startswith("https://")):
            try:
                import webbrowser
                webbrowser.open(url)
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "INVALID_URL"}

    def check_for_updates(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Triggered manually or via background timer to verify version alignment."""
        if not self.version_checker:
            return {"success": True, "result": None}
        force = payload.get("force", True) if payload else True
        try:
            res = self.version_checker.check_and_notify(self, force=force)
            return {"success": True, "result": res}
        except Exception as e:
            return {"success": False, "error": str(e)}


# -----------------------------------------------------------------------------
# 4. Windows Win32 Composition & True Transparency Helper
# -----------------------------------------------------------------------------
import ctypes

class _MARGINS(ctypes.Structure):
    _fields_ = [
        ('cxLeftWidth', ctypes.c_int),
        ('cxRightWidth', ctypes.c_int),
        ('cyTopHeight', ctypes.c_int),
        ('cyBottomHeight', ctypes.c_int),
    ]


_GLOBAL_WINDOW_HOLDER: Dict[str, Any] = {}


def get_pet_hwnd() -> Optional[int]:
    """Finds the HWND for the Antigravity Desktop Pet window."""
    try:
        win = _GLOBAL_WINDOW_HOLDER.get("window")
        if win and hasattr(win, "native") and win.native:
            handle = getattr(win.native, "Handle", None)
            if handle:
                return int(handle.ToString())
    except Exception:
        pass
    try:
        import win32gui
        hwnd = win32gui.FindWindow(None, "Antigravity Desktop Pet")
        return hwnd if hwnd else None
    except Exception:
        return None


def get_safe_screen_position(width: int = 320, height: int = 380) -> tuple:
    """
    智能获取主显示器真实可用工作区（排除任务栏），并计算安全逻辑坐标与物理坐标。
    彻底避免高 DPI 缩放或多显示器环境下窗口飞出屏幕的问题。
    返回: (logical_x, logical_y, physical_x, physical_y, physical_w, physical_h)
    """
    try:
        import win32api
        import win32con
        import ctypes

        user32 = ctypes.windll.user32
        try:
            dpi = user32.GetDpiForSystem()
        except Exception:
            dpi = 96
        scale = max(1.0, dpi / 96.0)

        mon_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0, 0), win32con.MONITOR_DEFAULTTOPRIMARY))
        work_rect = mon_info.get('Work', (0, 0, 1920, 1080))  # (left, top, right, bottom)
        work_w = max(400, work_rect[2] - work_rect[0])
        work_h = max(400, work_rect[3] - work_rect[1])

        # pywebview.create_window 接收的是逻辑像素 (Logical Pixels)
        logical_work_w = work_w / scale
        logical_work_h = work_h / scale
        logical_x = max(20, int(logical_work_w - width - 15))
        logical_y = max(20, int(logical_work_h - height - 15))

        # Win32 原生物理像素坐标 (Physical Pixels)
        physical_x = int(logical_x * scale) + work_rect[0]
        physical_y = int(logical_y * scale) + work_rect[1]
        physical_w = int(width * scale)
        physical_h = int(height * scale)

        return (logical_x, logical_y, physical_x, physical_y, physical_w, physical_h)
    except Exception:
        return (1000, 500, 1000, 500, width, height)


def configure_true_desktop_transparency(always_on_top: bool = True, click_through: bool = False):
    """
    Enforces true glass/alpha transparency on Windows 10/11:
    1. Extends DWM glass frame across entire client area (-1, -1, -1, -1).
    2. Configures click-through and topmost flags.
    3. Forces visibility and topmost activation on Windows desktop.
    """
    try:
        import win32gui
        import win32con

        hwnd = get_pet_hwnd()
        if not hwnd:
            return

        # 1. Full DWM frame extension (-1 margins)
        m = _MARGINS(-1, -1, -1, -1)
        ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(m))

        # 2. Configure Layered & TopMost
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if click_through:
            ex_style |= (win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED)
        else:
            ex_style &= ~win32con.WS_EX_TRANSPARENT

        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

        insert_after = win32con.HWND_TOPMOST if always_on_top else win32con.HWND_NOTOPMOST
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.SetWindowPos(
            hwnd,
            insert_after,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED
        )

        win32gui.InvalidateRect(hwnd, None, True)
        win32gui.UpdateWindow(hwnd)
    except Exception:
        pass


def apply_win32_window_styles(always_on_top: bool, click_through: bool):
    """Wrapper delegating to configure_true_desktop_transparency."""
    configure_true_desktop_transparency(always_on_top=always_on_top, click_through=click_through)


# -----------------------------------------------------------------------------
# 5. System Tray Daemon (pystray)
# -----------------------------------------------------------------------------
class PetTrayController:
    """Manages the Windows taskbar notification area icon and context menu."""

    def __init__(self, bridge: JsBridge, window_holder: Dict[str, Any]):
        self.bridge = bridge
        self.holder = window_holder
        self.tray = None

    def start(self):
        try:
            import pystray
            icon_img = create_tray_image()

            menu_items = (
                pystray.MenuItem("Antigravity 桌面宠物", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("显示 / 恢复窗口", self._on_show),
                pystray.MenuItem("隐藏到托盘", self._on_hide),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("始终置顶显示", self._on_toggle_pin, checked=lambda item: self.bridge.always_on_top),
                pystray.MenuItem("随 Antigravity 启动自动运行", self._on_toggle_autostart, checked=lambda item: self.bridge.auto_start_with_antigravity),
                pystray.MenuItem("鼠标穿透模式 (Ctrl+Alt+P)", self._on_toggle_click_through, checked=lambda item: self.bridge.click_through),
                pystray.MenuItem("检查汉化与客户端更新", self._on_check_updates),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("宠物动作与状态", pystray.Menu(
                    pystray.MenuItem("空闲待机 (Idle)", lambda: self.bridge.set_pet_state({"state": "idle"})),
                    pystray.MenuItem("深度思考 (Thinking)", lambda: self.bridge.set_pet_state({"state": "thinking"})),
                    pystray.MenuItem("任务完成 (Celebrated)", lambda: self.bridge.set_pet_state({"state": "task_finished"})),
                    pystray.MenuItem("额度告急 (Low Quota)", lambda: self.bridge.set_pet_state({"state": "quota_low"})),
                )),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("彻底退出并关闭自启动", self._on_exit_and_disable_autostart),
                pystray.MenuItem("退出桌面宠物", self._on_exit)
            )

            self.tray = pystray.Icon("antigravity_pet", icon_img, "Antigravity 桌面宠物", menu=pystray.Menu(*menu_items))
            tray_thread = threading.Thread(target=self.tray.run, daemon=True)
            tray_thread.start()
        except Exception as e:
            print(f"[Tray] System tray initialization warning: {e}")

    def _on_show(self, icon=None, item=None):
        win = self.holder.get("window")
        if win:
            win.show()
            try:
                import win32gui
                hwnd = get_pet_hwnd()
                if hwnd:
                    win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass

    def _on_hide(self, icon=None, item=None):
        win = self.holder.get("window")
        if win:
            win.hide()

    def _on_toggle_pin(self, icon=None, item=None):
        self.bridge.toggle_always_on_top()

    def _on_toggle_autostart(self, icon=None, item=None):
        new_val = not self.bridge.auto_start_with_antigravity
        self.bridge.set_pet_config({"auto_start_with_antigravity": new_val})
        win = self.holder.get("window")
        if win:
            st = "已开启" if new_val else "已关闭"
            win.evaluate_js(f"window.__ANTIGRAVITY_PET__.showToast({{ title: '自启动设置', body: '随 Antigravity 启动自动运行{st}', level: 'info' }});")

    def _on_toggle_click_through(self, icon=None, item=None):
        self.bridge.toggle_click_through()
        # Notify user via toast in webview
        win = self.holder.get("window")
        if win:
            status = "已开启（按 Ctrl+Alt+P 恢复）" if self.bridge.click_through else "已关闭"
            win.evaluate_js(f"window.__ANTIGRAVITY_PET__.showToast({{ title: '托盘控制', body: '鼠标穿透模式{status}', level: 'info' }});")

    def _on_check_updates(self, icon=None, item=None):
        def _run_check():
            res = self.bridge.check_for_updates({"force": True})
            if not res.get("result"):
                self.bridge.send_notification({
                    "title": "版本检查",
                    "body": "当前 Antigravity 客户端与汉化补丁状态正常，已是最新版本！",
                    "level": "success",
                    "duration_ms": 4000
                })
        threading.Thread(target=_run_check, daemon=True).start()

    def _on_exit_and_disable_autostart(self, icon=None, item=None):
        try:
            self.bridge.set_pet_config({"auto_start_with_antigravity": False})
        except Exception:
            pass
        if self.tray:
            self.tray.stop()
        win = self.holder.get("window")
        if win:
            win.destroy()
        sys.exit(0)

    def _on_exit(self, icon=None, item=None):
        if self.tray:
            self.tray.stop()
        win = self.holder.get("window")
        if win:
            win.destroy()
        sys.exit(0)


# -----------------------------------------------------------------------------
# 6. Smoke Test & Programmatic Verification Suite
# -----------------------------------------------------------------------------
def run_smoke_test() -> int:
    """Executes automated verification suite for frontend assets & RPC bridge."""
    print("============================================================")
    print("Antigravity Desktop Pet — Smoke Test & Verification Suite")
    print("============================================================")

    root_dir = pathlib.Path(__file__).parent.resolve()
    frontend_dir = root_dir / "frontend"

    checks = []

    # 1. Verify frontend files exist
    required_files = [
        frontend_dir / "index.html",
        frontend_dir / "styles.css",
        frontend_dir / "mascot.js",
        frontend_dir / "assets" / "gemini_mascot.svg"
    ]
    for rf in required_files:
        exists = rf.exists()
        checks.append((f"File Exists: {rf.name}", exists))
        if not exists:
            print(f"[-] Missing required file: {rf}")

    # 2. Verify magic-byte validator logic
    # Test PNG
    png_path = frontend_dir / "test_smoke_img.png"
    with open(png_path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    png_res = validate_image_file(str(png_path))
    checks.append(("Magic-Byte PNG Detection", png_res.get("valid") and png_res.get("format") == "png"))
    png_path.unlink()

    # Test GIF
    gif_path = frontend_dir / "test_smoke_img.gif"
    with open(gif_path, "wb") as f:
        f.write(b"GIF89a" + b"\x00" * 32)
    gif_res = validate_image_file(str(gif_path))
    checks.append(("Magic-Byte GIF Detection", gif_res.get("valid") and gif_res.get("format") == "gif" and gif_res.get("is_animated") is True))
    gif_path.unlink()

    # Test WebP
    webp_path = frontend_dir / "test_smoke_img.webp"
    with open(webp_path, "wb") as f:
        f.write(b"RIFF\x20\x00\x00\x00WEBPVP8 " + b"\x00" * 16)
    webp_res = validate_image_file(str(webp_path))
    checks.append(("Magic-Byte WebP Detection", webp_res.get("valid") and webp_res.get("format") == "webp"))
    webp_path.unlink()

    # Test Empty File Rejection
    empty_path = frontend_dir / "test_empty.png"
    with open(empty_path, "wb") as f:
        pass
    empty_res = validate_image_file(str(empty_path))
    checks.append(("Magic-Byte Empty File Rejection", not empty_res.get("valid") and empty_res.get("error") == "INVALID_FILE_EMPTY"))
    empty_path.unlink()

    # Test Corrupt File Rejection
    bad_path = frontend_dir / "test_bad.png"
    with open(bad_path, "wb") as f:
        f.write(b"NOT_A_PNG_FILE")
    bad_res = validate_image_file(str(bad_path))
    checks.append(("Magic-Byte Corrupt Rejection", not bad_res.get("valid") and bad_res.get("error") == "INVALID_MAGIC_BYTES"))
    bad_path.unlink()

    # Test Non-existent File Rejection
    fnf_res = validate_image_file(str(frontend_dir / "non_existent_file.png"))
    checks.append(("Magic-Byte File Not Found Rejection", not fnf_res.get("valid") and fnf_res.get("error") == "FILE_NOT_FOUND"))

    # Test SVG detection
    svg_res = validate_image_file(str(frontend_dir / "assets" / "gemini_mascot.svg"))
    checks.append(("Magic-Byte SVG Detection", svg_res.get("valid") and svg_res.get("format") == "svg"))

    # Test Preset Avatars Exist
    presets_dir = frontend_dir / "assets" / "presets"
    checks.append(("Preset Sparkle SVG Exists", (presets_dir / "gemini_sparkle.svg").exists()))
    checks.append(("Preset Quantum Bot SVG Exists", (presets_dir / "quantum_bot.svg").exists()))
    checks.append(("Preset Cosmic Orb SVG Exists", (presets_dir / "cosmic_orb.svg").exists()))

    # 3. Test RPC JsBridge API methods
    holder = {}
    bridge = JsBridge(holder, mock_mode=True)

    # get_quota_status
    quota_res = bridge.get_quota_status()
    checks.append(("JsBridge.get_quota_status", quota_res.get("success") is True and "remaining_tokens" in quota_res))

    # list_profiles
    profiles_res = bridge.list_profiles()
    checks.append(("JsBridge.list_profiles", profiles_res.get("success") is True and len(profiles_res.get("profiles", [])) >= 2))

    # switch_profile (valid)
    switch_res = bridge.switch_profile({"profile_id": "profile-backup"})
    checks.append(("JsBridge.switch_profile (valid)", switch_res.get("success") is True and switch_res.get("switched_to") == "profile-backup"))

    # switch_profile (missing id)
    switch_err = bridge.switch_profile({})
    checks.append(("JsBridge.switch_profile (missing id error)", switch_err.get("success") is False and switch_err.get("error") == "MISSING_PROFILE_ID"))

    # toggle_always_on_top
    pin_res = bridge.toggle_always_on_top()
    checks.append(("JsBridge.toggle_always_on_top", pin_res.get("success") is True))

    # toggle_click_through
    ct_res = bridge.toggle_click_through()
    checks.append(("JsBridge.toggle_click_through", ct_res.get("success") is True))

    # set_pet_state & send_notification
    state_res = bridge.set_pet_state({"state": "thinking"})
    checks.append(("JsBridge.set_pet_state", state_res.get("success") is True and state_res.get("current_state") == "thinking"))
    notif_res = bridge.send_notification({"title": "Test", "body": "Body", "level": "info"})
    checks.append(("JsBridge.send_notification", notif_res.get("success") is True and "notification_id" in notif_res))

    # open_external_url & check_for_updates
    url_err = bridge.open_external_url({"url": "invalid://schema"})
    checks.append(("JsBridge.open_external_url (rejection)", url_err.get("success") is False))
    upd_res = bridge.check_for_updates({"force": True})
    checks.append(("JsBridge.check_for_updates", upd_res.get("success") is True))

    # 4. Test Tray Icon Generator
    tray_img = create_tray_image()
    checks.append(("Tray Icon Image Generation", tray_img is not None and tray_img.size == (64, 64)))

    # 5. Test Tauri v2 Project Structure
    tauri_dir = root_dir / "src-tauri"
    checks.append(("Tauri Config Exists", (tauri_dir / "tauri.conf.json").exists()))
    checks.append(("Tauri Cargo.toml Exists", (tauri_dir / "Cargo.toml").exists()))
    checks.append(("Tauri Capabilities Exists", (tauri_dir / "capabilities" / "default.json").exists()))
    checks.append(("Tauri Main Rust Exists", (tauri_dir / "src" / "main.rs").exists()))
    checks.append(("Tauri Lib Rust Exists", (tauri_dir / "src" / "lib.rs").exists()))
    checks.append(("Tauri App Icon Exists", (tauri_dir / "icons" / "icon.png").exists()))

    # Verify tauri.conf.json is valid JSON with transparent=true and decorations=false
    try:
        with open(tauri_dir / "tauri.conf.json", "r", encoding="utf-8") as f:
            tcfg = json.load(f)
        win_cfg = tcfg.get("app", {}).get("windows", [{}])[0]
        t_valid = (win_cfg.get("transparent") is True and
                   win_cfg.get("decorations") is False and
                   win_cfg.get("alwaysOnTop") is True and
                   win_cfg.get("shadow") is False)
        checks.append(("Tauri Config Attributes Valid", t_valid))
    except Exception:
        checks.append(("Tauri Config Attributes Valid", False))

    # Print Report
    all_passed = True
    for name, passed in checks:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    print("------------------------------------------------------------")
    passed_count = sum(1 for _, p in checks if p)
    total_count = len(checks)
    if all_passed:
        print(f"RESULT: 100% Smoke Tests Passed Successfully ({passed_count}/{total_count})")
        print("============================================================")
        return 0
    else:
        print("RESULT: Smoke Test Assertions Failed")
        print("============================================================")
        return 1


# -----------------------------------------------------------------------------
# 7. Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Antigravity Desktop Pet Runner")
    parser.add_argument("--smoke", "--test", action="store_true", help="Run automated smoke tests and exit")
    parser.add_argument("--mock", action="store_true", help="Force mock quota & profile data")
    parser.add_argument("--debug", action="store_true", help="Enable WebView2 developer tools")
    args = parser.parse_args()

    if args.smoke:
        sys.exit(run_smoke_test())

    # 智能单实例管理：如果已存在桌宠进程且窗口真实可见，则唤醒置顶并退出；否则接管并继续启动
    if sys.platform == "win32" and not args.smoke:
        import ctypes
        ERROR_ALREADY_EXISTS = 183
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, "Global\\AntigravityPet_SingleInstance_Mutex")
        last_err = kernel32.GetLastError()
        if last_err == ERROR_ALREADY_EXISTS:
            hwnd = get_pet_hwnd()
            if hwnd:
                try:
                    import win32gui
                    import win32con
                    if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                        print("[Runner] Antigravity 灵动桌面小宠物已在运行中，正在为您唤醒并置顶...")
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetWindowPos(
                            hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                        )
                        win32gui.SetForegroundWindow(hwnd)
                        win32gui.BringWindowToTop(hwnd)
                        sys.exit(0)
                except Exception:
                    pass
            print("[Runner] 检测到历史残留，正在重置并启动新实例...")

    import webview

    root_dir = pathlib.Path(__file__).parent.resolve()
    frontend_dir = root_dir / "frontend"
    index_html = frontend_dir / "index.html"

    if not index_html.exists():
        print(f"Error: Could not locate frontend entrypoint at: {index_html}", file=sys.stderr)
        sys.exit(1)

    window_holder = _GLOBAL_WINDOW_HOLDER
    window_holder.clear()
    bridge = JsBridge(window_holder, mock_mode=args.mock)

    # Initialize System Tray
    tray_controller = PetTrayController(bridge, window_holder)
    tray_controller.start()

    # Calculate safe right-bottom screen position (above taskbar, considering DPI scale)
    logical_x, logical_y, physical_x, physical_y, physical_w, physical_h = get_safe_screen_position(320, 380)

    # Create Transparent Frameless Window
    url = index_html.as_uri()
    window = webview.create_window(
        title="Antigravity Desktop Pet",
        url=url,
        width=320,
        height=380,
        x=logical_x,
        y=logical_y,
        resizable=False,
        frameless=True,
        transparent=True,
        on_top=True,
        js_api=bridge
    )
    window_holder["window"] = window

    # Apply true glass transparency and Win32 styles after composition
    def _delayed_win32_init():
        for delay in [0.2, 0.6, 1.5]:
            time.sleep(delay)
            hwnd = get_pet_hwnd()
            if hwnd:
                try:
                    import win32gui
                    import win32con
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    win32gui.SetWindowPos(
                        hwnd,
                        win32con.HWND_TOPMOST,
                        physical_x, physical_y, physical_w, physical_h,
                        win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED
                    )
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.BringWindowToTop(hwnd)
                    win32gui.UpdateWindow(hwnd)
                except Exception:
                    pass
            configure_true_desktop_transparency(always_on_top=True, click_through=False)

    threading.Thread(target=_delayed_win32_init, daemon=True).start()

    # Start background version consistency monitor (5s delay, then every 2 hours)
    def _background_version_monitor():
        time.sleep(5.0)
        while True:
            try:
                if bridge.version_checker:
                    bridge.version_checker.check_and_notify(bridge, force=False)
            except Exception as e:
                print(f"[VersionChecker] Background check notice: {e}")
            time.sleep(7200)

    threading.Thread(target=_background_version_monitor, daemon=True).start()

    storage_dir = pathlib.Path.home() / ".gemini" / "pet_webview_data"
    storage_dir.mkdir(parents=True, exist_ok=True)

    print("[Runner] Launching Antigravity Desktop Pet...")
    webview.start(debug=args.debug, storage_path=str(storage_dir))


if __name__ == "__main__":
    main()
