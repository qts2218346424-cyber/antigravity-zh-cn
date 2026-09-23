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
            "when working in this project.": "在当前项目中工作时。"
        };
        const RULES = [
            ["^Learn more about (.*)$", "了解有关 $1 的更多信息"]
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

        const multiline = "  Requires manual review for all terminal commands and file\\n  accesses outside of the working folders.  ";
        const res = replaceText(multiline);
        if (res !== "  所有终端命令及工作目录外文件访问均需人工审查。  ") {
            process.exit(1);
        }

        const dynamic = "Learn more about Turbo mode";
        if (translate(dynamic) !== "了解有关 Turbo mode 的更多信息") {
            process.exit(2);
        }

        console.log("SUCCESS");
        """
        proc = subprocess.run(["node", "-e", js_code], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Node script failed: {proc.stderr}")
        self.assertIn("SUCCESS", proc.stdout)

if __name__ == '__main__':
    unittest.main()
