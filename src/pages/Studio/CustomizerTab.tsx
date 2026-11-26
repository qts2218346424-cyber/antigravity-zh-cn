import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Code,
  MessageSquarePlus,
  Palette,
  Play,
  RotateCcw,
  Save,
  Send,
  Sliders,
  Sparkles,
  Type,
} from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
import { resolveSkinVisualMotifs } from '../../components/Studio/skinIconRegistry';
import { studioService } from '../../services/studioService';
import type { SkinInfo, SkinManifest } from '../../types/studio';

interface CustomizerTabProps {
  skins: SkinInfo[];
  selectedSkinId: string;
  onSelectSkinId: (id: string) => void;
  onRefresh: () => Promise<void>;
}

const COLOR_GROUPS: Array<{
  title: string;
  items: Array<{ key: string; label: string }>;
}> = [
  {
    title: '核心基底',
    items: [
      { key: 'background', label: '对话主画布背景' },
      { key: 'foreground', label: '主前景色 / 正文' },
      { key: 'muted', label: '次级说明文字' },
    ],
  },
  {
    title: '应用骨架',
    items: [
      { key: 'titleBar', label: '顶部无边框标题栏' },
      { key: 'sidebar', label: '左侧会话导航栏' },
      { key: 'panel', label: '思考与工件卡片底色' },
      { key: 'input', label: '底部悬浮指令输入舱' },
    ],
  },
  {
    title: '信号交互',
    items: [
      { key: 'accent', label: '品牌主强调色 / 按钮' },
      { key: 'accentForeground', label: '强调按钮文字' },
      { key: 'border', label: '卡片极细分割线' },
      { key: 'selection', label: '会话选中光晕区' },
    ],
  },
];

const ALL_COLOR_KEYS = COLOR_GROUPS.flatMap((g) => g.items.map((i) => i.key));

