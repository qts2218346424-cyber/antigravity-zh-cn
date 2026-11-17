/**
 * 《CLANNAD》四大高定光学材质包与 60fps 启动动画引擎单元测试
 * 运行命令: npm test
 */
import sakuraHillSkin from '../../../../resources/skins/clannad-sakura-hill/skin.json';
import orbsSkin from '../../../../resources/skins/clannad-illusionary-orbs/skin.json';
import sunflowerSkin from '../../../../resources/skins/clannad-after-sunflower/skin.json';
import starfishSkin from '../../../../resources/skins/clannad-starfish-library/skin.json';
import {
  CLANNAD_SPLASH_THEMES,
  getSplashThemeSpec,
  loadStudioSplashPrefs,
  normalizeSplashThemeId,
  saveStudioSplashPrefs,
} from '../clannadSplashData';

let passed = 0;
let failed = 0;

function assertOk(condition: boolean, msg: string): void {
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
    passed += 1;
    console.log(`  PASS: ${description}`);
  } catch (err) {
    failed += 1;
    console.error(`  FAIL: ${description} — ${(err as Error).message}`);
  }
}

test('1. 4 款《CLANNAD》高定材质包 Schema、深浅分类与配色变量齐全合法', () => {
  const skins = [sakuraHillSkin, orbsSkin, sunflowerSkin, starfishSkin];
  assertEqual(skins.length, 4);

  const lightCount = skins.filter((s) => s.base === 'light').length;
  const darkCount = skins.filter((s) => s.base === 'dark').length;
  assertEqual(lightCount, 2, '应包含 2 款浅色护眼材质');
  assertEqual(darkCount, 2, '应包含 2 款深色沉浸材质');

  for (const skin of skins) {
    assertEqual(skin.schema, 1, `${skin.id} schema 必须为 1`);
    assertOk(skin.id.startsWith('clannad-'), `${skin.id} 命名应以 clannad- 开头`);
    assertOk(skin.name.includes('CLANNAD'), `${skin.id} 名称应体现 CLANNAD 主题`);
    assertEqual(skin.preview, 'preview.svg', `${skin.id} 应绑定矢量预览图`);
    assertEqual(skin.pet.character, 'ushio', `${skin.id} 应联动冈崎汐桌面伴侣`);
    assertOk(skin.colors.background.startsWith('#'), `${skin.id} background 应为 HEX`);
    assertOk(skin.colors.accent.startsWith('#'), `${skin.id} accent 应为 HEX`);
    assertOk(skin.surfaces.glass_blur >= 10, `${skin.id} 应具备毛玻璃表面参数`);
    assertOk(Array.isArray(skin.background) && skin.background.length > 0, `${skin.id} 应配置矢量暗纹背景`);
  }
});

test('2. 4 大《CLANNAD》启动序幕分镜与材质包一一对应且归一化准确', () => {
  assertEqual(CLANNAD_SPLASH_THEMES.length, 4);
  const validSkinIds = new Set([
    'clannad-sakura-hill',
    'clannad-illusionary-orbs',
    'clannad-after-sunflower',
    'clannad-starfish-library',
  ]);

  for (const spec of CLANNAD_SPLASH_THEMES) {
    assertOk(validSkinIds.has(spec.linkedSkinId), `${spec.id} 关联材质包不存在`);
    assertEqual(spec.steps.length, 3, `${spec.id} 应包含 3 个进度阶段提示`);
  }

  assertEqual(normalizeSplashThemeId('sakura'), 'clannad-sakura');
  assertEqual(normalizeSplashThemeId('dango'), 'clannad-sakura');
  assertEqual(normalizeSplashThemeId('ushio'), 'clannad-sunflower');
  assertEqual(normalizeSplashThemeId('kotomi'), 'clannad-starfish');
  assertEqual(normalizeSplashThemeId('none'), 'none');
  assertEqual(normalizeSplashThemeId('unknown'), 'clannad-orbs');
  assertEqual(getSplashThemeSpec('clannad-sakura').linkedSkinId, 'clannad-sakura-hill');
});

test('3. 启动动画本地偏好读写与安全回退正常', () => {
  const saved = saveStudioSplashPrefs({
    studioBootEnabled: true,
    themeId: 'clannad-sakura',
    durationMs: 3800,
    musicBoxEnabled: true,
  });
  assertEqual(saved.themeId, 'clannad-sakura');

  const loaded = loadStudioSplashPrefs();
  assertEqual(loaded.studioBootEnabled, true);
  assertEqual(loaded.themeId, 'clannad-sakura');
  assertEqual(loaded.durationMs, 3800);
  assertEqual(loaded.musicBoxEnabled, true);
});

if (failed > 0) {
  throw new Error(`CLANNAD 主题与启动动画单元测试存在 ${failed} 项失败 (通过 ${passed} 项)`);
}
