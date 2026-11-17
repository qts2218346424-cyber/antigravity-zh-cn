export type ClannadSplashThemeId =
  | 'clannad-orbs'
  | 'clannad-sakura'
  | 'clannad-sunflower'
  | 'clannad-starfish'
  | 'none';

export interface ClannadSplashThemeSpec {
  id: Exclude<ClannadSplashThemeId, 'none'>;
  name: string;
  shortName: string;
  badge: string;
  subtitle: string;
  quote: string;
  isLight: boolean;
  accent: string;
  secondaryAccent: string;
  linkedSkinId: string;
  steps: [string, string, string];
}

export interface StudioSplashPrefs {
  /** 是否在打开 Antigravity Studio 主窗口时展示启动序幕动画 */
  studioBootEnabled: boolean;
  /** 当前选定的启动动画主题 */
  themeId: ClannadSplashThemeId;
  /** 序幕展示时长（毫秒） */
  durationMs: 1800 | 2600 | 3800;
  /** 是否伴随播放清脆轻柔的八音盒琶音旋律 */
  musicBoxEnabled: boolean;
}

export const SPLASH_PREFS_STORAGE_KEY = 'agzh_clannad_splash_prefs_v1';
export const SPLASH_SESSION_PLAYED_KEY = 'agzh_clannad_splash_played_session';

export const DEFAULT_SPLASH_PREFS: StudioSplashPrefs = {
  studioBootEnabled: true,
  themeId: 'clannad-orbs',
  durationMs: 2600,
  musicBoxEnabled: false,
};

export const CLANNAD_SPLASH_THEMES: ClannadSplashThemeSpec[] = [
  {
    id: 'clannad-orbs',
    name: '幻想世界 · 星海光玉',
    shortName: '星海光玉',
    badge: '幻想世界篇 · 深空奇迹',
    subtitle: 'ILLUSIONARY WORLD // 小镇的心愿',
    quote: '「这座小镇，承载着无数温柔的心愿与奇迹 —— 欢迎回到工作台」',
    isLight: false,
    accent: '#f6c453',
    secondaryAccent: '#7dd3fc',
    linkedSkinId: 'clannad-illusionary-orbs',
    steps: [
      '星海微光汇聚 · 正在唤醒中文词典与核心状态...',
      '光玉缓缓升空 · 正在编织高定光学材质渲染层...',
      '奇迹星轨就绪 · 正在步入 Antigravity Studio 工作台...',
    ],
  },
  {
    id: 'clannad-sakura',
    name: '光坂坡道 · 樱吹雪与团子',
    shortName: '樱坡团子',
    badge: '学园篇 · 春樱与团子大家族',
    subtitle: 'SAKURA SLOPE // 漫长坡道的起点',
    quote: '「我们开始一起攀登，这长长的、长长的樱花坡道」',
    isLight: true,
    accent: '#e57399',
    secondaryAccent: '#81d4fa',
    linkedSkinId: 'clannad-sakura-hill',
    steps: [
      '晨曦洒满坡道 · 团子大家族正在列队唤醒服务...',
      '春樱随风旋舞 · 正在同步多账号配额与主题配置...',
      '坡道尽头重逢 · 正在轻盈展开主控制台...',
    ],
  },
  {
    id: 'clannad-sunflower',
    name: '盛夏晴空 · 汐与黄金花田',
    shortName: '晴空花田',
    badge: 'After Story · 夏日向日葵',
    subtitle: 'SUNFLOWER FIELD // 晴空下的约定',
    quote: '「在阳光洒满的黄金向日葵花田之后，去迎接崭新的每一天吧」',
    isLight: true,
    accent: '#e08e14',
    secondaryAccent: '#0284c7',
    linkedSkinId: 'clannad-after-sunflower',
    steps: [
      '夏风拂过花海 · 正在初始化本地反代与安全网关...',
      '逆光花粉飞扬 · 正在校准光学表面与伴侣遥测...',
      '晴空万里澄澈 · 准备开启今日高效创造之旅...',
    ],
  },
  {
    id: 'clannad-starfish',
    name: '旧校舍黄昏 · 海星与提琴',
    shortName: '海星提琴',
    badge: '学园篇 · 琴美与风子的纪念',
    subtitle: 'TWILIGHT LIBRARY // 弦音与海星',
    quote: '「请收下这枚小小的海星，愿温柔的旋律陪伴每一次思考」',
    isLight: false,
    accent: '#c084fc',
    secondaryAccent: '#fb923c',
    linkedSkinId: 'clannad-starfish-library',
    steps: [
      '斜阳穿过书架 · 正在加载静谧专注配色矩阵...',
      '提琴弦波流淌 · 正在校验组件与守护哨兵状态...',
      '暮色星光点亮 · 正在切入沉浸式工作空间...',
    ],
  },
];

export function normalizeSplashThemeId(raw?: string | null): ClannadSplashThemeId {
  const v = (raw || '').trim().toLowerCase();
  if (v === 'none' || v === 'off' || v === 'clean') return 'none';
  if (v === 'clannad-sakura' || v === 'sakura' || v === 'dango') return 'clannad-sakura';
  if (v === 'clannad-sunflower' || v === 'sunflower' || v === 'ushio') return 'clannad-sunflower';
  if (v === 'clannad-starfish' || v === 'starfish' || v === 'kotomi') return 'clannad-starfish';
  if (v === 'clannad-orbs' || v === 'orbs' || v === 'clannad') return 'clannad-orbs';
  return 'clannad-orbs';
}

