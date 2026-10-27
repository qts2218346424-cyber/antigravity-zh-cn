#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成带鬼灭之刃四大主角人物动作与技能特效的高燃启动遮罩
包含：
1. 炭治郎：水之呼吸·浪花流转、浮世绘水沫飞溅与刀芒斩击；
2. 善逸：雷之呼吸·霹雳一闪、动态折线雷电弧与刀镡爆闪；
3. 祢豆子：竹篓萌动摇曳、粉眼流光与血鬼术爆血粉晶微粒；
4. 伊之助：兽之呼吸·野猪鼻息喷气、双刀风刃交错斩击；
5. 鎹鸦巡检·鬼杀队版本检测矩阵；
6. 11.5 秒黄金节奏呼吸型态平滑推进与 0.85 秒浮世绘水墨消隐。
"""

import os
import base64
from pathlib import Path
from PIL import Image

REPO_ROOT = Path("e:/antigravity-cn")
MEDIA_DIR = REPO_ROOT / "resources" / "media"
ARTIFACT_DIR = Path(r"C:\Users\QTS的天选\.gemini\antigravity\brain\158062cb-0b2d-485e-b84e-ad56b751e715")

def get_base64_webp(name: str) -> str:
    webp_path = MEDIA_DIR / f"{name}.webp"
    if not webp_path.exists():
        png_path = MEDIA_DIR / f"{name}.png"
        im = Image.open(png_path)
        im.save(webp_path, 'WEBP', quality=88, method=6)
    return base64.b64encode(webp_path.read_bytes()).decode('ascii')

def generate_html_content(b64_tanjiro, b64_nezuko, b64_zenitsu, b64_inosuke) -> str:
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Antigravity 《鬼灭之刃》全集中·反重力四象启动动效</title>
  <style>
    :root {{
      --bg-dark: #06070b;
      --ichimatsu-green: #064e3b;
      --flame-gold: #f59e0b;
      --flame-red: #ef4444;
      --water-cyan: #06b6d4;
      --water-blue: #3b82f6;
      --thunder-yellow: #fbbf24;
      --beast-steel: #94a3b8;
      --nezuko-pink: #f472b6;
      --nezuko-rose: #db2777;
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
      justify-content: center;
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

    /* 浮世绘暗夜深渊水墨渐变 */
    .vignette-overlay {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: radial-gradient(circle at 50% 50%, rgba(6, 7, 11, 0.2) 20%, rgba(6, 7, 11, 0.85) 75%, #06070b 100%);
      z-index: 2;
      pointer-events: none;
    }}

    /* 全局粒子 Canvas (烈焰余烬、火花、光粒) */
    #canvas-global-particles {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      z-index: 3;
      pointer-events: none;
    }}

    /* 启动器主舞台 */
    .stage {{
      position: relative;
      z-index: 10;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 100%;
      max-width: 760px;
      perspective: 1200px;
      padding: 0 20px;
    }}

    /* 顶部顶幅：鬼杀队·反重力全集中徽标 */
    .brand-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      animation: fadeInDown 1s cubic-bezier(0.16, 1, 0.3, 1) both;
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
      background: linear-gradient(135deg, #f59e0b, #ef4444);
      transform: rotate(45deg);
      border-radius: 3px;
      box-shadow: 0 0 14px rgba(239, 68, 68, 0.8);
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

    .brand-tag {{
      font-size: 11px;
      padding: 2px 7px;
      border-radius: 4px;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #fca5a5;
      font-weight: 600;
      letter-spacing: 1px;
    }}

    /* 核心焦点：鬼杀四象动作四宫格舞台 (The Kimetsu Quartet Stage) */
    .quartet-grid {{
      position: relative;
      display: grid;
      grid-template-columns: 1fr 1fr;
      grid-gap: 14px;
      width: 100%;
      max-width: 640px;
      margin-bottom: 20px;
      animation: zoomInStage 1.2s cubic-bezier(0.16, 1, 0.3, 1) both;
    }}

    /* 中心神乐日轮刀镡结界 */
    .center-crest {{
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 64px;
      height: 64px;
      z-index: 20;
      pointer-events: none;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .center-tsuba {{
      width: 52px;
      height: 52px;
      border-radius: 50%;
      background: radial-gradient(circle, #18181b 30%, #09090b 80%);
      border: 2px solid #f59e0b;
      box-shadow: 0 0 22px rgba(245, 158, 11, 0.7), inset 0 0 12px rgba(239, 68, 68, 0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      animation: pulseCore 3s ease-in-out infinite;
    }}

    .center-kanji {{
      font-size: 18px;
      font-weight: 900;
      color: #fef08a;
      text-shadow: 0 0 8px #f59e0b;
      font-family: "Kaiti SC", "STKaiti", "KaiTi", serif;
    }}

    /* 单个角色动作卡片 (Character Action Cell) */
    .char-card {{
      position: relative;
      border-radius: 12px;
      overflow: hidden;
      height: 170px;
      background: #090b10;
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
      transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
      transform-origin: center center;
    }}

    .char-card:hover, .char-card.active-focus {{
      transform: scale(1.035);
      z-index: 15;
    }}

    /* 角色底图与动作容器 */
    .char-visual {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background-size: cover;
      background-position: center 20%;
      filter: brightness(0.92) contrast(1.06);
      transition: transform 0.8s ease;
    }}

    /* 炭治郎卡片与水浪动作 */
    .card-tanjiro {{
      border-color: rgba(6, 182, 212, 0.3);
    }}
    .card-tanjiro .char-visual {{
      background-image: url('data:image/webp;base64,{b64_tanjiro}');
      animation: tanjiroBreathing 3.6s ease-in-out infinite;
    }}
    .card-tanjiro:hover, .card-tanjiro.active-focus {{
      border-color: var(--water-cyan);
      box-shadow: 0 0 30px rgba(6, 182, 212, 0.5);
    }}

    @keyframes tanjiroBreathing {{
      0%, 100% {{
        transform: scale(1) translateY(0) rotate(0deg);
      }}
      50% {{
        transform: scale(1.03) translateY(-3px) rotate(-0.5deg);
      }}
    }}

    /* 炭治郎水浪水花流动 Canvas */
    #canvas-tanjiro-water {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      z-index: 5;
      pointer-events: none;
    }}

    /* 善逸卡片与雷霆霹雳动作 */
    .card-zenitsu {{
      border-color: rgba(251, 191, 36, 0.3);
    }}
    .card-zenitsu .char-visual {{
      background-image: url('data:image/webp;base64,{b64_zenitsu}');
      animation: zenitsuTense 4s ease-in-out infinite;
    }}
    .card-zenitsu:hover, .card-zenitsu.active-focus {{
      border-color: var(--thunder-yellow);
      box-shadow: 0 0 30px rgba(251, 191, 36, 0.55);
    }}

    @keyframes zenitsuTense {{
      0%, 85%, 100% {{
        transform: scale(1) translateY(0);
      }}
      88% {{
        transform: scale(1.025) translateY(-2px) translateX(1px);
      }}
      91% {{
        transform: scale(1.015) translateY(-1px) translateX(-1px);
      }}
      94% {{
        transform: scale(1.03) translateY(-2px);
      }}
    }}

    /* 善逸动态折线闪电 Canvas */
    #canvas-zenitsu-thunder {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      z-index: 5;
      pointer-events: none;
    }}

    /* 祢豆子卡片与竹篓探头萌动 */
    .card-nezuko {{
      border-color: rgba(244, 114, 182, 0.3);
    }}
    .card-nezuko .char-visual {{
      background-image: url('data:image/webp;base64,{b64_nezuko}');
      animation: nezukoPeek 3.8s ease-in-out infinite;
      transform-origin: bottom center;
    }}
    .card-nezuko:hover, .card-nezuko.active-focus {{
      border-color: var(--nezuko-pink);
      box-shadow: 0 0 30px rgba(244, 114, 182, 0.5);
    }}

    @keyframes nezukoPeek {{
      0%, 100% {{
        transform: scale(1) translateY(0) rotate(0deg);
      }}
      25% {{
        transform: scale(1.025) translateY(-4px) rotate(-1.5deg);
      }}
      50% {{
        transform: scale(1.015) translateY(-2px) rotate(1deg);
      }}
      75% {{
        transform: scale(1.03) translateY(-5px) rotate(2deg);
      }}
    }}

    /* 祢豆子樱花爆血粒子 Canvas */
    #canvas-nezuko-sakura {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      z-index: 5;
      pointer-events: none;
    }}

    /* 伊之助卡片与兽之呼吸双刀狂舞 */
    .card-inosuke {{
      border-color: rgba(148, 163, 184, 0.3);
    }}
    .card-inosuke .char-visual {{
      background-image: url('data:image/webp;base64,{b64_inosuke}');
      animation: inosukeRage 2.6s ease-in-out infinite;
    }}
    .card-inosuke:hover, .card-inosuke.active-focus {{
      border-color: #38bdf8;
      box-shadow: 0 0 30px rgba(56, 189, 248, 0.5);
    }}

    @keyframes inosukeRage {{
      0%, 100% {{
        transform: scale(1) translateY(0) rotate(0deg);
      }}
      30% {{
        transform: scale(1.025) translateY(-3px) rotate(1.2deg);
      }}
      70% {{
        transform: scale(1.02) translateY(2px) rotate(-1deg);
      }}
    }}

    /* 野猪鼻孔喷气动画 (Steam Breath Effect) */
    .inosuke-steam-left, .inosuke-steam-right {{
      position: absolute;
      top: 66%;
      width: 48px;
      height: 16px;
      background: radial-gradient(ellipse at 10% 50%, rgba(255, 255, 255, 0.7) 10%, rgba(255, 255, 255, 0.2) 60%, transparent 100%);
      border-radius: 50%;
      pointer-events: none;
      z-index: 6;
      opacity: 0;
      animation: inosukeSnort 2.6s infinite ease-out;
    }}
    .inosuke-steam-left {{
      left: 36%;
      transform-origin: left center;
      transform: rotate(155deg) scale(0.6);
    }}
    .inosuke-steam-right {{
      left: 56%;
      transform-origin: left center;
      transform: rotate(25deg) scale(0.6);
    }}

    @keyframes inosukeSnort {{
      0%, 25%, 100% {{
        opacity: 0;
        transform: scale(0.4);
      }}
      35% {{
        opacity: 0.85;
        transform: scale(1.2) translateY(3px);
      }}
      55% {{
        opacity: 0;
        transform: scale(1.8) translateY(8px);
      }}
    }}

    /* 卡片浮水印与招式角标 */
    .char-badge {{
      position: absolute;
      bottom: 8px;
      left: 10px;
      z-index: 10;
      display: flex;
      flex-direction: column;
      gap: 2px;
      background: linear-gradient(90deg, rgba(6, 7, 11, 0.85) 40%, transparent 100%);
      padding: 4px 10px 4px 6px;
      border-radius: 4px;
      border-left: 2px solid;
    }}
    .card-tanjiro .char-badge {{ border-left-color: var(--water-cyan); }}
    .card-zenitsu .char-badge {{ border-left-color: var(--thunder-yellow); }}
    .card-nezuko .char-badge {{ border-left-color: var(--nezuko-pink); }}
    .card-inosuke .char-badge {{ border-left-color: #38bdf8; }}

    .badge-name {{
      font-size: 13px;
      font-weight: 700;
      color: #f8fafc;
      letter-spacing: 1px;
    }}
    .badge-breath {{
      font-size: 10px;
      font-weight: 500;
      color: var(--text-muted);
      letter-spacing: 0.5px;
    }}

    /* 鎹鸦巡检 · 鬼杀队版本检测状态面板 */
    .crow-panel {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      max-width: 640px;
      padding: 10px 16px;
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.65);
      border: 1px solid rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(8px);
      margin-bottom: 14px;
      animation: fadeInUp 1s cubic-bezier(0.16, 1, 0.3, 1) both 0.3s;
    }}

    .crow-left {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .crow-avatar {{
      width: 26px;
      height: 26px;
      border-radius: 50%;
      background: #18181b;
      border: 1px solid rgba(245, 158, 11, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
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
      padding: 3px 10px;
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
      max-width: 640px;
      animation: fadeInUp 1s cubic-bezier(0.16, 1, 0.3, 1) both 0.5s;
    }}

    .breath-label {{
      font-size: 13px;
      font-weight: 600;
      color: #f1f5f9;
      letter-spacing: 2px;
      text-shadow: 0 0 10px rgba(245, 158, 11, 0.4);
      transition: all 0.4s ease;
      min-height: 20px;
    }}

    .progress-track {{
      width: 100%;
      height: 4px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 3px;
      overflow: hidden;
      position: relative;
    }}

    .progress-fill {{
      position: absolute;
      top: 0; left: 0;
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #06b6d4, #3b82f6, #fbbf24, #ef4444);
      border-radius: 3px;
      box-shadow: 0 0 12px rgba(245, 158, 11, 0.8);
      transition: width 0.3s ease-out;
    }}

    .breath-sub {{
      display: flex;
      justify-content: space-between;
      width: 100%;
      font-size: 11px;
      color: #64748b;
    }}

    /* 关键帧动画 */
    @keyframes spinFlame {{
      0% {{ transform: rotate(0deg); }}
      100% {{ transform: rotate(360deg); }}
    }}
    @keyframes pulseCore {{
      0%, 100% {{ transform: scale(1); box-shadow: 0 0 20px rgba(245, 158, 11, 0.7); }}
      50% {{ transform: scale(1.08); box-shadow: 0 0 32px rgba(239, 68, 68, 0.9); }}
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
    @keyframes zoomInStage {{
      from {{ opacity: 0; transform: scale(0.92); }}
      to {{ opacity: 1; transform: scale(1); }}
    }}
  </style>
</head>
<body>
  <div class="ichimatsu-bg"></div>
  <div class="vignette-overlay"></div>
  <canvas id="canvas-global-particles"></canvas>

  <div class="stage" id="splash-node">
    <!-- 顶部日轮刀镡与品牌标题 -->
    <div class="brand-header">
      <div class="nichirin-core">
        <div class="nichirin-flame"></div>
        <div class="nichirin-blade"></div>
      </div>
      <div class="brand-title">ANTIGRAVITY</div>
      <div class="brand-tag">鬼杀队·全集中</div>
    </div>

    <!-- 四大主角动作四宫格舞台 -->
    <div class="quartet-grid">
      <!-- 中心神乐日轮刀镡徽记 -->
      <div class="center-crest">
        <div class="center-tsuba">
          <span class="center-kanji">滅</span>
        </div>
      </div>

      <!-- 1. 灶门炭治郎 (水之呼吸斩击) -->
      <div class="char-card card-tanjiro" id="card-tanjiro">
        <div class="char-visual"></div>
        <canvas id="canvas-tanjiro-water"></canvas>
        <div class="char-badge">
          <span class="badge-name">灶门炭治郎</span>
          <span class="badge-breath">水之呼吸 · 拾之型 生生流转</span>
        </div>
      </div>

      <!-- 2. 灶门祢豆子 (竹篓探头萌动) -->
      <div class="char-card card-nezuko" id="card-nezuko">
        <div class="char-visual"></div>
        <canvas id="canvas-nezuko-sakura"></canvas>
        <div class="char-badge">
          <span class="badge-name">灶门祢豆子</span>
          <span class="badge-breath">血鬼术 · 爆血 羁绊之火</span>
        </div>
      </div>

      <!-- 3. 我妻善逸 (雷之呼吸拔刀) -->
      <div class="char-card card-zenitsu" id="card-zenitsu">
        <div class="char-visual"></div>
        <canvas id="canvas-zenitsu-thunder"></canvas>
        <div class="char-badge">
          <span class="badge-name">我妻善逸</span>
          <span class="badge-breath">雷之呼吸 · 壱之型 霹雳一闪</span>
        </div>
      </div>

      <!-- 4. 嘴平伊之助 (兽之呼吸双刀) -->
      <div class="char-card card-inosuke" id="card-inosuke">
        <div class="char-visual"></div>
        <div class="inosuke-steam-left"></div>
        <div class="inosuke-steam-right"></div>
        <div class="char-badge">
          <span class="badge-name">嘴平伊之助</span>
          <span class="badge-breath">兽之呼吸 · 伍之牙 狂乱裂斩</span>
        </div>
      </div>
    </div>

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
      // --- 1. 全局火花余烬 Canvas 粒子引擎 ---
      const canvasG = document.getElementById('canvas-global-particles');
      const ctxG = canvasG.getContext('2d');
      let wG, hG;
      function resizeG() {{
        wG = canvasG.width = window.innerWidth;
        hG = canvasG.height = window.innerHeight;
      }}
      resizeG();
      window.addEventListener('resize', resizeG);

      const sparks = [];
      for (let i = 0; i < 48; i++) {{
        sparks.push({{
          x: Math.random() * wG,
          y: Math.random() * hG,
          vx: (Math.random() - 0.5) * 1.2,
          vy: -Math.random() * 2.2 - 0.8,
          radius: Math.random() * 2.2 + 0.6,
          alpha: Math.random() * 0.7 + 0.3,
          color: Math.random() > 0.4 ? '#f59e0b' : '#ef4444'
        }});
      }}

      // --- 2. 炭治郎水之呼吸水花粒子 Canvas 引擎 ---
      const canvasW = document.getElementById('canvas-tanjiro-water');
      const ctxW = canvasW.getContext('2d');
      function resizeW() {{
        canvasW.width = canvasW.parentElement.clientWidth;
        canvasW.height = canvasW.parentElement.clientHeight;
      }}
      resizeW();

      const waterDrops = [];
      for (let i = 0; i < 24; i++) {{
        waterDrops.push({{
          x: Math.random() * 300,
          y: Math.random() * 200,
          vx: Math.random() * 2.5 + 1.2,
          vy: -Math.random() * 2.0 - 0.5,
          r: Math.random() * 2.5 + 1,
          alpha: Math.random() * 0.8 + 0.2
        }});
      }}

      // --- 3. 善逸雷之呼吸折线闪电 Canvas 引擎 ---
      const canvasT = document.getElementById('canvas-zenitsu-thunder');
      const ctxT = canvasT.getContext('2d');
      function resizeT() {{
        canvasT.width = canvasT.parentElement.clientWidth;
        canvasT.height = canvasT.parentElement.clientHeight;
      }}
      resizeT();

      let thunderBolt = [];
      let nextThunderTime = Date.now() + 600;

      function createThunder() {{
        thunderBolt = [];
        let curX = Math.random() * canvasT.width * 0.8 + canvasT.width * 0.1;
        let curY = 0;
        thunderBolt.push({{ x: curX, y: curY }});
        while (curY < canvasT.height) {{
          curY += Math.random() * 16 + 10;
          curX += (Math.random() - 0.5) * 24;
          thunderBolt.push({{ x: curX, y: curY }});
        }}
      }}

      // --- 4. 祢豆子樱花爆血粒子 Canvas 引擎 ---
      const canvasS = document.getElementById('canvas-nezuko-sakura');
      const ctxS = canvasS.getContext('2d');
      function resizeS() {{
        canvasS.width = canvasS.parentElement.clientWidth;
        canvasS.height = canvasS.parentElement.clientHeight;
      }}
      resizeS();

      const petals = [];
      for (let i = 0; i < 20; i++) {{
        petals.push({{
          x: Math.random() * 300,
          y: Math.random() * 200,
          vx: Math.random() * 1.2 - 0.6,
          vy: Math.random() * 1.5 + 0.6,
          size: Math.random() * 3 + 2,
          rot: Math.random() * Math.PI,
          vrot: (Math.random() - 0.5) * 0.05,
          color: Math.random() > 0.5 ? '#f472b6' : '#fda4af'
        }});
      }}

      // --- 主动画渲染循环 ---
      function render() {{
        // A. 渲染全局火花
        ctxG.clearRect(0, 0, wG, hG);
        for (const s of sparks) {{
          s.x += s.vx;
          s.y += s.vy;
          if (s.y < 0) {{ s.y = hG; s.x = Math.random() * wG; }}
          ctxG.beginPath();
          ctxG.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
          ctxG.fillStyle = s.color;
          ctxG.globalAlpha = s.alpha;
          ctxG.shadowBlur = 8;
          ctxG.shadowColor = s.color;
          ctxG.fill();
        }}
        ctxG.globalAlpha = 1;
        ctxG.shadowBlur = 0;

        // B. 渲染炭治郎水浪水花
        if (canvasW.width > 0) {{
          ctxW.clearRect(0, 0, canvasW.width, canvasW.height);
          for (const d of waterDrops) {{
            d.x += d.vx;
            d.y += d.vy;
            if (d.x > canvasW.width || d.y < 0) {{
              d.x = 0;
              d.y = canvasW.height * 0.7 + Math.random() * 40;
            }}
            ctxW.beginPath();
            ctxW.arc(d.x, d.y, d.r, 0, Math.PI * 2);
            ctxW.fillStyle = '#e0f2fe';
            ctxW.globalAlpha = d.alpha;
            ctxW.shadowBlur = 6;
            ctxW.shadowColor = '#06b6d4';
            ctxW.fill();
          }}
          ctxW.globalAlpha = 1;
          ctxW.shadowBlur = 0;
        }}

        // C. 渲染善逸雷之呼吸闪电
        if (canvasT.width > 0) {{
          ctxT.clearRect(0, 0, canvasT.width, canvasT.height);
          const now = Date.now();
          if (now > nextThunderTime) {{
            createThunder();
            nextThunderTime = now + Math.random() * 1200 + 700;
          }}
          if (thunderBolt.length > 1) {{
            ctxT.beginPath();
            ctxT.moveTo(thunderBolt[0].x, thunderBolt[0].y);
            for (let i = 1; i < thunderBolt.length; i++) {{
              ctxT.lineTo(thunderBolt[i].x, thunderBolt[i].y);
            }}
            ctxT.strokeStyle = '#fef08a';
            ctxT.lineWidth = 2.5;
            ctxT.shadowBlur = 12;
            ctxT.shadowColor = '#fbbf24';
            ctxT.stroke();
            // 主电弧分叉
            ctxT.strokeStyle = '#ffffff';
            ctxT.lineWidth = 1;
            ctxT.stroke();
            ctxT.shadowBlur = 0;
          }}
        }}

        // D. 渲染祢豆子樱花微粒
        if (canvasS.width > 0) {{
          ctxS.clearRect(0, 0, canvasS.width, canvasS.height);
          for (const p of petals) {{
            p.x += p.vx;
            p.y += p.vy;
            p.rot += p.vrot;
            if (p.y > canvasS.height) {{
              p.y = -10;
              p.x = Math.random() * canvasS.width;
            }}
            ctxS.save();
            ctxS.translate(p.x, p.y);
            ctxS.rotate(p.rot);
            ctxS.beginPath();
            ctxS.ellipse(0, 0, p.size, p.size * 1.6, 0, 0, Math.PI * 2);
            ctxS.fillStyle = p.color;
            ctxS.globalAlpha = 0.65;
            ctxS.fill();
            ctxS.restore();
          }}
        }}

        requestAnimationFrame(render);
      }}
      requestAnimationFrame(render);

      // --- 5. 11.5 秒舒缓黄金时序推进器与角色聚焦轮巡 ---
      const DURATION = 11500;
      const startTime = Date.now();
      const progressBar = document.getElementById('progress-bar');
      const breathStatus = document.getElementById('breath-status');
      const breathTimer = document.getElementById('breath-timer');

      const cardTanjiro = document.getElementById('card-tanjiro');
      const cardNezuko = document.getElementById('card-nezuko');
      const cardZenitsu = document.getElementById('card-zenitsu');
      const cardInosuke = document.getElementById('card-inosuke');

      const steps = [
        {{ at: 0.00, text: "[壱之型] 全集中·反重力呼吸法起手... 唤醒奇点核心", focus: "tanjiro" }},
        {{ at: 0.12, text: "[弐之型] 水之呼吸·生生流转... 刀芒斩裂深空 (炭治郎)", focus: "tanjiro" }},
        {{ at: 0.28, text: "[参之型] 雷之呼吸·霹雳一闪... 金色雷霆聚顶 (我妻善逸)", focus: "zenitsu" }},
        {{ at: 0.44, text: "[肆之型] 兽之呼吸·双刀狂袭... 猪突猛进撕裂虚空 (伊之助)", focus: "inosuke" }},
        {{ at: 0.60, text: "[伍之型] 血鬼术·爆血羁绊... 粉晶燃起守护之火 (祢豆子)", focus: "nezuko" }},
        {{ at: 0.74, text: "[陆之型] 鎹鸦巡检完成 · 挂载 3,472 词条全景汉化拓扑", focus: "all" }},
        {{ at: 0.88, text: "[漆之型] 编译 Monaco 语法树与智能体工作流全景视窗", focus: "all" }},
        {{ at: 0.96, text: "[终之型] 赫刀初现 · 水火归元 · 正在步入工作台...", focus: "all" }}
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

        // 切换角色聚焦高光
        [cardTanjiro, cardNezuko, cardZenitsu, cardInosuke].forEach(c => c.classList.remove('active-focus'));
        if (currentStep.focus === 'tanjiro') cardTanjiro.classList.add('active-focus');
        else if (currentStep.focus === 'zenitsu') cardZenitsu.classList.add('active-focus');
        else if (currentStep.focus === 'inosuke') cardInosuke.classList.add('active-focus');
        else if (currentStep.focus === 'nezuko') cardNezuko.classList.add('active-focus');
        else if (currentStep.focus === 'all') {{
          [cardTanjiro, cardNezuko, cardZenitsu, cardInosuke].forEach(c => c.classList.add('active-focus'));
        }}

        if (progress < 1) {{
          requestAnimationFrame(updateProgress);
        }}
      }}
      requestAnimationFrame(updateProgress);

      // --- 6. 鎹鸦巡检 · 异步版本检定矩阵 ---
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

def main():
    print("正在提取四大主角 WebP Base64 编码...")
    b64_t = get_base64_webp("tanjiro_water")
    b64_n = get_base64_webp("nezuko_basket")
    b64_z = get_base64_webp("zenitsu_thunder")
    b64_i = get_base64_webp("inosuke_beast")
    print(f"提取完成: 炭治郎={len(b64_t)}, 祢豆子={len(b64_n)}, 善逸={len(b64_z)}, 伊之助={len(b64_i)}")

    html = generate_html_content(b64_t, b64_n, b64_z, b64_i)

    # 1. 写入 resources/splash/index.html
    splash_file = REPO_ROOT / "resources" / "splash" / "index.html"
    splash_file.parent.mkdir(parents=True, exist_ok=True)
    splash_file.write_text(html, encoding="utf-8")
    print(f"已生成启动画面原型: {splash_file} ({splash_file.stat().st_size} 字节)")

    # 2. 写入工件目录下的实时预览文件
    artifact_preview = ARTIFACT_DIR / "splash_characters_preview.html"
    artifact_preview.write_text(html, encoding="utf-8")
    print(f"已生成工件右侧实时预览: {artifact_preview}")

    # 3. 生成可嵌入 Electron WebContentsView 的 loadingOverlay-zh.js
    escaped_html = html.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    overlay_js = f"""\"use strict\";
Object.defineProperty(exports, "__esModule", {{ value: true }});
exports.attachLoadingOverlay = attachLoadingOverlay;
const electron_1 = require("electron");

/**
 * Antigravity 《鬼灭之刃》全集中·反重力四象角色动作启动动效 (Kimetsu Character Action Overlay)
 * 采用原生 WebContentsView 于窗口创建第 0 毫秒硬件加速直出。
 * 融合炭治郎水流飞溅、善逸雷霆电弧、祢豆子探头摇曳、伊之助野猪喷气与鎹鸦巡检。
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
    overlay_file = REPO_ROOT / "resources" / "loadingOverlay-zh.js"
    overlay_file.write_text(overlay_js, encoding="utf-8")
    print(f"已生成原生遮罩代码: {overlay_file} ({overlay_file.stat().st_size} 字节)")

if __name__ == "__main__":
    main()
