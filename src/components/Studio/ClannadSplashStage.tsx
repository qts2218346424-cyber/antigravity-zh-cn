import React, { useEffect, useId, useMemo, useRef, useState } from 'react';
import { Music, Pause, Play, Volume2, VolumeX, X } from 'lucide-react';
import {
  BUILTIN_BGM_TRACKS,
  type ClannadBgmTrackId,
  loadCustomBgmMetaSync,
  startSplashBgm,
  stopActiveSplashBgm,
} from './clannadAudioEngine';
import {
  type ClannadSplashThemeId,
  getSplashThemeSpec,
  resolveEffectiveBgmTrack,
} from './clannadSplashData';

export interface ClannadSplashStageProps {
  themeId: Exclude<ClannadSplashThemeId, 'none'>;
  mode?: 'preview' | 'overlay';
  durationMs?: number;
  musicEnabled?: boolean;
  bgmTrackId?: ClannadBgmTrackId;
  bgmVolume?: number;
  bgmStartOffsetSec?: number;
  cinemaLetterbox?: boolean;
  customArtworkUrl?: string | null;
  isMusicPreviewPlaying?: boolean;
  onToggleMusicPreview?: () => void;
  onSkip?: () => void;
}

interface StageParticle {
  x: number;
  y: number;
  r: number;
  vx: number;
  vy: number;
  phase: number;
  spin: number;
  depth: number;
  alt: boolean;
}

function drawSakuraPetal(ctx: CanvasRenderingContext2D, radius: number) {
  ctx.beginPath();
  ctx.moveTo(0, -radius);
  ctx.bezierCurveTo(radius * 0.85, -radius * 0.75, radius * 0.95, radius * 0.35, 0, radius);
  ctx.bezierCurveTo(-radius * 0.95, radius * 0.35, -radius * 0.85, -radius * 0.75, 0, -radius);
  ctx.closePath();
  ctx.fill();
}

