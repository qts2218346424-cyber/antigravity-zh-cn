"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.attachLoadingOverlay = attachLoadingOverlay;
const electron_1 = require("electron");

/**
 * Antigravity 电影级反重力奇点与全息微引力场启动动效 (Cinematic Singularity Splash)
 * 采用原生 WebContentsView 于窗口创建第 0 毫秒硬件加速直出。
 * 彻底杜绝白屏与断层，提供极致未来科技仪式感与平滑无缝的主界面交接。
 */
function getLoadingHtml() {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
  :root {
    --bg-dark: #05070c;
    --cyan-glow: #00f2fe;
    --blue-neon: #38bdf8;
    --purple-deep: #7928ca;
    --purple-glow: #818cf8;
    --text-primary: #f8fafc;
    --text-muted: #64748b;
  }
  body {
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
    -webkit-app-region: drag;
  }

  /* 引力场与量子星尘 Canvas */
  #canvas-bg {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    z-index: 1; pointer-events: none;
  }

  /* 主舞台容器 */
  .stage {
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  /* 奇点与力场核心视窗 */
  .singularity-stage {
    position: relative;
    width: 260px;
    height: 260px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 28px;
    perspective: 1200px;
  }

  /* 宽银幕变形镜头光晕 (Anamorphic Lens Flare) */
  .lens-flare {
    position: absolute;
    width: 380px;
    height: 2px;
    background: linear-gradient(90deg, 
      transparent 0%, 
      rgba(0, 242, 254, 0.15) 20%, 
      rgba(0, 242, 254, 0.95) 50%, 
      rgba(121, 40, 202, 0.8) 55%, 
      rgba(0, 242, 254, 0.15) 80%, 
      transparent 100%
    );
    filter: drop-shadow(0 0 8px rgba(0, 242, 254, 0.9)) blur(0.5px);
    pointer-events: none;
    z-index: 6;
    animation: flarePulse 4s ease-in-out infinite alternate;
  }

  /* 外层 360° 全息精密刻度盘 (SVG Reticle) */
  .orbital-reticle {
    position: absolute;
    width: 250px;
    height: 250px;
    pointer-events: none;
    animation: spinClockwise 32s linear infinite;
    opacity: 0.75;
  }

  /* 中层反向高速电浆光流弧 (Counter Plasma Arcs) */
  .plasma-ring {
    position: absolute;
    width: 196px;
    height: 196px;
    border-radius: 50%;
    border: 2px solid transparent;
    border-top: 2px solid var(--cyan-glow);
    border-right: 1.5px solid rgba(0, 242, 254, 0.4);
    border-bottom: 2px solid var(--purple-glow);
    filter: drop-shadow(0 0 10px rgba(0, 242, 254, 0.8));
    animation: spinCounter 7s cubic-bezier(0.4, 0.1, 0.2, 1) infinite;
  }

  /* 内层正八边形反重力约束磁场 (Magnetic Containment Lattice) */
  .containment-lattice {
    position: absolute;
    width: 148px;
    height: 148px;
    pointer-events: none;
    animation: spinClockwise 16s cubic-bezier(0.68, -0.55, 0.27, 1.55) infinite;
    opacity: 0.65;
    filter: drop-shadow(0 0 6px rgba(129, 140, 248, 0.5));
  }

  /* 四角科技 HUD 瞄准锁框 (Quadrant HUD Brackets) */
  .hud-bracket {
    position: absolute;
    width: 14px;
    height: 14px;
    border: 1.5px solid rgba(56, 189, 248, 0.5);
    pointer-events: none;
  }
  .hud-bracket.tl { top: 12px; left: 12px; border-right: none; border-bottom: none; }
  .hud-bracket.tr { top: 12px; right: 12px; border-left: none; border-bottom: none; }
  .hud-bracket.bl { bottom: 12px; left: 12px; border-right: none; border-top: none; }
  .hud-bracket.br { bottom: 12px; right: 12px; border-left: none; border-top: none; }

  /* 吸积盘外晕 (Accretion Corona) */
  .accretion-corona {
    position: absolute;
    width: 110px;
    height: 110px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0, 242, 254, 0.45) 0%, rgba(121, 40, 202, 0.3) 50%, transparent 75%);
    filter: blur(14px);
    animation: coronaPulse 3.5s ease-in-out infinite alternate;
  }

  /* 视界深渊黑洞暗核 (Event Horizon Core) */
  .horizon-core {
    position: relative;
    width: 88px;
    height: 88px;
    border-radius: 50%;
    background: radial-gradient(circle at 40% 40%, #0d1527 0%, #05070c 80%);
    box-shadow: 
      0 0 0 1px rgba(0, 242, 254, 0.4),
      0 0 24px rgba(0, 242, 254, 0.7),
      0 0 55px rgba(121, 40, 202, 0.45),
      inset 0 0 18px rgba(0, 242, 254, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 5;
    animation: coreLevitate 4.5s ease-in-out infinite;
  }

  /* 反重力拓扑悬浮矢量徽标 (Antigravity Topological Glyph) */
  .core-glyph {
    width: 44px;
    height: 44px;
    filter: drop-shadow(0 0 8px rgba(0, 242, 254, 0.95)) drop-shadow(0 0 18px rgba(129, 140, 248, 0.7));
  }

  /* 品牌标识区域 */
  .brand-group {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 24px;
  }
  .title {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 7px;
    background: linear-gradient(135deg, #ffffff 15%, #cffafe 50%, #93c5fd 80%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 7px;
    text-transform: uppercase;
    text-shadow: 0 0 30px rgba(0, 242, 254, 0.4);
    display: flex;
    align-items: center;
    gap: 2px;
  }
  .title span.dot-accent {
    color: var(--cyan-glow);
    -webkit-text-fill-color: var(--cyan-glow);
    filter: drop-shadow(0 0 6px var(--cyan-glow));
  }
  .sub {
    font-size: 10px;
    font-family: "SF Mono", Consolas, Menlo, monospace;
    letter-spacing: 3px;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 8px;
    opacity: 0.85;
  }
  .sub::before, .sub::after {
    content: "";
    display: inline-block;
    width: 22px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.6));
  }
  .sub::after {
    background: linear-gradient(90deg, rgba(56, 189, 248, 0.6), transparent);
  }

  /* 分段式量子能量进度导轨 (Segmented Energy Rail) */
  .rail-wrapper {
    width: 360px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 14px;
  }
  .rail-meta {
    display: flex;
    justify-content: space-between;
    font-size: 10.5px;
    font-family: "SF Mono", Consolas, Menlo, monospace;
    color: #64748b;
    letter-spacing: 1px;
  }
  .rail-meta span.active-val {
    color: var(--cyan-glow);
    font-weight: 600;
  }
  .p-track {
    width: 100%;
    height: 4px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 2px;
    overflow: hidden;
    position: relative;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }
  .p-bar {
    position: absolute;
    top: 0; left: 0; height: 100%; width: 0%;
    background: linear-gradient(90deg, #0ea5e9, #00f2fe 70%, #ffffff 100%);
    box-shadow: 0 0 14px rgba(0, 242, 254, 0.9), 0 0 25px rgba(56, 189, 248, 0.5);
    transition: width 0.4s cubic-bezier(0.2, 0.8, 0.3, 1);
  }
  .p-scanline {
    position: absolute;
    top: 0; left: 0; width: 60px; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
    animation: scanMove 2s infinite linear;
  }

  /* 状态遥测流水日志 (Status Telemetry Terminal) */
  .telemetry-row {
    font-size: 11px;
    font-family: "SF Mono", Consolas, Menlo, monospace;
    color: #94a3b8;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 8px;
    height: 20px;
  }
  .telemetry-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--cyan-glow);
    box-shadow: 0 0 8px var(--cyan-glow);
    animation: pulseBlink 1.2s infinite ease-in-out alternate;
  }
  .telemetry-tag {
    color: #38bdf8;
    font-weight: 600;
  }
  .telemetry-text {
    color: #cbd5e1;
  }

  /* 底部四角微小遥测标识 */
  .corner-telemetry {
    position: absolute;
    font-size: 9.5px;
    font-family: "SF Mono", Consolas, Menlo, monospace;
    color: rgba(148, 163, 184, 0.45);
    letter-spacing: 1.5px;
  }
  .corner-telemetry.tl { top: 20px; left: 24px; }
  .corner-telemetry.tr { top: 20px; right: 24px; text-align: right; }
  .corner-telemetry.bl { bottom: 20px; left: 24px; }
  .corner-telemetry.br { bottom: 20px; right: 24px; text-align: right; }

  @keyframes spinClockwise {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  @keyframes spinCounter {
    0% { transform: rotateX(60deg) rotateZ(0deg); }
    100% { transform: rotateX(60deg) rotateZ(-360deg); }
  }
  @keyframes coreLevitate {
    0%, 100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-7px) scale(1.02); }
  }
  @keyframes flarePulse {
    0% { opacity: 0.6; transform: scaleX(0.92); }
    100% { opacity: 1; transform: scaleX(1.08); }
  }
  @keyframes coronaPulse {
    0% { transform: scale(0.9); opacity: 0.7; }
    100% { transform: scale(1.18); opacity: 1; }
  }
  @keyframes pulseBlink {
    0% { opacity: 0.35; transform: scale(0.85); }
    100% { opacity: 1; transform: scale(1.15); }
  }
  @keyframes scanMove {
    0% { transform: translateX(-100px); }
    100% { transform: translateX(360px); }
  }
