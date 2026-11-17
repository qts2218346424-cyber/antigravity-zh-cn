/**
 * 《CLANNAD》名场面背景音乐双模引擎
 * 1. 内置 4 首多小节双声部治愈器乐编曲（八音盒 / 抒情钢琴 / 樱坂二重奏 / 星海竖琴，带混响与柔和弦乐铺底）
 * 2. 支持用户导入本地原声音乐文件（MP3 / WAV / FLAC / OGG / M4A），通过 IndexedDB 持久化存储并支持指定副歌起始秒数与平滑淡入淡出
 */

export type ClannadBgmTrackId =
  | 'follow-scene'
  | 'dango-family'
  | 'ushio-pocket'
  | 'nagisa-slope'
  | 'town-flow-of-time'
  | 'custom-file'
  | 'off';

export interface ClannadBgmTrackMeta {
  id: Exclude<ClannadBgmTrackId, 'follow-scene' | 'custom-file' | 'off'>;
  title: string;
  subtitle: string;
  instrumentLabel: string;
  moodTag: string;
  bpm: number;
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
    title: '团子大家族 · 暖夜八音盒慢板',
    subtitle: '致敬片尾最温暖的大家庭摇篮曲',
    instrumentLabel: '清脆钢片八音盒 + 温暖分解和弦',
    moodTag: '温馨治愈',
    bpm: 84,
  },
  {
    id: 'ushio-pocket',
    title: '小小的手心 · 晴空花海钢琴曲',
    subtitle: '致敬第 18 / 22 话黄金向日葵花田重逢',
    instrumentLabel: '抒情三角钢琴 + 暖色大调弦乐',
    moodTag: '催泪释怀',
    bpm: 76,
  },
  {
    id: 'nagisa-slope',
    title: '樱坂微风 · 光坂坡道重逢曲',
    subtitle: '致敬漫长樱花坡道上的初遇与回眸',
    instrumentLabel: '钟琴与温润电钢琴三拍子二重奏',
    moodTag: '春樱悸动',
    bpm: 92,
  },
  {
    id: 'town-flow-of-time',
    title: '星海潮鸣 · 幻想世界光玉竖琴',
    subtitle: '致敬幻想世界漫天升腾的心愿光玉与旧书室回忆',
    instrumentLabel: '空灵泛音竖琴 + 深空柔弦铺底',
    moodTag: '空灵深邃',
    bpm: 72,
  },
];

interface MelodyEvent {
  /** 距离小节/乐段起点的拍数 */
  beat: number;
  /** MIDI 音高（60 = C4, 72 = C5） */
  midi: number;
  /** 持续拍数 */
  dur: number;
  /** 相对力度 (0.1 ~ 1.0) */
  vel?: number;
}

interface ChordPadEvent {
  beat: number;
  midis: number[];
  dur: number;
}

interface ScoreDefinition {
  bpm: number;
  timbre: 'celesta' | 'piano' | 'duet' | 'harp';
  totalBeats: number;
  melody: MelodyEvent[];
  chords: ChordPadEvent[];
}

function midiToFreq(midi: number): number {
  return 440 * Math.pow(2, (midi - 69) / 12);
}

/**
 * 精心编配的 4 首完整多小节双声部王道治愈和声乐谱（每首约 18~24 秒，支持无缝循环）
 */
