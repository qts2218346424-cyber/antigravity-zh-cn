import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { listen } from '@tauri-apps/api/event';
import { open } from '@tauri-apps/plugin-dialog';
import {
  Activity,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Disc3,
  Footprints,
  Heart,
  ImagePlus,
  Moon,
  Music,
  Pause,
  Pin,
  PinOff,
  Play,
  RefreshCw,
  Shuffle,
  SkipBack,
  SkipForward,
  Sparkles,
  Sun,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react';
import { studioService } from '../../services/studioService';
import { useAccountStore } from '../../stores/useAccountStore';
import type { MediaStatus, PetAssets, PetCharacterId } from '../../types/studio';
import { isTauri } from '../../utils/env';
import { petAudio } from './petAudio';
import {
  evaluateLowQuotaAlert,
  findActiveLyricIndex,
  normalizePetCharacter,
  parseLrcTimeline,
  PET_CHARACTER_ORDER,
  PET_CHARACTER_PROFILES,
  SCALE_PRESETS,
  shouldStartWindowDrag,
  type ParticleKind,
  type PetAction,
} from './petLogic';
import './petAnimations.css';

interface Particle {
  id: number;
  batchId: number;
  x: number;
  y: number;
  dx: number;
  scale: number;
  rotate: number;
  kind: ParticleKind;
}

/** 矢量物理微粒节点：飘落樱花瓣、上升星光、清泉水滴、雷光与地面扬尘 */
const ParticleSvg: React.FC<{ p: Particle; accentColor: string }> = ({ p, accentColor }) => {
  if (p.kind === 'dust') {
    return (
      <div
        className="dust-puff"
        style={
          {
            left: `${p.x}%`,
            '--dx': `${p.dx}px`,
          } as React.CSSProperties
        }
      />
    );
  }

  const motionCls = p.kind === 'petal' ? 'particle-flutter' : 'particle-float-up';

  return (
    <div
      className={motionCls}
      style={
        {
          left: `${p.x}%`,
          top: `${p.y}%`,
          '--pdx': `${p.dx}px`,
          '--ps': `${p.scale}`,
        } as React.CSSProperties
      }
    >
      {p.kind === 'petal' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2C15.5 6.5 20 10 18 16C16.2 20.8 7.8 20.8 6 16C4 10 8.5 6.5 12 2Z"
            fill={accentColor}
            fillOpacity="0.92"
          />
        </svg>
      )}
      {p.kind === 'star' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2L14.3 9.7L22 12L14.3 14.3L12 22L9.7 14.3L2 12L9.7 9.7L12 2Z"
            fill="#fde68a"
          />
        </svg>
      )}
      {p.kind === 'water' && (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2.5C12 2.5 5 10.5 5 15.2C5 19 8.1 22 12 22C15.9 22 19 19 19 15.2C19 10.5 12 2.5 12 2.5Z"
            fill="#38bdf8"
            fillOpacity="0.9"
          />
        </svg>
      )}
      {p.kind === 'lightning' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M13 2L4 14H11L9 22L20 10H13L13 2Z" fill="#facc15" />
        </svg>
      )}
      {p.kind === 'dango' && (
        <svg width="17" height="15" viewBox="0 0 28 24" fill="none">
          <ellipse
            cx="14"
            cy="13"
            rx="11"
            ry="8.8"
            fill={p.rotate % 3 === 0 ? '#f9a8d4' : p.rotate % 3 === 1 ? '#fde68a' : '#93c5fd'}
            stroke="#5c3a21"
            strokeWidth="1.8"
          />
          <line x1="11" y1="10.2" x2="11" y2="14.2" stroke="#4a2c1d" strokeWidth="1.8" strokeLinecap="round" />
          <line x1="17" y1="10.2" x2="17" y2="14.2" stroke="#4a2c1d" strokeWidth="1.8" strokeLinecap="round" />
          <circle cx="8" cy="14.5" r="1.5" fill="#fb7185" fillOpacity="0.55" />
          <circle cx="20" cy="14.5" r="1.5" fill="#fb7185" fillOpacity="0.55" />
        </svg>
      )}
      {p.kind === 'orb' && (
        <span
          className="block h-3.5 w-3.5 rounded-full"
          style={{
            background: 'radial-gradient(circle, #ffffff 0%, #fef08a 52%, transparent 100%)',
            boxShadow: '0 0 14px #fef08a, 0 0 22px #38bdf8',
          }}
        />
      )}
      {p.kind === 'spark' && (
        <span
          className="block h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: accentColor, boxShadow: `0 0 10px ${accentColor}` }}
        />
      )}
    </div>
  );
};

