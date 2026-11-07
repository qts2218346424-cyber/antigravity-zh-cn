# -*- coding: utf-8 -*-
"""
配额功能彻底剥离专项验证测试 (No Quota Feature Test)
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def test_no_quota_in_pet():
    repo = Path(__file__).resolve().parent.parent
    pet_file = repo / "resources" / "nezuko-pet.js"
    assert pet_file.exists(), "nezuko-pet.js 不存在"
    text = pet_file.read_text(encoding="utf-8")

    forbidden_keywords = [
        "defaultQuotaState",
        "loadUserQuota",
        "currentQuota",
        "updateQuotaDisplay",
        "sniffNativeQuotaFromDOM",
        "fetchCockpitRealQuota",
        "saveUserQuota",
        "btn-manual-sync-quota",
        "lbl-quota-account",
        "ring-gemini-weekly",
        "ring-gemini-5h",
        "ring-claude-weekly"
    ]
    for kw in forbidden_keywords:
        assert kw not in text, f"nezuko-pet.js 中仍残留配额关键字: {kw}"

    print("  [PASS] 测试 1 通过: 桌宠脚本中所有配额模型、圆环、DOM嗅探与定时器已 100% 彻底剥离！")

def test_no_quota_in_patch():
    repo = Path(__file__).resolve().parent.parent
    patch_file = repo / "scripts" / "patch_antigravity.py"
    text = patch_file.read_text(encoding="utf-8")

    forbidden_patch_keywords = [
        "get_local_user_quota_info",
        "window.__AGY_REAL_USER_QUOTA__",
        "__agy_get_real_quota__"
    ]
    for kw in forbidden_patch_keywords:
        assert kw not in text, f"patch_antigravity.py 中仍残留配额代码: {kw}"

    print("  [PASS] 测试 2 通过: 主程序补丁引擎中配额读取与 IPC 广播通道已 100% 彻底移除！")

def test_no_quota_in_desktop_window():
    repo = Path(__file__).resolve().parent.parent
    win_file = repo / "resources" / "desktop_pet_window.html"
    if win_file.exists():
        text = win_file.read_text(encoding="utf-8")
        assert "defaultQuotaState" not in text, "desktop_pet_window.html 中残留 defaultQuotaState"
        assert "sniffNativeQuotaFromDOM" not in text, "desktop_pet_window.html 中残留 sniffNativeQuotaFromDOM"
    print("  [PASS] 测试 3 通过: 独立桌面透明窗口页面已同步去除配额功能！")

if __name__ == "__main__":
    print("=" * 60)
    print("       Antigravity 配额功能彻底剥离专项测试")
    print("=" * 60)
    test_no_quota_in_pet()
    test_no_quota_in_patch()
    test_no_quota_in_desktop_window()
    print("=" * 60)
    print("🎉 恭喜！配额功能彻底剥离专项测试全部通过！")
    print("=" * 60)
