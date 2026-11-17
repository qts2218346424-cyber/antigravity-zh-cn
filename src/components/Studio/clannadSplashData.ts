import type { ClannadBgmTrackId } from './clannadAudioEngine';

export type ClannadSplashThemeId =
  | 'clannad-sunflower'
  | 'clannad-sakura'
  | 'clannad-orbs'
  | 'clannad-starfish'
  | 'none';

export type SplashDurationOption = 1800 | 2600 | 3800 | 4800 | 8000 | 12000;

export interface ClannadDialogueLine {
  speaker: string;
  zh: string;
  en: string;
}

export interface ClannadCameraMotion {
  fromScale: number;
  toScale: number;
  panXPercent: number;
  panYPercent: number;
}

export interface ClannadSplashThemeSpec {
  id: Exclude<ClannadSplashThemeId, 'none'>;
  name: string;
  shortName: string;
  episodeTag: string;
  badge: string;
  subtitle: string;
  quote: string;
  artworkUrl: string;
  recommendedBgmId: Exclude<ClannadBgmTrackId, 'follow-scene' | 'custom-file' | 'off'>;
  cameraMotion: ClannadCameraMotion;
  dialogues: [ClannadDialogueLine, ClannadDialogueLine, ClannadDialogueLine];
  isLight: boolean;
  accent: string;
  secondaryAccent: string;
  linkedSkinId: string;
  steps: [string, string, string];
}

export interface StudioSplashPrefs {
  /** 是否在打开 Antigravity Studio 主窗口时展示启动序幕动画 */
  studioBootEnabled: boolean;
  /** 当前选定的启动动画名场面主题 */
  themeId: ClannadSplashThemeId;
  /** 是否在每次启动时随机轮播四大感人名场面 */
  randomSceneOnBoot?: boolean;
  /** 序幕展示时长（毫秒） */
  durationMs: SplashDurationOption;
  /** 是否开启背景音乐伴奏（与 bgmTrackId 双向兼容） */
  musicBoxEnabled: boolean;
  /** 选定的背景音乐模式或曲目 ID */
  bgmTrackId?: ClannadBgmTrackId;
  /** 背景音乐音量 (0.05 ~ 1.0) */
  bgmVolume?: number;
  /** 自定义本地音乐的起始播放偏移秒数（可直接切入副歌高潮） */
  bgmStartOffsetSec?: number;
  /** 是否启用 2.35:1 电影院宽银幕黑边遮幅 */
  cinemaLetterbox?: boolean;
}

export const SPLASH_PREFS_STORAGE_KEY = 'agzh_clannad_splash_prefs_v1';
export const SPLASH_SESSION_PLAYED_KEY = 'agzh_clannad_splash_played_session';

export const DEFAULT_SPLASH_PREFS: StudioSplashPrefs = {
  studioBootEnabled: true,
  themeId: 'clannad-sunflower',
  randomSceneOnBoot: false,
  durationMs: 4800,
  musicBoxEnabled: true,
  bgmTrackId: 'follow-scene',
  bgmVolume: 0.7,
  bgmStartOffsetSec: 0,
  cinemaLetterbox: true,
};

