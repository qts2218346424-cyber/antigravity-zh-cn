/**
 * 国际化词典完整性、品牌命名一致性与日文零残留校验测试
 * 运行命令: npm test
 */
import zh from '../zh.json';
import en from '../en.json';

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

function flattenKeys(obj: Record<string, unknown>, prefix = ''): Map<string, string> {
  const map = new Map<string, string>();
  for (const [k, v] of Object.entries(obj)) {
    const nextKey = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      for (const [childKey, childVal] of flattenKeys(v as Record<string, unknown>, nextKey)) {
        map.set(childKey, childVal);
      }
    } else {
      map.set(nextKey, String(v ?? ''));
    }
  }
  return map;
}

const zhMap = flattenKeys(zh as Record<string, unknown>);
const enMap = flattenKeys(en as Record<string, unknown>);

test('1. 中文词典与英文词典核心业务键完整存在且品牌统一为 Antigravity Studio', () => {
  if (zhMap.get('common.app_name') !== 'Antigravity Studio') {
    throw new Error(`zh.json common.app_name 应为 Antigravity Studio，实际为 ${zhMap.get('common.app_name')}`);
  }
  if (enMap.get('common.app_name') !== 'Antigravity Studio') {
    throw new Error(`en.json common.app_name 应为 Antigravity Studio，实际为 ${enMap.get('common.app_name')}`);
  }

  const criticalKeys = [
    'nav.studio',
    'monitor.network.title',
    'debug_console.title',
    'proxy.opencode_sync.modal_title',
    'proxy.droid_sync.modal_title',
    'accounts.add.oauth_success',
    'accounts.device_fingerprint_dialog.storage_json_not_found',
    'common.copy_all',
    'common.empty',
    'common.retry',
  ];

  for (const key of criticalKeys) {
    if (!zhMap.has(key) || !zhMap.get(key)?.trim()) {
      throw new Error(`zh.json 缺失或为空的关键翻译键: ${key}`);
    }
    if (!enMap.has(key) || !enMap.get(key)?.trim()) {
      throw new Error(`en.json 缺失或为空的关键翻译键: ${key}`);
    }
  }
});

test('2. 中文语言包 (zh.json) 零日文平假名/片假名残留', () => {
  // 排除常见中文符号（如「」・），仅匹配日文平假名 \u3040-\u309F 与片假名字母 \u30A1-\u30FA
  const kanaRegex = /[\u3040-\u309F\u30A1-\u30FA]/;
  const polluted: string[] = [];

  for (const [key, val] of zhMap.entries()) {
    if (kanaRegex.test(val)) {
      polluted.push(`${key}: ${val}`);
    }
  }

  if (polluted.length > 0) {
    throw new Error(`zh.json 检测到日文假名残留:\n${polluted.slice(0, 5).join('\n')}`);
  }
});

if (failed > 0) {
  throw new Error(`国际化校验测试失败: ${failed} 项未通过 (通过 ${passed} 项)`);
}
