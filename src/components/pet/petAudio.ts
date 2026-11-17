/**
 * WebAudio + 原生音频解码双模桌面伴侣声学引擎
 * 优先使用 WebAudio AudioContext.decodeAudioData 解码播放内置原曲与角色原生语音，
 * 彻底绕过 Windows WebView2 对 HTMLAudioElement data: URI 的自动播放拦截与静默失败问题。
 */
class PetAudioEngine {
  private ctx: AudioContext | null = null;
  private decodedCache = new Map<string, AudioBuffer>();
  private currentSource: AudioBufferSourceNode | null = null;
  private currentFallbackAudio: HTMLAudioElement | null = null;
  private onVoiceStateCb: ((playing: boolean) => void) | null = null;
  private activePlayId = 0;
  public activeVoiceTag: string | null = null;
  public muted = false;

  /** 预热并解锁 WebAudio 上下文 */
  warmup() {
    this.ensureContext();
  }

  /** 停止当前正在播放的角色动漫原声或《团子大家族》原曲 */
  stopVoice() {
    this.activePlayId += 1;
    this.activeVoiceTag = null;
    if (this.currentSource) {
      try {
        this.currentSource.onended = null;
        this.currentSource.stop();
        this.currentSource.disconnect();
      } catch {
        // 忽略重复停止异常
      }
      this.currentSource = null;
    }
    if (this.currentFallbackAudio) {
      try {
        this.currentFallbackAudio.pause();
        this.currentFallbackAudio.currentTime = 0;
      } catch {
        // 忽略销毁异常
      }
      this.currentFallbackAudio = null;
    }
    if (this.onVoiceStateCb) {
      const cb = this.onVoiceStateCb;
      this.onVoiceStateCb = null;
      cb(false);
    }
  }

  private dataUriToArrayBuffer(dataUri: string): ArrayBuffer | null {
    const commaIdx = dataUri.indexOf(',');
    if (commaIdx < 0) return null;
    try {
      const base64 = dataUri.slice(commaIdx + 1);
      const binary = window.atob(base64);
      const len = binary.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      return bytes.buffer;
    } catch {
      return null;
    }
  }

  /**
   * 播放角色专属离线动漫原生语音或《团子大家族》原动画真曲
   * 通过 WebAudio 硬件混音通道解码输出，100% 杜绝 WebView2 <audio> 静默无声
   */
  playVoice(
    dataUri?: string | null,
    onStateChange?: (playing: boolean) => void,
    voiceTag?: string,
  ): boolean {
    if (this.muted || !dataUri || typeof window === 'undefined') return false;
    this.stopVoice();

    const playId = ++this.activePlayId;
    this.activeVoiceTag = voiceTag || 'voice';
    this.onVoiceStateCb = onStateChange || null;
    if (onStateChange) onStateChange(true);

    const finishIfCurrent = () => {
      if (this.activePlayId !== playId) return;
      this.currentSource = null;
      this.currentFallbackAudio = null;
      this.activeVoiceTag = null;
      if (this.onVoiceStateCb) {
        const cb = this.onVoiceStateCb;
        this.onVoiceStateCb = null;
        cb(false);
      }
    };

    const ctx = this.ensureContext();
    const cacheKey = `${voiceTag || ''}:${dataUri.length}:${dataUri.slice(-32)}`;

    const playBuffer = (audioBuffer: AudioBuffer) => {
      if (this.activePlayId !== playId || this.muted || !ctx) return;
      try {
        if (ctx.state === 'suspended') {
          void ctx.resume();
        }
        const source = ctx.createBufferSource();
        source.buffer = audioBuffer;
        const gainNode = ctx.createGain();
        // 对白给予饱满增益，原版歌曲保持柔和舒适音量
        gainNode.gain.value = voiceTag === 'ushio_dango' ? 0.92 : 1.08;
        source.connect(gainNode);
        gainNode.connect(ctx.destination);
        source.onended = finishIfCurrent;
        this.currentSource = source;
        source.start(0);
      } catch {
        this.playViaHtmlAudioFallback(dataUri, playId, finishIfCurrent);
      }
    };

    if (ctx) {
      const cached = this.decodedCache.get(cacheKey);
      if (cached) {
        playBuffer(cached);
        return true;
      }
      const rawBuffer = this.dataUriToArrayBuffer(dataUri);
      if (rawBuffer) {
        ctx
          .decodeAudioData(rawBuffer.slice(0))
          .then((decoded) => {
            this.decodedCache.set(cacheKey, decoded);
            playBuffer(decoded);
          })
          .catch(() => {
            this.playViaHtmlAudioFallback(dataUri, playId, finishIfCurrent);
          });
        return true;
      }
    }

    return this.playViaHtmlAudioFallback(dataUri, playId, finishIfCurrent);
  }

  private playViaHtmlAudioFallback(
    dataUri: string,
    playId: number,
    onDone: () => void,
  ): boolean {
    if (this.activePlayId !== playId || this.muted) return false;
    try {
      const audio = new Audio(dataUri);
      audio.volume = 0.95;
      this.currentFallbackAudio = audio;
      audio.addEventListener('ended', onDone, { once: true });
      audio.addEventListener('error', onDone, { once: true });
      void audio.play().catch(onDone);
      return true;
    } catch {
      onDone();
      return false;
    }
  }

