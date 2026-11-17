import React, { useMemo, useState } from 'react';
import { open, save } from '@tauri-apps/plugin-dialog';
import {
  Check,
  Copy,
  Download,
  FolderOpen,
  MonitorSmartphone,
  PowerOff,
  Send,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  Upload,
  Wand2,
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
  onNavigateL10n?: () => void;
}

type FilterMode = 'all' | 'clannad' | 'dark' | 'light' | 'custom';

/** 微缩真实 Google Antigravity 独立桌面应用（AGY Hub）光学预览组件 */
const MiniAntigravityAppPreview: React.FC<{ skin: SkinInfo }> = ({ skin }) => {
  const c = skin.colors;
  const bg = c.background || '#0b0e14';
  const sidebar = c.sidebar || '#101521';
  const titleBar = c.titleBar || sidebar;
  const panel = c.panel || sidebar;
  const inputBg = c.input || panel;
  const border = c.border || 'rgba(255,255,255,0.1)';
  const fg = c.foreground || '#e2e8f0';
  const muted = c.muted || '#64748b';
  const accent = c.accent || '#38bdf8';
  const accentFg = c.accentForeground || '#090d18';
  const selection = c.selection || `${accent}2e`;

  return (
    <div
      className="relative h-44 w-full overflow-hidden select-none p-3 flex items-center justify-center"
      style={{
        background: `radial-gradient(circle at 18% 20%, ${accent}28, transparent 58%), radial-gradient(circle at 86% 82%, ${accent}20, transparent 62%), ${bg}`,
      }}
    >
      {/* 主题专属意境插画暗纹叠加（如 CLANNAD 光玉、樱花团子、向日葵、海星） */}
      {skin.preview_data_uri && (
        <img
          src={skin.preview_data_uri}
          alt=""
          className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-25 mix-blend-luminosity transition-transform duration-700 group-hover:scale-105"
        />
      )}

      {/* 微缩 Antigravity 桌面应用无边框主视窗 */}
      <div
        className="relative z-10 w-full h-full rounded-xl overflow-hidden flex flex-col transition-transform duration-500 group-hover:-translate-y-0.5"
        style={{
          backgroundColor: bg,
          border: `1px solid ${border}`,
          boxShadow: '0 18px 36px -12px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.12)',
        }}
      >
        {/* 应用无边框顶栏 */}
        <div
          className="h-5 px-2.5 flex items-center justify-between border-b"
          style={{ backgroundColor: titleBar, borderColor: border }}
        >
          <div className="flex items-center gap-1.5">
            <span
              className="h-2 w-2 rounded-md shadow-sm"
              style={{ backgroundColor: accent }}
            />
            <span
              className="h-1.5 w-11 rounded-full opacity-75"
              style={{ backgroundColor: fg }}
            />
          </div>
          <div
            className="h-2.5 px-1.5 rounded-full flex items-center gap-1"
            style={{ backgroundColor: selection, border: `1px solid ${border}` }}
          >
            <span className="h-1 w-1 rounded-full" style={{ backgroundColor: accent }} />
            <span className="h-1 w-8 rounded-full opacity-70" style={{ backgroundColor: fg }} />
          </div>
          <div className="flex items-center gap-1 opacity-45">
            <span className="h-1 w-2 rounded-full" style={{ backgroundColor: fg }} />
            <span className="h-1.5 w-1.5 rounded-sm border" style={{ borderColor: fg }} />
          </div>
        </div>

        {/* 应用主体：会话导航侧边栏 + 智能体对话画布 + 伴生工件面板 */}
        <div className="flex flex-1 min-h-0">
          {/* 左侧会话与工作区抽屉（无 VS Code 竖排活动栏） */}
          <div
            className="w-[74px] p-1.5 flex flex-col justify-between border-r"
            style={{ backgroundColor: sidebar, borderColor: border }}
          >
            <div className="space-y-1">
              {/* 新建对话胶囊按钮 */}
              <div
                className="h-3 w-full rounded-md px-1.5 flex items-center gap-1"
                style={{
                  backgroundColor: `${accent}22`,
                  border: `1px solid ${accent}45`,
                }}
              >
                <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: accent }} />
                <span className="h-1 w-8 rounded-full opacity-85" style={{ backgroundColor: fg }} />
              </div>
              {/* 当前激活会话项 */}
              <div
                className="h-3 w-full rounded-md px-1.5 flex items-center gap-1"
                style={{ backgroundColor: selection }}
              >
                <span className="h-1 w-10 rounded-full" style={{ backgroundColor: fg }} />
              </div>
              <div
                className="h-1.5 w-11 rounded-full opacity-35 ml-1"
                style={{ backgroundColor: fg }}
              />
              <div
                className="h-1.5 w-9 rounded-full opacity-25 ml-1"
                style={{ backgroundColor: muted }}
              />
            </div>
            <div className="flex items-center gap-1 px-0.5 opacity-55">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: accent }} />
              <span className="h-1 w-7 rounded-full" style={{ backgroundColor: muted }} />
            </div>
          </div>

          {/* 中央智能体对话流 + 深度思考卡片 + 底部悬浮指令输入舱 */}
          <div className="flex-1 p-2 flex flex-col justify-between min-w-0 relative">
            <div className="space-y-1.5">
              {/* 用户消息气泡（右对齐胶囊） */}
              <div className="flex justify-end">
                <div
                  className="h-3 px-2 rounded-full flex items-center"
                  style={{
                    backgroundColor: selection,
                    border: `1px solid ${border}`,
                  }}
                >
                  <span className="h-1 w-10 rounded-full opacity-85" style={{ backgroundColor: fg }} />
                </div>
              </div>

              {/* 智能体毛玻璃深度思考与回复卡片 */}
              <div
                className="rounded-lg p-1.5 space-y-1"
                style={{
                  backgroundColor: panel,
                  border: `1px solid ${border}`,
                  boxShadow: '0 6px 16px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.08)',
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: accent }} />
                    <span className="h-1.5 w-10 rounded-full" style={{ backgroundColor: accent }} />
                  </div>
                  <span className="h-1 w-4 rounded-full opacity-40" style={{ backgroundColor: muted }} />
                </div>
                <div className="h-1.5 w-11/12 rounded-full opacity-75" style={{ backgroundColor: fg }} />
                <div className="h-1.5 w-3/5 rounded-full opacity-45" style={{ backgroundColor: muted }} />
              </div>
            </div>

            {/* 底部圆角悬浮指令输入舱（Composer） */}
            <div
              className="h-5 rounded-lg px-2 flex items-center justify-between"
              style={{
                backgroundColor: inputBg,
                border: `1px solid ${border}`,
                boxShadow: '0 4px 12px rgba(0,0,0,0.14)',
              }}
            >
              <span className="h-1 w-14 rounded-full opacity-45" style={{ backgroundColor: muted }} />
              <span
                className="h-3 w-3 rounded-full flex items-center justify-center"
                style={{ backgroundColor: accent, color: accentFg }}
              >
                <Send className="h-1.5 w-1.5" />
              </span>
            </div>
          </div>

          {/* 右侧微缩工件伴生视窗（Sidecar） */}
          <div
            className="w-11 p-1.5 border-l hidden sm:flex flex-col gap-1"
            style={{ backgroundColor: `${panel}cc`, borderColor: border }}
          >
            <span className="h-1 w-6 rounded-full opacity-60" style={{ backgroundColor: accent }} />
            <div
              className="flex-1 rounded p-1 space-y-1"
              style={{ backgroundColor: bg, border: `1px solid ${border}` }}
            >
              <div className="h-1 w-full rounded-full opacity-40" style={{ backgroundColor: fg }} />
              <div className="h-1 w-3/4 rounded-full opacity-25" style={{ backgroundColor: muted }} />
            </div>
          </div>
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
  onNavigateL10n,
}) => {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [filterMode, setFilterMode] = useState<FilterMode>('all');
  const [dupSource, setDupSource] = useState<SkinInfo | null>(null);
  const [dupNewId, setDupNewId] = useState('');
  const [dupNewName, setDupNewName] = useState('');
  const [overwriteImport, setOverwriteImport] = useState(true);
  const [confirmRestartMount, setConfirmRestartMount] = useState(false);

  const filteredSkins = useMemo(() => {
    return skins.filter((s) => {
      if (filterMode === 'clannad') return s.id.startsWith('clannad-');
      if (filterMode === 'dark') return s.base !== 'light';
      if (filterMode === 'light') return s.base === 'light';
      if (filterMode === 'custom') return !s.builtin;
      return true;
    });
  }, [skins, filterMode]);

  const hookReady = status.agent_status === 'patched' && status.enable_skin;

  const handleActivate = async (skin: SkinInfo) => {
    setBusyId(skin.id);
    try {
      await studioService.activateSkin(skin.id);
      await onRefresh();
      const latest = await studioService.getStatus();
      if (latest.agent_status === 'patched' && latest.enable_skin) {
        showToast(
          `已将「${skin.name}」应用至 Antigravity 桌面应用（实时热重载已生效）`,
          'success',
        );
      } else if (latest.agent_status === 'not_found') {
        showToast(
          `已编译激活「${skin.name}」，请先指定本机 Antigravity 应用安装目录`,
          'warning',
        );
      } else {
        showToast(
          `已编译激活「${skin.name}」，当前 Antigravity 正在运行，点击右上角「挂载至应用」或退出应用后自动生效`,
          'info',
        );
      }
    } catch (err: unknown) {
      showToast(`启用失败: ${String(err)}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  const handleMountHookToApp = async () => {
    setBusyId('__mount__');
    try {
      const res = await studioService.applyL10n({
        install_dir: status.install_dir || null,
        lang: status.lang || 'zh-cn',
        character: status.splash_character || 'none',
        enable_pet: false,
        enable_skin: true,
      });
      setConfirmRestartMount(false);
      showToast(`${res.message}（后续切换任意皮肤均支持毫秒级无感热重载）`, 'success');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`挂载应用皮肤钩子失败: ${String(err)}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  const handleDisable = async () => {
    setBusyId('__disable__');
    try {
      await studioService.disableSkin();
      showToast('已恢复 Antigravity 桌面应用默认原生外观', 'info');
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
                ['clannad', '🌸 CLANNAD 典藏'],
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
              还原应用默认样式
            </button>
          )}
        </div>

        {/* Antigravity 桌面应用原生热重载联动舱 */}
        <div className="flex flex-wrap items-center gap-2.5 rounded-xl bg-gray-50/90 dark:bg-black/30 px-3.5 py-2 border border-gray-200/80 dark:border-white/10">
          <MonitorSmartphone className="h-4 w-4 text-sky-500" />
          <div className="text-xs text-gray-600 dark:text-gray-300">
            Antigravity 应用联动：
            <span
              className={`font-semibold ml-1 ${
                hookReady
                  ? 'text-emerald-500'
                  : status.agent_status === 'not_found'
                    ? 'text-gray-400'
                    : 'text-amber-500'
              }`}
            >
              {hookReady
                ? '热重载钩子已就绪（切换即刻生效）'
                : status.agent_status === 'not_found'
                  ? '未探测到官方应用目录'
                  : '待挂载客户端皮肤钩子'}
            </span>
          </div>

          {!hookReady && status.agent_status !== 'not_found' && (
            <button
              type="button"
              onClick={() => {
                if (status.app_running) {
                  setConfirmRestartMount(true);
                } else {
                  void handleMountHookToApp();
                }
              }}
              disabled={busyId === '__mount__'}
              className="inline-flex items-center gap-1 rounded-lg bg-gradient-to-r from-sky-500 to-indigo-500 px-3 py-1 text-xs font-semibold text-white shadow-sm hover:opacity-90 disabled:opacity-50"
            >
              <Wand2 className="h-3 w-3" />
              {busyId === '__mount__'
                ? '正在挂载...'
                : status.app_running
                  ? '挂载至 Antigravity 应用'
                  : '一键挂载钩子'}
            </button>
          )}

          {status.agent_status === 'not_found' && onNavigateL10n && (
            <button
              type="button"
              onClick={onNavigateL10n}
              className="rounded-lg border border-gray-300 dark:border-white/15 px-2.5 py-1 text-xs font-medium text-sky-500 hover:bg-sky-500/10"
            >
              指定应用目录
            </button>
          )}
        </div>
      </div>

      {/* 客户端运行态挂载钩子温和确认条（保护正在进行的对话不被意外中断） */}
      {confirmRestartMount && (
        <div className="rounded-2xl border border-amber-400/60 dark:border-amber-500/35 bg-amber-50/85 dark:bg-amber-950/30 backdrop-blur-md p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-0.5 text-xs">
            <div className="font-bold text-amber-900 dark:text-amber-200">
              检测到官方 Antigravity 桌面应用正在运行
            </div>
            <p className="text-amber-800/90 dark:text-amber-300/85">
              首次写入（或官方更新后恢复）热加载钩子需短暂关闭客户端以更新 <code className="font-mono">app.asar</code>；挂载完成后，今后所有皮肤切换均支持毫秒级免重启热重载。你也可以直接先关闭客户端，后台哨兵会自动静默补齐。
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleMountHookToApp}
              disabled={busyId === '__mount__'}
              className="rounded-xl bg-amber-600 hover:bg-amber-700 px-3.5 py-2 text-xs font-semibold text-white shadow disabled:opacity-50"
            >
              {busyId === '__mount__' ? '正在关闭并挂载...' : '关闭客户端并立即挂载'}
            </button>
            <button
              type="button"
              onClick={() => setConfirmRestartMount(false)}
              className="rounded-xl border border-amber-400/40 px-3 py-2 text-xs text-amber-800 dark:text-amber-200"
            >
              稍后退出时自动挂载
            </button>
          </div>
        </div>
      )}

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
            skin.colors.panel || skin.colors.sidebar,
            skin.colors.input || skin.colors.background,
            skin.colors.accent,
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
                {/* 微缩真实 Antigravity 应用渲染区 */}
                <div className="relative">
                  <MiniAntigravityAppPreview skin={skin} />

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
                    {skin.id.startsWith('clannad-') && (
                      <span className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold tracking-wide backdrop-blur-md bg-pink-500/85 text-white border border-pink-300/40">
                        🌸 CLANNAD 典藏
                      </span>
                    )}
                  </div>

                  {/* 右上激活徽章 */}
                  {skin.active && (
                    <div className="absolute top-3 right-3 z-20 inline-flex items-center gap-1 rounded-full bg-emerald-500/95 px-2.5 py-0.5 text-[10px] font-bold text-white shadow-lg backdrop-blur">
                      <Check className="h-3 w-3" />
                      生效中
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
                      {skin.base === 'light' ? '浅色' : '深色'}
                    </span>
                  </div>

                  <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 min-h-[34px] leading-relaxed">
                    {skin.description || '专为 Antigravity 桌面应用打造的光学渐变与高对比材质方案'}
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
                    onClick={() => handleActivate(skin)}
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
