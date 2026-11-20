import { invoke } from '@tauri-apps/api/core';
import { isTauri } from '../utils/env';
import type {
  CleanResult,
  FileControlAction,
  JunkCategoryItem,
  LargeFileScanResult,
  MemoryBoostResult,
  OptimizerActionResult,
  OptimizerOverview,
  ProcessControlAction,
  ProcessGroupItem,
  ServiceControlAction,
  ServiceItem,
  WhitelistSnapshot,
} from '../types/optimizer';

let previewOverview: OptimizerOverview = {
  cpuPercent: 18.4,
  memTotalMb: 15616,
  memUsedMb: 11776,
  memAvailableMb: 3840,
  memPercent: 75.4,
  commitTotalMb: 22528,
  commitUsedMb: 17971,
  commitPercent: 79.8,
  timerResolutionMs: 15.625,
  menuShowDelayMs: 400,
  isElevated: false,
  isWindows: true,
  logicalCpus: 16,
  exileCoresLabel: 'CPU 14-15 (腾空 CPU 0-13)',
  ruthlessEnabled: false,
  foregroundProcess: 'Antigravity.exe',
  foregroundPid: 15224,
  throttledCount: 0,
  frozenCount: 0,
  protectedCount: 46,
  accessDeniedCount: 0,
  runningHeavyServices: 5,
};

let previewProcesses: ProcessGroupItem[] = [
  {
    name: 'Tabbit Browser.exe',
    count: 20,
    pids: [20964, 18476, 25800],
    workingSetMb: 1937.8,
    privateMb: 1316.3,
    cpuPercent: 11.6,
    protection: 'none',
    protectionLabel: '可压榨后台',
    state: 'normal',
    isFrozen: false,
    canControl: true,
    exePath: 'E:\\浏览器\\Tabbit\\Application\\Tabbit Browser.exe',
  },
  {
    name: 'Antigravity.exe',
    count: 20,
    pids: [15224, 16816, 33500],
    workingSetMb: 1827.6,
    privateMb: 1313.3,
    cpuPercent: 9.2,
    protection: 'antigravity',
    protectionLabel: 'Antigravity 核心',
    state: 'foreground_vip',
    isFrozen: false,
    canControl: false,
    exePath: 'C:\\Users\\QTS的天选\\AppData\\Local\\Programs\\Antigravity\\Antigravity.exe',
  },
  {
    name: 'chrome.exe',
    count: 14,
    pids: [24888, 12496],
    workingSetMb: 628.0,
    privateMb: 814.4,
    cpuPercent: 5.4,
    protection: 'none',
    protectionLabel: '可压榨后台',
    state: 'normal',
    isFrozen: false,
    canControl: true,
    exePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  },
  {
    name: 'language_server.exe',
    count: 1,
    pids: [14284],
    workingSetMb: 440.7,
    privateMb: 458.0,
    cpuPercent: 3.1,
    protection: 'antigravity',
    protectionLabel: 'Antigravity 核心',
    state: 'protected',
    isFrozen: false,
    canControl: false,
    exePath: null,
  },
  {
    name: 'FlClash.exe',
    count: 2,
    pids: [13720, 25944],
    workingSetMb: 247.7,
    privateMb: 351.5,
    cpuPercent: 1.8,
    protection: 'proxy',
    protectionLabel: '代理隧道免杀',
    state: 'protected',
    isFrozen: false,
    canControl: false,
    exePath: 'C:\\Program Files\\FlClash\\FlClash.exe',
  },
  {
    name: 'ArmouryCrate.DenoiseAI.exe',
    count: 1,
    pids: [14224],
    workingSetMb: 92.4,
    privateMb: 118.0,
    cpuPercent: 4.9,
    protection: 'none',
    protectionLabel: '可压榨后台',
    state: 'normal',
    isFrozen: false,
    canControl: true,
    exePath: null,
  },
  {
    name: 'msedgewebview2.exe (SearchHost)',
    count: 6,
    pids: [19516, 20240],
    workingSetMb: 364.2,
    privateMb: 420.0,
    cpuPercent: 2.3,
    protection: 'none',
    protectionLabel: '可压榨后台',
    state: 'normal',
    isFrozen: false,
    canControl: true,
    exePath: null,
  },
];