</style>
</head>
<body>
  <canvas id="canvas-bg"></canvas>

  <div class="corner-telemetry tl">SYS.MATRIX // 0x7E3A<br>QUANTUM_FLUX: 99.98%</div>
  <div class="corner-telemetry tr">DEEPMIND ENGINE v2.24<br>GRAVITY: -0.001G</div>
  <div class="corner-telemetry bl">TERMS: 3,404 LOCALIZED<br>FEDERATION: ACTIVE</div>
  <div class="corner-telemetry br">SEC.ZONE: LEVEL_0<br>MONACO_AST: COMPILED</div>

  <div class="stage">
    <div class="singularity-stage">
      <div class="hud-bracket tl"></div>
      <div class="hud-bracket tr"></div>
      <div class="hud-bracket bl"></div>
      <div class="hud-bracket br"></div>

      <!-- 电影级宽银幕镜头光芒 -->
      <div class="lens-flare"></div>

      <!-- 外层 360° 全息精密刻度盘 SVG -->
      <svg class="orbital-reticle" viewBox="0 0 250 250">
        <circle cx="125" cy="125" r="118" fill="none" stroke="rgba(0, 242, 254, 0.25)" stroke-width="1" stroke-dasharray="3 7"/>
        <circle cx="125" cy="125" r="112" fill="none" stroke="rgba(56, 189, 248, 0.4)" stroke-width="1.5" stroke-dasharray="14 18 2 18"/>
        <!-- 象限刻度标记 -->
        <line x1="125" y1="2" x2="125" y2="12" stroke="#00f2fe" stroke-width="2"/>
        <line x1="125" y1="238" x2="125" y2="248" stroke="#00f2fe" stroke-width="2"/>
        <line x1="2" y1="125" x2="12" y2="125" stroke="#00f2fe" stroke-width="2"/>
        <line x1="238" y1="125" x2="248" y2="125" stroke="#00f2fe" stroke-width="2"/>
        <!-- 45度辅助刻度 -->
        <circle cx="125" cy="125" r="102" fill="none" stroke="rgba(129, 140, 248, 0.2)" stroke-width="0.8"/>
      </svg>

      <!-- 中层反向电浆光流环 -->
      <div class="plasma-ring"></div>

      <!-- 内层八边形约束力场 SVG -->
      <svg class="containment-lattice" viewBox="0 0 148 148">
        <polygon points="44,5 104,5 143,44 143,104 104,143 44,143 5,104 5,44" fill="none" stroke="rgba(129, 140, 248, 0.55)" stroke-width="1.2" stroke-dasharray="8 6"/>
        <circle cx="44" cy="5" r="2" fill="#00f2fe"/>
        <circle cx="104" cy="5" r="2" fill="#00f2fe"/>
        <circle cx="143" cy="44" r="2" fill="#818cf8"/>
        <circle cx="143" cy="104" r="2" fill="#818cf8"/>
        <circle cx="104" cy="143" r="2" fill="#00f2fe"/>
        <circle cx="44" cy="143" r="2" fill="#00f2fe"/>
        <circle cx="5" cy="104" r="2" fill="#818cf8"/>
        <circle cx="5" cy="44" r="2" fill="#818cf8"/>
      </svg>

      <!-- 核心吸积盘光晕 -->
      <div class="accretion-corona"></div>

      <!-- 视界深渊暗核与反重力徽标 -->
      <div class="horizon-core">
        <svg class="core-glyph" viewBox="0 0 48 48" fill="none">
          <!-- 反重力量子折叠拓扑几何 -->
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
      <div class="sub">GOOGLE DEEPMIND · QUANTUM ARCHITECTURE</div>
    </div>

    <!-- 分段能量导轨进度条 -->
    <div class="rail-wrapper">
      <div class="rail-meta">
        <span>CORE.ACCELERATION</span>
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
      <span class="telemetry-text" id="st">正在唤醒深空反重力奇点核心...</span>
    </div>
  </div>

  <script>
    // 1. 引力透镜与物理星尘 Canvas 引擎
    const cvs = document.getElementById('canvas-bg');
    const ctx = cvs.getContext('2d');
    let w = cvs.width = window.innerWidth;
    let h = cvs.height = window.innerHeight;
    window.addEventListener('resize', () => {
      w = cvs.width = window.innerWidth;
      h = cvs.height = window.innerHeight;
    });

    const particles = [];
    const PARTICLE_COUNT = 90;
    const centerX = w / 2;
    const centerY = h / 2;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const angle = Math.random() * Math.PI * 2;
      const dist = Math.random() * Math.max(w, h) * 0.65 + 40;
      particles.push({
        x: centerX + Math.cos(angle) * dist,
        y: centerY + Math.sin(angle) * dist,
        vx: (Math.random() - 0.5) * 0.6,
        vy: -(Math.random() * 0.8 + 0.4),
        size: Math.random() * 1.8 + 0.6,
        alpha: Math.random() * 0.6 + 0.2,
        color: Math.random() > 0.4 ? '#00f2fe' : (Math.random() > 0.5 ? '#818cf8' : '#ffffff'),
        speedFactor: Math.random() * 0.8 + 0.6
      });
    }

    let ripples = [];
    let rippleTimer = 0;

    function renderScene() {
      ctx.clearRect(0, 0, w, h);

      // 周期性产生引力波纹 (Gravitational Shockwave)
      rippleTimer++;
      if (rippleTimer % 140 === 0) {
        ripples.push({ r: 40, maxR: 320, alpha: 0.45 });
      }

      for (let i = ripples.length - 1; i >= 0; i--) {
        const rp = ripples[i];
        rp.r += 2.2;
        rp.alpha -= 0.0035;
        if (rp.alpha <= 0 || rp.r >= rp.maxR) {
          ripples.splice(i, 1);
          continue;
        }
        ctx.beginPath();
        ctx.arc(w / 2, h / 2, rp.r, 0, Math.PI * 2);
        ctx.strokeStyle = '#00f2fe';
        ctx.lineWidth = 1;
        ctx.globalAlpha = rp.alpha;
        ctx.stroke();
      }

      // 绘制物理引力流星尘
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.y += p.vy * p.speedFactor;
        p.x += p.vx * p.speedFactor;

        // 微幅双曲反重力发散
        const dx = p.x - (w / 2);
        const dy = p.y - (h / 2);
        const distSq = dx * dx + dy * dy;
        if (distSq < 18000) {
          p.x += (dx / Math.sqrt(distSq)) * 0.9;
          p.y += (dy / Math.sqrt(distSq)) * 0.9;
        }

        if (p.y < -20 || p.x < -20 || p.x > w + 20) {
          p.y = h + 15;
          p.x = Math.random() * w;
        }

        // 运动拉伸轨迹 (Motion Tail)
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x - p.vx * 3, p.y - p.vy * 4);
        ctx.strokeStyle = p.color;
        ctx.lineWidth = p.size;
        ctx.globalAlpha = p.alpha;
        ctx.stroke();
      }

      requestAnimationFrame(renderScene);
    }
    requestAnimationFrame(renderScene);

    // 2. 7 秒平滑推进时序与高精遥测流水
    const stages = [
      { p: 14.5, hex: '[0x00A1]', text: '正在唤醒深空反重力奇点核心 (Singularity Matrix)...' },
      { p: 32.0, hex: '[0x01BF]', text: '校准时空微曲率引擎与空间引力透镜...' },
      { p: 48.5, hex: '[0x02DC]', text: '链接异构多智能体联邦总线 (Federation Backbone)...' },
      { p: 66.0, hex: '[0x03EA]', text: '挂载 3,404 词条全景汉化语义拓扑与工作区上下文...' },
      { p: 82.5, hex: '[0x04F8]', text: '编译 Monaco 语法树与语言服务集群 (LSP)...' },
      { p: 94.0, hex: '[0x05DE]', text: '预热 GPU 渲染管线与智能体拓扑视窗...' },
      { p: 100.0, hex: '[0x0600]', text: '反重力力场锁定完毕 · 正在平滑接入工作台...' }
    ];

    let currentStage = 0;
    let targetPct = stages[0].p;
    let currentPct = 0;

    const pb = document.getElementById('pbar');
    const pctVal = document.getElementById('pct-val');
    const tagEl = document.getElementById('tag');
    const stEl = document.getElementById('st');

    // 进度平滑插值步进
    const progressInterval = setInterval(() => {
      if (currentPct < targetPct) {
        currentPct += (targetPct - currentPct) * 0.12 + 0.15;
        if (currentPct > targetPct) currentPct = targetPct;
        if (pb) pb.style.width = currentPct.toFixed(1) + '%';
        if (pctVal) pctVal.textContent = currentPct.toFixed(1) + '%';
      }
    }, 40);

    // 阶段状态流转（覆盖 7 秒优雅节奏）
    const stageInterval = setInterval(() => {
      currentStage++;
      if (currentStage < stages.length) {
        targetPct = stages[currentStage].p;
        if (tagEl) tagEl.textContent = stages[currentStage].hex;
        if (stEl) stEl.textContent = stages[currentStage].text;
      } else {
        targetPct = 100.0;
        clearInterval(stageInterval);
      }
    }, 980);
  </script>
