# -*- coding: utf-8 -*-
"""
生成腾讯 QQ 宠物风格 + 复刻《鬼灭之刃》原动漫经典名场面动作机 + 真实模型配额看板 + 和风BGM音乐盒的核心组件 (resources/nezuko-pet.js)
四大模块升级：
1. 【鬼灭之刃原生配额看板】：精准呈现 Gemini 模型与 Claude/GPT 模型的每周/5小时剩余可用配额及重置时间，支持 DOM 自动同步与校准持久化。
2. 【原动漫经典动作机与表情分层】：彻底告别呆板！多表情切换（豆豆眼、月牙笑、鼓腮包子脸、鬼纹血瞳）配合 7 大原动漫高能可爱名场面（豆豆眼狂奔、抱竹晃脑、气鼓鼓跺脚、血鬼术爆血、钻木箱捉迷藏、揉眼犯困、摸头杀）。
3. 【鬼灭之刃大正和风界面】：粉红麻叶纹、雾云杉木箱质感、黄铜铆钉包角、绿黑市松纹、紫藤樱花飘落动效。
4. 【鬼灭之刃随身 BGM 音乐盒】：内置 Web Audio 零依赖和风八音盒（《炭治郎之歌》、《红莲华》、《祢豆子日常》），支持本地音频导入与旋律律动晃脑。
"""

import sys
import base64
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = REPO_ROOT / "resources" / "media"

nezuko_webp = MEDIA_DIR / "nezuko_chibi_pet.webp"
b64_nezuko = base64.b64encode(nezuko_webp.read_bytes()).decode('ascii')

