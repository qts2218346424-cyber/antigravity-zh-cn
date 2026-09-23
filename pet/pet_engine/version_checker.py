"""
pet_engine/version_checker.py - Antigravity Host & Localization Version Alignment Engine

Features:
- Inspects installed Antigravity app.asar to detect current official host version.
- Verifies if the local app.asar currently contains the Chinese localization patch marker.
- Detects version divergence when Google Antigravity auto-updates and overwrites the patch.
- Queries GitHub releases for new updates to the localization toolset.
- Proactively dispatches formatted toast notifications to the desktop pet with update links.
"""

from __future__ import annotations

import os
import sys
import json
import struct
import urllib.request
import urllib.error
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

PATCH_MARKER = b"__ANTIGRAVITY_ZH_CN_PATCHED__"
GITHUB_API_URL = "https://api.github.com/repos/qts2218346424-cyber/antigravity-zh-cn/releases/latest"
DEFAULT_RELEASE_URL = "https://github.com/qts2218346424-cyber/antigravity-zh-cn/releases"


class VersionChecker:
    """
    Evaluates host Antigravity version, localization patch integrity,
    and upstream GitHub localization releases.
    """

    def __init__(self, repo_root: Optional[Path] = None, cooldown_seconds: float = 7200.0):
        if repo_root is None:
            # Default to repo root relative to this file: pet/pet_engine/ -> repo root
            self.repo_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.repo_root = Path(repo_root)

        self.cooldown_seconds = float(cooldown_seconds)
        self._lock = threading.Lock()
        self._last_alert_time: float = 0.0
        self._last_alert_key: Optional[str] = None

    def get_default_antigravity_dir(self) -> Optional[Path]:
        """Detect default Antigravity installation path on Windows/Mac/Linux."""
        if sys.platform == "win32":
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            if local_app_data:
                candidate = Path(local_app_data) / "Programs" / "antigravity"
                if (candidate / "resources" / "app.asar").is_file():
                    return candidate
                prog_candidate = Path("C:/Program Files/antigravity")
                if (prog_candidate / "resources" / "app.asar").is_file():
                    return prog_candidate
        elif sys.platform == "darwin":
            candidate = Path("/Applications/Antigravity.app")
            if (candidate / "Contents" / "Resources" / "app.asar").is_file():
                return candidate
        else:
            for p in ["/opt/antigravity", str(Path.home() / ".local/share/antigravity"), "/usr/lib/antigravity"]:
                candidate = Path(p)
                if (candidate / "resources" / "app.asar").is_file():
                    return candidate
        return None

    def read_installed_host_info(self, install_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Inspects Antigravity's app.asar to extract host version and patch status.
        """
        target_dir = install_dir or self.get_default_antigravity_dir()
        if not target_dir:
            return {"installed": False, "version": None, "is_patched": False, "error": "NOT_FOUND"}

        asar_path = target_dir / "resources" / "app.asar"
        if not asar_path.is_file():
            # Check macOS bundle location
            asar_path = target_dir / "Contents" / "Resources" / "app.asar"
            if not asar_path.is_file():
                return {"installed": False, "version": None, "is_patched": False, "error": "ASAR_NOT_FOUND"}

        try:
            with open(asar_path, "rb") as f:
                size_bytes = f.read(8)
                if len(size_bytes) < 8:
                    return {"installed": True, "version": None, "is_patched": False, "error": "CORRUPT_ASAR"}
                header_size = struct.unpack_from("<I", size_bytes, 4)[0]
                header_pickle = f.read(header_size)
                header_str_size = struct.unpack_from("<i", header_pickle, 4)[0]
                header_str = header_pickle[8 : 8 + header_str_size].decode("utf-8")
                header = json.loads(header_str)

                # 1. Read package.json version
                version = "unknown"
                files_node = header.get("files", {})
                if "package.json" in files_node:
                    pkg_entry = files_node["package.json"]
                    offset = int(pkg_entry["offset"])
                    size = int(pkg_entry["size"])
                    f.seek(8 + header_size + offset)
                    pkg_bytes = f.read(size)
                    pkg = json.loads(pkg_bytes.decode("utf-8", errors="ignore"))
                    version = pkg.get("version", "unknown")

                # 2. Check if patch marker is present in preload.js or menu.js
                is_patched = False
                dist_files = files_node.get("dist", {}).get("files", {})
                for entry_name in ["preload.js", "menu.js", "utils.js"]:
                    if entry_name in dist_files:
                        entry = dist_files[entry_name]
                        offset = int(entry["offset"])
                        size = int(entry["size"])
                        f.seek(8 + header_size + offset)
                        content = f.read(size)
                        if PATCH_MARKER in content:
                            is_patched = True
                            break

                return {
                    "installed": True,
                    "version": version,
                    "is_patched": is_patched,
                    "install_dir": str(target_dir),
                    "asar_path": str(asar_path)
                }
        except Exception as e:
            return {"installed": True, "version": None, "is_patched": False, "error": str(e)}

    def read_local_localization_version(self) -> Dict[str, Any]:
        """Reads version.json from the localization repository."""
        ver_file = self.repo_root / "resources" / "version.json"
        if ver_file.is_file():
            try:
                with open(ver_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "version": "1.1.0",
            "target_antigravity_version": "2.17.0",
            "release_url": DEFAULT_RELEASE_URL
        }

    def check_remote_github_release(self, timeout: float = 3.0) -> Dict[str, Any]:
        """Checks latest GitHub release tag for the localization repository."""
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"User-Agent": "Antigravity-Pet-Updater", "Accept": "application/vnd.github.v3+json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    tag_name = data.get("tag_name", "").lstrip("v")
                    html_url = data.get("html_url", DEFAULT_RELEASE_URL)
                    body = data.get("name") or data.get("body") or "有新的汉化更新发布"
                    return {
                        "success": True,
                        "remote_version": tag_name,
                        "release_url": html_url,
                        "release_notes": body[:120]
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}

        return {"success": False, "error": "NO_RESPONSE"}

    def evaluate_version_status(
        self,
        install_dir: Optional[Path] = None,
        check_remote: bool = True
    ) -> Dict[str, Any]:
        """
        Synthesizes local host version, patch state, and remote updates.
        Returns a structured event dict if notification is warranted.
        """
        host_info = self.read_installed_host_info(install_dir)
        local_loc = self.read_local_localization_version()

        host_ver = host_info.get("version")
        is_patched = host_info.get("is_patched", False)
        target_ver = local_loc.get("target_antigravity_version", "")
        local_loc_ver = local_loc.get("version", "1.0.0")
        release_url = local_loc.get("release_url", DEFAULT_RELEASE_URL)

        # Case 1: Antigravity installed, but patch marker is missing
        # (Indicates Google updater updated Antigravity and wiped the patch)
        if host_info.get("installed") and not is_patched:
            alert_key = f"unpatched:{host_ver}"
            return {
                "needs_notification": True,
                "event_type": "PATCH_OVERWRITTEN",
                "alert_key": alert_key,
                "level": "warning",
                "title": "Antigravity 官方版本已更新",
                "body": f"检测到 Antigravity 客户端已更新至 v{host_ver}，当前汉化已被官方覆盖。点击运行一键补丁恢复中文！",
                "action_url": release_url,
                "action_text": "获取最新汉化",
                "host_version": host_ver,
                "local_loc_version": local_loc_ver
            }

        # Case 2: Check remote GitHub updates
        if check_remote:
            remote = self.check_remote_github_release(timeout=3.5)
            if remote.get("success") and remote.get("remote_version"):
                remote_ver = remote["remote_version"]
                if self._is_newer_version(remote_ver, local_loc_ver):
                    alert_key = f"new_release:{remote_ver}"
                    return {
                        "needs_notification": True,
                        "event_type": "NEW_LOCALIZATION_RELEASE",
                        "alert_key": alert_key,
                        "level": "info",
                        "title": "发现汉化补丁新版本",
                        "body": f"汉化项目已发布 v{remote_ver}（当前 v{local_loc_ver}）。包含了最新的界面汉化与功能优化！",
                        "action_url": remote.get("release_url", release_url),
                        "action_text": "查看更新详情",
                        "remote_version": remote_ver,
                        "local_loc_version": local_loc_ver
                    }

        return {
            "needs_notification": False,
            "event_type": "HEALTHY",
            "host_version": host_ver,
            "is_patched": is_patched,
            "local_loc_version": local_loc_ver
        }

    def check_and_notify(self, bridge_or_notifier, force: bool = False) -> Optional[Dict[str, Any]]:
        """
        Runs evaluation and dispatches notification via bridge/notifier if needed.
        Respects cooldown unless force is True.
        """
        status = self.evaluate_version_status(check_remote=True)
        if not status.get("needs_notification"):
            return None

        alert_key = status.get("alert_key")
        now = time.monotonic()

        with self._lock:
            if not force:
                if alert_key == self._last_alert_key and (now - self._last_alert_time < self.cooldown_seconds):
                    return None
            self._last_alert_time = now
            self._last_alert_key = alert_key

        # Send notification to Pet UI
        payload = {
            "title": status.get("title", "版本提醒"),
            "body": status.get("body", ""),
            "level": status.get("level", "info"),
            "duration_ms": 10000,
            "action_url": status.get("action_url", ""),
            "action_text": status.get("action_text", "查看详情")
        }

        if hasattr(bridge_or_notifier, "send_notification"):
            bridge_or_notifier.send_notification(payload)
        return payload

    @staticmethod
    def _is_newer_version(remote: str, current: str) -> bool:
        """Compares semver string tuple: returns True if remote > current."""
        try:
            r_parts = [int(x) for x in remote.strip().lstrip("v").split(".") if x.isdigit()]
            c_parts = [int(x) for x in current.strip().lstrip("v").split(".") if x.isdigit()]
            return r_parts > c_parts
        except Exception:
            return remote != current
