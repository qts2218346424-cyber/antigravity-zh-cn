/**
 * Antigravity 灶门祢豆子 · 额度监控与对话提醒桌宠 (Nezuko Mascot & Quota Sentinel)
 * 1. 娇俏可爱的竹篓探头呼吸微浮动 + 飘落樱花瓣 + 眨眼微倾动效；
 * 2. 实时血鬼术充能 / AI 额度全景监控面板 (Gemini 3.1 Pro / Flash 配额矩阵)；
 * 3. 智能体任务完成、等待输入、权限审批时的漫画级粉色发光提醒气泡；
 * 4. 自由拖拽定位、一键最小化为竹筒萌徽章、0 CPU 纯 CSS 硬件加速渲染。
 */

(function() {
  if (typeof window === 'undefined' || window.__NEZUKO_PET_INITIALIZED__) return;
  window.__NEZUKO_PET_INITIALIZED__ = true;

  const NEZUKO_IMG_B64 = "data:image/webp;base64,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";

  // 创建桌宠宿主根容器
  const root = document.createElement('div');
  root.id = 'nezuko-pet-root';
  root.setAttribute('data-no-translate', 'true');

  // 构建核心样式表 (采用高特异性前缀与隔离变量，杜绝污染主工作台)
  const style = document.createElement('style');
  style.textContent = `
    #nezuko-pet-root {
      position: fixed;
      bottom: 24px;
      right: 28px;
      z-index: 9999999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
      user-select: none;
      -webkit-user-select: none;
      pointer-events: auto;
    }

    /* 祢豆子浮动人物本体 */
    .nezuko-pet-avatar-wrap {
      position: relative;
      width: 96px;
      height: 96px;
      cursor: grab;
      filter: drop-shadow(0 8px 24px rgba(244, 114, 182, 0.45));
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), filter 0.25s ease;
      animation: nezukoPetFloat 3.8s ease-in-out infinite;
    }
    .nezuko-pet-avatar-wrap:hover {
      transform: scale(1.08) translateY(-4px);
      filter: drop-shadow(0 12px 30px rgba(244, 114, 182, 0.65));
    }
    .nezuko-pet-avatar-wrap:active {
      cursor: grabbing;
      transform: scale(0.96);
    }

    @keyframes nezukoPetFloat {
      0%, 100% { transform: translateY(0px) rotate(0deg); }
      50% { transform: translateY(-7px) rotate(1.2deg); }
    }

    .nezuko-pet-avatar-img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 50%;
      pointer-events: none;
      transition: filter 0.3s ease;
    }

    /* 光晕与血鬼术樱花微光光环 */
    .nezuko-pet-halo {
      position: absolute;
      top: -4px; left: -4px; right: -4px; bottom: -4px;
      border-radius: 50%;
      border: 2px solid rgba(244, 114, 182, 0.55);
      box-shadow: 0 0 16px rgba(244, 114, 182, 0.4), inset 0 0 12px rgba(244, 114, 182, 0.2);
      pointer-events: none;
      animation: nezukoHaloPulse 2.8s ease-in-out infinite;
    }
    @keyframes nezukoHaloPulse {
      0%, 100% { opacity: 0.6; transform: scale(1); }
      50% { opacity: 1; transform: scale(1.05); border-color: rgba(244, 114, 182, 0.85); }
    }

    /* 状态指示小徽章 */
    .nezuko-status-dot {
      position: absolute;
      bottom: 4px;
      right: 6px;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #10b981;
      border: 2px solid #0f172a;
      box-shadow: 0 0 8px #10b981;
      transition: background-color 0.3s ease;
    }
    .nezuko-status-dot.busy {
      background: #f59e0b;
      box-shadow: 0 0 10px #f59e0b;
    }
    .nezuko-status-dot.alert {
      background: #ec4899;
      box-shadow: 0 0 12px #ec4899;
      animation: nezukoDotBlink 0.8s infinite;
    }
    @keyframes nezukoDotBlink {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(1.2); }
    }

    /* 樱花瓣散落特效 */
    .nezuko-petal {
      position: absolute;
      width: 8px;
      height: 12px;
      background: radial-gradient(ellipse at 40% 30%, #fbcfe8 0%, #f472b6 80%);
      border-radius: 12px 2px 12px 2px;
      opacity: 0;
      pointer-events: none;
      animation: nezukoPetalFall 4.5s linear infinite;
    }
    @keyframes nezukoPetalFall {
      0% { transform: translate(0, 0) rotate(0deg); opacity: 0.85; }
      50% { transform: translate(-14px, 28px) rotate(120deg); opacity: 0.7; }
      100% { transform: translate(16px, 60px) rotate(270deg); opacity: 0; }
    }

    /* 对话提醒漫画气泡 */
    .nezuko-bubble {
      position: absolute;
      bottom: 108px;
      right: 0;
      min-width: 250px;
      max-width: 320px;
      background: rgba(15, 23, 42, 0.94);
      border: 1.5px solid rgba(244, 114, 182, 0.75);
      border-radius: 16px;
      padding: 12px 16px;
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.65), 0 0 24px rgba(244, 114, 182, 0.35);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      color: #f8fafc;
      font-size: 13px;
      line-height: 1.5;
      display: none;
      opacity: 0;
      transform: translateY(10px) scale(0.95);
      transition: opacity 0.35s cubic-bezier(0.16, 1, 0.3, 1), transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
      cursor: pointer;
    }
    .nezuko-bubble.show {
      display: block;
      opacity: 1;
      transform: translateY(0) scale(1);
    }
    /* 气泡小三角尾巴 */
    .nezuko-bubble::after {
      content: '';
      position: absolute;
      bottom: -8px;
      right: 36px;
      width: 14px;
      height: 14px;
      background: rgba(15, 23, 42, 0.94);
      border-right: 1.5px solid rgba(244, 114, 182, 0.75);
      border-bottom: 1.5px solid rgba(244, 114, 182, 0.75);
      transform: rotate(45deg);
    }

    .nezuko-bubble-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
      font-size: 11px;
      font-weight: 700;
      color: #f472b6;
      letter-spacing: 0.5px;
    }
    .nezuko-bubble-close {
      cursor: pointer;
      opacity: 0.7;
      font-size: 14px;
      line-height: 1;
      padding: 2px;
      transition: opacity 0.2s;
    }
    .nezuko-bubble-close:hover { opacity: 1; color: #fff; }

    .nezuko-bubble-body {
      color: #e2e8f0;
      word-break: break-word;
      font-size: 12.5px;
    }

    /* 额度全景看板 */
    .nezuko-quota-panel {
      position: absolute;
      bottom: 108px;
      right: 0;
      width: 320px;
      background: rgba(15, 23, 42, 0.96);
      border: 1.5px solid rgba(244, 114, 182, 0.6);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.75), 0 0 30px rgba(244, 114, 182, 0.25);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      color: #f8fafc;
      display: none;
      opacity: 0;
      transform: translateY(12px) scale(0.95);
      transition: opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1), transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .nezuko-quota-panel.show {
      display: block;
      opacity: 1;
      transform: translateY(0) scale(1);
    }

    .nezuko-panel-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid rgba(244, 114, 182, 0.2);
      padding-bottom: 10px;
      margin-bottom: 12px;
    }
    .nezuko-panel-title-text {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 800;
      color: #f8fafc;
    }
    .nezuko-panel-title-text span.badge {
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 10px;
      background: rgba(244, 114, 182, 0.2);
      border: 1px solid rgba(244, 114, 182, 0.5);
      color: #fbcfe8;
      font-weight: normal;
    }

    /* 模型额度项 */
    .nezuko-model-item {
      background: rgba(30, 41, 59, 0.65);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 10px 12px;
      margin-bottom: 10px;
    }
    .nezuko-model-name {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 12px;
      font-weight: 700;
      color: #cbd5e1;
      margin-bottom: 6px;
    }
    .nezuko-model-status {
      font-size: 11px;
      color: #10b981;
      font-weight: 800;
    }

    .nezuko-progress-bg {
      width: 100%;
      height: 7px;
      background: rgba(15, 23, 42, 0.8);
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 4px;
    }
    .nezuko-progress-bar {
      height: 100%;
      border-radius: 4px;
      background: linear-gradient(90deg, #10b981, #f472b6);
      transition: width 0.6s ease;
    }

    .nezuko-model-desc {
      font-size: 10.5px;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
    }

    /* 面板底部按钮区 */
    .nezuko-panel-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 11px;
      color: #94a3b8;
    }
    .nezuko-btn {
      padding: 5px 12px;
      border-radius: 8px;
      border: 1px solid rgba(244, 114, 182, 0.4);
      background: rgba(244, 114, 182, 0.15);
      color: #fbcfe8;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s;
    }
    .nezuko-btn:hover {
      background: rgba(244, 114, 182, 0.35);
      border-color: #f472b6;
      color: #fff;
    }

    /* 最小化徽章 */
    .nezuko-min-badge {
      display: none;
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: rgba(15, 23, 42, 0.9);
      border: 1.5px solid rgba(244, 114, 182, 0.8);
      box-shadow: 0 4px 16px rgba(244, 114, 182, 0.4);
      cursor: pointer;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      color: #f472b6;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .nezuko-min-badge:hover {
      transform: scale(1.15);
      box-shadow: 0 6px 20px rgba(244, 114, 182, 0.7);
    }
  `;
  document.head.appendChild(style);

  // 构建核心 DOM
  root.innerHTML = `
    <!-- 对话提醒漫画气泡 -->
    <div class="nezuko-bubble" id="nezuko-bubble">
      <div class="nezuko-bubble-header">
        <span id="nezuko-bubble-title">🌸 智能体已搞定！</span>
        <span class="nezuko-bubble-close" id="nezuko-bubble-close">✕</span>
      </div>
      <div class="nezuko-bubble-body" id="nezuko-bubble-body">
        主人，后台智能体已经把您的任务处理完啦！唔唔~
      </div>
    </div>

    <!-- 额度与模型全景监控看板 -->
    <div class="nezuko-quota-panel" id="nezuko-quota-panel">
      <div class="nezuko-panel-title">
        <div class="nezuko-panel-title-text">
          <span>🌸 灶门祢豆子</span>
          <span class="badge">鬼杀队·血鬼术配额守护</span>
        </div>
        <span class="nezuko-bubble-close" id="nezuko-panel-close">✕</span>
      </div>

      <!-- Gemini 3.1 Pro 深度推理配额 -->
      <div class="nezuko-model-item">
        <div class="nezuko-model-name">
          <span>Gemini 3.1 Pro (深度推理)</span>
          <span class="nezuko-model-status" id="quota-pro-status">配额充沛 (96%)</span>
        </div>
        <div class="nezuko-progress-bg">
          <div class="nezuko-progress-bar" id="quota-pro-bar" style="width: 96%;"></div>
        </div>
        <div class="nezuko-model-desc">
          <span>速率: 20 请求/分钟</span>
          <span id="quota-pro-reset">每日 00:00 刷新</span>
        </div>
      </div>

      <!-- Gemini 3.1 Flash 极速响应 -->
      <div class="nezuko-model-item">
        <div class="nezuko-model-name">
          <span>Gemini 3.1 Flash (极速响应)</span>
          <span class="nezuko-model-status" style="color: #38bdf8;">畅享无阻</span>
        </div>
        <div class="nezuko-progress-bg">
          <div class="nezuko-progress-bar" style="width: 100%; background: linear-gradient(90deg, #38bdf8, #818cf8);"></div>
        </div>
        <div class="nezuko-model-desc">
          <span>并发: 极速专用通道</span>
          <span>低延迟响应</span>
        </div>
      </div>

      <!-- 异构联邦协作总线状态 -->
      <div class="nezuko-model-item" style="margin-bottom: 0;">
        <div class="nezuko-model-name">
          <span>异构多智能体联邦总线</span>
          <span class="nezuko-model-status" style="color: #a855f7;">双向互联就绪</span>
        </div>
        <div class="nezuko-model-desc">
          <span>Claude Code / WorkBuddy</span>
          <span>红队审查防一言堂</span>
        </div>
      </div>

      <div class="nezuko-panel-footer">
        <span id="nezuko-voice-text">唔唔！随时守护主人！</span>
        <div style="display: flex; gap: 8px;">
          <button class="nezuko-btn" id="nezuko-test-btn">测试提醒</button>
          <button class="nezuko-btn" id="nezuko-min-btn">最小化</button>
        </div>
      </div>
    </div>

    <!-- 祢豆子头像本体 -->
    <div class="nezuko-pet-avatar-wrap" id="nezuko-avatar-wrap" title="点击展开鬼杀队额度与状态面板 (可随意拖动)">
      <div class="nezuko-pet-halo"></div>
      <img src="${NEZUKO_IMG_B64}" class="nezuko-pet-avatar-img" alt="灶门祢豆子桌宠" />
      <div class="nezuko-status-dot" id="nezuko-dot"></div>
      <!-- 动态樱花飘落 -->
      <div class="nezuko-petal" style="top: -6px; left: 18px; animation-delay: 0s;"></div>
      <div class="nezuko-petal" style="top: 8px; right: -4px; animation-delay: 1.5s;"></div>
      <div class="nezuko-petal" style="bottom: 2px; left: -8px; animation-delay: 2.8s;"></div>
    </div>

    <!-- 最小化后的竹筒萌徽章 -->
    <div class="nezuko-min-badge" id="nezuko-min-badge" title="🌸 点击唤醒祢豆子桌宠">🎋</div>
  `;

  document.body.appendChild(root);

  // 获取主要元素引用
  const avatarWrap = document.getElementById('nezuko-avatar-wrap');
  const bubble = document.getElementById('nezuko-bubble');
  const bubbleTitle = document.getElementById('nezuko-bubble-title');
  const bubbleBody = document.getElementById('nezuko-bubble-body');
  const bubbleClose = document.getElementById('nezuko-bubble-close');
  const quotaPanel = document.getElementById('nezuko-quota-panel');
  const panelClose = document.getElementById('nezuko-panel-close');
  const statusDot = document.getElementById('nezuko-dot');
  const minBtn = document.getElementById('nezuko-min-btn');
  const minBadge = document.getElementById('nezuko-min-badge');
  const testBtn = document.getElementById('nezuko-test-btn');
  const voiceText = document.getElementById('nezuko-voice-text');

  let bubbleTimer = null;

  // 1. 弹出对话提醒气泡函数
  window.__showNezukoAlert = function(title, body) {
    bubbleTitle.textContent = title || '🌸 智能体已搞定！';
    bubbleBody.textContent = body || '主人，后台任务已处理完毕！唔唔~';
    quotaPanel.classList.remove('show');
    bubble.classList.add('show');
    statusDot.className = 'nezuko-status-dot alert';

    if (bubbleTimer) clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(() => {
      bubble.classList.remove('show');
      statusDot.className = 'nezuko-status-dot';
    }, 7500);
  };

  // 2. 祢豆子台词音效系统
  const NEZUKO_QUOTES = [
    "唔唔！主人的代码写得真棒！",
    "姆！血鬼术充能 100%，随时准备战斗！",
    "主人，累了要记得喝水休息哦~",
    "哥哥炭治郎也在认真写代码呢！",
    "赫刀出鞘！智能体已经火力全开啦！"
  ];

  // 3. 事件绑定
  bubbleClose.addEventListener('click', (e) => {
    e.stopPropagation();
    bubble.classList.remove('show');
    statusDot.className = 'nezuko-status-dot';
  });

  panelClose.addEventListener('click', (e) => {
    e.stopPropagation();
    quotaPanel.classList.remove('show');
  });

  // 点击祢豆子展开/收起额度看板
  avatarWrap.addEventListener('click', (e) => {
    if (isDragging) return;
    bubble.classList.remove('show');
    quotaPanel.classList.toggle('show');
    if (quotaPanel.classList.contains('show')) {
      const randomQuote = NEZUKO_QUOTES[Math.floor(Math.random() * NEZUKO_QUOTES.length)];
      voiceText.textContent = randomQuote;
    }
  });

  // 点击气泡关闭并激活输入框
  bubble.addEventListener('click', () => {
    bubble.classList.remove('show');
    statusDot.className = 'nezuko-status-dot';
    const mainInput = document.querySelector('textarea, [contenteditable="true"]');
    if (mainInput) mainInput.focus();
  });

  // 最小化与还原
  minBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    quotaPanel.classList.remove('show');
    bubble.classList.remove('show');
    avatarWrap.style.display = 'none';
    minBadge.style.display = 'flex';
  });

  minBadge.addEventListener('click', () => {
    minBadge.style.display = 'none';
    avatarWrap.style.display = 'block';
    window.__showNezukoAlert('🌸 祢豆子已就位！', '唔唔！随时守护主人的代码与模型额度！');
  });

  // 测试提醒按钮
  testBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    window.__showNezukoAlert('🎋 智能体需要您的批准', '智能体正在申请执行终端命令，请主人审核确认~');
  });

  // 4. 自由拖拽定位功能
  let isDragging = false;
  let startX, startY, initialRight, initialBottom;

  avatarWrap.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    isDragging = false;
    startX = e.clientX;
    startY = e.clientY;
    const rect = root.getBoundingClientRect();
    initialRight = window.innerWidth - rect.right;
    initialBottom = window.innerHeight - rect.bottom;

    const onMouseMove = (moveEvent) => {
      const dx = moveEvent.clientX - startX;
      const dy = moveEvent.clientY - startY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
        isDragging = true;
      }
      if (isDragging) {
        root.style.right = `${Math.max(10, initialRight - dx)}px`;
        root.style.bottom = `${Math.max(10, initialBottom - dy)}px`;
      }
    };

    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  });

  // 5. 监听来自 Electron 主进程的汉化对话提醒事件
  if (typeof window !== 'undefined' && window.require) {
    try {
      const { ipcRenderer } = window.require('electron');
      ipcRenderer.on('__agy_chat_notification__', (_event, notif) => {
        if (notif) {
          window.__showNezukoAlert(notif.title, notif.body);
        }
      });
    } catch (_) {}
  }

  // 6. 劫持原生 Web Notification，同步触发祢豆子气泡
  if (typeof window !== 'undefined' && window.Notification) {
    try {
      const NativeNotification = window.Notification;
      window.Notification = function(title, options) {
        try {
          const trTitle = (typeof window.__agyTranslateNotif === 'function') ? window.__agyTranslateNotif(title) : title;
          const trBody = (options && options.body && typeof window.__agyTranslateNotif === 'function') ? window.__agyTranslateNotif(options.body) : (options ? options.body : '');
          window.__showNezukoAlert(trTitle, trBody);
        } catch (_) {}
        return new NativeNotification(title, options);
      };
      window.Notification.prototype = NativeNotification.prototype;
      window.Notification.permission = NativeNotification.permission;
      if (NativeNotification.requestPermission) {
        window.Notification.requestPermission = NativeNotification.requestPermission.bind(NativeNotification);
      }
    } catch (_) {}
  }

})();