export const CLANNAD_SPLASH_THEMES: ClannadSplashThemeSpec[] = [
  {
    id: 'clannad-sunflower',
    name: '盛夏花海 · 在爸爸怀里哭泣',
    shortName: '花海重逢',
    episodeTag: 'CLANNAD ~After Story~ · EP.18「大地の果て」',
    badge: '动画史封神回 · 黄金向日葵花田父女相拥',
    subtitle: 'EPISODE 18 // THE ENDS OF THE EARTH',
    quote: '「早苗阿姨说过……能哭的地方，只有厕所，和爸爸的怀里。」',
    artworkUrl: '/images/splash/scene-sunflower.webp',
    recommendedBgmId: 'ushio-pocket',
    cameraMotion: {
      fromScale: 1.02,
      toScale: 1.11,
      panXPercent: -1.2,
      panYPercent: -0.8,
    },
    dialogues: [
      {
        speaker: '冈崎汐',
        zh: '「早苗阿姨说过……能哭的地方，只有厕所，和爸爸的怀里。」',
        en: "Sanae-san told me... the only places I can cry are the bathroom, and in Daddy's arms.",
      },
      {
        speaker: '冈崎朋也',
        zh: '「对不起，汐……爸爸一直都在逃避，让你孤单忍耐了这么久。」',
        en: 'Forgive me, Ushio... From this moment on, Daddy will never let go of your little hand.',
      },
      {
        speaker: '花田微风',
        zh: '「在那片阳光洒满的黄金向日葵花海之后，我们终于重新成为了家人。」',
        en: 'Beyond the endless golden sea of sunflowers, our warmth begins anew.',
      },
    ],
    isLight: true,
    accent: '#fbbf24',
    secondaryAccent: '#38bdf8',
    linkedSkinId: 'clannad-after-sunflower',
    steps: [
      '夏风拂过黄金花海 · 正在唤醒核心服务与多账号网关...',
      '草帽与小机器人就位 · 正在校准高定光学材质与伴侣状态...',
      '晴空万里澄澈如初 · 正在为您展开主工作台...',
    ],
  },
  {
    id: 'clannad-sakura',
    name: '光坂坡道 · 樱花雨中的初遇与回眸',
    shortName: '樱坡初遇',
    episodeTag: 'CLANNAD · EP.01 & EP.22「桜並木の坂道」',
    badge: '命运起点 · 漫长樱花坡道上的驻足重逢',
    subtitle: 'SAKURA SLOPE // WHERE OUR STORY BEGAN',
    quote: '「无论重来多少次，我依然会在洒满春樱的坡道上喊出你的名字。」',
    artworkUrl: '/images/splash/scene-sakura.webp',
    recommendedBgmId: 'nagisa-slope',
    cameraMotion: {
      fromScale: 1.03,
      toScale: 1.12,
      panXPercent: 1.1,
      panYPercent: -1.0,
    },
    dialogues: [
      {
        speaker: '古河渚',
        zh: '「你喜欢这所学校吗？……我非常、非常喜欢这里，尽管一切都在慢慢改变。」',
        en: 'Do you like this school? I love it dearly, even though everything slowly changes.',
      },
      {
        speaker: '冈崎朋也',
        zh: '「就算曾经迷茫停滞，只要想到你在坡道上等我，我便从未后悔那天与你相遇。」',
        en: 'Even if time rewound a thousand times, I would still call out to you on this hill.',
      },
      {
        speaker: '春樱序曲',
        zh: '「走吧 —— 让我们一起攀登，这长长的、盛满春光的樱花坡道。」',
        en: "Let's climb this long, sunlit cherry-blossom slope together once again.",
      },
    ],
    isLight: true,
    accent: '#f472b6',
    secondaryAccent: '#7dd3fc',
    linkedSkinId: 'clannad-sakura-hill',
    steps: [
      '晨曦穿透满开春樱 · 正在加载中文词典与语义规则...',
      '落樱随微风轻舞 · 正在同步配额面板与主题表面...',
      '坡道尽头重逢 · 正在轻盈切入控制台空间...',
    ],
  },
  {
    id: 'clannad-orbs',
    name: '幻想世界 · 漫天升腾的心愿光玉',
    shortName: '星海光玉',
    episodeTag: 'CLANNAD ~After Story~ · EP.22「小さなてのひら」',
    badge: '终章奇迹 · 跨越时空守护小镇的星海光玉',
    subtitle: 'ILLUSIONARY WORLD // WISHES OF THE TOWN',
    quote: '「每一颗缓缓升向银河的光玉，都是小镇里人们用真心守护过的幸福。」',
    artworkUrl: '/images/splash/scene-orbs.webp',
    recommendedBgmId: 'dango-family',
    cameraMotion: {
      fromScale: 1.02,
      toScale: 1.1,
      panXPercent: 0.8,
      panYPercent: -1.4,
    },
    dialogues: [
      {
        speaker: '幻想世界少女',
        zh: '「这座小镇就像一个温暖的大家庭，承载着所有欢笑、泪水与心愿。」',
        en: 'This town is like one big family, holding every gentle wish and tear.',
      },
      {
        speaker: '星海回响',
        zh: '「呐，我已经全部想起来了……每一颗光玉，都是大家拼命守护的奇迹。」',
        en: 'Look up at the Milky Way—countless warm lights of happiness are rising.',
      },
      {
        speaker: '小小手心',
        zh: '「愿漫天汇聚的星海微光，守护你今天每一次专注与创造。」',
        en: 'May these gathered lights illuminate every line of thought in your studio.',
      },
    ],
    isLight: false,
    accent: '#f6c453',
    secondaryAccent: '#7dd3fc',
    linkedSkinId: 'clannad-illusionary-orbs',
    steps: [
      '星海微光缓缓汇聚 · 正在唤醒核心运行时与状态机...',
      '心愿光玉升向银河 · 正在编织高定液态光学渲染层...',
      '跨越时空的奇迹就绪 · 欢迎回到 Antigravity Studio...',
    ],
  },
  {
    id: 'clannad-starfish',
    name: '木雕海星的约定 · 直到梦的尽头',
    shortName: '风子海星',
    episodeTag: 'CLANNAD · EP.09「夢の最後まで」',
    badge: '学园催泪篇 · 风子双手递出木雕海星的心意',
    subtitle: 'UNTIL THE END OF THE DREAM // WOODEN STARFISH',
    quote: '「请收下这枚风子亲手雕刻的海星！哪怕有一天梦醒了，祝福也会永远留下……」',
    artworkUrl: '/images/splash/scene-starfish.webp',
    recommendedBgmId: 'town-flow-of-time',
    cameraMotion: {
      fromScale: 1.02,
      toScale: 1.09,
      panXPercent: -0.8,
      panYPercent: -0.5,
    },
    dialogues: [
      {
        speaker: '伊吹风子',
        zh: '「请收下这枚风子亲手雕刻的海星！哪怕梦醒后被大家遗忘，这份祝福也会留下……」',
        en: 'Please accept this carved starfish! Even when the dream fades, my wish remains.',
      },
      {
        speaker: '古河渚',
        zh: '「就算记忆暂时沉睡，掌心里木雕海星的温暖，一定会让大家在婚礼那天重逢。」',
        en: 'Even if memories sleep for a while, the warmth in our palms will reunite us.',
      },
      {
        speaker: '微风心愿',
        zh: '「愿这份笨拙却真挚的温柔，陪伴你今天每一次沉静思考与创造。」',
        en: 'May this sincere, gentle wish accompany every quiet moment in your workspace.',
      },
    ],
    isLight: false,
    accent: '#c084fc',
    secondaryAccent: '#fb923c',
    linkedSkinId: 'clannad-starfish-library',
    steps: [
      '校舍长廊微风轻拂 · 正在加载静谧护眼色彩矩阵...',
      '木雕海星传递祝福 · 正在校验组件与守护哨兵服务...',
      '温柔奇迹悄然点亮 · 正在进入沉浸式创作空间...',
    ],
  },
];

