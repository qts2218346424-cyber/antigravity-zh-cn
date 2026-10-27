/**
 * Antigravity 灶门祢豆子 · 鬼灭之刃大正和风桌宠系统 (Demon Slayer Nezuko Engine 2.0)
 * 1. 真实模型配额看板 (Gemini / Claude / GPT 每周与5小时限额及重置倒计时)
 * 2. 原动漫 7 大名场面连贯动作机 + 动态表情系统 (彻底告别呆板)
 * 3. 鬼灭之刃大正和风界面 (粉红麻叶纹、雾云杉木箱、黄铜包角、紫藤樱花)
 * 4. 鬼灭之刃随身 BGM 音乐盒 (内置 Web Audio 八音盒 + 本地音乐导入)
 */

(function() {
  if (typeof window === 'undefined' || window.__NEZUKO_PET_INITIALIZED__) return;
  window.__NEZUKO_PET_INITIALIZED__ = true;

  const NEZUKO_IMG_B64 = "data:image/webp;base64,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";

  // ==========================================
  // 一、模型配额中枢 (Gemini 与 Claude/GPT 原生对应)
  // ==========================================
  const defaultQuotaState = {
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
  };

  function loadUserQuota() {
    try {
      const saved = localStorage.getItem('__nezuko_model_quota_v2__');
      if (saved) return Object.assign({}, defaultQuotaState, JSON.parse(saved));
    } catch (_) {}
    return Object.assign({}, defaultQuotaState);
  }

  function saveUserQuota(state) {
    try {
      localStorage.setItem('__nezuko_model_quota_v2__', JSON.stringify(state));
    } catch (_) {}
  }

  let currentQuota = loadUserQuota();

  // 尝试从 Antigravity 原生 DOM 中实时嗅探配额
  function sniffNativeQuotaFromDOM() {
    try {
      const textNodes = [];
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
      let node;
      while (node = walker.nextNode()) {
        const txt = node.nodeValue.trim();
        if (txt.includes('每周剩余可用配额') || txt.includes('5 小时剩余可用配额') || txt.includes('Weekly limit')) {
          textNodes.push(node);
        }
      }
      if (textNodes.length > 0) {
        // 解析 DOM 中可能存在的配额数值
        let updated = false;
        textNodes.forEach(tn => {
          const parent = tn.parentElement;
          if (!parent) return;
          const container = parent.closest('.quota-section, div') || parent;
          const text = container.textContent || '';
          const matchWeekly = text.match(/每周剩余可用配额[^\d]*(\d+)%/);
          if (matchWeekly) {
            currentQuota.geminiWeeklyPct = parseInt(matchWeekly[1], 10);
            updated = true;
          }
          const match5h = text.match(/5\s*小时剩余可用配额[^\d]*(\d+)%/);
          if (match5h) {
            currentQuota.gemini5hPct = parseInt(match5h[1], 10);
            updated = true;
          }
        });
        if (updated) {
          currentQuota.lastSynced = new Date().toLocaleTimeString('zh-CN', { hour12: false });
          saveUserQuota(currentQuota);
          updateQuotaDisplay();
        }
      }
    } catch (_) {}
  }

  setInterval(sniffNativeQuotaFromDOM, 5000);

  // ==========================================
  // 二、鬼灭之刃 Web Audio 随身八音盒引擎
  // ==========================================
  const noteFreqs = {
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.26, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50
  };

  const PLAYLIST = [
    {
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
    },
    {
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
    },
    {
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
    }
  ];

  class DemonSlayerMusicEngine {
    constructor() {
      this.ctx = null;
      this.isPlaying = false;
      this.currentTrack = 0;
      this.stepIndex = 0;
      this.timer = null;
      this.volume = 0.5;
      this.customAudio = null;
    }

    initContext() {
      if (!this.ctx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioContext();
      }
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    playTone(freq, duration) {
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
    }

    playNextNote() {
      if (!this.isPlaying) return;
      if (this.customAudio) return; // 正在播放本地音频

      const track = PLAYLIST[this.currentTrack];
      if (this.stepIndex >= track.notes.length) {
        this.stepIndex = 0; // 循环播放当前曲目
      }

      const [noteName, dur] = track.notes[this.stepIndex];
      const freq = noteFreqs[noteName] || 440;
      this.playTone(freq, dur);

      // 联动桌宠晃头节拍
      triggerMusicBeat();

      this.stepIndex++;
      this.timer = setTimeout(() => this.playNextNote(), dur * 1000);
    }

    play() {
      if (this.customAudio) {
        this.customAudio.play();
        this.isPlaying = true;
        updateMusicUI();
        return;
      }
      this.initContext();
      this.isPlaying = true;
      this.playNextNote();
      updateMusicUI();
    }

    pause() {
      this.isPlaying = false;
      if (this.timer) clearTimeout(this.timer);
      if (this.customAudio) {
        this.customAudio.pause();
      }
      updateMusicUI();
    }

    toggle() {
      if (this.isPlaying) this.pause();
      else this.play();
    }

    next() {
      this.pause();
      if (this.customAudio) {
        this.customAudio = null;
      }
      this.currentTrack = (this.currentTrack + 1) % PLAYLIST.length;
      this.stepIndex = 0;
      this.play();
    }

    prev() {
      this.pause();
      if (this.customAudio) {
        this.customAudio = null;
      }
      this.currentTrack = (this.currentTrack - 1 + PLAYLIST.length) % PLAYLIST.length;
      this.stepIndex = 0;
      this.play();
    }

    setVolume(val) {
      this.volume = Math.max(0, Math.min(1, val));
      if (this.customAudio) {
        this.customAudio.volume = this.volume;
      }
    }

    loadLocalFile(file) {
      const url = URL.createObjectURL(file);
      this.pause();
      this.customAudio = new Audio(url);
      this.customAudio.volume = this.volume;
      this.customAudio.loop = true;
      this.customAudio.addEventListener('ended', () => this.next());
      this.play();
      updateMusicUI(file.name);
    }
  }

  const musicEngine = new DemonSlayerMusicEngine();

  // 节拍联动晃头
  let beatTimer = null;
  function triggerMusicBeat() {
    const petEl = document.getElementById('nezuko-pet-character');
    if (!petEl || !musicEngine.isPlaying) return;
    petEl.classList.add('nezuko-music-bob');
    if (beatTimer) clearTimeout(beatTimer);
    beatTimer = setTimeout(() => {
      petEl.classList.remove('nezuko-music-bob');
    }, 400);
  }

  // ==========================================
  // 三、CSS 样式库 (大正和风 + 鬼灭视觉 + 多表情动作)
  // ==========================================
  const styleEl = document.createElement('style');
  styleEl.id = 'nezuko-pet-advanced-styles';
  styleEl.textContent = `
    /* ===== 鬼灭之刃基础色彩与字体 ===== */
    :root {
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
    }

    /* 容器浮动 */
    #nezuko-pet-root {
      position: fixed;
      right: 28px;
      bottom: 24px;
      z-index: 999999;
      user-select: none;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }

    /* ===== 地面接触柔和阴影 ===== */
    .nezuko-pet-ground-shadow {
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
    }

    /* 桌宠主形象骨骼层 */
    .nezuko-pet-avatar {
      position: relative;
      width: 130px;
      height: 180px;
      cursor: grab;
      filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.2));
      transition: transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
      transform-origin: bottom center;
    }

    .nezuko-pet-avatar:active {
      cursor: grabbing;
    }

    /* 立绘图片主体 */
    .nezuko-pet-img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      pointer-events: none;
      display: block;
      transform-origin: bottom center;
    }

    /* ===== 多表情神态覆盖层 (Expression Overlay) ===== */
    .nezuko-face-rig {
      position: absolute;
      top: 36px;
      left: 38px;
      width: 56px;
      height: 44px;
      pointer-events: none;
      z-index: 5;
    }

    /* 默认眨眼萌眼 */
    .nezuko-eyes-default {
      width: 100%;
      height: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 4px;
      box-sizing: border-box;
      opacity: 0;
      transition: opacity 0.2s;
    }

    /* 经典魔性豆豆眼 (·_·) */
    .nezuko-eyes-dot {
      position: absolute;
      top: 14px;
      left: 6px;
      width: 44px;
      height: 16px;
      display: none;
      justify-content: space-between;
      align-items: center;
    }
    .nezuko-eyes-dot::before, .nezuko-eyes-dot::after {
      content: '';
      width: 9px;
      height: 9px;
      background: #111;
      border-radius: 50%;
      box-shadow: 0 0 2px rgba(0,0,0,0.8);
    }

    /* 闭眼月牙笑 (^‿^) */
    .nezuko-eyes-crescent {
      position: absolute;
      top: 12px;
      left: 4px;
      width: 48px;
      height: 16px;
      display: none;
      justify-content: space-between;
    }
    .nezuko-eyes-crescent::before, .nezuko-eyes-crescent::after {
      content: '';
      width: 16px;
      height: 8px;
      border-bottom: 3.5px solid #231612;
      border-radius: 0 0 16px 16px;
    }

    /* 气鼓鼓大腮帮 (包子脸) */
    .nezuko-cheeks-angry {
      position: absolute;
      top: 18px;
      left: 0;
      width: 56px;
      height: 20px;
      display: none;
      justify-content: space-between;
    }
    .nezuko-cheeks-angry::before, .nezuko-cheeks-angry::after {
      content: '';
      width: 14px;
      height: 14px;
      background: radial-gradient(circle, #ff80ab 0%, rgba(255, 64, 129, 0.4) 65%, transparent 100%);
      border-radius: 50%;
    }

    /* 鬼化额角与鲜红鬼纹 */
    .nezuko-demon-horn {
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
    }
    .nezuko-demon-veins {
      position: absolute;
      top: -4px;
      right: 6px;
      width: 22px;
      height: 20px;
      background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2 Q18 8 16 16 Q22 18 20 22 Q14 18 12 12 Q8 16 4 22' fill='none' stroke='%23ff1744' stroke-width='2'/%3E%3C/svg%3E") no-repeat center;
      display: none;
    }

    /* 表情状态机切换 */
    .expr-dot .nezuko-eyes-dot { display: flex !important; }
    .expr-crescent .nezuko-eyes-crescent { display: flex !important; }
    .expr-angry .nezuko-cheeks-angry { display: flex !important; }
    .expr-demon .nezuko-demon-horn,
    .expr-demon .nezuko-demon-veins { display: block !important; }

    /* ===== 原动漫名场面 7 大动作动画机 ===== */

    /* 动作 1：小豆丁风火轮狂奔 (Tiny Chibi Run) */
    .action-run {
      animation: nezukoRunCycle 0.55s infinite alternate ease-in-out !important;
    }
    @keyframes nezukoRunCycle {
      0% {
        transform: scale(0.72) translateY(12px) translateX(-28px) rotate(-10deg);
      }
      100% {
        transform: scale(0.72) translateY(6px) translateX(28px) rotate(10deg);
      }
    }
    .action-run ~ .nezuko-pet-ground-shadow {
      width: 70px;
      transform: translateX(-50%) scaleX(0.75);
    }

    /* 动作 2：抱竹歪头晃脑 (Head Tilt & Sway) */
    .action-tilt {
      animation: nezukoHeadSway 2.4s infinite ease-in-out !important;
    }
    @keyframes nezukoHeadSway {
      0%, 100% { transform: rotate(0deg) translateY(0); }
      25% { transform: rotate(-18deg) translateY(-2px); }
      50% { transform: rotate(0deg) translateY(0); }
      75% { transform: rotate(18deg) translateY(-2px); }
    }

    /* 动作 3：气鼓鼓跺小脚 (Angry Stomp) */
    .action-stomp {
      animation: nezukoAngryStomp 0.28s infinite alternate cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    @keyframes nezukoAngryStomp {
      0% { transform: translateY(0) rotate(0deg); }
      100% { transform: translateY(-7px) rotate(-5deg); }
    }

    /* 动作 4：血鬼术·爆血觉醒 (Blood Demon Art) */
    .action-burst {
      animation: nezukoBurstFlame 1.2s infinite ease-in-out !important;
      filter: drop-shadow(0 0 18px rgba(255, 23, 68, 0.9)) saturate(1.4) !important;
    }
    @keyframes nezukoBurstFlame {
      0%, 100% { transform: scale(1) translateY(0); }
      50% { transform: scale(1.1) translateY(-8px); }
    }

    /* 动作 5：钻雾云杉木箱捉迷藏 (Box Peek-a-boo) */
    .action-box {
      animation: nezukoBoxHide 1.8s infinite ease-in-out !important;
    }
    @keyframes nezukoBoxHide {
      0%, 100% { transform: scale(0.85) translateY(24px); opacity: 0.9; }
      50% { transform: scale(0.92) translateY(10px); opacity: 1; }
    }

    /* 动作 6：揉眼犯困打瞌睡 (Drowsy Sleep) */
    .action-sleep {
      animation: nezukoSleepCycle 3.2s infinite ease-in-out !important;
    }
    @keyframes nezukoSleepCycle {
      0%, 100% { transform: rotate(12deg) translateY(14px) scale(0.9); }
      50% { transform: rotate(15deg) translateY(18px) scale(0.88); }
    }

    /* 动作 7：摸头杀闭眼撒娇蹭蹭 (Headpat Cuddle) */
    .action-headpat {
      animation: nezukoHeadpatCuddle 1.4s infinite ease-in-out !important;
    }
    @keyframes nezukoHeadpatCuddle {
      0%, 100% { transform: translateY(0) rotate(0deg); }
      50% { transform: translateY(-6px) rotate(8deg); }
    }

    /* QQ宠物拖拽被提起 (悬空慌乱挣扎蹬腿) */
    .nezuko-picked-up {
      transform: scale(1.08) translateY(-22px) rotate(-8deg) !important;
      filter: drop-shadow(0 14px 22px rgba(0, 0, 0, 0.35)) !important;
      animation: nezukoStruggleLegs 0.22s infinite alternate ease-in-out !important;
    }
    @keyframes nezukoStruggleLegs {
      0% { transform: scale(1.08) translateY(-22px) rotate(-7deg); }
      100% { transform: scale(1.08) translateY(-22px) rotate(7deg); }
    }
    .nezuko-picked-up ~ .nezuko-pet-ground-shadow {
      transform: translateX(-50%) scale(0.55);
      opacity: 0.25;
    }

    /* 音乐节拍轻微晃脑 */
    .nezuko-music-bob {
      transform: translateY(-4px) rotate(3deg);
      transition: transform 0.15s ease-out;
    }

    /* 道具层：雾云杉木箱 */
    .nezuko-box-prop {
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
    }
    .nezuko-box-prop::before {
      content: '';
      position: absolute;
      top: 8px; left: 8px; right: 8px; bottom: 8px;
      border: 1px dashed var(--ds-brass-gold);
      opacity: 0.6;
    }
    .action-box ~ .nezuko-box-prop {
      display: block !important;
    }

    /* ===== 特效粒子层 (樱花、怒气十字、Zzz、爆血火焰) ===== */
    .nezuko-fx-container {
      position: absolute;
      inset: 0;
      pointer-events: none;
      z-index: 20;
    }

    .nezuko-fx-cross {
      position: absolute;
      top: 15px;
      right: 18px;
      color: #ff1744;
      font-size: 22px;
      font-weight: 900;
      display: none;
      animation: crossShake 0.3s infinite;
    }
    .action-stomp ~ .nezuko-fx-container .nezuko-fx-cross {
      display: block;
    }
    @keyframes crossShake {
      0% { transform: scale(1) rotate(0deg); }
      50% { transform: scale(1.25) rotate(12deg); }
      100% { transform: scale(1) rotate(-8deg); }
    }

    .nezuko-fx-zzz {
      position: absolute;
      top: 0;
      right: 8px;
      color: #f48fb1;
      font-size: 16px;
      font-weight: bold;
      display: none;
      animation: zzzFloat 2.2s infinite linear;
    }
    .action-sleep ~ .nezuko-fx-container .nezuko-fx-zzz {
      display: block;
    }
    @keyframes zzzFloat {
      0% { transform: translate(0, 0) scale(0.6); opacity: 0; }
      50% { opacity: 1; }
      100% { transform: translate(14px, -28px) scale(1.3); opacity: 0; }
    }

    .nezuko-fx-hearts {
      position: absolute;
      top: 10px;
      left: 10px;
      right: 10px;
      font-size: 18px;
      display: none;
      animation: heartSparkle 1.2s infinite ease-out;
    }
    .action-headpat ~ .nezuko-fx-container .nezuko-fx-hearts {
      display: block;
    }
    @keyframes heartSparkle {
      0% { transform: scale(0.8) translateY(0); opacity: 0; }
      50% { opacity: 1; }
      100% { transform: scale(1.2) translateY(-20px); opacity: 0; }
    }

    /* ===== 大正和风主操作面板 (雾云杉木箱 + 麻叶纹 + 烫金) ===== */
    #nezuko-main-card {
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
    }

    /* 粉红麻叶纹几何背景衬底 */
    .nezuko-asanoha-pattern {
      position: absolute;
      inset: 0;
      opacity: 0.08;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='103.92' viewBox='0 0 60 103.92'%3E%3Cpath d='M30 0 L60 17.32 L60 51.96 L30 69.28 L0 51.96 L0 17.32 Z' fill='none' stroke='%23f48fb1' stroke-width='1.5'/%3E%3Cpath d='M30 0 L30 69.28 M60 17.32 L0 51.96 M60 51.96 L0 17.32' stroke='%23f48fb1' stroke-width='1.5'/%3E%3Cpath d='M30 34.64 L30 0 M30 34.64 L60 17.32 M30 34.64 L60 51.96 M30 34.64 L30 69.28 M30 34.64 L0 51.96 M30 34.64 L0 17.32' stroke='%23f48fb1' stroke-width='2'/%3E%3C/svg%3E");
      pointer-events: none;
    }

    /* 顶部烫金日式和风标题条 */
    .nezuko-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      background: linear-gradient(90deg, #381f19 0%, #4a2920 100%);
      border-bottom: 1.5px solid var(--ds-brass-gold);
      position: relative;
    }
    .nezuko-header-title {
      font-size: 13px;
      font-weight: 700;
      color: var(--ds-gold-glow);
      display: flex;
      align-items: center;
      gap: 6px;
      text-shadow: 0 1px 3px rgba(0,0,0,0.8);
    }
    .nezuko-header-badge {
      font-size: 10px;
      background: var(--ds-dark-pink);
      color: #fff;
      padding: 1px 6px;
      border-radius: 4px;
      letter-spacing: 0.5px;
    }
    .nezuko-close-btn {
      background: transparent;
      border: none;
      color: #b0bec5;
      font-size: 16px;
      cursor: pointer;
      line-height: 1;
      padding: 2px 6px;
      border-radius: 4px;
    }
    .nezuko-close-btn:hover {
      color: #fff;
      background: rgba(255,255,255,0.1);
    }

    /* 卡片内容滚动区 */
    .nezuko-card-body {
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      max-height: 480px;
      overflow-y: auto;
      position: relative;
    }

    /* 模块分块样式 */
    .nezuko-section-box {
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(197, 155, 39, 0.35);
      border-radius: 8px;
      padding: 10px 12px;
      position: relative;
    }
    .nezuko-section-title {
      font-size: 12px;
      font-weight: 700;
      color: #e0e0e0;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    /* ===== 原生配额条目样式 ===== */
    .nezuko-quota-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .nezuko-quota-row:last-child {
      border-bottom: none;
      padding-bottom: 2px;
    }
    .nezuko-quota-meta {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .nezuko-quota-name {
      font-size: 12px;
      color: #f5f5f5;
    }
    .nezuko-quota-reset {
      font-size: 10px;
      color: #9e9e9e;
    }
    .nezuko-quota-val-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .nezuko-quota-pct {
      font-size: 13px;
      font-weight: 700;
      color: #81c784;
    }
    /* SVG 环形进度条 */
    .nezuko-ring-wrap {
      width: 24px;
      height: 24px;
      transform: rotate(-90deg);
    }
    .nezuko-ring-bg {
      fill: none;
      stroke: rgba(255, 255, 255, 0.15);
      stroke-width: 3.5;
    }
    .nezuko-ring-bar {
      fill: none;
      stroke: #81c784;
      stroke-width: 3.5;
      stroke-linecap: round;
      stroke-dasharray: 63;
      stroke-dashoffset: 0;
      transition: stroke-dashoffset 0.6s ease;
    }

    /* ===== BGM 随身音乐盒面板 ===== */
    .nezuko-music-player {
      background: linear-gradient(180deg, rgba(46, 26, 20, 0.7) 0%, rgba(20, 12, 10, 0.85) 100%);
      border: 1px solid var(--ds-brass-gold);
      border-radius: 8px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .nezuko-music-info {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    /* 迷你和风黑胶唱片 */
    .nezuko-record-disc {
      width: 34px;
      height: 34px;
      background: radial-gradient(circle, #ff80ab 15%, #111 16%, #222 65%, #111 100%);
      border: 1.5px solid var(--ds-brass-gold);
      border-radius: 50%;
      flex-shrink: 0;
      animation: recordSpin 3.5s infinite linear;
      animation-play-state: paused;
    }
    .record-spinning {
      animation-play-state: running !important;
    }
    @keyframes recordSpin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    .nezuko-song-texts {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .nezuko-song-title {
      font-size: 11.5px;
      font-weight: 700;
      color: #fff;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
    .nezuko-song-sub {
      font-size: 9.5px;
      color: var(--ds-pink);
    }

    /* 播放器控制按钮组 */
    .nezuko-music-controls {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      padding-top: 4px;
    }
    .nezuko-ctrl-btn {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(197, 155, 39, 0.4);
      color: #fff;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .nezuko-ctrl-btn:hover {
      background: var(--ds-dark-pink);
      border-color: var(--ds-pink);
    }
    .nezuko-ctrl-play {
      background: linear-gradient(135deg, var(--ds-dark-pink), var(--ds-crimson));
      font-weight: bold;
      padding: 4px 14px;
    }

    /* ===== 原动漫动作快捷网格 ===== */
    .nezuko-actions-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
    }
    .nezuko-act-btn {
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
    }
    .nezuko-act-btn:hover {
      background: var(--ds-dark-pink);
      color: #fff;
      border-color: var(--ds-pink);
      transform: translateY(-1.5px);
    }

    /* ===== 呼出与浮动按钮 ===== */
    .nezuko-float-badge {
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
    }
    .nezuko-float-badge:hover {
      opacity: 1;
      background: var(--ds-dark-pink);
      color: #fff;
    }

    /* 底部炭治郎市松纹装饰条 */
    .nezuko-ichimatsu-strip {
      height: 6px;
      width: 100%;
      background: repeating-linear-gradient(45deg, var(--ds-tanjiro-green) 0, var(--ds-tanjiro-green) 6px, var(--ds-ichimatsu-black) 6px, var(--ds-ichimatsu-black) 12px);
    }
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
      <img src="${NEZUKO_IMG_B64}" class="nezuko-pet-img" alt="灶门祢豆子">
      
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
              <span class="nezuko-quota-reset" id="lbl-gemini-weekly-reset">${currentQuota.geminiWeeklyReset}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-gemini-weekly-pct">${currentQuota.geminiWeeklyPct}%</span>
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
              <span class="nezuko-quota-reset" id="lbl-gemini-5h-reset">${currentQuota.gemini5hReset}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-gemini-5h-pct">${currentQuota.gemini5hPct}%</span>
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
              <span class="nezuko-quota-reset" id="lbl-claude-weekly-reset">${currentQuota.claudeWeeklyReset}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-claude-weekly-pct">${currentQuota.claudeWeeklyPct}%</span>
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
              <span class="nezuko-quota-reset" id="lbl-claude-5h-reset">${currentQuota.claude5hReset}</span>
            </div>
            <div class="nezuko-quota-val-group">
              <span class="nezuko-quota-pct" id="lbl-claude-5h-pct">${currentQuota.claude5hPct}%</span>
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
  function updateQuotaDisplay() {
    const CIRCLE_CIRCUM = 62.83; // 2 * PI * 10
    
    const setRing = (id, pct) => {
      const ring = document.getElementById(id);
      if (!ring) return;
      const offset = CIRCLE_CIRCUM * (1 - (pct / 100));
      ring.style.strokeDashoffset = offset;
      if (pct > 75) ring.style.stroke = '#81c784';
      else if (pct > 30) ring.style.stroke = '#ffd54f';
      else ring.style.stroke = '#e57373';
    };

    setRing('ring-gemini-weekly', currentQuota.geminiWeeklyPct);
    setRing('ring-gemini-5h', currentQuota.gemini5hPct);
    setRing('ring-claude-weekly', currentQuota.claudeWeeklyPct);
    setRing('ring-claude-5h', currentQuota.claude5hPct);

    document.getElementById('lbl-gemini-weekly-pct').textContent = currentQuota.geminiWeeklyPct + '%';
    document.getElementById('lbl-gemini-5h-pct').textContent = currentQuota.gemini5hPct + '%';
    document.getElementById('lbl-claude-weekly-pct').textContent = currentQuota.claudeWeeklyPct + '%';
    document.getElementById('lbl-claude-5h-pct').textContent = currentQuota.claude5hPct + '%';
  }
  updateQuotaDisplay();

  // 看板开启/关闭
  openBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    mainCard.style.display = mainCard.style.display === 'flex' ? 'none' : 'flex';
  });
  closeBtn.addEventListener('click', () => {
    mainCard.style.display = 'none';
  });
  charAvatar.addEventListener('dblclick', () => {
    mainCard.style.display = mainCard.style.display === 'flex' ? 'none' : 'flex';
  });

  // 动作与表情切换引擎
  let actionTimer = null;
  function triggerAction(actionName, exprName, duration = 6500) {
    // 清除既有动作
    charAvatar.classList.remove('action-run', 'action-tilt', 'action-stomp', 'action-burst', 'action-box', 'action-sleep', 'action-headpat');
    faceRig.classList.remove('expr-dot', 'expr-crescent', 'expr-angry', 'expr-demon');

    if (actionName) charAvatar.classList.add('action-' + actionName);
    if (exprName && exprName !== 'normal') faceRig.classList.add('expr-' + exprName);

    if (actionTimer) clearTimeout(actionTimer);
    actionTimer = setTimeout(() => {
      charAvatar.classList.remove('action-run', 'action-tilt', 'action-stomp', 'action-burst', 'action-box', 'action-sleep', 'action-headpat');
      faceRig.classList.remove('expr-dot', 'expr-crescent', 'expr-angry', 'expr-demon');
    }, duration);
  }

  // 动作按钮绑定
  document.querySelectorAll('.nezuko-act-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.getAttribute('data-action');
      const expr = btn.getAttribute('data-expr');
      triggerAction(action, expr);
    });
  });

  // 音乐控件绑定
  window.updateMusicUI = function(customName) {
    const titleEl = document.getElementById('music-title');
    const subEl = document.getElementById('music-sub');
    const playBtn = document.getElementById('m-btn-play');

    if (customName) {
      titleEl.textContent = customName;
      subEl.textContent = "本地音乐文件";
    } else {
      const trk = PLAYLIST[musicEngine.currentTrack];
      titleEl.textContent = trk.title;
      subEl.textContent = trk.subtitle;
    }

    if (musicEngine.isPlaying) {
      playBtn.textContent = "⏸ 暂停";
      disc.classList.add('record-spinning');
    } else {
      playBtn.textContent = "▶ 播放";
      disc.classList.remove('record-spinning');
    }
  };

  document.getElementById('m-btn-play').addEventListener('click', () => musicEngine.toggle());
  document.getElementById('m-btn-next').addEventListener('click', () => musicEngine.next());
  document.getElementById('m-btn-prev').addEventListener('click', () => musicEngine.prev());

  document.getElementById('m-file-input').addEventListener('change', (e) => {
    const f = e.target.files[0];
    if (f) musicEngine.loadLocalFile(f);
  });

  // 滚轮在桌宠上切歌
  charAvatar.addEventListener('wheel', (e) => {
    e.preventDefault();
    if (e.deltaY > 0) musicEngine.next();
    else musicEngine.prev();
  });

  // 自动同步按钮
  document.getElementById('btn-sync-quota').addEventListener('click', () => {
    sniffNativeQuotaFromDOM();
    updateQuotaDisplay();
  });

  // 手动校准展开
  const adjBox = document.getElementById('nezuko-adjust-box');
  document.getElementById('btn-toggle-adjust').addEventListener('click', () => {
    adjBox.style.display = adjBox.style.display === 'block' ? 'none' : 'block';
  });

  const rngGW = document.getElementById('rng-adj-gw');
  const rngG5 = document.getElementById('rng-adj-g5');
  rngGW.addEventListener('input', (e) => {
    currentQuota.geminiWeeklyPct = parseInt(e.target.value, 10);
    document.getElementById('val-adj-gw').textContent = e.target.value + '%';
    saveUserQuota(currentQuota);
    updateQuotaDisplay();
  });
  rngG5.addEventListener('input', (e) => {
    currentQuota.gemini5hPct = parseInt(e.target.value, 10);
    document.getElementById('val-adj-g5').textContent = e.target.value + '%';
    saveUserQuota(currentQuota);
    updateQuotaDisplay();
  });

  // ==========================================
  // 六、QQ 宠物级拖拽悬空挣扎与重力落地
  // ==========================================
  let isDragging = false;
  let dragStartX = 0, dragStartY = 0;
  let rootStartRight = 28, rootStartBottom = 24;

  charAvatar.addEventListener('mousedown', (e) => {
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
  });

  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStartX;
    const dy = e.clientY - dragStartY;

    root.style.right = (rootStartRight - dx) + 'px';
    root.style.bottom = (rootStartBottom - dy) + 'px';
  });

  window.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      charAvatar.classList.remove('nezuko-picked-up');
      faceRig.classList.remove('expr-dot');
    }
  });

  // 初始轻度眨眼待机
  setInterval(() => {
    if (!charAvatar.className.includes('action-') && !isDragging) {
      faceRig.classList.add('expr-crescent');
      setTimeout(() => faceRig.classList.remove('expr-crescent'), 350);
    }
  }, 4500);

})();
