import type { PetCharacterId } from '../../types/studio';

export type PetAction =
  | 'idle'
  | 'pat'
  | 'sleep'
  | 'box_spin'
  | 'box_peek'
  | 'stomp'
  | 'walk'
  | 'dash'
  | 'skid'
  | 'blood'
  | 'dance'
  | 'feed'
  | 'picked_up'
  | 'land_squash'
  | 'fox'
  | 'rose'
  | 'stars'
  | 'volcano'
  | 'dango_song'
  | 'sunflower'
  | 'light_orb'
  | 'water_slash'
  | 'thunder_dash'
  | 'beast_rush';

export type ParticleKind =
  | 'petal'
  | 'spark'
  | 'star'
  | 'dust'
  | 'water'
  | 'lightning'
  | 'dango'
  | 'orb';

export interface PetQuoteItem {
  zh: string;
  sub?: string;
}

export interface PetCharacterActionSpec {
  action: PetAction;
  label: string;
  bubble: string;
  toneClass: string;
}

export interface PetCharacterProfile {
  id: PetCharacterId;
  name: string;
  shortName: string;
  badge: string;
  accent: string;
  secondaryAccent: string;
  particleKind: ParticleKind;
  description: string;
  quotes: PetQuoteItem[];
  doubleClickAction: PetAction;
  doubleClickBubble: string;
  actions: PetCharacterActionSpec[];
}

export interface LyricLine {
  timeMs: number;
  text: string;
}

export const SCALE_PRESETS = [0.88, 1.0, 1.15] as const;

