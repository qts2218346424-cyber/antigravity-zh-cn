/**
 * 国际化词典完整性、品牌命名一致性与日文零残留校验测试
 * 运行命令: npm test
 */
import zh from '../zh.json';
import en from '../en.json';
import agyZhCn from '../../../resources/antigravity-zh-CN.json';
import agyZhTw from '../../../resources/antigravity-zh-TW.json';
import agyZhHk from '../../../resources/antigravity-zh-HK.json';
import agyRules from '../../../resources/rules-zh-CN.json';

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

test('3. 客户端多语种汉化词典 (CN/TW/HK) 与正则规则 JSON 结构完整且覆盖新增快捷键及地址栏词条', () => {
  const cnDict = agyZhCn as Record<string, string>;
  const twDict = agyZhTw as Record<string, string>;
  const hkDict = agyZhHk as Record<string, string>;
  const rules = agyRules as [string, string][];

  const expectedCnEntries: Record<string, string> = {
    'Submit Prompt (Alternate to Enter)': '提交提示词（Enter 备用快捷键）',
    'Enter always submits. This adds a second shortcut.': '按 Enter 键始终提交。此项可添加第二个快捷键。',
    'Jump to Previous Prompt': '跳转到上一条提示词',
    'Jump to Next Prompt': '跳转到下一条提示词',
    'Side Question Selection': '对所选内容发起侧边提问',
    'Pin / Unpin Conversation': '固定 / 取消固定会话',
    'Terminal: Select All': '终端：全选',
    'Search or enter a URL': '搜索或输入网址',
    "Good to see you. What's next?": '很高兴见到你。接下来做什么？',
    'Hey there, what should we build today?': '你好，今天想构建些什么？',
    'Welcome back. Where should we pick up?': '欢迎回来。我们从哪里继续？',
    'Weekly limit': '每周配额',
    'Daily limit': '每日配额',
    '5h limit': '5 小时配额',
    'Argon that may offload routine steps to Hydrogen. Same Argon-level quality, fewer tokens used.':
      '可将常规步骤卸载给 Hydrogen 处理的 Argon 模型。保持同等 Argon 级质量，消耗更少 Token。',
    'SSH Host': 'SSH 主机',
    'Search Hosts…': '搜索主机...',
    'No hosts in ~/.ssh/config yet': '~/.ssh/config 中暂无主机',
    'Connect to SSH Host…': '连接到 SSH 主机...',
    'Knowledge Work': '知识工作',
    'Simplified interface for research, writing, and everyday tasks.':
      '面向研究、写作与日常任务的精简界面。',
    'Software Engineering': '软件工程',
    'Full interface for coding, developer tools, and managing agents.':
      '面向编程、开发者工具与智能体管理的完整界面。',
    Extra: '超高',
    Max: '最高',
    'AI Noise-cancelling Input (ASUS Utility)': 'AI 降噪输入 (华硕实用程序)',
    'Uses your local files and tools. Schedules only.': '使用您的本地文件与工具。仅支持定时计划。',
    'Runs even when your computer is off. Schedules and events.':
      '即使您的电脑关机也能继续运行。支持定时计划与事件触发。',
    'Connect Antigravity to your Notion workspace with the Notion MCP server, plus skills for research, documentation, meeting prep, specs, trackers, and project updates.':
      '通过 Notion MCP 服务器将 Antigravity 连接至您的 Notion 工作区，并提供涵盖资料调研、文档撰写、会议筹备、技术方案、任务追踪与项目进展更新的专属技能。',
    'Create and send proposals, quotes, and contracts for e-signature. Track signing progress and identify documents that need follow-up.':
      '创建并发送商业提案、报价单与电子签约合同，实时追踪签署进度并自动识别需要跟进催办的文档。',
    'Official Trello plugin with the Trello MCP server and a skill for boards, lists, cards, checklists, Inbox, and Planner.':
      'Trello 官方插件，内置 Trello MCP 服务器及专属技能，轻松管理看板、列表、卡片、检查清单、收件箱与日程规划器。',
    'Build and deploy on Netlify: functions, edge functions, blobs, database, identity, forms, image CDN, caching, and AI Gateway, plus the Netlify MCP server.':
      '在 Netlify 上构建与部署应用：支持云函数、边缘函数、Blob 存储、数据库、身份认证、表单、图像 CDN、缓存策略与 AI 网关，内置 Netlify MCP 服务器。',
    "Deploy, configure, monitor, and troubleshoot apps, databases, and infrastructure on Railway from Antigravity with Railway's agent skill and hosted MCP server.":
      '借助 Railway 智能体技能与官方托管的 MCP 服务器，在 Antigravity 中一站式部署、配置、监控并排查 Railway 上的应用、数据库与基础设施故障。',
  };

  for (const [enKey, expectedZh] of Object.entries(expectedCnEntries)) {
    if (cnDict[enKey] !== expectedZh) {
      throw new Error(`antigravity-zh-CN.json 词条 [${enKey}] 期望 "${expectedZh}"，实际为 "${cnDict[enKey]}"`);
    }
    if (!twDict[enKey]?.trim()) {
      throw new Error(`antigravity-zh-TW.json 缺失词条: ${enKey}`);
    }
    if (!hkDict[enKey]?.trim()) {
      throw new Error(`antigravity-zh-HK.json 缺失词条: ${enKey}`);
    }
  }

  for (const [pattern, replacement] of rules) {
    // 校验所有正则表达式均可正常编译
    new RegExp(pattern, 'i');
    if (typeof replacement !== 'string') {
      throw new Error(`rules-zh-CN.json 存在非法替换目标: ${pattern}`);
    }
  }
});

