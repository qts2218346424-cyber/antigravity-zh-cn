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
  voiceKey?: string;
}

export interface PetCharacterActionSpec {
  action: PetAction;
  label: string;
  bubble: string;
  sub?: string;
  voiceKey?: string;
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
  doubleClickSub?: string;
  doubleClickVoiceKey?: string;
  actions: PetCharacterActionSpec[];
}

export const BUILTIN_VOICE_KEYS = [
  'ushio_toilet',
  'ushio_dango',
  'ushio_robot',
  'ushio_sanae',
  'ushio_trip',
  'ushio_sleep',
  'nezuko_ohayou',
  'nezuko_happiness',
  'nezuko_blood',
  'nezuko_box',
  'nezuko_angry',
  'nezuko_apologize',
  'prince_essential',
  'prince_rose',
  'prince_fox',
  'prince_sunset',
  'tanjiro_encourage',
  'tanjiro_water',
  'zenitsu_care',
  'zenitsu_thunder',
  'inosuke_praise',
  'inosuke_rush',
] as const;

export interface LyricLine {
  timeMs: number;
  text: string;
}

export const SCALE_PRESETS = [0.88, 1.0, 1.15] as const;

export const PET_CHARACTER_PROFILES: Record<PetCharacterId, PetCharacterProfile> = {
  nezuko: {
    id: 'nezuko',
    name: '灶门祢豆子（米豆子）· 原声多态版',
    shortName: '祢豆子',
    badge: '鬼灭 · 绯樱原声',
    accent: '#f472b6',
    secondaryAccent: '#fb7185',
    particleKind: 'petal',
    description:
      '内置鬼灭原生日语萌音与克服阳光经典金句：8帧3D大正木箱自转探头、豆豆眼风火轮疾跑、气鼓鼓跺脚、捧金平糖雀跃、爆血绯晶与竹篓甜睡。',
    quotes: [
      {
        zh: '「早…早上好！平安无事真是太好了呢，最喜欢你啦 ✨」',
        sub: 'お…おはよう！よかったね、本当によかったね！',
        voiceKey: 'nezuko_ohayou',
      },
      {
        zh: '「唔嗯~♪ 幸不幸福是由自己决定的，最重要的是珍惜『当下』哦 ♥」',
        sub: '幸せかどうかは自分で決めるの。大切なのは「今」なんだよ！',
        voiceKey: 'nezuko_happiness',
      },
      {
        zh: '「血鬼术·爆血！！哥哥和大家，绝对由米豆子来守护！」',
        sub: '血鬼術・爆血！！みんなは絶対に私が守る！',
        voiceKey: 'nezuko_blood',
      },
      {
        zh: '「唔嗯~♪ 亮晶晶的金平糖，米豆子最喜欢啦 ✨」',
        sub: 'ん〜っ♪ こんぺいとう、キラキラで大好きっ！',
        voiceKey: 'nezuko_box',
      },
      {
        zh: '「为什么要老是道歉呢？你每天都这么努力了…一起歇会儿吧 ♥」',
        sub: 'どうしていつも謝るの？毎日こんなに頑張ってるのに…',
        voiceKey: 'nezuko_apologize',
      },
      {
        zh: '「唔嗯——！！鼓起腮帮子气鼓鼓跺脚啦！」',
        sub: 'むぅ〜っ！！んーっ！！もう怒ったぞーっ！',
        voiceKey: 'nezuko_angry',
      },
    ],
    doubleClickAction: 'box_spin',
    doubleClickBubble: '「唔嗯~♪」3D 大正木箱旋风奇点开启！',
    doubleClickSub: 'ん〜っ♪ こんぺいとう、キラキラで大好きっ！',
    doubleClickVoiceKey: 'nezuko_box',
    actions: [
      {
        action: 'pat',
        label: '摸头',
        bubble: '「幸不幸福是由自己决定的，最重要的是珍惜当下哦 ♥」',
        sub: '幸せかどうかは自分で決めるの。大切なのは「今」なんだよ！',
        voiceKey: 'nezuko_happiness',
        toneClass: 'hover:bg-pink-500/25 text-pink-200',
      },
      {
        action: 'box_spin',
        label: '转箱',
        bubble: '「早…早上好！平安无事真是太好了呢 ✨」',
        sub: 'お…おはよう！よかったね、本当によかったね！',
        voiceKey: 'nezuko_ohayou',
        toneClass: 'hover:bg-amber-500/25 text-amber-200',
      },
      {
        action: 'dash',
        label: '狂奔',
        bubble: '豆豆眼变小形态 · 风火轮极速狂奔！',
        sub: 'ん〜っ！んん〜っ！',
        voiceKey: 'nezuko_box',
        toneClass: 'hover:bg-sky-500/25 text-sky-200',
      },
      {
        action: 'stomp',
        label: '跺脚',
        bubble: '「唔嗯——！！鼓起腮帮子气鼓鼓跺脚抗议！」',
        sub: 'むぅ〜っ！！んーっ！！もう怒ったぞーっ！',
        voiceKey: 'nezuko_angry',
        toneClass: 'hover:bg-orange-500/25 text-orange-200',
      },
      {
        action: 'blood',
        label: '爆血',
        bubble: '「血鬼术·爆血！！哥哥和大家，绝对由米豆子来守护！」',
        sub: '血鬼術・爆血！！みんなは絶対に私が守る！',
        voiceKey: 'nezuko_blood',
        toneClass: 'hover:bg-rose-500/25 text-pink-300',
      },
      {
        action: 'feed',
        label: '金平糖',
        bubble: '「唔嗯~♪ 亮晶晶的星空金平糖，最喜欢啦 ✨」',
        sub: 'ん〜っ♪ こんぺいとう、キラキラで大好きっ！',
        voiceKey: 'nezuko_box',
        toneClass: 'hover:bg-emerald-500/25 text-emerald-200',
      },
    ],
  },
  prince: {
    id: 'prince',
    name: 'B612 小王子 · 法语原声版',
    shortName: '小王子',
    badge: 'B612 · 法语童声',
    accent: '#38bdf8',
    secondaryAccent: '#fbbf24',
    particleKind: 'star',
    description:
      '回归初代经典明艳绘本原画并内置纯正法语童声原著独白：璀璨金卷发与晶莹蓝瞳自然眨眼、手捧玻璃罩玫瑰、温暖拥抱小狐狸、踏星漫步、44次日落与弯月星眠。',
    quotes: [
      {
        zh: '「只有用心才能看得清。真正重要的东西，用眼睛是看不见的。」',
        sub: "On ne voit bien qu'avec le cœur. L'essentiel est invisible pour les yeux.",
        voiceKey: 'prince_essential',
      },
      {
        zh: '「正因为你为你的玫瑰花费了时间，她才变得如此重要。」',
        sub: "C'est le temps que tu as perdu pour ta rose qui fait ta rose si importante.",
        voiceKey: 'prince_rose',
      },
      {
        zh: '「在我的 B612 小星球上，我一天看过四十四次金色日落。」',
        sub: "Sur ma petite planète, j'ai vu le soleil se coucher quarante-quatre fois.",
        voiceKey: 'prince_sunset',
      },
      {
        zh: '「如果你驯服了我，我们就彼此需要。对我而言你将是世上独一无二的。」',
        sub: "Si tu m'apprivoises, nous aurons besoin l'un de l'autre.",
        voiceKey: 'prince_fox',
      },
    ],
    doubleClickAction: 'stars',
    doubleClickBubble: '「真正重要的东西，用眼睛是看不见的 ✨」',
    doubleClickSub: "On ne voit bien qu'avec le cœur. L'essentiel est invisible pour les yeux.",
    doubleClickVoiceKey: 'prince_essential',
    actions: [
      {
        action: 'pat',
        label: '金句',
        bubble: '「只有用心才能看得清。真正重要的东西，用眼睛是看不见的 ✨」',
        sub: "L'essentiel est invisible pour les yeux.",
        voiceKey: 'prince_essential',
        toneClass: 'hover:bg-sky-500/25 text-sky-200',
      },
      {
        action: 'fox',
        label: '狐狸',
        bubble: '「如果你驯服了我，我们彼此就需要对方 🦊」',
        sub: "Si tu m'apprivoises, nous aurons besoin l'un de l'autre.",
        voiceKey: 'prince_fox',
        toneClass: 'hover:bg-amber-500/25 text-amber-200',
      },
      {
        action: 'rose',
        label: '玫瑰',
        bubble: '「因为你为你的玫瑰花费了时间，她才变得如此重要 🌹」',
        sub: "C'est le temps que tu as perdu pour ta rose...",
        voiceKey: 'prince_rose',
        toneClass: 'hover:bg-rose-500/25 text-rose-200',
      },
      {
        action: 'stars',
        label: '流星',
        bubble: '「在我的星球上，我一天看过四十四次金色日落 🌠」',
        sub: "J'ai vu le soleil se coucher quarante-quatre fois.",
        voiceKey: 'prince_sunset',
        toneClass: 'hover:bg-indigo-500/25 text-indigo-200',
      },
      {
        action: 'volcano',
        label: '火山',
        bubble: '认真清扫 B612 星球的小火山烟尘 🌋',
        toneClass: 'hover:bg-orange-500/25 text-orange-200',
      },
      {
        action: 'walk',
        label: '漫步',
        bubble: '金黄丝巾随风飘扬，踏着星尘轻盈漫步',
        toneClass: 'hover:bg-purple-500/25 text-purple-200',
      },
    ],
  },
  ushio: {
    id: 'ushio',
    name: '冈崎汐 · 团子原声版',
    shortName: '冈崎汐',
    badge: 'CLANNAD · 原声金句',
    accent: '#f59e0b',
    secondaryAccent: '#f472b6',
    particleKind: 'dango',
    description:
      '内置《CLANNAD ~AFTER STORY~》小汐原生稚嫩日语催泪金句与《团子大家族》童声哼唱：双呆毛眨眼、团子叠叠乐、花田小机器人、愿望光玉与团子甜睡。',
    quotes: [
      {
        zh: '「能哭的地方，只有厕所，和爸爸的怀里…」',
        sub: '泣いていいのは、おトイレか、パパの胸の中だけだって…',
        voiceKey: 'ushio_toilet',
      },
      {
        zh: '「团子，团子，团子，团子，团子大家族 ♪ 要一直在一起哦！」',
        sub: '♪ だんご だんご だんご大家族 — CLANNAD 原动画 ED 原曲（茶太）',
        voiceKey: 'ushio_dango',
      },
      {
        zh: '「那个呀…是爸爸第一个买给我的，全世界独一无二的宝物哦 🌻」',
        sub: 'パパが一番最初に買ってくれた、大事な宝物なの！',
        voiceKey: 'ushio_robot',
      },
      {
        zh: '「早苗奶奶说已经不用再忍耐了…满天都是光玉，最喜欢爸爸了 ✨」',
        sub: 'もう我慢しなくていいって…ほら、光の玉がいっぱいだよ！',
        voiceKey: 'ushio_sanae',
      },
      {
        zh: '「嗯！一起出门旅行好开心呀！粉色大团子也要一起去哦，嘿嘿 ♪」',
        sub: 'うん！お出かけたのしいね！おっきいだんごも一緒に行くの♪',
        voiceKey: 'ushio_trip',
      },
      {
        zh: '「唔…眼皮快合上啦…晚安呀，愿你也能做个暖呼呼的好梦…」',
        sub: 'おやすみなさい、あったかい夢が見られますように…',
        voiceKey: 'ushio_sleep',
      },
    ],
    doubleClickAction: 'dango_song',
    doubleClickBubble: '🎵 正在播放《CLANNAD》原动画 ED《团子大家族》原曲 ♪',
    doubleClickSub: '♪ だんご だんご だんご大家族 — 茶太（原动画真曲）',
    doubleClickVoiceKey: 'ushio_dango',
    actions: [
      {
        action: 'pat',
        label: '催泪金句',
        bubble: '「能哭的地方，只有厕所，和爸爸的怀里…」',
        sub: '泣いていいのは、おトイレか、パパの胸の中だけだって…',
        voiceKey: 'ushio_toilet',
        toneClass: 'hover:bg-pink-500/35 text-pink-100',
      },
      {
        action: 'dango_song',
        label: '团子歌',
        bubble: '🎵 正在播放《CLANNAD》原动画 ED《团子大家族》原曲 ♪',
        sub: '♪ だんご だんご だんご大家族 — 茶太（再次点击可停止）',
        voiceKey: 'ushio_dango',
        toneClass: 'hover:bg-amber-500/35 text-amber-100',
      },
      {
        action: 'sunflower',
        label: '花田宝物',
        bubble: '「那个呀…是爸爸第一个买给我的，全世界独一无二的宝物哦 🌻」',
        sub: 'パパが一番最初に買ってくれた、大事な宝物なの！',
        voiceKey: 'ushio_robot',
        toneClass: 'hover:bg-yellow-500/25 text-yellow-200',
      },
      {
        action: 'light_orb',
        label: '光玉约定',
        bubble: '「早苗奶奶说不用再忍耐了…满天都是光玉，最喜欢爸爸了 ✨」',
        sub: 'もう我慢しなくていいって…パパ、大好き！',
        voiceKey: 'ushio_sanae',
        toneClass: 'hover:bg-sky-500/25 text-sky-200',
      },
      {
        action: 'dash',
        label: '远行小跑',
        bubble: '「嗯！一起出门旅行好开心呀！粉色大团子也要一起去哦 ♪」',
        sub: 'お出かけ、たのしいね！だんごも一緒に行くの！',
        voiceKey: 'ushio_trip',
        toneClass: 'hover:bg-emerald-500/25 text-emerald-200',
      },
      {
        action: 'feed',
        label: '甜团子',
        bubble: '一口吃掉甜甜糯米团（悄悄躲开早苗奶奶的特制面包啦~）🍡',
        sub: 'おっきいだんごも一緒に行くの、えへへっ！',
        voiceKey: 'ushio_trip',
        toneClass: 'hover:bg-rose-500/25 text-rose-200',
      },
    ],
  },
  tanjiro: {
    id: 'tanjiro',
    name: '灶门炭治郎 · 3D 手办原声版',
    shortName: '炭治郎',
    badge: '3D 潮玩 · 碧海原声',
    accent: '#14b8a6',
    secondaryAccent: '#38bdf8',
    particleKind: 'water',
    description:
      '全新 3D 潮玩手办建模多姿态（待机眨眼、3D 水之呼吸漩涡挥刀、巡山疾跑、捧梅子饭团欢笑）与热血日语原声。',
    quotes: [
      {
        zh: '「加油！！心是人的原动力，心是可以无限变强的！」',
        sub: '頑張れ！！人は心が原動力だ！心はどこまでも強くなれる！',
        voiceKey: 'tanjiro_encourage',
      },
      {
        zh: '「全集中·水之呼吸！拾之型——生生流转 🌊」',
        sub: '全集中、水の呼吸！拾ノ型、生生流転！！',
        voiceKey: 'tanjiro_water',
      },
      {
        zh: '「闻到了隙之线的气息，今天也元气满满一起加油吧 ☀️」',
        sub: '頑張れ！！心はどこまでも強くなれる！',
        voiceKey: 'tanjiro_encourage',
      },
    ],
    doubleClickAction: 'water_slash',
    doubleClickBubble: '「全集中·水之呼吸！拾之型——生生流转 🌊」',
    doubleClickSub: '全集中、水の呼吸！拾ノ型、生生流転！！',
    doubleClickVoiceKey: 'tanjiro_water',
    actions: [
      {
        action: 'pat',
        label: '鼓励',
        bubble: '「加油！！心是人的原动力，心是可以无限变强的 ☀️」',
        sub: '頑張れ！！人は心が原動力だ！',
        voiceKey: 'tanjiro_encourage',
        toneClass: 'hover:bg-emerald-500/35 text-emerald-100',
      },
      {
        action: 'water_slash',
        label: '水之呼吸',
        bubble: '「全集中·水之呼吸！拾之型——生生流转 🌊」',
        sub: '全集中、水の呼吸！拾ノ型、生生流転！！',
        voiceKey: 'tanjiro_water',
        toneClass: 'hover:bg-cyan-500/35 text-cyan-100',
      },
      { action: 'dash', label: '疾跑', bubble: '背着木箱 3D 巡山步极速驰援！', toneClass: 'hover:bg-sky-500/35 text-sky-100' },
      { action: 'feed', label: '饭团', bubble: '捧着海苔梅子饭团幸福大笑 🍙', sub: 'うまいっ！！元気百倍だ！', voiceKey: 'tanjiro_encourage', toneClass: 'hover:bg-amber-500/35 text-amber-100' },
      { action: 'walk', label: '巡逻', bubble: '背着木箱沿桌面稳健巡航…', toneClass: 'hover:bg-teal-500/35 text-teal-100' },
    ],
  },
  zenitsu: {
    id: 'zenitsu',
    name: '我妻善逸 · 3D 手办原声版',
    shortName: '善逸',
    badge: '3D 潮玩 · 金雷原声',
    accent: '#facc15',
    secondaryAccent: '#fb923c',
    particleKind: 'lightning',
    description:
      '全新 3D 潮玩手办建模多姿态（头顶小麻雀啾太郎待机眨眼、3D 霹雳一闪金雷拔刀、捧腮甜笑、抱膝酣睡）与日语原声。',
    quotes: [
      {
        zh: '「雷之呼吸·壹之型——霹雳一闪·六连 ⚡」',
        sub: '雷の呼吸、壱ノ型——霹靂一閃、六連！！',
        voiceKey: 'zenitsu_thunder',
      },
      {
        zh: '「呜哇啊啊~ 你好温柔啊！我绝对会保护好你的 💛」',
        sub: 'うわぁぁん！優しい〜！俺、絶対に君のこと守るからね！',
        voiceKey: 'zenitsu_care',
      },
      {
        zh: '「只要专注把一件事登峰造极，就一定能化作金雷发光 ⚡」',
        sub: '雷の呼吸、壱ノ型——霹靂一閃！！',
        voiceKey: 'zenitsu_thunder',
      },
    ],
    doubleClickAction: 'thunder_dash',
    doubleClickBubble: '「雷之呼吸·壹之型——霹雳一闪·六连 ⚡」',
    doubleClickSub: '雷の呼吸、壱ノ型——霹靂一閃、六連！！',
    doubleClickVoiceKey: 'zenitsu_thunder',
    actions: [
      {
        action: 'pat',
        label: '顺毛',
        bubble: '「呜哇啊啊~ 终于有人温柔夸我啦，我绝对会保护你的 💛」',
        sub: 'うわぁぁん！優しい〜！絶対に君のこと守るからね！',
        voiceKey: 'zenitsu_care',
        toneClass: 'hover:bg-yellow-500/35 text-yellow-100',
      },
      {
        action: 'thunder_dash',
        label: '霹雳一闪',
        bubble: '「雷之呼吸·壹之型——霹雳一闪·六连 ⚡」',
        sub: '雷の呼吸、壱ノ型——霹靂一閃、六連！！',
        voiceKey: 'zenitsu_thunder',
        toneClass: 'hover:bg-amber-500/35 text-amber-100',
      },
      { action: 'stomp', label: '惊呼', bubble: '噫！！啾太郎发现可疑报错气息！', toneClass: 'hover:bg-orange-500/35 text-orange-100' },
      { action: 'feed', label: '甜点', bubble: '和啾太郎一起幸福品尝蜂蜜甜点 🍰', voiceKey: 'zenitsu_care', toneClass: 'hover:bg-pink-500/35 text-pink-100' },
      { action: 'sleep', label: '觉醒眠', bubble: '和啾太郎依偎进入半睡半醒雷神待机态…', toneClass: 'hover:bg-indigo-500/35 text-indigo-100' },
    ],
  },
  inosuke: {
    id: 'inosuke',
    name: '嘴平伊之助 · 3D 手办原声版',
    shortName: '伊之助',
    badge: '3D 潮玩 · 兽王原声',
    accent: '#60a5fa',
    secondaryAccent: '#34d399',
    particleKind: 'spark',
    description:
      '全新 3D 毛绒潮玩手办多姿态（野猪头套双刀待机眨眼、3D 兽之呼吸双刀斩、举炸虾天妇罗飘飘然、抱刀酣睡）与狂野日语原声。',
    quotes: [
      {
        zh: '「兽之呼吸！猪突猛进！！猪突猛进 🐗」',
        sub: '獣の呼吸！猪突猛進！！猪突猛進！！',
        voiceKey: 'inosuke_rush',
      },
      {
        zh: '「哇哈哈哈！再多夸夸本山大王吧（飘飘然~）✨」',
        sub: 'ふはははっ！もっと俺様を褒め称えろ！ほわほわ〜！',
        voiceKey: 'inosuke_praise',
      },
      {
        zh: '「来比试谁先跑通全部构建吧！哇哈哈哈 🐗」',
        sub: '獣の呼吸！猪突猛進！！',
        voiceKey: 'inosuke_rush',
      },
    ],
    doubleClickAction: 'beast_rush',
    doubleClickBubble: '「兽之呼吸！猪突猛进！！猪突猛进 🐗」',
    doubleClickSub: '獣の呼吸！猪突猛進！！猪突猛進！！',
    doubleClickVoiceKey: 'inosuke_rush',
    actions: [
      {
        action: 'pat',
        label: '夸奖',
        bubble: '「哇哈哈哈！再多夸夸本大爷（飘飘然~）✨」',
        sub: 'ふはははっ！もっと俺様を褒め称えろ！ほわほわ〜！',
        voiceKey: 'inosuke_praise',
        toneClass: 'hover:bg-sky-500/35 text-sky-100',
      },
      {
        action: 'beast_rush',
        label: '猪突猛进',
        bubble: '「兽之呼吸！猪突猛进！！猪突猛进 🐗」',
        sub: '獣の呼吸！猪突猛進！！猪突猛進！！',
        voiceKey: 'inosuke_rush',
        toneClass: 'hover:bg-indigo-500/35 text-indigo-100',
      },
      { action: 'feed', label: '天妇罗', bubble: '高举黄金酥脆炸虾天妇罗得意欢呼 🍤', sub: 'ほわほわ〜！天ぷら最高だぜ！', voiceKey: 'inosuke_praise', toneClass: 'hover:bg-amber-500/35 text-amber-100' },
      { action: 'dance', label: '庆功舞', bubble: '山大王胜利狂欢热舞开启 ♪', toneClass: 'hover:bg-emerald-500/35 text-emerald-100' },
      { action: 'sleep', label: '酣睡', bubble: '怀抱双把锯齿日轮刀盘腿呼呼大睡…', toneClass: 'hover:bg-purple-500/35 text-purple-100' },
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

/** 桌面伴侣上下文字控制栏默认无操作自动隐藏延时（毫秒） */
export const PET_HUD_AUTO_HIDE_MS = 4500;
/** 展开角色选择抽屉或配额/歌词扩展舱时的无操作自动隐藏延时（毫秒） */
export const PET_HUD_SUBPANEL_AUTO_HIDE_MS = 8000;

export interface HudAutoHideState {
  hudVisible: boolean;
  hudInteracting: boolean;
  pickerOpen: boolean;
  panelMode: 'none' | 'quota' | 'music';
}

/**
 * 计算当前状态下桌面伴侣上下文字面板的自动隐藏倒计时毫秒数：
 * - 面板未展示或指针/键盘焦点正停留在上下文字面板内操作时，返回 `null`（暂停计时）
 * - 展开了二级抽屉/遥测舱且指针已移开时，延长至 8000ms
 * - 常规展开态无点击交互时，4500ms 后自动淡出隐藏
 */
export function resolveHudAutoHideDelayMs(state: HudAutoHideState): number | null {
  if (!state.hudVisible || state.hudInteracting) {
    return null;
  }
  if (state.pickerOpen || state.panelMode !== 'none') {
    return PET_HUD_SUBPANEL_AUTO_HIDE_MS;
  }
  return PET_HUD_AUTO_HIDE_MS;
}