export const PET_CHARACTER_PROFILES: Record<PetCharacterId, PetCharacterProfile> = {
  nezuko: {
    id: 'nezuko',
    name: '灶门祢豆子（米豆子）· 多态灵动版',
    shortName: '祢豆子',
    badge: '鬼灭 · 绯樱多态',
    accent: '#f472b6',
    secondaryAccent: '#fb7185',
    particleKind: 'petal',
    description:
      '搭载全套高精透明多姿态原画与真实自然眨眼：8帧3D大正木箱自转与探头张望、豆豆眼风火轮狂奔急刹、气鼓鼓跺脚、捧金平糖雀跃、爆血绯晶与竹篓甜睡。',
    quotes: [
      { zh: '唔嗯~ 灵感与算力都在满格充能中 ✨' },
      { zh: '血鬼术·爆血，驱散一切隐蔽缺陷！' },
      { zh: '钻进鳞泷爷爷的大正木箱悄悄探头张望 👀' },
      { zh: '不管任务多复杂，米豆子都会一直陪在你身旁哦' },
      { zh: '摸摸头~ 今天的代码结构像金平糖一样甜 ✨' },
    ],
    doubleClickAction: 'box_spin',
    doubleClickBubble: '3D 大正木箱旋风奇点开启！',
    actions: [
      { action: 'pat', label: '摸头', bubble: '轻抚发梢 ~ 幸福弯弯笑眼开启 ♥', toneClass: 'hover:bg-pink-500/25 text-pink-200' },
      { action: 'box_spin', label: '转箱', bubble: '8帧 3D 大正木箱 360° 旋风旋转！', toneClass: 'hover:bg-amber-500/25 text-amber-200' },
      { action: 'dash', label: '狂奔', bubble: '豆豆眼变小形态 · 风火轮极速狂奔！', toneClass: 'hover:bg-sky-500/25 text-sky-200' },
      { action: 'stomp', label: '跺脚', bubble: '唔嗯！！鼓起腮帮子气鼓鼓跺脚！', toneClass: 'hover:bg-orange-500/25 text-orange-200' },
      { action: 'blood', label: '爆血', bubble: '血鬼术·爆血绯晶绽放！', toneClass: 'hover:bg-rose-500/25 text-pink-300' },
      { action: 'feed', label: '投喂', bubble: '双手捧住五彩金平糖，开心雀跃 ✨', toneClass: 'hover:bg-emerald-500/25 text-emerald-200' },
    ],
  },
  prince: {
    id: 'prince',
    name: 'B612 小王子 · 绘本星辰版',
    shortName: '小王子',
    badge: 'B612 · 双尾丝巾',
    accent: '#38bdf8',
    secondaryAccent: '#fbbf24',
    particleKind: 'star',
    description:
      '水彩厚涂绘本全套姿态与颈后双尾 Verlet 物理丝绸围巾：自然眨眼呼吸、拥抱驯服小狐狸、双手捧护玻璃罩红玫瑰、44次金色日落、流星许愿与弯月安眠。',
    quotes: [
      { zh: '真正重要的东西，用眼睛是看不见的。', sub: '用心灵才能洞察本质' },
      { zh: '因为你为你的玫瑰花费了时间，她才变得如此重要。', sub: '温柔守护每一行用心的杰作' },
      { zh: '我在 B612 星球上看过四十四次金色日落。', sub: '夕阳余晖正温柔洒满桌面' },
      { zh: '如果你驯服了我，我们彼此就需要对方。', sub: '小狐狸顺从地贴了贴你的手心' },
      { zh: '所有大人都曾经是小孩，虽然只有少数人记得。', sub: '仰望满天会笑的金色星辰 ✨' },
    ],
    doubleClickAction: 'stars',
    doubleClickBubble: 'B612 流星雨划过夜空，快许个愿吧 ✨',
    actions: [
      { action: 'pat', label: '轻抚', bubble: '微风拂过金发，星星都在对你微笑 ✨', toneClass: 'hover:bg-sky-500/25 text-sky-200' },
      { action: 'fox', label: '狐狸', bubble: '蹲下身和驯服的小狐狸温暖依偎 🦊', toneClass: 'hover:bg-amber-500/25 text-amber-200' },
      { action: 'rose', label: '玫瑰', bubble: '双手捧起玻璃钟罩，凝视独一无二的玫瑰 🌹', toneClass: 'hover:bg-rose-500/25 text-rose-200' },
      { action: 'stars', label: '流星', bubble: '仰望 B612 夜空双子流星划过 🌠', toneClass: 'hover:bg-indigo-500/25 text-indigo-200' },
      { action: 'volcano', label: '火山', bubble: '认真清扫 B612 星球的小火山烟尘 🌋', toneClass: 'hover:bg-orange-500/25 text-orange-200' },
      { action: 'walk', label: '漫步', bubble: '金黄丝巾随风飘扬，踏着星尘轻盈漫步', toneClass: 'hover:bg-purple-500/25 text-purple-200' },
    ],
  },
  ushio: {
    id: 'ushio',
    name: '冈崎汐 · 团子大家族版',
    shortName: '冈崎汐',
    badge: 'CLANNAD · 光玉花田',
    accent: '#f59e0b',
    secondaryAccent: '#f472b6',
    particleKind: 'dango',
    description:
      '《CLANNAD》温暖治愈女儿小汐怀抱樱粉团子大家族：双呆毛呼吸眨眼、八音盒《团子大家族》叠叠乐、向日葵花田寻宝、小镇愿望光玉升空与团子堆甜睡。',
    quotes: [
      { zh: '团子，团子，团子，团子，团子大家族 ♪', sub: '软乎乎的团子一直陪在身边哦' },
      { zh: '在金灿灿的向日葵花田里，找到了爸爸送的第一个宝物 🌻', sub: '最重要的回忆永远闪闪发光' },
      { zh: '爸爸说，能哭的地方只有厕所，和爸爸的怀里…', sub: '今天也要带着温暖的勇气出发' },
      { zh: '快看呀，夜空升起了好多温柔的光玉，愿望一定会实现的 ✨' },
      { zh: '小汐和粉色大团子，今天也会乖巧守护你的每一行代码 🍡' },
    ],
    doubleClickAction: 'dango_song',
    doubleClickBubble: '八音盒奏响《团子大家族》，三色小团子开心叠叠乐 ♪',
    actions: [
      { action: 'pat', label: '摸呆毛', bubble: '轻抚小汐头顶的小呆毛 ~ 团子叠叠乐开心晃动 🍡', toneClass: 'hover:bg-pink-500/25 text-pink-200' },
      { action: 'dango_song', label: '团子歌', bubble: '团子、团子、团子大家族 ~ 温暖八音盒响起 ♪', toneClass: 'hover:bg-amber-500/25 text-amber-200' },
      { action: 'sunflower', label: '花田', bubble: '金黄向日葵花田盛开，举起灿烂向日葵与小机器人 🌻', toneClass: 'hover:bg-yellow-500/25 text-yellow-200' },
      { action: 'light_orb', label: '光玉', bubble: '小镇的愿望光玉在天穹温柔飘升，守护奇迹 ✨', toneClass: 'hover:bg-sky-500/25 text-sky-200' },
      { action: 'dash', label: '小跑', bubble: '紧紧抱着粉团子哒哒哒欢快小跑！', toneClass: 'hover:bg-emerald-500/25 text-emerald-200' },
      { action: 'feed', label: '甜团子', bubble: '一口吃掉甜甜糯米团（躲开早苗阿姨的特制面包啦~）🍡', toneClass: 'hover:bg-rose-500/25 text-rose-200' },
    ],
  },
  tanjiro: {
    id: 'tanjiro',
    name: '灶门炭治郎 · 水之呼吸版',
    shortName: '炭治郎',
    badge: '鬼杀队 · 碧海流波',
    accent: '#14b8a6',
    secondaryAccent: '#38bdf8',
    particleKind: 'water',
    description:
      '搭载水之呼吸·生生流转流体刀纹环、清泉水滴粒子、高敏嗅觉预警与温柔热血鼓励交互。',
    quotes: [
      { zh: '加油！心是原动力，一步一步向前推进吧！' },
      { zh: '闻到了「隙之线」的气息，问题根源就在眼前！' },
      { zh: '水之呼吸·拾之型·生生流转 🌊' },
      { zh: '累了的话记得深呼吸，调整全集中常中状态哦' },
      { zh: '今天也辛苦啦，我会稳稳守护你的工作流！' },
    ],
    doubleClickAction: 'water_slash',
    doubleClickBubble: '水之呼吸·生生流转！碧波斩断阻塞 🌊',
    actions: [
      { action: 'pat', label: '鼓励', bubble: '炭治郎露出温暖阳光的笑容 ☀️', toneClass: 'hover:bg-emerald-500/25 text-emerald-200' },
      { action: 'water_slash', label: '水之呼吸', bubble: '全集中·水之呼吸！清澈流体剑纹绽放 🌊', toneClass: 'hover:bg-cyan-500/25 text-cyan-200' },
      { action: 'dash', label: '疾行', bubble: '巡山步法极速驰援！', toneClass: 'hover:bg-sky-500/25 text-sky-200' },
      { action: 'feed', label: '饭团', bubble: '大口吃下梅子饭团，元气满满 🍙', toneClass: 'hover:bg-amber-500/25 text-amber-200' },
      { action: 'walk', label: '巡逻', bubble: '背着木箱沿桌面稳健巡航…', toneClass: 'hover:bg-teal-500/25 text-teal-200' },
    ],
  },
  zenitsu: {
    id: 'zenitsu',
    name: '我妻善逸 · 霹雳一闪版',
    shortName: '善逸',
    badge: '鬼杀队 · 金雷电弧',
    accent: '#facc15',
    secondaryAccent: '#fb923c',
    particleKind: 'lightning',
    description:
      '闭眼觉醒反差萌、雷之呼吸·壹之型·霹雳一闪金色流光残影、麻雀啾太郎互动与顺风耳遥测。',
    quotes: [
      { zh: '雷之呼吸·壹之型——霹雳一闪 ⚡' },
      { zh: '啾太郎说今天的接口响应快如闪电！' },
      { zh: '呜哇虽然需求看起来好凶，但闭上眼就能秒杀！' },
      { zh: '听见了…极细微但平稳运转的心跳与算力声 ♪' },
      { zh: '只要专注把一件事登峰造极，就一定能发光！' },
    ],
    doubleClickAction: 'thunder_dash',
    doubleClickBubble: '雷之呼吸·壹之型·霹雳一闪·六连 ⚡',
    actions: [
      { action: 'pat', label: '顺毛', bubble: '呜哇~ 终于有人温柔夸我啦 💛', toneClass: 'hover:bg-yellow-500/25 text-yellow-200' },
      { action: 'thunder_dash', label: '霹雳一闪', bubble: '闭眼瞬身！金雷电弧破空而出 ⚡', toneClass: 'hover:bg-amber-500/25 text-amber-200' },
      { action: 'stomp', label: '惊呼', bubble: '噫！！发现可疑报错气息！', toneClass: 'hover:bg-orange-500/25 text-orange-200' },
      { action: 'feed', label: '甜点', bubble: '幸福地品尝蜂蜜蛋糕 🍰', toneClass: 'hover:bg-pink-500/25 text-pink-200' },
      { action: 'sleep', label: '觉醒眠', bubble: '进入半睡半醒最强雷神待机态…', toneClass: 'hover:bg-indigo-500/25 text-indigo-200' },
    ],
  },
  inosuke: {
    id: 'inosuke',
    name: '嘴平伊之助 · 猪突猛进版',
    shortName: '伊之助',
    badge: '鬼杀队 · 苍岚兽王',
    accent: '#60a5fa',
    secondaryAccent: '#34d399',
    particleKind: 'spark',
    description:
      '山大王热血气场、兽之呼吸·猪突猛进冲撞破障、空间触觉感知与飘飘然得意泡泡特效。',
    quotes: [
      { zh: '猪突猛进！！猪突猛进！！把难题统统撞飞 🐗' },
      { zh: '哼哼~ 交给本山大王准没错（飘飘然~）✨' },
      { zh: '兽之呼吸·柒之型·空间识觉，全盘尽在掌握！' },
      { zh: '来比试谁先跑通全部构建吧！哇哈哈哈！' },
      { zh: '天妇罗！再来十份炸虾天妇罗 🍤' },
    ],
    doubleClickAction: 'beast_rush',
    doubleClickBubble: '兽之呼吸·猪突猛进！全速冲锋 🐗',
    actions: [
      { action: 'pat', label: '夸奖', bubble: '哼哼~ 再多夸夸本大爷（头顶冒小绒球）✨', toneClass: 'hover:bg-sky-500/25 text-sky-200' },
      { action: 'beast_rush', label: '猪突猛进', bubble: '双刀交错·猪突猛进极速突袭 🐗', toneClass: 'hover:bg-indigo-500/25 text-indigo-200' },
      { action: 'stomp', label: '叫阵', bubble: '放马过来吧！任何复杂架构都不在话下！', toneClass: 'hover:bg-orange-500/25 text-orange-200' },
      { action: 'feed', label: '天妇罗', bubble: '大嚼特嚼酥脆炸虾天妇罗 🍤', toneClass: 'hover:bg-amber-500/25 text-amber-200' },
      { action: 'dance', label: '庆功舞', bubble: '胜利狂欢热舞开启 ♪', toneClass: 'hover:bg-emerald-500/25 text-emerald-200' },
    ],
  },
  custom: {
    id: 'custom',
    name: '自定义专属伴侣 · 自由立绘',
    shortName: '专属伴侣',
    badge: 'CUSTOM · 自由定制',
    accent: '#a78bfa',
    secondaryAccent: '#38bdf8',
    particleKind: 'spark',
    description:
      '支持一键导入本地 PNG / WebP / GIF / SVG 透明立绘或动态表情包，赋予专属 3D 视差悬浮与物理漫步生命力。',
    quotes: [
      { zh: '专属定制形态已激活，时刻守护你的灵感节拍 ✨' },
      { zh: '轻触互动、自由漫步与实时配额尽在掌控' },
      { zh: '今天也要保持松弛专注的节奏哦' },
    ],
    doubleClickAction: 'stars',
    doubleClickBubble: '星光环绕充能完毕 ✨',
    actions: [
      { action: 'pat', label: '互动', bubble: '收到温暖拍拍，状态满格 ✨', toneClass: 'hover:bg-purple-500/25 text-purple-200' },
      { action: 'dash', label: '冲刺', bubble: '灵动巡航冲刺！', toneClass: 'hover:bg-sky-500/25 text-sky-200' },
      { action: 'feed', label: '投喂', bubble: '开心收下能量补给 🍬', toneClass: 'hover:bg-emerald-500/25 text-emerald-200' },
      { action: 'stars', label: '星光', bubble: '点亮桌面星芒特效 ✨', toneClass: 'hover:bg-amber-500/25 text-amber-200' },
      { action: 'dance', label: '律动', bubble: '跟随节奏轻轻摇摆 ♪', toneClass: 'hover:bg-pink-500/25 text-pink-200' },
    ],
  },
};

