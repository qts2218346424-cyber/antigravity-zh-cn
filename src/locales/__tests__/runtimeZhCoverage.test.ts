/**
 * 客户端运行时汉化引擎 (runtime-zh.js) 与多语种词典覆盖率回归测试
 * 运行命令: npm test
 */
import agyZhCn from '../../../resources/antigravity-zh-CN.json';
import agyZhTw from '../../../resources/antigravity-zh-TW.json';
import agyZhHk from '../../../resources/antigravity-zh-HK.json';
import agyRules from '../../../resources/rules-zh-CN.json';
import desktopZhCn from '../../../resources/desktop-zh-CN.json';

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

function assertEqual(actual: unknown, expected: unknown, label: string): void {
  if (actual !== expected) {
    throw new Error(
      `${label}\n  期望: ${JSON.stringify(expected)}\n  实际: ${JSON.stringify(actual)}`,
    );
  }
}

// 构建轻量级 DOM 模拟环境以真实驱动 runtime-zh.js 的 TreeWalker 与节点翻译引擎
class MockNode {
  nodeType: number;
  nodeValue: string | null = null;
  parentElement: MockElement | null = null;
  childNodes: MockNode[] = [];

  constructor(nodeType: number) {
    this.nodeType = nodeType;
  }

  get previousSibling(): MockNode | null {
    if (!this.parentElement) return null;
    const idx = this.parentElement.childNodes.indexOf(this);
    return idx > 0 ? this.parentElement.childNodes[idx - 1] : null;
  }

  get nextSibling(): MockNode | null {
    if (!this.parentElement) return null;
    const idx = this.parentElement.childNodes.indexOf(this);
    return idx >= 0 && idx < this.parentElement.childNodes.length - 1
      ? this.parentElement.childNodes[idx + 1]
      : null;
  }

  get textContent(): string {
    if (this.nodeType === 3) return this.nodeValue ?? '';
    return this.childNodes.map((c) => c.textContent).join('');
  }

  set textContent(val: string) {
    if (this.nodeType === 3) {
      this.nodeValue = val;
      return;
    }
    const textNode = new MockTextNode(val);
    textNode.parentElement = this as unknown as MockElement;
    this.childNodes = [textNode];
  }
}

class MockTextNode extends MockNode {
  constructor(text: string) {
    super(3);
    this.nodeValue = text;
  }
}

class MockElement extends MockNode {
  tagName: string;
  attrs = new Map<string, string>();

  constructor(tagName: string) {
    super(1);
    this.tagName = tagName.toUpperCase();
  }

  appendChild<T extends MockNode>(child: T): T {
    child.parentElement = this;
    this.childNodes.push(child);
    return child;
  }

  get children(): MockElement[] {
    return this.childNodes.filter((c): c is MockElement => c.nodeType === 1);
  }

  setAttribute(name: string, val: string): void {
    this.attrs.set(name, val);
  }

  getAttribute(name: string): string | null {
    return this.attrs.get(name) ?? null;
  }

  matches(selector: string): boolean {
    const parts = selector.split(',').map((s) => s.trim().toLowerCase());
    const tagLower = this.tagName.toLowerCase();
    return parts.some((p) => p === tagLower);
  }

  closest(selector: string): MockElement | null {
    let cur: MockElement | null = this;
    while (cur) {
      if (cur.matches(selector)) return cur;
      cur = cur.parentElement;
    }
    return null;
  }

  querySelectorAll(_selector: string): MockElement[] {
    return [];
  }
}

