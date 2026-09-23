"""
Unit tests for pet_engine/version_checker.py
Verifies Antigravity host version reading, patch status inspection,
semver comparison, cooldown logic, and update notification dispatch.
"""

import os
import sys
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add pet/ to sys.path
PET_DIR = Path(__file__).resolve().parent.parent
if str(PET_DIR) not in sys.path:
    sys.path.insert(0, str(PET_DIR))

from pet_engine.version_checker import VersionChecker, PATCH_MARKER


def build_mock_asar(files_dict: dict) -> bytes:
    """Helper to build a valid minimal Electron ASAR binary archive."""
    header_files = {}
    body_parts = []
    current_offset = 0

    for fname, content in files_dict.items():
        if isinstance(content, str):
            data = content.encode("utf-8")
        else:
            data = content

        if "/" in fname:
            dir_name, base_name = fname.split("/", 1)
            if dir_name not in header_files:
                header_files[dir_name] = {"files": {}}
            header_files[dir_name]["files"][base_name] = {
                "size": len(data),
                "offset": str(current_offset)
            }
        else:
            header_files[fname] = {
                "size": len(data),
                "offset": str(current_offset)
            }

        body_parts.append(data)
        current_offset += len(data)

    header_json_str = json.dumps({"files": header_files})
    header_json_bytes = header_json_str.encode("utf-8")
    header_pickle = struct.pack("<ii", len(header_json_bytes) + 4, len(header_json_bytes)) + header_json_bytes
    header_size = len(header_pickle)

    asar_header = struct.pack("<II", 4, header_size) + header_pickle
    return asar_header + b"".join(body_parts)


