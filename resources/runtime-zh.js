/**
 * Antigravity 界面中文运行时注入脚本 (Runtime DOM Translation Engine)
 * 专为 Google Antigravity 桌面端定制的高性能、时序安全 DOM 动态翻译引擎。
 * 
 * 特性：
 * 1. 深度时序保护：支持 preload (isolated world) 与 executeJavaScript (main world) 双通道无缝运行；
 * 2. 采用 TreeWalker 极速检索并更新文本节点，严格保护代码编辑区 (Monaco/CodeMirror)、<pre>、<code> 与终端；
 * 3. 严格保留原有排版空格，支持 placeholder, title, aria-label, alt 等所有 UI 属性；
 * 4. 防抖 MutationObserver，完美适配 React 动态渲染与流式输出；
 * 5. 状态透明化，自动向控制台报告汉化命中统计。
 */
(() => {
  try {
    const DICT = window.__AGY_ZH_DICT__ || {};
    const RULES = window.__AGY_ZH_RULES__ || [];
    const LANG = window.__AGY_ZH_LANG__ || 'zh-CN';

    // 格式化与查词工具
    const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();

    const translate = (raw) => {
      if (!raw) return null;
      const text = norm(raw);
      if (!text) return null;

      // 1. 精确匹配字典
      if (DICT[text]) {
        return DICT[text];
      }

      // 1.1 标点容错（冒号、省略号、句号、问号）
      if (text.endsWith(':') && DICT[text.slice(0, -1).trim()]) {
        return DICT[text.slice(0, -1).trim()] + '：';
      }
      if (text.endsWith('...') && DICT[text.slice(0, -3).trim()]) {
        return DICT[text.slice(0, -3).trim()] + '...';
      }
      if (text.endsWith('…') && DICT[text.slice(0, -1).trim()]) {
        return DICT[text.slice(0, -1).trim()] + '...';
      }
      if (text.endsWith('.') && DICT[text.slice(0, -1).trim()]) {
        return DICT[text.slice(0, -1).trim()] + '。';
      }
      if (text.endsWith('?') && DICT[text.slice(0, -1).trim()]) {
        return DICT[text.slice(0, -1).trim()] + '？';
      }

      // 2. 正则动态匹配
      for (let i = 0; i < RULES.length; i++) {
        const item = RULES[i];
        try {
          const reg = item[0] instanceof RegExp ? item[0] : new RegExp(item[0]);
          const repl = item[1];
          if (reg.test(text)) {
            return text.replace(reg, repl);
          }
        } catch (_) {}
      }

      return null;
    };

    // 排除的容器标签
    const IGNORED_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'SVG', 'PATH', 'IFRAME']);

    // 严格代码与输入保护选择器：绝对不要篡改代码编辑器、终端输出与输入框
    const CODE_PROTECT_SELECTOR = [
      'pre', 'code', 'kbd', 'samp', 'var',
      '[data-language]',
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
      try {
        const el = node.nodeType === 1 ? node : node.parentElement;
        if (!el || !el.closest) return true;
        if (IGNORED_TAGS.has(el.tagName)) return true;
        if (el.closest(CODE_PROTECT_SELECTOR)) return true;
        if (el.closest(USER_CONTENT_SELECTOR)) return true;
        return false;
      } catch (_) {
        return true;
      }
    };

    // 遍历翻译文本节点
    const translateTextNodes = (root) => {
      if (!root) return 0;
      let count = 0;
      try {
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
          if (translated) {
            const trimmedOrig = norm(original);
            if (trimmedOrig !== norm(translated)) {
              // 保留原有空格与换行排版，且不受内部换行与多空格影响
              const leading = (original.match(/^\s*/) || [''])[0];
              const trailing = (original.match(/\s*$/) || [''])[0];
              current.nodeValue = leading + translated + trailing;
              count++;
            }
          }
        }
      } catch (err) {
        // 防止遍历异常中断主流程
      }
      return count;
    };

    // 属性翻译 (aria-label, placeholder, title, value, alt)
    const translateAttributes = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const elements = root.querySelectorAll('[aria-label],[placeholder],[title],[alt],input[type="button"],input[type="submit"]');
        elements.forEach((el) => {
          if (isProtectedNode(el)) return;
          ['aria-label', 'placeholder', 'title', 'alt', 'value'].forEach((attr) => {
            let val = el.getAttribute ? el.getAttribute(attr) : null;
            if (!val && attr in el && typeof el[attr] === 'string') val = el[attr];
            if (val) {
              const tr = translate(val);
              if (tr && norm(val) !== norm(tr)) {
                if (el.setAttribute) el.setAttribute(attr, tr);
                try { if (attr in el) el[attr] = tr; } catch (_) {}
                count++;
              }
            }
          });
        });
      } catch (_) {}
      return count;
    };

    // 全量执行单次翻译
    const runTranslation = () => {
      try {
        const root = document.body || document.documentElement;
        if (!root) return;
        if (document.documentElement && document.documentElement.getAttribute('lang') !== LANG) {
          document.documentElement.setAttribute('lang', LANG);
        }
        const textCount = translateTextNodes(root);
        const attrCount = translateAttributes(root);
        if (textCount > 0 || attrCount > 0) {
          console.log(`[AGY-ZH] Translated ${textCount} text nodes and ${attrCount} attributes.`);
        }
      } catch (err) {
        console.warn('[AGY-ZH] Error during runTranslation:', err);
      }
    };

    // 如果已经初始化过，立即重新扫描一次并退出避免重复监听
    if (window.__agyZhInited) {
      runTranslation();
      return;
    }
    window.__agyZhInited = true;

    console.log(`[AGY-ZH] DOM Translation Engine initializing. Target language: ${LANG}, Dict size: ${Object.keys(DICT).length}`);

    // 立即执行初始扫描
    runTranslation();

    // 监听 DOM 树变化并防抖触发（限制最大等待时间 150ms）
    let mutationTimer = null;
    let maxWaitDeadline = 0;

    const handleMutations = () => {
      maxWaitDeadline = 0;
      runTranslation();
    };

    const observer = new MutationObserver(() => {
      const now = Date.now();
      if (!maxWaitDeadline) {
        maxWaitDeadline = now + 150;
      }
      clearTimeout(mutationTimer);
      const delay = Math.max(0, Math.min(25, maxWaitDeadline - now));
      mutationTimer = setTimeout(handleMutations, delay);
    });

    // 安全挂载 MutationObserver
    const attachObserver = () => {
      const target = document.documentElement || document.body || document;
      if (target && target.nodeType) {
        try {
          observer.observe(target, {
            subtree: true,
            childList: true,
            characterData: true,
            attributes: true,
            attributeFilter: ['aria-label', 'placeholder', 'title', 'alt', 'value']
          });
          console.log('[AGY-ZH] MutationObserver attached successfully.');
        } catch (obsErr) {
          console.warn('[AGY-ZH] Failed to attach MutationObserver:', obsErr);
        }
      } else {
        // 如果 target 暂时不可用，等待 50ms 再次尝试
        setTimeout(attachObserver, 50);
      }
    };

    attachObserver();

    // 页面完全加载时再稳固执行
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => setTimeout(runTranslation, 100));
    }
    window.addEventListener('load', () => setTimeout(runTranslation, 200));

    // 定期心跳前 5 秒每秒补扫一次，确保所有异步 React 懒加载模块完全汉化
    let heartbeats = 0;
    const intervalId = setInterval(() => {
      heartbeats++;
      runTranslation();
      if (heartbeats >= 6) {
        clearInterval(intervalId);
      }
    }, 800);

  } catch (e) {
    console.warn('[AGY-ZH] Runtime translation failed to bootstrap:', e);
  }
})();
