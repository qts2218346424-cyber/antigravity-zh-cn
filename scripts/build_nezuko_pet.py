# -*- coding: utf-8 -*-
"""
生成腾讯 QQ 宠物风格 + 复刻《鬼灭之刃》原动漫真实手脚骨骼肢体动作机 + Antigravity 软件全局大正和风主题的核心组件 (resources/nezuko-pet.js)
两大突破性升级：
1. 【手脚身体真正独立运动的 2D 骨骼分肢动画机】：
   - 彻底告别“单张死图在抖动”！
   - 将角色精准拆解为 6 大独立解剖骨骼关节图层（头部、和服躯干、左手臂、右手臂、左脚、右脚）；
   - 豆豆眼风火轮狂奔：手臂以肩膀为轴前后狂甩，双腿以髋关节为轴交替快速迈步蹬地，身体上下颠簸，真正的手脚动态！
   - 气鼓鼓跺脚：右腿真实高频抬起踩地（连续跺脚），双手叉腰，身体震颤！
   - 摸头蹭蹭：头部主动仰头左右蹭，双手捧脸！
   - 揉眼打哈欠：手臂真正抬起揉眼睛！
   - 血鬼术爆血：双手真正推到胸前合十，全身喷涌爆血烈焰！
2. 【Antigravity 软件界面的《鬼灭之刃》大正和风全套全局主题】：
   - 真正将鬼灭之刃主题注入整个 Antigravity 软件界面！
   - 活动栏：炭治郎绿黑市松纹锦缎饰边 + 大正黑胡桃木纹 + 日之呼吸烫金指示器；
   - 侧边栏：祢豆子深粉黑木纹 + 矢量粉金麻叶纹底纹 + 烫金大正标题；
   - 状态栏：炭治郎绿黑市松格大正装饰带 + 黄铜金边 + [ 鬼滅の刃 · 竈門禰豆子 ] 专属日式印章；
   - 标题栏与标签栏：大正木箱质感 + 祢豆子粉红流光激活标签；
   - 滚动条：大正竹节黄铜滑块。
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

source_png = MEDIA_DIR / "nezuko_chibi_pet.png"
im = Image.open(source_png).convert('RGBA')
w, h = im.size

# 1. 精确裁剪 6 大独立骨骼肢体切片
crop_boxes = {
    'head': (0, 0, w, 180),
    'torso': (50, 160, 142, 275),
    'arm_l': (0, 160, 75, 265),
    'arm_r': (120, 160, w, 265),
    'leg_l': (60, 265, 102, h),
    'leg_r': (98, 265, 140, h)
}

b64_parts = {}
for name, box in crop_boxes.items():
    cropped = im.crop(box)
    buf = BytesIO()
    cropped.save(buf, format='WEBP', quality=92)
    b64_parts[name] = base64.b64encode(buf.getvalue()).decode('ascii')

js_code = f"""/**
 * Antigravity 灶门祢豆子 · 鬼灭之刃全套主题与真实手脚骨骼动作引擎 (Demon Slayer Engine 3.0)
 * 1. 2D 骨骼关节分肢动画机 (头部、躯干、左臂、右臂、左脚、右脚独立物理摆动，手脚真在动)
 * 2. Antigravity 软件界面全套《鬼灭之刃》大正和风全局主题 (活动栏、侧边栏、状态栏、标签栏、滚动条)
 * 3. 彻底修复动作条 Hover Gap 消失 Bug (透明安全桥接 + 450ms防抖 + 单击锁定)
 * 4. 原生模型配额看板 (Gemini / Claude / GPT 每周与5小时限额及重置倒计时)
 * 5. 鬼灭之刃随身 BGM 音乐盒 (内置 Web Audio 八音盒 + 本地音乐导入)
 */

