import type { ProcessGroupItem } from '../../types/optimizer';

export type PetHudPanelMode = 'none' | 'quota' | 'music' | 'boost';
export type ProcessFilterMode = 'all' | 'controllable' | 'frozen' | 'protected';
export type ProcessSortMode = 'memory' | 'cpu' | 'name';

/**
 * 统一将 MB 格式化为紧凑等宽友好字符串
 */
export function formatBytesMb(mb: number): string {
  if (!Number.isFinite(mb) || mb <= 0) return '0 MB';
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(2)} GB`;
  }
  if (mb >= 100) {
    return `${Math.round(mb)} MB`;
  }
  return `${mb.toFixed(1)} MB`;
}

/**
 * 判定当前系统内存 + Commit 提交内存的真实压力等级
 */
export function classifyCommitPressure(
  commitPercent: number,
  memPercent: number,
): 'healthy' | 'elevated' | 'critical' {
  const peak = Math.max(commitPercent, memPercent);
  if (peak >= 80) return 'critical';
  if (peak >= 65) return 'elevated';
  return 'healthy';
}

/**
 * 按筛选态、关键词与排序维度过滤进程分组
 */
export function filterAndSortProcessGroups(
  list: ProcessGroupItem[],
  filter: ProcessFilterMode,
  search: string,
  sortBy: ProcessSortMode,
): ProcessGroupItem[] {
  const query = search.trim().toLowerCase();

  const filtered = list.filter((item) => {
    if (filter === 'controllable' && !item.canControl) return false;
    if (filter === 'frozen' && !item.isFrozen) return false;
    if (filter === 'protected' && item.canControl) return false;

    if (!query) return true;
    return (
      item.name.toLowerCase().includes(query) ||
      item.protectionLabel.toLowerCase().includes(query) ||
      (item.exePath && item.exePath.toLowerCase().includes(query))
    );
  });

  const sorted = [...filtered];
  sorted.sort((a, b) => {
    if (sortBy === 'cpu') {
      if (b.cpuPercent !== a.cpuPercent) return b.cpuPercent - a.cpuPercent;
      return b.workingSetMb - a.workingSetMb;
    }
    if (sortBy === 'name') {
      return a.name.localeCompare(b.name, 'en', { sensitivity: 'base' });
    }
    return b.workingSetMb - a.workingSetMb;
  });

  return sorted;
}

/**
 * 规范化用户输入的白名单进程列表（按逗号/换行/空格切分、小写、去 .exe、去重）
 */
export function normalizeCustomWhitelistInput(raw: string): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const part of raw.split(/[\n,;，；\s]+/)) {
    const clean = part.trim().toLowerCase().replace(/\.exe$/i, '');
    if (clean && !seen.has(clean)) {
      seen.add(clean);
      out.push(clean);
    }
  }
  return out;
}

/**
 * 根据桌宠展开状态动态计算窗口安全逻辑高度
 */
export function resolvePetHudHeight(
  hudVisible: boolean,
  panelMode: PetHudPanelMode,
  pickerOpen: boolean,
): number {
  if (!hudVisible || (panelMode === 'none' && !pickerOpen)) {
    return 420;
  }
  if (panelMode === 'boost') {
    return 640;
  }
  return 586;
}