  private ensureContext(): AudioContext | null {
    if (this.muted || typeof window === 'undefined') return null;
    try {
      const AC =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!AC) return null;
      if (!this.ctx) this.ctx = new AC();
      if (this.ctx.state === 'suspended') {
        void this.ctx.resume();
      }
      return this.ctx;
    } catch {
      return null;
    }
  }

  private playTone(
    freqStart: number,
    freqEnd: number,
    durationSec: number,
    type: OscillatorType = 'sine',
    gainPeak = 0.08,
    delaySec = 0,
  ) {
    const ctx = this.ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime + delaySec;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freqStart, now);
    osc.frequency.exponentialRampToValueAtTime(Math.max(40, freqEnd), now + durationSec);

    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.linearRampToValueAtTime(gainPeak, now + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + durationSec);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + durationSec + 0.02);
  }

  /** 温柔摸头 / 投喂：温暖治愈双和弦叮咚 */
  playCare() {
    this.playTone(587.33, 783.99, 0.16, 'sine', 0.08, 0);
    this.playTone(880, 1046.5, 0.22, 'triangle', 0.06, 0.08);
  }

  /** 轻盈木地板碎步声 */
  playFootstep() {
    this.playTone(170, 82, 0.065, 'triangle', 0.05, 0);
  }

  /** 8帧转木箱 / 风火轮狂奔旋风音效 */
  playSpinWind() {
    const ctx = this.ensureContext();
    if (!ctx) return;
    const dur = 0.48;
    const bufferSize = Math.floor(ctx.sampleRate * dur);
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.sin((i / bufferSize) * Math.PI);
    }
    const noise = ctx.createBufferSource();
    noise.buffer = buffer;

    const filter = ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.Q.value = 2.6;
    filter.frequency.setValueAtTime(340, ctx.currentTime);
    filter.frequency.exponentialRampToValueAtTime(1650, ctx.currentTime + dur * 0.65);
    filter.frequency.exponentialRampToValueAtTime(420, ctx.currentTime + dur);

    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.11, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);

    noise.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);
    noise.start();
  }

  /** 木箱落地 / 跺脚厚重震响 */
  playWoodThud() {
    this.playTone(155, 52, 0.22, 'sine', 0.14, 0);
    this.playTone(95, 38, 0.18, 'triangle', 0.09, 0.02);
  }

  /** 血鬼术·爆血晶体迸发音效 */
  playBloodBurst() {
    this.playTone(440, 1180, 0.18, 'sawtooth', 0.045, 0);
    this.playTone(880, 1567.98, 0.28, 'sine', 0.07, 0.06);
  }

  /** 小王子玫瑰/狐狸星尘谐音 */
  playStardust() {
    this.playTone(659.25, 987.77, 0.18, 'sine', 0.065, 0);
    this.playTone(1318.51, 1567.98, 0.26, 'sine', 0.05, 0.07);
  }

  /** B612 许愿流星划过 */
  playShootingStar() {
    this.playTone(1046.5, 2093, 0.24, 'sine', 0.06, 0);
    this.playTone(1567.98, 1318.51, 0.32, 'triangle', 0.05, 0.12);
  }

  /** 炭治郎 · 水之呼吸清泉流波音效 */
  playWaterBreath() {
    this.playTone(392.0, 587.33, 0.22, 'sine', 0.075, 0);
    this.playTone(587.33, 880.0, 0.26, 'sine', 0.065, 0.09);
    this.playTone(1174.66, 783.99, 0.28, 'triangle', 0.045, 0.18);
  }

  /** 善逸 · 雷之呼吸霹雳一闪瞬发电流音 */
  playThunderSpark() {
    this.playTone(1760, 320, 0.14, 'sawtooth', 0.055, 0);
    this.playTone(2349.32, 987.77, 0.19, 'triangle', 0.06, 0.05);
  }

  /** 伊之助 · 兽之呼吸双刀突进战鼓音 */
  playBeastRoar() {
    this.playTone(130.81, 65.41, 0.2, 'sawtooth', 0.07, 0);
    this.playTone(261.63, 392.0, 0.18, 'triangle', 0.07, 0.06);
  }

  /** 低配额温和双音风铃提示 */
  playQuotaAlert() {
    this.playTone(783.99, 659.25, 0.18, 'sine', 0.06, 0);
    this.playTone(659.25, 523.25, 0.24, 'sine', 0.055, 0.16);
  }

  /** Web 纯静态预览无后端音频包时的八音盒微旋律回退 */
  playDangoMelody() {
    const notes = [
      { f: 880.0, d: 0.16, t: 0.0 },
      { f: 783.99, d: 0.16, t: 0.15 },
      { f: 880.0, d: 0.18, t: 0.3 },
      { f: 659.25, d: 0.24, t: 0.47 },
      { f: 698.46, d: 0.32, t: 0.7 },
    ];
    for (const n of notes) {
      this.playTone(n.f, n.f * 1.002, n.d, 'sine', 0.068, n.t);
      this.playTone(n.f * 2, n.f * 2, n.d * 0.75, 'triangle', 0.022, n.t);
    }
  }

  /** CLANNAD 小镇愿望光玉空灵水晶琶音 */
  playLightOrb() {
    this.playTone(1046.5, 1046.5, 0.28, 'sine', 0.05, 0);
    this.playTone(1318.51, 1318.51, 0.3, 'sine', 0.05, 0.09);
    this.playTone(1567.98, 1567.98, 0.34, 'sine', 0.048, 0.18);
    this.playTone(1975.53, 1975.53, 0.42, 'triangle', 0.038, 0.27);
  }
}

export const petAudio = new PetAudioEngine();
