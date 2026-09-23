#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 汉化项目单元测试套件 (tests/test_patcher.py)
用于验证：
1. 词典 JSON 文件合法性与编码规范；
2. 动态正则规则的编译与匹配替换准确性；
3. 原位 (In-place) ASAR 无损修补与 unpacked 外部链接索引 100% 保留；
4. 真实 app.asar 结构的无损修补验证。
"""

import os
import re
import sys
import json
import struct
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
    read_asar_header,
    encode_asar_header_dynamic,
    replace_asar_file_content,
    read_asar_file_content,
    PATCH_MARKER
)

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
                    py_repl = re.sub(r'\$(\d+)', r'\\\1', repl)
                    result = reg.sub(py_repl, text)
                    self.assertEqual(result, expected, f"规则替换结果不符: 原文 '{text}', 得到 '{result}', 期望 '{expected}'")
                    matched = True
                    break
            self.assertTrue(matched, f"未匹配到任何正则规则: '{text}'")

    def test_in_place_asar_patching_with_unpacked_preservation(self):
        """测试原位修补技术并验证对 unpacked 外部文件引用的 100% 保护"""
        # 构建一个模拟的 ASAR，包含 unpacked: true 的文件条目
        f1_data = b"console.log('original menu');"
        f2_data = b"console.log('original preload');"
        
        body_data = f1_data + f2_data
        
        mock_header = {
            "files": {
                "dist": {
                    "files": {
                        "menu.js": {
                            "size": len(f1_data),
                            "offset": "0"
                        },
                        "preload.js": {
                            "size": len(f2_data),
                            "offset": str(len(f1_data))
                        }
                    }
                },
                "node_modules": {
                    "files": {
                        "chrome-devtools-mcp": {
                            "files": {
                                "tool.js": {
                                    "unpacked": True
                                }
                            }
                        }
                    }
                }
            }
        }
        
        header_bytes = encode_asar_header_dynamic(json.dumps(mock_header, separators=(',', ':')))
        asar_bytes = bytearray(header_bytes + body_data)
        
        # 1. 验证初始 header
        _, _, init_h = read_asar_header(asar_bytes)
        self.assertTrue(init_h["files"]["node_modules"]["files"]["chrome-devtools-mcp"]["files"]["tool.js"]["unpacked"])
        
        # 2. 原位替换 menu.js 为更长的新内容
        new_menu = b"console.log('patched menu with new window text');"
        patched_asar = replace_asar_file_content(asar_bytes, "dist/menu.js", new_menu)
        
        # 3. 验证修补后 unpacked 引用绝对未丢失
        _, _, patched_h = read_asar_header(patched_asar)
        self.assertTrue(
            patched_h["files"]["node_modules"]["files"]["chrome-devtools-mcp"]["files"]["tool.js"]["unpacked"],
            "严重错误: 原位修补丢弃了 unpacked: true 外部链接！"
        )
        
        # 4. 验证内容读取正确
        read_back_menu = read_asar_file_content(patched_asar, "dist/menu.js")
        self.assertEqual(read_back_menu, new_menu)
        
        # 5. 验证后续文件 preload.js 偏移自动校准且内容依然无损
        read_back_preload = read_asar_file_content(patched_asar, "dist/preload.js")
        self.assertEqual(read_back_preload, f2_data)

    def test_real_antigravity_asar_unpacked_preservation(self):
        """如果本地存在真实的 Antigravity app.asar.bak，进行真实结构测试"""
        real_asar_bak = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "antigravity" / "resources" / "app.asar.bak"
        if not real_asar_bak.is_file():
            self.skipTest("本地未检测到 app.asar.bak，跳过真实环境测试")
            
        data = bytearray(real_asar_bak.read_bytes())
        _, _, h = read_asar_header(data)
        
        def count_unpacked(node):
            cnt = 0
            if isinstance(node, dict):
                for k, v in node.get("files", {}).items():
                    if isinstance(v, dict):
                        if v.get("unpacked") is True:
                            cnt += 1
                        cnt += count_unpacked(v)
            return cnt
            
        orig_unpacked = count_unpacked(h)
        self.assertEqual(orig_unpacked, 293, f"原版 unpacked 数量不符合预期: {orig_unpacked}")
        
        # 模拟修补 dist/menu.js
        old_menu = read_asar_file_content(data, "dist/menu.js")
        new_menu = old_menu + b" // test comment"
        patched = replace_asar_file_content(data, "dist/menu.js", new_menu)
        
        _, _, patched_h = read_asar_header(patched)
        patched_unpacked = count_unpacked(patched_h)
        self.assertEqual(patched_unpacked, 293, "真实 asar 修补后丢弃了 unpacked 文件！")


if __name__ == "__main__":
    unittest.main()
