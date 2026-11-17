/**
 * 《CLANNAD》原版真曲背景音乐引擎
 * 1. 内置 4 首《CLANNAD》原动画真曲音源（《だんご大家族》《小さな手のひら》《渚·坂の下の別れ》《汐·潮鳴り》），支持任意高潮秒数切入与平滑淡入淡出
 * 2. 采用 HTMLAudioElement 流式秒开 + WebAudio API (decodeAudioData) 冷启动双通道容错架构
 * 3. 支持用户额外导入本地自定义音乐文件（MP3 / WAV / FLAC / OGG / M4A）与自定义原画剧照，通过 IndexedDB 持久化存储
 */

export type ClannadBgmTrackId =
  | 'follow-scene'
  | 'dango-family'
  | 'ushio-pocket'
  | 'nagisa-slope'
  | 'town-flow-of-time'
  | 'custom-file'
  | 'off';

export interface ClannadBgmCuePreset {
  label: string;
  offsetSec: number;
}

export interface ClannadBgmTrackMeta {
  id: Exclude<ClannadBgmTrackId, 'follow-scene' | 'custom-file' | 'off'>;
  title: string;
  subtitle: string;
  artist: string;
  instrumentLabel: string;
  moodTag: string;
  bpm: number;
  audioUrl: string;
  durationSec: number;
  cuePresets: ClannadBgmCuePreset[];
}

export interface CustomBgmStoredMeta {
  fileName: string;
  mimeType: string;
  sizeBytes: number;
  updatedAt: number;
}

export const BUILTIN_BGM_TRACKS: ClannadBgmTrackMeta[] = [
  {
    id: 'dango-family',
    title: '《だんご大家族》· 团子大家族 (原唱ED)',
    subtitle: '茶太原唱 · 麻枝准词曲 · 片尾最温暖的大家庭摇篮曲',
    artist: '茶太 / 麻枝准',
    instrumentLabel: '原动画 ED 完整原唱真曲 (04:33)',
    moodTag: '原唱真曲',
    bpm: 84,
    audioUrl: '/audio/splash/dango-family.mp3',
    durationSec: 273,
    cuePresets: [
      { label: '00:00 清唱副歌前奏', offsetSec: 0 },
      { label: '00:19 温柔主歌入唱', offsetSec: 19 },
      { label: '01:15 大家庭合唱段', offsetSec: 75 },
      { label: '02:37 全曲温暖高潮', offsetSec: 157 },
    ],
  },
  {
    id: 'ushio-pocket',
    title: '《小さな手のひら》· 小小的手心 (终章原曲)',
    subtitle: 'riya 原唱 · After Story 第 22 话催泪大结局真曲',
    artist: 'riya (eufonius) / 麻枝准',
    instrumentLabel: '原动画终章完整原唱真曲 (04:45)',
    moodTag: '封神终章',
    bpm: 76,
    audioUrl: '/audio/splash/ushio-pocket.mp3',
    durationSec: 285,
    cuePresets: [
      { label: '00:00 八音盒晶莹序奏', offsetSec: 0 },
      { label: '00:39 清澈人声主歌', offsetSec: 39 },
      { label: '01:59 催泪副歌高潮', offsetSec: 119 },
      { label: '03:20 终章释怀尾奏', offsetSec: 200 },
    ],
  },
  {
    id: 'nagisa-slope',
    title: '《渚 · 坂の下の別れ》· 光坂坡道重逢原曲',
    subtitle: '古河渚主题原曲 · 漫长春樱坡道上的初遇与回眸',
    artist: '麻枝准 (Key Sounds Label)',
    instrumentLabel: '原版 OST 纯钢琴重逢原曲 (01:51)',
    moodTag: '春樱原声',
    bpm: 92,
    audioUrl: '/audio/splash/nagisa-slope.mp3',
    durationSec: 111,
    cuePresets: [
      { label: '00:00 经典坡道主旋律', offsetSec: 0 },
      { label: '00:20 温暖和声展开', offsetSec: 20 },
      { label: '00:54 坡道回眸变奏', offsetSec: 54 },
    ],
  },
  {
    id: 'town-flow-of-time',
    title: '《汐 · 潮鳴り》· 幻想星海原版 OST',
    subtitle: '冈崎汐与幻想世界原声组曲 · 星海光玉与海星的约定',
    artist: '戸越まごめ / 麻枝准',
    instrumentLabel: '原版 OST 幻想星海组曲 (03:54)',
    moodTag: '星海原声',
    bpm: 72,
    audioUrl: '/audio/splash/town-flow-of-time.mp3',
    durationSec: 234,
    cuePresets: [
      { label: '00:00 空灵水晶前奏', offsetSec: 0 },
      { label: '00:19 《汐》钢琴主旋律', offsetSec: 19 },
      { label: '01:16 星海弦乐高潮', offsetSec: 76 },
      { label: '02:15 《潮鳴り》乐章', offsetSec: 135 },
    ],
  },
];