const VALID_DURATIONS = new Set<SplashDurationOption>([1800, 2600, 3800, 4800, 8000, 12000]);
const VALID_BGM_IDS = new Set<ClannadBgmTrackId>([
  'follow-scene',
  'dango-family',
  'ushio-pocket',
  'nagisa-slope',
  'town-flow-of-time',
  'custom-file',
  'off',
]);

export function normalizeSplashThemeId(raw?: string | null): ClannadSplashThemeId {
  const v = (raw || '').trim().toLowerCase();
  if (v === 'none' || v === 'off' || v === 'clean') return 'none';
  if (v === 'clannad-sakura' || v === 'sakura' || v === 'dango' || v === 'nagisa') {
    return 'clannad-sakura';
  }
  if (v === 'clannad-sunflower' || v === 'sunflower' || v === 'ushio') {
    return 'clannad-sunflower';
  }
  if (v === 'clannad-starfish' || v === 'starfish' || v === 'kotomi' || v === 'fuko') {
    return 'clannad-starfish';
  }
  if (v === 'clannad-orbs' || v === 'orbs' || v === 'clannad') {
    return 'clannad-orbs';
  }
  return 'clannad-orbs';
}

export function getSplashThemeSpec(id?: string | null): ClannadSplashThemeSpec {
  const normalized = normalizeSplashThemeId(id);
  return (
    CLANNAD_SPLASH_THEMES.find((item) => item.id === normalized) || CLANNAD_SPLASH_THEMES[0]
  );
}

export function pickBootSceneThemeId(prefs: StudioSplashPrefs): ClannadSplashThemeId {
  if (!prefs.studioBootEnabled || prefs.themeId === 'none') return 'none';
  if (prefs.randomSceneOnBoot) {
    const idx = Math.floor(Math.random() * CLANNAD_SPLASH_THEMES.length);
    return CLANNAD_SPLASH_THEMES[idx].id;
  }
  return prefs.themeId;
}