async function runRuntimeEngineTest(): Promise<void> {
  const dynImport = new Function('m', 'return import(m)') as (m: string) => Promise<Record<string, unknown>>;
  const fsMod = (await dynImport('node:fs')) as { readFileSync: (p: URL, enc: string) => string };
  const vmMod = (await dynImport('node:vm')) as { runInNewContext: (code: string, ctx: Record<string, unknown>) => void };

  const cnDict = agyZhCn as Record<string, string>;
  const rules = agyRules as [string, string][];
  const runtimeUrl = new URL('../../../resources/runtime-zh.js', import.meta.url);
  const runtimeCode = fsMod.readFileSync(runtimeUrl, 'utf8');

  class MockNode {
    nodeType: number;
    nodeValue: string | null = null;
    parentElement: MockElement | null = null;
    constructor(nodeType: number) {
      this.nodeType = nodeType;
    }
  }

  class MockTextNode extends MockNode {
    constructor(text: string, parent: MockElement | null = null) {
      super(3);
      this.nodeValue = text;
      this.parentElement = parent;
    }
  }

  class MockElement extends MockNode {
    tagName: string;
    attrs = new Map<string, string>();
    children: MockElement[] = [];
    childNodes: MockNode[] = [];
    placeholder = '';
    value = '';

    constructor(tagName: string) {
      super(1);
      this.tagName = tagName.toUpperCase();
    }

    get textContent(): string {
      return this.childNodes
        .map((n) => (n.nodeType === 3 ? n.nodeValue || '' : (n as MockElement).textContent))
        .join('');
    }

    set textContent(v: string) {
      this.childNodes = [new MockTextNode(v, this)];
      this.children = [];
    }

    appendText(t: string): MockTextNode {
      const tn = new MockTextNode(t, this);
      this.childNodes.push(tn);
      return tn;
    }

    appendChildEl(el: MockElement): MockElement {
      el.parentElement = this;
      this.children.push(el);
      this.childNodes.push(el);
      return el;
    }

    setAttribute(name: string, val: string): void {
      this.attrs.set(name, val);
      if (name === 'placeholder') this.placeholder = val;
      if (name === 'value') this.value = val;
    }

    getAttribute(name: string): string | null {
      return this.attrs.has(name) ? (this.attrs.get(name) ?? null) : null;
    }

    matches(selector: string): boolean {
      const parts = selector.split(',').map((s) => s.trim());
      for (const p of parts) {
        if (p.startsWith('[') && p.endsWith(']')) {
          const attrName = p.slice(1, -1).split('=')[0].trim();
          if (this.attrs.has(attrName)) return true;
        } else if (p === 'input[type="button"]') {
          if (this.tagName === 'INPUT' && this.getAttribute('type') === 'button') return true;
        } else if (p === 'input[type="submit"]') {
          if (this.tagName === 'INPUT' && this.getAttribute('type') === 'submit') return true;
        } else if (p.toUpperCase() === this.tagName) {
          return true;
        }
      }
      return false;
    }

    closest(selector: string): MockElement | null {
      let cur: MockElement | null = this;
      while (cur) {
        if (cur.matches(selector)) return cur;
        cur = cur.parentElement;
      }
      return null;
    }

    querySelectorAll(selector: string): MockElement[] {
      const out: MockElement[] = [];
      const visit = (el: MockElement) => {
        for (const child of el.children) {
          if (child.matches(selector)) out.push(child);
          visit(child);
        }
      };
      visit(this);
      return out;
    }
  }

  const body = new MockElement('BODY');
  const row1 = body.appendChildEl(new MockElement('DIV'));
  const tSubmit = row1.appendText('Submit Prompt (Alternate to Enter)');
  const tDesc = body.appendChildEl(new MockElement('DIV')).appendText('Enter always submits. This adds a second shortcut.');
  const tPrev = body.appendChildEl(new MockElement('DIV')).appendText('Jump to Previous Prompt');
  const tNext = body.appendChildEl(new MockElement('DIV')).appendText('Jump to Next Prompt');
  const tSide = body.appendChildEl(new MockElement('DIV')).appendText('Side Question Selection');
  const tPin = body.appendChildEl(new MockElement('DIV')).appendText('Pin / Unpin Conversation');
  const tTerm = body.appendChildEl(new MockElement('DIV')).appendText('Terminal: Select All');
  // 测试未显式写入全句但满足通用模块前缀组合的词条 (Browser + Reload -> 浏览器：重新加载)
  const tScopedFallback = body.appendChildEl(new MockElement('DIV')).appendText('Browser: Reload');
  // 测试未知子命令绝不拼接成半中半英
  const tUnknownScoped = body.appendChildEl(new MockElement('DIV')).appendText('Terminal: UnknownActionXYZ');

  const urlInput = body.appendChildEl(new MockElement('INPUT'));
  urlInput.setAttribute('type', 'text');
  urlInput.setAttribute('placeholder', 'Search or enter a URL');
  urlInput.value = 'Select All'; // 模拟用户刚好输入了与词典键同名的英文，绝不可被误翻译

  const ariaInput = body.appendChildEl(new MockElement('DIV'));
  ariaInput.setAttribute('aria-placeholder', 'Search or enter a URL');

  // 覆盖 v2.33.0 五大界面区域（首页问候语、配额时间窗口、Argon 分流气泡、SSH 主机菜单、界面布局卡片）
  const tGreet1 = body.appendChildEl(new MockElement('DIV')).appendText("Good to see you, xinxin. What's next?");
  const tGreet2 = body.appendChildEl(new MockElement('DIV')).appendText('Hey xinxin, what should we build today?');
  const tGreet3 = body.appendChildEl(new MockElement('DIV')).appendText('Welcome back, xinxin. Where should we pick up?');
  const tWeeklyLimit = body.appendChildEl(new MockElement('SPAN')).appendText('Weekly limit');
  const tFiveHourLimit = body.appendChildEl(new MockElement('SPAN')).appendText('5h limit');
  const tDynamicWindowLimit = body.appendChildEl(new MockElement('SPAN')).appendText('12h limit');
  const tCompoundLimitReset = body.appendChildEl(new MockElement('SPAN')).appendText('5h limit, resets in 4h 30m');
  const tArgonOffload = body
    .appendChildEl(new MockElement('DIV'))
    .appendText('Argon that may offload routine steps to Hydrogen. Same Argon-level quality, fewer tokens used.');
  const tCarbonOffload = body
    .appendChildEl(new MockElement('DIV'))
    .appendText('Carbon that may offload routine steps to Hydrogen. Same Carbon-level quality, fewer tokens used.');
  const tSshHost = body.appendChildEl(new MockElement('SPAN')).appendText('SSH Host');
  const tNoSshHosts = body.appendChildEl(new MockElement('DIV')).appendText('No hosts in ~/.ssh/config yet');
  const tConnectSsh = body.appendChildEl(new MockElement('SPAN')).appendText('Connect to SSH Host\u2026');
  const sshSearchInput = body.appendChildEl(new MockElement('INPUT'));
  sshSearchInput.setAttribute('type', 'text');
  sshSearchInput.setAttribute('placeholder', 'Search Hosts\u2026');
  const tKnowledgeWork = body.appendChildEl(new MockElement('SPAN')).appendText('Knowledge Work');
  const tKnowledgeDesc = body
    .appendChildEl(new MockElement('DIV'))
    .appendText('Simplified interface for research, writing, and everyday tasks.');
  const tSoftEng = body.appendChildEl(new MockElement('SPAN')).appendText('Software Engineering');
  const tSoftEngDesc = body
    .appendChildEl(new MockElement('DIV'))
    .appendText('Full interface for coding, developer tools, and managing agents.');
  const tEffortExtra = body.appendChildEl(new MockElement('SPAN')).appendText('Extra');
  const tModelExtra = body.appendChildEl(new MockElement('SPAN')).appendText('Gemini 4 Carbon (Extra)');
  const tModelXHigh = body.appendChildEl(new MockElement('SPAN')).appendText('Gemini 4 Carbon (xhigh)');
  const tEffortCtx = body.appendChildEl(new MockElement('SPAN')).appendText('Extra \u00b7 1M');
  const tMicComm = body
    .appendChildEl(new MockElement('DIV'))
    .appendText('Communications - 麦克风 (C-Media(R) Audio) (0b05:6208)');
  const tMicPlain = body
    .appendChildEl(new MockElement('DIV'))
    .appendText('麦克风 (C-Media(R) Audio) (0b05:6208)');
  const tMicAsus = body
    .appendChildEl(new MockElement('DIV'))
    .appendText('AI Noise-cancelling Input (ASUS Utility)');
  const tMicSysDefault = body
    .appendChildEl(new MockElement('DIV'))
    .appendText('System default (AI Noise-cancelling Input (ASUS Utility))');
  const tLocalSchedule = body
    .appendChildEl(new MockElement('SPAN'))
    .appendText('Uses your local files and tools. Schedules only.');
  const tNotionTruncated = body
    .appendChildEl(new MockElement('SPAN'))
    .appendText('Connect Antigravity to your Notion workspace ...');
  const tPandaTruncated = body
    .appendChildEl(new MockElement('SPAN'))
    .appendText('Create and send proposals, quotes, and contr...');
  const tTrelloTruncated = body
    .appendChildEl(new MockElement('SPAN'))
    .appendText('Official Trello plugin with the Trello MCP serve...');
  const tNetlifyTruncated = body
    .appendChildEl(new MockElement('SPAN'))
    .appendText('Build and deploy on Netlify: functions, edge fu...');
  const tRailwayTruncated = body
    .appendChildEl(new MockElement('SPAN'))
    .appendText('Deploy, configure, monitor, and troubleshoot a...');

  let observerCallback: ((mutations: unknown[]) => void) | null = null;

  const collectTextNodes = (root: MockNode): MockTextNode[] => {
    const list: MockTextNode[] = [];
    const walk = (n: MockNode) => {
      if (n.nodeType === 3) {
        list.push(n as MockTextNode);
      } else if (n instanceof MockElement) {
        for (const c of n.childNodes) walk(c);
      }
    };
    walk(root);
    return list;
  };

  const sandbox: Record<string, unknown> = {
    NodeFilter: { SHOW_TEXT: 4, FILTER_ACCEPT: 1, FILTER_REJECT: 2 },
    Node: MockNode,
    Element: MockElement,
    MutationObserver: class {
      constructor(cb: (mutations: unknown[]) => void) {
        observerCallback = cb;
      }
      observe() {}
      disconnect() {}
    },
    WeakSet,
    Set,
    Map,
    RegExp,
    Object,
    Array,
    console: { log() {}, warn() {}, error() {} },
    setTimeout: () => 0,
    clearTimeout: () => {},
    setInterval: () => 0,
    clearInterval: () => {},
    performance: { now: () => 0 },
    localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
    document: {
      readyState: 'complete',
      body,
      documentElement: body,
      addEventListener() {},
      createTextNode: (d: string) => new MockTextNode(d),
      createTreeWalker: (
        root: MockNode,
        _what: number,
        filter: { acceptNode: (n: MockTextNode) => number },
      ) => {
        const all = collectTextNodes(root).filter((n) => filter.acceptNode(n) === 1);
        let idx = -1;
        return {
          nextNode() {
            idx += 1;
            return idx < all.length ? all[idx] : null;
          },
        };
      },
    },
  };
  sandbox.window = {
    __AGY_ZH_DICT__: cnDict,
    __AGY_ZH_RULES__: rules,
    __AGY_ZH_LANG__: 'zh-CN',
    addEventListener() {},
    document: sandbox.document,
  };

  vmMod.runInNewContext(runtimeCode, sandbox);

  if (tSubmit.nodeValue !== '提交提示词（Enter 备用快捷键）') {
    throw new Error(`Submit Prompt 翻译不符: ${tSubmit.nodeValue}`);
  }
  if (tDesc.nodeValue !== '按 Enter 键始终提交。此项可添加第二个快捷键。') {
    throw new Error(`副标题翻译不符: ${tDesc.nodeValue}`);
  }
  if (tPrev.nodeValue !== '跳转到上一条提示词') {
    throw new Error(`Jump to Previous Prompt 翻译不符: ${tPrev.nodeValue}`);
  }
  if (tNext.nodeValue !== '跳转到下一条提示词') {
    throw new Error(`Jump to Next Prompt 翻译不符: ${tNext.nodeValue}`);
  }
  if (tSide.nodeValue !== '对所选内容发起侧边提问') {
    throw new Error(`Side Question Selection 翻译不符: ${tSide.nodeValue}`);
  }
  if (tPin.nodeValue !== '固定 / 取消固定会话') {
    throw new Error(`Pin / Unpin Conversation 翻译不符: ${tPin.nodeValue}`);
  }
  if (tTerm.nodeValue !== '终端：全选') {
    throw new Error(`Terminal: Select All 翻译不符: ${tTerm.nodeValue}`);
  }
  if (tScopedFallback.nodeValue !== '浏览器：重新加载') {
    throw new Error(`通用分类前缀组合翻译不符: ${tScopedFallback.nodeValue}`);
  }
  if (tUnknownScoped.nodeValue !== 'Terminal: UnknownActionXYZ') {
    throw new Error(`未知子动作不应被半汉化: ${tUnknownScoped.nodeValue}`);
  }
  if (urlInput.getAttribute('placeholder') !== '搜索或输入网址' || urlInput.placeholder !== '搜索或输入网址') {
    throw new Error(`地址栏 placeholder 翻译不符: ${urlInput.getAttribute('placeholder')}`);
  }
  if (ariaInput.getAttribute('aria-placeholder') !== '搜索或输入网址') {
    throw new Error(`aria-placeholder 翻译不符: ${ariaInput.getAttribute('aria-placeholder')}`);
  }
  if (urlInput.value !== 'Select All') {
    throw new Error(`严重缺陷：用户输入 value 被误篡改为 ${urlInput.value}`);
  }
  if (tGreet1.nodeValue !== '很高兴见到你，xinxin。接下来做什么？') {
    throw new Error(`首页问候语1翻译不符: ${tGreet1.nodeValue}`);
  }
  if (tGreet2.nodeValue !== '你好 xinxin，今天想构建些什么？') {
    throw new Error(`首页问候语2翻译不符: ${tGreet2.nodeValue}`);
  }
  if (tGreet3.nodeValue !== '欢迎回来，xinxin。我们从哪里继续？') {
    throw new Error(`首页问候语3翻译不符: ${tGreet3.nodeValue}`);
  }
  if (tWeeklyLimit.nodeValue !== '每周配额' || tFiveHourLimit.nodeValue !== '5 小时配额' || tDynamicWindowLimit.nodeValue !== '12 小时配额') {
    throw new Error(`配额限制窗口翻译不符: ${tWeeklyLimit.nodeValue} / ${tFiveHourLimit.nodeValue} / ${tDynamicWindowLimit.nodeValue}`);
  }
  if (tCompoundLimitReset.nodeValue !== '5 小时配额，4 小时 30 分钟后重置') {
    throw new Error(`复合配额重置文本翻译不符: ${tCompoundLimitReset.nodeValue}`);
  }
  if (tArgonOffload.nodeValue !== '可将常规步骤卸载给 Hydrogen 处理的 Argon 模型。保持同等 Argon 级质量，消耗更少 Token。') {
    throw new Error(`Argon 分流提示翻译不符: ${tArgonOffload.nodeValue}`);
  }
  if (tCarbonOffload.nodeValue !== '可将常规步骤卸载给 Hydrogen 处理的 Carbon 模型。保持同等 Carbon 级质量，消耗更少 Token。') {
    throw new Error(`泛化模型分流提示翻译不符: ${tCarbonOffload.nodeValue}`);
  }
  if (tSshHost.nodeValue !== 'SSH 主机' || tNoSshHosts.nodeValue !== '~/.ssh/config 中暂无主机' || tConnectSsh.nodeValue !== '连接到 SSH 主机...') {
    throw new Error(`SSH 菜单文本翻译不符: ${tSshHost.nodeValue} / ${tNoSshHosts.nodeValue} / ${tConnectSsh.nodeValue}`);
  }
  if (sshSearchInput.getAttribute('placeholder') !== '搜索主机...') {
    throw new Error(`SSH 搜索框 placeholder 翻译不符: ${sshSearchInput.getAttribute('placeholder')}`);
  }
  if (
    tKnowledgeWork.nodeValue !== '知识工作' ||
    tKnowledgeDesc.nodeValue !== '面向研究、写作与日常任务的精简界面。' ||
    tSoftEng.nodeValue !== '软件工程' ||
    tSoftEngDesc.nodeValue !== '面向编程、开发者工具与智能体管理的完整界面。'
  ) {
    throw new Error(`界面布局卡片翻译不符: ${tKnowledgeWork.nodeValue} / ${tSoftEng.nodeValue}`);
  }
  if (
    tEffortExtra.nodeValue !== '超高' ||
    tModelExtra.nodeValue !== 'Gemini 4 Carbon（超高）' ||
    tModelXHigh.nodeValue !== 'Gemini 4 Carbon（超高）' ||
    tEffortCtx.nodeValue !== '超高 · 1M'
  ) {
    throw new Error(
      `模型思考等级翻译不符: ${tEffortExtra.nodeValue} / ${tModelExtra.nodeValue} / ${tModelXHigh.nodeValue} / ${tEffortCtx.nodeValue}`,
    );
  }
  if (
    tMicComm.nodeValue !== '通信设备 - 麦克风 (C-Media(R) 音频) (0b05:6208)' ||
    tMicPlain.nodeValue !== '麦克风 (C-Media(R) 音频) (0b05:6208)' ||
    tMicAsus.nodeValue !== 'AI 降噪输入 (华硕实用程序)' ||
    tMicSysDefault.nodeValue !== '系统默认 (AI 降噪输入 (华硕实用程序))'
  ) {
    throw new Error(
      `麦克风设备名称翻译不符: ${tMicComm.nodeValue} / ${tMicPlain.nodeValue} / ${tMicAsus.nodeValue} / ${tMicSysDefault.nodeValue}`,
    );
  }
  if (tLocalSchedule.nodeValue !== '使用您的本地文件与工具。仅支持定时计划。') {
    throw new Error(`自动化本地计划说明翻译不符: ${tLocalSchedule.nodeValue}`);
  }
  if (
    !tNotionTruncated.nodeValue?.startsWith('通过 Notion MCP 服务器') ||
    !tPandaTruncated.nodeValue?.startsWith('创建并发送商业提案') ||
    !tTrelloTruncated.nodeValue?.startsWith('Trello 官方插件') ||
    !tNetlifyTruncated.nodeValue?.startsWith('在 Netlify 上构建与部署应用') ||
    !tRailwayTruncated.nodeValue?.startsWith('借助 Railway 智能体技能')
  ) {
    throw new Error(
      `插件市场截断卡片描述翻译不符: ${tNotionTruncated.nodeValue} / ${tPandaTruncated.nodeValue}`,
    );
  }

  // 验证单节点 attributes MutationObserver (m.target 为独立 input 自身，无任何子节点) 依然能即时翻译
  const lateInput = new MockElement('INPUT');
  lateInput.attrs.set('placeholder', 'Search or enter a URL');
  lateInput.placeholder = 'Search or enter a URL';
  if (!observerCallback) {
    throw new Error('MutationObserver 未成功挂载');
  }
  (observerCallback as (m: unknown[]) => void)([
    { type: 'attributes', target: lateInput, addedNodes: [] },
  ]);
  if (lateInput.getAttribute('placeholder') !== '搜索或输入网址') {
    throw new Error(`单元素 attributes 变更未能翻译自身 placeholder: ${lateInput.getAttribute('placeholder')}`);
  }
}

await runRuntimeEngineTest().then(
  () => {
    passed += 1;
    console.log('  ok  4. runtime-zh.js 运行时引擎精准翻译新增文本节点、独立 input placeholder 属性及通用模块前缀并保护用户输入 value');
  },
  (err) => {
    failed += 1;
    console.error('  FAIL  4. runtime-zh.js 运行时引擎精准翻译新增文本节点、独立 input placeholder 属性及通用模块前缀并保护用户输入 value');
    console.error(err);
  },
);

if (failed > 0) {
  throw new Error(`国际化校验测试失败: ${failed} 项未通过 (通过 ${passed} 项)`);
}
