# -*- coding: utf-8 -*-
"""
生成双角色桌宠系统：
1. 【🌸 灶门祢豆子】(鬼灭之刃大正和风 + 2D骨骼解剖分肢动画 + 原生配额看板)
2. 【👑 小王子 (B612星球)】(浪漫法国童话 + 随风飘扬长围巾 + 玻璃罩红玫瑰 + 12句中法双语哲思名言定时气泡)
3. 【🎵 深度对接电脑 QQ 音乐客户端】：
   - 全局媒体键无缝对接 (播放/暂停、上一曲、下一曲)；
   - 一键唤醒 QQ 音乐客户端；
   - 动态声波柱与唱片旋转联动；
   - 兼具纯正和风治愈八音盒双模式。
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

# 1. 祢豆子骨骼切片
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

# 2. 小王子全身立绘
prince_webp = MEDIA_DIR / "little_prince_pet.webp"
b64_prince = base64.b64encode(prince_webp.read_bytes()).decode('ascii')

js_code = f"""/**
 * Antigravity 异构多角色桌宠引擎 5.0 (Dual-Pet & QQ Music Bridge)
 * 1. 深度对接电脑上的 QQ 音乐客户端 (播放/暂停、上一曲、下一曲、一键唤醒)
 * 2. 角色 1：🌸 灶门祢豆子 (2D 骨骼分肢动力学 + 全局和风主题 + 原生配额看板)
 * 3. 角色 2：👑 小王子 (B612星球治愈系 + 随风飘扬围巾 + 玫瑰 + 12句中法双语名言定期气泡)
 * 4. 自由一键切换中枢 + 本地记忆
 */

