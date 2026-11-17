/**
 * WebAudio 桌面伴侣实时治愈音效合成器（零外部音频文件依赖）
 */
class PetAudioEngine {
  private ctx: AudioContext | null = null;
  public muted = false;

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

  /** 冈崎汐 ·《团子大家族》八音盒晶莹五音前奏微旋律 (6-5-6-3-4) */
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
