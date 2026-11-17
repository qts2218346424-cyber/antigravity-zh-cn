import React, { useEffect, useState } from 'react';
import { open } from '@tauri-apps/plugin-dialog';
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  FolderSearch,
  Languages,
  RotateCcw,
  ShieldCheck,
  ShieldOff,
  Wand2,
} from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
import { studioService } from '../../services/studioService';
import type { L10nPatchResult, StudioStatus } from '../../types/studio';
import { isTauri } from '../../utils/env';

interface L10nTabProps {
  status: StudioStatus;
  onRefresh: () => Promise<void>;
}

export const L10nTab: React.FC<L10nTabProps> = ({ status, onRefresh }) => {
  const [installDir, setInstallDir] = useState(status.install_dir || '');
  const [ideRoot, setIdeRoot] = useState(status.ide_root || '');
  const [lang, setLang] = useState(status.lang || 'zh-cn');
  const [enableSkin, setEnableSkin] = useState(status.enable_skin ?? true);
  const [busy, setBusy] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<L10nPatchResult | null>(null);

  useEffect(() => {
    if (status.install_dir) setInstallDir(status.install_dir);
    if (status.ide_root) setIdeRoot(status.ide_root);
    if (status.lang) setLang(status.lang);
  }, [status]);

  const browseFolder = async (target: 'agent' | 'ide') => {
    if (!isTauri()) {
      showToast('请在桌面客户端中浏览选择安装目录', 'warning');
      return;
    }
    const picked = await open({
      directory: true,
      multiple: false,
      title: target === 'agent' ? '选择 Antigravity 客户端安装目录' : '选择 Antigravity IDE 目录',
    });
    if (!picked || Array.isArray(picked)) return;
    if (target === 'agent') {
      setInstallDir(picked);
      await studioService.updatePaths(picked, undefined);
    } else {
      setIdeRoot(picked);
      await studioService.updatePaths(undefined, picked);
    }
    await onRefresh();
  };

  const handleApplyPatch = async () => {
    setBusy('apply');
    try {
      const res = await studioService.applyL10n({
        install_dir: installDir || null,
        lang,
        character: status.splash_character || 'none',
        enable_pet: false,
        enable_skin: enableSkin,
      });
      setLastResult(res);
      showToast(res.message, 'success');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`汉化注入失败: ${String(err)}`, 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleRestore = async () => {
    setBusy('restore');
    try {
      const msg = await studioService.restoreL10n(installDir || null);
      showToast(msg, 'info');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`还原备份失败: ${String(err)}`, 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleToggleUpdates = async () => {
    setBusy('updates');
    try {
      const nextDisabled = !status.updates_disabled;
      const result = await studioService.toggleUpdates(installDir || null, nextDisabled);
      showToast(
        result ? '已屏蔽官方自动更新（保护汉化补丁不被覆盖）' : '已恢复官方自动更新配置',
        'success',
      );
      await onRefresh();
    } catch (err: unknown) {
      showToast(`切换更新开关失败: ${String(err)}`, 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleLocalizeSkills = async () => {
    setBusy('skills');
    try {
      const res = await studioService.localizeSkills();
      showToast(
        `扫描 ${res.scanned} 个 Skill 描述，成功汉化 ${res.updated} 项`,
        res.updated > 0 ? 'success' : 'info',
      );
    } catch (err: unknown) {
      showToast(`Skill 汉化失败: ${String(err)}`, 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleEnsureProtocol = async () => {
    setBusy('protocol');
    try {
      const added = await studioService.ensureProtocol();
      showToast(
        added
          ? '已将《全中文呈现与深度思考规范》写入 ~/.gemini/GEMINI.md'
          : '~/.gemini/GEMINI.md 中已包含全中文思考规范，无需重复注入',
        'success',
      );
    } catch (err: unknown) {
      showToast(`规范写入失败: ${String(err)}`, 'error');
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      {status.has_legacy_pet && (
        <div className="rounded-xl border border-amber-400/70 bg-amber-50 dark:bg-amber-950/35 p-4 flex flex-wrap items-center justify-between gap-3 shadow-sm">
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <div className="text-xs font-bold text-amber-800 dark:text-amber-200">
                检测到 Antigravity 客户端内部仍注入了旧脚本的老宠物代码
              </div>
              <p className="text-[11.5px] text-amber-700/90 dark:text-amber-300/90">
                这是先前旧补丁写入 <code className="font-mono">app.asar</code> 的残留（新版已迁移至「伴侣与守护」独立窗口）。点击右侧按钮将关闭并重刷客户端，彻底清除老宠物残留。
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleApplyPatch}
            disabled={busy !== null}
            className="inline-flex items-center gap-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 px-4 py-2 text-xs font-semibold text-white shadow disabled:opacity-60"
          >
            <Wand2 className="h-3.5 w-3.5" />
            {busy === 'apply' ? '正在清除并重刷...' : '立即清除老宠物并升级补丁'}
          </button>
        </div>
      )}

      {/* 安装路径配置卡片 */}
      <div className="rounded-xl border border-gray-200 dark:border-base-300 bg-white dark:bg-base-100 p-5 space-y-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-bold text-gray-800 dark:text-gray-100">
            <FolderSearch className="h-4 w-4 text-blue-500" />
            Antigravity 客户端安装路径探测
          </div>
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
              status.agent_status === 'patched'
                ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                : status.agent_status === 'clean'
                  ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                  : 'bg-gray-200 dark:bg-base-300 text-gray-500'
            }`}
          >
            {status.agent_status === 'patched'
              ? '已汉化并增强'
              : status.agent_status === 'clean'
                ? '官方原版 (未汉化)'
                : '未检测到安装目录'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Antigravity 桌面客户端根目录（含 resources/app.asar）
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={installDir}
                onChange={(e) => setInstallDir(e.target.value)}
                onBlur={() => studioService.updatePaths(installDir, undefined).catch(() => {})}
                placeholder="自动探测中..."
                className="flex-1 rounded-lg border border-gray-300 dark:border-base-300 bg-gray-50 dark:bg-base-200 px-3 py-2 text-xs font-mono"
              />
              <button
                onClick={() => browseFolder('agent')}
                className="rounded-lg border border-gray-300 dark:border-base-300 px-3 py-2 text-xs font-medium hover:bg-gray-100 dark:hover:bg-base-200"
              >
                浏览
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Antigravity IDE 应用根目录（含 workbench.desktop.main.css）
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={ideRoot}
                onChange={(e) => setIdeRoot(e.target.value)}
                onBlur={() => studioService.updatePaths(undefined, ideRoot).catch(() => {})}
                placeholder="自动探测或手动选择..."
                className="flex-1 rounded-lg border border-gray-300 dark:border-base-300 bg-gray-50 dark:bg-base-200 px-3 py-2 text-xs font-mono"
              />
              <button
                onClick={() => browseFolder('ide')}
                className="rounded-lg border border-gray-300 dark:border-base-300 px-3 py-2 text-xs font-medium hover:bg-gray-100 dark:hover:bg-base-200"
              >
                浏览
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 语言与核心注入选项 */}
      <div className="rounded-xl border border-gray-200 dark:border-base-300 bg-white dark:bg-base-100 p-5 space-y-5 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="flex items-center gap-1.5 text-xs font-bold text-gray-700 dark:text-gray-200 mb-2">
              <Languages className="h-4 w-4 text-sky-500" />
              目标汉化语言
            </label>
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-base-300 bg-white dark:bg-base-200 px-3 py-2 text-xs"
            >
              <option value="zh-cn">简体中文 (中国大陆 · 3500+ 词条)</option>
              <option value="zh-tw">繁體中文 (台灣常用術語)</option>
              <option value="zh-hk">繁體中文 (香港特別行政區)</option>
            </select>
          </div>

          <div className="flex flex-col justify-end gap-2">
            <div className="text-[11.5px] text-emerald-600 dark:text-emerald-400">
              ✓ 已保留官方原版极速启动流程；桌面伴侣由「伴侣与守护」独立悬浮窗接管
            </div>
            <label className="inline-flex items-center gap-2 text-xs text-gray-700 dark:text-gray-200 cursor-pointer">
              <input
                type="checkbox"
                checked={enableSkin}
                onChange={(e) => setEnableSkin(e.target.checked)}
                className="rounded border-gray-300 text-purple-600"
              />
              注入主进程皮肤热重载钩子 (`__agzhSkin`)
            </label>
          </div>
        </div>

        {/* 核心操作按钮矩阵 */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-gray-100 dark:border-base-300">
          <button
            onClick={handleApplyPatch}
            disabled={busy !== null}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow hover:from-blue-700 hover:to-indigo-700 disabled:opacity-60"
          >
            <Wand2 className="h-4 w-4" />
            {busy === 'apply' ? '正在原位注入 app.asar ...' : '一键汉化并应用增强补丁'}
          </button>

          <button
            onClick={handleRestore}
            disabled={busy !== null}
            className="inline-flex items-center gap-1.5 rounded-xl border border-gray-300 dark:border-base-300 px-4 py-2.5 text-xs font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-base-200 disabled:opacity-60"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            还原官方原版 (.bak)
          </button>

          <button
            onClick={handleToggleUpdates}
            disabled={busy !== null}
            className={`inline-flex items-center gap-1.5 rounded-xl border px-4 py-2.5 text-xs font-medium transition-colors ${
              status.updates_disabled
                ? 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300'
                : 'border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-300'
            }`}
          >
            {status.updates_disabled ? (
              <>
                <ShieldCheck className="h-3.5 w-3.5" />
                已阻止自动更新覆盖（点击恢复）
              </>
            ) : (
              <>
                <ShieldOff className="h-3.5 w-3.5" />
                一键屏蔽自动更新
              </>
            )}
          </button>
        </div>

        {/* 最近一次执行详情 */}
        {lastResult && (
          <div className="rounded-lg bg-emerald-50 dark:bg-emerald-950/25 border border-emerald-200 dark:border-emerald-800/60 p-3 text-xs space-y-1">
            <div className="flex items-center gap-1.5 font-semibold text-emerald-700 dark:text-emerald-300">
              <CheckCircle2 className="h-4 w-4" />
              {lastResult.message}
            </div>
            <div className="text-[11px] text-gray-600 dark:text-gray-400">
              已修补内部模块：{lastResult.patched_files.join('、')}
            </div>
            {lastResult.warnings.length > 0 && (
              <div className="text-[11px] text-amber-600 dark:text-amber-400">
                提示：{lastResult.warnings.join('；')}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 生态附属增强：Skill 自动汉化 & 全中文思考规范 */}
      <div className="rounded-xl border border-gray-200 dark:border-base-300 bg-white dark:bg-base-100 p-5 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm font-bold text-gray-800 dark:text-gray-100">
            <BookOpen className="h-4 w-4 text-purple-500" />
            AI 技能列表汉化与思考规范固化
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            批量翻译 <code className="font-mono">~/.gemini</code> 下所有内置与插件 Skill 技能面板描述，并注入全局中文深度思考协议。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleLocalizeSkills}
            disabled={busy !== null}
            className="rounded-lg bg-purple-600 px-3.5 py-2 text-xs font-medium text-white hover:bg-purple-700 disabled:opacity-60"
          >
            {busy === 'skills' ? '扫描汉化中...' : '一键汉化全部 Skill 描述'}
          </button>
          <button
            onClick={handleEnsureProtocol}
            disabled={busy !== null}
            className="rounded-lg border border-gray-300 dark:border-base-300 px-3.5 py-2 text-xs font-medium hover:bg-gray-100 dark:hover:bg-base-200 disabled:opacity-60"
          >
            写入 GEMINI.md 全中文思考规范
          </button>
        </div>
      </div>
    </div>
  );
};
