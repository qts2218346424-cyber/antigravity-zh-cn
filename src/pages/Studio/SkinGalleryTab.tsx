import React, { useMemo, useState } from 'react';
import { open, save } from '@tauri-apps/plugin-dialog';
import {
  Check,
  Copy,
  Download,
  FolderOpen,
  Layers,
  PowerOff,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  Upload,
} from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
import { studioService } from '../../services/studioService';
import type { SkinInfo, StudioStatus } from '../../types/studio';
import { isTauri } from '../../utils/env';

interface SkinGalleryTabProps {
  skins: SkinInfo[];
  status: StudioStatus;
  onRefresh: () => Promise<void>;
  onSelectForCustomize: (skinId: string) => void;
}

type FilterMode = 'all' | 'dark' | 'light' | 'custom';

/** 微缩真实 IDE 光学结构预览组件：直观体现配色阶梯、强调光束与面板材质 */
const MiniWorkbenchPreview: React.FC<{ skin: SkinInfo }> = ({ skin }) => {
  const c = skin.colors;
  const bg = c.background || '#0b0e14';
  const sidebar = c.sidebar || '#101521';
  const activity = c.activityBar || '#07090d';
  const titleBar = c.titleBar || activity;
  const statusBar = c.statusBar || c.accent || '#38bdf8';
  const panel = c.panel || sidebar;
  const border = c.border || 'rgba(255,255,255,0.1)';
  const fg = c.foreground || '#e2e8f0';
  const muted = c.muted || '#64748b';
  const accent = c.accent || '#38bdf8';
  const selection = c.selection || `${accent}33`;

  return (
    <div
      className="relative h-44 w-full overflow-hidden select-none p-3 flex items-center justify-center"
      style={{
        background: `radial-gradient(circle at 20% 20%, ${accent}26, transparent 55%), radial-gradient(circle at 85% 80%, ${statusBar}30, transparent 60%), ${bg}`,
      }}
    >
      {/* 可选底层纹理图叠加 */}
      {skin.preview_data_uri && (
        <img
          src={skin.preview_data_uri}
          alt=""
          className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-20 mix-blend-luminosity transition-transform duration-700 group-hover:scale-105"
        />
      )}

      {/* 微缩桌面 IDE 主窗体（真实比例光学渲染） */}
      <div
        className="relative z-10 w-full h-full rounded-xl overflow-hidden flex flex-col transition-transform duration-500 group-hover:-translate-y-0.5"
        style={{
          backgroundColor: bg,
          border: `1px solid ${border}`,
          boxShadow: `0 18px 36px -12px rgba(0,0,0,0.65), inset 0 1px 0 rgba(255,255,255,0.12)`,
        }}
      >
        {/* 顶栏 */}
        <div
          className="h-5 px-2.5 flex items-center justify-between border-b"
          style={{ backgroundColor: titleBar, borderColor: border }}
        >
          <div className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-400/80" />
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400/80" />
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400/80" />
          </div>
          <div
            className="h-2.5 w-24 rounded-sm opacity-80"
            style={{ backgroundColor: c.input || panel, border: `1px solid ${border}` }}
          />
          <div className="h-1.5 w-4 rounded-full opacity-40" style={{ backgroundColor: fg }} />
        </div>

        {/* 主体容器 */}
        <div className="flex flex-1 min-h-0">
          {/* 活动栏 */}
          <div
            className="w-5 py-2 flex flex-col items-center gap-1.5 border-r"
            style={{ backgroundColor: activity, borderColor: border }}
          >
            <div
              className="w-2.5 h-2.5 rounded-sm relative"
              style={{ backgroundColor: accent }}
            />
            <div className="w-2.5 h-2.5 rounded-sm opacity-25" style={{ backgroundColor: fg }} />
            <div className="w-2.5 h-2.5 rounded-sm opacity-25" style={{ backgroundColor: fg }} />
          </div>

          {/* 侧边文件树 */}
          <div
            className="w-20 p-1.5 space-y-1 border-r"
            style={{ backgroundColor: sidebar, borderColor: border }}
          >
            <div className="h-1.5 w-10 rounded-full opacity-35" style={{ backgroundColor: muted }} />
            <div
              className="h-3 w-full rounded px-1 flex items-center"
              style={{ backgroundColor: selection, borderLeft: `2px solid ${accent}` }}
            >
              <div className="h-1 w-10 rounded-full" style={{ backgroundColor: fg }} />
            </div>
            <div className="h-1.5 w-12 rounded-full opacity-30 ml-1" style={{ backgroundColor: fg }} />
            <div className="h-1.5 w-9 rounded-full opacity-25 ml-1" style={{ backgroundColor: fg }} />
          </div>

          {/* 编辑器与 AI 对话卡片区 */}
          <div className="flex-1 p-2 flex flex-col justify-between min-w-0">
            <div className="space-y-1.5">
              {/* 代码高亮片段 */}
              <div className="flex items-center gap-1">
                <span className="h-1.5 w-5 rounded-full" style={{ backgroundColor: accent }} />
                <span className="h-1.5 w-12 rounded-full opacity-75" style={{ backgroundColor: fg }} />
                <span className="h-1.5 w-6 rounded-full opacity-40" style={{ backgroundColor: muted }} />
              </div>
              <div className="flex items-center gap-1 pl-2.5">
                <span className="h-1.5 w-8 rounded-full opacity-60" style={{ backgroundColor: fg }} />
                <span className="h-1.5 w-10 rounded-full" style={{ backgroundColor: accent, opacity: 0.75 }} />
              </div>
              {/* 悬浮毛玻璃卡片 */}
              <div
                className="mt-1.5 rounded-md p-1.5 space-y-1"
                style={{
                  backgroundColor: panel,
                  border: `1px solid ${border}`,
                  boxShadow: '0 6px 14px rgba(0,0,0,0.22)',
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="h-1.5 w-11 rounded-full" style={{ backgroundColor: accent }} />
                  <span className="h-1.5 w-4 rounded-full opacity-40" style={{ backgroundColor: muted }} />
                </div>
                <div className="h-1.5 w-4/5 rounded-full opacity-60" style={{ backgroundColor: fg }} />
              </div>
            </div>
          </div>
        </div>

        {/* 底部状态条 */}
        <div
          className="h-3.5 px-2 flex items-center justify-between"
          style={{ backgroundColor: statusBar }}
        >
          <span className="h-1 w-8 rounded-full opacity-80 bg-white" />
          <span className="h-1 w-5 rounded-full opacity-65 bg-white" />
        </div>
      </div>
    </div>
  );
};

export const SkinGalleryTab: React.FC<SkinGalleryTabProps> = ({
  skins,
  status,
  onRefresh,
  onSelectForCustomize,
}) => {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [filterMode, setFilterMode] = useState<FilterMode>('all');
  const [dupSource, setDupSource] = useState<SkinInfo | null>(null);
  const [dupNewId, setDupNewId] = useState('');
  const [dupNewName, setDupNewName] = useState('');
  const [overwriteImport, setOverwriteImport] = useState(true);

  const filteredSkins = useMemo(() => {
    return skins.filter((s) => {
      if (filterMode === 'dark') return s.base !== 'light';
      if (filterMode === 'light') return s.base === 'light';
      if (filterMode === 'custom') return !s.builtin;
      return true;
    });
  }, [skins, filterMode]);

  const handleActivate = async (skinId: string) => {
    setBusyId(skinId);
    try {
      await studioService.activateSkin(skinId);
      showToast(`已激活光学材质「${skinId}」，工作台已实时编译同步`, 'success');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`启用失败: ${String(err)}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  const handleDisable = async () => {
    setBusyId('__disable__');
    try {
      await studioService.disableSkin();
      showToast('已恢复默认外观并卸下材质包', 'info');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`停用失败: ${String(err)}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  const handleImportZip = async () => {
    if (!isTauri()) {
      showToast('请在桌面端中使用 .zip 材质包导入功能', 'warning');
      return;
    }
    try {
      const selected = await open({
        multiple: false,
        title: '选择材质包 (.zip)',
        filters: [{ name: '材质包归档', extensions: ['zip'] }],
      });
      if (!selected || Array.isArray(selected)) return;
      setBusyId('__import__');
      const info = await studioService.importSkinZip(selected, overwriteImport);
      showToast(`已校验并导入材质包「${info.name}」`, 'success');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`导入失败: ${String(err)}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  const handleExportZip = async (skin: SkinInfo) => {
    if (!isTauri()) {
      showToast('请在桌面端中使用导出功能', 'warning');
      return;
    }
    try {
      const outPath = await save({
        title: '导出材质包 (.zip)',
        defaultPath: `${skin.id}.zip`,
        filters: [{ name: '材质包归档', extensions: ['zip'] }],
      });
      if (!outPath) return;
      setBusyId(skin.id);
      const saved = await studioService.exportSkinZip(skin.id, outPath, true);
      showToast(`已打包导出至 ${saved}`, 'success');
    } catch (err: unknown) {
      showToast(`导出失败: ${String(err)}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  const handleConfirmDuplicate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dupSource) return;
    try {
      setBusyId(dupSource.id);
      const created = await studioService.duplicateSkin(
        dupSource.id,
        dupNewId.trim(),
        dupNewName.trim(),
      );
      showToast(`已派生专属材质包「${created.name}」`, 'success');
      setDupSource(null);
      await onRefresh();
    } catch (err: unknown) {
      showToast(`复制失败: ${String(err)}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async (skin: SkinInfo) => {
    try {
      setBusyId(skin.id);
      await studioService.deleteSkin(skin.id);
      showToast(`已移除自定义材质包「${skin.name}」`, 'info');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`删除失败: ${String(err)}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  const handleInjectIde = async (skinId?: string) => {
    setBusyId('__ide__');
    try {
      const msg = await studioService.injectIde(skinId || status.active_skin, status.ide_root);
      showToast(msg, 'success');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`IDE 注入失败: ${String(err)}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  const handleRemoveIde = async () => {
    setBusyId('__ide__');
    try {
      const msg = await studioService.removeIde(status.ide_root);
      showToast(msg, 'info');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`移除 IDE 样式失败: ${String(err)}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* 高定玻璃质感控制栏 */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          {/* 分类胶囊 */}
          <div className="inline-flex rounded-xl bg-gray-100/90 dark:bg-white/5 p-1 text-xs border border-gray-200/50 dark:border-white/5">
            {(
              [
                ['all', '全部主题'],
                ['dark', '深邃暗调'],
                ['light', '浅色护眼'],
                ['custom', '我的派生'],
              ] as Array<[FilterMode, string]>
            ).map(([k, label]) => (
              <button
                key={k}
                onClick={() => setFilterMode(k)}
                className={`rounded-lg px-3 py-1.5 font-medium transition-all ${
                  filterMode === k
                    ? 'bg-white dark:bg-slate-800 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <button
            onClick={handleImportZip}
            disabled={busyId === '__import__'}
            className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 dark:bg-sky-500 px-3.5 py-2 text-xs font-semibold text-white dark:text-slate-950 hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            <Upload className="h-3.5 w-3.5" />
            导入 .zip
          </button>

          <label className="inline-flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 cursor-pointer ml-1">
            <input
              type="checkbox"
              checked={overwriteImport}
              onChange={(e) => setOverwriteImport(e.target.checked)}
              className="rounded border-gray-300 dark:border-gray-600 text-sky-500"
            />
            允许覆盖
          </label>

          {status.skin_enabled && (
            <button
              onClick={handleDisable}
              disabled={busyId === '__disable__'}
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-white/10 px-3 py-2 text-xs font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5"
            >
              <PowerOff className="h-3.5 w-3.5 text-amber-500" />
              还原原版样式
            </button>
          )}
        </div>

        {/* Antigravity IDE 样式同步舱 */}
        <div className="flex flex-wrap items-center gap-2.5 rounded-xl bg-gray-50/90 dark:bg-black/30 px-3.5 py-2 border border-gray-200/80 dark:border-white/10">
          <Layers className="h-4 w-4 text-sky-500" />
          <div className="text-xs text-gray-600 dark:text-gray-300">
            IDE 核心联动：
            <span
              className={`font-semibold ml-1 ${
                status.ide_status === 'injected'
                  ? 'text-emerald-500'
                  : status.ide_status === 'stale'
                    ? 'text-amber-500'
                    : 'text-gray-400'
              }`}
            >
              {status.ide_status === 'injected'
                ? 'SHA-256 校验已同步'
                : status.ide_status === 'stale'
                  ? '样式过期待重新注入'
                  : status.ide_status === 'clean'
                    ? '未注入'
                    : '未定位到 IDE'}
            </span>
          </div>
          <button
            onClick={() => handleInjectIde()}
            disabled={busyId === '__ide__' || status.ide_status === 'not_found'}
            className="rounded-lg bg-gradient-to-r from-sky-500 to-indigo-500 px-3 py-1 text-xs font-semibold text-white shadow-sm hover:opacity-90 disabled:opacity-40"
          >
            同步至 Antigravity IDE
          </button>
          {status.ide_enabled && (
            <button
              onClick={handleRemoveIde}
              disabled={busyId === '__ide__'}
              className="rounded-lg border border-gray-300 dark:border-white/15 px-2.5 py-1 text-xs text-gray-500 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-white/10"
            >
              剥离
            </button>
          )}
        </div>
      </div>

      {/* 派生确认条 */}
      {dupSource && (
        <form
          onSubmit={handleConfirmDuplicate}
          className="rounded-2xl border border-sky-300/60 dark:border-sky-500/30 bg-sky-50/70 dark:bg-sky-950/25 backdrop-blur-md p-4 flex flex-wrap items-end gap-3"
        >
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              基于「{dupSource.name}」派生新 ID（小写字母/数字/-）
            </label>
            <input
              type="text"
              required
              value={dupNewId}
              onChange={(e) => setDupNewId(e.target.value)}
              className="w-full rounded-xl border border-gray-300 dark:border-white/15 bg-white dark:bg-slate-900 px-3 py-2 text-xs font-mono"
            />
          </div>
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              自定义主题名称
            </label>
            <input
              type="text"
              required
              value={dupNewName}
              onChange={(e) => setDupNewName(e.target.value)}
              className="w-full rounded-xl border border-gray-300 dark:border-white/15 bg-white dark:bg-slate-900 px-3 py-2 text-xs"
            />
          </div>
          <button
            type="submit"
            className="rounded-xl bg-sky-500 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-600"
          >
            创建派生包
          </button>
          <button
            type="button"
            onClick={() => setDupSource(null)}
            className="rounded-xl border border-gray-300 dark:border-white/15 px-3 py-2 text-xs"
          >
            取消
          </button>
        </form>
      )}

      {/* 高定材质包卡片陈列网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSkins.map((skin) => {
          const isBusy = busyId === skin.id;
          const swatchColors = [
            skin.colors.background,
            skin.colors.sidebar,
            skin.colors.panel,
            skin.colors.accent,
            skin.colors.statusBar,
          ].filter(Boolean) as string[];

          return (
            <div
              key={skin.id}
              className={`group relative flex flex-col justify-between rounded-2xl border transition-all duration-300 overflow-hidden bg-white dark:bg-slate-900/75 backdrop-blur-xl ${
                skin.active
                  ? 'border-sky-500 ring-2 ring-sky-500/25 shadow-[0_20px_44px_-12px_rgba(56,189,248,0.28)]'
                  : 'border-gray-200/80 dark:border-white/10 shadow-sm hover:shadow-xl hover:border-gray-300 dark:hover:border-white/20'
              }`}
            >
              <div>
                {/* 微缩真实工作台渲染区 */}
                <div className="relative">
                  <MiniWorkbenchPreview skin={skin} />

                  {/* 左上标签 */}
                  <div className="absolute top-3 left-3 z-20 flex items-center gap-1.5">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold tracking-wide backdrop-blur-md border ${
                        skin.builtin
                          ? 'bg-black/60 text-slate-200 border-white/15'
                          : 'bg-indigo-600/85 text-white border-indigo-400/40'
                      }`}
                    >
                      {skin.builtin ? '高定内置' : '自定义包'}
                    </span>
                  </div>

                  {/* 右上激活徽章 */}
                  {skin.active && (
                    <div className="absolute top-3 right-3 z-20 inline-flex items-center gap-1 rounded-full bg-emerald-500/95 px-2.5 py-0.5 text-[10px] font-bold text-white shadow-lg backdrop-blur">
                      <Check className="h-3 w-3" />
                      LIVE 生效中
                    </div>
                  )}
                </div>

                {/* 信息与色彩 DNA */}
                <div className="p-4 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="text-sm font-bold text-gray-900 dark:text-white truncate flex items-center gap-1.5">
                        {skin.name}
                      </h3>
                      <p className="text-[11px] font-mono text-gray-400 mt-0.5 truncate">
                        {skin.id} · v{skin.version} · {skin.author}
                      </p>
                    </div>
                    <span className="shrink-0 rounded-md bg-gray-100 dark:bg-white/5 px-2 py-0.5 text-[10px] font-medium text-gray-500 dark:text-gray-400 border border-gray-200/60 dark:border-white/10">
                      {skin.base === 'light' ? 'Light' : 'Dark'}
                    </span>
                  </div>

                  <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 min-h-[34px] leading-relaxed">
                    {skin.description || '光学渐变与高对比工作台材质方案'}
                  </p>

                  {/* Color DNA 色谱条 */}
                  <div className="flex items-center gap-1.5 pt-1">
                    <span className="text-[10px] text-gray-400 mr-1">DNA</span>
                    {swatchColors.map((hex, i) => (
                      <div
                        key={`${skin.id}-dna-${i}`}
                        title={hex}
                        className="h-3.5 flex-1 rounded-full border border-black/10 dark:border-white/15 shadow-inner transition-transform hover:scale-y-125"
                        style={{ backgroundColor: hex }}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* 底部极简操控栏 */}
              <div className="flex items-center justify-between gap-2 border-t border-gray-100 dark:border-white/10 bg-gray-50/70 dark:bg-black/25 px-4 py-2.5">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleActivate(skin.id)}
                    disabled={isBusy}
                    className={`rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all ${
                      skin.active
                        ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25'
                        : 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:opacity-90'
                    }`}
                  >
                    {isBusy ? '编译中...' : skin.active ? '重新编译' : '立即应用'}
                  </button>
                  <button
                    onClick={() => onSelectForCustomize(skin.id)}
                    className="inline-flex items-center gap-1 rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 px-2.5 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/10"
                  >
                    <SlidersHorizontal className="h-3.5 w-3.5 text-sky-500" />
                    光学精调
                  </button>
                </div>

                <div className="flex items-center gap-0.5">
                  <button
                    onClick={() => {
                      setDupSource(skin);
                      setDupNewId(`${skin.id}-studio`);
                      setDupNewName(`${skin.name} · 精调版`);
                    }}
                    className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-200/70 dark:hover:bg-white/10 hover:text-gray-800 dark:hover:text-white transition-colors"
                    title="复制并派生新材质"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => handleExportZip(skin)}
                    className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-200/70 dark:hover:bg-white/10 hover:text-gray-800 dark:hover:text-white transition-colors"
                    title="打包导出 .zip"
                  >
                    <Download className="h-3.5 w-3.5" />
                  </button>
                  {!skin.builtin && (
                    <button
                      onClick={() => handleDelete(skin)}
                      className="p-1.5 rounded-lg text-rose-400 hover:bg-rose-500/15 hover:text-rose-500 transition-colors"
                      title="删除自定义包"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {filteredSkins.length === 0 && (
          <div className="col-span-full rounded-2xl border border-dashed border-gray-300 dark:border-white/15 py-14 text-center text-xs text-gray-400 space-y-2">
            <Sparkles className="h-6 w-6 mx-auto opacity-40" />
            <div>当前筛选下暂无材质包，可点击「复制并派生」或「导入 .zip」创建你的专属皮肤</div>
          </div>
        )}
      </div>

      {/* 本地皮肤存储目录 */}
      <div className="flex items-center gap-2 text-[11px] text-gray-400 font-mono">
        <FolderOpen className="h-3.5 w-3.5" />
        <span>本地皮肤工作目录：{status.config_dir}</span>
      </div>
    </div>
  );
};
