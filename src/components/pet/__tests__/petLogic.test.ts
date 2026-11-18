import {
  BUILTIN_VOICE_KEYS,
  evaluateLowQuotaAlert,
  findActiveLyricIndex,
  normalizePetCharacter,
  parseLrcTimeline,
  PET_CHARACTER_ORDER,
  PET_CHARACTER_PROFILES,
  PET_HUD_AUTO_HIDE_MS,
  PET_HUD_SUBPANEL_AUTO_HIDE_MS,
  resolveHudAutoHideDelayMs,
  SCALE_PRESETS,
  shouldStartWindowDrag,
} from '../petLogic.ts';

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

test('1. 7 大角色生态与动作/语录配置完整无缺失（含冈崎汐与团子大家族）', () => {
  assertEqual(PET_CHARACTER_ORDER.length, 7);
  assertEqual(SCALE_PRESETS.length, 3);

  for (const id of PET_CHARACTER_ORDER) {
    const profile = PET_CHARACTER_PROFILES[id];
    assertOk(Boolean(profile), `缺少角色配置: ${id}`);
    assertOk(profile.quotes.length >= 3, `${id} 语录不足`);
    assertOk(profile.actions.length >= 5, `${id} 动作不足`);
  }

  const nezuko = PET_CHARACTER_PROFILES.nezuko;
  const prince = PET_CHARACTER_PROFILES.prince;
  const ushio = PET_CHARACTER_PROFILES.ushio;
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

  assertEqual(ushio.doubleClickAction, 'dango_song');
  assertEqual(ushio.particleKind, 'dango');
  assertOk(ushio.actions.some((a) => a.action === 'dango_song'));
  assertOk(ushio.actions.some((a) => a.action === 'sunflower'));
  assertOk(ushio.actions.some((a) => a.action === 'light_orb'));
});

