# -*- coding: utf-8 -*-
"""
生成双角色桌宠系统：
1. 【🌸 灶门祢豆子】(鬼灭之刃大正和风 + 2D骨骼解剖分肢动画 + 原生配额看板 + 和风BGM)
2. 【👑 小王子 (B612星球)】(浪漫法国童话 + 随风飘扬长围巾 + 玻璃罩红玫瑰 + 12句中法双语经典哲思名言定时气泡 + 仰望星空/四十四次日落/小狐狸动作)
3. 【🔁 自由一键切换中枢】：本地持久化记忆当前选定角色。
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
 * Antigravity 异构多角色桌宠引擎 4.0 (Dual-Pet Engine)
 * 角色 1：🌸 灶门祢豆子 (鬼灭之刃 2D 骨骼分肢动力学 + 全局和风主题 + 原生配额看板)
 * 角色 2：👑 小王子 (B612星球治愈系 + 随风飘扬围巾 + 玻璃罩玫瑰 + 12句中法双语名言定期气泡)
 * 核心：支持一键切换并本地持久化记忆。
 */

(function() {{
  if (typeof window === 'undefined' || window.__NEZUKO_PET_INITIALIZED__) return;
  window.__NEZUKO_PET_INITIALIZED__ = true;

  // 资源 Base64
  const NEZUKO_HEAD = "data:image/webp;base64,{b64_nezuko_parts['head']}";
  const NEZUKO_TORSO = "data:image/webp;base64,{b64_nezuko_parts['torso']}";
  const NEZUKO_ARM_L = "data:image/webp;base64,{b64_nezuko_parts['arm_l']}";
  const NEZUKO_ARM_R = "data:image/webp;base64,{b64_nezuko_parts['arm_r']}";
  const NEZUKO_LEG_L = "data:image/webp;base64,{b64_nezuko_parts['leg_l']}";
  const NEZUKO_LEG_R = "data:image/webp;base64,{b64_nezuko_parts['leg_r']}";

  const PRINCE_IMG = "data:image/webp;base64,{b64_prince}";

  // ==========================================
  // 一、《小王子》12 句中法双语经典哲思名言库
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

  // 读取当前激活角色 ('nezuko' | 'prince')
  function getActivePet() {{
    return localStorage.getItem('__agy_active_pet_character__') || 'nezuko';
  }}
  function setActivePet(name) {{
    localStorage.setItem('__agy_active_pet_character__', name);
  }}

  // ==========================================
  // 二、Antigravity 软件界面鬼灭和风全局主题
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
    .sidebar .title-label h2, .sidebar .pane-header .title {{
      color: #ffd54f !important; font-weight: 700 !important;
    }}
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
  // 三、模型配额中枢
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

  // ==========================================
  // 四、随身 BGM 音乐盒 (含小王子星空八音盒)
  // ==========================================
  const noteFreqs = {{
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.26, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50
  }};

  const PLAYLIST = [
    {{
      title: "星の王子さま (小王子的星空)",
      subtitle: "B612星球 · 浪漫治愈八音盒",
      notes: [
        ['E5', 0.5], ['G5', 0.5], ['B5', 0.8], ['A5', 0.5], ['G5', 0.8],
        ['E5', 0.5], ['D5', 0.5], ['E5', 1.0], ['G5', 0.5], ['A5', 0.8],
        ['B5', 0.5], ['D6', 0.5], ['B5', 1.0], ['A5', 0.5], ['G5', 1.2]
      ]
    }},
    {{
      title: "竈門炭治郎のうた (灶门炭治郎之歌)",
      subtitle: "治愈抒情 · 椎名豪 / 中川奈美",
      notes: [
        ['G4', 0.45], ['A4', 0.45], ['B4', 0.7], ['D5', 0.45], ['B4', 0.7],
        ['A4', 0.45], ['G4', 0.45], ['E4', 0.9], ['G4', 0.45], ['A4', 0.9],
        ['B4', 0.45], ['D5', 0.45], ['E5', 0.9], ['D5', 0.45], ['B4', 0.9]
      ]
    }},
    {{
      title: "紅蓮華 (红莲华)",
      subtitle: "经典热血 OP · LiSA 和风版",
      notes: [
        ['D5', 0.3], ['D5', 0.3], ['C5', 0.3], ['A4', 0.3], ['C5', 0.3], ['D5', 0.6],
        ['D5', 0.3], ['E5', 0.3], ['F5', 0.3], ['E5', 0.3], ['D5', 0.3], ['C5', 0.6]
      ]
    }}
  ];

  class DualPetMusicEngine {{
    constructor() {{
      this.ctx = null;
      this.isPlaying = false;
      this.currentTrack = 0;
      this.stepIndex = 0;
      this.timer = null;
      this.volume = 0.5;
      this.customAudio = null;
    }}
    initContext() {{
      if (!this.ctx) {{
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioContext();
      }}
      if (this.ctx.state === 'suspended') this.ctx.resume();
    }}
    playTone(freq, duration) {{
      if (!this.ctx) return;
      const t = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t);
      gain.gain.setValueAtTime(0.001, t);
      gain.gain.exponentialRampToValueAtTime(0.35 * this.volume, t + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + duration * 1.6);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(t);
      osc.stop(t + duration * 1.7);
    }}
    playNextNote() {{
      if (!this.isPlaying || this.customAudio) return;
      const track = PLAYLIST[this.currentTrack];
      if (this.stepIndex >= track.notes.length) this.stepIndex = 0;
      const [noteName, dur] = track.notes[this.stepIndex];
      const freq = noteFreqs[noteName] || 440;
      this.playTone(freq, dur);
      triggerMusicBeat();
      this.stepIndex++;
      this.timer = setTimeout(() => this.playNextNote(), dur * 1000);
    }}
    play() {{
      if (this.customAudio) {{
        this.customAudio.play();
        this.isPlaying = true;
        updateMusicUI();
        return;
      }}
      this.initContext();
      this.isPlaying = true;
      this.playNextNote();
      updateMusicUI();
    }}
    pause() {{
      this.isPlaying = false;
      if (this.timer) clearTimeout(this.timer);
      if (this.customAudio) this.customAudio.pause();
      updateMusicUI();
    }}
    toggle() {{
      if (this.isPlaying) this.pause();
      else this.play();
    }}
    next() {{
      this.pause();
      if (this.customAudio) this.customAudio = null;
      this.currentTrack = (this.currentTrack + 1) % PLAYLIST.length;
      this.stepIndex = 0;
      this.play();
    }}
    prev() {{
      this.pause();
      if (this.customAudio) this.customAudio = null;
      this.currentTrack = (this.currentTrack - 1 + PLAYLIST.length) % PLAYLIST.length;
      this.stepIndex = 0;
      this.play();
    }}
    loadLocalFile(file) {{
      const url = URL.createObjectURL(file);
      this.pause();
      this.customAudio = new Audio(url);
      this.customAudio.volume = this.volume;
      this.customAudio.loop = true;
      this.customAudio.addEventListener('ended', () => this.next());
      this.play();
      updateMusicUI(file.name);
    }}
  }}
  const musicEngine = new DualPetMusicEngine();

  let beatTimer = null;
  function triggerMusicBeat() {{
    const headEl = document.getElementById('bone-head');
    const princeEl = document.getElementById('prince-avatar-body');
    if (headEl && musicEngine.isPlaying) {{
      headEl.classList.add('head-music-bob');
      if (beatTimer) clearTimeout(beatTimer);
      beatTimer = setTimeout(() => headEl.classList.remove('head-music-bob'), 400);
    }}
    if (princeEl && musicEngine.isPlaying) {{
      princeEl.classList.add('prince-music-bob');
      if (beatTimer) clearTimeout(beatTimer);
      beatTimer = setTimeout(() => princeEl.classList.remove('prince-music-bob'), 400);
    }}
  }}

  // ==========================================
  // 五、样式库 (双角色骨骼 + 小王子星空名言气泡)
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
      --lp-blue-dark: #0f172a;
      --lp-blue-card: #1e293b;
      --lp-star-gold: #facc15;
      --lp-rose-red: #f43f5e;
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

    /* 角色画框容器 */
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

    /* ========================================================= */
    /* 角色 1：祢豆子 2D 骨骼图层 */
    /* ========================================================= */
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

    /* 祢豆子骨骼动作动画 */
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

    /* ========================================================= */
    /* 角色 2：小王子 (B612星球治愈系立绘与专属动作) */
    /* ========================================================= */
    .prince-avatar-img {{
      width: 100%; height: 100%; object-fit: contain; pointer-events: none; display: block;
      transform-origin: bottom center;
    }}
    .prince-music-bob {{ transform: translateY(-4px) rotate(3deg) !important; }}

    /* 小王子专属动作 1：飘逸长围巾随风吹拂 (action-scarf) */
    .action-scarf {{
      animation: princeScarfWind 2.2s infinite ease-in-out !important;
    }}
    @keyframes princeScarfWind {{
      0%, 100% {{ transform: translateY(0) rotate(0deg); }}
      30% {{ transform: translateY(-4px) rotate(4deg) skewX(2deg); }}
      70% {{ transform: translateY(-2px) rotate(-3deg) skewX(-2deg); }}
    }}

    /* 小王子专属动作 2：呵护玻璃罩红玫瑰 (action-rose) */
    .action-rose {{
      animation: princeRoseCuddle 1.8s infinite ease-in-out !important;
      filter: drop-shadow(0 0 14px rgba(244, 63, 94, 0.75)) !important;
    }}
    @keyframes princeRoseCuddle {{
      0%, 100% {{ transform: scale(1) translateY(0); }}
      50% {{ transform: scale(1.06) translateY(-6px); }}
    }}

    /* 小王子专属动作 3：召唤小狐狸 (action-fox) */
    .action-fox {{
      animation: princeFoxHop 1.4s infinite ease-in-out !important;
    }}
    @keyframes princeFoxHop {{
      0%, 100% {{ transform: translateY(0); }}
      50% {{ transform: translateY(-8px) rotate(5deg); }}
    }}

    /* 小王子专属动作 4：仰望繁星 (action-stars) */
    .action-stars {{
      animation: princeGazeStars 2.8s infinite ease-in-out !important;
      filter: drop-shadow(0 0 16px rgba(250, 204, 21, 0.8)) !important;
    }}
    @keyframes princeGazeStars {{
      0%, 100% {{ transform: translateY(0) rotate(0deg); }}
      50% {{ transform: translateY(-5px) rotate(-6deg); }}
    }}

    /* 小王子专属动作 5：看四十四次日落 (action-sunset) */
    .action-sunset {{
      animation: princeSunsetGlow 3.2s infinite ease-in-out !important;
      filter: drop-shadow(0 0 20px rgba(251, 146, 60, 0.85)) !important;
    }}
    @keyframes princeSunsetGlow {{
      0%, 100% {{ transform: translateY(0) scale(1); }}
      50% {{ transform: translateY(4px) scale(0.96); }}
    }}

    /* ========================================================= */
    /* 核心灵魂：《小王子》星空治愈名言气泡引擎 (中法双语) */
    /* ========================================================= */
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
      content: '';
      position: absolute;
      top: 100%;
      left: 50%;
      transform: translateX(-50%);
      border: 8px solid transparent;
      border-top-color: var(--lp-star-gold);
    }}
    .quote-tag {{
      font-size: 10px;
      color: var(--lp-star-gold);
      font-weight: bold;
      margin-bottom: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .quote-zh {{
      font-size: 12.5px;
      color: #fef08a;
      line-height: 1.55;
      font-weight: 500;
      letter-spacing: 0.3px;
    }}
    .quote-fr {{
      font-size: 9.5px;
      color: #94a3b8;
      font-style: italic;
      margin-top: 4px;
      line-height: 1.35;
    }}
    .quote-hint {{
      font-size: 9px;
      color: #64748b;
      text-align: right;
      margin-top: 4px;
    }}

    /* 快捷胶囊动作条 */
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
      content: '';
      position: absolute;
      top: 100%;
      left: -20px;
      right: -20px;
      height: 44px;
      background: transparent;
      pointer-events: auto;
    }}
    .nezuko-pet-stage:hover .nezuko-action-capsule,
    .nezuko-action-capsule:hover,
    .nezuko-action-capsule.is-active {{
      opacity: 1 !important;
      pointer-events: auto !important;
      transform: translateX(-50%) translateY(0) scale(1) !important;
    }}

    .nezuko-capsule-btn {{
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(197, 155, 39, 0.45);
      color: #fff;
      font-size: 15px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.18s cubic-bezier(0.2, 0.8, 0.2, 1);
      position: relative;
      flex-shrink: 0;
    }}
    .nezuko-capsule-btn:hover {{
      background: var(--ds-dark-pink);
      border-color: var(--ds-pink);
      transform: scale(1.18);
      box-shadow: 0 0 12px rgba(244, 143, 177, 0.7);
    }}
    .nezuko-capsule-btn:active {{ transform: scale(0.95); }}
    .nezuko-capsule-btn[data-tip]::before {{
      content: attr(data-tip);
      position: absolute;
      bottom: calc(100% + 7px);
      left: 50%;
      transform: translateX(-50%) scale(0.8);
      background: rgba(20, 12, 10, 0.95);
      border: 1px solid var(--ds-brass-gold);
      color: var(--ds-gold-glow);
      font-size: 10px;
      font-weight: bold;
      padding: 2px 7px;
      border-radius: 4px;
      white-space: nowrap;
      pointer-events: none;
      opacity: 0;
      transition: all 0.18s ease;
      box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }}
    .nezuko-capsule-btn:hover::before {{ opacity: 1; transform: translateX(-50%) scale(1); }}

    .btn-switch-pet {{
      background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
      border-color: #60a5fa !important;
    }}

    .btn-music-spin {{
      background: radial-gradient(circle, #ff80ab 20%, #231612 21%, #111 100%);
    }}
    .btn-music-spin.playing {{
      animation: recordSpin 3.5s infinite linear;
      border-color: var(--ds-pink);
      box-shadow: 0 0 10px rgba(244, 143, 177, 0.8);
    }}
    @keyframes recordSpin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}

    /* 拖拽被提起 */
    .pet-picked-up {{
      transform: scale(1.08) translateY(-22px) rotate(-8deg) !important;
      filter: drop-shadow(0 14px 22px rgba(0, 0, 0, 0.35)) !important;
    }}

    /* 主操作看板 */
    #nezuko-main-card {{
      position: absolute;
      bottom: 225px;
      right: 0;
      width: 340px;
      background: linear-gradient(135deg, rgba(35, 22, 18, 0.96) 0%, rgba(20, 12, 10, 0.98) 100%);
      border: 2px solid var(--ds-brass-gold);
      border-radius: 12px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65), 0 0 20px rgba(244, 143, 177, 0.25);
      color: #fff;
      overflow: hidden;
      display: none;
      flex-direction: column;
      z-index: 120;
      backdrop-filter: blur(12px);
    }}
    .nezuko-card-header {{
      display: flex; justify-content: space-between; align-items: center; padding: 10px 14px;
      background: linear-gradient(90deg, #381f19 0%, #4a2920 100%);
      border-bottom: 1.5px solid var(--ds-brass-gold);
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
    .nezuko-quota-row {{
      display: flex; justify-content: space-between; align-items: center; padding: 6px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .nezuko-quota-row:last-child {{ border-bottom: none; }}
    .nezuko-quota-meta {{ display: flex; flex-direction: column; gap: 2px; }}
    .nezuko-quota-name {{ font-size: 12px; color: #f5f5f5; }}
    .nezuko-quota-reset {{ font-size: 10px; color: #9e9e9e; }}
    .nezuko-quota-val-group {{ display: flex; align-items: center; gap: 8px; }}
    .nezuko-quota-pct {{ font-size: 13px; font-weight: 700; color: #81c784; }}
    .nezuko-ring-wrap {{ width: 24px; height: 24px; transform: rotate(-90deg); }}
    .nezuko-ring-bg {{ fill: none; stroke: rgba(255, 255, 255, 0.15); stroke-width: 3.5; }}
    .nezuko-ring-bar {{
      fill: none; stroke: #81c784; stroke-width: 3.5; stroke-linecap: round; stroke-dasharray: 63;
      stroke-dashoffset: 0; transition: stroke-dashoffset 0.6s ease;
    }}

    .nezuko-music-player {{
      background: linear-gradient(180deg, rgba(46, 26, 20, 0.7) 0%, rgba(20, 12, 10, 0.85) 100%);
      border: 1px solid var(--ds-brass-gold); border-radius: 8px; padding: 10px 12px;
      display: flex; flex-direction: column; gap: 8px;
    }}
    .nezuko-music-info {{ display: flex; align-items: center; gap: 10px; }}
    .nezuko-record-disc {{
      width: 34px; height: 34px;
      background: radial-gradient(circle, #ff80ab 15%, #111 16%, #222 65%, #111 100%);
      border: 1.5px solid var(--ds-brass-gold); border-radius: 50%; flex-shrink: 0;
      animation: recordSpin 3.5s infinite linear; animation-play-state: paused;
    }}
    .record-spinning {{ animation-play-state: running !important; }}
    .nezuko-song-texts {{ display: flex; flex-direction: column; overflow: hidden; }}
    .nezuko-song-title {{ font-size: 11.5px; font-weight: 700; color: #fff; white-space: nowrap; text-overflow: ellipsis; overflow: hidden; }}
    .nezuko-song-sub {{ font-size: 9.5px; color: var(--ds-pink); }}
    .nezuko-music-controls {{ display: flex; align-items: center; justify-content: space-between; gap: 6px; }}
    .nezuko-ctrl-btn {{
      background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(197, 155, 39, 0.4);
      color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; transition: all 0.2s;
    }}
    .nezuko-ctrl-btn:hover {{ background: var(--ds-dark-pink); border-color: var(--ds-pink); }}
    .nezuko-ctrl-play {{ background: linear-gradient(135deg, var(--ds-dark-pink), var(--ds-crimson)); font-weight: bold; padding: 4px 14px; }}

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
  // 六、DOM 组装 (双角色共用舞台 + 治愈名言气泡)
  // ==========================================
  const root = document.createElement('div');
  root.id = 'nezuko-pet-root';
  root.innerHTML = `
    <div class="nezuko-pet-stage" id="nezuko-pet-stage">
      <!-- 地面接触软阴影 -->
      <div class="nezuko-pet-ground-shadow" id="nezuko-ground-shadow"></div>

      <!-- 《小王子》治愈名言星空发光气泡 -->
      <div id="little-prince-quote-bubble">
        <div class="quote-tag">
          <span id="qp-tag">🦊 狐狸的秘密 · B612星球</span>
          <span style="font-size:9px; opacity:0.8;">✦ 治愈哲思</span>
        </div>
        <div class="quote-zh" id="qp-zh">真正重要的东西，用眼睛是看不见的，只有用心才能看清。</div>
        <div class="quote-fr" id="qp-fr">L'essentiel est invisible pour les yeux.</div>
        <div class="quote-hint">点击抽取下一句 ✨</div>
      </div>

      <!-- 头顶快捷胶囊动作条 -->
      <div class="nezuko-action-capsule" id="nezuko-action-capsule">
        <!-- 切换角色按钮 -->
        <button class="nezuko-capsule-btn btn-switch-pet" id="btn-quick-switch" data-tip="切换宠物 (祢豆子/小王子)" title="切换宠物">🔁</button>

        <!-- 动作按钮容器 (由 JS 动态装载对应角色的动作) -->
        <div id="action-buttons-container" style="display:flex; gap:7px;"></div>

        <button class="nezuko-capsule-btn btn-music-spin" id="btn-quick-music" data-tip="播放/切歌" title="播放/切换BGM">🎵</button>
        <button class="nezuko-capsule-btn" id="btn-quick-board" data-tip="配额看板" title="打开配额看板">🎋</button>
      </div>

      <!-- 角色 1：祢豆子 2D 骨骼机架 -->
      <div class="nezuko-pet-rig" id="pet-nezuko" style="display:none;" title="单击锁定动作条 · 双击打开看板 · 按住拖拽 · 滚轮切歌">
        <div class="bone-layer" id="bone-leg-l"></div>
        <div class="bone-layer" id="bone-leg-r"></div>
        <div class="bone-layer" id="bone-torso"></div>
        <div class="bone-layer" id="bone-arm-l"></div>
        <div class="bone-layer" id="bone-arm-r"></div>
        <div class="bone-layer" id="bone-head"></div>
      </div>

      <!-- 角色 2：小王子 B612 治愈立绘 -->
      <div class="prince-pet-rig" id="pet-prince" style="display:none;" title="单击听名言哲思 · 双击打开看板 · 按住拖拽 · 滚轮切歌">
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
        <!-- 角色切换与管理卡片 -->
        <div class="nezuko-section-box" style="background: rgba(59, 130, 246, 0.18); border-color: #60a5fa;">
          <div class="nezuko-section-title">
            <span style="color:#93c5fd;">⭐ 桌面宠物随心切换</span>
            <span id="cur-pet-label" style="font-size:10px; color:#facc15;">小王子模式</span>
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

        <!-- 随身 BGM 音乐盒 -->
        <div class="nezuko-music-player">
          <div class="nezuko-music-info">
            <div class="nezuko-record-disc" id="nezuko-disc"></div>
            <div class="nezuko-song-texts">
              <span class="nezuko-song-title" id="music-title">星の王子さま</span>
              <span class="nezuko-song-sub" id="music-sub">B612星球 · 治愈八音盒</span>
            </div>
          </div>
          <div class="nezuko-music-controls">
            <button class="nezuko-ctrl-btn" id="m-btn-prev" title="上一曲">⏮</button>
            <button class="nezuko-ctrl-btn nezuko-ctrl-play" id="m-btn-play" title="播放/暂停">▶ 播放</button>
            <button class="nezuko-ctrl-btn" id="m-btn-next" title="下一曲">⏭</button>
            <label class="nezuko-ctrl-btn" style="cursor:pointer;" title="导入本地音频">
              📁 导入
              <input type="file" id="m-file-input" accept="audio/*" style="display:none;">
            </label>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(root);

  // ==========================================
  // 七、角色状态机与名言气泡引擎
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

  let activePet = getActivePet();
  let currentQuoteIndex = 0;
  let quoteAutoTimer = null;
  let quoteHideTimer = null;

  // 弹出名言气泡函数
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
    }}, 9500); // 9.5秒后优雅淡出
  }}

  // 切换角色动作按钮
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

    // 绑定动作触发
    actionBtnBox.querySelectorAll('.nezuko-capsule-btn').forEach(btn => {{
      btn.addEventListener('click', (e) => {{
        e.stopPropagation();
        const action = btn.getAttribute('data-action');
        if (action === 'quote') {{
          showNextQuote();
        }} else {{
          triggerCurrentPetAction(action);
        }}
      }});
    }});
  }}

  // 动作分发
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

  // 切换角色核心流程
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
      // 开启定期送名言 (每 180 秒自动弹出一句)
      if (quoteAutoTimer) clearInterval(quoteAutoTimer);
      quoteAutoTimer = setInterval(showNextQuote, 180000);
      showNextQuote(); // 切换时送上一句暖心问候
    }}

    renderActionButtons();
  }}

  // 快捷切换按钮
  document.getElementById('btn-quick-switch').addEventListener('click', (e) => {{
    e.stopPropagation();
    switchPet(activePet === 'nezuko' ? 'prince' : 'nezuko');
  }});
  document.getElementById('btn-select-nezuko').addEventListener('click', () => switchPet('nezuko'));
  document.getElementById('btn-select-prince').addEventListener('click', () => switchPet('prince'));

  // 点击小王子身体或气泡：抽取下一句
  petPrince.addEventListener('click', (e) => {{
    if (isDragging) return;
    showNextQuote();
    triggerCurrentPetAction('rose', 2000);
  }});
  quoteBubble.addEventListener('click', (e) => {{
    e.stopPropagation();
    showNextQuote();
  }});

  // 首次装载激活角色
  switchPet(activePet);

  // ==========================================
  // 八、防消失悬停桥接与拖拽手感
  // ==========================================
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

  // 配额更新与音乐
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

  window.updateMusicUI = function(customName) {{
    const titleEl = document.getElementById('music-title');
    const subEl = document.getElementById('music-sub');
    const playBtn = document.getElementById('m-btn-play');
    if (customName) {{
      titleEl.textContent = customName;
      subEl.textContent = "本地音乐文件";
    }} else {{
      const trk = PLAYLIST[musicEngine.currentTrack];
      titleEl.textContent = trk.title;
      subEl.textContent = trk.subtitle;
    }}
    if (musicEngine.isPlaying) {{
      playBtn.textContent = "⏸ 暂停";
      disc.classList.add('record-spinning');
      quickMusicBtn.classList.add('playing');
    }} else {{
      playBtn.textContent = "▶ 播放";
      disc.classList.remove('record-spinning');
      quickMusicBtn.classList.remove('playing');
    }}
  }};

  quickMusicBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    if (!musicEngine.isPlaying) musicEngine.play();
    else musicEngine.next();
  }});
  document.getElementById('m-btn-play').addEventListener('click', () => musicEngine.toggle());
  document.getElementById('m-btn-next').addEventListener('click', () => musicEngine.next());
  document.getElementById('m-btn-prev').addEventListener('click', () => musicEngine.prev());

  document.getElementById('m-file-input').addEventListener('change', (e) => {{
    const f = e.target.files[0];
    if (f) musicEngine.loadLocalFile(f);
  }});

  // 滚轮切歌
  stageEl.addEventListener('wheel', (e) => {{
    e.preventDefault();
    if (e.deltaY > 0) musicEngine.next();
    else musicEngine.prev();
  }});

}})();
"""

target_js = REPO_ROOT / "resources" / "nezuko-pet.js"
target_js.write_text(js_code, encoding="utf-8")
print(f"✅ 成功生成支持小王子切换与名言气泡的双角色桌宠引擎: {target_js} ({len(js_code.encode('utf-8'))} 字节)")