const SCORES: Record<Exclude<ClannadBgmTrackId, 'follow-scene' | 'custom-file' | 'off'>, ScoreDefinition> = {
  // 1. 团子大家族意象：A 自然小调 / C 大调温暖五声八音盒摇篮曲 (32 拍)
  'dango-family': {
    bpm: 84,
    timbre: 'celesta',
    totalBeats: 32,
    melody: [
      // 第 1-2 小节：温柔唤起
      { beat: 0, midi: 76, dur: 1.5, vel: 0.85 },
      { beat: 1.5, midi: 79, dur: 0.5, vel: 0.72 },
      { beat: 2, midi: 81, dur: 1.5, vel: 0.92 },
      { beat: 3.5, midi: 79, dur: 0.5, vel: 0.7 },
      { beat: 4, midi: 76, dur: 1.0, vel: 0.82 },
      { beat: 5, midi: 74, dur: 1.0, vel: 0.78 },
      { beat: 6, midi: 72, dur: 2.0, vel: 0.85 },
      // 第 3-4 小节：依偎回应
      { beat: 8, midi: 74, dur: 1.0, vel: 0.8 },
      { beat: 9, midi: 76, dur: 1.0, vel: 0.84 },
      { beat: 10, midi: 79, dur: 1.5, vel: 0.9 },
      { beat: 11.5, midi: 76, dur: 0.5, vel: 0.72 },
      { beat: 12, midi: 74, dur: 1.5, vel: 0.8 },
      { beat: 13.5, midi: 72, dur: 0.5, vel: 0.68 },
      { beat: 14, midi: 69, dur: 2.0, vel: 0.82 },
      // 第 5-6 小节：高八度星光展开
      { beat: 16, midi: 81, dur: 1.5, vel: 0.92 },
      { beat: 17.5, midi: 84, dur: 0.5, vel: 0.8 },
      { beat: 18, midi: 86, dur: 1.5, vel: 0.96 },
      { beat: 19.5, midi: 84, dur: 0.5, vel: 0.78 },
      { beat: 20, midi: 81, dur: 1.0, vel: 0.88 },
      { beat: 21, midi: 79, dur: 1.0, vel: 0.84 },
      { beat: 22, midi: 76, dur: 2.0, vel: 0.88 },
      // 第 7-8 小节：温暖归宿收束
      { beat: 24, midi: 77, dur: 1.0, vel: 0.85 },
      { beat: 25, midi: 76, dur: 1.0, vel: 0.8 },
      { beat: 26, midi: 74, dur: 1.5, vel: 0.82 },
      { beat: 27.5, midi: 72, dur: 0.5, vel: 0.72 },
      { beat: 28, midi: 74, dur: 1.0, vel: 0.78 },
      { beat: 29, midi: 76, dur: 1.0, vel: 0.82 },
      { beat: 30, midi: 72, dur: 2.0, vel: 0.9 },
    ],
    chords: [
      { beat: 0, midis: [53, 60, 64, 69], dur: 4 },   // Fmaj7
      { beat: 4, midis: [55, 59, 62, 67], dur: 4 },   // G6
      { beat: 8, midis: [52, 59, 64, 67], dur: 4 },   // Em7
      { beat: 12, midis: [57, 60, 64, 71], dur: 4 },  // Am9
      { beat: 16, midis: [53, 60, 65, 69], dur: 4 },  // Fmaj7
      { beat: 20, midis: [52, 59, 64, 67], dur: 4 },  // Em7
      { beat: 24, midis: [50, 57, 62, 65], dur: 4 },  // Dm7
      { beat: 28, midis: [48, 55, 60, 64], dur: 4 },  // Cmaj7
    ],
  },

  // 2. 小小的手心 / 晴空花海：G 大调催泪抒情钢琴叙事曲 (32 拍)
  'ushio-pocket': {
    bpm: 76,
    timbre: 'piano',
    totalBeats: 32,
    melody: [
      // 第 1-2 小节：清澈深情大六度扬起
      { beat: 0, midi: 74, dur: 1.0, vel: 0.82 },
      { beat: 1, midi: 79, dur: 1.5, vel: 0.92 },
      { beat: 2.5, midi: 81, dur: 0.5, vel: 0.8 },
      { beat: 3, midi: 83, dur: 1.0, vel: 0.94 },
      { beat: 4, midi: 81, dur: 1.5, vel: 0.88 },
      { beat: 5.5, midi: 79, dur: 0.5, vel: 0.76 },
      { beat: 6, midi: 76, dur: 2.0, vel: 0.84 },
      // 第 3-4 小节：泪光中的拥抱
      { beat: 8, midi: 76, dur: 1.0, vel: 0.82 },
      { beat: 9, midi: 79, dur: 1.0, vel: 0.86 },
      { beat: 10, midi: 83, dur: 1.5, vel: 0.94 },
      { beat: 11.5, midi: 86, dur: 0.5, vel: 0.9 },
      { beat: 12, midi: 81, dur: 2.0, vel: 0.92 },
      { beat: 14, midi: 79, dur: 2.0, vel: 0.8 },
      // 第 5-6 小节：情感推向高潮（副歌情绪）
      { beat: 16, midi: 84, dur: 1.5, vel: 0.96 },
      { beat: 17.5, midi: 83, dur: 0.5, vel: 0.84 },
      { beat: 18, midi: 81, dur: 1.0, vel: 0.88 },
      { beat: 19, midi: 79, dur: 1.0, vel: 0.85 },
      { beat: 20, midi: 83, dur: 1.5, vel: 0.95 },
      { beat: 21.5, midi: 81, dur: 0.5, vel: 0.82 },
      { beat: 22, midi: 79, dur: 1.0, vel: 0.86 },
      { beat: 23, midi: 76, dur: 1.0, vel: 0.8 },
      // 第 7-8 小节：晴空释怀落句
      { beat: 24, midi: 74, dur: 1.0, vel: 0.84 },
      { beat: 25, midi: 76, dur: 1.0, vel: 0.86 },
      { beat: 26, midi: 79, dur: 1.5, vel: 0.9 },
      { beat: 27.5, midi: 81, dur: 0.5, vel: 0.82 },
      { beat: 28, midi: 79, dur: 4.0, vel: 0.92 },
    ],
    chords: [
      { beat: 0, midis: [48, 55, 60, 64, 67], dur: 4 },  // Cmaj7
      { beat: 4, midis: [50, 57, 62, 66], dur: 4 },      // Dadd9
      { beat: 8, midis: [47, 54, 59, 62, 66], dur: 4 },  // Bm7
      { beat: 12, midis: [52, 59, 64, 67], dur: 4 },     // Em7
      { beat: 16, midis: [48, 55, 60, 64, 69], dur: 4 }, // C6/9
      { beat: 20, midis: [47, 55, 59, 62, 67], dur: 4 }, // G/B
      { beat: 24, midis: [45, 52, 57, 60, 67], dur: 2 }, // Am7
      { beat: 26, midis: [50, 57, 60, 66], dur: 2 },     // D7
      { beat: 28, midis: [43, 50, 55, 59, 66], dur: 4 }, // Gmaj7
    ],
  },

  // 3. 樱坂微风：F 大调三拍子浪漫樱花圆舞曲 (24 拍 = 8 小节 3/4 拍)
  'nagisa-slope': {
    bpm: 92,
    timbre: 'duet',
    totalBeats: 24,
    melody: [
      { beat: 0, midi: 77, dur: 2.0, vel: 0.88 },
      { beat: 2, midi: 81, dur: 1.0, vel: 0.82 },
      { beat: 3, midi: 84, dur: 2.0, vel: 0.94 },
      { beat: 5, midi: 81, dur: 1.0, vel: 0.8 },
      { beat: 6, midi: 79, dur: 2.0, vel: 0.88 },
      { beat: 8, midi: 77, dur: 1.0, vel: 0.78 },
      { beat: 9, midi: 76, dur: 2.5, vel: 0.85 },
      { beat: 11.5, midi: 74, dur: 0.5, vel: 0.72 },
      { beat: 12, midi: 74, dur: 2.0, vel: 0.84 },
      { beat: 14, midi: 77, dur: 1.0, vel: 0.82 },
      { beat: 15, midi: 81, dur: 2.0, vel: 0.92 },
      { beat: 17, midi: 86, dur: 1.0, vel: 0.9 },
      { beat: 18, midi: 84, dur: 1.5, vel: 0.92 },
      { beat: 19.5, midi: 81, dur: 0.5, vel: 0.78 },
      { beat: 20, midi: 79, dur: 1.0, vel: 0.82 },
      { beat: 21, midi: 77, dur: 3.0, vel: 0.9 },
    ],
    chords: [
      { beat: 0, midis: [58, 62, 65, 69], dur: 3 },  // Bbmaj7
      { beat: 3, midis: [60, 64, 67, 70], dur: 3 },  // C7
      { beat: 6, midis: [57, 60, 64, 69], dur: 3 },  // Am7
      { beat: 9, midis: [50, 57, 62, 65], dur: 3 },  // Dm7
      { beat: 12, midis: [55, 58, 62, 65], dur: 3 }, // Gm7
      { beat: 15, midis: [48, 55, 60, 64], dur: 3 }, // C
      { beat: 18, midis: [53, 57, 60, 64], dur: 3 }, // Fmaj7
      { beat: 21, midis: [53, 57, 60, 65], dur: 3 }, // F
    ],
  },

  // 4. 星海潮鸣：D 自然小调 / F 大调空灵幻想世界竖琴连绵琶音 (32 拍)
  'town-flow-of-time': {
    bpm: 72,
    timbre: 'harp',
    totalBeats: 32,
    melody: [
      { beat: 0, midi: 74, dur: 1.5, vel: 0.84 },
      { beat: 1.5, midi: 81, dur: 1.5, vel: 0.9 },
      { beat: 3, midi: 79, dur: 1.0, vel: 0.8 },
      { beat: 4, midi: 77, dur: 2.0, vel: 0.86 },
      { beat: 6, midi: 76, dur: 1.0, vel: 0.78 },
      { beat: 7, midi: 72, dur: 1.0, vel: 0.76 },
      { beat: 8, midi: 74, dur: 1.5, vel: 0.85 },
      { beat: 9.5, midi: 84, dur: 1.5, vel: 0.94 },
      { beat: 11, midi: 81, dur: 1.0, vel: 0.86 },
      { beat: 12, midi: 79, dur: 2.0, vel: 0.88 },
      { beat: 14, midi: 77, dur: 2.0, vel: 0.82 },
      { beat: 16, midi: 86, dur: 1.5, vel: 0.95 },
      { beat: 17.5, midi: 84, dur: 0.5, vel: 0.82 },
      { beat: 18, midi: 81, dur: 1.5, vel: 0.9 },
      { beat: 19.5, midi: 79, dur: 0.5, vel: 0.78 },
      { beat: 20, midi: 77, dur: 1.5, vel: 0.86 },
      { beat: 21.5, midi: 76, dur: 0.5, vel: 0.76 },
      { beat: 22, midi: 74, dur: 2.0, vel: 0.84 },
      { beat: 24, midi: 72, dur: 1.5, vel: 0.82 },
      { beat: 25.5, midi: 76, dur: 0.5, vel: 0.78 },
      { beat: 26, midi: 79, dur: 2.0, vel: 0.88 },
      { beat: 28, midi: 74, dur: 4.0, vel: 0.9 },
    ],
    chords: [
      { beat: 0, midis: [50, 57, 62, 65, 69], dur: 4 },  // Dm9
      { beat: 4, midis: [58, 62, 65, 69], dur: 4 },      // Bbmaj7
      { beat: 8, midis: [53, 57, 60, 64, 69], dur: 4 },  // Fmaj9
      { beat: 12, midis: [48, 55, 60, 64, 67], dur: 4 }, // C
      { beat: 16, midis: [55, 58, 62, 65, 69], dur: 4 }, // Gm9
      { beat: 20, midis: [50, 57, 62, 65], dur: 4 },     // Dm7
      { beat: 24, midis: [58, 62, 65, 67], dur: 4 },     // Bb6
      { beat: 28, midis: [50, 57, 62, 69], dur: 4 },     // Dm
    ],
  },
};

