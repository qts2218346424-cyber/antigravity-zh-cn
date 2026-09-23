#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试集：
1. 真实 Antigravity 双轨配额与用户信息解析测试；
2. 高频并发连击与拖拽防崩测试；
3. 偏好设置 (pet_config.json) 与自启开关读写测试；
4. 前端 HTML/JS 契约一致性测试。
"""

import os
import sys
import json
import time
import threading
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "pet"))

from pet_engine.quota import QuotaMonitor
from pet_engine.models import QuotaStatus
from run_pet import JsBridge


class TestV2Features(unittest.TestCase):

    def test_live_quota_groups_and_user_meta(self):
        """测试 Antigravity 系统真实配额与用户信息提取"""
        monitor = QuotaMonitor()
        status = monitor.get_quota_status()

        self.assertIsInstance(status, QuotaStatus)
        d = status.to_dict()
        self.assertTrue(d.get("success"))
        self.assertGreaterEqual(status.remaining_percentage, 0.0)
        self.assertLessEqual(status.remaining_percentage, 100.0)

        # 验证提取到的 groups 双轨结构（若本地有 Antigravity 凭据）
        self.assertIn("groups", d)
        if d.get("groups"):
            groups = d["groups"]
            self.assertGreaterEqual(len(groups), 1)
            for g in groups:
                self.assertIn("displayName", g)
                self.assertIn("buckets", g)
                for b in g["buckets"]:
                    self.assertIn("percentage", b)
                    self.assertIn("resetTime", b)
                    self.assertGreaterEqual(b["percentage"], 0.0)
                    self.assertLessEqual(b["percentage"], 100.0)

        # 验证用户信息
        if d.get("user_name"):
            self.assertIsInstance(d["user_name"], str)
            self.assertGreater(len(d["user_name"]), 0)

    def test_rapid_concurrency_and_drag_lock_safety(self):
        """模拟高频 100 次并发连击与拖拽请求，验证防死锁与防崩溃机制"""
        holder = {"window": None}
        bridge = JsBridge(holder)
        errors = []

        def worker(thread_id):
            for i in range(20):
                try:
                    res = bridge.start_drag()
                    self.assertIn("success", res)
                except Exception as ex:
                    errors.append(f"Thread {thread_id} iter {i}: {ex}")

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=3.0)

        self.assertEqual(len(errors), 0, f"Concurrent rapid drag caused errors: {errors}")

    def test_pet_config_roundtrip(self):
        """验证 ~/.gemini/pet_config.json 的读写一致性"""
        holder = {"window": None}
        bridge = JsBridge(holder)
        original_res = bridge.get_pet_config()
        self.assertTrue(original_res["success"])
        original_cfg = original_res.get("config", {})

        # 修改为 False
        res1 = bridge.set_pet_config({"auto_start_with_antigravity": False})
        self.assertTrue(res1["success"])
        cfg_after1 = bridge.get_pet_config()["config"]
        self.assertFalse(cfg_after1["auto_start_with_antigravity"])

        # 修改为 True
        res2 = bridge.set_pet_config({"auto_start_with_antigravity": True})
        self.assertTrue(res2["success"])
        cfg_after2 = bridge.get_pet_config()["config"]
        self.assertTrue(cfg_after2["auto_start_with_antigravity"])

        # 恢复原始状态
        if "auto_start_with_antigravity" in original_cfg:
            bridge.set_pet_config({"auto_start_with_antigravity": original_cfg["auto_start_with_antigravity"]})

    def test_frontend_elements_contract(self):
        """验证前端 index.html 与 mascot.js 中的关节点与样式对应"""
        html_path = REPO_ROOT / "pet" / "frontend" / "index.html"
        js_path = REPO_ROOT / "pet" / "frontend" / "mascot.js"
        css_path = REPO_ROOT / "pet" / "frontend" / "styles.css"

        html_content = html_path.read_text(encoding="utf-8")
        js_content = js_path.read_text(encoding="utf-8")
        css_content = css_path.read_text(encoding="utf-8")

        # 验证双轨配额容器元素
        self.assertIn('id="quota-groups-container"', html_content)
        self.assertIn('id="quota-user-avatar"', html_content)
        self.assertIn('id="btn-refresh-quota"', html_content)

        # 验证设置模态框与开关
        self.assertIn('id="modal-settings"', html_content)
        self.assertIn('id="toggle-autostart"', html_content)
        self.assertIn('id="btn-settings"', html_content)

        # 验证 JS 绑定与类
        self.assertIn("class SettingsModalController", js_content)
        self.assertIn("set_pet_config", js_content)
        self.assertIn("get_pet_config", js_content)
        self.assertIn("_translateGroupName", js_content)
        self.assertIn("_translateBucketName", js_content)

        # 验证 CSS 样式类
        self.assertIn(".quota-group-card", css_content)
        self.assertIn(".quota-bucket-fill", css_content)
        self.assertIn(".toggle-switch", css_content)


if __name__ == '__main__':
    unittest.main()