export function getBuiltinBgmTrackMeta(
  trackId: Exclude<ClannadBgmTrackId, 'follow-scene' | 'custom-file' | 'off'>,
): ClannadBgmTrackMeta {
  return BUILTIN_BGM_TRACKS.find((t) => t.id === trackId) || BUILTIN_BGM_TRACKS[0];
}

// ======================== IndexedDB 自定义本地音乐与截图持久化 ========================

const IDB_NAME = 'agzh_clannad_bgm_db_v1';
const IDB_STORE = 'custom_tracks';
const IDB_KEY = 'primary_bgm';
const IDB_ARTWORK_KEY = 'primary_artwork';
export const CUSTOM_BGM_META_STORAGE_KEY = 'agzh_clannad_custom_bgm_meta_v1';
export const CUSTOM_ARTWORK_META_STORAGE_KEY = 'agzh_clannad_custom_artwork_meta_v1';

interface StoredBgmRecord {
  blob: Blob;
  meta: CustomBgmStoredMeta;
}

function openBgmDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('当前环境不支持 IndexedDB 本地音频仓库'));
      return;
    }
    const req = indexedDB.open(IDB_NAME, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(IDB_STORE)) {
        db.createObjectStore(IDB_STORE);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error || new Error('打开本地音频数据库失败'));
  });
}

export function loadCustomBgmMetaSync(): CustomBgmStoredMeta | null {
  try {
    if (typeof localStorage === 'undefined') return null;
    const raw = localStorage.getItem(CUSTOM_BGM_META_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<CustomBgmStoredMeta>;
    if (!parsed.fileName || typeof parsed.sizeBytes !== 'number') return null;
    return {
      fileName: parsed.fileName,
      mimeType: parsed.mimeType || 'audio/mpeg',
      sizeBytes: parsed.sizeBytes,
      updatedAt: parsed.updatedAt || Date.now(),
    };
  } catch {
    return null;
  }
}

export async function saveCustomBgmFile(file: File): Promise<CustomBgmStoredMeta> {
  if (file.size <= 0) {
    throw new Error('所选音频文件为空');
  }
  if (file.size > 45 * 1024 * 1024) {
    throw new Error('音频文件请控制在 45MB 以内以保证秒级启动响应');
  }

  const meta: CustomBgmStoredMeta = {
    fileName: file.name,
    mimeType: file.type || 'audio/mpeg',
    sizeBytes: file.size,
    updatedAt: Date.now(),
  };

  const db = await openBgmDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(IDB_STORE, 'readwrite');
    const store = tx.objectStore(IDB_STORE);
    store.put({ blob: file, meta } satisfies StoredBgmRecord, IDB_KEY);
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error || new Error('保存音频至 IndexedDB 失败'));
    };
  });

  try {
    localStorage.setItem(CUSTOM_BGM_META_STORAGE_KEY, JSON.stringify(meta));
  } catch {
    // 忽略受限存储异常
  }

  return meta;
}

export async function clearCustomBgmFile(): Promise<void> {
  try {
    localStorage.removeItem(CUSTOM_BGM_META_STORAGE_KEY);
  } catch {
    // 忽略
  }
  try {
    const db = await openBgmDb();
    await new Promise<void>((resolve) => {
      const tx = db.transaction(IDB_STORE, 'readwrite');
      tx.objectStore(IDB_STORE).delete(IDB_KEY);
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
      tx.onerror = () => {
        db.close();
        resolve();
      };
    });
  } catch {
    // 忽略
  }
}