(function() {{
  if (typeof window === 'undefined' || window.__NEZUKO_PET_INITIALIZED__) return;
  window.__NEZUKO_PET_INITIALIZED__ = true;

  // 6 大骨骼解剖图层 Base64
  const BONE_HEAD = "data:image/webp;base64,{b64_parts['head']}";
  const BONE_TORSO = "data:image/webp;base64,{b64_parts['torso']}";
  const BONE_ARM_L = "data:image/webp;base64,{b64_parts['arm_l']}";
  const BONE_ARM_R = "data:image/webp;base64,{b64_parts['arm_r']}";
  const BONE_LEG_L = "data:image/webp;base64,{b64_parts['leg_l']}";
  const BONE_LEG_R = "data:image/webp;base64,{b64_parts['leg_r']}";

  // ==========================================
  // 一、Antigravity 软件界面《鬼灭之刃》全局主题注入
  // ==========================================
  const ideThemeStyle = document.createElement('style');
  ideThemeStyle.id = 'agy-demon-slayer-ide-theme';
  ideThemeStyle.textContent = `
    /* 1. 活动栏 (Activity Bar) - 炭治郎黑绿市松纹与大正黑胡桃木 */
    .part.activitybar,
    #workbench\\\\.parts\\\\.activitybar,
    .activitybar {{
      background: linear-gradient(180deg, #1f130e 0%, #150c09 100%) !important;
      border-right: 2px solid #c59b27 !important;
      box-shadow: 2px 0 10px rgba(0, 0, 0, 0.45) !important;
      position: relative !important;
    }}
    .part.activitybar::before,
    #workbench\\\\.parts\\\\.activitybar::before,
    .activitybar::before {{
      content: '' !important;
      position: absolute !important;
      top: 0 !important; left: 0 !important; bottom: 0 !important;
      width: 5px !important;
      background: repeating-linear-gradient(45deg, #2e7d32 0, #2e7d32 6px, #111 6px, #111 12px) !important;
      z-index: 10 !important;
    }}
    .activitybar .action-item.checked,
    .activitybar .action-item.active {{
      border-left: 3px solid #ffd54f !important;
    }}
    .activitybar .action-item.checked .action-label,
    .activitybar .action-item.active .action-label {{
      color: #ffd54f !important;
      filter: drop-shadow(0 0 6px rgba(255, 213, 79, 0.6)) !important;
    }}

    /* 2. 侧边栏 (Sidebar) - 祢豆子深粉黑木纹 + 麻叶纹底纹 */
    .part.sidebar,
    #workbench\\\\.parts\\\\.sidebar,
    .sidebar {{
      background: linear-gradient(135deg, rgba(28, 17, 13, 0.98) 0%, rgba(18, 10, 8, 0.99) 100%) !important;
      border-right: 1.5px solid rgba(197, 155, 39, 0.4) !important;
      position: relative !important;
    }}
    .sidebar .title-label h2,
    .sidebar .pane-header .title {{
      color: #ffd54f !important;
      font-weight: 700 !important;
      text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8) !important;
      letter-spacing: 0.5px !important;
    }}
    .monaco-list.focused .monaco-list-row.selected,
    .monaco-list .monaco-list-row.selected {{
      background: linear-gradient(90deg, rgba(194, 24, 91, 0.35) 0%, rgba(35, 22, 18, 0.5) 100%) !important;
      color: #fff !important;
      border-left: 2px solid #f48fb1 !important;
    }}
    .monaco-list .monaco-list-row:hover:not(.selected) {{
      background: rgba(244, 143, 177, 0.12) !important;
    }}

    /* 3. 底部状态栏 (Status Bar) - 炭治郎绿黑市松纹锦缎带 */
    .part.statusbar,
    #workbench\\\\.parts\\\\.statusbar,
    .statusbar {{
      background: repeating-linear-gradient(45deg, #1b3820 0, #1b3820 8px, #111a13 8px, #111a13 16px) !important;
      border-top: 1.5px solid #c59b27 !important;
      color: #fff9c4 !important;
      box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.3) !important;
    }}
    .statusbar .statusbar-item a,
    .statusbar .statusbar-item {{
      color: #fff9c4 !important;
    }}
    .statusbar .statusbar-item:hover {{
      background: rgba(244, 143, 177, 0.25) !important;
    }}

    /* 4. 标题栏 (Titlebar) - 大正云杉木纹与黄铜下边框 */
    .part.titlebar,
    #workbench\\\\.parts\\\\.titlebar,
    .titlebar {{
      background: linear-gradient(90deg, #2b1711 0%, #1a0f0a 100%) !important;
      border-bottom: 1.5px solid #c59b27 !important;
    }}
    .titlebar .window-title {{
      color: #ffd54f !important;
      font-weight: 600 !important;
      text-shadow: 0 1px 3px rgba(0, 0, 0, 0.9) !important;
    }}

    /* 5. 编辑区标签栏 (Editor Tabs) - 祢豆子粉红呼吸流光 */
    .tabs-and-actions-container,
    .tab {{
      background: #140c09 !important;
    }}
    .tab.active {{
      background: linear-gradient(180deg, rgba(46, 26, 20, 0.9) 0%, #1f120d 100%) !important;
      border-top: 2.5px solid #f48fb1 !important;
      color: #fff !important;
      box-shadow: inset 0 1px 8px rgba(244, 143, 177, 0.2) !important;
    }}
    .tab:hover:not(.active) {{
      background: rgba(46, 26, 20, 0.5) !important;
    }}

    /* 6. 全局滚动条 (Scrollbars) - 大正黄铜竹节质感 */
    .monaco-scrollable-element .scrollbar .slider {{
      background: rgba(197, 155, 39, 0.45) !important;
      border-radius: 4px !important;
    }}
    .monaco-scrollable-element .scrollbar .slider:hover {{
      background: #f48fb1 !important;
      box-shadow: 0 0 6px rgba(244, 143, 177, 0.8) !important;
    }}
  `;

  // 根据本地设置决定是否启用软件全局主题 (默认开启)
  function isIdeThemeEnabled() {{
    const val = localStorage.getItem('__agy_demon_slayer_ide_theme__');
    return val === null || val === 'true';
  }}
  function setIdeTheme(enabled) {{
    localStorage.setItem('__agy_demon_slayer_ide_theme__', enabled ? 'true' : 'false');
    if (enabled) {{
      if (!document.getElementById('agy-demon-slayer-ide-theme')) {{
        document.head.appendChild(ideThemeStyle);
      }}
    }} else {{
      const el = document.getElementById('agy-demon-slayer-ide-theme');
      if (el) el.remove();
    }}
  }}
  if (isIdeThemeEnabled()) {{
    document.head.appendChild(ideThemeStyle);
  }}

  // ==========================================
  // 二、模型配额中枢 (Gemini 与 Claude/GPT 原生对应)
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
  // 三、鬼灭之刃 Web Audio 随身八音盒引擎
  // ==========================================
  const noteFreqs = {{
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.26, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50
  }};

  const PLAYLIST = [
    {{
      title: "竈門炭治郎のうた (灶门炭治郎之歌)",
      subtitle: "治愈抒情 · 椎名豪 / 中川奈美",
      notes: [
        ['G4', 0.45], ['A4', 0.45], ['B4', 0.7], ['D5', 0.45], ['B4', 0.7],
        ['A4', 0.45], ['G4', 0.45], ['E4', 0.9], ['G4', 0.45], ['A4', 0.9],
        ['B4', 0.45], ['D5', 0.45], ['E5', 0.9], ['D5', 0.45], ['B4', 0.9],
        ['A4', 0.45], ['B4', 0.45], ['A4', 0.45], ['G4', 1.0],
        ['D5', 0.45], ['E5', 0.45], ['G5', 0.9], ['E5', 0.45], ['D5', 0.7],
        ['B4', 0.45], ['D5', 0.45], ['E5', 0.9], ['D5', 0.9]
      ]
    }},
    {{
      title: "紅蓮華 (红莲华)",
      subtitle: "经典热血 OP · LiSA 和风版",
      notes: [
        ['D5', 0.3], ['D5', 0.3], ['C5', 0.3], ['A4', 0.3], ['C5', 0.3], ['D5', 0.6],
        ['D5', 0.3], ['E5', 0.3], ['F5', 0.3], ['E5', 0.3], ['D5', 0.3], ['C5', 0.6],
        ['A4', 0.3], ['C5', 0.3], ['D5', 0.45], ['D5', 0.45], ['C5', 0.45], ['D5', 0.9]
      ]
    }},
    {{
      title: "禰豆子の平穏 (祢豆子的日常)",
      subtitle: "活泼治愈 · 萌宠八音盒小调",
      notes: [
        ['E5', 0.35], ['G5', 0.35], ['A5', 0.5], ['G5', 0.35], ['E5', 0.5],
        ['D5', 0.35], ['E5', 0.35], ['G5', 0.7], ['E5', 0.35], ['D5', 0.7],
        ['C5', 0.35], ['D5', 0.35], ['E5', 0.5], ['G5', 0.35], ['A5', 0.7]
      ]
    }}
  ];

  class DemonSlayerMusicEngine {{
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
      if (this.ctx.state === 'suspended') {{
        this.ctx.resume();
      }}
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
      if (!this.isPlaying) return;
      if (this.customAudio) return;

      const track = PLAYLIST[this.currentTrack];
      if (this.stepIndex >= track.notes.length) {{
        this.stepIndex = 0;
      }}

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
      if (this.customAudio) {{
        this.customAudio.pause();
      }}
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

  const musicEngine = new DemonSlayerMusicEngine();

  let beatTimer = null;
  function triggerMusicBeat() {{
    const headEl = document.getElementById('bone-head');
    if (!headEl || !musicEngine.isPlaying) return;
    headEl.classList.add('head-music-bob');
    if (beatTimer) clearTimeout(beatTimer);
    beatTimer = setTimeout(() => {{
      headEl.classList.remove('head-music-bob');
    }}, 400);
  }}

  // ==========================================
  // 四、CSS 样式库 (含 2D 骨骼关节分肢连动动画机)
  // ==========================================
  const styleEl = document.createElement('style');
  styleEl.id = 'nezuko-pet-advanced-styles';
  styleEl.textContent = `
    :root {{
      --ds-pink: #f48fb1;
      --ds-dark-pink: #c2185b;
      --ds-crimson: #b71c1c;
      --ds-blood: #ff1744;
      --ds-tanjiro-green: #2e7d32;
      --ds-ichimatsu-black: #1b1b1b;
      --ds-wood-dark: #231612;
      --ds-wood-light: #3d271d;
      --ds-brass-gold: #c59b27;
      --ds-gold-glow: #ffd54f;
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

    /* ========================================================= */
    /* 核心突破：2D 骨骼肢体解剖画框与关节图层 (手脚真正独立运动) */
    /* ========================================================= */
    .nezuko-pet-rig {{
      position: relative;
      width: 130px;
      height: 215px;
      cursor: grab;
      filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.2));
      transition: transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
      transform-origin: bottom center;
    }}
    .nezuko-pet-rig:active {{
      cursor: grabbing;
    }}

    /* 6 大骨骼肢体独立图层 */
    .bone-layer {{
      position: absolute;
      background-size: contain;
      background-repeat: no-repeat;
      pointer-events: none;
      transition: transform 0.15s ease-out;
    }}

    /* 1. 头部 (含长发与发带): 支点在颈部 */
    #bone-head {{
      top: 0;
      left: 0;
      width: 130px;
      height: 121px;
      background-image: url('${{BONE_HEAD}}');
      transform-origin: 50% 90%;
      z-index: 10;
    }}

    /* 2. 躯干 (和服主袍): 支点在腰腹 */
    #bone-torso {{
      top: 108px;
      left: 34px;
      width: 62px;
      height: 77px;
      background-image: url('${{BONE_TORSO}}');
      transform-origin: 50% 100%;
      z-index: 6;
    }}

    /* 3. 左手臂 (画面左侧): 支点在左肩关节 */
    #bone-arm-l {{
      top: 108px;
      left: 0;
      width: 50px;
      height: 71px;
      background-image: url('${{BONE_ARM_L}}');
      transform-origin: 75% 20%;
      z-index: 8;
    }}

    /* 4. 右手臂 (画面右侧): 支点在右肩关节 */
    #bone-arm-r {{
      top: 108px;
      left: 81px;
      width: 49px;
      height: 71px;
      background-image: url('${{BONE_ARM_R}}');
      transform-origin: 25% 20%;
      z-index: 8;
    }}

    /* 5. 左小脚: 支点在左大腿髋关节 */
    #bone-leg-l {{
      top: 178px;
      left: 40px;
      width: 28px;
      height: 37px;
      background-image: url('${{BONE_LEG_L}}');
      transform-origin: 50% 10%;
      z-index: 4;
    }}

    /* 6. 右小脚: 支点在右大腿髋关节 */
    #bone-leg-r {{
      top: 178px;
      left: 66px;
      width: 28px;
      height: 37px;
      background-image: url('${{BONE_LEG_R}}');
      transform-origin: 50% 10%;
      z-index: 4;
    }}

    /* ========================================================= */
    /* 核心：原动漫 7 大名场面多骨骼关节分肢协同动力学 */
    /* ========================================================= */

    /* ===== 动作 1：小豆丁风火轮疾走狂奔 (手脚极速大摆动) ===== */
    .action-run #bone-arm-l {{
      animation: runArmL 0.16s infinite alternate ease-in-out !important;
    }}
    .action-run #bone-arm-r {{
      animation: runArmR 0.16s infinite alternate ease-in-out !important;
    }}
    .action-run #bone-leg-l {{
      animation: runLegL 0.16s infinite alternate ease-in-out !important;
    }}
    .action-run #bone-leg-r {{
      animation: runLegR 0.16s infinite alternate ease-in-out !important;
    }}
    .action-run #bone-torso {{
      animation: runTorso 0.16s infinite alternate ease-in-out !important;
    }}
    .action-run #bone-head {{
      animation: runHead 0.16s infinite alternate ease-in-out !important;
    }}
    .action-run {{
      animation: runStageHop 0.55s infinite alternate ease-in-out !important;
    }}

    @keyframes runArmL {{
      0% {{ transform: rotate(-55deg) translateY(-2px); }}
      100% {{ transform: rotate(55deg) translateY(2px); }}
    }}
    @keyframes runArmR {{
      0% {{ transform: rotate(55deg) translateY(2px); }}
      100% {{ transform: rotate(-55deg) translateY(-2px); }}
    }}
    @keyframes runLegL {{
      0% {{ transform: rotate(50deg) translateY(-3px); }}
      100% {{ transform: rotate(-50deg) translateY(3px); }}
    }}
    @keyframes runLegR {{
      0% {{ transform: rotate(-50deg) translateY(3px); }}
      100% {{ transform: rotate(50deg) translateY(-3px); }}
    }}
    @keyframes runTorso {{
      0% {{ transform: translateY(0) scaleY(0.96); }}
      100% {{ transform: translateY(-4px) scaleY(1.02); }}
    }}
    @keyframes runHead {{
      0% {{ transform: translateY(0) rotate(-3deg); }}
      100% {{ transform: translateY(-3px) rotate(3deg); }}
    }}
    @keyframes runStageHop {{
      0% {{ transform: scale(0.75) translateX(-32px) rotate(-6deg); }}
      100% {{ transform: scale(0.75) translateX(32px) rotate(6deg); }}
    }}

    /* ===== 动作 2：气鼓鼓跺小脚 (右腿高频连续跺地，身体剧烈震颤) ===== */
    .action-stomp #bone-arm-l {{
      transform: rotate(-28deg) translateY(-2px) !important;
    }}
    .action-stomp #bone-arm-r {{
      transform: rotate(28deg) translateY(-2px) !important;
    }}
    .action-stomp #bone-leg-r {{
      animation: stompRightFoot 0.2s infinite cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    .action-stomp #bone-torso {{
      animation: stompShockTorso 0.2s infinite ease-out !important;
    }}
    .action-stomp #bone-head {{
      animation: stompShockHead 0.2s infinite ease-out !important;
    }}

    @keyframes stompRightFoot {{
      0% {{ transform: rotate(-35deg) translateY(-10px); }}
      55% {{ transform: rotate(0deg) translateY(0); }}
      65% {{ transform: rotate(4deg) translateY(2px); }}
      100% {{ transform: rotate(-35deg) translateY(-10px); }}
    }}
    @keyframes stompShockTorso {{
      0%, 100% {{ transform: translateY(0); }}
      60% {{ transform: translateY(3px); }}
    }}
    @keyframes stompShockHead {{
      0%, 100% {{ transform: translateY(0) rotate(0deg); }}
      60% {{ transform: translateY(2px) rotate(-3deg); }}
    }}

    /* ===== 动作 3：抱竹歪头晃脑 (双手紧抱竹筒，小脑瓜节奏摆动) ===== */
    .action-tilt #bone-arm-l {{
      transform: rotate(18deg) translateY(-6px) !important;
    }}
    .action-tilt #bone-arm-r {{
      transform: rotate(-18deg) translateY(-6px) !important;
    }}
    .action-tilt #bone-head {{
      animation: tiltHeadSway 2.4s infinite ease-in-out !important;
    }}
    @keyframes tiltHeadSway {{
      0%, 100% {{ transform: rotate(0deg) translateY(0); }}
      25% {{ transform: rotate(-22deg) translateY(-3px); }}
      50% {{ transform: rotate(0deg) translateY(0); }}
      75% {{ transform: rotate(22deg) translateY(-3px); }}
    }}

    /* ===== 动作 4：血鬼术·爆血觉醒 (双手合十向前推，烈焰爆发) ===== */
    .action-burst #bone-arm-l {{
      transform: rotate(38deg) translateX(12px) translateY(-8px) !important;
    }}
    .action-burst #bone-arm-r {{
      transform: rotate(-38deg) translateX(-12px) translateY(-8px) !important;
    }}
    .action-burst #bone-head {{
      animation: burstHeadFlame 1.2s infinite ease-in-out !important;
    }}
    .action-burst {{
      filter: drop-shadow(0 0 20px rgba(255, 23, 68, 0.95)) saturate(1.4) !important;
    }}
    @keyframes burstHeadFlame {{
      0%, 100% {{ transform: scale(1); }}
      50% {{ transform: scale(1.08) translateY(-4px); }}
    }}

    /* ===== 动作 5：揉眼犯困打瞌睡 (手臂抬起揉眼睛，慢慢耷拉倒下) ===== */
    .action-sleep #bone-arm-l {{
      animation: sleepRubEye 1.6s infinite ease-in-out !important;
    }}
    .action-sleep #bone-arm-r {{
      transform: rotate(35deg) translateY(6px) !important;
    }}
    .action-sleep #bone-head {{
      transform: rotate(16deg) translateY(12px) !important;
    }}
    .action-sleep #bone-torso {{
      transform: rotate(6deg) translateY(8px) scale(0.95) !important;
    }}
    @keyframes sleepRubEye {{
      0%, 100% {{ transform: rotate(-65deg) translateX(4px) translateY(-14px); }}
      50% {{ transform: rotate(-80deg) translateX(8px) translateY(-18px); }}
    }}

    /* ===== 动作 6：摸头杀闭眼撒娇蹭蹭 (仰头向上拱，左右轻蹭) ===== */
    .action-headpat #bone-head {{
      animation: headpatCuddleMotion 1.4s infinite ease-in-out !important;
    }}
    .action-headpat #bone-arm-l {{
      transform: rotate(12deg) translateY(-4px) !important;
    }}
    .action-headpat #bone-arm-r {{
      transform: rotate(-12deg) translateY(-4px) !important;
    }}
    @keyframes headpatCuddleMotion {{
      0%, 100% {{ transform: translateY(0) rotate(0deg); }}
      50% {{ transform: translateY(-7px) rotate(10deg); }}
    }}

    /* ===== 动作 7：钻木箱捉迷藏 ===== */
    .action-box {{
      animation: boxPeekaboo 1.8s infinite ease-in-out !important;
    }}
    @keyframes boxPeekaboo {{
      0%, 100% {{ transform: scale(0.85) translateY(22px); opacity: 0.88; }}
      50% {{ transform: scale(0.92) translateY(8px); opacity: 1; }}
    }}

    /* QQ宠物拖拽被提起 (两腿空中慌乱蹬水挣扎) */
    .nezuko-picked-up {{
      transform: scale(1.08) translateY(-22px) rotate(-8deg) !important;
      filter: drop-shadow(0 14px 22px rgba(0, 0, 0, 0.35)) !important;
    }}
    .nezuko-picked-up #bone-leg-l {{
      animation: struggleLegL 0.18s infinite alternate ease-in-out !important;
    }}
    .nezuko-picked-up #bone-leg-r {{
      animation: struggleLegR 0.18s infinite alternate ease-in-out !important;
    }}
    @keyframes struggleLegL {{
      0% {{ transform: rotate(45deg); }}
      100% {{ transform: rotate(-45deg); }}
    }}
    @keyframes struggleLegR {{
      0% {{ transform: rotate(-45deg); }}
      100% {{ transform: rotate(45deg); }}
    }}
    .nezuko-picked-up ~ .nezuko-pet-ground-shadow {{
      transform: translateX(-50%) scale(0.55); opacity: 0.25;
    }}

    .head-music-bob {{
      transform: translateY(-4px) rotate(3deg) !important;
      transition: transform 0.15s ease-out;
    }}

    /* ========================================================= */
    /* 头顶快捷胶囊动作条 (带透明安全桥接垫片，彻底防消失) */
    /* ========================================================= */
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
    .nezuko-capsule-btn:active {{
      transform: scale(0.95);
    }}
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
    .nezuko-capsule-btn:hover::before {{
      opacity: 1;
      transform: translateX(-50%) scale(1);
    }}

    .btn-music-spin {{
      background: radial-gradient(circle, #ff80ab 20%, #231612 21%, #111 100%);
    }}
    .btn-music-spin.playing {{
      animation: recordSpin 3.5s infinite linear;
      border-color: var(--ds-pink);
      box-shadow: 0 0 10px rgba(244, 143, 177, 0.8);
    }}

    /* 多表情叠加层 */
    .nezuko-face-rig {{
      position: absolute;
      top: 36px;
      left: 38px;
      width: 56px;
      height: 44px;
      pointer-events: none;
      z-index: 15;
    }}
    .nezuko-eyes-default {{
      width: 100%; height: 100%; display: flex; justify-content: space-between; align-items: center;
      padding: 0 4px; box-sizing: border-box; opacity: 0;
    }}
    .nezuko-eyes-dot {{
      position: absolute; top: 14px; left: 6px; width: 44px; height: 16px;
      display: none; justify-content: space-between; align-items: center;
    }}
    .nezuko-eyes-dot::before, .nezuko-eyes-dot::after {{
      content: ''; width: 9px; height: 9px; background: #111; border-radius: 50%;
      box-shadow: 0 0 2px rgba(0,0,0,0.8);
    }}
    .nezuko-eyes-crescent {{
      position: absolute; top: 12px; left: 4px; width: 48px; height: 16px;
      display: none; justify-content: space-between;
    }}
    .nezuko-eyes-crescent::before, .nezuko-eyes-crescent::after {{
      content: ''; width: 16px; height: 8px; border-bottom: 3.5px solid #231612;
      border-radius: 0 0 16px 16px;
    }}
    .nezuko-cheeks-angry {{
      position: absolute; top: 18px; left: 0; width: 56px; height: 20px;
      display: none; justify-content: space-between;
    }}
    .nezuko-cheeks-angry::before, .nezuko-cheeks-angry::after {{
      content: ''; width: 14px; height: 14px;
      background: radial-gradient(circle, #ff80ab 0%, rgba(255, 64, 129, 0.4) 65%, transparent 100%);
      border-radius: 50%;
    }}
    .nezuko-demon-horn {{
      position: absolute; top: -14px; right: 14px; width: 16px; height: 22px;
      background: linear-gradient(135deg, #fff 0%, #e0e0e0 60%, #b0bec5 100%);
      clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
      transform: rotate(20deg); filter: drop-shadow(0 0 6px rgba(255, 23, 68, 0.8));
      display: none;
    }}
    .nezuko-demon-veins {{
      position: absolute; top: -4px; right: 6px; width: 22px; height: 20px;
      background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2 Q18 8 16 16 Q22 18 20 22 Q14 18 12 12 Q8 16 4 22' fill='none' stroke='%23ff1744' stroke-width='2'/%3E%3C/svg%3E") no-repeat center;
      display: none;
    }}

    .expr-dot .nezuko-eyes-dot {{ display: flex !important; }}
    .expr-crescent .nezuko-eyes-crescent {{ display: flex !important; }}
    .expr-angry .nezuko-cheeks-angry {{ display: flex !important; }}
    .expr-demon .nezuko-demon-horn,
    .expr-demon .nezuko-demon-veins {{ display: block !important; }}

    .nezuko-box-prop {{
      position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
      width: 110px; height: 140px;
      background: linear-gradient(180deg, var(--ds-wood-light) 0%, var(--ds-wood-dark) 100%);
      border: 3px solid var(--ds-brass-gold); border-radius: 8px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.5), inset 0 0 15px rgba(0,0,0,0.6);
      display: none; z-index: 1;
    }}
    .action-box ~ .nezuko-box-prop {{ display: block !important; }}

    .nezuko-fx-container {{ position: absolute; inset: 0; pointer-events: none; z-index: 25; }}
    .nezuko-fx-cross {{
      position: absolute; top: 15px; right: 18px; color: #ff1744; font-size: 22px; font-weight: 900;
      display: none; animation: crossShake 0.3s infinite;
    }}
    .action-stomp ~ .nezuko-fx-container .nezuko-fx-cross {{ display: block; }}
    @keyframes crossShake {{
      0% {{ transform: scale(1) rotate(0deg); }}
      50% {{ transform: scale(1.25) rotate(12deg); }}
      100% {{ transform: scale(1) rotate(-8deg); }}
    }}
    .nezuko-fx-zzz {{
      position: absolute; top: 0; right: 8px; color: #f48fb1; font-size: 16px; font-weight: bold;
      display: none; animation: zzzFloat 2.2s infinite linear;
    }}
    .action-sleep ~ .nezuko-fx-container .nezuko-fx-zzz {{ display: block; }}
    @keyframes zzzFloat {{
      0% {{ transform: translate(0, 0) scale(0.6); opacity: 0; }}
      50% {{ opacity: 1; }}
      100% {{ transform: translate(14px, -28px) scale(1.3); opacity: 0; }}
    }}
    .nezuko-fx-hearts {{
      position: absolute; top: 10px; left: 10px; right: 10px; font-size: 18px;
      display: none; animation: heartSparkle 1.2s infinite ease-out;
    }}
    .action-headpat ~ .nezuko-fx-container .nezuko-fx-hearts {{ display: block; }}
    @keyframes heartSparkle {{
      0% {{ transform: scale(0.8) translateY(0); opacity: 0; }}
      50% {{ opacity: 1; }}
      100% {{ transform: scale(1.2) translateY(-20px); opacity: 0; }}
    }}

    /* 鬼灭大正和风主操作看板 */
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
    .nezuko-asanoha-pattern {{
      position: absolute; inset: 0; opacity: 0.08;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='103.92' viewBox='0 0 60 103.92'%3E%3Cpath d='M30 0 L60 17.32 L60 51.96 L30 69.28 L0 51.96 L0 17.32 Z' fill='none' stroke='%23f48fb1' stroke-width='1.5'/%3E%3Cpath d='M30 0 L30 69.28 M60 17.32 L0 51.96 M60 51.96 L0 17.32' stroke='%23f48fb1' stroke-width='1.5'/%3E%3Cpath d='M30 34.64 L30 0 M30 34.64 L60 17.32 M30 34.64 L60 51.96 M30 34.64 L30 69.28 M30 34.64 L0 51.96 M30 34.64 L0 17.32' stroke='%23f48fb1' stroke-width='2'/%3E%3C/svg%3E");
      pointer-events: none;
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
    .nezuko-header-badge {{
      font-size: 10px; background: var(--ds-dark-pink); color: #fff; padding: 1px 6px; border-radius: 4px;
    }}
    .nezuko-close-btn {{
      background: transparent; border: none; color: #b0bec5; font-size: 16px; cursor: pointer; padding: 2px 6px;
    }}
    .nezuko-close-btn:hover {{ color: #fff; background: rgba(255,255,255,0.1); }}
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
    @keyframes recordSpin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
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
    .nezuko-ichimatsu-strip {{
      height: 6px; width: 100%;
      background: repeating-linear-gradient(45deg, var(--ds-tanjiro-green) 0, var(--ds-tanjiro-green) 6px, var(--ds-ichimatsu-black) 6px, var(--ds-ichimatsu-black) 12px);
    }}
  `;
  document.head.appendChild(styleEl);

  // ==========================================
  // 五、DOM 结构组装 (2D 骨骼关节分层)
  // ==========================================
  const root = document.createElement('div');
  root.id = 'nezuko-pet-root';
  root.innerHTML = `
    <div class="nezuko-pet-stage" id="nezuko-pet-stage">
      <!-- 地面接触软阴影 -->
      <div class="nezuko-pet-ground-shadow" id="nezuko-ground-shadow"></div>

      <!-- 雾云杉木箱道具 -->
      <div class="nezuko-box-prop"></div>

      <!-- 粒子特效容器 -->
      <div class="nezuko-fx-container">
        <div class="nezuko-fx-cross">💢</div>
        <div class="nezuko-fx-zzz">Zzz...</div>
        <div class="nezuko-fx-hearts">🌸 ✨ 💖</div>
      </div>

      <!-- 头顶快捷胶囊动作条 (带透明安全桥接垫片) -->
      <div class="nezuko-action-capsule" id="nezuko-action-capsule">
        <button class="nezuko-capsule-btn" data-action="headpat" data-expr="crescent" data-tip="摸头杀蹭蹭" title="摸头杀蹭蹭">🐱</button>
        <button class="nezuko-capsule-btn" data-action="run" data-expr="dot" data-tip="风火轮狂奔" title="豆豆眼风火轮疾走">🏃</button>
        <button class="nezuko-capsule-btn" data-action="box" data-expr="normal" data-tip="钻木箱捉猫" title="钻雾云杉木箱捉迷藏">📦</button>
        <button class="nezuko-capsule-btn" data-action="stomp" data-expr="angry" data-tip="气鼓跺小脚" title="气鼓鼓跺小脚">😤</button>
        <button class="nezuko-capsule-btn" data-action="burst" data-expr="demon" data-tip="血鬼术·爆血" title="血鬼术·爆血觉醒">🔥</button>
        <button class="nezuko-capsule-btn" data-action="sleep" data-expr="crescent" data-tip="揉眼伸懒腰" title="揉眼睛伸懒腰打瞌睡">🥱</button>
        <button class="nezuko-capsule-btn btn-music-spin" id="btn-quick-music" data-tip="播放/切歌" title="播放/切换鬼灭BGM">🎵</button>
        <button class="nezuko-capsule-btn" id="btn-quick-board" data-tip="鬼灭看板" title="打开鬼灭配额看板">🎋</button>
      </div>

      <!-- 2D 骨骼关节分层人体机架 (手脚身体真正独立运动) -->
      <div class="nezuko-pet-rig" id="nezuko-pet-character" title="单击锁定动作条 · 双击打开看板 · 按住拖拽 · 滚轮切歌">
        
        <!-- 骨骼 5 & 6：左右小短腿 (置于躯干后层) -->
        <div class="bone-layer" id="bone-leg-l"></div>
        <div class="bone-layer" id="bone-leg-r"></div>

        <!-- 骨骼 2：和服躯干本体 -->
        <div class="bone-layer" id="bone-torso"></div>

        <!-- 骨骼 3 & 4：左右手臂 (以肩膀为轴自由摆动) -->
        <div class="bone-layer" id="bone-arm-l"></div>
        <div class="bone-layer" id="bone-arm-r"></div>

        <!-- 骨骼 1：头部与长发 (以颈部为轴点头歪头) -->
        <div class="bone-layer" id="bone-head">
          <!-- 动态表情叠加层 -->
          <div class="nezuko-face-rig" id="nezuko-face-rig">
            <div class="nezuko-eyes-default"></div>
            <div class="nezuko-eyes-dot"></div>
            <div class="nezuko-eyes-crescent"></div>
            <div class="nezuko-cheeks-angry"></div>
            <div class="nezuko-demon-horn"></div>
            <div class="nezuko-demon-veins"></div>
          </div>
        </div>

        <div class="nezuko-float-badge" id="nezuko-open-btn">🎋 鬼灭看板</div>
      </div>
    </div>

    <!-- 大正和风主操作看板 (雾云杉木箱质感) -->
    <div id="nezuko-main-card">
      <div class="nezuko-asanoha-pattern"></div>
      <div class="nezuko-card-header">
        <div class="nezuko-header-title">
          <span>🌸 竈門禰豆子</span>
          <span class="nezuko-header-badge">大正和风 · 鬼灭看板</span>
        </div>
        <button class="nezuko-close-btn" id="nezuko-close-card" title="关闭面板">✕</button>
      </div>

      <div class="nezuko-card-body">
        <!-- 模块 0：软件界面《鬼灭之刃》全套主题开关 -->
        <div class="nezuko-section-box" style="background: rgba(194, 24, 91, 0.15); border-color: var(--ds-pink);">
          <div class="nezuko-section-title">
            <span style="color:#ffd54f;">🌸 软件界面《鬼灭之刃》全局主题</span>
            <span id="theme-status-tag" style="font-size:10px; color:#81c784;">● 已激活</span>
          </div>
          <div style="font-size:11px; color:#cfd8dc; margin-bottom:8px; line-height:1.5;">
            活动栏黑绿市松纹、侧边栏麻叶和纸木纹、状态栏大正锦缎、烫金标题与粉红流光标签页已全量生效。
          </div>
          <button class="nezuko-ctrl-btn" id="btn-toggle-ide-theme" style="width:100%; padding:5px; background:linear-gradient(135deg, var(--ds-dark-pink), var(--ds-crimson)); font-weight:bold;">
            🎋 切换软件鬼灭主题 (开/关)
          </button>
        </div>

        <!-- 模块 1：Gemini 模型专属配额 (对应截图) -->
        <div class="nezuko-section-box">
          <div class="nezuko-section-title">
            <span>Gemini 模型</span>
            <span style="font-size:10px; color:#81c784;">● 状态活跃</span>
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

        <!-- 模块 2：Claude 与 GPT 模型专属配额 (对应截图) -->
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

          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
            <button class="nezuko-ctrl-btn" id="btn-sync-quota" style="font-size:10px; padding:3px 8px;">🔄 自动同步原生配额</button>
            <button class="nezuko-ctrl-btn" id="btn-toggle-adjust" style="font-size:10px; padding:3px 8px;">⚙️ 手动校准微调</button>
          </div>

          <div id="nezuko-adjust-box" style="display:none; margin-top:8px; padding-top:8px; border-top:1px dashed rgba(255,255,255,0.15);">
            <div style="font-size:11px; color:#ffd54f; margin-bottom:4px;">Gemini 每周配额: <span id="val-adj-gw">91%</span></div>
            <input type="range" id="rng-adj-gw" min="0" max="100" value="91" style="width:100%; accent-color:#f48fb1;">
            
            <div style="font-size:11px; color:#ffd54f; margin-top:4px; margin-bottom:4px;">Gemini 5小时配额: <span id="val-adj-g5">72%</span></div>
            <input type="range" id="rng-adj-g5" min="0" max="100" value="72" style="width:100%; accent-color:#f48fb1;">
          </div>
        </div>

        <!-- 模块 3：鬼灭之刃随身音乐盒 (BGM 播放器) -->
        <div class="nezuko-music-player">
          <div class="nezuko-music-info">
            <div class="nezuko-record-disc" id="nezuko-disc"></div>
            <div class="nezuko-song-texts">
              <span class="nezuko-song-title" id="music-title">竈門炭治郎のうた</span>
              <span class="nezuko-song-sub" id="music-sub">治愈抒情 · 椎名豪 / 中川奈美</span>
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

      <div class="nezuko-ichimatsu-strip"></div>
    </div>
  `;
  document.body.appendChild(root);

  // ==========================================
  // 六、交互驱动与防消失逻辑绑定
  // ==========================================
  const charAvatar = document.getElementById('nezuko-pet-character');
  const stageEl = document.getElementById('nezuko-pet-stage');
  const capsuleBar = document.getElementById('nezuko-action-capsule');
  const mainCard = document.getElementById('nezuko-main-card');
  const openBtn = document.getElementById('nezuko-open-btn');
  const closeBtn = document.getElementById('nezuko-close-card');
  const faceRig = document.getElementById('nezuko-face-rig');
  const disc = document.getElementById('nezuko-disc');
  const quickMusicBtn = document.getElementById('btn-quick-music');
  const quickBoardBtn = document.getElementById('btn-quick-board');

  // 主题开关按钮
  const btnToggleTheme = document.getElementById('btn-toggle-ide-theme');
  const themeStatusTag = document.getElementById('theme-status-tag');
  btnToggleTheme.addEventListener('click', () => {{
    const current = isIdeThemeEnabled();
    const next = !current;
    setIdeTheme(next);
    themeStatusTag.textContent = next ? '● 已激活' : '○ 已停用';
    themeStatusTag.style.color = next ? '#81c784' : '#e0e0e0';
  }});

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

  charAvatar.addEventListener('click', (e) => {{
    if (isDragging) return;
    isCapsulePinned = !isCapsulePinned;
    if (isCapsulePinned) showCapsule();
    else scheduleHideCapsule();
  }});

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
  charAvatar.addEventListener('dblclick', () => {{
    mainCard.style.display = mainCard.style.display === 'flex' ? 'none' : 'flex';
  }});

  // 骨骼动作与表情协同驱动
  let actionTimer = null;
  function triggerAction(actionName, exprName, duration = 6500) {{
    charAvatar.classList.remove('action-run', 'action-tilt', 'action-stomp', 'action-burst', 'action-box', 'action-sleep', 'action-headpat');
    faceRig.classList.remove('expr-dot', 'expr-crescent', 'expr-angry', 'expr-demon');

    if (actionName) charAvatar.classList.add('action-' + actionName);
    if (exprName && exprName !== 'normal') faceRig.classList.add('expr-' + exprName);

    if (actionTimer) clearTimeout(actionTimer);
    actionTimer = setTimeout(() => {{
      charAvatar.classList.remove('action-run', 'action-tilt', 'action-stomp', 'action-burst', 'action-box', 'action-sleep', 'action-headpat');
      faceRig.classList.remove('expr-dot', 'expr-crescent', 'expr-angry', 'expr-demon');
    }}, duration);
  }}

  document.querySelectorAll('.nezuko-capsule-btn[data-action]').forEach(btn => {{
    btn.addEventListener('click', (e) => {{
      e.stopPropagation();
      const action = btn.getAttribute('data-action');
      const expr = btn.getAttribute('data-expr');
      triggerAction(action, expr);
    }});
  }});

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

  charAvatar.addEventListener('wheel', (e) => {{
    e.preventDefault();
    if (e.deltaY > 0) musicEngine.next();
    else musicEngine.prev();
  }});

  document.getElementById('btn-sync-quota').addEventListener('click', () => {{
    sniffNativeQuotaFromDOM();
    updateQuotaDisplay();
  }});

  const adjBox = document.getElementById('nezuko-adjust-box');
  document.getElementById('btn-toggle-adjust').addEventListener('click', () => {{
    adjBox.style.display = adjBox.style.display === 'block' ? 'none' : 'block';
  }});

  const rngGW = document.getElementById('rng-adj-gw');
  const rngG5 = document.getElementById('rng-adj-g5');
  rngGW.addEventListener('input', (e) => {{
    currentQuota.geminiWeeklyPct = parseInt(e.target.value, 10);
    document.getElementById('val-adj-gw').textContent = e.target.value + '%';
    saveUserQuota(currentQuota);
    updateQuotaDisplay();
  }});
  rngG5.addEventListener('input', (e) => {{
    currentQuota.gemini5hPct = parseInt(e.target.value, 10);
    document.getElementById('val-adj-g5').textContent = e.target.value + '%';
    saveUserQuota(currentQuota);
    updateQuotaDisplay();
  }});

  // 物理拖拽与悬空摇腿
  let isDragging = false;
  let dragStartX = 0, dragStartY = 0;
  let rootStartRight = 32, rootStartBottom = 24;

  charAvatar.addEventListener('mousedown', (e) => {{
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
        charAvatar.classList.add('nezuko-picked-up');
        triggerAction(null, 'dot', 999999);
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
        charAvatar.classList.remove('nezuko-picked-up');
        faceRig.classList.remove('expr-dot');
        setTimeout(() => {{ isDragging = false; }}, 50);
      }}
    }};

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }});

  setInterval(() => {{
    if (!charAvatar.className.includes('action-') && !isDragging) {{
      faceRig.classList.add('expr-crescent');
      setTimeout(() => faceRig.classList.remove('expr-crescent'), 350);
    }}
  }}, 4500);

}})();
"""

target_js = REPO_ROOT / "resources" / "nezuko-pet.js"
target_js.write_text(js_code, encoding="utf-8")
print(f"✅ 成功生成 2D 骨骼分肢动力学与软件鬼灭主题引擎: {target_js} ({len(js_code.encode('utf-8'))} 字节)")
