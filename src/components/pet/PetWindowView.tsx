import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { listen } from '@tauri-apps/api/event';
import {
  Activity,
  Disc3,
  Footprints,
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
  Volume2,
  VolumeX,
  Wind,
  X,
} from 'lucide-react';
import { studioService } from '../../services/studioService';
import { useAccountStore } from '../../stores/useAccountStore';
import type { MediaStatus, PetAssets } from '../../types/studio';
import { isTauri } from '../../utils/env';
import { petAudio } from './petAudio';
import './petAnimations.css';

type PetCharacter = 'nezuko' | 'prince';
type PetAction =
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
  | 'volcano';

interface Particle {
  id: number;
  x: number;
  y: number;
  scale: number;
  rotate: number;
  kind: 'petal' | 'spark' | 'star' | 'dust';
}

const NEZUKO_QUOTES = [
  '唔嗯~ 灵感与算力都在满格充能中',
  '血鬼术·爆血，驱散一切隐蔽 BUG',
  '钻进大正木箱安静打个盹…',
  '不管任务多复杂，都会一直陪在你身旁哦',
  '摸摸头~ 今天代码结构真优雅',
];

const PRINCE_QUOTES: { zh: string; sub: string }[] = [
  { zh: '真正重要的东西，用眼睛是看不见的。', sub: "L'essentiel est invisible pour les yeux." },
  { zh: '因为你为你的玫瑰花费了时间，她才变得如此重要。', sub: "C'est le temps que tu as perdu pour ta rose..." },
  { zh: '我在 B612 星球上看过四十四次金色日落。', sub: "J'ai vu quarante-quatre fois le soleil se coucher." },
  { zh: '如果你驯服了我，我们彼此就需要对方。', sub: 'Si tu m’apprivoises, nous aurons besoin l’un de l’autre.' },
  { zh: '所有大人都曾经是小孩，虽然只有少数人记得。', sub: 'Toutes les grandes personnes ont d’abord été des enfants.' },
];

const SCALE_PRESETS = [0.88, 1.0, 1.15];

function parseLrcLines(lrc: string): string[] {
  if (!lrc) return [];
  return lrc
    .split(/\r?\n/)
    .map((line) => line.replace(/\[\d{1,2}:\d{2}(?:[.:]\d{1,3})?\]/g, '').trim())
    .filter((text) => text.length > 0 && !text.startsWith('ti:') && !text.startsWith('ar:'));
}

/** B612 小王子 Verlet 物理金黄丝绸围巾实时 Canvas */
const PrinceScarfCanvas: React.FC<{ facing: 1 | -1; windBoost: number }> = ({ facing, windBoost }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const boostRef = useRef(windBoost);
  const facingRef = useRef(facing);
  boostRef.current = windBoost;
  facingRef.current = facing;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const COUNT = 7;
    const SEG = 11;
    const nodes = Array.from({ length: COUNT }, (_, i) => ({
      x: 78 - i * SEG,
      y: 72 + i * 2,
      ox: 78 - i * SEG,
      oy: 72 + i * 2,
    }));

    let raf = 0;
    let t = 0;
    const render = () => {
      t += 0.065;
      const windDir = facingRef.current === 1 ? -1 : 1;
      const speed = 1 + boostRef.current * 2.2;

      nodes[0].x = 76;
      nodes[0].y = 70;
      for (let i = 1; i < COUNT; i++) {
        const n = nodes[i];
        const vx = (n.x - n.ox) * 0.88;
        const vy = (n.y - n.oy) * 0.88;
        n.ox = n.x;
        n.oy = n.y;
        const wave = Math.sin(t * speed - i * 0.7) * (1.2 + boostRef.current * 1.6);
        n.x += vx + windDir * (1.1 + boostRef.current * 1.4);
        n.y += vy + 0.12 + wave * 0.38;
      }
      for (let iter = 0; iter < 4; iter++) {
        nodes[0].x = 76;
        nodes[0].y = 70;
        for (let i = 0; i < COUNT - 1; i++) {
          const a = nodes[i];
          const b = nodes[i + 1];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.hypot(dx, dy) || 0.001;
          const diff = (dist - SEG) / dist;
          if (i === 0) {
            b.x -= dx * diff;
            b.y -= dy * diff;
          } else {
            a.x += dx * diff * 0.5;
            a.y += dy * diff * 0.5;
            b.x -= dx * diff * 0.5;
            b.y -= dy * diff * 0.5;
          }
        }
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const grad = ctx.createLinearGradient(nodes[0].x, nodes[0].y, nodes[COUNT - 1].x, nodes[COUNT - 1].y);
      grad.addColorStop(0, 'rgba(250, 204, 21, 0.96)');
      grad.addColorStop(0.6, 'rgba(245, 158, 11, 0.9)');
      grad.addColorStop(1, 'rgba(253, 230, 138, 0.32)');

      ctx.beginPath();
      ctx.moveTo(nodes[0].x, nodes[0].y);
      for (let i = 1; i < COUNT - 1; i++) {
        const xc = (nodes[i].x + nodes[i + 1].x) * 0.5;
        const yc = (nodes[i].y + nodes[i + 1].y) * 0.5;
        ctx.quadraticCurveTo(nodes[i].x, nodes[i].y, xc, yc);
      }
      ctx.lineWidth = 10;
      ctx.lineCap = 'round';
      ctx.strokeStyle = grad;
      ctx.shadowBlur = 10;
      ctx.shadowColor = 'rgba(250, 204, 21, 0.5)';
      ctx.stroke();

      raf = requestAnimationFrame(render);
    };
    raf = requestAnimationFrame(render);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      width={160}
      height={150}
      className="pointer-events-none absolute -top-2 left-1/2 -translate-x-1/2 z-[12]"
    />
  );
};

