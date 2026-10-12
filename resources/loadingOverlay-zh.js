"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.attachLoadingOverlay = attachLoadingOverlay;
const electron_1 = require("electron");

/**
 * Antigravity 原厂级反重力深空启动动效 (Native WebContentsView Splash)
 * 在主进程创建窗口的第 0 毫秒同步挂载，配合智能渲染就绪握手，彻底杜绝白屏与加载中断。
 */
function getLoadingHtml() {
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
  body {
    background-color: #07090e;
    color: #f1f5f9;
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
  #canvas-bg {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    z-index: 1; pointer-events: none;
  }
  .stage {
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .core-stage {
    position: relative;
    width: 200px;
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    perspective: 1000px;
  }
  .ring-outer {
    position: absolute;
    width: 190px; height: 190px;
    border-radius: 50%;
    border: 1.5px dashed rgba(56, 189, 248, 0.45);
    box-shadow: 0 0 25px rgba(56, 189, 248, 0.15);
    animation: rot1 14s linear infinite;
  }
  .ring-middle {
    position: absolute;
    width: 148px; height: 148px;
    border-radius: 50%;
    border: 2px solid transparent;
    border-top-color: #38bdf8;
    border-bottom-color: #818cf8;
    filter: drop-shadow(0 0 12px rgba(56, 189, 248, 0.8));
    animation: rot2 6s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite;
  }
  .ring-inner {
    position: absolute;
    width: 110px; height: 110px;
    border-radius: 50%;
    border: 1px solid rgba(129, 140, 248, 0.3);
    border-left: 2px solid #a855f7;
    animation: rot3 4s linear infinite reverse;
  }
  .wave {
    position: absolute;
    width: 84px; height: 84px;
    border-radius: 50%;
    border: 1.5px solid rgba(56, 189, 248, 0.7);
    animation: rip 2.6s cubic-bezier(0.1, 0.8, 0.3, 1) infinite;
  }
  .sphere {
    position: relative;
    width: 80px; height: 80px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #ffffff 0%, #38bdf8 30%, #4338ca 75%, #0f172a 100%);
    box-shadow: 0 0 35px rgba(56, 189, 248, 0.9), 0 0 70px rgba(129, 140, 248, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    animation: lev 3.2s ease-in-out infinite;
  }
  .logo-svg {
    width: 40px; height: 40px;
    fill: none; stroke: #ffffff; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round;
    filter: drop-shadow(0 0 6px rgba(255, 255, 255, 0.9));
  }
  .title {
    font-size: 27px;
    font-weight: 700;
    letter-spacing: 4px;
    background: linear-gradient(135deg, #ffffff 30%, #bae6fd 60%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 6px;
    text-transform: uppercase;
  }
  .sub {
    font-size: 11px;
    letter-spacing: 2px;
    color: #94a3b8;
    margin-bottom: 22px;
  }
  .p-box {
    width: 300px; height: 3.5px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 3px;
    overflow: hidden;
    position: relative;
    margin-bottom: 12px;
  }
  .p-bar {
    position: absolute; top: 0; left: 0; height: 100%; width: 0%;
    background: linear-gradient(90deg, #06b6d4, #38bdf8, #818cf8);
    box-shadow: 0 0 10px #38bdf8;
    transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .status {
    font-size: 11px;
    font-family: "SF Mono", Consolas, Menlo, monospace;
    color: #94a3b8;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 6px;
    height: 18px;
  }
  .dot {
    width: 5px; height: 5px; border-radius: 50%;
    background-color: #38bdf8;
    box-shadow: 0 0 6px #38bdf8;
    animation: blink 1s infinite alternate;
  }
  @keyframes rot1 { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
  @keyframes rot2 { 0% { transform: rotateX(65deg) rotateY(25deg) rotateZ(0deg); } 100% { transform: rotateX(65deg) rotateY(25deg) rotateZ(360deg); } }
  @keyframes rot3 { 0% { transform: rotateX(35deg) rotateY(65deg) rotateZ(0deg); } 100% { transform: rotateX(35deg) rotateY(65deg) rotateZ(360deg); } }
  @keyframes lev { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
  @keyframes rip { 0% { transform: scale(0.9); opacity: 0.9; } 100% { transform: scale(2.2); opacity: 0; } }
  @keyframes blink { 0% { opacity: 0.3; } 100% { opacity: 1; } }
</style>
</head>
<body>
  <canvas id="canvas-bg"></canvas>
  <div class="stage">
    <div class="core-stage">
      <div class="ring-outer"></div>
      <div class="ring-middle"></div>
      <div class="ring-inner"></div>
      <div class="wave"></div>
      <div class="sphere">
        <svg class="logo-svg" viewBox="0 0 24 24">
          <path d="M12 3L4 14h5v7h6v-7h5L12 3z"/>
          <circle cx="12" cy="19" r="1.5" fill="#38bdf8"/>
        </svg>
      </div>
    </div>
    <div class="title">Antigravity</div>
    <div class="sub">GOOGLE DEEPMIND · AGENT ARCHITECTURE</div>
    <div class="p-box"><div class="p-bar" id="pbar"></div></div>
    <div class="status"><span class="dot"></span><span id="st">正在启动反重力引擎内核...</span></div>
  </div>
  <script>
    const cvs = document.getElementById('canvas-bg');
    const ctx = cvs.getContext('2d');
    let w = cvs.width = window.innerWidth;
    let h = cvs.height = window.innerHeight;
    const pts = [];
    for (let i = 0; i < 70; i++) {
      pts.push({
        x: Math.random() * w,
        y: Math.random() * h,
        s: Math.random() * 2 + 0.8,
        vy: -(Math.random() * 1.3 + 0.5),
        vx: (Math.random() - 0.5) * 0.6,
        a: Math.random() * 0.5 + 0.2,
        c: Math.random() > 0.5 ? '#38bdf8' : '#818cf8'
      });
    }
    function draw() {
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        p.y += p.vy;
        p.x += p.vx;
        if (p.y < -10) { p.y = h + 10; p.x = Math.random() * w; }
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.s, 0, Math.PI * 2);
        ctx.fillStyle = p.c;
        ctx.globalAlpha = p.a;
        ctx.fill();
      }
      requestAnimationFrame(draw);
    }
    requestAnimationFrame(draw);

    const stages = [
      { p: 15, t: '正在启动反重力引擎内核 (Antigravity Engine)...' },
      { p: 35, t: '校准引力场曲率与量子矩阵...' },
      { p: 58, t: '初始化异构多智能体联邦通信总线...' },
      { p: 76, t: '加载本地全景汉化与工作区上下文...' },
      { p: 88, t: '挂载代码分析引擎与智能体协同拓扑...' },
      { p: 96, t: '正在构建主工作台界面与会话面板...' },
      { p: 100, t: '反重力就绪 · 正在进入工作台...' }
    ];
    let idx = 0;
    const pb = document.getElementById('pbar');
    const st = document.getElementById('st');
    const timer = setInterval(() => {
      if (idx < stages.length) {
        if (pb) pb.style.width = stages[idx].p + '%';
        if (st) st.textContent = stages[idx].t;
        idx++;
      } else {
        clearInterval(timer);
      }
    }, 650);
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
  // 基础沉浸展示时长提升至 4.8 秒，充分覆盖大型 React/Monaco 引擎冷启动耗时
  const MIN_DISPLAY_TIME = 4800;
  // 最大超时保底提升至 7.2 秒
  const MAX_TIMEOUT = 7200;

  let pageLoaded = false;
  win.webContents.once('did-finish-load', () => {
    pageLoaded = true;
  });

  const checkAndDismiss = async () => {
    if (isRemoved) return;
    const elapsed = Date.now() - startTime;

    // 1. 如果时间尚未达到 4.8 秒最低沉浸展示时长，继续等待
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
              (document.getElementById('root') && document.getElementById('root').querySelectorAll('*').length > 15) ||
              document.body.querySelectorAll('*').length > 25
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

    // 4. 正式平滑淡出与交接
    isRemoved = true;
    try {
      view.webContents.executeJavaScript(`
        document.body.style.transition = 'opacity 0.65s cubic-bezier(0.4, 0, 0.2, 1), transform 0.65s ease';
        document.body.style.opacity = '0';
        document.body.style.transform = 'scale(1.03)';
      `).catch(() => {});
    } catch (_) {}

    setTimeout(() => {
      try {
        if (!win.isDestroyed()) {
          win.contentView.removeChildView(view);
        }
      } catch (_) {}
      win.off('resize', updateBounds);
    }, 650);
  };

  // 触发首轮就绪检查
  setTimeout(checkAndDismiss, MIN_DISPLAY_TIME);
  // 最大保底强制执行
  setTimeout(() => {
    if (!isRemoved) checkAndDismiss();
  }, MAX_TIMEOUT);
}