export function getSplashThemeSpec(id?: string | null): ClannadSplashThemeSpec {
  const normalized = normalizeSplashThemeId(id);
  return (
    CLANNAD_SPLASH_THEMES.find((item) => item.id === normalized) || CLANNAD_SPLASH_THEMES[0]
  );
}

export function loadStudioSplashPrefs(): StudioSplashPrefs {
  try {
    if (typeof localStorage === 'undefined') return { ...DEFAULT_SPLASH_PREFS };
    const raw = localStorage.getItem(SPLASH_PREFS_STORAGE_KEY);
    if (!raw) return { ...DEFAULT_SPLASH_PREFS };
    const parsed = JSON.parse(raw) as Partial<StudioSplashPrefs>;
    const dur =
      parsed.durationMs === 1800 || parsed.durationMs === 2600 || parsed.durationMs === 3800
        ? parsed.durationMs
        : 2600;
    return {
      studioBootEnabled:
        typeof parsed.studioBootEnabled === 'boolean'
          ? parsed.studioBootEnabled
          : DEFAULT_SPLASH_PREFS.studioBootEnabled,
      themeId: normalizeSplashThemeId(parsed.themeId),
      durationMs: dur,
      musicBoxEnabled: Boolean(parsed.musicBoxEnabled),
    };
  } catch {
    return { ...DEFAULT_SPLASH_PREFS };
  }
}

export function saveStudioSplashPrefs(next: StudioSplashPrefs): StudioSplashPrefs {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(SPLASH_PREFS_STORAGE_KEY, JSON.stringify(next));
    }
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('studio:splash-prefs-changed', { detail: next }));
    }
  } catch {
    // 忽略存储受限环境异常
  }
  return next;
}

/**
 * 使用 WebAudio 合成清脆温暖的五声音阶八音盒琶音（灵感源自《团子大家族》与《汐》的清澈钟琴音色）
 * 返回可随时终止的清理函数，零音频文件依赖。
 */
export function playClannadMusicBox(themeId: ClannadSplashThemeId): () => void {
  if (typeof window === 'undefined' || themeId === 'none') return () => {};
  const AudioCtx =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtx) return () => {};

  let ctx: AudioContext | null = null;
  try {
    ctx = new AudioCtx();
    if (ctx.state === 'suspended') {
      ctx.resume().catch(() => {});
    }

    // 不同分镜对应的温柔五声八音盒简短动机（Hz）
    const melodies: Record<Exclude<ClannadSplashThemeId, 'none'>, number[]> = {
      // 星海光玉：空灵高八度 C5 - G5 - A5 - E5 - F5 - C6
      'clannad-orbs': [523.25, 783.99, 880.0, 659.25, 698.46, 1046.5],
      // 樱坡团子：温暖轻快 G5 - E5 - G5 - A5 - G5 - E5 - D5
      'clannad-sakura': [783.99, 659.25, 783.99, 880.0, 783.99, 659.25, 587.33],
      // 晴空花田：明朗大调 F5 - A5 - C6 - D6 - C6 - A5
      'clannad-sunflower': [698.46, 880.0, 1046.5, 1174.66, 1046.5, 880.0],
      // 海星提琴：柔美泛音 E5 - B5 - C6 - B5 - G5 - A5
      'clannad-starfish': [659.25, 987.77, 1046.5, 987.77, 783.99, 880.0],
    };

    const notes = melodies[themeId] || melodies['clannad-orbs'];
    const now = ctx.currentTime + 0.04;
    const stepSec = 0.28;

    notes.forEach((freq, idx) => {
      if (!ctx) return;
      const t0 = now + idx * stepSec;

      // 主音正弦波（温润基音）
      const oscMain = ctx.createOscillator();
      const gainMain = ctx.createGain();
      oscMain.type = 'sine';
      oscMain.frequency.setValueAtTime(freq, t0);

      gainMain.gain.setValueAtTime(0.0001, t0);
      gainMain.gain.exponentialRampToValueAtTime(0.065, t0 + 0.018);
      gainMain.gain.exponentialRampToValueAtTime(0.0001, t0 + 1.15);

      oscMain.connect(gainMain);
      gainMain.connect(ctx.destination);
      oscMain.start(t0);
      oscMain.stop(t0 + 1.2);

      // 八音盒钢片高次泛音（清脆叮咚点缀）
      const oscBell = ctx.createOscillator();
      const gainBell = ctx.createGain();
      oscBell.type = 'triangle';
      oscBell.frequency.setValueAtTime(freq * 2, t0);

      gainBell.gain.setValueAtTime(0.0001, t0);
      gainBell.gain.exponentialRampToValueAtTime(0.018, t0 + 0.01);
      gainBell.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.35);

      oscBell.connect(gainBell);
      gainBell.connect(ctx.destination);
      oscBell.start(t0);
      oscBell.stop(t0 + 0.38);
    });
  } catch {
    // 忽略音频设备未就绪异常
  }

  return () => {
    if (ctx && ctx.state !== 'closed') {
      ctx.close().catch(() => {});
    }
  };
}
