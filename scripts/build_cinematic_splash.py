# -*- coding: utf-8 -*-
"""
生成电影级《星际穿越》黑洞启动动效 HTML 并同步至资源与工件预览
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
media_dir = REPO_ROOT / "resources" / "media"
video_data_path = media_dir / "video_data.json"

if not video_data_path.is_file():
    raise FileNotFoundError("未找到 video_data.json，请先生成视频缓存。")

with open(video_data_path, "r", encoding="utf-8") as f:
    vdata = json.load(f)
mp4_b64 = vdata["mp4_base64"]

html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Antigravity 《星际穿越》电影级黑洞启动动效控制台</title>
  <style>
    :root {{
      --bg-dark: #05070c;
      --cyan-glow: #00f2fe;
      --blue-neon: #38bdf8;
      --purple-deep: #7928ca;
      --purple-glow: #818cf8;
      --text-primary: #f8fafc;
      --text-muted: #64748b;
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
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: relative;
    }}

    /* 电影视频全屏沉浸铺底 */
    .cinematic-video {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      z-index: 1;
      filter: brightness(0.85) contrast(1.18) saturate(1.15);
      pointer-events: none;
      transition: opacity 1.2s ease;
    }}

    /* 电影级深空暗角遮罩 (Cinematic Vignette) */
    .cinematic-vignette {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 2;
      background: radial-gradient(circle at 50% 50%, rgba(5, 7, 12, 0.15) 15%, rgba(5, 7, 12, 0.65) 60%, #05070c 100%);
      pointer-events: none;
    }}

    /* 备用星尘引力场 Canvas */
    #canvas-bg {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 3;
      pointer-events: none;
      opacity: 0.45;
    }}

    /* 启动器主视窗容器 */
    .splash-container {{
      position: relative;
      z-index: 10;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 100%;
      max-width: 620px;
      perspective: 1200px;
      transition: opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    /* 奇点与力场核心视窗 */
    .singularity-stage {{
      position: relative;
      width: 280px;
      height: 280px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 24px;
      perspective: 1200px;
    }}

    /* 宽银幕变形镜头光晕 (Anamorphic Lens Flare) */
    .lens-flare {{
      position: absolute;
      width: 440px;
      height: 2px;
      background: linear-gradient(90deg, 
        transparent 0%, 
        rgba(0, 242, 254, 0.2) 20%, 
        rgba(0, 242, 254, 0.95) 50%, 
        rgba(255, 255, 255, 1) 52%,
        rgba(121, 40, 202, 0.85) 58%, 
        rgba(0, 242, 254, 0.2) 80%, 
        transparent 100%
      );
      filter: drop-shadow(0 0 10px rgba(0, 242, 254, 0.9)) blur(0.5px);
      pointer-events: none;
      z-index: 6;
      animation: flarePulse 4s ease-in-out infinite alternate;
    }}

    /* 外层 360° 全息精密刻度盘 (SVG Reticle) */
    .orbital-reticle {{
      position: absolute;
      width: 270px;
      height: 270px;
      pointer-events: none;
      animation: spinClockwise 36s linear infinite;
      opacity: 0.65;
    }}

    /* 中层高速电浆逆流光环 */
    .plasma-ring {{
      position: absolute;
      width: 210px;
      height: 210px;
      border-radius: 50%;
      border: 1.5px solid transparent;
      border-top: 2px solid var(--cyan-glow);
      border-right: 1.5px solid rgba(0, 242, 254, 0.4);
      border-bottom: 2px solid var(--purple-glow);
      filter: drop-shadow(0 0 12px rgba(0, 242, 254, 0.8));
      animation: spinCounter 8s cubic-bezier(0.4, 0.1, 0.2, 1) infinite;
    }}

    /* 四角科技 HUD 瞄准锁框 */
    .hud-bracket {{
      position: absolute;
      width: 14px;
      height: 14px;
      border: 1.5px solid rgba(56, 189, 248, 0.6);
      pointer-events: none;
    }}
    .hud-bracket.tl {{ top: 10px; left: 10px; border-right: none; border-bottom: none; }}
    .hud-bracket.tr {{ top: 10px; right: 10px; border-left: none; border-bottom: none; }}
    .hud-bracket.bl {{ bottom: 10px; left: 10px; border-right: none; border-top: none; }}
    .hud-bracket.br {{ bottom: 10px; right: 10px; border-left: none; border-top: none; }}

    /* 悬浮反重力量子徽标核心 */
    .horizon-core {{
      position: relative;
      width: 92px;
      height: 92px;
      border-radius: 50%;
      background: radial-gradient(circle at 40% 40%, rgba(13, 21, 39, 0.75) 0%, rgba(5, 7, 12, 0.85) 80%);
      box-shadow: 
        0 0 0 1px rgba(0, 242, 254, 0.4),
        0 0 25px rgba(0, 242, 254, 0.7),
        0 0 60px rgba(121, 40, 202, 0.5),
        inset 0 0 20px rgba(0, 242, 254, 0.35);
      backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 5;
      animation: coreLevitate 4.5s ease-in-out infinite;
    }}

    .core-glyph {{
      width: 46px;
      height: 46px;
      filter: drop-shadow(0 0 8px rgba(0, 242, 254, 0.95)) drop-shadow(0 0 18px rgba(129, 140, 248, 0.7));
    }}

    /* 品牌标识区域 */
    .brand-group {{
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: 22px;
    }}
    .title {{
      font-size: 27px;
      font-weight: 800;
      letter-spacing: 8px;
      background: linear-gradient(135deg, #ffffff 15%, #cffafe 50%, #93c5fd 80%, #a78bfa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 7px;
      text-transform: uppercase;
      text-shadow: 0 0 35px rgba(0, 242, 254, 0.4);
      display: flex;
      align-items: center;
      gap: 2px;
    }}
    .title span.dot-accent {{
      color: var(--cyan-glow);
      -webkit-text-fill-color: var(--cyan-glow);
      filter: drop-shadow(0 0 6px var(--cyan-glow));
    }}
    .sub {{
      font-size: 10px;
      font-family: "SF Mono", Consolas, Menlo, monospace;
      letter-spacing: 3.5px;
      color: #94a3b8;
      display: flex;
      align-items: center;
      gap: 8px;
      opacity: 0.9;
    }}
    .sub::before, .sub::after {{
      content: "";
      display: inline-block;
      width: 24px;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.6));
    }}
    .sub::after {{
      background: linear-gradient(90deg, rgba(56, 189, 248, 0.6), transparent);
    }}

    /* 分段式量子能量进度导轨 */
    .rail-wrapper {{
      width: 380px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 14px;
    }}
    .rail-meta {{
      display: flex;
      justify-content: space-between;
      font-size: 10.5px;
      font-family: "SF Mono", Consolas, Menlo, monospace;
      color: #64748b;
      letter-spacing: 1px;
    }}
    .rail-meta span.active-val {{
      color: var(--cyan-glow);
      font-weight: 600;
    }}
    .p-track {{
      width: 100%;
      height: 4px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 2px;
      overflow: hidden;
      position: relative;
      border: 1px solid rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(4px);
    }}
    .p-bar {{
      position: absolute;
      top: 0; left: 0; height: 100%; width: 0%;
      background: linear-gradient(90deg, #0ea5e9, #00f2fe 70%, #ffffff 100%);
      box-shadow: 0 0 14px rgba(0, 242, 254, 0.9), 0 0 25px rgba(56, 189, 248, 0.5);
      transition: width 0.4s cubic-bezier(0.2, 0.8, 0.3, 1);
    }}
    .p-scanline {{
      position: absolute;
      top: 0; left: 0; width: 60px; height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
      animation: scanMove 2s infinite linear;
    }}

    /* 状态遥测流水日志 */
    .telemetry-row {{
      font-size: 11px;
      font-family: "SF Mono", Consolas, Menlo, monospace;
      color: #94a3b8;
      letter-spacing: 0.5px;
      display: flex;
      align-items: center;
      gap: 8px;
      height: 20px;
    }}
    .telemetry-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: var(--cyan-glow);
      box-shadow: 0 0 8px var(--cyan-glow);
      animation: pulseBlink 1.2s infinite ease-in-out alternate;
    }}
    .telemetry-tag {{
      color: #38bdf8;
      font-weight: 600;
    }}
    .telemetry-text {{
      color: #cbd5e1;
    }}

    /* 底部四角微小遥测标识 */
    .corner-telemetry {{
      position: absolute;
      font-size: 9.5px;
      font-family: "SF Mono", Consolas, Menlo, monospace;
      color: rgba(148, 163, 184, 0.55);
      letter-spacing: 1.5px;
      z-index: 10;
    }}
    .corner-telemetry.tl {{ top: 22px; left: 24px; }}
    .corner-telemetry.tr {{ top: 22px; right: 24px; text-align: right; }}
    .corner-telemetry.bl {{ bottom: 22px; left: 24px; }}
    .corner-telemetry.br {{ bottom: 22px; right: 24px; text-align: right; }}

    /* 控制面板 */
    .control-panel {{
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(15, 23, 42, 0.88);
      border: 1px solid rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(16px);
      padding: 10px 22px;
      border-radius: 30px;
      display: flex;
      gap: 16px;
      z-index: 100;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    }}
    .btn {{
      background: rgba(56, 189, 248, 0.18);
      border: 1px solid rgba(56, 189, 248, 0.45);
      color: #38bdf8;
      padding: 6px 16px;
      border-radius: 16px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s ease;
      font-weight: 600;
    }}
    .btn:hover {{
      background: rgba(56, 189, 248, 0.35);
      color: #ffffff;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
    }}

    @keyframes spinClockwise {{
      0% {{ transform: rotate(0deg); }}
      100% {{ transform: rotate(360deg); }}
    }}
    @keyframes spinCounter {{
      0% {{ transform: rotateX(60deg) rotateZ(0deg); }}
      100% {{ transform: rotateX(60deg) rotateZ(-360deg); }}
    }}
    @keyframes coreLevitate {{
      0%, 100% {{ transform: translateY(0) scale(1); }}
      50% {{ transform: translateY(-7px) scale(1.02); }}
    }}
    @keyframes flarePulse {{
      0% {{ opacity: 0.65; transform: scaleX(0.92); }}
      100% {{ opacity: 1; transform: scaleX(1.08); }}
    }}
    @keyframes pulseBlink {{
      0% {{ opacity: 0.35; transform: scale(0.85); }}
      100% {{ opacity: 1; transform: scale(1.15); }}
    }}
    @keyframes scanMove {{
      0% {{ transform: translateX(-100px); }}
      100% {{ transform: translateX(380px); }}
    }}
  </style>
</head>
<body>
  <!-- 1. 电影级真实卡冈图雅黑洞吸积盘旋转视频 (MP4 Base64 硬件解码) -->
  <video class="cinematic-video" autoplay muted loop playsinline id="main-video">
    <source src="data:video/mp4;base64,{mp4_b64}" type="video/mp4">
  </video>

  <!-- 2. 电影级深空暗角遮罩 -->
  <div class="cinematic-vignette"></div>

  <!-- 3. 极微星尘 Canvas -->
  <canvas id="canvas-bg"></canvas>

  <div class="corner-telemetry tl">SYS.MATRIX // GARGANTUA_LENSING<br>QUANTUM_FLUX: 99.98%</div>
  <div class="corner-telemetry tr">DEEPMIND ENGINE v2.24<br>GRAVITY: -0.001G</div>
  <div class="corner-telemetry bl">TERMS: 3,404 LOCALIZED<br>FEDERATION: ACTIVE</div>
  <div class="corner-telemetry br">HORIZON: 1.0 Rg<br>AST_STATUS: COMPILED</div>

  <div class="splash-container" id="splash-node">
    <div class="singularity-stage">
      <div class="hud-bracket tl"></div>
      <div class="hud-bracket tr"></div>
      <div class="hud-bracket bl"></div>
      <div class="hud-bracket br"></div>

      <!-- 宽银幕镜头光芒 -->
      <div class="lens-flare"></div>

      <!-- 360° 全息精密刻度盘 SVG -->
      <svg class="orbital-reticle" viewBox="0 0 250 250">
        <circle cx="125" cy="125" r="118" fill="none" stroke="rgba(0, 242, 254, 0.25)" stroke-width="1" stroke-dasharray="3 7"/>
        <circle cx="125" cy="125" r="112" fill="none" stroke="rgba(56, 189, 248, 0.4)" stroke-width="1.5" stroke-dasharray="14 18 2 18"/>
        <line x1="125" y1="2" x2="125" y2="12" stroke="#00f2fe" stroke-width="2"/>
        <line x1="125" y1="238" x2="125" y2="248" stroke="#00f2fe" stroke-width="2"/>
        <line x1="2" y1="125" x2="12" y2="125" stroke="#00f2fe" stroke-width="2"/>
        <line x1="238" y1="125" x2="248" y2="125" stroke="#00f2fe" stroke-width="2"/>
        <circle cx="125" cy="125" r="102" fill="none" stroke="rgba(129, 140, 248, 0.2)" stroke-width="0.8"/>
      </svg>

      <!-- 中层电浆逆流环 -->
      <div class="plasma-ring"></div>

      <!-- 悬浮量子徽标 -->
      <div class="horizon-core">
        <svg class="core-glyph" viewBox="0 0 48 48" fill="none">
          <path d="M24 6L40 34H8L24 6Z" stroke="url(#glyph-grad-1)" stroke-width="2.5" stroke-linejoin="round"/>
          <path d="M24 18L34 36H14L24 18Z" stroke="url(#glyph-grad-2)" stroke-width="1.8" stroke-dasharray="3 3"/>
          <circle cx="24" cy="28" r="3.5" fill="#00f2fe" filter="drop-shadow(0 0 6px #00f2fe)"/>
          <path d="M24 2V8M40 34L45 37M8 34L3 37" stroke="#00f2fe" stroke-width="2" stroke-linecap="round"/>
          <defs>
            <linearGradient id="glyph-grad-1" x1="8" y1="6" x2="40" y2="34" gradientUnits="userSpaceOnUse">
              <stop stop-color="#ffffff"/>
              <stop offset="0.5" stop-color="#00f2fe"/>
              <stop offset="1" stop-color="#7928ca"/>
            </linearGradient>
            <linearGradient id="glyph-grad-2" x1="14" y1="18" x2="34" y2="36" gradientUnits="userSpaceOnUse">
              <stop stop-color="#38bdf8"/>
              <stop offset="1" stop-color="#c084fc"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
    </div>

    <!-- 标题与副标题 -->
    <div class="brand-group">
      <div class="title">ANTIGRAVITY<span class="dot-accent">.</span></div>
      <div class="sub">INTERSTELLAR GARGANTUA · QUANTUM SINGULARITY</div>
    </div>

    <!-- 分段能量导轨进度条 -->
    <div class="rail-wrapper">
      <div class="rail-meta">
        <span>GRAVITATIONAL.ACCELERATION</span>
        <span class="active-val" id="pct-val">0.0%</span>
      </div>
      <div class="p-track">
        <div class="p-bar" id="pbar"></div>
        <div class="p-scanline"></div>
      </div>
    </div>

    <!-- 遥测流水状态日志 -->
    <div class="telemetry-row">
      <span class="telemetry-dot"></span>
      <span class="telemetry-tag" id="tag">[0x00A1]</span>
      <span class="telemetry-text" id="st">正在唤醒卡冈图雅反重力奇点核心...</span>
    </div>
  </div>

  <div class="control-panel">
    <button class="btn" onclick="replayAnimation()">重新演练 (7.0 秒)</button>
    <button class="btn" onclick="toggleDismiss()">模拟就绪平滑淡出</button>
  </div>

  <script>
    // 备用物理微星尘 Canvas
    const cvs = document.getElementById('canvas-bg');
    const ctx = cvs.getContext('2d');
    let w = cvs.width = window.innerWidth;
    let h = cvs.height = window.innerHeight;
    window.addEventListener('resize', () => {{
      w = cvs.width = window.innerWidth;
      h = cvs.height = window.innerHeight;
    }});

    const particles = [];
    for (let i = 0; i < 40; i++) {{
      particles.push({{
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.4,
        vy: -(Math.random() * 0.6 + 0.2),
        size: Math.random() * 1.5 + 0.5,
        alpha: Math.random() * 0.5 + 0.1,
        color: Math.random() > 0.5 ? '#00f2fe' : '#818cf8'
      }});
    }}

    function renderDust() {{
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < particles.length; i++) {{
        const p = particles[i];
        p.y += p.vy;
        p.x += p.vx;
        if (p.y < -10) {{ p.y = h + 10; p.x = Math.random() * w; }}
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.alpha;
        ctx.fill();
      }}
      requestAnimationFrame(renderDust);
    }}
    requestAnimationFrame(renderDust);

    // 7 秒平滑时序控制
    const stages = [
      {{ p: 14.5, hex: '[0x00A1]', text: '正在唤醒卡冈图雅反重力奇点核心 (Interstellar Singularity)...' }},
      {{ p: 32.0, hex: '[0x01BF]', text: '校准时空微曲率引擎与空间引力透镜吸积盘...' }},
      {{ p: 48.5, hex: '[0x02DC]', text: '链接异构多智能体联邦总线 (Federation Backbone)...' }},
      {{ p: 66.0, hex: '[0x03EA]', text: '挂载 3,404 词条全景汉化语义拓扑与工作区上下文...' }},
      {{ p: 82.5, hex: '[0x04F8]', text: '编译 Monaco 语法树与语言服务集群 (LSP)...' }},
      {{ p: 94.0, hex: '[0x05DE]', text: '预热 GPU 渲染管线与智能体拓扑视窗...' }},
      {{ p: 100.0, hex: '[0x0600]', text: '引力透镜常数锁定完毕 · 正在平滑接入工作台...' }}
    ];

    let currentStage = 0;
    let targetPct = stages[0].p;
    let currentPct = 0;
    let progressInterval, stageInterval;

    const splashNode = document.getElementById('splash-node');
    const pb = document.getElementById('pbar');
    const pctVal = document.getElementById('pct-val');
    const tagEl = document.getElementById('tag');
    const stEl = document.getElementById('st');
    const vid = document.getElementById('main-video');

    function startProgress() {{
      currentStage = 0;
      targetPct = stages[0].p;
      currentPct = 0;
      splashNode.style.opacity = '1';
      splashNode.style.transform = 'scale(1)';
      if (vid) vid.currentTime = 0;
      if (tagEl) tagEl.textContent = stages[0].hex;
      if (stEl) stEl.textContent = stages[0].text;

      clearInterval(progressInterval);
      clearInterval(stageInterval);

      progressInterval = setInterval(() => {{
        if (currentPct < targetPct) {{
          currentPct += (targetPct - currentPct) * 0.12 + 0.15;
          if (currentPct > targetPct) currentPct = targetPct;
          if (pb) pb.style.width = currentPct.toFixed(1) + '%';
          if (pctVal) pctVal.textContent = currentPct.toFixed(1) + '%';
        }}
      }}, 40);

      stageInterval = setInterval(() => {{
        currentStage++;
        if (currentStage < stages.length) {{
          targetPct = stages[currentStage].p;
          if (tagEl) tagEl.textContent = stages[currentStage].hex;
          if (stEl) stEl.textContent = stages[currentStage].text;
        }} else {{
          targetPct = 100.0;
          clearInterval(stageInterval);
        }}
      }}, 980);
    }}

    startProgress();

    function replayAnimation() {{
      startProgress();
    }}

    function toggleDismiss() {{
      splashNode.style.opacity = '0';
      splashNode.style.transform = 'scale(1.04)';
      setTimeout(() => {{
        alert('启动动效已优雅淡出！底层主工作台已无缝就绪。');
        splashNode.style.opacity = '1';
        splashNode.style.transform = 'scale(1)';
      }}, 850);
    }}
  </script>
</body>
</html>"""

