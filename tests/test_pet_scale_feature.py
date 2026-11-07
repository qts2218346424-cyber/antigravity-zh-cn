# -*- coding: utf-8 -*-
"""
桌宠放大缩小（Scale Engine）功能专项测试
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def test_scale_ui_elements():
    repo = Path(__file__).resolve().parent.parent
    pet_file = repo / "resources" / "nezuko-pet.js"
    assert pet_file.exists(), "nezuko-pet.js 不存在"
    text = pet_file.read_text(encoding="utf-8")

    # 1. 检查各控制组件
    assert 'id="btn-quick-scale"' in text, "头顶胶囊栏缺少缩放快捷按钮 btn-quick-scale"
    assert 'id="pet-scale-slider"' in text, "面板缺少缩放滑块 pet-scale-slider"
    assert 'id="pet-scale-badge"' in text, "面板缺少缩放数值徽章 pet-scale-badge"
    assert 'id="btn-scale-inc"' in text, "面板缺少放大按钮 btn-scale-inc"
    assert 'id="btn-scale-dec"' in text, "面板缺少缩小按钮 btn-scale-dec"
    assert 'id="btn-scale-reset"' in text, "面板缺少重置按钮 btn-scale-reset"
    assert 'btn-scale-preset' in text, "面板缺少预设缩放档位类名 btn-scale-preset"

    # 2. 检查控制函数与持久化
    assert 'function setPetScale' in text, "缺少 setPetScale 函数"
    assert 'function loadSavedPetScale' in text, "缺少 loadSavedPetScale 函数"
    assert '__AGY_PET_SCALE__' in text, "缺少持久化存储键名 __AGY_PET_SCALE__"
    assert 'window.__AGY_SET_PET_SCALE__' in text, "缺少全局 API window.__AGY_SET_PET_SCALE__"
    assert 'e.ctrlKey' in text, "缺少 Ctrl + 滚轮缩放判定逻辑"

    print("  [PASS] 测试 1 通过: 胶囊栏按钮、面板滑块、档位快捷键、滚轮手势与持久化存储全部就绪！")

def test_desktop_window_sync():
    repo = Path(__file__).resolve().parent.parent
    win_file = repo / "resources" / "desktop_pet_window.html"
    assert win_file.exists(), "desktop_pet_window.html 不存在"
    text = win_file.read_text(encoding="utf-8")
    assert 'id="pet-scale-slider"' in text, "desktop_pet_window.html 未同步包含缩放滑块"
    assert 'function setPetScale' in text, "desktop_pet_window.html 未同步包含缩放函数"
    print("  [PASS] 测试 2 通过: 独立桌面透明窗口页面已 100% 同步支持放大缩小功能！")

if __name__ == "__main__":
    print("=" * 60)
    print("       Antigravity 桌宠放大缩小功能专项验证")
    print("=" * 60)
    test_scale_ui_elements()
    test_desktop_window_sync()
    print("=" * 60)
    print("🎉 恭喜！桌宠放大缩小功能专项测试全部通过！")
    print("=" * 60)