const PetWindowView: React.FC = () => {
  const [character, setCharacter] = useState<PetCharacterId>('nezuko');
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
  const [pickerOpen, setPickerOpen] = useState<boolean>(false);
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
  const [trackElapsedMs, setTrackElapsedMs] = useState(0);
  const [manualLineShift, setManualLineShift] = useState(0);
  const [switchingAccount, setSwitchingAccount] = useState(false);
  const [refreshingQuota, setRefreshingQuota] = useState(false);
  const [voicePlaying, setVoicePlaying] = useState(false);

  const actionTimerRef = useRef<number | null>(null);
  const boxStepTimerRef = useRef<number | null>(null);
  const roamLoopRef = useRef<number | null>(null);
  const dragMonitorTimerRef = useRef<number | null>(null);
  const quoteIdxRef = useRef<number>(0);
  const assetsRef = useRef<PetAssets>({});
  assetsRef.current = assets;
  const pointerDownRef = useRef<{ x: number; y: number; active: boolean; dragged: boolean }>({
    x: 0,
    y: 0,
    active: false,
    dragged: false,
  });
  const isHoveredRef = useRef(false);
  const alertedAccountRef = useRef<string>('');
  const actionRef = useRef<PetAction>('idle');
  actionRef.current = action;
  const facingRef = useRef<1 | -1>(1);
  facingRef.current = facing;

  const {
    accounts,
    currentAccount,
    fetchAccounts,
    fetchCurrentAccount,
    refreshQuota,
    switchAccount,
  } = useAccountStore();

  const profile = PET_CHARACTER_PROFILES[character] || PET_CHARACTER_PROFILES.nezuko;
  const themeAccent = profile.accent;

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

  const spawnBatch = useCallback((kind: ParticleKind, count = 10) => {
    const batchId = Date.now() + Math.random();
    const batch: Particle[] = Array.from({ length: count }, (_, idx) => ({
      id: batchId + idx * 0.001,
      batchId,
      x: 16 + Math.random() * 68,
      y: kind === 'dust' ? 86 : kind === 'petal' ? 12 + Math.random() * 34 : 28 + Math.random() * 44,
      dx: (Math.random() - 0.5) * 44,
      scale: 0.78 + Math.random() * 0.58,
      rotate: Math.round(Math.random() * 360),
      kind,
    }));
    setParticles((prev) => [...prev.slice(-26), ...batch]);
    window.setTimeout(() => {
      setParticles((prev) => prev.filter((item) => item.batchId !== batchId));
    }, 1580);
  }, []);

  const showMood = useCallback((icon: string, ms = 1800) => {
    setMoodIcon(icon);
    window.setTimeout(() => setMoodIcon(''), ms);
  }, []);

  const playVoiceByKey = useCallback((voiceKey?: string) => {
    if (!voiceKey) return false;
    const uri = assetsRef.current.voices?.[voiceKey];
    if (!uri) return false;
    return petAudio.playVoice(uri, setVoicePlaying, voiceKey);
  }, []);

  const applyCharacterGreeting = useCallback(
    (ch: PetCharacterId, speak = false) => {
      const p = PET_CHARACTER_PROFILES[ch] || PET_CHARACTER_PROFILES.nezuko;
      quoteIdxRef.current = 0;
      const first = p.quotes[0];
      setBubble(first.zh);
      setSubBubble(first.sub || '');
      if (speak && first.voiceKey) {
        playVoiceByKey(first.voiceKey);
      }
    },
    [playVoiceByKey],
  );

  const handleCycleAnimeQuote = useCallback(() => {
    const quotes = profile.quotes;
    if (!quotes || quotes.length === 0) return;
    quoteIdxRef.current = (quoteIdxRef.current + 1) % quotes.length;
    const item = quotes[quoteIdxRef.current];
    setBubble(item.zh);
    setSubBubble(item.sub || '');
    showMood('💬', 1600);
    spawnBatch(profile.particleKind, 7);
    if (!playVoiceByKey(item.voiceKey)) {
      petAudio.playCare();
    }
  }, [playVoiceByKey, profile, showMood, spawnBatch]);

  const triggerAction = useCallback(
    (
      next: PetAction,
      msg?: string,
      durationMs = 2800,
      opts?: { sub?: string; voiceKey?: string; silentVoice?: boolean },
    ) => {
      // 再次点击正在播放的原动画《团子大家族》按钮时，支持优雅暂停停止
      if (
        next === 'dango_song' &&
        actionRef.current === 'dango_song' &&
        petAudio.activeVoiceTag === 'ushio_dango'
      ) {
        clearActionTimers();
        petAudio.stopVoice();
        setAction('idle');
        setBubble('🎵 已暂停《团子大家族》原曲演唱，想听随时再点我哦 ♪');
        setSubBubble('');
        return;
      }

      clearActionTimers();
      setAction(next);

      let chosenVoiceKey = opts?.voiceKey;
      if (msg) {
        setBubble(msg);
        setSubBubble(opts?.sub || '');
      } else {
        const quotes = profile.quotes;
        const q = quotes[Math.floor(Math.random() * quotes.length)];
        setBubble(q.zh);
        setSubBubble(q.sub || '');
        if (!chosenVoiceKey) chosenVoiceKey = q.voiceKey;
      }

      const spoke = !opts?.silentVoice && playVoiceByKey(chosenVoiceKey);
      const effectiveDuration =
        next === 'dango_song' && spoke ? 57200 : durationMs;

      if (next === 'pat') {
        if (!spoke) petAudio.playCare();
        showMood('💗');
        spawnBatch(profile.particleKind, 10);
      } else if (next === 'feed') {
        if (!spoke) petAudio.playCare();
        showMood('🍬');
        spawnBatch('spark', 12);
      } else if (next === 'blood') {
        if (!spoke) petAudio.playBloodBurst();
        showMood('🌸');
        spawnBatch('petal', 16);
      } else if (next === 'stomp') {
        petAudio.playWoodThud();
        showMood('💢');
        spawnBatch('dust', 7);
      } else if (next === 'fox' || next === 'rose') {
        if (!spoke) petAudio.playStardust();
        showMood(next === 'fox' ? '🦊' : '🌹');
        spawnBatch('star', 11);
      } else if (next === 'stars') {
        if (!spoke) petAudio.playShootingStar();
        showMood('🌠');
        spawnBatch('star', 15);
      } else if (next === 'volcano') {
        petAudio.playWoodThud();
        showMood('🌋');
        spawnBatch('dust', 6);
      } else if (next === 'dango_song') {
        if (!spoke) petAudio.playDangoMelody();
        showMood('🍡', 2600);
        spawnBatch('dango', 13);
      } else if (next === 'sunflower') {
        if (!spoke) petAudio.playStardust();
        showMood('🌻', 2400);
        spawnBatch('star', 11);
      } else if (next === 'light_orb') {
        if (!spoke) petAudio.playLightOrb();
        showMood('✨', 2600);
        spawnBatch('orb', 14);
      } else if (next === 'water_slash') {
        if (!spoke) petAudio.playWaterBreath();
        showMood('🌊');
        spawnBatch('water', 14);
      } else if (next === 'thunder_dash') {
        if (!spoke) petAudio.playThunderSpark();
        showMood('⚡');
        spawnBatch('lightning', 12);
      } else if (next === 'beast_rush') {
        if (!spoke) petAudio.playBeastRoar();
        showMood('🐗');
        spawnBatch('dust', 9);
      } else if (next === 'box_spin') {
        petAudio.playSpinWind();
        showMood('✨');
        boxStepTimerRef.current = window.setTimeout(() => {
          petAudio.playWoodThud();
          spawnBatch('petal', 12);
          setAction('box_peek');
          if (!spoke) {
            setBubble('半掩大正木箱门，悄悄探出小脑袋好奇张望 👀');
          }
          actionTimerRef.current = window.setTimeout(() => {
            setAction('idle');
          }, 2600);
        }, 1250);
        return;
      } else if (next === 'dash') {
        petAudio.playSpinWind();
        showMood('💨');
        spawnBatch('dust', 8);
        let ticks = 0;
        roamLoopRef.current = window.setInterval(() => {
          ticks += 1;
          if (ticks % 4 === 0) {
            spawnBatch('dust', 3);
          }
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
            spawnBatch('dust', 5);
            setAction('skid');
            if (!spoke) {
              setBubble(
                character === 'nezuko'
                  ? '风火轮急刹车！稳稳停住啦 ✨'
                  : '迎着星风轻盈收步停驻 ✨',
              );
            }
            actionTimerRef.current = window.setTimeout(() => setAction('idle'), 460);
          }
        }, 65);
        return;
      } else if (next === 'walk') {
        petAudio.playFootstep();
        let ticks = 0;
        roamLoopRef.current = window.setInterval(() => {
          ticks += 1;
          if (ticks % 4 === 0) {
            spawnBatch(profile.particleKind, 2);
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
        }, effectiveDuration);
      }
    },
    [character, clearActionTimers, playVoiceByKey, profile, showMood, spawnBatch],
  );

  // 初始化状态同步与拟人化随机自然眨眼（等待资产与语音库加载完毕后立即播放角色原声问候）
  useEffect(() => {
    document.documentElement.classList.add('pet-window');
    document.body.classList.add('pet-window');
    const root = document.getElementById('root');
    if (root) root.classList.add('pet-root');
    petAudio.warmup();

    Promise.all([studioService.getPetAssets(), studioService.getStatus()])
      .then(([loadedAssets, st]) => {
        assetsRef.current = loadedAssets;
        setAssets(loadedAssets);
        const ch = normalizePetCharacter(st.pet_character);
        setCharacter(ch);
        setRoaming(st.pet_roaming ?? true);
        setAlwaysOnTop(st.pet_always_on_top ?? true);
        setScaleIdx(
          typeof st.pet_scale_idx === 'number' ? Math.min(2, Math.max(0, st.pet_scale_idx)) : 1,
        );
        const isMuted = Boolean(st.pet_muted);
        petAudio.muted = isMuted;
        setMuted(isMuted);
        applyCharacterGreeting(ch, !isMuted);
      })
      .catch(console.error);

    fetchAccounts().catch(() => {});
    fetchCurrentAccount().catch(() => {});
    const quotaTimer = window.setInterval(() => {
      fetchCurrentAccount().catch(() => {});
    }, 30000);

    const unlisteners: Array<() => void> = [];
    if (isTauri()) {
      listen<string>('pet:character-changed', (ev) => {
        const ch = normalizePetCharacter(ev.payload);
        setCharacter(ch);
        setAction('idle');
        applyCharacterGreeting(ch, true);
      })
        .then((fn) => unlisteners.push(fn))
        .catch(() => {});

      listen('pet:assets-updated', () => {
        studioService
          .getPetAssets()
          .then((loaded) => {
            assetsRef.current = loaded;
            setAssets(loaded);
          })
          .catch(() => {});
      })
        .then((fn) => unlisteners.push(fn))
        .catch(() => {});

      listen<{ action: PetAction; message?: string; sub?: string; voiceKey?: string }>(
        'pet:remote-action',
        (ev) => {
          if (ev.payload?.action) {
            triggerAction(ev.payload.action, ev.payload.message, 3200, {
              sub: ev.payload.sub,
              voiceKey: ev.payload.voiceKey,
            });
          }
        },
      )
        .then((fn) => unlisteners.push(fn))
        .catch(() => {});

      listen('accounts://refreshed', () => {
        fetchCurrentAccount().catch(() => {});
        fetchAccounts().catch(() => {});
      })
        .then((fn) => unlisteners.push(fn))
        .catch(() => {});

      listen('tray://account-switched', () => {
        fetchCurrentAccount().catch(() => {});
        fetchAccounts().catch(() => {});
      })
        .then((fn) => unlisteners.push(fn))
        .catch(() => {});

      getCurrentWindow()
        .onMoved(() => {
          if (!pointerDownRef.current.dragged) return;
          if (dragMonitorTimerRef.current) {
            window.clearTimeout(dragMonitorTimerRef.current);
          }
          dragMonitorTimerRef.current = window.setTimeout(() => {
            pointerDownRef.current.dragged = false;
            pointerDownRef.current.active = false;
            isHoveredRef.current = false;
            petAudio.playFootstep();
            setAction('land_squash');
            setBubble('稳稳弹性着陆 ✨');
            window.setTimeout(() => setAction('idle'), 360);
          }, 180);
        })
        .then((fn) => unlisteners.push(fn))
        .catch(() => {});
    }

    // 拟人化自然眨眼循环：随机 2.6s~4.8s 间隔，25% 概率触发灵动双连眨
    let blinkTimeout = 0;
    let blinkInner1 = 0;
    let blinkInner2 = 0;
    let blinkInner3 = 0;
    let cancelled = false;

    const scheduleNextBlink = () => {
      const delay = 2600 + Math.random() * 2200;
      blinkTimeout = window.setTimeout(() => {
        if (cancelled) return;
        setBlinking(true);
        blinkInner1 = window.setTimeout(() => {
          if (cancelled) return;
          setBlinking(false);
          if (Math.random() < 0.25) {
            blinkInner2 = window.setTimeout(() => {
              if (cancelled) return;
              setBlinking(true);
              blinkInner3 = window.setTimeout(() => {
                if (!cancelled) setBlinking(false);
              }, 115);
            }, 130);
          }
          scheduleNextBlink();
        }, 125);
      }, delay);
    };
    scheduleNextBlink();

    return () => {
      cancelled = true;
      petAudio.stopVoice();
      clearActionTimers();
      if (dragMonitorTimerRef.current) window.clearTimeout(dragMonitorTimerRef.current);
      window.clearInterval(quotaTimer);
      window.clearTimeout(blinkTimeout);
      window.clearTimeout(blinkInner1);
      window.clearTimeout(blinkInner2);
      window.clearTimeout(blinkInner3);
      unlisteners.forEach((fn) => fn());
      document.documentElement.classList.remove('pet-window');
      document.body.classList.remove('pet-window');
      if (root) root.classList.remove('pet-root');
    };
  }, [applyCharacterGreeting, clearActionTimers, fetchAccounts, fetchCurrentAccount, triggerAction]);

  useEffect(() => {
    if (!isTauri()) return;
    const height = panelMode === 'none' && !pickerOpen ? 420 : 586;
    studioService.setPetSize(386, height).catch(() => {});
  }, [panelMode, pickerOpen]);

  useEffect(() => {
    if (!currentAccount) return;
    const alert = evaluateLowQuotaAlert(currentAccount.quota?.models, 20);
    const alertKey = `${currentAccount.id}:${alert.lowestModelName}`;
    if (alert.hasLowQuota && alertedAccountRef.current !== alertKey) {
      alertedAccountRef.current = alertKey;
      petAudio.playQuotaAlert();
      showMood('⚠️', 2800);
      setBubble(alert.alertMessage);
      setSubBubble('');
    }
  }, [currentAccount, showMood]);

  useEffect(() => {
    const poll = () => {
      studioService
        .getMediaStatus()
        .then((res) => {
          setMedia((prev) => {
            if (prev.rawTitle !== res.rawTitle) {
              setTrackElapsedMs(0);
              setManualLineShift(0);
            }
            if (!res.isPlaying && actionRef.current === 'dance') {
              setAction('idle');
            }
            return res;
          });
        })
        .catch(() => {});
    };
    poll();
    const timer = window.setInterval(poll, 2600);
    return () => window.clearInterval(timer);
  }, []);

  const parsedLyrics = useMemo(() => parseLrcTimeline(media.lrc), [media.lrc]);

  useEffect(() => {
    if (!media.isPlaying || parsedLyrics.length === 0) return;
    const maxTime = parsedLyrics[parsedLyrics.length - 1].timeMs + 5000;
    const ticker = window.setInterval(() => {
      setTrackElapsedMs((ms) => (ms + 400 > maxTime ? 0 : ms + 400));
    }, 400);
    return () => window.clearInterval(ticker);
  }, [media.isPlaying, parsedLyrics]);

  const activeLyricIndex = useMemo(() => {
    if (parsedLyrics.length === 0) return -1;
    const baseIdx = findActiveLyricIndex(parsedLyrics, trackElapsedMs);
    const shifted = (baseIdx + manualLineShift) % parsedLyrics.length;
    return shifted < 0 ? shifted + parsedLyrics.length : shifted;
  }, [parsedLyrics, trackElapsedMs, manualLineShift]);

  // 自主桌边漫步心跳
  useEffect(() => {
    if (!roaming) return;
    const timer = window.setInterval(() => {
      if (isHoveredRef.current || panelMode !== 'none' || pickerOpen || actionRef.current !== 'idle') {
        return;
      }
      const roll = Math.random();
      if (roll < 0.52) {
        if (Math.random() < 0.35) setFacing((f) => (f === 1 ? -1 : 1));
        triggerAction(
          'walk',
          character === 'prince'
            ? '金黄丝巾随风微扬，踏着星尘漫步…'
            : `${profile.shortName}沿桌面轻快散步中…`,
          2800,
          { silentVoice: true },
        );
      } else if (roll < 0.74) {
        triggerAction(
          'dash',
          character === 'nezuko'
            ? '豆豆眼风火轮疾跑巡航！'
            : character === 'prince'
              ? '迎着星海微风追逐金色日落 ✨'
              : `${profile.shortName}轻盈疾跑巡视！`,
          2800,
          { silentVoice: true },
        );
      } else if (roll < 0.86) {
        setFacing((f) => (f === 1 ? -1 : 1));
        showMood('✨');
      }
    }, 9500);
    return () => window.clearInterval(timer);
  }, [roaming, panelMode, pickerOpen, character, profile.shortName, triggerAction, showMood]);

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (
      target.closest('button') ||
      target.closest('input') ||
      target.closest('a') ||
      target.closest('[data-no-drag]')
    ) {
      return;
    }
    if (!isTauri() || e.button !== 0) return;
    pointerDownRef.current = {
      x: e.clientX,
      y: e.clientY,
      active: true,
      dragged: false,
    };
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
    const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
    setTilt({ x: nx, y: ny });

    if (
      pointerDownRef.current.active &&
      !pointerDownRef.current.dragged &&
      shouldStartWindowDrag(pointerDownRef.current.x, pointerDownRef.current.y, e.clientX, e.clientY, 5)
    ) {
      pointerDownRef.current.dragged = true;
      pointerDownRef.current.active = false;
      setAction('picked_up');
      setBubble(`${profile.shortName}被轻轻拎起啦，松手即弹性落地 ✨`);
      getCurrentWindow()
        .startDragging()
        .catch(() => {
          pointerDownRef.current.dragged = false;
          setAction('idle');
        });
    }
  };

  const handlePointerUp = () => {
    pointerDownRef.current.active = false;
  };

  const selectCharacter = (next: PetCharacterId) => {
    clearActionTimers();
    setCharacter(next);
    setAction('idle');
    setPickerOpen(false);
    applyCharacterGreeting(next, true);
    studioService.updatePetPrefs({ character: next }).catch(() => {});
  };

  const handleImportCustomAvatar = async () => {
    if (!isTauri()) return;
    try {
      const picked = await open({
        multiple: false,
        title: '选择自定义桌宠立绘 (PNG / WebP / GIF / SVG)',
        filters: [{ name: '透明立绘与动图', extensions: ['png', 'webp', 'gif', 'svg', 'jpg', 'jpeg'] }],
      });
      if (!picked || Array.isArray(picked)) return;
      const dataUri = await studioService.importPetAvatar(picked);
      setAssets((prev) => ({ ...prev, custom_avatar: dataUri }));
      selectCharacter('custom');
      setBubble('专属自定义立绘已成功载入 ✨');
    } catch (err) {
      setBubble(`导入立绘失败: ${String(err)}`);
    }
  };

  const toggleRoaming = () => {
    const next = !roaming;
    setRoaming(next);
    setBubble(next ? '🐾 桌面自由巡航已开启' : '📍 已切换为安静定点陪伴');
    studioService.updatePetPrefs({ roaming: next }).catch(() => {});
  };

  const toggleTop = () => {
    const next = !alwaysOnTop;
    setAlwaysOnTop(next);
    studioService.setPetAlwaysOnTop(next).catch(() => {});
  };

  const toggleMute = () => {
    const next = !muted;
    petAudio.muted = next;
    if (next) petAudio.stopVoice();
    setMuted(next);
    setBubble(next ? '🔇 原声语音与互动音效已静音' : '🔊 角色动漫原声与治愈音效已开启');
    studioService.updatePetPrefs({ muted: next }).catch(() => {});
  };

  const cycleScale = () => {
    const nextIdx = (scaleIdx + 1) % SCALE_PRESETS.length;
    setScaleIdx(nextIdx);
    studioService.updatePetPrefs({ scaleIdx: nextIdx }).catch(() => {});
  };

  const handleQuickRefreshQuota = async () => {
    if (!currentAccount || refreshingQuota) return;
    setRefreshingQuota(true);
    try {
      await refreshQuota(currentAccount.id);
      await fetchCurrentAccount();
      setBubble('⚡ 当前账号算力配额已实时刷新');
    } catch {
      setBubble('配额刷新暂未响应，请稍后重试');
    } finally {
      setRefreshingQuota(false);
    }
  };

  const handleQuickSwitchAccount = async () => {
    if (switchingAccount) return;
    const candidates = accounts.filter((a) => !a.disabled && a.id !== currentAccount?.id);
    if (candidates.length === 0) {
      setBubble('账号池暂无其他可切换的备用账号');
      return;
    }
    setSwitchingAccount(true);
    try {
      const nextAcc = candidates[0];
      await switchAccount(nextAcc.id);
      await fetchCurrentAccount();
      petAudio.playCare();
      showMood('🚀');
      setBubble(`已无缝切换至账号：${nextAcc.custom_label || nextAcc.email}`);
    } catch (err) {
      setBubble(`切换账号失败: ${String(err)}`);
    } finally {
      setSwitchingAccount(false);
    }
  };

  const topModels = (currentAccount?.quota?.models || []).slice(0, 3);
  const rigScale = SCALE_PRESETS[scaleIdx] ?? 1.0;

  // 统一多姿态弹性运动类名映射（为米豆子、小王子及全角色提供精准物理反馈）
  const activeMotionClass = useMemo(() => {
    if (action === 'picked_up') return 'rig-picked-up';
    if (action === 'land_squash') return 'rig-landing-squash';
    if (action === 'skid') return 'rig-skid';
    if (action === 'box_peek') return 'peeker-pop';
    if (action === 'sleep') return 'pet-sleep-breathe';
    if (action === 'pat') return 'pet-pat-bliss';
    if (action === 'feed') return 'rig-feed';
    if (action === 'dance') return 'rig-dance';
    if (action === 'stomp') return 'rig-stomp';
    if (action === 'blood') return 'rig-blood';
    if (action === 'dash') {
      return character === 'nezuko' ? 'nezuko-wheel-dash' : 'prince-walk';
    }
    if (action === 'walk') return 'prince-walk';
    if (action === 'fox') return 'prince-fox-cuddle';
    if (action === 'rose') return 'prince-rose-cherish';
    if (action === 'dango_song') return 'ushio-dango-sway';
    if (action === 'sunflower') return 'ushio-sunflower-pose';
    if (action === 'water_slash') return 'hero-water-slash';
    if (action === 'thunder_dash') return 'hero-thunder-dash';
    if (action === 'beast_rush') return 'hero-beast-rush';
    return 'hero-idle-breath';
  }, [action, character]);

  // 多姿态高清透明立绘智能选择器（含双帧无痕眨眼切换）
  const activeSpriteSrc = useMemo(() => {
    if (character === 'nezuko') {
      if (action === 'box_peek' && assets.nezuko_peeker) return assets.nezuko_peeker;
      if (action === 'sleep' && assets.nezuko_basket) return assets.nezuko_basket;
      if ((action === 'pat' || action === 'feed' || action === 'dance') && assets.nezuko_happy) {
        return assets.nezuko_happy;
      }
      if ((action === 'walk' || action === 'dash' || action === 'skid') && assets.nezuko_run) {
        return assets.nezuko_run;
      }
      if (action === 'stomp' && assets.nezuko_stomp) return assets.nezuko_stomp;
      if (action === 'blood' && assets.nezuko_blood) return assets.nezuko_blood;
      if (action === 'idle' && blinking && assets.nezuko_blink) return assets.nezuko_blink;
      return assets.nezuko_chibi || null;
    }

    if (character === 'prince') {
      if (action === 'sleep' && assets.prince_sleep) return assets.prince_sleep;
      if (action === 'fox' && assets.prince_fox) return assets.prince_fox;
      if (action === 'rose' && assets.prince_rose_pose) return assets.prince_rose_pose;
      if ((action === 'walk' || action === 'dash' || action === 'skid') && assets.prince_walk) {
        return assets.prince_walk;
      }
      if ((action === 'idle' || action === 'pat') && blinking && assets.prince_blink) {
        return assets.prince_blink;
      }
      return assets.little_prince || null;
    }

    if (character === 'ushio') {
      if (action === 'sleep' && assets.ushio_sleep) return assets.ushio_sleep;
      if (
        (action === 'pat' || action === 'dango_song' || action === 'feed' || action === 'dance') &&
        assets.ushio_happy
      ) {
        return assets.ushio_happy;
      }
      if ((action === 'walk' || action === 'dash' || action === 'skid') && assets.ushio_walk) {
        return assets.ushio_walk;
      }
      if (action === 'sunflower' && assets.ushio_sunflower) return assets.ushio_sunflower;
      if ((action === 'idle' || action === 'light_orb') && blinking && assets.ushio_blink) {
        return assets.ushio_blink;
      }
      return assets.ushio_chibi || null;
    }

    if (character === 'tanjiro') {
      if ((action === 'pat' || action === 'feed' || action === 'dance') && assets.tanjiro_happy) {
        return assets.tanjiro_happy;
      }
      if ((action === 'walk' || action === 'dash' || action === 'skid') && assets.tanjiro_run) {
        return assets.tanjiro_run;
      }
      if (action === 'water_slash' && assets.tanjiro_water) return assets.tanjiro_water;
      if (action === 'idle' && blinking && assets.tanjiro_blink) return assets.tanjiro_blink;
      return assets.tanjiro_chibi || assets.tanjiro_water || null;
    }

    if (character === 'zenitsu') {
      if (action === 'sleep' && assets.zenitsu_sleep) return assets.zenitsu_sleep;
      if ((action === 'pat' || action === 'feed' || action === 'dance') && assets.zenitsu_happy) {
        return assets.zenitsu_happy;
      }
      if (action === 'thunder_dash' && assets.zenitsu_thunder) return assets.zenitsu_thunder;
      if (action === 'idle' && blinking && assets.zenitsu_blink) return assets.zenitsu_blink;
      return assets.zenitsu_chibi || assets.zenitsu_thunder || null;
    }

    if (character === 'inosuke') {
      if (action === 'sleep' && assets.inosuke_sleep) return assets.inosuke_sleep;
      if ((action === 'pat' || action === 'feed' || action === 'dance') && assets.inosuke_happy) {
        return assets.inosuke_happy;
      }
      if (action === 'beast_rush' && assets.inosuke_beast) return assets.inosuke_beast;
      if (action === 'idle' && blinking && assets.inosuke_blink) return assets.inosuke_blink;
      return assets.inosuke_chibi || assets.inosuke_beast || null;
    }

    if (character === 'custom') return assets.custom_avatar || null;
    return assets.nezuko_chibi || null;
  }, [character, action, blinking, assets]);

  return (
    <div
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onMouseEnter={() => {
        isHoveredRef.current = true;
      }}
      onMouseLeave={() => {
        isHoveredRef.current = false;
        pointerDownRef.current.active = false;
        setTilt({ x: 0, y: 0 });
      }}
      className="relative flex h-screen w-screen flex-col items-center justify-end select-none p-2.5 bg-transparent overflow-hidden"
    >
      {/* 顶部高对比实心黑曜石灵动岛控制坞（防桌面透底发虚） */}
      <div
        data-no-drag
        className="relative z-30 mb-1.5 flex items-center gap-0.5 rounded-full bg-[#0b1120]/[0.97] px-2.5 py-1 text-white border border-slate-500/70"
        style={{
          boxShadow: '0 14px 32px rgba(0,0,0,0.85), inset 0 1px 0 rgba(255,255,255,0.22)',
        }}
      >
        <button
          type="button"
          onClick={() => setPickerOpen((v) => !v)}
          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 text-[11.5px] font-bold rounded-full bg-slate-800 hover:bg-slate-700 text-white border border-slate-600/80 transition-colors"
          title="切换陪伴角色或导入自定义立绘"
        >
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: themeAccent, boxShadow: `0 0 8px ${themeAccent}` }}
          />
          <span>{profile.shortName}</span>
          <ChevronDown
            className={`w-3 h-3 opacity-75 transition-transform ${pickerOpen ? 'rotate-180' : ''}`}
          />
        </button>

        <div className="h-3 w-px bg-white/15 mx-0.5" />

        <button
          type="button"
          onClick={toggleRoaming}
          className={`p-1.5 rounded-full transition-colors ${
            roaming ? 'text-emerald-400 bg-emerald-500/15' : 'text-slate-400 hover:bg-white/10'
          }`}
          title={roaming ? '自由漫步：开启' : '自由漫步：停驻'}
        >
          <Footprints className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={toggleMute}
          className="p-1.5 rounded-full hover:bg-white/10 text-slate-300 transition-colors"
          title={muted ? '取消静音' : '静音互动音效'}
        >
          {muted ? (
            <VolumeX className="w-3.5 h-3.5 text-rose-400" />
          ) : (
            <Volume2 className="w-3.5 h-3.5 text-sky-300" />
          )}
        </button>
        <button
          type="button"
          onClick={cycleScale}
          className="px-1.5 py-0.5 rounded-full hover:bg-white/10 text-[10px] font-mono text-amber-300 transition-colors"
          title="循环缩放身材 (88% / 100% / 115%)"
        >
          {Math.round(rigScale * 100)}%
        </button>
        <button
          type="button"
          onClick={() => {
            setPickerOpen(false);
            setPanelMode((m) => (m === 'quota' ? 'none' : 'quota'));
          }}
          className={`p-1.5 rounded-full transition-colors ${
            panelMode === 'quota' ? 'bg-sky-500/30 text-sky-300' : 'hover:bg-white/10 text-slate-300'
          }`}
          title="算力配额与一键切号"
        >
          <Activity className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={() => {
            setPickerOpen(false);
            setPanelMode((m) => (m === 'music' ? 'none' : 'music'));
          }}
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
          type="button"
          onClick={toggleTop}
          className="p-1.5 rounded-full hover:bg-white/10 text-slate-300 transition-colors"
          title={alwaysOnTop ? '取消置顶' : '窗口置顶'}
        >
          {alwaysOnTop ? (
            <Pin className="w-3.5 h-3.5 text-amber-300" />
          ) : (
            <PinOff className="w-3.5 h-3.5" />
          )}
        </button>
        <button
          type="button"
          onClick={() => studioService.closePet().catch(() => {})}
          className="p-1.5 rounded-full hover:bg-rose-500/30 text-slate-300 hover:text-rose-200 transition-colors"
          title="收起桌面伴侣"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 角色矩阵弹出抽屉（实心深曜石高对比装甲 + 3D 角色头像预览） */}
      {pickerOpen && (
        <div
          data-no-drag
          className="z-30 mb-2 w-full max-w-[354px] rounded-2xl bg-[#0b1120]/[0.98] p-2.5 text-xs text-white border border-slate-500/75 space-y-2"
          style={{ boxShadow: '0 20px 44px rgba(0,0,0,0.88), inset 0 1px 0 rgba(255,255,255,0.18)' }}
        >
          <div className="grid grid-cols-3 gap-1.5">
            {PET_CHARACTER_ORDER.map((cid) => {
              const item = PET_CHARACTER_PROFILES[cid];
              const isSelected = cid === character;
              const thumbSrc =
                cid === 'nezuko'
                  ? assets.nezuko_chibi
                  : cid === 'prince'
                    ? assets.little_prince
                    : cid === 'ushio'
                      ? assets.ushio_chibi
                      : cid === 'tanjiro'
                        ? assets.tanjiro_chibi || assets.tanjiro_water
                        : cid === 'zenitsu'
                          ? assets.zenitsu_chibi || assets.zenitsu_thunder
                          : cid === 'inosuke'
                            ? assets.inosuke_chibi || assets.inosuke_beast
                            : assets.custom_avatar;
              return (
                <button
                  key={cid}
                  type="button"
                  onClick={() => selectCharacter(cid)}
                  className={`flex items-center gap-1.5 rounded-xl px-2 py-1.5 text-[11.5px] font-semibold border transition-all ${
                    isSelected
                      ? 'bg-sky-500/30 text-white border-sky-400 shadow-[0_0_12px_rgba(56,189,248,0.35)]'
                      : 'bg-slate-800/95 text-slate-100 border-slate-600/80 hover:bg-slate-700 hover:border-slate-400'
                  }`}
                >
                  {thumbSrc ? (
                    <img
                      src={thumbSrc}
                      alt=""
                      className="h-5 w-5 rounded-md object-contain bg-slate-900/90 shrink-0"
                    />
                  ) : (
                    <span
                      className="h-2.5 w-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: item.accent }}
                    />
                  )}
                  <span className="truncate">{item.shortName}</span>
                </button>
              );
            })}
          </div>
          <div className="flex items-center justify-between pt-1.5 border-t border-slate-700/80">
            <span className="text-[10.5px] text-slate-300">支持 PNG / WebP / GIF / SVG</span>
            <button
              type="button"
              onClick={handleImportCustomAvatar}
              className="inline-flex items-center gap-1 rounded-lg bg-purple-600/80 hover:bg-purple-500 text-white px-2.5 py-1 text-[10.5px] font-semibold transition-colors"
            >
              <ImagePlus className="w-3 h-3" />
              导入自定义形象
            </button>
          </div>
        </div>
      )}

      {/* 高对比实心对白气泡（点击可循环聆听当前角色动漫原生经典金句） */}
      <button
        type="button"
        data-no-drag
        onClick={handleCycleAnimeQuote}
        title="点击切换并播放下一句动漫原生金句语音"
        className="group mb-1.5 max-w-[354px] rounded-2xl bg-[#0b1120]/[0.97] hover:bg-[#131d36] px-3.5 py-1.5 text-center text-[12px] font-semibold text-white border border-slate-500/75 hover:border-sky-400/80 transition-all cursor-pointer"
        style={{
          boxShadow: '0 12px 30px rgba(0,0,0,0.85), inset 0 1px 0 rgba(255,255,255,0.2)',
        }}
      >
        <div className="inline-flex items-center justify-center gap-1.5 leading-snug">
          {!muted && (
            <Volume2
              className={`w-3.5 h-3.5 shrink-0 transition-transform ${
                voicePlaying
                  ? 'text-pink-400 scale-115 animate-pulse'
                  : 'text-sky-300 group-hover:text-sky-200'
              }`}
            />
          )}
          <span>{bubble}</span>
        </div>
        {subBubble && (
          <div className="text-[10px] font-medium text-amber-300 mt-0.5">{subBubble}</div>
        )}
      </button>

      {/* 3D 视差生态玻璃容器舞台 */}
      <div
        id="nezuko-pet-stage"
        className="relative flex h-56 w-64 items-end justify-center cursor-grab active:cursor-grabbing"
        style={{ perspective: '760px' }}
      >
        {/* 远景环境体积光晕（日落或向日葵花田模式下切换为温暖金橙霞光） */}
        <div
          className="pointer-events-none absolute inset-4 rounded-full blur-2xl transition-all duration-700"
          style={{
            background:
              (character === 'prince' && (sunsetMode || action === 'rose')) ||
              (character === 'ushio' && action === 'sunflower')
                ? 'radial-gradient(circle, rgba(251, 191, 36, 0.48) 0%, rgba(244, 114, 182, 0.22) 52%, transparent 74%)'
                : `radial-gradient(circle, ${themeAccent}42 0%, transparent 72%)`,
            transform: `translate3d(${tilt.x * -8}px, ${tilt.y * -8}px, 0)`,
          }}
        />

        {/* 冈崎汐专属：《CLANNAD》小镇温暖愿望光玉漂浮层 */}
        {character === 'ushio' && (
          <>
            <div
              className="clannad-light-orb"
              style={{ left: '22%', animationDuration: '3.4s', '--orb-dx': '16px' } as React.CSSProperties}
            />
            <div
              className="clannad-light-orb"
              style={{
                left: '74%',
                animationDuration: '3.9s',
                animationDelay: '1.3s',
                '--orb-dx': '-14px',
              } as React.CSSProperties}
            />
            {(action === 'light_orb' || action === 'dango_song') && (
              <>
                <div
                  className="clannad-light-orb"
                  style={{ left: '36%', animationDuration: '2.2s', '--orb-dx': '-20px' } as React.CSSProperties}
                />
                <div
                  className="clannad-light-orb"
                  style={{
                    left: '58%',
                    animationDuration: '2.5s',
                    animationDelay: '0.45s',
                    '--orb-dx': '22px',
                  } as React.CSSProperties}
                />
                <div
                  className="clannad-light-orb"
                  style={{
                    left: '48%',
                    animationDuration: '2.1s',
                    animationDelay: '0.85s',
                    '--orb-dx': '8px',
                  } as React.CSSProperties}
                />
              </>
            )}
          </>
        )}

        {/* 情绪飘浮气泡 */}
        {moodIcon && (
          <div className="pointer-events-none absolute top-2 right-10 z-40 text-lg animate-bounce drop-shadow-md">
            {moodIcon}
          </div>
        )}

        {/* 摸头温柔光波弧 & 休眠 Zzz 梦境气泡 */}
        {action === 'pat' && <div className="pat-halo-wave" />}
        {action === 'sleep' && (
          <>
            <span className="sleep-zzz-note">Zzz</span>
            <span
              className="sleep-zzz-note"
              style={{ animationDelay: '1.25s', right: '30px', top: '12px', fontSize: '10.5px' }}
            >
              zZ
            </span>
          </>
        )}

        {/* 小王子高精度矢量 B612 星海天穹、双子流星与微缩火山 */}
        {character === 'prince' && (
          <>
            <svg
              viewBox="0 0 240 200"
              className="pointer-events-none absolute inset-0 h-full w-full opacity-85"
              style={{
                transform: `translate3d(${tilt.x * -9}px, ${tilt.y * -5}px, 0)`,
                transition: 'transform 160ms ease-out',
              }}
            >
              <circle cx="38" cy="34" r="1.8" fill="#fef08a" className="animate-pulse" />
              <circle cx="204" cy="28" r="2.2" fill="#bae6fd" className="animate-pulse" />
              <circle cx="182" cy="68" r="1.5" fill="#fde68a" />
              <circle cx="54" cy="76" r="1.4" fill="#e0f2fe" />
              <path
                d="M196 46L197.8 51.2L203 53L197.8 54.8L196 60L194.2 54.8L189 53L194.2 51.2L196 46Z"
                fill="#fde047"
                fillOpacity="0.9"
              />
              <path
                d="M44 48L45.3 51.7L49 53L45.3 54.3L44 58L42.7 54.3L39 53L42.7 51.7L44 48Z"
                fill="#fef08a"
                fillOpacity="0.82"
              />
              {/* 微缩 B612 星球地平弧线 */}
              <path
                d="M36 192 Q120 174 204 192"
                stroke={sunsetMode ? 'rgba(251, 191, 36, 0.5)' : 'rgba(125, 211, 252, 0.35)'}
                strokeWidth="2.2"
                fill="none"
                strokeLinecap="round"
              />
            </svg>

            {action === 'stars' && (
              <>
                <div className="shooting-star-streak" />
                <div
                  className="shooting-star-streak"
                  style={{ top: '34px', right: '42px', width: '58px', animationDelay: '0.55s' }}
                />
              </>
            )}

            {action === 'volcano' && (
              <>
                <svg
                  width="38"
                  height="28"
                  viewBox="0 0 40 30"
                  className="pointer-events-none absolute bottom-2 left-5 z-[14] drop-shadow"
                >
                  <path
                    d="M4 28 L14 8 L26 8 L36 28 Z"
                    fill="#78716c"
                    stroke="#44403c"
                    strokeWidth="2.2"
                    strokeLinejoin="round"
                  />
                  <ellipse cx="20" cy="8" rx="6" ry="2.4" fill="#fb923c" />
                </svg>
                <div className="volcano-puff" />
                <div className="volcano-puff" style={{ animationDelay: '0.68s', left: '34px' }} />
              </>
            )}
          </>
        )}

        {/* 祢豆子血鬼术·爆血绯晶旋转法阵光环 */}
        {character === 'nezuko' && action === 'blood' && <div className="blood-aura-ring" />}

        {/* 炭治郎水之呼吸剑纹环 / 善逸霹雳一闪流光弧 */}
        {action === 'water_slash' && <div className="water-ripple-ring" />}
        {action === 'thunder_dash' && <div className="thunder-flash-arc" />}

        {/* 3D 大正木箱旋转落地冲击波 */}
        {action === 'box_spin' && assets.shockwave && (
          <img
            src={assets.shockwave}
            alt=""
            className="box-impact-ring pointer-events-none absolute bottom-0 h-28 w-44 object-contain z-20"
          />
        )}

        {/* 动态物理微粒与地面扬尘 */}
        {particles.map((p) => (
          <ParticleSvg key={p.id} p={p} accentColor={themeAccent} />
        ))}

        {/* 3D 潮玩手办立体透视展台底座（隔离杂乱壁纸透底并塑造真实 3D 手办立体空间感） */}
        <div
          className="pet-3d-pedestal"
          style={
            {
              '--pedestal-accent': `${themeAccent}b8`,
              '--pedestal-glow': `${themeAccent}52`,
              opacity: action === 'picked_up' ? 0.45 : 0.96,
              transform: `translate3d(${tilt.x * 4}px, 0, 0) rotateX(68deg) scale(${
                action === 'picked_up' ? 0.72 : action === 'land_squash' ? 1.12 : 1
              })`,
            } as React.CSSProperties
          }
        />

        {/* 前景角色动画本体容器（分离内外层变换避免镜像翻转破坏 3D 陀螺仪倾斜矩阵） */}
        <div
          id="pet-character-viewport"
          onClick={() => {
            if (pointerDownRef.current.dragged) return;
            const firstAct = profile.actions[0];
            triggerAction('pat', firstAct?.bubble, 3200, {
              sub: firstAct?.sub,
              voiceKey: firstAct?.voiceKey,
            });
          }}
          onDoubleClick={() => {
            if (pointerDownRef.current.dragged) return;
            triggerAction(profile.doubleClickAction, profile.doubleClickBubble, 3200, {
              sub: profile.doubleClickSub,
              voiceKey: profile.doubleClickVoiceKey,
            });
          }}
          className="pet-spring-transform relative z-10 flex items-end justify-center"
          style={{
            transform: `scale(${rigScale}) rotateX(${(tilt.y * -6).toFixed(2)}deg) rotateY(${(
              tilt.x * 8
            ).toFixed(2)}deg)`,
            transformOrigin: '50% 100%',
          }}
        >
          <div
            className="relative flex items-end justify-center"
            style={{
              transform: `scaleX(${facing})`,
              transformOrigin: '50% 100%',
            }}
          >
            {character === 'nezuko' && action === 'box_spin' && assets.nezuko_spin_sheet ? (
              <div className="box-sprite-viewport">
                <div
                  className="box-sprite-strip"
                  style={{ backgroundImage: `url(${assets.nezuko_spin_sheet})` }}
                />
              </div>
            ) : (
              <div
                className={`relative flex h-48 w-44 items-end justify-center ${activeMotionClass}`}
              >
                {/* 祢豆子风火轮高速旋风残影涡流环 */}
                {character === 'nezuko' && action === 'dash' && <div className="wind-wheel-ring" />}

                {activeSpriteSrc ? (
                  <img
                    src={activeSpriteSrc}
                    alt={profile.shortName}
                    className="pet-sprite-img relative z-10 h-48 w-44 object-contain drop-shadow-[0_14px_24px_rgba(0,0,0,0.52)]"
                    draggable={false}
                  />
                ) : (
                  <button
                    type="button"
                    data-no-drag
                    onClick={character === 'custom' ? handleImportCustomAvatar : undefined}
                    className="relative z-10 flex h-32 w-32 flex-col items-center justify-center rounded-3xl bg-slate-900/85 text-white border border-dashed border-purple-400/50 hover:border-purple-300 px-3 text-center transition-colors"
                  >
                    {character === 'custom' ? (
                      <>
                        <ImagePlus className="h-7 w-7 mb-1.5 text-purple-300" />
                        <span className="text-[11px] font-semibold">点击上传立绘</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-7 w-7 mb-1 text-sky-300" />
                        <span className="text-xs font-semibold">{profile.shortName}</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 底部高对比实心互动控制胶囊（自适应当前角色专属动作组，清晰不透底） */}
      <div
        id="nezuko-action-capsule"
        data-no-drag
        className="mt-1.5 flex flex-wrap items-center justify-center gap-1 rounded-full bg-[#0b1120]/[0.97] px-2.5 py-1 text-[11.5px] font-semibold text-white border border-slate-500/75"
        style={{
          boxShadow: '0 12px 28px rgba(0,0,0,0.85), inset 0 1px 0 rgba(255,255,255,0.2)',
        }}
      >
        {profile.actions.map((act) => (
          <button
            key={`${character}-${act.action}-${act.label}`}
            type="button"
            onClick={() =>
              triggerAction(act.action, act.bubble, 3200, {
                sub: act.sub,
                voiceKey: act.voiceKey,
              })
            }
            className={`px-2 py-0.5 rounded-full transition-colors ${act.toneClass}`}
          >
            {act.label}
          </button>
        ))}

        {character === 'prince' && (
          <>
            <button
              type="button"
              onClick={() => {
                const enteringSunset = !sunsetMode;
                setSunsetMode(enteringSunset);
                if (enteringSunset) {
                  setBubble('「在我的 B612 小星球上，我一天看过四十四次金色日落 🌠」');
                  setSubBubble("Sur ma petite planète, j'ai vu le soleil se coucher quarante-quatre fois.");
                  playVoiceByKey('prince_sunset');
                } else {
                  setBubble('深蓝星海悄然笼罩天穹 ✨');
                  setSubBubble('');
                }
              }}
              className="px-2 py-0.5 rounded-full hover:bg-amber-500/25 transition-colors inline-flex items-center gap-1"
            >
              <Sun className="w-3 h-3 text-amber-300" />
              {sunsetMode ? '星夜' : '日落'}
            </button>
            <button
              type="button"
              onClick={() =>
                triggerAction(
                  action === 'sleep' ? 'idle' : 'sleep',
                  action === 'sleep'
                    ? '从金色弯月醒来，继续陪你探索星海 ✨'
                    : '依偎在金色新月上和小狐狸安静入眠…',
                )
              }
              className="px-2 py-0.5 rounded-full hover:bg-indigo-500/25 text-indigo-200 transition-colors inline-flex items-center gap-0.5"
            >
              <Moon className="w-3 h-3 text-amber-200" />
              {action === 'sleep' ? '唤醒' : '星眠'}
            </button>
          </>
        )}

        {(character === 'nezuko' || character === 'ushio') && (
          <button
            type="button"
            onClick={() =>
              triggerAction(
                action === 'sleep' ? 'idle' : 'sleep',
                character === 'ushio'
                  ? action === 'sleep'
                    ? '「早安呀！小汐和粉色大团子又充满元气啦 🍡」'
                    : '「唔…眼皮快合上啦…晚安呀，愿你也能做个暖呼呼的好梦…」'
                  : action === 'sleep'
                    ? '「早…早上好！平安无事真是太好了呢 ✨」'
                    : '「为什么要老是道歉呢？你每天都这么努力了…一起歇会儿吧…」',
                3200,
                {
                  sub:
                    character === 'ushio'
                      ? action === 'sleep'
                        ? 'うん！おっきいだんごも一緒だよ♪'
                        : 'おやすみなさい、あったかい夢が見られますように…'
                      : action === 'sleep'
                        ? 'お…おはよう！本当によかったね！'
                        : '毎日こんなに頑張ってるのに…少し一緒に休もうね…',
                  voiceKey:
                    character === 'ushio'
                      ? action === 'sleep'
                        ? 'ushio_trip'
                        : 'ushio_sleep'
                      : action === 'sleep'
                        ? 'nezuko_ohayou'
                        : 'nezuko_apologize',
                },
              )
            }
            className="px-2 py-0.5 rounded-full hover:bg-indigo-500/25 text-indigo-200 transition-colors"
          >
            {action === 'sleep' ? '唤醒' : character === 'ushio' ? '午睡' : '休眠'}
          </button>
        )}

        {action === 'dance' && (
          <button
            type="button"
            onClick={() => {
              setAction('idle');
              setBubble('停下舞步轻轻喘口气 ✨');
            }}
            className="px-2 py-0.5 rounded-full bg-rose-500/25 text-rose-200 hover:bg-rose-500/35 transition-colors"
          >
            停舞
          </button>
        )}
      </div>

      {/* 扩展遥测 HUD：算力配额一键切号舱 / 声学黑胶时间轴歌词舱 */}
      {panelMode !== 'none' && (
        <div
          id="nezuko-main-card"
          data-no-drag
          className="mt-2 w-full max-w-[354px] rounded-2xl bg-[#0b1120]/[0.98] p-3.5 text-xs text-slate-100 border border-slate-500/75"
          style={{
            boxShadow: '0 22px 48px rgba(0,0,0,0.88), inset 0 1px 0 rgba(255,255,255,0.2)',
          }}
        >
          {panelMode === 'quota' && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between gap-2 text-[11px]">
                <span className="truncate font-semibold text-sky-300 max-w-[175px]">
                  {currentAccount
                    ? currentAccount.custom_label || currentAccount.email
                    : '未检测到激活账号'}
                </span>
                <div className="flex items-center gap-1 shrink-0">
                  <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-mono text-slate-300">
                    {currentAccount?.quota?.subscription_tier || 'FREE'}
                  </span>
                  <button
                    type="button"
                    onClick={handleQuickRefreshQuota}
                    disabled={refreshingQuota || !currentAccount}
                    className="p-1 rounded-full bg-white/10 hover:bg-white/20 text-slate-200 disabled:opacity-40 transition-colors"
                    title="立即刷新当前账号配额"
                  >
                    <RefreshCw className={`w-3 h-3 ${refreshingQuota ? 'animate-spin' : ''}`} />
                  </button>
                  <button
                    type="button"
                    onClick={handleQuickSwitchAccount}
                    disabled={switchingAccount || accounts.length <= 1}
                    className="inline-flex items-center gap-1 rounded-full bg-sky-500/25 hover:bg-sky-500/40 px-2 py-0.5 text-[10px] font-semibold text-sky-200 disabled:opacity-40 transition-colors"
                    title="一键热切换至下一可用账号"
                  >
                    <Shuffle className="w-2.5 h-2.5" />
                    切号
                  </button>
                </div>
              </div>
              {topModels.length === 0 ? (
                <div className="text-center text-slate-400 py-2 text-[11px]">
                  请在主控台「账号管理」中添加并激活账号
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
                <button
                  type="button"
                  onClick={() =>
                    action === 'dance'
                      ? setAction('idle')
                      : triggerAction('dance', '声波律动热舞模式开启 ♪')
                  }
                  className="relative shrink-0 flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-slate-800 to-black border border-white/20 shadow-inner"
                  title="点击切换伴侣随乐律动热舞"
                >
                  <Disc3
                    className={`h-6 w-6 text-emerald-400 ${media.isPlaying ? 'animate-spin' : ''}`}
                    style={{ animationDuration: '4s' }}
                  />
                </button>

                <div className="min-w-0 flex-1">
                  <div className="truncate font-semibold text-white">
                    {media.isPlaying ? media.title || media.rawTitle : '声学频道待机中'}
                  </div>
                  <div className="truncate text-[10.5px] text-slate-400">
                    {media.isPlaying
                      ? `${media.artist || '未知歌手'} · ${media.source}`
                      : '打开 QQ音乐 / 网易云播放即可同步 LRC 时间轴'}
                  </div>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  <button
                    type="button"
                    onClick={() => studioService.sendMediaCommand('prev').catch(() => {})}
                    className="p-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                    title="上一曲"
                  >
                    <SkipBack className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => studioService.sendMediaCommand('play_pause').catch(() => {})}
                    className="p-1.5 rounded-full bg-emerald-500/25 hover:bg-emerald-500/45 text-emerald-300 transition-colors"
                    title="播放 / 暂停"
                  >
                    {media.isPlaying ? (
                      <Pause className="w-3.5 h-3.5" />
                    ) : (
                      <Play className="w-3.5 h-3.5" />
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => studioService.sendMediaCommand('next').catch(() => {})}
                    className="p-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                    title="下一曲"
                  >
                    <SkipForward className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="relative rounded-xl bg-black/45 px-6 py-2 border border-white/10 text-center space-y-1 min-h-[46px] flex flex-col justify-center">
                {parsedLyrics.length > 0 && activeLyricIndex >= 0 ? (
                  <>
                    <button
                      type="button"
                      onClick={() => setManualLineShift((s) => s - 1)}
                      className="absolute left-1 top-1/2 -translate-y-1/2 p-1 text-slate-500 hover:text-slate-200"
                      title="微调上一句歌词"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                    </button>
                    <div className="text-[11.5px] font-semibold text-amber-200 truncate">
                      {parsedLyrics[activeLyricIndex]?.text}
                    </div>
                    {parsedLyrics.length > 1 && (
                      <div className="text-[10px] text-slate-500 truncate">
                        {parsedLyrics[(activeLyricIndex + 1) % parsedLyrics.length]?.text}
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={() => setManualLineShift((s) => s + 1)}
                      className="absolute right-1 top-1/2 -translate-y-1/2 p-1 text-slate-500 hover:text-slate-200"
                      title="微调下一句歌词"
                    >
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </>
                ) : (
                  <div className="text-[11px] text-slate-400">
                    {media.isPlaying ? (
                      <span className="inline-flex items-center gap-1">
                        <Heart className="w-3 h-3 text-pink-400" /> 正在享受纯音乐旋律
                      </span>
                    ) : (
                      '播放曲目后自动检索并按毫秒时间轴同步 LRC 歌词'
                    )}
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
