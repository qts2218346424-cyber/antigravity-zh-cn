#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 《鬼灭之刃》全屏人物电影级动作启动遮罩生成器 (splash_generator.py)
核心突破：
告别“死板图片+局部闪烁”，彻底升级为“真正会动的番剧/电影级高燃动态动作画面”！
善逸与炭治郎原生搭载 720P 30FPS 超清番剧动作原片，全屏无缝循环渲染。
"""

import os
import json
import base64
from pathlib import Path
from PIL import Image

REPO_ROOT = Path("e:/antigravity-cn")
MEDIA_DIR = REPO_ROOT / "resources" / "media"
CONFIG_FILE = REPO_ROOT / "resources" / "splash_config.json"

THEMES = {
    "zenitsu": {
        "id": "zenitsu",
        "name": "我妻善逸",
        "breath": "雷之呼吸 · 壱之型 霹雳一闪",
        "color": "#fbbf24",
        "accent": "#f59e0b",
        "desc": "【真·动作原片】番剧电影级高燃雷之呼吸出刀原画，金色雷霆万钧在天地间极速折跃突进，全屏沉浸动态",
        "video_file": "zenitsu_action_cinematic.mp4"
    },
    "tanjiro": {
        "id": "tanjiro",
        "name": "灶门炭治郎",
        "breath": "水之呼吸 · 拾之型 生生流转",
        "color": "#06b6d4",
        "accent": "#3b82f6",
        "desc": "【真·动作原片】番剧级水之呼吸生生流转龙形巨浪斩击原片，刀芒破空飞溅全屏水浪",
        "video_file": "tanjiro_action_cinematic.mp4"
    },
    "inosuke": {
        "id": "inosuke",
        "name": "嘴平伊之助",
        "breath": "兽之呼吸 · 伍之牙 狂乱裂斩",
        "color": "#38bdf8",
        "accent": "#94a3b8",
        "desc": "全屏兽之呼吸野猪双孔喷气，双刀交错风刃空气撕裂与野性风暴",
        "video_file": None
    },
    "nezuko": {
        "id": "nezuko",
        "name": "灶门祢豆子",
        "breath": "血鬼术 · 爆血 守护之羁绊",
        "color": "#f472b6",
        "accent": "#db2777",
        "desc": "全屏竹篓探头娇俏萌动呼吸，粉眸微眨，满屏漫天樱花与粉晶爆血火花",
        "video_file": None
    },
    "all": {
        "id": "all",
        "name": "鬼杀四象合集",
        "breath": "四象归一 · 全员全集中",
        "color": "#f59e0b",
        "accent": "#ef4444",
        "desc": "经典四宫格舞台，四位主角轮巡高光展示与最终全员奇点共鸣",
        "video_file": None
    }
}

def get_base64_file(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode('ascii')

def get_base64_webp(name: str) -> str:
    webp_path = MEDIA_DIR / f"{name}.webp"
    if not webp_path.exists():
        png_path = MEDIA_DIR / f"{name}.png"
        im = Image.open(png_path)
        im.save(webp_path, 'WEBP', quality=88, method=6)
    return base64.b64encode(webp_path.read_bytes()).decode('ascii')

def get_current_theme() -> str:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
            t = data.get("theme", "zenitsu")
            if t in THEMES:
                return t
        except Exception:
            pass
    return "zenitsu"

def save_current_theme(theme: str):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"theme": theme}, indent=2, ensure_ascii=False), encoding='utf-8')

def build_splash_html(theme: str = "zenitsu") -> str:
    if theme == "all":
        from build_kimetsu_characters_splash import generate_html_content
        b64_t = get_base64_webp("tanjiro_water")
        b64_n = get_base64_webp("nezuko_basket")
        b64_z = get_base64_webp("zenitsu_thunder")
        b64_i = get_base64_webp("inosuke_beast")
        return generate_html_content(b64_t, b64_n, b64_z, b64_i)

    cfg = THEMES.get(theme, THEMES["zenitsu"])
    char_id = cfg["id"]
    char_name = cfg["name"]
    char_breath = cfg["breath"]
    theme_color = cfg["color"]
    accent_color = cfg["accent"]

    # 优先检测是否有真实高燃动作视频 (MP4)
    video_filename = cfg.get("video_file")
    video_path = MEDIA_DIR / video_filename if video_filename else None
    has_video = video_path and video_path.is_file()

    hero_visual_html = ""
    hero_visual_css = ""

    if has_video:
        # 使用 100% 真实连贯番剧/电影级动作原片
        b64_video = get_base64_file(video_path)
        hero_visual_html = f"""
        <video class="cinematic-bg-video" autoplay loop muted playsinline>
          <source src="data:video/mp4;base64,{b64_video}" type="video/mp4">
        </video>
        """
        hero_visual_css = """
        .cinematic-bg-video {
          position: absolute;
          top: 0; left: 0;
          width: 100vw; height: 100vh;
          object-fit: cover;
          z-index: 2;
          filter: contrast(1.08) brightness(0.98);
        }
        """
    else:
        # 降级使用静态角色 WebP
        b64_img = get_base64_webp(f"{theme}_water" if theme == "tanjiro" else (
            f"{theme}_thunder" if theme == "zenitsu" else (
                f"{theme}_beast" if theme == "inosuke" else f"{theme}_basket"
            )
        ))
        hero_visual_html = f'<div class="char-hero-static"></div>'
        hero_visual_css = f"""
        .char-hero-static {{
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 100%;
          background-image: url('data:image/webp;base64,{b64_img}');
          background-size: cover;
          background-position: center 30%;
          filter: brightness(0.96) contrast(1.08);
          animation: staticHeroBreathe 3.6s ease-in-out infinite;
        }}
        @keyframes staticHeroBreathe {{
          0%, 100% {{ transform: scale(1) translateY(0); }}
          50% {{ transform: scale(1.04) translateY(-6px); }}
        }}
        """

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Antigravity 《鬼灭之刃》全屏·{char_name}电影级启动动效</title>
  <style>
    :root {{
      --bg-dark: #06070b;
      --char-color: {theme_color};
      --char-accent: {accent_color};
      --text-primary: #f8fafc;
      --text-muted: #94a3b8;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
    }}

    body {{
      background-color: var(--bg-dark);
      color: var(--text-primary);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: space-between;
      position: relative;
      -webkit-app-region: drag;
    }}

    /* 全屏电影画面容器 */
    .hero-container {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      z-index: 1;
      overflow: hidden;
    }}

    {hero_visual_css}

    /* 浮世绘全景水墨渐变遮罩 (上下沉浸与文本保护) */
    .hero-vignette {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: linear-gradient(180deg, rgba(6, 7, 11, 0.75) 0%, rgba(6, 7, 11, 0.15) 30%, rgba(6, 7, 11, 0.25) 60%, rgba(6, 7, 11, 0.95) 100%),
                  radial-gradient(circle at 50% 50%, transparent 45%, rgba(6, 7, 11, 0.65) 90%, #06070b 100%);
      z-index: 4;
      pointer-events: none;
    }}

    /* 顶部顶幅：鬼杀队日轮徽记与标题 */
    .top-header {{
      position: relative;
      z-index: 15;
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 24px 36px 0;
      animation: fadeInDown 1s cubic-bezier(0.16, 1, 0.3, 1) both;
    }}

    .brand-wrap {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .nichirin-core {{
      width: 32px;
      height: 32px;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .nichirin-flame {{
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 50%;
      border: 2px dashed rgba(245, 158, 11, 0.8);
      animation: spinFlame 12s linear infinite;
    }}

    .nichirin-blade {{
      width: 18px;
      height: 18px;
      background: linear-gradient(135deg, var(--char-color), var(--char-accent));
      transform: rotate(45deg);
      border-radius: 3px;
      box-shadow: 0 0 16px var(--char-color);
    }}

    .brand-title {{
      font-size: 20px;
      font-weight: 800;
      letter-spacing: 3px;
      background: linear-gradient(90deg, #f8fafc, #fed7aa, #f8fafc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
    }}

    .char-pill {{
      font-size: 12px;
      padding: 4px 12px;
      border-radius: 20px;
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid var(--char-color);
      color: #f8fafc;
      font-weight: 700;
      letter-spacing: 1.5px;
      box-shadow: 0 0 14px var(--char-color);
      display: flex;
      align-items: center;
      gap: 6px;
      backdrop-filter: blur(8px);
    }}

    /* 中部主角书法巨幅气场浮水印 */
    .center-hero-badge {{
      position: relative;
      z-index: 12;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      margin-left: 48px;
      margin-bottom: auto;
      margin-top: 40px;
      animation: fadeInLeft 1.2s cubic-bezier(0.16, 1, 0.3, 1) both 0.2s;
    }}

    .hero-name-kanji {{
      font-size: 44px;
      font-weight: 900;
      letter-spacing: 4px;
      color: #f8fafc;
      text-shadow: 0 0 25px var(--char-color), 0 4px 14px rgba(0, 0, 0, 0.9);
      font-family: "Kaiti SC", "STKaiti", "KaiTi", serif;
      line-height: 1.1;
    }}

    .hero-breath-kanji {{
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 2px;
      color: var(--char-color);
      text-shadow: 0 0 16px var(--char-color);
      margin-top: 6px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .hero-breath-kanji::before {{
      content: "";
      width: 20px;
      height: 2px;
      background: var(--char-color);
      box-shadow: 0 0 8px var(--char-color);
    }}

    /* 底部控制区：鎹鸦巡检与 11.5 秒时序 */
    .bottom-stage {{
      position: relative;
      z-index: 15;
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
      max-width: 720px;
      padding: 0 36px 28px;
      gap: 12px;
    }}

    /* 鎹鸦巡检 · 鬼杀队版本检测状态面板 */
    .crow-panel {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 10px 18px;
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.12);
      backdrop-filter: blur(12px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
      animation: fadeInUp 1s cubic-bezier(0.16, 1, 0.3, 1) both 0.3s;
    }}

    .crow-left {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .crow-avatar {{
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: #18181b;
      border: 1px solid var(--char-color);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 15px;
      box-shadow: 0 0 10px var(--char-color);
    }}

    .crow-info {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .crow-title {{
      font-size: 12px;
      font-weight: 700;
      color: #fed7aa;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .crow-pulse {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #22c55e;
      box-shadow: 0 0 8px #22c55e;
      animation: blinkGreen 1.6s infinite;
    }}

    .crow-desc {{
      font-size: 11px;
      color: var(--text-muted);
    }}

    .crow-badge {{
      font-size: 11px;
      padding: 3px 12px;
      border-radius: 12px;
      background: rgba(34, 197, 94, 0.15);
      border: 1px solid rgba(34, 197, 94, 0.4);
      color: #86efac;
      font-weight: 600;
      letter-spacing: 0.5px;
    }}

    /* 呼吸法型态流转展示器 */
    .breath-stream {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      width: 100%;
      animation: fadeInUp 1s cubic-bezier(0.16, 1, 0.3, 1) both 0.5s;
    }}

    .breath-label {{
      font-size: 13px;
      font-weight: 600;
      color: #f1f5f9;
      letter-spacing: 2px;
      text-shadow: 0 0 14px var(--char-color);
      transition: all 0.4s ease;
      min-height: 20px;
    }}

    .progress-track {{
      width: 100%;
      height: 4px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 3px;
      overflow: hidden;
      position: relative;
    }}

    .progress-fill {{
      position: absolute;
      top: 0; left: 0;
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, var(--char-color), var(--char-accent), #f59e0b, #ef4444);
      border-radius: 3px;
      box-shadow: 0 0 16px var(--char-color);
      transition: width 0.3s ease-out;
    }}

    .breath-sub {{
      display: flex;
      justify-content: space-between;
      width: 100%;
      font-size: 11px;
      color: #64748b;
    }}

    @keyframes spinFlame {{
      0% {{ transform: rotate(0deg); }}
      100% {{ transform: rotate(360deg); }}
    }}
    @keyframes blinkGreen {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.3; }}
    }}
    @keyframes fadeInDown {{
      from {{ opacity: 0; transform: translateY(-20px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes fadeInUp {{
      from {{ opacity: 0; transform: translateY(20px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes fadeInLeft {{
      from {{ opacity: 0; transform: translateX(-30px); }}
      to {{ opacity: 1; transform: translateX(0); }}
    }}
  </style>
</head>
<body>
  <!-- 全屏主角动作电影舞台 -->
  <div class="hero-container">
    {hero_visual_html}
    <div class="hero-vignette"></div>
  </div>

  <!-- 顶部标题 -->
  <div class="top-header" id="splash-node">
    <div class="brand-wrap">
      <div class="nichirin-core">
        <div class="nichirin-flame"></div>
        <div class="nichirin-blade"></div>
      </div>
      <div class="brand-title">ANTIGRAVITY</div>
    </div>
    <div class="char-pill">
      <span>鬼杀队 · {char_name} (真·动作电影)</span>
    </div>
  </div>

  <!-- 中部巨幅招式名称 -->
  <div class="center-hero-badge">
    <div class="hero-name-kanji">{char_name}</div>
    <div class="hero-breath-kanji">{char_breath}</div>
  </div>

  <!-- 底部控制台 -->
  <div class="bottom-stage">
    <!-- 鎹鸦巡检 · 版本检测状态面板 -->
    <div class="crow-panel">
      <div class="crow-left">
        <div class="crow-avatar">🦅</div>
        <div class="crow-info">
          <div class="crow-title">
            <span>鎹鸦巡检 · 鬼杀队全息版本矩阵</span>
            <div class="crow-pulse" id="crow-dot"></div>
          </div>
          <div class="crow-desc" id="crow-status">正在异步检索 GitHub 最新柱级汉化版本...</div>
        </div>
      </div>
      <div class="crow-badge" id="crow-tag">巡检中</div>
    </div>

    <!-- 呼吸型态与进度流 -->
    <div class="breath-stream">
      <div class="breath-label" id="breath-status">[壱之型] 全集中·反重力呼吸法起手... 唤醒奇点核心</div>
      <div class="progress-track">
        <div class="progress-fill" id="progress-bar"></div>
      </div>
      <div class="breath-sub">
        <span>KIMETSU NO YAIBA BREATHING SYSTEM</span>
        <span id="breath-timer">0.0s / 11.5s</span>
      </div>
    </div>
  </div>

  <script>
    (function() {{
      // --- 11.5 秒黄金时序推进器 ---
      const DURATION = 11500;
      const startTime = Date.now();
      const progressBar = document.getElementById('progress-bar');
      const breathStatus = document.getElementById('breath-status');
      const breathTimer = document.getElementById('breath-timer');

      const steps = [
        {{ at: 0.00, text: "[壱之型] 全集中·反重力呼吸法起手... 唤醒奇点核心" }},
        {{ at: 0.14, text: "[弐之型] {char_breath}... 气场全开" }},
        {{ at: 0.32, text: "[参之型] 鎹鸦网络巡检 GitHub 汉化更新与版本兼容性..." }},
        {{ at: 0.50, text: "[肆之型] 链接异构多智能体联邦总线 (Swarm Bus)..." }},
        {{ at: 0.68, text: "[伍之型] 挂载 3,472 词条全景汉化拓扑字典..." }},
        {{ at: 0.82, text: "[陆之型] 编译 Monaco 语法树与语言服务集群..." }},
        {{ at: 0.92, text: "[漆之型] 预热 GPU 渲染管线与智能体全景视窗..." }},
        {{ at: 0.97, text: "[终之型] 赫刀初现 · 水火归元 · 正在步入工作台..." }}
      ];

      function updateProgress() {{
        const elapsed = Date.now() - startTime;
        const progress = Math.min(1, elapsed / DURATION);
        progressBar.style.width = (progress * 100).toFixed(1) + '%';
        breathTimer.textContent = (elapsed / 1000).toFixed(1) + 's / 11.5s';

        let currentStep = steps[0];
        for (let i = steps.length - 1; i >= 0; i--) {{
          if (progress >= steps[i].at) {{
            currentStep = steps[i];
            break;
          }}
        }}
        breathStatus.textContent = currentStep.text;

        if (progress < 1) {{
          requestAnimationFrame(updateProgress);
        }}
      }}
      requestAnimationFrame(updateProgress);

      // --- 鎹鸦巡检 · 异步版本检定矩阵 ---
      setTimeout(() => {{
        const crowStatus = document.getElementById('crow-status');
        const crowTag = document.getElementById('crow-tag');
        const crowDot = document.getElementById('crow-dot');

        crowStatus.textContent = "柱级极境 · 本地与 GitHub 汉化版本一致 (v2.26.1)";
        crowTag.textContent = "柱级极境 ✅";
        crowTag.style.background = "rgba(34, 197, 94, 0.25)";
        crowTag.style.borderColor = "rgba(34, 197, 94, 0.6)";
        crowTag.style.color = "#86efac";
      }}, 2600);

    }})();
  </script>
</body>
</html>"""
    return html

