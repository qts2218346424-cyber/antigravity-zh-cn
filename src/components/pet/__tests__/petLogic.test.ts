/**
 * 灵动桌面伴侣核心纯逻辑与交互算法单元测试
 * 运行命令: npm test
 */
import {
  PET_CHARACTER_ORDER,
  PET_CHARACTER_PROFILES,
  SCALE_PRESETS,
  evaluateLowQuotaAlert,
  findActiveLyricIndex,
  normalizePetCharacter,
  parseLrcTimeline,
  shouldStartWindowDrag,
} from '../petLogic';

let passed = 0;
let failed = 0;

function test(description: string, fn: () => void): void {
  try {
    fn();
    passed += 1;
    console.log(`  ok  ${description}`);
  } catch (err) {
    failed += 1;
    console.error(`  FAIL  ${description}`);
    console.error(err);
  }
}

function assert(condition: boolean, msg: string): void {
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

test('1. 6 大角色生态定义完整且动作/语录/主题色齐备', () => {
  assertEqual(PET_CHARACTER_ORDER.length, 6, '角色顺序列表应包含 6 个角色');
  assertEqual(SCALE_PRESETS.length, 3, '缩放预设应包含 3 档');

  for (const id of PET_CHARACTER_ORDER) {
    const profile = PET_CHARACTER_PROFILES[id];
    assert(Boolean(profile), `缺少角色配置: ${id}`);
    assertEqual(profile.id, id);
    assert(profile.name.length > 0, `${id} 缺少完整名称`);
    assert(profile.shortName.length > 0, `${id} 缺少简称`);
    assert(profile.accent.startsWith('#'), `${id} 主强调色应为 HEX 格式`);
    assert(profile.quotes.length >= 3, `${id} 语录数量至少为 3 条`);
    assert(profile.actions.length >= 5, `${id} 快捷交互动作至少为 5 项`);
  }
});

test('2. normalizePetCharacter 安全归一化各类输入与历史别名', () => {
  assertEqual(normalizePetCharacter('nezuko'), 'nezuko');
  assertEqual(normalizePetCharacter('  PRINCE '), 'prince');
  assertEqual(normalizePetCharacter('little-prince'), 'prince');
  assertEqual(normalizePetCharacter('little_prince'), 'prince');
  assertEqual(normalizePetCharacter('Tanjiro'), 'tanjiro');
  assertEqual(normalizePetCharacter('ZENITSU'), 'zenitsu');
  assertEqual(normalizePetCharacter('inosuke'), 'inosuke');
  assertEqual(normalizePetCharacter('custom'), 'custom');
  assertEqual(normalizePetCharacter('unknown-role'), 'nezuko');
  assertEqual(normalizePetCharacter(''), 'nezuko');
  assertEqual(normalizePetCharacter(null), 'nezuko');
  assertEqual(normalizePetCharacter(undefined), 'nezuko');
});

test('3. parseLrcTimeline 支持多时间标签、毫秒精度、offset 校准与元信息过滤', () => {
  const sampleLrc = [
    '[ti:红莲华]',
    '[ar:LiSA]',
    '[offset:200]',
    '[00:05.00]第一句前奏开场',
    '[00:12.34][00:42.500]重复副歌段落',
    '[00:25:80]冒号毫秒分隔兼容',
    '[00:30.00]',
  ].join('\n');

  const lines = parseLrcTimeline(sampleLrc);
  assertEqual(lines.length, 4, '有效带词时间戳应展开为 4 条');
  // 5000 - 200 = 4800
  assertEqual(lines[0].timeMs, 4800);
  assertEqual(lines[0].text, '第一句前奏开场');
  // 12340 - 200 = 12140
  assertEqual(lines[1].timeMs, 12140);
  assertEqual(lines[1].text, '重复副歌段落');
  // 25800 - 200 = 25600
  assertEqual(lines[2].timeMs, 25600);
  assertEqual(lines[2].text, '冒号毫秒分隔兼容');
  // 42500 - 200 = 42300
  assertEqual(lines[3].timeMs, 42300);
  assertEqual(lines[3].text, '重复副歌段落');
});

test('4. parseLrcTimeline 对纯文本无时间轴歌词自动生成 3200ms 均匀时间轴', () => {
  const plain = '星光洒满 B612\n玫瑰在玻璃罩下呼吸\n小狐狸竖起耳朵';
  const lines = parseLrcTimeline(plain);
  assertEqual(lines.length, 3);
  assertEqual(lines[0].timeMs, 0);
  assertEqual(lines[1].timeMs, 3200);
  assertEqual(lines[2].timeMs, 6400);
  assertEqual(parseLrcTimeline('   \n  ').length, 0);
});

test('5. findActiveLyricIndex 二分查找时间轴边界精确命中', () => {
  assertEqual(findActiveLyricIndex([], 1000), -1);

  const lines = [
    { timeMs: 1000, text: '第一句' },
    { timeMs: 4500, text: '第二句' },
    { timeMs: 9000, text: '第三句' },
  ];
  assertEqual(findActiveLyricIndex(lines, 0), 0, '未到首句时展示首句预备');
  assertEqual(findActiveLyricIndex(lines, 1000), 0, '精确命中首句');
  assertEqual(findActiveLyricIndex(lines, 4499), 0, '第二句前 1ms 仍停留在第一句');
  assertEqual(findActiveLyricIndex(lines, 4500), 1, '精确切换至第二句');
  assertEqual(findActiveLyricIndex(lines, 8999), 1);
  assertEqual(findActiveLyricIndex(lines, 9000), 2);
  assertEqual(findActiveLyricIndex(lines, 99999), 2, '超过末句保持最后一句');
});

test('6. shouldStartWindowDrag 5px 物理位移防抖避免单击与双击被窗口拖拽吞没', () => {
  assertEqual(shouldStartWindowDrag(100, 100, 100, 100), false);
  assertEqual(shouldStartWindowDrag(100, 100, 103, 103), false, '4.24px 小幅抖动不应触发拖拽');
  assertEqual(shouldStartWindowDrag(100, 100, 103, 104), true, '3-4-5 直角三角形恰好 5px 应触发拖拽');
  assertEqual(shouldStartWindowDrag(200, 200, 190, 200), true);
});

test('7. evaluateLowQuotaAlert 精确捕获最低配额模型并生成预警文案', () => {
  const emptyRes = evaluateLowQuotaAlert([]);
  assertEqual(emptyRes.hasLowQuota, false);

  const healthyRes = evaluateLowQuotaAlert([
    { name: 'claude-sonnet-4-6', display_name: 'Claude Sonnet 4.6', percentage: 82 },
    { name: 'gemini-3.1-pro', display_name: 'Gemini 3.1 Pro', percentage: 45 },
  ]);
  assertEqual(healthyRes.hasLowQuota, false);
  assertEqual(healthyRes.lowestPercentage, 45);

  const lowRes = evaluateLowQuotaAlert([
    { name: 'gemini-3.1-pro', display_name: 'Gemini 3.1 Pro', percentage: 68 },
    { name: 'claude-opus-4-6-thinking', display_name: 'Claude Opus 4.6', percentage: 12 },
  ]);
  assertEqual(lowRes.hasLowQuota, true);
  assertEqual(lowRes.lowestModelName, 'Claude Opus 4.6');
  assertEqual(lowRes.lowestPercentage, 12);
  assert(lowRes.alertMessage.includes('12%'), '预警文案应包含具体百分比');
});

if (failed > 0) {
  throw new Error(`桌面伴侣逻辑测试失败: ${failed} 项未通过 (通过 ${passed} 项)`);
}
