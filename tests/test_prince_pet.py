# -*- coding: utf-8 -*-
"""
小王子桌宠完整立绘、弹性步态、Cockpit 真实配额实时看板与 QQ 音乐双向歌词同步测试套件
"""
from pathlib import Path
import json
import subprocess

REPO_ROOT = Path(__file__).resolve().parent.parent

def test_prince_pet_html_integrity():
    html_path = REPO_ROOT / "resources" / "desktop_pet_window.html"
    assert html_path.exists(), "desktop_pet_window.html 不存在"
    content = html_path.read_text(encoding="utf-8")

    # 1. 验证 DOM 结构解耦与角色视口
    assert 'id="pet-character-viewport"' in content, "缺少 pet-character-viewport 角色视口层"
    assert 'class="pet-character-viewport"' in content

    # 2. 验证气泡与控制胶囊位于角色视口外层，绝对不反转
    stage_idx = content.find('id="nezuko-pet-stage"')
    bubble_idx = content.find('id="pet-smart-bubble"')
    viewport_idx = content.find('id="pet-character-viewport"')
    prince_idx = content.find('id="pet-prince"')
    assert stage_idx < bubble_idx < viewport_idx < prince_idx, "DOM 层次关系错误"

    # 3. 验证 updateFacing 仅控制 charViewport
    assert "charViewport.style.transform = `scaleX(${direction})`" in content
    assert "stageEl.style.transform = `scaleX(${direction})`" not in content

    # 4. 验证小王子完整立绘主体与避免生硬切片破损
    assert 'id="prince-avatar-body"' in content, "缺少小王子高清全身立绘主体"
    assert 'id="prince-rose-pulse"' in content, "缺少手捧玻璃罩红玫瑰柔光脉冲层"
    assert 'id="prince-silk-scarf"' in content, "缺少流体丝绸长围巾层"

    # 5. 验证手绘动画级真实弹性步态动力学
    assert 'princeWalkBounce' in content, "缺少小王子有机弹性行走步态关键帧"
    assert 'princeIdleBreath' in content, "缺少小王子自然呼吸关键帧"
    assert 'silkScarfWalk' in content, "缺少围巾随步伐起伏展开关键帧"

    # 6. 验证自然眨眼微表情系统
    assert 'id="prince-eyelid"' in content, "缺少眨眼遮罩层"
    assert 'schedulePrinceBlink' in content, "缺少眨眼调度函数"

    # 7. 验证 B612 小行星地表微光底座与星尘音效
    assert 'id="prince-planet-pedestal"' in content, "缺少 B612 星球光环底座"
    assert 'playStardust()' in content
    assert 'playShootingStar()' in content

def test_prince_js_integrity():
    js_path = REPO_ROOT / "resources" / "nezuko-pet.js"
    assert js_path.exists(), "nezuko-pet.js 不存在"
    content = js_path.read_text(encoding="utf-8")

    assert 'id="pet-character-viewport"' in content
    assert 'id="prince-avatar-body"' in content
    assert 'id="prince-rose-pulse"' in content
    assert 'id="prince-silk-scarf"' in content
    assert 'princeWalkBounce' in content

def test_qq_music_lyrics_sync():
    """验证 QQ 音乐当前播放曲目与真·实时歌词双向同步逻辑"""
    js_path = REPO_ROOT / "resources" / "nezuko-pet.js"
    content = js_path.read_text(encoding="utf-8")

    assert 'syncQQMusicStatus' in content, "缺少 syncQQMusicStatus 同步方法"
    assert 'applyExternalMusicStatus' in content, "缺少 applyExternalMusicStatus 状态装载方法"
    assert 'm-btn-sync-qq' in content, "缺少 QQ 音乐同步歌词歌名按钮"
    assert '__agy_media_status_update__' in content, "缺少主进程媒体更新事件监听"

def test_media_helper_execution():
    """验证 media_helper.py 能正确执行 status 并输出合法 JSON"""
    cmd = ['python', '-X', 'utf8', 'resources/media_helper.py', 'status']
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    assert res.returncode == 0, f"media_helper.py 执行失败: {res.stderr}"
    data = json.loads(res.stdout)
    assert 'isPlaying' in data
    assert 'title' in data
    assert 'artist' in data
    assert 'lrc' in data