test('2. 支持小王子、米豆子与冈崎汐/团子等多别名规范化映射', () => {
  assertEqual(normalizePetCharacter('米豆子'), 'nezuko');
  assertEqual(normalizePetCharacter('祢豆子'), 'nezuko');
  assertEqual(normalizePetCharacter('midouzi'), 'nezuko');
  assertEqual(normalizePetCharacter('NEZUKO'), 'nezuko');
  assertEqual(normalizePetCharacter('小王子'), 'prince');
  assertEqual(normalizePetCharacter('little-prince'), 'prince');
  assertEqual(normalizePetCharacter('little_prince'), 'prince');
  assertEqual(normalizePetCharacter('ushio'), 'ushio');
  assertEqual(normalizePetCharacter('冈崎汐'), 'ushio');
  assertEqual(normalizePetCharacter('小汐'), 'ushio');
  assertEqual(normalizePetCharacter('clannad'), 'ushio');
  assertEqual(normalizePetCharacter('团子'), 'ushio');
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

test('5. 全角色动漫原生语音键名与冈崎汐/米豆子经典金句矩阵 100% 对齐无悬空', () => {
  assertEqual(BUILTIN_VOICE_KEYS.length, 22);
  const validKeys = new Set<string>(BUILTIN_VOICE_KEYS);
  assertEqual(validKeys.size, 22);

  // 校验冈崎汐 (CLANNAD After Story) 6 句催泪与治愈经典金句及原生语音
  const ushio = PET_CHARACTER_PROFILES.ushio;
  assertEqual(ushio.quotes.length, 6);
  assertOk(
    ushio.quotes.some((q) => q.zh.includes('厕所') && q.zh.includes('爸爸的怀里') && q.voiceKey === 'ushio_toilet'),
    '冈崎汐缺少「厕所和爸爸的怀里」经典金句',
  );
  assertOk(
    ushio.quotes.some((q) => q.zh.includes('团子大家族') && q.voiceKey === 'ushio_dango'),
    '冈崎汐缺少「团子大家族」经典金句',
  );
  assertOk(
    ushio.quotes.some((q) => q.zh.includes('第一个买给我的') && q.voiceKey === 'ushio_robot'),
    '冈崎汐缺少「花田小机器人宝物」经典金句',
  );
  assertOk(
    ushio.quotes.some((q) => q.zh.includes('不用再忍耐') && q.voiceKey === 'ushio_sanae'),
    '冈崎汐缺少「早苗奶奶与光玉」经典金句',
  );
  for (const q of ushio.quotes) {
    assertOk(Boolean(q.sub && q.sub.length > 0), '冈崎汐金句缺少日语原声副标');
    assertOk(Boolean(q.voiceKey && validKeys.has(q.voiceKey)), `冈崎汐无效语音键: ${q.voiceKey}`);
  }

  // 校验灶门祢豆子（米豆子）6 句鬼灭经典金句与萌音
  const nezuko = PET_CHARACTER_PROFILES.nezuko;
  assertEqual(nezuko.quotes.length, 6);
  assertOk(
    nezuko.quotes.some((q) => q.zh.includes('早上好') && q.voiceKey === 'nezuko_ohayou'),
    '米豆子缺少克服阳光「早…早上好」经典金句',
  );
  assertOk(
    nezuko.quotes.some((q) => q.zh.includes('幸不幸福是由自己决定') && q.voiceKey === 'nezuko_happiness'),
    '米豆子缺少「幸不幸福由自己决定」经典金句',
  );
  assertOk(
    nezuko.quotes.some((q) => q.zh.includes('血鬼术·爆血') && q.voiceKey === 'nezuko_blood'),
    '米豆子缺少「血鬼术·爆血」经典金句',
  );
  for (const q of nezuko.quotes) {
    assertOk(Boolean(q.sub && q.sub.length > 0), '米豆子金句缺少日语原声副标');
    assertOk(Boolean(q.voiceKey && validKeys.has(q.voiceKey)), `米豆子无效语音键: ${q.voiceKey}`);
  }

  // 遍历全角色校验所有引用到的 voiceKey 均存在于 22 条内置音频池中，且全部 22 条音频均被覆盖
  const referencedKeys = new Set<string>();
  for (const cid of PET_CHARACTER_ORDER) {
    const p = PET_CHARACTER_PROFILES[cid];
    if (p.doubleClickVoiceKey) {
      assertOk(validKeys.has(p.doubleClickVoiceKey), `${cid} doubleClickVoiceKey 非法: ${p.doubleClickVoiceKey}`);
      referencedKeys.add(p.doubleClickVoiceKey);
    }
    for (const q of p.quotes) {
      if (q.voiceKey) {
        assertOk(validKeys.has(q.voiceKey), `${cid} quote voiceKey 非法: ${q.voiceKey}`);
        referencedKeys.add(q.voiceKey);
      }
    }
    for (const act of p.actions) {
      if (act.voiceKey) {
        assertOk(validKeys.has(act.voiceKey), `${cid} action voiceKey 非法: ${act.voiceKey}`);
        referencedKeys.add(act.voiceKey);
      }
    }
  }
  // 加上 PetWindowView 休眠触发的 ushio_sleep / nezuko_apologize 已在 quotes 中注册，因此 referencedKeys 应正好等于 22
  assertEqual(referencedKeys.size, 22, '存在未被角色语录或动作引用的孤立内置语音');
});

test('6. 上下文字控制面板按需点击展开与自动隐藏倒计时判定准确', () => {
  // 默认隐藏状态下不启动冗余定时器
  assertEqual(
    resolveHudAutoHideDelayMs({
      hudVisible: false,
      hudInteracting: false,
      pickerOpen: false,
      panelMode: 'none',
    }),
    null,
  );

  // 点击唤醒后、未悬停面板按钮时，4.5s 自动隐藏
  assertEqual(
    resolveHudAutoHideDelayMs({
      hudVisible: true,
      hudInteracting: false,
      pickerOpen: false,
      panelMode: 'none',
    }),
    PET_HUD_AUTO_HIDE_MS,
  );

  // 指针或焦点正在上下文字面板内操作时，暂停倒计时防误关
  assertEqual(
    resolveHudAutoHideDelayMs({
      hudVisible: true,
      hudInteracting: true,
      pickerOpen: false,
      panelMode: 'none',
    }),
    null,
  );

  // 展开角色抽屉或算力/歌词二级面板且移开指针后，延长至 8s 自动收起
  assertEqual(
    resolveHudAutoHideDelayMs({
      hudVisible: true,
      hudInteracting: false,
      pickerOpen: true,
      panelMode: 'none',
    }),
    PET_HUD_SUBPANEL_AUTO_HIDE_MS,
  );
  assertEqual(
    resolveHudAutoHideDelayMs({
      hudVisible: true,
      hudInteracting: false,
      pickerOpen: false,
      panelMode: 'music',
    }),
    PET_HUD_SUBPANEL_AUTO_HIDE_MS,
  );
});

console.log(`\n测试汇总: ${passed} 通过, ${failed} 失败`);
if (failed > 0) {
  throw new Error(`桌面伴侣单元测试存在 ${failed} 项未通过`);
}
