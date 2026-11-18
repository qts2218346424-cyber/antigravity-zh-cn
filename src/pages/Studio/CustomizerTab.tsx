import React, { useEffect, useState } from 'react';
import {
  Code,
  MessageSquarePlus,
  Palette,
  RotateCcw,
  Save,
  Send,
  Sliders,
  Sparkles,
  Type,
} from 'lucide-react';
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
          <div className="flex items-center justify-between text-xs font-bold text-gray-800 dark:text-white">
            <span className="inline-flex items-center gap-1.5">
              <Sparkles className="h-4 w-4 text-sky-500" />
              Antigravity 应用实时视窗预览
            </span>
            <span className="text-[11px] font-mono text-gray-400">
              blur({glassBlur}px) · {Math.round(cardOpacity * 100)}%
            </span>
          </div>

          <div
            className="relative h-[520px] w-full overflow-hidden rounded-2xl border shadow-2xl flex flex-col select-none"
            style={{
              backgroundColor: bg,
              color: fg,
              borderColor: border,
              fontFamily,
              fontSize: `${fontSize}px`,
              backgroundImage: `radial-gradient(76% 42% at 50% 0%, ${accent}22 0%, transparent 72%), radial-gradient(circle at 86% 84%, ${accent}18 0%, transparent 56%)`,
            }}
          >

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
              <div className="flex-1 flex flex-col min-w-0 p-3.5 justify-between gap-3 overflow-hidden">
                <div className="space-y-3">
                  {/* 用户消息胶囊 */}
                  <div className="flex justify-end">
                    <div
                      className="px-3 py-1.5 text-[11px] max-w-[85%]"
                      style={{
                        backgroundColor: colors.selection || `${accent}28`,
                        borderRadius: `${borderRadius}px`,
                        border: `1px solid ${border}`,
                      }}
                    >
                      将这些皮肤全面适配到 Antigravity 桌面应用
                    </div>
                  </div>

                  {/* 玻璃态深度思考折叠卡（仅背景应用通透度，保持文字 100% 锐利清晰） */}
                  <div
                    className="p-3 space-y-1.5 transition-all"
                    style={{
                      backgroundColor: `color-mix(in srgb, ${panel} ${Math.round(cardOpacity * 100)}%, transparent)`,
                      borderRadius: `${borderRadius}px`,
                      border: `1px solid ${border}`,
                      backdropFilter: `blur(${glassBlur}px) saturate(1.35)`,
                      boxShadow: `inset 0 1px 0 rgba(255,255,255,${borderGlowAlpha}), 0 14px 32px rgba(0,0,0,0.32)`,
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
                        深度思考过程 · 已折叠推演流
                      </span>
                      <span style={{ color: colors.muted || '#7e8ca6' }}>实时热重载</span>
                    </div>
                    <p className="text-[11px] leading-relaxed opacity-90">
                      已完成 Antigravity 应用原生宿主令牌（<code className="font-mono">--background</code> / <code className="font-mono">--card</code> / <code className="font-mono">--primary</code>）与三层幕布色彩同步。
                    </p>
                  </div>

                  {/* 工件代码片段预览卡 */}
                  <div
                    className="p-3 text-[11px] leading-relaxed"
                    style={{
                      backgroundColor: colors.input || '#131a27',
                      fontFamily: monoFamily,
                      borderRadius: `${Math.max(6, borderRadius - 2)}px`,
                      border: `1px solid ${border}`,
                      boxShadow: `inset 0 1px 0 rgba(255,255,255,${borderGlowAlpha * 0.6})`,
                    }}
                  >
                    <div>
                      <span style={{ color: accent }}>setHubCurtainColor</span>(win,{' '}
                      <span style={{ color: accent }}>&quot;{bg}&quot;</span>);
                    </div>
                    <div className="pl-3 opacity-85">
                      glassBlur: <span style={{ color: accent }}>{glassBlur}px</span>, cardOpacity:{' '}
                      <span style={{ color: accent }}>{cardOpacity.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                {/* 底部悬浮指令输入舱（Composer） */}
                <div
                  className="flex items-center justify-between px-3 py-2.5 text-[11px] shadow-lg"
                  style={{
                    backgroundColor: colors.input || '#131a27',
                    borderRadius: `${borderRadius}px`,
                    border: `1px solid ${border}`,
                    color: colors.muted || '#7e8ca6',
                  }}
                >
                  <span>向 Antigravity 智能体下达指令…</span>
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
  );
};
