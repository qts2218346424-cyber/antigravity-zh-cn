import React, { useEffect, useState } from 'react';
import { Code, Cpu, Palette, RotateCcw, Save, Sliders, Sparkles, Type } from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
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
      { key: 'background', label: '主画布背景' },
      { key: 'foreground', label: '主前景色' },
      { key: 'muted', label: '次级弱化文字' },
    ],
  },
  {
    title: '空间骨架',
    items: [
      { key: 'titleBar', label: '顶栏标题栏' },
      { key: 'activityBar', label: '最左活动栏' },
      { key: 'sidebar', label: '侧边资源栏' },
      { key: 'panel', label: '悬浮面板底色' },
      { key: 'statusBar', label: '底部状态条' },
    ],
  },
  {
    title: '信号交互',
    items: [
      { key: 'accent', label: '品牌主强调色' },
      { key: 'accentForeground', label: '强调色文字' },
      { key: 'border', label: '极细分割线' },
      { key: 'selection', label: '选中光晕区' },
      { key: 'input', label: '输入框槽位' },
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

  const [customCss, setCustomCss] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!selectedSkinId && skins.length > 0) {
      onSelectSkinId(skins[0].id);
      return;
    }
    if (!selectedSkinId) return;

    studioService
      .getSkinManifest(selectedSkinId)
      .then((m) => {
        setManifest(m);
        const cMap: Record<string, string> = {};
        for (const k of ALL_COLOR_KEYS) {
          cMap[k] = (m.colors?.[k] as string) || '#0f172a';
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

        const firstBg = Array.isArray(m.background) ? m.background[0] : m.background;
        setBgOpacity(firstBg?.opacity ?? 0.14);
        setBgBlur(firstBg?.blur ?? 2);
      })
      .catch((err) => showToast(`加载材质包清单失败: ${String(err)}`, 'error'));
  }, [selectedSkinId, skins, onSelectSkinId]);

  const handleSave = async () => {
    if (scope === 'skin' && !selectedSkinId) {
      showToast('请先选择需要微调的材质包', 'warning');
      return;
    }
    setSaving(true);
    try {
      const patch: Record<string, unknown> = {
        colors,
        surfaces: {
          radius: `${borderRadius}px`,
          glass_blur: glassBlur,
          card_opacity: Number(cardOpacity.toFixed(2)),
          border_glow: `rgba(255, 255, 255, ${borderGlowAlpha.toFixed(2)})`,
          noise_grain: Number(noiseGrain.toFixed(3)),
          shadow_elevation: '0 20px 50px -12px rgba(0, 0, 0, 0.72)',
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
      showToast(
        scope === 'global'
          ? '已保存全局光学覆盖层并重新编译当前主题'
          : `已保存「${selectedSkinId}」高定微调并实时应用`,
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
        setManifest(refreshed);
      }
    } catch (err: unknown) {
      showToast(`重置失败: ${String(err)}`, 'error');
    }
  };

  const accent = colors.accent || '#38bdf8';
  const bg = colors.background || '#080a0f';
  const fg = colors.foreground || '#e6edf7';
  const panel = colors.panel || '#0f141f';
  const border = colors.border || '#1f293b';

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
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
            <button
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
            色彩基因谱系 (Color DNA)
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
                <span>浮层透光不透明度</span>
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
                <span>面板倒角曲率</span>
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
                <span>壁纸曝光透明度</span>
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
              <label className="block text-[11px] text-gray-500 mb-1">UI 字体族</label>
              <input
                type="text"
                value={fontFamily}
                onChange={(e) => setFontFamily(e.target.value)}
                className="w-full rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-black/30 px-3 py-1.5 text-xs font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] text-gray-500 mb-1">等宽代码字体</label>
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
              自定义附加样式表（安全沙盒编译，自动过滤危险脚本）
            </div>
            <textarea
              rows={4}
              value={customCss}
              onChange={(e) => setCustomCss(e.target.value)}
              placeholder="/* 可直接书写 Monaco / Workbench / Agent UI 微调规则 */"
              className="w-full rounded-xl border border-gray-200 dark:border-white/10 bg-slate-950 p-3 text-xs font-mono text-emerald-300 focus:outline-none focus:ring-2 focus:ring-sky-500/40"
            />
          </div>
        </div>
      </div>

      {/* 右侧 1:1 真实感 Antigravity 光学视窗模拟器 */}
      <div className="xl:col-span-5">
        <div className="sticky top-6 rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-xs font-bold text-gray-800 dark:text-white">
            <span className="inline-flex items-center gap-1.5">
              <Sparkles className="h-4 w-4 text-sky-500" />
              光学物理视窗模拟器 (Live Viewport)
            </span>
            <span className="text-[11px] font-mono text-gray-400">
              blur({glassBlur}px) · {Math.round(cardOpacity * 100)}%
            </span>
          </div>

          {/* 模拟壁纸底层光斑环境，用于凸显真实亚克力折射与透光效果 */}
          <div
            className="relative h-[520px] w-full overflow-hidden rounded-2xl border shadow-2xl flex flex-col select-none"
            style={{
              backgroundColor: bg,
              color: fg,
              borderColor: border,
              fontFamily,
              fontSize: `${fontSize}px`,
              backgroundImage: `radial-gradient(circle at 18% 22%, ${accent}38 0%, transparent 45%), radial-gradient(circle at 85% 75%, ${colors.statusBar || accent}44 0%, transparent 50%)`,
            }}
          >
            {/* 微粒噪点遮罩 */}
            {noiseGrain > 0 && (
              <div
                className="pointer-events-none absolute inset-0"
                style={{
                  opacity: noiseGrain,
                  backgroundImage:
                    'radial-gradient(rgba(255,255,255,0.6) 0.5px, transparent 0.5px)',
                  backgroundSize: '3px 3px',
                }}
              />
            )}

            {/* 模拟标题栏 */}
            <div
              className="relative z-10 flex items-center justify-between px-3.5 py-2.5 text-[11px] border-b"
              style={{
                backgroundColor: colors.titleBar || '#07090e',
                borderColor: border,
              }}
            >
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-rose-400/90" />
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-400/90" />
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/90" />
                </div>
                <span className="font-semibold tracking-tight opacity-90">
                  Antigravity Studio
                </span>
              </div>
              <div
                className="px-3 py-0.5 rounded-md text-[10px] opacity-80"
                style={{
                  backgroundColor: colors.input || '#131a27',
                  border: `1px solid ${border}`,
                }}
              >
                ⌘K 调度全局智能体与命令…
              </div>
            </div>

            {/* 工作台主区 */}
            <div className="relative z-10 flex flex-1 min-h-0">
              {/* 活动栏 */}
              <div
                className="w-11 flex flex-col items-center gap-3.5 py-3.5 border-r"
                style={{
                  backgroundColor: colors.activityBar || '#06080c',
                  borderColor: border,
                }}
              >
                <div
                  className="h-6 w-6 rounded-lg flex items-center justify-center shadow"
                  style={{ backgroundColor: accent, color: colors.accentForeground || '#04131e' }}
                >
                  <Cpu className="h-3.5 w-3.5" />
                </div>
                <div className="h-5 w-5 rounded bg-current opacity-20" />
                <div className="h-5 w-5 rounded bg-current opacity-20" />
              </div>

              {/* 侧边栏 */}
              <div
                className="w-36 p-3 border-r space-y-1.5 text-[11px]"
                style={{
                  backgroundColor: colors.sidebar || '#0c1018',
                  borderColor: border,
                }}
              >
                <div className="text-[10px] font-semibold uppercase tracking-wider opacity-50 mb-2">
                  工程目录
                </div>
                <div
                  className="px-2 py-1.5 font-medium truncate"
                  style={{
                    backgroundColor: colors.selection || `${accent}30`,
                    borderRadius: `${Math.min(borderRadius, 10)}px`,
                    borderLeft: `2px solid ${accent}`,
                  }}
                >
                  skin_manager.rs
                </div>
                <div className="px-2 py-1 opacity-65">l10n.rs</div>
                <div className="px-2 py-1 opacity-65">PetWindowView.tsx</div>
                <div className="px-2 py-1 opacity-45">update_checker.rs</div>
              </div>

              {/* 交互思考与毛玻璃悬浮卡片展示区 */}
              <div className="flex-1 flex flex-col min-w-0 p-3.5 justify-between gap-3 overflow-hidden">
                <div className="space-y-3">
                  {/* 真实玻璃态思考过程卡 */}
                  <div
                    className="p-3 space-y-1.5 transition-all"
                    style={{
                      backgroundColor: panel,
                      opacity: cardOpacity,
                      borderRadius: `${borderRadius}px`,
                      border: `1px solid ${border}`,
                      backdropFilter: `blur(${glassBlur}px) saturate(1.4)`,
                      boxShadow: `inset 0 1px 0 rgba(255,255,255,${borderGlowAlpha}), 0 14px 32px rgba(0,0,0,0.45)`,
                    }}
                  >
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="font-semibold flex items-center gap-1" style={{ color: accent }}>
                        <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ backgroundColor: accent }} />
                        Thinking Process · 深度思考中
                      </span>
                      <span style={{ color: colors.muted || '#7e8ca6' }}>Claude 3.7</span>
                    </div>
                    <p className="text-[11px] leading-relaxed opacity-90">
                      已完成高定光学折射阴影变量编译，正在校准 Antigravity IDE <code className="font-mono">product.json</code> 校验和…
                    </p>
                  </div>

                  {/* 代码着色卡片 */}
                  <div
                    className="p-3 text-[11px] leading-relaxed"
                    style={{
                      backgroundColor: colors.input || '#131a27',
                      fontFamily: monoFamily,
                      borderRadius: `${Math.max(4, borderRadius - 2)}px`,
                      border: `1px solid ${border}`,
                      boxShadow: `inset 0 1px 0 rgba(255,255,255,${borderGlowAlpha * 0.6})`,
                    }}
                  >
                    <div>
                      <span style={{ color: accent }}>pub async fn</span>{' '}
                      <span className="font-semibold">compile_optical_skin</span>() {'{'}
                    </div>
                    <div className="pl-3 opacity-85">
                      blur: <span style={{ color: accent }}>{glassBlur}px</span>, opacity:{' '}
                      <span style={{ color: accent }}>{cardOpacity.toFixed(2)}</span>
                    </div>
                    <div>{'}'}</div>
                  </div>
                </div>

                {/* 输入交互栏 */}
                <div
                  className="flex items-center justify-between px-3 py-2 text-[11px]"
                  style={{
                    backgroundColor: colors.input || '#131a27',
                    borderRadius: `${borderRadius}px`,
                    border: `1px solid ${border}`,
                    color: colors.muted || '#7e8ca6',
                  }}
                >
                  <span>向工作台下达全中文指令…</span>
                  <span
                    className="px-2.5 py-0.5 text-[10px] font-semibold"
                    style={{
                      backgroundColor: accent,
                      color: colors.accentForeground || '#04131e',
                      borderRadius: `${Math.max(4, borderRadius - 4)}px`,
                    }}
                  >
                    发送
                  </span>
                </div>
              </div>
            </div>

            {/* 底部状态指示条 */}
            <div
              className="relative z-10 flex items-center justify-between px-3.5 py-1.5 text-[10px] font-medium"
              style={{
                backgroundColor: colors.statusBar || '#0e1726',
                color: fg,
                borderTop: `1px solid ${border}`,
              }}
            >
              <span className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                OTA 在线更新通道正常 · 中文核已就绪
              </span>
              <span className="font-mono opacity-75">{manifest?.id || selectedSkinId}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
