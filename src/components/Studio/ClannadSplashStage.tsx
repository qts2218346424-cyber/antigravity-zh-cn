import React, { useEffect, useRef, useState } from 'react';
import { Sparkles, Volume2, X } from 'lucide-react';
import {
  type ClannadSplashThemeId,
  getSplashThemeSpec,
  playClannadMusicBox,
} from './clannadSplashData';

interface ClannadSplashStageProps {
  themeId: Exclude<ClannadSplashThemeId, 'none'>;
  mode?: 'preview' | 'overlay';
  durationMs?: number;
  musicEnabled?: boolean;
  onSkip?: () => void;
  onReplayMusic?: () => void;
}

interface StageParticle {
  x: number;
  y: number;
  r: number;
  vx: number;
  vy: number;
  phase: number;
  alt: boolean;
}

export const ClannadSplashStage: React.FC<ClannadSplashStageProps> = ({
  themeId,
  mode = 'preview',
  durationMs = 2600,
  musicEnabled = false,
  onSkip,
  onReplayMusic,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [progress, setProgress] = useState(mode === 'preview' ? 68 : 12);
  const spec = getSplashThemeSpec(themeId);

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

  // 可选八音盒清脆琶音播放
  useEffect(() => {
    if (!musicEnabled) return;
    const stopAudio = playClannadMusicBox(themeId);
    return () => stopAudio();
  }, [musicEnabled, themeId]);

  // 序幕进度推进（预览模式下循环演练，全屏模式下线性推进至 100%）
  useEffect(() => {
    const start = Date.now();
    const timer = window.setInterval(() => {
      const elapsed = Date.now() - start;
      if (mode === 'preview') {
        const cycle = (elapsed % 4800) / 4800;
        setProgress(Math.max(12, Math.min(100, Math.round(cycle * 108))));
      } else {
        const pct = Math.min(100, Math.round((elapsed / Math.max(1200, durationMs - 260)) * 100));
        setProgress(Math.max(14, pct));
      }
    }, 80);
    return () => window.clearInterval(timer);
  }, [durationMs, mode, themeId]);

  // 60fps Canvas 粒子与《CLANNAD》光影场渲染（严格兼容 prefers-reduced-motion）
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

    const particleCount = reducedMotion ? 18 : 46;
    const particles: StageParticle[] = Array.from({ length: particleCount }, (_, idx) => ({
      x: Math.random(),
      y: Math.random(),
      r: 2.4 + Math.random() * 6.8,
      vx: (Math.random() - 0.5) * 0.0007,
      vy:
        themeId === 'clannad-sakura'
          ? 0.0009 + Math.random() * 0.0014
          : -(0.0005 + Math.random() * 0.0011),
      phase: Math.random() * Math.PI * 2,
      alt: idx % 3 === 0,
    }));

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = container.clientWidth || 800;
      const h = container.clientHeight || 450;
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
      const w = container.clientWidth || 800;
      const h = container.clientHeight || 450;
      const t = (now - startTs) * 0.001;

      // 1. 绘制《CLANNAD》四季苍穹渐变底色
      const sky = ctx.createLinearGradient(0, 0, 0, h);
      if (themeId === 'clannad-sakura') {
        sky.addColorStop(0, '#ffeef5');
        sky.addColorStop(0.55, '#fff9fb');
        sky.addColorStop(1, '#fbd8e6');
      } else if (themeId === 'clannad-sunflower') {
        sky.addColorStop(0, '#38bdf8');
        sky.addColorStop(0.54, '#e0f2fe');
        sky.addColorStop(1, '#fef08a');
      } else if (themeId === 'clannad-starfish') {
        sky.addColorStop(0, '#100c1b');
        sky.addColorStop(0.55, '#211637');
        sky.addColorStop(1, '#3b2048');
      } else {
        sky.addColorStop(0, '#050811');
        sky.addColorStop(0.58, '#0d162c');
        sky.addColorStop(1, '#182a4f');
      }
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, w, h);

      // 2. 主题专属远景氛围光束 / 五线谱弦波 / 坡道剪影
      if (themeId === 'clannad-sakura') {
        const beam = ctx.createLinearGradient(w * 0.15, 0, w * 0.72, h);
        beam.addColorStop(0, 'rgba(255,255,255,0.68)');
        beam.addColorStop(1, 'rgba(255,214,229,0)');
        ctx.fillStyle = beam;
        ctx.beginPath();
        ctx.moveTo(w * 0.1, 0);
        ctx.lineTo(w * 0.42, 0);
        ctx.lineTo(w * 0.85, h);
        ctx.lineTo(w * 0.4, h);
        ctx.closePath();
        ctx.fill();
      } else if (themeId === 'clannad-sunflower') {
        const sun = ctx.createRadialGradient(w * 0.82, h * 0.18, 4, w * 0.82, h * 0.18, w * 0.28);
        sun.addColorStop(0, 'rgba(255,255,255,0.92)');
        sun.addColorStop(0.45, 'rgba(254,240,138,0.55)');
        sun.addColorStop(1, 'rgba(253,224,71,0)');
        ctx.fillStyle = sun;
        ctx.beginPath();
        ctx.arc(w * 0.82, h * 0.18, w * 0.28, 0, Math.PI * 2);
        ctx.fill();
      } else if (themeId === 'clannad-starfish') {
        ctx.save();
        ctx.strokeStyle = 'rgba(192,132,252,0.22)';
        ctx.lineWidth = 1.3;
        for (let lineIdx = 0; lineIdx < 3; lineIdx++) {
          ctx.beginPath();
          const baseY = h * 0.68 + lineIdx * 14;
          for (let x = 0; x <= w; x += 24) {
            const y = baseY + Math.sin(x * 0.012 + t * 1.4 + lineIdx * 0.6) * 14;
            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          }
          ctx.stroke();
        }
        ctx.restore();
      } else {
        // 幻想世界星环柔雾
        const nebula = ctx.createRadialGradient(w * 0.5, h * 0.48, 10, w * 0.5, h * 0.48, w * 0.42);
        nebula.addColorStop(0, 'rgba(246,196,83,0.14)');
        nebula.addColorStop(0.55, 'rgba(56,189,248,0.08)');
        nebula.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = nebula;
        ctx.fillRect(0, 0, w, h);
      }

      // 3. 绘制动态光玉 / 五瓣春樱 / 向日葵花粉 / 暮色星芒
      for (const p of particles) {
        if (!reducedMotion) {
          p.x += p.vx + Math.sin(t + p.phase) * 0.00038;
          p.y += p.vy;
          if (p.y < -0.08) p.y = 1.08;
          if (p.y > 1.08) p.y = -0.08;
          if (p.x < -0.06) p.x = 1.06;
          if (p.x > 1.06) p.x = -0.06;
        }
        const px = p.x * w;
        const py = p.y * h;
        const alpha = 0.42 + 0.34 * Math.sin(t * 1.7 + p.phase);

        if (themeId === 'clannad-sakura') {
          ctx.save();
          ctx.translate(px, py);
          ctx.rotate(t * 0.85 + p.phase);
          ctx.fillStyle = p.alt
            ? `rgba(240, 98, 146, ${alpha})`
            : `rgba(248, 187, 208, ${Math.min(0.95, alpha + 0.18)})`;
          ctx.beginPath();
          ctx.ellipse(0, 0, p.r * 1.25, p.r * 0.68, 0, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        } else {
          const radius = p.r * 3.1;
          const rg = ctx.createRadialGradient(px, py, 0, px, py, radius);
          const midColor =
            themeId === 'clannad-sunflower'
              ? `rgba(245, 158, 11, ${alpha})`
              : themeId === 'clannad-starfish'
                ? p.alt
                  ? `rgba(251, 146, 60, ${alpha})`
                  : `rgba(192, 132, 252, ${alpha})`
                : p.alt
                  ? `rgba(125, 211, 252, ${alpha})`
                  : `rgba(246, 196, 83, ${alpha})`;
          rg.addColorStop(0, `rgba(255, 255, 255, ${Math.min(1, alpha + 0.28)})`);
          rg.addColorStop(0.38, midColor);
          rg.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = rg;
          ctx.beginPath();
          ctx.arc(px, py, radius, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      if (!reducedMotion) {
        rafId = window.requestAnimationFrame(renderFrame);
      }
    };

    rafId = window.requestAnimationFrame(renderFrame);
    return () => {
      if (rafId) window.cancelAnimationFrame(rafId);
      ro?.disconnect();
    };
  }, [themeId]);

  const stepIndex = Math.min(
    spec.steps.length - 1,
    Math.floor((progress / 100) * spec.steps.length),
  );

  return (
    <div
      ref={containerRef}
      role={mode === 'overlay' ? 'dialog' : 'region'}
      aria-label={spec.name}
      onDoubleClick={mode === 'overlay' ? onSkip : undefined}
      className={`relative w-full h-full overflow-hidden select-none flex items-center justify-center ${
        mode === 'overlay' ? 'fixed inset-0 z-[120]' : 'rounded-2xl'
      }`}
    >
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full block pointer-events-none" />

      {/* 右上角控制按钮组 */}
      <div className="absolute top-4 right-4 z-20 flex items-center gap-2">
        {onReplayMusic && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onReplayMusic();
            }}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium backdrop-blur-md border transition-all ${
              spec.isLight
                ? 'bg-white/75 text-gray-800 border-pink-200/80 hover:bg-white'
                : 'bg-slate-900/60 text-slate-100 border-white/15 hover:bg-slate-900/80'
            }`}
            title="试听《CLANNAD》八音盒琶音"
          >
            <Volume2 className="w-3.5 h-3.5" style={{ color: spec.accent }} />
            八音盒试听
          </button>
        )}

        {onSkip && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onSkip();
            }}
            className={`inline-flex items-center gap-1 px-3.5 py-1.5 rounded-full text-xs font-medium backdrop-blur-md border transition-all ${
              spec.isLight
                ? 'bg-white/80 text-gray-800 border-gray-300/70 hover:bg-white'
                : 'bg-slate-900/65 text-slate-100 border-white/15 hover:bg-slate-900/85'
            }`}
          >
            <X className="w-3.5 h-3.5" />
            跳过序幕 (ESC)
          </button>
        )}
      </div>

      {/* 中央光学磨砂主视觉铭牌 */}
      <div
        className={`relative z-10 mx-6 max-w-xl w-full rounded-3xl px-8 py-7 text-center backdrop-blur-xl border transition-all ${
          spec.isLight
            ? 'bg-white/68 border-white/80 text-[#382932] shadow-[0_24px_60px_-15px_rgba(217,107,144,0.25)]'
            : 'bg-slate-950/55 border-white/12 text-slate-50 shadow-[0_28px_70px_-15px_rgba(0,0,0,0.72)]'
        }`}
      >
        {/* 主题徽标与代表物矢量意象（团子大家族 / 光玉 / 向日葵 / 海星） */}
        <div className="flex items-center justify-center mb-3">
          {themeId === 'clannad-sakura' && (
            <svg viewBox="0 0 136 44" className="w-28 h-9 overflow-visible" aria-hidden="true">
              <g className=" motion-safe:animate-bounce" style={{ animationDuration: '2.2s' }}>
                <ellipse cx="30" cy="25" rx="18" ry="14" fill="#ffe082" />
                <line x1="25" y1="21" x2="25" y2="27" stroke="#5c4722" strokeWidth="2" strokeLinecap="round" />
                <line x1="34" y1="21" x2="34" y2="27" stroke="#5c4722" strokeWidth="2" strokeLinecap="round" />
              </g>
              <g className="motion-safe:animate-bounce" style={{ animationDuration: '1.9s' }}>
                <ellipse cx="68" cy="22" rx="22" ry="17" fill="#f48fb1" />
                <line x1="62" y1="18" x2="62" y2="25" stroke="#5d3a47" strokeWidth="2.2" strokeLinecap="round" />
                <line x1="74" y1="18" x2="74" y2="25" stroke="#5d3a47" strokeWidth="2.2" strokeLinecap="round" />
              </g>
              <g className="motion-safe:animate-bounce" style={{ animationDuration: '2.4s' }}>
                <ellipse cx="106" cy="25" rx="18" ry="14" fill="#81d4fa" />
                <line x1="101" y1="21" x2="101" y2="27" stroke="#2c4a5e" strokeWidth="2" strokeLinecap="round" />
                <line x1="110" y1="21" x2="110" y2="27" stroke="#2c4a5e" strokeWidth="2" strokeLinecap="round" />
              </g>
            </svg>
          )}

          {themeId === 'clannad-orbs' && (
            <div
              className="w-11 h-11 rounded-full flex items-center justify-center"
              style={{
                background: 'radial-gradient(circle, #fffbeb 0%, #f6c453 45%, rgba(246,196,83,0) 72%)',
                boxShadow: '0 0 28px rgba(246, 196, 83, 0.65)',
              }}
            >
              <Sparkles className="w-5 h-5 text-amber-950" />
            </div>
          )}

          {themeId === 'clannad-sunflower' && (
            <svg viewBox="0 0 48 48" className="w-11 h-11" aria-hidden="true">
              <g fill="#f59e0b">
                <ellipse cx="24" cy="9" rx="4.5" ry="8.5" />
                <ellipse cx="24" cy="39" rx="4.5" ry="8.5" />
                <ellipse cx="9" cy="24" rx="8.5" ry="4.5" />
                <ellipse cx="39" cy="24" rx="8.5" ry="4.5" />
                <ellipse cx="13.5" cy="13.5" rx="7.5" ry="4" transform="rotate(45 13.5 13.5)" />
                <ellipse cx="34.5" cy="34.5" rx="7.5" ry="4" transform="rotate(45 34.5 34.5)" />
                <ellipse cx="34.5" cy="13.5" rx="7.5" ry="4" transform="rotate(-45 34.5 13.5)" />
                <ellipse cx="13.5" cy="34.5" rx="7.5" ry="4" transform="rotate(-45 13.5 34.5)" />
              </g>
              <circle cx="24" cy="24" r="8.5" fill="#78350f" />
            </svg>
          )}

          {themeId === 'clannad-starfish' && (
            <svg viewBox="0 0 48 48" className="w-11 h-11" aria-hidden="true">
              <path
                d="M24 5 L29.8 17.6 L43.5 19.3 L33.4 28.8 L36 42.4 L24 35.7 L12 42.4 L14.6 28.8 L4.5 19.3 L18.2 17.6 Z"
                fill="#fb923c"
                stroke="#fed7aa"
                strokeWidth="2"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </div>

        <div
          className="text-[11px] font-bold tracking-[0.22em] uppercase mb-1.5"
          style={{ color: spec.accent }}
        >
          {spec.subtitle}
        </div>

        <h2 className="text-xl sm:text-2xl font-bold tracking-wide mb-2.5">{spec.name}</h2>

        <p
          className={`text-xs sm:text-sm leading-relaxed mb-5 ${
            spec.isLight ? 'text-gray-600' : 'text-slate-300'
          }`}
        >
          {spec.quote}
        </p>

        {/* 丝滑星轨进度条 */}
        <div
          className={`w-full h-1.5 rounded-full overflow-hidden mb-2.5 ${
            spec.isLight ? 'bg-gray-900/10' : 'bg-white/12'
          }`}
        >
          <div
            className="h-full rounded-full transition-all duration-150"
            style={{
              width: `${progress}%`,
              background: `linear-gradient(90deg, ${spec.accent}, ${spec.secondaryAccent})`,
            }}
          />
        </div>

        <div
          className={`text-[11px] flex items-center justify-between ${
            spec.isLight ? 'text-gray-500' : 'text-slate-400'
          }`}
        >
          <span className="truncate">{spec.steps[stepIndex]}</span>
          <span className="font-mono ml-2">{progress}%</span>
        </div>
      </div>

      {/* 底部品牌角标 */}
      <div
        className={`absolute bottom-3.5 left-0 right-0 text-center text-[11px] tracking-wider pointer-events-none ${
          spec.isLight ? 'text-gray-600/75' : 'text-slate-300/60'
        }`}
      >
        Antigravity Studio · CLANNAD 视觉与光学声学纪念剧场
      </div>
    </div>
  );
};
