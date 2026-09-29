#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 技能说明全自动汉化引擎 (localize_skills.py)

功能：
1. 自动扫描用户与系统目录下所有已安装技能 (~/.gemini/skills, ~/.gemini/config/plugins, ~/.gemini/antigravity/builtin/skills 等);
2. 提取并精准翻译 SKILL.md 中的 YAML description 元数据说明；
3. 同步将所有技能描述写入前端 DOM 运行时字典 resources/antigravity-zh-CN.json，实现双重保障；
4. 支持单次扫描 (--apply) 与巡检模式 (--check)。
"""

import sys
import json
import re
from pathlib import Path

# UTF-8 编码兼容
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# 技能高精度中文描述映射库 (Skill Localization Catalog)
SKILL_TRANSLATION_MAP = {
    "autoresearch": "执行有界、基于源事实的深入调研循环，起草带引用的研究档案，并在向主流程汇报前通过严格的断言验证与自我审查。",
    "banner-design": "为社交媒体、广告投放、网站首屏 (Hero)、创意资产与印刷品设计横幅 (Banner)。支持极简、渐变、粗排版、3D、拟物微质感等多元艺术风格与 AI 视觉资产生成。",
    "brand": "品牌语调、视觉识别系统 (VI)、信息传达框架、数字资产管理与品牌一致性维护。适用于品牌内容生成、口吻校准、营销物料设计与风格指南制定。",
    "canvas": "创建、检查并更新 Obsidian 白板 (JSON Canvas)，支持文本、文件、链接、分组与连线节点。用于白板状态管理、可视化思维导图、空间布局与白板笔记归档。",
    "defuddle": "在获得明确网络许可的前提下，使用 Defuddle 清洗器将网页文章提取为整洁的 Markdown 文档。用于去除网页杂乱干扰、生成可读文档或预处理维基知识源。",
    "design": "综合设计专家技能：涵盖品牌识别、设计令牌 (Design Tokens)、UI 样式规范、Logo 标识设计、企业视觉识别系统 (CIP)、演示幻灯片与全渠道社媒视觉物料。",
    "design-system": "设计系统与令牌架构：三层令牌体系（基础→语义→组件）、CSS 变量规范、间距与字阶比例、组件开发规范以及符合品牌标准的演示文稿生成。",
    "obsidian-bases": "解析、起草与校验 Obsidian Bases (.base) 文件。支持动态过滤、公式计算、属性配置以及表格、卡片和列表视图，适用于类数据库视图构建与任务跟踪。",
    "obsidian-markdown": "解析、起草与校验 Obsidian 专属 Markdown 语法：包含 Frontmatter 属性、双链 (Wikilinks)、嵌入、标注框 (Callouts)、标签、块引用、公式与 Mermaid 图表。",
    "save": "将选定的回答、关键决策、分析洞察或会话总结以原子事务的形式保存到 Obsidian 知识库中。触发词：/save、保存会话、存档此分析、记录该洞见。",
    "slides": "使用 Chart.js、设计令牌、自适应布局与结构化文案模型，快速构建高质感、交互式的 HTML 战略演示文稿与演示幻灯片。",
    "think": "运用源自 Fable 的十阶循环（观察、倾听、思考、联结、共鸣、创造与成长），针对关键架构、权衡分析、复盘排查或复杂假设进行深度慢思考与严谨决策推演。",
    "ui-styling": "使用 shadcn/ui (Radix UI + Tailwind) 与原子化 Tailwind CSS 构建现代、无障碍且美观的 Web 用户界面。用于组件开发、主题与深色模式定制、视觉排版与前端样式落地。",
    "ui-ux-pro-max": "全平台 (Web/移动/桌面) UI/UX 设计智能中枢。用于界面设计、审查或重构，覆盖组件库、设计系统、无障碍规范、交互体验、响应式排版、配色方案、图表与前端落地规范。",
    "wiki": "通过便携式 claude-obsidian 核心初始化、纳管并路由独立 Obsidian 知识库工作流。用于知识库初始化、架构脚手架、工作区配置与第二大脑持久化维护。",
    "wiki-cli": "检测并调度 Obsidian 官方命令行工具 (CLI) 进行只读访问，执行反向链接检索、标签统计、知识库检索与只读健康排查；修改操作均走事务内核保障。",
    "wiki-fold": "对近期 Obsidian 知识库日志条目进行有界、抽取式、结构幂等的摘要折叠与日志合并，支持预览模式与单次事务应用，在不篡改子页面的前提下精简知识库日志。",
    "wiki-ingest": "将外部素材（粘贴文本、收件箱文件或经审核的网络文章）摄取至 Obsidian 知识库，并附带溯源依据与断言追踪，适用于单文档或有界批量的知识归档。",
    "wiki-lint": "对 Obsidian 知识库执行确定性只读体检。检测孤立笔记、失效双链、Frontmatter 属性异常、空白章节与过期索引，提供详尽的图谱与链接健康报告。",
    "wiki-mode": "读取或配置知识库归档方法论（通用分类、LYT 知识脉络、PARA 四象限或卡片盒笔记法 Zettelkasten），并为新建笔记智能规划推荐归档路径。",
    "wiki-query": "基于 Obsidian 知识库内容进行只读检索与精准问答。在不篡改笔记的前提下，快速查询、总结或提取指定知识库中的关键事实与上下文。",
    "wiki-retrieve": "构建并查询知识库本地上下文 BM25 检索索引，支持多语言语义重排序 (Rerank) 与混合检索，用于精准段落定位、语义检索与相关度诊断。",
    "typesafe-coprocessor": "通用的 TypeSafe Jev (系统一) 直觉式协处理器。用于在无需消耗大量推理 Token 的情况下执行极速微决策：在执行终端命令或提交代码差异前进行安全/风险门禁（一票否决权）、对代码质量或技术方案进行 0~4 分客观评分、意图与错误分类，以及校准的假设真值验证。",
    "a11y-debugging": "基于 web.dev 指南通过 Chrome DevTools MCP 进行无障碍 (a11y) 调试与审计。在测试语义化 HTML、ARIA 标签、焦点状态、键盘导航、点击目标与色彩对比度时使用此技能。",
    "chrome-devtools": "通过 MCP 使用 Chrome DevTools 进行高效调试、故障排查与浏览器自动化。当调试网页、自动化浏览器交互、分析性能或检查网络请求时使用此技能。",
    "chrome-extensions": "遵循 Manifest V3 最佳实践构建与发布 Chrome 浏览器扩展。当用户要求创建、修改、调试或理解 Chrome 浏览器扩展、插件或涉及 Chrome Extensions API 时使用此技能。",
    "debug-optimize-lcp": "指导使用 Chrome DevTools MCP 工具调试与优化最大内容绘制 (LCP)。当用户询问 LCP 性能、页面加载缓慢、核心网页指标 (CWV) 优化，或希望提升主内容与首屏大图渲染速度时使用此技能。",
    "generative_ui": "在聊天中内联或作为独立工件渲染丰富的交互式 HTML 微件。当您需要向用户展示图表、数据可视化、交互式控件、教学演练或任何超越纯文本和 Markdown 的丰富视觉内容时使用此技能。",
    "memory-leak-debugging": "诊断并解决 JavaScript/Node.js 应用程序中的内存泄漏问题。当用户报告内存占用过高、OOM 内存溢出错误，或希望分析堆快照 (heapsnapshots) 及运行 memlab 内存泄漏检测工具时使用此技能。",
    "migrate-workflows": "自动将全局和工作区配置中的旧版工作流 (workflows) 迁移到现代技能 (skills)。扫描现有工作流，创建目标 SKILL.md 文件，并安全归档旧的工作流文件。",
    "modern-web-guidance": "现代 Web 开发最佳实践搜索工具。在处理所有 HTML/CSS 和客户端 JS 任务时强制优先执行，获取最新的 Web API 与前端规范。",
    "troubleshooting": "使用 Chrome DevTools MCP 及官方文档排查连接与目标故障。当 list_pages、new_page 或 navigate_page 失败，或 MCP 服务初始化异常时触发此技能。"
}

def get_skill_search_roots() -> list[Path]:
    """获取所有潜在的技能存储路径"""
    home = Path.home()
    roots = [
        home / ".gemini" / "skills",
        home / ".gemini" / "config" / "plugins",
        home / ".gemini" / "antigravity" / "builtin" / "skills",
        home / ".gemini" / "antigravity-ide" / "plugins",
    ]
    return [r for r in roots if r.exists()]

def find_all_skills() -> list[Path]:
    """发现所有已安装技能的 SKILL.md 文件"""
    skills = []
    for root in get_skill_search_roots():
        for skill_file in root.glob("**/SKILL.md"):
            skills.append(skill_file)
    return sorted(list(set(skills)))

def localize_skill_file(skill_file: Path, dry_run: bool = False) -> tuple[bool, str, str]:
    """
    汉化单个技能的 SKILL.md 文件中的 description 元数据
    返回: (是否修改, 技能名, 描述信息)
    """
    skill_name = skill_file.parent.name
    if skill_name not in SKILL_TRANSLATION_MAP:
        return False, skill_name, "未在汉化字典中收录"

    target_desc = SKILL_TRANSLATION_MAP[skill_name]
    content = skill_file.read_text(encoding="utf-8")

    # 检查当前是否已包含中文
    desc_match = re.search(r"^description:\s*(.*?)$", content, re.MULTILINE)
    if not desc_match:
        # 尝试匹配多行 description (> 或 >-)
        desc_multi_match = re.search(r"^description:\s*[>|-]\s*\n((?:\s+.*?\n)+)", content, re.MULTILINE)
        if desc_multi_match:
            current_desc = desc_multi_match.group(1).strip()
            if any('\u4e00' <= char <= '\u9fa5' for char in current_desc):
                return False, skill_name, "已包含中文说明"
        else:
            return False, skill_name, "未找到 description 字段"
    else:
        current_desc = desc_match.group(1).strip().strip('"\'')
        if any('\u4e00' <= char <= '\u9fa5' for char in current_desc):
            return False, skill_name, "已包含中文说明"

    if dry_run:
        return True, skill_name, f"待汉化 -> {target_desc[:40]}..."

    # 替换单行或多行 description
    new_content = None
    if desc_match:
        old_line = desc_match.group(0)
        # 用安全双引号包裹中文，防止特殊标点破坏 YAML
        safe_desc = target_desc.replace('"', '\\"')
        new_line = f'description: "{safe_desc}"'
        new_content = content.replace(old_line, new_line, 1)
    elif desc_multi_match:
        old_block = desc_multi_match.group(0)
        safe_desc = target_desc.replace('"', '\\"')
        new_block = f'description: "{safe_desc}"\n'
        new_content = content.replace(old_block, new_block, 1)

    if new_content and new_content != content:
        skill_file.write_text(new_content, encoding="utf-8")
        return True, skill_name, target_desc

    return False, skill_name, "无变更"

def sync_descriptions_to_runtime_dict(repo_root: Path):
    """将所有技能的中文描述同步写入 resources/antigravity-zh-CN.json"""
    dict_file = repo_root / "resources" / "antigravity-zh-CN.json"
    if not dict_file.exists():
        return 0

    with open(dict_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for name, zh_desc in SKILL_TRANSLATION_MAP.items():
        if zh_desc and data.get(name) != zh_desc:
            data[f"skill.{name}.description"] = zh_desc
            count += 1

    if count > 0:
        with open(dict_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return count

def run_localization(apply_changes: bool = True):
    print("=" * 65)
    print("   Antigravity 技能说明全自动汉化引擎 (Skill Localizer)")
    print("=" * 65)

    skills = find_all_skills()
    print(f"• 扫描到技能文件总数: {len(skills)}")

    updated_count = 0
    for s in skills:
        modified, name, info = localize_skill_file(s, dry_run=not apply_changes)
        if modified:
            status = "✅ 已汉化" if apply_changes else "⚡ 待汉化"
            print(f"  {status} [{name}] -> {s.parent.name}/SKILL.md")
            updated_count += 1

    repo_root = Path(__file__).resolve().parent.parent
    if apply_changes and updated_count > 0:
        sync_count = sync_descriptions_to_runtime_dict(repo_root)
        print(f"• 同步注入前端运行时字典: {sync_count} 项")

    print("-" * 65)
    if apply_changes:
        print(f"🎉 技能汉化完成！共处理更新 {updated_count} 个技能。")
    else:
        print(f"ℹ 巡检发现 {updated_count} 个技能说明需要汉化。运行 --apply 可自动更新。")
    print("=" * 65)

if __name__ == "__main__":
    apply_mode = "--check" not in sys.argv
    run_localization(apply_changes=apply_mode)