(function() {{
  if (typeof window === 'undefined' || window.__NEZUKO_PET_INITIALIZED__) return;
  window.__NEZUKO_PET_INITIALIZED__ = true;

  const NEZUKO_HEAD = "data:image/webp;base64,{b64_nezuko_parts['head']}";
  const NEZUKO_TORSO = "data:image/webp;base64,{b64_nezuko_parts['torso']}";
  const NEZUKO_ARM_L = "data:image/webp;base64,{b64_nezuko_parts['arm_l']}";
  const NEZUKO_ARM_R = "data:image/webp;base64,{b64_nezuko_parts['arm_r']}";
  const NEZUKO_LEG_L = "data:image/webp;base64,{b64_nezuko_parts['leg_l']}";
  const NEZUKO_LEG_R = "data:image/webp;base64,{b64_nezuko_parts['leg_r']}";

  const PRINCE_IMG = "data:image/webp;base64,{b64_prince}";

  // ==========================================
  // 一、QQ 音乐客户端系统级对接遥控引擎
  // ==========================================
  class QQMusicBridgeEngine {{
    constructor() {{
      this.mode = 'qqmusic'; // 'qqmusic' | 'synth'
      this.isPlaying = false;
      this.ipc = null;
      this.initIPC();
    }}

    initIPC() {{
      try {{
        if (typeof window !== 'undefined' && window.require) {{
          const electron = window.require('electron');
          if (electron && electron.ipcRenderer) {{
            this.ipc = electron.ipcRenderer;
          }}
        }}
      }} catch (_) {{}}
    }}

    sendCommand(cmd) {{
      if (this.ipc) {{
        this.ipc.send('__agy_media_command__', cmd);
      }} else {{
        // Web 浏览器端降级：尝试调用协议
        if (cmd === 'open_qq') {{
          try {{ window.location.href = 'qqmusic://'; }} catch (_) {{}}
        }}
      }}
    }}

    playPause() {{
      this.isPlaying = !this.isPlaying;
      this.sendCommand('play_pause');
      triggerMusicBeat();
      updateMusicUI();
    }}

    nextTrack() {{
      this.isPlaying = true;
      this.sendCommand('next');
      triggerMusicBeat();
      updateMusicUI();
    }}

    prevTrack() {{
      this.isPlaying = true;
      this.sendCommand('prev');
      triggerMusicBeat();
      updateMusicUI();
    }}

    wakeUpQQMusic() {{
      this.sendCommand('open_qq');
    }}
  }}

  const qqBridge = new QQMusicBridgeEngine();

  // ==========================================
  // 二、《小王子》12 句中法双语经典哲思名言库
  // ==========================================
  const LITTLE_PRINCE_QUOTES = [
    {{
      zh: "真正重要的东西，用眼睛是看不见的，只有用心才能看清。",
      fr: "L'essentiel est invisible pour les yeux.",
      tag: "🦊 狐狸的秘密"
    }},
    {{
      zh: "如果你说你在下午四点来，从三点开始，我就开始感觉很快乐。",
      fr: "Si tu viens à quatre heures de l'après-midi, dès trois heures je commencerai d'être heureux.",
      tag: "🦊 期待的幸福"
    }},
    {{
      zh: "你在你的玫瑰花身上耗费的时间，使得你的玫瑰花变得如此重要。",
      fr: "C'est le temps que tu as perdu pour ta rose qui fait ta rose si importante.",
      tag: "🌹 爱的驯养"
    }},
    {{
      zh: "星星发亮，是为了让每一个人有一天都能找到属于自己的星星。",
      fr: "Les étoiles sont éclairées pour que chacun puisse un jour retrouver la sienne.",
      tag: "✨ 漫天繁星"
    }},
    {{
      zh: "所有的大人都曾经是小孩，虽然，只有少数的人记得。",
      fr: "Toutes les grandes personnes ont d'abord été des enfants.",
      tag: "👑 永恒的童心"
    }},
    {{
      zh: "天上的星星有亿万颗，唯独只有一颗星上开着我的花，只要仰望星空，就会感到幸福。",
      fr: "Si quelqu'un aime une fleur unique, cela suffit pour qu'il soit heureux.",
      tag: "🌟 独一无二"
    }},
    {{
      zh: "当你驯养了我，我们就会彼此需要。对我来说，你就是世界上唯一的。",
      fr: "Tu seras pour moi unique au monde. Je serai pour toi unique au monde.",
      tag: "🦊 羁绊与陪伴"
    }},
    {{
      zh: "一个人只有在感到悲伤的时候，才会喜欢看日落... ‘有一天，我看了四十四次日落。’",
      fr: "Un jour, j'ai vu le soleil se coucher quarante-quatre fois...",
      tag: "🌅 B612的黄昏"
    }},
    {{
      zh: "沙漠之所以美丽，是因为在某个角落，藏着一口清泉。",
      fr: "Ce qui embellit le désert, c'est qu'il cache un puits quelque part.",
      tag: "💧 心灵的甘泉"
    }},
    {{
      zh: "我就在其中的一颗星星上微笑着。当你夜晚仰望星空时，就好像所有的星星都在对你微笑。",
      fr: "Alors ce sera pour toi comme si riaient toutes les étoiles.",
      tag: "🌠 会笑的星星"
    }},
    {{
      zh: "审判自己比审判别人难得多。如果你能成功地审判自己，你就是真正的智者。",
      fr: "Il est bien plus difficile de se juger soi-même que de juger autrui.",
      tag: "🪐 国王的星球"
    }},
    {{
      zh: "我的那朵玫瑰花，比花园里五千朵玫瑰都要重要，因为我为她遮过风，听过她的抱怨与沉默。",
      fr: "Mais elle seule est plus importante que vous toutes, puisque c'est elle que j'ai arrosée.",
      tag: "🥀 守护的责任"
    }}
  ];

  function getActivePet() {{
    return localStorage.getItem('__agy_active_pet_character__') || 'nezuko';
  }}
  function setActivePet(name) {{
    localStorage.setItem('__agy_active_pet_character__', name);
  }}

  // ==========================================
  // 三、Antigravity 软件界面鬼灭和风全局主题
  // ==========================================
  const ideThemeStyle = document.createElement('style');
  ideThemeStyle.id = 'agy-demon-slayer-ide-theme';
  ideThemeStyle.textContent = `
    .part.activitybar, #workbench\\\\.parts\\\\.activitybar, .activitybar {{
      background: linear-gradient(180deg, #1f130e 0%, #150c09 100%) !important;
      border-right: 2px solid #c59b27 !important; position: relative !important;
    }}
    .part.activitybar::before, #workbench\\\\.parts\\\\.activitybar::before, .activitybar::before {{
      content: '' !important; position: absolute !important; top: 0 !important; left: 0 !important; bottom: 0 !important;
      width: 5px !important; background: repeating-linear-gradient(45deg, #2e7d32 0, #2e7d32 6px, #111 6px, #111 12px) !important;
      z-index: 10 !important;
    }}
    .activitybar .action-item.checked .action-label, .activitybar .action-item.active .action-label {{
      color: #ffd54f !important; filter: drop-shadow(0 0 6px rgba(255, 213, 79, 0.6)) !important;
    }}
    .part.sidebar, #workbench\\\\.parts\\\\.sidebar, .sidebar {{
      background: linear-gradient(135deg, rgba(28, 17, 13, 0.98) 0%, rgba(18, 10, 8, 0.99) 100%) !important;
      border-right: 1.5px solid rgba(197, 155, 39, 0.4) !important;
    }}
    .sidebar .title-label h2, .sidebar .pane-header .title {{ color: #ffd54f !important; font-weight: 700 !important; }}
    .part.statusbar, #workbench\\\\.parts\\\\.statusbar, .statusbar {{
      background: repeating-linear-gradient(45deg, #1b3820 0, #1b3820 8px, #111a13 8px, #111a13 16px) !important;
      border-top: 1.5px solid #c59b27 !important; color: #fff9c4 !important;
    }}
    .statusbar .statusbar-item a, .statusbar .statusbar-item {{ color: #fff9c4 !important; }}
    .part.titlebar, #workbench\\\\.parts\\\\.titlebar, .titlebar {{
      background: linear-gradient(90deg, #2b1711 0%, #1a0f0a 100%) !important; border-bottom: 1.5px solid #c59b27 !important;
    }}
    .titlebar .window-title {{ color: #ffd54f !important; font-weight: 600 !important; }}
    .tab.active {{
      background: linear-gradient(180deg, rgba(46, 26, 20, 0.9) 0%, #1f120d 100%) !important;
      border-top: 2.5px solid #f48fb1 !important; color: #fff !important;
    }}
    .monaco-scrollable-element .scrollbar .slider {{
      background: rgba(197, 155, 39, 0.45) !important; border-radius: 4px !important;
    }}
  `;

  function isIdeThemeEnabled() {{
    const val = localStorage.getItem('__agy_demon_slayer_ide_theme__');
    return val === null || val === 'true';
  }}
  function setIdeTheme(enabled) {{
    localStorage.setItem('__agy_demon_slayer_ide_theme__', enabled ? 'true' : 'false');
    if (enabled) {{
      if (!document.getElementById('agy-demon-slayer-ide-theme')) document.head.appendChild(ideThemeStyle);
    }} else {{
      const el = document.getElementById('agy-demon-slayer-ide-theme');
      if (el) el.remove();
    }}
  }}
  if (isIdeThemeEnabled()) document.head.appendChild(ideThemeStyle);

  // ==========================================
  // 四、模型配额中枢
  // ==========================================
  const defaultQuotaState = {{
    username: "qts2218346424@gmail.com",
    geminiWeeklyPct: 91,
    geminiWeeklyReset: "6 天 19 小时后重置",
    gemini5hPct: 72,
    gemini5hReset: "46 分钟后重置",
    claudeWeeklyPct: 100,
    claudeWeeklyReset: "7 天后重置",
    claude5hPct: 100,
    claude5hReset: "5 小时后重置",
    lastSynced: "刚刚"
  }};

  function loadUserQuota() {{
    try {{
      const saved = localStorage.getItem('__nezuko_model_quota_v2__');
      if (saved) return Object.assign({{}}, defaultQuotaState, JSON.parse(saved));
    }} catch (_) {{}}
    return Object.assign({{}}, defaultQuotaState);
  }}
  function saveUserQuota(state) {{
    try {{
      localStorage.setItem('__nezuko_model_quota_v2__', JSON.stringify(state));
    }} catch (_) {{}}
  }}
  let currentQuota = loadUserQuota();

  function sniffNativeQuotaFromDOM() {{
    try {{
      const textNodes = [];
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
      let node;
      while (node = walker.nextNode()) {{
        const txt = node.nodeValue.trim();
        if (txt.includes('每周剩余可用配额') || txt.includes('5 小时剩余可用配额') || txt.includes('Weekly limit')) {{
          textNodes.push(node);
        }}
      }}
      if (textNodes.length > 0) {{
        let updated = false;
        textNodes.forEach(tn => {{
          const parent = tn.parentElement;
          if (!parent) return;
          const container = parent.closest('.quota-section, div') || parent;
          const text = container.textContent || '';
          const matchWeekly = text.match(/每周剩余可用配额[^\\d]*(\\d+)%/);
          if (matchWeekly) {{
            currentQuota.geminiWeeklyPct = parseInt(matchWeekly[1], 10);
            updated = true;
          }}
          const match5h = text.match(/5\\s*小时剩余可用配额[^\\d]*(\\d+)%/);
          if (match5h) {{
            currentQuota.gemini5hPct = parseInt(match5h[1], 10);
            updated = true;
          }}
        }});
        if (updated) {{
          currentQuota.lastSynced = new Date().toLocaleTimeString('zh-CN', {{ hour12: false }});
          saveUserQuota(currentQuota);
          updateQuotaDisplay();
        }}
      }}
    }} catch (_) {{}}
  }}
  setInterval(sniffNativeQuotaFromDOM, 5000);

  // 节拍晃脑
  let beatTimer = null;
  function triggerMusicBeat() {{
    const headEl = document.getElementById('bone-head');
    const princeEl = document.getElementById('prince-avatar-body');
    if (headEl) {{
      headEl.classList.add('head-music-bob');
      if (beatTimer) clearTimeout(beatTimer);
      beatTimer = setTimeout(() => headEl.classList.remove('head-music-bob'), 400);
    }}
    if (princeEl) {{
      princeEl.classList.add('prince-music-bob');
      if (beatTimer) clearTimeout(beatTimer);
      beatTimer = setTimeout(() => princeEl.classList.remove('prince-music-bob'), 400);
    }}
  }}

  // ==========================================
  // 五、CSS 样式库
  // ==========================================
  const styleEl = document.createElement('style');
  styleEl.id = 'dual-pet-advanced-styles';
  styleEl.textContent = `
    :root {{
      --ds-pink: #f48fb1;
      --ds-dark-pink: #c2185b;
      --ds-crimson: #b71c1c;
      --ds-tanjiro-green: #2e7d32;
      --ds-wood-dark: #231612;
      --ds-brass-gold: #c59b27;
      --ds-gold-glow: #ffd54f;
      --lp-star-gold: #facc15;
      --qq-green: #10b981;
    }}

    #nezuko-pet-root {{
      position: fixed;
      right: 32px;
      bottom: 24px;
      z-index: 999999;
      user-select: none;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }}

    .nezuko-pet-stage {{
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}

    .nezuko-pet-ground-shadow {{
      position: absolute;
      bottom: -6px;
      left: 50%;
      transform: translateX(-50%);
      width: 105px;
      height: 15px;
      background: radial-gradient(ellipse at center, rgba(10, 5, 8, 0.45) 0%, rgba(10, 5, 8, 0.15) 50%, transparent 75%);
      border-radius: 50%;
      pointer-events: none;
      transition: all 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
    }}

    .nezuko-pet-rig, .prince-pet-rig {{
      position: relative;
      width: 130px;
      height: 215px;
      cursor: grab;
      filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.2));
      transition: transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
      transform-origin: bottom center;
    }}
    .nezuko-pet-rig:active, .prince-pet-rig:active {{
      cursor: grabbing;
    }}

    /* 骨骼图层 */
    .bone-layer {{
      position: absolute;
      background-size: contain;
      background-repeat: no-repeat;
      pointer-events: none;
      transition: transform 0.15s ease-out;
    }}
    #bone-head {{
      top: 0; left: 0; width: 130px; height: 121px;
      background-image: url('${{NEZUKO_HEAD}}');
      transform-origin: 50% 90%; z-index: 10;
    }}
    #bone-torso {{
      top: 108px; left: 34px; width: 62px; height: 77px;
      background-image: url('${{NEZUKO_TORSO}}');
      transform-origin: 50% 100%; z-index: 6;
    }}
    #bone-arm-l {{
      top: 108px; left: 0; width: 50px; height: 71px;
      background-image: url('${{NEZUKO_ARM_L}}');
      transform-origin: 75% 20%; z-index: 8;
    }}
    #bone-arm-r {{
      top: 108px; left: 81px; width: 49px; height: 71px;
      background-image: url('${{NEZUKO_ARM_R}}');
      transform-origin: 25% 20%; z-index: 8;
    }}
    #bone-leg-l {{
      top: 178px; left: 40px; width: 28px; height: 37px;
      background-image: url('${{NEZUKO_LEG_L}}');
      transform-origin: 50% 10%; z-index: 4;
    }}
    #bone-leg-r {{
      top: 178px; left: 66px; width: 28px; height: 37px;
      background-image: url('${{NEZUKO_LEG_R}}');
      transform-origin: 50% 10%; z-index: 4;
    }}

    /* 骨骼动画 */
    .action-run #bone-arm-l {{ animation: runArmL 0.16s infinite alternate ease-in-out !important; }}
    .action-run #bone-arm-r {{ animation: runArmR 0.16s infinite alternate ease-in-out !important; }}
    .action-run #bone-leg-l {{ animation: runLegL 0.16s infinite alternate ease-in-out !important; }}
    .action-run #bone-leg-r {{ animation: runLegR 0.16s infinite alternate ease-in-out !important; }}
    .action-run #bone-torso {{ animation: runTorso 0.16s infinite alternate ease-in-out !important; }}
    .action-run #bone-head {{ animation: runHead 0.16s infinite alternate ease-in-out !important; }}
    .action-run {{ animation: runStageHop 0.55s infinite alternate ease-in-out !important; }}

    @keyframes runArmL {{ 0% {{ transform: rotate(-55deg); }} 100% {{ transform: rotate(55deg); }} }}
    @keyframes runArmR {{ 0% {{ transform: rotate(55deg); }} 100% {{ transform: rotate(-55deg); }} }}
    @keyframes runLegL {{ 0% {{ transform: rotate(50deg); }} 100% {{ transform: rotate(-50deg); }} }}
    @keyframes runLegR {{ 0% {{ transform: rotate(-50deg); }} 100% {{ transform: rotate(50deg); }} }}
    @keyframes runTorso {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-4px); }} }}
    @keyframes runHead {{ 0% {{ transform: translateY(0) rotate(-3deg); }} 100% {{ transform: translateY(-3px) rotate(3deg); }} }}
    @keyframes runStageHop {{ 0% {{ transform: scale(0.75) translateX(-32px) rotate(-6deg); }} 100% {{ transform: scale(0.75) translateX(32px) rotate(6deg); }} }}

    .action-stomp #bone-arm-l {{ transform: rotate(-28deg) !important; }}
    .action-stomp #bone-arm-r {{ transform: rotate(28deg) !important; }}
    .action-stomp #bone-leg-r {{ animation: stompRightFoot 0.2s infinite cubic-bezier(0.4, 0, 0.2, 1) !important; }}
    .action-stomp #bone-torso {{ animation: stompShockTorso 0.2s infinite ease-out !important; }}
    .action-stomp #bone-head {{ animation: stompShockHead 0.2s infinite ease-out !important; }}

    @keyframes stompRightFoot {{
      0% {{ transform: rotate(-35deg) translateY(-10px); }}
      55% {{ transform: rotate(0deg) translateY(0); }}
      65% {{ transform: rotate(4deg) translateY(2px); }}
      100% {{ transform: rotate(-35deg) translateY(-10px); }}
    }}
    @keyframes stompShockTorso {{ 0%, 100% {{ transform: translateY(0); }} 60% {{ transform: translateY(3px); }} }}
    @keyframes stompShockHead {{ 0%, 100% {{ transform: translateY(0) rotate(0deg); }} 60% {{ transform: translateY(2px) rotate(-3deg); }} }}

    .action-tilt #bone-head {{ animation: tiltHeadSway 2.4s infinite ease-in-out !important; }}
    @keyframes tiltHeadSway {{ 0%, 100% {{ transform: rotate(0deg); }} 25% {{ transform: rotate(-22deg); }} 50% {{ transform: rotate(0deg); }} 75% {{ transform: rotate(22deg); }} }}

    .action-burst #bone-arm-l {{ transform: rotate(38deg) translateX(12px) translateY(-8px) !important; }}
    .action-burst #bone-arm-r {{ transform: rotate(-38deg) translateX(-12px) translateY(-8px) !important; }}
    .action-burst {{ filter: drop-shadow(0 0 20px rgba(255, 23, 68, 0.95)) saturate(1.4) !important; }}

    .action-sleep #bone-arm-l {{ animation: sleepRubEye 1.6s infinite ease-in-out !important; }}
    .action-sleep #bone-head {{ transform: rotate(16deg) translateY(12px) !important; }}
    @keyframes sleepRubEye {{ 0%, 100% {{ transform: rotate(-65deg) translateX(4px); }} 50% {{ transform: rotate(-80deg) translateX(8px); }} }}

    .action-headpat #bone-head {{ animation: headpatCuddleMotion 1.4s infinite ease-in-out !important; }}
    @keyframes headpatCuddleMotion {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-7px) rotate(10deg); }} }}

    .head-music-bob {{ transform: translateY(-4px) rotate(3deg) !important; }}

    /* 小王子立绘与动作 */
    .prince-avatar-img {{
      width: 100%; height: 100%; object-fit: contain; pointer-events: none; display: block;
      transform-origin: bottom center;
    }}
    .prince-music-bob {{ transform: translateY(-4px) rotate(3deg) !important; }}

    .action-scarf {{ animation: princeScarfWind 2.2s infinite ease-in-out !important; }}
    @keyframes princeScarfWind {{
      0%, 100% {{ transform: translateY(0) rotate(0deg); }}
      30% {{ transform: translateY(-4px) rotate(4deg) skewX(2deg); }}
      70% {{ transform: translateY(-2px) rotate(-3deg) skewX(-2deg); }}
    }}

    .action-rose {{
      animation: princeRoseCuddle 1.8s infinite ease-in-out !important;
      filter: drop-shadow(0 0 14px rgba(244, 63, 94, 0.75)) !important;
    }}
    @keyframes princeRoseCuddle {{
      0%, 100% {{ transform: scale(1) translateY(0); }}
      50% {{ transform: scale(1.06) translateY(-6px); }}
    }}

    .action-fox {{ animation: princeFoxHop 1.4s infinite ease-in-out !important; }}
    @keyframes princeFoxHop {{
      0%, 100% {{ transform: translateY(0); }}
      50% {{ transform: translateY(-8px) rotate(5deg); }}
    }}

    .action-stars {{
      animation: princeGazeStars 2.8s infinite ease-in-out !important;
      filter: drop-shadow(0 0 16px rgba(250, 204, 21, 0.8)) !important;
    }}
    @keyframes princeGazeStars {{
      0%, 100% {{ transform: translateY(0) rotate(0deg); }}
      50% {{ transform: translateY(-5px) rotate(-6deg); }}
    }}

    .action-sunset {{
      animation: princeSunsetGlow 3.2s infinite ease-in-out !important;
      filter: drop-shadow(0 0 20px rgba(251, 146, 60, 0.85)) !important;
    }}
    @keyframes princeSunsetGlow {{
      0%, 100% {{ transform: translateY(0) scale(1); }}
      50% {{ transform: translateY(4px) scale(0.96); }}
    }}

    /* 小王子名言气泡 */
    #little-prince-quote-bubble {{
      position: absolute;
      bottom: calc(100% + 22px);
      left: 50%;
      transform: translateX(-50%) translateY(10px) scale(0.9);
      width: 260px;
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(30, 41, 59, 0.98) 100%);
      border: 1.5px solid var(--lp-star-gold);
      border-radius: 12px;
      padding: 10px 14px;
      color: #f8fafc;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.65), 0 0 18px rgba(250, 204, 21, 0.35);
      opacity: 0;
      pointer-events: none;
      transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
      z-index: 150;
      backdrop-filter: blur(10px);
      cursor: pointer;
    }}
    #little-prince-quote-bubble.show {{
      opacity: 1 !important;
      pointer-events: auto !important;
      transform: translateX(-50%) translateY(0) scale(1) !important;
    }}
    #little-prince-quote-bubble::after {{
      content: ''; position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
      border: 8px solid transparent; border-top-color: var(--lp-star-gold);
    }}
    .quote-tag {{
      font-size: 10px; color: var(--lp-star-gold); font-weight: bold; margin-bottom: 4px;
      display: flex; justify-content: space-between; align-items: center;
    }}
    .quote-zh {{ font-size: 12.5px; color: #fef08a; line-height: 1.55; font-weight: 500; }}
    .quote-fr {{ font-size: 9.5px; color: #94a3b8; font-style: italic; margin-top: 4px; line-height: 1.35; }}

    /* 快捷胶囊条 */
    .nezuko-action-capsule {{
      position: absolute;
      top: -50px;
      left: 50%;
      transform: translateX(-50%) translateY(8px) scale(0.92);
      background: linear-gradient(135deg, rgba(35, 22, 18, 0.95) 0%, rgba(20, 12, 10, 0.98) 100%);
      border: 1.5px solid var(--ds-brass-gold);
      border-radius: 28px;
      padding: 5px 10px;
      display: flex;
      align-items: center;
      gap: 7px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.65), 0 0 16px rgba(244, 143, 177, 0.35);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
      z-index: 100;
      backdrop-filter: blur(8px);
    }}
    .nezuko-action-capsule::after {{
      content: ''; position: absolute; top: 100%; left: -20px; right: -20px; height: 44px;
      background: transparent; pointer-events: auto;
    }}
    .nezuko-pet-stage:hover .nezuko-action-capsule,
    .nezuko-action-capsule:hover,
    .nezuko-action-capsule.is-active {{
      opacity: 1 !important; pointer-events: auto !important; transform: translateX(-50%) translateY(0) scale(1) !important;
    }}

    .nezuko-capsule-btn {{
      width: 32px; height: 32px; border-radius: 50%;
      background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(197, 155, 39, 0.45);
      color: #fff; font-size: 15px; display: flex; align-items: center; justify-content: center;
      cursor: pointer; transition: all 0.18s cubic-bezier(0.2, 0.8, 0.2, 1); position: relative; flex-shrink: 0;
    }}
    .nezuko-capsule-btn:hover {{
      background: var(--ds-dark-pink); border-color: var(--ds-pink); transform: scale(1.18);
      box-shadow: 0 0 12px rgba(244, 143, 177, 0.7);
    }}
    .nezuko-capsule-btn:active {{ transform: scale(0.95); }}
    .nezuko-capsule-btn[data-tip]::before {{
      content: attr(data-tip); position: absolute; bottom: calc(100% + 7px); left: 50%;
      transform: translateX(-50%) scale(0.8); background: rgba(20, 12, 10, 0.95);
      border: 1px solid var(--ds-brass-gold); color: var(--ds-gold-glow); font-size: 10px;
      font-weight: bold; padding: 2px 7px; border-radius: 4px; white-space: nowrap; pointer-events: none;
      opacity: 0; transition: all 0.18s ease; box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }}
    .nezuko-capsule-btn:hover::before {{ opacity: 1; transform: translateX(-50%) scale(1); }}

    .btn-switch-pet {{
      background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important; border-color: #60a5fa !important;
    }}

    .btn-music-spin {{
      background: radial-gradient(circle, #ff80ab 20%, #231612 21%, #111 100%);
    }}
    .btn-music-spin.playing {{
      animation: recordSpin 3.5s infinite linear; border-color: var(--ds-pink); box-shadow: 0 0 10px rgba(244, 143, 177, 0.8);
    }}
    @keyframes recordSpin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}

    .pet-picked-up {{
      transform: scale(1.08) translateY(-22px) rotate(-8deg) !important;
      filter: drop-shadow(0 14px 22px rgba(0, 0, 0, 0.35)) !important;
    }}

    /* 主操作看板 */
    #nezuko-main-card {{
      position: absolute; bottom: 225px; right: 0; width: 345px;
      background: linear-gradient(135deg, rgba(35, 22, 18, 0.96) 0%, rgba(20, 12, 10, 0.98) 100%);
      border: 2px solid var(--ds-brass-gold); border-radius: 12px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65), 0 0 20px rgba(244, 143, 177, 0.25);
      color: #fff; overflow: hidden; display: none; flex-direction: column; z-index: 120;
      backdrop-filter: blur(12px);
    }}
    .nezuko-card-header {{
      display: flex; justify-content: space-between; align-items: center; padding: 10px 14px;
      background: linear-gradient(90deg, #381f19 0%, #4a2920 100%); border-bottom: 1.5px solid var(--ds-brass-gold);
    }}
    .nezuko-header-title {{
      font-size: 13px; font-weight: 700; color: var(--ds-gold-glow);
      display: flex; align-items: center; gap: 6px; text-shadow: 0 1px 3px rgba(0,0,0,0.8);
    }}
    .nezuko-card-body {{
      padding: 12px 14px; display: flex; flex-direction: column; gap: 12px; max-height: 480px; overflow-y: auto;
    }}
    .nezuko-section-box {{
      background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(197, 155, 39, 0.35);
      border-radius: 8px; padding: 10px 12px;
    }}
    .nezuko-section-title {{
      font-size: 12px; font-weight: 700; color: #e0e0e0; margin-bottom: 8px;
      display: flex; justify-content: space-between; align-items: center;
    }}

    /* ========================================================= */
    /* 核心焦点：QQ 音乐联动专属高能和风播放器面板 */
    /* ========================================================= */
    .qq-music-player-box {{
      background: linear-gradient(180deg, rgba(16, 185, 129, 0.12) 0%, rgba(20, 12, 10, 0.9) 100%);
      border: 1.5px solid var(--qq-green);
      border-radius: 8px; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px;
      box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
    }}
    .qq-status-bar {{
      display: flex; justify-content: space-between; align-items: center;
      font-size: 10.5px; color: #6ee7b7; font-weight: bold;
    }}
    .qq-pulse-dot {{
      width: 7px; height: 7px; border-radius: 50%; background: #10b981; display: inline-block;
      margin-right: 4px; box-shadow: 0 0 6px #10b981; animation: pulseGlow 1.5s infinite;
    }}
    @keyframes pulseGlow {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}

    .nezuko-music-info {{ display: flex; align-items: center; gap: 10px; }}
    .nezuko-record-disc {{
      width: 36px; height: 36px;
      background: radial-gradient(circle, #10b981 18%, #111 19%, #222 65%, #111 100%);
      border: 1.5px solid var(--qq-green); border-radius: 50%; flex-shrink: 0;
      animation: recordSpin 3.5s infinite linear; animation-play-state: paused;
    }}
    .record-spinning {{ animation-play-state: running !important; }}
    .nezuko-song-texts {{ display: flex; flex-direction: column; overflow: hidden; }}
    .nezuko-song-title {{ font-size: 12px; font-weight: 700; color: #fff; white-space: nowrap; text-overflow: ellipsis; overflow: hidden; }}
    .nezuko-song-sub {{ font-size: 10px; color: #a7f3d0; }}

    /* 跳动声波柱动效 */
    .sound-waves-box {{
      display: flex; align-items: flex-end; gap: 2px; height: 14px;
    }}
    .sound-bar {{
      width: 3px; background: #10b981; border-radius: 2px;
      animation: barJump 0.8s infinite ease-in-out alternate;
    }}
    .sound-bar:nth-child(1) {{ height: 6px; animation-delay: 0.1s; }}
    .sound-bar:nth-child(2) {{ height: 14px; animation-delay: 0.3s; }}
    .sound-bar:nth-child(3) {{ height: 9px; animation-delay: 0.2s; }}
    .sound-bar:nth-child(4) {{ height: 12px; animation-delay: 0.4s; }}
    @keyframes barJump {{ 0% {{ height: 3px; }} 100% {{ height: 14px; }} }}

    .nezuko-music-controls {{ display: flex; align-items: center; justify-content: space-between; gap: 6px; }}
    .nezuko-ctrl-btn {{
      background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(197, 155, 39, 0.4);
      color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; transition: all 0.2s;
    }}
    .nezuko-ctrl-btn:hover {{ background: var(--ds-dark-pink); border-color: var(--ds-pink); }}
    .nezuko-ctrl-play {{
      background: linear-gradient(135deg, #059669, #047857) !important;
      border-color: #34d399 !important; font-weight: bold; padding: 5px 16px;
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
    }}

    .nezuko-float-badge {{
      position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%);
      background: rgba(35, 22, 18, 0.88); border: 1px solid var(--ds-brass-gold);
      color: var(--ds-gold-glow); font-size: 10px; padding: 2px 8px; border-radius: 12px;
      cursor: pointer; white-space: nowrap; box-shadow: 0 4px 10px rgba(0,0,0,0.4);
      opacity: 0.85; transition: opacity 0.2s;
    }}
    .nezuko-float-badge:hover {{ opacity: 1; background: var(--ds-dark-pink); color: #fff; }}
  `;
  document.head.appendChild(styleEl);

  // ==========================================
  // 六、DOM 组装
  // ==========================================
  const root = document.createElement('div');
  root.id = 'nezuko-pet-root';
  root.innerHTML = `
    <div class="nezuko-pet-stage" id="nezuko-pet-stage">
      <div class="nezuko-pet-ground-shadow" id="nezuko-ground-shadow"></div>

      <!-- 小王子名言气泡 -->
      <div id="little-prince-quote-bubble">
        <div class="quote-tag">
          <span id="qp-tag">🦊 狐狸的秘密 · B612星球</span>
          <span style="font-size:9px; opacity:0.8;">✦ 治愈哲思</span>
        </div>
        <div class="quote-zh" id="qp-zh">真正重要的东西，用眼睛是看不见的，只有用心才能看清。</div>
        <div class="quote-fr" id="qp-fr">L'essentiel est invisible pour les yeux.</div>
      </div>

      <!-- 头顶快捷胶囊动作条 -->
      <div class="nezuko-action-capsule" id="nezuko-action-capsule">
        <button class="nezuko-capsule-btn btn-switch-pet" id="btn-quick-switch" data-tip="切换角色 (祢豆子/小王子)" title="切换角色">🔁</button>
        <div id="action-buttons-container" style="display:flex; gap:7px;"></div>
        <button class="nezuko-capsule-btn btn-music-spin" id="btn-quick-music" data-tip="QQ音乐播放/切歌" title="遥控电脑QQ音乐">🎵</button>
        <button class="nezuko-capsule-btn" id="btn-quick-board" data-tip="配额看板" title="打开配额看板">🎋</button>
      </div>

      <!-- 角色 1：祢豆子 2D 骨骼机架 -->
      <div class="nezuko-pet-rig" id="pet-nezuko" style="display:none;" title="双击打开看板 · 按住拖拽 · 滚轮切QQ音乐">
        <div class="bone-layer" id="bone-leg-l"></div>
        <div class="bone-layer" id="bone-leg-r"></div>
        <div class="bone-layer" id="bone-torso"></div>
        <div class="bone-layer" id="bone-arm-l"></div>
        <div class="bone-layer" id="bone-arm-r"></div>
        <div class="bone-layer" id="bone-head"></div>
      </div>

      <!-- 角色 2：小王子 B612 治愈立绘 -->
      <div class="prince-pet-rig" id="pet-prince" style="display:none;" title="单击听名言 · 双击打开看板 · 按住拖拽 · 滚轮切歌">
        <img src="${{PRINCE_IMG}}" class="prince-avatar-img" id="prince-avatar-body" alt="小王子">
      </div>

      <div class="nezuko-float-badge" id="nezuko-open-btn">🎋 桌面守护</div>
    </div>

    <!-- 主操作看板 -->
    <div id="nezuko-main-card">
      <div class="nezuko-card-header">
        <div class="nezuko-header-title">
          <span id="board-title-char">🌸 灶门祢豆子</span>
          <span class="nezuko-header-badge" id="board-role-badge">桌宠中枢</span>
        </div>
        <button class="nezuko-close-btn" id="nezuko-close-card" title="关闭面板">✕</button>
      </div>

      <div class="nezuko-card-body">
        <!-- 核心模块：电脑 QQ 音乐客户端无缝遥控中枢 -->
        <div class="qq-music-player-box">
          <div class="qq-status-bar">
            <span><span class="qq-pulse-dot"></span>已对接电脑 QQ 音乐客户端</span>
            <button class="nezuko-ctrl-btn" id="m-btn-wake-qq" style="font-size:9.5px; padding:2px 6px; background:rgba(16,185,129,0.25); border-color:#10b981;">
              🚀 唤醒QQ音乐
            </button>
          </div>

          <div class="nezuko-music-info">
            <div class="nezuko-record-disc" id="nezuko-disc"></div>
            <div class="nezuko-song-texts" style="flex:1;">
              <span class="nezuko-song-title" id="music-title">QQ 音乐播放联动</span>
              <span class="nezuko-song-sub" id="music-sub">点击下方按钮直接控制电脑上的 QQ 音乐</span>
            </div>
            <div class="sound-waves-box" id="sound-waves" style="display:none;">
              <div class="sound-bar"></div><div class="sound-bar"></div>
              <div class="sound-bar"></div><div class="sound-bar"></div>
            </div>
          </div>

          <div class="nezuko-music-controls">
            <button class="nezuko-ctrl-btn" id="m-btn-prev" title="QQ 音乐上一曲">⏮ 上一曲</button>
            <button class="nezuko-ctrl-btn nezuko-ctrl-play" id="m-btn-play" title="播放 / 暂停 QQ 音乐">▶ 播放</button>
            <button class="nezuko-ctrl-btn" id="m-btn-next" title="QQ 音乐下一曲">⏭ 下一曲</button>
          </div>
        </div>

        <!-- 角色切换与管理卡片 -->
        <div class="nezuko-section-box" style="background: rgba(59, 130, 246, 0.18); border-color: #60a5fa;">
          <div class="nezuko-section-title">
            <span style="color:#93c5fd;">⭐ 桌面宠物随心切换</span>
            <span id="cur-pet-label" style="font-size:10px; color:#facc15;">当前角色</span>
          </div>
          <div style="display:flex; gap:8px;">
            <button class="nezuko-ctrl-btn" id="btn-select-nezuko" style="flex:1; padding:6px; background:linear-gradient(135deg, #c2185b, #b71c1c);">
              🌸 灶门祢豆子
            </button>
            <button class="nezuko-ctrl-btn" id="btn-select-prince" style="flex:1; padding:6px; background:linear-gradient(135deg, #2563eb, #7c3aed);">
              👑 小王子 (B612)
            </button>
          </div>
        </div>

        <!-- 软件界面鬼灭全套主题开关 -->
        <div class="nezuko-section-box" style="background: rgba(194, 24, 91, 0.15); border-color: var(--ds-pink);">
          <div class="nezuko-section-title">
            <span style="color:#ffd54f;">🌸 软件界面《鬼灭之刃》全局主题</span>
            <span id="theme-status-tag" style="font-size:10px; color:#81c784;">● 已激活</span>
          </div>
          <button class="nezuko-ctrl-btn" id="btn-toggle-ide-theme" style="width:100%; padding:5px; background:linear-gradient(135deg, var(--ds-dark-pink), var(--ds-crimson)); font-weight:bold;">
            🎋 切换软件鬼灭主题 (开/关)
          </button>
        </div>

        <!-- Gemini 模型专属配额 (对应截图) -->
        <div class="nezuko-section-box">
          <div class="nezuko-section-title">
            <span>Gemini 模型</span>
            <span style="font-size:10px; color:#81c784;">● 活跃</span>
          </div>
          <div class="nezuko-quota-row">
            <div class="nezuko-quota-meta">
              <span class="nezuko-quota-name">每周剩余可用配额</span>
              <span class="nezuko-quota-reset" id="lbl-gemini-weekly-reset">${{currentQuota.geminiWeeklyReset}}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-gemini-weekly-pct">${{currentQuota.geminiWeeklyPct}}%</span>
              <div class="nezuko-ring-wrap">
                <svg viewBox="0 0 24 24" width="24" height="24">
                  <circle cx="12" cy="12" r="10" class="nezuko-ring-bg"/>
                  <circle cx="12" cy="12" r="10" class="nezuko-ring-bar" id="ring-gemini-weekly"/>
                </svg>
              </div>
            </div>
          </div>
          <div class="nezuko-quota-row">
            <div class="nezuko-quota-meta">
              <span class="nezuko-quota-name">5 小时剩余可用配额</span>
              <span class="nezuko-quota-reset" id="lbl-gemini-5h-reset">${{currentQuota.gemini5hReset}}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-gemini-5h-pct">${{currentQuota.gemini5hPct}}%</span>
              <div class="nezuko-ring-wrap">
                <svg viewBox="0 0 24 24" width="24" height="24">
                  <circle cx="12" cy="12" r="10" class="nezuko-ring-bg"/>
                  <circle cx="12" cy="12" r="10" class="nezuko-ring-bar" id="ring-gemini-5h"/>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Claude 与 GPT 模型专属配额 (对应截图) -->
        <div class="nezuko-section-box">
          <div class="nezuko-section-title">
            <span>Claude 与 GPT 模型</span>
            <span style="font-size:10px; color:#81c784;">● 充足</span>
          </div>
          <div class="nezuko-quota-row">
            <div class="nezuko-quota-meta">
              <span class="nezuko-quota-name">每周剩余可用配额</span>
              <span class="nezuko-quota-reset" id="lbl-claude-weekly-reset">${{currentQuota.claudeWeeklyReset}}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-claude-weekly-pct">${{currentQuota.claudeWeeklyPct}}%</span>
              <div class="nezuko-ring-wrap">
                <svg viewBox="0 0 24 24" width="24" height="24">
                  <circle cx="12" cy="12" r="10" class="nezuko-ring-bg"/>
                  <circle cx="12" cy="12" r="10" class="nezuko-ring-bar" id="ring-claude-weekly"/>
                </svg>
              </div>
            </div>
          </div>
          <div class="nezuko-quota-row">
            <div class="nezuko-quota-meta">
              <span class="nezuko-quota-name">5 小时剩余可用配额</span>
              <span class="nezuko-quota-reset" id="lbl-claude-5h-reset">${{currentQuota.claude5hReset}}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-claude-5h-pct">${{currentQuota.claude5hPct}}%</span>
              <div class="nezuko-ring-wrap">
                <svg viewBox="0 0 24 24" width="24" height="24">
                  <circle cx="12" cy="12" r="10" class="nezuko-ring-bg"/>
                  <circle cx="12" cy="12" r="10" class="nezuko-ring-bar" id="ring-claude-5h"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(root);

  // ==========================================
  // 七、逻辑与事件驱动
  // ==========================================
  const petNezuko = document.getElementById('pet-nezuko');
  const petPrince = document.getElementById('pet-prince');
  const actionBtnBox = document.getElementById('action-buttons-container');
  const quoteBubble = document.getElementById('little-prince-quote-bubble');
  const boardTitleChar = document.getElementById('board-title-char');
  const boardRoleBadge = document.getElementById('board-role-badge');
  const curPetLabel = document.getElementById('cur-pet-label');
  const mainCard = document.getElementById('nezuko-main-card');
  const openBtn = document.getElementById('nezuko-open-btn');
  const closeBtn = document.getElementById('nezuko-close-card');
  const stageEl = document.getElementById('nezuko-pet-stage');
  const capsuleBar = document.getElementById('nezuko-action-capsule');
  const disc = document.getElementById('nezuko-disc');
  const quickMusicBtn = document.getElementById('btn-quick-music');
  const quickBoardBtn = document.getElementById('btn-quick-board');
  const soundWaves = document.getElementById('sound-waves');

  // QQ 音乐播放界面更新
  window.updateMusicUI = function() {{
    const playBtn = document.getElementById('m-btn-play');
    const titleEl = document.getElementById('music-title');
    const subEl = document.getElementById('music-sub');

    if (qqBridge.isPlaying) {{
      playBtn.textContent = "⏸ 暂停";
      playBtn.style.background = "linear-gradient(135deg, #ef4444, #b91c1c)";
      playBtn.style.borderColor = "#f87171";
      disc.classList.add('record-spinning');
      quickMusicBtn.classList.add('playing');
      soundWaves.style.display = 'flex';
      titleEl.textContent = "QQ 音乐正在播放中";
      subEl.textContent = "音效已同步 · 点击可暂停或切歌";
    }} else {{
      playBtn.textContent = "▶ 播放";
      playBtn.style.background = "linear-gradient(135deg, #059669, #047857)";
      playBtn.style.borderColor = "#34d399";
      disc.classList.remove('record-spinning');
      quickMusicBtn.classList.remove('playing');
      soundWaves.style.display = 'none';
      titleEl.textContent = "QQ 音乐已就绪";
      subEl.textContent = "点击播放直接启动电脑上的 QQ 音乐";
    }}
  }};

  // 播放按钮控制
  document.getElementById('m-btn-play').addEventListener('click', () => qqBridge.playPause());
  document.getElementById('m-btn-next').addEventListener('click', () => qqBridge.nextTrack());
  document.getElementById('m-btn-prev').addEventListener('click', () => qqBridge.prevTrack());
  document.getElementById('m-btn-wake-qq').addEventListener('click', () => qqBridge.wakeUpQQMusic());

  quickMusicBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    qqBridge.playPause();
  }});

  // 滚轮在桌宠上切歌
  stageEl.addEventListener('wheel', (e) => {{
    e.preventDefault();
    if (e.deltaY > 0) qqBridge.nextTrack();
    else qqBridge.prevTrack();
  }});

  // 角色切换
  let activePet = getActivePet();
  let currentQuoteIndex = 0;
  let quoteAutoTimer = null;
  let quoteHideTimer = null;

  function showNextQuote() {{
    const q = LITTLE_PRINCE_QUOTES[currentQuoteIndex];
    document.getElementById('qp-tag').textContent = q.tag + " · B612星球";
    document.getElementById('qp-zh').textContent = q.zh;
    document.getElementById('qp-fr').textContent = q.fr;
    currentQuoteIndex = (currentQuoteIndex + 1) % LITTLE_PRINCE_QUOTES.length;

    quoteBubble.classList.add('show');
    if (quoteHideTimer) clearTimeout(quoteHideTimer);
    quoteHideTimer = setTimeout(() => {{
      quoteBubble.classList.remove('show');
    }}, 9500);
  }}

  function renderActionButtons() {{
    actionBtnBox.innerHTML = '';
    if (activePet === 'nezuko') {{
      actionBtnBox.innerHTML = `
        <button class="nezuko-capsule-btn" data-action="headpat" data-tip="摸头杀蹭蹭" title="摸头杀蹭蹭">🐱</button>
        <button class="nezuko-capsule-btn" data-action="run" data-tip="风火轮狂奔" title="豆豆眼风火轮狂奔">🏃</button>
        <button class="nezuko-capsule-btn" data-action="box" data-tip="钻木箱捉猫" title="钻雾云杉木箱捉迷藏">📦</button>
        <button class="nezuko-capsule-btn" data-action="stomp" data-tip="气鼓跺小脚" title="气鼓鼓跺小脚">😤</button>
        <button class="nezuko-capsule-btn" data-action="burst" data-tip="血鬼术·爆血" title="血鬼术·爆血觉醒">🔥</button>
        <button class="nezuko-capsule-btn" data-action="sleep" data-tip="揉眼伸懒腰" title="揉眼睛伸懒腰打瞌睡">🥱</button>
      `;
    }} else {{
      actionBtnBox.innerHTML = `
        <button class="nezuko-capsule-btn" data-action="scarf" data-tip="飘逸长围巾" title="黄色围巾迎风飞扬">🧣</button>
        <button class="nezuko-capsule-btn" data-action="rose" data-tip="呵护红玫瑰" title="呵护玻璃罩里的红玫瑰">🌹</button>
        <button class="nezuko-capsule-btn" data-action="fox" data-tip="驯养小狐狸" title="与小狐狸相互依偎">🦊</button>
        <button class="nezuko-capsule-btn" data-action="stars" data-tip="仰望繁星" title="仰望夜空寻找属于自己的星星">✨</button>
        <button class="nezuko-capsule-btn" data-action="sunset" data-tip="四十四次日落" title="看第四十四次日落">🌅</button>
        <button class="nezuko-capsule-btn" data-action="quote" data-tip="抽取哲思名句" title="抽取《小王子》经典名言">📖</button>
      `;
    }}

    actionBtnBox.querySelectorAll('.nezuko-capsule-btn').forEach(btn => {{
      btn.addEventListener('click', (e) => {{
        e.stopPropagation();
        const action = btn.getAttribute('data-action');
        if (action === 'quote') showNextQuote();
        else triggerCurrentPetAction(action);
      }});
    }});
  }}

  let actionTimer = null;
  function triggerCurrentPetAction(actionName, duration = 6500) {{
    const currentRig = activePet === 'nezuko' ? petNezuko : petPrince;
    currentRig.className = (activePet === 'nezuko' ? 'nezuko-pet-rig' : 'prince-pet-rig');
    if (actionName) currentRig.classList.add('action-' + actionName);

    if (actionTimer) clearTimeout(actionTimer);
    actionTimer = setTimeout(() => {{
      currentRig.className = (activePet === 'nezuko' ? 'nezuko-pet-rig' : 'prince-pet-rig');
    }}, duration);
  }}

  function switchPet(targetPet) {{
    activePet = targetPet;
    setActivePet(targetPet);

    if (targetPet === 'nezuko') {{
      petNezuko.style.display = 'block';
      petPrince.style.display = 'none';
      quoteBubble.classList.remove('show');
      boardTitleChar.textContent = "🌸 竈門禰豆子";
      boardRoleBadge.textContent = "大正和风 · 鬼灭桌宠";
      curPetLabel.textContent = "当前: 灶门祢豆子";
      openBtn.textContent = "🎋 鬼灭看板";
      if (quoteAutoTimer) clearInterval(quoteAutoTimer);
    }} else {{
      petNezuko.style.display = 'none';
      petPrince.style.display = 'block';
      boardTitleChar.textContent = "👑 小王子 (B612)";
      boardRoleBadge.textContent = "B612星球 · 治愈桌宠";
      curPetLabel.textContent = "当前: 小王子";
      openBtn.textContent = "⭐ B612 看板";
      if (quoteAutoTimer) clearInterval(quoteAutoTimer);
      quoteAutoTimer = setInterval(showNextQuote, 180000);
      showNextQuote();
    }}

    renderActionButtons();
  }}

  document.getElementById('btn-quick-switch').addEventListener('click', (e) => {{
    e.stopPropagation();
    switchPet(activePet === 'nezuko' ? 'prince' : 'nezuko');
  }});
  document.getElementById('btn-select-nezuko').addEventListener('click', () => switchPet('nezuko'));
  document.getElementById('btn-select-prince').addEventListener('click', () => switchPet('prince'));

  petPrince.addEventListener('click', (e) => {{
    if (isDragging) return;
    showNextQuote();
    triggerCurrentPetAction('rose', 2000);
  }});
  quoteBubble.addEventListener('click', (e) => {{
    e.stopPropagation();
    showNextQuote();
  }});

  switchPet(activePet);

  // 防消失与交互
  let hideCapsuleTimer = null;
  let isCapsulePinned = false;

  function showCapsule() {{
    if (hideCapsuleTimer) {{
      clearTimeout(hideCapsuleTimer);
      hideCapsuleTimer = null;
    }}
    capsuleBar.classList.add('is-active');
  }}
  function scheduleHideCapsule() {{
    if (isCapsulePinned) return;
    if (hideCapsuleTimer) clearTimeout(hideCapsuleTimer);
    hideCapsuleTimer = setTimeout(() => {{
      capsuleBar.classList.remove('is-active');
    }}, 450);
  }}

  stageEl.addEventListener('mouseenter', showCapsule);
  stageEl.addEventListener('mouseleave', scheduleHideCapsule);
  capsuleBar.addEventListener('mouseenter', showCapsule);
  capsuleBar.addEventListener('mouseleave', scheduleHideCapsule);

  stageEl.addEventListener('dblclick', () => {{
    mainCard.style.display = mainCard.style.display === 'flex' ? 'none' : 'flex';
  }});
  openBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    mainCard.style.display = mainCard.style.display === 'flex' ? 'none' : 'flex';
  }});
  quickBoardBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    mainCard.style.display = mainCard.style.display === 'flex' ? 'none' : 'flex';
  }});
  closeBtn.addEventListener('click', () => {{
    mainCard.style.display = 'none';
  }});

  // 物理拖拽
  let isDragging = false;
  let dragStartX = 0, dragStartY = 0;
  let rootStartRight = 32, rootStartBottom = 24;

  const onDragDown = (e) => {{
    if (e.button !== 0) return;
    isDragging = false;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    
    const rect = root.getBoundingClientRect();
    rootStartRight = window.innerWidth - rect.right;
    rootStartBottom = window.innerHeight - rect.bottom;

    const onMove = (moveEvt) => {{
      const dx = moveEvt.clientX - dragStartX;
      const dy = moveEvt.clientY - dragStartY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {{
        isDragging = true;
        const currentRig = activePet === 'nezuko' ? petNezuko : petPrince;
        currentRig.classList.add('pet-picked-up');
      }}
      if (isDragging) {{
        root.style.right = (rootStartRight - dx) + 'px';
        root.style.bottom = (rootStartBottom - dy) + 'px';
      }}
    }};

    const onUp = () => {{
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      if (isDragging) {{
        const currentRig = activePet === 'nezuko' ? petNezuko : petPrince;
        currentRig.classList.remove('pet-picked-up');
        setTimeout(() => {{ isDragging = false; }}, 50);
      }}
    }};

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }};

  petNezuko.addEventListener('mousedown', onDragDown);
  petPrince.addEventListener('mousedown', onDragDown);

  // 配额更新
  function updateQuotaDisplay() {{
    const CIRCLE_CIRCUM = 62.83;
    const setRing = (id, pct) => {{
      const ring = document.getElementById(id);
      if (!ring) return;
      const offset = CIRCLE_CIRCUM * (1 - (pct / 100));
      ring.style.strokeDashoffset = offset;
      if (pct > 75) ring.style.stroke = '#81c784';
      else if (pct > 30) ring.style.stroke = '#ffd54f';
      else ring.style.stroke = '#e57373';
    }};
    setRing('ring-gemini-weekly', currentQuota.geminiWeeklyPct);
    setRing('ring-gemini-5h', currentQuota.gemini5hPct);
    setRing('ring-claude-weekly', currentQuota.claudeWeeklyPct);
    setRing('ring-claude-5h', currentQuota.claude5hPct);

    document.getElementById('lbl-gemini-weekly-pct').textContent = currentQuota.geminiWeeklyPct + '%';
    document.getElementById('lbl-gemini-5h-pct').textContent = currentQuota.gemini5hPct + '%';
    document.getElementById('lbl-claude-weekly-pct').textContent = currentQuota.claudeWeeklyPct + '%';
    document.getElementById('lbl-claude-5h-pct').textContent = currentQuota.claude5hPct + '%';
  }}
  updateQuotaDisplay();

}})();
"""

target_js = REPO_ROOT / "resources" / "nezuko-pet.js"
target_js.write_text(js_code, encoding="utf-8")
print(f"✅ 成功生成对接电脑 QQ 音乐的桌宠组件: {target_js} ({len(js_code.encode('utf-8'))} 字节)")
