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
            "Add Context": "添加上下文"
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
            ["^Resets in (.+)$", "$1 后重置"]
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
        if (translate("Resets in 3d") !== "3 天后重置") {
            console.error("Resets in 3d failed:", translate("Resets in 3d"));
            process.exit(3);
        }
        if (translate("Resets in 1h 47m") !== "1 小时 47 分钟后重置") {
            console.error("Resets in 1h 47m failed:", translate("Resets in 1h 47m"));
            process.exit(4);
        }
        if (translate("Resets in 6d") !== "6 天后重置") {
            console.error("Resets in 6d failed:", translate("Resets in 6d"));
            process.exit(5);
        }

        // 4. Exact dictionary matches
        if (translate("Weekly Limit Remaining") !== "每周剩余可用配额") process.exit(6);
        if (translate("Five Hour Limit Remaining") !== "5 小时剩余可用配额") process.exit(7);
        if (translate("Copy Project Name") !== "复制项目名称") process.exit(8);
        if (translate("Mark Unread") !== "标记为未读") process.exit(9);
        if (translate("Add Context") !== "添加上下文") process.exit(10);

        console.log("SUCCESS");
        """
        proc = subprocess.run(["node", "-e", js_code], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Node script failed: {proc.stderr}")
        self.assertIn("SUCCESS", proc.stdout)

if __name__ == '__main__':
    unittest.main()
