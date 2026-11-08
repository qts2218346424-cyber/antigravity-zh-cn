# -*- coding: utf-8 -*-
"""
Antigravity 检查更新与防静默覆盖专项测试 (test_updater_feature.py)
用于验证：
1. app-update.yml 配置完整性；
2. updater.js 弹窗汉化与 autoDownload=false 防静默覆盖；
3. toggle_auto_updates 切换机制正常。
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# UTF-8 控制台编码兼容
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from patch_antigravity import (
    toggle_auto_updates,
    get_default_install_path,
    get_asar_path,
    read_asar_file_content,
    apply_patch,
    encode_asar_header_dynamic
)


class TestUpdaterFeature(unittest.TestCase):

    def test_updater_js_modifications(self):
        """验证 dist/updater.js 中的防静默更新与弹窗汉化逻辑"""
        install_dir = get_default_install_path()
        if not install_dir or not install_dir.is_dir():
            self.skipTest("本地未检测到 Antigravity 安装目录，跳过宿主验证")

        asar_path = get_asar_path(install_dir)
        if not asar_path.is_file():
            self.skipTest("本地未检测到 app.asar 文件，跳过宿主验证")

        data = asar_path.read_bytes()
        try:
            content = read_asar_file_content(data, "dist/updater.js").decode("utf-8")
        except Exception:
            self.skipTest("app.asar 中未找到 dist/updater.js")

        self.assertIn("autoDownload = false;", content, "必须禁用自动静默下载以保护汉化")
        self.assertIn("autoInstallOnAppQuit = false;", content, "必须禁用退出时静默覆盖安装")

    def test_toggle_auto_updates_toggle(self):
        """验证 toggle_auto_updates 的开关逻辑与文件重命名行为"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir)
            res_dir = install_dir / "resources"
            res_dir.mkdir(parents=True)

            update_yml = res_dir / "app-update.yml"
            disabled_yml = res_dir / "app-update.yml.disabled"

            # 初始创建
            update_yml.write_text("provider: generic\nurl: https://test.com\n", encoding="utf-8")

            # 禁用更新
            toggle_auto_updates(install_dir, disable=True)
            self.assertTrue(disabled_yml.is_file(), "禁用时应重命名为 app-update.yml.disabled")
            self.assertFalse(update_yml.is_file(), "禁用时 app-update.yml 不应存在")

            # 恢复更新
            toggle_auto_updates(install_dir, disable=False)
            self.assertTrue(update_yml.is_file(), "恢复时应还原为 app-update.yml")
            self.assertFalse(disabled_yml.is_file(), "恢复时 app-update.yml.disabled 不应存在")

    def test_app_update_yml_is_active_in_current_install(self):
        """验证当前宿主安装目录下的 app-update.yml 未处于 disabled 状态"""
        install_dir = get_default_install_path()
        if not install_dir or not install_dir.is_dir():
            self.skipTest("本地未检测到 Antigravity 安装目录，跳过宿主验证")

        update_yml = install_dir / "resources" / "app-update.yml"
        disabled_yml = install_dir / "resources" / "app-update.yml.disabled"

        self.assertFalse(disabled_yml.is_file(), "宿主目录不应存在 app-update.yml.disabled，会导致检查更新报错 ENOENT")
        self.assertTrue(update_yml.is_file(), "宿主目录应存在有效可用的 app-update.yml 配置文件")


if __name__ == "__main__":
    unittest.main()
