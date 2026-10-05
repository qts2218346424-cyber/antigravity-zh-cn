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
      if (/(?:子智能体|智能体|代理|任务|文件|项目|命令|会话|工具)s\b/.test(text)) {
        const cleaned = text
          .replace(/\((\d+)\s*(?:子智能体|智能体|代理)s\)/g, '($1 个子智能体)')
          .replace(/(\d+)\s*(?:子智能体|智能体|代理)s/g, '$1 个子智能体')
          .replace(/(\d+)\s*个(?:代理|智能体)s\s*正在运行/g, '$1 个智能体正在运行')
          .replace(/(子智能体|智能体|代理|任务|文件|项目|命令|会话|工具)s\b/g, '$1');
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
      if (text.startsWith('...') || text.startsWith('…')) {
        const leadLen = text.startsWith('...') ? 3 : 1;
        const inner = text.slice(leadLen).trim();
        const tr = DICT[inner] || LOWER_DICT[inner.toLowerCase()] || translate(inner);
        if (tr) {
          return '...' + tr;
        }
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

      // 1.16 预算与额度动态百分比直通匹配 (例如 "84.1% of the customization budget is available.")
      const budgetPctMatch = text.match(/^([0-9.]+)%\s+of\s+the\s+(?:customization\s+)?budget\s+is\s+available\.?$/i);
      if (budgetPctMatch) {
        return `自定义预算剩余 ${budgetPctMatch[1]}%`;
      }
      if (/^of\s+the\s+(?:customization\s+)?budget\s+is\s+available\.?$/i.test(text)) {
        return '可用自定义预算。';
      }

      // 1.17 布局宽度模式匹配 (Narrow / Default / Wide)
      if (/^narrow$/i.test(text)) return '较窄';
      if (/^wide$/i.test(text)) return '较宽';

      // 1.18 常用配置与操作动作模式匹配 (Customize / Browse / Apply)
      if (/^customize(?:\.\.\.|…)?$/i.test(text)) return '自定义';
      if (/^customize\s*>$/i.test(text)) return '自定义 >';
      if (/^browse(?:\.\.\.|…)?$/i.test(text)) return '浏览';
      if (/^apply$/i.test(text)) return '应用';
      if (/^discard$/i.test(text)) return '放弃';

      // 1.19 英文月份与动态日期通用转换 (e.g. "November 2, 2026" -> "2026 年 11 月 2 日")
      const MONTH_MAP = {
        january: '1 月', february: '2 月', march: '3 月', april: '4 月',
        may: '5 月', june: '6 月', july: '7 月', august: '8 月',
        september: '9 月', october: '10 月', november: '11 月', december: '12 月',
        jan: '1 月', feb: '2 月', mar: '3 月', apr: '4 月',
        jun: '6 月', jul: '7 月', aug: '8 月', sep: '9 月', sept: '9 月',
        oct: '10 月', nov: '11 月', dec: '12 月'
      };

      const formatEnDate = (dateStr) => {
        if (!dateStr) return '';
        const trimmed = dateStr.trim();
        let m = trimmed.match(/^([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})$/i);
        if (m) {
          const month = MONTH_MAP[m[1].toLowerCase()] || m[1];
          return `${m[3]} 年 ${month} ${m[2]} 日`;
        }
        m = trimmed.match(/^([A-Za-z]+)\s+(\d{4})$/i);
        if (m) {
          const month = MONTH_MAP[m[1].toLowerCase()] || m[1];
          return `${m[2]} 年 ${month}`;
        }
        m = trimmed.match(/^(\d{1,2})\s+([A-Za-z]+),?\s*(\d{4})$/i);
        if (m) {
          const month = MONTH_MAP[m[2].toLowerCase()] || m[2];
          return `${m[3]} 年 ${month} ${m[1]} 日`;
        }
        return trimmed;
      };

      // 1.20 模型与服务生命周期/下线通知动态匹配 (e.g. "GPT-OSS will be removed from Antigravity on November 2, 2026.")
      const modelRemovalDateMatch = text.match(/^(.+?)\s+will\s+be\s+removed\s+from\s+Antigravity\s+on\s+([A-Za-z]+(?:\s+\d{1,2})?,\s*\d{4})\.?$/i);
      if (modelRemovalDateMatch) {
        const zhDate = formatEnDate(modelRemovalDateMatch[2]);
        const modelName = modelRemovalDateMatch[1].trim();
        return `${modelName} 将于 ${zhDate}从 Antigravity 中下线。`;
      }

      const modelRemovalMatch = text.match(/^(.+?)\s+will\s+be\s+removed\s+from\s+Antigravity\.?$/i);
      if (modelRemovalMatch) {
        return `${modelRemovalMatch[1].trim()} 即将从 Antigravity 中下线。`;
      }

      const modelDeprecateDateMatch = text.match(/^(.+?)\s+will\s+be\s+deprecated\s+on\s+([A-Za-z]+(?:\s+\d{1,2})?,\s*\d{4})\.?$/i);
      if (modelDeprecateDateMatch) {
        const zhDate = formatEnDate(modelDeprecateDateMatch[2]);
        return `${modelDeprecateDateMatch[1].trim()} 将于 ${zhDate}弃用。`;
      }

      const modelDeprecatedAndRemovedMatch = text.match(/^(.+?)\s+is\s+deprecated\s+and\s+will\s+be\s+removed\s+on\s+([A-Za-z]+(?:\s+\d{1,2})?,\s*\d{4})\.?$/i);
      if (modelDeprecatedAndRemovedMatch) {
        const zhDate = formatEnDate(modelDeprecatedAndRemovedMatch[2]);
        return `${modelDeprecatedAndRemovedMatch[1].trim()} 已废弃，将于 ${zhDate}移除。`;
      }

      const modelRemovedOnMatch = text.match(/^(.+?)\s+will\s+be\s+removed\s+on\s+([A-Za-z]+(?:\s+\d{1,2})?,\s*\d{4})\.?$/i);
      if (modelRemovedOnMatch) {
        const zhDate = formatEnDate(modelRemovedOnMatch[2]);
        return `${modelRemovedOnMatch[1].trim()} 将于 ${zhDate}移除。`;
      }

      // 1.21 会话统计胶囊 (e.g. "1 active conversation and 2 archived conversations", "1 active conversation")
      const convoCountMatch = text.match(/^(?:(\d+)\s+active\s+conversations?)?(?:\s*and\s*)?(?:(\d+)\s+archived\s+conversations?)?$/i);
      if (convoCountMatch && (convoCountMatch[1] || convoCountMatch[2])) {
        const parts = [];
        if (convoCountMatch[1]) parts.push(`${convoCountMatch[1]} 个活跃会话`);
        if (convoCountMatch[2]) parts.push(`${convoCountMatch[2]} 个已归档会话`);
        return parts.join(' 和 ');
      }

      // 1.22 会话归档短语碎片与链接前缀容错
      if (/^View\s+archived\s+conversations\s+in(?:\s+history)?\.?$/i.test(text)) {
        return '在历史记录中查看已归档会话。';
      }
      if (/^View\s+archived\s+conversations\s+in\s*:?$/i.test(text)) {
        return '在历史记录中查看已归档会话：';
      }
      if (/^View\s+archived\s+conversations$/i.test(text)) {
        return '查看已归档会话';
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

    // 排除的非文本或纯图形容器标签（注意：保留 SVG <text> 与 <tspan> 文本节点通道）
    const IGNORED_TAGS = new Set([
      'SCRIPT', 'STYLE', 'NOSCRIPT', 'IFRAME',
      'PATH', 'RECT', 'CIRCLE', 'ELLIPSE', 'LINE', 'POLYLINE', 'POLYGON', 'DEFS', 'CLIPPATH', 'MASK', 'PATTERN', 'USE'
    ]);

    // 严格代码与终端保护选择器：绝对保护专业代码编辑器核心行与终端输出
    const CODE_PROTECT_SELECTOR = [
      'pre', 'code', 'kbd', 'samp', 'var',
      '[data-language]',
      '.cm-editor .cm-content', '.cm-line',
      '.monaco-editor .view-lines', '.monaco-editor .lines-content',
      '.xterm', '.terminal-container',
      '.code-block-content'
    ].join(',');

    const isProtectedTextNode = (node) => {
      try {
        const el = node.nodeType === 1 ? node : node.parentElement;
        if (!el || !el.closest) return false;
        if (IGNORED_TAGS.has(el.tagName)) return true;

        // 0. 【最高优先级】绝对保护正在编辑中的用户真实输入内容（contenteditable="true", textarea, input）
        // 关键防护：必须置顶！绝不可被后续的 widget、card、dialog 等外层容器匹配所击穿！
        const editableContainer = el.closest('[contenteditable="true"], textarea, input:not([type="button"]):not([type="submit"]):not([type="reset"])');
        if (editableContainer) {
          // 仅当节点本身处于明确的 placeholder 占位符容器内时才允许汉化，输入内容绝对不能碰
          const placeholderEl = el.closest('[class*="placeholder"], [data-placeholder]');
          if (!placeholderEl) {
            return true;
          }
        }

        // 1. 严格保护专业代码编辑器核心与终端容器 (Monaco / CodeMirror / Xterm)
        if (el.closest(CODE_PROTECT_SELECTOR)) {
          return true;
        }

        // 1.1 严格保护思考面板内部的思维链正文与 Markdown 内容，阻断零散词典替换污染！
        // 关键逻辑：外层触发器按钮（[data-testid="thinking-collapsible-trigger"]）及其内部文本允许正常汉化；
        // 仅保护折叠展开后的思考 Markdown 正文区（.cursor-edit 及触发器紧随的同级正文容器）
        if (el.closest('.cursor-edit, [data-testid="thinking-collapsible-trigger"] ~ div, [data-testid="thinking-content"], [aria-label*="Thought"] ~ div, [aria-label*="思考"] ~ div')) {
          return true;
        }

        // 2. 保护用户已发送的聊天历史消息正文
        if (el.closest('[data-testid="user-message"]')) {
          return true;
        }

        // 3. 占位符、浮层提示等 UI 描述文本允许汉化
        if (el.closest('[class*="placeholder"], [data-placeholder], [class*="pointer-events-none"]')) {
          return false;
        }

        // 4. 浮层菜单、列表框、弹出浮层、提示框与斜杠命令自动补全一律允许汉化
        if (el.closest('[role="listbox"], [role="menu"], [role="tooltip"], [class*="tooltip"], [class*="typeahead"], [class*="popover"], [class*="dropdown"], [class*="menu-item"], [data-radix-popper-content-wrapper], [data-floating-ui-portal]')) {
          return false;
        }

        // 5. 查找替换面板与搜索栏控制组件一律允许汉化
        if (el.closest('.find-widget, .monaco-findInput, [class*="find-widget"], [class*="search-widget"]')) {
          return false;
        }

        // 6. 自定义预算面板、进度条、徽章、控制开关等辅助组件一律允许汉化
        // 注意：移除全局通配型选择器 [class*="widget"], [role="region"], [role="presentation"]，防止其穿透并击穿编辑器保护！
        if (el.closest('[class*="customization"], [class*="budget"], [class*="progress"], [class*="pill"], [class*="toggle"], [class*="segmented"], [class*="badge"], [role="progressbar"]')) {
          return false;
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
        // 允许查找替换面板、自定义预算与交互控件的 placeholder/title/aria-label 进行汉化
        if (el.closest('.find-widget, .monaco-findInput, [class*="find-widget"], [class*="search-widget"], [class*="customization"], [class*="budget"], [class*="progress"], [class*="segmented"], [class*="toggle"], [class*="badge"], [role="tooltip"], [class*="tooltip"]')) return false;
        // 严格保护代码编辑器核心与终端
        if (el.closest(CODE_PROTECT_SELECTOR)) return true;
        return false;
      } catch (_) {
        return true;
      }
    };

    // 已翻译文本节点与容器弱引用集合，阻断重复翻译
    const translatedNodeSet = new WeakSet();

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
        let lastEndedWithSubagent = false;
        let lastEndedWithThinkingTimer = false;
        while ((current = walker.nextNode())) {
          let original = current.nodeValue;
          const trimmed = (original || '').trim();

          // 若前一个兄弟文本节点以子智能体/代理结尾，且当前节点为独立的 "s)" 或 "s"，消除该复数残留
          if (lastEndedWithSubagent && (trimmed === 's)' || trimmed === 's')) {
            current.nodeValue = trimmed === 's)' ? ')' : '';
            count++;
            lastEndedWithSubagent = trimmed === 's)';
            continue;
          }

          // 若前一个兄弟文本节点以思考计时器或秒数结尾，且当前节点为独立的 "s" 或 "s)"，转为中文单位 " 秒"
          if (lastEndedWithThinkingTimer && (trimmed === 's' || trimmed === 's)')) {
            current.nodeValue = trimmed === 's)' ? ' 秒)' : ' 秒';
            count++;
            lastEndedWithThinkingTimer = false;
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
          lastEndedWithSubagent = /(?:子智能体|智能体|代理)$/.test((current.nodeValue || '').trim());
          const curTrimmed = (current.nodeValue || '').trim();
          lastEndedWithThinkingTimer = /(?:正在思考|已思考|思考了|思考耗时)$/.test(curTrimmed) || (lastEndedWithThinkingTimer && /^\d+$/.test(curTrimmed));
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
            // 绝对不可修改常规文本输入框或文本域的 value，防止篡改用户键入的真实字符
            if (attr === 'value' && !(el.matches && el.matches('input[type="button"], input[type="submit"]'))) {
              return;
            }
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

    // 自动重组并翻译被搜索高亮（highlight/match span）打碎的富文本标签容器（如 slash command / skill 下拉菜单）
    const translateHighlightedContainers = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const highlightElements = root.querySelectorAll('.highlight, [class*="highlight"], mark, [class*="match"], .monaco-match, [class*="monaco-highlighted-label"], [class*="highlighted-label"]');
        if (highlightElements.length === 0) return 0;

        const processedContainers = new Set();
        for (let i = 0; i < highlightElements.length; i++) {
          const hl = highlightElements[i];
          let container = (hl.matches && hl.matches('[class*="highlighted-label"]')) ? hl : hl.parentElement;
          if (!container) continue;

          // 若父级也是纯描述/标签容器（例如 .details-label / [class*="desc"]），尝试向上一级提升以获取完整描述句
          if (container.parentElement && container.parentElement.matches && container.parentElement.matches('[class*="desc"], [class*="detail"], [class*="label"], [class*="secondary"]')) {
            if (container.parentElement.children.length <= 3) {
              container = container.parentElement;
            }
          }

          if (processedContainers.has(container) || translatedNodeSet.has(container)) continue;
          processedContainers.add(container);

          if (isProtectedTextNode(container)) continue;
          const rawText = container.textContent || '';
          const fullText = norm(rawText);
          if (!fullText || fullText.length < 3 || fullText.length > 400) continue;

          const translated = translate(fullText);
          if (translated && norm(translated) !== fullText) {
            const leading = (rawText.match(/^\s*/) || [''])[0];
            const trailing = (rawText.match(/\s*$/) || [''])[0];
            container.textContent = leading + translated + trailing;
            try { translatedNodeSet.add(container); } catch (_) {}
            count++;
          }
        }
      } catch (_) {}
      return count;
    };

    // 专治预算描述、进度百分比被拆解或动态计算的容器复合汉化
    const translateBudgetContainers = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const candidates = root.querySelectorAll('[class*="budget"], [class*="customization"], [class*="progress"], [role="progressbar"], [class*="quota"], [class*="usage"]');
        for (let i = 0; i < candidates.length; i++) {
          const el = candidates[i];
          if (translatedNodeSet.has(el) || isProtectedTextNode(el)) continue;
          const text = (el.textContent || '').trim();
          if (!text || text.length > 200) continue;

          // 匹配 "84.1% of the customization budget is available." 等拆分场景
          const budgetMatch = text.match(/^([0-9.]+)%\s+of\s+the\s+(?:customization\s+)?budget\s+is\s+available\.?$/i);
          if (budgetMatch) {
            // 确保只处理包含文本的最内层匹配容器
            if (el.children.length > 0) {
              let childMatched = false;
              for (let c = 0; c < el.children.length; c++) {
                if (el.children[c].textContent && /of\s+the\s+(?:customization\s+)?budget\s+is\s+available/i.test(el.children[c].textContent)) {
                  childMatched = true;
                  break;
                }
              }
              if (childMatched) continue;
            }
            el.textContent = `自定义预算剩余 ${budgetMatch[1]}%`;
            try { translatedNodeSet.add(el); } catch (_) {}
            count++;
            continue;
          }

          // 匹配拆开后单独呈现的 "of the customization budget is available."
          const segMatch = text.match(/^of\s+the\s+(?:customization\s+)?budget\s+is\s+available\.?$/i);
          if (segMatch) {
            el.textContent = '可用自定义预算。';
            try { translatedNodeSet.add(el); } catch (_) {}
            count++;
          }
        }
      } catch (_) {}
      return count;
    };

    // 专门处理 Toast 通知、带内联超链接及 Markdown 渲染的系统浮层 (e.g. "View archived conversations in [history](notification://history).")
    const translateNotificationContainers = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const candidates = root.querySelectorAll(
          '[role="alert"], [role="status"], [class*="toast"], [class*="notification"], [data-testid*="toast"], [data-testid*="notification"], p, span, div'
        );
        for (let i = 0; i < candidates.length; i++) {
          const el = candidates[i];
          if (translatedNodeSet.has(el) || isProtectedTextNode(el)) continue;
          const text = norm(el.textContent || '');
          if (!text || text.length > 300) continue;

          // 匹配包含超链接或内联文本的归档通知: "View archived conversations in history."
          if (/^View archived conversations in\s+history\.?$/i.test(text)) {
            let deepChildMatched = false;
            for (let c = 0; c < el.children.length; c++) {
              if (/View archived conversations in\s+history/i.test(norm(el.children[c].textContent || ''))) {
                deepChildMatched = true;
                break;
              }
            }
            if (deepChildMatched) continue;

            const link = el.querySelector('a');
            if (link) {
              const childNodes = Array.from(el.childNodes);
              let foundLink = false;
              for (let n = 0; n < childNodes.length; n++) {
                const node = childNodes[n];
                if (node === link) {
                  link.textContent = '历史记录';
                  try { translatedNodeSet.add(link); } catch (_) {}
                  foundLink = true;
                } else if (node.nodeType === 3) {
                  if (!foundLink) {
                    node.nodeValue = '在 ';
                  } else {
                    node.nodeValue = ' 中查看已归档会话。';
                  }
                  try { translatedNodeSet.add(node); } catch (_) {}
                }
              }
              try { translatedNodeSet.add(el); } catch (_) {}
              count++;
              continue;
            } else {
              el.textContent = '在历史记录中查看已归档会话。';
              try { translatedNodeSet.add(el); } catch (_) {}
              count++;
              continue;
            }
          }
        }
      } catch (_) {}
      return count;
    };

    // 专门处理思考过程折叠触发器与计时器动态汉化 (Thinking for Xs / Thought for Xs / Thought Process)
    const translateThinkingTriggers = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const triggers = root.querySelectorAll('[data-testid="thinking-collapsible-trigger"], button[aria-label*="Thought"], button[aria-label*="Thinking"], button[aria-label*="思考"]');
        for (let i = 0; i < triggers.length; i++) {
          const btn = triggers[i];
          const ariaLabel = btn.getAttribute ? btn.getAttribute('aria-label') : null;
          if (ariaLabel) {
            const trLabel = translate(ariaLabel);
            if (trLabel && trLabel !== ariaLabel) {
              btn.setAttribute('aria-label', trLabel);
              count++;
            }
          }
          const textSpan = btn.querySelector ? btn.querySelector('span.text-secondary-foreground, span') : null;
          if (textSpan) {
            const raw = textSpan.textContent || '';
            const trimmed = norm(raw);
            const thinkingForMatch = trimmed.match(/^Thinking\s+for\s+(\d+)\s*s$/i);
            if (thinkingForMatch) {
              const target = `已思考 ${thinkingForMatch[1]} 秒`;
              if (textSpan.textContent !== target) {
                textSpan.textContent = target;
                try { translatedNodeSet.add(textSpan); } catch (_) {}
                count++;
              }
              continue;
            }
            const thoughtForMatch = trimmed.match(/^Thought\s+for\s+(\d+)\s*s$/i);
            if (thoughtForMatch) {
              const target = `思考了 ${thoughtForMatch[1]} 秒`;
              if (textSpan.textContent !== target) {
                textSpan.textContent = target;
                try { translatedNodeSet.add(textSpan); } catch (_) {}
                count++;
              }
              continue;
            }
            if (/^thought\s+process$/i.test(trimmed)) {
              if (textSpan.textContent !== '思考过程') {
                textSpan.textContent = '思考过程';
                try { translatedNodeSet.add(textSpan); } catch (_) {}
                count++;
              }
              continue;
            }
            if (/^thinking$/i.test(trimmed)) {
              if (textSpan.textContent !== '思考中...') {
                textSpan.textContent = '思考中...';
                try { translatedNodeSet.add(textSpan); } catch (_) {}
                count++;
              }
              continue;
            }
          }
        }
      } catch (_) {}
      return count;
    };

    // 专用思维链模式库与短语词典 (Thinking Chain-of-Thought Patterns & Phrases)
    const THINKING_PHRASES = [
      // 定语后置结构平滑处理
      [/(?:the\s+)?regular\s+expression\s+rules\s+in\s+the\s+configuration(?:\s+file)?/gi, '配置文件中的正则表达式规则'],
      [/(?:the\s+)?files?\s+in\s+the\s+workspace/gi, '工作区中的文件'],
      [/(?:the\s+)?files?\s+in\s+the\s+directory/gi, '目录中的文件'],
      [/(?:the\s+)?files?\s+in\s+the\s+codebase/gi, '代码库中的文件'],
      [/(?:the\s+)?test\s+suite\s+in\s+the\s+codebase/gi, '代码库中的测试套件'],
      [/(?:the\s+)?rules?\s+in\s+the\s+configuration(?:\s+file)?/gi, '配置文件中的规则'],
      [/(?:the\s+)?code\s+in\s+the\s+file/gi, '文件中的代码'],
      [/\bcomponent(?:'s)?\b/gi, '组件'],
      [/\bscript\b/gi, '脚本'],
      [/\bfiles?\b/gi, '文件'],

      // 介词短语
      [/in the workspace/gi, '在工作区中'],
      [/in the codebase/gi, '在代码库中'],
      [/in the repository/gi, '在仓库中'],
      [/in the configuration file/gi, '在配置文件中'],
      [/in the configuration/gi, '在配置中'],
      [/in the directory/gi, '在目录中'],
      [/in the file/gi, '在文件中'],
      [/in the implementation/gi, '在具体实现中'],
      [/in the test suite/gi, '在测试套件中'],
      [/in the following/gi, '在以下内容中'],
      [/in order to/gi, '为了'],
      [/based on/gi, '基于'],
      [/according to/gi, '根据'],
      [/at the same time/gi, '同时'],
      [/on the other hand/gi, '另一方面'],
      [/step-by-step|step by step/gi, '逐步'],
      [/as follows/gi, '如下'],
      [/for example/gi, '例如'],
      [/starting with examining/gi, '从检查开始'],
      [/to identify and potentially add/gi, '以识别并添加'],
      [/to identify/gi, '以识别'],
      [/to verify/gi, '以验证'],
      [/to check/gi, '以检查'],
      [/to resolve the issue|to address the issue/gi, '以解决该问题'],
      [/to resolve this|to address this/gi, '以解决此问题'],
      [/to fix this/gi, '以修复此问题'],

      // 名词与术语短语
      [/source code/gi, '源代码'],
      [/unit tests/gi, '单元测试'],
      [/test suite/gi, '测试套件'],
      [/root cause/gi, '根本原因'],
      [/regular expression rules/gi, '正则表达式规则'],
      [/regular expressions/gi, '正则表达式'],
      [/regular expression/gi, '正则表达式'],
      [/translation engine/gi, '翻译引擎'],
      [/translation issue|translation problem/gi, '汉化翻译问题'],
      [/mixed language reports/gi, '中英混杂反馈'],
      [/mixed language/gi, '中英混杂'],
      [/persistent translation issue/gi, '持续存在的汉化翻译问题'],
      [/persistent issue/gi, '持续存在的问题'],
      [/a persistent/gi, '持续存在的'],
      [/possible causes|potential causes/gi, '可能的原因'],
      [/the implementation/gi, '具体实现'],
      [/the component(?:'s)? source code/gi, '组件源代码'],
      [/the generic case/gi, '"generic" 分支'],
      [/reveals the agent termination message/gi, '揭示了智能体终止消息'],
      [/agent termination message/gi, '智能体终止消息'],
      [/agent termination/gi, '智能体终止'],
      [/error notification card/gi, '错误通知卡片'],
      [/error notification/gi, '错误通知'],
      [/error message/gi, '错误信息'],
      [/error card/gi, '错误卡片'],
      [/new patterns that enhance error tolerance/gi, '提升容错能力的新模式'],
      [/new patterns/gi, '新模式'],
      [/error tolerance/gi, '容错能力'],
      [/passed at 100%/gi, '100% 通过'],
      [/all tests passed/gi, '所有测试均已通过'],
      [/\bthe project\b/gi, '项目']
    ];

    const smoothPhrases = (text) => {
      if (!text) return '';
      let res = text;
      for (let i = 0; i < THINKING_PHRASES.length; i++) {
        res = res.replace(THINKING_PHRASES[i][0], THINKING_PHRASES[i][1]);
      }
      res = res
        .replace(/\b(?:a|an|the)\s+/gi, '')
        .replace(/\s*([，。！？；：])/g, '$1')
        .replace(/([，。！？；：])\s*/g, '$1')
        .trim();
      if (res.endsWith('.')) res = res.slice(0, -1) + '。';
      return res;
    };

    const THINKING_PATTERNS = [
      // 1. 开篇陈述与反馈
      [/^The task is to (.+)$/i, (m, p1) => '本次任务是' + smoothPhrases(p1)],
      [/^The user (?:reports|is reporting|reported) (?:that )?(.+)$/i, (m, p1) => '用户反馈' + smoothPhrases(p1)],
      [/^The user is asking (?:for|to) (.+)$/i, (m, p1) => '用户要求' + smoothPhrases(p1)],
      [/^The user wants to (.+)$/i, (m, p1) => '用户希望' + smoothPhrases(p1)],
      [/^The repeated report of (.+) suggests (.+)$/i, (m, p1, p2) => '用户反复反馈的' + smoothPhrases(p1) + '表明' + smoothPhrases(p2)],
      [/^Mixed language reports (?:repeatedly )?appearing point to (.+)$/i, (m, p1) => '反复出现的中英混杂反馈表明' + smoothPhrases(p1)],
      [/^The core issue (?:is|appears to be) (.+)$/i, (m, p1) => '核心问题在于' + smoothPhrases(p1)],
      [/^The root cause (?:is|appears to be) (.+)$/i, (m, p1) => '根本原因似乎在于' + smoothPhrases(p1)],
      [/^The main goal is to (.+)$/i, (m, p1) => '主要目标是' + smoothPhrases(p1)],
      [/^The problem is (?:clearly )?about (.+)$/i, (m, p1) => '问题显然在于' + smoothPhrases(p1)],
      [/^Initial observation:?\s*(.+)$/i, (m, p1) => '初步观察：' + smoothPhrases(p1)],
      [/^This indicates (?:that )?(.+)$/i, (m, p1) => '这表明' + smoothPhrases(p1)],
      [/^This suggests (?:that )?(.+)$/i, (m, p1) => '这表明' + smoothPhrases(p1)],
      [/^This confirms (?:that )?(.+)$/i, (m, p1) => '这证实了' + smoothPhrases(p1)],
      [/^This means (?:that )?(.+)$/i, (m, p1) => '这意味着' + smoothPhrases(p1)],
      [/^The error notification card appears to be rendered by (.+)$/i, (m, p1) => '错误通知卡片似乎由 ' + p1 + ' 渲染'],
      [/^The error card presents several key pieces of information\.?$/i, () => '错误卡片展示了几个关键信息。'],

      // 2. 动词起手式与排查动作
      [/^Analyzing (?:the )?(.+)$/i, (m, p1) => '正在分析' + smoothPhrases(p1)],
      [/^Examining (?:the )?(.+)$/i, (m, p1) => '正在检查' + smoothPhrases(p1)],
      [/^Investigating (?:the )?(?:possible causes|potential causes)?(?: of)?\s*(.+)$/i, (m, p1) => '正在排查' + smoothPhrases(p1)],
      [/^Looking (?:at|into) (?:the )?(.+)$/i, (m, p1) => '查看' + smoothPhrases(p1)],
      [/^Checking (?:the )?(.+)$/i, (m, p1) => '正在检查' + smoothPhrases(p1)],
      [/^Inspecting (?:the )?(.+)$/i, (m, p1) => '正在审查' + smoothPhrases(p1)],
      [/^Reviewing (?:the )?(.+)$/i, (m, p1) => '正在审查' + smoothPhrases(p1)],
      [/^Exploring (?:how )?(.+)$/i, (m, p1) => '正在探索' + smoothPhrases(p1)],
      [/^Testing (?:the )?(.+)$/i, (m, p1) => '正在测试' + smoothPhrases(p1)],
      [/^Verifying (?:that|if|whether)?\s*(.+)$/i, (m, p1) => '正在验证' + smoothPhrases(p1)],
      [/^Searching (?:for )?(.+)$/i, (m, p1) => '正在搜索' + smoothPhrases(p1)],
      [/^Reading (?:the )?(.+)$/i, (m, p1) => '正在读取' + smoothPhrases(p1)],
      [/^Updating (?:the )?(.+)$/i, (m, p1) => '正在更新' + smoothPhrases(p1)],
      [/^Modifying (?:the )?(.+)$/i, (m, p1) => '正在修改' + smoothPhrases(p1)],
      [/^Fixing (?:the )?(.+)$/i, (m, p1) => '正在修复' + smoothPhrases(p1)],
      [/^Resolving (?:the )?(.+)$/i, (m, p1) => '正在解决' + smoothPhrases(p1)],
      [/^Preparing (?:the )?(.+)$/i, (m, p1) => '正在准备' + smoothPhrases(p1)],

      // 3. 第一人称与祈使式动作
      [/^Let's check (?:the )?(.+)$/i, (m, p1) => '让我们检查' + smoothPhrases(p1)],
      [/^Let's examine (?:the )?(.+)$/i, (m, p1) => '让我们查看' + smoothPhrases(p1)],
      [/^Let's inspect (?:the )?(.+)$/i, (m, p1) => '让我们审查' + smoothPhrases(p1)],
      [/^Let's look at (?:the )?(.+)$/i, (m, p1) => '让我们查看' + smoothPhrases(p1)],
      [/^Let's verify (?:that|if|whether)?\s*(.+)$/i, (m, p1) => '让我们验证' + smoothPhrases(p1)],
      [/^Let's run (?:the )?(.+)$/i, (m, p1) => '让我们执行' + smoothPhrases(p1)],
      [/^We need to (.+)$/i, (m, p1) => '我们需要' + smoothPhrases(p1)],
      [/^We should (.+)$/i, (m, p1) => '我们应该' + smoothPhrases(p1)],
      [/^First, (?:let's |we should |we need to )?(.+)$/i, (m, p1) => '首先，' + smoothPhrases(p1)],
      [/^Next, (?:let's |we should |we need to )?(.+)$/i, (m, p1) => '接下来，' + smoothPhrases(p1)],
      [/^Now, (?:let's |we should |we need to )?(.+)$/i, (m, p1) => '现在，' + smoothPhrases(p1)],
      [/^To resolve this, (.+)$/i, (m, p1) => '为了解决此问题，' + smoothPhrases(p1)],
      [/^All tests passed\.?$/i, () => '所有测试均已通过。'],
      [/^Unit tests passed at 100%\.?$/i, () => '单元测试 100% 通过。'],

      // 4. 转折、核对、假设与反思推演 (Wait / Hold on / Double check / Based on / In summary)
      [/^(?:Wait|Hold on), (?:let's |let me |let us )?(.+)$/i, (m, p1) => '等等，让我' + smoothPhrases(p1)],
      [/^Let me double[- ]check (?:the )?(.+)$/i, (m, p1) => '让我仔细复核' + smoothPhrases(p1)],
      [/^Let me check (?:the )?(.+)$/i, (m, p1) => '让我检查' + smoothPhrases(p1)],
      [/^Let me examine (?:the )?(.+)$/i, (m, p1) => '让我查看' + smoothPhrases(p1)],
      [/^Let me verify (?:that|if|whether)?\s*(.+)$/i, (m, p1) => '让我验证' + smoothPhrases(p1)],
      [/^Let me inspect (?:the )?(.+)$/i, (m, p1) => '让我审查' + smoothPhrases(p1)],
      [/^Let me run (?:the )?(.+)$/i, (m, p1) => '让我执行' + smoothPhrases(p1)],
      [/^Let me test (?:the )?(.+)$/i, (m, p1) => '让我测试' + smoothPhrases(p1)],
      [/^Let's consider (?:the )?(.+)$/i, (m, p1) => '让我们考虑' + smoothPhrases(p1)],
      [/^Let's break down (?:the )?(?:problem|task|requirements):?\s*(.*)$/i, (m, p1) => '让我们拆解需求：' + smoothPhrases(p1)],
      [/^Here is what we need to do:?\s*(.*)$/i, (m, p1) => '以下是我们要做的事：' + smoothPhrases(p1)],
      [/^Based on (?:the )?(?:above|previous) (?:analysis|investigation), (.+)$/i, (m, p1) => '基于上述分析，' + smoothPhrases(p1)],
      [/^In conclusion, (.+)$/i, (m, p1) => '总的来说，' + smoothPhrases(p1)],
      [/^In summary, (.+)$/i, (m, p1) => '概括而言，' + smoothPhrases(p1)],
      [/^To fix this issue, (.+)$/i, (m, p1) => '为了解决此问题，' + smoothPhrases(p1)],
      [/^To resolve this issue, (.+)$/i, (m, p1) => '为了解决此问题，' + smoothPhrases(p1)],
      [/^The next step is to (.+)$/i, (m, p1) => '下一步是' + smoothPhrases(p1)],
      [/^This approach ensures that (.+)$/i, (m, p1) => '该方案可确保' + smoothPhrases(p1)],
      [/^Now, let's verify (?:that )?(.+)$/i, (m, p1) => '现在，让我们验证' + smoothPhrases(p1)],
      [/^Let's look at the implementation of (?:the )?(.+)$/i, (m, p1) => '让我们查看 ' + smoothPhrases(p1) + ' 的具体实现'],
      [/^Let's examine the source code of (?:the )?(.+)$/i, (m, p1) => '让我们检查 ' + smoothPhrases(p1) + ' 的源代码'],
      [/^It seems that (.+)$/i, (m, p1) => '看起来' + smoothPhrases(p1)],
      [/^It appears that (.+)$/i, (m, p1) => '看起来' + smoothPhrases(p1)],
      [/^Notice that (.+)$/i, (m, p1) => '注意：' + smoothPhrases(p1)],
      [/^Recall that (.+)$/i, (m, p1) => '回顾可知：' + smoothPhrases(p1)],
      [/^Everything looks good\.?$/i, () => '一切正常。'],
      [/^The implementation is complete\.?$/i, () => '具体实现已完成。'],
      [/^The fix is verified\.?$/i, () => '修复已验证完成。']
    ];

    const translateSingleThinkingSentence = (str) => {
      const trimmed = norm(str);
      if (!trimmed) return str;
      if (DICT[trimmed]) return DICT[trimmed];
      if (LOWER_DICT[trimmed.toLowerCase()]) return LOWER_DICT[trimmed.toLowerCase()];

      for (let i = 0; i < THINKING_PATTERNS.length; i++) {
        const [pattern, handler] = THINKING_PATTERNS[i];
        const match = trimmed.match(pattern);
        if (match) {
          return handler(...match);
        }
      }
      return smoothPhrases(trimmed);
    };

    const translateThinkingLine = (line) => {
      const prefixMatch = line.match(/^(\s*(?:\d+\.|\-|\*)\s*)/);
      const prefix = prefixMatch ? prefixMatch[1] : '';
      const content = prefixMatch ? line.slice(prefix.length) : line;

      const sentences = content.split(/(?<=\.\s+|;\s+|:\s+)/);
      const translated = sentences.map(s => translateSingleThinkingSentence(s)).join('');
      return prefix + translated;
    };

    const translateThinkingText = (raw) => {
      if (!raw || !/[a-zA-Z]/.test(raw)) return null;
      if (typeof raw === 'string' && raw.includes('\n')) {
        const lines = raw.split('\n');
        let anyTranslated = false;
        const translatedLines = lines.map(line => {
          const trimmed = line.trim();
          if (!trimmed || !/[a-zA-Z]/.test(trimmed)) return line;
          const tr = translateThinkingLine(trimmed);
          if (tr && tr !== trimmed) {
            anyTranslated = true;
            const lead = (line.match(/^\s*/) || [''])[0];
            const trail = (line.match(/\s*$/) || [''])[0];
            return lead + tr + trail;
          }
          return line;
        });
        return anyTranslated ? translatedLines.join('\n') : null;
      }
      const trimmed = raw.trim();
      const tr = translateThinkingLine(trimmed);
      if (tr && tr !== trimmed) {
        const lead = (raw.match(/^\s*/) || [''])[0];
        const trail = (raw.match(/\s*$/) || [''])[0];
        return lead + tr + trail;
      }
      return null;
    };

    // 专门扫描并流式重构展开后的思考过程正文内容 (Thinking Process Content Stream)
    const translateThinkingContainers = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const thinkingContainers = root.querySelectorAll(
          '.cursor-edit, [data-testid="thinking-content"], [data-testid="thought-content"], [data-testid="thinking-collapsible-trigger"] ~ div, button[aria-label*="Thought"] ~ div, button[aria-label*="Thinking"] ~ div, button[aria-label*="思考"] ~ div'
        );
        for (let i = 0; i < thinkingContainers.length; i++) {
          const container = thinkingContainers[i];
          const walker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            {
              acceptNode(n) {
                const el = n.nodeType === 1 ? n : n.parentElement;
                if (!el || !el.closest) return NodeFilter.FILTER_REJECT;
                // 绝对保护代码块、代码编辑器与终端
                if (el.closest('pre, code, kbd, samp, var, [data-language], .cm-editor, .monaco-editor, .xterm')) {
                  return NodeFilter.FILTER_REJECT;
                }
                // 绝对保护用户真实输入框
                if (el.closest('[contenteditable="true"], textarea, input')) {
                  return NodeFilter.FILTER_REJECT;
                }
                if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
                if (translatedNodeSet.has(n)) return NodeFilter.FILTER_REJECT;
                return NodeFilter.FILTER_ACCEPT;
              }
            }
          );

          let current;
          while ((current = walker.nextNode())) {
            const original = current.nodeValue;
            const translated = translateThinkingText(original);
            if (translated && norm(original) !== norm(translated)) {
              current.nodeValue = translated;
              translatedNodeSet.add(current);
              count++;
            }
          }
        }
      } catch (_) {}
      return count;
    };

    // 弱引用记录已挂载 MutationObserver 的根节点与 ShadowRoot
    const observedRoots = new WeakSet();

    // 统一 MutationObserver 挂载器
    let observer = null;
    const observeRoot = (target) => {
      if (!target || !target.nodeType || observedRoots.has(target) || !observer) return;
      try {
        observer.observe(target, {
          subtree: true,
          childList: true,
          characterData: true,
          attributes: true,
          attributeFilter: ['aria-label', 'placeholder', 'data-placeholder', 'title', 'alt', 'data-tooltip', 'value']
        });
        observedRoots.add(target);
      } catch (_) {}
    };

    // 递归发现并遍历包含 ShadowRoot 在内的所有 DOM 根
    const forAllRoots = (root, callback) => {
      if (!root) return;
      callback(root);
      try {
        if (root.querySelectorAll) {
          const allDescendants = root.querySelectorAll('*');
          for (let i = 0; i < allDescendants.length; i++) {
            const el = allDescendants[i];
            if (el.shadowRoot) {
              forAllRoots(el.shadowRoot, callback);
            }
          }
        }
      } catch (_) {}
    };

    // 全量执行单次翻译（穿透所有 Shadow DOM 与挂载根）
    const runTranslation = () => {
      try {
        const root = document.body || document.documentElement;
        if (!root) return;
        if (document.documentElement && document.documentElement.getAttribute('lang') !== LANG) {
          document.documentElement.setAttribute('lang', LANG);
        }
        let textCount = 0;
        let attrCount = 0;
        let hlCount = 0;
        let budgetCount = 0;
        let thinkingCount = 0;

        forAllRoots(root, (currentRoot) => {
          observeRoot(currentRoot);
          thinkingCount += translateThinkingTriggers(currentRoot);
          thinkingCount += translateThinkingContainers(currentRoot);
          budgetCount += translateBudgetContainers(currentRoot);
          budgetCount += translateNotificationContainers(currentRoot);
          hlCount += translateHighlightedContainers(currentRoot);
          textCount += translateTextNodes(currentRoot);
          attrCount += translateAttributes(currentRoot);
        });

        if (textCount > 0 || attrCount > 0 || hlCount > 0 || budgetCount > 0 || thinkingCount > 0) {
          console.log(`[AGY-ZH] Translated ${textCount} text nodes, ${attrCount} attributes, ${hlCount} highlighted containers, ${budgetCount} budget containers, and ${thinkingCount} thinking items.`);
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
            if (typeof data === 'string' && data.length > 2 && data.length < 500) {
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

      // 拦截 window.Notification (消灭原生与网页通知英文)
      if (typeof window !== 'undefined' && window.Notification) {
        try {
          const OrigNotification = window.Notification;
          const PatchedNotification = function(title, opt) {
            try {
              const trTitle = translate(title) || title;
              const newOpt = opt ? Object.assign({}, opt) : {};
              if (newOpt.body) {
                newOpt.body = translate(newOpt.body) || newOpt.body;
              }
              return new OrigNotification(trTitle, newOpt);
            } catch (_) {
              return new OrigNotification(title, opt);
            }
          };
          PatchedNotification.prototype = OrigNotification.prototype;
          PatchedNotification.permission = OrigNotification.permission;
          if (OrigNotification.requestPermission) {
            PatchedNotification.requestPermission = OrigNotification.requestPermission.bind(OrigNotification);
          }
          window.Notification = PatchedNotification;
        } catch (_) {}
      }
    } catch (_) {}

    // 监听 DOM 树变化并根据交互场景智能分流：
    // 默认在当前微任务中同步增量直出（先于浏览器 Paint 绘制完成，彻底根除英文闪烁），
    // 超过 15ms 保险丝的超大型长列表变更，安全移交后台轻量防抖处理。
    let mutationTimer = null;
    let maxWaitDeadline = 0;

    const handleMutations = () => {
      maxWaitDeadline = 0;
      runTranslation();
    };

    observer = new MutationObserver((mutations) => {
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
                syncCount += translateThinkingTriggers(node);
                syncCount += translateThinkingContainers(node);
                syncCount += translateBudgetContainers(node);
                syncCount += translateNotificationContainers(node);
                syncCount += translateHighlightedContainers(node);
                syncCount += translateTextNodes(node);
                syncCount += translateAttributes(node);
                if (node.shadowRoot) {
                  forAllRoots(node.shadowRoot, (sr) => {
                    observeRoot(sr);
                    syncCount += translateThinkingTriggers(sr);
                    syncCount += translateThinkingContainers(sr);
                    syncCount += translateBudgetContainers(sr);
                    syncCount += translateNotificationContainers(sr);
                    syncCount += translateHighlightedContainers(sr);
                    syncCount += translateTextNodes(sr);
                    syncCount += translateAttributes(sr);
                  });
                }
              } else if (node.nodeType === 3) { // 文本节点
                if (!translatedNodeSet.has(node) && !isProtectedTextNode(node)) {
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
              const parent = node.parentElement;
              if (parent && parent.closest && parent.closest('.cursor-edit, [data-testid="thinking-content"], [data-testid="thought-content"], [data-testid="thinking-collapsible-trigger"] ~ div, button[aria-label*="Thought"] ~ div, button[aria-label*="Thinking"] ~ div, button[aria-label*="思考"] ~ div')) {
                if (!parent.closest('pre, code, kbd, samp, var, [data-language], .cm-editor, .monaco-editor, .xterm, [contenteditable="true"], textarea, input')) {
                  const orig = node.nodeValue;
                  const tr = translateThinkingText(orig);
                  if (tr && norm(orig) !== norm(tr)) {
                    node.nodeValue = tr;
                    translatedNodeSet.add(node);
                    syncCount++;
                  }
                }
              } else if (!isProtectedTextNode(node)) {
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

    // 拦截 Element.prototype.attachShadow，实现 Shadow DOM 的首帧即时汉化与动态监听
    try {
      const origAttachShadow = Element.prototype.attachShadow;
      if (origAttachShadow) {
        Element.prototype.attachShadow = function(init) {
          const shadowRoot = origAttachShadow.call(this, init);
          try {
            observeRoot(shadowRoot);
            setTimeout(() => {
              translateThinkingTriggers(shadowRoot);
              translateThinkingContainers(shadowRoot);
              translateBudgetContainers(shadowRoot);
              translateNotificationContainers(shadowRoot);
              translateHighlightedContainers(shadowRoot);
              translateTextNodes(shadowRoot);
              translateAttributes(shadowRoot);
            }, 0);
          } catch (_) {}
          return shadowRoot;
        };
      }
    } catch (_) {}

    // 安全挂载 MutationObserver
    const attachObserver = () => {
      const target = document.documentElement || document.body || document;
      if (target && target.nodeType) {
        try {
          observeRoot(target);
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
