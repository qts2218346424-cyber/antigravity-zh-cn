# -*- coding: utf-8 -*-
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

# 1. 裁剪祢豆子 2D 骨骼关节肢体
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

# 2. 读取小王子透明立绘
prince_webp = MEDIA_DIR / "little_prince_pet.webp"
if not prince_webp.exists():
    prince_webp = MEDIA_DIR / "little_prince_pet.png"
b64_prince = base64.b64encode(prince_webp.read_bytes()).decode('ascii')

js_code = f"""// 灶门祢豆子 & 小王子 (B612) · 双角色二头身骨骼桌宠 + 电脑 QQ 音乐无缝联动 + 额度告急与疲劳关怀中枢
(function() {{
  if (typeof window === 'undefined' || window.__AGY_NEZUKO_PET_INITIALIZED__) return;
  window.__AGY_NEZUKO_PET_INITIALIZED__ = true;

  // 1. 2D 骨骼关节分肢图层
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
      this.mode = 'qqmusic';
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
  // 二、Web Audio 极速警报与关怀音效引擎
  // ==========================================
  class PetAudioSynth {{
    constructor() {{
      this.ctx = null;
    }}
    ensureCtx() {{
      if (!this.ctx) {{
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) this.ctx = new AudioCtx();
      }}
      if (this.ctx && this.ctx.state === 'suspended') {{
        this.ctx.resume();
      }}
    }}
    // 额度告急警报音（急促双频警报声）
    playAlertSound() {{
      try {{
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.setValueAtTime(659, now + 0.12);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.36);
      }} catch (_) {{}}
    }}
    // 疲劳健康关怀温和音效（三和弦轻灵水滴声）
    playCareSound() {{
      try {{
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const notes = [523.25, 659.25, 783.99];
        notes.forEach((freq, idx) => {{
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, now + idx * 0.08);
          gain.gain.setValueAtTime(0.09, now + idx * 0.08);
          gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 0.35);
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.start(now + idx * 0.08);
          osc.stop(now + idx * 0.08 + 0.38);
        }});
      }} catch (_) {{}}
    }}
  }}
  const petAudio = new PetAudioSynth();

  // ==========================================
  // 三、《小王子》12 句中法双语经典哲思名言库
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
      zh: "审判自己比审判别人要难得多。如果你能正确地审判自己，你就是一个真正有智慧的人。",
      fr: "Il est bien plus difficile de se juger soi-même que de juger autrui.",
      tag: "⚖️ 自省与智慧"
    }},
    {{
      zh: "即使在人群中，人也一样会感到孤单。用心去寻找，才能找到真正的陪伴。",
      fr: "On est un peu seul dans le désert... On est seul aussi chez les hommes.",
      tag: "🌌 星际旅途"
    }}
  ];

  function getActivePet() {{
    return localStorage.getItem('__agy_active_pet_character__') || 'nezuko';
  }}
  function setActivePet(name) {{
    localStorage.setItem('__agy_active_pet_character__', name);
  }}

  // ==========================================
  // 四、Antigravity 软件界面鬼灭和风全局主题
  // ==========================================
  const ideThemeStyle = document.createElement('style');
  ideThemeStyle.id = 'agy-demon-slayer-ide-theme';
  ideThemeStyle.textContent = `
    .part.activitybar, #workbench\\.parts\\.activitybar, .activitybar {{
      background: linear-gradient(180deg, #1f130e 0%, #150c09 100%) !important;
      border-right: 2px solid #c59b27 !important; position: relative !important;
    }}
    .part.activitybar::before, #workbench\\.parts\\.activitybar::before, .activitybar::before {{
      content: '' !important; position: absolute !important; top: 0 !important; left: 0 !important; bottom: 0 !important;
      width: 5px !important; background: repeating-linear-gradient(45deg, #2e7d32 0, #2e7d32 6px, #111 6px, #111 12px) !important;
      z-index: 10 !important;
    }}
    .activitybar .action-item.checked .action-label, .activitybar .action-item.active .action-label {{
      color: #ffd54f !important; filter: drop-shadow(0 0 6px rgba(255, 213, 79, 0.6)) !important;
    }}
    .part.sidebar, #workbench\\.parts\\.sidebar, .sidebar {{
      background: linear-gradient(135deg, rgba(28, 17, 13, 0.98) 0%, rgba(18, 10, 8, 0.99) 100%) !important;
      border-right: 1.5px solid rgba(197, 155, 39, 0.4) !important;
    }}
    .sidebar .title-label h2, .sidebar .pane-header .title {{ color: #ffd54f !important; font-weight: 700 !important; }}
    .part.statusbar, #workbench\\.parts\\.statusbar, .statusbar {{
      background: repeating-linear-gradient(45deg, #1b3820 0, #1b3820 8px, #111a13 8px, #111a13 16px) !important;
      border-top: 1.5px solid #c59b27 !important; color: #fff9c4 !important;
    }}
    .statusbar .statusbar-item a, .statusbar .statusbar-item {{ color: #fff9c4 !important; }}
    .part.titlebar, #workbench\\.parts\\.titlebar, .titlebar {{
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
  if (isIdeThemeEnabled()) {{
    document.head.appendChild(ideThemeStyle);
  }}

  // ==========================================
  // 五、模型配额与额度低于 10% 警报引擎
  // ==========================================
  const defaultQuotaState = {{
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

  // 额度告急提醒状态
  let lastQuotaAlertKey = '';
  let lastQuotaAlertTime = 0;
  let quotaAlertEnabled = localStorage.getItem('__agy_quota_alert_enabled__') !== 'false';

  function checkQuotaAlert(force = false) {{
    if (!quotaAlertEnabled && !force) return false;

    const alertItems = [];
    if (currentQuota.geminiWeeklyPct <= 10) {{
      alertItems.push({{ name: 'Gemini 模型', period: '每周配额', pct: currentQuota.geminiWeeklyPct, reset: currentQuota.geminiWeeklyReset }});
    }}
    if (currentQuota.gemini5hPct <= 10) {{
      alertItems.push({{ name: 'Gemini 模型', period: '5小时配额', pct: currentQuota.gemini5hPct, reset: currentQuota.gemini5hReset }});
    }}
    if (currentQuota.claudeWeeklyPct <= 10) {{
      alertItems.push({{ name: 'Claude 模型', period: '每周配额', pct: currentQuota.claudeWeeklyPct, reset: currentQuota.claudeWeeklyReset }});
    }}
    if (currentQuota.claude5hPct <= 10) {{
      alertItems.push({{ name: 'Claude 模型', period: '5小时配额', pct: currentQuota.claude5hPct, reset: currentQuota.claude5hReset }});
    }}

    const alertTag = document.getElementById('quota-alert-status-tag');
    if (alertTag) {{
      if (alertItems.length > 0) {{
        alertTag.textContent = '🚨 告急 (低于10%)';
        alertTag.style.color = '#ef4444';
      }} else {{
        alertTag.textContent = '● 配额充裕';
        alertTag.style.color = '#81c784';
      }}
    }}

    if (alertItems.length === 0) return false;

    const now = Date.now();
    const alertKey = alertItems.map(it => `${{it.name}}_${{it.period}}_${{it.pct}}`).join('|');
    // 防骚扰：同一级别警报 15 分钟内不重复弹窗，除非强制触发
    if (!force && lastQuotaAlertKey === alertKey && (now - lastQuotaAlertTime < 15 * 60 * 1000)) {{
      return false;
    }}
    lastQuotaAlertKey = alertKey;
    lastQuotaAlertTime = now;

    // 触发警报
    triggerQuotaAlertUI(alertItems[0]);
    return true;
  }}

  function triggerQuotaAlertUI(item) {{
    petAudio.playAlertSound();

    if (activePet === 'nezuko') {{
      triggerCurrentPetAction('burst', 6500);
      showSmartBubble({{
        type: 'alert',
        tag: '🚨 鬼杀队紧急配额告急 · 低于10%',
        zh: `🔥 唔嗯嗯！哥哥/主人快注意！你的【${{item.name}} · ${{item.period}}】剩余可用额度仅剩 <b style="color:#ef4444;font-size:14px;">${{item.pct}}%</b> 啦！鬼杀队物资告急，请合理规划提问节奏，注意体力分配哦~（${{item.reset}}）`,
        sub: "Conseil de combat : Économisez vos requêtes restantes.",
        actions: [
          {{ text: '🎋 查看看板', cls: 'bubble-act-primary', onClick: () => openMainCard() }},
          {{ text: '知道了', cls: 'bubble-act-subtle', onClick: () => hideSmartBubble() }}
        ]
      }}, 12000);
    }} else {{
      triggerCurrentPetAction('rose', 6500);
      showSmartBubble({{
        type: 'alert',
        tag: '🚨 B612星球能源告急 · 低于10%',
        zh: `🌹 糟糕了！你的【${{item.name}} · ${{item.period}}】额度只剩下 <b style="color:#ef4444;font-size:14px;">${{item.pct}}%</b> 了……就像小星球的水井快要见底一样。请小心节省使用，别让娇嫩的玫瑰花渴着了哦。（${{item.reset}}）`,
        sub: "L'eau est épuisée sur l'astéroïde B612. Protégez votre rose.",
        actions: [
          {{ text: '⭐ 查看看板', cls: 'bubble-act-primary', onClick: () => openMainCard() }},
          {{ text: '知道了', cls: 'bubble-act-subtle', onClick: () => hideSmartBubble() }}
        ]
      }}, 12000);
    }}
  }}

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
          const matchWeekly = text.match(/每周剩余可用配额[^\d]*(\d+)%/);
          if (matchWeekly) {{
            currentQuota.geminiWeeklyPct = parseInt(matchWeekly[1], 10);
            updated = true;
          }}
          const match5h = text.match(/5\s*小时剩余可用配额[^\d]*(\d+)%/);
          if (match5h) {{
            currentQuota.gemini5hPct = parseInt(match5h[1], 10);
            updated = true;
          }}
        }});
        if (updated) {{
          currentQuota.lastSynced = new Date().toLocaleTimeString('zh-CN', {{ hour12: false }});
          saveUserQuota(currentQuota);
          updateQuotaDisplay();
          checkQuotaAlert();
        }}
      }}
    }} catch (_) {{}}
  }}
  setInterval(sniffNativeQuotaFromDOM, 5000);

  // ==========================================
  // 六、工作时间过长久坐疲劳关怀引擎
  // ==========================================
  let workStartTime = Date.now();
  let lastActiveTime = Date.now();
  let continuousWorkMinutes = 0;
  let fatigueThresholdMinutes = parseInt(localStorage.getItem('__agy_fatigue_threshold__') || '45', 10);
  let fatigueAlertEnabled = localStorage.getItem('__agy_fatigue_alert_enabled__') !== 'false';
  let triggeredStages = {{ 30: false, 45: false, 60: false, 90: false, 120: false }};

  function onUserActive() {{
    const now = Date.now();
    // 离开电脑超过 10 分钟，自动视为已起身休息，重置工作计时
    if (now - lastActiveTime > 10 * 60 * 1000) {{
      workStartTime = now;
      continuousWorkMinutes = 0;
      triggeredStages = {{ 30: false, 45: false, 60: false, 90: false, 120: false }};
    }}
    lastActiveTime = now;
  }}

  window.addEventListener('mousemove', onUserActive, {{ passive: true }});
  window.addEventListener('keydown', onUserActive, {{ passive: true }});
  window.addEventListener('mousedown', onUserActive, {{ passive: true }});
  window.addEventListener('wheel', onUserActive, {{ passive: true }});

  function updateWorkTimeDisplay() {{
    const labelEl = document.getElementById('work-timer-label');
    if (!labelEl) return;
    if (continuousWorkMinutes < 60) {{
      labelEl.textContent = `${{continuousWorkMinutes}} 分钟`;
    }} else {{
      const h = Math.floor(continuousWorkMinutes / 60);
      const m = continuousWorkMinutes % 60;
      labelEl.textContent = `${{h}} 小时 ${{m}} 分钟`;
    }}
  }}

  function triggerFatigueAlertUI(minutes) {{
    petAudio.playCareSound();

    if (activePet === 'nezuko') {{
      triggerCurrentPetAction(minutes >= 60 ? 'sleep' : 'box', 7000);
      let zhMsg = '';
      if (minutes <= 45) {{
        zhMsg = `🍵 唔嗯嗯~ 主人你已经专注编码战斗 <b style="color:#6ee7b7;font-size:13px;">${{minutes}} 分钟</b> 啦！祢豆子给你倒了一杯大正热绿茶，快眨眨眼睛、活动活动手腕休息 2 分钟吧~`;
      }} else if (minutes <= 60) {{
        zhMsg = `📦 呼啊~（揉眼睛伸懒腰）你已经连续战斗整整 <b style="color:#6ee7b7;font-size:13px;">1 个小时</b> 啦！身体是斩鬼的本钱，快站起来走动走动，不然祢豆子要把你抱进木箱里强制休眠啦！`;
      }} else {{
        zhMsg = `😤 气鼓鼓！连续工作已经超过 <b style="color:#f87171;font-size:13px;">${{minutes}} 分钟</b> 超负荷啦！炭治郎哥哥说过身体是最珍贵的武器，现在立刻、马上离开屏幕走走，喝口水再来！`;
      }}

      showSmartBubble({{
        type: 'fatigue',
        tag: `🍵 祢豆子的久坐健康关怀 · 连续工作 ${{minutes}} 分钟`,
        zh: zhMsg,
        sub: "Un repos réparateur décuple la puissance du Souffle.",
        actions: [
          {{ text: '🙆 好的，休息5分钟', cls: 'bubble-act-green', onClick: () => resetWorkTimer() }},
          {{ text: '⏰ 稍后10分钟提醒', cls: 'bubble-act-subtle', onClick: () => delayFatigueAlert(10) }}
        ]
      }}, 14000);
    }} else {{
      triggerCurrentPetAction(minutes >= 60 ? 'sunset' : 'rose', 7000);
      let zhMsg = '';
      if (minutes <= 45) {{
        zhMsg = `✨ 在这颗繁忙的小星球上，你已经连续工作了 <b style="color:#6ee7b7;font-size:13px;">${{minutes}} 分钟</b>。停下来看一眼窗外吧，去喝一杯甘甜的清水，水对疲惫的眼睛也是有益的。`;
      }} else if (minutes <= 60) {{
        zhMsg = `🌅 你已经连续工作整整 <b style="color:#6ee7b7;font-size:13px;">1 小时</b> 了。那个每天不停点灯熄灯的点灯人，就是因为没有时间休息才那么忧伤的。站起来伸个懒腰，陪我去看一场第44次日落吧。`;
      }} else {{
        zhMsg = `🦊（小狐狸悄悄拉了拉你的衣角）即使是最重要的事务，过度劳累的眼睛也会看不清的。请离开屏幕 5 分钟，让大脑去星球的草地上散步一会儿。`;
      }}

      showSmartBubble({{
        type: 'fatigue',
        tag: `👑 小王子的久坐关怀 · 连续工作 ${{minutes}} 分钟`,
        zh: zhMsg,
        sub: "Prenez le temps d'apprivoiser le repos. Regardez le coucher de soleil.",
        actions: [
          {{ text: '🙆 去看日落休息', cls: 'bubble-act-green', onClick: () => resetWorkTimer() }},
          {{ text: '⏰ 稍后10分钟提醒', cls: 'bubble-act-subtle', onClick: () => delayFatigueAlert(10) }}
        ]
      }}, 14000);
    }}
  }}

  function resetWorkTimer() {{
    workStartTime = Date.now();
    lastActiveTime = Date.now();
    continuousWorkMinutes = 0;
    triggeredStages = {{ 30: false, 45: false, 60: false, 90: false, 120: false }};
    updateWorkTimeDisplay();
    hideSmartBubble();
    if (activePet === 'nezuko') triggerCurrentPetAction('sleep', 4000);
  }}

  function delayFatigueAlert(minutes) {{
    hideSmartBubble();
    setTimeout(() => {{
      triggerFatigueAlertUI(continuousWorkMinutes);
    }}, minutes * 60 * 1000);
  }}

  setInterval(() => {{
    const now = Date.now();
    if (now - lastActiveTime <= 10 * 60 * 1000) {{
      continuousWorkMinutes = Math.floor((now - workStartTime) / 60000);
    }} else {{
      continuousWorkMinutes = 0;
    }}
    updateWorkTimeDisplay();

    if (!fatigueAlertEnabled) return;
    const stages = [120, 90, 60, 45, 30];
    for (const stage of stages) {{
      if (continuousWorkMinutes >= stage && stage >= fatigueThresholdMinutes && !triggeredStages[stage]) {{
        triggeredStages[stage] = true;
        triggerFatigueAlertUI(stage);
        break;
      }}
    }}
  }}, 10000);

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
  // 七、CSS 样式库
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
      transform-origin: 50% 15%; z-index: 4;
    }}
    #bone-leg-r {{
      top: 178px; left: 62px; width: 28px; height: 37px;
      background-image: url('${{NEZUKO_LEG_R}}');
      transform-origin: 50% 15%; z-index: 4;
    }}

    /* 小王子立绘样式 */
    .prince-avatar-img {{
      width: 100%; height: 100%;
      object-fit: contain; pointer-events: none;
      filter: drop-shadow(0 6px 14px rgba(250, 204, 21, 0.25));
      transform-origin: bottom center;
      transition: transform 0.2s ease-out;
    }}

    /* 音乐节拍晃脑 */
    .head-music-bob {{ transform: rotate(7deg) scale(1.05) !important; }}
    .prince-music-bob {{ transform: rotate(5deg) scale(1.04) !important; }}

    /* 骨骼待机动画 */
    @keyframes boneBreathing {{
      0%, 100% {{ transform: translateY(0); }}
      50% {{ transform: translateY(4px); }}
    }}
    @keyframes headGentleTilt {{
      0%, 100% {{ transform: rotate(-2deg); }}
      50% {{ transform: rotate(3deg); }}
    }}
    @keyframes armSwayL {{
      0%, 100% {{ transform: rotate(-4deg); }}
      50% {{ transform: rotate(6deg); }}
    }}
    @keyframes armSwayR {{
      0%, 100% {{ transform: rotate(4deg); }}
      50% {{ transform: rotate(-6deg); }}
    }}

    .nezuko-pet-rig {{ animation: boneBreathing 3.6s infinite ease-in-out; }}
    .nezuko-pet-rig #bone-head {{ animation: headGentleTilt 4.2s infinite ease-in-out; }}
    .nezuko-pet-rig #bone-arm-l {{ animation: armSwayL 3.2s infinite ease-in-out; }}
    .nezuko-pet-rig #bone-arm-r {{ animation: armSwayR 3.2s infinite ease-in-out; }}

    .prince-pet-rig {{ animation: boneBreathing 3.8s infinite ease-in-out; }}
    .prince-pet-rig .prince-avatar-img {{ animation: headGentleTilt 4.5s infinite ease-in-out; }}

    /* 祢豆子 6 大动作 */
    .action-headpat #bone-head {{ transform: translateY(8px) scale(0.96) rotate(-4deg) !important; }}
    .action-headpat #bone-arm-l {{ transform: rotate(-25deg) !important; }}
    .action-headpat #bone-arm-r {{ transform: rotate(25deg) !important; }}

    .action-run #bone-arm-l {{ animation: armRunL 0.25s infinite alternate !important; }}
    .action-run #bone-arm-r {{ animation: armRunR 0.25s infinite alternate !important; }}
    .action-run #bone-leg-l {{ animation: legRunL 0.25s infinite alternate !important; }}
    .action-run #bone-leg-r {{ animation: legRunR 0.25s infinite alternate !important; }}
    .action-run #bone-head {{ animation: headBobRun 0.25s infinite alternate !important; }}
    @keyframes armRunL {{ 0% {{ transform: rotate(45deg); }} 100% {{ transform: rotate(-45deg); }} }}
    @keyframes armRunR {{ 0% {{ transform: rotate(-45deg); }} 100% {{ transform: rotate(45deg); }} }}
    @keyframes legRunL {{ 0% {{ transform: rotate(-40deg) translateY(-4px); }} 100% {{ transform: rotate(40deg); }} }}
    @keyframes legRunR {{ 0% {{ transform: rotate(40deg); }} 100% {{ transform: rotate(-40deg) translateY(-4px); }} }}
    @keyframes headBobRun {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-6px); }} }}

    .action-box {{ transform: scale(0.48) translateY(115px) !important; }}
    .action-stomp #bone-leg-r {{ animation: stompLeg 0.2s 8 alternate !important; }}
    .action-stomp #bone-head {{ animation: stompHead 0.2s 8 alternate !important; }}
    @keyframes stompLeg {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-16px) rotate(15deg); }} }}
    @keyframes stompHead {{ 0% {{ transform: rotate(-4deg); }} 100% {{ transform: rotate(5deg) translateY(2px); }} }}

    .action-burst {{
      filter: drop-shadow(0 0 25px rgba(220, 38, 38, 0.95)) drop-shadow(0 0 10px #f43f5e) !important;
      animation: burstShake 0.12s infinite alternate !important;
    }}
    @keyframes burstShake {{ 0% {{ transform: translateX(-3px); }} 100% {{ transform: translateX(3px); }} }}

    .action-sleep #bone-head {{ transform: translateY(12px) rotate(8deg) scale(0.96) !important; }}
    .action-sleep #bone-arm-r {{ transform: rotate(-35deg) translateY(-8px) !important; }}

    /* 小王子 6 大专属动效 */
    .action-scarf .prince-avatar-img {{
      animation: scarfWind 0.8s infinite ease-in-out alternate !important;
      filter: drop-shadow(0 0 15px rgba(250, 204, 21, 0.75)) !important;
    }}
    @keyframes scarfWind {{ 0% {{ transform: skewX(-5deg) rotate(-2deg); }} 100% {{ transform: skewX(6deg) rotate(4deg); }} }}

    .action-rose .prince-avatar-img {{
      transform: scale(1.06) translateY(-4px) !important;
      filter: drop-shadow(0 0 20px rgba(244, 63, 94, 0.8)) !important;
    }}
    .action-fox .prince-avatar-img {{
      transform: rotate(-6deg) translateY(6px) !important;
      filter: drop-shadow(0 0 16px rgba(249, 115, 22, 0.75)) !important;
    }}
    .action-stars .prince-avatar-img {{
      animation: starsFloat 1.2s infinite ease-in-out alternate !important;
      filter: drop-shadow(0 0 24px rgba(250, 204, 21, 0.9)) !important;
    }}
    @keyframes starsFloat {{ 0% {{ transform: translateY(0) scale(1); }} 100% {{ transform: translateY(-12px) scale(1.05); }} }}

    .action-sunset .prince-avatar-img {{
      filter: drop-shadow(0 0 20px rgba(234, 88, 12, 0.85)) hue-rotate(-15deg) !important;
      transform: scale(0.95) translateY(4px) !important;
    }}

    /* ========================================================= */
    /* 多态智能气泡引擎 (Smart Multi-State Bubble) */
    /* ========================================================= */
    .pet-smart-bubble {{
      position: absolute;
      bottom: calc(100% + 22px);
      left: 50%;
      transform: translateX(-50%) translateY(10px) scale(0.9);
      width: 275px;
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(30, 41, 59, 0.98) 100%);
      border: 1.5px solid var(--lp-star-gold);
      border-radius: 12px;
      padding: 10px 14px;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.65), 0 0 16px rgba(250, 204, 21, 0.3);
      pointer-events: none;
      opacity: 0;
      transition: all 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
      z-index: 150;
      backdrop-filter: blur(10px);
    }}
    .pet-smart-bubble.show {{
      opacity: 1 !important;
      pointer-events: auto !important;
      transform: translateX(-50%) translateY(0) scale(1) !important;
    }}
    .pet-smart-bubble::after {{
      content: ''; position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
      border: 8px solid transparent; border-top-color: var(--lp-star-gold);
    }}

    /* 额度低于10%告急警报模式 */
    .pet-smart-bubble.mode-alert {{
      background: linear-gradient(135deg, rgba(69, 10, 10, 0.97) 0%, rgba(35, 10, 10, 0.98) 100%) !important;
      border-color: #ef4444 !important;
      box-shadow: 0 12px 35px rgba(0, 0, 0, 0.75), 0 0 24px rgba(239, 68, 68, 0.6) !important;
      animation: alertPulseBorder 1.5s infinite alternate !important;
    }}
    .pet-smart-bubble.mode-alert::after {{
      border-top-color: #ef4444 !important;
    }}
    @keyframes alertPulseBorder {{
      0% {{ box-shadow: 0 0 12px rgba(239, 68, 68, 0.4); }}
      100% {{ box-shadow: 0 0 28px rgba(239, 68, 68, 0.9); border-color: #f87171; }}
    }}

    /* 久坐疲劳健康关怀模式 */
    .pet-smart-bubble.mode-fatigue {{
      background: linear-gradient(135deg, rgba(6, 78, 59, 0.96) 0%, rgba(15, 23, 42, 0.98) 100%) !important;
      border-color: #10b981 !important;
      box-shadow: 0 12px 35px rgba(0, 0, 0, 0.7), 0 0 20px rgba(16, 185, 129, 0.45) !important;
    }}
    .pet-smart-bubble.mode-fatigue::after {{
      border-top-color: #10b981 !important;
    }}

    .bubble-tag-bar {{
      display: flex; justify-content: space-between; align-items: center;
      font-size: 10px; font-weight: bold; margin-bottom: 5px;
    }}
    .bubble-tag-text {{
      color: var(--lp-star-gold); display: flex; align-items: center; gap: 4px;
    }}
    .mode-alert .bubble-tag-text {{ color: #fca5a5 !important; }}
    .mode-fatigue .bubble-tag-text {{ color: #6ee7b7 !important; }}

    .bubble-close-btn {{
      background: transparent; border: none; color: #94a3b8; font-size: 11px;
      cursor: pointer; padding: 2px 4px; border-radius: 4px; line-height: 1;
    }}
    .bubble-close-btn:hover {{ color: #fff; background: rgba(255, 255, 255, 0.15); }}

    .bubble-main-txt {{
      font-size: 12px; line-height: 1.55; color: #f8fafc; font-weight: 500;
    }}
    .mode-alert .bubble-main-txt {{ color: #fee2e2 !important; font-weight: 600; }}
    .mode-fatigue .bubble-main-txt {{ color: #ecfdf5 !important; }}

    .bubble-sub-txt {{
      font-size: 9.5px; color: #94a3b8; font-style: italic; margin-top: 4px; line-height: 1.35;
    }}

    .bubble-actions-row {{
      display: flex; gap: 6px; margin-top: 8px; justify-content: flex-end;
    }}
    .bubble-act-btn {{
      font-size: 10px; padding: 3px 8px; border-radius: 4px; cursor: pointer; border: 1px solid;
      transition: all 0.2s;
    }}
    .bubble-act-primary {{
      background: rgba(239, 68, 68, 0.25); border-color: #ef4444; color: #fecaca;
    }}
    .bubble-act-primary:hover {{ background: #ef4444; color: #fff; }}
    .bubble-act-green {{
      background: rgba(16, 185, 129, 0.25); border-color: #10b981; color: #a7f3d0;
    }}
    .bubble-act-green:hover {{ background: #10b981; color: #fff; }}
    .bubble-act-subtle {{
      background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.2); color: #cbd5e1;
    }}
    .bubble-act-subtle:hover {{ background: rgba(255, 255, 255, 0.2); color: #fff; }}

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

    /* QQ 音乐播放器控制区 */
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

    /* 配额项样式 */
    .nezuko-quota-row {{
      display: flex; align-items: center; justify-content: space-between;
      padding: 6px 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
    }}
    .nezuko-quota-row:last-child {{ border-bottom: none; }}
    .nezuko-quota-meta {{ display: flex; flex-direction: column; }}
    .nezuko-quota-name {{ font-size: 11px; color: #d1d5db; }}
    .nezuko-quota-reset {{ font-size: 9.5px; color: #9ca3af; }}
    .nezuko-quota-val-group {{ display: flex; align-items: center; gap: 8px; }}
    .nezuko-quota-pct {{ font-size: 12px; font-weight: 700; color: #ffd54f; min-width: 38px; text-align: right; }}

    .nezuko-ring-box {{ width: 26px; height: 26px; position: relative; }}
    .nezuko-ring-box svg {{ transform: rotate(-90deg); width: 26px; height: 26px; }}
    .nezuko-ring-bg {{ fill: none; stroke: rgba(255, 255, 255, 0.12); stroke-width: 3.5; }}
    .nezuko-ring-prog {{
      fill: none; stroke: #81c784; stroke-width: 3.5; stroke-linecap: round;
      stroke-dasharray: 62.83; stroke-dashoffset: 6.28; transition: stroke-dashoffset 0.6s ease;
    }}
  `;
  document.head.appendChild(styleEl);

  // ==========================================
  // 八、DOM 组装
  // ==========================================
  const root = document.createElement('div');
  root.id = 'nezuko-pet-root';
  root.innerHTML = `
    <div class="nezuko-pet-stage" id="nezuko-pet-stage">
      <div class="nezuko-pet-ground-shadow" id="nezuko-ground-shadow"></div>

      <!-- 智能多态交互气泡中枢 (名言 / 额度告急 / 久坐疲劳关怀) -->
      <div class="pet-smart-bubble" id="pet-smart-bubble">
        <div class="bubble-tag-bar">
          <span class="bubble-tag-text" id="bubble-tag-text">🦊 狐狸的秘密 · B612星球</span>
          <button class="bubble-close-btn" id="bubble-close-btn" title="关闭气泡">✕</button>
        </div>
        <div class="bubble-main-txt" id="bubble-main-txt">真正重要的东西，用眼睛是看不见的，只有用心才能看清。</div>
        <div class="bubble-sub-txt" id="bubble-sub-txt">L'essentiel est invisible pour les yeux.</div>
        <div class="bubble-actions-row" id="bubble-actions-row" style="display:none;"></div>
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

        <!-- 疲劳关怀与久坐健康提醒控制区 -->
        <div class="nezuko-section-box" style="background: rgba(16, 185, 129, 0.15); border-color: #10b981;">
          <div class="nezuko-section-title">
            <span style="color:#6ee7b7;">🍵 专注工作与久坐健康关怀</span>
            <span id="fatigue-status-tag" style="font-size:10px; color:#81c784;">● 已激活</span>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; font-size:11px; color:#d1fae5;">
            <span>当前已连续工作:</span>
            <b id="work-timer-label" style="color:#fde047; font-size:13px;">0 分钟</b>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="nezuko-ctrl-btn" id="btn-test-fatigue" style="flex:1; padding:5px; background:linear-gradient(135deg, #059669, #047857); border-color:#34d399; font-weight:bold;">
              🍵 立即体验久坐关怀
            </button>
            <button class="nezuko-ctrl-btn" id="btn-reset-work-timer" style="padding:5px 8px; background:rgba(255,255,255,0.1);" title="重置当前专注工作时间">
              🔄 重置计时
            </button>
          </div>
        </div>

        <!-- 额度低于10%及时预警设置区 -->
        <div class="nezuko-section-box" style="background: rgba(220, 38, 38, 0.15); border-color: #ef4444;">
          <div class="nezuko-section-title">
            <span style="color:#fca5a5;">🚨 额度极低及时告急提醒</span>
            <span id="quota-alert-status-tag" style="font-size:10px; color:#81c784;">● 配额充裕</span>
          </div>
          <div style="font-size:10px; color:#cbd5e1; margin-bottom:8px; line-height:1.4;">
            当 Gemini 或 Claude 配额低于 <b style="color:#ef4444;">10%</b> 时，桌宠将立即进行专属警报、跳动提醒并播放警示音！
          </div>
          <div style="display:flex; gap:6px;">
            <button class="nezuko-ctrl-btn" id="btn-test-quota-alert" style="flex:1; padding:5px; background:linear-gradient(135deg, #dc2626, #991b1b); border-color:#f87171; font-weight:bold;">
              🚨 模拟低于10%告急警报
            </button>
            <button class="nezuko-ctrl-btn" id="btn-mock-low-quota" style="padding:5px 8px; background:rgba(255,255,255,0.1);" title="将每周配额设定为 8% 进行真实测试">
              📉 设为8%
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
              <div class="nezuko-ring-box">
                <svg viewBox="0 0 26 26">
                  <circle class="nezuko-ring-bg" cx="13" cy="13" r="10" />
                  <circle class="nezuko-ring-prog" id="ring-gemini-weekly" cx="13" cy="13" r="10" />
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
              <div class="nezuko-ring-box">
                <svg viewBox="0 0 26 26">
                  <circle class="nezuko-ring-bg" cx="13" cy="13" r="10" />
                  <circle class="nezuko-ring-prog" id="ring-gemini-5h" cx="13" cy="13" r="10" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Claude 模型配额 (对应截图) -->
        <div class="nezuko-section-box">
          <div class="nezuko-section-title">
            <span>Claude 模型</span>
            <span style="font-size:10px; color:#81c784;">● 活跃</span>
          </div>
          <div class="nezuko-quota-row">
            <div class="nezuko-quota-meta">
              <span class="nezuko-quota-name">每周剩余可用配额</span>
              <span class="nezuko-quota-reset" id="lbl-claude-weekly-reset">${{currentQuota.claudeWeeklyReset}}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-claude-weekly-pct">${{currentQuota.claudeWeeklyPct}}%</span>
              <div class="nezuko-ring-box">
                <svg viewBox="0 0 26 26">
                  <circle class="nezuko-ring-bg" cx="13" cy="13" r="10" />
                  <circle class="nezuko-ring-prog" id="ring-claude-weekly" cx="13" cy="13" r="10" />
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
              <div class="nezuko-ring-box">
                <svg viewBox="0 0 26 26">
                  <circle class="nezuko-ring-bg" cx="13" cy="13" r="10" />
                  <circle class="nezuko-ring-prog" id="ring-claude-5h" cx="13" cy="13" r="10" />
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
  // 九、元素绑定与事件响应
  // ==========================================
  const stageEl = document.getElementById('nezuko-pet-stage');
  const petNezuko = document.getElementById('pet-nezuko');
  const petPrince = document.getElementById('pet-prince');
  const smartBubble = document.getElementById('pet-smart-bubble');
  const bubbleTagText = document.getElementById('bubble-tag-text');
  const bubbleCloseBtn = document.getElementById('bubble-close-btn');
  const bubbleMainTxt = document.getElementById('bubble-main-txt');
  const bubbleSubTxt = document.getElementById('bubble-sub-txt');
  const bubbleActionsRow = document.getElementById('bubble-actions-row');

  const mainCard = document.getElementById('nezuko-main-card');
  const openBtn = document.getElementById('nezuko-open-btn');
  const closeBtn = document.getElementById('nezuko-close-card');
  const actionBtnBox = document.getElementById('action-buttons-container');
  const boardTitleChar = document.getElementById('board-title-char');
  const boardRoleBadge = document.getElementById('board-role-badge');
  const curPetLabel = document.getElementById('cur-pet-label');
  const capsuleBar = document.getElementById('nezuko-action-capsule');
  const disc = document.getElementById('nezuko-disc');
  const quickMusicBtn = document.getElementById('btn-quick-music');
  const quickBoardBtn = document.getElementById('btn-quick-board');
  const soundWaves = document.getElementById('sound-waves');

  function openMainCard() {{
    mainCard.style.display = 'flex';
  }}
  function closeMainCard() {{
    mainCard.style.display = 'none';
  }}

  // 智能气泡通用驱动
  let smartBubbleHideTimer = null;
  function showSmartBubble(cfg, duration = 8000) {{
    smartBubble.className = 'pet-smart-bubble';
    if (cfg.type === 'alert') smartBubble.classList.add('mode-alert');
    else if (cfg.type === 'fatigue') smartBubble.classList.add('mode-fatigue');

    bubbleTagText.textContent = cfg.tag || '✦ 桌面守护';
    bubbleMainTxt.innerHTML = cfg.zh || '';
    bubbleSubTxt.textContent = cfg.sub || '';

    bubbleActionsRow.innerHTML = '';
    if (cfg.actions && cfg.actions.length > 0) {{
      bubbleActionsRow.style.display = 'flex';
      cfg.actions.forEach(act => {{
        const btn = document.createElement('button');
        btn.className = `bubble-act-btn ${{act.cls || 'bubble-act-subtle'}}`;
        btn.textContent = act.text;
        btn.onclick = (e) => {{
          e.stopPropagation();
          if (act.onClick) act.onClick();
        }};
        bubbleActionsRow.appendChild(btn);
      }});
    }} else {{
      bubbleActionsRow.style.display = 'none';
    }}

    smartBubble.classList.add('show');
    if (smartBubbleHideTimer) clearTimeout(smartBubbleHideTimer);
    if (duration > 0) {{
      smartBubbleHideTimer = setTimeout(() => hideSmartBubble(), duration);
    }}
  }}

  function hideSmartBubble() {{
    smartBubble.classList.remove('show');
    if (smartBubbleHideTimer) {{
      clearTimeout(smartBubbleHideTimer);
      smartBubbleHideTimer = null;
    }}
  }}

  bubbleCloseBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    hideSmartBubble();
  }});

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

  // 角色切换与动作渲染
  let activePet = getActivePet();
  let currentQuoteIndex = 0;
  let quoteAutoTimer = null;

  function showNextQuote() {{
    const q = LITTLE_PRINCE_QUOTES[currentQuoteIndex];
    currentQuoteIndex = (currentQuoteIndex + 1) % LITTLE_PRINCE_QUOTES.length;
    showSmartBubble({{
      type: 'quote',
      tag: q.tag + " · B612星球",
      zh: q.zh,
      sub: q.fr
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
      hideSmartBubble();
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

  // 小王子身体点击
  petPrince.addEventListener('click', (e) => {{
    if (isDragging) return;
    showNextQuote();
    triggerCurrentPetAction('rose', 2000);
  }});

  // 祢豆子身体点击
  petNezuko.addEventListener('click', (e) => {{
    if (isDragging) return;
    triggerCurrentPetAction('headpat', 2200);
  }});

  // 气泡点击
  smartBubble.addEventListener('click', (e) => {{
    e.stopPropagation();
    if (!smartBubble.classList.contains('mode-alert') && !smartBubble.classList.contains('mode-fatigue')) {{
      showNextQuote();
    }}
  }});

  // 疲劳与告急按钮交互绑定
  document.getElementById('btn-test-fatigue').addEventListener('click', () => {{
    triggerFatigueAlertUI(continuousWorkMinutes >= 30 ? continuousWorkMinutes : 45);
  }});
  document.getElementById('btn-reset-work-timer').addEventListener('click', () => {{
    resetWorkTimer();
  }});

  document.getElementById('btn-test-quota-alert').addEventListener('click', () => {{
    checkQuotaAlert(true);
  }});
  document.getElementById('btn-mock-low-quota').addEventListener('click', () => {{
    currentQuota.geminiWeeklyPct = 8;
    saveUserQuota(currentQuota);
    updateQuotaDisplay();
    checkQuotaAlert(true);
  }});

  document.getElementById('btn-toggle-ide-theme').addEventListener('click', () => {{
    const current = isIdeThemeEnabled();
    setIdeTheme(!current);
    document.getElementById('theme-status-tag').textContent = !current ? "● 已激活" : "○ 已关闭";
    document.getElementById('theme-status-tag').style.color = !current ? "#81c784" : "#9ca3af";
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

  // 拖拽引擎
  let isDragging = false;
  let startX = 0, startY = 0;
  let origRight = 32, origBottom = 24;

  const onDragDown = (e) => {{
    if (e.target.closest('.nezuko-action-capsule') || e.target.closest('.pet-smart-bubble')) return;
    isDragging = false;
    startX = e.clientX;
    startY = e.clientY;
    const rect = root.getBoundingClientRect();
    origRight = window.innerWidth - rect.right;
    origBottom = window.innerHeight - rect.bottom;

    const onMove = (ev) => {{
      const dx = ev.clientX - startX;
      const dy = ev.clientY - startY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {{
        isDragging = true;
        const currentRig = activePet === 'nezuko' ? petNezuko : petPrince;
        currentRig.classList.add('pet-picked-up');
        root.style.right = (origRight - dx) + 'px';
        root.style.bottom = (origBottom - dy) + 'px';
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

  // 配额更新展示
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
  updateWorkTimeDisplay();
  checkQuotaAlert();

}})();
"""

target_js = REPO_ROOT / "resources" / "nezuko-pet.js"
target_js.write_text(js_code, encoding="utf-8")
print(f"✅ 成功生成对接电脑 QQ 音乐与额度/疲劳提醒的桌宠组件: {target_js} ({len(js_code.encode('utf-8'))} 字节)")