async function createRuntimeHarness() {
  const dynImport = new Function('m', 'return import(m)') as (
    m: string,
  ) => Promise<Record<string, unknown>>;
  const fsMod = (await dynImport('node:fs')) as {
    readFileSync: (p: URL, enc: string) => string;
  };
  const vmMod = (await dynImport('node:vm')) as {
    runInNewContext: (code: string, ctx: Record<string, unknown>) => void;
  };

  const dict = agyZhCn as Record<string, string>;
  const rules = agyRules as [string, string][];
  const runtimeUrl = new URL('../../../resources/runtime-zh.js', import.meta.url);
  const runtimeCode = fsMod.readFileSync(runtimeUrl, 'utf8');

  const body = new MockElement('body');
  const docEl = new MockElement('html');
  docEl.appendChild(body);

  const mockDocument = {
    readyState: 'complete',
    documentElement: docEl,
    body,
    addEventListener() {},
    createTextNode(text: string) {
      return new MockTextNode(text);
    },
    createTreeWalker(
      root: MockNode,
      _whatToShow: number,
      filter?: { acceptNode?: (n: MockNode) => number },
    ) {
      const textNodes: MockNode[] = [];
      const collect = (n: MockNode) => {
        if (n.nodeType === 3) {
          const res = filter?.acceptNode ? filter.acceptNode(n) : 1;
          if (res === 1) textNodes.push(n);
        } else {
          for (const child of n.childNodes) collect(child);
        }
      };
      collect(root);
      let idx = -1;
      return {
        nextNode() {
          idx += 1;
          return idx < textNodes.length ? textNodes[idx] : null;
        },
      };
    },
  };

  class MockMutationObserver {
    observe() {}
    disconnect() {}
  }

  const sandbox: Record<string, unknown> = {
    window: null as unknown,
    document: mockDocument,
    Node: MockNode,
    Element: MockElement,
    NodeFilter: { SHOW_TEXT: 4, FILTER_ACCEPT: 1, FILTER_REJECT: 2 },
    MutationObserver: MockMutationObserver,
    WeakSet,
    Set,
    Map,
    Object,
    RegExp,
    Array,
    console: { log() {}, warn() {}, error() {} },
    performance: { now: () => Date.now() },
    setTimeout: () => 0,
    clearTimeout: () => {},
    setInterval: () => 0,
    clearInterval: () => {},
    __AGY_ZH_LANG__: 'zh-CN',
    __AGY_ZH_DICT__: dict,
    __AGY_ZH_RULES__: rules,
  };
  sandbox.window = sandbox;
  sandbox.addEventListener = () => {};

  vmMod.runInNewContext(runtimeCode, sandbox);

  const runOnNode = (el: MockElement): string => {
    body.childNodes = [];
    body.appendChild(el);
    sandbox.__agyZhInited = true;
    vmMod.runInNewContext(runtimeCode, sandbox);
    return el.textContent;
  };

  const translateSingleText = (text: string): string => {
    const span = new MockElement('span');
    span.appendChild(new MockTextNode(text));
    return runOnNode(span);
  };

  return { runOnNode, translateSingleText };
}

