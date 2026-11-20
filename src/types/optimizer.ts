export type ProtectionKind =
  | 'system'
  | 'proxy'
  | 'antigravity'
  | 'antigravity_tree'
  | 'custom'
  | 'foreground'
  | 'none';

export type ProcessRuntimeState =
  | 'foreground_vip'
  | 'protected'
  | 'frozen'
  | 'isolated'
  | 'normal';

export interface OptimizerOverview {
  cpuPercent: number;
  memTotalMb: number;
  memUsedMb: number;
  memAvailableMb: number;
  memPercent: number;
  commitTotalMb: number;
  commitUsedMb: number;
  commitPercent: number;
  timerResolutionMs: number;
  menuShowDelayMs: number;
  isElevated: boolean;
  isWindows: boolean;
  logicalCpus: number;
  exileCoresLabel: string;
  ruthlessEnabled: boolean;
  foregroundProcess: string | null;
  foregroundPid: number | null;
  throttledCount: number;
  frozenCount: number;
  protectedCount: number;
  accessDeniedCount: number;
  runningHeavyServices: number;
}

export interface ProcessGroupItem {
  name: string;
  count: number;
  pids: number[];
  workingSetMb: number;
  privateMb: number;
  cpuPercent: number;
  protection: ProtectionKind;
  protectionLabel: string;
  state: ProcessRuntimeState;
  isFrozen: boolean;
  canControl: boolean;
  exePath: string | null;
}

export interface OptimizerActionResult {
  success: boolean;
  message: string;
  affected: number;
  denied: number;
  needsElevation: boolean;
}

export interface MemoryBoostResult {
  success: boolean;
  standbyPurged: boolean;
  trimmedProcesses: number;
  freedMb: number;
  beforeAvailMb: number;
  afterAvailMb: number;
  needsElevation: boolean;
  message: string;
}

export interface ServiceItem {
  name: string;
  displayName: string;
  category: 'database' | 'windows' | 'asus' | string;
  status: 'running' | 'stopped' | 'pending' | string;
  startType: 'auto' | 'manual' | 'disabled' | 'unknown' | string;
  estMemoryMb: number;
  riskNote: string;
  recommendedStop: boolean;
}

export interface JunkCategoryItem {
  id: string;
  name: string;
  group: 'safe' | 'browser' | 'dev_cache' | 'recycle' | string;
  path: string;
  sizeMb: number;
  fileCount: number;
  defaultChecked: boolean;
  description: string;
}

export interface CleanResult {
  success: boolean;
  deletedFiles: number;
  skippedFiles: number;
  freedMb: number;
  message: string;
}

export interface LargeFileEntry {
  path: string;
  name: string;
  sizeMb: number;
  ext: string;
  modifiedTs: number;
}

export interface LargeDirEntry {
  path: string;
  name: string;
  sizeMb: number;
  percent: number;
}

export interface LargeFileScanResult {
  rootPath: string;
  totalScannedMb: number;
  directories: LargeDirEntry[];
  files: LargeFileEntry[];
}

export interface WhitelistSnapshot {
  system: string[];
  proxy: string[];
  antigravity: string[];
  custom: string[];
  dynamicTreeCount: number;
}

export type ProcessControlAction = 'freeze' | 'unfreeze' | 'isolate' | 'restore' | 'kill';
export type ServiceControlAction = 'stop' | 'start' | 'manual' | 'auto';
export type FileControlAction = 'reveal' | 'trash';
