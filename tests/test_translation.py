import unittest
import subprocess
import json
from pathlib import Path

class TestRuntimeTranslation(unittest.TestCase):
    def test_whitespace_and_newline_replacement(self):
        js_code = """
        const DICT = {
            "Requires manual review for all terminal commands and file accesses outside of the working folders.": "所有终端命令及工作目录外文件访问均需人工审查。",
            "Turbo Mode": "Turbo 极速模式",
            "Also includes": "同时包含",
            "when working in this project.": "在当前项目中工作时。",
            "Weekly Limit Remaining": "每周剩余可用配额",
            "Five Hour Limit Remaining": "5 小时剩余可用配额",
            "Gemini Models": "Gemini 模型",
            "Claude and GPT models": "Claude 与 GPT 模型",
            "Copy Project Name": "复制项目名称",
            "Mark Unread": "标记为未读",
            "Add Context": "添加上下文",
            "Feedback Type": "反馈类型",
            "Bug Report": "问题报告",
            "Feature Request": "功能建议",
            "Auth and Billing": "认证与计费",
            "Remote Control Issue": "远程控制问题",
            "General Feedback": "通用反馈",
            "Describe the bug you encountered...": "请描述您遇到的错误或 Bug...",
            "Steps to reproduce the issue": "复现问题的具体步骤",
            "Expected behavior": "预期行为表现",
            "Actual behavior": "实际异常表现",
            "Any error messages": "任何相关的错误提示信息",
            "Any relevant information": "其他任何相关信息",
            "When toggled on, Antigravity collects usage data to help Google enhance performance and features.": "启用后，Antigravity 将收集匿名使用数据以帮助 Google 持续优化产品性能与功能体验。",
            "Receive product updates, tips, and promotions from Google Antigravity via email.": "通过电子邮件接收来自 Google Antigravity 的产品更新、实用技巧以及优惠动态。",
            "Your Plan:": "当前计划:",
            "You can upgrade to a Google AI Ultra plan to receive higher rate limits.": "您可以升级至 Google AI Ultra 订阅计划以获取更高的请求速率与使用额度。",
            "Upgrade": "升级",
            "Sign Out": "退出登录",
            "By using this app, you agree to its": "使用本应用即表示您同意其",
            "Terms of Service": "服务条款"
        };
        const RULES = [
            ["^Learn more about (.+)$", "了解有关 $1 的更多信息"],
            ["^Updated (.+)$", "更新于 $1"],
            ["^Resets in (\\\\d+)d (\\\\d+)h$", "$1 天 $2 小时后重置"],
            ["^Resets in (\\\\d+)d$", "$1 天后重置"],
            ["^Resets in (\\\\d+)h (\\\\d+)m$", "$1 小时 $2 分钟后重置"],
            ["^Resets in (\\\\d+)h$", "$1 小时后重置"],
            ["^Resets in (\\\\d+)m$", "$1 分钟后重置"],
            ["^Resets in <1m$", "<1 分钟后重置"],
            ["^Resets in (.+)$", "$1 后重置"],
            ["^When toggled on, (.+) collects usage data to help Google enhance performance and features\\\\.?$", "启用后，$1 将收集匿名使用数据以帮助 Google 持续优化产品性能与功能体验。"],
            ["^Receive product updates, tips, and promotions from (.+) via email\\\\.?$", "通过电子邮件接收来自 $1 的产品更新、实用技巧以及优惠动态。"],
            ["^You can upgrade to a (.+) plan to receive higher rate limits\\\\.?$", "您可以升级至 $1 订阅计划以获取更高的请求速率与使用额度。"],
            ["^Your Plan:\\\\s*(.+)$", "当前计划: $1"]
        ];

        const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();

        const translate = (raw) => {
            if (!raw) return null;
            const text = norm(raw);
            if (!text) return null;
            if (DICT[text]) return DICT[text];
            if (text.endsWith(':') && DICT[text.slice(0, -1).trim()]) return DICT[text.slice(0, -1).trim()] + '：';
            if (text.endsWith('.') && DICT[text.slice(0, -1).trim()]) return DICT[text.slice(0, -1).trim()] + '。';
            for (let i = 0; i < RULES.length; i++) {
                const reg = new RegExp(RULES[i][0]);
                if (reg.test(text)) return text.replace(reg, RULES[i][1]);
            }
            return null;
        };

        const replaceText = (original) => {
            const translated = translate(original);
            if (!translated) return original;
            const leading = (original.match(/^\\s*/) || [''])[0];
            const trailing = (original.match(/\\s*$/) || [''])[0];
            return leading + translated + trailing;
        };

        // 1. Multiline text with internal newlines
        const multiline = "  Requires manual review for all terminal commands and file\\n  accesses outside of the working folders.  ";
        const res = replaceText(multiline);
        if (res !== "  所有终端命令及工作目录外文件访问均需人工审查。  ") {
            console.error("Multiline failed:", res);
            process.exit(1);
        }

        // 2. Updated timestamp regex
        const updatedTime = "Updated 9月20日, 3:25";
        if (translate(updatedTime) !== "更新于 9月20日, 3:25") {
            console.error("Updated time failed:", translate(updatedTime));
            process.exit(2);
        }

        // 3. Resets in timings
        if (translate("Resets in 3d") !== "3 天后重置") process.exit(3);
        if (translate("Resets in 1h 47m") !== "1 小时 47 分钟后重置") process.exit(4);

        // 4. Feedback Dialog & Placeholders
        if (translate("Feedback Type") !== "反馈类型") process.exit(5);
        if (translate("Bug Report") !== "问题报告") process.exit(6);
        if (translate("Describe the bug you encountered...") !== "请描述您遇到的错误或 Bug...") process.exit(7);
        if (translate("Steps to reproduce the issue") !== "复现问题的具体步骤") process.exit(8);

        // 5. Account & General Settings
        if (translate("When toggled on, Antigravity collects usage data to help Google enhance performance and features.") !== "启用后，Antigravity 将收集匿名使用数据以帮助 Google 持续优化产品性能与功能体验。") process.exit(9);
        if (translate("Receive product updates, tips, and promotions from Google Antigravity via email.") !== "通过电子邮件接收来自 Google Antigravity 的产品更新、实用技巧以及优惠动态。") process.exit(10);
        if (translate("Your Plan: Google AI Pro") !== "当前计划: Google AI Pro") process.exit(11);
        if (translate("You can upgrade to a Google AI Ultra plan to receive higher rate limits.") !== "您可以升级至 Google AI Ultra 订阅计划以获取更高的请求速率与使用额度。") process.exit(12);
        if (translate("Upgrade") !== "升级") process.exit(13);
        if (translate("Sign Out") !== "退出登录") process.exit(14);
        if (translate("By using this app, you agree to its") !== "使用本应用即表示您同意其") process.exit(15);
        if (translate("Terms of Service") !== "服务条款") process.exit(16);

        console.log("SUCCESS");
        """
        proc = subprocess.run(["node", "-e", js_code], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Node script failed: {proc.stderr}")
        self.assertIn("SUCCESS", proc.stdout)

if __name__ == '__main__':
    unittest.main()
