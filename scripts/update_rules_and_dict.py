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
        r"\((\d+)\s+subagents?\)": "($1 个子智能体)",
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
        r"^[Tt]hinking for (\d+)m (\d+)s(?:\s*[ˇ⌄▼])?$": "思考了 $1 分钟 $2 秒",
        r"^[Tt]hought for (\d+)m (\d+)s(?:\s*[ˇ⌄▼])?$": "思考了 $1 分钟 $2 秒",
        r"^[Tt]hinking for (\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼])?$": "思考了 $1 分钟 $2 秒",
        r"^[Tt]hought for (\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼])?$": "思考了 $1 分钟 $2 秒",
        r"^[Tt]hinking for (\d+)m(?:\s*[ˇ⌄▼])?$": "思考了 $1 分钟",
        r"^[Tt]hought for (\d+)m(?:\s*[ˇ⌄▼])?$": "思考了 $1 分钟",
        r"^Thinking for (\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼])?$": "思考了 $1 分钟 $2 秒",
        r"^Thought for (\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼])?$": "思考了 $1 分钟 $2 秒",
        r"^Thinking for (\d+)m(?:\s*[ˇ⌄▼])?$": "思考了 $1 分钟",
        r"^Thought for (\d+)m(?:\s*[ˇ⌄▼])?$": "思考了 $1 分钟",
        r"^[Tt]hinking for (.+)$": "思考了 $1",
        r"^[Tt]hought for (.+)$": "思考了 $1",
        r"^Ran for (.+)$": "已运行 $1",
        r"^Ran command:\s*(.+)$": "执行了命令：$1",
        r"^Viewed file:\s*(.+)$": "查看了文件：$1",
        r"^Edited file:\s*(.+)$": "编辑了文件：$1",
        r"^Created file:\s*(.+)$": "创建了文件：$1",
        r"^Deleted file:\s*(.+)$": "删除了文件：$1",
        r"^Searching codebase:\s*(.+)$": "正在搜索代码库：$1",
        r"^(\d+)m\s*(\d+)s$": "$1 分钟 $2 秒",
        r"^(\d+)h\s*(\d+)m$": "$1 小时 $2 分钟",
        r"^(\d+)h\s*(\d+)m\s*(\d+)s$": "$1 小时 $2 分钟 $3 秒",
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
        r"^[eE]nabled(\s*[✓✔])$": "已启用$1",
        r"^[dD]isabled(\s*[✓✔])$": "已禁用$1",
        r"^(?:全部|所有|All)?\s*scheduled tasks run as (.+?)\.?$": "所有定时任务均以 $1 运行。",
        r"^(\d+) agents? running$": "$1 个智能体正在运行",
        r"^No agents? running$": "无正在运行的智能体",
        r"^No agents running$": "无正在运行的智能体",
    }

    new_rules = []
    seen_patterns = set()

    for pattern, repl in rules:
        if pattern == r"^\(?(\d+)\s*(?:subagents?|子智能体s?)\)?$":
            continue
        if "hinking for (.+?)" in pattern or "hought for (.+?)" in pattern:
            continue
        if pattern == r"^Are you sure you want to delete (.+)\?$":
            project_rule = r"^[Aa]re you sure you want to delete\s+(?:the\s+)?(?:projects?\s+|项目\s*)(.+?)[\?？]?$"
            if project_rule not in seen_patterns:
                seen_patterns.add(project_rule)
                new_rules.append([project_rule, "确定要删除项目 $1 吗？"])

        if pattern == r"^Ran\s+(.+)$":
            tool_action_rules = [
                [r"^[Rr]an\s+command:\s*(.+)$", "执行了命令：$1"],
                [r"^[Rr]un\s+command:\s*(.+)$", "执行命令：$1"],
                [r"^[Rr]unning\s+command:\s*(.+)$", "正在执行命令：$1"],
                [r"^[Rr]an\s+(\d+)\s+commands?\s*(?:>|›)?$", "已执行 $1 条命令"],
                [r"^[Rr]unning\s+(\d+)\s+commands?\s*(?:>|›)?$", "正在执行 $1 条命令"],
                [r"^[Vv]iewed\s+file:\s*(.+)$", "查看了文件：$1"],
                [r"^[Vv]iewing\s+file:\s*(.+)$", "正在查看文件：$1"],
                [r"^[Vv]iew\s+file:\s*(.+)$", "查看文件：$1"],
                [r"^[Rr]ead\s+file:\s*(.+)$", "读取了文件：$1"],
                [r"^[Rr]eading\s+file:\s*(.+)$", "正在读取文件：$1"],
                [r"^[Ee]dited\s+file:\s*(.+)$", "编辑了文件：$1"],
                [r"^[Ee]diting\s+file:\s*(.+)$", "正在编辑文件：$1"],
                [r"^[Cc]reated\s+file:\s*(.+)$", "创建了文件：$1"],
                [r"^[Cc]reating\s+file:\s*(.+)$", "正在创建文件：$1"],
                [r"^[Dd]eleted\s+file:\s*(.+)$", "删除了文件：$1"],
                [r"^[Dd]eleting\s+file:\s*(.+)$", "正在删除文件：$1"],
                [r"^[Ss]earching\s+codebase:\s*(.+)$", "正在搜索代码库：$1"],
                [r"^[Ss]earched\s+codebase:\s*(.+)$", "已搜索代码库：$1"],
                [r"^[Ss]earching\s+(?:in\s+)?workspace:\s*(.+)$", "正在工作区中搜索：$1"],
                [r"^[Ss]earched\s+(?:in\s+)?workspace:\s*(.+)$", "已在工作区中搜索：$1"],
                [r"^[Ee]xploring\s+directory:\s*(.+)$", "正在探索目录：$1"],
                [r"^[Ee]xplored\s+directory:\s*(.+)$", "已探索目录：$1"],
                [r"^[Cc]alling\s+tool:\s*(.+)$", "正在调用工具：$1"],
                [r"^[Cc]alled\s+tool:\s*(.+)$", "已调用工具：$1"],
                [r"^[Tt]ool\s+result:\s*(.+)$", "工具返回结果：$1"],
                [r"^[Tt]ool\s+call:\s*(.+)$", "工具调用：$1"],
            ]
            for ta_pat, ta_repl in tool_action_rules:
                if ta_pat not in seen_patterns:
                    seen_patterns.add(ta_pat)
                    new_rules.append([ta_pat, ta_repl])

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

        if "hinking for" in pattern and ")m (" in pattern and ")s" in pattern:
            repl = "思考了 $1 分钟 $2 秒"
        elif "hought for" in pattern and ")m (" in pattern and ")s" in pattern:
            repl = "思考了 $1 分钟 $2 秒"
        elif pattern in fix_map:
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

        # 思考耗时标题与折叠 (Thinking for / Thought for All Combinations)
        [r"^[Tt]hinking for (\d+)h\s*(\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 小时 $2 分钟 $3 秒"],
        [r"^[Tt]hought for (\d+)h\s*(\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 小时 $2 分钟 $3 秒"],
        [r"^[Tt]hinking for (\d+)h\s*(\d+)m(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 小时 $2 分钟"],
        [r"^[Tt]hought for (\d+)h\s*(\d+)m(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 小时 $2 分钟"],
        [r"^[Tt]hinking for (\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟 $2 秒"],
        [r"^[Tt]hought for (\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟 $2 秒"],
        [r"^[Tt]hinking for (\d+)m(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟"],
        [r"^[Tt]hought for (\d+)m(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟"],
        [r"^[Tt]hinking for (\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 秒"],
        [r"^[Tt]hought for (\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 秒"],
        [r"^[Tt]hinking for (\d+)\s*(?:mins?|minutes?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟"],
        [r"^[Tt]hought for (\d+)\s*(?:mins?|minutes?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟"],
        [r"^[Tt]hinking for (\d+)\s*(?:secs?|seconds?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 秒"],
        [r"^[Tt]hought for (\d+)\s*(?:secs?|seconds?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 秒"],
        [r"^[Tt]hinking for a few seconds(?:\s*[ˇ⌄▼>›])?$", "思考了数秒"],
        [r"^[Tt]hought for a few seconds(?:\s*[ˇ⌄▼>›])?$", "思考了数秒"],
        [r"^[Tt]hinking for a moment(?:\s*[ˇ⌄▼>›])?$", "思考了片刻"],
        [r"^[Tt]hought for a moment(?:\s*[ˇ⌄▼>›])?$", "思考了片刻"],
        [r"^[Tt]hinking for\s+(.+?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1"],
        [r"^[Tt]hought for\s+(.+?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1"],
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
        [r"^Remediation and Hardening Worker$", "修复与加固工作人员"],
        [r"^Forensic Integrity Auditor$", "司法取证与完整性审计员"],
        [r"^Boundary and Payload Challenger$", "边界与有效载荷挑战员"],
        [r"^Concurrency and Swap Challenger$", "并发与切换挑战员"],
        [r"^Architecture Reviewer (\d+)$", "架构审查员 $1"],
        [r"^Architecture Reviewer$", "架构审查员"],
        [r"^Codebase Reviewer (\d+)$", "代码库审查员 $1"],
        [r"^Codebase Reviewer$", "代码库审查员"],
        [r"^Frontend and Window Shell Worker$", "前端与窗口外壳工作人员"],
        [r"^Backend and Switcher Worker$", "后端与切换器工作人员"],
        [r"^Reviewer (\d+)$", "审查员 $1"],
        [r"^Worker (\d+)$", "工作人员 $1"],
        [r"^Auditor (\d+)$", "审计员 $1"],
        [r"^Challenger (\d+)$", "挑战员 $1"],
        [r"^(.+?)\s+Reviewer\s+(\d+)$", "$1 审查员 $2"],
        [r"^(.+?)\s+Reviewer$", "$1 审查员"],
        [r"^(.+?)\s+Worker\s+(\d+)$", "$1 工作人员 $2"],
        [r"^(.+?)\s+Worker$", "$1 工作人员"],
        [r"^(.+?)\s+Auditor\s+(\d+)$", "$1 审计员 $2"],
        [r"^(.+?)\s+Auditor$", "$1 审计员"],
        [r"^(.+?)\s+Challenger\s+(\d+)$", "$1 挑战员 $2"],
        [r"^(.+?)\s+Challenger$", "$1 挑战员"],
        [r"^(.+?)\s+Specialist\s+(\d+)$", "$1 专家 $2"],
        [r"^(.+?)\s+Specialist$", "$1 专家"],
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

        # 权限与配置下拉项 (包含单选勾选标记 ✓ / ✔)
        [r"^[Aa]sk(\s*[✓✔])?$", "询问$1"],
        [r"^[Aa]llow(\s*[✓✔])?$", "允许$1"],
        [r"^[Dd]eny(\s*[✓✔])?$", "拒绝$1"],
        [r"^[Bb]lock(\s*[✓✔])?$", "阻止$1"],
        [r"^[Aa]lways\s+[Aa]sk(\s*[✓✔])?$", "总是询问$1"],
        [r"^[Aa]sk\s+every\s+time(\s*[✓✔])?$", "每次询问$1"],
        [r"^[Aa]lways\s+[Aa]llow(\s*[✓✔])?$", "总是允许$1"],
        [r"^[Aa]lways\s+[Dd]eny(\s*[✓✔])?$", "总是拒绝$1"],
        [r"^[Aa]sk\s+first(\s*[✓✔])?$", "先询问$1"],
        [r"^[Aa]sk\s+before\s+(?:running|executing)(\s*[✓✔])?$", "执行前询问$1"],
        [r"^[Aa]sk\s+(?:for\s+)?confirmation(\s*[✓✔])?$", "请求确认$1"],

        # 子智能体单复数、残留 s 彻底清洗与规范化 (16 子智能体s / 16 subagents)
        [r"^\((\d+)\s*(?:subagents?|子智能体s?)\)$", "($1 个子智能体)"],
        [r"^(\d+)\s*(?:subagents?|子智能体s?)$", "$1 个子智能体"],
        [r"^\((\d+)\s*子智能体s\)$", "($1 个子智能体)"],
        [r"^(\d+)\s*子智能体s\)$", "$1 个子智能体)"],
        [r"^子智能体s$", "子智能体"],
        [r"^子智能体s\)$", "子智能体)"],
        [r"^Child Subagents\s*\(([0-9]+)\)$", "子智能体 ($1)"],
        [r"^Child Subagents$", "子智能体"],

        # 团队项目草稿与工件面板 UI (Teamwork Prompt Draft)
        [r"^Teamwork Project Prompt(?:\s*[—–-]\s*Draft)?$", "团队项目提示词 — 草稿"],
        [r"^Teamwork Project Prompt$", "团队项目提示词"],
        [r"^Prompt Draft$", "提示词草稿"],
        [r"^Status:\s*Launched$", "状态：已启动"],
        [r"^Status:\s*(.+)$", "状态：$1"],
        [r"^Goal:\s*(.+)$", "目标：$1"],
        [r"^Requested team:\s*(.+)$", "请求团队：$1"],
        [r"^Working directory:\s*(.+)$", "工作目录：$1"],
        [r"^Integrity mode:\s*(.+)$", "完整性模式：$1"],
        [r"^Requirements$", "需求清单"],

        # 配额限制与刷新倒计时 (You have used some of your 5-hour limit, it will fully refresh in 4 hours, 13 minutes.)
        [r"^[Yy]ou have used some of your 5-hour limit,\s*it will fully refresh in (\d+)\s+hours?,\s+(\d+)\s+minutes?\.?$", "您已使用部分 5 小时配额，将在 $1 小时 $2 分钟后完全刷新。"],
        [r"^[Yy]ou have used all of your 5-hour limit,\s*it will fully refresh in (\d+)\s+hours?,\s+(\d+)\s+minutes?\.?$", "您的 5 小时配额已用尽，将在 $1 小时 $2 分钟后完全刷新。"],
        [r"^[Yy]ou have used some of your 5-hour limit,\s*it will fully refresh in (\d+)\s+hours?\.?$", "您已使用部分 5 小时配额，将在 $1 小时后完全刷新。"],
        [r"^[Yy]ou have used all of your 5-hour limit,\s*it will fully refresh in (\d+)\s+hours?\.?$", "您的 5 小时配额已用尽，将在 $1 小时后完全刷新。"],
        [r"^[Yy]ou have used some of your 5-hour limit,\s*it will fully refresh in (\d+)\s+minutes?\.?$", "您已使用部分 5 小时配额，将在 $1 分钟后完全刷新。"],
        [r"^[Yy]ou have used all of your 5-hour limit,\s*it will fully refresh in (\d+)\s+minutes?\.?$", "您的 5 小时配额已用尽，将在 $1 分钟后完全刷新。"],
        [r"^[Yy]ou have used some of your 5-hour limit,\s*it will fully refresh in (.+?)\.?$", "您已使用部分 5 小时配额，将在 $1 后完全刷新。"],
        [r"^[Yy]ou have used all of your 5-hour limit,\s*it will fully refresh in (.+?)\.?$", "您的 5 小时配额已用尽，将在 $1 后完全刷新。"],
        [r"^[Yy]ou have used some of your 5-hour limit\.?$", "您已使用部分 5 小时配额。"],
        [r"^[Yy]ou have used all of your 5-hour limit\.?$", "您的 5 小时配额已用尽。"],
        [r"^[Yy]ou have used some of your weekly limit,\s*it will fully refresh in (\d+)\s+days?,\s+(\d+)\s+hours?\.?$", "您已使用部分每周配额，将在 $1 天 $2 小时后完全刷新。"],
        [r"^[Yy]ou have used all of your weekly limit,\s*it will fully refresh in (\d+)\s+days?,\s+(\d+)\s+hours?\.?$", "您的每周配额已用尽，将在 $1 天 $2 小时后完全刷新。"],
        [r"^[Yy]ou have used some of your weekly limit,\s*it will fully refresh in (\d+)\s+days?\.?$", "您已使用部分每周配额，将在 $1 天后完全刷新。"],
        [r"^[Yy]ou have used all of your weekly limit,\s*it will fully refresh in (\d+)\s+days?\.?$", "您的每周配额已用尽，将在 $1 天后完全刷新。"],
        [r"^[Yy]ou have used some of your weekly limit,\s*it will fully refresh in (\d+)\s+hours?\.?$", "您已使用部分每周配额，将在 $1 小时后完全刷新。"],
        [r"^[Yy]ou have used all of your weekly limit,\s*it will fully refresh in (\d+)\s+hours?\.?$", "您的每周配额已用尽，将在 $1 小时后完全刷新。"],
        [r"^[Ii]t will fully refresh in (\d+)\s+hours?,\s+(\d+)\s+minutes?\.?$", "将在 $1 小时 $2 分钟后完全刷新。"],
        [r"^[Ii]t will fully refresh in (\d+)\s+days?,\s+(\d+)\s+hours?\.?$", "将在 $1 天 $2 小时后完全刷新。"],
        [r"^fully refresh in (\d+)\s+hours?,\s+(\d+)\s+minutes?\.?$", "将在 $1 小时 $2 分钟后完全刷新。"],
        [r"^fully refresh in (\d+)\s+days?,\s+(\d+)\s+hours?\.?$", "将在 $1 天 $2 小时后完全刷新。"],
        [r"^(\d+)\s+hours?,\s*(\d+)\s+minutes?$", "$1 小时 $2 分钟"],
        [r"^(\d+)\s+days?,\s*(\d+)\s+hours?$", "$1 天 $2 小时"],

        # MCP 工具授权弹窗 (Allow using this MCP tool?)
        [r"^[Aa]llow using this MCP tool[\?？]?$", "允许使用此 MCP 工具吗？"],
        [r"^[Aa]llow using this MCP tool\.?$", "允许使用此 MCP 工具"],
        [r"^[Aa]llow using this (.+?) tool[\?？]?$", "允许使用此 $1 工具吗？"],
        [r"^[Aa]llow using this tool[\?？]?$", "允许使用此工具吗？"],
        [r"^[Aa]llow using MCP tool[\?？]?$", "允许使用 MCP 工具吗？"],

        # /plan 计划命令、推荐卡片与提示 (Try Planning with /plan)
        [r"^[Pp]lan carefully before executing a task\.?$", "在执行任务前周密制定计划。"],
        [r"^[Tt]ry [Pp]lanning with /plan\.?$", "尝试使用 /plan 制定计划"],
        [r"^[Aa]dd /plan to explicitly ask your agent to generate a structured plan before implementation\.?$", "添加 /plan 以明确要求您的智能体在开始实现前生成结构化的执行计划。"],
        [r"^[Aa]dd /plan to explicitly ask your agent to generate a (.+?) plan before implementation\.?$", "添加 /plan 以明确要求您的智能体在开始实现前生成 $1 计划。"],
        [r"^[Tt]ry [Pp]lanning with (.+?)$", "尝试使用 $1 制定计划"],

        # 模型思考深度标签 (Medium / High / Low) 与托盘菜单
        [r"^Gemini Flash Medium$", "Gemini Flash (中等)"],
        [r"^Gemini Flash High$", "Gemini Flash (高)"],
        [r"^Gemini Flash Low$", "Gemini Flash (低)"],
        [r"^[Mm]edium$", "中等"],
        [r"^[Hh]igh$", "高"],
        [r"^[Ll]ow$", "低"],
        [r"^Connect to WSL$", "连接到 WSL"],
        [r"^Open Antigravity$", "打开 Antigravity"],
        [r"^Quit$", "退出"],
        [r"^(\d+)\s+agent(?:s)?\s+running$", "$1 个智能体正在运行"],
        [r"^(\d+)\s*个(?:代理|智能体)s?\s*正在运行$", "$1 个智能体正在运行"],
        [r"^No agents? running$", "无正在运行的智能体"],

        # 会话标题编辑与重命名 (Edit Conversation Title)
        [r"^[Ee]dit [Cc]onversation [Tt]itle$", "编辑会话标题"],
        [r"^[Ee]dit [Tt]itle$", "编辑标题"],
        [r"^[Cc]onversation [Tt]itle$", "会话标题"],
        [r"^[Rr]ename [Cc]onversation$", "重命名会话"],

        # 斜杠命令描述与交互 (grill-me / plan)
        [r"^[Ii]nterview me to align on a plan\.?$", "通过人机交互访谈对齐设计与技术方案。"],
        [r"^[Ii]nterview me to align on a plan$", "通过人机交互访谈对齐设计与技术方案"],

        # 对话撤销与回滚提示 (Confirm Undo Action Dialog)
        [r"^[Tt]his undo action will not make any code changes\.?$", "此撤销操作不会产生任何代码更改。"],
        [r"^[Tt]his undo action will not make any changes\.?$", "此撤销操作不会产生任何更改。"],
        [r"^[Tt]his action will not make any code changes\.?$", "此操作不会产生任何代码更改。"],
        [r"^[Tt]his action will not make any changes\.?$", "此操作不会产生任何更改。"],

        # 思考耗时与运行耗时全组合 (Thinking / Thought / Ran / Worked for All Time Formats)
        [r"^[Tt]hinking for (\d+)h\s*(\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 小时 $2 分钟 $3 秒"],
        [r"^[Tt]hought for (\d+)h\s*(\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 小时 $2 分钟 $3 秒"],
        [r"^[Tt]hinking for (\d+)h\s*(\d+)m(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 小时 $2 分钟"],
        [r"^[Tt]hought for (\d+)h\s*(\d+)m(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 小时 $2 分钟"],
        [r"^[Tt]hinking for (\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟 $2 秒"],
        [r"^[Tt]hought for (\d+)m\s*(\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟 $2 秒"],
        [r"^[Tt]hinking for (\d+)m(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟"],
        [r"^[Tt]hought for (\d+)m(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟"],
        [r"^[Tt]hinking for (\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 秒"],
        [r"^[Tt]hought for (\d+)s(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 秒"],
        [r"^[Tt]hinking for (\d+)\s*(?:mins?|minutes?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟"],
        [r"^[Tt]hought for (\d+)\s*(?:mins?|minutes?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 分钟"],
        [r"^[Tt]hinking for (\d+)\s*(?:secs?|seconds?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 秒"],
        [r"^[Tt]hought for (\d+)\s*(?:secs?|seconds?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1 秒"],
        [r"^[Tt]hinking for a few seconds(?:\s*[ˇ⌄▼>›])?$", "思考了数秒"],
        [r"^[Tt]hought for a few seconds(?:\s*[ˇ⌄▼>›])?$", "思考了数秒"],
        [r"^[Tt]hinking for a moment(?:\s*[ˇ⌄▼>›])?$", "思考了片刻"],
        [r"^[Tt]hought for a moment(?:\s*[ˇ⌄▼>›])?$", "思考了片刻"],
        [r"^[Tt]hinking for\s+(.+?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1"],
        [r"^[Tt]hought for\s+(.+?)(?:\s*[ˇ⌄▼>›])?$", "思考了 $1"],

        # 纯独立时间节点清洗 (消除 1m 24s 等独立时间文本的中英混杂)
        [r"^(\d+)h\s*(\d+)m\s*(\d+)s$", "$1 小时 $2 分钟 $3 秒"],
        [r"^(\d+)h\s*(\d+)m$", "$1 小时 $2 分钟"],
        [r"^(\d+)m\s*(\d+)s$", "$1 分钟 $2 秒"],
        [r"^(\d+)h$", "$1 小时"],
        [r"^(\d+)m$", "$1 分钟"],
        [r"^(\d+)s$", "$1 秒"],
        [r"^(\d+)\s*mins?$", "$1 分钟"],
        [r"^(\d+)\s*secs?$", "$1 秒"],

        # 思考动作多重组合与工具调用 (Action Summaries & Tool Invocations)
        [r"^[Ee]xplored\s+(\d+)\s+files?,\s*ran\s+(\d+)\s+commands?(?:\s*[ˇ⌄▼>›])?$", "已探索 $1 个文件，执行了 $2 条命令"],
        [r"^[Ee]xploring\s+(\d+)\s+files?,\s*running\s+(\d+)\s+commands?(?:\s*[ˇ⌄▼>›])?$", "正在探索 $1 个文件，正在执行 $2 条命令"],
        [r"^[Ee]xplored\s+(\d+)\s+files?,\s*edited\s+(\d+)\s+files?(?:\s*[ˇ⌄▼>›])?$", "已探索 $1 个文件，编辑了 $2 个文件"],
        [r"^[Ee]xplored\s+(\d+)\s+files?,\s*created\s+(\d+)\s+files?(?:\s*[ˇ⌄▼>›])?$", "已探索 $1 个文件，创建了 $2 个文件"],
        [r"^[Ee]dited\s+(\d+)\s+files?,\s*created\s+(\d+)\s+files?(?:\s*[ˇ⌄▼>›])?$", "已编辑 $1 个文件，创建了 $2 个文件"],
        [r"^[Rr]an\s+(\d+)\s+commands?,\s*edited\s+(\d+)\s+files?(?:\s*[ˇ⌄▼>›])?$", "已执行 $1 条命令，编辑了 $2 个文件"],
        [r"^[Rr]an\s+command:\s*(.+)$", "执行了命令：$1"],
        [r"^[Rr]un\s+command:\s*(.+)$", "执行命令：$1"],
        [r"^[Rr]unning\s+command:\s*(.+)$", "正在执行命令：$1"],
        [r"^[Vv]iewed\s+file:\s*(.+)$", "查看了文件：$1"],
        [r"^[Vv]iewing\s+file:\s*(.+)$", "正在查看文件：$1"],
        [r"^[Vv]iew\s+file:\s*(.+)$", "查看文件：$1"],
        [r"^[Rr]ead\s+file:\s*(.+)$", "读取了文件：$1"],
        [r"^[Rr]eading\s+file:\s*(.+)$", "正在读取文件：$1"],
        [r"^[Ee]dited\s+file:\s*(.+)$", "编辑了文件：$1"],
        [r"^[Ee]diting\s+file:\s*(.+)$", "正在编辑文件：$1"],
        [r"^[Cc]reated\s+file:\s*(.+)$", "创建了文件：$1"],
        [r"^[Cc]reating\s+file:\s*(.+)$", "正在创建文件：$1"],
        [r"^[Dd]eleted\s+file:\s*(.+)$", "删除了文件：$1"],
        [r"^[Dd]eleting\s+file:\s*(.+)$", "正在删除文件：$1"],
        [r"^[Ss]earching\s+(?:in\s+)?workspace:\s*(.+)$", "正在工作区中搜索：$1"],
        [r"^[Ss]earched\s+(?:in\s+)?workspace:\s*(.+)$", "已在工作区中搜索：$1"],
        [r"^[Ss]earching\s+codebase:\s*(.+)$", "正在搜索代码库：$1"],
        [r"^[Ss]earched\s+codebase:\s*(.+)$", "已搜索代码库：$1"],
        [r"^[Ee]xploring\s+directory:\s*(.+)$", "正在探索目录：$1"],
        [r"^[Ee]xplored\s+directory:\s*(.+)$", "已探索目录：$1"],
        [r"^[Cc]alling\s+tool:\s*(.+)$", "正在调用工具：$1"],
        [r"^[Cc]alled\s+tool:\s*(.+)$", "已调用工具：$1"],
        [r"^[Tt]ool\s+result:\s*(.+)$", "工具返回结果：$1"],
        [r"^[Tt]ool\s+call:\s*(.+)$", "工具调用：$1"],

        # 思考步骤、深度、预算与折叠状态 (Thinking Steps, Budget & Badges)
        [r"^[Tt]hought [Pp]rocess\s*\(([0-9]+)\s*steps?\)$", "思考过程 ($1 个步骤)"],
        [r"^[Tt]hinking [Pp]rocess\s*\(([0-9]+)\s*steps?\)$", "思考过程 ($1 个步骤)"],
        [r"^[Tt]hinking\s*\(([0-9]+)\s*steps?\)$", "正在思考 ($1 个步骤)"],
        [r"^[Tt]hinking\s*\(step\s+([0-9]+)/([0-9]+)\)$", "正在思考 (步骤 $1/$2)"],
        [r"^[Tt]hought\s*for\s+([0-9]+)\s*steps?$", "思考了 $1 个步骤"],
        [r"^[Tt]hinking:\s*(.+)$", "思考中：$1"],
        [r"^[Tt]hinking\s+budget:\s*(.+)$", "思考预算：$1"],
        [r"^[Tt]hinking\s+depth:\s*(.+)$", "思考深度：$1"],
        [r"^[Tt]hinking\s+budget$", "思考预算"],
        [r"^[Tt]hinking\s+depth$", "思考深度"],
        [r"^[Ee]xtended\s+[Tt]hinking$", "扩展思考"],
        [r"^[Dd]eep\s+[Tt]hinking$", "深度思考"],
        [r"^[Cc]ollapse\s+[Tt]houghts?$", "折叠思考过程"],
        [r"^[Ee]xpand\s+[Tt]houghts?$", "展开思考过程"],
        [r"^[Hh]ide\s+[Tt]houghts?$", "隐藏思考过程"],
        [r"^[Ss]how\s+[Tt]houghts?$", "显示思考过程"],
        [r"^[Cc]ollapse\s+[Tt]hinking$", "折叠思考"],
        [r"^[Ee]xpand\s+[Tt]hinking$", "展开思考"],
        [r"^[Hh]ide\s+[Tt]hinking$", "隐藏思考"],
        [r"^[Ss]how\s+[Tt]hinking$", "显示思考"],

        # 图 1：自定义预算比例与文本
        [r"^([0-9.]+)%\s+of the customization budget is available\.?$", "自定义预算剩余 $1%。"],
        [r"^([0-9.]+)%\s+of the customization budget is available$", "自定义预算剩余 $1%"],
        [r"^of the customization budget is available\.?$", "自定义预算可用。"],
        [r"^of the customization budget is available$", "自定义预算可用"],

        # 图 2：配置默认行为、技能与 MCP 服务器说明
        [r"^[Cc]onfigure default behaviors,\s*skills,\s*and MCP servers\.?$", "配置默认行为、技能与 MCP 服务器。"],
        [r"^[Cc]onfigure default behaviors,\s*skills,\s*and MCP servers$", "配置默认行为、技能与 MCP 服务器"],
        [r"^[Cc]onfigure default behaviors,\s*skills,\s*and MCP servers\.\s*了解详情\.?$", "配置默认行为、技能与 MCP 服务器。了解详情。"],

        # 图 3：官方推荐 MCP 服务器描述 (前缀匹配带省略号或完整文本)
        [r"^[Tt]he Cloud Audit Manager remote MCP server allows you to enroll projects,\s*generate audit and scope reports,\s*and check resource enrollment statuses.*$", "Cloud Audit Manager 远程 MCP 服务器允许您登记项目、生成审计与范围报告，并检查资源登记状态。"],
        [r"^[Ii]nvestigate and fix software issues using AI-powered root cause analysis\..*$", "使用基于 AI 的根本原因分析排查并修复软件问题。该 MCP 服务器连接到您的 Antimetal 账户以搜索问题、读取调查数据。"],
        [r"^[Qq]uery and act on your marketing,\s*analytics,\s*CRM,\s*e-commerce,\s*and warehouse data across 325\+\s*connectors.*$", "跨 325+ 个连接器（Meta 广告、Google 广告、TikTok 广告、GA4、HubSpot 等）查询并操作您的营销、分析、CRM、电子商务及数仓数据。"],
        [r"^[Qq]uery your GitLab SDLC as a knowledge graph\..*$", "将您的 GitLab 软件开发生命周期 (SDLC) 作为知识图谱进行查询。Orbit 将群组、项目、源码、合并请求、流水线、工作项和安全发现编入索引。"],
        [r"^[Ee]nable Antigravity to deploy apps to Google Cloud Run\.?$", "允许 Antigravity 将应用程序部署到 Google Cloud Run。"],
        [r"^[Aa]sk questions\.\s*Get answers\.\s*The MCP is a server your coding agent talks to\..*$", "提出问题并获取解答。该 MCP 是代码智能体与之交互的服务器。使用自然语言提问，它将针对您的 PostHog 数据执行查询并返回分析结论。"],

        # 图 4：浏览器脚本执行控制说明
        [r"^[Bb]lock all browser JavaScript execution\.?$", "阻止所有浏览器 JavaScript 执行。"],
        [r"^[Pp]rompt for approval before running browser scripts\.?$", "运行浏览器脚本前提示以获取批准。"],
        [r"^[Aa]llow full browser script execution without prompting\.?$", "允许完全执行浏览器脚本，无需提示。"],
        [r"^[Bb]lock all browser script execution\.?$", "阻止所有浏览器脚本执行。"],
        [r"^[Aa]llow full browser script execution\.?$", "允许完全执行浏览器脚本。"],

        # 图 5：活跃会话数量统计
        [r"^(\d+)\s+active\s+conversations?\.?$", "$1 个活跃会话。"],
        [r"^(\d+)\s+active\s+conversations?$", "$1 个活跃会话"],
        [r"^[Nn]o active conversations?\.?$", "无活跃会话。"],
        [r"^[Nn]o active conversations?$", "无活跃会话"],

        # 最新批次截图规则：会话标题编辑、测试标签、删除服务器、项目之外与会话生成标题
        [r"^[Ee]dit [Cc]onversation [Tt]itle[\.\s]*$", "编辑会话标题"],
        [r"^[Tt]ests?$", "测试"],
        [r"^[Dd]elete [Ss]erver[\.\s]*$", "删除服务器"],
        [r"^[Oo]utside of [Pp]roject$", "项目之外"],
        [r"^[Oo]utside of [Ww]orkspace$", "工作区之外"],
        [r"^[Cc]reate\s+(.+?)\s+[Pp]roject$", "创建 $1 项目"],
        [r"^Antigravity Translation Project$", "Antigravity 汉化项目"],
        [r"^Antigravity Translation$", "Antigravity 汉化"],
        [r"^Translation Project$", "汉化项目"],

        # Git 控制台与源码管理状态提示信息 (Git Status & Hints Localization)
        [r"^[Oo]n branch\s+(.+)$", "位于分支 $1"],
        [r"^[Yy]our branch is up to date with\s+['\"]?(.+?)['\"]?\.?$", "您的分支已与 '$1' 保持同步。"],
        [r"^[Yy]our branch is ahead of\s+['\"]?(.+?)['\"]?\s+by\s+(\d+)\s+commits?\.?$", "您的分支领先 '$1' $2 个提交。"],
        [r"^[Yy]our branch is behind\s+['\"]?(.+?)['\"]?\s+by\s+(\d+)\s+commits?\.?$", "您的分支落后 '$1' $2 个提交。"],
        [r"^[Yy]our branch and\s+['\"]?(.+?)['\"]?\s+have diverged.*$", "您的分支与 '$1' 出现偏离。"],
        [r"^[Cc]hanges not staged for commit:?$", "未暂存以备提交的更改："],
        [r"^[Cc]hanges to be committed:?$", "要提交的更改："],
        [r"^[Uu]ntracked files:?$", "未跟踪的文件："],
        [r"^[Ii]gnored files:?$", "已忽略的文件："],
        [r"^[Uu]nmerged paths:?$", "未合并的路径："],
        [r"^\(use \"git add <file>\.\.\.\" to update what will be committed\)$", "（使用 \"git add <file>...\" 更新要提交的内容）"],
        [r"^\(use \"git restore <file>\.\.\.\" to discard changes in working directory\)$", "（使用 \"git restore <file>...\" 放弃工作目录中的更改）"],
        [r"^\(use \"git restore --staged <file>\.\.\.\" to unstage\)$", "（使用 \"git restore --staged <file>...\" 撤销暂存）"],
        [r"^\(use \"git reset HEAD <file>\.\.\.\" to unstage\)$", "（使用 \"git reset HEAD <file>...\" 撤销暂存）"],
        [r"^\(use \"git add <file>\.\.\.\" to include in what will be committed\)$", "（使用 \"git add <file>...\" 以包含在要提交的内容中）"],
        [r"^\(use \"git checkout -- <file>\.\.\.\" to discard changes in working directory\)$", "（使用 \"git checkout -- <file>...\" 放弃工作目录中的更改）"],
        [r"^\(use \"git push\" to publish your local commits\)$", "（使用 \"git push\" 发布您的本地提交）"],
        [r"^\(use \"git pull\" to merge the remote branch into yours\)$", "（使用 \"git pull\" 将远程分支合并到本地）"],
        [r"^\(commit or discard the untracked or modified content in submodules\)$", "（提交或放弃子模块中未跟踪或已修改的内容）"],
        [r"^modified:\s+(.+)$", "已修改:   $1"],
        [r"^new file:\s+(.+)$", "新文件:   $1"],
        [r"^deleted:\s+(.+)$", "已删除:   $1"],
        [r"^renamed:\s+(.+?)\s*->\s*(.+)$", "重命名:   $1 -> $2"],
        [r"^both modified:\s+(.+)$", "双方均修改: $1"],
        [r"^both added:\s+(.+)$", "双方均添加: $1"],
        [r"^[Nn]o changes added to commit\s*\(use \"git add\" and/or \"git commit -a\"\)$", "没有添加用于提交的更改（使用 \"git add\" 和/或 \"git commit -a\"）"],
        [r"^[Nn]othing to commit,\s*working tree clean$", "无变更需要提交，工作区干净"],
        [r"^[Nn]othing to commit,\s*working directory clean$", "无变更需要提交，工作目录干净"],
        [r"^[Nn]othing added to commit but untracked files present\s*\(use \"git add\" to track\)$", "未添加任何内容至提交，但存在未跟踪文件（使用 \"git add\" 进行跟踪）"],
    ]

    for pattern, repl in additional_rules:
        if pattern not in seen_patterns:
            seen_patterns.add(pattern)
            new_rules.append([pattern, repl])
        else:
            for item in new_rules:
                if item[0] == pattern:
                    item[1] = repl

    # 终极规则清洗：确保所有思考与运行耗时一律采用完整规范的“分钟”和“秒”
    for item in new_rules:
        pat = item[0]
        if ("hinking for" in pat or "hought for" in pat) and ")m" in pat and ")s" in pat:
            item[1] = "思考了 $1 分钟 $2 秒"
        elif ("hinking for" in pat or "hought for" in pat) and ")m" in pat and ")s" not in pat:
            item[1] = "思考了 $1 分钟"
        elif ("hinking for" in pat or "hought for" in pat) and ")s" in pat and ")m" not in pat:
            item[1] = "思考了 $1 秒"

    # 保存
    with open(RULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(new_rules, f, ensure_ascii=False, indent=2)

    print(f"更新后规则总数: {len(new_rules)}")
    print("rules-zh-CN.json 审查并更新完毕！")

if __name__ == '__main__':
    audit_and_update_rules()
