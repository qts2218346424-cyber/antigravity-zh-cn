#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 《鬼灭之刃》全屏人物启动遮罩生成器 (splash_generator.py)
支持生成：
1. tanjiro: 灶门炭治郎 (全屏水之呼吸·生生流转斩击)
2. zenitsu: 我妻善逸 (全屏雷之呼吸·霹雳一闪雷霆爆闪)
3. inosuke: 嘴平伊之助 (全屏兽之呼吸·猪突猛进野猪喷气)
4. nezuko:  灶门祢豆子 (全屏竹篓探头萌动与樱花爆血)
5. all:     鬼杀四象合璧 (四宫格四主角轮巡大赏)
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
    "tanjiro": {
        "id": "tanjiro",
        "name": "灶门炭治郎",
        "breath": "水之呼吸 · 拾之型 生生流转",
        "color": "#06b6d4",
        "accent": "#3b82f6",
        "desc": "全屏水之呼吸生生流转巨浪斩击，浮世绘水沫飞溅与青蓝刀芒"
    },
    "zenitsu": {
        "id": "zenitsu",
        "name": "我妻善逸",
        "breath": "雷之呼吸 · 壱之型 霹雳一闪",
        "color": "#fbbf24",
        "accent": "#f59e0b",
        "desc": "全屏雷之呼吸霹雳一闪，狂暴折线金色雷电撕裂夜空与瞬时高曝光"
    },
    "inosuke": {
        "id": "inosuke",
        "name": "嘴平伊之助",
        "breath": "兽之呼吸 · 伍之牙 狂乱裂斩",
        "color": "#38bdf8",
        "accent": "#94a3b8",
        "desc": "全屏兽之呼吸野猪双孔喷气，双刀交错风刃空气撕裂与野性风暴"
    },
    "nezuko": {
        "id": "nezuko",
        "name": "灶门祢豆子",
        "breath": "血鬼术 · 爆血 守护之羁绊",
        "color": "#f472b6",
        "accent": "#db2777",
        "desc": "全屏竹篓探头娇俏萌动呼吸，粉眸微眨，满屏漫天樱花与粉晶爆血火花"
    },
    "all": {
        "id": "all",
        "name": "鬼杀四象合集",
        "breath": "四象归一 · 全员全集中",
        "color": "#f59e0b",
        "accent": "#ef4444",
        "desc": "经典四宫格舞台，四位主角轮巡高光展示与最终全员奇点共鸣"
    }
}

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
            t = data.get("theme", "tanjiro")
            if t in THEMES:
                return t
        except Exception:
            pass
    return "tanjiro"

def save_current_theme(theme: str):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"theme": theme}, indent=2, ensure_ascii=False), encoding='utf-8')