// ======================== IndexedDB 自定义本地音乐持久化 ========================

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

// ======================== 自定义原画截图持久化（可选覆盖当前场面底图） ========================

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
 * 启动指定背景音乐（自动终止上一段残留播放，支持自定义本地音乐与多声部合成乐曲，退场平滑淡出）
 */
export function startSplashBgm(options: StartSplashBgmOptions): () => void {
  stopActiveSplashBgm();

  if (typeof window === 'undefined' || options.trackId === 'off') {
    return () => {};
  }

  const targetVolume = Math.max(0.05, Math.min(1, options.volume ?? 0.65));

  if (options.trackId === 'custom-file') {
    let cancelled = false;
    let audioEl: HTMLAudioElement | null = null;
    let blobUrl: string | null = null;
    let fadeTimer: number | null = null;
    let fallbackCleanup: (() => void) | null = null;

    loadCustomBgmBlob().then((blob) => {
      if (cancelled) return;
      if (!blob) {
        // 若本地文件尚未导入或已被清理，平滑回退到场景推荐内置名曲
        const fb = options.fallbackTrackId || 'ushio-pocket';
        fallbackCleanup = playBuiltinScore(fb, targetVolume, options.loop ?? true);
        return;
      }

      blobUrl = URL.createObjectURL(blob);
      const audio = new Audio(blobUrl);
      audio.loop = options.loop ?? true;
      audio.preload = 'auto';
      audio.volume = 0.01;
      audioEl = audio;

      const seekOffset = Math.max(0, options.startOffsetSec ?? 0);
      const startPlayback = () => {
        if (cancelled) return;
        if (seekOffset > 0 && Number.isFinite(audio.duration) && seekOffset < audio.duration - 1) {
          try {
            audio.currentTime = seekOffset;
          } catch {
            // 忽略流媒体游标边界异常
          }
        }
        audio.play().catch(() => {
          // 浏览器自动播放受阻时静默忽略，用户点击页面试听按钮时即可立即发声
        });

        // 320ms 柔和淡入
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

      if (seekOffset > 0) {
        audio.addEventListener('loadedmetadata', startPlayback, { once: true });
      } else {
        startPlayback();
      }
    });

    const stopFn = () => {
      if (cancelled) return;
      cancelled = true;
      if (fadeTimer) {
        window.clearInterval(fadeTimer);
        fadeTimer = null;
      }
      if (fallbackCleanup) {
        fallbackCleanup();
        fallbackCleanup = null;
      }
      if (audioEl) {
        const el = audioEl;
        audioEl = null;
        const urlToRevoke = blobUrl;
        blobUrl = null;
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
            if (urlToRevoke) URL.revokeObjectURL(urlToRevoke);
          }
        }, 45);
      } else if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
        blobUrl = null;
      }
    };

    activeStopHandle = stopFn;
    return stopFn;
  }

  const stopBuiltin = playBuiltinScore(options.trackId, targetVolume, options.loop ?? true);
  activeStopHandle = stopBuiltin;
  return stopBuiltin;
}

