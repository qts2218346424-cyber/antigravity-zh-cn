import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import ts from 'typescript';

function tryResolveFile(basePath) {
  const candidates = [
    basePath,
    `${basePath}.ts`,
    `${basePath}.tsx`,
    `${basePath}.js`,
    `${basePath}.mjs`,
    `${basePath}.json`,
    path.join(basePath, 'index.ts'),
    path.join(basePath, 'index.tsx'),
    path.join(basePath, 'index.js'),
  ];

  for (const candidate of candidates) {
    try {
      if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
        return candidate;
      }
    } catch {
      // 忽略无效路径探测错误
    }
  }
  return null;
}

export async function resolve(specifier, context, nextResolve) {
  if (
    (specifier.startsWith('./') || specifier.startsWith('../') || specifier.startsWith('/')) &&
    context.parentURL &&
    context.parentURL.startsWith('file:')
  ) {
    const parentDir = path.dirname(fileURLToPath(context.parentURL));
    const targetBase = specifier.startsWith('/')
      ? specifier
      : path.resolve(parentDir, specifier);
    const hit = tryResolveFile(targetBase);
    if (hit) {
      return {
        url: pathToFileURL(hit).href,
        shortCircuit: true,
      };
    }
  }
  return nextResolve(specifier, context);
}

export async function load(url, context, nextLoad) {
  if (url.startsWith('file:')) {
    const filePath = fileURLToPath(url);
    if (filePath.endsWith('.ts') || filePath.endsWith('.tsx')) {
      const rawSource = fs.readFileSync(filePath, 'utf8');
      const transpiled = ts.transpileModule(rawSource, {
        fileName: filePath,
        compilerOptions: {
          module: ts.ModuleKind.ESNext,
          target: ts.ScriptTarget.ES2022,
          jsx: ts.JsxEmit.ReactJSX,
          esModuleInterop: true,
          resolveJsonModule: true,
          isolatedModules: true,
        },
      });
      return {
        format: 'module',
        shortCircuit: true,
        source: transpiled.outputText,
      };
    }

    if (filePath.endsWith('.json')) {
      const rawJson = fs.readFileSync(filePath, 'utf8');
      return {
        format: 'module',
        shortCircuit: true,
        source: `export default ${rawJson};\n`,
      };
    }
  }

  return nextLoad(url, context);
}
