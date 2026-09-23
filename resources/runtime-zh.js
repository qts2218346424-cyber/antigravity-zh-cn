/**
 * Antigravity 界面中文运行时注入脚本 (Runtime DOM Translation Engine)
 * 专为 Google Antigravity 桌面端定制的高性能 DOM 文本动态翻译引擎。
 * 
 * 特性：
 * 1. 采用 TreeWalker 极速检索并更新文本节点；
 * 2. 严格跳过代码编辑区 (Monaco/CodeMirror)、<pre>、<code>、终端以及用户输入区，防止篡改代码与用户指令；
 * 3. 翻译 placeholder, title, aria-label 等 UI 提示属性；
 * 4. 带截止时间保护的防抖 MutationObserver，完美兼容 AI 流式输出。
 */
(() => {
  try {
    if (window.__agyZhInited) return;
    window.__agyZhInited = true;

    const DICT = window.__AGY_ZH_DICT__ || {};
    const RULES = window.__AGY_ZH_RULES__ || [];
    const LANG = window.__AGY_ZH_LANG__ || 'zh-CN';

    // 设置 html 语言属性
    if (document.documentElement) {
      document.documentElement.setAttribute('lang', LANG);
    }

    // 格式化文本工具
    const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();

    // 翻译查找函数
    const translate = (raw) => {
      if (!raw) return null;
      const text = norm(raw);
      if (!text) return null;

      // 1. 精确匹配字典
      if (DICT[text]) {
        return DICT[text];
      }

      // 2. 正则动态匹配
      for (let i = 0; i < RULES.length; i++) {
        const item = RULES[i];
        const reg = item[0] instanceof RegExp ? item[0] : new RegExp(item[0]);
        const repl = item[1];
        if (reg.test(text)) {
          return text.replace(reg, repl);
        }
      }

      return null;
    };

    // 排除的容器标签
    const IGNORED_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'SVG', 'PATH', 'IFRAME']);

    // 严格代码与输入保护选择器：绝对不要触碰代码编辑器、终端输出与输入框
    const CODE_PROTECT_SELECTOR = [
      'pre', 'code', 'kbd', 'samp', 'var',
      '[data-language]', '[data-testid*="code"]',
      '.cm-editor', '.cm-content', '.cm-line',
      '.monaco-editor', '.monaco-editor *',
      '.xterm', '.xterm *', '.terminal-container',
      '[contenteditable="true"]',
      'textarea', 'input:not([type="button"]):not([type="submit"])'
    ].join(',');

    // 用户聊天输入与模型输出中代码保护
    const USER_CONTENT_SELECTOR = [
      '[data-testid="user-message"]',
      '[data-testid="chat-input"]',
      '.code-block-content'
    ].join(',');

    const isProtectedNode = (node) => {
      const el = node.nodeType === 1 ? node : node.parentElement;
      if (!el) return true;
      if (IGNORED_TAGS.has(el.tagName)) return true;
      if (el.closest(CODE_PROTECT_SELECTOR)) return true;
      if (el.closest(USER_CONTENT_SELECTOR)) return true;
      return false;
    };

    // 遍历翻译文本节点
    const translateTextNodes = (root) => {
      if (!root) return;
      const walker = document.createTreeWalker(
        root,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode(n) {
            if (isProtectedNode(n)) return NodeFilter.FILTER_REJECT;
            if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
            return NodeFilter.FILTER_ACCEPT;
          }
        }
      );

      let current;
      while ((current = walker.nextNode())) {
        const original = current.nodeValue;
        const translated = translate(original);
        if (translated && norm(original) !== norm(translated)) {
          current.nodeValue = translated;
        }
      }
    };

    // 属性翻译 (aria-label, placeholder, title, value)
    const translateAttributes = (root) => {
      if (!root) return;
      const elements = root.querySelectorAll('[aria-label],[placeholder],[title],input[type="button"],input[type="submit"]');
      elements.forEach((el) => {
        if (isProtectedNode(el)) return;
        ['aria-label', 'placeholder', 'title', 'value'].forEach((attr) => {
          let val = el.getAttribute ? el.getAttribute(attr) : null;
          if (!val && attr in el) val = el[attr];
          if (val) {
            const tr = translate(val);
            if (tr && norm(val) !== norm(tr)) {
              if (el.setAttribute) el.setAttribute(attr, tr);
              try { if (attr in el) el[attr] = tr; } catch (_) {}
            }
          }
        });
      });
    };

    // 全量执行一次翻译
    const runTranslation = () => {
      try {
        const body = document.body || document.documentElement;
        if (!body) return;
        translateTextNodes(body);
        translateAttributes(body);
      } catch (err) {
        // 静默防崩溃
      }
    };

    // 立即执行初始扫描
    runTranslation();

    // 监听 DOM 树变化并防抖触发（限制最大等待时间 250ms）
    let mutationTimer = null;
    let maxWaitDeadline = 0;

    const handleMutations = () => {
      maxWaitDeadline = 0;
      runTranslation();
    };

    const observer = new MutationObserver(() => {
      const now = Date.now();
      if (!maxWaitDeadline) {
        maxWaitDeadline = now + 250;
      }
      clearTimeout(mutationTimer);
      const delay = Math.max(0, Math.min(30, maxWaitDeadline - now));
      mutationTimer = setTimeout(handleMutations, delay);
    });

    observer.observe(document.documentElement || document.body, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ['aria-label', 'placeholder', 'title', 'value']
    });

    // 页面加载完成后再稳固执行一次
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => setTimeout(runTranslation, 100));
    }
  } catch (e) {
    console.warn('[antigravity-zh-cn] Runtime translation failed to start:', e);
  }
})();