/** 矢量物理微粒节点：渲染樱花花瓣、星光、星尘与地面扬尘 */
const ParticleSvg: React.FC<{ p: Particle; accentColor: string }> = ({ p, accentColor }) => {
  if (p.kind === 'dust') {
    return (
      <div
        className="dust-puff"
        style={{
          left: `${p.x}%`,
          '--dx': `${p.rotate > 180 ? 28 : -28}px`,
        } as React.CSSProperties}
      />
    );
  }
  return (
    <div
      className="pointer-events-none absolute animate-ping"
      style={{
        left: `${p.x}%`,
        top: `${p.y}%`,
        transform: `scale(${p.scale}) rotate(${p.rotate}deg)`,
        animationDuration: '1.65s',
      }}
    >
      {p.kind === 'petal' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M12 2C15 7 20 10 18 16C16 21 8 21 6 16C4 10 9 7 12 2Z" fill={accentColor} fillOpacity="0.92" />
        </svg>
      )}
      {p.kind === 'star' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L14.2 9.8L22 12L14.2 14.2L12 22L9.8 14.2L2 12L9.8 9.8L12 2Z" fill="#fde68a" />
        </svg>
      )}
      {p.kind === 'spark' && (
        <span
          className="block h-2 w-2 rounded-full blur-[0.5px]"
          style={{ backgroundColor: accentColor, boxShadow: `0 0 10px ${accentColor}` }}
        />
      )}
    </div>
  );
};

