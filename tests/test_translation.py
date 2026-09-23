import unittest
import subprocess
from pathlib import Path

class TestRuntimeTranslation(unittest.TestCase):
    def test_translation_engine_against_production_dict(self):
        repo_root = Path(__file__).resolve().parent.parent.as_posix()

        js_template = r"""
        const fs = require('fs');
        const DICT = JSON.parse(fs.readFileSync('__REPO_ROOT__/resources/antigravity-zh-CN.json', 'utf-8'));
        const RULES = JSON.parse(fs.readFileSync('__REPO_ROOT__/resources/rules-zh-CN.json', 'utf-8'));

        const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();

        const translate = (raw) => {
            if (!raw) return null;
            const text = norm(raw);
            if (!text) return null;
            if (DICT[text]) return DICT[text];
            if (text.endsWith(':') && DICT[text.slice(0, -1).trim()]) return DICT[text.slice(0, -1).trim()] + '：';
            if (text.endsWith('...') && DICT[text.slice(0, -3).trim()]) return DICT[text.slice(0, -3).trim()] + '...';
            if (text.endsWith('…') && DICT[text.slice(0, -1).trim()]) return DICT[text.slice(0, -1).trim()] + '...';
            if (text.endsWith('.') && DICT[text.slice(0, -1).trim()]) return DICT[text.slice(0, -1).trim()] + '。';
            if (text.endsWith('?') && DICT[text.slice(0, -1).trim()]) return DICT[text.slice(0, -1).trim()] + '？';

            if (text.endsWith('>') && DICT[text.slice(0, -1).trim()]) return DICT[text.slice(0, -1).trim()] + ' >';
            if (text.startsWith('(') && text.endsWith(')') && DICT[text.slice(1, -1).trim()]) return '（' + DICT[text.slice(1, -1).trim()] + '）';
            const countMatch = text.match(/^(.+?)\s*\(([0-9]+)\)$/);
            if (countMatch && DICT[countMatch[1].trim()]) return DICT[countMatch[1].trim()] + ' (' + countMatch[2] + ')';
            const modelTagMatch = text.match(/^(.+?)\s*\((Thinking|Fast|Medium|High|Low)\)$/i);
            if (modelTagMatch && DICT[modelTagMatch[2]]) return modelTagMatch[1] + '（' + DICT[modelTagMatch[2]] + '）';

            for (let i = 0; i < RULES.length; i++) {
                const item = RULES[i];
                try {
                    const reg = item[0] instanceof RegExp ? item[0] : new RegExp(item[0]);
                    const repl = item[1];
                    if (reg.test(text)) return text.replace(reg, repl);
                } catch (_) {}
            }
            return null;
        };

        const replaceText = (original) => {
            const translated = translate(original);
            if (!translated) return original;
            const leading = (original.match(/^\s*/) || [''])[0];
            const trailing = (original.match(/\s*$/) || [''])[0];
            return leading + translated + trailing;
        };

        // 1. Multiline text with internal newlines
        const multiline = "  Requires manual review for all terminal commands and file\n  accesses outside of the working folders.  ";
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
        if (translate("Resets in 6d") !== "6 天后重置") process.exit(5);
        if (translate("Resets in 2d 23h") !== "2 天 23 小时后重置") process.exit(25);

        // 4. Feedback Dialog & Placeholders
        if (translate("Feedback Type") !== "反馈类型") process.exit(6);
        if (translate("Bug Report") !== "问题报告") process.exit(7);
        if (translate("Describe the bug you encountered...") !== "请描述您遇到的错误或 Bug...") process.exit(8);
        if (translate("Steps to reproduce the issue") !== "复现问题的具体步骤") process.exit(9);

        // 5. Account & General Settings
        if (translate("When toggled on, Antigravity collects usage data to help Google enhance performance and features.") !== "启用后，Antigravity 将收集匿名使用数据以帮助 Google 持续优化产品性能与功能体验。") process.exit(10);
        if (translate("Receive product updates, tips, and promotions from Google Antigravity via email.") !== "通过电子邮件接收来自 Google Antigravity 的产品更新、实用技巧以及优惠动态。") process.exit(11);
        if (translate("Your Plan: Google AI Pro") !== "当前计划: Google AI Pro") process.exit(12);
        if (translate("You can upgrade to a Google AI Ultra plan to receive higher rate limits.") !== "您可以升级至 Google AI Ultra 订阅计划以获取更高的请求速率与使用额度。") process.exit(13);
        if (translate("Upgrade") !== "升级") process.exit(14);
        if (translate("Sign Out") !== "退出登录") process.exit(15);
        if (translate("By using this app, you agree to its") !== "使用本应用即表示您同意其") process.exit(16);
        if (translate("Terms of Service") !== "服务条款") process.exit(17);

        // 6. Interactive Questions & Chat Input
        if (translate("Multi-select") !== "多选") process.exit(18);
        if (translate("Other (write your answer)") !== "其他（填写您的回答）") process.exit(19);
        if (translate("3 of 3") !== "3 / 3") process.exit(20);
        if (!translate("Ask anything, @ to mention, / for actions").includes("随时提问")) process.exit(21);

        // 7. Trajectory & Thought
        if (translate("Thought for 5s") !== "思考了 5 秒") process.exit(22);
        if (translate("Exploring 1 action") !== "正在探索 1 个操作") process.exit(23);
        if (translate("Edited Prompt Draft") !== "已编辑 Prompt Draft") process.exit(24);

        // 8. Model picker, quota popup & sidebar
        if (translate("Show All") !== "显示全部") process.exit(26);
        if (translate("Not in Project") !== "未归入项目" && translate("Not in Project") !== "不在项目中") process.exit(27);
        if (translate("Gemini Models") !== "Gemini 模型") process.exit(28);
        if (translate("Weekly Limit Remaining") !== "每周剩余可用配额") process.exit(29);
        if (translate("Five Hour Limit Remaining") !== "5 小时剩余可用配额") process.exit(30);
        if (translate("Claude and GPT models") !== "Claude 与 GPT 模型") process.exit(31);
        if (translate("View Usage >") !== "查看用量 >") process.exit(32);
        if (translate("High") !== "高") process.exit(33);
        if (translate("Medium") !== "中等") process.exit(34);
        if (translate("Fast") !== "快速") process.exit(35);
        if (!translate("Claude Sonnet 4.6 (Thinking)").includes("思考")) process.exit(36);
        if (translate("GPT-OSS 120B (Medium)") !== "GPT-OSS 120B（中等）") process.exit(37);
        if (translate("Tool Calls (3)") !== "工具调用 (3)") process.exit(38);

        console.log("SUCCESS");
        """
        js_code = js_template.replace('__REPO_ROOT__', repo_root)
        proc = subprocess.run(["node", "-e", js_code], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Node script failed: {proc.stderr}")
        self.assertIn("SUCCESS", proc.stdout)

if __name__ == '__main__':
    unittest.main()
