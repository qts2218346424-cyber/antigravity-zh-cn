# -*- coding: utf-8 -*-
"""
生成全套动画级别（Animation Quality）动作效果的灶门祢豆子 & 小王子桌宠组件
包含：
1. 8 帧大正雾云杉木箱 360 度多视角原画分镜精灵图 (Sprite Sheet)
2. 真实挤压与拉伸 (Squash & Stretch) 落地震地冲击波与风刃枫叶粒子
3. 迪士尼十二黄金法则驱动的行走小碎步 (Dual-Joint IK Walk) 与风火轮狂奔 (Run Dash)
4. 动漫级急刹车滑行 (Skid Brake) 与多阶段烟尘喷发
5. 有机呼吸与自然眨眼微表情
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

# 2. 读取 8 帧 360 度转木箱分镜精灵图
box_sheet_webp = MEDIA_DIR / "nezuko_box_spin_sheet.webp"
b64_box_sheet = base64.b64encode(box_sheet_webp.read_bytes()).decode('ascii')

# 读取落地冲击波素材
box_fx_webp = MEDIA_DIR / "box_impact_shockwave.webp"
b64_box_fx = base64.b64encode(box_fx_webp.read_bytes()).decode('ascii')

# 3. 读取小王子核心与动作素材
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

js_code = f"""// 灶门祢豆子 & 小王子 (B612) · 动画级别动作引擎 (Animation-Grade Motion Rig)
// 包含：8帧360度转木箱分镜 + 真实挤压与拉伸物理形变 + 双关节步态行走与风火轮狂奔 + 震地冲击波与动漫刹车
(function() {{
  if (typeof window === 'undefined' || window.__AGY_NEZUKO_PET_INITIALIZED__) return;
  window.__AGY_NEZUKO_PET_INITIALIZED__ = true;

  // 1. 核心分肢与动画分镜大图素材
  const NEZUKO_HEAD = "data:image/webp;base64,{b64_nezuko_parts['head']}";
  const NEZUKO_TORSO = "data:image/webp;base64,{b64_nezuko_parts['torso']}";
  const NEZUKO_ARM_L = "data:image/webp;base64,{b64_nezuko_parts['arm_l']}";
  const NEZUKO_ARM_R = "data:image/webp;base64,{b64_nezuko_parts['arm_r']}";
  const NEZUKO_LEG_L = "data:image/webp;base64,{b64_nezuko_parts['leg_l']}";
  const NEZUKO_LEG_R = "data:image/webp;base64,{b64_nezuko_parts['leg_r']}";
  const NEZUKO_PEEKER_HEAD = "data:image/webp;base64,{b64_head_peeker}";

  // 8 帧大正雾云杉木箱 360 度多视角原画分镜精灵图 (1280x220)
  const BOX_SPIN_SHEET = "data:image/webp;base64,{b64_box_sheet}";
  // 落地金色冲击波
  const BOX_IMPACT_FX = "data:image/webp;base64,{b64_box_fx}";

  const PRINCE_IMG = "data:image/webp;base64,{b64_prince}";
  const PRINCE_FOX_IMG = "data:image/webp;base64,{b64_prince_fox}";
  const PRINCE_ROSE_IMG = "data:image/webp;base64,{b64_prince_rose}";
  const PRINCE_SUNSET_IMG = "data:image/webp;base64,{b64_prince_sunset}";
  const PRINCE_STARS_IMG = "data:image/webp;base64,{b64_prince_stars}";

  // ==========================================
  // 一、QQ 音乐客户端联动
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
          if (electron && electron.ipcRenderer) this.ipc = electron.ipcRenderer;
        }}
      }} catch (_) {{}}
    }}
    sendCommand(cmd) {{
      if (this.ipc) this.ipc.send('__agy_media_command__', cmd);
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
  // 二、拟真 Web Audio 音效 (沉木碰撞/气旋风刃/碎步/警报)
  // ==========================================
  class PetAudioSynth {{
    constructor() {{ this.ctx = null; }}
    ensureCtx() {{
      if (!this.ctx) {{
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) this.ctx = new AudioCtx();
      }}
      if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume();
    }}
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
        osc.connect(gain); gain.connect(this.ctx.destination);
        osc.start(now); osc.stop(now + 0.36);
      }} catch (_) {{}}
    }}
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
          osc.connect(gain); gain.connect(this.ctx.destination);
          osc.start(now + idx * 0.08); osc.stop(now + idx * 0.08 + 0.38);
        }});
      }} catch (_) {{}}
    }}
    // 木箱落地沉重撞击厚实音
    playWoodThud() {{
      try {{
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(155, now);
        osc.frequency.exponentialRampToValueAtTime(38, now + 0.22);
        gain.gain.setValueAtTime(0.25, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.24);
        osc.connect(gain); gain.connect(this.ctx.destination);
        osc.start(now); osc.stop(now + 0.25);
      }} catch (_) {{}}
    }}
    // 转木箱高速风刃呼啸旋转音
    playSpinWind() {{
      try {{
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(260, now);
        osc.frequency.linearRampToValueAtTime(700, now + 0.28);
        osc.frequency.linearRampToValueAtTime(200, now + 0.7);
        gain.gain.setValueAtTime(0.02, now);
        gain.gain.linearRampToValueAtTime(0.14, now + 0.25);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.72);
        osc.connect(gain); gain.connect(this.ctx.destination);
        osc.start(now); osc.stop(now + 0.73);
      }} catch (_) {{}}
    }}
    // 奔跑轻快卡通小脚步
    playFootstep() {{
      try {{
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(450, now);
        gain.gain.setValueAtTime(0.035, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.connect(gain); gain.connect(this.ctx.destination);
        osc.start(now); osc.stop(now + 0.06);
      }} catch (_) {{}}
    }}
    // 动漫爆发疾冲破风音效 (Dash Whoosh)
    playDashWhoosh() {{
      try {{
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(140, now);
        osc.frequency.exponentialRampToValueAtTime(780, now + 0.12);
        osc.frequency.exponentialRampToValueAtTime(220, now + 0.42);
        gain.gain.setValueAtTime(0.01, now);
        gain.gain.linearRampToValueAtTime(0.16, now + 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
        osc.connect(gain); gain.connect(this.ctx.destination);
        osc.start(now); osc.stop(now + 0.46);

        const osc2 = this.ctx.createOscillator();
        const gain2 = this.ctx.createGain();
        osc2.type = 'triangle';
        osc2.frequency.setValueAtTime(420, now);
        osc2.frequency.linearRampToValueAtTime(180, now + 0.38);
        gain2.gain.setValueAtTime(0.08, now);
        gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.38);
        osc2.connect(gain2); gain2.connect(this.ctx.destination);
        osc2.start(now); osc2.stop(now + 0.4);
      }} catch (_) {{}}
    }}
    // 动漫急刹车地面摩擦制动音效 (Skid Brake)
    playSkidBrake() {{
      try {{
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(620, now);
        osc.frequency.exponentialRampToValueAtTime(160, now + 0.28);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.32);
        osc.connect(gain); gain.connect(this.ctx.destination);
        osc.start(now); osc.stop(now + 0.33);
      }} catch (_) {{}}
    }}
  }}
  const petAudio = new PetAudioSynth();

  // ==========================================
  // 三、《小王子》12 句中法经典名言
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

  function getActivePet() {{ return localStorage.getItem('__agy_active_pet_character__') || 'nezuko'; }}
  function setActivePet(name) {{ localStorage.setItem('__agy_active_pet_character__', name); }}

  // ==========================================
  // 四、模型配额与同步体系
  // ==========================================
  const defaultQuotaState = {{
    geminiWeeklyPct: 91,
    geminiWeeklyReset: "6 天 19 小时后重置",
    gemini5hPct: 72,
    gemini5hReset: "46 分钟后重置",
    claudeWeeklyPct: 100,
    claudeWeeklyReset: "7 天后重置",
    lastSynced: "刚刚"
  }};
  function loadUserQuota() {{
    try {{
      const saved = localStorage.getItem('__nezuko_model_quota_v2__');
      if (saved) return Object.assign({{}}, defaultQuotaState, JSON.parse(saved));
    }} catch (_) {{}}
    return Object.assign({{}}, defaultQuotaState);
  }}
  let currentQuota = loadUserQuota();

  // ==========================================
  // 五、动画级别 CSS 样式库 (含 8 帧分镜动画 + 真实形变)
  // ==========================================
  const styleEl = document.createElement('style');
  styleEl.id = 'dual-pet-animation-grade-styles';
  styleEl.textContent = `
    :root {{
      --ds-pink: #f48fb1;
      --ds-dark-pink: #c2185b;
      --ds-crimson: #b71c1c;
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
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      transition: right 0.75s cubic-bezier(0.25, 1, 0.5, 1), bottom 0.3s ease;
    }}

    .nezuko-pet-stage {{
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      transform-origin: bottom center;
      transition: transform 0.22s ease-out;
    }}

    /* 真实随步伐与跳跃缩放的地面阴影 */
    .nezuko-pet-ground-shadow {{
      position: absolute;
      bottom: -6px;
      left: 50%;
      transform: translateX(-50%);
      width: 100px;
      height: 14px;
      background: radial-gradient(ellipse at center, rgba(10, 5, 8, 0.55) 0%, rgba(10, 5, 8, 0.15) 55%, transparent 75%);
      border-radius: 50%;
      pointer-events: none;
      transition: transform 0.15s ease, opacity 0.15s ease;
    }}

    .nezuko-pet-rig, .prince-pet-rig {{
      position: relative;
      width: 130px;
      height: 215px;
      cursor: grab;
      filter: drop-shadow(0 5px 12px rgba(0, 0, 0, 0.25));
      transition: transform 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
      transform-origin: bottom center;
    }}
    .nezuko-pet-rig:active, .prince-pet-rig:active {{ cursor: grabbing; }}

    /* 骨骼图层 */
    .bone-layer {{
      position: absolute;
      background-size: contain;
      background-repeat: no-repeat;
      pointer-events: none;
    }}
    #bone-head {{
      top: 0; left: 0; width: 130px; height: 121px;
      background-image: url('${{NEZUKO_HEAD}}');
      transform-origin: 50% 90%; z-index: 10;
      transition: transform 0.12s ease-out;
    }}
    #bone-torso {{
      top: 108px; left: 34px; width: 62px; height: 77px;
      background-image: url('${{NEZUKO_TORSO}}');
      transform-origin: 50% 95%; z-index: 6;
      transition: transform 0.12s ease-out;
    }}
    #bone-arm-l {{
      top: 108px; left: 0; width: 50px; height: 71px;
      background-image: url('${{NEZUKO_ARM_L}}');
      transform-origin: 75% 20%; z-index: 8;
      transition: transform 0.12s ease-out;
    }}
    #bone-arm-r {{
      top: 108px; left: 81px; width: 49px; height: 71px;
      background-image: url('${{NEZUKO_ARM_R}}');
      transform-origin: 25% 20%; z-index: 8;
      transition: transform 0.12s ease-out;
    }}
    #bone-leg-l {{
      top: 178px; left: 40px; width: 28px; height: 37px;
      background-image: url('${{NEZUKO_LEG_L}}');
      transform-origin: 50% 15%; z-index: 4;
      transition: transform 0.12s ease-out;
    }}
    #bone-leg-r {{
      top: 178px; left: 62px; width: 28px; height: 37px;
      background-image: url('${{NEZUKO_LEG_R}}');
      transform-origin: 50% 15%; z-index: 4;
      transition: transform 0.12s ease-out;
    }}

    /* 动态眼皮与自然眨眼 */
    .nezuko-eyelid-overlay {{
      position: absolute;
      top: 48px; left: 38px; width: 54px; height: 24px;
      pointer-events: none; z-index: 12; opacity: 0;
      background: radial-gradient(ellipse at center, #ffd1c1 0%, #ffc0b0 70%, transparent 100%);
      border-radius: 50%; transform: scaleY(0);
      transition: transform 0.08s ease-in, opacity 0.08s ease-in;
    }}
    .is-blinking .nezuko-eyelid-overlay {{
      opacity: 1 !important; transform: scaleY(1) !important;
    }}

    /* 情绪浮动气泡 */
    .floating-mood-bubble {{
      position: absolute; top: -14px; right: 10px; font-size: 16px;
      pointer-events: none; opacity: 0; transform: translateY(0) scale(0.6);
      transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
      z-index: 40; filter: drop-shadow(0 2px 5px rgba(0,0,0,0.4));
    }}
    .floating-mood-bubble.active {{
      opacity: 1; transform: translateY(-18px) scale(1.15);
    }}

    /* ========================================================= */
    /* 核心 1：动画级有机呼吸 (Organic Breathing) */
    /* ========================================================= */
    @keyframes organicBreathing {{
      0%, 100% {{
        transform: translateY(0) scale(1, 1);
      }}
      50% {{
        transform: translateY(3.5px) scale(1.025, 0.975);
      }}
    }}
    @keyframes headGentleBob {{
      0%, 100% {{ transform: rotate(-2deg) translateY(0); }}
      50% {{ transform: rotate(3deg) translateY(1.5px); }}
    }}
    @keyframes armOrganicIdleL {{
      0%, 100% {{ transform: rotate(-5deg); }}
      50% {{ transform: rotate(7deg); }}
    }}
    @keyframes armOrganicIdleR {{
      0%, 100% {{ transform: rotate(5deg); }}
      50% {{ transform: rotate(-7deg); }}
    }}

    .nezuko-pet-rig {{ animation: organicBreathing 3.6s infinite ease-in-out; }}
    .nezuko-pet-rig #bone-head {{ animation: headGentleBob 3.6s infinite ease-in-out; }}
    .nezuko-pet-rig #bone-arm-l {{ animation: armOrganicIdleL 3.6s infinite ease-in-out; }}
    .nezuko-pet-rig #bone-arm-r {{ animation: armOrganicIdleR 3.6s infinite ease-in-out; }}

    /* ========================================================= */
    /* 核心 2：迪士尼十二法则驱动的动画级步态行走 (Walk Cycle) */
    /* ========================================================= */
    .is-walking {{
      animation: animeWalkRig 0.5s infinite ease-in-out alternate !important;
    }}
    @keyframes animeWalkRig {{
      0% {{
        transform: translateY(0) rotate(2deg) scale(1.03, 0.97); /* 落地接触缓冲 */
      }}
      50% {{
        transform: translateY(-6px) rotate(-1deg) scale(0.97, 1.03); /* 腾空最高点 */
      }}
      100% {{
        transform: translateY(0) rotate(-2deg) scale(1.03, 0.97);
      }}
    }}

    .is-walking #bone-leg-l {{
      animation: animeLegCycleL 0.5s infinite alternate ease-in-out !important;
    }}
    .is-walking #bone-leg-r {{
      animation: animeLegCycleR 0.5s infinite alternate ease-in-out !important;
    }}
    @keyframes animeLegCycleL {{
      0% {{ transform: rotate(-28deg) translateY(-2px); }}
      50% {{ transform: rotate(6deg) translateY(-5px); }}
      100% {{ transform: rotate(32deg) translateY(0); }}
    }}
    @keyframes animeLegCycleR {{
      0% {{ transform: rotate(32deg) translateY(0); }}
      50% {{ transform: rotate(6deg) translateY(-5px); }}
      100% {{ transform: rotate(-28deg) translateY(-2px); }}
    }}

    .is-walking #bone-arm-l {{ animation: animeArmCycleL 0.5s infinite alternate ease-in-out !important; }}
    .is-walking #bone-arm-r {{ animation: animeArmCycleR 0.5s infinite alternate ease-in-out !important; }}
    @keyframes animeArmCycleL {{ 0% {{ transform: rotate(26deg); }} 100% {{ transform: rotate(-26deg); }} }}
    @keyframes animeArmCycleR {{ 0% {{ transform: rotate(-26deg); }} 100% {{ transform: rotate(26deg); }} }}

    /* ========================================================= */
    /* 核心 3：电影级动漫爆发飞奔冲刺与急刹车滑行制动 (Anime Dash & Skid Brake) */
    /* ========================================================= */
    /* 起跑蓄力压缩前摇 (Anticipation) */
    .is-anticipating {{
      transform: translateY(6px) rotate(4deg) scale(1.12, 0.88) !important;
      transition: transform 0.1s cubic-bezier(0.2, 0.9, 0.4, 1) !important;
    }}
    .prince-pet-rig.is-anticipating {{
      transform: translateX(-50%) translateY(7px) rotate(5deg) scale(1.1, 0.88) !important;
      transition: transform 0.1s cubic-bezier(0.2, 0.9, 0.4, 1) !important;
    }}

    /* 祢豆子飞奔冲刺主体态 (告别扭曲平移，前倾俯冲 + 高频起伏颠簸) */
    .nezuko-pet-rig.is-running {{
      animation: nezukoAnimeDash 0.13s infinite alternate ease-in-out !important;
    }}
    @keyframes nezukoAnimeDash {{
      0% {{
        transform: translateY(1px) rotate(-11deg) scale(1.04, 0.96);
      }}
      100% {{
        transform: translateY(-7px) rotate(-14deg) scale(0.96, 1.04);
      }}
    }}

    /* 祢豆子经典动漫飞机跑：双臂向后展翅飞拂，双手自然随风扑腾 */
    .nezuko-pet-rig.is-running #bone-arm-l {{
      animation: nezukoDashArmL 0.13s infinite alternate ease-in-out !important;
      z-index: 5 !important;
    }}
    .nezuko-pet-rig.is-running #bone-arm-r {{
      animation: nezukoDashArmR 0.13s infinite alternate ease-in-out !important;
      z-index: 5 !important;
    }}
    @keyframes nezukoDashArmL {{
      0% {{ transform: rotate(72deg) translateY(-2px); }}
      100% {{ transform: rotate(84deg) translateY(3px); }}
    }}
    @keyframes nezukoDashArmR {{
      0% {{ transform: rotate(76deg) translateY(-3px); }}
      100% {{ transform: rotate(88deg) translateY(2px); }}
    }}

    /* 祢豆子小短腿极速倒腾高频踏步循环 (告别穿模圆规，萌感风火轮) */
    .nezuko-pet-rig.is-running #bone-leg-l {{
      animation: nezukoDashLegL 0.13s infinite alternate ease-in-out !important;
    }}
    .nezuko-pet-rig.is-running #bone-leg-r {{
      animation: nezukoDashLegR 0.13s infinite alternate ease-in-out !important;
    }}
    @keyframes nezukoDashLegL {{
      0% {{ transform: rotate(-24deg) translateY(-4px); }}
      50% {{ transform: rotate(0deg) translateY(2px); }}
      100% {{ transform: rotate(26deg) translateY(-3px); }}
    }}
    @keyframes nezukoDashLegR {{
      0% {{ transform: rotate(26deg) translateY(-3px); }}
      50% {{ transform: rotate(0deg) translateY(2px); }}
      100% {{ transform: rotate(-24deg) translateY(-4px); }}
    }}

    /* 冲刺飞奔时头部微抬专注注视前方 */
    .nezuko-pet-rig.is-running #bone-head {{
      transform: rotate(9deg) translateY(1px) !important;
    }}

    /* 祢豆子电影级急刹车滑行制动 (Skid Brake with Overshoot & Settle) */
    .nezuko-pet-rig.action-skid {{
      animation: nezukoSkidBrake 0.38s cubic-bezier(0.2, 0.8, 0.3, 1) forwards !important;
    }}
    @keyframes nezukoSkidBrake {{
      0% {{
        transform: translateY(4px) rotate(16deg) scale(1.08, 0.92);
      }}
      45% {{
        transform: translateY(-3px) rotate(-5deg) scale(0.97, 1.03);
      }}
      100% {{
        transform: translateY(0) rotate(0deg) scale(1, 1);
      }}
    }}
    .nezuko-pet-rig.action-skid #bone-arm-l {{
      transform: rotate(-22deg) translateY(-2px) !important;
      transition: transform 0.25s ease-out;
    }}
    .nezuko-pet-rig.action-skid #bone-arm-r {{
      transform: rotate(22deg) translateY(-2px) !important;
      transition: transform 0.25s ease-out;
    }}
    .nezuko-pet-rig.action-skid #bone-leg-l {{
      transform: rotate(18deg) translateY(-2px) !important;
    }}
    .nezuko-pet-rig.action-skid #bone-leg-r {{
      transform: rotate(26deg) translateY(2px) !important;
    }}

    /* 小王子专属御风踏空飞奔态 (保持 translateX(-50%) 居中与 15° 俯冲动势) */
    .prince-pet-rig.is-running {{
      animation: princeDashRig 0.13s infinite alternate ease-in-out !important;
    }}
    @keyframes princeDashRig {{
      0% {{
        transform: translateX(-50%) translateY(-2px) rotate(-13deg) scale(1.04, 0.96);
      }}
      100% {{
        transform: translateX(-50%) translateY(-9px) rotate(-16deg) scale(0.96, 1.04);
      }}
    }}
    .prince-pet-rig.action-skid {{
      animation: princeSkidBrake 0.38s cubic-bezier(0.2, 0.8, 0.3, 1) forwards !important;
    }}
    @keyframes princeSkidBrake {{
      0% {{
        transform: translateX(-50%) translateY(5px) rotate(14deg) scale(1.08, 0.92);
      }}
      45% {{
        transform: translateX(-50%) translateY(-3px) rotate(-4deg) scale(0.97, 1.03);
      }}
      100% {{
        transform: translateX(-50%) translateY(0) rotate(0deg) scale(1, 1);
      }}
    }}

    /* 动漫动态半透明残影 (Motion Blur Ghost Trail) */
    .dash-ghost-shadow {{
      position: absolute;
      bottom: 0;
      width: 130px;
      height: 215px;
      pointer-events: none;
      z-index: 3;
      transform-origin: 50% 100%;
      animation: ghostFadeOut 0.36s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
    }}
    @keyframes ghostFadeOut {{
      0% {{ opacity: 0.72; transform: scale(1); }}
      100% {{ opacity: 0; transform: scale(1.08) translateY(-6px); filter: blur(3px); }}
    }}

    /* 冲刺连续扬尘与急刹滑行烟云粒子 */
    .dash-dust-container {{
      position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
      pointer-events: none; width: 130px; height: 40px; z-index: 2;
    }}
    .dust-puff {{
      position: absolute; bottom: 0; width: 18px; height: 18px; border-radius: 50%;
      background: radial-gradient(circle at 35% 35%, rgba(245, 230, 215, 0.9) 0%, rgba(210, 190, 170, 0.6) 60%, transparent 80%);
      opacity: 0;
      animation: dustAnimeRise 0.5s ease-out forwards;
    }}
    @keyframes dustAnimeRise {{
      0% {{ transform: translate(0, 0) scale(0.4); opacity: 0.9; }}
      50% {{ opacity: 0.8; }}
      100% {{ transform: translate(var(--dust-x, 30px), -24px) scale(1.8); opacity: 0; }}
    }}
    .skid-smoke-puff {{
      position: absolute; bottom: 2px; width: 22px; height: 22px; border-radius: 50%;
      background: radial-gradient(circle at 40% 40%, rgba(255, 255, 255, 0.95) 0%, rgba(245, 235, 225, 0.7) 50%, transparent 80%);
      opacity: 0;
      animation: skidSmokeDrift 0.42s ease-out forwards;
    }}
    @keyframes skidSmokeDrift {{
      0% {{ transform: translate(0, 0) scale(0.5); opacity: 0.95; }}
      100% {{ transform: translate(var(--skid-dx, 36px), -12px) scale(2.2); opacity: 0; filter: blur(2px); }}
    }}

    /* ========================================================= */
    /* 核心 4：大正雾云杉木箱 8 帧分镜 360° 转木箱神技 */
    /* ========================================================= */
    .box-action-container {{
      position: absolute;
      top: 15px;
      left: 50%;
      transform: translateX(-50%);
      width: 160px;
      height: 220px;
      z-index: 25;
      display: none;
      pointer-events: none;
    }}
    .show-box-action {{
      display: block !important;
      pointer-events: auto !important;
    }}

    /* 8 帧木箱分镜精灵视窗 */
    .box-sprite-viewport {{
      position: relative;
      width: 160px;
      height: 220px;
      overflow: hidden;
      transform-origin: bottom center;
    }}

    /* 精灵图平铺层 (1280px x 220px) */
    .box-sprite-strip {{
      position: absolute;
      top: 0; left: 0;
      width: 1280px;
      height: 220px;
      background-image: url('${{BOX_SPIN_SHEET}}');
      background-size: 1280px 220px;
      background-repeat: no-repeat;
    }}

    /* 动效 A：360度高速转木箱 + 抛物线腾空 + 真实挤压拉伸 */
    .action-box-spin .box-sprite-viewport {{
      animation: animeBoxSpinToss 1.25s cubic-bezier(0.2, 0.8, 0.25, 1) forwards !important;
    }}
    .action-box-spin .box-sprite-strip {{
      animation: playBox8Frames 0.4s steps(8) infinite !important;
    }}
    @keyframes playBox8Frames {{
      from {{ transform: translateX(0); }}
      to {{ transform: translateX(-1280px); }}
    }}

    @keyframes animeBoxSpinToss {{
      0% {{
        transform: translateY(0) scale(1.15, 0.85); /* 预备蓄力下沉 */
      }}
      25% {{
        transform: translateY(-68px) scale(1.05, 1.05) rotate(14deg); /* 腾空冲顶高速旋转 */
      }}
      55% {{
        transform: translateY(-75px) scale(1.08, 1.08) rotate(-10deg);
      }}
      80% {{
        transform: translateY(-15px) scale(0.96, 1.04); /* 重力加速坠落 */
      }}
      90% {{
        transform: translateY(8px) scale(1.36, 0.65); /* 落地强烈挤压形变 (Squash) */
      }}
      96% {{
        transform: translateY(-5px) scale(0.92, 1.08); /* 弹性向上回弹 (Stretch) */
      }}
      100% {{
        transform: translateY(0) scale(1, 1); /* 平稳落定 */
      }}
    }}

    /* 落地冲击波光环图层 */
    .box-impact-ring {{
      position: absolute;
      bottom: -15px;
      left: 50%;
      transform: translateX(-50%) scale(0.3);
      width: 200px;
      height: 200px;
      background-image: url('${{BOX_IMPACT_FX}}');
      background-size: contain;
      background-repeat: no-repeat;
      pointer-events: none;
      opacity: 0;
      z-index: 20;
    }}
    .action-box-spin .box-impact-ring {{
      animation: shockwaveBurst 0.65s ease-out 0.88s forwards !important;
    }}
    @keyframes shockwaveBurst {{
      0% {{ transform: translateX(-50%) scale(0.3); opacity: 0; }}
      20% {{ opacity: 1; transform: translateX(-50%) scale(0.9); }}
      100% {{ transform: translateX(-50%) scale(1.4); opacity: 0; }}
    }}

    /* 转木箱飞旋的风刃与枫叶樱花粒子 */
    .box-spin-particles {{
      position: absolute; inset: -40px; pointer-events: none; z-index: 30; opacity: 0;
    }}
    .action-box-spin .box-spin-particles {{ opacity: 1 !important; }}
    .spin-petal {{ position: absolute; font-size: 18px; opacity: 0; }}
    .action-box-spin .spin-petal.sp1 {{ top: 20px; left: -15px; animation: petalAnimeBurst 1s ease-out 0.15s; }}
    .action-box-spin .spin-petal.sp2 {{ top: 10px; right: -20px; animation: petalAnimeBurst 1s ease-out 0.3s; }}
    .action-box-spin .spin-petal.sp3 {{ bottom: 20px; left: -20px; animation: petalAnimeBurst 1s ease-out 0.45s; }}
    .action-box-spin .spin-petal.sp4 {{ bottom: 10px; right: -15px; animation: petalAnimeBurst 1s ease-out 0.6s; }}
    @keyframes petalAnimeBurst {{
      0% {{ transform: translate(30px, 30px) rotate(0deg) scale(0.4); opacity: 0; }}
      30% {{ opacity: 1; transform: translate(var(--tx, -45px), var(--ty, -35px)) rotate(180deg) scale(1.3); }}
      100% {{ opacity: 0; transform: translate(var(--tx, -80px), var(--ty, -60px)) rotate(420deg) scale(0.8); }}
    }}

    /* 动效 B：钻木箱与探头探脑 (Peek-a-boo Box) */
    .box-peek-container {{
      position: absolute; inset: 0; display: none; z-index: 10;
    }}
    .action-box-peek .box-peek-container {{ display: block !important; }}
    .action-box-peek .box-sprite-viewport {{ display: none !important; }}

    .peek-box-body {{
      position: absolute; inset: 0;
      background: linear-gradient(180deg, #422518 0%, #2b160f 45%, #1c0e09 100%);
      border: 3px solid #140b07; border-radius: 6px;
      box-shadow: inset 0 0 12px rgba(0,0,0,0.7), 0 8px 20px rgba(0,0,0,0.6);
      overflow: hidden;
    }}
    .peek-box-body::before {{
      content: ''; position: absolute; inset: 4px;
      background: repeating-linear-gradient(90deg, transparent 0, transparent 20px, rgba(0,0,0,0.18) 20px, rgba(0,0,0,0.18) 22px);
      border: 1px solid rgba(197, 155, 39, 0.25); border-radius: 3px; pointer-events: none;
    }}
    .peek-box-interior {{
      position: absolute; inset: 10px 14px; background: #0d0604; border-radius: 4px;
      overflow: hidden; z-index: 4; display: flex; justify-content: center; align-items: flex-end;
    }}
    .peeker-chibi-img {{
      width: 110px; height: 135px; object-fit: contain;
      transform: translateY(12px) scale(1);
      transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
      filter: drop-shadow(0 -4px 8px rgba(0,0,0,0.5));
    }}
    .peek-box-door {{
      position: absolute; inset: 10px 12px;
      background: linear-gradient(180deg, #4a281a 0%, #351a10 50%, #200f09 100%);
      border: 2px solid #140b07; border-radius: 3px;
      transform-origin: left center; transform-style: preserve-3d;
      transition: transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
      z-index: 12; box-shadow: inset 0 0 8px rgba(0,0,0,0.6), 2px 0 6px rgba(0,0,0,0.5);
    }}
    .action-box-peek .peek-box-door {{ transform: rotateY(-112deg) !important; }}
    .action-box-peek .peeker-chibi-img {{ transform: translateY(-4px) scale(1.08) !important; }}

    /* 摸头动作 */
    .action-headpat #bone-head {{ transform: translateY(9px) scale(0.95) rotate(-5deg) !important; }}
    .action-headpat #bone-arm-l {{ transform: rotate(-28deg) !important; }}
    .action-headpat #bone-arm-r {{ transform: rotate(28deg) !important; }}

    /* 气鼓跺脚 */
    .action-stomp #bone-leg-r {{ animation: stompLeg 0.18s 8 alternate !important; }}
    .action-stomp #bone-head {{ animation: stompHead 0.18s 8 alternate !important; }}
    @keyframes stompLeg {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-18px) rotate(18deg); }} }}
    @keyframes stompHead {{ 0% {{ transform: rotate(-6deg); }} 100% {{ transform: rotate(6deg) translateY(3px); }} }}

    /* 血鬼术爆血 */
    .action-burst {{
      filter: drop-shadow(0 0 25px rgba(220, 38, 38, 0.95)) drop-shadow(0 0 12px #f43f5e) !important;
      animation: burstShake 0.1s infinite alternate !important;
    }}
    @keyframes burstShake {{ 0% {{ transform: translateX(-4px) scale(1.02); }} 100% {{ transform: translateX(4px) scale(1.04); }} }}

    .action-sleep #bone-head {{ transform: translateY(14px) rotate(9deg) scale(0.95) !important; }}
    .action-sleep #bone-arm-r {{ transform: rotate(-38deg) translateY(-8px) !important; }}

    /* 小王子立绘样式 */
    .prince-avatar-img {{
      width: 100%; height: 100%; object-fit: contain; pointer-events: none;
      filter: drop-shadow(0 6px 14px rgba(250, 204, 21, 0.25));
      transform-origin: bottom center; transition: transform 0.2s ease-out;
    }}
    .head-music-bob {{ transform: rotate(7deg) scale(1.05) !important; }}
    .prince-music-bob {{ transform: rotate(5deg) scale(1.04) !important; }}

    /* 小王子动作层 */
    .prince-action-layer {{
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      pointer-events: none; opacity: 0; transition: opacity 0.35s ease, transform 0.35s ease;
      display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 20;
    }}
    .action-fox #layer-action-fox {{ opacity: 1 !important; pointer-events: auto !important; }}
    .action-fox #prince-avatar-body {{ opacity: 0 !important; transform: scale(0.95); }}
    .prince-fox-img {{
      width: 100%; height: 100%; object-fit: contain;
      filter: drop-shadow(0 8px 18px rgba(249, 115, 22, 0.45));
      animation: foxCuddle 1.8s infinite ease-in-out; transform-origin: bottom center;
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
    .wind-scarf-ribbon {{
      position: absolute; top: 62px; left: -25px; width: 140px; height: 35px;
      background: linear-gradient(90deg, #dc2626 0%, #ef4444 60%, rgba(254, 202, 202, 0.8) 100%);
      border-radius: 18px 8px 18px 8px; box-shadow: 0 0 14px rgba(239, 68, 68, 0.85), inset 0 0 6px #fff;
      transform-origin: right center; animation: scarfRibbonWave 0.4s infinite ease-in-out alternate;
    }}
    @keyframes scarfRibbonWave {{
      0% {{ transform: rotate(-18deg) skewY(-8deg) scaleY(0.85); }}
      50% {{ transform: rotate(12deg) skewY(12deg) scaleY(1.2) translateY(-8px); }}
      100% {{ transform: rotate(-12deg) skewY(-6deg) scaleY(0.9); }}
    }}

    .action-stars #layer-action-stars {{ opacity: 1 !important; pointer-events: auto !important; }}
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
      position: absolute; bottom: calc(100% + 22px); left: 50%;
      transform: translateX(-50%) translateY(10px) scale(0.9); width: 275px;
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(30, 41, 59, 0.98) 100%);
      border: 1.5px solid var(--lp-star-gold); border-radius: 12px; padding: 10px 14px;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.65), 0 0 16px rgba(250, 204, 21, 0.3);
      pointer-events: none; opacity: 0; transition: all 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
      z-index: 150; backdrop-filter: blur(10px);
    }}
    .pet-smart-bubble.show {{
      opacity: 1 !important; pointer-events: auto !important; transform: translateX(-50%) translateY(0) scale(1) !important;
    }}
    .pet-smart-bubble::after {{
      content: ''; position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
      border: 8px solid transparent; border-top-color: var(--lp-star-gold);
    }}

    .bubble-tag-bar {{ display: flex; justify-content: space-between; align-items: center; font-size: 10px; font-weight: bold; margin-bottom: 5px; }}
    .bubble-tag-text {{ color: var(--lp-star-gold); display: flex; align-items: center; gap: 4px; }}
    .bubble-close-btn {{ background: transparent; border: none; color: #94a3b8; font-size: 11px; cursor: pointer; padding: 2px 4px; }}
    .bubble-close-btn:hover {{ color: #fff; }}
    .bubble-main-txt {{ font-size: 12px; line-height: 1.55; color: #f8fafc; font-weight: 500; }}
    .bubble-sub-txt {{ font-size: 9.5px; color: #94a3b8; font-style: italic; margin-top: 4px; line-height: 1.35; }}

    /* 快捷胶囊条 */
    .nezuko-action-capsule {{
      position: absolute; top: -52px; left: 50%;
      transform: translateX(-50%) translateY(8px) scale(0.92);
      background: linear-gradient(135deg, rgba(35, 22, 18, 0.95) 0%, rgba(20, 12, 10, 0.98) 100%);
      border: 1.5px solid var(--ds-brass-gold); border-radius: 28px; padding: 5px 10px;
      display: flex; align-items: center; gap: 7px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.65), 0 0 16px rgba(244, 143, 177, 0.35);
      opacity: 0; pointer-events: none;
      transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
      z-index: 100; backdrop-filter: blur(8px);
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

    /* QQ音乐卡片 */
    .qq-music-player-box {{
      background: linear-gradient(180deg, rgba(16, 185, 129, 0.12) 0%, rgba(20, 12, 10, 0.9) 100%);
      border: 1.5px solid var(--qq-green); border-radius: 8px; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px;
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
  `;
  document.head.appendChild(styleEl);

  // ==========================================
  // 六、DOM 组装 (含 8 帧分镜木箱与落地冲击波视窗)
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
      </div>

      <!-- 头顶快捷胶囊条 -->
      <div class="nezuko-action-capsule" id="nezuko-action-capsule">
        <button class="nezuko-capsule-btn btn-switch-pet" id="btn-quick-switch" data-tip="切换角色 (祢豆子/小王子)" title="切换角色">🔁</button>
        <button class="nezuko-capsule-btn btn-roam-mode roaming" id="btn-quick-roam" data-tip="自主走动漫步 (已开启)" title="切换自主漫步/锁定">🚶</button>
        <div id="action-buttons-container" style="display:flex; gap:7px;"></div>
        <button class="nezuko-capsule-btn btn-music-spin" id="btn-quick-music" data-tip="QQ音乐播放/切歌" title="遥控电脑QQ音乐">🎵</button>
        <button class="nezuko-capsule-btn" id="btn-quick-board" data-tip="配额看板" title="打开配额看板">🎋</button>
      </div>

      <!-- 情绪浮动微气泡 -->
      <div class="floating-mood-bubble" id="floating-mood-bubble">🌸</div>

      <!-- 角色 1：祢豆子 2D 骨骼机架 (支持双关节行走与风火轮飞奔) -->
      <div class="nezuko-pet-rig" id="pet-nezuko" style="display:none;" title="双击打开看板 · 单击摸头 · 拖拽移动 · 滚轮切歌">
        <div class="bone-layer" id="bone-leg-l"></div>
        <div class="bone-layer" id="bone-leg-r"></div>
        <div class="bone-layer" id="bone-torso"></div>
        <div class="bone-layer" id="bone-arm-l"></div>
        <div class="bone-layer" id="bone-arm-r"></div>
        <div class="bone-layer" id="bone-head">
          <div class="nezuko-eyelid-overlay" id="nezuko-eyelid"></div>
        </div>
      </div>

      <!-- 角色 2：大正雾云杉木箱 (8帧360°旋转分镜 + 探头探脑视窗) -->
      <div class="box-action-container" id="box-action-container">
        <!-- 8 帧分镜精灵视窗 (用于 360 度转木箱神技) -->
        <div class="box-sprite-viewport" id="box-sprite-viewport">
          <div class="box-sprite-strip"></div>
        </div>

        <!-- 落地冲击波光环图层 -->
        <div class="box-impact-ring"></div>

        <!-- 飞旋的枫叶樱花粒子 -->
        <div class="box-spin-particles">
          <span class="spin-petal sp1" style="--tx:-50px; --ty:-40px;">🍁</span>
          <span class="spin-petal sp2" style="--tx:60px; --ty:-45px;">🌸</span>
          <span class="spin-petal sp3" style="--tx:-55px; --ty:30px;">🍂</span>
          <span class="spin-petal sp4" style="--tx:50px; --ty:35px;">🌸</span>
        </div>

        <!-- 探头探脑专属视窗 (用于钻木箱动作) -->
        <div class="box-peek-container" id="box-peek-container">
          <div class="peek-box-body">
            <div class="peek-box-interior">
              <img src="${{NEZUKO_PEEKER_HEAD}}" class="peeker-chibi-img" alt="木箱里的祢豆子">
            </div>
            <div class="peek-box-door"></div>
          </div>
        </div>
      </div>

      <!-- 冲刺奔跑烟尘粒子容器 -->
      <div class="dash-dust-container" id="dash-dust-container"></div>

      <!-- 角色 3：小王子 B612 治愈多图层动态机架 -->
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

        <!-- 动画级走动漫步与冲刺飞奔控制区 -->
        <div class="nezuko-section-box" style="background: rgba(16, 185, 129, 0.15); border-color: #10b981;">
          <div class="nezuko-section-title">
            <span style="color:#6ee7b7;">🚶 动画级物理走动与冲刺</span>
            <span id="roam-status-tag" style="font-size:10px; color:#81c784;">● 自由漫步中</span>
          </div>
          <div style="font-size:10px; color:#cbd5e1; margin-bottom:8px; line-height:1.4;">
            具备双关节起伏步态与极速风火轮冲刺；遇到边界平滑掉头；支持一键暂停自由漫步。
          </div>
          <div style="display:flex; gap:6px;">
            <button class="nezuko-ctrl-btn" id="btn-toggle-roam" style="flex:1; padding:5px; background:linear-gradient(135deg, #059669, #047857); border-color:#34d399; font-weight:bold;">
              🚶 切换漫步模式 (开/关)
            </button>
            <button class="nezuko-ctrl-btn" id="btn-instant-dash" style="padding:5px 10px; background:linear-gradient(135deg, #ec4899, #be185d); font-weight:bold;">
              🏃 立即冲刺狂奔
            </button>
          </div>
        </div>

      </div>
    </div>
  `;
  document.body.appendChild(root);

  // ==========================================
  // 七、DOM 元素引用与交互绑定
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
  const moodBubble = document.getElementById('floating-mood-bubble');

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
    bubbleTagText.textContent = cfg.tag || '✦ 桌面守护';
    bubbleMainTxt.innerHTML = cfg.zh || '';
    bubbleSubTxt.textContent = cfg.sub || '';
    smartBubble.classList.add('show');
    if (smartBubbleHideTimer) clearTimeout(smartBubbleHideTimer);
    if (duration > 0) smartBubbleHideTimer = setTimeout(() => hideSmartBubble(), duration);
  }}
  function hideSmartBubble() {{
    smartBubble.classList.remove('show');
    if (smartBubbleHideTimer) {{ clearTimeout(smartBubbleHideTimer); smartBubbleHideTimer = null; }}
  }}
  bubbleCloseBtn.addEventListener('click', (e) => {{ e.stopPropagation(); hideSmartBubble(); }});

  // QQ 音乐状态更新
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
  // 八、动态生理眨眼与情绪微表情系统
  // ==========================================
  function scheduleNextBlink() {{
    const delay = 3200 + Math.random() * 2600;
    setTimeout(() => {{
      if (activePet === 'nezuko' && petNezuko.style.display !== 'none') {{
        petNezuko.classList.add('is-blinking');
        setTimeout(() => {{
          petNezuko.classList.remove('is-blinking');
          scheduleNextBlink();
        }}, 130);
      }} else {{
        scheduleNextBlink();
      }}
    }}, delay);
  }}
  scheduleNextBlink();

  const MOOD_LIST = ['🌸', '✨', '💤', '❓', '💖', '🍵', '🍂'];
  function showRandomMood() {{
    if (Math.random() < 0.45) {{
      const mood = MOOD_LIST[Math.floor(Math.random() * MOOD_LIST.length)];
      moodBubble.textContent = mood;
      moodBubble.classList.add('active');
      setTimeout(() => moodBubble.classList.remove('active'), 2000);
    }}
  }}
  setInterval(showRandomMood, 8500);

  // ==========================================
  // 九、动画级行走与冲刺位移引擎 (PetMotionController)
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
    puff.style.setProperty('--dust-x', (facingDirection > 0 ? '30px' : '-30px'));
    dustContainer.appendChild(puff);
    setTimeout(() => puff.remove(), 550);
  }}

  // 动画级行走小碎步
  function walkTo(targetRight, speed = 1.0, onComplete = null) {{
    if (isActionPlaying) return;
    const maxRight = Math.min(window.innerWidth - 180, 850);
    const minRight = 24;
    targetRight = Math.max(minRight, Math.min(maxRight, targetRight));

    const dist = targetRight - curRight;
    if (Math.abs(dist) < 15) return;

    const dir = dist > 0 ? 1 : -1;
    updateFacing(dir);

    const activeRig = activePet === 'nezuko' ? petNezuko : petPrince;
    activeRig.classList.add('is-walking');
    isMoving = true;

    const durationSec = Math.max(0.65, Math.abs(dist) / (125 * speed));
    root.style.transition = `right ${{durationSec}}s cubic-bezier(0.25, 1, 0.5, 1), bottom 0.3s ease`;
    root.style.right = targetRight + 'px';
    curRight = targetRight;

    petAudio.playFootstep();

    setTimeout(() => {{
      activeRig.classList.remove('is-walking');
      isMoving = false;
      if (onComplete) onComplete();
    }}, durationSec * 1000);
  }}

  // 极速风火轮狂奔冲刺与急刹车 (Run Dash)
  function runDash(customDist = 0) {{
    if (isActionPlaying) return;
    isActionPlaying = true;
    const maxRight = Math.min(window.innerWidth - 180, 850);
    const minRight = 24;

    let targetDist = customDist !== 0 ? customDist : (facingDirection > 0 ? 300 : -300);
    let targetRight = curRight + targetDist;

    if (targetRight > maxRight) {{
      targetRight = curRight - 300;
      updateFacing(-1);
    }} else if (targetRight < minRight) {{
      targetRight = curRight + 300;
      updateFacing(1);
    }}

    const dist = targetRight - curRight;
    updateFacing(dist > 0 ? 1 : -1);

    const activeRig = activePet === 'nezuko' ? petNezuko : petPrince;
    activeRig.classList.add('is-running');
    petAudio.playSpinWind();

    const dustTimer = setInterval(spawnDustPuff, 70);

    const durationSec = 0.95;
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
      }}, 400);
    }}, durationSec * 1000);
  }}

  // 自主漫步巡航心跳
  let roamInterval = null;
  function startRoamHeartbeat() {{
    if (roamInterval) clearInterval(roamInterval);
    roamInterval = setInterval(() => {{
      if (!isRoamingEnabled || isMoving || isActionPlaying || isDragging || mainCard.style.display === 'flex') return;

      const rnd = Math.random();
      if (rnd < 0.38) {{
        walkTo(curRight + 65 + Math.random() * 95, 1.0);
      }} else if (rnd < 0.76) {{
        walkTo(curRight - (65 + Math.random() * 95), 1.0);
      }} else if (rnd < 0.90) {{
        updateFacing(facingDirection * -1);
        moodBubble.textContent = '❓';
        moodBubble.classList.add('active');
        setTimeout(() => moodBubble.classList.remove('active'), 1800);
      }} else {{
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
  // 十、8 帧原画分镜 360° 转木箱神技动作引擎
  // ==========================================
  let boxSpinCount = 0;
  function triggerDemonSlayerBoxAction() {{
    if (isActionPlaying) return;
    isActionPlaying = true;

    boxSpinCount++;
    const isSpin = (boxSpinCount % 2 === 1);

    petNezuko.style.display = 'none';
    boxContainer.classList.add('show-box-action');
    boxContainer.className = 'box-action-container show-box-action';

    if (isSpin) {{
      // 动作 A：8 帧分镜 360° 转木箱 (Spin Box Whirlwind)
      boxContainer.classList.add('action-box-spin');
      petAudio.playSpinWind();

      // 落地砸地音效与冲击波同步
      setTimeout(() => petAudio.playWoodThud(), 880);

      setTimeout(() => {{
        // 旋转砸地完毕，平稳切换至探头探脑
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
        }}, 2400);
      }}, 1300);
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
  // 十一、角色切换与胶囊条按钮绑定
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
        <button class="nezuko-capsule-btn" data-action="box" data-tip="8帧分镜 360°转木箱 / 钻木箱" title="8帧大正雾云杉木箱360度凌空旋转">📦</button>
        <button class="nezuko-capsule-btn" data-action="run" data-tip="极速风火轮冲刺飞奔" title="风火轮狂奔与急刹车滑行">🏃</button>
        <button class="nezuko-capsule-btn" data-action="headpat" data-tip="摸头杀眯眯眼蹭蹭" title="摸头闭眼享受蹭蹭">🐱</button>
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

  switchPet(activePet);

  // 胶囊防消失
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

  // 拖拽物理引擎
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
        root.style.transition = 'none';
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
        root.style.transition = 'right 0.75s cubic-bezier(0.25, 1, 0.5, 1), bottom 0.3s ease';
        setTimeout(() => {{ isDragging = false; }}, 50);
      }}
    }};
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }};

  petNezuko.addEventListener('mousedown', onDragDown);
  petPrince.addEventListener('mousedown', onDragDown);

}})();
"""

target_js = REPO_ROOT / "resources" / "nezuko-pet.js"
target_js.write_text(js_code, encoding="utf-8")
print(f"✅ 成功生成动画级别动作引擎桌宠代码: {target_js} ({len(js_code.encode('utf-8'))} 字节)")

# 同步写入 scripts/build_nezuko_pet.py
build_py = REPO_ROOT / "scripts" / "build_nezuko_pet.py"
build_py.write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
print(f"✅ 成功同步 build_nezuko_pet.py: {build_py}")