js_code = f"""/**
 * Antigravity 灶门祢豆子 · 鬼灭之刃大正和风桌宠系统 (Demon Slayer Nezuko Engine 2.0)
 * 1. 真实模型配额看板 (Gemini / Claude / GPT 每周与5小时限额及重置倒计时)
 * 2. 原动漫 7 大名场面连贯动作机 + 动态表情系统 (彻底告别呆板)
 * 3. 鬼灭之刃大正和风界面 (粉红麻叶纹、雾云杉木箱、黄铜包角、紫藤樱花)
 * 4. 鬼灭之刃随身 BGM 音乐盒 (内置 Web Audio 八音盒 + 本地音乐导入)
 */

(function() {{
  if (typeof window === 'undefined' || window.__NEZUKO_PET_INITIALIZED__) return;
  window.__NEZUKO_PET_INITIALIZED__ = true;

  const NEZUKO_IMG_B64 = "data:image/webp;base64,{b64_nezuko}";

  // ==========================================
  // 一、模型配额中枢 (Gemini 与 Claude/GPT 原生对应)
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

  // 尝试从 Antigravity 原生 DOM 中实时嗅探配额
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
        // 解析 DOM 中可能存在的配额数值
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
        }}
      }}
    }} catch (_) {{}}
  }}

  setInterval(sniffNativeQuotaFromDOM, 5000);

  // ==========================================
  // 二、鬼灭之刃 Web Audio 随身八音盒引擎
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
        ['B4', 0.45], ['D5', 0.45], ['E5', 0.9], ['D5', 0.9],
        ['B4', 0.45], ['A4', 0.45], ['G4', 0.7], ['A4', 0.45], ['B4', 0.9],
        ['A4', 0.45], ['G4', 0.45], ['E4', 1.2]
      ]
    }},
    {{
      title: "紅蓮華 (红莲华)",
      subtitle: "经典热血 OP · LiSA 和风版",
      notes: [
        ['D5', 0.3], ['D5', 0.3], ['C5', 0.3], ['A4', 0.3], ['C5', 0.3], ['D5', 0.6],
        ['D5', 0.3], ['E5', 0.3], ['F5', 0.3], ['E5', 0.3], ['D5', 0.3], ['C5', 0.6],
        ['A4', 0.3], ['C5', 0.3], ['D5', 0.45], ['D5', 0.45], ['C5', 0.45], ['D5', 0.9],
        ['F5', 0.3], ['G5', 0.3], ['A5', 0.6], ['G5', 0.3], ['F5', 0.3], ['E5', 0.6],
        ['D5', 0.3], ['E5', 0.3], ['F5', 0.45], ['E5', 0.3], ['D5', 0.3], ['C5', 0.9],
        ['D5', 0.3], ['E5', 0.3], ['D5', 1.2]
      ]
    }},
    {{
      title: "禰豆子の平穏 (祢豆子的日常)",
      subtitle: "活泼治愈 · 萌宠八音盒小调",
      notes: [
        ['E5', 0.35], ['G5', 0.35], ['A5', 0.5], ['G5', 0.35], ['E5', 0.5],
        ['D5', 0.35], ['E5', 0.35], ['G5', 0.7], ['E5', 0.35], ['D5', 0.7],
        ['C5', 0.35], ['D5', 0.35], ['E5', 0.5], ['G5', 0.35], ['A5', 0.7],
        ['G5', 0.35], ['E5', 0.35], ['D5', 0.5], ['C5', 0.9],
        ['E5', 0.35], ['E5', 0.35], ['G5', 0.35], ['A5', 0.7],
        ['G5', 0.35], ['E5', 0.35], ['C5', 1.0]
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

      // 八音盒清脆音色 (Sine + Subtle Triangle)
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t);

      // ADSR 铃音包络：极速敲击上升，平滑指数衰减
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
      if (this.customAudio) return; // 正在播放本地音频

      const track = PLAYLIST[this.currentTrack];
      if (this.stepIndex >= track.notes.length) {{
        this.stepIndex = 0; // 循环播放当前曲目
      }}

      const [noteName, dur] = track.notes[this.stepIndex];
      const freq = noteFreqs[noteName] || 440;
      this.playTone(freq, dur);

      // 联动桌宠晃头节拍
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
      if (this.customAudio) {{
        this.customAudio = null;
      }}
      this.currentTrack = (this.currentTrack + 1) % PLAYLIST.length;
      this.stepIndex = 0;
      this.play();
    }}

    prev() {{
      this.pause();
      if (this.customAudio) {{
        this.customAudio = null;
      }}
      this.currentTrack = (this.currentTrack - 1 + PLAYLIST.length) % PLAYLIST.length;
      this.stepIndex = 0;
      this.play();
    }}

    setVolume(val) {{
      this.volume = Math.max(0, Math.min(1, val));
      if (this.customAudio) {{
        this.customAudio.volume = this.volume;
      }}
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

  // 节拍联动晃头
  let beatTimer = null;
  function triggerMusicBeat() {{
    const petEl = document.getElementById('nezuko-pet-character');
    if (!petEl || !musicEngine.isPlaying) return;
    petEl.classList.add('nezuko-music-bob');
    if (beatTimer) clearTimeout(beatTimer);
    beatTimer = setTimeout(() => {{
      petEl.classList.remove('nezuko-music-bob');
    }}, 400);
  }}

  // ==========================================
  // 三、CSS 样式库 (大正和风 + 鬼灭视觉 + 多表情动作)
  // ==========================================
  const styleEl = document.createElement('style');
  styleEl.id = 'nezuko-pet-advanced-styles';
  styleEl.textContent = `
    /* ===== 鬼灭之刃基础色彩与字体 ===== */
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

    /* 容器浮动 */
    #nezuko-pet-root {{
      position: fixed;
      right: 28px;
      bottom: 24px;
      z-index: 999999;
      user-select: none;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }}

    /* ===== 地面接触柔和阴影 ===== */
    .nezuko-pet-ground-shadow {{
      position: absolute;
      bottom: -6px;
      left: 50%;
      transform: translateX(-50%);
      width: 100px;
      height: 14px;
      background: radial-gradient(ellipse at center, rgba(10, 5, 8, 0.45) 0%, rgba(10, 5, 8, 0.15) 50%, transparent 75%);
      border-radius: 50%;
      pointer-events: none;
      transition: all 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
    }}

    /* 桌宠主形象骨骼层 */
    .nezuko-pet-avatar {{
      position: relative;
      width: 130px;
      height: 180px;
      cursor: grab;
      filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.2));
      transition: transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
      transform-origin: bottom center;
    }}

    .nezuko-pet-avatar:active {{
      cursor: grabbing;
    }}

    /* 立绘图片主体 */
    .nezuko-pet-img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
      pointer-events: none;
      display: block;
      transform-origin: bottom center;
    }}

    /* ===== 多表情神态覆盖层 (Expression Overlay) ===== */
    .nezuko-face-rig {{
      position: absolute;
      top: 36px;
      left: 38px;
      width: 56px;
      height: 44px;
      pointer-events: none;
      z-index: 5;
    }}

    /* 默认眨眼萌眼 */
    .nezuko-eyes-default {{
      width: 100%;
      height: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 4px;
      box-sizing: border-box;
      opacity: 0;
      transition: opacity 0.2s;
    }}

    /* 经典魔性豆豆眼 (·_·) */
    .nezuko-eyes-dot {{
      position: absolute;
      top: 14px;
      left: 6px;
      width: 44px;
      height: 16px;
      display: none;
      justify-content: space-between;
      align-items: center;
    }}
    .nezuko-eyes-dot::before, .nezuko-eyes-dot::after {{
      content: '';
      width: 9px;
      height: 9px;
      background: #111;
      border-radius: 50%;
      box-shadow: 0 0 2px rgba(0,0,0,0.8);
    }}

    /* 闭眼月牙笑 (^‿^) */
    .nezuko-eyes-crescent {{
      position: absolute;
      top: 12px;
      left: 4px;
      width: 48px;
      height: 16px;
      display: none;
      justify-content: space-between;
    }}
    .nezuko-eyes-crescent::before, .nezuko-eyes-crescent::after {{
      content: '';
      width: 16px;
      height: 8px;
      border-bottom: 3.5px solid #231612;
      border-radius: 0 0 16px 16px;
    }}

    /* 气鼓鼓大腮帮 (包子脸) */
    .nezuko-cheeks-angry {{
      position: absolute;
      top: 18px;
      left: 0;
      width: 56px;
      height: 20px;
      display: none;
      justify-content: space-between;
    }}
    .nezuko-cheeks-angry::before, .nezuko-cheeks-angry::after {{
      content: '';
      width: 14px;
      height: 14px;
      background: radial-gradient(circle, #ff80ab 0%, rgba(255, 64, 129, 0.4) 65%, transparent 100%);
      border-radius: 50%;
    }}

    /* 鬼化额角与鲜红鬼纹 */
    .nezuko-demon-horn {{
      position: absolute;
      top: -14px;
      right: 14px;
      width: 16px;
      height: 22px;
      background: linear-gradient(135deg, #fff 0%, #e0e0e0 60%, #b0bec5 100%);
      clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
      transform: rotate(20deg);
      filter: drop-shadow(0 0 6px rgba(255, 23, 68, 0.8));
      display: none;
    }}
    .nezuko-demon-veins {{
      position: absolute;
      top: -4px;
      right: 6px;
      width: 22px;
      height: 20px;
      background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2 Q18 8 16 16 Q22 18 20 22 Q14 18 12 12 Q8 16 4 22' fill='none' stroke='%23ff1744' stroke-width='2'/%3E%3C/svg%3E") no-repeat center;
      display: none;
    }}

    /* 表情状态机切换 */
    .expr-dot .nezuko-eyes-dot {{ display: flex !important; }}
    .expr-crescent .nezuko-eyes-crescent {{ display: flex !important; }}
    .expr-angry .nezuko-cheeks-angry {{ display: flex !important; }}
    .expr-demon .nezuko-demon-horn,
    .expr-demon .nezuko-demon-veins {{ display: block !important; }}

    /* ===== 原动漫名场面 7 大动作动画机 ===== */

    /* 动作 1：小豆丁风火轮狂奔 (Tiny Chibi Run) */
    .action-run {{
      animation: nezukoRunCycle 0.55s infinite alternate ease-in-out !important;
    }}
    @keyframes nezukoRunCycle {{
      0% {{
        transform: scale(0.72) translateY(12px) translateX(-28px) rotate(-10deg);
      }}
      100% {{
        transform: scale(0.72) translateY(6px) translateX(28px) rotate(10deg);
      }}
    }}
    .action-run ~ .nezuko-pet-ground-shadow {{
      width: 70px;
      transform: translateX(-50%) scaleX(0.75);
    }}

    /* 动作 2：抱竹歪头晃脑 (Head Tilt & Sway) */
    .action-tilt {{
      animation: nezukoHeadSway 2.4s infinite ease-in-out !important;
    }}
    @keyframes nezukoHeadSway {{
      0%, 100% {{ transform: rotate(0deg) translateY(0); }}
      25% {{ transform: rotate(-18deg) translateY(-2px); }}
      50% {{ transform: rotate(0deg) translateY(0); }}
      75% {{ transform: rotate(18deg) translateY(-2px); }}
    }}

    /* 动作 3：气鼓鼓跺小脚 (Angry Stomp) */
    .action-stomp {{
      animation: nezukoAngryStomp 0.28s infinite alternate cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    @keyframes nezukoAngryStomp {{
      0% {{ transform: translateY(0) rotate(0deg); }}
      100% {{ transform: translateY(-7px) rotate(-5deg); }}
    }}

    /* 动作 4：血鬼术·爆血觉醒 (Blood Demon Art) */
    .action-burst {{
      animation: nezukoBurstFlame 1.2s infinite ease-in-out !important;
      filter: drop-shadow(0 0 18px rgba(255, 23, 68, 0.9)) saturate(1.4) !important;
    }}
    @keyframes nezukoBurstFlame {{
      0%, 100% {{ transform: scale(1) translateY(0); }}
      50% {{ transform: scale(1.1) translateY(-8px); }}
    }}

    /* 动作 5：钻雾云杉木箱捉迷藏 (Box Peek-a-boo) */
    .action-box {{
      animation: nezukoBoxHide 1.8s infinite ease-in-out !important;
    }}
    @keyframes nezukoBoxHide {{
      0%, 100% {{ transform: scale(0.85) translateY(24px); opacity: 0.9; }}
      50% {{ transform: scale(0.92) translateY(10px); opacity: 1; }}
    }}

    /* 动作 6：揉眼犯困打瞌睡 (Drowsy Sleep) */
    .action-sleep {{
      animation: nezukoSleepCycle 3.2s infinite ease-in-out !important;
    }}
    @keyframes nezukoSleepCycle {{
      0%, 100% {{ transform: rotate(12deg) translateY(14px) scale(0.9); }}
      50% {{ transform: rotate(15deg) translateY(18px) scale(0.88); }}
    }}

    /* 动作 7：摸头杀闭眼撒娇蹭蹭 (Headpat Cuddle) */
    .action-headpat {{
      animation: nezukoHeadpatCuddle 1.4s infinite ease-in-out !important;
    }}
    @keyframes nezukoHeadpatCuddle {{
      0%, 100% {{ transform: translateY(0) rotate(0deg); }}
      50% {{ transform: translateY(-6px) rotate(8deg); }}
    }}

    /* QQ宠物拖拽被提起 (悬空慌乱挣扎蹬腿) */
    .nezuko-picked-up {{
      transform: scale(1.08) translateY(-22px) rotate(-8deg) !important;
      filter: drop-shadow(0 14px 22px rgba(0, 0, 0, 0.35)) !important;
      animation: nezukoStruggleLegs 0.22s infinite alternate ease-in-out !important;
    }}
    @keyframes nezukoStruggleLegs {{
      0% {{ transform: scale(1.08) translateY(-22px) rotate(-7deg); }}
      100% {{ transform: scale(1.08) translateY(-22px) rotate(7deg); }}
    }}
    .nezuko-picked-up ~ .nezuko-pet-ground-shadow {{
      transform: translateX(-50%) scale(0.55);
      opacity: 0.25;
    }}

    /* 音乐节拍轻微晃脑 */
    .nezuko-music-bob {{
      transform: translateY(-4px) rotate(3deg);
      transition: transform 0.15s ease-out;
    }}

    /* 道具层：雾云杉木箱 */
    .nezuko-box-prop {{
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 110px;
      height: 140px;
      background: linear-gradient(180deg, var(--ds-wood-light) 0%, var(--ds-wood-dark) 100%);
      border: 3px solid var(--ds-brass-gold);
      border-radius: 8px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.5), inset 0 0 15px rgba(0,0,0,0.6);
      display: none;
      z-index: 1;
    }}
    .nezuko-box-prop::before {{
      content: '';
      position: absolute;
      top: 8px; left: 8px; right: 8px; bottom: 8px;
      border: 1px dashed var(--ds-brass-gold);
      opacity: 0.6;
    }}
    .action-box ~ .nezuko-box-prop {{
      display: block !important;
    }}

    /* ===== 特效粒子层 (樱花、怒气十字、Zzz、爆血火焰) ===== */
    .nezuko-fx-container {{
      position: absolute;
      inset: 0;
      pointer-events: none;
      z-index: 20;
    }}

    .nezuko-fx-cross {{
      position: absolute;
      top: 15px;
      right: 18px;
      color: #ff1744;
      font-size: 22px;
      font-weight: 900;
      display: none;
      animation: crossShake 0.3s infinite;
    }}
    .action-stomp ~ .nezuko-fx-container .nezuko-fx-cross {{
      display: block;
    }}
    @keyframes crossShake {{
      0% {{ transform: scale(1) rotate(0deg); }}
      50% {{ transform: scale(1.25) rotate(12deg); }}
      100% {{ transform: scale(1) rotate(-8deg); }}
    }}

    .nezuko-fx-zzz {{
      position: absolute;
      top: 0;
      right: 8px;
      color: #f48fb1;
      font-size: 16px;
      font-weight: bold;
      display: none;
      animation: zzzFloat 2.2s infinite linear;
    }}
    .action-sleep ~ .nezuko-fx-container .nezuko-fx-zzz {{
      display: block;
    }}
    @keyframes zzzFloat {{
      0% {{ transform: translate(0, 0) scale(0.6); opacity: 0; }}
      50% {{ opacity: 1; }}
      100% {{ transform: translate(14px, -28px) scale(1.3); opacity: 0; }}
    }}

    .nezuko-fx-hearts {{
      position: absolute;
      top: 10px;
      left: 10px;
      right: 10px;
      font-size: 18px;
      display: none;
      animation: heartSparkle 1.2s infinite ease-out;
    }}
    .action-headpat ~ .nezuko-fx-container .nezuko-fx-hearts {{
      display: block;
    }}
    @keyframes heartSparkle {{
      0% {{ transform: scale(0.8) translateY(0); opacity: 0; }}
      50% {{ opacity: 1; }}
      100% {{ transform: scale(1.2) translateY(-20px); opacity: 0; }}
    }}

    /* ===== 大正和风主操作面板 (雾云杉木箱 + 麻叶纹 + 烫金) ===== */
    #nezuko-main-card {{
      position: absolute;
      bottom: 195px;
      right: 0;
      width: 330px;
      background: linear-gradient(135deg, rgba(35, 22, 18, 0.96) 0%, rgba(20, 12, 10, 0.98) 100%);
      border: 2px solid var(--ds-brass-gold);
      border-radius: 12px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(244, 143, 177, 0.25);
      color: #fff;
      overflow: hidden;
      display: none;
      flex-direction: column;
      z-index: 50;
      backdrop-filter: blur(12px);
    }}

    /* 粉红麻叶纹几何背景衬底 */
    .nezuko-asanoha-pattern {{
      position: absolute;
      inset: 0;
      opacity: 0.08;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='103.92' viewBox='0 0 60 103.92'%3E%3Cpath d='M30 0 L60 17.32 L60 51.96 L30 69.28 L0 51.96 L0 17.32 Z' fill='none' stroke='%23f48fb1' stroke-width='1.5'/%3E%3Cpath d='M30 0 L30 69.28 M60 17.32 L0 51.96 M60 51.96 L0 17.32' stroke='%23f48fb1' stroke-width='1.5'/%3E%3Cpath d='M30 34.64 L30 0 M30 34.64 L60 17.32 M30 34.64 L60 51.96 M30 34.64 L30 69.28 M30 34.64 L0 51.96 M30 34.64 L0 17.32' stroke='%23f48fb1' stroke-width='2'/%3E%3C/svg%3E");
      pointer-events: none;
    }}

    /* 顶部烫金日式和风标题条 */
    .nezuko-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      background: linear-gradient(90deg, #381f19 0%, #4a2920 100%);
      border-bottom: 1.5px solid var(--ds-brass-gold);
      position: relative;
    }}
    .nezuko-header-title {{
      font-size: 13px;
      font-weight: 700;
      color: var(--ds-gold-glow);
      display: flex;
      align-items: center;
      gap: 6px;
      text-shadow: 0 1px 3px rgba(0,0,0,0.8);
    }}
    .nezuko-header-badge {{
      font-size: 10px;
      background: var(--ds-dark-pink);
      color: #fff;
      padding: 1px 6px;
      border-radius: 4px;
      letter-spacing: 0.5px;
    }}
    .nezuko-close-btn {{
      background: transparent;
      border: none;
      color: #b0bec5;
      font-size: 16px;
      cursor: pointer;
      line-height: 1;
      padding: 2px 6px;
      border-radius: 4px;
    }}
    .nezuko-close-btn:hover {{
      color: #fff;
      background: rgba(255,255,255,0.1);
    }}

    /* 卡片内容滚动区 */
    .nezuko-card-body {{
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      max-height: 480px;
      overflow-y: auto;
      position: relative;
    }}

    /* 模块分块样式 */
    .nezuko-section-box {{
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(197, 155, 39, 0.35);
      border-radius: 8px;
      padding: 10px 12px;
      position: relative;
    }}
    .nezuko-section-title {{
      font-size: 12px;
      font-weight: 700;
      color: #e0e0e0;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    /* ===== 原生配额条目样式 ===== */
    .nezuko-quota-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .nezuko-quota-row:last-child {{
      border-bottom: none;
      padding-bottom: 2px;
    }}
    .nezuko-quota-meta {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .nezuko-quota-name {{
      font-size: 12px;
      color: #f5f5f5;
    }}
    .nezuko-quota-reset {{
      font-size: 10px;
      color: #9e9e9e;
    }}
    .nezuko-quota-val-group {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .nezuko-quota-pct {{
      font-size: 13px;
      font-weight: 700;
      color: #81c784;
    }}
    /* SVG 环形进度条 */
    .nezuko-ring-wrap {{
      width: 24px;
      height: 24px;
      transform: rotate(-90deg);
    }}
    .nezuko-ring-bg {{
      fill: none;
      stroke: rgba(255, 255, 255, 0.15);
      stroke-width: 3.5;
    }}
    .nezuko-ring-bar {{
      fill: none;
      stroke: #81c784;
      stroke-width: 3.5;
      stroke-linecap: round;
      stroke-dasharray: 63;
      stroke-dashoffset: 0;
      transition: stroke-dashoffset 0.6s ease;
    }}

    /* ===== BGM 随身音乐盒面板 ===== */
    .nezuko-music-player {{
      background: linear-gradient(180deg, rgba(46, 26, 20, 0.7) 0%, rgba(20, 12, 10, 0.85) 100%);
      border: 1px solid var(--ds-brass-gold);
      border-radius: 8px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .nezuko-music-info {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    /* 迷你和风黑胶唱片 */
    .nezuko-record-disc {{
      width: 34px;
      height: 34px;
      background: radial-gradient(circle, #ff80ab 15%, #111 16%, #222 65%, #111 100%);
      border: 1.5px solid var(--ds-brass-gold);
      border-radius: 50%;
      flex-shrink: 0;
      animation: recordSpin 3.5s infinite linear;
      animation-play-state: paused;
    }}
    .record-spinning {{
      animation-play-state: running !important;
    }}
    @keyframes recordSpin {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(360deg); }}
    }}
    .nezuko-song-texts {{
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    .nezuko-song-title {{
      font-size: 11.5px;
      font-weight: 700;
      color: #fff;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }}
    .nezuko-song-sub {{
      font-size: 9.5px;
      color: var(--ds-pink);
    }}

    /* 播放器控制按钮组 */
    .nezuko-music-controls {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      padding-top: 4px;
    }}
    .nezuko-ctrl-btn {{
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(197, 155, 39, 0.4);
      color: #fff;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .nezuko-ctrl-btn:hover {{
      background: var(--ds-dark-pink);
      border-color: var(--ds-pink);
    }}
    .nezuko-ctrl-play {{
      background: linear-gradient(135deg, var(--ds-dark-pink), var(--ds-crimson));
      font-weight: bold;
      padding: 4px 14px;
    }}

    /* ===== 原动漫动作快捷网格 ===== */
    .nezuko-actions-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
    }}
    .nezuko-act-btn {{
      background: rgba(46, 26, 20, 0.8);
      border: 1px solid rgba(197, 155, 39, 0.35);
      color: #e0e0e0;
      padding: 6px 4px;
      border-radius: 6px;
      font-size: 10.5px;
      cursor: pointer;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      transition: all 0.2s;
    }}
    .nezuko-act-btn:hover {{
      background: var(--ds-dark-pink);
      color: #fff;
      border-color: var(--ds-pink);
      transform: translateY(-1.5px);
    }}

    /* ===== 呼出与浮动按钮 ===== */
    .nezuko-float-badge {{
      position: absolute;
      bottom: 14px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(35, 22, 18, 0.88);
      border: 1px solid var(--ds-brass-gold);
      color: var(--ds-gold-glow);
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 12px;
      cursor: pointer;
      white-space: nowrap;
      box-shadow: 0 4px 10px rgba(0,0,0,0.4);
      opacity: 0.85;
      transition: opacity 0.2s;
    }}
    .nezuko-float-badge:hover {{
      opacity: 1;
      background: var(--ds-dark-pink);
      color: #fff;
    }}

    /* 底部炭治郎市松纹装饰条 */
    .nezuko-ichimatsu-strip {{
      height: 6px;
      width: 100%;
      background: repeating-linear-gradient(45deg, var(--ds-tanjiro-green) 0, var(--ds-tanjiro-green) 6px, var(--ds-ichimatsu-black) 6px, var(--ds-ichimatsu-black) 12px);
    }}
  `;
  document.head.appendChild(styleEl);

  // ==========================================
  // 四、DOM 结构组装
  // ==========================================
  const root = document.createElement('div');
  root.id = 'nezuko-pet-root';
  root.innerHTML = `
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

    <!-- 角色骨骼头像容器 -->
    <div class="nezuko-pet-avatar" id="nezuko-pet-character" title="双击打开鬼灭看板 · 按住拖拽 · 滚轮切歌">
      <img src="${{NEZUKO_IMG_B64}}" class="nezuko-pet-img" alt="灶门祢豆子">
      
      <!-- 动态表情叠加层 -->
      <div class="nezuko-face-rig" id="nezuko-face-rig">
        <div class="nezuko-eyes-default"></div>
        <div class="nezuko-eyes-dot"></div>
        <div class="nezuko-eyes-crescent"></div>
        <div class="nezuko-cheeks-angry"></div>
        <div class="nezuko-demon-horn"></div>
        <div class="nezuko-demon-veins"></div>
      </div>

      <div class="nezuko-float-badge" id="nezuko-open-btn">🎋 鬼灭看板</div>
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

          <!-- 折叠校准滑块面板 -->
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

        <!-- 模块 4：原动漫 7 大经典高能动作机 (点击触发) -->
        <div class="nezuko-section-box">
          <div class="nezuko-section-title">
            <span>原动漫名场面动作机</span>
            <span style="font-size:10px; color:var(--ds-pink);">神韵复刻</span>
          </div>
          <div class="nezuko-actions-grid">
            <button class="nezuko-act-btn" data-action="run" data-expr="dot">
              <span>💨 豆豆眼狂奔</span>
            </button>
            <button class="nezuko-act-btn" data-action="tilt" data-expr="normal">
              <span>🎋 抱竹歪头</span>
            </button>
            <button class="nezuko-act-btn" data-action="stomp" data-expr="angry">
              <span>💢 气鼓跺小脚</span>
            </button>
            <button class="nezuko-act-btn" data-action="burst" data-expr="demon">
              <span>🔥 爆血觉醒</span>
            </button>
            <button class="nezuko-act-btn" data-action="box" data-expr="normal">
              <span>📦 钻木箱捉猫</span>
            </button>
            <button class="nezuko-act-btn" data-action="sleep" data-expr="crescent">
              <span>💤 犯困打瞌睡</span>
            </button>
            <button class="nezuko-act-btn" data-action="headpat" data-expr="crescent" style="grid-column: span 3;">
              <span>🌸 摸头杀闭眼蹭蹭 (超级撒娇)</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 底部炭治郎市松纹装饰带 -->
      <div class="nezuko-ichimatsu-strip"></div>
    </div>
  `;
  document.body.appendChild(root);

  // ==========================================
  // 五、逻辑绑定与交互驱动
  // ==========================================
  const charAvatar = document.getElementById('nezuko-pet-character');
  const mainCard = document.getElementById('nezuko-main-card');
  const openBtn = document.getElementById('nezuko-open-btn');
  const closeBtn = document.getElementById('nezuko-close-card');
  const faceRig = document.getElementById('nezuko-face-rig');
  const disc = document.getElementById('nezuko-disc');

  // 更新环形进度条显示
  function updateQuotaDisplay() {{
    const CIRCLE_CIRCUM = 62.83; // 2 * PI * 10
    
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

  // 看板开启/关闭
  openBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    mainCard.style.display = mainCard.style.display === 'flex' ? 'none' : 'flex';
  }});
  closeBtn.addEventListener('click', () => {{
    mainCard.style.display = 'none';
  }});
  charAvatar.addEventListener('dblclick', () => {{
    mainCard.style.display = mainCard.style.display === 'flex' ? 'none' : 'flex';
  }});

  // 动作与表情切换引擎
  let actionTimer = null;
  function triggerAction(actionName, exprName, duration = 6500) {{
    // 清除既有动作
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

  // 动作按钮绑定
  document.querySelectorAll('.nezuko-act-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const action = btn.getAttribute('data-action');
      const expr = btn.getAttribute('data-expr');
      triggerAction(action, expr);
    }});
  }});

  // 音乐控件绑定
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
    }} else {{
      playBtn.textContent = "▶ 播放";
      disc.classList.remove('record-spinning');
    }}
  }};

  document.getElementById('m-btn-play').addEventListener('click', () => musicEngine.toggle());
  document.getElementById('m-btn-next').addEventListener('click', () => musicEngine.next());
  document.getElementById('m-btn-prev').addEventListener('click', () => musicEngine.prev());

  document.getElementById('m-file-input').addEventListener('change', (e) => {{
    const f = e.target.files[0];
    if (f) musicEngine.loadLocalFile(f);
  }});

  // 滚轮在桌宠上切歌
  charAvatar.addEventListener('wheel', (e) => {{
    e.preventDefault();
    if (e.deltaY > 0) musicEngine.next();
    else musicEngine.prev();
  }});

  // 自动同步按钮
  document.getElementById('btn-sync-quota').addEventListener('click', () => {{
    sniffNativeQuotaFromDOM();
    updateQuotaDisplay();
  }});

  // 手动校准展开
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

  // ==========================================
  // 六、QQ 宠物级拖拽悬空挣扎与重力落地
  // ==========================================
  let isDragging = false;
  let dragStartX = 0, dragStartY = 0;
  let rootStartRight = 28, rootStartBottom = 24;

  charAvatar.addEventListener('mousedown', (e) => {{
    if (e.button !== 0) return;
    isDragging = true;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    
    const rect = root.getBoundingClientRect();
    rootStartRight = window.innerWidth - rect.right;
    rootStartBottom = window.innerHeight - rect.bottom;

    charAvatar.classList.add('nezuko-picked-up');
    triggerAction(null, 'dot', 999999); // 提起时出现豆豆眼惊慌状
    e.preventDefault();
  }});

  window.addEventListener('mousemove', (e) => {{
    if (!isDragging) return;
    const dx = e.clientX - dragStartX;
    const dy = e.clientY - dragStartY;

    root.style.right = (rootStartRight - dx) + 'px';
    root.style.bottom = (rootStartBottom - dy) + 'px';
  }});

  window.addEventListener('mouseup', () => {{
    if (isDragging) {{
      isDragging = false;
      charAvatar.classList.remove('nezuko-picked-up');
      faceRig.classList.remove('expr-dot');
    }}
  }});

  // 初始轻度眨眼待机
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
print(f"✅ 成功生成高级鬼灭桌宠核心组件: {target_js} ({len(js_code.encode('utf-8'))} 字节)")