class TestVersionChecker(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        # Create resources/version.json
        res_dir = self.root_path / "resources"
        res_dir.mkdir(parents=True, exist_ok=True)
        self.ver_file = res_dir / "version.json"
        with open(self.ver_file, "w", encoding="utf-8") as f:
            json.dump({
                "version": "1.1.0",
                "target_antigravity_version": "2.17.0",
                "release_url": "https://github.com/qts2218346424-cyber/antigravity-zh-cn/releases"
            }, f)

        self.checker = VersionChecker(repo_root=self.root_path, cooldown_seconds=3600.0)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_read_local_localization_version(self):
        ver_info = self.checker.read_local_localization_version()
        self.assertEqual(ver_info.get("version"), "1.1.0")
        self.assertEqual(ver_info.get("target_antigravity_version"), "2.17.0")

    def test_version_comparison_semver(self):
        self.assertTrue(VersionChecker._is_newer_version("1.2.0", "1.1.0"))
        self.assertTrue(VersionChecker._is_newer_version("2.0.0", "1.9.9"))
        self.assertTrue(VersionChecker._is_newer_version("v1.1.1", "1.1.0"))
        self.assertFalse(VersionChecker._is_newer_version("1.1.0", "1.1.0"))
        self.assertFalse(VersionChecker._is_newer_version("1.0.9", "1.1.0"))
        self.assertFalse(VersionChecker._is_newer_version("0.9.0", "1.0.0"))

    def test_read_installed_host_info_not_found(self):
        fake_dir = self.root_path / "non_existent_antigravity"
        info = self.checker.read_installed_host_info(fake_dir)
        self.assertFalse(info["installed"])
        self.assertIsNone(info["version"])
        self.assertFalse(info["is_patched"])

    def test_read_installed_host_info_patched(self):
        fake_app_dir = self.root_path / "fake_antigravity"
        res_dir = fake_app_dir / "resources"
        res_dir.mkdir(parents=True, exist_ok=True)

        asar_bytes = build_mock_asar({
            "package.json": json.dumps({"name": "antigravity", "version": "2.17.0"}),
            "dist/preload.js": b"// Preload script\nconsole.log('ready');\n" + PATCH_MARKER
        })
        with open(res_dir / "app.asar", "wb") as f:
            f.write(asar_bytes)

        info = self.checker.read_installed_host_info(fake_app_dir)
        self.assertTrue(info["installed"])
        self.assertEqual(info["version"], "2.17.0")
        self.assertTrue(info["is_patched"])

    def test_read_installed_host_info_unpatched(self):
        fake_app_dir = self.root_path / "fake_antigravity_unpatched"
        res_dir = fake_app_dir / "resources"
        res_dir.mkdir(parents=True, exist_ok=True)

        asar_bytes = build_mock_asar({
            "package.json": json.dumps({"name": "antigravity", "version": "2.18.0"}),
            "dist/preload.js": b"// Clean official bundle without patch"
        })
        with open(res_dir / "app.asar", "wb") as f:
            f.write(asar_bytes)

        info = self.checker.read_installed_host_info(fake_app_dir)
        self.assertTrue(info["installed"])
        self.assertEqual(info["version"], "2.18.0")
        self.assertFalse(info["is_patched"])

    def test_evaluate_version_status_patch_overwritten(self):
        fake_app_dir = self.root_path / "fake_antigravity_overwrite"
        res_dir = fake_app_dir / "resources"
        res_dir.mkdir(parents=True, exist_ok=True)

        asar_bytes = build_mock_asar({
            "package.json": json.dumps({"name": "antigravity", "version": "2.18.1"}),
            "dist/preload.js": b"// Official updated file"
        })
        with open(res_dir / "app.asar", "wb") as f:
            f.write(asar_bytes)

        status = self.checker.evaluate_version_status(install_dir=fake_app_dir, check_remote=False)
        self.assertTrue(status["needs_notification"])
        self.assertEqual(status["event_type"], "PATCH_OVERWRITTEN")
        self.assertEqual(status["level"], "warning")
        self.assertIn("2.18.1", status["body"])
        self.assertIn("已更新", status["title"])

    def test_evaluate_version_status_new_release(self):
        fake_app_dir = self.root_path / "fake_antigravity_healthy"
        res_dir = fake_app_dir / "resources"
        res_dir.mkdir(parents=True, exist_ok=True)

        asar_bytes = build_mock_asar({
            "package.json": json.dumps({"name": "antigravity", "version": "2.17.0"}),
            "dist/preload.js": PATCH_MARKER
        })
        with open(res_dir / "app.asar", "wb") as f:
            f.write(asar_bytes)

        # Mock remote github check returning 1.2.0 (local is 1.1.0)
        with patch.object(self.checker, "check_remote_github_release", return_value={
            "success": True,
            "remote_version": "1.2.0",
            "release_url": "https://github.com/qts2218346424-cyber/antigravity-zh-cn/releases/tag/v1.2.0",
            "release_notes": "支持更多汉化内容"
        }):
            status = self.checker.evaluate_version_status(install_dir=fake_app_dir, check_remote=True)
            self.assertTrue(status["needs_notification"])
            self.assertEqual(status["event_type"], "NEW_LOCALIZATION_RELEASE")
            self.assertEqual(status["remote_version"], "1.2.0")
            self.assertIn("1.2.0", status["body"])

    def test_check_and_notify_cooldown(self):
        # Mock evaluate_version_status returning an alert
        mock_status = {
            "needs_notification": True,
            "event_type": "PATCH_OVERWRITTEN",
            "alert_key": "unpatched:2.18.0",
            "title": "官方已更新",
            "body": "请重新运行汉化",
            "level": "warning",
            "action_url": "https://example.com/update",
            "action_text": "更新"
        }

        mock_bridge = MagicMock()

        with patch.object(self.checker, "evaluate_version_status", return_value=mock_status):
            # First call -> sends notification
            res1 = self.checker.check_and_notify(mock_bridge, force=False)
            self.assertIsNotNone(res1)
            mock_bridge.send_notification.assert_called_once()
            self.assertEqual(res1["title"], "官方已更新")
            self.assertEqual(res1["action_url"], "https://example.com/update")

            # Second call immediately -> suppressed by cooldown
            mock_bridge.reset_mock()
            res2 = self.checker.check_and_notify(mock_bridge, force=False)
            self.assertIsNone(res2)
            mock_bridge.send_notification.assert_not_called()

            # Forced call -> bypasses cooldown
            res3 = self.checker.check_and_notify(mock_bridge, force=True)
            self.assertIsNotNone(res3)
            mock_bridge.send_notification.assert_called_once()


if __name__ == "__main__":
    unittest.main()
