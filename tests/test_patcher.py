#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 汉化项目单元测试套件 (tests/test_patcher.py)
用于验证：
1. 词典 JSON 文件合法性与编码规范；
2. 动态正则规则的编译与匹配替换准确性；
3. Python 原生 ASAR 解包与打包的一致性与无损回环；
4. 补丁注入与修补的幂等性与标记完整性。
"""

import os
import re
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from patch_antigravity import AsarArchive, patch_dist_files, PATCH_MARKER

class TestAntigravityZh(unittest.TestCase):
    
    def test_json_dictionaries_validity(self):
        """测试所有资源词典 JSON 语法的合法性与非空校验"""
        res_dir = REPO_ROOT / "resources"
        json_files = [
            "antigravity-zh-CN.json",
            "antigravity-zh-TW.json",
            "antigravity-zh-HK.json",
            "desktop-zh-CN.json",
            "rules-zh-CN.json"
        ]

        for fname in json_files:
            file_path = res_dir / fname
            self.assertTrue(file_path.is_file(), f"缺少必要资源文件: {fname}")
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertTrue(len(data) > 0, f"词典文件内容为空: {fname}")
                
            # 校验桌面词典关键键
            if fname == "desktop-zh-CN.json":
                self.assertIn("menu", data)
                self.assertIn("tray", data)

    def test_regex_rules_matching(self):
        """测试动态正则表达式规则编译与实际字符串替换能力"""
        rules_path = REPO_ROOT / "resources" / "rules-zh-CN.json"
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = json.load(f)

        test_cases = [
            ("1 agent running", "1 个代理正在运行"),
            ("3 agents running", "3 个代理正在运行"),
            ("No agents running", "无运行中的代理"),
            ("5 files changed", "5 个文件已修改"),
            ("12 additions, 3 deletions", "12 处添加，3 处删除"),
            ("Added 10 lines", "添加了 10 行"),
            ("Deleted 4 lines", "删除了 4 行"),
            ("Step 2 of 10", "步骤 2 / 10"),
            ("Task 3 completed", "任务 3 已完成"),
            ("5 mins ago", "5 分钟前"),
            ("Just now", "刚刚"),
            ("Delete 2 chats", "删除 2 个对话"),
            ("Are you sure you want to delete test.txt?", "确定要删除 test.txt 吗？")
        ]

        compiled_rules = [(re.compile(r[0]), r[1]) for r in rules]

        for text, expected in test_cases:
            matched = False
            for reg, repl in compiled_rules:
                if reg.search(text):
                    # 将 JS 替换语法 $1, $2 转换为 Python re 兼容的 \1, \2
                    py_repl = re.sub(r'\$(\d+)', r'\\\1', repl)
                    result = reg.sub(py_repl, text)
                    self.assertEqual(result, expected, f"规则替换结果不符: 原文 '{text}', 得到 '{result}', 期望 '{expected}'")
                    matched = True
                    break
            self.assertTrue(matched, f"未匹配到任何正则规则: '{text}'")

    def test_python_asar_pack_and_extract_roundtrip(self):
        """测试纯 Python ASAR 打包与解包的完全一致性"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_dir = temp_path / "source"
            source_dir.mkdir()

            # 创建模拟目录与文件
            (source_dir / "index.html").write_text("<!doctype html><html><body>Test</body></html>", encoding="utf-8")
            sub_dir = source_dir / "dist"
            sub_dir.mkdir()
            (sub_dir / "main.js").write_text("console.log('antigravity');", encoding="utf-8")
            (sub_dir / "binary.bin").write_bytes(b"\x00\x01\x02\x03\xFF\xFE\xFD")

            asar_output = temp_path / "test.asar"
            extracted_dir = temp_path / "extracted"

            # 1. 打包
            AsarArchive.pack(source_dir, asar_output)
            self.assertTrue(asar_output.is_file(), "ASAR 打包未生成文件")
            self.assertGreater(asar_output.stat().st_size, 0, "生成的 ASAR 文件为空")

            # 2. 解包
            AsarArchive.extract(asar_output, extracted_dir)
            
            # 3. 比对还原完整性
            self.assertTrue((extracted_dir / "index.html").is_file())
            self.assertEqual((extracted_dir / "index.html").read_text(encoding="utf-8"),
                             (source_dir / "index.html").read_text(encoding="utf-8"))
            
            self.assertTrue((extracted_dir / "dist" / "main.js").is_file())
            self.assertEqual((extracted_dir / "dist" / "main.js").read_text(encoding="utf-8"),
                             (source_dir / "dist" / "main.js").read_text(encoding="utf-8"))
            
            self.assertEqual((extracted_dir / "dist" / "binary.bin").read_bytes(),
                             (source_dir / "dist" / "binary.bin").read_bytes())

    def test_patch_dist_files_execution(self):
        """测试对 dist 目录各文件的修补逻辑"""
        with tempfile.TemporaryDirectory() as temp_dir:
            dist_dir = Path(temp_dir) / "dist"
            dist_dir.mkdir()

            menu_js = dist_dir / "menu.js"
            menu_js.write_text("const a = 'New Window'; const b = 'Help';", encoding="utf-8")

            tray_js = dist_dir / "tray.js"
            tray_js.write_text("const item = 'No agents running'; const q = 'Quit';", encoding="utf-8")

            updater_js = dist_dir / "updater.js"
            updater_js.write_text('const s = "Check for Updates";', encoding="utf-8")

            preload_js = dist_dir / "preload.js"
            preload_js.write_text("console.log('preload ready');", encoding="utf-8")

            patch_dist_files(dist_dir, "zh-CN", REPO_ROOT)

            # 验证菜单修补
            self.assertIn("新建窗口", menu_js.read_text(encoding="utf-8"))
            self.assertIn("帮助", menu_js.read_text(encoding="utf-8"))

            # 验证托盘修补
            self.assertIn("无运行中的代理", tray_js.read_text(encoding="utf-8"))
            self.assertIn("退出", tray_js.read_text(encoding="utf-8"))

            # 验证更新器修补
            self.assertIn("检查更新", updater_js.read_text(encoding="utf-8"))

            # 验证预加载脚本注入
            preload_content = preload_js.read_text(encoding="utf-8")
            self.assertIn(PATCH_MARKER, preload_content)
            self.assertIn("window.__AGY_ZH_DICT__", preload_content)


if __name__ == "__main__":
    unittest.main()
