#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

const inputVersion = process.argv[2];
if (!inputVersion || !/^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$/.test(inputVersion)) {
  console.error('用法: node scripts/bump-version.mjs <semver>  (示例: 5.1.0 或 5.1.0-beta.1)');
  process.exit(1);
}

const cleanVersion = inputVersion.replace(/^v/, '');

// 1. 更新 package.json
const pkgPath = path.join(rootDir, 'package.json');
const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
pkg.version = cleanVersion;
fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n', 'utf8');

// 2. 更新 src-tauri/tauri.conf.json
const tauriConfPath = path.join(rootDir, 'src-tauri', 'tauri.conf.json');
const tauriConf = JSON.parse(fs.readFileSync(tauriConfPath, 'utf8'));
tauriConf.version = cleanVersion;
fs.writeFileSync(tauriConfPath, JSON.stringify(tauriConf, null, 2) + '\n', 'utf8');

// 3. 更新 src-tauri/Cargo.toml (仅更新 [package] 段第一处 version)
const cargoPath = path.join(rootDir, 'src-tauri', 'Cargo.toml');
const cargoRaw = fs.readFileSync(cargoPath, 'utf8');
const cargoUpdated = cargoRaw.replace(
  /^(version\s*=\s*)"[^"]+"/m,
  `$1"${cleanVersion}"`,
);
fs.writeFileSync(cargoPath, cargoUpdated, 'utf8');

console.log(`✅ 已将全工程版本号同步为 v${cleanVersion}:`);
console.log('   - package.json');
console.log('   - src-tauri/tauri.conf.json');
console.log('   - src-tauri/Cargo.toml');
