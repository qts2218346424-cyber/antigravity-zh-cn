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
        [r"^Cancel\s*\((Ctrl\+D)\)$", "取消 ($1)"],
        [r"^Cancel\s*\((.+?)\)$", "取消 ($1)"],
        [r"^Delete [Pp]lugin\??$", "删除插件"],

        # 筛选与视图模式
        [r"^Only Unread$", "仅未读"],
        [r"^Scheduled$", "已计划"],
        [r"^Project \+ Worktree$", "项目 + 工作树"],
        [r"^Subtitle$", "副标题"],
        [r"^Subtitles$", "字幕"],

        # 插件详情描述
        [r"^Reliable automation, in-depth debugging, and performance analysis in Chrome using Chrome DevTools and Puppeteer\.?$", "使用 Chrome DevTools 和 Puppeteer 在 Chrome 中进行可靠的自动化、深度调试和性能分析。"],
        [r"^Keep your coding agent up to date with the latest web best practices\.?$", "让您的编程智能体始终掌握最新的 Web 最佳实践。"],
        [r"^Universal TypeSafe Jev \(System One\) Coprocessor for rapid micro-decisions, risk gating, multi-criteria scoring, and intent classification across all coding and researc\.\.\.$", "通用的 TypeSafe Jev (系统一) 协处理器，用于在所有编程和研究任务中进行快速微决策、风险门禁、多维度评分及意图分类..."],
        [r"^Universal TypeSafe Jev \(System One\) Coprocessor for rapid micro-decisions, risk gating, multi-criteria scoring, and intent classification across all coding and research tasks\.?$", "通用的 TypeSafe Jev (系统一) 协处理器，用于在所有编程和研究任务中进行快速微决策、风险门禁、多维度评分及意图分类。"],

        # 项目修改数扩展
        [r"^Modified in\s+(\d+)\s+(?:projects?|项目列表|个项目)$", "在 $1 个项目中已修改"],
        [r"^Modified in\s+(\d+)\s+(?:files?|文件)$", "在 $1 个文件中已修改"],
        [r"^Modified in\s+(\d+)\s+(?:items?|项)$", "在 $1 个项目中已修改"],
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