export function resolveEffectiveBgmTrack(
  prefs: Pick<StudioSplashPrefs, 'musicBoxEnabled' | 'bgmTrackId'>,
  themeId: ClannadSplashThemeId,
): Exclude<ClannadBgmTrackId, 'follow-scene'> {
  if (themeId === 'none' || !prefs.musicBoxEnabled || prefs.bgmTrackId === 'off') {
    return 'off';
  }
  const track = prefs.bgmTrackId || 'follow-scene';
  if (track === 'follow-scene') {
    return getSplashThemeSpec(themeId).recommendedBgmId;
  }
  return track;
}

export function loadStudioSplashPrefs(): StudioSplashPrefs {
  try {
    if (typeof localStorage === 'undefined') return { ...DEFAULT_SPLASH_PREFS };
    const raw = localStorage.getItem(SPLASH_PREFS_STORAGE_KEY);
    if (!raw) return { ...DEFAULT_SPLASH_PREFS };
    const parsed = JSON.parse(raw) as Partial<StudioSplashPrefs>;

    const dur = VALID_DURATIONS.has(parsed.durationMs as SplashDurationOption)
      ? (parsed.durationMs as SplashDurationOption)
      : DEFAULT_SPLASH_PREFS.durationMs;

    const musicEnabled =
      typeof parsed.musicBoxEnabled === 'boolean'
        ? parsed.musicBoxEnabled
        : DEFAULT_SPLASH_PREFS.musicBoxEnabled;

    let bgmTrackId: ClannadBgmTrackId = VALID_BGM_IDS.has(parsed.bgmTrackId as ClannadBgmTrackId)
      ? (parsed.bgmTrackId as ClannadBgmTrackId)
      : musicEnabled
        ? 'follow-scene'
        : 'off';

    if (!musicEnabled && bgmTrackId !== 'off') {
      bgmTrackId = 'off';
    } else if (musicEnabled && bgmTrackId === 'off') {
      bgmTrackId = 'follow-scene';
    }

    const vol =
      typeof parsed.bgmVolume === 'number' && Number.isFinite(parsed.bgmVolume)
        ? Math.max(0.05, Math.min(1, parsed.bgmVolume))
        : DEFAULT_SPLASH_PREFS.bgmVolume;

    const startOffset =
      typeof parsed.bgmStartOffsetSec === 'number' && Number.isFinite(parsed.bgmStartOffsetSec)
        ? Math.max(0, Math.min(600, parsed.bgmStartOffsetSec))
        : 0;

    return {
      studioBootEnabled:
        typeof parsed.studioBootEnabled === 'boolean'
          ? parsed.studioBootEnabled
          : DEFAULT_SPLASH_PREFS.studioBootEnabled,
      themeId: normalizeSplashThemeId(parsed.themeId),
      randomSceneOnBoot: Boolean(parsed.randomSceneOnBoot),
      durationMs: dur,
      musicBoxEnabled: musicEnabled,
      bgmTrackId,
      bgmVolume: vol,
      bgmStartOffsetSec: startOffset,
      cinemaLetterbox:
        typeof parsed.cinemaLetterbox === 'boolean' ? parsed.cinemaLetterbox : true,
    };
  } catch {
    return { ...DEFAULT_SPLASH_PREFS };
  }
}

export function saveStudioSplashPrefs(next: StudioSplashPrefs): StudioSplashPrefs {
  const normalizedMusicEnabled =
    next.bgmTrackId !== undefined ? next.bgmTrackId !== 'off' && next.musicBoxEnabled : next.musicBoxEnabled;
  const normalizedTrackId: ClannadBgmTrackId = !normalizedMusicEnabled
    ? 'off'
    : next.bgmTrackId && next.bgmTrackId !== 'off'
      ? next.bgmTrackId
      : 'follow-scene';

  const sanitized: StudioSplashPrefs = {
    ...next,
    musicBoxEnabled: normalizedMusicEnabled,
    bgmTrackId: normalizedTrackId,
    bgmVolume: Math.max(0.05, Math.min(1, next.bgmVolume ?? 0.7)),
    bgmStartOffsetSec: Math.max(0, Math.min(600, next.bgmStartOffsetSec ?? 0)),
    cinemaLetterbox: next.cinemaLetterbox ?? true,
  };

  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(SPLASH_PREFS_STORAGE_KEY, JSON.stringify(sanitized));
    }
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('studio:splash-prefs-changed', { detail: sanitized }));
    }
  } catch {
    // 忽略存储受限环境异常
  }
  return sanitized;
}