let previewServices: ServiceItem[] = [
  {
    name: 'MSSQLSERVER',
    displayName: 'SQL Server 主数据库引擎',
    category: 'database',
    status: 'running',
    startType: 'auto',
    estMemoryMb: 640,
    riskNote: '本地不开发数据库时常驻锁定 600MB+ 内存，停止后立即释放巨额 Commit 压力。',
    recommendedStop: true,
  },
  {
    name: 'SysMain',
    displayName: 'SysMain (Superfetch 预读服务)',
    category: 'windows',
    status: 'running',
    startType: 'auto',
    estMemoryMb: 180,
    riskNote: 'SSD 固态硬盘上长期预读会推高后台磁盘排队与 Standby 缓存占用。',
    recommendedStop: true,
  },
  {
    name: 'WSearch',
    displayName: 'Windows Search 文件索引',
    category: 'windows',
    status: 'running',
    startType: 'auto',
    estMemoryMb: 120,
    riskNote: '后台周期性全盘建索引消耗 I/O 与 CPU。',
    recommendedStop: false,
  },
  {
    name: 'ROG Live Service',
    displayName: 'ROG Live 灯效与同步服务',
    category: 'asus',
    status: 'running',
    startType: 'auto',
    estMemoryMb: 85,
    riskNote: 'ROG 外设灯光与同步守护，关闭后降低后台 CPU 轮询。',
    recommendedStop: true,
  },
  {
    name: 'ArmouryCrateService',
    displayName: '华硕奥创主服务',
    category: 'asus',
    status: 'running',
    startType: 'auto',
    estMemoryMb: 140,
    riskNote: '负责奥创中心硬件配置与灯效。',
    recommendedStop: false,
  },
];

let previewCustomWhitelist: string[] = [];

async function callOpt<T>(
  cmd: string,
  args: Record<string, unknown> = {},
  fallback?: () => T,
): Promise<T> {
  if (!isTauri()) {
    if (fallback) return fallback();
    throw new Error(`当前处于纯浏览器预览模式，无法调用 ${cmd}`);
  }
  return invoke<T>(cmd, args);
}