async function loadCustomBgmBlob(): Promise<Blob | null> {
  try {
    const db = await openBgmDb();
    return await new Promise<Blob | null>((resolve) => {
      const tx = db.transaction(IDB_STORE, 'readonly');
      const req = tx.objectStore(IDB_STORE).get(IDB_KEY);
      req.onsuccess = () => {
        db.close();
        const record = req.result as StoredBgmRecord | undefined;
        resolve(record?.blob || null);
      };
      req.onerror = () => {
        db.close();
        resolve(null);
      };
    });
  } catch {
    return null;
  }
}

export function loadCustomArtworkMetaSync(): CustomBgmStoredMeta | null {
  try {
    if (typeof localStorage === 'undefined') return null;
    const raw = localStorage.getItem(CUSTOM_ARTWORK_META_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<CustomBgmStoredMeta>;
    if (!parsed.fileName || typeof parsed.sizeBytes !== 'number') return null;
    return {
      fileName: parsed.fileName,
      mimeType: parsed.mimeType || 'image/png',
      sizeBytes: parsed.sizeBytes,
      updatedAt: parsed.updatedAt || Date.now(),
    };
  } catch {
    return null;
  }
}

export async function saveCustomArtworkFile(file: File): Promise<CustomBgmStoredMeta> {
  if (file.size <= 0) {
    throw new Error('所选图片文件为空');
  }
  if (file.size > 25 * 1024 * 1024) {
    throw new Error('画面截图请控制在 25MB 以内');
  }

  const meta: CustomBgmStoredMeta = {
    fileName: file.name,
    mimeType: file.type || 'image/png',
    sizeBytes: file.size,
    updatedAt: Date.now(),
  };

  const db = await openBgmDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(IDB_STORE, 'readwrite');
    tx.objectStore(IDB_STORE).put({ blob: file, meta } satisfies StoredBgmRecord, IDB_ARTWORK_KEY);
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error || new Error('保存自定义截图失败'));
    };
  });

  try {
    localStorage.setItem(CUSTOM_ARTWORK_META_STORAGE_KEY, JSON.stringify(meta));
  } catch {
    // 忽略
  }
  return meta;
}

export async function loadCustomArtworkBlob(): Promise<Blob | null> {
  try {
    const db = await openBgmDb();
    return await new Promise<Blob | null>((resolve) => {
      const tx = db.transaction(IDB_STORE, 'readonly');
      const req = tx.objectStore(IDB_STORE).get(IDB_ARTWORK_KEY);
      req.onsuccess = () => {
        db.close();
        const record = req.result as StoredBgmRecord | undefined;
        resolve(record?.blob || null);
      };
      req.onerror = () => {
        db.close();
        resolve(null);
      };
    });
  } catch {
    return null;
  }
}

export async function clearCustomArtworkFile(): Promise<void> {
  try {
    localStorage.removeItem(CUSTOM_ARTWORK_META_STORAGE_KEY);
  } catch {
    // 忽略
  }
  try {
    const db = await openBgmDb();
    await new Promise<void>((resolve) => {
      const tx = db.transaction(IDB_STORE, 'readwrite');
      tx.objectStore(IDB_STORE).delete(IDB_ARTWORK_KEY);
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
      tx.onerror = () => {
        db.close();
        resolve();
      };
    });
  } catch {
    // 忽略
  }
}

// ======================== 全局单例防叠音播放调度器 ========================

let activeStopHandle: (() => void) | null = null;
const decodedAudioBufferCache = new Map<string, AudioBuffer>();

export function stopActiveSplashBgm(): void {
  if (activeStopHandle) {
    const fn = activeStopHandle;
    activeStopHandle = null;
    fn();
  }
}

export interface StartSplashBgmOptions {
  trackId: Exclude<ClannadBgmTrackId, 'follow-scene'>;
  volume?: number;
  startOffsetSec?: number;
  loop?: boolean;
  fallbackTrackId?: Exclude<ClannadBgmTrackId, 'follow-scene' | 'custom-file' | 'off'>;
}

