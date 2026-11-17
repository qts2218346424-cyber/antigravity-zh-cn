import {
  evaluateLowQuotaAlert,
  findActiveLyricIndex,
  normalizePetCharacter,
  parseLrcTimeline,
  PET_CHARACTER_ORDER,
  PET_CHARACTER_PROFILES,
  SCALE_PRESETS,
  shouldStartWindowDrag,
} from '../petLogic';

let passed = 0;
let failed = 0;

function assertOk(condition: boolean, msg = '断言未通过'): void {
  if (!condition) {
    throw new Error(msg);
  }
}

function assertEqual<T>(actual: T, expected: T, msg?: string): void {
  if (actual !== expected) {
    throw new Error(
      `${msg ? `${msg}: ` : ''}expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
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

console.log('=== 桌面伴侣角色与交互逻辑单元测试 ===');

test('1. 6 大角色生态与动作/语录配置完整无缺失', () => {
  assertEqual(PET_CHARACTER_ORDER.length, 6);
  assertEqual(SCALE_PRESETS.length, 3);

  for (const id of PET_CHARACTER_ORDER) {
    const profile = PET_CHARACTER_PROFILES[id];
    assertOk(Boolean(profile), `缺少角色配置: ${id}`);
    assertOk(profile.quotes.length >= 3, `${id} 语录不足`);
    assertOk(profile.actions.length >= 5, `${id} 动作不足`);
  }

  const nezuko = PET_CHARACTER_PROFILES.nezuko;
  const prince = PET_CHARACTER_PROFILES.prince;
  assertEqual(nezuko.doubleClickAction, 'box_spin');
  assertOk(nezuko.actions.some((a) => a.action === 'pat'));
  assertOk(nezuko.actions.some((a) => a.action === 'box_spin'));
  assertOk(nezuko.actions.some((a) => a.action === 'dash'));
  assertOk(nezuko.actions.some((a) => a.action === 'stomp'));
  assertOk(nezuko.actions.some((a) => a.action === 'blood'));
  assertOk(nezuko.actions.some((a) => a.action === 'feed'));

  assertEqual(prince.doubleClickAction, 'stars');
  assertOk(prince.actions.some((a) => a.action === 'fox'));
  assertOk(prince.actions.some((a) => a.action === 'rose'));
  assertOk(prince.actions.some((a) => a.action === 'stars'));
  assertOk(prince.actions.some((a) => a.action === 'volcano'));
  assertOk(prince.actions.some((a) => a.action === 'walk'));
});

test('2. 支持小王子与米豆子/祢豆子等多别名规范化映射', () => {
  assertEqual(normalizePetCharacter('米豆子'), 'nezuko');
  assertEqual(normalizePetCharacter('祢豆子'), 'nezuko');
  assertEqual(normalizePetCharacter('midouzi'), 'nezuko');
  assertEqual(normalizePetCharacter('NEZUKO'), 'nezuko');
  assertEqual(normalizePetCharacter('小王子'), 'prince');
  assertEqual(normalizePetCharacter('little-prince'), 'prince');
  assertEqual(normalizePetCharacter('little_prince'), 'prince');
  assertEqual(normalizePetCharacter('tanjiro'), 'tanjiro');
  assertEqual(normalizePetCharacter('zenitsu'), 'zenitsu');
  assertEqual(normalizePetCharacter('inosuke'), 'inosuke');
  assertEqual(normalizePetCharacter('custom'), 'custom');
  assertEqual(normalizePetCharacter(undefined), 'nezuko');
});

test('3. LRC 时间轴解析、纯文本回退与二分查找精准定位当前歌词行', () => {
  const sampleLrc = '[ti:B612]\n[offset:100]\n[00:02.00]第一句星光\n[00:05.50][00:12.00]副歌重唱';
  const lines = parseLrcTimeline(sampleLrc);
  assertEqual(lines.length, 3);
  assertEqual(lines[0].timeMs, 1900);
  assertEqual(findActiveLyricIndex(lines, 500), 0);
  assertEqual(findActiveLyricIndex(lines, 6000), 1);
  assertEqual(findActiveLyricIndex(lines, 13000), 2);
  assertEqual(findActiveLyricIndex([], 1000), -1);

  const plain = parseLrcTimeline('第一行\n第二行');
  assertEqual(plain.length, 2);
  assertEqual(plain[1].timeMs, 3200);
});

test('4. 窗口拖拽位移阈值与低配额预警判定准确', () => {
  assertEqual(shouldStartWindowDrag(100, 100, 102, 102, 5), false);
  assertEqual(shouldStartWindowDrag(100, 100, 103, 104, 5), true);
  assertEqual(shouldStartWindowDrag(100, 100, 104, 104, 5), true);

  const alert = evaluateLowQuotaAlert(
    [
      { name: 'claude-sonnet', display_name: 'Claude Sonnet', percentage: 85 },
      { name: 'gemini-pro', display_name: 'Gemini Pro', percentage: 12 },
    ],
    20,
  );
  assertEqual(alert.hasLowQuota, true);
  assertEqual(alert.lowestPercentage, 12);
});

console.log(`\n测试汇总: ${passed} 通过, ${failed} 失败`);
if (failed > 0) {
  throw new Error(`桌面伴侣单元测试存在 ${failed} 项未通过`);
}
