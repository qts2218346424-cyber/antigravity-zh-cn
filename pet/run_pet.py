#!/usr/bin/env python3
"""
Antigravity Desktop Pet — Zero-Install Desktop Preview Runner (Windows)
Powered by pywebview (WebView2) + pystray + pywin32
Provides frameless transparent desktop window, system tray menu, and IPC bridge.
"""

import sys
import os
import json
import time
import threading
import argparse
import pathlib
from typing import Dict, Any, Optional

# Attempt to load pet_engine backend if available
try:
    from pet_engine.switcher import AccountSwitcher
    from pet_engine.quota import QuotaMonitor
    HAS_PET_ENGINE = True
except ImportError:
    HAS_PET_ENGINE = False


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

        # Initialize backend engine if available
        if HAS_PET_ENGINE and not self.mock_mode:
            try:
                self.switcher = AccountSwitcher()
                self.quota_monitor = QuotaMonitor(mode="auto")
            except Exception as e:
                print(f"[JsBridge] Backend init warning, falling back to mock: {e}")
                self.mock_mode = True

    @property
    def window(self):
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

        if self.window:
            try:
                self.window.on_top = self.always_on_top
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

    def set_pet_state(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Contract: set_pet_state(state, message?) -> { success, current_state }"""
        st = payload.get("state", "idle")
        self.pet_state = st
        if self.window:
            try:
                self.window.evaluate_js(f"window.__ANTIGRAVITY_PET__.setState('{st}');")
            except Exception:
                pass
        return {"success": True, "current_state": st}

    def send_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Contract: send_notification(req) -> { success, notification_id }"""
        notif_id = f"notif-{int(time.time() * 1000)}"
        if self.window:
            try:
                opts = json.dumps(payload)
                self.window.evaluate_js(f"window.__ANTIGRAVITY_PET__.showToast({opts});")
            except Exception:
                pass
        return {"success": True, "notification_id": notif_id}

    def hide_window(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Hides the pet window to system tray."""
        if self.window:
            try:
                self.window.hide()
            except Exception:
                pass
        return {"success": True}


# -----------------------------------------------------------------------------
# 4. Windows Win32 Composition & Transparency Helper
# -----------------------------------------------------------------------------
def get_pet_hwnd() -> Optional[int]:
    """Finds the HWND for the Antigravity Desktop Pet window."""
    try:
        import win32gui
        hwnd = win32gui.FindWindow(None, "Antigravity Desktop Pet")
        return hwnd if hwnd else None
    except Exception:
        return None


def apply_win32_window_styles(always_on_top: bool, click_through: bool):
    """Configures HWND styles for click-through and topmost composition."""
    try:
        import win32gui
        import win32con

        hwnd = get_pet_hwnd()
        if not hwnd:
            return

        # 1. Update Click-Through (WS_EX_TRANSPARENT)
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if click_through:
            ex_style |= (win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED)
        else:
            ex_style &= ~win32con.WS_EX_TRANSPARENT

        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

        # 2. Update Always-on-Top (HWND_TOPMOST)
        insert_after = win32con.HWND_TOPMOST if always_on_top else win32con.HWND_NOTOPMOST
        win32gui.SetWindowPos(
            hwnd,
            insert_after,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE | win32con.SWP_FRAMECHANGED
        )
    except Exception as e:
        # Non-fatal on non-Windows or development environments
        pass


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
                pystray.MenuItem("Antigravity Pet", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Show / Restore", self._on_show),
                pystray.MenuItem("Hide Pet", self._on_hide),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Always on Top", self._on_toggle_pin, checked=lambda item: self.bridge.always_on_top),
                pystray.MenuItem("Click-Through Mode", self._on_toggle_click_through, checked=lambda item: self.bridge.click_through),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Mascot State", pystray.Menu(
                    pystray.MenuItem("Idle", lambda: self.bridge.set_pet_state({"state": "idle"})),
                    pystray.MenuItem("Thinking", lambda: self.bridge.set_pet_state({"state": "thinking"})),
                    pystray.MenuItem("Task Finished", lambda: self.bridge.set_pet_state({"state": "task_finished"})),
                    pystray.MenuItem("Low Quota", lambda: self.bridge.set_pet_state({"state": "quota_low"})),
                )),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self._on_exit)
            )

            self.tray = pystray.Icon("antigravity_pet", icon_img, "Antigravity Desktop Pet", menu=pystray.Menu(*menu_items))
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

    def _on_toggle_click_through(self, icon=None, item=None):
        self.bridge.toggle_click_through()
        # Notify user via toast in webview
        win = self.holder.get("window")
        if win:
            status = "enabled" if self.bridge.click_through else "disabled"
            win.evaluate_js(f"window.__ANTIGRAVITY_PET__.showToast({{ title: 'Tray Control', body: 'Click-through mode {status}.', level: 'info' }});")

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

    import webview

    root_dir = pathlib.Path(__file__).parent.resolve()
    frontend_dir = root_dir / "frontend"
    index_html = frontend_dir / "index.html"

    if not index_html.exists():
        print(f"Error: Could not locate frontend entrypoint at: {index_html}", file=sys.stderr)
        sys.exit(1)

    window_holder = {}
    bridge = JsBridge(window_holder, mock_mode=args.mock)

    # Initialize System Tray
    tray_controller = PetTrayController(bridge, window_holder)
    tray_controller.start()

    # Create Transparent Frameless Window
    url = index_html.as_uri()
    window = webview.create_window(
        title="Antigravity Desktop Pet",
        url=url,
        width=320,
        height=380,
        resizable=False,
        frameless=True,
        transparent=True,
        on_top=True,
        js_api=bridge
    )
    window_holder["window"] = window

    # Apply initial Win32 styles after brief composition delay
    def _delayed_win32_init():
        time.sleep(1.0)
        apply_win32_window_styles(always_on_top=True, click_through=False)

    threading.Thread(target=_delayed_win32_init, daemon=True).start()

    print("[Runner] Launching Antigravity Desktop Pet...")
    webview.start(debug=args.debug)


if __name__ == "__main__":
    main()