export const optimizerService = {
  getOverview: () =>
    callOpt<OptimizerOverview>('optimizer_get_overview', {}, () => ({ ...previewOverview })),

  toggleRuthless: (enable: boolean) =>
    callOpt<OptimizerOverview>('optimizer_toggle_ruthless', { enable }, () => {
      previewOverview = {
        ...previewOverview,
        ruthlessEnabled: enable,
        timerResolutionMs: enable ? 0.5 : 15.625,
        menuShowDelayMs: enable ? 0 : previewOverview.menuShowDelayMs,
        throttledCount: enable ? 34 : 0,
      };
      previewProcesses = previewProcesses.map((p) =>
        p.canControl && !p.isFrozen ? { ...p, state: enable ? 'isolated' : 'normal' } : p,
      );
      return { ...previewOverview };
    }),

  boostMemory: () =>
    callOpt<MemoryBoostResult>('optimizer_boost_memory', {}, () => {
      const before = previewOverview.memAvailableMb;
      const gained = 960;
      previewOverview = {
        ...previewOverview,
        memAvailableMb: before + gained,
        memUsedMb: Math.max(2048, previewOverview.memUsedMb - gained),
        memPercent: Number(
          (((previewOverview.memTotalMb - (before + gained)) / previewOverview.memTotalMb) * 100).toFixed(1),
        ),
      };
      return {
        success: true,
        standbyPurged: true,
        trimmedProcesses: 28,
        freedMb: gained,
        beforeAvailMb: before,
        afterAvailMb: before + gained,
        needsElevation: false,
        message: `[预览模拟] 已清空 Standby 缓存死锁并修剪 28 个非白名单后台，净增 ${gained} MB`,
      };
    }),

  listProcesses: () =>
    callOpt<ProcessGroupItem[]>('optimizer_list_processes', {}, () =>
      previewProcesses.map((p) => ({ ...p })),
    ),

  processAction: (processName: string, action: ProcessControlAction) =>
    callOpt<OptimizerActionResult>(
      'optimizer_process_action',
      { processName, action },
      () => {
        if (action === 'kill') {
          previewProcesses = previewProcesses.filter((p) => p.name !== processName);
        } else {
          previewProcesses = previewProcesses.map((p) => {
            if (p.name !== processName) return p;
            if (action === 'freeze') {
              return { ...p, isFrozen: true, state: 'frozen', cpuPercent: 0 };
            }
            if (action === 'unfreeze') {
              return {
                ...p,
                isFrozen: false,
                state: previewOverview.ruthlessEnabled ? 'isolated' : 'normal',
              };
            }
            if (action === 'isolate') return { ...p, isFrozen: false, state: 'isolated' };
            return { ...p, isFrozen: false, state: 'normal' };
          });
        }
        previewOverview = {
          ...previewOverview,
          frozenCount: previewProcesses.filter((p) => p.isFrozen).length,
        };
        return {
          success: true,
          message: `[预览模拟] 已对 ${processName} 执行 ${action}`,
          affected: 1,
          denied: 0,
          needsElevation: false,
        };
      },
    ),

  unfreezeAll: () =>
    callOpt<OptimizerActionResult>('optimizer_unfreeze_all', {}, () => {
      const cnt = previewProcesses.filter((p) => p.isFrozen).length;
      previewProcesses = previewProcesses.map((p) =>
        p.isFrozen ? { ...p, isFrozen: false, state: 'normal' } : p,
      );
      previewOverview = { ...previewOverview, frozenCount: 0 };
      return {
        success: true,
        message: `[预览模拟] 已解冻 ${cnt} 个挂起进程组`,
        affected: cnt,
        denied: 0,
        needsElevation: false,
      };
    }),

  listServices: () =>
    callOpt<ServiceItem[]>('optimizer_list_services', {}, () =>
      previewServices.map((s) => ({ ...s })),
    ),

  serviceAction: (name: string, action: ServiceControlAction) =>
    callOpt<string>('optimizer_service_action', { name, action }, () => {
      previewServices = previewServices.map((s) => {
        if (s.name !== name) return s;
        if (action === 'stop') return { ...s, status: 'stopped' };
        if (action === 'start') return { ...s, status: 'running' };
        if (action === 'manual') return { ...s, startType: 'manual' };
        return { ...s, startType: 'auto' };
      });
      previewOverview = {
        ...previewOverview,
        runningHeavyServices: previewServices.filter((s) => s.status === 'running').length,
      };
      return `[预览模拟] 服务 ${name} 已执行 ${action}`;
    }),

  scanJunk: () =>
    callOpt<JunkCategoryItem[]>('optimizer_scan_junk', {}, () => [
      {
        id: 'user_temp',
        name: '用户临时文件夹 (TEMP)',
        group: 'safe',
        path: 'C:\\Users\\QTS的天选\\AppData\\Local\\Temp',
        sizeMb: 216.2,
        fileCount: 1420,
        defaultChecked: true,
        description: '安装包残余与程序运行临时文件，被占用文件将自动跳过。',
      },
      {
        id: 'crash_dumps',
        name: '程序崩溃转储 (CrashDumps)',
        group: 'safe',
        path: 'C:\\Users\\QTS的天选\\AppData\\Local\\CrashDumps',
        sizeMb: 9.2,
        fileCount: 1,
        defaultChecked: true,
        description: '应用闪退生成的内存转储 .dmp 文件。',
      },
      {
        id: 'chrome_cache',
        name: 'Chrome 网页媒体缓存 (仅 Cache)',
        group: 'browser',
        path: 'C:\\Users\\QTS的天选\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache',
        sizeMb: 373.6,
        fileCount: 2810,
        defaultChecked: false,
        description: '仅清理网页媒体缓存，不触碰 Cookie 与登录态。',
      },
      {
        id: 'cache_codex',
        name: '开发缓存 · codex-runtimes',
        group: 'dev_cache',
        path: 'C:\\Users\\QTS的天选\\.cache\\codex-runtimes',
        sizeMb: 2201.6,
        fileCount: 18500,
        defaultChecked: false,
        description: '多版本 Codex 运行时缓存（按需勾选释放约 2.15GB）。',
      },
      {
        id: 'cache_puppeteer',
        name: '开发缓存 · puppeteer / 浏览器镜像',
        group: 'dev_cache',
        path: 'C:\\Users\\QTS的天选\\.cache\\puppeteer',
        sizeMb: 540.3,
        fileCount: 3100,
        defaultChecked: false,
        description: '无头浏览器测试镜像缓存。',
      },
    ]),

  cleanJunk: (categoryIds: string[]) =>
    callOpt<CleanResult>('optimizer_clean_junk', { categoryIds }, () => ({
      success: true,
      deletedFiles: 1421,
      skippedFiles: 18,
      freedMb: 225.4,
      message: '[预览模拟] 清理完成：删除 1421 个文件，释放 225.4 MB',
    })),

  scanLargeFiles: (rootPath?: string | null, minFileMb = 50) =>
    callOpt<LargeFileScanResult>(
      'optimizer_scan_large_files',
      { rootPath: rootPath ?? null, minFileMb },
      () => ({
        rootPath: rootPath || 'C:\\Users\\QTS的天选',
        totalScannedMb: 12480.5,
        directories: [
          { path: 'C:\\Users\\QTS的天选\\.cache', name: '.cache', sizeMb: 3865.5, percent: 31.0 },
          { path: 'C:\\Users\\QTS的天选\\AppData', name: 'AppData', sizeMb: 5420.0, percent: 43.4 },
          { path: 'C:\\Users\\QTS的天选\\Documents', name: 'Documents', sizeMb: 2140.0, percent: 17.1 },
        ],
        files: [
          {
            path: 'C:\\Users\\QTS的天选\\.cache\\codex-runtimes\\node-pack.tar.gz',
            name: 'node-pack.tar.gz',
            sizeMb: 412.6,
            ext: 'GZ',
            modifiedTs: 1763596800,
          },
        ],
      }),
    ),

  fileAction: (path: string, action: FileControlAction) =>
    callOpt<string>('optimizer_file_action', { path, action }, () =>
      `[预览模拟] 已执行 ${action}: ${path}`,
    ),

  getWhitelist: () =>
    callOpt<WhitelistSnapshot>('optimizer_get_whitelist', {}, () => ({
      system: ['system', 'dwm', 'explorer', 'svchost', 'csrss', 'lsass'],
      proxy: ['flclash', 'flclashcore', 'flclashhelperservice', 'clash', 'mihomo', 'tailscale', 'tailscaled'],
      antigravity: ['antigravity', 'antigravity-tools', 'language_server', 'sidecar-web-server'],
      custom: [...previewCustomWhitelist],
      dynamicTreeCount: 15,
    })),

  updateWhitelist: (items: string[]) =>
    callOpt<WhitelistSnapshot>('optimizer_update_whitelist', { items }, () => {
      previewCustomWhitelist = [...items];
      return {
        system: ['system', 'dwm', 'explorer', 'svchost', 'csrss', 'lsass'],
        proxy: ['flclash', 'flclashcore', 'flclashhelperservice', 'clash', 'mihomo', 'tailscale', 'tailscaled'],
        antigravity: ['antigravity', 'antigravity-tools', 'language_server', 'sidecar-web-server'],
        custom: [...previewCustomWhitelist],
        dynamicTreeCount: 15,
      };
    }),

  relaunchAsAdmin: () =>
    callOpt<boolean>('optimizer_relaunch_as_admin', {}, () => {
      previewOverview = { ...previewOverview, isElevated: true };
      return true;
    }),

  openFullPanel: () =>
    callOpt<void>('optimizer_open_full_panel', {}, () => {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('studio:open-tab', { detail: 'optimizer' }));
      }
    }),
};
