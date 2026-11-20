import {
  classifyCommitPressure,
  filterAndSortProcessGroups,
  formatBytesMb,
  normalizeCustomWhitelistInput,
  resolvePetHudHeight,
} from '../optimizerLogic.ts';
import type { ProcessGroupItem } from '../../../types/optimizer.ts';

let passed = 0;
let failed = 0;

function assertEqual<T>(actual: T, expected: T, msg?: string): void {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) {
    throw new Error(`${msg ? `${msg}: ` : ''}expected ${e}, got ${a}`);
  }
}

function test(description: string, fn: () => void): void {
  try {
    fn();
    passed++;
    console.log(`  PASS: ${description}`);
  } catch (err) {
    failed++;
    console.error(`  FAIL: ${description} — ${(err as Error).message}`);
  }
}

console.log('=== 极客压榨与治理舱纯逻辑单元测试 ===');

test('1. formatBytesMb 在 MB 与 GB 之间准确切换', () => {
  assertEqual(formatBytesMb(0), '0 MB');
  assertEqual(formatBytesMb(-10), '0 MB');
  assertEqual(formatBytesMb(42.34), '42.3 MB');
  assertEqual(formatBytesMb(645.7), '646 MB');
  assertEqual(formatBytesMb(1937.8), '1.89 GB');
});

test('2. classifyCommitPressure 精准识别高提交内存换页风险', () => {
  assertEqual(classifyCommitPressure(50, 55), 'healthy');
  assertEqual(classifyCommitPressure(72, 60), 'elevated');
  assertEqual(classifyCommitPressure(81, 74), 'critical');
  assertEqual(classifyCommitPressure(60, 88), 'critical');
});

test('3. filterAndSortProcessGroups 准确过滤可压榨大户、冻结态与白名单', () => {
  const sample: ProcessGroupItem[] = [
    {
      name: 'FlClash.exe',
      count: 1,
      pids: [13720],
      workingSetMb: 247.7,
      privateMb: 351.5,
      cpuPercent: 4.5,
      protection: 'proxy',
      protectionLabel: '代理隧道免杀',
      state: 'protected',
      isFrozen: false,
      canControl: false,
      exePath: null,
    },
    {
      name: 'Tabbit Browser.exe',
      count: 20,
      pids: [20964],
      workingSetMb: 1937.8,
      privateMb: 1316.3,
      cpuPercent: 12.2,
      protection: 'none',
      protectionLabel: '可压榨后台',
      state: 'isolated',
      isFrozen: false,
      canControl: true,
      exePath: null,
    },
    {
      name: 'chrome.exe',
      count: 14,
      pids: [24888],
      workingSetMb: 628.0,
      privateMb: 814.4,
      cpuPercent: 18.0,
      protection: 'none',
      protectionLabel: '可压榨后台',
      state: 'frozen',
      isFrozen: true,
      canControl: true,
      exePath: null,
    },
  ];

  const controllable = filterAndSortProcessGroups(sample, 'controllable', '', 'memory');
  assertEqual(
    controllable.map((i) => i.name),
    ['Tabbit Browser.exe', 'chrome.exe'],
  );

  const byCpu = filterAndSortProcessGroups(sample, 'controllable', '', 'cpu');
  assertEqual(
    byCpu.map((i) => i.name),
    ['chrome.exe', 'Tabbit Browser.exe'],
  );

  const frozen = filterAndSortProcessGroups(sample, 'frozen', '', 'memory');
  assertEqual(
    frozen.map((i) => i.name),
    ['chrome.exe'],
  );

  const protectedOnly = filterAndSortProcessGroups(sample, 'protected', 'flclash', 'memory');
  assertEqual(
    protectedOnly.map((i) => i.name),
    ['FlClash.exe'],
  );
});

test('4. normalizeCustomWhitelistInput 支持混合分隔符并规范去除 .exe 与重复项', () => {
  assertEqual(
    normalizeCustomWhitelistInput('CS2.exe, valorant.EXE;\nobs64  cs2  WeChat.exe'),
    ['cs2', 'valorant', 'obs64', 'wechat'],
  );
});

test('5. resolvePetHudHeight 为压榨 HUD 分配足够的 640px 展开高度且保持收起 420px', () => {
  assertEqual(resolvePetHudHeight(false, 'boost', false), 420);
  assertEqual(resolvePetHudHeight(true, 'none', false), 420);
  assertEqual(resolvePetHudHeight(true, 'quota', false), 586);
  assertEqual(resolvePetHudHeight(true, 'music', false), 586);
  assertEqual(resolvePetHudHeight(true, 'boost', false), 640);
});

console.log(`\n共 ${passed + failed} 项测试: ${passed} 通过, ${failed} 失败`);
if (failed > 0) {
  throw new Error(`极客压榨纯逻辑单元测试存在 ${failed} 项未通过`);
}