const PetWindowView: React.FC = () => {
  const [character, setCharacter] = useState<PetCharacter>('nezuko');
  const [action, setAction] = useState<PetAction>('idle');
  const [facing, setFacing] = useState<1 | -1>(1);
  const [roaming, setRoaming] = useState<boolean>(true);
  const [muted, setMuted] = useState<boolean>(false);
  const [scaleIdx, setScaleIdx] = useState<number>(1);
  const [blinking, setBlinking] = useState<boolean>(false);
  const [bubble, setBubble] = useState<string>('已连接工作室感官核心');
  const [subBubble, setSubBubble] = useState<string>('');
  const [moodIcon, setMoodIcon] = useState<string>('');
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
  const boxStepTimerRef = useRef<number | null>(null);
  const roamLoopRef = useRef<number | null>(null);
  const isHoveredRef = useRef(false);
  const actionRef = useRef<PetAction>('idle');
  actionRef.current = action;
  const facingRef = useRef<1 | -1>(1);
  facingRef.current = facing;

  const { currentAccount, fetchCurrentAccount } = useAccountStore();

  const clearActionTimers = useCallback(() => {
    if (actionTimerRef.current) {
      window.clearTimeout(actionTimerRef.current);
      actionTimerRef.current = null;
    }
    if (boxStepTimerRef.current) {
      window.clearTimeout(boxStepTimerRef.current);
      boxStepTimerRef.current = null;
    }
    if (roamLoopRef.current) {
      window.clearInterval(roamLoopRef.current);
      roamLoopRef.current = null;
    }
  }, []);

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
          setBubble(PRINCE_QUOTES[0].zh);
          setSubBubble(PRINCE_QUOTES[0].sub);
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
        if (ch === 'prince') {
          setBubble(PRINCE_QUOTES[0].zh);
          setSubBubble(PRINCE_QUOTES[0].sub);
        } else {
          setBubble(NEZUKO_QUOTES[0]);
          setSubBubble('');
        }
      })
        .then((fn) => {
          unlisten = fn;
        })
        .catch(() => {});
    }

    // 自然眨眼定时器
    const blinkTimer = window.setInterval(() => {
      setBlinking(true);
      window.setTimeout(() => setBlinking(false), 125);
    }, 3600);

    return () => {
      clearActionTimers();
      window.clearInterval(quotaTimer);
      window.clearInterval(blinkTimer);
      if (unlisten) unlisten();
      document.documentElement.classList.remove('pet-window');
      document.body.classList.remove('pet-window');
      if (root) root.classList.remove('pet-root');
    };
  }, [clearActionTimers, fetchCurrentAccount]);

  useEffect(() => {
    if (!isTauri()) return;
    const height = panelMode === 'none' ? 420 : 580;
    studioService.setPetSize(386, height).catch(() => {});
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

  const spawnBatch = useCallback((kind: Particle['kind'], count = 11) => {
    const batch: Particle[] = Array.from({ length: count }, (_, idx) => ({
      id: Date.now() + idx + Math.random(),
      x: 16 + Math.random() * 68,
      y: kind === 'dust' ? 85 : 10 + Math.random() * 55,
      scale: 0.7 + Math.random() * 0.65,
      rotate: Math.round(Math.random() * 360),
      kind,
    }));
    setParticles(batch);
    window.setTimeout(() => setParticles([]), 1600);
  }, []);

  const showMood = useCallback((icon: string, ms = 1800) => {
    setMoodIcon(icon);
    window.setTimeout(() => setMoodIcon(''), ms);
  }, []);

  const triggerAction = useCallback(
    (next: PetAction, msg?: string, durationMs = 2800) => {
      clearActionTimers();
      setAction(next);

      if (msg) {
        setBubble(msg);
        setSubBubble('');
      } else if (character === 'prince') {
        const q = PRINCE_QUOTES[Math.floor(Math.random() * PRINCE_QUOTES.length)];
        setBubble(q.zh);
        setSubBubble(q.sub);
      } else {
        setBubble(NEZUKO_QUOTES[Math.floor(Math.random() * NEZUKO_QUOTES.length)]);
        setSubBubble('');
      }

      if (next === 'pat') {
        petAudio.playCare();
        showMood('💗');
        spawnBatch(character === 'prince' ? 'star' : 'spark', 10);
      } else if (next === 'feed') {
        petAudio.playCare();
        showMood('🍬');
        spawnBatch('spark', 12);
      } else if (next === 'blood') {
        petAudio.playBloodBurst();
        showMood('🩸');
        spawnBatch('petal', 16);
      } else if (next === 'stomp') {
        petAudio.playWoodThud();
        showMood('💢');
        spawnBatch('dust', 6);
      } else if (next === 'fox' || next === 'rose') {
        petAudio.playStardust();
        showMood(next === 'fox' ? '🦊' : '🌹');
        spawnBatch('star', 10);
      } else if (next === 'stars') {
        petAudio.playShootingStar();
        showMood('🌠');
        spawnBatch('star', 14);
      } else if (next === 'volcano') {
        petAudio.playWoodThud();
        showMood('🌋');
      } else if (next === 'box_spin') {
        petAudio.playSpinWind();
        showMood('✨');
        boxStepTimerRef.current = window.setTimeout(() => {
          petAudio.playWoodThud();
          spawnBatch('petal', 12);
          setAction('box_peek');
          setBubble('从木箱里悄悄探出头来好奇张望 👀');
          actionTimerRef.current = window.setTimeout(() => {
            setAction('idle');
          }, 2400);
        }, 1250);
        return;
      } else if (next === 'dash') {
        petAudio.playSpinWind();
        showMood('💨');
        spawnBatch('dust', 8);
        let ticks = 0;
        roamLoopRef.current = window.setInterval(() => {
          ticks += 1;
          if (isTauri()) {
            studioService
              .nudgePet(facingRef.current * 14)
              .then((edge) => {
                if (edge === 1 || edge === -1) setFacing(edge);
              })
              .catch(() => {});
          }
          if (ticks >= 12) {
            if (roamLoopRef.current) window.clearInterval(roamLoopRef.current);
            petAudio.playFootstep();
            setAction('skid');
            setBubble('风火轮急刹车！稳稳停住 ✨');
            actionTimerRef.current = window.setTimeout(() => setAction('idle'), 450);
          }
        }, 65);
        return;
      } else if (next === 'walk') {
        petAudio.playFootstep();
        let ticks = 0;
        roamLoopRef.current = window.setInterval(() => {
          ticks += 1;
          if (character === 'prince' && ticks % 3 === 0) {
            spawnBatch('star', 3);
          }
          if (isTauri()) {
            studioService
              .nudgePet(facingRef.current * 5)
              .then((edge) => {
                if (edge === 1 || edge === -1) setFacing(edge);
              })
              .catch(() => {});
          }
          if (ticks >= 22) {
            if (roamLoopRef.current) window.clearInterval(roamLoopRef.current);
            setAction('idle');
          }
        }, 90);
        return;
      }

      if (next !== 'sleep' && next !== 'dance' && next !== 'picked_up') {
        actionTimerRef.current = window.setTimeout(() => {
          setAction('idle');
        }, durationMs);
      }
    },
    [character, clearActionTimers, showMood, spawnBatch],
  );

  // 自主桌边漫步心跳
  useEffect(() => {
    if (!roaming) return;
    const timer = window.setInterval(() => {
      if (isHoveredRef.current || panelMode !== 'none' || actionRef.current !== 'idle') return;
      const roll = Math.random();
      if (roll < 0.5) {
        if (Math.random() < 0.35) setFacing((f) => (f === 1 ? -1 : 1));
        triggerAction('walk', character === 'nezuko' ? '沿桌面散步巡航中…' : '踏着星尘缓缓踱步…');
      } else if (roll < 0.72) {
        triggerAction('dash', character === 'nezuko' ? '风火轮疾跑冲刺！' : '迎风飞奔去追落日余晖');
      } else if (roll < 0.85) {
        setFacing((f) => (f === 1 ? -1 : 1));
        showMood('❓');
      }
    }, 9500);
    return () => window.clearInterval(timer);
  }, [roaming, panelMode, character, triggerAction, showMood]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
    const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
    setTilt({ x: nx, y: ny });
  };

  const handleStartDrag = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (target.closest('button') || target.closest('input') || target.closest('a')) return;
    if (!isTauri() || e.button !== 0) return;
    setAction('picked_up');
    setBubble(character === 'nezuko' ? '呜哇~ 被拎起来啦，放手时会弹性落地哦' : '悬浮在星海半空之中 ✨');
    getCurrentWindow()
      .startDragging()
      .then(() => {
        petAudio.playFootstep();
        setAction('land_squash');
        window.setTimeout(() => setAction('idle'), 360);
      })
      .catch(() => setAction('idle'));
  };

  const toggleCharacter = () => {
    clearActionTimers();
    const next: PetCharacter = character === 'nezuko' ? 'prince' : 'nezuko';
    setCharacter(next);
    setAction('idle');
    if (next === 'prince') {
      setBubble(PRINCE_QUOTES[0].zh);
      setSubBubble(PRINCE_QUOTES[0].sub);
    } else {
      setBubble(NEZUKO_QUOTES[0]);
      setSubBubble('');
    }
    petAudio.playCare();
  };

  const toggleTop = () => {
    const next = !alwaysOnTop;
    setAlwaysOnTop(next);
    studioService.setPetAlwaysOnTop(next).catch(() => {});
  };

  const toggleMute = () => {
    const next = !muted;
    petAudio.muted = next;
    setMuted(next);
    setBubble(next ? '🔇 音效已静音' : '🔊 治愈互动音效已开启');
  };

  const themeAccent = character === 'nezuko' ? '#f472b6' : '#38bdf8';
  const topModels = (currentAccount?.quota?.models || []).slice(0, 3);
  const hasBones = Boolean(assets.nezuko_head && assets.nezuko_torso && assets.nezuko_arm_l && assets.nezuko_arm_r);
  const rigScale = SCALE_PRESETS[scaleIdx];

  const nezukoRigClass = useMemo(() => {
    const map: Record<string, string> = {
      idle: 'rig-idle',
      walk: 'rig-walk',
      dash: 'rig-dash',
      skid: 'rig-skid',
      stomp: 'rig-stomp',
      pat: 'rig-pat',
      feed: 'rig-feed',
      blood: 'rig-blood',
      dance: 'rig-dance',
      picked_up: 'rig-picked-up',
      land_squash: 'rig-landing-squash',
    };
    return `${map[action] || 'rig-idle'} ${blinking ? 'is-blinking' : ''}`;
  }, [action, blinking]);

  return (
    <div
      onMouseDown={handleStartDrag}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => {
        isHoveredRef.current = true;
      }}
      onMouseLeave={() => {
        isHoveredRef.current = false;
        setTilt({ x: 0, y: 0 });
      }}
      className="relative flex h-screen w-screen flex-col items-center justify-end select-none p-2.5 bg-transparent overflow-hidden"
    >
      {/* 顶部 Apple 灵动岛黑曜石玻璃控制坞 */}
      <div
        className="mb-1.5 flex items-center gap-0.5 rounded-full bg-slate-950/80 px-2 py-1 text-white backdrop-blur-2xl border border-white/15"
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
          onClick={() => setRoaming((r) => !r)}
          className={`p-1.5 rounded-full transition-colors ${roaming ? 'text-emerald-400 bg-emerald-500/15' : 'text-slate-400 hover:bg-white/10'}`}
          title={roaming ? '自由漫步：开启' : '自由漫步：停驻'}
        >
          <Footprints className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={toggleMute}
          className="p-1.5 rounded-full hover:bg-white/10 text-slate-300 transition-colors"
          title={muted ? '取消静音' : '静音互动音效'}
        >
          {muted ? <VolumeX className="w-3.5 h-3.5 text-rose-400" /> : <Volume2 className="w-3.5 h-3.5 text-sky-300" />}
        </button>
        <button
          onClick={() => setScaleIdx((i) => (i + 1) % SCALE_PRESETS.length)}
          className="px-1.5 py-0.5 rounded-full hover:bg-white/10 text-[10px] font-mono text-amber-300 transition-colors"
          title="循环缩放身材 (88% / 100% / 115%)"
        >
          {Math.round(rigScale * 100)}%
        </button>
        <button
          onClick={() => setPanelMode((m) => (m === 'quota' ? 'none' : 'quota'))}
          className={`p-1.5 rounded-full transition-colors ${panelMode === 'quota' ? 'bg-sky-500/30 text-sky-300' : 'hover:bg-white/10 text-slate-300'}`}
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
        className="mb-1.5 max-w-[330px] rounded-2xl bg-slate-950/78 px-3.5 py-1.5 text-center text-[11.5px] font-medium text-slate-100 backdrop-blur-2xl border border-white/15 transition-all"
        style={{
          boxShadow: '0 10px 28px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.16)',
        }}
      >
        <div>{bubble}</div>
        {subBubble && <div className="text-[9.5px] italic text-amber-200/80 mt-0.5">{subBubble}</div>}
      </div>

      {/* 3D 视差生态玻璃容器舞台 (Living Terrarium Stage) */}
      <div
        id="nezuko-pet-stage"
        className="relative flex h-56 w-64 items-end justify-center cursor-grab active:cursor-grabbing"
        style={{ perspective: '760px' }}
      >
        {/* 远景环境体积光晕 */}
        <div
          className="pointer-events-none absolute inset-4 rounded-full blur-2xl transition-all duration-700"
          style={{
            background: `radial-gradient(circle, ${themeAccent}42 0%, transparent 72%)`,
            transform: `translate3d(${tilt.x * -8}px, ${tilt.y * -8}px, 0)`,
          }}
        />

        {/* 情绪飘浮气泡 */}
        {moodIcon && (
          <div className="pointer-events-none absolute top-2 right-12 z-40 text-lg animate-bounce drop-shadow-md">
            {moodIcon}
          </div>
        )}

        {/* 小王子多层视差环境 + Verlet 物理丝绸围巾 */}
        {character === 'prince' && (
          <>
            {assets.prince_stars && (
              <img
                src={assets.prince_stars}
                alt=""
                className="pointer-events-none absolute inset-0 h-full w-full object-contain opacity-80 animate-pulse"
                style={{ transform: `translate3d(${tilt.x * -10}px, ${tilt.y * -6}px, 0)`, transition: 'transform 160ms ease-out' }}
              />
            )}
            {(sunsetMode || action === 'rose') && assets.prince_sunset && (
              <img
                src={assets.prince_sunset}
                alt=""
                className="pointer-events-none absolute inset-2 h-full w-full object-cover rounded-full opacity-55 mix-blend-screen"
                style={{ transform: `translate3d(${tilt.x * -6}px, ${tilt.y * -4}px, 0)` }}
              />
            )}
            {action === 'stars' && <div className="shooting-star-streak" />}
            {action === 'volcano' && (
              <>
                <div className="volcano-puff" />
                <div className="volcano-puff" style={{ animationDelay: '0.7s', left: '42px' }} />
              </>
            )}
            {assets.prince_rose && (
              <img
                src={assets.prince_rose}
                alt="玫瑰"
                className={`pointer-events-none absolute bottom-3 right-4 h-12 w-12 object-contain drop-shadow-[0_6px_14px_rgba(0,0,0,0.5)] ${
                  action === 'rose' ? 'scale-125 brightness-125' : ''
                } transition-transform duration-500`}
                style={{ transform: `translate3d(${tilt.x * 7}px, ${tilt.y * 5}px, 0)` }}
              />
            )}
            {action !== 'fox' && action !== 'sleep' && (
              <PrinceScarfCanvas facing={facing} windBoost={action === 'walk' || action === 'dash' ? 1.5 : 0.4} />
            )}
          </>
        )}

        {/* 旋转落地冲击波 */}
        {action === 'box_spin' && assets.shockwave && (
          <img
            src={assets.shockwave}
            alt=""
            className="box-impact-ring pointer-events-none absolute bottom-1 h-28 w-44 object-contain z-20"
          />
        )}

        {/* 物理矢量微粒 & 地面扬尘 */}
        {particles.map((p) => (
          <ParticleSvg key={p.id} p={p} accentColor={themeAccent} />
        ))}

        {/* 前景接触投影 */}
        <div
          className="pointer-events-none absolute bottom-1 h-3.5 w-28 rounded-full bg-black/55 blur-md transition-transform duration-300"
          style={{
            transform: `translate3d(${tilt.x * 4}px, 0, 0) scale(${action === 'picked_up' ? 0.65 : action === 'blood' ? 0.82 : 1})`,
          }}
        />

        {/* 前景角色动画本体容器 */}
        <div
          id="pet-character-viewport"
          onClick={() =>
            triggerAction(
              'pat',
              character === 'prince' ? '小狐狸顺从地依偎过来 ✨' : '唔嗯♥ 感受到你的温暖啦',
            )
          }
          onDoubleClick={() =>
            triggerAction(character === 'nezuko' ? 'box_spin' : 'stars', character === 'nezuko' ? '8帧木箱旋风奇点开启！' : 'B612 流星雨许愿时刻 ✨')
          }
          className="relative flex items-end justify-center transition-transform duration-200 ease-out"
          style={{
            transform: `scale(${rigScale}) scaleX(${facing}) rotateX(${tilt.y * -6}deg) rotateY(${tilt.x * 8}deg)`,
            transformOrigin: '50% 100%',
          }}
        >
          {character === 'nezuko' ? (
            action === 'box_spin' && assets.nezuko_spin_sheet ? (
              <div className="box-sprite-viewport">
                <div
                  className="box-sprite-strip"
                  style={{ backgroundImage: `url(${assets.nezuko_spin_sheet})` }}
                />
              </div>
            ) : action === 'box_peek' && assets.nezuko_peeker ? (
              <img
                src={assets.nezuko_peeker}
                alt="木箱探头"
                className="peeker-pop h-40 w-36 object-contain drop-shadow-[0_14px_24px_rgba(0,0,0,0.55)]"
                draggable={false}
              />
            ) : action === 'sleep' && assets.nezuko_basket ? (
              <img
                src={assets.nezuko_basket}
                alt="竹篓休眠"
                className="h-36 w-36 object-contain animate-pulse drop-shadow-[0_12px_22px_rgba(0,0,0,0.55)]"
                draggable={false}
              />
            ) : hasBones ? (
              <div className={`nezuko-bone-rig ${nezukoRigClass}`}>
                <div
                  id="bone-head"
                  className="bone-layer"
                  style={{
                    backgroundImage: `url(${assets.nezuko_head})`,
                    transform:
                      action === 'idle'
                        ? `rotate(${(tilt.x * 8 * facing).toFixed(1)}deg) translateY(${(tilt.y * 2.5).toFixed(1)}px)`
                        : undefined,
                  }}
                />
                <div className="nezuko-eyelid" />
                <div
                  id="bone-torso"
                  className="bone-layer"
                  style={{ backgroundImage: `url(${assets.nezuko_torso})` }}
                />
                <div
                  id="bone-arm-l"
                  className="bone-layer"
                  style={{ backgroundImage: `url(${assets.nezuko_arm_l})` }}
                />
                <div
                  id="bone-arm-r"
                  className="bone-layer"
                  style={{ backgroundImage: `url(${assets.nezuko_arm_r})` }}
                />
                {assets.nezuko_leg_l && (
                  <div
                    id="bone-leg-l"
                    className="bone-layer"
                    style={{ backgroundImage: `url(${assets.nezuko_leg_l})` }}
                  />
                )}
                {assets.nezuko_leg_r && (
                  <div
                    id="bone-leg-r"
                    className="bone-layer"
                    style={{ backgroundImage: `url(${assets.nezuko_leg_r})` }}
                  />
                )}
              </div>
            ) : assets.nezuko_chibi ? (
              <img
                src={assets.nezuko_chibi}
                alt="祢豆子"
                className="h-44 w-36 object-contain drop-shadow-[0_14px_24px_rgba(0,0,0,0.55)]"
                draggable={false}
              />
            ) : null
          ) : (
            <div
              className={`flex h-44 w-40 items-end justify-center ${
                action === 'walk' || action === 'dash'
                  ? 'prince-walk'
                  : action === 'fox'
                    ? 'prince-fox-cuddle'
                    : action === 'picked_up'
                      ? 'rig-picked-up'
                      : action === 'land_squash'
                        ? 'rig-landing-squash'
                        : ''
              }`}
            >
              {(action === 'fox' || action === 'pat') && assets.prince_fox ? (
                <img
                  src={assets.prince_fox}
                  alt="小王子与狐狸"
                  className="h-44 w-40 object-contain drop-shadow-[0_14px_24px_rgba(0,0,0,0.55)]"
                  draggable={false}
                />
              ) : assets.little_prince ? (
                <img
                  src={assets.little_prince}
                  alt="小王子"
                  className="h-44 w-40 object-contain drop-shadow-[0_14px_24px_rgba(0,0,0,0.55)]"
                  draggable={false}
                />
              ) : (
                <div className="flex h-28 w-28 flex-col items-center justify-center rounded-full bg-sky-600/80 text-white border border-white/25">
                  <Sparkles className="h-7 w-7 mb-1" />
                  <span className="text-xs font-semibold">小王子</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 底部磨砂互动控制胶囊（完整复刻丰富动作集） */}
      <div
        id="nezuko-action-capsule"
        className="mt-1.5 flex flex-wrap items-center justify-center gap-1 rounded-full bg-slate-950/80 px-2.5 py-1 text-[11px] font-medium text-slate-200 border border-white/15 backdrop-blur-2xl"
        style={{
          boxShadow: '0 10px 26px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.16)',
        }}
      >
        {character === 'nezuko' ? (
          <>
            <button onClick={() => triggerAction('pat', '轻抚发梢 ~ 心情指数 +100%')} className="px-2 py-0.5 rounded-full hover:bg-white/15 transition-colors">
              摸头
            </button>
            <button onClick={() => triggerAction('box_spin', '8帧大正木箱 360° 旋风旋转！')} className="px-2 py-0.5 rounded-full hover:bg-amber-500/25 text-amber-200 transition-colors">
              转箱
            </button>
            <button onClick={() => triggerAction('dash', '风火轮极速狂奔！')} className="px-2 py-0.5 rounded-full hover:bg-sky-500/25 text-sky-200 transition-colors inline-flex items-center gap-0.5">
              <Wind className="w-3 h-3" />
              狂奔
            </button>
            <button onClick={() => triggerAction('stomp', '哼！气鼓鼓跺脚抗议！')} className="px-2 py-0.5 rounded-full hover:bg-orange-500/25 text-orange-200 transition-colors">
              跺脚
            </button>
            <button onClick={() => triggerAction('blood', '血鬼术·爆血绯晶绽放！')} className="px-2 py-0.5 rounded-full hover:bg-rose-500/25 text-pink-300 transition-colors">
              爆血
            </button>
            <button onClick={() => triggerAction('feed', '投喂星空金平糖，开心蹦跳 ✨')} className="px-2 py-0.5 rounded-full hover:bg-emerald-500/25 text-emerald-200 transition-colors">
              投喂
            </button>
            <button
              onClick={() =>
                triggerAction(
                  action === 'sleep' ? 'idle' : 'sleep',
                  action === 'sleep' ? '睡醒伸个懒腰，重新陪伴你' : '缩小钻进竹篓安心休眠…',
                )
              }
              className="px-2 py-0.5 rounded-full hover:bg-indigo-500/25 transition-colors"
            >
              {action === 'sleep' ? '唤醒' : '休眠'}
            </button>
          </>
        ) : (
          <>
            <button onClick={() => triggerAction('pat')} className="px-2 py-0.5 rounded-full hover:bg-sky-500/25 transition-colors inline-flex items-center gap-1">
              <Heart className="w-3 h-3 text-pink-300" />
              语录
            </button>
            <button onClick={() => triggerAction('fox', '和驯服的小狐狸贴贴依偎 🦊')} className="px-2 py-0.5 rounded-full hover:bg-amber-500/25 text-amber-200 transition-colors">
              狐狸
            </button>
            <button onClick={() => triggerAction('rose', '在玻璃罩前细心浇灌玫瑰 🌹')} className="px-2 py-0.5 rounded-full hover:bg-rose-500/25 text-rose-200 transition-colors">
              玫瑰
            </button>
            <button
              onClick={() => {
                setSunsetMode((s) => !s);
                setBubble(!sunsetMode ? 'B612 的第四十四次金色日落' : '深蓝星海悄然笼罩天穹');
              }}
              className="px-2 py-0.5 rounded-full hover:bg-amber-500/25 transition-colors inline-flex items-center gap-1"
            >
              <Sun className="w-3 h-3 text-amber-300" />
              {sunsetMode ? '星夜' : '日落'}
            </button>
            <button onClick={() => triggerAction('stars', '仰望夜空流星划过 ✨')} className="px-2 py-0.5 rounded-full hover:bg-indigo-500/25 text-indigo-200 transition-colors">
              流星
            </button>
            <button onClick={() => triggerAction('volcano', '勤快清扫 B612 的小火山烟尘 🌋')} className="px-2 py-0.5 rounded-full hover:bg-orange-500/25 text-orange-200 transition-colors">
              火山
            </button>
            <button onClick={() => triggerAction('walk', '带着飘扬丝巾在星轨漫步')} className="px-2 py-0.5 rounded-full hover:bg-purple-500/25 text-purple-200 transition-colors">
              漫步
            </button>
          </>
        )}
      </div>

      {/* 扩展遥测 HUD：模型配额或声学黑胶律动舱 */}
      {panelMode !== 'none' && (
        <div
          id="nezuko-main-card"
          className="mt-2 w-full max-w-[346px] rounded-2xl bg-slate-950/88 p-3.5 text-xs text-slate-200 border border-white/15 backdrop-blur-2xl"
          style={{
            boxShadow: '0 22px 48px rgba(0,0,0,0.65), inset 0 1px 0 rgba(255,255,255,0.2)',
          }}
        >
          {panelMode === 'quota' && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-[11px]">
                <span className="truncate font-semibold text-sky-300 max-w-[210px]">
                  {currentAccount ? currentAccount.custom_label || currentAccount.email : '未检测到激活账号'}
                </span>
                <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-mono text-slate-300">
                  {currentAccount?.quota?.subscription_tier || 'FREE'}
                </span>
              </div>
              {topModels.length === 0 ? (
                <div className="text-center text-slate-400 py-2 text-[11px]">请在管理器「账号管理」页签中绑定账号</div>
              ) : (
                <div className="space-y-2">
                  {topModels.map((m) => (
                    <div key={m.name} className="space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="truncate max-w-[205px] text-slate-300">{m.display_name || m.name}</span>
                        <span className={`font-mono font-semibold ${m.percentage < 20 ? 'text-rose-400' : 'text-emerald-400'}`}>
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
                <div className="relative shrink-0 flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-slate-800 to-black border border-white/20 shadow-inner">
                  <Disc3 className={`h-6 w-6 text-emerald-400 ${media.isPlaying ? 'animate-spin' : ''}`} style={{ animationDuration: '4s' }} />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="truncate font-semibold text-white">
                    {media.isPlaying ? media.title || media.rawTitle : '声学频道待机中'}
                  </div>
                  <div className="truncate text-[10.5px] text-slate-400">
                    {media.isPlaying ? `${media.artist || '未知歌手'} · ${media.source}` : '打开 QQ音乐 / 网易云播放即可联动'}
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
                      if (action !== 'dance') triggerAction('dance', '声波律动热舞模式开启 ♪');
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
                    {media.isPlaying ? '♪ 正在享受纯音乐韵律 ♪' : '播放曲目后自动检索并同步酷狗 LRC 歌词'}
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
