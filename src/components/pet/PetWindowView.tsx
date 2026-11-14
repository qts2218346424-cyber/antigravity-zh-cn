import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { listen } from '@tauri-apps/api/event';
import {
  Activity,
  Disc3,
  Heart,
  Music,
  Pause,
  Pin,
  PinOff,
  Play,
  SkipBack,
  SkipForward,
  Sparkles,
  Sun,
  X,
} from 'lucide-react';
import { studioService } from '../../services/studioService';
import { useAccountStore } from '../../stores/useAccountStore';
import type { MediaStatus, PetAssets } from '../../types/studio';
import { isTauri } from '../../utils/env';

type PetCharacter = 'nezuko' | 'prince';
type PetAction = 'idle' | 'pat' | 'sleep' | 'box_spin' | 'blood' | 'dance' | 'feed';

interface Particle {
  id: number;
  x: number;
  y: number;
  scale: number;
  rotate: number;
  kind: 'petal' | 'spark' | 'star';
}

const NEZUKO_QUOTES = [
  '唔嗯~ 灵感正在充能中',
  '血鬼术·爆血，驱散一切隐蔽漏洞',
  '钻进竹篓安静歇息一会儿…',
  '不管任务多复杂，都会一直陪着你哦',
  '摸摸头，今天架构写得真漂亮',
];

const PRINCE_QUOTES = [
  '“真正重要的东西，用眼睛是看不见的。”',
  '“因为你为你的玫瑰花费了时间，她才变得如此重要。”',
  '“我在 B612 星球上看过四十四次日落。”',
  '“如果你驯服了我，我们彼此就需要对方。”',
  '“所有大人都曾经是小孩，虽然只有少数人记得。”',
];

function parseLrcLines(lrc: string): string[] {
  if (!lrc) return [];
  return lrc
    .split(/\r?\n/)
    .map((line) => line.replace(/\[\d{1,2}:\d{2}(?:[.:]\d{1,3})?\]/g, '').trim())
    .filter((text) => text.length > 0 && !text.startsWith('ti:') && !text.startsWith('ar:'));
}

/** 矢量物理粒子节点：渲染樱花花瓣、极光微芒与 B612 星尘 */
const ParticleSvg: React.FC<{ p: Particle; accentColor: string }> = ({ p, accentColor }) => {
  return (
    <div
      className="pointer-events-none absolute animate-ping"
      style={{
        left: `${p.x}%`,
        top: `${p.y}%`,
        transform: `scale(${p.scale}) rotate(${p.rotate}deg)`,
        animationDuration: '1.8s',
      }}
    >
      {p.kind === 'petal' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2C15 7 20 10 18 16C16 21 8 21 6 16C4 10 9 7 12 2Z"
            fill={accentColor}
            fillOpacity="0.88"
          />
        </svg>
      )}
      {p.kind === 'star' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2L14.2 9.8L22 12L14.2 14.2L12 22L9.8 14.2L2 12L9.8 9.8L12 2Z"
            fill="#fde68a"
            fillOpacity="0.95"
          />
        </svg>
      )}
      {p.kind === 'spark' && (
        <span
          className="block h-2 w-2 rounded-full blur-[0.5px]"
          style={{
            backgroundColor: accentColor,
            boxShadow: `0 0 10px ${accentColor}`,
          }}
        />
      )}
    </div>
  );
};

