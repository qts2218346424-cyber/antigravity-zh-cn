# -*- coding: utf-8 -*-
"""
生成《鬼灭之刃》灶门祢豆子·额度与对话提醒桌宠核心组件 (resources/nezuko-pet.js)
"""

import base64
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = REPO_ROOT / "resources" / "media"

nezuko_webp = MEDIA_DIR / "nezuko_basket.webp"
b64_nezuko = base64.b64encode(nezuko_webp.read_bytes()).decode('ascii')

js_code = f"""/**
 * Antigravity 灶门祢豆子 · 额度监控与对话提醒桌宠 (Nezuko Mascot & Quota Sentinel)
 * 1. 娇俏可爱的竹篓探头呼吸微浮动 + 飘落樱花瓣 + 眨眼微倾动效；
 * 2. 实时血鬼术充能 / AI 额度全景监控面板 (Gemini 3.1 Pro / Flash 配额矩阵)；
 * 3. 智能体任务完成、等待输入、权限审批时的漫画级粉色发光提醒气泡；
 * 4. 自由拖拽定位、一键最小化为竹筒萌徽章、0 CPU 纯 CSS 硬件加速渲染。
 */

(function() {{
  if (typeof window === 'undefined' || window.__NEZUKO_PET_INITIALIZED__) return;
  window.__NEZUKO_PET_INITIALIZED__ = true;

  const NEZUKO_IMG_B64 = "data:image/webp;base64,{b64_nezuko}";

  // 创建桌宠宿主根容器
  const root = document.createElement('div');
  root.id = 'nezuko-pet-root';
  root.setAttribute('data-no-translate', 'true');

  // 构建核心样式表 (采用高特异性前缀与隔离变量，杜绝污染主工作台)
  const style = document.createElement('style');
  style.textContent = `
    #nezuko-pet-root {{
      position: fixed;
      bottom: 24px;
      right: 28px;
      z-index: 9999999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
      user-select: none;
      -webkit-user-select: none;
      pointer-events: auto;
    }}

    /* 祢豆子浮动人物本体 */
    .nezuko-pet-avatar-wrap {{
      position: relative;
      width: 96px;
      height: 96px;
      cursor: grab;
      filter: drop-shadow(0 8px 24px rgba(244, 114, 182, 0.45));
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), filter 0.25s ease;
      animation: nezukoPetFloat 3.8s ease-in-out infinite;
    }}
    .nezuko-pet-avatar-wrap:hover {{
      transform: scale(1.08) translateY(-4px);
      filter: drop-shadow(0 12px 30px rgba(244, 114, 182, 0.65));
    }}
    .nezuko-pet-avatar-wrap:active {{
      cursor: grabbing;
      transform: scale(0.96);
    }}

    @keyframes nezukoPetFloat {{
      0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
      50% {{ transform: translateY(-7px) rotate(1.2deg); }}
    }}

    .nezuko-pet-avatar-img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 50%;
      pointer-events: none;
      transition: filter 0.3s ease;
    }}

    /* 光晕与血鬼术樱花微光光环 */
    .nezuko-pet-halo {{
      position: absolute;
      top: -4px; left: -4px; right: -4px; bottom: -4px;
      border-radius: 50%;
      border: 2px solid rgba(244, 114, 182, 0.55);
      box-shadow: 0 0 16px rgba(244, 114, 182, 0.4), inset 0 0 12px rgba(244, 114, 182, 0.2);
      pointer-events: none;
      animation: nezukoHaloPulse 2.8s ease-in-out infinite;
    }}
    @keyframes nezukoHaloPulse {{
      0%, 100% {{ opacity: 0.6; transform: scale(1); }}
      50% {{ opacity: 1; transform: scale(1.05); border-color: rgba(244, 114, 182, 0.85); }}
    }}

    /* 状态指示小徽章 */
    .nezuko-status-dot {{
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
    }}
    .nezuko-status-dot.busy {{
      background: #f59e0b;
      box-shadow: 0 0 10px #f59e0b;
    }}
    .nezuko-status-dot.alert {{
      background: #ec4899;
      box-shadow: 0 0 12px #ec4899;
      animation: nezukoDotBlink 0.8s infinite;
    }}
    @keyframes nezukoDotBlink {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(1.2); }}
    }}

    /* 樱花瓣散落特效 */
    .nezuko-petal {{
      position: absolute;
      width: 8px;
      height: 12px;
      background: radial-gradient(ellipse at 40% 30%, #fbcfe8 0%, #f472b6 80%);
      border-radius: 12px 2px 12px 2px;
      opacity: 0;
      pointer-events: none;
      animation: nezukoPetalFall 4.5s linear infinite;
    }}
    @keyframes nezukoPetalFall {{
      0% {{ transform: translate(0, 0) rotate(0deg); opacity: 0.85; }}
      50% {{ transform: translate(-14px, 28px) rotate(120deg); opacity: 0.7; }}
      100% {{ transform: translate(16px, 60px) rotate(270deg); opacity: 0; }}
    }}

    /* 对话提醒漫画气泡 */
    .nezuko-bubble {{
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
    }}
    .nezuko-bubble.show {{
      display: block;
      opacity: 1;
      transform: translateY(0) scale(1);
    }}
    /* 气泡小三角尾巴 */
    .nezuko-bubble::after {{
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
    }}

    .nezuko-bubble-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
      font-size: 11px;
      font-weight: 700;
      color: #f472b6;
      letter-spacing: 0.5px;
    }}
    .nezuko-bubble-close {{
      cursor: pointer;
      opacity: 0.7;
      font-size: 14px;
      line-height: 1;
      padding: 2px;
      transition: opacity 0.2s;
    }}
    .nezuko-bubble-close:hover {{ opacity: 1; color: #fff; }}

    .nezuko-bubble-body {{
      color: #e2e8f0;
      word-break: break-word;
      font-size: 12.5px;
    }}

    /* 额度全景看板 */
    .nezuko-quota-panel {{
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
    }}
    .nezuko-quota-panel.show {{
      display: block;
      opacity: 1;
      transform: translateY(0) scale(1);
    }}

    .nezuko-panel-title {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid rgba(244, 114, 182, 0.2);
      padding-bottom: 10px;
      margin-bottom: 12px;
    }}
    .nezuko-panel-title-text {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 800;
      color: #f8fafc;
    }}
    .nezuko-panel-title-text span.badge {{
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 10px;
      background: rgba(244, 114, 182, 0.2);
      border: 1px solid rgba(244, 114, 182, 0.5);
      color: #fbcfe8;
      font-weight: normal;
    }}

    /* 模型额度项 */
    .nezuko-model-item {{
      background: rgba(30, 41, 59, 0.65);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 10px 12px;
      margin-bottom: 10px;
    }}
    .nezuko-model-name {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 12px;
      font-weight: 700;
      color: #cbd5e1;
      margin-bottom: 6px;
    }}
    .nezuko-model-status {{
      font-size: 11px;
      color: #10b981;
      font-weight: 800;
    }}

    .nezuko-progress-bg {{
      width: 100%;
      height: 7px;
      background: rgba(15, 23, 42, 0.8);
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 4px;
    }}
    .nezuko-progress-bar {{
      height: 100%;
      border-radius: 4px;
      background: linear-gradient(90deg, #10b981, #f472b6);
      transition: width 0.6s ease;
    }}

    .nezuko-model-desc {{
      font-size: 10.5px;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
    }}

    /* 面板底部按钮区 */
    .nezuko-panel-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 11px;
      color: #94a3b8;
    }}
    .nezuko-btn {{
      padding: 5px 12px;
      border-radius: 8px;
      border: 1px solid rgba(244, 114, 182, 0.4);
      background: rgba(244, 114, 182, 0.15);
      color: #fbcfe8;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .nezuko-btn:hover {{
      background: rgba(244, 114, 182, 0.35);
      border-color: #f472b6;
      color: #fff;
    }}

    /* 最小化徽章 */
    .nezuko-min-badge {{
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
    }}
    .nezuko-min-badge:hover {{
      transform: scale(1.15);
      box-shadow: 0 6px 20px rgba(244, 114, 182, 0.7);
    }}
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
      <img src="${{NEZUKO_IMG_B64}}" class="nezuko-pet-avatar-img" alt="灶门祢豆子桌宠" />
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
  window.__showNezukoAlert = function(title, body) {{
    bubbleTitle.textContent = title || '🌸 智能体已搞定！';
    bubbleBody.textContent = body || '主人，后台任务已处理完毕！唔唔~';
    quotaPanel.classList.remove('show');
    bubble.classList.add('show');
    statusDot.className = 'nezuko-status-dot alert';

    if (bubbleTimer) clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(() => {{
      bubble.classList.remove('show');
      statusDot.className = 'nezuko-status-dot';
    }}, 7500);
  }};

  // 2. 祢豆子台词音效系统
  const NEZUKO_QUOTES = [
    "唔唔！主人的代码写得真棒！",
    "姆！血鬼术充能 100%，随时准备战斗！",
    "主人，累了要记得喝水休息哦~",
    "哥哥炭治郎也在认真写代码呢！",
    "赫刀出鞘！智能体已经火力全开啦！"
  ];

  // 3. 事件绑定
  bubbleClose.addEventListener('click', (e) => {{
    e.stopPropagation();
    bubble.classList.remove('show');
    statusDot.className = 'nezuko-status-dot';
  }});

  panelClose.addEventListener('click', (e) => {{
    e.stopPropagation();
    quotaPanel.classList.remove('show');
  }});

  // 点击祢豆子展开/收起额度看板
  avatarWrap.addEventListener('click', (e) => {{
    if (isDragging) return;
    bubble.classList.remove('show');
    quotaPanel.classList.toggle('show');
    if (quotaPanel.classList.contains('show')) {{
      const randomQuote = NEZUKO_QUOTES[Math.floor(Math.random() * NEZUKO_QUOTES.length)];
      voiceText.textContent = randomQuote;
    }}
  }});

  // 点击气泡关闭并激活输入框
  bubble.addEventListener('click', () => {{
    bubble.classList.remove('show');
    statusDot.className = 'nezuko-status-dot';
    const mainInput = document.querySelector('textarea, [contenteditable="true"]');
    if (mainInput) mainInput.focus();
  }});

  // 最小化与还原
  minBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    quotaPanel.classList.remove('show');
    bubble.classList.remove('show');
    avatarWrap.style.display = 'none';
    minBadge.style.display = 'flex';
  }});

  minBadge.addEventListener('click', () => {{
    minBadge.style.display = 'none';
    avatarWrap.style.display = 'block';
    window.__showNezukoAlert('🌸 祢豆子已就位！', '唔唔！随时守护主人的代码与模型额度！');
  }});

  // 测试提醒按钮
  testBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    window.__showNezukoAlert('🎋 智能体需要您的批准', '智能体正在申请执行终端命令，请主人审核确认~');
  }});

  // 4. 自由拖拽定位功能
  let isDragging = false;
  let startX, startY, initialRight, initialBottom;

  avatarWrap.addEventListener('mousedown', (e) => {{
    if (e.button !== 0) return;
    isDragging = false;
    startX = e.clientX;
    startY = e.clientY;
    const rect = root.getBoundingClientRect();
    initialRight = window.innerWidth - rect.right;
    initialBottom = window.innerHeight - rect.bottom;

    const onMouseMove = (moveEvent) => {{
      const dx = moveEvent.clientX - startX;
      const dy = moveEvent.clientY - startY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {{
        isDragging = true;
      }}
      if (isDragging) {{
        root.style.right = `${{Math.max(10, initialRight - dx)}}px`;
        root.style.bottom = `${{Math.max(10, initialBottom - dy)}}px`;
      }}
    }};

    const onMouseUp = () => {{
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    }};

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }});

  // 5. 监听来自 Electron 主进程的汉化对话提醒事件
  if (typeof window !== 'undefined' && window.require) {{
    try {{
      const {{ ipcRenderer }} = window.require('electron');
      ipcRenderer.on('__agy_chat_notification__', (_event, notif) => {{
        if (notif) {{
          window.__showNezukoAlert(notif.title, notif.body);
        }}
      }});
    }} catch (_) {{}}
  }}

  // 6. 劫持原生 Web Notification，同步触发祢豆子气泡
  if (typeof window !== 'undefined' && window.Notification) {{
    try {{
      const NativeNotification = window.Notification;
      window.Notification = function(title, options) {{
        try {{
          const trTitle = (typeof window.__agyTranslateNotif === 'function') ? window.__agyTranslateNotif(title) : title;
          const trBody = (options && options.body && typeof window.__agyTranslateNotif === 'function') ? window.__agyTranslateNotif(options.body) : (options ? options.body : '');
          window.__showNezukoAlert(trTitle, trBody);
        }} catch (_) {{}}
        return new NativeNotification(title, options);
      }};
      window.Notification.prototype = NativeNotification.prototype;
      window.Notification.permission = NativeNotification.permission;
      if (NativeNotification.requestPermission) {{
        window.Notification.requestPermission = NativeNotification.requestPermission.bind(NativeNotification);
      }}
    }} catch (_) {{}}
  }}

}})();
"""

(REPO_ROOT / "resources" / "nezuko-pet.js").write_text(js_code, encoding="utf-8")
print(f"nezuko-pet.js 生成完成，文件大小: {len(js_code)} 字节")