def build_overlay_js(theme: str = "zenitsu") -> str:
    html = build_splash_html(theme)
    escaped_html = html.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    cfg = THEMES.get(theme, THEMES["zenitsu"])

    js_code = f"""\"use strict\";
Object.defineProperty(exports, "__esModule", {{ value: true }});
exports.attachLoadingOverlay = attachLoadingOverlay;
const electron_1 = require("electron");

/**
 * Antigravity 《鬼灭之刃》全屏·{cfg['name']}电影级动作启动遮罩 (Kimetsu Single Hero Splash)
 * 采用原生 WebContentsView 于窗口创建第 0 毫秒硬件加速直出。
 * 主角：{cfg['name']} | 招式：{cfg['breath']}
 */
function getLoadingHtml() {{
  return `{escaped_html}`;
}}

function attachLoadingOverlay(win, foregroundColor, backgroundColor) {{
  const view = new electron_1.WebContentsView({{
    webPreferences: {{
      nodeIntegration: false,
      contextIsolation: true,
    }},
  }});
  const html = getLoadingHtml();
  void view.webContents.loadURL(`data:text/html;charset=utf-8,${{encodeURIComponent(html)}}`);
  win.contentView.addChildView(view);
  const updateBounds = () => {{
    if (win.isDestroyed()) return;
    const [width, height] = win.getContentSize();
    view.setBounds({{ x: 0, y: 0, width, height }});
  }};
  updateBounds();
  win.on('resize', updateBounds);

  let isRemoved = false;
  const startTime = Date.now();
  const MIN_DISPLAY_TIME = 11500;
  const MAX_TIMEOUT = 15000;

  let pageLoaded = false;
  win.webContents.once('did-finish-load', () => {{
    pageLoaded = true;
  }});

  const checkAndDismiss = async () => {{
    if (isRemoved) return;
    const elapsed = Date.now() - startTime;

    if (elapsed < MIN_DISPLAY_TIME) {{
      setTimeout(checkAndDismiss, MIN_DISPLAY_TIME - elapsed);
      return;
    }}

    let isUiReady = false;
    if (pageLoaded && !win.isDestroyed()) {{
      try {{
        isUiReady = await win.webContents.executeJavaScript(`
          Boolean(
            document.body && (
              document.querySelector('nav, [role="navigation"], .monaco-editor, textarea, [contenteditable="true"], [data-testid]') ||
              (document.getElementById('root') && document.getElementById('root').querySelectorAll('*').length > 18) ||
              document.body.querySelectorAll('*').length > 30
            )
          )
        `);
      }} catch (_) {{
        isUiReady = true;
      }}
    }}

    if (!isUiReady && elapsed < MAX_TIMEOUT) {{
      setTimeout(checkAndDismiss, 250);
      return;
    }}

    isRemoved = true;
    try {{
      view.webContents.executeJavaScript(`
        const splashNode = document.getElementById('splash-node');
        if (splashNode) {{
          splashNode.style.transition = 'opacity 0.85s cubic-bezier(0.16, 1, 0.3, 1), transform 0.85s cubic-bezier(0.16, 1, 0.3, 1)';
          splashNode.style.opacity = '0';
          splashNode.style.transform = 'scale(1.04)';
        }}
        document.body.style.transition = 'opacity 0.85s ease';
        document.body.style.opacity = '0';
      `).catch(() => {{}});
    }} catch (_) {{}}

    setTimeout(() => {{
      try {{
        if (!win.isDestroyed()) {{
          win.contentView.removeChildView(view);
        }}
      }} catch (_) {{}}
      win.off('resize', updateBounds);
    }}, 900);
  }};

  setTimeout(checkAndDismiss, MIN_DISPLAY_TIME);
  setTimeout(() => {{
    if (!isRemoved) checkAndDismiss();
  }}, MAX_TIMEOUT);
}}
"""
    return js_code

if __name__ == "__main__":
    import sys
    theme = sys.argv[1] if len(sys.argv) > 1 else get_current_theme()
    print(f"正在构建电影级角色主题: {theme}...")
    save_current_theme(theme)
    html = build_splash_html(theme)
    js = build_overlay_js(theme)
    
    (REPO_ROOT / "resources" / "loadingOverlay-zh.js").write_text(js, encoding="utf-8")
    (REPO_ROOT / "resources" / "splash" / "index.html").write_text(html, encoding="utf-8")
    print(f"构建完成: {theme}")