function playBuiltinScore(
  trackId: Exclude<ClannadBgmTrackId, 'follow-scene' | 'custom-file' | 'off'>,
  volume: number,
  loop: boolean,
): () => void {
  const AudioCtx =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtx) return () => {};

  const score = SCORES[trackId] || SCORES['dango-family'];
  let ctx: AudioContext | null = null;
  let loopTimer: number | null = null;
  let stopped = false;

  try {
    ctx = new AudioCtx();
    if (ctx.state === 'suspended') {
      ctx.resume().catch(() => {});
    }

    const masterGain = ctx.createGain();
    const scaledMaster = 0.24 * volume;
    masterGain.gain.setValueAtTime(0.0001, ctx.currentTime);
    masterGain.gain.linearRampToValueAtTime(scaledMaster, ctx.currentTime + 0.25);

    // 温暖立体声延迟混响效果总线（营造剧场空间余韵）
    const delayNode = ctx.createDelay(1.0);
    delayNode.delayTime.value = 0.29;
    const feedbackGain = ctx.createGain();
    feedbackGain.gain.value = 0.28;
    const wetFilter = ctx.createBiquadFilter();
    wetFilter.type = 'lowpass';
    wetFilter.frequency.value = 2400;
    const wetGain = ctx.createGain();
    wetGain.gain.value = 0.34;

    masterGain.connect(ctx.destination);
    masterGain.connect(delayNode);
    delayNode.connect(wetFilter);
    wetFilter.connect(feedbackGain);
    feedbackGain.connect(delayNode);
    wetFilter.connect(wetGain);
    wetGain.connect(ctx.destination);

    const beatSec = 60 / score.bpm;
    const loopDurationSec = score.totalBeats * beatSec;

    const schedulePass = (passStartTime: number) => {
      if (!ctx || stopped) return;

      // 1. 调度左手分解和弦与温暖弦乐铺底
      for (const ch of score.chords) {
        const chStart = passStartTime + ch.beat * beatSec;
        const chDurSec = ch.dur * beatSec;

        // 轻柔弦乐长音底垫
        ch.midis.slice(0, 3).forEach((m) => {
          if (!ctx) return;
          const oscPad = ctx.createOscillator();
          const padGain = ctx.createGain();
          const padFilter = ctx.createBiquadFilter();
          oscPad.type = 'triangle';
          oscPad.frequency.setValueAtTime(midiToFreq(m), chStart);
          padFilter.type = 'lowpass';
          padFilter.frequency.value = 950;

          padGain.gain.setValueAtTime(0.0001, chStart);
          padGain.gain.linearRampToValueAtTime(0.055, chStart + Math.min(0.45, chDurSec * 0.25));
          padGain.gain.exponentialRampToValueAtTime(0.0001, chStart + chDurSec + 0.15);

          oscPad.connect(padFilter);
          padFilter.connect(padGain);
          padGain.connect(masterGain);
          oscPad.start(chStart);
          oscPad.stop(chStart + chDurSec + 0.2);
        });

        // 分解琶音流动伴奏
        const arpStep = score.timbre === 'harp' ? beatSec * 0.5 : beatSec * 0.75;
        const arpCount = Math.floor(chDurSec / arpStep);
        for (let i = 0; i < arpCount; i++) {
          const m = ch.midis[i % ch.midis.length] + 12;
          const tArp = chStart + i * arpStep;
          const oscArp = ctx.createOscillator();
          const arpGain = ctx.createGain();
          oscArp.type = 'sine';
          oscArp.frequency.setValueAtTime(midiToFreq(m), tArp);

          arpGain.gain.setValueAtTime(0.0001, tArp);
          arpGain.gain.linearRampToValueAtTime(0.065, tArp + 0.02);
          arpGain.gain.exponentialRampToValueAtTime(0.0001, tArp + arpStep * 1.6);

          oscArp.connect(arpGain);
          arpGain.connect(masterGain);
          oscArp.start(tArp);
          oscArp.stop(tArp + arpStep * 1.65);
        }
      }

      // 2. 调度歌唱性主旋律（叠加泛音锤击层模拟三角钢琴 / 八音盒钟琴音色）
      for (const note of score.melody) {
        const t0 = passStartTime + note.beat * beatSec;
        const noteDur = Math.max(0.35, note.dur * beatSec);
        const vel = note.vel ?? 0.85;
        const freq = midiToFreq(note.midi);

        // 主基音
        const oscMain = ctx.createOscillator();
        const gainMain = ctx.createGain();
        oscMain.type = score.timbre === 'piano' ? 'triangle' : 'sine';
        oscMain.frequency.setValueAtTime(freq, t0);

        const mainFilter = ctx.createBiquadFilter();
        mainFilter.type = 'lowpass';
        mainFilter.frequency.setValueAtTime(score.timbre === 'piano' ? 2800 : 4200, t0);

        gainMain.gain.setValueAtTime(0.0001, t0);
        gainMain.gain.linearRampToValueAtTime(0.24 * vel, t0 + 0.016);
        gainMain.gain.exponentialRampToValueAtTime(0.07 * vel, t0 + noteDur * 0.55);
        gainMain.gain.exponentialRampToValueAtTime(0.0001, t0 + noteDur + 0.65);

        oscMain.connect(mainFilter);
        mainFilter.connect(gainMain);
        gainMain.connect(masterGain);
        oscMain.start(t0);
        oscMain.stop(t0 + noteDur + 0.7);

        // 高八度晶莹泛音点缀（赋予八音盒钢片或钢琴音板光泽）
        const oscHarm = ctx.createOscillator();
        const gainHarm = ctx.createGain();
        oscHarm.type = 'sine';
        oscHarm.frequency.setValueAtTime(
          score.timbre === 'harp' ? freq * 3 : freq * 2,
          t0,
        );
        const harmPeak = score.timbre === 'celesta' ? 0.085 * vel : 0.045 * vel;
        gainHarm.gain.setValueAtTime(0.0001, t0);
        gainHarm.gain.linearRampToValueAtTime(harmPeak, t0 + 0.008);
        gainHarm.gain.exponentialRampToValueAtTime(0.0001, t0 + Math.min(0.55, noteDur * 0.7));

        oscHarm.connect(gainHarm);
        gainHarm.connect(masterGain);
        oscHarm.start(t0);
        oscHarm.stop(t0 + Math.min(0.6, noteDur * 0.75));
      }
    };

    const firstStart = ctx.currentTime + 0.05;
    schedulePass(firstStart);

    if (loop) {
      let nextPassTime = firstStart + loopDurationSec;
      loopTimer = window.setInterval(() => {
        if (!ctx || stopped) return;
        if (ctx.currentTime + 1.2 >= nextPassTime) {
          schedulePass(nextPassTime);
          nextPassTime += loopDurationSec;
        }
      }, 400);
    }

    return () => {
      if (stopped) return;
      stopped = true;
      if (loopTimer) {
        window.clearInterval(loopTimer);
        loopTimer = null;
      }
      if (ctx && ctx.state !== 'closed') {
        const closingCtx = ctx;
        try {
          const now = closingCtx.currentTime;
          masterGain.gain.cancelScheduledValues(now);
          masterGain.gain.setValueAtTime(Math.max(0.0001, masterGain.gain.value), now);
          masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.32);
        } catch {
          // 忽略
        }
        window.setTimeout(() => {
          if (closingCtx.state !== 'closed') {
            closingCtx.close().catch(() => {});
          }
        }, 360);
      }
    };
  } catch {
    if (ctx && ctx.state !== 'closed') {
      ctx.close().catch(() => {});
    }
    return () => {};
  }
}