/**
 * WebAudio 硬解码回退通道（当冷启动无鼠标手势导致 HTMLAudioElement.play 被浏览器拦截时无缝接管）
 */
function playViaWebAudioBuffer(
  cacheKey: string,
  loader: () => Promise<ArrayBuffer>,
  targetVolume: number,
  startOffsetSec: number,
  loop: boolean,
): () => void {
  const AudioCtx =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtx) return () => {};

  let stopped = false;
  let ctx: AudioContext | null = null;
  let sourceNode: AudioBufferSourceNode | null = null;
  let gainNode: GainNode | null = null;

  try {
    ctx = new AudioCtx();
    const currentCtx = ctx;
    const unlock = () => {
      if (!stopped && currentCtx.state === 'suspended') {
        currentCtx.resume().catch(() => {});
      }
    };
    if (currentCtx.state === 'suspended') {
      unlock();
      window.addEventListener('pointerdown', unlock, { once: true });
      window.addEventListener('keydown', unlock, { once: true });
    }

    gainNode = currentCtx.createGain();
    gainNode.gain.setValueAtTime(0.0001, currentCtx.currentTime);
    gainNode.gain.linearRampToValueAtTime(targetVolume, currentCtx.currentTime + 0.32);
    gainNode.connect(currentCtx.destination);

    const mountBuffer = (audioBuffer: AudioBuffer) => {
      if (stopped || currentCtx.state === 'closed' || !gainNode) return;
      const src = currentCtx.createBufferSource();
      src.buffer = audioBuffer;
      src.loop = loop;
      src.connect(gainNode);
      const safeOffset =
        audioBuffer.duration > 1
          ? Math.max(0, Math.min(startOffsetSec, audioBuffer.duration - 0.5))
          : 0;
      src.start(0, safeOffset);
      sourceNode = src;
    };

    const cached = decodedAudioBufferCache.get(cacheKey);
    if (cached) {
      mountBuffer(cached);
    } else {
      loader()
        .then((raw) => {
          if (stopped || currentCtx.state === 'closed') return null;
          return currentCtx.decodeAudioData(raw.slice(0));
        })
        .then((decoded) => {
          if (!decoded) return;
          decodedAudioBufferCache.set(cacheKey, decoded);
          mountBuffer(decoded);
        })
        .catch(() => {});
    }

    return () => {
      if (stopped) return;
      stopped = true;
      window.removeEventListener('pointerdown', unlock);
      window.removeEventListener('keydown', unlock);
      if (gainNode && currentCtx.state !== 'closed') {
        try {
          const now = currentCtx.currentTime;
          gainNode.gain.cancelScheduledValues(now);
          gainNode.gain.setValueAtTime(Math.max(0.0001, gainNode.gain.value), now);
          gainNode.gain.exponentialRampToValueAtTime(0.0001, now + 0.28);
        } catch {
          // 忽略关闭渐变异常
        }
      }
      window.setTimeout(() => {
        try {
          sourceNode?.stop();
        } catch {
          // 忽略
        }
        if (currentCtx.state !== 'closed') {
          currentCtx.close().catch(() => {});
        }
      }, 310);
    };
  } catch {
    if (ctx && ctx.state !== 'closed') {
      ctx.close().catch(() => {});
    }
    return () => {};
  }
}

/**
 * 播放指定 URL 原曲音频（流式秒播优先 + 冷启动 WebAudio 自动接管 + 320ms 柔和淡入淡出）
 */
