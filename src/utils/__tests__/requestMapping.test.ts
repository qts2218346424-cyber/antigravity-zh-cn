/**
 * 前后端双模请求路由映射与路径参数防误吞单元测试
 * 运行命令: npm test
 */
import { COMMAND_MAPPING, buildMappedRequestUrl } from '../request';

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

test('1. GET 请求替换路径占位符时绝不误吞同值的合法查询参数', () => {
  // 历史缺陷回归测试：当 accountId === "1" 时，旧实现使用 url.includes("1") 会误把 page=1 吞掉
  const res = buildMappedRequestUrl('/api/accounts/:accountId/quota', 'GET', {
    accountId: '1',
    page: 1,
    limit: 1,
  });
  assertEqual(res.url, '/api/accounts/1/quota?page=1&limit=1');

  // 当路径段包含 logs 且 query 值也为 "logs" 时同样不能误伤
  const res2 = buildMappedRequestUrl('/api/logs/:logId', 'GET', {
    logId: 'logs',
    category: 'logs',
  });
  assertEqual(res2.url, '/api/logs/logs?category=logs');
});

test('2. 路径参数支持多段替换、URL 特殊字符安全编码且不污染入参对象', () => {
  const originalArgs = {
    accountId: 'user@example.com',
    versionId: 'v1/alpha 2',
    force: true,
  };
  const res = buildMappedRequestUrl(
    '/api/accounts/:accountId/device-versions/:versionId/restore',
    'POST',
    originalArgs,
  );
  assertEqual(
    res.url,
    '/api/accounts/user%40example.com/device-versions/v1%2Falpha%202/restore',
  );
  assertEqual(res.bodyArgs?.accountId, undefined, '已注入路径的字段应从 POST bodyArgs 中剥离');
  assertEqual(res.bodyArgs?.versionId, undefined);
  assertEqual(res.bodyArgs?.force, true, '非路径字段必须完整保留在 POST bodyArgs 中');
  assertEqual(originalArgs.accountId, 'user@example.com', '不得修改调用方原始入参对象');
});

test('3. 查询参数正确忽略 null/undefined 并保留 0 与 false', () => {
  const res = buildMappedRequestUrl('/api/security/logs', 'GET', {
    limit: 50,
    offset: 0,
    blockedOnly: false,
    ipFilter: undefined,
    extra: null,
  });
  assertEqual(res.url, '/api/security/logs?limit=50&offset=0&blockedOnly=false');
});

test('4. COMMAND_MAPPING 完整覆盖核心业务与本次重构补齐的全部命令', () => {
  const requiredCommands: Array<[string, 'GET' | 'POST' | 'DELETE' | 'PATCH']> = [
    ['test_model_connectivity', 'POST'],
    ['update_account_label', 'POST'],
    ['update_account_project_id', 'POST'],
    ['auto_fetch_account_project_id', 'POST'],
    ['get_active_clients_status', 'GET'],
    ['get_proxy_logs_paginated', 'GET'],
    ['get_droid_sync_status', 'POST'],
    ['execute_droid_sync', 'POST'],
    ['execute_droid_restore', 'POST'],
    ['get_droid_config_content', 'POST'],
    ['get_token_stats_minute', 'GET'],
    ['get_token_stats_model_trend_minute', 'GET'],
    ['get_token_stats_account_trend_minute', 'GET'],
    ['clear_ip_blacklist', 'POST'],
    ['clear_ip_whitelist', 'POST'],
    ['get_ip_access_logs', 'GET'],
  ];

  for (const [cmd, expectedMethod] of requiredCommands) {
    const entry = COMMAND_MAPPING[cmd];
    assert(Boolean(entry), `COMMAND_MAPPING 缺少关键命令映射: ${cmd}`);
    assertEqual(entry.method, expectedMethod, `${cmd} 的 HTTP 方法不匹配`);
  }
});

if (failed > 0) {
  throw new Error(`请求映射单元测试失败: ${failed} 项未通过 (通过 ${passed} 项)`);
}
