#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');
const srcDir = path.join(rootDir, 'src');
const registerUrl = pathToFileURL(path.join(__dirname, 'ts-register.mjs')).href;

function collectTestFiles(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      collectTestFiles(fullPath, out);
    } else if (/\.test\.tsx?$/.test(entry.name)) {
      out.push(fullPath);
    }
  }
  return out;
}

const filterKeyword = process.argv[2]?.trim().toLowerCase() || '';
const allTests = collectTestFiles(srcDir)
  .sort((a, b) => a.localeCompare(b))
  .filter((file) => !filterKeyword || file.toLowerCase().includes(filterKeyword));

if (allTests.length === 0) {
  console.error('❌ 未找到匹配的单元测试文件');
  process.exit(1);
}

console.log(`\n🧪 Antigravity Studio 自动化测试引擎启动（共 ${allTests.length} 个测试套件）\n`);

let suitePassed = 0;
let suiteFailed = 0;
const totalStart = Date.now();

for (const testFile of allTests) {
  const relPath = path.relative(rootDir, testFile).replace(/\\/g, '/');
  const start = Date.now();
  const res = spawnSync(
    process.execPath,
    ['--no-warnings', '--import', registerUrl, testFile],
    {
      cwd: rootDir,
      encoding: 'utf8',
      env: { ...process.env, NODE_ENV: 'test' },
    },
  );
  const elapsed = Date.now() - start;

  if (res.status === 0) {
    suitePassed += 1;
    console.log(`✅ [通过] ${relPath} (${elapsed}ms)`);
  } else {
    suiteFailed += 1;
    console.error(`❌ [失败] ${relPath} (${elapsed}ms)`);
    if (res.stdout) console.error(res.stdout.trim());
    if (res.stderr) console.error(res.stderr.trim());
  }
}

const totalElapsed = Date.now() - totalStart;
console.log(
  `\n📊 测试汇总: ${suitePassed}/${allTests.length} 套件通过, ${suiteFailed} 失败, 总耗时 ${totalElapsed}ms\n`,
);

if (suiteFailed > 0) {
  process.exit(1);
}
