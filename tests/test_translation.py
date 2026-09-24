import unittest
import subprocess
import os
from pathlib import Path

class TestRuntimeTranslation(unittest.TestCase):
    def test_translation_engine_against_production_dict(self):
        repo_root = Path(__file__).resolve().parent.parent.as_posix()

        js_template = r"""
        const fs = require('fs');
        const DICT = JSON.parse(fs.readFileSync('__REPO_ROOT__/resources/antigravity-zh-CN.json', 'utf-8'));
        const RULES = JSON.parse(fs.readFileSync('__REPO_ROOT__/resources/rules-zh-CN.json', 'utf-8'));

        const LOWER_DICT = {};
        for (const k in DICT) {
            const lk = k.toLowerCase();
            if (!LOWER_DICT[lk]) LOWER_DICT[lk] = DICT[k];
        }

        const norm = (s) => (s || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim();

        const translate = (raw) => {
            if (!raw) return null;

            if (typeof raw === 'string' && raw.includes('\n')) {
                const lines = raw.split('\n');
                let anyTranslated = false;
                const translatedLines = lines.map(line => {
                    const trimmed = line.trim();
                    if (!trimmed) return line;
                    const tr = translate(trimmed);
                    if (tr) {
                        anyTranslated = true;
                        const lead = (line.match(/^\s*/) || [''])[0];
                        const trail = (line.match(/\s*$/) || [''])[0];
                        return lead + tr + trail;
                    }
                    return line;
                });
                if (anyTranslated) {
                    return translatedLines.join('\n');
                }
            }

            const text = norm(raw);
            if (!text) return null;

            if (/[\u4e00-\u9fa5]/.test(text)) {
                const cleaned = text
                    .replace(/\((\d+)\s*子智能体s\)/g, '($1 个子智能体)')
                    .replace(/(\d+)\s*子智能体s/g, '$1 个子智能体')
                    .replace(/(\d+)\s*个(?:代理|智能体)s\s*正在运行/g, '$1 个智能体正在运行')
                    .replace(/(子智能体|代理|任务|文件|项目|命令|会话|工具)s\b/g, '$1')
                    .replace(/([\u4e00-\u9fa5])s(?=[^\w]|$)/g, '$1');
                if (cleaned !== text) return cleaned;
            }

            if (DICT[text]) return DICT[text];
            const lower = text.toLowerCase();
            if (LOWER_DICT[lower]) return LOWER_DICT[lower];

            if (text.endsWith(':') && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + '：';
            if (text.endsWith('...') && (DICT[text.slice(0, -3).trim()] || LOWER_DICT[lower.slice(0, -3).trim()])) return (DICT[text.slice(0, -3).trim()] || LOWER_DICT[lower.slice(0, -3).trim()]) + '...';
            if (text.endsWith('…') && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + '...';
            if (text.endsWith('.') && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + '。';
            if (text.endsWith('?') && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + '？';

            if (text.endsWith('>') && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + ' >';
            if ((text.endsWith('✓') || text.endsWith('✔')) && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) {
                return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + ' ' + text.slice(-1);
            }
            if ((text.startsWith('✓') || text.startsWith('✔')) && (DICT[text.slice(1).trim()] || LOWER_DICT[lower.slice(1).trim()])) {
                return text.charAt(0) + ' ' + (DICT[text.slice(1).trim()] || LOWER_DICT[lower.slice(1).trim()]);
            }
            if (text.startsWith('(') && text.endsWith(')') && (DICT[text.slice(1, -1).trim()] || LOWER_DICT[lower.slice(1, -1).trim()])) return '（' + (DICT[text.slice(1, -1).trim()] || LOWER_DICT[lower.slice(1, -1).trim()]) + '）';
            const countMatch = text.match(/^(.+?)\s*\(([0-9]+)\)$/);
            if (countMatch && (DICT[countMatch[1].trim()] || LOWER_DICT[countMatch[1].trim().toLowerCase()])) return (DICT[countMatch[1].trim()] || LOWER_DICT[countMatch[1].trim().toLowerCase()]) + ' (' + countMatch[2] + ')';
            const modelTagMatch = text.match(/^(.+?)\s*\((Thinking|Fast|Medium|High|Low)\)$/i);
            if (modelTagMatch && (DICT[modelTagMatch[2]] || LOWER_DICT[modelTagMatch[2].toLowerCase()])) return modelTagMatch[1] + '（' + (DICT[modelTagMatch[2]] || LOWER_DICT[modelTagMatch[2].toLowerCase()]) + '）';

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

        // 9. Audio, message queueing shortcuts and limited time
        if (translate("Limited time") !== "限时体验") process.exit(39);
        if (translate("Limited time ✓") !== "限时体验 ✓") process.exit(40);
        if (translate("Record Audio") !== "录制音频") process.exit(41);
        if (translate("Record Audio Ctrl+M") !== "录制音频 Ctrl+M") process.exit(42);
        if (translate("Enter Queues after the turn") !== "Enter：本轮结束后排队") process.exit(43);
        if (translate("Alt+Enter Sends immediately") !== "Alt+Enter：立即发送") process.exit(44);
        if (translate("Alt+Enter On empty prompt, sends next in queue") !== "Alt+Enter：若输入为空，发送队列中下一条") process.exit(45);
        if (translate("Queues after the turn") !== "本轮结束后排队") process.exit(46);
        if (translate("Sends immediately") !== "立即发送") process.exit(47);
        if (translate("On empty prompt, sends next in queue") !== "若输入为空，发送队列中下一条") process.exit(48);

        // Multiline tooltip test
        const multilineTooltip = "Enter Queues after the turn\nAlt+Enter Sends immediately\nAlt+Enter On empty prompt, sends next in queue";
        const expectedMultiline = "Enter：本轮结束后排队\nAlt+Enter：立即发送\nAlt+Enter：若输入为空，发送队列中下一条";
        if (translate(multilineTooltip) !== expectedMultiline) {
            console.error("Multiline tooltip test failed:\nExpected:\n" + expectedMultiline + "\nGot:\n" + translate(multilineTooltip));
            process.exit(49);
        }

        // 10. Queue message, image attachment, undo to this point, see less, changes since
        if (translate("Queue message Enter") !== "消息排队 Enter") process.exit(50);
        if (translate("Send immediately (Alt+Enter)") !== "立即发送 (Alt+Enter)") process.exit(51);
        if (translate("image.png") !== "图片.png") process.exit(52);
        if (translate("Undo to this point") !== "撤销至此处") process.exit(53);
        if (translate("See less") !== "收起") process.exit(54);
        if (translate("See more") !== "展开") process.exit(55);
        if (translate("All changes since origin/main") !== "自 origin/main 以来的所有更改") process.exit(56);
        // 11. Maximize Pane, Enabled state, and Browser subagent settings
        if (translate("Maximize Pane") !== "最大化窗格") process.exit(57);
        if (translate("Enabled") !== "已启用") process.exit(58);
        if (translate("Enabled ✓") !== "已启用 ✓") process.exit(59);
        if (translate("Configure the browser subagent. It requires") !== "配置浏览器子代理。该功能需要安装") process.exit(60);
        if (translate("to be installed.") !== "浏览器。") process.exit(61);
        // 12. Thinking Process UI and Quota Refresh Messages
        if (translate("Thought Process") !== "思考过程") process.exit(63);
        if (translate("Hide thoughts") !== "收起思考") process.exit(64);
        if (translate("Show thoughts") !== "展开思考") process.exit(65);
        if (translate("Working") !== "正在处理") process.exit(66);
        if (!translate("You have used some of your weekly limit, it will fully refresh in 6 days, 22 hours.").includes("您已使用部分每周配额")) process.exit(67);

        // 13. Media date, Modified stats, Settings descriptions, Sort & Filters, and Retry notices
        if (translate("Media (Today 4:59 AM)") !== "媒体 (今天 4:59 AM)") {
            console.error("Media Today test failed:", translate("Media (Today 4:59 AM)"));
            process.exit(68);
        }
        if (translate("Media (Yesterday 10:20 PM)") !== "媒体 (昨天 10:20 PM)") {
            console.error("Media Yesterday test failed:", translate("Media (Yesterday 10:20 PM)"));
            process.exit(69);
        }
        if (translate("Modified in 3 项目列表") !== "在 3 个项目中已修改") {
            console.error("Modified in 3 项目列表 failed:", translate("Modified in 3 项目列表"));
            process.exit(70);
        }
        if (translate("Modified in 1 project") !== "在 1 个项目中已修改") process.exit(71);
        if (translate("Manage Antigravity app settings.") !== "管理 Antigravity 应用程序设置。") process.exit(72);
        if (translate("Last Prompt") !== "最新提示词") process.exit(73);
        if (translate("Alphabetical (A-Z)") !== "按字母排序 (A-Z)") process.exit(74);
        if (translate("Date Added") !== "添加日期") process.exit(75);
        if (translate("Select Environment (Ctrl+.)") !== "选择运行环境 (Ctrl+.)") process.exit(76);
        if (translate("Model unavailable, retrying in 34s (attempt 5/9).") !== "模型不可用，将在 34 秒后重试 (第 5/9 次尝试)。") {
            console.error("Model unavailable failed:", translate("Model unavailable, retrying in 34s (attempt 5/9)."));
            process.exit(77);
        }
        if (translate("All crons run as Flash.") !== "所有定时任务均以 Flash 运行。") {
            console.error("All crons run as Flash failed:", translate("All crons run as Flash."));
            process.exit(78);
        }
        if (translate("Only Unread") !== "仅未读") process.exit(79);
        if (translate("Scheduled") !== "已计划") process.exit(80);
        if (translate("Project + Worktree") !== "项目 + 工作树") process.exit(81);
        if (translate("Delete plugin") !== "删除插件") process.exit(82);
        if (translate("Cancel (Ctrl+D)") !== "取消 (Ctrl+D)") process.exit(83);
        if (!translate("Keep your coding agent up to date with the latest web best practices.").includes("Web 最佳实践")) process.exit(84);
        if (!translate("Reliable automation, in-depth debugging, and performance analysis in Chrome using Chrome DevTools and Puppeteer").includes("性能分析")) process.exit(85);
        if (translate("Project + Worktree ✓") !== "项目 + 工作树 ✓") {
            console.error("Project + Worktree checkmark failed:", translate("Project + Worktree ✓"));
            process.exit(86);
        }
        if (translate("Scheduled ✓") !== "已计划 ✓") process.exit(87);
        if (translate("Only Unread ✓") !== "仅未读 ✓") process.exit(88);
        if (!translate("Universal TypeSafe Jev (System One) Coprocessor for rapid micro-decisions, risk gating, multi-criteria scoring, and intent classification across all coding and researc...").includes("协处理器")) {
            console.error("Jev description prefix failed:", translate("Universal TypeSafe Jev (System One) Coprocessor for rapid micro-decisions, risk gating, multi-criteria scoring, and intent classification across all coding and researc..."));
            process.exit(89);
        }
        if (translate("Show in File Explorer") !== "在文件资源管理器中显示") {
            console.error("Show in File Explorer failed:", translate("Show in File Explorer"));
            process.exit(90);
        }
        if (translate("5 tools") !== "5 个工具") {
            console.error("5 tools failed:", translate("5 tools"));
            process.exit(91);
        }
        if (translate("5 tools 38") !== "5 个工具 38") {
            console.error("5 tools 38 failed:", translate("5 tools 38"));
            process.exit(92);
        }
        if (translate("crons") !== "定时任务") process.exit(93);

        // 14. Action combinations, Thinking for header, isolated action verbs, and Project deletion confirm
        if (translate("Explored 16 files, ran 7 commands >") !== "已探索 16 个文件，执行了 7 条命令") {
            console.error("Explored ran combination failed:", translate("Explored 16 files, ran 7 commands >"));
            process.exit(94);
        }
        if (translate("Edited") !== "已编辑") process.exit(95);
        if (translate("Thinking for 3s") !== "思考了 3 秒") {
            console.error("Thinking for 3s failed:", translate("Thinking for 3s"));
            process.exit(96);
        }
        if (translate("Thinking for 3s ˇ") !== "思考了 3 秒") {
            console.error("Thinking for 3s dropdown failed:", translate("Thinking for 3s ˇ"));
            process.exit(96);
        }
        if (translate("Are you sure you want to delete the 项目 从0开始学大模型开发?") !== "确定要删除项目 从0开始学大模型开发 吗？") {
            console.error("Delete project confirm failed:", translate("Are you sure you want to delete the 项目 从0开始学大模型开发?"));
            process.exit(97);
        }

        // 15. Stop hook, Subagent runtime with arrow, browser moved notice, notification pref, WSL connect, and Models & Usage
        if (translate("Stop hook blocked termination: The user has automatically... >") !== "停止钩子已阻止终止：用户已自动...") {
            console.error("Stop hook failed:", translate("Stop hook blocked termination: The user has automatically... >"));
            process.exit(98);
        }
        if (translate("Ran for 3m >") !== "已运行 3 分钟") {
            console.error("Ran for 3m failed:", translate("Ran for 3m >"));
            process.exit(99);
        }
        if (translate("Browser settings have moved to the Browser section of General settings. Go to General settings") !== "浏览器设置已移至通用设置中的“浏览器”部分。前往通用设置") {
            console.error("Browser moved failed:", translate("Browser settings have moved to the Browser section of General settings. Go to General settings"));
            process.exit(100);
        }
        if (!translate("To modify notification settings, open your operating system's system preferences.").includes("系统偏好设置")) process.exit(101);
        if (translate("Connect") !== "连接") process.exit(102);
        if (translate("Models & Usage") !== "模型与用量") process.exit(103);

        // 16. Diff viewer controls, Push status notice, Session title, and Customization budget segmentation
        if (translate("Multi-Agent AI Task Delegation") !== "多智能体 AI 任务委派") {
            console.error("Multi-Agent AI Task Delegation failed:", translate("Multi-Agent AI Task Delegation"));
            process.exit(104);
        }
        if (translate("View Split Diff") !== "查看分屏差异") process.exit(105);
        if (translate("Hide Whitespace Changes") !== "隐藏空白字符更改") process.exit(106);
        if (translate("Collapse All") !== "全部折叠") process.exit(107);
        if (translate("No commits to push") !== "没有需要推送的提交") process.exit(108);
        if (!translate("83.6% of the customization budget is available.").includes("83.6%")) {
            console.error("Budget percentage failed:", translate("83.6% of the customization budget is available."));
            process.exit(109);
        }
        if (translate("of the customization budget is available.") !== "可用自定义预算。") {
            console.error("Budget segment failed:", translate("of the customization budget is available."));
            process.exit(110);
        }

        // 17. Killed status, Subagent role names, Active conversations count, resources/scripts, and Copy code
        if (translate("Killed") !== "已终止") process.exit(111);
        if (translate("killed") !== "已终止") process.exit(112);
        if (translate("CLI Interface Explorer") !== "CLI 接口探索员") {
            console.error("CLI Interface Explorer failed:", translate("CLI Interface Explorer"));
            process.exit(113);
        }
        if (translate("Atomic Switcher Explorer") !== "原子切换探索员") process.exit(114);
        if (translate("E2E Test Writer") !== "端到端测试编写员") process.exit(115);
        if (translate("Requirements and Spec Miner") !== "需求与规范挖掘员") process.exit(116);
        if (translate("including 5 active conversations.") !== "包含 5 个活跃会话。") {
            console.error("including 5 active conversations failed:", translate("including 5 active conversations."));
            process.exit(117);
        }
        if (translate("resources") !== "资源") process.exit(118);
        if (translate("scripts") !== "脚本") process.exit(119);
        if (translate("Copy code") !== "复制代码") {
            console.error("Copy code failed:", translate("Copy code"));
            process.exit(120);
        }
        if (translate("Copied!") !== "已复制！") process.exit(121);

        // 18. Permission choices and dropdown options (ask / ask ✓ / always ask / allow / deny)
        if (translate("ask") !== "询问") {
            console.error("ask failed:", translate("ask"));
            process.exit(122);
        }
        if (translate("Ask") !== "询问") process.exit(123);
        if (translate("ask ✓") !== "询问 ✓") {
            console.error("ask checkmark failed:", translate("ask ✓"));
            process.exit(124);
        }
        if (translate("always ask") !== "总是询问") process.exit(125);
        if (translate("Ask first") !== "先询问") process.exit(127);

        // 19. Subagent plural cleanup, s display bug eradication, and Teamwork prompt draft UI
        if (translate("(16 子智能体s)") !== "(16 个子智能体)") {
            console.error("(16 子智能体s) failed:", translate("(16 子智能体s)"));
            process.exit(128);
        }
        if (translate("16 子智能体s") !== "16 个子智能体") process.exit(129);
        if (translate("(16 subagents)") !== "(16 个子智能体)") {
            console.error("(16 subagents) failed:", translate("(16 subagents)"));
            process.exit(130);
        }
        if (translate("16 subagents") !== "16 个子智能体") process.exit(131);
        if (translate("子智能体s") !== "子智能体") process.exit(132);
        if (translate("Teamwork Project Prompt — Draft") !== "团队项目提示词 — 草稿") process.exit(133);
        if (translate("Status: Launched") !== "状态：已启动") process.exit(134);
        if (translate("Requirements") !== "需求清单") process.exit(135);

        // 20. Quota 5-hour limit countdown & MCP tool permissions
        if (translate("You have used some of your 5-hour limit, it will fully refresh in 4 hours, 13 minutes.") !== "您已使用部分 5 小时配额，将在 4 小时 13 分钟后完全刷新。") {
            console.error("5-hour limit countdown failed:", translate("You have used some of your 5-hour limit, it will fully refresh in 4 hours, 13 minutes."));
            process.exit(136);
        }
        if (translate("Allow using this MCP tool?") !== "允许使用此 MCP 工具吗？") {
            console.error("Allow using this MCP tool failed:", translate("Allow using this MCP tool?"));
            process.exit(137);
        }
        if (translate("Allow using this MCP tool") !== "允许使用此 MCP 工具") process.exit(138);

        // 21. System tray menu and WSL entries
        if (translate("Connect to WSL") !== "连接到 WSL") process.exit(139);
        if (translate("Open Antigravity") !== "打开 Antigravity") process.exit(140);
        if (translate("Quit") !== "退出") process.exit(141);
        if (translate("2 个代理s 正在运行") !== "2 个智能体正在运行") {
            console.error("Tray agent plural s failed:", translate("2 个代理s 正在运行"));
            process.exit(142);
        }
        if (translate("2 agents running") !== "2 个智能体正在运行") process.exit(143);
        if (translate("1 agent running") !== "1 个智能体正在运行") process.exit(144);
        if (translate("No agents running") !== "无正在运行的智能体") process.exit(145);

        // 22. /plan command prompt cards, Thinking depth labels (Medium/High/Low)
        if (translate("Plan carefully before executing a task.") !== "在执行任务前周密制定计划。") {
            console.error("Plan command bubble failed:", translate("Plan carefully before executing a task."));
            process.exit(146);
        }
        if (translate("Try Planning with /plan") !== "尝试使用 /plan 制定计划") {
            console.error("Try Planning with /plan failed:", translate("Try Planning with /plan"));
            process.exit(147);
        }
        if (translate("Add /plan to explicitly ask your agent to generate a structured plan before implementation.") !== "添加 /plan 以明确要求您的智能体在开始实现前生成结构化的执行计划。") {
            console.error("Add /plan description failed:", translate("Add /plan to explicitly ask your agent to generate a structured plan before implementation."));
            process.exit(148);
        }
        if (translate("Gemini Flash Medium") !== "Gemini Flash (中等)") process.exit(149);
        if (translate("Medium") !== "中等") process.exit(150);

        // 23. Edit Conversation Title, grill-me command, and all Subagent role names from latest screenshot
        if (translate("Edit Conversation Title") !== "编辑会话标题") {
            console.error("Edit Conversation Title failed:", translate("Edit Conversation Title"));
            process.exit(151);
        }
        if (translate("Interview me to align on a plan.") !== "通过人机交互访谈对齐设计与技术方案。") {
            console.error("Interview me to align on a plan failed:", translate("Interview me to align on a plan."));
            process.exit(152);
        }
        if (translate("Remediation and Hardening Worker") !== "修复与加固工作人员") process.exit(153);
        if (translate("Forensic Integrity Auditor") !== "司法取证与完整性审计员") process.exit(154);
        if (translate("Boundary and Payload Challenger") !== "边界与有效载荷挑战员") process.exit(155);
        if (translate("Concurrency and Swap Challenger") !== "并发与切换挑战员") process.exit(156);
        if (translate("Architecture Reviewer 2") !== "架构审查员 2") {
            console.error("Architecture Reviewer 2 failed:", translate("Architecture Reviewer 2"));
            process.exit(157);
        }
        if (translate("Codebase Reviewer 1") !== "代码库审查员 1") {
            console.error("Codebase Reviewer 1 failed:", translate("Codebase Reviewer 1"));
            process.exit(158);
        }
        if (translate("Frontend and Window Shell Worker") !== "前端与窗口外壳工作人员") process.exit(159);
        if (translate("Backend and Switcher Worker") !== "后端与切换器工作人员") process.exit(160);

        // 24. Confirm Undo dialog description
        if (translate("This undo action will not make any code changes.") !== "此撤销操作不会产生任何代码更改。") {
            console.error("Undo prompt failed:", translate("This undo action will not make any code changes."));
            process.exit(161);
        }
        if (translate("Confirm Undo") !== "确认撤销") process.exit(162);

        // 25. Thinking duration combinations, pure time spans, tool calls, and thought steps
        if (translate("Thinking for 1m 24s") !== "思考了 1 分钟 24 秒") {
            console.error("Thinking 1m 24s failed:", translate("Thinking for 1m 24s"));
            process.exit(163);
        }
        if (translate("Thought for 2m 5s >") !== "思考了 2 分钟 5 秒") {
            console.error("Thought 2m 5s failed:", translate("Thought for 2m 5s >"));
            process.exit(164);
        }
        if (translate("1m 24s") !== "1 分钟 24 秒") process.exit(165);
        if (translate("Explored 16 files, edited 3 files >") !== "已探索 16 个文件，编辑了 3 个文件") process.exit(166);
        if (translate("Ran command: python test.py") !== "执行了命令：python test.py") process.exit(167);
        if (translate("Viewed file: src/app.tsx") !== "查看了文件：src/app.tsx") process.exit(168);
        if (translate("Searching codebase: get_user") !== "正在搜索代码库：get_user") process.exit(169);
        if (translate("Thought Process (32 steps)") !== "思考过程 (32 个步骤)") process.exit(170);
        if (translate("Collapse Thoughts") !== "折叠思考过程") process.exit(171);

        // 26. New uploaded 5 images: Budget, Configuration desc, MCP descriptions, Script controls, Active conversations
        if (translate("89.7% of the customization budget is available.") !== "自定义预算剩余 89.7%") {
            console.error("Budget failed:", translate("89.7% of the customization budget is available."));
            process.exit(172);
        }
        if (translate("Configure default behaviors, skills, and MCP servers.") !== "配置默认行为、技能与 MCP 服务器。") process.exit(173);
        if (translate("Enable Antigravity to deploy apps to Google Cloud Run.") !== "允许 Antigravity 将应用程序部署到 Google Cloud Run。") process.exit(174);
        if (translate("Block all browser JavaScript execution.") !== "阻止所有浏览器 JavaScript 执行。") process.exit(175);
        if (translate("Prompt for approval before running browser scripts.") !== "运行浏览器脚本前提示以获取批准。") process.exit(176);
        if (translate("Allow full browser script execution without prompting.") !== "允许完全执行浏览器脚本，无需提示。") process.exit(177);
        if (translate("1 active conversation.") !== "1 个活跃会话。") process.exit(178);
        if (translate("3 active conversations.") !== "3 个活跃会话。") process.exit(179);

        // 27. Latest 5 images: Edit Conversation Title, tests, Delete server, Outside of Project, Create Project
        if (translate("Edit Conversation Title") !== "编辑会话标题") process.exit(180);
        if (translate("tests") !== "测试") process.exit(181);
        if (translate("Delete server") !== "删除服务器") process.exit(182);
        if (translate("Outside of Project") !== "项目之外") process.exit(183);
        if (translate("Create Antigravity Translation Project") !== "创建 Antigravity 汉化项目") process.exit(184);

        // 28. Git status localization preserving identifiers, branches and paths
        if (translate("On branch main") !== "位于分支 main") process.exit(185);
        if (translate("Your branch is up to date with 'origin/main'.") !== "您的分支已与 'origin/main' 保持同步。") process.exit(186);
        if (translate("Changes not staged for commit:") !== "未暂存以备提交的更改：") process.exit(187);
        if (translate('(use "git add <file>..." to update what will be committed)') !== '（使用 "git add <file>..." 更新要提交的内容）') process.exit(188);
        if (translate('(use "git restore <file>..." to discard changes in working directory)') !== '（使用 "git restore <file>..." 放弃工作目录中的更改）') process.exit(189);
        if (translate("modified:   pet/run_pet.py") !== "已修改:   pet/run_pet.py") process.exit(190);

        // 验证多行整段 Git status 复合结构逐行汉化
        const multilineGit = `On branch main\nYour branch is up to date with 'origin/main'.\n\nChanges not staged for commit:\n  (use "git add <file>..." to update what will be committed)\n  (use "git restore <file>..." to discard changes in working directory)\n\tmodified:   pet/run_pet.py\n\tmodified:   resources/antigravity-zh-CN.json`;
        const translatedMulti = translate(multilineGit);
        if (!translatedMulti.includes("位于分支 main")) process.exit(191);
        if (!translatedMulti.includes("您的分支已与 'origin/main' 保持同步。")) process.exit(192);
        if (!translatedMulti.includes("未暂存以备提交的更改：")) process.exit(193);
        if (!translatedMulti.includes("已修改:   pet/run_pet.py")) process.exit(194);

        // 29. Subagent UI, System Initial Prompt, and Precision Updated rules
        const subagentPrompt = "You are Worker Remediation for the Antigravity Desktop Pet project. Your working directory is: C:\\\\Users\\\\worker";
        const translatedPrompt = translate(subagentPrompt);
        if (!translatedPrompt || !translatedPrompt.includes("您是 Antigravity Desktop Pet 项目的 Remediation 专员。您的工作目录为：")) {
            console.error("Subagent prompt translation failed:", translatedPrompt);
            process.exit(195);
        }

        if (translate("Summary of Completed Remediation") !== "已完成的修复总结") process.exit(196);
        if (translate("Directory Traversal Protection in switcher.py") !== "switcher.py 中的目录遍历防护") process.exit(197);
        if (translate("Eliminated Rollback Self-Deadlock & Latency Penalty") !== "消除回滚自死锁与延迟损耗") process.exit(198);
        if (translate("Worker Remediation") !== "修复专员") process.exit(199);
        if (translate("Remediation and Hardening Worker") !== "修复与加固工作人员") process.exit(200);

        // 验证去除了贪婪 ^Updated (.+)$，技术句子不再产生半中半英怪胎，而时间更新正常翻译
        if (translate("Updated 5 minutes ago") !== "更新于 5 分钟前") process.exit(201);
        if (translate("Updated just now") !== "刚刚更新") process.exit(202);
        const codeSentence = "Updated in restore_backup to synchronize with _thread_lock";
        if (translate(codeSentence) && translate(codeSentence).startsWith("更新于 in restore_backup")) {
            console.error("Greedy Updated leaked:", translate(codeSentence));
            process.exit(203);
        }

        console.log("SUCCESS");
        """
        import tempfile
        js_code = js_template.replace('__REPO_ROOT__', repo_root)
        with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as tf:
            tf.write(js_code)
            temp_path = tf.name

        try:
            proc = subprocess.run(["node", temp_path], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(proc.returncode, 0, f"Node script failed: {proc.stderr}")
            self.assertIn("SUCCESS", proc.stdout)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == '__main__':
    unittest.main()
