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

    // 构建小写不敏感字典索引，提升各类样式大小写与动态拼接场景的容错率
    const LOWER_DICT = {};
    for (const k in DICT) {
      const lk = k.toLowerCase();
      if (!LOWER_DICT[lk]) LOWER_DICT[lk] = DICT[k];
    }

    // 格式化与查词工具：去除零宽字符，合并连续空白
    const norm = (s) => (s || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim();

    const translate = (raw) => {
      if (!raw) return null;

      // 0. 多行文本逐行翻译（如快捷键提示浮层、复合说明）
      if (typeof raw === 'string' && raw.includes('\n')) {
        const lines = raw.split('\n');
        let anyTranslated = false;
        const translatedLines = lines.map(line => {
          const trimmed = line.trim();
          if (!trimmed) return line;
          const tr = translate(trimmed);
          if (tr) {
            anyTranslated = true;
            const lead = (line.match(/^\s*/) || [''])[0];
            const trail = (line.match(/\s*$/) || [''])[0];
            return lead + tr + trail;
          }
          return line;
        });
        if (anyTranslated) {
          return translatedLines.join('\n');
        }
      }

      const text = norm(raw);
      if (!text) return null;

      // 0.1 中文词汇残存复数 s 自动清洗（根治如 "(16 子智能体s)"、"子智能体s" 等英文拼接残留 bug）
      if (/[\u4e00-\u9fa5]/.test(text)) {
        const cleaned = text
          .replace(/\((\d+)\s*子智能体s\)/g, '($1 个子智能体)')
          .replace(/(\d+)\s*子智能体s/g, '$1 个子智能体')
          .replace(/(\d+)\s*个(?:代理|智能体)s\s*正在运行/g, '$1 个智能体正在运行')
          .replace(/(子智能体|代理|任务|文件|项目|命令|会话|工具)s\b/g, '$1')
          .replace(/([\u4e00-\u9fa5])s(?=[^\w]|$)/g, '$1');
        if (cleaned !== text) {
          return cleaned;
        }
      }

      // 1. 精确匹配字典（含小写兜底）
      if (DICT[text]) {
        return DICT[text];
      }
      const lower = text.toLowerCase();
      if (LOWER_DICT[lower]) {
        return LOWER_DICT[lower];
      }

      // 1.1 标点与后缀容错（冒号、省略号、句号、问号、箭头、括号、勾选标记）
      if (text.endsWith(':') && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) {
        return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + '：';
      }
      if (text.endsWith('...') && (DICT[text.slice(0, -3).trim()] || LOWER_DICT[lower.slice(0, -3).trim()])) {
        return (DICT[text.slice(0, -3).trim()] || LOWER_DICT[lower.slice(0, -3).trim()]) + '...';
      }
      if (text.endsWith('…') && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) {
        return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + '...';
      }
      if (text.endsWith('.') && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) {
        return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + '。';
      }
      if (text.endsWith('?') && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) {
        return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + '？';
      }
      if (text.endsWith('>') && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) {
        return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + ' >';
      }
      if ((text.endsWith('✓') || text.endsWith('✔')) && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) {
        return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + ' ' + text.slice(-1);
      }
      if ((text.startsWith('✓') || text.startsWith('✔')) && (DICT[text.slice(1).trim()] || LOWER_DICT[lower.slice(1).trim()])) {
        return text.charAt(0) + ' ' + (DICT[text.slice(1).trim()] || LOWER_DICT[lower.slice(1).trim()]);
      }
      if (text.startsWith('(') && text.endsWith(')') && (DICT[text.slice(1, -1).trim()] || LOWER_DICT[lower.slice(1, -1).trim()])) {
        return '（' + (DICT[text.slice(1, -1).trim()] || LOWER_DICT[lower.slice(1, -1).trim()]) + '）';
      }
      const countMatch = text.match(/^(.+?)\s*\(([0-9]+)\)$/);
      if (countMatch && (DICT[countMatch[1].trim()] || LOWER_DICT[countMatch[1].trim().toLowerCase()])) {
        return (DICT[countMatch[1].trim()] || LOWER_DICT[countMatch[1].trim().toLowerCase()]) + ' (' + countMatch[2] + ')';
      }
      const modelTagMatch = text.match(/^(.+?)\s*\((Thinking|Fast|Medium|High|Low)\)$/i);
      if (modelTagMatch && (DICT[modelTagMatch[2]] || LOWER_DICT[modelTagMatch[2].toLowerCase()])) {
        return modelTagMatch[1] + '（' + (DICT[modelTagMatch[2]] || LOWER_DICT[modelTagMatch[2].toLowerCase()]) + '）';
      }

      // 1.15 分类与排序模式匹配: e.g. "Projects (Status)", "Conversations (Date)"
      const categoryMatch = text.match(/^(.+?)\s*\((Status|Name|Date|Recent|Alphabetical|Last Modified|All|None)\)$/i);
      if (categoryMatch) {
        const catMap = {
          status: '状态',
          name: '名称',
          date: '日期',
          recent: '最近',
          alphabetical: '按字母顺序',
          'last modified': '最后修改',
          all: '全部',
          none: '无'
        };
        const catWord = catMap[categoryMatch[2].toLowerCase()] || (DICT[categoryMatch[2]] || categoryMatch[2]);
        const innerHead = categoryMatch[1].trim();
        const trHead = DICT[innerHead] || LOWER_DICT[innerHead.toLowerCase()] || innerHead;
        return (trHead === '项目列表' ? '项目' : trHead) + ' (' + catWord + ')';
      }

      // 1.2 任务操作前缀与状态动态包裹 (Checked task ..., Checking task ..., Running task ...)
      const taskActionMatch = text.match(/^(Checked|Checking|Running|Started|Completed|Failed|Cancelled|Canceled|Killed)\s+task\s+(.+)$/i);
      if (taskActionMatch) {
        const actionMap = {
          checked: '已检查任务',
          checking: '正在检查任务',
          running: '正在执行任务',
          started: '已启动任务',
          completed: '已完成任务',
          failed: '任务执行失败',
          cancelled: '已取消任务',
          canceled: '已取消任务',
          killed: '已终止任务'
        };
        const actionPrefix = actionMap[taskActionMatch[1].toLowerCase()] || '任务';
        const inner = taskActionMatch[2].trim();
        const trInner = translate(inner) || inner;
        return actionPrefix + ' ' + trInner;
      }

      // 1.3 任务执行与状态胶囊 (Run pytest suite finished >, Commit Strong localization finished >)
      const taskStatusMatch = text.match(/^(.+?)\s+(finished|completed|failed|running|cancelled|canceled)(?:\s*([>›]))?$/i);
      if (taskStatusMatch && (taskStatusMatch[3] || /[\u4e00-\u9fa5]/.test(taskStatusMatch[1]) || /^(run|running|commit|committing|check|checking|exec|executing|build|building|test|testing|git|npm|python|cargo|mvn|docker|node|make)\b/i.test(taskStatusMatch[1].trim()))) {
        const statusMap = {
          finished: '已完成',
          completed: '已完成',
          failed: '失败',
          running: '运行中',
          cancelled: '已取消',
          canceled: '已取消'
        };
        const statusWord = statusMap[taskStatusMatch[2].toLowerCase()] || taskStatusMatch[2];
        const inner = taskStatusMatch[1].trim();
        const trInner = translate(inner) || inner;
        const chevron = taskStatusMatch[3] ? ' ' + taskStatusMatch[3] : '';
        return trInner + ' ' + statusWord + chevron;
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

    // 严格代码与终端保护选择器：绝对不要篡改专业代码编辑器核心、终端输出与代码高亮块
    const CODE_PROTECT_SELECTOR = [
      'pre', 'code', 'kbd', 'samp', 'var',
      '[data-language]',
      '.cm-editor', '.cm-content', '.cm-line',
      '.monaco-editor',
      '.xterm', '.terminal-container',
      '.code-block-content'
    ].join(',');

    const isProtectedTextNode = (node) => {
      try {
        const el = node.nodeType === 1 ? node : node.parentElement;
        if (!el || !el.closest) return false;
        if (IGNORED_TAGS.has(el.tagName)) return true;

        // 1. 占位符、浮层提示、禁用指针或不可编辑嵌入组件的 UI 描述文本一律允许汉化（如 Lexical placeholder / 附件芯片）
        if (el.closest('[class*="placeholder"], [data-placeholder], [class*="pointer-events-none"], [contenteditable="false"]')) {
          return false;
        }

        // 2. 浮层菜单、列表框、弹出浮层、提示框与斜杠命令自动补全一律允许汉化
        if (el.closest('[role="listbox"], [role="menu"], [role="tooltip"], [class*="tooltip"], [class*="typeahead"], [class*="popover"], [class*="dropdown"], [class*="menu-item"], [data-radix-popper-content-wrapper], [data-floating-ui-portal]')) {
          return false;
        }

        // 2.1 查找替换面板与搜索栏控制组件一律允许汉化
        if (el.closest('.find-widget, .monaco-findInput, [class*="find-widget"], [class*="search-widget"]')) {
          return false;
        }

        // 3. 严格保护专业代码编辑器核心与终端容器
        if (el.closest(CODE_PROTECT_SELECTOR)) {
          return true;
        }

        // 3. 保护用户已发送的聊天历史消息正文
        if (el.closest('[data-testid="user-message"]')) {
          return true;
        }

        // 4. 保护正在编辑中的用户真实输入内容（注意：非占位符）
        if (el.closest('[contenteditable="true"], textarea, input:not([type="button"]):not([type="submit"])')) {
          return true;
        }

        return false;
      } catch (_) {
        return true;
      }
    };

    const isProtectedAttrNode = (el) => {
      try {
        if (!el || !el.closest) return false;
        if (IGNORED_TAGS.has(el.tagName)) return true;
        // 允许查找替换面板与输入框的 placeholder/title/aria-label 进行汉化
        if (el.closest('.find-widget, .monaco-findInput, [class*="find-widget"], [class*="search-widget"]')) return false;
        // 允许 input 与 textarea 的 placeholder/title/aria-label 进行汉化，仅严格保护代码编辑器核心与终端
        if (el.closest('.monaco-editor, .cm-editor, .xterm, .code-block-content')) return true;
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
              if (isProtectedTextNode(n)) return NodeFilter.FILTER_REJECT;
              if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
              return NodeFilter.FILTER_ACCEPT;
            }
          }
        );

        let current;
        let lastEndedWithChinese = false;
        while ((current = walker.nextNode())) {
          let original = current.nodeValue;
          const trimmed = (original || '').trim();

          // 若前一个兄弟文本节点以中文字符结尾，且当前节点为独立的 "s)" 或 "s"，消除该复数残留
          if (lastEndedWithChinese && (trimmed === 's)' || trimmed === 's')) {
            current.nodeValue = trimmed === 's)' ? ')' : '';
            count++;
            lastEndedWithChinese = trimmed === 's)';
            continue;
          }

          const translated = translate(original);
          if (translated) {
            const trimmedOrig = norm(original);
            if (trimmedOrig !== norm(translated)) {
              // 保留原有空格与换行排版，且不受内部换行与多空格影响
              const leading = (original.match(/^\s*/) || [''])[0];
              const trailing = (original.match(/\s*$/) || [''])[0];
              current.nodeValue = leading + translated + trailing;
              try { translatedNodeSet.add(current); } catch (_) {}
              count++;
            }
          }
          lastEndedWithChinese = /[\u4e00-\u9fa5]$/.test((current.nodeValue || '').trim());
        }
      } catch (err) {
        // 防止遍历异常中断主流程
      }
      return count;
    };

    // 属性翻译 (aria-label, placeholder, data-placeholder, title, value, alt, data-tooltip)
    const translateAttributes = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const elements = root.querySelectorAll('[aria-label],[placeholder],[data-placeholder],[title],[alt],[data-tooltip],input[type="button"],input[type="submit"]');
        elements.forEach((el) => {
          if (isProtectedAttrNode(el)) return;
          ['aria-label', 'placeholder', 'data-placeholder', 'title', 'alt', 'data-tooltip', 'value'].forEach((attr) => {
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

    // 全局用户交互感知窗口（点击/按压时开启 250ms 零延迟同步直出通道）
    let isUserInteracting = false;
    let interactExpiry = 0;
    const markInteraction = () => {
      isUserInteracting = true;
      interactExpiry = (typeof performance !== 'undefined' ? performance.now() : Date.now()) + 300;
    };

    ['pointerdown', 'mousedown', 'keydown', 'touchstart'].forEach((evtType) => {
      try {
        window.addEventListener(evtType, markInteraction, { capture: true, passive: true });
      } catch (_) {}
    });

    // 原生 DOM 属性透明拦截器：从根源上消灭英文向 DOM 树的写入，实现物理 0ms 纯中文直出
    try {
      const origTextContentDesc = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
      if (origTextContentDesc && origTextContentDesc.set) {
        const origTextContentSet = origTextContentDesc.set;
        Object.defineProperty(Node.prototype, 'textContent', {
          set(val) {
            try {
              if (typeof val === 'string' && val.length > 0 && val.length < 500) {
                if (!isProtectedTextNode(this)) {
                  const tr = translate(val);
                  if (tr && norm(val) !== norm(tr)) {
                    const lead = (val.match(/^\s*/) || [''])[0];
                    const trail = (val.match(/\s*$/) || [''])[0];
                    return origTextContentSet.call(this, lead + tr + trail);
                  }
                }
              }
            } catch (_) {}
            return origTextContentSet.call(this, val);
          },
          get: origTextContentDesc.get,
          configurable: true,
          enumerable: origTextContentDesc.enumerable
        });
      }

      const origNodeValueDesc = Object.getOwnPropertyDescriptor(Node.prototype, 'nodeValue');
      if (origNodeValueDesc && origNodeValueDesc.set) {
        const origNodeValueSet = origNodeValueDesc.set;
        Object.defineProperty(Node.prototype, 'nodeValue', {
          set(val) {
            try {
              if (this.nodeType === 3 && typeof val === 'string' && val.length > 0 && val.length < 500) {
                if (!isProtectedTextNode(this)) {
                  const tr = translate(val);
                  if (tr && norm(val) !== norm(tr)) {
                    const lead = (val.match(/^\s*/) || [''])[0];
                    const trail = (val.match(/\s*$/) || [''])[0];
                    return origNodeValueSet.call(this, lead + tr + trail);
                  }
                }
              }
            } catch (_) {}
            return origNodeValueSet.call(this, val);
          },
          get: origNodeValueDesc.get,
          configurable: true,
          enumerable: origNodeValueDesc.enumerable
        });
      }

      // 拦截 setAttribute (消灭 placeholder, aria-label, title 等的闪烁)
      const origSetAttribute = Element.prototype.setAttribute;
      if (origSetAttribute) {
        Element.prototype.setAttribute = function(name, val) {
          try {
            if (['aria-label', 'placeholder', 'data-placeholder', 'title', 'alt', 'data-tooltip', 'value'].includes(name) && typeof val === 'string' && val.length > 0 && val.length < 500) {
              if (!isProtectedAttrNode(this)) {
                const tr = translate(val);
                if (tr && norm(val) !== norm(tr)) {
                  return origSetAttribute.call(this, name, tr);
                }
              }
            }
          } catch (_) {}
          return origSetAttribute.call(this, name, val);
        };
      }

      // 拦截 document.createTextNode (消灭 React 动态创建文本节点的闪烁)
      const origCreateTextNode = document.createTextNode;
      if (origCreateTextNode) {
        document.createTextNode = function(data) {
          try {
            if (typeof data === 'string' && data.length > 0 && data.length < 500) {
              const tr = translate(data);
              if (tr && norm(data) !== norm(tr)) {
                const lead = (data.match(/^\s*/) || [''])[0];
                const trail = (data.match(/\s*$/) || [''])[0];
                return origCreateTextNode.call(document, lead + tr + trail);
              }
            }
          } catch (_) {}
          return origCreateTextNode.call(document, data);
        };
      }
    } catch (_) {}

    // 自动重组并翻译被搜索高亮（highlight span）打碎的富文本标签容器
    const translateHighlightedContainers = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const highlightElements = root.querySelectorAll('.highlight, [class*="highlight"], mark');
        if (highlightElements.length === 0) return 0;

        const processedContainers = new Set();
        for (let i = 0; i < highlightElements.length; i++) {
          const hl = highlightElements[i];
          const container = hl.parentElement;
          if (!container || processedContainers.has(container) || translatedNodeSet.has(container)) continue;
          processedContainers.add(container);

          if (isProtectedTextNode(container)) continue;
          const fullText = (container.textContent || '').trim();
          if (!fullText || fullText.length > 300) continue;

          const translated = translate(fullText);
          if (translated && norm(translated) !== norm(fullText)) {
            const leading = (container.textContent.match(/^\s*/) || [''])[0];
            const trailing = (container.textContent.match(/\s*$/) || [''])[0];
            container.textContent = leading + translated + trailing;
            translatedNodeSet.add(container);
            count++;
          }
        }
      } catch (_) {}
      return count;
    };

    // 已翻译文本节点弱引用集合，彻底阻断活锁与重复处理
    const translatedNodeSet = new WeakSet();

    // 监听 DOM 树变化并根据交互场景智能分流：
    // 默认在当前微任务中同步增量直出（先于浏览器 Paint 绘制完成，彻底根除英文闪烁），
    // 超过 15ms 保险丝的超大型长列表变更，安全移交后台轻量防抖处理。
    let mutationTimer = null;
    let maxWaitDeadline = 0;

    const handleMutations = () => {
      maxWaitDeadline = 0;
      runTranslation();
    };

    const observer = new MutationObserver((mutations) => {
      const now = typeof performance !== 'undefined' ? performance.now() : Date.now();
      let syncCount = 0;
      let exceededBudget = false;

      if (mutations && mutations.length > 0) {
        const syncStart = now;
        const MAX_SYNC_BUDGET_MS = 15; // 放宽到 15ms，绝大部分 UI 组件 (如下拉框/弹窗) 都能在微任务中就地完成翻译，不出现闪烁

        for (let i = 0; i < mutations.length; i++) {
          // 超出 15ms 预算时立即熔断让出主线程，剩余节点由后续后台防抖队列平滑处理
          if (typeof performance !== 'undefined' && performance.now() - syncStart > MAX_SYNC_BUDGET_MS) {
            exceededBudget = true;
            break;
          }
          const m = mutations[i];
          if (m.type === 'childList') {
            for (let j = 0; j < m.addedNodes.length; j++) {
              const node = m.addedNodes[j];
              if (node.nodeType === 1) { // 元素节点
                syncCount += translateHighlightedContainers(node);
                syncCount += translateTextNodes(node);
                syncCount += translateAttributes(node);
              } else if (node.nodeType === 3) { // 文本节点
                if (!translatedNodeSet.has(node)) {
                  const orig = node.nodeValue;
                  const tr = translate(orig);
                  if (tr && norm(orig) !== norm(tr)) {
                    const lead = (orig.match(/^\s*/) || [''])[0];
                    const trail = (orig.match(/\s*$/) || [''])[0];
                    node.nodeValue = lead + tr + trail;
                    translatedNodeSet.add(node);
                    syncCount++;
                  }
                }
              }
            }
          } else if (m.type === 'characterData') {
            const node = m.target;
            if (node && node.nodeType === 3 && !translatedNodeSet.has(node)) {
              const orig = node.nodeValue;
              const tr = translate(orig);
              if (tr && norm(orig) !== norm(tr)) {
                const lead = (orig.match(/^\s*/) || [''])[0];
                const trail = (orig.match(/\s*$/) || [''])[0];
                node.nodeValue = lead + tr + trail;
                translatedNodeSet.add(node);
                syncCount++;
              }
            }
          } else if (m.type === 'attributes') {
            if (m.target && m.target.nodeType === 1) {
              syncCount += translateAttributes(m.target);
            }
          }
        }

        // 若在 15ms 预算内全部增量翻译完毕，直接返回！首帧即为纯正中文，0ms 零延迟！
        if (!exceededBudget) {
          return;
        }
      }

      // 超出帧预算的极端海量 DOM 节点挂载：采用轻量后台平滑调度
      if (!maxWaitDeadline) {
        maxWaitDeadline = now + 60;
      }
      clearTimeout(mutationTimer);
      const delay = Math.max(0, Math.min(16, maxWaitDeadline - now));
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
            attributeFilter: ['aria-label', 'placeholder', 'data-placeholder', 'title', 'alt', 'data-tooltip', 'value']
          });
          console.log('[AGY-ZH] MutationObserver attached successfully with zero-fouc sync channel.');
        } catch (obsErr) {
          console.warn('[AGY-ZH] Failed to attach MutationObserver:', obsErr);
        }
      } else {
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
