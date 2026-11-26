/**
 * 棱镜光学切面与轻量交互运行时测试套件
 * 运行命令: npm test
 */

interface NodeFs {
  readFileSync: (p: string, enc: string) => string;
}

interface NodePath {
  resolve: (...parts: string[]) => string;
}

interface NodeVm {
  Script: new (code: string, opts?: { filename?: string }) => unknown;
  runInNewContext: (code: string, context: Record<string, unknown>) => unknown;
}

const nodeProc = (
  globalThis as unknown as {
    process?: {
      cwd: () => string;
      exit: (code: number) => never;
      getBuiltinModule?: (id: string) => unknown;
    };
  }
).process;

const fs = nodeProc?.getBuiltinModule?.('node:fs') as NodeFs | undefined;
const path = nodeProc?.getBuiltinModule?.('node:path') as NodePath | undefined;
const vm = nodeProc?.getBuiltinModule?.('node:vm') as NodeVm | undefined;

let passed = 0;
let failed = 0;

function assertOk(condition: boolean, msg: string): void {
  if (!condition) {
    throw new Error(msg);
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

const rootDir = nodeProc?.cwd() || '.';

test('1. skin-runtime.js 语法合法且支持棱镜生命周期与无痕卸载', () => {
  assertOk(Boolean(fs && path && vm), 'Node 内置模块不可用');
  const runtimePath = path!.resolve(rootDir, 'resources/skin-runtime.js');
  const code = fs!.readFileSync(runtimePath, 'utf8');
  assertOk(code.includes('__AGZH_SKIN_RUNTIME__'), '缺少运行时标识头');
  assertOk(code.includes('teardownPrismControllers'), '缺少统一卸载清理函数');
  assertOk(code.includes('data-agzh-rim-active'), '缺少近场边框高光追踪标记');
  assertOk(code.includes('agzh-code-fold-btn'), '缺少长代码块折叠按钮注入逻辑');
  assertOk(code.includes('agzh-rail-hud'), '缺少会话轮次导轨控件');
  assertOk(code.includes('agzh-aura-bar'), '缺少语义边缘余晖指示条');

  new vm!.Script(code, { filename: 'skin-runtime.js' });

  type MockStyle = {
    colorScheme: string;
    props: Record<string, string>;
    setProperty: (k: string, v: string) => void;
    removeProperty: (k: string) => void;
  };

  type MockEl = {
    id: string;
    tagName: string;
    className: string;
    textContent: string;
    style: MockStyle;
    classList: {
      set: Set<string>;
      contains: (c: string) => boolean;
      toggle: (c: string, force?: boolean) => void;
    };
    attrs: Map<string, string>;
    children: MockEl[];
    parentNode: MockEl | null;
    setAttribute: (k: string, v: string) => void;
    getAttribute: (k: string) => string | null;
    removeAttribute: (k: string) => void;
    appendChild: (c: MockEl) => MockEl;
    removeChild: (c: MockEl) => MockEl;
    addEventListener: () => void;
    removeEventListener: () => void;
    querySelector: () => null;
    querySelectorAll: () => MockEl[];
  };

  const byId = new Map<string, MockEl>();
  function makeEl(tagName: string, id = ''): MockEl {
    const clsSet = new Set<string>();
    const attrs = new Map<string, string>();
    const children: MockEl[] = [];
    const props: Record<string, string> = {};
    const styleObj: MockStyle = {
      colorScheme: '',
      props,
      setProperty(k: string, v: string) {
        props[k] = v;
      },
      removeProperty(k: string) {
        delete props[k];
      },
    };
    const el: MockEl = {
      id,
      tagName,
      className: '',
      textContent: '',
      style: styleObj,
      classList: {
        set: clsSet,
        contains: (c: string) => clsSet.has(c),
        toggle: (c: string, force?: boolean) => {
          const want = force === undefined ? !clsSet.has(c) : Boolean(force);
          if (want) clsSet.add(c);
          else clsSet.delete(c);
        },
      },
      attrs,
      children,
      parentNode: null,
      setAttribute(k: string, v: string) {
        attrs.set(k, String(v));
        if (k === 'id') {
          el.id = String(v);
          byId.set(el.id, el);
        }
      },
      getAttribute: (k: string) => attrs.get(k) ?? null,
      removeAttribute: (k: string) => {
        attrs.delete(k);
      },
      appendChild(c: MockEl) {
        c.parentNode = el;
        children.push(c);
        if (c.id) byId.set(c.id, c);
        return c;
      },
      removeChild(c: MockEl) {
        const idx = children.indexOf(c);
        if (idx >= 0) children.splice(idx, 1);
        c.parentNode = null;
        if (c.id) byId.delete(c.id);
        return c;
      },
      addEventListener: () => {},
      removeEventListener: () => {},
      querySelector: () => null,
      querySelectorAll: () => [],
    };
    return el;
  }

  const docEl = makeEl('HTML');
  const headEl = makeEl('HEAD');
  const bodyEl = makeEl('BODY');
  bodyEl.classList.toggle('theme-light', true);

  const mockDocument = {
    readyState: 'complete',
    hidden: false,
    documentElement: docEl,
    head: headEl,
    body: bodyEl,
    activeElement: bodyEl,
    createElement: (tag: string) => makeEl(tag.toUpperCase()),
    getElementById: (id: string) => byId.get(id) ?? null,
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener: () => {},
    removeEventListener: () => {},
  };

  let ipcHandler: ((_ev: unknown, live: unknown) => void) | null = null;
  const mockWindow: Record<string, unknown> = {
    __AGZH_SKIN__: {
      skin_id: 'obsidian-glass',
      base: 'dark',
      css: ':root{--agzh-accent:#38bdf8;}',
      prism: { facets: true, rim_glow: true, code_enhance: true, ambient_aura: true },
    },
    addEventListener: () => {},
    removeEventListener: () => {},
  };

  const sandbox: Record<string, unknown> = {
    window: mockWindow,
    document: mockDocument,
    console,
    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,
    require: (mod: string) => {
      if (mod === 'electron') {
        return {
          ipcRenderer: {
            sendSync: () => undefined,
            invoke: async () => undefined,
            on: (_ch: string, fn: (_ev: unknown, live: unknown) => void) => {
              ipcHandler = fn;
            },
          },
        };
      }
      return null;
    },
  };
  mockWindow.window = mockWindow;

  vm!.runInNewContext(code, sandbox);

  assertOk(docEl.getAttribute('data-agzh-skin') === 'obsidian-glass', '激活后应标记 data-agzh-skin');
  assertOk(docEl.getAttribute('data-agzh-prism') === '1', '激活后应标记 data-agzh-prism=1');
  assertOk(Boolean(byId.get('agzh-skin-style')), '激活后应挂载皮肤样式节点');
  assertOk(Boolean(byId.get('agzh-aura-bar')), '激活后应挂载语义余晖条');

  assertOk(Boolean(ipcHandler), '应绑定 agzh:skin-updated IPC 监听');
  ipcHandler!({}, null);

  assertOk(docEl.getAttribute('data-agzh-skin') === null, '停用后应清除 data-agzh-skin');
  assertOk(docEl.getAttribute('data-agzh-prism') === null, '停用后应清除 data-agzh-prism');
  assertOk(!byId.get('agzh-skin-style'), '停用后应卸载样式节点');
  assertOk(!byId.get('agzh-aura-bar'), '停用后应卸载语义余晖条');
  assertOk(bodyEl.classList.contains('theme-light'), '停用后应还原宿主原始 theme-light 类名');
});

test('2. Rust skin_manager.rs 棱镜切面编译器令牌、守卫与语法结构完整', () => {
  assertOk(Boolean(fs && path), 'Node 内置模块不可用');
  const rsPath = path!.resolve(rootDir, 'src-tauri/src/modules/studio/skin_manager.rs');
  const rs = fs!.readFileSync(rsPath, 'utf8');

  for (const token of [
    '--agzh-facet-top',
    '--agzh-facet-edge',
    '--agzh-well-bg',
    '--agzh-kbd-bg',
    '--agzh-chip-bg',
    '--agzh-spring',
    '"prism": {',
    'prism_facets',
    'rim_glow',
    'code_enhance',
    'ambient_aura',
    'backdrop_mode',
    'test_prism_facets_tokens_compiled_for_all_builtin_skins',
  ]) {
    assertOk(rs.includes(token), `skin_manager.rs 缺少必要标识符或测试: ${token}`);
  }

  const compileSection = rs.slice(rs.indexOf('pub fn compile_skin'), rs.indexOf('#[cfg(test)]'));
  assertOk(!compileSection.includes('z-index: 9980'), 'compile_skin 不得包含 z-index: 9980');
  assertOk(!compileSection.includes('z-index: 9985'), 'compile_skin 不得包含 z-index: 9985');
  assertOk(!compileSection.includes('--text-sm:'), 'compile_skin 不得强改 --text-sm');
});

console.log(`\n📦 prismSkinEngine.test.ts: ${passed} passed, ${failed} failed`);
if (failed > 0) {
  nodeProc?.exit(1);
}
