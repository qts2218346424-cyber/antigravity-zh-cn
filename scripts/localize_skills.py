# -*- coding: utf-8 -*-
"""
Antigravity 技能说明全自动汉化引擎 (Skill Localizer)
=====================================================
自动扫描本机安装的所有 Skill（包括官方、第三方插件与内置技能），
将元数据 description 替换为规范准确的中文说明，并将其同步写入前端翻译字典。
"""

import os
import re
import sys
import json
import yaml
from pathlib import Path

# 保证 UTF-8 控制台输出
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# 核心技能汉化字典对照表
SKILL_TRANSLATION_MAP = {
    "a11y-debugging": "基于 web.dev 指南通过 Chrome DevTools MCP 进行无障碍 (a11y) 调试与审计。在测试语义化 HTML、ARIA 标签、焦点状态、键盘导航、点击目标与色彩对比度时使用此技能。",
    "agy-customizations": "Antigravity 自定义扩展系统综合指南与参考手册。用于解释自定义功能的工作原理、加载优先级、发现机制，并指导技能、规则、插件、Hook 与 MCP 服务的创建。",
    "alphafold-database-fetch-and-analyze": "检索并分析蛋白质的 AlphaFold 预测三维结构。当用户提供具体的 UniProt 登录号并需要结构置信度度量 (pLDDT)、结构域边界分析或无序区域评估时使用。",
    "alphagenome-atlas-website-links": "为 AlphaGenome Atlas 网站构建深层链接与 URL。支持生成单变异探索链接、基因组位点视图、候选变异摘要表及 AlphaGenome 参考与突变预测对比。",
    "alphagenome-single-variant-analysis": "利用 AlphaGenome API 分析基因变异对基因表达 (RNA-seq)、染色质可及性 (DNASE)、组蛋白修饰 (ChIP) 及转录因子的功能影响。",
    "alphagenome-variant-impact-score": "使用 AlphaGenome 变异影响 (AVI) 分数评估、注释并分析遗传变异的功能影响。支持单变异查询、批注 VCF 变异集及饱和突变扫描。",
    "android-cli": "Android 官方命令行工具使用指南。辅助创建 Android 工程、在真实或虚拟设备上运行应用、管理 AVD、截屏并检查 UI 布局、检索官方文档。",
    "android-device-hub": "Android 设备控制中心 (Device Hub) 协同操作指南。用于列出、启停、创建和删除 Android 模拟器 (AVD)，镜像控制物理设备并进行布局检查与交互。",
    "antigravity-guide": "Google Antigravity (AGY) 官方综合指南与全景速查手册。涵盖 agy CLI、Antigravity 2.0、IDE 架构、Python SDK、快捷指令与扩展定制体系。",
    "automation": "交互式向导，用于设计与创建计划后台自动化任务。当用户希望配置自动化工作流或定时任务（如每日早间邮件摘要、每周待办汇总）时使用。",
    "biomolecular-structure-viewer": "基于 Mol* 的交互式 3D 生物大分子结构视窗。支持渲染本地工作区或工件中的 .cif、.mmcif、.pdb 结构文件，并管理 3D 注释与关键残基高亮。",
    "chembl-database": "查询 ChEMBL 生物活性分子数据库。用于检索化合物、药物靶点、IC50/Ki 活性数据、上市批准药物及化学结构式搜索。",
    "chrome-devtools": "通过 MCP 使用 Chrome DevTools 进行高效调试、故障排查与浏览器自动化。当调试网页、自动化浏览器交互、分析性能或检查网络请求时使用此技能。",
    "chrome-extensions": "遵循 Manifest V3 最佳实践构建与发布 Chrome 浏览器扩展。当用户要求创建、修改、调试或理解 Chrome 浏览器扩展、插件或涉及 Chrome Extensions API 时使用此技能。",
    "clinical-trials-database": "通过 APIv2 查询 ClinicalTrials.gov 临床试验数据库。支持按适应症、药物、地点、状态或分期搜索临床试验及入排标准。",
    "clinvar-database": "查询 NCBI ClinVar 人类基因变异临床意义与致病性分类数据库（如致病、良性、意义未明 VUS），检索临床证据与阳性基准对照。",
    "compose-preview": "Android Jetpack Compose 实时预览侧边栏操作指南。调用 `android preview render` 渲染 @Preview 函数并在侧边栏视窗中实时显示 UI 预览。",
    "cookie-debugging": "通过 Chrome DevTools MCP 检查、调试并测试 Cookie、会话状态、认证鉴权问题与 Cookie 合规授权。排查 401/403 异常与跨域 SameSite 警告。",
    "credentials": "安全处理 API 密钥与凭据的规范协议。用于验证凭据是否存在，并在缺失时引导用户通过安全配置通道添加密钥。",
    "dbsnp-database": "查询、映射与检索 NCBI dbSNP 数据库中的短遗传变异（SNP、Indel）。支持在 rsID、VCF 基因组坐标与 HGVS 标识符之间相互转换与频率查询。",
    "debug-optimize-lcp": "指导使用 Chrome DevTools MCP 工具调试与优化最大内容绘制 (LCP)。当用户询问 LCP 性能、页面加载缓慢、核心网页指标 (CWV) 优化，或希望提升主内容与首屏大图渲染速度时使用此技能。",
    "embl-ebi-ols": "查询并检索 EMBL-EBI 本体查找服务 (OLS)，跨 250 多个生物医学本体库（如 GO、DOID、HP）导航词条层级与属性定义。",
    "encode-ccres-database": "通过 SCREEN GraphQL API 查询 ENCODE 顺式调控元件登记库 (cCRE)，或查询 ENCODE REST API 检索人类细胞类型实验与 ChIP-seq 峰图数据。",
    "ensembl-database": "查询 Ensembl 数据库以解析基因、转录本与蛋白质 ID，抓取基因组序列与外显子结构，获取变异效应预测 (VEP)。",
    "foldseek-structural-search": "利用 Foldseek API 对蛋白质 3D 结构文件 (.cif, .pdb) 在各大型数据库（PDB、AlphaFold 等）中进行三维结构相似性对齐检索。",
    "generative_ui": "在对话中或作为独立工件渲染丰富的交互式 HTML 微件。当需要向用户展示可视化图表、数据图形、交互控件、教学演示或富媒体内容时使用此技能。",
    "gnomad-database": "查询人类基因组通识数据库 (gnomAD)。检索特定遗传变异的人群等位基因频率、变异罕见度及基因功能丧失不耐受约束指标 (pLI, LOEUF)。",
    "gtex-database": "从 GTEx 项目中检索跨 54 个正常人体组织器官的定量 RNA 表达数据及表达数量性状位点 (eQTL) 关联信息。",
    "human-protein-atlas-database": "从人类蛋白质图谱 (HPA) 中检索蛋白质在人体各组织器官、细胞及亚细胞结构中的半定量表达水平与空间定位分布数据。",
    "interpro-database": "检索 InterPro 蛋白质家族、结构域与功能位点集成数据库。支持结构域架构 (IDA) 检索并注释 GO 术语与功能分类。",
    "jaspar-database": "查询 JASPAR 转录因子结合轮廓数据库。检索特定转录因子的位置频率矩阵 (PFM) 与位置权重矩阵 (PWM)，支持多种主流基序输出格式。",
    "literature-search-arxiv": "检索 arXiv 预印本学术文献。提取论文元数据、摘要并支持下载开放获取全文 PDF 或 HTML 论文。",
    "literature-search-biorxiv": "检索、筛选并下载 bioRxiv 与 medRxiv 生命科学、生物学与医学领域预印本论文元数据及 PDF 全文。",
    "literature-search-europepmc": "检索 Europe PMC 生命科学学术文献库，获取开放获取全文 XML/纯文本、PDF 论文及引用文献列表。",
    "literature-search-openalex": "查询 OpenAlex 全球学术图谱数据库。检索研究论文、学者画像、机构、学术主题、引用计量（h 指数、影响因子）与开放获取全文。",
    "memory-leak-debugging": "诊断并解决 JavaScript/Node.js 应用程序中的内存泄漏问题。当用户报告内存占用过高、OOM 内存溢出错误，或希望分析堆快照 (heapsnapshots) 及运行 memlab 内存泄漏检测工具时使用此技能。",
    "migrate-workflows": "自动将旧版工作流 (Workflows) 迁移为现代技能 (Skills)。扫描现有工作流，创建规范的 SKILL.md 并安全归档历史文件。",
    "modern-web-guidance": "现代 Web 开发最佳实践搜索工具。在处理所有 HTML/CSS 和客户端 JS 任务时强制优先执行，获取最新的 Web API 与前端规范。",
    "ncbi-sequence-fetch": "使用 E-utilities 从 NCBI 数据库检索蛋白质与核苷酸序列。支持通过登录号、基因名称、PubMed 关联合成 CDS 序列提取。",
    "openfda-database": "查询并下载美国 FDA openFDA 开放监管数据。涵盖药物与医疗器械不良事件、召回警示、说明书标签、510(k) 审批与 NDC 药品代码。",
    "opentargets-database": "查询 Open Targets 药物靶点发现平台。检索靶点-疾病关联度、可药性评估、临床前/临床安全证据与已知化合物信息。",
    "pdb-database": "检索并下载蛋白质数据库 (PDB) 实验解析的三维生物大分子结构（X-射线晶体衍射、冷冻电镜 cryo-EM、NMR），获取实验元数据。",
    "plugin": "管理与创建 Antigravity 插件系统。指导插件的启用、禁用、安装、卸载与打包，集成技能、代理、规则与 MCP 服务组件。",
    "predictingthepast": "利用 Aeneas (拉丁文) 与 Ithaca (古希腊文) AI 模型对古代历史碑文与铭文手稿进行残缺复原、作者归属、测年定位与语境分析。",
    "protein-sequence-msa": "使用 EBI Clustal Omega 执行蛋白质多序列比对 (MSA)。用于评估序列同源性、结构域保守性与关键活性残基保守特征。",
    "protein-sequence-similarity-search": "使用 MMseqs2（极速）或 BLAST（高灵敏度）检索同源蛋白质序列，基于序列相似度推断蛋白质潜在生物学功能。",
    "pubchem-database": "查询 PubChem 化学物质数据库。支持按化学品名称、CID、SMILES 检索分子式、理化性质、同分异构体及生物活性数据。",
    "pubmed-database": "检索 PubMed / PMC 生物医学文献数据库。获取论文摘要、全文并关联基因、蛋白质及化合物数据库信息。",
    "pymol": "使用 PyMOL 3D 引擎对蛋白质与分子结构进行可视化、渲染出图、三维对齐重叠、结合口袋分析与按 pLDDT 置信度上色。",
    "quickgo-database": "查询 QuickGO 基因本体论 (GO) 与证据本体 (ECO) 接口。将基因映射到生物学过程、分子功能与细胞组分层次。",
    "reactome-database": "查询 Reactome 生物反应与通路数据库。支持通路富集分析、反应参与物拓扑分析与信号传导层次图谱导出。",
    "retrieving-developer-knowledge": "检索并综合 Google 官方开发者文档（覆盖 Google Cloud, Gemini API, Android, Chrome, Web, Flutter, Firebase 等）。",
    "string-database": "查询 STRING 蛋白质相互作用 (PPI) 数据库。检索蛋白质物理与功能相互作用网络、证据可信度评分与功能通路富集。",
    "troubleshooting": "使用 Chrome DevTools MCP 工具排查浏览器连接与目标页面故障。诊断调试通道异常与连接超时问题。",
    "typesafe-coprocessor": "通用的 TypeSafe Jev (系统一) 直觉式协处理器。用于在无需消耗大量推理 Token 的情况下执行极速微决策：在执行终端命令或提交代码差异前进行安全/风险门禁（一票否决权）、对代码质量或技术方案进行 0~4 分客观评分、意图与错误分类，以及校准的假设真值验证。",
    "ucsc-conservation-and-tfbs": "从 UCSC 基因组浏览器获取进化保守性评分 (phyloP, phastCons) 与转录因子结合位点 (TFBS) 调控区域数据。",
    "ui-plugin-navigation": "发现与当前任务相关的 UI 插件面板，并在对话中呈现一键快捷胶囊按钮，方便用户在侧边栏一键开启/折叠插件面板。",
    "unibind-database": "查询 UniBind 经实验验证的转录因子结合位点数据集，获取高可信度的 TF-DNA 直接相互作用区域坐标数据。",
    "uniprot-database": "访问 UniProtKB、UniParc 与 UniRef 蛋白质核心数据库。检索蛋白质详细注释、功能、分类学谱系、序列与文献证据。",
    "uv": "检查并管理 Python uv 极速包管理器。确保 uv 已安装并正确配置在系统 PATH 环境变量中。",
    "workflow-skill-creator": "将已完成的用户工作流或交互操作沉淀提炼为可复用的自定义智能体技能 (Skill)。"
}

