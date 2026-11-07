#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证语音模式与浏览器子智能体设置项的 100% 汉化测试
"""

import json
import re
import unittest
from pathlib import Path

class TestVoiceAndBrowserI18n(unittest.TestCase):
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
        if trimmed in self.dict_cn:
            return self.dict_cn[trimmed]
        if trimmed.lower() in self.lower_dict_cn:
            return self.lower_dict_cn[trimmed.lower()]
        for pattern, repl in self.rules:
            if re.search(pattern, trimmed):
                py_repl = repl.replace("$1", r"\1").replace("$2", r"\2").replace("$3", r"\3")
                return re.sub(pattern, py_repl, trimmed)
        return text

    def test_exact_words(self):
        cases = [
            ("Start Voice mode", "开启语音模式"),
            ("End Voice mode", "结束语音模式"),
            ("Voice mode", "语音模式"),
            ("Voice Mode", "语音模式"),
            ("Voice", "音色"),
            ("Not set", "未设置"),
            ("Change", "更改"),
            ("Microphone", "麦克风"),
            ("System default", "系统默认"),
            ("The voice used in Voice mode. Powered by Gemini Live.", "语音模式所使用的音色。由 Gemini Live 提供技术支持。"),
            ("Input device for voice mode and dictation.", "语音模式与语音听写的音频输入设备。"),
            ("How loud Antigravity's voice is.", "Antigravity 朗读语音的音量大小。"),
            ("to be installed. The browser subagent can be invoked by typing /browser in the conversation input box.", "环境。可在对话输入框中键入 /browser 唤出浏览器子智能体。"),
            ("Browser Subagent", "浏览器子智能体"),
            ("Choose Antigravity's Voice", "选择 Antigravity 音色"),
            ("Clear and friendly", "清晰亲和"),
        ]
        for en, expected in cases:
            actual = self.translate_cn(en)
            self.assertEqual(actual, expected, f"Failed for word: {en}")

    def test_dynamic_rules(self):
        cases = [
            ("System default (Realtek High Definition Audio)", "系统默认 (Realtek High Definition Audio)"),
            ("Choose Jetski's Voice", "选择 Jetski 音色"),
            ("Use Aoede", "使用 Aoede 音色"),
            ("Use Puck", "使用 Puck 音色"),
            ("Aoede, voice 1 of 10", "Aoede，第 1 / 10 种音色"),
        ]
        for en, expected in cases:
            actual = self.translate_cn(en)
            self.assertEqual(actual, expected, f"Failed for dynamic rule: {en}")

    def test_tw_and_hk_synced(self):
        keys = [
            "Start Voice mode", "End Voice mode", "Voice mode", "Voice",
            "Not set", "Change", "Microphone", "Choose Antigravity's Voice",
            "to be installed. The browser subagent can be invoked by typing /browser in the conversation input box."
        ]
        for k in keys:
            self.assertIn(k, self.dict_tw, f"Missing in zh-TW: {k}")
            self.assertIn(k, self.dict_hk, f"Missing in zh-HK: {k}")

if __name__ == "__main__":
    unittest.main()
