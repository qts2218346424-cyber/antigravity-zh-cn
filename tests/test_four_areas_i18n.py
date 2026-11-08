#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证问候语、扩展菜单、内置浏览器与插件市场的 100% 汉化自动化测试
"""

import json
import re
import unittest
from pathlib import Path

class TestFourAreasI18n(unittest.TestCase):
    def setUp(self):
        res_dir = Path(__file__).resolve().parent.parent / "resources"
        with open(res_dir / "antigravity-zh-CN.json", "r", encoding="utf-8") as f:
            self.dict_cn = json.load(f)
        with open(res_dir / "antigravity-zh-TW.json", "r", encoding="utf-8") as f:
            self.dict_tw = json.load(f)
        with open(res_dir / "antigravity-zh-HK.json", "r", encoding="utf-8") as f:
            self.dict_hk = json.load(f)
        with open(res_dir / "rules-zh-CN.json", "r", encoding="utf-8") as f:
            self.rules = json.load(f)

        self.lower_dict_cn = {k.lower(): v for k, v in self.dict_cn.items()}

    def translate_cn(self, text: str) -> str:
        trimmed = text.strip()
        # 1. 问候语模式
        m = re.match(r"^(?:Hi|Hello|Hey)\s+(.+?),\s*what\s+can\s+we\s+get\s+done\s+today\??$", trimmed, re.I)
        if m:
            return f"你好 {m.group(1)}，今天想做些什么？"

        # 2. 词典直查
        if trimmed in self.dict_cn:
            return self.dict_cn[trimmed]
        if trimmed.lower() in self.lower_dict_cn:
            return self.lower_dict_cn[trimmed.lower()]

        # 3. 动态正则
        for pattern, repl in self.rules:
            if re.search(pattern, trimmed):
                py_repl = repl.replace("$1", r"\1").replace("$2", r"\2").replace("$3", r"\3")
                return re.sub(pattern, py_repl, trimmed)

        return text

    def test_area1_greeting(self):
        cases = [
            ("Hi tao, what can we get done today?", "你好 tao，今天想做些什么？"),
            ("Hi alex, what can we get done today?", "你好 alex，今天想做些什么？"),
            ("What can we get done today?", "今天想做些什么？"),
        ]
        for en, expected in cases:
            self.assertEqual(self.translate_cn(en), expected)

    def test_area2_extensions(self):
        cases = [
            ("Android Compose Preview", "Android Compose 实时预览"),
            ("Android Device Hub", "Android 设备控制中心"),
            ("Biomolecular Structure Viewer", "生物大分子三维结构视窗"),
        ]
        for en, expected in cases:
            self.assertEqual(self.translate_cn(en), expected)

    def test_area3_builtin_browser(self):
        cases = [
            ("Built-in Browser", "内置浏览器"),
            ("Configure link opening and built-in browser preferences.", "配置链接打开方式与内置浏览器偏好设置。"),
            ("Choose where links open by default when clicked.", "选择点击链接时的默认打开方式。"),
            ("Folder where files downloaded in the built-in browser are saved.", "保存内置浏览器中所下载文件的文件夹。"),
            ("Browsing History", "浏览历史"),
            ("Clear visited URLs and autocomplete suggestions from the built-in browser.", "清除内置浏览器中已访问的网址与自动补全建议。"),
            ("Clear visited URLs and autocomplete suggestions from side panel preview.", "清除侧面板预览中已访问的网址与自动补全建议。"),
        ]
        for en, expected in cases:
            self.assertEqual(self.translate_cn(en), expected)

    def test_area4_marketplace_shelves_and_plugins(self):
        cases = [
            ("Business", "商业与企业运营"),
            ("Payments, CRM, accounting, data, identity, customer support, marketing, and workflow automation.", "支付收款、客户关系管理 (CRM)、财务会计、数据分析、身份认证、客户支持、市场营销及工作流自动化。"),
            ("Design, Creative & Media", "设计、创意与多媒体"),
            ("Productivity & Project Management", "生产力与项目管理"),
            ("Cloud Hosting & Deployment", "云托管与应用部署"),
            ("Developer Tools", "开发者工具"),
            ("More Plugins", "更多精选插件"),
            ("Manage your Bigin CRM from Antigravity: review pipelines, find contacts and deals, log calls, plan follow-ups, and email customers.", "在 Antigravity 中管理 Bigin CRM：查看销售商机管道、查找联系人与交易、记录通话、规划跟进任务并向客户发送邮件。"),
            ("SEO workflows on live Semrush data: keyword research, site audit, organic search performance, competitor analysis, and backlink exploration.", "基于实时 Semrush 数据的 SEO 工作流：关键词挖掘调研、网站诊断体检、自然搜索表现、竞争对手分析及外链反向链接探索。"),
            ("Accept payments and grow your business. Stripe's suite of APIs powers commerce for online businesses.", "接入在线支付并加速业务增长。Stripe 全套 API 工具为线上商业交易提供全方位支持。"),
        ]
        for en, expected in cases:
            self.assertEqual(self.translate_cn(en), expected)

    def test_tw_and_hk_coverage(self):
        keys = [
            "What can we get done today?",
            "Android Compose Preview",
            "Android Device Hub",
            "Biomolecular Structure Viewer",
            "Built-in Browser",
            "Browsing History",
            "Business",
            "Developer Tools",
        ]
        for k in keys:
            self.assertIn(k, self.dict_tw)
            self.assertIn(k, self.dict_hk)

if __name__ == "__main__":
    unittest.main()