function playStreamedAudioUrl(
  url: string,
  targetVolume: number,
  startOffsetSec: number,
  loop: boolean,
  revokeOnStop = false,
): () => void {
  let cancelled = false;
  let fadeTimer: number | null = null;
  let webAudioCleanup: (() => void) | null = null;
  let audioEl: HTMLAudioElement | null = new Audio(url);

  audioEl.loop = loop;
  audioEl.preload = 'auto';
  audioEl.volume = 0.01;

  const seekOffset = Math.max(0, startOffsetSec);

  const startFadeIn = () => {
    let step = 0;
    const steps = 8;
    fadeTimer = window.setInterval(() => {
      step += 1;
      if (!audioEl || cancelled) {
        if (fadeTimer) window.clearInterval(fadeTimer);
        return;
      }
      audioEl.volume = Math.min(targetVolume, (targetVolume * step) / steps);
      if (step >= steps && fadeTimer) {
        window.clearInterval(fadeTimer);
        fadeTimer = null;
      }
    }, 40);
  };

  const launchPlayback = () => {
    if (cancelled || !audioEl) return;
    if (seekOffset > 0 && Number.isFinite(audioEl.duration) && seekOffset < audioEl.duration - 0.5) {
      try {
        audioEl.currentTime = seekOffset;
      } catch {
        // 忽略游标异常
      }
    }

    audioEl
      .play()
      .then(() => {
        if (!cancelled) startFadeIn();
      })
      .catch(() => {
        if (cancelled) return;
        // 冷启动无交互手势导致 HTMLAudioElement 被拦截时，立即无缝切换至 WebAudio 硬件混音通道
        if (audioEl) {
          audioEl.pause();
          audioEl.src = '';
          audioEl = null;
        }
        webAudioCleanup = playViaWebAudioBuffer(
          url,
          () => fetch(url).then((r) => r.arrayBuffer()),
          targetVolume,
          seekOffset,
          loop,
        );
      });
  };

  if (seekOffset > 0) {
    audioEl.addEventListener('loadedmetadata', launchPlayback, { once: true });
  } else {
    launchPlayback();
  }

  return () => {
    if (cancelled) return;
    cancelled = true;
    if (fadeTimer) {
      window.clearInterval(fadeTimer);
      fadeTimer = null;
    }
    if (webAudioCleanup) {
      webAudioCleanup();
      webAudioCleanup = null;
    }
    if (audioEl) {
      const el = audioEl;
      audioEl = null;
      const startVol = el.volume;
      let step = 0;
      const steps = 7;
      const outTimer = window.setInterval(() => {
        step += 1;
        el.volume = Math.max(0, startVol * (1 - step / steps));
        if (step >= steps) {
          window.clearInterval(outTimer);
          el.pause();
          el.src = '';
          if (revokeOnStop) URL.revokeObjectURL(url);
        }
      }, 42);
    } else if (revokeOnStop) {
      URL.revokeObjectURL(url);
    }
  };
}

/**
 * 启动指定背景音乐（自动终止上一段残留播放，内置 4 首《CLANNAD》原版真曲与自定义本地音频均支持高潮偏移秒切）
 */
export function startSplashBgm(options: StartSplashBgmOptions): () => void {
  stopActiveSplashBgm();

  if (typeof window === 'undefined' || options.trackId === 'off') {
    return () => {};
  }

  const targetVolume = Math.max(0.05, Math.min(1, options.volume ?? 0.7));
  const seekOffset = Math.max(0, options.startOffsetSec ?? 0);
  const loop = options.loop ?? true;

  if (options.trackId === 'custom-file') {
    let cancelled = false;
    let innerCleanup: (() => void) | null = null;

    loadCustomBgmBlob().then((blob) => {
      if (cancelled) return;
      if (!blob) {
        const fbMeta = getBuiltinBgmTrackMeta(options.fallbackTrackId || 'ushio-pocket');
        innerCleanup = playStreamedAudioUrl(fbMeta.audioUrl, targetVolume, 0, loop, false);
        return;
      }
      const blobUrl = URL.createObjectURL(blob);
      innerCleanup = playStreamedAudioUrl(blobUrl, targetVolume, seekOffset, loop, true);
    });

    const stopCustom = () => {
      if (cancelled) return;
      cancelled = true;
      if (innerCleanup) {
        innerCleanup();
        innerCleanup = null;
      }
    };
    activeStopHandle = stopCustom;
    return stopCustom;
  }

  const meta = getBuiltinBgmTrackMeta(options.trackId);
  const stopBuiltin = playStreamedAudioUrl(meta.audioUrl, targetVolume, seekOffset, loop, false);
  activeStopHandle = stopBuiltin;
  return stopBuiltin;
}