def build_splash_html(theme: str = "tanjiro") -> str:
    if theme == "all":
        # 导入多角色四宫格生成逻辑
        from build_kimetsu_characters_splash import generate_html_content
        b64_t = get_base64_webp("tanjiro_water")
        b64_n = get_base64_webp("nezuko_basket")
        b64_z = get_base64_webp("zenitsu_thunder")
        b64_i = get_base64_webp("inosuke_beast")
        return generate_html_content(b64_t, b64_n, b64_z, b64_i)

    cfg = THEMES.get(theme, THEMES["tanjiro"])
    b64_img = get_base64_webp(f"{theme}_water" if theme == "tanjiro" else (
        f"{theme}_thunder" if theme == "zenitsu" else (
            f"{theme}_beast" if theme == "inosuke" else f"{theme}_basket"
        )
    ))

    # 根据角色个性化特效代码
    char_id = cfg["id"]
    char_name = cfg["name"]
    char_breath = cfg["breath"]
    theme_color = cfg["color"]
    accent_color = cfg["accent"]

    # 角色专属 Canvas 与动画差异化逻辑
    specific_css = ""
    specific_html = ""
    specific_js = ""

    if char_id == "tanjiro":
        specific_css = f"""
        .char-hero {{
          background-position: center 25%;
          animation: heroBreathe 3.6s ease-in-out infinite;
        }}
        @keyframes heroBreathe {{
          0%, 100% {{ transform: scale(1) translateY(0); }}
          50% {{ transform: scale(1.04) translateY(-6px); }}
        }}
        /* 巨型斜角水刃流光斩击 */
        .water-slash-blade {{
          position: absolute;
          top: -20%;
          left: -30%;
          width: 160%;
          height: 140%;
          background: linear-gradient(135deg, transparent 40%, rgba(6, 182, 212, 0.45) 48%, rgba(255, 255, 255, 0.95) 50%, rgba(59, 130, 246, 0.45) 52%, transparent 60%);
          transform: rotate(32deg) translateY(-100%);
          pointer-events: none;
          z-index: 6;
          animation: waterSlashSlash 3.4s cubic-bezier(0.16, 1, 0.3, 1) infinite;
        }}
        @keyframes waterSlashSlash {{
          0%, 65% {{ transform: rotate(32deg) translateY(-120%); opacity: 0; }}
          70% {{ opacity: 1; }}
          82% {{ transform: rotate(32deg) translateY(120%); opacity: 0.9; }}
          90%, 100% {{ transform: rotate(32deg) translateY(120%); opacity: 0; }}
        }}
        """
        specific_html = """
        <div class="water-slash-blade"></div>
        <canvas id="canvas-hero-effect"></canvas>
        """
        specific_js = """
        // 炭治郎水浪水花喷射引擎
        const canvasE = document.getElementById('canvas-hero-effect');
        const ctxE = canvasE.getContext('2d');
        function resizeE() {
          canvasE.width = window.innerWidth;
          canvasE.height = window.innerHeight;
        }
        resizeE();
        window.addEventListener('resize', resizeE);

        const waterDrops = [];
        for (let i = 0; i < 60; i++) {
          waterDrops.push({
            x: Math.random() * window.innerWidth * 0.8,
            y: window.innerHeight * 0.85 + Math.random() * 80,
            vx: Math.random() * 4.5 + 2.5,
            vy: -Math.random() * 4.2 - 2.0,
            r: Math.random() * 3.5 + 1.2,
            alpha: Math.random() * 0.8 + 0.2
          });
        }
        function renderCharEffect() {
          ctxE.clearRect(0, 0, canvasE.width, canvasE.height);
          for (const d of waterDrops) {
            d.x += d.vx;
            d.y += d.vy;
            d.vy += 0.08; // 重力微下坠
            if (d.x > canvasE.width || d.y > canvasE.height) {
              d.x = Math.random() * canvasE.width * 0.5;
              d.y = canvasE.height * 0.8 + Math.random() * 50;
              d.vy = -Math.random() * 4.5 - 2.5;
            }
            ctxE.beginPath();
            ctxE.arc(d.x, d.y, d.r, 0, Math.PI * 2);
            ctxE.fillStyle = '#e0f2fe';
            ctxE.globalAlpha = d.alpha;
            ctxE.shadowBlur = 8;
            ctxE.shadowColor = '#06b6d4';
            ctxE.fill();
          }
          ctxE.shadowBlur = 0;
          ctxE.globalAlpha = 1;
        }
        """

    elif char_id == "zenitsu":
        specific_css = f"""
        .char-hero {{
          background-position: center 30%;
          animation: zenitsuVibrate 4.2s ease-in-out infinite;
        }}
        @keyframes zenitsuVibrate {{
          0%, 82%, 100% {{ transform: scale(1) translateY(0); }}
          85% {{ transform: scale(1.03) translateY(-3px) translateX(2px); }}
          88% {{ transform: scale(1.02) translateY(-1px) translateX(-2px); }}
          91% {{ transform: scale(1.04) translateY(-4px) translateX(1px); }}
          94% {{ transform: scale(1.01) translateY(0); }}
        }}
        /* 闪电全屏爆闪高光层 */
        .thunder-flash-overlay {{
          position: absolute;
          top: 0; left: 0; width: 100%; height: 100%;
          background: radial-gradient(circle at 45% 60%, rgba(254, 240, 138, 0.45) 10%, rgba(255, 255, 255, 0.85) 40%, rgba(251, 191, 36, 0.2) 70%, transparent 100%);
          pointer-events: none;
          z-index: 7;
          opacity: 0;
          transition: opacity 0.05s ease-out;
        }}
        """
        specific_html = """
        <div class="thunder-flash-overlay" id="flash-overlay"></div>
        <canvas id="canvas-hero-effect"></canvas>
        """
        specific_js = """
        // 善逸全屏折线闪电引擎
        const canvasE = document.getElementById('canvas-hero-effect');
        const ctxE = canvasE.getContext('2d');
        const flashOverlay = document.getElementById('flash-overlay');
        function resizeE() {
          canvasE.width = window.innerWidth;
          canvasE.height = window.innerHeight;
        }
        resizeE();
        window.addEventListener('resize', resizeE);

        let thunderBranches = [];
        let nextThunderTime = Date.now() + 500;

        function createThunder() {
          thunderBranches = [];
          let startX = Math.random() * canvasE.width * 0.7 + canvasE.width * 0.15;
          let startY = 0;
          let curX = startX, curY = startY;
          const mainLine = [{ x: curX, y: curY }];
          while (curY < canvasE.height) {
            curY += Math.random() * 25 + 15;
            curX += (Math.random() - 0.5) * 45;
            mainLine.push({ x: curX, y: curY });
          }
          thunderBranches.push(mainLine);

          // 触发高曝光全屏爆闪
          flashOverlay.style.opacity = '0.7';
          setTimeout(() => { flashOverlay.style.opacity = '0'; }, 80);
        }

        function renderCharEffect() {
          ctxE.clearRect(0, 0, canvasE.width, canvasE.height);
          const now = Date.now();
          if (now > nextThunderTime) {
            createThunder();
            nextThunderTime = now + Math.random() * 1400 + 800;
          }
          for (const line of thunderBranches) {
            if (line.length > 1) {
              ctxE.beginPath();
              ctxE.moveTo(line[0].x, line[0].y);
              for (let i = 1; i < line.length; i++) {
                ctxE.lineTo(line[i].x, line[i].y);
              }
              ctxE.strokeStyle = '#fef08a';
              ctxE.lineWidth = 4;
              ctxE.shadowBlur = 18;
              ctxE.shadowColor = '#fbbf24';
              ctxE.stroke();
              // 内层纯白烈焰光芒
              ctxE.strokeStyle = '#ffffff';
              ctxE.lineWidth = 1.8;
              ctxE.stroke();
              ctxE.shadowBlur = 0;
            }
          }
        }
        """

    elif char_id == "inosuke":
        specific_css = f"""
        .char-hero {{
          background-position: center 30%;
          animation: inosukeRage 2.8s ease-in-out infinite;
        }}
        @keyframes inosukeRage {{
          0%, 100% {{ transform: scale(1) translateY(0); }}
          25% {{ transform: scale(1.035) translateY(-4px) rotate(1deg); }}
          75% {{ transform: scale(1.025) translateY(2px) rotate(-1deg); }}
        }}
        /* 野猪鼻孔全屏双侧狂暴喷气 (Gigantic Snort Effect) */
        .snort-steam-left, .snort-steam-right {{
          position: absolute;
          top: 48%;
          width: 140px;
          height: 48px;
          background: radial-gradient(ellipse at 15% 50%, rgba(255, 255, 255, 0.85) 15%, rgba(224, 242, 254, 0.35) 60%, transparent 100%);
          border-radius: 50%;
          pointer-events: none;
          z-index: 6;
          opacity: 0;
          animation: snortBurst 2.8s infinite ease-out;
        }}
        .snort-steam-left {{
          left: 41%;
          transform-origin: left center;
          transform: rotate(155deg) scale(0.6);
        }}
        .snort-steam-right {{
          left: 54%;
          transform-origin: left center;
          transform: rotate(25deg) scale(0.6);
        }}
        @keyframes snortBurst {{
          0%, 25%, 100% {{ opacity: 0; transform: scale(0.3); }}
          35% {{ opacity: 0.95; transform: scale(1.3) translateY(4px); }}
          55% {{ opacity: 0; transform: scale(2.4) translateY(18px); }}
        }}
        /* 双刀空气撕裂风刃 */
        .cross-blade-cut {{
          position: absolute;
          top: 30%; left: 15%; width: 70%; height: 40%;
          border-top: 3px solid rgba(56, 189, 248, 0.8);
          border-bottom: 3px solid rgba(255, 255, 255, 0.9);
          transform: rotate(-18deg) scaleX(0);
          filter: drop-shadow(0 0 12px #38bdf8);
          pointer-events: none;
          z-index: 6;
          animation: bladeCut 2.8s ease-in-out infinite 0.9s;
        }}
        @keyframes bladeCut {{
          0%, 40% {{ transform: rotate(-18deg) scaleX(0); opacity: 0; }}
          50% {{ transform: rotate(-18deg) scaleX(1.2); opacity: 1; }}
          65%, 100% {{ transform: rotate(-18deg) scaleX(1.3); opacity: 0; }}
        }}
        """
        specific_html = """
        <div class="snort-steam-left"></div>
        <div class="snort-steam-right"></div>
        <div class="cross-blade-cut"></div>
        <canvas id="canvas-hero-effect"></canvas>
        """
        specific_js = """
        // 伊之助野性撕裂粒子引擎
        const canvasE = document.getElementById('canvas-hero-effect');
        const ctxE = canvasE.getContext('2d');
        function resizeE() {
          canvasE.width = window.innerWidth;
          canvasE.height = window.innerHeight;
        }
        resizeE();
        window.addEventListener('resize', resizeE);

        const windSlices = [];
        for (let i = 0; i < 36; i++) {
          windSlices.push({
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            len: Math.random() * 60 + 30,
            speed: Math.random() * 8 + 5,
            angle: Math.random() * 0.4 - 0.2,
            alpha: Math.random() * 0.6 + 0.2
          });
        }
        function renderCharEffect() {
          ctxE.clearRect(0, 0, canvasE.width, canvasE.height);
          for (const w of windSlices) {
            w.x += w.speed;
            w.y += w.speed * w.angle;
            if (w.x > canvasE.width) {
              w.x = -80;
              w.y = Math.random() * canvasE.height;
            }
            ctxE.beginPath();
            ctxE.moveTo(w.x, w.y);
            ctxE.lineTo(w.x + w.len, w.y + w.len * w.angle);
            ctxE.strokeStyle = '#bae6fd';
            ctxE.lineWidth = 1.5;
            ctxE.globalAlpha = w.alpha;
            ctxE.shadowBlur = 6;
            ctxE.shadowColor = '#38bdf8';
            ctxE.stroke();
          }
          ctxE.shadowBlur = 0;
          ctxE.globalAlpha = 1;
        }
        """

    elif char_id == "nezuko":
        specific_css = f"""
        .char-hero {{
          background-position: center 35%;
          animation: nezukoSway 4.0s ease-in-out infinite;
          transform-origin: bottom center;
        }}
        @keyframes nezukoSway {{
          0%, 100% {{ transform: scale(1) translateY(0) rotate(0deg); }}
          25% {{ transform: scale(1.03) translateY(-6px) rotate(-1.5deg); }}
          50% {{ transform: scale(1.02) translateY(-2px) rotate(1deg); }}
          75% {{ transform: scale(1.035) translateY(-8px) rotate(2deg); }}
        }}
        /* 唯美樱花与血鬼术火花光晕暗角 */
        .nezuko-vignette {{
          position: absolute;
          top: 0; left: 0; width: 100%; height: 100%;
          background: radial-gradient(circle at 50% 50%, transparent 40%, rgba(219, 39, 119, 0.18) 75%, rgba(6, 7, 11, 0.85) 100%);
          pointer-events: none;
          z-index: 5;
        }}
        """
        specific_html = """
        <div class="nezuko-vignette"></div>
        <canvas id="canvas-hero-effect"></canvas>
        """
        specific_js = """
        // 祢豆子樱花落樱与血鬼术爆血粉晶粒子
        const canvasE = document.getElementById('canvas-hero-effect');
        const ctxE = canvasE.getContext('2d');
        function resizeE() {
          canvasE.width = window.innerWidth;
          canvasE.height = window.innerHeight;
        }
        resizeE();
        window.addEventListener('resize', resizeE);

        const petals = [];
        for (let i = 0; i < 45; i++) {
          petals.push({
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            vx: Math.random() * 1.6 - 0.8,
            vy: Math.random() * 2.0 + 0.8,
            size: Math.random() * 4 + 2.5,
            rot: Math.random() * Math.PI,
            vrot: (Math.random() - 0.5) * 0.04,
            color: Math.random() > 0.4 ? '#f472b6' : '#fda4af',
            isSpark: Math.random() > 0.65
          });
        }
        function renderCharEffect() {
          ctxE.clearRect(0, 0, canvasE.width, canvasE.height);
          for (const p of petals) {
            p.x += p.vx;
            p.y += (p.isSpark ? -p.vy * 1.5 : p.vy);
            p.rot += p.vrot;
            if (p.isSpark && p.y < 0) {
              p.y = canvasE.height + 10;
              p.x = Math.random() * canvasE.width;
            } else if (!p.isSpark && p.y > canvasE.height) {
              p.y = -10;
              p.x = Math.random() * canvasE.width;
            }
            ctxE.save();
            ctxE.translate(p.x, p.y);
            ctxE.rotate(p.rot);
            ctxE.beginPath();
            if (p.isSpark) {
              ctxE.arc(0, 0, p.size * 0.6, 0, Math.PI * 2);
              ctxE.fillStyle = '#f43f5e';
              ctxE.shadowBlur = 10;
              ctxE.shadowColor = '#f43f5e';
            } else {
              ctxE.ellipse(0, 0, p.size, p.size * 1.7, 0, 0, Math.PI * 2);
              ctxE.fillStyle = p.color;
            }
            ctxE.globalAlpha = 0.75;
            ctxE.fill();
            ctxE.restore();
          }
          ctxE.shadowBlur = 0;
          ctxE.globalAlpha = 1;
        }
        """

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Antigravity 《鬼灭之刃》全屏·{char_name}启动动效</title>
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

    /* 炭治郎绿黑市松纹暗底 */
    .ichimatsu-bg {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background-image: 
        linear-gradient(45deg, rgba(6, 78, 59, 0.08) 25%, transparent 25%),
        linear-gradient(-45deg, rgba(6, 78, 59, 0.08) 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, rgba(6, 78, 59, 0.08) 75%),
        linear-gradient(-45deg, transparent 75%, rgba(6, 78, 59, 0.08) 75%);
      background-size: 40px 40px;
      background-position: 0 0, 0 20px, 20px -20px, -20px 0px;
      z-index: 1;
      pointer-events: none;
      opacity: 0.65;
    }}

    /* 满屏主角全景高燃视觉舞台 (Full-screen Hero Canvas) */
    .hero-container {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      z-index: 2;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .char-hero {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background-image: url('data:image/webp;base64,{b64_img}');
      background-size: cover;
      filter: brightness(0.96) contrast(1.08);
      transform-origin: center center;
    }}

    /* 浮世绘全景水墨渐变遮罩 (四周与底栏保护) */
    .hero-vignette {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: linear-gradient(180deg, rgba(6, 7, 11, 0.65) 0%, rgba(6, 7, 11, 0.15) 30%, rgba(6, 7, 11, 0.25) 60%, rgba(6, 7, 11, 0.95) 100%),
                  radial-gradient(circle at 50% 50%, transparent 40%, rgba(6, 7, 11, 0.75) 90%, #06070b 100%);
      z-index: 4;
      pointer-events: none;
    }}

    {specific_css}

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
      background: rgba(15, 23, 42, 0.65);
      border: 1px solid var(--char-color);
      color: #f8fafc;
      font-weight: 700;
      letter-spacing: 1.5px;
      box-shadow: 0 0 14px var(--char-color);
      display: flex;
      align-items: center;
      gap: 6px;
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
      font-size: 42px;
      font-weight: 900;
      letter-spacing: 4px;
      color: #f8fafc;
      text-shadow: 0 0 25px var(--char-color), 0 4px 12px rgba(0, 0, 0, 0.8);
      font-family: "Kaiti SC", "STKaiti", "KaiTi", serif;
      line-height: 1.1;
    }}

    .hero-breath-kanji {{
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 2px;
      color: var(--char-color);
      text-shadow: 0 0 14px var(--char-color);
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
      border: 1px solid rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6);
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
      text-shadow: 0 0 12px var(--char-color);
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
      box-shadow: 0 0 14px var(--char-color);
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
  <div class="ichimatsu-bg"></div>

  <!-- 全屏主角动作舞台 -->
  <div class="hero-container">
    <div class="char-hero"></div>
    <div class="hero-vignette"></div>
    {specific_html}
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
      <span>鬼杀队 · {char_name}</span>
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
      {specific_js}

      // --- 角色专属效果主渲染循环 ---
      function mainRender() {{
        if (typeof renderCharEffect === 'function') {{
          renderCharEffect();
        }}
        requestAnimationFrame(mainRender);
      }}
      requestAnimationFrame(mainRender);

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

def build_overlay_js(theme: str = "tanjiro") -> str:
    html = build_splash_html(theme)
    escaped_html = html.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    cfg = THEMES.get(theme, THEMES["tanjiro"])

    js_code = f"""\"use strict\";
Object.defineProperty(exports, "__esModule", {{ value: true }});
exports.attachLoadingOverlay = attachLoadingOverlay;
const electron_1 = require("electron");

/**
 * Antigravity 《鬼灭之刃》全屏·{cfg['name']}角色启动遮罩 (Kimetsu Single Hero Splash)
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
    print(f"正在构建角色主题: {theme}...")
    save_current_theme(theme)
    html = build_splash_html(theme)
    js = build_overlay_js(theme)
    
    (REPO_ROOT / "resources" / "loadingOverlay-zh.js").write_text(js, encoding="utf-8")
    (REPO_ROOT / "resources" / "splash" / "index.html").write_text(html, encoding="utf-8")
    print(f"构建完成: {theme}")
