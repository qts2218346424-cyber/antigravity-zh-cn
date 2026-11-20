import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Cpu,
  Flame,
  FolderOpen,
  HardDrive,
  Lock,
  Plus,
  Power,
  RefreshCw,
  RotateCcw,
  Search,
  Server,
  ShieldAlert,
  ShieldCheck,
  Snowflake,
  Trash2,
  X,
  Zap,
} from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
import {
  classifyCommitPressure,
  filterAndSortProcessGroups,
  formatBytesMb,
  normalizeCustomWhitelistInput,
  type ProcessFilterMode,
  type ProcessSortMode,
} from '../../components/pet/optimizerLogic';
import { optimizerService } from '../../services/optimizerService';
import type {
  JunkCategoryItem,
  LargeFileScanResult,
  OptimizerOverview,
  ProcessGroupItem,
  ServiceItem,
  WhitelistSnapshot,
} from '../../types/optimizer';

type OptimizerSubSection = 'processes' | 'services' | 'files' | 'whitelist';

export const OptimizerTab: React.FC = () => {
  const [section, setSection] = useState<OptimizerSubSection>('processes');
  const [overview, setOverview] = useState<OptimizerOverview | null>(null);
  const [processes, setProcesses] = useState<ProcessGroupItem[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [junkList, setJunkList] = useState<JunkCategoryItem[]>([]);
  const [selectedJunkIds, setSelectedJunkIds] = useState<Set<string>>(new Set());
  const [largeScan, setLargeScan] = useState<LargeFileScanResult | null>(null);
  const [scanRootInput, setScanRootInput] = useState<string>('');
  const [minFileMb, setMinFileMb] = useState<number>(50);
  const [whitelist, setWhitelist] = useState<WhitelistSnapshot | null>(null);
  const [customWhitelistInput, setCustomWhitelistInput] = useState<string>('');

  const [procFilter, setProcFilter] = useState<ProcessFilterMode>('all');
  const [procSort, setProcSort] = useState<ProcessSortMode>('memory');
  const [procSearch, setProcSearch] = useState<string>('');
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [confirmKillName, setConfirmKillName] = useState<string | null>(null);

  const refreshOverviewAndProcs = useCallback(async () => {
    try {
      const [ov, procs] = await Promise.all([
        optimizerService.getOverview(),
        optimizerService.listProcesses(),
      ]);
      setOverview(ov);
      setProcesses(procs);
    } catch (err) {
      showToast(`刷新系统性能状态失败: ${String(err)}`, 'error');
    }
  }, []);

  const refreshServices = useCallback(async () => {
    try {
      const svcs = await optimizerService.listServices();
      setServices(svcs);
    } catch (err) {
      showToast(`读取系统服务失败: ${String(err)}`, 'error');
    }
  }, []);

  const refreshJunk = useCallback(async () => {
    setBusyKey('scan_junk');
    try {
      const list = await optimizerService.scanJunk();
      setJunkList(list);
      setSelectedJunkIds(new Set(list.filter((i) => i.defaultChecked).map((i) => i.id)));
    } catch (err) {
      showToast(`扫描缓存失败: ${String(err)}`, 'error');
    } finally {
      setBusyKey(null);
    }
  }, []);

  const refreshLargeFiles = useCallback(
    async (customRoot?: string) => {
      setBusyKey('scan_large');
      try {
        const res = await optimizerService.scanLargeFiles(
          (customRoot ?? scanRootInput) || null,
          minFileMb,
        );
        setLargeScan(res);
        if (!scanRootInput && res.rootPath) {
          setScanRootInput(res.rootPath);
        }
      } catch (err) {
        showToast(`大文件扫描失败: ${String(err)}`, 'error');
      } finally {
        setBusyKey(null);
      }
    },
    [minFileMb, scanRootInput],
  );

  const refreshWhitelist = useCallback(async () => {
    try {
      const wl = await optimizerService.getWhitelist();
      setWhitelist(wl);
    } catch (err) {
      showToast(`获取白名单失败: ${String(err)}`, 'error');
    }
  }, []);

  useEffect(() => {
    refreshOverviewAndProcs();
    refreshServices();
    refreshWhitelist();
    const timer = window.setInterval(() => {
      optimizerService
        .getOverview()
        .then(setOverview)
        .catch(() => {});
    }, 3000);
    return () => window.clearInterval(timer);
  }, [refreshOverviewAndProcs, refreshServices, refreshWhitelist]);

  useEffect(() => {
    if (section === 'files' && junkList.length === 0) {
      refreshJunk();
      refreshLargeFiles();
    }
  }, [section, junkList.length, refreshJunk, refreshLargeFiles]);

  const handleToggleRuthless = async () => {
    const next = !(overview?.ruthlessEnabled ?? false);
    setBusyKey('ruthless');
    try {
      const ov = await optimizerService.toggleRuthless(next);
      setOverview(ov);
      showToast(
        next
          ? `极客霸权已锁定：0.5ms 时钟已就绪，已将 ${ov.throttledCount} 个后台进程孤立至 ${ov.exileCoresLabel}`
          : '已安全退出极客霸权模式并恢复所有后台正常调度',
        next ? 'success' : 'info',
      );
      await refreshOverviewAndProcs();
    } catch (err) {
      showToast(`切换模式失败: ${String(err)}`, 'error');
    } finally {
      setBusyKey(null);
    }
  };

  const handleBoostMemory = async () => {
    setBusyKey('memory');
    try {
      const res = await optimizerService.boostMemory();
      showToast(res.message, res.needsElevation ? 'info' : 'success');
      await refreshOverviewAndProcs();
    } catch (err) {
      showToast(`内存释放失败: ${String(err)}`, 'error');
    } finally {
      setBusyKey(null);
    }
  };

  const handleUnfreezeAll = async () => {
    setBusyKey('unfreeze_all');
    try {
      const res = await optimizerService.unfreezeAll();
      showToast(res.message, 'success');
      await refreshOverviewAndProcs();
    } catch (err) {
      showToast(`解冻失败: ${String(err)}`, 'error');
    } finally {
      setBusyKey(null);
    }
  };

  const handleProcessAction = async (
    name: string,
    action: 'freeze' | 'unfreeze' | 'isolate' | 'restore' | 'kill',
  ) => {
    setBusyKey(`proc:${name}`);
    setConfirmKillName(null);
    try {
      const res = await optimizerService.processAction(name, action);
      showToast(res.message, res.success ? 'success' : 'error');
      await refreshOverviewAndProcs();
    } catch (err) {
      showToast(`进程操作失败: ${String(err)}`, 'error');
    } finally {
      setBusyKey(null);
    }
  };

  const handleAddCustomWhitelist = async (procName: string) => {
    if (!whitelist) return;
    const merged = normalizeCustomWhitelistInput([...whitelist.custom, procName].join(','));
    try {
      const updated = await optimizerService.updateWhitelist(merged);
      setWhitelist(updated);
      showToast(`已将「${procName}」加入永久免疫白名单`, 'success');
      await refreshOverviewAndProcs();
    } catch (err) {
      showToast(`加入白名单失败: ${String(err)}`, 'error');
    }
  };

  const handleRemoveCustomWhitelist = async (procName: string) => {
    if (!whitelist) return;
    const next = whitelist.custom.filter((c) => c !== procName);
    try {
      const updated = await optimizerService.updateWhitelist(next);
      setWhitelist(updated);
      showToast(`已从自定义白名单移除「${procName}」`, 'info');
      await refreshOverviewAndProcs();
    } catch (err) {
      showToast(`移除白名单失败: ${String(err)}`, 'error');
    }
  };

  const handleAddWhitelistInput = async () => {
    if (!whitelist || !customWhitelistInput.trim()) return;
    const merged = normalizeCustomWhitelistInput(
      `${whitelist.custom.join(',')},${customWhitelistInput}`,
    );
    try {
      const updated = await optimizerService.updateWhitelist(merged);
      setWhitelist(updated);
      setCustomWhitelistInput('');
      showToast('自定义白名单已更新并即时生效', 'success');
      await refreshOverviewAndProcs();
    } catch (err) {
      showToast(`更新白名单失败: ${String(err)}`, 'error');
    }
  };

  const handleServiceAction = async (
    name: string,
    action: 'stop' | 'start' | 'manual' | 'auto',
  ) => {
    setBusyKey(`svc:${name}:${action}`);
    try {
      const msg = await optimizerService.serviceAction(name, action);
      showToast(msg, 'success');
      await Promise.all([refreshServices(), refreshOverviewAndProcs()]);
    } catch (err) {
      showToast(String(err), 'error');
    } finally {
      setBusyKey(null);
    }
  };

  const handleCleanJunk = async () => {
    if (selectedJunkIds.size === 0) return;
    setBusyKey('clean_junk');
    try {
      const res = await optimizerService.cleanJunk(Array.from(selectedJunkIds));
      showToast(res.message, 'success');
      await refreshJunk();
    } catch (err) {
      showToast(`清理失败: ${String(err)}`, 'error');
    } finally {
      setBusyKey(null);
    }
  };

  const handleFileAction = async (path: string, action: 'reveal' | 'trash') => {
    setBusyKey(`file:${path}`);
    try {
      const msg = await optimizerService.fileAction(path, action);
      showToast(msg, 'success');
      if (action === 'trash') {
        await refreshLargeFiles();
      }
    } catch (err) {
      showToast(String(err), 'error');
    } finally {
      setBusyKey(null);
    }
  };

  const handleElevate = async () => {
    setBusyKey('elevate');
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem('studio:resume-tab', 'optimizer');
      }
      await optimizerService.relaunchAsAdmin();
    } catch (err) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('studio:resume-tab');
      }
      showToast(String(err), 'error');
    } finally {
      setBusyKey(null);
    }
  };

  const visibleProcesses = useMemo(
    () => filterAndSortProcessGroups(processes, procFilter, procSearch, procSort),
    [processes, procFilter, procSearch, procSort],
  );

  const selectedJunkTotalMb = useMemo(
    () =>
      junkList
        .filter((j) => selectedJunkIds.has(j.id))
        .reduce((acc, j) => acc + j.sizeMb, 0),
    [junkList, selectedJunkIds],
  );

  const pressure = classifyCommitPressure(
    overview?.commitPercent ?? 0,
    overview?.memPercent ?? 0,
  );

  return (
    <div className="space-y-6">
      {/* UAC 提权引导横幅（仅在 Windows 非管理员态出现） */}
      {overview && overview.isWindows && !overview.isElevated && (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-amber-500/25 bg-amber-500/10 px-6 py-4">
          <div className="flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-amber-500 dark:text-amber-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-sm font-semibold text-slate-900 dark:text-zinc-100">
                当前运行于普通用户权限，部分内核压榨与服务止血受限
              </div>
              <p className="mt-0.5 text-xs text-slate-600 dark:text-zinc-400 leading-relaxed">
                以管理员身份重启后将自动开启 SeDebugPrivilege 与 SeProfileSingleProcessPrivilege，可彻底解锁：清空系统 Standby 备用内存死锁、启停 SQL Server / SysMain / 奥创系统服务，以及压制高权限后台进程。
              </p>
            </div>
          </div>
          <button
            type="button"
            disabled={busyKey === 'elevate'}
            onClick={handleElevate}
            className="inline-flex items-center gap-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-zinc-950 px-4 py-2 text-xs font-semibold transition-all active:scale-[0.98]"
          >
            <Lock className="h-3.5 w-3.5" />
            {busyKey === 'elevate' ? '正在提权重启…' : '一键 UAC 管理员提权'}
          </button>
        </div>
      )}

      {/* 顶部系统遥测与极客霸权主控台 */}
      <div className="rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900/80 p-6 shadow-xs space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <span
                className={`inline-flex h-9 w-9 items-center justify-center rounded-xl border ${
                  overview?.ruthlessEnabled
                    ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-500 dark:text-emerald-400'
                    : 'bg-indigo-500/10 border-indigo-500/25 text-indigo-600 dark:text-indigo-400'
                }`}
              >
                <Zap className="h-4 w-4" />
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-semibold tracking-tight text-slate-900 dark:text-zinc-50">
                    极客霸权压榨与资源治理台
                  </h2>
                  {overview?.isElevated && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20 px-2.5 py-0.5 text-[11px] font-medium">
                      <ShieldCheck className="h-3 w-3" />
                      管理员内核权限已就绪
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-xs text-slate-500 dark:text-zinc-400">
                  {overview?.logicalCpus ?? 16} 逻辑核心 · 孤立围栏：{overview?.exileCoresLabel || 'CPU 14-15'} · 代理与 Antigravity 进程树 100% 免杀保护
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              disabled={Boolean(busyKey)}
              onClick={handleBoostMemory}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200/80 dark:border-white/10 bg-slate-50 dark:bg-zinc-800/70 hover:bg-slate-100 dark:hover:bg-zinc-800 px-3.5 py-2 text-xs font-medium text-slate-700 dark:text-zinc-200 transition-all active:scale-[0.98]"
            >
              <Activity className="h-3.5 w-3.5 text-sky-500" />
              {busyKey === 'memory' ? '释放中…' : '释放 Standby 与后台内存'}
            </button>

            {(overview?.frozenCount ?? 0) > 0 && (
              <button
                type="button"
                disabled={Boolean(busyKey)}
                onClick={handleUnfreezeAll}
                className="inline-flex items-center gap-1.5 rounded-lg border border-sky-500/30 bg-sky-500/10 hover:bg-sky-500/20 px-3.5 py-2 text-xs font-medium text-sky-600 dark:text-sky-300 transition-all active:scale-[0.98]"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                解冻全部 ({overview?.frozenCount})
              </button>
            )}

            <button
              type="button"
              disabled={busyKey === 'ruthless'}
              onClick={handleToggleRuthless}
              className={`inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-semibold transition-all active:scale-[0.98] ${
                overview?.ruthlessEnabled
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white'
              }`}
            >
              <Flame className="h-3.5 w-3.5" />
              {busyKey === 'ruthless'
                ? '正在调度…'
                : overview?.ruthlessEnabled
                  ? '极客霸权守护中（点击还原）'
                  : '一键开启极客霸权压榨'}
            </button>
          </div>
        </div>

        {/* 四大 KPI 等宽数值卡 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-xl border border-slate-200/80 dark:border-white/[0.08] bg-slate-50/70 dark:bg-zinc-950/60 p-4">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-zinc-400">
              <span>物理内存可用</span>
              <span className="font-mono tabular-nums font-medium">
                {(overview?.memPercent ?? 0).toFixed(1)}%
              </span>
            </div>
            <div className="mt-2 text-2xl font-bold tracking-tight tabular-nums text-slate-900 dark:text-zinc-50">
              {formatBytesMb(overview?.memAvailableMb ?? 0)}
            </div>
            <div className="mt-2 h-1.5 w-full rounded-full bg-slate-200 dark:bg-zinc-800 overflow-hidden">
              <div
                className="h-full rounded-full bg-indigo-500 transition-all duration-300"
                style={{ width: `${Math.min(100, overview?.memPercent ?? 0)}%` }}
              />
            </div>
            <div className="mt-1.5 text-[11px] text-slate-400 dark:text-zinc-500 tabular-nums">
              已用 {formatBytesMb(overview?.memUsedMb ?? 0)} / {formatBytesMb(overview?.memTotalMb ?? 0)}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200/80 dark:border-white/[0.08] bg-slate-50/70 dark:bg-zinc-950/60 p-4">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-zinc-400">
              <span>虚拟提交 (Commit 换页压力)</span>
              <span
                className={`font-mono tabular-nums font-medium ${
                  pressure === 'critical'
                    ? 'text-rose-500 dark:text-rose-400'
                    : pressure === 'elevated'
                      ? 'text-amber-500 dark:text-amber-400'
                      : 'text-emerald-500 dark:text-emerald-400'
                }`}
              >
                {(overview?.commitPercent ?? 0).toFixed(1)}%
              </span>
            </div>
            <div className="mt-2 text-2xl font-bold tracking-tight tabular-nums text-slate-900 dark:text-zinc-50">
              {formatBytesMb(overview?.commitUsedMb ?? 0)}
            </div>
            <div className="mt-2 h-1.5 w-full rounded-full bg-slate-200 dark:bg-zinc-800 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  pressure === 'critical'
                    ? 'bg-rose-500'
                    : pressure === 'elevated'
                      ? 'bg-amber-500'
                      : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(100, overview?.commitPercent ?? 0)}%` }}
              />
            </div>
            <div className="mt-1.5 text-[11px] text-slate-400 dark:text-zinc-500 tabular-nums">
              提交上限 {formatBytesMb(overview?.commitTotalMb ?? 0)}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200/80 dark:border-white/[0.08] bg-slate-50/70 dark:bg-zinc-950/60 p-4">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-zinc-400">
              <span>系统时钟精度 & 菜单延迟</span>
              <Cpu className="h-3.5 w-3.5 text-zinc-500" />
            </div>
            <div className="mt-2 text-2xl font-bold tracking-tight tabular-nums text-slate-900 dark:text-zinc-50">
              {(overview?.timerResolutionMs ?? 15.625).toFixed(2)} ms
            </div>
            <div className="mt-2 flex items-center gap-2 text-[11px]">
              <span
                className={`rounded-md px-1.5 py-0.5 border font-mono tabular-nums ${
                  (overview?.menuShowDelayMs ?? 400) === 0
                    ? 'bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 border-emerald-500/20'
                    : 'bg-zinc-200/70 dark:bg-zinc-800 text-slate-600 dark:text-zinc-400 border-transparent'
                }`}
              >
                菜单延迟 {overview?.menuShowDelayMs ?? 400}ms
              </span>
              <span className="text-slate-400 dark:text-zinc-500 tabular-nums">
                CPU {(overview?.cpuPercent ?? 0).toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200/80 dark:border-white/[0.08] bg-slate-50/70 dark:bg-zinc-950/60 p-4">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-zinc-400">
              <span>压榨与白名单护盾统计</span>
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
            </div>
            <div className="mt-2 text-2xl font-bold tracking-tight tabular-nums text-slate-900 dark:text-zinc-50">
              {overview?.throttledCount ?? 0}{' '}
              <span className="text-sm font-medium text-slate-500 dark:text-zinc-400">
                / 冻 {overview?.frozenCount ?? 0}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-500 dark:text-zinc-400 truncate">
              VIP 前台：{overview?.foregroundProcess || '自动追踪'}
            </div>
            <div className="mt-0.5 text-[11px] text-emerald-600 dark:text-emerald-400 tabular-nums">
              已护盾 {overview?.protectedCount ?? 0} 个代理/核心实例
            </div>
          </div>
        </div>
      </div>

      {/* 四大治理子区导航 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="inline-flex rounded-xl border border-slate-200/80 dark:border-white/10 bg-slate-100/80 dark:bg-zinc-900/70 p-1 gap-1">
          {(
            [
              ['processes', '进程霸权台', Activity],
              ['services', '常驻服务止血', Server],
              ['files', '缓存与大文件清理', HardDrive],
              ['whitelist', '神圣白名单管理', ShieldCheck],
            ] as Array<[OptimizerSubSection, string, React.ComponentType<{ className?: string }>]>
          ).map(([key, label, Icon]) => {
            const active = section === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setSection(key)}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all ${
                  active
                    ? 'bg-white dark:bg-zinc-800 text-slate-900 dark:text-zinc-50 shadow-xs ring-1 ring-black/5 dark:ring-white/10'
                    : 'text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-zinc-200'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{label}</span>
              </button>
            );
          })}
        </div>

        <button
          type="button"
          onClick={() => {
            refreshOverviewAndProcs();
            refreshServices();
            if (section === 'files') refreshJunk();
            if (section === 'whitelist') refreshWhitelist();
          }}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-zinc-300 hover:bg-slate-50 dark:hover:bg-zinc-800 transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          刷新探测
        </button>
      </div>

      {/* 1. 进程霸权台 */}
      {section === 'processes' && (
        <div className="rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900/80 p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="relative flex-1 min-w-[220px] max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 dark:text-zinc-500" />
              <input
                type="text"
                value={procSearch}
                onChange={(e) => setProcSearch(e.target.value)}
                placeholder="搜索进程名、路径或防护标签…"
                className="w-full rounded-lg border border-slate-200/80 dark:border-white/10 bg-slate-50 dark:bg-zinc-950/60 pl-9 pr-3 py-1.5 text-xs text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 dark:placeholder:text-zinc-500 focus:outline-none focus:border-indigo-500/50"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {(
                [
                  ['all', '全部'],
                  ['controllable', '可压榨大户'],
                  ['frozen', '已冻结'],
                  ['protected', '受保护白名单'],
                ] as Array<[ProcessFilterMode, string]>
              ).map(([fk, fl]) => (
                <button
                  key={fk}
                  type="button"
                  onClick={() => setProcFilter(fk)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium border transition-colors ${
                    procFilter === fk
                      ? 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 border-indigo-500/30'
                      : 'bg-transparent text-slate-600 dark:text-zinc-400 border-slate-200/80 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-zinc-800'
                  }`}
                >
                  {fl}
                </button>
              ))}

              <select
                value={procSort}
                onChange={(e) => setProcSort(e.target.value as ProcessSortMode)}
                className="rounded-lg border border-slate-200/80 dark:border-white/10 bg-slate-50 dark:bg-zinc-950/60 px-2.5 py-1 text-xs text-slate-700 dark:text-zinc-300 focus:outline-none"
              >
                <option value="memory">按内存占用排序</option>
                <option value="cpu">按 CPU 占用排序</option>
                <option value="name">按名称排序</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200/80 dark:border-white/[0.08] text-[11px] font-medium uppercase tracking-wider text-slate-400 dark:text-zinc-500">
                  <th className="py-2.5 pr-4">进程聚合名 / 实例</th>
                  <th className="py-2.5 px-3">物理内存</th>
                  <th className="py-2.5 px-3">CPU</th>
                  <th className="py-2.5 px-3">调度与护盾状态</th>
                  <th className="py-2.5 pl-3 text-right">治理操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-white/[0.06] text-xs">
                {visibleProcesses.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-10 text-center text-slate-400 dark:text-zinc-500">
                      未匹配到符合条件的进程组
                    </td>
                  </tr>
                ) : (
                  visibleProcesses.map((proc) => (
                    <tr
                      key={proc.name}
                      className="hover:bg-slate-50/80 dark:hover:bg-white/[0.02] transition-colors"
                    >
                      <td className="py-2.5 pr-4">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-slate-900 dark:text-zinc-100">
                            {proc.name}
                          </span>
                          {proc.count > 1 && (
                            <span className="rounded-md bg-slate-100 dark:bg-zinc-800 px-1.5 py-0.5 text-[10px] font-mono tabular-nums text-slate-500 dark:text-zinc-400">
                              ×{proc.count}
                            </span>
                          )}
                        </div>
                        {proc.exePath && (
                          <div className="mt-0.5 text-[11px] text-slate-400 dark:text-zinc-500 truncate max-w-md">
                            {proc.exePath}
                          </div>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono tabular-nums text-slate-700 dark:text-zinc-200">
                        {formatBytesMb(proc.workingSetMb)}
                      </td>
                      <td className="py-2.5 px-3 font-mono tabular-nums text-slate-600 dark:text-zinc-300">
                        {proc.cpuPercent.toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-3">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span
                            className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium border ${
                              proc.protection === 'proxy'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200/60 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20'
                                : proc.protection === 'antigravity' ||
                                    proc.protection === 'antigravity_tree'
                                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200/60 dark:bg-indigo-500/10 dark:text-indigo-400 dark:border-indigo-500/20'
                                  : proc.protection === 'system' || proc.protection === 'custom'
                                    ? 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-zinc-800 dark:text-zinc-300 dark:border-white/10'
                                    : proc.protection === 'foreground'
                                      ? 'bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-500/10 dark:text-sky-300 dark:border-sky-500/20'
                                      : 'bg-amber-50 text-amber-700 border-amber-200/60 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20'
                            }`}
                          >
                            {proc.protectionLabel}
                          </span>
                          {proc.isFrozen && (
                            <span className="inline-flex items-center gap-0.5 rounded-md bg-sky-500/15 border border-sky-500/25 px-1.5 py-0.5 text-[10px] font-medium text-sky-400">
                              <Snowflake className="h-2.5 w-2.5" />
                              已冻结
                            </span>
                          )}
                          {!proc.isFrozen && proc.state === 'isolated' && (
                            <span className="inline-flex items-center rounded-md bg-zinc-800 border border-white/10 px-1.5 py-0.5 text-[10px] text-zinc-400">
                              已隔离末端核
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-2.5 pl-3 text-right">
                        {!proc.canControl ? (
                          <span className="inline-flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400">
                            <ShieldCheck className="h-3.5 w-3.5" />
                            白名单免杀
                          </span>
                        ) : (
                          <div className="inline-flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              disabled={busyKey === `proc:${proc.name}`}
                              onClick={() =>
                                handleProcessAction(
                                  proc.name,
                                  proc.isFrozen ? 'unfreeze' : 'freeze',
                                )
                              }
                              className={`rounded-md px-2 py-1 text-[11px] font-medium border transition-colors ${
                                proc.isFrozen
                                  ? 'bg-sky-500/20 border-sky-500/30 text-sky-300 hover:bg-sky-500/30'
                                  : 'bg-zinc-800/80 border-white/10 text-zinc-200 hover:border-sky-500/40 hover:text-sky-300'
                              }`}
                              title={proc.isFrozen ? '解冻恢复运行' : '冻结挂起进程（CPU 归零不丢状态）'}
                            >
                              {proc.isFrozen ? '解冻' : '冻结'}
                            </button>
                            <button
                              type="button"
                              disabled={busyKey === `proc:${proc.name}`}
                              onClick={() =>
                                handleProcessAction(
                                  proc.name,
                                  proc.state === 'isolated' ? 'restore' : 'isolate',
                                )
                              }
                              className="rounded-md border border-slate-200/80 dark:border-white/10 px-2 py-1 text-[11px] font-medium text-slate-600 dark:text-zinc-300 hover:border-amber-500/40 hover:text-amber-300 transition-colors"
                            >
                              {proc.state === 'isolated' ? '还原' : '孤立'}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleAddCustomWhitelist(proc.name)}
                              className="rounded-md border border-slate-200/80 dark:border-white/10 px-2 py-1 text-[11px] font-medium text-slate-600 dark:text-zinc-300 hover:border-emerald-500/40 hover:text-emerald-300 transition-colors"
                              title="加入永久自定义白名单"
                            >
                              加白
                            </button>
                            {confirmKillName === proc.name ? (
                              <button
                                type="button"
                                onClick={() => handleProcessAction(proc.name, 'kill')}
                                className="rounded-md bg-rose-600 hover:bg-rose-500 px-2 py-1 text-[11px] font-semibold text-white"
                              >
                                确认结束
                              </button>
                            ) : (
                              <button
                                type="button"
                                onClick={() => setConfirmKillName(proc.name)}
                                className="rounded-md border border-rose-500/25 bg-rose-500/10 hover:bg-rose-500/20 px-2 py-1 text-[11px] font-medium text-rose-400 transition-colors"
                              >
                                结束
                              </button>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 2. 常驻重型服务一键止血 */}
      {section === 'services' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {services.length === 0 ? (
            <div className="md:col-span-2 rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900/80 p-10 text-center text-xs text-slate-400 dark:text-zinc-500">
              当前未探测到需要治理的重型常驻 Windows 服务
            </div>
          ) : (
            services.map((svc) => {
              const isRunning = svc.status === 'running';
              const isAuto = svc.startType === 'auto';
              return (
                <div
                  key={svc.name}
                  className="rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900/80 p-5 flex flex-col justify-between gap-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`h-2 w-2 rounded-full ${
                              isRunning ? 'bg-amber-400 animate-pulse' : 'bg-zinc-500'
                            }`}
                          />
                          <h3 className="text-sm font-semibold text-slate-900 dark:text-zinc-100">
                            {svc.displayName}
                          </h3>
                        </div>
                        <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-500 dark:text-zinc-400 font-mono tabular-nums">
                          <span>{svc.name}</span>
                          <span>·</span>
                          <span>约占 {svc.estMemoryMb} MB</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10.5px] font-medium border ${
                            isRunning
                              ? 'bg-amber-50 text-amber-700 border-amber-200/60 dark:bg-amber-500/10 dark:text-amber-300 dark:border-amber-500/20'
                              : 'bg-emerald-50 text-emerald-700 border-emerald-200/60 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20'
                          }`}
                        >
                          {isRunning ? '运行中' : '已停止'}
                        </span>
                        <span className="rounded-full bg-slate-100 dark:bg-zinc-800 border border-slate-200 dark:border-white/10 px-2 py-0.5 text-[10.5px] text-slate-600 dark:text-zinc-300">
                          {isAuto ? '开机自启' : '手动触发'}
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-600 dark:text-zinc-400 leading-relaxed">
                      {svc.riskNote}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-slate-100 dark:border-white/[0.06]">
                    {svc.recommendedStop && isRunning ? (
                      <span className="text-[11px] font-medium text-amber-500 dark:text-amber-400">
                        💡 推荐日常停用释放内存
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-400 dark:text-zinc-500">
                        可随时无损还原
                      </span>
                    )}

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        disabled={Boolean(busyKey)}
                        onClick={() => handleServiceAction(svc.name, isAuto ? 'manual' : 'auto')}
                        className="rounded-lg border border-slate-200/80 dark:border-white/10 px-2.5 py-1 text-[11px] font-medium text-slate-600 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
                      >
                        {isAuto ? '改设为手动' : '恢复自启'}
                      </button>
                      <button
                        type="button"
                        disabled={Boolean(busyKey)}
                        onClick={() => handleServiceAction(svc.name, isRunning ? 'stop' : 'start')}
                        className={`inline-flex items-center gap-1 rounded-lg px-3 py-1 text-[11px] font-semibold transition-colors ${
                          isRunning
                            ? 'bg-rose-500/15 text-rose-600 dark:text-rose-300 border border-rose-500/25 hover:bg-rose-500/25'
                            : 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border border-emerald-500/25 hover:bg-emerald-500/25'
                        }`}
                      >
                        <Power className="h-3 w-3" />
                        {isRunning ? '立即停止' : '重新启动'}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* 3. 智能缓存清理 + 大文件体积雷达 */}
      {section === 'files' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左栏：分类缓存清理 */}
          <div className="rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900/80 p-6 flex flex-col justify-between gap-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-zinc-100">
                    安全垃圾与开发冗余缓存
                  </h3>
                  <p className="mt-0.5 text-xs text-slate-500 dark:text-zinc-400">
                    默认仅勾选安全目录；浏览器清理仅删媒体 Cache，绝对保留账号登录态。
                  </p>
                </div>
                <button
                  type="button"
                  disabled={busyKey === 'scan_junk'}
                  onClick={refreshJunk}
                  className="rounded-lg border border-slate-200/80 dark:border-white/10 px-2.5 py-1.5 text-xs font-medium text-slate-600 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-zinc-800"
                >
                  {busyKey === 'scan_junk' ? '扫描中…' : '重新扫描'}
                </button>
              </div>

              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {junkList.map((item) => {
                  const checked = selectedJunkIds.has(item.id);
                  return (
                    <label
                      key={item.id}
                      className="flex items-start justify-between gap-3 rounded-xl border border-slate-200/80 dark:border-white/[0.08] bg-slate-50/70 dark:bg-zinc-950/50 p-3 cursor-pointer hover:border-indigo-500/30 transition-colors"
                    >
                      <div className="flex items-start gap-2.5 min-w-0">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => {
                            setSelectedJunkIds((prev) => {
                              const next = new Set(prev);
                              if (next.has(item.id)) next.delete(item.id);
                              else next.add(item.id);
                              return next;
                            });
                          }}
                          className="mt-0.5 rounded border-zinc-600 accent-indigo-600"
                        />
                        <div className="min-w-0">
                          <div className="text-xs font-semibold text-slate-900 dark:text-zinc-100">
                            {item.name}
                          </div>
                          <div className="mt-0.5 text-[11px] text-slate-500 dark:text-zinc-400">
                            {item.description}
                          </div>
                          <div className="mt-0.5 text-[10.5px] font-mono text-slate-400 dark:text-zinc-500 truncate">
                            {item.path}
                          </div>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-xs font-bold font-mono tabular-nums text-slate-800 dark:text-zinc-100">
                          {formatBytesMb(item.sizeMb)}
                        </div>
                        <div className="text-[10.5px] text-slate-400 dark:text-zinc-500 tabular-nums">
                          {item.fileCount} 项
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-white/[0.06]">
              <span className="text-xs text-slate-500 dark:text-zinc-400 tabular-nums">
                已选预计释放：<strong className="text-slate-900 dark:text-zinc-100">{formatBytesMb(selectedJunkTotalMb)}</strong>
              </span>
              <button
                type="button"
                disabled={selectedJunkIds.size === 0 || Boolean(busyKey)}
                onClick={handleCleanJunk}
                className="inline-flex items-center gap-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 px-4 py-2 text-xs font-semibold text-white disabled:opacity-40 transition-colors"
              >
                <Trash2 className="h-3.5 w-3.5" />
                {busyKey === 'clean_junk' ? '清理中…' : '一键安全清理'}
              </button>
            </div>
          </div>

          {/* 右栏：大文件与目录雷达 */}
          <div className="rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900/80 p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-zinc-100">
                  磁盘大文件与体积排行雷达
                </h3>
                <p className="mt-0.5 text-xs text-slate-500 dark:text-zinc-400">
                  所有大文件删除默认移入系统回收站（FOF_ALLOWUNDO），防误删兜底。
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <input
                type="text"
                value={scanRootInput}
                onChange={(e) => setScanRootInput(e.target.value)}
                placeholder="输入扫描目录（默认用户主目录）"
                className="flex-1 min-w-[180px] rounded-lg border border-slate-200/80 dark:border-white/10 bg-slate-50 dark:bg-zinc-950/60 px-3 py-1.5 text-xs text-slate-900 dark:text-zinc-100 focus:outline-none focus:border-indigo-500/50"
              />
              <select
                value={minFileMb}
                onChange={(e) => setMinFileMb(Number(e.target.value))}
                className="rounded-lg border border-slate-200/80 dark:border-white/10 bg-slate-50 dark:bg-zinc-950/60 px-2.5 py-1.5 text-xs text-slate-700 dark:text-zinc-300"
              >
                <option value={50}>≥ 50 MB</option>
                <option value={100}>≥ 100 MB</option>
                <option value={300}>≥ 300 MB</option>
              </select>
              <button
                type="button"
                disabled={busyKey === 'scan_large'}
                onClick={() => refreshLargeFiles()}
                className="rounded-lg bg-indigo-600 hover:bg-indigo-500 px-3 py-1.5 text-xs font-semibold text-white transition-colors"
              >
                {busyKey === 'scan_large' ? '扫描中…' : '扫描体积'}
              </button>
            </div>

            {/* 占空间子目录条 */}
            {largeScan && largeScan.directories.length > 0 && (
              <div className="space-y-1.5">
                <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400 dark:text-zinc-500">
                  占用前 6 子目录（总扫描 {formatBytesMb(largeScan.totalScannedMb)}）
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {largeScan.directories.slice(0, 6).map((dir) => (
                    <div
                      key={dir.path}
                      className="rounded-lg border border-slate-200/80 dark:border-white/[0.06] bg-slate-50/70 dark:bg-zinc-950/50 px-2.5 py-2 text-xs"
                    >
                      <div className="flex items-center justify-between gap-1">
                        <button
                          type="button"
                          onClick={() => handleFileAction(dir.path, 'reveal')}
                          className="font-medium text-slate-800 dark:text-zinc-200 hover:text-indigo-400 truncate text-left"
                          title={dir.path}
                        >
                          {dir.name}
                        </button>
                        <span className="font-mono tabular-nums text-[11px] text-slate-500 dark:text-zinc-400 shrink-0">
                          {formatBytesMb(dir.sizeMb)}
                        </span>
                      </div>
                      <div className="mt-1.5 h-1 w-full rounded-full bg-slate-200 dark:bg-zinc-800 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-indigo-500"
                          style={{ width: `${Math.min(100, dir.percent)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top 大文件清单 */}
            <div className="space-y-1.5 max-h-[240px] overflow-y-auto pr-1">
              {!largeScan || largeScan.files.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-400 dark:text-zinc-500">
                  {busyKey === 'scan_large' ? '正在遍历统计文件体积…' : `该目录下未发现超过 ${minFileMb} MB 的大文件`}
                </div>
              ) : (
                largeScan.files.map((file) => (
                  <div
                    key={file.path}
                    className="flex items-center justify-between gap-3 rounded-lg border border-slate-200/80 dark:border-white/[0.06] bg-slate-50/70 dark:bg-zinc-950/50 px-3 py-2 text-xs"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5">
                        <span className="truncate font-medium text-slate-900 dark:text-zinc-100">
                          {file.name}
                        </span>
                        {file.ext && (
                          <span className="rounded bg-zinc-200/80 dark:bg-zinc-800 px-1 py-0.5 text-[9.5px] font-mono text-slate-600 dark:text-zinc-400">
                            {file.ext}
                          </span>
                        )}
                      </div>
                      <div className="mt-0.5 text-[10.5px] text-slate-400 dark:text-zinc-500 truncate">
                        {file.path}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="font-mono font-semibold tabular-nums text-amber-600 dark:text-amber-300">
                        {formatBytesMb(file.sizeMb)}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleFileAction(file.path, 'reveal')}
                        className="p-1 rounded-md hover:bg-slate-200 dark:hover:bg-zinc-800 text-slate-500 dark:text-zinc-400"
                        title="在资源管理器中定位"
                      >
                        <FolderOpen className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        disabled={busyKey === `file:${file.path}`}
                        onClick={() => handleFileAction(file.path, 'trash')}
                        className="p-1 rounded-md hover:bg-rose-500/20 text-rose-500 dark:text-rose-400"
                        title="安全移入系统回收站"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* 4. 神圣白名单与进程树保护管理 */}
      {section === 'whitelist' && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900/80 p-6 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-zinc-100">
                自定义进程免疫白名单
              </h3>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-zinc-400">
                加入白名单的进程（如游戏、直播推流 OBS、音乐播放器等）将免疫后台隔离、冻结与内存修剪，并自动享有全核心正常调度。
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <input
                type="text"
                value={customWhitelistInput}
                onChange={(e) => setCustomWhitelistInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddWhitelistInput();
                }}
                placeholder="输入进程名（多个可用逗号或空格分隔，例如 cs2.exe, obs64.exe）"
                className="flex-1 min-w-[240px] rounded-lg border border-slate-200/80 dark:border-white/10 bg-slate-50 dark:bg-zinc-950/60 px-3 py-2 text-xs text-slate-900 dark:text-zinc-100 focus:outline-none focus:border-emerald-500/50"
              />
              <button
                type="button"
                onClick={handleAddWhitelistInput}
                className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-xs font-semibold text-white transition-colors"
              >
                <Plus className="h-3.5 w-3.5" />
                加入白名单
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              {!whitelist || whitelist.custom.length === 0 ? (
                <span className="text-xs text-slate-400 dark:text-zinc-500">
                  暂无自定义进程，可在下方输入或在「进程霸权台」中一键加白。
                </span>
              ) : (
                whitelist.custom.map((item) => (
                  <span
                    key={item}
                    className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-300"
                  >
                    {item}
                    <button
                      type="button"
                      onClick={() => handleRemoveCustomWhitelist(item)}
                      className="hover:text-rose-400"
                      title="移除"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900/80 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                  🛡️ 代理网络免杀（硬保护）
                </span>
                <span className="text-[11px] text-slate-400 dark:text-zinc-500 tabular-nums">
                  {whitelist?.proxy.length ?? 0} 项
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {(whitelist?.proxy ?? []).map((p) => (
                  <span
                    key={p}
                    className="rounded-md bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[11px] font-mono text-emerald-700 dark:text-emerald-300"
                  >
                    {p}
                  </span>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900/80 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                  🤖 Antigravity 生态（含进程树）
                </span>
                <span className="text-[11px] text-indigo-400 tabular-nums">
                  动态子树 {whitelist?.dynamicTreeCount ?? 0} 个
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-zinc-400">
                仅由 Antigravity / Studio 拉起的子进程（如自身 msedgewebview2 / node）自动继承免杀；无关系统搜索拉起的 WebView2 正常压制。
              </p>
              <div className="flex flex-wrap gap-1.5">
                {(whitelist?.antigravity ?? []).map((a) => (
                  <span
                    key={a}
                    className="rounded-md bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 text-[11px] font-mono text-indigo-700 dark:text-indigo-300"
                  >
                    {a}
                  </span>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white dark:bg-zinc-900/80 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700 dark:text-zinc-200">
                  ⚙️ Windows 内核护盾
                </span>
                <span className="text-[11px] text-slate-400 dark:text-zinc-500 tabular-nums">
                  {whitelist?.system.length ?? 0} 项
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto">
                {(whitelist?.system ?? []).map((s) => (
                  <span
                    key={s}
                    className="rounded-md bg-slate-100 dark:bg-zinc-800 border border-slate-200 dark:border-white/10 px-2 py-0.5 text-[11px] font-mono text-slate-600 dark:text-zinc-300"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