</body>
</html>`;
}

function attachLoadingOverlay(win, foregroundColor, backgroundColor) {
  const view = new electron_1.WebContentsView({
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });
  const html = getLoadingHtml();
  void view.webContents.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
  win.contentView.addChildView(view);
  const updateBounds = () => {
    if (win.isDestroyed()) return;
    const [width, height] = win.getContentSize();
    view.setBounds({ x: 0, y: 0, width, height });
  };
  updateBounds();
  win.on('resize', updateBounds);

  let isRemoved = false;
  const startTime = Date.now();
  // 电影级沉浸展示时长延长至 7.0 秒整，彻底消除急促感，确保底层 React+Monaco 完全渲染就绪
  const MIN_DISPLAY_TIME = 7000;
  // 最大超时保底提升至 9.5 秒
  const MAX_TIMEOUT = 9500;

  let pageLoaded = false;
  win.webContents.once('did-finish-load', () => {
    pageLoaded = true;
  });

  const checkAndDismiss = async () => {
    if (isRemoved) return;
    const elapsed = Date.now() - startTime;

    // 1. 如果时间尚未达到 7.0 秒最低沉浸展示时长，继续等待
    if (elapsed < MIN_DISPLAY_TIME) {
      setTimeout(checkAndDismiss, MIN_DISPLAY_TIME - elapsed);
      return;
    }

    // 2. 达到最低时间后，检测底层主界面是否真正深度渲染就绪（排除初级空骨架）
    let isUiReady = false;
    if (pageLoaded && !win.isDestroyed()) {
      try {
        isUiReady = await win.webContents.executeJavaScript(`
          Boolean(
            document.body && (
              document.querySelector('nav, [role="navigation"], .monaco-editor, textarea, [contenteditable="true"], [data-testid]') ||
              (document.getElementById('root') && document.getElementById('root').querySelectorAll('*').length > 18) ||
              document.body.querySelectorAll('*').length > 30
            )
          )
        `);
      } catch (_) {
        isUiReady = true; // 异常时容错放行
      }
    }

    // 3. 如果底层 UI 仍在构建且未超过最大保底时间，稍等 250ms 继续探测
    if (!isUiReady && elapsed < MAX_TIMEOUT) {
      setTimeout(checkAndDismiss, 250);
      return;
    }

    // 4. 正式平滑淡出与交接 (0.8 秒电影级深度消隐与缩放)
    isRemoved = true;
    try {
      view.webContents.executeJavaScript(`
        document.body.style.transition = 'opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
        document.body.style.opacity = '0';
        document.body.style.transform = 'scale(1.04)';
      `).catch(() => {});
    } catch (_) {}

    setTimeout(() => {
      try {
        if (!win.isDestroyed()) {
          win.contentView.removeChildView(view);
        }
      } catch (_) {}
      win.off('resize', updateBounds);
    }, 850);
  };

  // 触发首轮就绪检查 (7.0 秒)
  setTimeout(checkAndDismiss, MIN_DISPLAY_TIME);
  // 最大保底强制执行 (9.5 秒)
  setTimeout(() => {
    if (!isRemoved) checkAndDismiss();
  }, MAX_TIMEOUT);
}
