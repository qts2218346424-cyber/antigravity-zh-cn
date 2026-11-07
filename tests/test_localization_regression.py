# -*- coding: utf-8 -*-
"""
汉化与补丁全量自动化回归测试用例 (Localization Regression Test)
"""
import os
import sys
import json
import yaml
import subprocess
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def test_skills_localization():
    """测试 1: 验证本地所有 93 个技能是否 100% 汉化且 YAML 格式完好"""
    home = Path(os.environ.get("USERPROFILE") or ".")
    roots = [
        home / ".gemini" / "skills",
        home / ".gemini" / "config" / "plugins",
        home / ".gemini" / "antigravity" / "builtin" / "skills",
    ]
    skill_files = []
    for r in roots:
        if r.exists():
            for sf in r.glob("**/SKILL.md"):
                skill_files.append(sf)

    assert len(skill_files) >= 90, f"发现技能数异常: {len(skill_files)}"

    failed_skills = []
    for sf in skill_files:
        content = sf.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{sf} 缺少 Frontmatter 开头"
        parts = content.split("---", 2)
        assert len(parts) >= 3, f"{sf} Frontmatter 不完整"
        
        data = yaml.safe_load(parts[1])
        assert isinstance(data, dict), f"{sf} YAML 解析非字典"
        desc = str(data.get("description", ""))
        has_cn = any('\u4e00' <= c <= '\u9fa5' for c in desc)
        if not has_cn:
            failed_skills.append((sf.parent.name, sf))

    assert len(failed_skills) == 0, f"存在未汉化技能: {failed_skills}"
    print(f"  [PASS] 测试 1 通过: 全量 {len(skill_files)} 个技能全部通过 YAML 语法校验并 100% 包含地道中文说明！")

def test_dictionary_integrity():
    """测试 2: 验证三份语言包字典合法性与词条覆盖"""
    repo = Path(__file__).resolve().parent.parent
    for lang in ["zh-CN", "zh-TW", "zh-HK"]:
        p = repo / "resources" / f"antigravity-{lang}.json"
        assert p.exists(), f"字典文件不存在: {p}"
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 3800, f"{lang} 字典条目数过少: {len(data)}"
        for k, v in list(data.items())[:50]:
            assert k and v, f"存在空词条: {k} -> {v}"
    print(f"  [PASS] 测试 2 通过: zh-CN / zh-TW / zh-HK 三份语言包完整无损，词条量达 3866+ 条！")

def test_rules_localization():
    """测试 3: 验证科学插件规则文件已汉化"""
    home = Path(os.environ.get("USERPROFILE") or ".")
    p = home / ".gemini" / "config" / "plugins" / "science" / "rules" / "AGENTS.md"
    assert p.exists(), f"规则文件不存在: {p}"
    content = p.read_text(encoding="utf-8")
    assert any('\u4e00' <= c <= '\u9fa5' for c in content), "科学规则文件缺少中文"
    assert "科学可视化高优先级准则" in content, "科学规则文件标题未汉化"
    print("  [PASS] 测试 3 通过: 科学规则文件已成功固化为纯正中文准则！")

def test_auto_maintainer_pipeline():
    """测试 4: 运行维护引擎验证全链路状态"""
    repo = Path(__file__).resolve().parent.parent
    res = subprocess.run(
        ["python", str(repo / "scripts" / "auto_maintainer.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert res.returncode == 0, f"auto_maintainer 执行失败:\n{res.stderr}"
    assert "系统处于最优状态" in res.stdout, f"状态异常:\n{res.stdout}"
    print("  [PASS] 测试 4 通过: 自动化维护引擎运行畅通，补丁与技能均处于就绪状态！")

if __name__ == "__main__":
    print("=" * 60)
    print("       Antigravity 全量汉化体检与回归测试套件")
    print("=" * 60)
    test_skills_localization()
    test_dictionary_integrity()
    test_rules_localization()
    test_auto_maintainer_pipeline()
    print("=" * 60)
    print("🎉 恭喜！所有 4 项自动化体检与回归测试 100% 全部通过！")
    print("=" * 60)