async function main() {
  const { runOnNode, translateSingleText } = await createRuntimeHarness();

  test('1. 资源文件完整性、三语词典同步性与正则规则可编译校验', () => {
    const kanaRegex = /[\u3040-\u309F\u30A1-\u30FA]/;
    const cnDict = agyZhCn as Record<string, string>;
    const twDict = agyZhTw as Record<string, string>;
    const hkDict = agyZhHk as Record<string, string>;

    for (const [k, v] of Object.entries(cnDict)) {
      if (typeof v === 'string' && kanaRegex.test(v)) {
        throw new Error(`antigravity-zh-CN.json 检测到日文假名残留: ${k} -> ${v}`);
      }
    }

    if (
      Object.keys(cnDict).length !== Object.keys(twDict).length &&
      Object.keys(twDict).length < 4500
    ) {
      throw new Error('繁体词典词条规模异常');
    }
    if (Object.keys(hkDict).length < 4500) {
      throw new Error('香港繁体词典词条规模异常');
    }

    const rules = agyRules as [string, string][];
    for (const [pattern, repl] of rules) {
      new RegExp(pattern);
      if (typeof repl !== 'string') {
        throw new Error(`正则替换值不是字符串: ${pattern}`);
      }
    }
  });

  test('2. 本地与远程会话设置（含内联超链接拆分节点与段末英文句点自动转中文句号）', () => {
    const p = new MockElement('p');
    p.appendChild(
      new MockTextNode('Configure what the agent can do in local and remote conversations. '),
    );
    const link = new MockElement('a');
    link.appendChild(new MockTextNode('Learn more'));
    p.appendChild(link);
    p.appendChild(new MockTextNode('.'));

    const result = runOnNode(p);
    assertEqual(
      result,
      '配置智能体在本地与远程会话中可执行的操作。 了解详情。',
      '内联超链接复合段落汉化及句末半角句点收尾失败',
    );
  });

  test('3. 内置浏览器子智能体允许/拒绝 URL 说明与项目外部会话设置汉化', () => {
    assertEqual(
      translateSingleText(
        'Configure allowed and denied URLs for the browser subagent. It runs in the built-in browser, so no separate browser install is needed.',
      ),
      '配置浏览器子智能体的允许和拒绝访问网址列表。它在内置浏览器中运行，无需单独安装外部浏览器。',
      '内置浏览器子智能体设置文案未汉化',
    );

    assertEqual(
      translateSingleText('Settings for conversations outside of projects.'),
      '项目外部会话的设置。',
      '项目外部会话设置文案未汉化',
    );
  });

  test('4. SSH 远程主机新建项目菜单、悬浮提示卡片与桌面端菜单词典汉化', () => {
    assertEqual(translateSingleText('SSH Host...'), 'SSH 主机...', 'SSH Host... 菜单未汉化');
    assertEqual(
      translateSingleText(
        "Create a project on a machine you reach over SSH. It opens in that host's own window.",
      ),
      '在通过 SSH 连接的远程主机上创建项目。该项目将在对应主机的独立窗口中打开。',
      'SSH 主机悬浮说明卡片未汉化',
    );
    assertEqual(
      translateSingleText('Connecting to SSH host: dev-server...'),
      '正在连接 SSH 主机 dev-server...',
      'SSH 动态连接状态未汉化',
    );

    const desktopDict = desktopZhCn as {
      menu: Record<string, string>;
      dialog: Record<string, string>;
    };
    assertEqual(desktopDict.menu['SSH Host...'], 'SSH 主机...', 'desktop-zh-CN.json 缺失 SSH Host...');
    assertEqual(
      desktopDict.dialog['SSH setup failed'],
      'SSH 环境配置失败',
      'desktop-zh-CN.json 缺失 SSH setup failed',
    );
  });

  test('5. 插件市场卡片完整描述、省略号截断描述与 "+ See N more" 展开按钮全覆盖', () => {
    assertEqual(translateSingleText('+ See 1 more'), '+ 展开另外 1 项', '+ See 1 more 未汉化');
    assertEqual(translateSingleText('See 1 more'), '展开另外 1 项', 'See 1 more 未汉化');
    assertEqual(translateSingleText('+ See 8 more'), '+ 展开另外 8 项', '+ See 8 more 未汉化');
    assertEqual(translateSingleText('- See less'), '- 收起', '- See less 未汉化');

    const fullSamples: [string, string][] = [
      [
        "Teamwork Graph CLI is Atlassian's agent-first interface to your entire work context: Jira issues, Confluence pages, Bitbucket PRs, along with your connected third-party data sources. Purpose-built for coding agents like Antigravity (terminal-first, fast).",
        'Teamwork Graph CLI 是 Atlassian 面向智能体打造的全局工作上下文接口，涵盖 Jira 议题、Confluence 页面、Bitbucket PR 及已连接的第三方数据源，专为 Antigravity 等编程智能体量身构建。',
      ],
      [
        'Connect Antigravity to Dropbox to search, inspect, summarize, share, collect uploads, organize folders, and clean up files with confirmation for write actions.',
        '将 Antigravity 连接至 Dropbox，支持搜索、查看、摘要生成、分享、收集上传、整理文件夹，并在获得确认后安全清理文件。',
      ],
      [
        'The product development system for teams and agents. Manage issues, projects, and documents across your Linear workspace from Antigravity.',
        '面向团队与智能体的产品研发协作系统。直接从 Antigravity 跨 Linear 工作区管理议题、项目与文档。',
      ],
      [
        'Plan and track work in monday.com from Antigravity: create, update and assign items, write docs, and build forms that turn requests into items.',
        '直接从 Antigravity 在 monday.com 中规划和跟踪工作：创建、更新并指派事项，编写文档，并构建将需求自动转化为事项的表单。',
      ],
      [
        'Connect Antigravity to your Notion workspace with the Notion MCP server, plus skills for research, documentation, meeting prep, specs, trackers, and project updates.',
        '通过 Notion MCP 服务将 Antigravity 连接至您的 Notion 工作区，并提供调研、文档编写、会议准备、技术规范、进度追踪与项目更新等技能。',
      ],
      [
        'Create and send proposals, quotes, and contracts for e-signature. Track signing progress and identify documents that need follow-up.',
        '创建并发送提案、报价单与电子签名合同，实时追踪签署进度并识别需要跟进的文档。',
      ],
    ];

    for (const [enText, expectedZh] of fullSamples) {
      assertEqual(
        translateSingleText(enText),
        expectedZh,
        `完整市场描述汉化失败: ${enText.slice(0, 40)}`,
      );
    }

    const truncatedSamples = [
      "Teamwork Graph CLI is Atlassian's agent-first i...",
      'Connect Antigravity to Dropbox to search, insp...',
      'The product development system for teams an...',
      'Plan and track work in monday.com from Antig...',
      'Connect Antigravity to your Notion workspace ...',
      'Create and send proposals, quotes, and contr...',
    ];
    for (const sample of truncatedSamples) {
      const tr = translateSingleText(sample);
      if (!/[\u4e00-\u9fa5]/.test(tr) || tr === sample) {
        throw new Error(`省略号截断描述未能命中中文容错: ${sample} -> ${tr}`);
      }
    }
  });

  if (failed > 0) {
    throw new Error(`运行时汉化回归测试失败: ${failed} 项未通过 (通过 ${passed} 项)`);
  }
}

main();