export const PET_CHARACTER_ORDER: PetCharacterId[] = [
  'nezuko',
  'prince',
  'ushio',
  'tanjiro',
  'zenitsu',
  'inosuke',
  'custom',
];

/** 规范化任意角色字符串为标准 PetCharacterId */
export function normalizePetCharacter(raw?: string | null): PetCharacterId {
  const cleaned = (raw || '').trim().toLowerCase();
  if (
    cleaned === 'prince' ||
    cleaned === 'little-prince' ||
    cleaned === 'little_prince' ||
    cleaned === '小王子'
  ) {
    return 'prince';
  }
  if (
    cleaned === 'ushio' ||
    cleaned === 'clannad' ||
    cleaned === 'dango' ||
    cleaned === '冈崎汐' ||
    cleaned === '小汐' ||
    cleaned === '汐' ||
    cleaned === '团子'
  ) {
    return 'ushio';
  }
  if (cleaned === 'tanjiro') return 'tanjiro';
  if (cleaned === 'zenitsu') return 'zenitsu';
  if (cleaned === 'inosuke') return 'inosuke';
  if (cleaned === 'custom') return 'custom';
  if (cleaned === 'nezuko' || cleaned === 'midouzi' || cleaned === '米豆子' || cleaned === '祢豆子') {
    return 'nezuko';
  }
  return 'nezuko';
}