# 写入 resources/splash/index.html
splash_html_path = REPO_ROOT / "resources" / "splash" / "index.html"
splash_html_path.write_text(html_template, encoding="utf-8")
print(f"成功更新演示文件: {splash_html_path}")

# 同步更新工件预览
artifact_path = Path(r"C:\Users\QTS的天选\.gemini\antigravity\brain\158062cb-0b2d-485e-b84e-ad56b751e715\splash_preview.html")
if artifact_path.parent.is_dir():
    artifact_path.write_text(html_template, encoding="utf-8")
    print(f"成功更新工件预览: {artifact_path}")

# 生成纯自包含的主进程原生遮罩 resources/loadingOverlay-zh.js
overlay_js_content = f'''"use strict";
Object.defineProperty(exports, "__esModule", {{ value: true }});
exports.attachLoadingOverlay = attachLoadingOverlay;
const electron_1 = require("electron");

/**
 * Antigravity 《星际穿越》电影级卡冈图雅黑洞与全息微引力场启动动效 (Cinematic Gargantua Splash)
 * 采用原生 WebContentsView 于窗口创建第 0 毫秒硬件加速直出。
 * 全屏沉浸式电影级黑洞吸积盘视频 (GPU 硬件解码) + 悬浮极简科技 HUD，彻底杜绝白屏断层。
 */
function getLoadingHtml() {{
  return `{html_template.replace("<!-- 底部控制面板（仅演示环境有效） -->", "").replace('<div class="control-panel">', '<div class="control-panel" style="display:none">')}`;
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
  // 电影级沉浸展示时长延长至 7.0 秒整，彻底消除急促感，确保底层 React+Monaco 完全渲染就绪
  const MIN_DISPLAY_TIME = 7000;
  // 最大超时保底提升至 9.5 秒
  const MAX_TIMEOUT = 9500;

  let pageLoaded = false;
  win.webContents.once('did-finish-load', () => {{
    pageLoaded = true;
  }});

  const checkAndDismiss = async () => {{
    if (isRemoved) return;
    const elapsed = Date.now() - startTime;

    // 1. 如果时间尚未达到 7.0 秒最低沉浸展示时长，继续等待
    if (elapsed < MIN_DISPLAY_TIME) {{
      setTimeout(checkAndDismiss, MIN_DISPLAY_TIME - elapsed);
      return;
    }}

    // 2. 达到最低时间后，检测底层主界面是否真正深度渲染就绪（排除初级空骨架）
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
        isUiReady = true; // 异常时容错放行
      }}
    }}

    // 3. 如果底层 UI 仍在构建且未超过最大保底时间，稍等 250ms 继续探测
    if (!isUiReady && elapsed < MAX_TIMEOUT) {{
      setTimeout(checkAndDismiss, 250);
      return;
    }}

    // 4. 正式平滑淡出与交接 (0.8 秒电影级深度消隐与微膨胀)
    isRemoved = true;
    try {{
      view.webContents.executeJavaScript(`
        const splashNode = document.getElementById('splash-node');
        const videoNode = document.querySelector('.cinematic-video');
        if (splashNode) {{
          splashNode.style.transition = 'opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
          splashNode.style.opacity = '0';
          splashNode.style.transform = 'scale(1.04)';
        }}
        if (videoNode) {{
          videoNode.style.transition = 'opacity 0.8s ease';
          videoNode.style.opacity = '0';
        }}
        document.body.style.transition = 'opacity 0.8s ease';
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
    }}, 850);
  }};

  // 触发首轮就绪检查 (7.0 秒)
  setTimeout(checkAndDismiss, MIN_DISPLAY_TIME);
  // 最大保底强制执行 (9.5 秒)
  setTimeout(() => {{
    if (!isRemoved) checkAndDismiss();
  }}, MAX_TIMEOUT);
}}
'''

loading_overlay_path = REPO_ROOT / "resources" / "loadingOverlay-zh.js"
loading_overlay_path.write_text(overlay_js_content, encoding="utf-8")
print(f"成功更新主进程原生开屏遮罩: {loading_overlay_path} ({loading_overlay_path.stat().st_size / 1024:.2f} KB)")