const PetWindowView: React.FC = () => {
  const [character, setCharacter] = useState<PetCharacter>('nezuko');
  const [action, setAction] = useState<PetAction>('idle');
  const [bubble, setBubble] = useState<string>('已连接工作室感官核心');
  const [assets, setAssets] = useState<PetAssets>({});
  const [panelMode, setPanelMode] = useState<'none' | 'quota' | 'music'>('none');
  const [alwaysOnTop, setAlwaysOnTop] = useState(true);
  const [sunsetMode, setSunsetMode] = useState(false);
  const [particles, setParticles] = useState<Particle[]>([]);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [media, setMedia] = useState<MediaStatus>({
    isPlaying: false,
    title: '',
    artist: '',
    rawTitle: '',
    source: '',
    lrc: '',
  });
  const [lrcOffset, setLrcOffset] = useState(0);

  const actionTimerRef = useRef<number | null>(null);
  const { currentAccount, fetchCurrentAccount } = useAccountStore();

  useEffect(() => {
    document.documentElement.classList.add('pet-window');
    document.body.classList.add('pet-window');
    const root = document.getElementById('root');
    if (root) root.classList.add('pet-root');

    studioService.getPetAssets().then(setAssets).catch(console.error);
    studioService
      .getStatus()
      .then((st) => {
        if (
          st.splash_character === 'prince' ||
          st.active_skin === 'midnight-dark' ||
          st.active_skin === 'obsidian-glass' ||
          st.active_skin === 'nordic-aurora'
        ) {
          setCharacter('prince');
          setBubble(PRINCE_QUOTES[0]);
        }
      })
      .catch(() => {});

    fetchCurrentAccount().catch(() => {});
    const quotaTimer = window.setInterval(() => {
      fetchCurrentAccount().catch(() => {});
    }, 30000);

    let unlisten: (() => void) | undefined;
    if (isTauri()) {
      listen<string>('pet:character-changed', (ev) => {
        const ch = ev.payload === 'prince' || ev.payload === 'little-prince' ? 'prince' : 'nezuko';
        setCharacter(ch);
        setBubble(ch === 'prince' ? PRINCE_QUOTES[0] : NEZUKO_QUOTES[0]);
      })
        .then((fn) => {
          unlisten = fn;
        })
        .catch(() => {});
    }

    return () => {
      window.clearInterval(quotaTimer);
      if (unlisten) unlisten();
      document.documentElement.classList.remove('pet-window');
      document.body.classList.remove('pet-window');
      if (root) root.classList.remove('pet-root');
    };
  }, [fetchCurrentAccount]);

  useEffect(() => {
    if (!isTauri()) return;
    const height = panelMode === 'none' ? 335 : 495;
    studioService.setPetSize(350, height).catch(() => {});
  }, [panelMode]);

  useEffect(() => {
    let timer: number | null = null;
    const poll = () => {
      studioService
        .getMediaStatus()
        .then((res) => {
          setMedia((prev) => {
            if (prev.rawTitle !== res.rawTitle) setLrcOffset(0);
            return res;
          });
        })
        .catch(() => {});
    };
    poll();
    timer = window.setInterval(poll, 2600);
    return () => {
      if (timer) window.clearInterval(timer);
    };
  }, []);

  const parsedLyrics = useMemo(() => parseLrcLines(media.lrc), [media.lrc]);

  useEffect(() => {
    if (!media.isPlaying || parsedLyrics.length === 0) return;
    const t = window.setInterval(() => {
      setLrcOffset((n) => (n + 1) % parsedLyrics.length);
    }, 3200);
    return () => window.clearInterval(t);
  }, [media.isPlaying, parsedLyrics]);

  const triggerAction = useCallback(
    (next: PetAction, msg?: string) => {
      if (actionTimerRef.current) {
        window.clearTimeout(actionTimerRef.current);
      }
      setAction(next);
      if (msg) {
        setBubble(msg);
      } else if (character === 'prince') {
        setBubble(PRINCE_QUOTES[Math.floor(Math.random() * PRINCE_QUOTES.length)]);
      } else {
        setBubble(NEZUKO_QUOTES[Math.floor(Math.random() * NEZUKO_QUOTES.length)]);
      }

      if (next === 'blood' || next === 'pat' || next === 'feed') {
        const kind: Particle['kind'] =
          character === 'prince' ? 'star' : next === 'blood' ? 'petal' : 'spark';
        const batch: Particle[] = Array.from({ length: 11 }, (_, idx) => ({
          id: Date.now() + idx,
          x: 16 + Math.random() * 68,
          y: 10 + Math.random() * 55,
          scale: 0.7 + Math.random() * 0.7,
          rotate: Math.round(Math.random() * 360),
          kind,
        }));
        setParticles(batch);
        window.setTimeout(() => setParticles([]), 2000);
      }

      if (next !== 'sleep' && next !== 'dance') {
        actionTimerRef.current = window.setTimeout(() => {
          setAction('idle');
        }, 2800);
      }
    },
    [character],
  );

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
    const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
    setTilt({ x: nx, y: ny });
  };

  const handleStartDrag = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) return;
    if (isTauri()) {
      getCurrentWindow().startDragging().catch(() => {});
    }
  };

  const toggleCharacter = () => {
    const next: PetCharacter = character === 'nezuko' ? 'prince' : 'nezuko';
    setCharacter(next);
    setAction('idle');
    setBubble(next === 'prince' ? '欢迎回到 B612 星球观测站' : '祢豆子已进入伴随待命');
  };

  const toggleTop = () => {
    const next = !alwaysOnTop;
    setAlwaysOnTop(next);
    studioService.setPetAlwaysOnTop(next).catch(() => {});
  };

  const activeImg = useMemo(() => {
    if (character === 'prince') {
      if (action === 'pat' && assets.prince_fox) return assets.prince_fox;
      return assets.little_prince || null;
    }
    if (action === 'sleep' && assets.nezuko_basket) return assets.nezuko_basket;
    if (action === 'box_spin' && assets.nezuko_spin_sheet) return assets.nezuko_spin_sheet;
    return assets.nezuko_chibi || null;
  }, [character, action, assets]);

  const topModels = useMemo(() => {
    const list = currentAccount?.quota?.models || [];
    return list.slice(0, 4);
  }, [currentAccount]);

  const themeAccent =
    character === 'nezuko'
      ? action === 'blood'
        ? '#fb7185'
        : '#f472b6'
      : sunsetMode
        ? '#f59e0b'
        : '#38bdf8';

  const animClass =
    action === 'box_spin'
      ? 'animate-spin'
      : action === 'blood' || action === 'feed'
        ? '-translate-y-2 scale-105'
        : action === 'dance'
          ? 'animate-pulse scale-105'
          : action === 'sleep'
            ? 'scale-90 opacity-90 translate-y-2'
            : 'hover:scale-[1.04]';

  return (
    <div
      onMouseDown={handleStartDrag}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setTilt({ x: 0, y: 0 })}
      className="relative flex h-screen w-screen flex-col items-center justify-end select-none p-2.5 bg-transparent overflow-hidden"
    >
      {/* 顶部 Apple 灵动岛黑曜石玻璃控制坞 */}
      <div
        className="mb-2 flex items-center gap-1 rounded-full bg-slate-950/75 px-2.5 py-1 text-white backdrop-blur-2xl border border-white/15"
        style={{
          boxShadow: '0 14px 32px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.2)',
        }}
      >
        <button
          onClick={toggleCharacter}
          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 text-[11px] font-semibold rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
          title="切换陪伴角色"
        >
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: themeAccent, boxShadow: `0 0 8px ${themeAccent}` }}
          />
          {character === 'nezuko' ? '祢豆子' : '小王子'}
        </button>

        <div className="h-3 w-px bg-white/15 mx-0.5" />

        <button
          onClick={() => setPanelMode((m) => (m === 'quota' ? 'none' : 'quota'))}
          className={`p-1.5 rounded-full transition-colors ${
            panelMode === 'quota' ? 'bg-sky-500/30 text-sky-300' : 'hover:bg-white/10 text-slate-300'
          }`}
          title="算力配额遥测"
        >
          <Activity className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setPanelMode((m) => (m === 'music' ? 'none' : 'music'))}
          className={`p-1.5 rounded-full transition-colors ${
            panelMode === 'music'
              ? 'bg-emerald-500/30 text-emerald-300'
              : media.isPlaying
                ? 'text-emerald-400 hover:bg-white/10'
                : 'hover:bg-white/10 text-slate-300'
          }`}
          title="声学黑胶歌词舱"
        >
          <Music className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={toggleTop}
          className="p-1.5 rounded-full hover:bg-white/10 text-slate-300 transition-colors"
          title={alwaysOnTop ? '取消置顶' : '窗口置顶'}
        >
          {alwaysOnTop ? <Pin className="w-3.5 h-3.5 text-amber-300" /> : <PinOff className="w-3.5 h-3.5" />}
        </button>
        <button
          onClick={() => studioService.closePet().catch(() => {})}
          className="p-1.5 rounded-full hover:bg-rose-500/30 text-slate-300 hover:text-rose-200 transition-colors"
          title="收起桌面伴侣"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 玻璃微胶囊对白气泡 */}
      <div
        className="mb-2 max-w-[300px] rounded-2xl bg-slate-950/75 px-3.5 py-1.5 text-center text-[11.5px] font-medium text-slate-100 backdrop-blur-2xl border border-white/15 transition-all"
        style={{
          boxShadow: '0 10px 28px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.16)',
        }}
      >
        {bubble}
      </div>

      {/* 3D 视差生态玻璃容器舞台 (Living Terrarium Stage) */}
      <div
        id="nezuko-pet-stage"
        className="relative flex h-44 w-60 items-end justify-center cursor-grab active:cursor-grabbing"
        style={{
          perspective: '720px',
        }}
      >
        {/* 远景环境体积光晕（随主题与动作呼吸渐变） */}
        <div
          className="pointer-events-none absolute inset-4 rounded-full blur-2xl transition-all duration-700"
          style={{
            background: `radial-gradient(circle, ${themeAccent}42 0%, transparent 72%)`,
            transform: `translate3d(${tilt.x * -8}px, ${tilt.y * -8}px, 0)`,
          }}
        />

        {/* 小王子多层视差环境 */}
        {character === 'prince' && (
          <>
            {assets.prince_stars && (
              <img
                src={assets.prince_stars}
                alt=""
                className="pointer-events-none absolute inset-0 h-full w-full object-contain opacity-80 animate-pulse"
                style={{
                  transform: `translate3d(${tilt.x * -10}px, ${tilt.y * -6}px, 0)`,
                  transition: 'transform 160ms ease-out',
                }}
              />
            )}
            {sunsetMode && assets.prince_sunset && (
              <img
                src={assets.prince_sunset}
                alt=""
                className="pointer-events-none absolute inset-1 h-full w-full object-cover rounded-full opacity-55 mix-blend-screen"
                style={{
                  transform: `translate3d(${tilt.x * -6}px, ${tilt.y * -4}px, 0)`,
                  transition: 'transform 160ms ease-out',
                }}
              />
            )}
            {assets.prince_rose && (
              <img
                src={assets.prince_rose}
                alt="玫瑰"
                className="pointer-events-none absolute bottom-3 right-5 h-12 w-12 object-contain drop-shadow-[0_6px_14px_rgba(0,0,0,0.5)]"
                style={{
                  transform: `translate3d(${tilt.x * 7}px, ${tilt.y * 5}px, 0)`,
                  transition: 'transform 160ms ease-out',
                }}
              />
            )}
          </>
        )}

        {/* 旋转冲能冲击波 */}
        {action === 'box_spin' && assets.shockwave && (
          <img
            src={assets.shockwave}
            alt=""
            className="pointer-events-none absolute bottom-1 h-28 w-44 object-contain opacity-85 animate-ping"
          />
        )}

        {/* 物理矢量微粒 */}
        {particles.map((p) => (
          <ParticleSvg key={p.id} p={p} accentColor={themeAccent} />
        ))}

        {/* 前景角色接触投影（物理软椭圆形底影） */}
        <div
          className="pointer-events-none absolute bottom-1.5 h-3.5 w-28 rounded-full bg-black/55 blur-md transition-transform duration-300"
          style={{
            transform: `translate3d(${tilt.x * 4}px, 0, 0) scale(${action === 'blood' ? 0.82 : 1})`,
          }}
        />

        {/* 前景 3D 视差人物本体 */}
        <div
          id="pet-character-viewport"
          onClick={() =>
            triggerAction(
              'pat',
              character === 'prince' ? '小狐狸顺从地依偎过来 ✨' : '唔嗯♥ 感受到你的温暖啦',
            )
          }
          className={`relative flex h-36 w-36 items-center justify-center transition-all duration-300 ease-out ${animClass}`}
          style={{
            transform: `rotateX(${tilt.y * -7}deg) rotateY(${tilt.x * 9}deg) translate3d(${tilt.x * 6}px, ${tilt.y * 4}px, 0)`,
          }}
        >
          {activeImg ? (
            <img
              src={activeImg}
              alt={character}
              className="h-full w-full object-contain drop-shadow-[0_14px_24px_rgba(0,0,0,0.55)]"
              draggable={false}
            />
          ) : (
            <div
              className="flex h-28 w-28 flex-col items-center justify-center rounded-full text-white border border-white/25 backdrop-blur-xl shadow-2xl"
              style={{
                background: `linear-gradient(135deg, ${themeAccent}cc, #0f172a)`,
              }}
            >
              <Sparkles className="h-7 w-7 mb-1 opacity-90" />
              <span className="text-xs font-semibold">
                {character === 'nezuko' ? '灶门祢豆子' : '小王子'}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 底部磨砂互动控制胶囊 */}
      <div
        id="nezuko-action-capsule"
        className="mt-2 flex flex-wrap items-center justify-center gap-1 rounded-full bg-slate-950/75 px-2.5 py-1 text-[11px] font-medium text-slate-200 border border-white/15 backdrop-blur-2xl"
        style={{
          boxShadow: '0 10px 26px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.16)',
        }}
      >
        {character === 'nezuko' ? (
          <>
            <button
              onClick={() => triggerAction('pat', '轻抚发梢 ~ 心情指数 +100%')}
              className="px-2.5 py-0.5 rounded-full hover:bg-white/15 transition-colors"
            >
              摸头
            </button>
            <button
              onClick={() => triggerAction('blood', '血鬼术·爆血光华绽放')}
              className="px-2.5 py-0.5 rounded-full hover:bg-rose-500/25 text-pink-300 transition-colors"
            >
              爆血
            </button>
            <button
              onClick={() => triggerAction('box_spin', '竹箱奇点旋风觉醒')}
              className="px-2.5 py-0.5 rounded-full hover:bg-amber-500/25 text-amber-200 transition-colors"
            >
              旋风
            </button>
            <button
              onClick={() => triggerAction('feed', '尝了一颗星空金平糖 ✨')}
              className="px-2.5 py-0.5 rounded-full hover:bg-emerald-500/25 text-emerald-200 transition-colors"
            >
              投喂
            </button>
            <button
              onClick={() =>
                triggerAction(
                  action === 'sleep' ? 'idle' : 'sleep',
                  action === 'sleep' ? '休息完毕，重新点亮视野' : '缩小钻进竹篓休眠…',
                )
              }
              className="px-2.5 py-0.5 rounded-full hover:bg-indigo-500/25 transition-colors"
            >
              {action === 'sleep' ? '唤醒' : '休眠'}
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => triggerAction('pat')}
              className="px-2.5 py-0.5 rounded-full hover:bg-sky-500/25 transition-colors inline-flex items-center gap-1"
            >
              <Heart className="w-3 h-3 text-pink-300" />
              哲思语录
            </button>
            <button
              onClick={() => {
                setSunsetMode((s) => !s);
                setBubble(!sunsetMode ? 'B612 的第四十四次金色日落' : '深蓝星海悄然笼罩天穹');
              }}
              className="px-2.5 py-0.5 rounded-full hover:bg-amber-500/25 transition-colors inline-flex items-center gap-1"
            >
              <Sun className="w-3 h-3 text-amber-300" />
              {sunsetMode ? '星夜' : '日落'}
            </button>
            <button
              onClick={() => triggerAction('dance', '和小狐狸在星轨旁轻盈漫步')}
              className="px-2.5 py-0.5 rounded-full hover:bg-purple-500/25 transition-colors inline-flex items-center gap-1"
            >
              <Sparkles className="w-3 h-3 text-purple-300" />
              漫步
            </button>
          </>
        )}
      </div>

      {/* 扩展遥测 HUD：模型配额或声学黑胶律动舱 */}
      {panelMode !== 'none' && (
        <div
          id="nezuko-main-card"
          className="mt-2.5 w-full max-w-[330px] rounded-2xl bg-slate-950/85 p-3.5 text-xs text-slate-200 border border-white/15 backdrop-blur-2xl"
          style={{
            boxShadow: '0 22px 48px rgba(0,0,0,0.65), inset 0 1px 0 rgba(255,255,255,0.2)',
          }}
        >
          {panelMode === 'quota' && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-[11px]">
                <span className="truncate font-semibold text-sky-300 max-w-[210px]">
                  {currentAccount
                    ? currentAccount.custom_label || currentAccount.email
                    : '未检测到激活账号'}
                </span>
                <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-mono text-slate-300">
                  {currentAccount?.quota?.subscription_tier || 'FREE'}
                </span>
              </div>
              {topModels.length === 0 ? (
                <div className="text-center text-slate-400 py-2 text-[11px]">
                  请在管理器「账号管理」页签中绑定账号
                </div>
              ) : (
                <div className="space-y-2">
                  {topModels.map((m) => (
                    <div key={m.name} className="space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="truncate max-w-[205px] text-slate-300">
                          {m.display_name || m.name}
                        </span>
                        <span
                          className={`font-mono font-semibold ${
                            m.percentage < 20 ? 'text-rose-400' : 'text-emerald-400'
                          }`}
                        >
                          {m.percentage}%
                        </span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.max(0, Math.min(100, m.percentage))}%`,
                            background:
                              m.percentage < 20
                                ? 'linear-gradient(90deg, #f43f5e, #fb7185)'
                                : `linear-gradient(90deg, ${themeAccent}, #818cf8)`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {panelMode === 'music' && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between gap-2.5">
                {/* 旋转黑胶唱片图标 */}
                <div className="relative shrink-0 flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-slate-800 to-black border border-white/20 shadow-inner">
                  <Disc3
                    className={`h-6 w-6 text-emerald-400 ${media.isPlaying ? 'animate-spin' : ''}`}
                    style={{ animationDuration: '4s' }}
                  />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="truncate font-semibold text-white">
                    {media.isPlaying ? media.title || media.rawTitle : '声学频道待机中'}
                  </div>
                  <div className="truncate text-[10.5px] text-slate-400 flex items-center gap-1.5">
                    <span>
                      {media.isPlaying
                        ? `${media.artist || '未知歌手'} · ${media.source}`
                        : '打开 QQ音乐 / 网易云播放即可联动'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => studioService.sendMediaCommand('prev').catch(() => {})}
                    className="p-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                    title="上一曲"
                  >
                    <SkipBack className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      studioService.sendMediaCommand('play_pause').catch(() => {});
                      if (action !== 'dance') triggerAction('dance', '声波律动模式开启 ♪');
                    }}
                    className="p-1.5 rounded-full bg-emerald-500/25 hover:bg-emerald-500/45 text-emerald-300 transition-colors"
                    title="播放 / 暂停"
                  >
                    {media.isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    onClick={() => studioService.sendMediaCommand('next').catch(() => {})}
                    className="p-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                    title="下一曲"
                  >
                    <SkipForward className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* 电影级双行渐隐实时 LRC 歌词流 */}
              <div className="rounded-xl bg-black/45 px-3 py-2 border border-white/10 text-center space-y-1 min-h-[44px] flex flex-col justify-center">
                {parsedLyrics.length > 0 ? (
                  <>
                    <div className="text-[11.5px] font-semibold text-amber-200 truncate">
                      {parsedLyrics[lrcOffset % parsedLyrics.length]}
                    </div>
                    {parsedLyrics.length > 1 && (
                      <div className="text-[10px] text-slate-500 truncate">
                        {parsedLyrics[(lrcOffset + 1) % parsedLyrics.length]}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-[11px] text-slate-400">
                    {media.isPlaying
                      ? '♪ 正在享受纯音乐韵律 ♪'
                      : '播放曲目后自动检索并同步酷狗 LRC 歌词'}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PetWindowView;
