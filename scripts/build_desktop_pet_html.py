# -*- coding: utf-8 -*-
"""
生成专为 Windows 独立透明悬浮窗口定制的桌面桌宠页面 desktop_pet_window.html
"""
import sys
import base64
from io import BytesIO
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = REPO_ROOT / "resources" / "media"
OUT_HTML = REPO_ROOT / "resources" / "desktop_pet_window.html"

# 1. 读取并切片祢豆子
nezuko_png = MEDIA_DIR / "nezuko_chibi_pet.png"
im_nezuko = Image.open(nezuko_png).convert('RGBA')
nw, nh = im_nezuko.size

nezuko_boxes = {
    'head': (0, 0, nw, 180),
    'torso': (50, 160, 142, 275),
    'arm_l': (0, 160, 75, 265),
    'arm_r': (120, 160, nw, 265),
    'leg_l': (60, 265, 102, nh),
    'leg_r': (98, 265, 140, nh)
}

b64_nezuko_parts = {}
for name, box in nezuko_boxes.items():
    cropped = im_nezuko.crop(box)
    buf = BytesIO()
    cropped.save(buf, format='WEBP', quality=92)
    b64_nezuko_parts[name] = base64.b64encode(buf.getvalue()).decode('ascii')

# 2. 读取小王子核心与动作素材
prince_webp = MEDIA_DIR / "little_prince_pet.webp"
b64_prince = base64.b64encode(prince_webp.read_bytes()).decode('ascii')

prince_fox_webp = MEDIA_DIR / "prince_action_fox.webp"
b64_prince_fox = base64.b64encode(prince_fox_webp.read_bytes()).decode('ascii')

prince_rose_webp = MEDIA_DIR / "prince_asset_rose.webp"
b64_prince_rose = base64.b64encode(prince_rose_webp.read_bytes()).decode('ascii')

prince_sunset_webp = MEDIA_DIR / "prince_asset_sunset.webp"
b64_prince_sunset = base64.b64encode(prince_sunset_webp.read_bytes()).decode('ascii')

prince_stars_webp = MEDIA_DIR / "prince_asset_stars.webp"
b64_prince_stars = base64.b64encode(prince_stars_webp.read_bytes()).decode('ascii')

# 读取已有的 nezuko-pet.js 中的 CSS 和 DOM
nezuko_js_path = REPO_ROOT / "resources" / "nezuko-pet.js"
nezuko_js_content = nezuko_js_path.read_text(encoding="utf-8")

# 在独立桌面透明窗口中，我们需要：
# 1. html, body 绝对透明、无边框、无滚动条
# 2. #nezuko-pet-root 不再使用固定 fixed 右下角，而是充满窗口或者居中浮动
# 3. 按住角色触发 pywebview.api.start_drag() 原生硬件拖拽
# 4. 支持双击、点击名言、气泡交互等

print("正在生成 desktop_pet_window.html ...")

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>🌸 灶门祢豆子 & 小王子 · 独立桌面悬浮宠物</title>
  <style>
    /* 核心透明化样式 */
    html, body {{
      background: transparent !important;
      background-color: transparent !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
      user-select: none !important;
      -webkit-user-select: none !important;
      width: 100vw;
      height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }}

    /* 覆盖 nezuko-pet-root 定位：在独立桌面窗口内居中放置 */
    #nezuko-pet-root {{
      position: absolute !important;
      left: 50% !important;
      bottom: 20px !important;
      transform: translateX(-50%) !important;
      right: auto !important;
      margin: 0 !important;
      z-index: 1000 !important;
    }}

    /* 角色区域光标为抓手，提示可拖拽 */
    .nezuko-pet-stage, .nezuko-pet-rig, .prince-pet-rig {{
      cursor: grab !important;
    }}
    .nezuko-pet-stage:active, .nezuko-pet-rig:active, .prince-pet-rig:active {{
      cursor: grabbing !important;
    }}

    /* 按钮和输入框允许点击，不触发拖拽 */
    button, input, .bubble-close-btn, .nezuko-capsule-btn, .nezuko-modal-close {{
      cursor: pointer !important;
      -webkit-app-region: no-drag !important;
    }}
  </style>
</head>
<body>
  <!-- 引入桌面桌宠核心引擎 -->
  <script>
    // 标记为独立桌面窗口模式
    window.__IS_DESKTOP_STANDALONE_PET__ = true;

    // 原生无边框拖拽桥接：鼠标在宠物身上按下时通知 Python 端调用 Win32 硬件拖拽
    window.addEventListener('DOMContentLoaded', () => {{
      let isDragging = false;
      let startX = 0, startY = 0;

      document.addEventListener('mousedown', (e) => {{
        // 排除按钮、输入框、控制面板内部
        const target = e.target;
        if (target.closest('button') || target.closest('input') || target.closest('.nezuko-modal-overlay') || target.closest('.bubble-close-btn') || target.closest('.nezuko-action-capsule')) {{
          return;
        }}

        // 仅在点击桌宠身体、气泡或舞台时触发拖拽
        if (target.closest('.nezuko-pet-stage') || target.closest('#pet-nezuko') || target.closest('#pet-prince') || target.closest('#pet-smart-bubble')) {{
          if (e.button === 0) {{ // 鼠标左键
            startX = e.screenX;
            startY = e.screenY;

            // 如果有 pywebview 原生桥接，直接启动 Win32 原生平滑拖拽
            if (window.pywebview && window.pywebview.api && window.pywebview.api.start_drag) {{
              window.pywebview.api.start_drag();
            }}
          }}
        }}
      }});
    }});
  </script>

  <!-- 注入完整桌宠核心代码 -->
  <script>
{nezuko_js_content}
  </script>

  <!-- 桌面专属微调脚本：处理双击看板、托盘联动与位置记忆 -->
  <script>
    (function() {{
      // 增强小王子点击听名言与双击开看板判定
      const princeEl = document.getElementById('pet-prince');
      const nezukoEl = document.getElementById('pet-nezuko');

      if (princeEl) {{
        princeEl.setAttribute('title', '鼠标按住任意拖动 · 单击换名言 · 双击打开看板 · 滚轮切QQ音乐');
      }}
      if (nezukoEl) {{
        nezukoEl.setAttribute('title', '鼠标按住任意拖动 · 悬空蹬腿挣扎 · 双击打开看板 · 滚轮切QQ音乐');
      }}

    }})();
  </script>
</body>
</html>
"""

OUT_HTML.write_text(html_content, encoding="utf-8")
print(f"✅ 成功生成独立桌面端页面: {OUT_HTML} ({OUT_HTML.stat().st_size / 1024:.1f} KB)")