/**
 * 解析带时间戳（或纯文本回退）的 LRC 歌词，返回按毫秒升序排列的时间轴数组。
 * 完整支持：
 * - 单行多时间标签，例如 `[00:15.20][01:32.45]副歌歌词`
 * - 2位百分秒 `[01:02.34]` 或 3位毫秒 `[01:02.345]` 或冒号分隔 `[01:02:34]`
 * - `[offset:+/-ms]` 全局偏移校准
 * - 自动过滤 `[ti:...]`、`[ar:...]`、`[al:...]`、`[by:...]` 等元信息头
 */
export function parseLrcTimeline(lrc: string): LyricLine[] {
  if (!lrc || !lrc.trim()) return [];

  const rawLines = lrc.split(/\r?\n/);
  let globalOffsetMs = 0;
  const offsetRe = /^\[offset:\s*([+-]?\d+)\s*\]$/i;
  const metaRe = /^\[(ti|ar|al|by|re|ve|au|length):.*\]$/i;
  const timeTagRe = /\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\]/g;

  const timedEntries: LyricLine[] = [];
  const plainLines: string[] = [];

  for (const rawLine of rawLines) {
    const trimmed = rawLine.trim();
    if (!trimmed) continue;

    const offsetMatch = trimmed.match(offsetRe);
    if (offsetMatch) {
      globalOffsetMs = parseInt(offsetMatch[1], 10) || 0;
      continue;
    }
    if (metaRe.test(trimmed)) continue;
    if (/^(ti|ar|al|by):/i.test(trimmed)) continue;

    const matches = Array.from(trimmed.matchAll(timeTagRe));
    const text = trimmed.replace(timeTagRe, '').trim();

    if (matches.length > 0) {
      if (!text) continue;
      for (const m of matches) {
        const mins = parseInt(m[1], 10) || 0;
        const secs = parseInt(m[2], 10) || 0;
        const fracRaw = m[3] || '0';
        const fracMs =
          fracRaw.length === 1
            ? parseInt(fracRaw, 10) * 100
            : fracRaw.length === 2
              ? parseInt(fracRaw, 10) * 10
              : parseInt(fracRaw.slice(0, 3), 10);
        const totalMs = Math.max(0, mins * 60_000 + secs * 1_000 + fracMs - globalOffsetMs);
        timedEntries.push({ timeMs: totalMs, text });
      }
    } else if (!trimmed.startsWith('[')) {
      plainLines.push(trimmed);
    }
  }

  if (timedEntries.length > 0) {
    return timedEntries.sort((a, b) => a.timeMs - b.timeMs);
  }

  // 无时间标签的纯文本歌词按每句 3200ms 生成均匀时间轴
  return plainLines.map((text, idx) => ({
    timeMs: idx * 3200,
    text,
  }));
}