def get_skill_search_roots() -> list[Path]:
    """获取所有技能可能存在的根目录"""
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or ".")
    roots = [
        home / ".gemini" / "skills",
        home / ".gemini" / "config" / "plugins",
        home / ".gemini" / "antigravity" / "builtin" / "skills",
    ]
    return [r for r in roots if r.exists()]

def find_all_skills() -> list[Path]:
    """递归发现所有 SKILL.md 文件"""
    skill_files = []
    for root in get_skill_search_roots():
        for skill_path in root.glob("**/SKILL.md"):
            skill_files.append(skill_path)
    return skill_files

def localize_skill_file(skill_file: Path, dry_run: bool = False) -> tuple[bool, str, str]:
    """
    稳健汉化单个技能的 SKILL.md 文件中的 description 元数据。
    彻底杜绝多行缩进文本遗留与 YAML 损坏问题。
    返回: (是否修改, 技能名, 描述信息)
    """
    skill_name = skill_file.parent.name
    if skill_name not in SKILL_TRANSLATION_MAP:
        return False, skill_name, "未在汉化字典中收录"

    target_desc = SKILL_TRANSLATION_MAP[skill_name]
    try:
        content = skill_file.read_text(encoding="utf-8")
    except Exception as e:
        return False, skill_name, f"读取失败: {e}"

    if not content.startswith("---"):
        return False, skill_name, "无 Frontmatter 标记"

    parts = content.split("---", 2)
    if len(parts) < 3:
        return False, skill_name, "Frontmatter 不完整"

    fm_text = parts[1]
    body_text = parts[2]

    # 解析 YAML 检查是否已包含中文
    try:
        data = yaml.safe_load(fm_text)
        if isinstance(data, dict):
            cur = str(data.get("description", ""))
            if any('\u4e00' <= char <= '\u9fa5' for char in cur):
                return False, skill_name, "已包含中文说明"
    except Exception:
        pass

    if dry_run:
        return True, skill_name, f"待汉化 -> {target_desc[:40]}..."

    # 安全重构 Frontmatter 的 description 块
    # 匹配从 ^description: 开始，到下一个非缩进键名（如 ^[a-zA-Z0-9_-]+:）或 Frontmatter 结尾的所有行
    pattern = r"(?m)^description:(?:[ \t]*[^\r\n]*)?(?:\r?\n[ \t]+[^\r\n]*)*"
    safe_desc = target_desc.replace('"', '\\"')
    new_desc_field = f'description: "{safe_desc}"'

    if re.search(pattern, fm_text):
        new_fm = re.sub(pattern, new_desc_field, fm_text, count=1)
    else:
        new_fm = fm_text.strip() + f"\n{new_desc_field}\n"

    # 验证新生成的 Frontmatter 是否是合法的 YAML
    try:
        parsed_new = yaml.safe_load(new_fm)
        if not isinstance(parsed_new, dict):
            return False, skill_name, "生成的新 Frontmatter 不是合法的映射结构，跳过替换"
    except Exception as e:
        return False, skill_name, f"YAML 语法校验未通过: {e}"

    new_content = f"---{new_fm}---{body_text}"
    if new_content != content:
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

    synced = 0
    for k, v in SKILL_TRANSLATION_MAP.items():
        if k not in data or data[k] != v:
            data[k] = v
            synced += 1

    if synced > 0:
        with open(dict_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return synced

def run_localization(apply_changes: bool = True):
    """执行技能全自动汉化流程"""
    skills = find_all_skills()
    print("=" * 65)
    print("   Antigravity 技能说明全自动汉化引擎 (Skill Localizer)")
    print("=" * 65)
    print(f"• 扫描到技能文件总数: {len(skills)}")
    print("-" * 65)

    updated_count = 0
    skipped_count = 0

    for s_file in skills:
        changed, s_name, msg = localize_skill_file(s_file, dry_run=not apply_changes)
        if changed:
            updated_count += 1
            print(f"  [√] 成功汉化: {s_name:<32} -> {msg[:35]}...")
        else:
            skipped_count += 1

    print("-" * 65)
    if apply_changes:
        print(f"✅ 汉化完成！已更新: {updated_count} 个，保持原有状态: {skipped_count} 个。")
        repo_root = Path(__file__).resolve().parent.parent
        synced = sync_descriptions_to_runtime_dict(repo_root)
        if synced > 0:
            print(f"• 同步更新前端运行字典: resources/antigravity-zh-CN.json (+{synced} 条)")
    else:
        if updated_count > 0:
            print(f"ℹ 巡检发现 {updated_count} 个技能说明需要汉化。运行 --apply 可自动更新。")
        else:
            print("✅ 所有技能均已完成汉化，无需更新。")
    print("=" * 65)

if __name__ == "__main__":
    apply = "--apply" in sys.argv or "-a" in sys.argv
    run_localization(apply_changes=apply)
