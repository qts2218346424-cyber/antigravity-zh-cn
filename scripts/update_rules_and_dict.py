# -*- coding: utf-8 -*-
"""
脚本：update_rules_and_dict.py
用途：审查并修复 resources/rules-zh-CN.json，补全丢失的 $1 捕获变量，并注入最新截图发现的翻译规则与字典词条。
"""

import json
import re
import os
import sys

# 避免控制台编码异常
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

RULES_PATH = os.path.join(os.path.dirname(__file__), '..', 'resources', 'rules-zh-CN.json')

def audit_and_update_rules():
    with open(RULES_PATH, 'r', encoding='utf-8') as f:
        rules = json.load(f)

    print(f"原始规则数量: {len(rules)}")

    # 1. 修复已知由于转义丢失 $1, $2 变量的规则
    fix_map = {
        r"^(\d+)\s*days?,\s*(\d+)\s*hours?$": "$1 天 $2 小时",
        r"^(\d+)\s*hours?,\s*(\d+)\s*minutes?$": "$1 小时 $2 分钟",
        r"^(\d+)\s*minutes?,\s*(\d+)\s*seconds?$": "$1 分钟 $2 秒",
        r"^You have used all of your weekly limit,\s*it will fully refresh in (.+?)\.?$": "您的每周配额已用尽，将在 $1 后完全刷新。",
        r"^You have used some of your weekly limit,\s*it will fully refresh in (.+?)\.?$": "您已使用部分每周配额，将在 $1 后完全刷新。",
        r"^You have used all of your five hour limit,\s*it will fully refresh in (.+?)\.?$": "您的 5 小时配额已用尽，将在 $1 后完全刷新。",
        r"^You have used some of your five hour limit,\s*it will fully refresh in (.+?)\.?$": "您已使用部分 5 小时配额，将在 $1 后完全刷新。",
        r"^it will fully refresh in (.+?)\.?$": "将在 $1 后完全刷新。",
        r"^will fully refresh in (.+?)\.?$": "将在 $1 后完全刷新。",
        r"^Modified in\s+(\d+)\s+projects?$": "在 $1 个项目中已修改",
        r"^Modified in\s+(\d+)\s+files?$": "在 $1 个文件中已修改",
        r"^Modified in\s+(\d+)\s+items?$": "在 $1 个项目中已修改",
        r"^Modified in\s+(\d+)\s+项目列表$": "在 $1 个项目中已修改",
        r"^Modified in\s+(.+)$": "修改于 $1",
        r"^Select Environment(?:\s*\((.+)\))?$": "选择运行环境 ($1)",
        r"^Alphabetical\s*\((.+)\)$": "按字母排序 ($1)",
        r"^Media\s*\(Today\s+(.+)\)$": "媒体 (今天 $1)",
        r"^Media\s*\(Yesterday\s+(.+)\)$": "媒体 (昨天 $1)",
        r"^Media\s*\((.+)\)$": "媒体 ($1)",
        r"^Media\s+(\d+)$": "媒体 $1",
        r"([0-9.]+)%\s+of the customization budget is available\.?": "自定义预算剩余 $1%",
        r"\((\d+)\s+subagents?\)": "($1 个子代理)",
        r"^Worked for (\d+)h (\d+)m$": "已工作 $1 小时 $2 分钟",
        r"^Worked for (\d+)m (\d+)s$": "已工作 $1 分钟 $2 秒",
        r"^Worked for (\d+)h$": "已工作 $1 小时",
        r"^Worked for (\d+)m$": "已工作 $1 分钟",
        r"^Worked for (\d+)s$": "已工作 $1 秒",
        r"^Worked for (.+)$": "已工作 $1",
        r"^Skills Used\s+(\d+)$": "已使用技能 $1",
        r"^Skills used\s+(\d+)$": "已使用技能 $1",
        r"^(\d+)\s+tasks?\s+running$": "$1 个任务运行中",
        r"^(\d+)\s+tasks?\s+completed$": "$1 个任务已完成",
        r"^(\d+)\s+tasks?\s+failed$": "$1 个任务失败",
        r"^Thinking for (\d+)s$": "思考了 $1 秒",
        r"^Thought for (\d+)s$": "思考了 $1 秒",
        r"^[Tt]hought for (\d+)s(?:\s*[ˇ⌄▼])?$": "思考了 $1 秒",
        r"^[Tt]hinking for (\d+)s(?:\s*[ˇ⌄▼])?$": "思考了 $1 秒",
        r"^(\d+)\s+tasks?\s+pending$": "$1 个任务等待中",
        r"^(\d+)d$": "$1 天",
        r"^(\d+)h$": "$1 小时",
        r"^(\d+)m$": "$1 分钟",
        r"^(\d+)s$": "$1 秒",
        r"^(\d+)w$": "$1 周",
        r"^(\d+)mo$": "$1 个月",
        r"^(\d+)y$": "$1 年",
        r"^Are you sure you want to delete the project\s*(.+)?$": "确定要删除项目 $1 吗？",
        r"^[Ll]imited[\s-]+[Tt]ime(\s*[✓✔])$": "限时体验$1",
        r"^Record\s+[Aa]udio\s+(.+)$": "录制音频 $1",
        r"^[iI]mage\.(png|jpe?g|gif|webp|svg)$": "图片.$1",
        r"^[aA]ll\s+changes\s+since\s+(.+)$": "自 $1 以来的所有更改",
        r"^[cC]hanges\s+since\s+(.+)$": "自 $1 以来的更改",
        r"^[cC]ompare\s+with\s+(.+)$": "与 $1 进行对比",
        r"^[eE]nabled(\s*[✓✔])$": "已启用$1",
        r"^[dD]isabled(\s*[✓✔])$": "已禁用$1",
        r"^(?:全部|所有|All)?\s*scheduled tasks run as (.+?)\.?$": "所有定时任务均以 $1 运行。",
    }

    new_rules = []
    seen_patterns = set()

    for pattern, repl in rules:
        if pattern == r"^Are you sure you want to delete (.+)\?$":
            project_rule = r"^[Aa]re you sure you want to delete\s+(?:the\s+)?(?:projects?\s+|项目\s*)(.+?)[\?？]?$"
            if project_rule not in seen_patterns:
                seen_patterns.add(project_rule)
                new_rules.append([project_rule, "确定要删除项目 $1 吗？"])

        if pattern == r"^Ran\s+(.+)$":
            time_rules = [
                [r"^[Rr]an for (\d+)\s*(?:mins?|m)\s*(?:>|›)?$", "已运行 $1 分钟"],
                [r"^[Rr]an for (\d+)h\s*(\d+)m\s*(?:>|›)?$", "已运行 $1 小时 $2 分钟"],
                [r"^[Rr]an for (\d+)m\s*(\d+)s\s*(?:>|›)?$", "已运行 $1 分钟 $2 秒"],
                [r"^[Rr]an for (\d+)s\s*(?:>|›)?$", "已运行 $1 秒"],
                [r"^[Ww]orked for (\d+)\s*(?:mins?|m)\s*(?:>|›)?$", "已运行 $1 分钟"],
                [r"^[Ww]orked for (\d+)h\s*(\d+)m\s*(?:>|›)?$", "已运行 $1 小时 $2 分钟"],
                [r"^[Ww]orked for (\d+)m\s*(\d+)s\s*(?:>|›)?$", "已运行 $1 分钟 $2 秒"],
                [r"^[Ww]orked for (\d+)h\s*(?:>|›)?$", "已运行 $1 小时"],
                [r"^[Ww]orked for (\d+)s\s*(?:>|›)?$", "已运行 $1 秒"],
                [r"^[Rr]an for\s+(.+?)\s*(?:>|›)?$", "已运行 $1"],
                [r"^[Ww]orked for\s+(.+?)\s*(?:>|›)?$", "已运行 $1"],
            ]
            for tr_pat, tr_repl in time_rules:
                if tr_pat not in seen_patterns:
                    seen_patterns.add(tr_pat)
                    new_rules.append([tr_pat, tr_repl])

        if pattern in fix_map:
            repl = fix_map[pattern]
        if pattern not in seen_patterns:
            seen_patterns.add(pattern)
            new_rules.append([pattern, repl])

    # 2. 检查是否有规则包含未匹配的捕获组
    print("\n--- 检查潜在丢失捕获组的规则 ---")
    issue_count = 0
    for idx, (pattern, repl) in enumerate(new_rules):
        try:
            compiled = re.compile(pattern)
            num_groups = compiled.groups
            vars_found = re.findall(r'\$(\d+)', repl)
            if num_groups > 0 and len(vars_found) == 0:
                print(f"[警告] [{idx}]: {pattern} 拥有 {num_groups} 个组，但替换为 '{repl}'")
                issue_count += 1
        except Exception as e:
            print(f"[正则语法错误] [{idx}]: {pattern} -> {e}")
            issue_count += 1
    print(f"剩余潜在问题数: {issue_count}")

    # 3. 补充新一批从最新截图提炼的规则
    additional_rules = [
        # 模型重试提示 (Model unavailable, retrying in 34s (attempt 5/9).)
        [r"^Model unavailable, retrying in (\d+)s \(attempt (\d+)/(\d+)\)\.?$", "模型不可用，将在 $1 秒后重试 (第 $2/$3 次尝试)。"],
        [r"^Model unavailable, retrying in (\d+)s\.?$", "模型不可用，将在 $1 秒后重试。"],
        [r"^Model unavailable, retrying in (.+?)\.?$", "模型不可用，将在 $1 后重试。"],
        [r"^Model unavailable\.?$", "模型不可用。"],
        [r"^retrying in (\d+)s \(attempt (\d+)/(\d+)\)\.?$", "将在 $1 秒后重试 (第 $2/$3 次尝试)。"],
        [r"^retrying in (\d+)s\.?$", "将在 $1 秒后重试。"],
        [r"^\(attempt (\d+)/(\d+)\)$", "(第 $1/$2 次尝试)"],

        # Cron 定时任务提示 (All crons run as Flash.)
        [r"^All crons run as (.+?)\.?$", "所有定时任务均以 $1 运行。"],
        [r"^全部 定时任务s? run as (.+?)\.?$", "所有定时任务均以 $1 运行。"],
        [r"^全部 定时任务 run as (.+?)\.?$", "所有定时任务均以 $1 运行。"],

        # 快捷操作与按钮
        [r"^Cancel\s*\((?:Ctrl\+D|Ctrl\s*\+\s*D)\)$", "取消 (Ctrl+D)"],
        [r"^Cancel\s*\((.+?)\)$", "取消 ($1)"],
        [r"^Delete\s+[Pp]lugin(?:\.{3})?\??$", "删除插件"],

        # 筛选与视图模式（支持右侧带勾选标记 ✓ / ✔ 的选中国态）
        [r"^Project\s*\+\s*Worktree(\s*[✓✔])?$", "项目 + 工作树$1"],
        [r"^Only\s+Unread(\s*[✓✔])?$", "仅未读$1"],
        [r"^Scheduled(\s*[✓✔])?$", "已计划$1"],
        [r"^Archived(\s*[✓✔])?$", "已归档$1"],
        [r"^Unread(\s*[✓✔])?$", "未读$1"],
        [r"^Subtitle(\s*[✓✔])?$", "副标题$1"],
        [r"^Subtitles(\s*[✓✔])?$", "字幕$1"],

        # 插件详情描述（前缀模糊通配，彻底防御字符截断与 CSS 省略号）
        [r"^Reliable automation, in-depth debugging.*$", "使用 Chrome DevTools 和 Puppeteer 在 Chrome 中进行可靠的自动化、深度调试和性能分析。"],
        [r"^Keep your coding agent up to date.*$", "让您的编程智能体始终掌握最新的 Web 最佳实践。"],
        [r"^Universal TypeSafe Jev \(System One\) Coprocessor.*$", "通用的 TypeSafe Jev (系统一) 协处理器，用于在所有编程和研究任务中进行快速微决策、风险门禁、多维度评分及意图分类。"],

        # 项目修改数扩展
        [r"^Modified in\s+(\d+)\s+(?:projects?|项目列表|个项目)$", "在 $1 个项目中已修改"],
        [r"^Modified in\s+(\d+)\s+(?:files?|文件)$", "在 $1 个文件中已修改"],
        [r"^Modified in\s+(\d+)\s+(?:items?|项)$", "在 $1 个项目中已修改"],

        # 文件操作与系统目录定位
        [r"^[Ss]how in [Ff]ile [Ee]xplorer$", "在文件资源管理器中显示"],
        [r"^[Rr]eveal in [Ff]ile [Ee]xplorer$", "在文件资源管理器中显示"],
        [r"^[Oo]pen in [Ff]ile [Ee]xplorer$", "在文件资源管理器中打开"],
        [r"^[Ss]how in [Ee]xplorer$", "在资源管理器中显示"],
        [r"^[Ss]how in [Ff]inder$", "在访达中显示"],
        [r"^[Rr]eveal in [Ff]inder$", "在访达中显示"],

        # 工具与调用统计 (5 tools 38)
        [r"^(\d+)\s+tools?$", "$1 个工具"],
        [r"^(\d+)\s+tools?\s+(\d+)$", "$1 个工具 $2"],
        [r"^(\d+)\s+tool\s+calls?$", "$1 次工具调用"],
        [r"^(\d+)\s+tools?\s*,\s*(\d+)\s*calls?$", "$1 个工具，$2 次调用"],

        # 运行方式子短语与定时任务容错
        [r"^runs?\s+as\s+(.+?)\.?$", "以 $1 运行。"],
        [r"^crons?$", "定时任务"],

        # 思考耗时标题与折叠 (Thinking for 3s ˇ)
        [r"^[Tt]hinking for (\d+)s(?:\s*[ˇ⌄▼])?$", "思考了 $1 秒"],
        [r"^[Tt]hinking for (\d+)m (\d+)s(?:\s*[ˇ⌄▼])?$", "思考了 $1 分 $2 秒"],
        [r"^[Tt]hinking for (\d+)m(?:\s*[ˇ⌄▼])?$", "思考了 $1 分钟"],
        [r"^[Tt]hinking for (.+?)(?:\s*[ˇ⌄▼])?$", "思考了 $1"],
        [r"^[Tt]hought for (\d+)s(?:\s*[ˇ⌄▼])?$", "思考了 $1 秒"],
        [r"^[Tt]hought for (\d+)m (\d+)s(?:\s*[ˇ⌄▼])?$", "思考了 $1 分 $2 秒"],
        [r"^[Tt]hought for (.+?)(?:\s*[ˇ⌄▼])?$", "思考了 $1"],
        [r"^[Tt]hought for\s*$", "思考耗时"],
        [r"^[Tt]hinking for\s*$", "思考耗时"],

        # 多操作组合折叠行 (Explored 16 files, ran 7 commands >)
        [r"^[Ee]xplored\s+(\d+)\s+files?,\s*ran\s+(\d+)\s+commands?\s*(?:>|›)?$", "已探索 $1 个文件，执行了 $2 条命令"],
        [r"^[Ee]xplored\s+(\d+)\s+files?,\s*edited\s+(\d+)\s+files?\s*(?:>|›)?$", "已探索 $1 个文件，编辑了 $2 个文件"],
        [r"^[Ee]xploring\s+(\d+)\s+files?,\s*running\s+(\d+)\s+commands?\s*(?:>|›)?$", "正在探索 $1 个文件，正在执行 $2 条命令"],
        [r"^[Ee]xplored\s+(\d+)\s+files?\s*(?:>|›)?$", "已探索 $1 个文件"],
        [r"^[Ee]xploring\s+(\d+)\s+files?\s*(?:>|›)?$", "正在探索 $1 个文件"],
        [r"^[Rr]an\s+(\d+)\s+commands?\s*(?:>|›)?$", "已执行 $1 条命令"],
        [r"^[Rr]unning\s+(\d+)\s+commands?\s*(?:>|›)?$", "正在执行 $1 条命令"],
        [r"^[Ee]dited\s+(\d+)\s+files?\s*(?:>|›)?$", "已编辑 $1 个文件"],
        [r"^[Ee]diting\s+(\d+)\s+files?\s*(?:>|›)?$", "正在编辑 $1 个文件"],

        # 独立动作状态标签 (Edited [icon] file +124 -0)
        [r"^[Ee]dited$", "已编辑"],
        [r"^[Ee]diting$", "正在编辑"],
        [r"^[Cc]reated$", "已创建"],
        [r"^[Cc]reating$", "正在创建"],
        [r"^[Dd]eleted$", "已删除"],
        [r"^[Dd]eleting$", "正在删除"],
        [r"^[Ee]xplored$", "已探索"],
        [r"^[Ee]xploring$", "正在探索"],
        [r"^[Rr]an$", "已执行"],
        [r"^[Rr]unning$", "正在执行"],
        [r"^[Vv]iewed$", "已查看"],
        [r"^[Vv]iewing$", "正在查看"],
        [r"^[Rr]ead$", "已读取"],
        [r"^[Rr]eading$", "正在读取"],

        # 删除确认弹窗 (Are you sure you want to delete the 项目 从0开始学大模型开发?)
        [r"^[Aa]re you sure you want to delete (?:the\s+)?(?:project\s+|项目\s*)?(.+?)[\?？]?$", "确定要删除项目 $1 吗？"],
        [r"^[Aa]re you sure you want to delete (?:the\s+)?(.+?)[\?？]?$", "确定要删除 $1 吗？"],
        [r"^[Aa]re you sure you want to delete the\??$", "确定要删除吗？"],
        [r"^[Aa]re you sure you want to delete\??$", "确定要删除吗？"],

        # 停止钩子阻断 (Stop hook blocked termination: The user has automatically... >)
        [r"^[Ss]top hook blocked termination:\s*The user has automatically\.{3}\s*(?:>|›)?$", "停止钩子已阻止终止：用户已自动..."],
        [r"^[Ss]top hook blocked termination:\s*(.+?)\s*(?:>|›)?$", "停止钩子已阻止终止：$1"],
        [r"^[Ss]top hook blocked termination:\s*$", "停止钩子已阻止终止："],
        [r"^[Ss]top hook blocked termination$", "停止钩子已阻止终止"],
        [r"^The user has automatically\.{3}$", "用户已自动..."],

        # Subagent 运行耗时防丢数字与消息来源 (Worked for / Ran for)
        [r"^[Ww]orked for (\d+)\s*(?:mins?|m)\s*(?:>|›)?$", "已运行 $1 分钟"],
        [r"^[Ww]orked for (\d+)h\s*(\d+)m\s*(?:>|›)?$", "已运行 $1 小时 $2 分钟"],
        [r"^[Ww]orked for (\d+)m\s*(\d+)s\s*(?:>|›)?$", "已运行 $1 分钟 $2 秒"],
        [r"^[Ww]orked for (\d+)h\s*(?:>|›)?$", "已运行 $1 小时"],
        [r"^[Ww]orked for (\d+)s\s*(?:>|›)?$", "已运行 $1 秒"],
        [r"^[Rr]an for (\d+)\s*(?:mins?|m)\s*(?:>|›)?$", "已运行 $1 分钟"],
        [r"^[Rr]an for (\d+)h\s*(\d+)m\s*(?:>|›)?$", "已运行 $1 小时 $2 分钟"],
        [r"^[Rr]an for (\d+)m\s*(\d+)s\s*(?:>|›)?$", "已运行 $1 分钟 $2 秒"],
        [r"^[Rr]an for (\d+)s\s*(?:>|›)?$", "已运行 $1 秒"],
        [r"^[Ww]orked for\s+(.+?)\s*(?:>|›)?$", "已运行 $1"],
        [r"^[Rr]an for\s+(.+?)\s*(?:>|›)?$", "已运行 $1"],
        [r"^已运行\s+分钟\s*(?:>|›)?$", "已运行数分钟"],
        [r"^[Mm]essage from (.+?)\s*(?:>|›)?$", "来自 $1 的消息"],
        [r"^[Hh]eartbeat check confirmed:\s*(.+)$", "心跳检测确认：$1"],

        # 浏览器设置迁移卡片 (Browser settings have moved)
        [r"^[Bb]rowser settings have moved to the Browser section of General settings\.\s*Go to General settings$", "浏览器设置已移至通用设置中的“浏览器”部分。前往通用设置"],
        [r"^[Bb]rowser settings have moved to the Browser section of General settings\.?$", "浏览器设置已移至通用设置中的“浏览器”部分。"],
        [r"^[Bb]rowser settings have moved\.?$", "浏览器设置已移动。"],
        [r"^Go to General settings\.?$", "前往通用设置"],

        # 系统设置与 WSL 连接按钮
        [r"^To modify notification settings, open your operating system's system preferences\.?$", "如需修改通知设置，请打开您操作系统的系统偏好设置。"],
        [r"^Connect$", "连接"],
        [r"^Connecting\.{0,3}$", "正在连接..."],
        [r"^Connected$", "已连接"],
        [r"^Disconnect$", "断开连接"],

        # 模型与用量大标题 (Models & Usage)
        [r"^Models?\s*&\s*Usage$", "模型与用量"],
        [r"^Models?\s+and\s+Usage$", "模型与用量"],

        # 历史会话常见技术标题 (Multi-Agent AI Task Delegation)
        [r"^[Mm]ulti-[Aa]gent AI Task Delegation\s*(?:>|›)?$", "多智能体 AI 任务委派"],

        # 代码差异审查与 Diff 菜单 (View Split Diff / Hide Whitespace Changes / Collapse All)
        [r"^[Vv]iew Split Diff$", "查看分屏差异"],
        [r"^[Vv]iew Unified Diff$", "查看合并差异"],
        [r"^[Hh]ide Whitespace Changes$", "隐藏空白字符更改"],
        [r"^[Ss]how Whitespace Changes$", "显示空白字符更改"],
        [r"^[Cc]ollapse All$", "全部折叠"],
        [r"^[Ee]xpand All$", "全部展开"],

        # Git 提交与推送状态提示 (No commits to push)
        [r"^[Nn]o commits to push\.?$", "没有需要推送的提交"],
        [r"^[Nn]o commits to pull\.?$", "没有需要拉取的提交"],
        [r"^[Nn]o changes to commit\.?$", "没有需要提交的更改"],

        # 自定义预算拆分节点容错 (of the customization budget is available.)
        [r"^of the customization budget is available\.?$", "可用自定义预算。"],
        [r"^of the (.+?) budget is available\.?$", "可用 $1 预算。"],
        [r"^([0-9.]+)%\s+of the customization budget is available\.?$", "自定义预算剩余 $1%"],

        # 子智能体与任务终止状态 (Killed / Killing)
        [r"^[Kk]illed$", "已终止"],
        [r"^[Kk]illing$", "正在终止"],
        [r"^Task (.+?) killed$", "任务 $1 已终止"],
        [r"^Subagent (.+?) killed$", "子代理 $1 已终止"],
        [r"^Agent (.+?) killed$", "代理 $1 已终止"],

        # 子智能体角色名称与通用后缀 (Subagent Role Names)
        [r"^CLI Interface Explorer$", "CLI 接口探索员"],
        [r"^Atomic Switcher Explorer$", "原子切换探索员"],
        [r"^Data Models Explorer$", "数据模型探索员"],
        [r"^E2E Test Writer$", "端到端测试编写员"],
        [r"^Requirements and Spec Miner$", "需求与规范挖掘员"],
        [r"^Auth and Quota Explorer$", "鉴权与配额探索员"],
        [r"^Toolchain and Window Explorer$", "工具链与窗口探索员"],
        [r"^(.+?)\s+Explorer$", "$1 探索员"],
        [r"^(.+?)\s+Writer$", "$1 编写员"],
        [r"^(.+?)\s+Miner$", "$1 挖掘员"],

        # 包含活跃会话统计 (including 5 active conversations.)
        [r"^[Ii]ncluding\s+(\d+)\s+active\s+conversations?\.?$", "包含 $1 个活跃会话。"],
        [r"^[Ii]ncluding\s+(\d+)\s+conversations?\.?$", "包含 $1 个会话。"],
        [r"^[Ii]ncluding\s+(\d+)\s+active\s+tasks?\.?$", "包含 $1 个活跃任务。"],
        [r"^[Ii]ncluding\s+(\d+)\s+active\s+agents?\.?$", "包含 $1 个活跃代理。"],
        [r"^[Ii]ncluding\s+(.+)$", "包含 $1"],

        # 目录与资源分组标签 (resources / scripts)
        [r"^resources$", "资源"],
        [r"^scripts$", "脚本"],

        # 代码块操作与剪贴板 (Copy code / Copied!)
        [r"^[Cc]opy\s+code$", "复制代码"],
        [r"^[Cc]opied\s+code$", "已复制代码"],
        [r"^[Cc]opied!$", "已复制！"],
        [r"^[Cc]opied to clipboard\.?$", "已复制到剪贴板"],
        [r"^[Cc]opy to clipboard\.?$", "复制到剪贴板"],
        [r"^[Cc]opy\s+link$", "复制链接"],
        [r"^[Cc]opy\s+path$", "复制路径"],
        [r"^[Cc]opy\s+relative\s+path$", "复制相对路径"],
    ]

    for pattern, repl in additional_rules:
        if pattern not in seen_patterns:
            seen_patterns.add(pattern)
            new_rules.append([pattern, repl])
        else:
            for item in new_rules:
                if item[0] == pattern:
                    item[1] = repl

    # 保存
    with open(RULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(new_rules, f, ensure_ascii=False, indent=2)

    print(f"更新后规则总数: {len(new_rules)}")
    print("rules-zh-CN.json 审查并更新完毕！")

if __name__ == '__main__':
    audit_and_update_rules()