/** 二分查找当前播放毫秒对应的歌词索引（若尚未到达首句时间则返回 0） */
export function findActiveLyricIndex(lines: LyricLine[], elapsedMs: number): number {
  if (lines.length === 0) return -1;
  if (elapsedMs <= lines[0].timeMs) return 0;

  let low = 0;
  let high = lines.length - 1;
  let ans = 0;
  while (low <= high) {
    const mid = (low + high) >> 1;
    if (lines[mid].timeMs <= elapsedMs) {
      ans = mid;
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }
  return ans;
}

/** 判定指针移动距离是否达到触发窗口拖拽的物理阈值（避免单击/双击被 startDragging 吞没） */
export function shouldStartWindowDrag(
  startX: number,
  startY: number,
  currentX: number,
  currentY: number,
  thresholdPx = 5,
): boolean {
  return Math.hypot(currentX - startX, currentY - startY) >= thresholdPx;
}

/** 检测当前激活账号是否存在低于阈值的核心模型配额，返回预警提示信息 */
export function evaluateLowQuotaAlert(
  models: Array<{ name: string; display_name?: string; percentage: number }> | undefined | null,
  threshold = 20,
): { hasLowQuota: boolean; lowestModelName: string; lowestPercentage: number; alertMessage: string } {
  if (!models || models.length === 0) {
    return {
      hasLowQuota: false,
      lowestModelName: '',
      lowestPercentage: 100,
      alertMessage: '',
    };
  }

  let lowest = models[0];
  for (const m of models) {
    if (m.percentage < lowest.percentage) {
      lowest = m;
    }
  }

  const label = lowest.display_name || lowest.name;
  if (lowest.percentage < threshold) {
    return {
      hasLowQuota: true,
      lowestModelName: label,
      lowestPercentage: lowest.percentage,
      alertMessage: `⚠️ 算力预警：「${label}」剩余 ${lowest.percentage}%，可在配额舱一键切号`,
    };
  }

  return {
    hasLowQuota: false,
    lowestModelName: label,
    lowestPercentage: lowest.percentage,
    alertMessage: '',
  };
}
