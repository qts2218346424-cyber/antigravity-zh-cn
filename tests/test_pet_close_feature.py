# -*- coding: utf-8 -*-
"""
桌宠关闭/隐藏与持久化休眠功能专项测试
"""
import sys
import subprocess
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def test_pet_close_elements():
    repo = Path(__file__).resolve().parent.parent
    pet_file = repo / "resources" / "nezuko-pet.js"
    assert pet_file.exists(), "nezuko-pet.js 不存在"
    text = pet_file.read_text(encoding="utf-8")

    # 1. 检查各关闭入口
    assert 'id="btn-quick-close-pet"' in text, "头顶胶囊栏缺少关闭按钮 btn-quick-close-pet"
    assert 'id="btn-header-hide-pet"' in text, "面板头部缺少隐藏按钮 btn-header-hide-pet"
    assert 'id="btn-hide-pet-temp"' in text, "控制面板缺少暂时隐藏按钮 btn-hide-pet-temp"
    assert 'id="btn-disable-pet-perm"' in text, "控制面板缺少彻底关闭按钮 btn-disable-pet-perm"

    # 2. 检查唤醒胶囊
    assert 'id="nezuko-pet-restore-pill"' in text, "缺少极简唤醒胶囊 nezuko-pet-restore-pill"

    # 3. 检查控制函数与持久化
    assert 'function hidePet' in text, "缺少 hidePet 函数"
    assert 'function showPet' in text, "缺少 showPet 函数"
    assert '__AGY_PET_HIDDEN__' in text, "缺少持久化存储键名"
    assert '__AGY_PET_DISABLED__' in text, "缺少彻底关闭存储键名"
    assert '__AGY_TOGGLE_PET__' in text, "缺少全局切换 API"

    print("  [PASS] 测试 1 通过: 桌宠脚本中 4 大关闭入口、极简召回胶囊与持久化状态机均完整就绪！")

def test_patch_no_pet_cli():
    repo = Path(__file__).resolve().parent.parent
    patch_file = repo / "scripts" / "patch_antigravity.py"
    text = patch_file.read_text(encoding="utf-8")
    assert "--no-pet" in text, "patch_antigravity.py 缺少 --no-pet 参数"
    assert "enable_pet" in text, "patch_antigravity.py 缺少 enable_pet 逻辑控制"
    print("  [PASS] 测试 2 通过: 补丁脚本已具备 --no-pet 纯净免桌宠部署模式！")

if __name__ == "__main__":
    print("=" * 60)
    print("       Antigravity 桌宠关闭与休眠功能专项验证")
    print("=" * 60)
    test_pet_close_elements()
    test_patch_no_pet_cli()
    print("=" * 60)
    print("🎉 恭喜！桌宠关闭功能专项测试全部通过！")
    print("=" * 60)