export const ClannadSplashStage: React.FC<ClannadSplashStageProps> = ({
  themeId,
  mode = 'preview',
  durationMs = 4800,
  musicEnabled = false,
  bgmTrackId = 'follow-scene',
  bgmVolume = 0.7,
  bgmStartOffsetSec = 0,
  cinemaLetterbox = true,
  customArtworkUrl,
  isMusicPreviewPlaying = false,
  onToggleMusicPreview,
  onSkip,
}) => {
  const titleHeadingId = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [progress, setProgress] = useState(mode === 'preview' ? 24 : 8);
  const [motionPaused, setMotionPaused] = useState(false);
  const [overlayMuted, setOverlayMuted] = useState(!musicEnabled);
  const [imgFailed, setImgFailed] = useState(false);

  const spec = getSplashThemeSpec(themeId);
  const activeImgSrc = customArtworkUrl || spec.artworkUrl;

  useEffect(() => {
    setImgFailed(false);
  }, [activeImgSrc]);

  useEffect(() => {
    setOverlayMuted(!musicEnabled);
  }, [musicEnabled, themeId]);

  const reducedMotion = useMemo(() => {
    if (typeof window === 'undefined') return false;
    return Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
  }, []);

  const effectiveBgmTrack = useMemo(
    () =>
      resolveEffectiveBgmTrack(
        {
          musicBoxEnabled: mode === 'overlay' ? !overlayMuted : isMusicPreviewPlaying,
          bgmTrackId,
        },
        themeId,
      ),
    [mode, overlayMuted, isMusicPreviewPlaying, bgmTrackId, themeId],
  );

  const currentTrackDisplayLabel = useMemo(() => {
    const rawCandidate =
      bgmTrackId === 'follow-scene' || !bgmTrackId ? spec.recommendedBgmId : bgmTrackId;
    if (rawCandidate === 'off') return '静音模式';
    if (rawCandidate === 'custom-file') {
      const meta = loadCustomBgmMetaSync();
      return meta?.fileName ? `本地原声 · ${meta.fileName}` : '本地原声音乐';
    }
    const found = BUILTIN_BGM_TRACKS.find((t) => t.id === rawCandidate);
    return found ? found.title : '暖夜八音盒慢板';
  }, [bgmTrackId, spec.recommendedBgmId]);

  // 全屏模式下支持 ESC / Space / Enter 一键无延迟跳过
  useEffect(() => {
    if (mode !== 'overlay' || !onSkip) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        onSkip();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [mode, onSkip]);

  // 全屏覆盖层自动播放与退场平滑淡出控制
  useEffect(() => {
    if (mode !== 'overlay') return;
    if (effectiveBgmTrack === 'off') {
      stopActiveSplashBgm();
      return;
    }
    const stopAudio = startSplashBgm({
      trackId: effectiveBgmTrack,
      volume: bgmVolume,
      startOffsetSec: bgmStartOffsetSec,
      loop: true,
      fallbackTrackId: spec.recommendedBgmId,
    });
    return () => {
      stopAudio();
    };
  }, [
    mode,
    effectiveBgmTrack,
    bgmVolume,
    bgmStartOffsetSec,
    spec.recommendedBgmId,
  ]);

  // 序幕进度与三幕台词时间轴推进
  useEffect(() => {
    if (motionPaused && mode === 'preview') return;
    const start = Date.now();
    const cycleMs = mode === 'preview' ? 9600 : Math.max(1600, durationMs - 240);
    const timer = window.setInterval(() => {
      const elapsed = Date.now() - start;
      if (mode === 'preview') {
        const cycle = (elapsed % cycleMs) / cycleMs;
        setProgress(Math.max(6, Math.min(100, Math.round(cycle * 100))));
      } else {
        const pct = Math.min(100, Math.round((elapsed / cycleMs) * 100));
        setProgress(Math.max(8, pct));
      }
    }, 90);
    return () => window.clearInterval(timer);
  }, [durationMs, mode, themeId, motionPaused]);

  // 60fps Canvas 景深自然光影粒子层（叠加于原版动画截图之上，绝不喧宾夺主）
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const shouldAnimate = !reducedMotion && !motionPaused;
    const particleCount = reducedMotion ? 12 : 34;

    const particles: StageParticle[] = Array.from({ length: particleCount }, (_, idx) => {
      const depth = 0.45 + (idx % 5) * 0.16;
      return {
        x: Math.random(),
        y: Math.random(),
        r: (2.2 + Math.random() * 4.8) * depth,
        vx:
          themeId === 'clannad-sakura'
            ? (0.00035 + Math.random() * 0.00075) * depth
            : (Math.random() - 0.5) * 0.0005 * depth,
        vy:
          themeId === 'clannad-sakura'
            ? (0.00065 + Math.random() * 0.0011) * depth
            : -(0.00035 + Math.random() * 0.00085) * depth,
        phase: Math.random() * Math.PI * 2,
        spin: (Math.random() - 0.5) * 1.4,
        depth,
        alt: idx % 3 === 0,
      };
    });

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = container.clientWidth || 960;
      const h = container.clientHeight || 540;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();

    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(resize) : null;
    ro?.observe(container);

    let rafId = 0;
    const startTs = performance.now();

    const renderFrame = (now: number) => {
      const w = container.clientWidth || 960;
      const h = container.clientHeight || 540;
      const t = (now - startTs) * 0.001;

      ctx.clearRect(0, 0, w, h);

      // 若图片加载失败则提供柔和的原画色温苍穹兜底
      if (imgFailed) {
        const sky = ctx.createLinearGradient(0, 0, 0, h);
        if (themeId === 'clannad-sakura') {
          sky.addColorStop(0, '#ffdde9');
          sky.addColorStop(0.55, '#fff4f8');
          sky.addColorStop(1, '#f8bbd0');
        } else if (themeId === 'clannad-sunflower') {
          sky.addColorStop(0, '#0284c7');
          sky.addColorStop(0.55, '#bae6fd');
          sky.addColorStop(1, '#fde047');
        } else if (themeId === 'clannad-starfish') {
          sky.addColorStop(0, '#170f26');
          sky.addColorStop(0.55, '#3b1d4a');
          sky.addColorStop(1, '#7c2d12');
        } else {
          sky.addColorStop(0, '#040814');
          sky.addColorStop(0.6, '#0c1938');
          sky.addColorStop(1, '#172b56');
        }
        ctx.fillStyle = sky;
        ctx.fillRect(0, 0, w, h);
      }

      // 柔和电影镜头体积柔光（克制低透明度，烘托原版截图氛围）
      if (themeId === 'clannad-sunflower') {
        const sunGlow = ctx.createRadialGradient(w * 0.16, h * 0.14, 8, w * 0.16, h * 0.14, w * 0.42);
        sunGlow.addColorStop(0, 'rgba(255, 251, 235, 0.24)');
        sunGlow.addColorStop(0.45, 'rgba(253, 224, 71, 0.11)');
        sunGlow.addColorStop(1, 'rgba(253, 224, 71, 0)');
        ctx.fillStyle = sunGlow;
        ctx.fillRect(0, 0, w, h);
      } else if (themeId === 'clannad-sakura') {
        const springGlow = ctx.createLinearGradient(0, 0, w * 0.65, h * 0.75);
        springGlow.addColorStop(0, 'rgba(255, 245, 250, 0.22)');
        springGlow.addColorStop(1, 'rgba(255, 228, 238, 0)');
        ctx.fillStyle = springGlow;
        ctx.fillRect(0, 0, w, h);
      }

      // 绘制自然飘舞物（五瓣落樱 / 光玉 / 逆光花粉 / 暮色微尘），闪烁频率缓慢低于 0.4Hz
      for (const p of particles) {
        if (shouldAnimate) {
          p.x += p.vx + Math.sin(t * 0.9 + p.phase) * 0.00032;
          p.y += p.vy;
          if (p.y < -0.08) p.y = 1.08;
          if (p.y > 1.08) p.y = -0.08;
          if (p.x < -0.06) p.x = 1.06;
          if (p.x > 1.06) p.x = -0.06;
        }
        const px = p.x * w;
        const py = p.y * h;
        const pulse = 0.45 + 0.28 * Math.sin(t * 1.3 + p.phase);

        if (themeId === 'clannad-sakura') {
          ctx.save();
          ctx.translate(px, py);
          ctx.rotate(t * p.spin + p.phase);
          ctx.scale(1, 0.62 + 0.32 * Math.cos(t * 1.5 + p.phase));
          ctx.fillStyle = p.alt
            ? `rgba(251, 182, 206, ${Math.min(0.88, pulse + 0.15)})`
            : `rgba(255, 228, 238, ${Math.min(0.92, pulse + 0.2)})`;
          drawSakuraPetal(ctx, p.r * 1.15);
          ctx.restore();
        } else {
          const radius = p.r * (themeId === 'clannad-orbs' ? 3.2 : 2.3);
          const rg = ctx.createRadialGradient(px, py, 0, px, py, radius);
          const midColor =
            themeId === 'clannad-sunflower'
              ? `rgba(253, 224, 71, ${pulse * 0.72})`
              : themeId === 'clannad-starfish'
                ? p.alt
                  ? `rgba(251, 146, 60, ${pulse * 0.68})`
                  : `rgba(216, 180, 254, ${pulse * 0.62})`
                : p.alt
                  ? `rgba(125, 211, 252, ${pulse * 0.85})`
                  : `rgba(246, 196, 83, ${pulse * 0.9})`;
          rg.addColorStop(0, `rgba(255, 255, 255, ${Math.min(0.95, pulse + 0.22)})`);
          rg.addColorStop(0.36, midColor);
          rg.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = rg;
          ctx.beginPath();
          ctx.arc(px, py, radius, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      if (shouldAnimate) {
        rafId = window.requestAnimationFrame(renderFrame);
      }
    };

    rafId = window.requestAnimationFrame(renderFrame);
    return () => {
      if (rafId) window.cancelAnimationFrame(rafId);
      ro?.disconnect();
    };
  }, [themeId, reducedMotion, motionPaused, imgFailed]);

  const dialogueIdx = Math.min(
    spec.dialogues.length - 1,
    Math.floor((progress / 100) * spec.dialogues.length),
  );
  const currentDialogue = spec.dialogues[dialogueIdx];

  const stepIndex = Math.min(
    spec.steps.length - 1,
    Math.floor((progress / 100) * spec.steps.length),
  );

  // Ken Burns 缓慢呼吸推镜计算（仅使用合成器属性 scale / translate3d）
  const cameraRatio = reducedMotion ? 0 : progress / 100;
  const currentScale =
    spec.cameraMotion.fromScale +
    (spec.cameraMotion.toScale - spec.cameraMotion.fromScale) * cameraRatio;
  const currentPanX = spec.cameraMotion.panXPercent * cameraRatio;
  const currentPanY = spec.cameraMotion.panYPercent * cameraRatio;

  const isAudioActive = mode === 'overlay' ? !overlayMuted && effectiveBgmTrack !== 'off' : isMusicPreviewPlaying;

  return (
    <div
      ref={containerRef}
      role={mode === 'overlay' ? 'dialog' : undefined}
      aria-modal={mode === 'overlay' ? true : undefined}
      aria-labelledby={mode === 'overlay' ? titleHeadingId : undefined}
      onDoubleClick={mode === 'overlay' ? onSkip : undefined}
      className={`relative w-full h-full overflow-hidden select-none bg-[#050811] text-white ${
        mode === 'overlay' ? 'fixed inset-0 z-[120]' : 'rounded-2xl'
      }`}
    >
      {/* 1. 底层：原版动画高清名场面剧照（支持缓慢电影镜头推拉，主体中央完全无遮挡） */}
      {!imgFailed && (
        <img
          src={activeImgSrc}
          alt={spec.name}
          onError={() => setImgFailed(true)}
          className="absolute inset-0 w-full h-full object-cover object-center pointer-events-none will-change-transform transition-transform duration-300 ease-out"
          style={{
            transform: `scale(${currentScale.toFixed(4)}) translate3d(${currentPanX.toFixed(2)}%, ${currentPanY.toFixed(2)}%, 0)`,
          }}
        />
      )}

      {/* 2. 中层：60fps 自然氛围粒子光影层 */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full block pointer-events-none" />

      {/* 3. 电影宽银幕暗角与字幕渐变保护层（绝不在画面中央堆砌卡片遮挡人物） */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'linear-gradient(180deg, rgba(4,7,15,0.62) 0%, rgba(4,7,15,0.06) 22%, rgba(4,7,15,0.04) 62%, rgba(4,7,15,0.84) 100%)',
        }}
      />

      {/* 可选 2.35:1 变形宽银幕电影院上下遮幅 */}
      {cinemaLetterbox && (
        <>
          <div
            aria-hidden="true"
            className="absolute top-0 left-0 right-0 h-[5.5%] min-h-[18px] max-h-[42px] bg-black/90 pointer-events-none z-10 border-b border-white/5"
          />
          <div
            aria-hidden="true"
            className="absolute bottom-0 left-0 right-0 h-[5.5%] min-h-[18px] max-h-[42px] bg-black/92 pointer-events-none z-10 border-t border-white/5"
          />
        </>
      )}

      {/* 4. 左上角：原版剧集名场面场记铭牌 + 动态背景音乐唱片栏 */}
      <div
        className={`absolute left-5 right-5 flex flex-wrap items-start justify-between gap-3 z-20 ${
          cinemaLetterbox ? 'top-[7.2%]' : 'top-4'
        }`}
      >
        <div className="flex flex-col gap-1.5 max-w-[68%]">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-black/50 backdrop-blur-md border border-white/15 w-fit">
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{
                backgroundColor: spec.accent,
                boxShadow: `0 0 10px ${spec.accent}`,
              }}
            />
            <span className="text-[11px] font-semibold tracking-wider text-white/95 truncate">
              {spec.episodeTag}
            </span>
          </div>

          <h2
            id={titleHeadingId}
            className="text-sm sm:text-base font-bold tracking-wide text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.85)] pl-1"
          >
            {spec.name}
          </h2>

          <div className="inline-flex items-center gap-1.5 pl-1 text-[11px] text-white/80 drop-shadow-[0_1px_4px_rgba(0,0,0,0.9)]">
            <Music className="w-3 h-3 shrink-0" style={{ color: spec.accent }} />
            <span className="truncate">{currentTrackDisplayLabel}</span>
            {isAudioActive && (
              <span className="inline-flex items-end gap-0.5 h-2.5 ml-1" aria-hidden="true">
                <span className="w-0.5 bg-amber-300 rounded-full h-1.5 motion-safe:animate-pulse" />
                <span className="w-0.5 bg-pink-300 rounded-full h-2.5 motion-safe:animate-pulse" />
                <span className="w-0.5 bg-sky-300 rounded-full h-2 motion-safe:animate-pulse" />
              </span>
            )}
          </div>
        </div>

        {/* 右上角：无障碍控制按钮组 */}
        <div className="flex items-center gap-2">
          {mode === 'preview' && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setMotionPaused((prev) => !prev);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 min-h-7 rounded-full text-xs font-medium bg-black/55 hover:bg-black/75 text-white border border-white/20 backdrop-blur-md transition-colors"
            >
              {motionPaused ? (
                <>
                  <Play className="w-3.5 h-3.5 text-emerald-300" />
                  继续播放画面
                </>
              ) : (
                <>
                  <Pause className="w-3.5 h-3.5 text-amber-300" />
                  暂停画面
                </>
              )}
            </button>
          )}

          {mode === 'preview' && onToggleMusicPreview && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onToggleMusicPreview();
              }}
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 min-h-7 rounded-full text-xs font-semibold backdrop-blur-md border transition-colors ${
                isMusicPreviewPlaying
                  ? 'bg-amber-500/85 hover:bg-amber-500 text-slate-950 border-amber-300'
                  : 'bg-black/55 hover:bg-black/75 text-white border-white/20'
              }`}
            >
              {isMusicPreviewPlaying ? (
                <>
                  <VolumeX className="w-3.5 h-3.5" />
                  停止试听音乐
                </>
              ) : (
                <>
                  <Volume2 className="w-3.5 h-3.5" style={{ color: spec.accent }} />
                  试听背景音乐
                </>
              )}
            </button>
          )}

          {mode === 'overlay' && bgmTrackId !== 'off' && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setOverlayMuted((prev) => !prev);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 min-h-7 rounded-full text-xs font-medium bg-black/55 hover:bg-black/75 text-white border border-white/20 backdrop-blur-md transition-colors"
            >
              {overlayMuted ? (
                <>
                  <VolumeX className="w-3.5 h-3.5 text-slate-300" />
                  开启配乐
                </>
              ) : (
                <>
                  <Volume2 className="w-3.5 h-3.5 text-amber-300" />
                  静音
                </>
              )}
            </button>
          )}

          {onSkip && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onSkip();
              }}
              className="inline-flex items-center gap-1 px-3.5 py-1.5 min-h-7 rounded-full text-xs font-semibold bg-black/65 hover:bg-black/85 text-white border border-white/25 backdrop-blur-md transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              跳过序幕 (ESC)
            </button>
          )}
        </div>
      </div>

      {/* 5. 底部：原版动画电影双语台词字幕流 + 极细星轨流光进度线 */}
      <div
        className={`absolute left-6 right-6 z-20 flex flex-col items-center text-center ${
          cinemaLetterbox ? 'bottom-[7.2%]' : 'bottom-4'
        }`}
      >
        <div className="max-w-3xl w-full space-y-1.5 mb-3.5 px-2">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-black/45 border border-white/15 text-[10.5px] font-semibold tracking-wider text-amber-200/95">
            {currentDialogue.speaker}
          </div>

          <p
            key={`${themeId}-${dialogueIdx}`}
            className="text-sm sm:text-lg md:text-xl font-bold tracking-wide text-white leading-relaxed"
            style={{
              textShadow:
                '0 2px 10px rgba(0,0,0,0.95), 0 0 3px rgba(0,0,0,0.95), 0 1px 2px rgba(0,0,0,1)',
            }}
          >
            {currentDialogue.zh}
          </p>

          <p
            className="text-[11px] sm:text-xs text-slate-200/85 italic tracking-wide"
            style={{
              textShadow: '0 1px 6px rgba(0,0,0,0.95)',
            }}
          >
            {currentDialogue.en}
          </p>
        </div>

        {/* 2px 电影流光进度条 */}
        <div className="w-full max-w-2xl space-y-1.5">
          <div
            role="progressbar"
            aria-label="启动序幕加载进度"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progress}
            className="w-full h-1 rounded-full bg-white/20 overflow-hidden backdrop-blur-sm"
          >
            <div
              className="h-full rounded-full transition-all duration-150"
              style={{
                width: `${progress}%`,
                background: `linear-gradient(90deg, ${spec.accent}, ${spec.secondaryAccent})`,
                boxShadow: `0 0 12px ${spec.accent}`,
              }}
            />
          </div>

          <div className="flex items-center justify-between text-[10.5px] text-slate-200/80 drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)]">
            <span className="truncate">{spec.steps[stepIndex]}</span>
            <span className="font-mono ml-2">{progress}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