export const CustomizerTab: React.FC<CustomizerTabProps> = ({
  skins,
  selectedSkinId,
  onSelectSkinId,
  onRefresh,
}) => {
  const [scope, setScope] = useState<'skin' | 'global'>('skin');
  const [manifest, setManifest] = useState<SkinManifest | null>(null);
  const [colors, setColors] = useState<Record<string, string>>({});
  const [fontFamily, setFontFamily] = useState('');
  const [monoFamily, setMonoFamily] = useState('');
  const [fontSize, setFontSize] = useState(13);

  // 光学物理材质参数
  const [glassBlur, setGlassBlur] = useState(18);
  const [cardOpacity, setCardOpacity] = useState(0.76);
  const [borderRadius, setBorderRadius] = useState(12);
  const [borderGlowAlpha, setBorderGlowAlpha] = useState(0.16);
  const [noiseGrain, setNoiseGrain] = useState(0.03);
  const [bgOpacity, setBgOpacity] = useState(0.14);
  const [bgBlur, setBgBlur] = useState(2);

  // 棱镜光学切面与工作台增强参数
  const [prismFacets, setPrismFacets] = useState(true);
  const [rimGlow, setRimGlow] = useState(true);
  const [codeEnhance, setCodeEnhance] = useState(true);
  const [ambientAura, setAmbientAura] = useState(true);
  const [backdropMode, setBackdropMode] = useState<'auto' | 'light' | 'off'>('auto');
  const [motionPreset, setMotionPreset] = useState<'full' | 'focus' | 'silent'>('full');
  const [horizonRipple, setHorizonRipple] = useState(true);
  const [inkStream, setInkStream] = useState(true);
  const [contextVial, setContextVial] = useState(true);
  const [liveCharm, setLiveCharm] = useState(true);

  // 右侧 1:1 实时动态模拟器交互状态
  const [simRim, setSimRim] = useState<{ target: 'think' | 'code' | 'composer'; x: number; y: number } | null>(null);
  const [simCodeFolded, setSimCodeFolded] = useState(false);
  const [simAura, setSimAura] = useState<'thinking' | 'attention' | 'done'>('thinking');
  const [inkDemoTick, setInkDemoTick] = useState(5);
  const [charmHop, setCharmHop] = useState(false);
  const [charmSparkKey, setCharmSparkKey] = useState(0);
  const horizonCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const ripplesRef = useRef<Array<{ x: number; y: number; r: number; a: number }>>([]);

  const [customCss, setCustomCss] = useState('');
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  const applyManifestToForm = React.useCallback((m: SkinManifest) => {
    setManifest(m);
    const isLight = m.base === 'light';
    const fallbackBg = isLight ? '#fff8fb' : '#0f172a';
    const cMap: Record<string, string> = {};
    for (const k of ALL_COLOR_KEYS) {
      cMap[k] = (m.colors?.[k] as string) || fallbackBg;
    }
    setColors(cMap);
    setFontFamily(m.font?.family || "Inter, 'PingFang SC', 'Microsoft YaHei UI', sans-serif");
    setMonoFamily(m.font?.monoFamily || "'JetBrains Mono', 'Cascadia Code', monospace");
    setFontSize(m.font?.size || 13);
    setCustomCss(m.css || m.custom_css || '');

    setGlassBlur(m.surfaces?.glass_blur ?? 18);
    setCardOpacity(m.surfaces?.card_opacity ?? 0.78);
    const parsedRadius = parseInt(String(m.surfaces?.radius || '12').replace(/px/g, ''), 10);
    setBorderRadius(Number.isFinite(parsedRadius) ? parsedRadius : 12);
    setNoiseGrain(m.surfaces?.noise_grain ?? 0.03);
    setPrismFacets(m.surfaces?.prism_facets !== false);
    setRimGlow(m.surfaces?.rim_glow !== false);
    setCodeEnhance(m.surfaces?.code_enhance !== false);
    setAmbientAura(m.surfaces?.ambient_aura !== false);
    const bm = m.surfaces?.backdrop_mode;
    setBackdropMode(bm === 'light' || bm === 'off' ? bm : 'auto');
    const mp = m.surfaces?.motion_preset;
    const resolvedPreset = mp === 'focus' || mp === 'silent' ? mp : 'full';
    setMotionPreset(resolvedPreset);
    setHorizonRipple(m.surfaces?.horizon_ripple ?? resolvedPreset === 'full');
    setInkStream(m.surfaces?.ink_stream ?? resolvedPreset !== 'silent');
    setContextVial(m.surfaces?.context_vial ?? resolvedPreset !== 'silent');
    setLiveCharm(m.surfaces?.live_charm ?? resolvedPreset === 'full');

    // 从 rgba(..., alpha) 解析高光透明度
    const glowRaw = m.surfaces?.border_glow || '';
    const rgbaMatch = glowRaw.match(/rgba?\([^,]+,[^,]+,[^,]+,\s*([0-9.]+)\)/i);
    if (rgbaMatch) {
      const parsedAlpha = parseFloat(rgbaMatch[1]);
      setBorderGlowAlpha(
        Number.isFinite(parsedAlpha) ? Math.min(0.45, Math.max(0, parsedAlpha)) : 0.16,
      );
    } else {
      setBorderGlowAlpha(0.16);
    }

    const firstBg = Array.isArray(m.background) ? m.background[0] : m.background;
    setBgOpacity(firstBg?.opacity ?? 0.14);
    setBgBlur(firstBg?.blur ?? 2);
    setDirty(false);
  }, []);

  useEffect(() => {
    if (!selectedSkinId && skins.length > 0) {
      onSelectSkinId(skins[0].id);
      return;
    }
    if (!selectedSkinId) return;

    studioService
      .getSkinManifest(selectedSkinId)
      .then(applyManifestToForm)
      .catch((err) => showToast(`加载材质包清单失败: ${String(err)}`, 'error'));
  }, [selectedSkinId, skins, onSelectSkinId, applyManifestToForm]);

  const handleSave = async () => {
    if (scope === 'skin' && !selectedSkinId) {
      showToast('请先选择需要微调的材质包', 'warning');
      return;
    }
    setSaving(true);
    try {
      const defaultShadow =
        manifest?.base === 'light'
          ? '0 16px 36px -12px rgba(15, 23, 42, 0.14)'
          : '0 20px 50px -12px rgba(0, 0, 0, 0.72)';
      const patch: Record<string, unknown> = {
        colors,
        surfaces: {
          radius: `${borderRadius}px`,
          glass_blur: glassBlur,
          card_opacity: Number(cardOpacity.toFixed(2)),
          border_glow: `rgba(255, 255, 255, ${borderGlowAlpha.toFixed(2)})`,
          noise_grain: Number(noiseGrain.toFixed(3)),
          shadow_elevation: manifest?.surfaces?.shadow_elevation || defaultShadow,
          prism_facets: prismFacets,
          rim_glow: rimGlow,
          code_enhance: codeEnhance,
          ambient_aura: ambientAura,
          backdrop_mode: backdropMode,
          motion_preset: motionPreset,
          horizon_ripple: horizonRipple,
          ink_stream: inkStream,
          context_vial: contextVial,
          live_charm: liveCharm,
        },
        font: {
          family: fontFamily.trim(),
          monoFamily: monoFamily.trim(),
          size: fontSize,
        },
        css: customCss,
      };

      if (manifest?.background) {
        if (Array.isArray(manifest.background)) {
          patch.background = manifest.background.map((item, idx) =>
            idx === 0 ? { ...item, opacity: bgOpacity, blur: bgBlur } : item,
          );
        } else {
          patch.background = {
            ...manifest.background,
            opacity: bgOpacity,
            blur: bgBlur,
          };
        }
      }

      await studioService.saveOverride(scope, scope === 'skin' ? selectedSkinId : null, patch);
      setDirty(false);
      showToast(
        scope === 'global'
          ? '已保存全局光学覆盖层并热重载至 Antigravity 应用'
          : `已保存「${selectedSkinId}」高定微调并实时推送至 Antigravity 应用`,
        'success',
      );
      await onRefresh();
    } catch (err: unknown) {
      showToast(`保存失败: ${String(err)}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    try {
      await studioService.resetOverride(scope, scope === 'skin' ? selectedSkinId : null);
      showToast('已重置覆盖层并恢复材质包原始设定', 'info');
      await onRefresh();
      if (selectedSkinId) {
        const refreshed = await studioService.getSkinManifest(selectedSkinId);
        applyManifestToForm(refreshed);
      }
    } catch (err: unknown) {
      showToast(`重置失败: ${String(err)}`, 'error');
    } finally {
      setDirty(false);
    }
  };

  const accent = colors.accent || '#38bdf8';
  const bg = colors.background || '#080a0f';
  const fg = colors.foreground || '#e6edf7';
  const panel = colors.panel || '#0f141f';
  const border = colors.border || '#1f293b';

  const selectedSkin = useMemo(
    () => skins.find((s) => s.id === selectedSkinId),
    [skins, selectedSkinId],
  );
  const motifs = useMemo(
    () => (selectedSkin ? resolveSkinVisualMotifs(selectedSkin) : null),
    [selectedSkin],
  );

  const applyMotionPreset = (preset: 'full' | 'focus' | 'silent') => {
    setMotionPreset(preset);
    if (preset === 'full') {
      setPrismFacets(true);
      setRimGlow(true);
      setCodeEnhance(true);
      setAmbientAura(true);
      setHorizonRipple(true);
      setInkStream(true);
      setContextVial(true);
      setLiveCharm(true);
    } else if (preset === 'focus') {
      setPrismFacets(true);
      setRimGlow(true);
      setCodeEnhance(true);
      setAmbientAura(true);
      setHorizonRipple(false);
      setInkStream(true);
      setContextVial(true);
      setLiveCharm(false);
    } else {
      setPrismFacets(true);
      setRimGlow(false);
      setCodeEnhance(true);
      setAmbientAura(false);
      setHorizonRipple(false);
      setInkStream(false);
      setContextVial(false);
      setLiveCharm(false);
    }
    setDirty(true);
  };

  useEffect(() => {
    const cv = horizonCanvasRef.current;
    if (!cv || !horizonRipple || motionPreset === 'silent') return;
    let raf = 0;
    let phase = 0;
    let lastDraw = 0;
    const glyphs = ['·', '∘', '✦', '◇', '⊹'];

    const parseHex = (hex: string) => {
      const m = /^#([0-9a-f]{6})/i.exec(hex.trim());
      if (!m) return { r: 56, g: 189, b: 248 };
      return {
        r: parseInt(m[1].slice(0, 2), 16),
        g: parseInt(m[1].slice(2, 4), 16),
        b: parseInt(m[1].slice(4, 6), 16),
      };
    };

    const draw = (ts: number) => {
      if (ts - lastDraw >= 36) {
        lastDraw = ts;
        const w = cv.clientWidth || 320;
        const h = cv.clientHeight || 420;
        if (cv.width !== w || cv.height !== h) {
          cv.width = w;
          cv.height = h;
        }
        const ctx = cv.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, w, h);
          const rgb = parseHex(accent);
          phase += 0.055;
          ctx.font = '11px monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          for (let y = 20; y < h - 16; y += 26) {
            for (let x = 20; x < w - 16; x += 26) {
              const wave = Math.sin(x * 0.024 + y * 0.02 + phase) * 0.5 + 0.5;
              let boost = 0;
              for (const rp of ripplesRef.current) {
                const d = Math.abs(Math.hypot(x - rp.x, y - rp.y) - rp.r);
                if (d < 36) boost = Math.max(boost, (1 - d / 36) * rp.a);
              }
              const alpha = Math.min(0.85, 0.06 + wave * 0.1 + boost * 0.72);
              const gIdx = Math.min(glyphs.length - 1, Math.floor((wave + boost) * 2.6));
              ctx.fillStyle = `rgba(${rgb.r},${rgb.g},${rgb.b},${alpha.toFixed(3)})`;
              ctx.fillText(glyphs[gIdx], x, y);
            }
          }
          ripplesRef.current = ripplesRef.current
            .map((rp) => ({ ...rp, r: rp.r + 5.5, a: rp.a * 0.93 }))
            .filter((rp) => rp.a > 0.05);
        }
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [accent, horizonRipple, motionPreset]);

  useEffect(() => {
    if (inkDemoTick >= 5) return;
    const t = setTimeout(() => setInkDemoTick((v) => v + 1), 90);
    return () => clearTimeout(t);
  }, [inkDemoTick]);

  return (
    <div
      className="grid grid-cols-1 xl:grid-cols-12 gap-6"
      onChangeCapture={(e) => {
        const target = e.target as HTMLElement;
        if (target.tagName === 'SELECT') return;
        setDirty(true);
      }}
    >
      {/* 左侧参数实验室 */}
      <div className="xl:col-span-7 space-y-5">
        {/* 顶栏选择器 */}
        <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-4 flex flex-wrap items-center justify-between gap-3 shadow-sm">
          <div className="flex flex-wrap items-center gap-3">
            <select
              value={selectedSkinId}
              onChange={(e) => onSelectSkinId(e.target.value)}
              className="rounded-xl border border-gray-300 dark:border-white/15 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs font-semibold"
            >
              {skins.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.id})
                </option>
              ))}
            </select>

            <div className="inline-flex rounded-xl bg-gray-100 dark:bg-white/5 p-0.5 text-xs border border-gray-200/60 dark:border-white/10">
              <button
                type="button"
                onClick={() => setScope('skin')}
                className={`rounded-lg px-3 py-1 transition-all ${
                  scope === 'skin'
                    ? 'bg-white dark:bg-slate-800 font-semibold shadow-sm text-sky-500'
                    : 'text-gray-500'
                }`}
              >
                仅调当前材质
              </button>
              <button
                type="button"
                onClick={() => setScope('global')}
                className={`rounded-lg px-3 py-1 transition-all ${
                  scope === 'global'
                    ? 'bg-white dark:bg-slate-800 font-semibold shadow-sm text-indigo-500'
                    : 'text-gray-500'
                }`}
              >
                全局光学覆盖
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {dirty && (
              <span className="rounded-full bg-amber-500/15 border border-amber-500/30 px-2.5 py-0.5 text-[10.5px] font-medium text-amber-600 dark:text-amber-300">
                有未保存微调
              </span>
            )}
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center gap-1 rounded-xl border border-gray-300 dark:border-white/15 px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              还原
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 px-4 py-1.5 text-xs font-semibold text-white shadow hover:opacity-90 disabled:opacity-60"
            >
              <Save className="h-3.5 w-3.5" />
              {saving ? '编译推送中...' : '保存并热重载'}
            </button>
          </div>
        </div>

        {/* 模块一：色彩基因谱系 (Color DNA) */}
        <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-gray-900 dark:text-white">
            <Palette className="h-4 w-4 text-sky-500" />
            Antigravity 应用色彩基因谱系 (Color DNA)
          </div>

          <div className="space-y-4">
            {COLOR_GROUPS.map((grp) => (
              <div key={grp.title} className="space-y-2">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                  {grp.title}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                  {grp.items.map((item) => {
                    const val = colors[item.key] || '#0f172a';
                    const pickerHex = /^#[0-9a-fA-F]{6}$/.test(val.slice(0, 7))
                      ? val.slice(0, 7)
                      : '#38bdf8';
                    return (
                      <div
                        key={item.key}
                        className="flex items-center justify-between gap-2 rounded-xl border border-gray-200/70 dark:border-white/10 bg-gray-50/70 dark:bg-black/25 px-2.5 py-2"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="text-[11px] font-medium text-gray-700 dark:text-gray-200 truncate">
                            {item.label}
                          </div>
                          <input
                            type="text"
                            value={val}
                            onChange={(e) =>
                              setColors((prev) => ({ ...prev, [item.key]: e.target.value }))
                            }
                            className="w-full bg-transparent text-[10px] font-mono text-gray-400 focus:text-sky-400 focus:outline-none"
                          />
                        </div>
                        <input
                          type="color"
                          value={pickerHex}
                          onChange={(e) =>
                            setColors((prev) => ({ ...prev, [item.key]: e.target.value }))
                          }
                          className="h-7 w-7 shrink-0 cursor-pointer rounded-lg border border-white/20 bg-transparent p-0"
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 模块二：光学表面与物理质感 */}
        <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-gray-900 dark:text-white">
            <Sliders className="h-4 w-4 text-purple-500" />
            光学表面与物理质感 (Surface Physics)
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <div className="flex justify-between text-[11px] text-gray-500 mb-1">
                <span>亚克力高斯模糊</span>
                <span className="font-mono text-sky-500">{glassBlur}px</span>
              </div>
              <input
                type="range"
                min={0}
                max={36}
                value={glassBlur}
                onChange={(e) => setGlassBlur(Number(e.target.value))}
                className="w-full accent-sky-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-gray-500 mb-1">
                <span>思考卡片通透度</span>
                <span className="font-mono text-indigo-500">{Math.round(cardOpacity * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.25}
                max={1}
                step={0.02}
                value={cardOpacity}
                onChange={(e) => setCardOpacity(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-gray-500 mb-1">
                <span>玻璃边缘折射高光</span>
                <span className="font-mono text-amber-500">{Math.round(borderGlowAlpha * 100)}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={0.45}
                step={0.02}
                value={borderGlowAlpha}
                onChange={(e) => setBorderGlowAlpha(Number(e.target.value))}
                className="w-full accent-amber-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-gray-500 mb-1">
                <span>卡片与输入舱圆角</span>
                <span className="font-mono text-emerald-500">{borderRadius}px</span>
              </div>
              <input
                type="range"
                min={0}
                max={24}
                value={borderRadius}
                onChange={(e) => setBorderRadius(Number(e.target.value))}
                className="w-full accent-emerald-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-gray-500 mb-1">
                <span>插画暗纹曝光度</span>
                <span className="font-mono">{Math.round(bgOpacity * 100)}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={0.65}
                step={0.01}
                value={bgOpacity}
                onChange={(e) => setBgOpacity(Number(e.target.value))}
                className="w-full accent-pink-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-gray-500 mb-1">
                <span>胶片微颗粒纹理</span>
                <span className="font-mono">{Math.round(noiseGrain * 100)}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={0.12}
                step={0.01}
                value={noiseGrain}
                onChange={(e) => setNoiseGrain(Number(e.target.value))}
                className="w-full accent-slate-500"
              />
            </div>
          </div>

          {/* 棱镜光学元素与工作台增强 */}
          <div className="pt-3 border-t border-gray-200/70 dark:border-white/10 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-[11px] font-semibold text-gray-700 dark:text-gray-200">
                动态光学引擎与工作台增强（自适应当前主题色）
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <div className="inline-flex rounded-xl bg-gray-100 dark:bg-white/5 p-0.5 text-[10.5px] border border-gray-200/60 dark:border-white/10">
                  {(
                    [
                      ['full', '完整光效'],
                      ['focus', '专注编码'],
                      ['silent', '静默省电'],
                    ] as const
                  ).map(([presetKey, presetLabel]) => (
                    <button
                      key={presetKey}
                      type="button"
                      onClick={() => applyMotionPreset(presetKey)}
                      className={`rounded-lg px-2.5 py-1 transition-all ${
                        motionPreset === presetKey
                          ? 'bg-gradient-to-r from-sky-500 to-indigo-500 font-semibold text-white shadow-sm'
                          : 'text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
                      }`}
                    >
                      {presetLabel}
                    </button>
                  ))}
                </div>
                <div className="inline-flex rounded-xl bg-gray-100 dark:bg-white/5 p-0.5 text-[10.5px] border border-gray-200/60 dark:border-white/10">
                  {(
                    [
                      ['auto', '模糊平衡'],
                      ['light', '轻盈模糊'],
                      ['off', '纯切面'],
                    ] as const
                  ).map(([modeKey, modeLabel]) => (
                    <button
                      key={modeKey}
                      type="button"
                      onClick={() => {
                        setBackdropMode(modeKey);
                        setDirty(true);
                      }}
                      className={`rounded-lg px-2 py-1 transition-all ${
                        backdropMode === modeKey
                          ? 'bg-white dark:bg-slate-800 font-semibold text-sky-500 shadow-sm'
                          : 'text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
                      }`}
                    >
                      {modeLabel}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {(
                [
                  {
                    key: 'horizon',
                    label: 'Canvas 字符波纹矩阵',
                    desc: '首页交互波纹与对话地平线极光（空闲 0fps）',
                    checked: horizonRipple,
                    toggle: () => setHorizonRipple((v) => !v),
                  },
                  {
                    key: 'rim',
                    label: 'Canvas 近场棱镜折光',
                    desc: '指针靠近卡片自动绘制主题色激光边框高光',
                    checked: rimGlow,
                    toggle: () => setRimGlow((v) => !v),
                  },
                  {
                    key: 'ink',
                    label: '五级水墨流式淡入',
                    desc: '零 DOM 侵入的 AI 流式吐字水墨晕染渐显',
                    checked: inkStream,
                    toggle: () => setInkStream((v) => !v),
                  },
                  {
                    key: 'vial',
                    label: '512K 液态上下文试管',
                    desc: '双波浪上升气泡玻璃试管，点击切换光效预设',
                    checked: contextVial,
                    toggle: () => setContextVial((v) => !v),
                  },
                  {
                    key: 'charm',
                    label: '活体伴读角色与星芒彩蛋',
                    desc: '输入舱挂件呼吸律动、鼠标注视与点击 Q 弹跳跃',
                    checked: liveCharm,
                    toggle: () => setLiveCharm((v) => !v),
                  },
                  {
                    key: 'aura',
                    label: '三态切工水晶光束',
                    desc: '思考流光 / 待决策琥珀 / 完成翡翠回响扫光',
                    checked: ambientAura,
                    toggle: () => setAmbientAura((v) => !v),
                  },
                  {
                    key: 'facets',
                    label: '棱镜切面与控制台凹槽',
                    desc: '旋转流光输入舱、kbd 键帽、文件芯片与终端内陷',
                    checked: prismFacets,
                    toggle: () => setPrismFacets((v) => !v),
                  },
                  {
                    key: 'code',
                    label: '代码块吸顶折叠与导轨',
                    desc: '顶栏吸顶、长代码手动收起、Alt+↑/↓ 轮次跳转',
                    checked: codeEnhance,
                    toggle: () => setCodeEnhance((v) => !v),
                  },
                ] as const
              ).map((item) => (
                <button
                  key={item.key}
                  type="button"
                  role="switch"
                  aria-checked={item.checked}
                  onClick={() => {
                    item.toggle();
                    setDirty(true);
                  }}
                  className={`flex items-center justify-between gap-3 rounded-xl border px-3 py-2.5 text-left transition-all active:scale-[0.99] ${
                    item.checked
                      ? 'border-sky-500/40 bg-sky-500/10 dark:bg-sky-500/10'
                      : 'border-gray-200/70 dark:border-white/10 bg-gray-50/70 dark:bg-black/20 opacity-75'
                  }`}
                >
                  <div className="min-w-0">
                    <div className="text-[11.5px] font-semibold text-gray-800 dark:text-gray-100 truncate">
                      {item.label}
                    </div>
                    <div className="text-[10px] text-gray-500 dark:text-gray-400 truncate">
                      {item.desc}
                    </div>
                  </div>
                  <span
                    className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors ${
                      item.checked ? 'bg-sky-500' : 'bg-gray-300 dark:bg-white/15'
                    }`}
                  >
                    <span
                      className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
                        item.checked ? 'translate-x-4.5' : 'translate-x-1'
                      }`}
                    />
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 模块三：字体与自定义 CSS */}
        <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-gray-900 dark:text-white">
            <Type className="h-4 w-4 text-emerald-500" />
            字体排印与自定义 CSS 注入
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-1">
              <label className="block text-[11px] text-gray-500 mb-1">全局字号 ({fontSize}px)</label>
              <input
                type="range"
                min={11}
                max={18}
                value={fontSize}
                onChange={(e) => setFontSize(Number(e.target.value))}
                className="w-full accent-emerald-500 mt-1.5"
              />
            </div>
            <div>
              <label className="block text-[11px] text-gray-500 mb-1">对话界面字体族</label>
              <input
                type="text"
                value={fontFamily}
                onChange={(e) => setFontFamily(e.target.value)}
                className="w-full rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-black/30 px-3 py-1.5 text-xs font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] text-gray-500 mb-1">代码块与终端字体</label>
              <input
                type="text"
                value={monoFamily}
                onChange={(e) => setMonoFamily(e.target.value)}
                className="w-full rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-black/30 px-3 py-1.5 text-xs font-mono"
              />
            </div>
          </div>

          <div className="space-y-1.5 pt-1">
            <div className="flex items-center gap-1.5 text-[11px] text-gray-500">
              <Code className="h-3.5 w-3.5 text-emerald-500" />
              自定义附加样式表（安全沙盒编译，自动映射至 Antigravity 应用渲染层）
            </div>
            <textarea
              rows={4}
              value={customCss}
              onChange={(e) => setCustomCss(e.target.value)}
              placeholder="/* 可直接书写 Antigravity 应用 (--background / --card / --primary / aside) 微调规则 */"
              className="w-full rounded-xl border border-gray-200 dark:border-white/10 bg-slate-950 p-3 text-xs font-mono text-emerald-300 focus:outline-none focus:ring-2 focus:ring-sky-500/40"
            />
          </div>
        </div>
      </div>

      {/* 右侧 1:1 真实感 Google Antigravity 桌面应用视窗模拟器 */}
      <div className="xl:col-span-5">
        <div className="sticky top-6 rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between gap-2 text-xs font-bold text-gray-800 dark:text-white">
            <span className="inline-flex items-center gap-1.5">
              <Sparkles className="h-4 w-4 text-sky-500" />
              Antigravity 动态视窗实验室
            </span>
            <div className="flex items-center gap-1.5 text-[10px] font-normal">
              <button
                type="button"
                onClick={() =>
                  setSimAura((a) =>
                    a === 'thinking' ? 'attention' : a === 'attention' ? 'done' : 'thinking',
                  )
                }
                className="rounded-lg border border-gray-200 dark:border-white/15 px-2 py-0.5 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10"
              >
                光束：{simAura === 'thinking' ? '思考流光' : simAura === 'attention' ? '待决策琥珀' : '完成翡翠'}
              </button>
              <button
                type="button"
                onClick={() => setInkDemoTick(0)}
                className="inline-flex items-center gap-1 rounded-lg border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-sky-600 dark:text-sky-300 hover:bg-sky-500/20"
              >
                <Play className="h-2.5 w-2.5" />
                水墨演示
              </button>
            </div>
          </div>

          <div
            className="relative h-[520px] w-full overflow-hidden rounded-2xl border shadow-2xl flex flex-col select-none"
            onClick={(e) => {
              const cv = horizonCanvasRef.current;
              if (!cv || !horizonRipple || motionPreset === 'silent') return;
              const rect = cv.getBoundingClientRect();
              ripplesRef.current.push({
                x: Math.round(e.clientX - rect.left),
                y: Math.round(e.clientY - rect.top),
                r: 6,
                a: 0.95,
              });
            }}
            onMouseMove={(e) => {
              const cv = horizonCanvasRef.current;
              if (!cv || !horizonRipple || motionPreset === 'silent' || Math.random() > 0.18) return;
              const rect = cv.getBoundingClientRect();
              ripplesRef.current.push({
                x: Math.round(e.clientX - rect.left),
                y: Math.round(e.clientY - rect.top),
                r: 4,
                a: 0.55,
              });
              if (ripplesRef.current.length > 8) ripplesRef.current.shift();
            }}
            style={{
              backgroundColor: bg,
              color: fg,
              borderColor: border,
              fontFamily,
              fontSize: `${fontSize}px`,
              backgroundImage: `radial-gradient(76% 42% at 50% 0%, ${accent}22 0%, transparent 72%), radial-gradient(circle at 86% 84%, ${accent}18 0%, transparent 56%)`,
            }}
          >
            {/* 真实交互式 Canvas 字符波纹矩阵 */}
            {horizonRipple && motionPreset !== 'silent' && (
              <canvas
                ref={horizonCanvasRef}
                className="pointer-events-none absolute inset-0 z-0 h-full w-full opacity-90"
              />
            )}

            {/* 模拟 Antigravity 应用无边框顶栏 */}
            <div
              className="relative z-10 flex items-center justify-between px-3.5 py-2.5 text-[11px] border-b"
              style={{
                backgroundColor: colors.titleBar || '#07090e',
                borderColor: border,
              }}
            >
              <div className="flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-md shadow-sm"
                  style={{ backgroundColor: accent }}
                />
                <span className="font-semibold tracking-tight opacity-95">Antigravity</span>
              </div>
              <div
                className="px-2.5 py-0.5 rounded-full text-[10px] font-medium opacity-85"
                style={{
                  backgroundColor: colors.selection || `${accent}24`,
                  border: `1px solid ${border}`,
                }}
              >
                当前工作区 · antigravity-cn
              </div>
              <div className="flex items-center gap-2 opacity-50 text-[10px]">
                <span>—</span>
                <span>□</span>
                <span>×</span>
              </div>
            </div>

            {/* Antigravity 应用主区：左侧会话抽屉 + 中央对话与指令输入舱 */}
            <div className="relative z-10 flex flex-1 min-h-0">
              {/* 顶部 2.5px 三态切工水晶光束预览条 */}
              {ambientAura && (
                <div
                  className="pointer-events-none absolute top-0 left-0 right-0 h-[2.5px] z-20 transition-all duration-300"
                  style={{
                    background:
                      simAura === 'attention'
                        ? 'linear-gradient(90deg, transparent 0%, #f59e0b 50%, transparent 100%)'
                        : simAura === 'done'
                          ? 'linear-gradient(90deg, transparent 0%, #10b981 48%, #a7f3d0 50%, #10b981 52%, transparent 100%)'
                          : `linear-gradient(90deg, transparent 0%, ${accent} 35%, #ffffff 50%, ${accent} 65%, transparent 100%)`,
                    boxShadow:
                      simAura === 'attention'
                        ? '0 0 12px rgba(245,158,11,0.75)'
                        : simAura === 'done'
                          ? '0 0 12px rgba(16,185,129,0.75)'
                          : `0 0 12px ${accent}88`,
                  }}
                />
              )}

              {/* 左侧会话导航抽屉（无 IDE 活动栏与文件树） */}
              <div
                className="w-36 p-3 border-r flex flex-col justify-between text-[11px]"
                style={{
                  backgroundColor: colors.sidebar || '#0c1018',
                  borderColor: border,
                }}
              >
                <div className="space-y-2">
                  <div
                    className="px-2.5 py-1.5 font-semibold flex items-center gap-1.5 shadow-sm"
                    style={{
                      backgroundColor: `${accent}22`,
                      color: fg,
                      borderRadius: `${Math.min(borderRadius, 12)}px`,
                      border: `1px solid ${accent}48`,
                    }}
                  >
                    <MessageSquarePlus className="h-3.5 w-3.5" style={{ color: accent }} />
                    <span>新建对话</span>
                  </div>

                  <div className="pt-1 space-y-1">
                    <div className="text-[10px] font-semibold uppercase tracking-wider opacity-45 px-1">
                      近期智能体会话
                    </div>
                    <div
                      className="px-2.5 py-1.5 font-medium truncate"
                      style={{
                        backgroundColor: colors.selection || `${accent}2e`,
                        borderRadius: `${Math.min(borderRadius, 10)}px`,
                      }}
                    >
                      光学皮肤引擎重构
                    </div>
                    <div className="px-2.5 py-1 opacity-65 truncate">多智能体架构推演</div>
                    <div className="px-2.5 py-1 opacity-50 truncate">桌面伴侣语音调优</div>
                  </div>
                </div>

                <div
                  className="px-2 py-1.5 text-[10px] opacity-75 truncate border-t"
                  style={{ borderColor: border, color: colors.muted || '#7e8ca6' }}
                >
                  主题：{manifest?.id || selectedSkinId}
                </div>
              </div>

              {/* 中央智能体对话流与悬浮输入舱 */}
              <div className="relative flex-1 flex flex-col min-w-0 p-3.5 justify-between gap-2.5 overflow-hidden">
                {/* 右侧微缩会话轮次导轨 */}
                {codeEnhance && (
                  <div
                    className="absolute right-2 top-1/2 -translate-y-1/2 z-20 flex flex-col items-center gap-1 px-1 py-1.5 rounded-full"
                    style={{
                      backgroundColor: `color-mix(in srgb, ${panel} 88%, transparent)`,
                      border: `1px solid ${border}`,
                      boxShadow: '0 6px 16px rgba(0,0,0,0.22)',
                    }}
                    title="轮次导轨 (Alt+↑/↓)"
                  >
                    <span className="text-[8px] opacity-65">↑</span>
                    <span className="text-[8px] font-mono opacity-80">2/3</span>
                    <span className="text-[8px] opacity-65">↓</span>
                  </div>
                )}

                <div className="space-y-2.5">
                  {/* 用户消息胶囊（切面微渐变 + 顶沿折射高光） */}
                  <div className="flex justify-end">
                    <div
                      className="px-3 py-1.5 text-[11px] max-w-[85%]"
                      style={{
                        backgroundColor: colors.selection || `${accent}28`,
                        backgroundImage: prismFacets
                          ? `linear-gradient(180deg, ${accent}20 0%, transparent 100%)`
                          : undefined,
                        borderRadius: `${borderRadius}px`,
                        border: `1px solid ${border}`,
                        boxShadow: prismFacets
                          ? `inset 0 1px 0 rgba(255,255,255,${Math.min(0.9, borderGlowAlpha + 0.1)})`
                          : undefined,
                      }}
                    >
                      将这些棱镜元素融合进 Antigravity 主题
                    </div>
                  </div>

                  {/* 玻璃态深度思考折叠卡（支持指针边框高光交互 + 文件芯片 + kbd 键帽） */}
                  <div
                    className="p-2.5 space-y-1.5 transition-all"
                    onMouseMove={(e) => {
                      if (!rimGlow) return;
                      const rect = e.currentTarget.getBoundingClientRect();
                      setSimRim({
                        target: 'think',
                        x: Math.round(e.clientX - rect.left),
                        y: Math.round(e.clientY - rect.top),
                      });
                    }}
                    onMouseLeave={() => setSimRim(null)}
                    style={{
                      backgroundColor: `color-mix(in srgb, ${panel} ${Math.round(cardOpacity * 100)}%, transparent)`,
                      backgroundImage:
                        rimGlow && simRim?.target === 'think'
                          ? `radial-gradient(180px circle at ${simRim.x}px ${simRim.y}px, ${accent}26 0%, transparent 72%)`
                          : undefined,
                      borderRadius: `${borderRadius}px`,
                      border: `1px solid ${
                        rimGlow && simRim?.target === 'think' ? `${accent}88` : border
                      }`,
                      backdropFilter:
                        backdropMode === 'off'
                          ? undefined
                          : `blur(${backdropMode === 'light' ? Math.max(4, Math.round(glassBlur / 2)) : glassBlur}px) saturate(1.35)`,
                      boxShadow: `inset 0 1px 0 rgba(255,255,255,${borderGlowAlpha}), 0 14px 32px rgba(0,0,0,0.28)`,
                    }}
                  >
                    <div className="flex items-center justify-between text-[10px]">
                      <span
                        className="font-semibold flex items-center gap-1.5"
                        style={{ color: accent }}
                      >
                        <span
                          className="h-1.5 w-1.5 rounded-full animate-pulse"
                          style={{ backgroundColor: accent }}
                        />
                        深度思考过程 · 光学切面同步
                      </span>
                      {prismFacets ? (
                        <span className="inline-flex items-center gap-1">
                          <kbd
                            className="px-1 py-0.5 rounded text-[9px] font-mono"
                            style={{
                              backgroundColor: colors.input || panel,
                              border: `1px solid ${border}`,
                              borderBottomWidth: '2px',
                            }}
                          >
                            Alt
                          </kbd>
                          <kbd
                            className="px-1 py-0.5 rounded text-[9px] font-mono"
                            style={{
                              backgroundColor: colors.input || panel,
                              border: `1px solid ${border}`,
                              borderBottomWidth: '2px',
                            }}
                          >
                            ↑
                          </kbd>
                        </span>
                      ) : (
                        <span style={{ color: colors.muted || '#7e8ca6' }}>实时热重载</span>
                      )}
                    </div>
                    <p className="text-[10.5px] leading-relaxed opacity-90">
                      <span
                        className="transition-all duration-200"
                        style={{
                          opacity: !inkStream || inkDemoTick >= 1 ? 1 : 0.15,
                          color: inkStream && inkDemoTick === 1 ? accent : fg,
                        }}
                      >
                        已更新{' '}
                      </span>
                      <span
                        className="inline-block px-1.5 py-0.2 text-[9.5px] font-mono transition-all duration-200"
                        style={{
                          backgroundColor: prismFacets ? `${accent}1e` : 'transparent',
                          border: prismFacets ? `1px solid ${accent}4a` : 'none',
                          borderRadius: '9999px',
                          opacity: !inkStream || inkDemoTick >= 2 ? 1 : 0.15,
                        }}
                      >
                        skin_manager.rs
                      </span>{' '}
                      <span
                        className="transition-all duration-200"
                        style={{
                          opacity: !inkStream || inkDemoTick >= 3 ? 1 : 0.15,
                          color: inkStream && inkDemoTick === 3 ? accent : fg,
                        }}
                      >
                        切面令牌，
                      </span>
                      <span
                        className="transition-all duration-200"
                        style={{
                          opacity: !inkStream || inkDemoTick >= 4 ? 1 : 0.15,
                          color: inkStream && inkDemoTick === 4 ? accent : fg,
                        }}
                      >
                        水墨流式渐显与波纹矩阵均已实时激活。
                      </span>
                    </p>
                  </div>

                  {/* 工件代码块卡（Sticky 顶栏 + 可点击折叠） */}
                  <div
                    className="overflow-hidden text-[10.5px] leading-relaxed transition-all"
                    onMouseMove={(e) => {
                      if (!rimGlow) return;
                      const rect = e.currentTarget.getBoundingClientRect();
                      setSimRim({
                        target: 'code',
                        x: Math.round(e.clientX - rect.left),
                        y: Math.round(e.clientY - rect.top),
                      });
                    }}
                    onMouseLeave={() => setSimRim(null)}
                    style={{
                      backgroundColor: colors.input || '#131a27',
                      fontFamily: monoFamily,
                      borderRadius: `${Math.max(6, borderRadius - 2)}px`,
                      border: `1px solid ${
                        rimGlow && simRim?.target === 'code' ? `${accent}88` : border
                      }`,
                      backgroundImage:
                        rimGlow && simRim?.target === 'code'
                          ? `radial-gradient(180px circle at ${simRim.x}px ${simRim.y}px, ${accent}22 0%, transparent 72%)`
                          : undefined,
                    }}
                  >
                    {codeEnhance && (
                      <div
                        className="flex items-center justify-between px-2.5 py-1 text-[9.5px] border-b"
                        style={{
                          borderColor: border,
                          backgroundColor: `color-mix(in srgb, ${panel} 80%, transparent)`,
                        }}
                      >
                        <span className="opacity-70">rust · skin_manager.rs</span>
                        <button
                          type="button"
                          onClick={() => setSimCodeFolded((v) => !v)}
                          className="rounded-full px-2 py-0.5 text-[9px] font-semibold transition-colors"
                          style={{
                            backgroundColor: `${accent}24`,
                            border: `1px solid ${accent}52`,
                            color: fg,
                          }}
                        >
                          {simCodeFolded ? '展开代码 (52行)' : '收起代码 (52行)'}
                        </button>
                      </div>
                    )}
                    {!simCodeFolded && (
                      <div className="px-2.5 py-1.5">
                        <div>
                          <span style={{ color: accent }}>setHubCurtainColor</span>(win,{' '}
                          <span style={{ color: accent }}>&quot;{bg}&quot;</span>);
                        </div>
                        <div className="pl-3 opacity-85">
                          prismFacets: <span style={{ color: accent }}>{String(prismFacets)}</span>, backdrop:{' '}
                          <span style={{ color: accent }}>{backdropMode}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 沉降式控制台凹槽 Console Well */}
                  {prismFacets && (
                    <div
                      className="px-2.5 py-1.5 text-[9.5px] font-mono flex items-center justify-between"
                      style={{
                        backgroundColor:
                          manifest?.base === 'light' ? 'rgba(15,23,42,0.05)' : 'rgba(0,0,0,0.42)',
                        borderRadius: `${Math.max(6, borderRadius - 4)}px`,
                        border: `1px solid ${border}`,
                        boxShadow: 'inset 0 2px 5px rgba(0,0,0,0.28)',
                      }}
                    >
                      <span className="opacity-80">
                        <span style={{ color: accent }}>$</span> npm test -- prismSkinEngine
                      </span>
                      <span className="text-emerald-400">PASS</span>
                    </div>
                  )}
                </div>

                {/* 底部悬浮指令输入舱（Composer · 含活体伴读点击跳跃与 512K 液态上下文试管） */}
                <div
                  className="relative flex items-center justify-between px-3 py-2 text-[11px] shadow-lg transition-all"
                  onMouseMove={(e) => {
                    if (!rimGlow) return;
                    const rect = e.currentTarget.getBoundingClientRect();
                    setSimRim({
                      target: 'composer',
                      x: Math.round(e.clientX - rect.left),
                      y: Math.round(e.clientY - rect.top),
                    });
                  }}
                  onMouseLeave={() => setSimRim(null)}
                  style={{
                    backgroundColor: colors.input || '#131a27',
                    backgroundImage:
                      rimGlow && simRim?.target === 'composer'
                        ? `radial-gradient(180px circle at ${simRim.x}px ${simRim.y}px, ${accent}28 0%, transparent 72%)`
                        : undefined,
                    borderRadius: `${borderRadius}px`,
                    border: `1px solid ${
                      rimGlow && simRim?.target === 'composer' ? accent : `${accent}55`
                    }`,
                    boxShadow:
                      prismFacets && motionPreset !== 'silent'
                        ? `0 0 0 1px ${accent}22, 0 8px 22px -6px ${accent}33`
                        : undefined,
                    color: colors.muted || '#7e8ca6',
                  }}
                >
                  {/* 活体伴读角色挂件（可点击 Q 弹跳跃并喷发星芒粒子） */}
                  {liveCharm && motifs?.composerCharmUri && (
                    <button
                      type="button"
                      onClick={(ev) => {
                        ev.stopPropagation();
                        setCharmHop(true);
                        setCharmSparkKey((k) => k + 1);
                        setTimeout(() => setCharmHop(false), 520);
                      }}
                      title="点击戳戳伴读团子 ✨"
                      className={`absolute -top-[18px] right-4 z-30 h-6 w-14 flex items-end justify-end transition-transform duration-300 ${
                        charmHop ? '-translate-y-2.5 scale-110' : 'hover:-translate-y-0.5'
                      }`}
                    >
                      <img
                        src={motifs.composerCharmUri}
                        alt=""
                        className="h-full w-auto object-contain drop-shadow"
                      />
                      {charmSparkKey > 0 && charmHop && (
                        <span
                          key={charmSparkKey}
                          className="pointer-events-none absolute -top-2 right-3 text-[10px] animate-ping"
                          style={{ color: accent }}
                        >
                          ✦ ✧ ✦
                        </span>
                      )}
                    </button>
                  )}

                  <span className="truncate">向 Antigravity 智能体下达指令…</span>

                  <div className="flex items-center gap-1.5 shrink-0">
                    {/* 512K 液态上下文试管指示器 */}
                    {contextVial && (
                      <div
                        className="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[9px] font-mono"
                        style={{
                          backgroundColor: `${panel}cc`,
                          border: `1px solid ${border}`,
                          color: fg,
                        }}
                        title="512K 液态上下文实时监控"
                      >
                        <svg viewBox="0 0 12 16" width="10" height="14" aria-hidden="true">
                          <rect
                            x="1"
                            y="1"
                            width="10"
                            height="14"
                            rx="3"
                            fill="none"
                            stroke={accent}
                            strokeOpacity="0.6"
                            strokeWidth="1"
                          />
                          <path
                            d="M1.5 7 Q 4 5.5 6.5 7 T 10.5 7 V 14.5 H 1.5 Z"
                            fill={accent}
                            opacity="0.88"
                          />
                        </svg>
                        <span>142K</span>
                      </div>
                    )}

                    <span
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-[10px] font-semibold shadow-sm"
                      style={{
                        backgroundColor: accent,
                        color: colors.accentForeground || '#04131e',
                        borderRadius: `${Math.max(6, borderRadius - 4)}px`,
                      }}
                    >
                      <Send className="h-2.5 w-2.5" />
                      发送
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
