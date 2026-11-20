import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowUpRight,
  Cpu,
  Flame,
  HardDrive,
  Lock,
  Power,
  RefreshCw,
  ShieldCheck,
  Snowflake,
  Sparkles,
  Trash2,
  Zap,
} from 'lucide-react';
import { optimizerService } from '../../services/optimizerService';
import type {
  JunkCategoryItem,
  OptimizerOverview,
  ProcessGroupItem,
  ServiceItem,
} from '../../types/optimizer';
import { classifyCommitPressure, formatBytesMb } from './optimizerLogic';

interface PetOptimizerHudProps {
  onBoostFeedback?: (message: string, mood?: string) => void;
}

type HudSubTab = 'squeeze' | 'govern' | 'clean';
type GovernSubMode = 'processes' | 'services';

export const PetOptimizerHud: React.FC<PetOptimizerHudProps> = ({ onBoostFeedback }) => {
  const [subTab, setSubTab] = useState<HudSubTab>('squeeze');
  const [governMode, setGovernMode] = useState<GovernSubMode>('processes');
  const [overview, setOverview] = useState<OptimizerOverview | null>(null);
  const [processes, setProcesses] = useState<ProcessGroupItem[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [junkList, setJunkList] = useState<JunkCategoryItem[]>([]);
  const [selectedJunkIds, setSelectedJunkIds] = useState<Set<string>>(new Set());
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [inlineNotice, setInlineNotice] = useState<string>('');

  const loadOverviewAndQuickData = useCallback(async () => {
    try {
      const ov = await optimizerService.getOverview();
      setOverview(ov);
    } catch {
      // 静默容错
    }
  }, []);

  const loadGovernData = useCallback(async () => {
    try {
      const [procs, svcs] = await Promise.all([
        optimizerService.listProcesses(),
        optimizerService.listServices(),
      ]);
      setProcesses(procs);
      setServices(svcs);
    } catch {
      // 静默容错
    }
  }, []);

  const loadJunkData = useCallback(async () => {
    setBusyAction('scan_junk');
    try {
      const list = await optimizerService.scanJunk();
      setJunkList(list);
      setSelectedJunkIds(new Set(list.filter((i) => i.defaultChecked).map((i) => i.id)));
    } catch (err) {
      setInlineNotice(String(err));
    } finally {
      setBusyAction(null);
    }
  }, []);

  useEffect(() => {
    loadOverviewAndQuickData();
    loadGovernData();
    const timer = window.setInterval(loadOverviewAndQuickData, 2500);
    return () => window.clearInterval(timer);
  }, [loadOverviewAndQuickData, loadGovernData]);

  useEffect(() => {
    if (subTab === 'govern') {
      loadGovernData();
    } else if (subTab === 'clean' && junkList.length === 0) {
      loadJunkData();
    }
  }, [subTab, junkList.length, loadGovernData, loadJunkData]);

  const handleToggleRuthless = async () => {
    if (busyAction) return;
    const next = !(overview?.ruthlessEnabled ?? false);
    setBusyAction('ruthless');
    try {
      const updated = await optimizerService.toggleRuthless(next);
      setOverview(updated);
      const msg = next
        ? `极客霸权已锁定：0.5ms 时钟就绪，已将 ${updated.throttledCount} 个后台驱逐至 ${updated.exileCoresLabel}`
        : '已退出极客霸权模式并平滑恢复默认调度';
      setInlineNotice(msg);
      onBoostFeedback?.(msg, next ? '⚡' : '✨');
      loadGovernData();
    } catch (err) {
      setInlineNotice(String(err));
    } finally {
      setBusyAction(null);
    }
  };

  const handleBoostMemory = async () => {
    if (busyAction) return;
    setBusyAction('memory');
    try {
      const res = await optimizerService.boostMemory();
      setInlineNotice(res.message);
      onBoostFeedback?.(res.message, '💨');
      await loadOverviewAndQuickData();
    } catch (err) {
      setInlineNotice(String(err));
    } finally {
      setBusyAction(null);
    }
  };

  const handleFreezeHeavyBrowsers = async () => {
    if (busyAction) return;
    setBusyAction('freeze_browsers');
    try {
      const targets = processes.filter(
        (p) =>
          p.canControl &&
          !p.isFrozen &&
          (p.name.toLowerCase().includes('tabbit') || p.name.toLowerCase().includes('chrome')),
      );
      if (targets.length === 0) {
        const res = await optimizerService.unfreezeAll();
        setInlineNotice(res.affected > 0 ? res.message : '当前无可冻结的第三方高耗浏览器后台');
      } else {
        let totalAffected = 0;
        for (const item of targets) {
          const r = await optimizerService.processAction(item.name, 'freeze');
          totalAffected += r.affected;
        }
        const msg = `已冻结 ${targets.length} 组高耗浏览器（共 ${totalAffected} 个进程），CPU 瞬间归零不丢页面`;
        setInlineNotice(msg);
        onBoostFeedback?.(msg, '❄️');
      }
      await Promise.all([loadOverviewAndQuickData(), loadGovernData()]);
    } catch (err) {
      setInlineNotice(String(err));
    } finally {
      setBusyAction(null);
    }
  };

  const handleProcessAction = async (
    item: ProcessGroupItem,
    action: 'freeze' | 'unfreeze' | 'isolate',
  ) => {
    setBusyAction(`proc:${item.name}`);
    try {
      const res = await optimizerService.processAction(item.name, action);
      setInlineNotice(res.message);
      await Promise.all([loadOverviewAndQuickData(), loadGovernData()]);
    } catch (err) {
      setInlineNotice(String(err));
    } finally {
      setBusyAction(null);
    }
  };

  const handleServiceToggle = async (svc: ServiceItem) => {
    const action = svc.status === 'running' ? 'stop' : 'start';
    setBusyAction(`svc:${svc.name}`);
    try {
      const msg = await optimizerService.serviceAction(svc.name, action);
      setInlineNotice(msg);
      await Promise.all([loadOverviewAndQuickData(), loadGovernData()]);
    } catch (err) {
      setInlineNotice(String(err));
    } finally {
      setBusyAction(null);
    }
  };

  const handleCleanJunk = async () => {
    if (selectedJunkIds.size === 0 || busyAction) return;
    setBusyAction('clean_junk');
    try {
      const res = await optimizerService.cleanJunk(Array.from(selectedJunkIds));
      setInlineNotice(res.message);
      onBoostFeedback?.(res.message, '🧹');
      await loadJunkData();
    } catch (err) {
      setInlineNotice(String(err));
    } finally {
      setBusyAction(null);
    }
  };

  const handleElevate = async () => {
    try {
      await optimizerService.relaunchAsAdmin();
    } catch (err) {
      setInlineNotice(String(err));
    }
  };

  const topControllable = useMemo(
    () => processes.filter((p) => p.canControl).slice(0, 6),
    [processes],
  );

  const selectedJunkMb = useMemo(
    () =>
      junkList
        .filter((j) => selectedJunkIds.has(j.id))
        .reduce((sum, j) => sum + j.sizeMb, 0),
    [junkList, selectedJunkIds],
  );

  const pressure = classifyCommitPressure(
    overview?.commitPercent ?? 0,
    overview?.memPercent ?? 0,
  );
  const timerLow = (overview?.timerResolutionMs ?? 15.6) <= 1.0;

  return (
    <div className="space-y-2.5 text-zinc-100">
      {/* 顶部微遥测条 + 权限徽章 + 全景直达 */}
      <div className="flex items-center justify-between gap-2 text-[10.5px]">
        <div className="flex items-center gap-2 font-mono tabular-nums">
          <span className="inline-flex items-center gap-1 text-zinc-300">
            <Cpu className="w-3 h-3 text-sky-400" />
            {(overview?.cpuPercent ?? 0).toFixed(0)}%
          </span>
          <span
            className={`inline-flex items-center gap-1 ${
              pressure === 'critical'
                ? 'text-rose-400'
                : pressure === 'elevated'
                  ? 'text-amber-300'
                  : 'text-emerald-400'
            }`}
            title={`物理可用 ${formatBytesMb(overview?.memAvailableMb ?? 0)} | 虚拟提交 ${(overview?.commitPercent ?? 0).toFixed(0)}%`}
          >
            余 {formatBytesMb(overview?.memAvailableMb ?? 0)}
          </span>
          <span
            className={`rounded-full px-1.5 py-0.5 text-[9.5px] border ${
              timerLow
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25'
                : 'bg-zinc-800 text-zinc-400 border-white/10'
            }`}
          >
            {(overview?.timerResolutionMs ?? 15.625).toFixed(2)}ms
          </span>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {overview && !overview.isElevated && overview.isWindows && (
            <button
              type="button"
              onClick={handleElevate}
              className="inline-flex items-center gap-0.5 rounded-full bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 px-2 py-0.5 text-[9.5px] font-semibold text-amber-300 transition-colors"
              title="点击以管理员身份重启，解锁 Standby 内存清空、服务启停与高权进程压制"
            >
              <Lock className="w-2.5 h-2.5" />
              提权
            </button>
          )}
          {overview?.isElevated && (
            <span className="inline-flex items-center gap-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/25 px-1.5 py-0.5 text-[9.5px] text-emerald-300">
              <ShieldCheck className="w-2.5 h-2.5" />
              Admin
            </span>
          )}
          <button
            type="button"
            onClick={() => optimizerService.openFullPanel().catch(() => {})}
            className="inline-flex items-center gap-0.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/10 px-2 py-0.5 text-[9.5px] font-semibold text-zinc-200 transition-colors"
            title="打开 Studio 全景压榨与文件清理控制台"
          >
            全景
            <ArrowUpRight className="w-2.5 h-2.5" />
          </button>
        </div>
      </div>

      {/* Hero 极客霸权主控胶囊 */}
      <div
        className={`rounded-xl border px-3 py-2 transition-all duration-200 ${
          overview?.ruthlessEnabled
            ? 'bg-emerald-500/10 border-emerald-400/35 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]'
            : 'bg-zinc-900/80 border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]'
        }`}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span
                className={`h-2 w-2 rounded-full ${
                  overview?.ruthlessEnabled
                    ? 'bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]'
                    : 'bg-zinc-500'
                }`}
              />
              <span className="text-[11.5px] font-semibold text-zinc-100 truncate">
                {overview?.ruthlessEnabled ? '极客霸权守护中' : '极客霸权压榨模式'}
              </span>
            </div>
            <div className="mt-0.5 text-[10px] text-zinc-400 truncate">
              {overview?.ruthlessEnabled
                ? `已隔离 ${overview.throttledCount} 后台至末端核 · 白名单全速免杀`
                : '独占 CPU 0-13 · 0.5ms 时钟 · 代理与核心树免杀'}
            </div>
          </div>

          <button
            type="button"
            disabled={busyAction === 'ruthless'}
            onClick={handleToggleRuthless}
            className={`shrink-0 inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10.5px] font-semibold transition-all active:scale-[0.97] ${
              overview?.ruthlessEnabled
                ? 'bg-emerald-500 text-zinc-950 hover:bg-emerald-400'
                : 'bg-sky-500/25 text-sky-200 border border-sky-400/40 hover:bg-sky-500/35'
            }`}
          >
            <Flame className="w-3 h-3" />
            {busyAction === 'ruthless'
              ? '调度中'
              : overview?.ruthlessEnabled
                ? '已开启'
                : '一键压榨'}
          </button>
        </div>
      </div>

      {/* 三合一紧凑分段器 */}
      <div className="grid grid-cols-3 gap-1 rounded-lg bg-zinc-950/80 p-0.5 border border-white/[0.08]">
        {(
          [
            ['squeeze', '压榨'],
            ['govern', '治理'],
            ['clean', '清理'],
          ] as Array<[HudSubTab, string]>
        ).map(([k, label]) => (
          <button
            key={k}
            type="button"
            onClick={() => setSubTab(k)}
            className={`rounded-md py-1 text-[10.5px] font-semibold transition-colors ${
              subTab === k
                ? 'bg-zinc-800 text-white shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* 子视图 1：极速压榨面板 */}
      {subTab === 'squeeze' && (
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-1.5">
            <button
              type="button"
              disabled={Boolean(busyAction)}
              onClick={handleBoostMemory}
              className="flex items-center justify-center gap-1.5 rounded-lg bg-zinc-800/80 hover:bg-zinc-700/80 border border-white/10 px-2 py-1.5 text-[10.5px] font-semibold text-sky-300 transition-all active:scale-[0.98]"
            >
              <Zap className="w-3 h-3" />
              {busyAction === 'memory' ? '释放中…' : '释放 Standby'}
            </button>
            <button
              type="button"
              disabled={Boolean(busyAction)}
              onClick={handleFreezeHeavyBrowsers}
              className="flex items-center justify-center gap-1.5 rounded-lg bg-zinc-800/80 hover:bg-zinc-700/80 border border-white/10 px-2 py-1.5 text-[10.5px] font-semibold text-indigo-300 transition-all active:scale-[0.98]"
            >
              <Snowflake className="w-3 h-3" />
              {(overview?.frozenCount ?? 0) > 0 ? '全部解冻' : '冻结闲置浏览器'}
            </button>
          </div>

          <div className="grid grid-cols-2 gap-1.5 text-[10px]">
            <div className="rounded-lg bg-zinc-900/70 border border-white/[0.06] px-2.5 py-1.5">
              <div className="text-zinc-500">当前前台 VIP</div>
              <div className="mt-0.5 font-semibold text-zinc-200 truncate">
                {overview?.foregroundProcess || '自动追踪中'}
              </div>
            </div>
            <div className="rounded-lg bg-zinc-900/70 border border-white/[0.06] px-2.5 py-1.5 tabular-nums">
              <div className="text-zinc-500">提交内存 / 重服务</div>
              <div className="mt-0.5 font-semibold text-zinc-200">
                {(overview?.commitPercent ?? 0).toFixed(0)}% · {overview?.runningHeavyServices ?? 0} 运行中
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 子视图 2：进程 Top 与重服务一键止血 */}
      {subTab === 'govern' && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[10px]">
            <div className="inline-flex gap-1">
              <button
                type="button"
                onClick={() => setGovernMode('processes')}
                className={`px-2 py-0.5 rounded-md font-medium ${
                  governMode === 'processes'
                    ? 'bg-sky-500/20 text-sky-300 border border-sky-400/30'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                可压榨大户 ({topControllable.length})
              </button>
              <button
                type="button"
                onClick={() => setGovernMode('services')}
                className={`px-2 py-0.5 rounded-md font-medium ${
                  governMode === 'services'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-400/30'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                重型服务 ({services.length})
              </button>
            </div>
            <button
              type="button"
              onClick={loadGovernData}
              className="p-1 rounded-md hover:bg-white/10 text-zinc-400 hover:text-white"
              title="刷新列表"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>

          <div className="max-h-[132px] overflow-y-auto space-y-1 pr-0.5">
            {governMode === 'processes' ? (
              topControllable.length === 0 ? (
                <div className="py-4 text-center text-[10.5px] text-zinc-500">
                  暂无高耗非白名单后台进程
                </div>
              ) : (
                topControllable.map((proc) => (
                  <div
                    key={proc.name}
                    className="flex items-center justify-between gap-2 rounded-lg bg-zinc-900/75 border border-white/[0.06] px-2 py-1 text-[10.5px]"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1">
                        <span className="truncate font-medium text-zinc-200">{proc.name}</span>
                        {proc.count > 1 && (
                          <span className="text-[9px] text-zinc-500 font-mono">×{proc.count}</span>
                        )}
                      </div>
                      <div className="text-[9.5px] text-zinc-400 font-mono tabular-nums">
                        {formatBytesMb(proc.workingSetMb)} · {proc.isFrozen ? '已冻结' : proc.state === 'isolated' ? '已隔离' : '普通'}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        type="button"
                        disabled={busyAction === `proc:${proc.name}`}
                        onClick={() =>
                          handleProcessAction(proc, proc.isFrozen ? 'unfreeze' : 'freeze')
                        }
                        className={`rounded-md px-1.5 py-0.5 text-[9.5px] font-semibold transition-colors ${
                          proc.isFrozen
                            ? 'bg-sky-500/25 text-sky-300 hover:bg-sky-500/35'
                            : 'bg-white/10 text-zinc-300 hover:bg-indigo-500/30 hover:text-indigo-200'
                        }`}
                        title={proc.isFrozen ? '解冻恢复' : '冻结 CPU 归零'}
                      >
                        {proc.isFrozen ? '解冻' : '冻结'}
                      </button>
                      {!proc.isFrozen && proc.state !== 'isolated' && (
                        <button
                          type="button"
                          disabled={busyAction === `proc:${proc.name}`}
                          onClick={() => handleProcessAction(proc, 'isolate')}
                          className="rounded-md bg-white/10 hover:bg-amber-500/30 px-1.5 py-0.5 text-[9.5px] font-semibold text-zinc-300 hover:text-amber-200"
                          title="压制至末端小核"
                        >
                          压制
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )
            ) : services.length === 0 ? (
              <div className="py-4 text-center text-[10.5px] text-zinc-500">
                未发现重型常驻服务
              </div>
            ) : (
              services.slice(0, 8).map((svc) => {
                const running = svc.status === 'running';
                return (
                  <div
                    key={svc.name}
                    className="flex items-center justify-between gap-2 rounded-lg bg-zinc-900/75 border border-white/[0.06] px-2 py-1 text-[10.5px]"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                            running ? 'bg-amber-400' : 'bg-zinc-600'
                          }`}
                        />
                        <span className="truncate font-medium text-zinc-200">
                          {svc.displayName}
                        </span>
                      </div>
                      <div className="text-[9.5px] text-zinc-500 font-mono tabular-nums">
                        {svc.name} · 约 {svc.estMemoryMb} MB
                      </div>
                    </div>
                    <button
                      type="button"
                      disabled={busyAction === `svc:${svc.name}`}
                      onClick={() => handleServiceToggle(svc)}
                      className={`shrink-0 inline-flex items-center gap-0.5 rounded-md px-2 py-0.5 text-[9.5px] font-semibold transition-colors ${
                        running
                          ? 'bg-rose-500/20 text-rose-300 hover:bg-rose-500/35'
                          : 'bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/30'
                      }`}
                    >
                      <Power className="w-2.5 h-2.5" />
                      {running ? '停止' : '启动'}
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* 子视图 3：安全缓存清理 */}
      {subTab === 'clean' && (
        <div className="space-y-1.5">
          <div className="max-h-[116px] overflow-y-auto space-y-1 pr-0.5">
            {junkList.length === 0 ? (
              <div className="py-4 text-center text-[10.5px] text-zinc-500">
                {busyAction === 'scan_junk' ? '正在扫描缓存目录…' : '暂无可清理缓存'}
              </div>
            ) : (
              junkList.map((item) => {
                const checked = selectedJunkIds.has(item.id);
                return (
                  <label
                    key={item.id}
                    className="flex items-center justify-between gap-2 rounded-lg bg-zinc-900/75 border border-white/[0.06] px-2 py-1 text-[10.5px] cursor-pointer hover:border-white/15"
                  >
                    <div className="flex items-center gap-1.5 min-w-0">
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
                        className="rounded border-zinc-600 bg-zinc-800 accent-sky-500"
                      />
                      <span className="truncate text-zinc-200">{item.name}</span>
                    </div>
                    <span className="shrink-0 font-mono text-[10px] text-zinc-400 tabular-nums">
                      {formatBytesMb(item.sizeMb)}
                    </span>
                  </label>
                );
              })
            )}
          </div>

          <div className="flex items-center justify-between gap-2 pt-0.5">
            <button
              type="button"
              onClick={() => optimizerService.openFullPanel().catch(() => {})}
              className="inline-flex items-center gap-1 text-[10px] text-zinc-400 hover:text-zinc-200"
            >
              <HardDrive className="w-3 h-3" />
              大文件雷达
            </button>
            <button
              type="button"
              disabled={selectedJunkIds.size === 0 || Boolean(busyAction)}
              onClick={handleCleanJunk}
              className="inline-flex items-center gap-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/35 border border-rose-500/30 px-2.5 py-1 text-[10px] font-semibold text-rose-200 disabled:opacity-40 transition-colors"
            >
              <Trash2 className="w-3 h-3" />
              {busyAction === 'clean_junk'
                ? '清理中…'
                : `清理 (${formatBytesMb(selectedJunkMb)})`}
            </button>
          </div>
        </div>
      )}

      {/* 极简状态回执行 */}
      {inlineNotice && (
        <div className="flex items-start gap-1.5 rounded-lg bg-zinc-900/90 border border-white/[0.08] px-2 py-1 text-[10px] text-zinc-300 leading-snug">
          <Sparkles className="w-3 h-3 text-sky-400 shrink-0 mt-0.5" />
          <span className="line-clamp-2">{inlineNotice}</span>
        </div>
      )}
    </div>
  );
};
