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

# 裁剪探头特写头像（用于木箱探头）
head_crop = im_nezuko.crop((15, 0, nw - 15, 175))
buf_head = BytesIO()
head_crop.save(buf_head, format='WEBP', quality=92)
b64_head_peeker = base64.b64encode(buf_head.getvalue()).decode('ascii')

# 2. 读取小王子核心与动作素材
prince_webp = MEDIA_DIR / "little_prince_pet.webp"
b64_prince = base64.b64encode(prince_webp.read_bytes()).decode('ascii')

prince_fox_webp = MEDIA_DIR / "prince_action_fox.webp"
b64_prince_fox = base64.b64encode(prince_fox_webp.read_bytes()).decode('ascii')

prince_rose_webp = MEDIA_DIR / "prince_asset_rose.webp"
b64_prince_rose = base64.b64encode(prince_rose_webp.read_bytes()).decode('ascii')

prince_sunset_webp = MEDIA_DIR / "prince_asset_sunset.webp"
b64_prince_sunset = base64.b64encode(prince_sunset_webp.read_bytes()).decode('ascii')

prince_stars_webp = MEDIA_DIR / "prince_asset_stars.webp"
b64_prince_stars = base64.b64encode(prince_stars_webp.read_bytes()).decode('ascii')

js_code = f"""// 灶门祢豆子 & 小王子 (B612) · 真实物理位移走动 + 3D转木箱神技 + 自主AI漫步巡航 + 动态眨眼与微表情 + QQ音乐联动 + 四维配额看板
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
  const NEZUKO_PEEKER_HEAD = "data:image/webp;base64,{b64_head_peeker}";

  const PRINCE_IMG = "data:image/webp;base64,{b64_prince}";
  const PRINCE_FOX_IMG = "data:image/webp;base64,{b64_prince_fox}";
  const PRINCE_ROSE_IMG = "data:image/webp;base64,{b64_prince_rose}";
  const PRINCE_SUNSET_IMG = "data:image/webp;base64,{b64_prince_sunset}";
  const PRINCE_STARS_IMG = "data:image/webp;base64,{b64_prince_stars}";

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
      const btn = document.getElementById('m-btn-wake-qq');
      if (btn) {{
        const origTxt = btn.innerHTML;
        btn.innerHTML = '✨ 唤醒中...';
        setTimeout(() => {{ btn.innerHTML = origTxt; }}, 2000);
      }}
      if (typeof showSmartBubble === 'function') {{
        showSmartBubble({{
          type: 'notice',
          tag: '🎵 本地 QQ 音乐联动',
          zh: '🚀 <b>正在呼出 QQ 音乐主界面！</b><br>已检测到本地客户端路径并拉起，窗口即将前置显示~',
          sub: 'Ouverture de la fenêtre QQ Music en cours...'
        }}, 4000);
      }}
    }}
  }}

  const qqBridge = new QQMusicBridgeEngine();

  // ==========================================
  // 二、Web Audio 拟真音效引擎 (木箱/风刃/碎步/警报/关怀)
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
    // 疲劳健康关怀音效（三和弦轻灵水滴声）
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
    // 木箱落地厚重沉闷沉木声
    playWoodThud() {{
      try {{
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(140, now);
        osc.frequency.exponentialRampToValueAtTime(45, now + 0.18);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.23);
      }} catch (_) {{}}
    }}
    // 转木箱高速风刃呼啸旋转声
    playSpinWind() {{
      try {{
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(280, now);
        osc.frequency.linearRampToValueAtTime(650, now + 0.3);
        osc.frequency.linearRampToValueAtTime(220, now + 0.7);
        gain.gain.setValueAtTime(0.01, now);
        gain.gain.linearRampToValueAtTime(0.12, now + 0.25);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.75);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.76);
      }} catch (_) {{}}
    }}
    // 奔跑轻快卡通碎步小节拍
    playFootstep() {{
      try {{
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(420, now);
        gain.gain.setValueAtTime(0.04, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.07);
      }} catch (_) {{}}
    }}
  }}

  const petAudio = new PetAudioSynth();

  // ==========================================
  // 三、《小王子》12 句经典哲思名言库
  // ==========================================
  const LITTLE_PRINCE_QUOTES = [
    {{ zh: "真正重要的东西，用眼睛是看不见的，只有用心才能看清。", fr: "L'essentiel est invisible pour les yeux.", tag: "🦊 狐狸的秘密" }},
    {{ zh: "如果你说你在下午四点来，从三点开始，我就开始感觉很快乐。", fr: "Si tu viens à quatre heures de l'après-midi, dès trois heures je commencerai d'être heureux.", tag: "🦊 期待的幸福" }},
    {{ zh: "你在你的玫瑰花身上耗费的时间，使得你的玫瑰花变得如此重要。", fr: "C'est le temps que tu as perdu pour ta rose qui fait ta rose si importante.", tag: "🌹 爱的驯养" }},
    {{ zh: "星星发亮，是为了让每一个人有一天都能找到属于自己的星星。", fr: "Les étoiles sont éclairées pour que chacun puisse un jour retrouver la sienne.", tag: "✨ 漫天繁星" }},
    {{ zh: "所有的大人都曾经是小孩，虽然，只有少数的人记得。", fr: "Toutes les grandes personnes ont d'abord été des enfants.", tag: "👑 永恒的童心" }},
    {{ zh: "天上的星星有亿万颗，唯独只有一颗星上开着我的花，只要仰望星空，就会感到幸福。", fr: "Si quelqu'un aime une fleur unique, cela suffit pour qu'il soit heureux.", tag: "🌟 独一无二" }},
    {{ zh: "当你驯养了我，我们就会彼此需要。对我来说，你就是世界上唯一的。", fr: "Tu seras pour moi unique au monde. Je serai pour toi unique au monde.", tag: "🦊 羁绊与陪伴" }},
    {{ zh: "一个人只有在感到悲伤的时候，才会喜欢看日落... ‘有一天，我看了四十四次日落。’", fr: "Un jour, j'ai vu le soleil se coucher quarante-quatre fois...", tag: "🌅 B612的黄昏" }},
    {{ zh: "沙漠之所以美丽，是因为在某个角落，藏着一口清泉。", fr: "Ce qui embellit le désert, c'est qu'il cache un puits quelque part.", tag: "💧 心灵的甘泉" }},
    {{ zh: "我就在其中的一颗星星上微笑着。当你夜晚仰望星空时，就好像所有的星星都在对你微笑。", fr: "Alors ce sera pour toi comme si riaient toutes les étoiles.", tag: "🌠 会笑的星星" }},
    {{ zh: "审判自己比审判别人要难得多。如果你能正确地审判自己，你就是一个真正有智慧的人。", fr: "Il est bien plus difficile de se juger soi-même que de juger autrui.", tag: "⚖️ 自省与智慧" }},
    {{ zh: "即使在人群中，人也一样会感到孤单。用心去寻找，才能找到真正的陪伴。", fr: "On est un peu seul dans le désert... On est seul aussi chez les hommes.", tag: "🌌 星际旅途" }}
  ];

  function getActivePet() {{
    return localStorage.getItem('__agy_active_pet_character__') || 'nezuko';
  }}
  function setActivePet(name) {{
    localStorage.setItem('__agy_active_pet_character__', name);
  }}

  // ==========================================
  // 四、Antigravity 界面鬼灭主题
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
    .tab.active {{
      background: linear-gradient(180deg, rgba(46, 26, 20, 0.9) 0%, #1f120d 100%) !important;
      border-top: 2.5px solid #f48fb1 !important; color: #fff !important;
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
  // 五、模型配额与同步体系
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

  function sniffNativeQuotaFromDOM() {{
    let updated = false;
    try {{
      const textNodes = [];
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
      let node;
      while (node = walker.nextNode()) {{
        const txt = node.nodeValue.trim();
        if (!txt) continue;
        if (
          txt.includes('每周剩余') || txt.includes('Weekly limit') || txt.includes('Weekly request') ||
          txt.includes('5 小时') || txt.includes('5小时') || txt.includes('5-hour') || txt.includes('5h limit') ||
          txt.includes('剩余可用配额') || txt.includes('Remaining quota')
        ) {{
          textNodes.push(node);
        }}
      }}

      textNodes.forEach(tn => {{
        const container = tn.parentElement ? (tn.parentElement.closest('.quota-section, .monaco-list-row, div') || tn.parentElement) : null;
        if (!container) return;
        const text = container.textContent || '';

        const mGW = text.match(/(?:每周|Weekly)[^\d%]*?(\d{1,3})%/i);
        if (mGW) {{
          const val = parseInt(mGW[1], 10);
          if (val >= 0 && val <= 100) {{ currentQuota.geminiWeeklyPct = val; updated = true; }}
        }}
        const mG5 = text.match(/(?:5\s*(?:小时|hour|h))[^\d%]*?(\d{1,3})%/i);
        if (mG5) {{
          const val = parseInt(mG5[1], 10);
          if (val >= 0 && val <= 100) {{ currentQuota.gemini5hPct = val; updated = true; }}
        }}

        if (text.toLowerCase().includes('claude') || text.toLowerCase().includes('gpt')) {{
          const mCW = text.match(/(?:每周|Weekly)[^\d%]*?(\d{1,3})%/i);
          if (mCW) {{ currentQuota.claudeWeeklyPct = parseInt(mCW[1], 10); updated = true; }}
          const mC5 = text.match(/(?:5\s*(?:小时|hour|h))[^\d%]*?(\d{1,3})%/i);
          if (mC5) {{ currentQuota.claude5hPct = parseInt(mC5[1], 10); updated = true; }}
        }}
      }});

      if (updated) {{
        currentQuota.lastSynced = new Date().toLocaleTimeString('zh-CN', {{ hour12: false }});
        saveUserQuota(currentQuota);
        updateQuotaDisplay();
        checkQuotaAlert();
      }}
    }} catch (_) {{}}
    return updated;
  }}
  setInterval(sniffNativeQuotaFromDOM, 5000);

  let lastQuotaAlertKey = '';
  let lastQuotaAlertTime = 0;
  let quotaAlertEnabled = localStorage.getItem('__agy_quota_alert_enabled__') !== 'false';

  function checkQuotaAlert(force = false) {{
    if (!quotaAlertEnabled && !force) return false;
    const alertItems = [];
    if (currentQuota.geminiWeeklyPct <= 10) alertItems.push({{ name: 'Gemini 模型', period: '每周配额', pct: currentQuota.geminiWeeklyPct, reset: currentQuota.geminiWeeklyReset }});
    if (currentQuota.gemini5hPct <= 10) alertItems.push({{ name: 'Gemini 模型', period: '5小时配额', pct: currentQuota.gemini5hPct, reset: currentQuota.gemini5hReset }});
    if (currentQuota.claudeWeeklyPct <= 10) alertItems.push({{ name: 'Claude 模型', period: '每周配额', pct: currentQuota.claudeWeeklyPct, reset: currentQuota.claudeWeeklyReset }});
    if (currentQuota.claude5hPct <= 10) alertItems.push({{ name: 'Claude 模型', period: '5小时配额', pct: currentQuota.claude5hPct, reset: currentQuota.claude5hReset }});

    const alertTag = document.getElementById('quota-alert-status-tag');
    if (alertTag) {{
      alertTag.textContent = alertItems.length > 0 ? '🚨 告急 (低于10%)' : '● 配额充裕';
      alertTag.style.color = alertItems.length > 0 ? '#ef4444' : '#81c784';
    }}
    if (alertItems.length === 0) return false;

    const now = Date.now();
    const alertKey = alertItems.map(it => `${{it.name}}_${{it.period}}_${{it.pct}}`).join('|');
    if (!force && lastQuotaAlertKey === alertKey && (now - lastQuotaAlertTime < 15 * 60 * 1000)) return false;
    lastQuotaAlertKey = alertKey;
    lastQuotaAlertTime = now;

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

  // ==========================================
  // 六、久坐疲劳健康关怀引擎
  // ==========================================
  let workStartTime = Date.now();
  let lastActiveTime = Date.now();
  let continuousWorkMinutes = 0;
  let fatigueThresholdMinutes = parseInt(localStorage.getItem('__agy_fatigue_threshold__') || '45', 10);
  let fatigueAlertEnabled = localStorage.getItem('__agy_fatigue_alert_enabled__') !== 'false';
  let triggeredStages = {{ 30: false, 45: false, 60: false, 90: false, 120: false }};

  function onUserActive() {{
    const now = Date.now();
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
    if (continuousWorkMinutes < 60) labelEl.textContent = `${{continuousWorkMinutes}} 分钟`;
    else {{
      const h = Math.floor(continuousWorkMinutes / 60);
      const m = continuousWorkMinutes % 60;
      labelEl.textContent = `${{h}} 小时 ${{m}} 分钟`;
    }}
  }}

  function triggerFatigueAlertUI(minutes) {{
    petAudio.playCareSound();
    if (activePet === 'nezuko') {{
      triggerCurrentPetAction(minutes >= 60 ? 'sleep' : 'box-peek', 7000);
      let zhMsg = minutes <= 45 
        ? `🍵 唔嗯嗯~ 主人你已经专注编码战斗 <b style="color:#6ee7b7;font-size:13px;">${{minutes}} 分钟</b> 啦！祢豆子给你倒了一杯大正热绿茶，快眨眨眼睛、活动活动手腕休息 2 分钟吧~`
        : `📦 呼啊~（揉眼睛伸懒腰）你已经连续战斗整整 <b style="color:#6ee7b7;font-size:13px;">${{minutes}} 分钟</b> 啦！身体是斩鬼的本钱，快站起来走动走动，不然祢豆子要把你抱进木箱里强制休眠啦！`;
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
      let zhMsg = `✨ 在这颗繁忙的小星球上，你已经连续工作了 <b style="color:#6ee7b7;font-size:13px;">${{minutes}} 分钟</b>。停下来看一眼窗外吧，去喝一杯甘甜的清水。陪我去看一场第44次日落吧。`;
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
    setTimeout(() => triggerFatigueAlertUI(continuousWorkMinutes), minutes * 60 * 1000);
  }}

  setInterval(() => {{
    const now = Date.now();
    continuousWorkMinutes = (now - lastActiveTime <= 10 * 60 * 1000) ? Math.floor((now - workStartTime) / 60000) : 0;
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
  // 七、生动 CSS 动画与 3D 雾云杉木箱样式库
  // ==========================================
  const styleEl = document.createElement('style');
  styleEl.id = 'dual-pet-advanced-styles-v3';
  styleEl.textContent = `
    :root {{
      --ds-pink: #f48fb1;
      --ds-dark-pink: #c2185b;
      --ds-crimson: #b71c1c;
      --ds-tanjiro-green: #2e7d32;
      --ds-wood-dark: #231612;
      --ds-wood-border: #140d0a;
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
      transition: right 0.8s cubic-bezier(0.25, 1, 0.5, 1), bottom 0.3s ease;
    }}

    .nezuko-pet-stage {{
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      transform-origin: bottom center;
      transition: transform 0.25s ease-out;
    }}

    .nezuko-pet-ground-shadow {{
      position: absolute;
      bottom: -6px;
      left: 50%;
      transform: translateX(-50%);
      width: 105px;
      height: 15px;
      background: radial-gradient(ellipse at center, rgba(10, 5, 8, 0.5) 0%, rgba(10, 5, 8, 0.15) 50%, transparent 75%);
      border-radius: 50%;
      pointer-events: none;
      transition: all 0.28s ease;
    }}

    .nezuko-pet-rig, .prince-pet-rig {{
      position: relative;
      width: 130px;
      height: 215px;
      cursor: grab;
      filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.2));
      transition: transform 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
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

    /* 动态自然眨眼系统 (Blinking Eyelid Overlay) */
    .nezuko-eyelid-overlay {{
      position: absolute;
      top: 48px;
      left: 38px;
      width: 54px;
      height: 24px;
      pointer-events: none;
      z-index: 12;
      opacity: 0;
      background: radial-gradient(ellipse at center, #ffd1c1 0%, #ffc0b0 70%, transparent 100%);
      border-radius: 50%;
      transform: scaleY(0);
      transition: transform 0.08s ease-in, opacity 0.08s ease-in;
    }}
    .is-blinking .nezuko-eyelid-overlay {{
      opacity: 1 !important;
      transform: scaleY(1) !important;
    }}

    /* 浮动情绪微表情 (Mood Emoticons) */
    .floating-mood-bubble {{
      position: absolute;
      top: -12px;
      right: 15px;
      font-size: 16px;
      pointer-events: none;
      opacity: 0;
      transform: translateY(0) scale(0.6);
      transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
      z-index: 40;
      filter: drop-shadow(0 2px 5px rgba(0,0,0,0.4));
    }}
    .floating-mood-bubble.active {{
      opacity: 1;
      transform: translateY(-16px) scale(1.1);
    }}

    /* 待机自然呼吸 */
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

    /* ========================================================= */
    /* 核心一：生动真实走动与狂奔位移动画 (Walking & Running) */
    /* ========================================================= */
    .is-walking {{
      animation: walkBobbing 0.5s infinite ease-in-out alternate !important;
    }}
    @keyframes walkBobbing {{
      0% {{ transform: translateY(0) rotate(1deg); }}
      100% {{ transform: translateY(-4px) rotate(-1deg); }}
    }}
    .is-walking #bone-leg-l {{
      animation: walkLegL 0.5s infinite alternate ease-in-out !important;
    }}
    .is-walking #bone-leg-r {{
      animation: walkLegR 0.5s infinite alternate ease-in-out !important;
    }}
    .is-walking #bone-arm-l {{
      animation: walkArmL 0.5s infinite alternate ease-in-out !important;
    }}
    .is-walking #bone-arm-r {{
      animation: walkArmR 0.5s infinite alternate ease-in-out !important;
    }}
    @keyframes walkLegL {{ 0% {{ transform: rotate(-24deg); }} 100% {{ transform: rotate(24deg); }} }}
    @keyframes walkLegR {{ 0% {{ transform: rotate(24deg); }} 100% {{ transform: rotate(-24deg); }} }}
    @keyframes walkArmL {{ 0% {{ transform: rotate(20deg); }} 100% {{ transform: rotate(-20deg); }} }}
    @keyframes walkArmR {{ 0% {{ transform: rotate(-20deg); }} 100% {{ transform: rotate(20deg); }} }}

    /* 狂奔冲刺态 (High-Speed Dash Run) */
    .is-running {{
      animation: runBobbing 0.22s infinite alternate ease-in-out !important;
    }}
    @keyframes runBobbing {{
      0% {{ transform: translateY(0) skewX(-6deg); }}
      100% {{ transform: translateY(-7px) skewX(4deg); }}
    }}
    .is-running #bone-arm-l {{ animation: armRunL 0.22s infinite alternate !important; }}
    .is-running #bone-arm-r {{ animation: armRunR 0.22s infinite alternate !important; }}
    .is-running #bone-leg-l {{ animation: legRunL 0.22s infinite alternate !important; }}
    .is-running #bone-leg-r {{ animation: legRunR 0.22s infinite alternate !important; }}
    .is-running #bone-head {{ animation: headBobRun 0.22s infinite alternate !important; }}
    @keyframes armRunL {{ 0% {{ transform: rotate(55deg); }} 100% {{ transform: rotate(-55deg); }} }}
    @keyframes armRunR {{ 0% {{ transform: rotate(-55deg); }} 100% {{ transform: rotate(55deg); }} }}
    @keyframes legRunL {{ 0% {{ transform: rotate(-50deg) translateY(-5px); }} 100% {{ transform: rotate(50deg); }} }}
    @keyframes legRunR {{ 0% {{ transform: rotate(50deg); }} 100% {{ transform: rotate(-50deg) translateY(-5px); }} }}
    @keyframes headBobRun {{ 0% {{ transform: translateY(0) rotate(-3deg); }} 100% {{ transform: translateY(-7px) rotate(4deg); }} }}

    /* 冲刺扬尘粒子 (Dust Clouds) */
    .dash-dust-container {{
      position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
      pointer-events: none; width: 100px; height: 30px; z-index: 2;
    }}
    .dust-puff {{
      position: absolute; bottom: 0; width: 14px; height: 14px; border-radius: 50%;
      background: rgba(220, 200, 180, 0.7); opacity: 0;
      animation: dustFloat 0.5s ease-out forwards;
    }}
    @keyframes dustFloat {{
      0% {{ transform: translate(0, 0) scale(0.5); opacity: 0.8; }}
      100% {{ transform: translate(var(--dust-x, -25px), -18px) scale(1.6); opacity: 0; }}
    }}

    /* 刹车滑行 (Skid Stop) */
    .action-skid {{
      transform: skewX(-14deg) translateY(2px) !important;
      transition: transform 0.25s ease-out;
    }}

    /* 摸头动作 */
    .action-headpat #bone-head {{ transform: translateY(9px) scale(0.95) rotate(-5deg) !important; }}
    .action-headpat #bone-arm-l {{ transform: rotate(-28deg) !important; }}
    .action-headpat #bone-arm-r {{ transform: rotate(28deg) !important; }}

    /* 跺小脚与震动波 (Stomp Shockwave) */
    .action-stomp #bone-leg-r {{ animation: stompLeg 0.18s 8 alternate !important; }}
    .action-stomp #bone-head {{ animation: stompHead 0.18s 8 alternate !important; }}
    @keyframes stompLeg {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-18px) rotate(18deg); }} }}
    @keyframes stompHead {{ 0% {{ transform: rotate(-6deg); }} 100% {{ transform: rotate(6deg) translateY(3px); }} }}

    .stomp-ripple {{
      position: absolute; bottom: -4px; left: 50%; transform: translateX(-50%);
      width: 20px; height: 8px; border: 2px solid #ef4444; border-radius: 50%;
      opacity: 0; pointer-events: none;
    }}
    .action-stomp .stomp-ripple {{
      animation: rippleExpand 0.36s 4 ease-out !important;
    }}
    @keyframes rippleExpand {{
      0% {{ width: 20px; height: 8px; opacity: 0.9; }}
      100% {{ width: 90px; height: 20px; opacity: 0; }}
    }}

    /* 血鬼术·爆血觉醒 */
    .action-burst {{
      filter: drop-shadow(0 0 25px rgba(220, 38, 38, 0.95)) drop-shadow(0 0 12px #f43f5e) !important;
      animation: burstShake 0.1s infinite alternate !important;
    }}
    @keyframes burstShake {{ 0% {{ transform: translateX(-4px) scale(1.02); }} 100% {{ transform: translateX(4px) scale(1.04); }} }}

    .action-sleep #bone-head {{ transform: translateY(14px) rotate(9deg) scale(0.95) !important; }}
    .action-sleep #bone-arm-r {{ transform: rotate(-38deg) translateY(-8px) !important; }}

    /* ========================================================= */
    /* 核心二：大正雾云杉木箱 (3D立体渲染与华丽转木箱动作) */
    /* ========================================================= */
    .box-action-container {{
      position: absolute;
      top: 25px;
      left: 50%;
      transform: translateX(-50%);
      width: 120px;
      height: 165px;
      perspective: 700px;
      z-index: 25;
      display: none;
      pointer-events: none;
    }}
    .show-box-action {{
      display: block !important;
      pointer-events: auto !important;
    }}

    /* 3D 木箱本体 */
    .ds-3d-box {{
      position: relative;
      width: 100%;
      height: 100%;
      transform-style: preserve-3d;
      transform-origin: center center;
      transition: transform 0.35s ease;
    }}

    /* 箱身外观 (大正雾云杉木质纹理与金属包角) */
    .ds-box-body {{
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, #422518 0%, #2b160f 45%, #1c0e09 100%);
      border: 3px solid #140b07;
      border-radius: 6px;
      box-shadow: inset 0 0 12px rgba(0,0,0,0.7), 0 8px 20px rgba(0,0,0,0.6);
      overflow: hidden;
    }}
    /* 木纹条纹装饰 */
    .ds-box-body::before {{
      content: '';
      position: absolute;
      inset: 4px;
      background: repeating-linear-gradient(90deg, transparent 0, transparent 20px, rgba(0,0,0,0.18) 20px, rgba(0,0,0,0.18) 22px);
      border: 1px solid rgba(197, 155, 39, 0.25);
      border-radius: 3px;
      pointer-events: none;
    }}

    /* 4 个黑色精铁包角与金色铆钉 */
    .ds-box-bracket {{
      position: absolute;
      width: 16px;
      height: 16px;
      background: #111;
      border: 1px solid #444;
      z-index: 10;
    }}
    .ds-box-bracket::after {{
      content: '';
      position: absolute;
      width: 4px;
      height: 4px;
      background: #c59b27;
      border-radius: 50%;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      box-shadow: 0 0 2px #ffe082;
    }}
    .ds-box-bracket.tl {{ top: 2px; left: 2px; border-top: 2.5px solid #222; border-left: 2.5px solid #222; }}
    .ds-box-bracket.tr {{ top: 2px; right: 2px; border-top: 2.5px solid #222; border-right: 2.5px solid #222; }}
    .ds-box-bracket.bl {{ bottom: 2px; left: 2px; border-bottom: 2.5px solid #222; border-left: 2.5px solid #222; }}
    .ds-box-bracket.br {{ bottom: 2px; right: 2px; border-bottom: 2.5px solid #222; border-right: 2.5px solid #222; }}

    /* 顶部炭治郎同款双肩金属提梁 */
    .ds-box-top-handle {{
      position: absolute;
      top: -10px;
      left: 50%;
      transform: translateX(-50%);
      width: 48px;
      height: 10px;
      border: 2.5px solid #222;
      border-bottom: none;
      border-radius: 4px 4px 0 0;
      background: linear-gradient(180deg, #555, #222);
      box-shadow: 0 2px 4px rgba(0,0,0,0.4);
    }}

    /* 黑色强化横梁铁条 */
    .ds-box-steel-strap {{
      position: absolute;
      left: 0; right: 0;
      height: 9px;
      background: linear-gradient(180deg, #333 0%, #1a1a1a 100%);
      border-top: 1px solid #555;
      border-bottom: 1px solid #000;
      z-index: 8;
    }}
    .ds-box-steel-strap.top {{ top: 40px; }}
    .ds-box-steel-strap.mid {{ top: 80px; }}
    .ds-box-steel-strap.bot {{ top: 120px; }}

    /* 箱内暗室与祢豆子探头特写层 (Interior Peeker) */
    .ds-box-interior {{
      position: absolute;
      inset: 8px 12px;
      background: #0d0604;
      border-radius: 4px;
      box-shadow: inset 0 0 16px rgba(0,0,0,0.9);
      overflow: hidden;
      z-index: 4;
      display: flex;
      justify-content: center;
      align-items: flex-end;
    }}
    .peeker-chibi-img {{
      width: 100px;
      height: 120px;
      object-fit: contain;
      transform: translateY(25px) scale(0.9);
      transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
      filter: drop-shadow(0 -4px 8px rgba(0,0,0,0.5));
    }}

    /* 真实 3D 可旋转开启的木箱门 (3D Hinged Door) */
    .ds-box-door {{
      position: absolute;
      inset: 8px 10px;
      background: linear-gradient(180deg, #4a281a 0%, #351a10 50%, #200f09 100%);
      border: 2px solid #140b07;
      border-radius: 3px;
      transform-origin: left center;
      transform-style: preserve-3d;
      transition: transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
      z-index: 12;
      box-shadow: inset 0 0 8px rgba(0,0,0,0.6), 2px 0 6px rgba(0,0,0,0.5);
    }}
    /* 门环与门锁 */
    .ds-door-ring {{
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      width: 14px;
      height: 14px;
      border: 2px solid #c59b27;
      border-radius: 50%;
      box-shadow: 0 1px 4px rgba(0,0,0,0.8);
      background: rgba(0,0,0,0.2);
    }}
    .ds-door-ring::before {{
      content: '';
      position: absolute;
      top: -3px; left: 3px;
      width: 4px; height: 4px;
      background: #ffe082;
      border-radius: 50%;
    }}

    /* 动效 1：华丽 3D 转木箱动作 (Spin Box Whirlwind) */
    .action-box-spin .ds-3d-box {{
      animation: spinBox3D 1.2s cubic-bezier(0.2, 0.8, 0.2, 1) forwards !important;
    }}
    @keyframes spinBox3D {{
      0% {{
        transform: translateY(0) scale(1) rotateY(0deg) rotateX(0deg);
      }}
      25% {{
        transform: translateY(-46px) scale(1.08) rotateY(200deg) rotateX(12deg);
      }}
      50% {{
        transform: translateY(-52px) scale(1.12) rotateY(420deg) rotateX(-8deg);
      }}
      75% {{
        transform: translateY(-28px) scale(1.05) rotateY(640deg) rotateX(6deg);
      }}
      90% {{
        transform: translateY(3px) scale(1.08, 0.94) rotateY(720deg) rotateX(0deg);
      }}
      100% {{
        transform: translateY(0) scale(1) rotateY(720deg) rotateX(0deg);
      }}
    }}

    /* 转木箱飞旋的风刃与枫叶樱花粒子 */
    .box-spin-particles {{
      position: absolute;
      inset: -30px;
      pointer-events: none;
      z-index: 30;
      opacity: 0;
    }}
    .action-box-spin .box-spin-particles {{
      opacity: 1 !important;
    }}
    .spin-petal {{
      position: absolute;
      font-size: 16px;
      opacity: 0;
    }}
    .action-box-spin .spin-petal.sp1 {{
      top: 20px; left: -10px; animation: petalBurst 1s ease-out 0.1s;
    }}
    .action-box-spin .spin-petal.sp2 {{
      top: 10px; right: -15px; animation: petalBurst 1s ease-out 0.25s;
    }}
    .action-box-spin .spin-petal.sp3 {{
      bottom: 20px; left: -15px; animation: petalBurst 1s ease-out 0.35s;
    }}
    .action-box-spin .spin-petal.sp4 {{
      bottom: 10px; right: -10px; animation: petalBurst 1s ease-out 0.45s;
    }}
    @keyframes petalBurst {{
      0% {{ transform: translate(30px, 30px) rotate(0deg) scale(0.4); opacity: 0; }}
      30% {{ opacity: 1; transform: translate(var(--tx, -40px), var(--ty, -30px)) rotate(180deg) scale(1.2); }}
      100% {{ opacity: 0; transform: translate(var(--tx, -70px), var(--ty, -50px)) rotate(360deg) scale(0.8); }}
    }}

    /* 动效 2：钻木箱与探头探脑动作 (Peek-a-boo Box) */
    .action-box-peek .ds-box-door {{
      transform: rotateY(-115deg) !important;
    }}
    .action-box-peek .peeker-chibi-img {{
      transform: translateY(0) scale(1.04) !important;
    }}
    .action-box-peek .ds-3d-box {{
      animation: boxWobblePeek 0.6s ease-in-out !important;
    }}
    @keyframes boxWobblePeek {{
      0%, 100% {{ transform: rotate(0deg); }}
      30% {{ transform: rotate(-3deg); }}
      70% {{ transform: rotate(3deg); }}
    }}

    /* 小王子立绘样式 */
    .prince-avatar-img {{
      width: 100%; height: 100%;
      object-fit: contain; pointer-events: none;
      filter: drop-shadow(0 6px 14px rgba(250, 204, 21, 0.25));
      transform-origin: bottom center;
      transition: transform 0.2s ease-out;
    }}

    /* 音乐晃脑 */
    .head-music-bob {{ transform: rotate(7deg) scale(1.05) !important; }}
    .prince-music-bob {{ transform: rotate(5deg) scale(1.04) !important; }}

    /* 小王子动作层 */
    .prince-action-layer {{
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      pointer-events: none; opacity: 0; transition: opacity 0.35s ease, transform 0.35s ease;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      z-index: 20;
    }}
    .action-fox #layer-action-fox {{ opacity: 1 !important; pointer-events: auto !important; }}
    .action-fox #prince-avatar-body {{ opacity: 0 !important; transform: scale(0.95); }}
    .prince-fox-img {{
      width: 100%; height: 100%; object-fit: contain;
      filter: drop-shadow(0 8px 18px rgba(249, 115, 22, 0.45));
      animation: foxCuddle 1.8s infinite ease-in-out;
      transform-origin: bottom center;
    }}
    @keyframes foxCuddle {{
      0%, 100% {{ transform: translateY(0) rotate(0deg) scale(1); }}
      30% {{ transform: translateY(-4px) rotate(-2deg) scale(1.03); }}
      70% {{ transform: translateY(-2px) rotate(2deg) scale(1.02); }}
    }}

    .action-rose #layer-action-rose {{ opacity: 1 !important; pointer-events: auto !important; }}
    .action-rose #prince-avatar-body {{
      transform: scale(1.04) translateY(-3px) rotate(-1deg) !important;
      filter: drop-shadow(0 0 20px rgba(244, 63, 94, 0.7)) !important;
    }}
    .rose-dome-img {{
      position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
      width: 140px; height: 175px; object-fit: contain;
      animation: roseDomeRise 2.5s infinite ease-in-out alternate;
      filter: drop-shadow(0 0 16px rgba(244, 63, 94, 0.85));
    }}
    @keyframes roseDomeRise {{
      0% {{ transform: translateX(-50%) translateY(4px) scale(0.96); }}
      100% {{ transform: translateX(-50%) translateY(-6px) scale(1.03); }}
    }}

    .action-scarf #layer-action-scarf {{ opacity: 1 !important; pointer-events: auto !important; }}
    .action-scarf #prince-avatar-body {{
      animation: scarfBodyTilt 0.45s infinite ease-in-out alternate !important;
      filter: drop-shadow(0 0 16px rgba(250, 204, 21, 0.8)) !important;
    }}
    @keyframes scarfBodyTilt {{
      0% {{ transform: skewX(-4deg) rotate(-2deg); }}
      100% {{ transform: skewX(5deg) rotate(3deg); }}
    }}
    .wind-scarf-ribbon {{
      position: absolute; top: 62px; left: -25px; width: 140px; height: 35px;
      background: linear-gradient(90deg, #dc2626 0%, #ef4444 60%, rgba(254, 202, 202, 0.8) 100%);
      border-radius: 18px 8px 18px 8px;
      box-shadow: 0 0 14px rgba(239, 68, 68, 0.85), inset 0 0 6px #fff;
      transform-origin: right center;
      animation: scarfRibbonWave 0.4s infinite ease-in-out alternate;
    }}
    @keyframes scarfRibbonWave {{
      0% {{ transform: rotate(-18deg) skewY(-8deg) scaleY(0.85); }}
      50% {{ transform: rotate(12deg) skewY(12deg) scaleY(1.2) translateY(-8px); }}
      100% {{ transform: rotate(-12deg) skewY(-6deg) scaleY(0.9); }}
    }}

    .action-stars #layer-action-stars {{ opacity: 1 !important; pointer-events: auto !important; }}
    .action-stars #prince-avatar-body {{
      transform: translateY(-8px) scale(1.05) !important;
      filter: drop-shadow(0 0 25px rgba(250, 204, 21, 0.95)) !important;
    }}
    .stars-orbit-img {{
      position: absolute; bottom: 15px; left: 50%; transform: translateX(-50%);
      width: 140px; height: 140px; object-fit: contain;
      animation: starsOrbitPulse 2.8s infinite ease-in-out alternate;
      filter: drop-shadow(0 0 18px rgba(254, 240, 138, 0.9));
    }}
    @keyframes starsOrbitPulse {{
      0% {{ transform: translateX(-50%) scale(0.92) rotate(-5deg); }}
      100% {{ transform: translateX(-50%) scale(1.08) rotate(8deg); }}
    }}

    .action-sunset #layer-action-sunset {{ opacity: 1 !important; pointer-events: auto !important; }}
    .action-sunset #prince-avatar-body {{
      filter: drop-shadow(0 0 24px rgba(249, 115, 22, 0.9)) sepia(30%) hue-rotate(-12deg) !important;
      transform: scale(0.96) translateY(5px) !important;
    }}
    .sunset-glow-img {{
      position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
      width: 150px; height: 150px; object-fit: contain;
      animation: sunSinkingSlow 5s infinite ease-in-out alternate;
      filter: drop-shadow(0 0 22px rgba(249, 115, 22, 0.95));
    }}
    @keyframes sunSinkingSlow {{
      0% {{ transform: translateX(-50%) translateY(-25px) scale(0.92); opacity: 0.75; }}
      50% {{ transform: translateX(-50%) translateY(5px) scale(1.05); opacity: 1; }}
      100% {{ transform: translateX(-50%) translateY(32px) scale(0.98); opacity: 0.85; }}
    }}

    /* 气泡与看板 */
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

    .pet-smart-bubble.mode-alert {{
      background: linear-gradient(135deg, rgba(69, 10, 10, 0.97) 0%, rgba(35, 10, 10, 0.98) 100%) !important;
      border-color: #ef4444 !important;
      box-shadow: 0 12px 35px rgba(0, 0, 0, 0.75), 0 0 24px rgba(239, 68, 68, 0.6) !important;
    }}
    .pet-smart-bubble.mode-alert::after {{ border-top-color: #ef4444 !important; }}

    .pet-smart-bubble.mode-fatigue {{
      background: linear-gradient(135deg, rgba(6, 78, 59, 0.96) 0%, rgba(15, 23, 42, 0.98) 100%) !important;
      border-color: #10b981 !important;
      box-shadow: 0 12px 35px rgba(0, 0, 0, 0.7), 0 0 20px rgba(16, 185, 129, 0.45) !important;
    }}
    .pet-smart-bubble.mode-fatigue::after {{ border-top-color: #10b981 !important; }}

    .bubble-tag-bar {{ display: flex; justify-content: space-between; align-items: center; font-size: 10px; font-weight: bold; margin-bottom: 5px; }}
    .bubble-tag-text {{ color: var(--lp-star-gold); display: flex; align-items: center; gap: 4px; }}
    .mode-alert .bubble-tag-text {{ color: #fca5a5 !important; }}
    .mode-fatigue .bubble-tag-text {{ color: #6ee7b7 !important; }}
    .bubble-close-btn {{ background: transparent; border: none; color: #94a3b8; font-size: 11px; cursor: pointer; padding: 2px 4px; }}
    .bubble-close-btn:hover {{ color: #fff; }}
    .bubble-main-txt {{ font-size: 12px; line-height: 1.55; color: #f8fafc; font-weight: 500; }}
    .bubble-sub-txt {{ font-size: 9.5px; color: #94a3b8; font-style: italic; margin-top: 4px; line-height: 1.35; }}
    .bubble-actions-row {{ display: flex; gap: 6px; margin-top: 8px; justify-content: flex-end; }}
    .bubble-act-btn {{ font-size: 10px; padding: 3px 8px; border-radius: 4px; cursor: pointer; border: 1px solid; transition: all 0.2s; }}
    .bubble-act-primary {{ background: rgba(239, 68, 68, 0.25); border-color: #ef4444; color: #fecaca; }}
    .bubble-act-green {{ background: rgba(16, 185, 129, 0.25); border-color: #10b981; color: #a7f3d0; }}
    .bubble-act-subtle {{ background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.2); color: #cbd5e1; }}

    /* 快捷胶囊条 */
    .nezuko-action-capsule {{
      position: absolute;
      top: -52px;
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

    .btn-switch-pet {{ background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important; border-color: #60a5fa !important; }}
    .btn-roam-mode.roaming {{ background: linear-gradient(135deg, #10b981, #059669) !important; border-color: #34d399 !important; }}
    .btn-music-spin.playing {{ animation: recordSpin 3.5s infinite linear; border-color: var(--ds-pink); box-shadow: 0 0 10px rgba(244, 143, 177, 0.8); }}
    @keyframes recordSpin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}

    .pet-picked-up {{
      transform: scale(1.08) translateY(-22px) rotate(-8deg) !important;
      filter: drop-shadow(0 14px 22px rgba(0, 0, 0, 0.35)) !important;
    }}

    /* 看板卡片 */
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
    .nezuko-header-title {{ font-size: 13px; font-weight: 700; color: var(--ds-gold-glow); display: flex; align-items: center; gap: 6px; }}
    .nezuko-close-btn {{ background: transparent; border: none; color: #9ca3af; font-size: 14px; cursor: pointer; }}
    .nezuko-close-btn:hover {{ color: #fff; }}
    .nezuko-card-body {{ padding: 12px 14px; display: flex; flex-direction: column; gap: 12px; max-height: 480px; overflow-y: auto; }}
    .nezuko-section-box {{ background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(197, 155, 39, 0.35); border-radius: 8px; padding: 10px 12px; }}
    .nezuko-section-title {{ font-size: 12px; font-weight: 700; color: #e0e0e0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }}
    .nezuko-ctrl-btn {{ background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(197, 155, 39, 0.4); color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; transition: all 0.2s; }}
    .nezuko-ctrl-btn:hover {{ background: var(--ds-dark-pink); border-color: var(--ds-pink); }}

    /* QQ音乐播放器控制区 */
    .qq-music-player-box {{
      background: linear-gradient(180deg, rgba(16, 185, 129, 0.12) 0%, rgba(20, 12, 10, 0.9) 100%);
      border: 1.5px solid var(--qq-green);
      border-radius: 8px; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px;
    }}
    .qq-status-bar {{ display: flex; justify-content: space-between; align-items: center; font-size: 10.5px; color: #6ee7b7; font-weight: bold; }}
    .qq-pulse-dot {{ width: 7px; height: 7px; border-radius: 50%; background: #10b981; display: inline-block; margin-right: 4px; box-shadow: 0 0 6px #10b981; animation: pulseGlow 1.5s infinite; }}
    @keyframes pulseGlow {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
    .nezuko-music-info {{ display: flex; align-items: center; gap: 10px; }}
    .nezuko-record-disc {{ width: 36px; height: 36px; background: radial-gradient(circle, #10b981 18%, #111 19%, #222 65%, #111 100%); border: 1.5px solid var(--qq-green); border-radius: 50%; flex-shrink: 0; animation: recordSpin 3.5s infinite linear; animation-play-state: paused; }}
    .record-spinning {{ animation-play-state: running !important; }}
    .nezuko-song-texts {{ display: flex; flex-direction: column; overflow: hidden; }}
    .nezuko-song-title {{ font-size: 12px; font-weight: 700; color: #fff; white-space: nowrap; text-overflow: ellipsis; overflow: hidden; }}
    .nezuko-song-sub {{ font-size: 10px; color: #a7f3d0; }}
    .sound-waves-box {{ display: flex; align-items: flex-end; gap: 2px; height: 14px; }}
    .sound-bar {{ width: 3px; background: #10b981; border-radius: 2px; animation: barJump 0.8s infinite ease-in-out alternate; }}
    .sound-bar:nth-child(1) {{ height: 6px; animation-delay: 0.1s; }}
    .sound-bar:nth-child(2) {{ height: 14px; animation-delay: 0.3s; }}
    .sound-bar:nth-child(3) {{ height: 9px; animation-delay: 0.2s; }}
    .sound-bar:nth-child(4) {{ height: 12px; animation-delay: 0.4s; }}
    @keyframes barJump {{ 0% {{ height: 3px; }} 100% {{ height: 14px; }} }}
    .nezuko-music-controls {{ display: flex; align-items: center; justify-content: space-between; gap: 6px; }}
    .nezuko-ctrl-play {{ background: linear-gradient(135deg, #059669, #047857) !important; border-color: #34d399 !important; font-weight: bold; padding: 5px 16px; box-shadow: 0 0 10px rgba(16, 185, 129, 0.4); }}

    .nezuko-float-badge {{
      position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%);
      background: rgba(35, 22, 18, 0.88); border: 1px solid var(--ds-brass-gold);
      color: var(--ds-gold-glow); font-size: 10px; padding: 2px 8px; border-radius: 12px;
      cursor: pointer; white-space: nowrap; box-shadow: 0 4px 10px rgba(0,0,0,0.4);
      opacity: 0.85; transition: opacity 0.2s;
    }}
    .nezuko-float-badge:hover {{ opacity: 1; background: var(--ds-dark-pink); color: #fff; }}

    /* 配额项样式 */
    .nezuko-quota-row {{ display: flex; align-items: center; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.1); }}
    .nezuko-quota-row:last-child {{ border-bottom: none; }}
    .nezuko-quota-meta {{ display: flex; flex-direction: column; }}
    .nezuko-quota-name {{ font-size: 11px; color: #d1d5db; }}
    .nezuko-quota-reset {{ font-size: 9.5px; color: #9ca3af; }}
    .nezuko-quota-val-group {{ display: flex; align-items: center; gap: 8px; }}
    .nezuko-quota-pct {{ font-size: 12px; font-weight: 700; color: #ffd54f; min-width: 38px; text-align: right; }}
    .nezuko-ring-box {{ width: 26px; height: 26px; position: relative; }}
    .nezuko-ring-box svg {{ transform: rotate(-90deg); width: 26px; height: 26px; }}
    .nezuko-ring-bg {{ fill: none; stroke: rgba(255, 255, 255, 0.12); stroke-width: 3.5; }}
    .nezuko-ring-prog {{ fill: none; stroke: #81c784; stroke-width: 3.5; stroke-linecap: round; stroke-dasharray: 62.83; stroke-dashoffset: 6.28; transition: stroke-dashoffset 0.6s ease; }}
  `;
  document.head.appendChild(styleEl);

  // ==========================================
  // 八、DOM 组装 (加入 3D 木箱本体与粒子系统)
  // ==========================================
  const root = document.createElement('div');
  root.id = 'nezuko-pet-root';
  root.innerHTML = `
    <div class="nezuko-pet-stage" id="nezuko-pet-stage">
      <div class="nezuko-pet-ground-shadow" id="nezuko-ground-shadow"></div>

      <!-- 智能多态交互气泡中枢 -->
      <div class="pet-smart-bubble" id="pet-smart-bubble">
        <div class="bubble-tag-bar">
          <span class="bubble-tag-text" id="bubble-tag-text">🦊 狐狸的秘密 · B612星球</span>
          <button class="bubble-close-btn" id="bubble-close-btn" title="关闭气泡">✕</button>
        </div>
        <div class="bubble-main-txt" id="bubble-main-txt">真正重要的东西，用眼睛是看不见的，只有用心才能看清。</div>
        <div class="bubble-sub-txt" id="bubble-sub-txt">L'essentiel est invisible pour les yeux.</div>
        <div class="bubble-actions-row" id="bubble-actions-row" style="display:none;"></div>
      </div>

      <!-- 头顶快捷胶囊动作条 (包含转木箱、狂奔走动、漫步切换) -->
      <div class="nezuko-action-capsule" id="nezuko-action-capsule">
        <button class="nezuko-capsule-btn btn-switch-pet" id="btn-quick-switch" data-tip="切换角色 (祢豆子/小王子)" title="切换角色">🔁</button>
        <button class="nezuko-capsule-btn btn-roam-mode roaming" id="btn-quick-roam" data-tip="自主走动漫步 (已开启)" title="切换自主漫步/锁定">🚶</button>
        <div id="action-buttons-container" style="display:flex; gap:7px;"></div>
        <button class="nezuko-capsule-btn btn-music-spin" id="btn-quick-music" data-tip="QQ音乐播放/切歌" title="遥控电脑QQ音乐">🎵</button>
        <button class="nezuko-capsule-btn" id="btn-quick-board" data-tip="配额看板" title="打开配额看板">🎋</button>
      </div>

      <!-- 情绪浮动微气泡 -->
      <div class="floating-mood-bubble" id="floating-mood-bubble">🌸</div>

      <!-- 角色 1：祢豆子 2D 骨骼机架 -->
      <div class="nezuko-pet-rig" id="pet-nezuko" style="display:none;" title="双击打开看板 · 单击摸头 · 拖拽移动 · 滚轮切歌">
        <div class="stomp-ripple"></div>
        <div class="bone-layer" id="bone-leg-l"></div>
        <div class="bone-layer" id="bone-leg-r"></div>
        <div class="bone-layer" id="bone-torso"></div>
        <div class="bone-layer" id="bone-arm-l"></div>
        <div class="bone-layer" id="bone-arm-r"></div>
        <div class="bone-layer" id="bone-head">
          <div class="nezuko-eyelid-overlay" id="nezuko-eyelid"></div>
        </div>
      </div>

      <!-- 专属动作组件：大正雾云杉 3D 木箱 (转木箱与钻木箱探头) -->
      <div class="box-action-container" id="box-action-container">
        <div class="ds-3d-box" id="ds-3d-box">
          <div class="ds-box-top-handle"></div>
          <div class="ds-box-body">
            <div class="ds-box-steel-strap top"></div>
            <div class="ds-box-steel-strap mid"></div>
            <div class="ds-box-steel-strap bot"></div>
            <div class="ds-box-bracket tl"></div>
            <div class="ds-box-bracket tr"></div>
            <div class="ds-box-bracket bl"></div>
            <div class="ds-box-bracket br"></div>
            
            <!-- 木箱暗室内衬与探头特写头像 -->
            <div class="ds-box-interior">
              <img src="${{NEZUKO_PEEKER_HEAD}}" class="peeker-chibi-img" id="peeker-chibi-img" alt="木箱里的祢豆子">
            </div>

            <!-- 3D 轴心旋转开启的木箱门 -->
            <div class="ds-box-door" id="ds-box-door">
              <div class="ds-door-ring"></div>
            </div>
          </div>
        </div>

        <!-- 转木箱飞旋的风刃、枫叶与樱花粒子 -->
        <div class="box-spin-particles">
          <span class="spin-petal sp1" style="--tx:-45px; --ty:-35px;">🍁</span>
          <span class="spin-petal sp2" style="--tx:55px; --ty:-40px;">🌸</span>
          <span class="spin-petal sp3" style="--tx:-50px; --ty:25px;">🍂</span>
          <span class="spin-petal sp4" style="--tx:45px; --ty:30px;">🌸</span>
        </div>
      </div>

      <!-- 冲刺奔跑烟尘粒子容器 -->
      <div class="dash-dust-container" id="dash-dust-container"></div>

      <!-- 角色 2：小王子 B612 治愈多图层动态机架 -->
      <div class="prince-pet-rig" id="pet-prince" style="display:none;" title="单击听名言 · 双击打开看板 · 拖拽移动 · 滚轮切歌">
        <img src="${{PRINCE_IMG}}" class="prince-avatar-img" id="prince-avatar-body" alt="小王子">

        <div class="prince-action-layer" id="layer-action-fox">
          <img src="${{PRINCE_FOX_IMG}}" class="prince-fox-img" alt="小王子与小狐狸">
        </div>
        <div class="prince-action-layer" id="layer-action-rose">
          <img src="${{PRINCE_ROSE_IMG}}" class="rose-dome-img" alt="玻璃罩红玫瑰">
        </div>
        <div class="prince-action-layer" id="layer-action-scarf">
          <div class="wind-scarf-ribbon"></div>
        </div>
        <div class="prince-action-layer" id="layer-action-stars">
          <img src="${{PRINCE_STARS_IMG}}" class="stars-orbit-img" alt="繁星小行星">
        </div>
        <div class="prince-action-layer" id="layer-action-sunset">
          <img src="${{PRINCE_SUNSET_IMG}}" class="sunset-glow-img" alt="日落夕阳">
        </div>
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

        <!-- 角色切换与漫步模式管理 -->
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

        <!-- 自主漫步走动与物理位移控制器卡片 -->
        <div class="nezuko-section-box" style="background: rgba(16, 185, 129, 0.15); border-color: #10b981;">
          <div class="nezuko-section-title">
            <span style="color:#6ee7b7;">🚶 自主漫步巡航与物理走动</span>
            <span id="roam-status-tag" style="font-size:10px; color:#81c784;">● 自由漫步中</span>
          </div>
          <div style="font-size:10px; color:#cbd5e1; margin-bottom:8px; line-height:1.4;">
            桌宠具备自主 AI 决策漫步，将在屏幕底栏自由漫步探险；遇到边界自动掉头；点击狂奔即可飞奔冲刺！
          </div>
          <div style="display:flex; gap:6px;">
            <button class="nezuko-ctrl-btn" id="btn-toggle-roam" style="flex:1; padding:5px; background:linear-gradient(135deg, #059669, #047857); border-color:#34d399; font-weight:bold;">
              🚶 切换漫步模式 (开/关)
            </button>
            <button class="nezuko-ctrl-btn" id="btn-instant-dash" style="padding:5px 10px; background:linear-gradient(135deg, #ec4899, #be185d); font-weight:bold;" title="立即飞奔冲刺一段距离">
              🏃 立即冲刺
            </button>
          </div>
        </div>

        <!-- 疲劳关怀与久坐健康提醒控制区 -->
        <div class="nezuko-section-box" style="background: rgba(16, 185, 129, 0.12); border-color: #10b981;">
          <div class="nezuko-section-title">
            <span style="color:#6ee7b7;">🍵 专注工作与久坐健康关怀</span>
            <span id="fatigue-status-tag" style="font-size:10px; color:#81c784;">● 已激活</span>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; font-size:11px; color:#d1fae5;">
            <span>当前已连续工作:</span>
            <b id="work-timer-label" style="color:#fde047; font-size:13px;">0 分钟</b>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="nezuko-ctrl-btn" id="btn-test-fatigue" style="flex:1; padding:5px; background:linear-gradient(135deg, #059669, #047857); border-color:#34d399;">
              🍵 体验久坐关怀
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
          <div style="display:flex; gap:6px;">
            <button class="nezuko-ctrl-btn" id="btn-test-quota-alert" style="flex:1; padding:5px; background:linear-gradient(135deg, #dc2626, #991b1b); border-color:#f87171;">
              🚨 模拟低于10%告急
            </button>
          </div>
        </div>

        <!-- 模型配额总看板 -->
        <div class="nezuko-section-box" style="background: rgba(30, 20, 15, 0.7); border-color: var(--ds-brass-gold);">
          <div class="nezuko-section-title">
            <span style="color:var(--ds-gold-glow);">📊 模型配额实时监控</span>
            <span id="quota-sync-time-tag" style="font-size:10px; color:#81c784;">刚刚已同步</span>
          </div>

          <div class="nezuko-quota-row">
            <div class="nezuko-quota-meta">
              <span class="nezuko-quota-name">Gemini 每周可用配额</span>
              <span class="nezuko-quota-reset" id="lbl-gemini-weekly-reset">${{currentQuota.geminiWeeklyReset}}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-gemini-weekly-pct">${{currentQuota.geminiWeeklyPct}}%</span>
              <div class="nezuko-ring-box">
                <svg viewBox="0 0 26 26"><circle class="nezuko-ring-bg" cx="13" cy="13" r="10" /><circle class="nezuko-ring-prog" id="ring-gemini-weekly" cx="13" cy="13" r="10" /></svg>
              </div>
            </div>
          </div>

          <div class="nezuko-quota-row">
            <div class="nezuko-quota-meta">
              <span class="nezuko-quota-name">Gemini 5小时可用配额</span>
              <span class="nezuko-quota-reset" id="lbl-gemini-5h-reset">${{currentQuota.gemini5hReset}}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-gemini-5h-pct">${{currentQuota.gemini5hPct}}%</span>
              <div class="nezuko-ring-box">
                <svg viewBox="0 0 26 26"><circle class="nezuko-ring-bg" cx="13" cy="13" r="10" /><circle class="nezuko-ring-prog" id="ring-gemini-5h" cx="13" cy="13" r="10" /></svg>
              </div>
            </div>
          </div>

          <div class="nezuko-quota-row">
            <div class="nezuko-quota-meta">
              <span class="nezuko-quota-name">Claude 每周可用配额</span>
              <span class="nezuko-quota-reset" id="lbl-claude-weekly-reset">${{currentQuota.claudeWeeklyReset}}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-claude-weekly-pct">${{currentQuota.claudeWeeklyPct}}%</span>
              <div class="nezuko-ring-box">
                <svg viewBox="0 0 26 26"><circle class="nezuko-ring-bg" cx="13" cy="13" r="10" /><circle class="nezuko-ring-prog" id="ring-claude-weekly" cx="13" cy="13" r="10" /></svg>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  `;
  document.body.appendChild(root);

  // ==========================================
  // 九、DOM 元素引用与基础控制
  // ==========================================
  const stageEl = document.getElementById('nezuko-pet-stage');
  const petNezuko = document.getElementById('pet-nezuko');
  const petPrince = document.getElementById('pet-prince');
  const boxContainer = document.getElementById('box-action-container');
  const smartBubble = document.getElementById('pet-smart-bubble');
  const bubbleTagText = document.getElementById('bubble-tag-text');
  const bubbleCloseBtn = document.getElementById('bubble-close-btn');
  const bubbleMainTxt = document.getElementById('bubble-main-txt');
  const bubbleSubTxt = document.getElementById('bubble-sub-txt');
  const bubbleActionsRow = document.getElementById('bubble-actions-row');
  const moodBubble = document.getElementById('floating-mood-bubble');
  const eyelidEl = document.getElementById('nezuko-eyelid');

  const mainCard = document.getElementById('nezuko-main-card');
  const openBtn = document.getElementById('nezuko-open-btn');
  const closeBtn = document.getElementById('nezuko-close-card');
  const actionBtnBox = document.getElementById('action-buttons-container');
  const boardTitleChar = document.getElementById('board-title-char');
  const boardRoleBadge = document.getElementById('board-role-badge');
  const curPetLabel = document.getElementById('cur-pet-label');
  const capsuleBar = document.getElementById('nezuko-action-capsule');
  const quickRoamBtn = document.getElementById('btn-quick-roam');
  const disc = document.getElementById('nezuko-disc');
  const quickMusicBtn = document.getElementById('btn-quick-music');
  const quickBoardBtn = document.getElementById('btn-quick-board');
  const soundWaves = document.getElementById('sound-waves');
  const dustContainer = document.getElementById('dash-dust-container');

  function openMainCard() {{ mainCard.style.display = 'flex'; }}
  function closeMainCard() {{ mainCard.style.display = 'none'; }}

  // 气泡控制
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
        btn.onclick = (e) => {{ e.stopPropagation(); if (act.onClick) act.onClick(); }};
        bubbleActionsRow.appendChild(btn);
      }});
    }} else {{
      bubbleActionsRow.style.display = 'none';
    }}

    smartBubble.classList.add('show');
    if (smartBubbleHideTimer) clearTimeout(smartBubbleHideTimer);
    if (duration > 0) smartBubbleHideTimer = setTimeout(() => hideSmartBubble(), duration);
  }}

  function hideSmartBubble() {{
    smartBubble.classList.remove('show');
    if (smartBubbleHideTimer) {{ clearTimeout(smartBubbleHideTimer); smartBubbleHideTimer = null; }}
  }}
  bubbleCloseBtn.addEventListener('click', (e) => {{ e.stopPropagation(); hideSmartBubble(); }});

  // QQ 音乐界面响应
  window.updateMusicUI = function() {{
    const playBtn = document.getElementById('m-btn-play');
    const titleEl = document.getElementById('music-title');
    const subEl = document.getElementById('music-sub');
    if (qqBridge.isPlaying) {{
      playBtn.textContent = "⏸ 暂停";
      playBtn.style.background = "linear-gradient(135deg, #ef4444, #b91c1c)";
      disc.classList.add('record-spinning');
      quickMusicBtn.classList.add('playing');
      soundWaves.style.display = 'flex';
      titleEl.textContent = "QQ 音乐正在播放中";
      subEl.textContent = "音效已同步 · 点击可暂停或切歌";
    }} else {{
      playBtn.textContent = "▶ 播放";
      playBtn.style.background = "linear-gradient(135deg, #059669, #047857)";
      disc.classList.remove('record-spinning');
      quickMusicBtn.classList.remove('playing');
      soundWaves.style.display = 'none';
      titleEl.textContent = "QQ 音乐已就绪";
      subEl.textContent = "点击播放直接启动电脑上的 QQ 音乐";
    }}
  }};

  document.getElementById('m-btn-play').addEventListener('click', () => qqBridge.playPause());
  document.getElementById('m-btn-next').addEventListener('click', () => qqBridge.nextTrack());
  document.getElementById('m-btn-prev').addEventListener('click', () => qqBridge.prevTrack());
  document.getElementById('m-btn-wake-qq').addEventListener('click', () => qqBridge.wakeUpQQMusic());
  quickMusicBtn.addEventListener('click', (e) => {{ e.stopPropagation(); qqBridge.playPause(); }});

  stageEl.addEventListener('wheel', (e) => {{
    e.preventDefault();
    if (e.deltaY > 0) qqBridge.nextTrack();
    else qqBridge.prevTrack();
  }});

  // ==========================================
  // 十、动态自然眨眼与情绪微表情系统
  // ==========================================
  function scheduleNextBlink() {{
    const delay = 3200 + Math.random() * 2800;
    setTimeout(() => {{
      if (activePet === 'nezuko' && petNezuko.style.display !== 'none') {{
        petNezuko.classList.add('is-blinking');
        setTimeout(() => {{
          petNezuko.classList.remove('is-blinking');
          scheduleNextBlink();
        }}, 140);
      }} else {{
        scheduleNextBlink();
      }}
    }}, delay);
  }}
  scheduleNextBlink();

  const MOOD_LIST = ['🌸', '✨', '💤', '❓', '💖', '🍵', '🍂'];
  function showRandomMood() {{
    if (Math.random() < 0.4) {{
      const mood = MOOD_LIST[Math.floor(Math.random() * MOOD_LIST.length)];
      moodBubble.textContent = mood;
      moodBubble.classList.add('active');
      setTimeout(() => moodBubble.classList.remove('active'), 2200);
    }}
  }}
  setInterval(showRandomMood, 8000);

  // ==========================================
  // 十一、真实物理走动与自主漫步巡航引擎 (PetMotionController)
  // ==========================================
  let curRight = 32;
  let curBottom = 24;
  let facingDirection = 1; // 1: 朝左, -1: 朝右
  let isRoamingEnabled = localStorage.getItem('__agy_pet_roam_enabled__') !== 'false';
  let isMoving = false;
  let isActionPlaying = false;

  function updateFacing(direction) {{
    facingDirection = direction;
    stageEl.style.transform = `scaleX(${{direction}})`;
    // 气泡和胶囊反向纠偏，防止文字被镜像倒转
    smartBubble.style.transform = direction === 1 
      ? 'translateX(-50%) translateY(0) scale(1)' 
      : 'translateX(50%) translateY(0) scale(1) scaleX(-1)';
    capsuleBar.style.transform = direction === 1 
      ? 'translateX(-50%) translateY(0) scale(1)' 
      : 'translateX(50%) translateY(0) scale(1) scaleX(-1)';
  }}

  function spawnDustPuff() {{
    const puff = document.createElement('div');
    puff.className = 'dust-puff';
    puff.style.left = (facingDirection > 0 ? '70%' : '30%');
    puff.style.setProperty('--dust-x', (facingDirection > 0 ? '25px' : '-25px'));
    dustContainer.appendChild(puff);
    setTimeout(() => puff.remove(), 550);
  }}

  // 平滑走动到目标坐标
  function walkTo(targetRight, speed = 1.0, onComplete = null) {{
    if (isActionPlaying) return;
    const maxRight = Math.min(window.innerWidth - 170, 850);
    const minRight = 24;
    targetRight = Math.max(minRight, Math.min(maxRight, targetRight));

    const dist = targetRight - curRight;
    if (Math.abs(dist) < 15) return;

    const dir = dist > 0 ? 1 : -1; // dist > 0 表示向左移动（right增加），dir=1
    updateFacing(dir);

    const activeRig = activePet === 'nezuko' ? petNezuko : petPrince;
    activeRig.classList.add('is-walking');
    isMoving = true;

    const durationSec = Math.max(0.6, Math.abs(dist) / (120 * speed));
    root.style.transition = `right ${{durationSec}}s cubic-bezier(0.25, 1, 0.5, 1), bottom 0.3s ease`;
    root.style.right = targetRight + 'px';
    curRight = targetRight;

    // 走动时播放轻快碎步小音效
    petAudio.playFootstep();

    setTimeout(() => {{
      activeRig.classList.remove('is-walking');
      isMoving = false;
      if (onComplete) onComplete();
    }}, durationSec * 1000);
  }}

  // 飞奔冲刺动作 (Dashing Run)
  function runDash(customDist = 0) {{
    if (isActionPlaying) return;
    isActionPlaying = true;
    const maxRight = Math.min(window.innerWidth - 180, 850);
    const minRight = 24;

    // 计算冲刺目标
    let targetDist = customDist !== 0 ? customDist : (facingDirection > 0 ? 280 : -280);
    let targetRight = curRight + targetDist;

    // 遇边界反弹掉头冲刺
    if (targetRight > maxRight) {{
      targetRight = curRight - 280;
      updateFacing(-1);
    }} else if (targetRight < minRight) {{
      targetRight = curRight + 280;
      updateFacing(1);
    }}

    const dist = targetRight - curRight;
    updateFacing(dist > 0 ? 1 : -1);

    const activeRig = activePet === 'nezuko' ? petNezuko : petPrince;
    activeRig.classList.add('is-running');
    petAudio.playSpinWind();

    // 冲刺期间喷出连续烟尘粒子
    const dustTimer = setInterval(spawnDustPuff, 80);

    const durationSec = 1.0;
    root.style.transition = `right ${{durationSec}}s cubic-bezier(0.12, 0.8, 0.32, 1)`;
    root.style.right = targetRight + 'px';
    curRight = targetRight;

    setTimeout(() => {{
      clearInterval(dustTimer);
      activeRig.classList.remove('is-running');
      activeRig.classList.add('action-skid');
      petAudio.playFootstep();

      setTimeout(() => {{
        activeRig.classList.remove('action-skid');
        isActionPlaying = false;
      }}, 350);
    }}, durationSec * 1000);
  }}

  // 自主漫步巡航心跳
  let roamInterval = null;
  function startRoamHeartbeat() {{
    if (roamInterval) clearInterval(roamInterval);
    roamInterval = setInterval(() => {{
      if (!isRoamingEnabled || isMoving || isActionPlaying || isDragging || mainCard.style.display === 'flex') return;

      const rnd = Math.random();
      const maxRight = Math.min(window.innerWidth - 180, 850);
      const minRight = 24;

      if (rnd < 0.38) {{
        // 向左走动
        const step = 60 + Math.random() * 100;
        walkTo(curRight + step, 1.0);
      }} else if (rnd < 0.76) {{
        // 向右走动
        const step = 60 + Math.random() * 100;
        walkTo(curRight - step, 1.0);
      }} else if (rnd < 0.90) {{
        // 原地好奇东张西望
        updateFacing(facingDirection * -1);
        moodBubble.textContent = '❓';
        moodBubble.classList.add('active');
        setTimeout(() => moodBubble.classList.remove('active'), 1800);
      }} else {{
        // 原地小憩或打哈欠
        if (activePet === 'nezuko') triggerCurrentPetAction('sleep', 2500);
      }}
    }}, 11000);
  }}

  function toggleRoamMode() {{
    isRoamingEnabled = !isRoamingEnabled;
    localStorage.setItem('__agy_pet_roam_enabled__', isRoamingEnabled ? 'true' : 'false');
    const roamTag = document.getElementById('roam-status-tag');
    if (roamTag) {{
      roamTag.textContent = isRoamingEnabled ? '● 自由漫步中' : '○ 锁定角落';
      roamTag.style.color = isRoamingEnabled ? '#81c784' : '#9ca3af';
    }}
    if (quickRoamBtn) {{
      if (isRoamingEnabled) {{
        quickRoamBtn.classList.add('roaming');
        quickRoamBtn.setAttribute('data-tip', '自主走动漫步 (已开启)');
        quickRoamBtn.textContent = '🚶';
      }} else {{
        quickRoamBtn.classList.remove('roaming');
        quickRoamBtn.setAttribute('data-tip', '自主漫步已暂停 (点击开启)');
        quickRoamBtn.textContent = '📌';
      }}
    }}
    if (isRoamingEnabled) startRoamHeartbeat();
  }}

  if (isRoamingEnabled) startRoamHeartbeat();
  quickRoamBtn.addEventListener('click', (e) => {{ e.stopPropagation(); toggleRoamMode(); }});
  document.getElementById('btn-toggle-roam').addEventListener('click', toggleRoamMode);
  document.getElementById('btn-instant-dash').addEventListener('click', () => runDash());

  // ==========================================
  // 十二、3D 转木箱与钻木箱神技动作引擎
  // ==========================================
  let boxSpinCount = 0;
  function triggerDemonSlayerBoxAction() {{
    if (isActionPlaying) return;
    isActionPlaying = true;

    boxSpinCount++;
    const isSpin = (boxSpinCount % 2 === 1); // 奇数次转木箱，偶数次钻木箱探头

    // 隐藏立绘，唤出 3D 木箱
    petNezuko.style.display = 'none';
    boxContainer.classList.add('show-box-action');
    boxContainer.className = 'box-action-container show-box-action';

    if (isSpin) {{
      // 动作 A：华丽 3D 转木箱 (Spin Box 360 Whirlwind)
      boxContainer.classList.add('action-box-spin');
      petAudio.playSpinWind();

      setTimeout(() => petAudio.playWoodThud(), 850);

      setTimeout(() => {{
        // 旋转落地后推开门探头
        boxContainer.classList.remove('action-box-spin');
        boxContainer.classList.add('action-box-peek');
        moodBubble.textContent = '✨';
        moodBubble.classList.add('active');

        setTimeout(() => {{
          moodBubble.classList.remove('active');
          boxContainer.className = 'box-action-container';
          boxContainer.classList.remove('show-box-action');
          petNezuko.style.display = 'block';
          isActionPlaying = false;
        }}, 2200);
      }}, 1250);
    }} else {{
      // 动作 B：钻木箱与探头探脑 (Peek-a-boo Box)
      boxContainer.classList.add('action-box-peek');
      petAudio.playCareSound();
      moodBubble.textContent = '🌸';
      moodBubble.classList.add('active');

      setTimeout(() => {{
        moodBubble.classList.remove('active');
        boxContainer.className = 'box-action-container';
        boxContainer.classList.remove('show-box-action');
        petNezuko.style.display = 'block';
        isActionPlaying = false;
      }}, 3200);
    }}
  }}

  // 动作调度中心
  let actionTimer = null;
  function triggerCurrentPetAction(actionName, duration = 6500) {{
    if (actionName === 'box') {{
      triggerDemonSlayerBoxAction();
      return;
    }}
    if (actionName === 'run') {{
      runDash();
      return;
    }}

    const currentRig = activePet === 'nezuko' ? petNezuko : petPrince;
    currentRig.className = (activePet === 'nezuko' ? 'nezuko-pet-rig' : 'prince-pet-rig');
    if (actionName) currentRig.classList.add('action-' + actionName);

    if (actionTimer) clearTimeout(actionTimer);
    actionTimer = setTimeout(() => {{
      currentRig.className = (activePet === 'nezuko' ? 'nezuko-pet-rig' : 'prince-pet-rig');
    }}, duration);
  }}

  // ==========================================
  // 十三、角色切换与胶囊条动作绑定
  // ==========================================
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
        <button class="nezuko-capsule-btn" data-action="box" data-tip="3D转木箱 / 钻木箱神技" title="3D转木箱与钻木箱探头">📦</button>
        <button class="nezuko-capsule-btn" data-action="run" data-tip="疾速冲刺飞奔" title="真正沿屏幕飞奔冲刺">🏃</button>
        <button class="nezuko-capsule-btn" data-action="headpat" data-tip="摸头杀蹭蹭" title="摸头杀蹭蹭">🐱</button>
        <button class="nezuko-capsule-btn" data-action="stomp" data-tip="气鼓跺小脚" title="气鼓鼓跺小脚">😤</button>
        <button class="nezuko-capsule-btn" data-action="burst" data-tip="血鬼术·爆血" title="血鬼术·爆血觉醒">🔥</button>
        <button class="nezuko-capsule-btn" data-action="sleep" data-tip="揉眼伸懒腰" title="揉眼睛伸懒腰打瞌睡">🥱</button>
      `;
    }} else {{
      actionBtnBox.innerHTML = `
        <button class="nezuko-capsule-btn" data-action="run" data-tip="星际飞奔漫步" title="在屏幕底栏飞奔冲刺">🏃</button>
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

  function switchPet(targetPet) {{
    activePet = targetPet;
    setActivePet(targetPet);
    boxContainer.className = 'box-action-container';
    boxContainer.classList.remove('show-box-action');

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

  petPrince.addEventListener('click', () => {{
    if (isDragging) return;
    showNextQuote();
    triggerCurrentPetAction('rose', 2000);
  }});
  petNezuko.addEventListener('click', () => {{
    if (isDragging) return;
    triggerCurrentPetAction('headpat', 2200);
  }});

  // 疲劳与告急按钮交互
  document.getElementById('btn-test-fatigue').addEventListener('click', () => {{
    triggerFatigueAlertUI(continuousWorkMinutes >= 30 ? continuousWorkMinutes : 45);
  }});
  document.getElementById('btn-reset-work-timer').addEventListener('click', resetWorkTimer);
  document.getElementById('btn-test-quota-alert').addEventListener('click', () => checkQuotaAlert(true));

  switchPet(activePet);

  // 胶囊显示防消失
  let hideCapsuleTimer = null;
  function showCapsule() {{
    if (hideCapsuleTimer) clearTimeout(hideCapsuleTimer);
    capsuleBar.classList.add('is-active');
  }}
  function scheduleHideCapsule() {{
    if (hideCapsuleTimer) clearTimeout(hideCapsuleTimer);
    hideCapsuleTimer = setTimeout(() => capsuleBar.classList.remove('is-active'), 450);
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
  closeBtn.addEventListener('click', () => mainCard.style.display = 'none');

  // 鼠标拖拽引擎
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
        curRight = origRight - dx;
        curBottom = origBottom - dy;
        root.style.transition = 'none'; // 拖拽时立即跟随无过渡
        root.style.right = curRight + 'px';
        root.style.bottom = curBottom + 'px';
      }}
    }};

    const onUp = () => {{
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      if (isDragging) {{
        const currentRig = activePet === 'nezuko' ? petNezuko : petPrince;
        currentRig.classList.remove('pet-picked-up');
        root.style.transition = 'right 0.8s cubic-bezier(0.25, 1, 0.5, 1), bottom 0.3s ease';
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
      ring.style.stroke = pct > 75 ? '#81c784' : (pct > 30 ? '#ffd54f' : '#e57373');
    }};
    setRing('ring-gemini-weekly', currentQuota.geminiWeeklyPct);
    setRing('ring-gemini-5h', currentQuota.gemini5hPct);
    setRing('ring-claude-weekly', currentQuota.claudeWeeklyPct);

    document.getElementById('lbl-gemini-weekly-pct').textContent = currentQuota.geminiWeeklyPct + '%';
    document.getElementById('lbl-gemini-5h-pct').textContent = currentQuota.gemini5hPct + '%';
    document.getElementById('lbl-claude-weekly-pct').textContent = currentQuota.claudeWeeklyPct + '%';
  }}
  updateQuotaDisplay();
  updateWorkTimeDisplay();
  checkQuotaAlert();

}})();
"""

target_js = REPO_ROOT / "resources" / "nezuko-pet.js"
target_js.write_text(js_code, encoding="utf-8")
print(f"✅ 成功生成全套生动化、物理走动漫步巡航与3D转木箱桌宠组件: {target_js} ({len(js_code.encode('utf-8'))} 字节)")

# 同步更新 build_nezuko_pet.py 保持源头同步
build_py = REPO_ROOT / "scripts" / "build_nezuko_pet.py"
build_py.write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
print(f"✅ 成功将最新生成逻辑同步至 build_nezuko_pet.py: {build_py}")
