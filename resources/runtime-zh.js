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
      if ((text.endsWith('>') || text.endsWith('›') || text.endsWith('→')) && (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()])) {
        return (DICT[text.slice(0, -1).trim()] || LOWER_DICT[lower.slice(0, -1).trim()]) + ' ' + text.slice(-1);
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

      // 1.23 欢迎问候模式匹配 (Welcome to Antigravity / Welcome to ...)
      if (/^Welcome\s+to\s+(.+)$/i.test(text)) {
        const m = text.match(/^Welcome\s+to\s+(.+)$/i);
        const targetApp = DICT[m[1].trim()] || LOWER_DICT[m[1].trim().toLowerCase()] || m[1].trim();
        return '欢迎使用 ' + targetApp;
      }
      if (/^Welcome\s+to$/i.test(text)) {
        return '欢迎使用 ';
      }

      // 1.24 动态空状态与通知提示
      if (/^No\s+changes\s+to\s+review\.?$/i.test(text)) {
        return '没有需要审查的更改';
      }
      if (/^No\s+uploads\.?$/i.test(text)) {
        return '暂无上传内容';
      }

      // 1.25 运行策略与权限预设描述
      if (/^Every\s+command\s+requires\s+approval\.?$/i.test(text)) {
        return '每条命令都需要批准。';
      }
      if (/^Ask\s+before\s+sensitive\s+operations\.?$/i.test(text)) {
        return '执行敏感操作前先询问。';
      }
      if (/^Run\s+all\s+commands\s+without\s+restrictions\.?$/i.test(text)) {
        return '无限制执行所有命令。';
      }
      if (/^Security\s+agent\s+decides\s+if\s+commands\s+run\.?$/i.test(text)) {
        return '由安全智能体决定命令是否运行。';
      }
      if (/^Automatically\s+decide\s+if\s+commands\s+run\.?$/i.test(text)) {
        return '自动决定命令是否运行。';
      }
      if (/^Use\s+Global\s+Settings?$/i.test(text)) {
        return '使用全局设置';
      }
      if (/^Use\s+Project\s+Settings?$/i.test(text)) {
        return '使用项目设置';
      }

      // 1.26 动态 AI 积分额度标签匹配 (Available AI Credits: 0 / 100 ...)
      const aiCreditsMatch = text.match(/^Available\s+AI\s+Credits\s*:\s*(\d+(?:,\d+)?(?:\.\d+)?)$/i);
      if (aiCreditsMatch) {
        return `可用 AI 积分: ${aiCreditsMatch[1]}`;
      }
      if (/^Available\s+AI\s+Credits\s*:?$/i.test(text)) {
        return '可用 AI 积分：';
      }

      // 1.27 第三方模型下线与方案变更动态通知
      // e.g. "Sonnet 5.5 is now available on paid Pro and Ultra plans. Third-party model access will no longer be available on your current plan starting on November 2, 2026."
      const modelAvailableThirdPartyMatch = text.match(/^(.+?)\s+is\s+now\s+available\s+on\s+paid\s+Pro\s+and\s+Ultra\s+plans\.\s*Third-party\s+model\s+access\s+will\s+no\s+longer\s+be\s+available\s+on\s+your\s+current\s+plan\s+starting\s+on\s+([A-Za-z]+(?:\s+\d{1,2})?,\s*\d{4})\.?$/i);
      if (modelAvailableThirdPartyMatch) {
        const modelName = modelAvailableThirdPartyMatch[1].trim();
        const zhDate = formatEnDate(modelAvailableThirdPartyMatch[2]);
        return `${modelName} 现已在付费 Pro 和 Ultra 方案中可用。自 ${zhDate}起，您当前的方案将不再支持第三方模型访问。`;
      }

      const modelAvailablePlansMatch = text.match(/^(.+?)\s+is\s+now\s+available\s+on\s+paid\s+Pro\s+and\s+Ultra\s+plans\.?$/i);
      if (modelAvailablePlansMatch) {
        return `${modelAvailablePlansMatch[1].trim()} 现已在付费 Pro 和 Ultra 方案中可用。`;
      }

      const thirdPartyRemovedMatch = text.match(/^Third-party\s+model\s+access\s+will\s+no\s+longer\s+be\s+available\s+on\s+your\s+current\s+plan\s+starting\s+on\s+([A-Za-z]+(?:\s+\d{1,2})?,\s*\d{4})\.?$/i);
      if (thirdPartyRemovedMatch) {
        const zhDate = formatEnDate(thirdPartyRemovedMatch[1]);
        return `自 ${zhDate}起，您当前的方案将不再支持第三方模型访问。`;
      }

      // 1.28 悬浮操作与快速复制指令精确匹配 (Hover Copy Popup & Quick Actions)
      if (/^copy$/i.test(text)) return '复制';
      if (/^copied$/i.test(text)) return '已复制';
      if (/^copy\s+code$/i.test(text)) return '复制代码';
      if (/^copy\s+link(?: address)?$/i.test(text)) return '复制链接';
      if (/^copy\s+path$/i.test(text)) return '复制路径';
      if (/^copy\s+file\s+path$/i.test(text)) return '复制文件路径';
      if (/^copy\s+full\s+path$/i.test(text)) return '复制完整路径';
      if (/^copy\s+citation$/i.test(text)) return '复制引用';
      if (/^copy\s+text$/i.test(text)) return '复制文本';
      if (/^copy\s+all$/i.test(text)) return '复制全部';

      // 1.29 短格式相对时间戳匹配 (e.g. "3m ago", "5m ago", "1h ago", "2d ago", "just now")
      const relTimeMatch = text.match(/^(\d+)\s*(s|m|h|d|w|mo|y)\s+ago$/i);
      if (relTimeMatch) {
        const num = relTimeMatch[1];
        const unit = relTimeMatch[2].toLowerCase();
        const unitMap = {
          s: '秒前',
          m: '分钟前',
          h: '小时前',
          d: '天前',
          w: '周前',
          mo: '个月前',
          y: '年前'
        };
        return `${num} ${unitMap[unit] || '前'}`;
      }
      if (/^just\s+now$/i.test(text)) return '刚刚';

      // 1.30 法律条款引导前缀与自定义智能体兜底 (Visit ..., Custom Agents)
      if (/^visit\s*$/i.test(text)) return '访问 ';
      if (/^custom\s+agents?$/i.test(text)) return '自定义智能体';
      if (/^no\s+custom\s+agents?\s+yet\.?$/i.test(text)) return '暂无自定义智能体。';
      if (/^自定义\s*Agent(?:s)?$/i.test(text)) return '自定义智能体';

      // 1.31 官方插件与扩展卡片描述动态匹配 (支持完整句与带省略号截断)
      if (/^Search and retrieve official documentation across Google Cloud/i.test(text) || /^Search and retrieve official documentation acr(?:\.\.\.|…)?$/i.test(text)) {
        return '检索涵盖 Google Cloud、Gemini、Android、Firebase、Flutter 及 Web 的官方文档。需要 Google Cloud 凭据 (ADC) 或 API 密钥。';
      }
      if (/^Integration skill and tools for Google Maps Platform/i.test(text) || /^Integration skill and tools for Google Maps Pl(?:\.\.\.|…)?$/i.test(text)) {
        return 'Google Maps Platform API 的集成技能与工具套件。';
      }
      if (/^Official plugin for Dart and Flutter that installs/i.test(text)) {
        return 'Dart 与 Flutter 官方插件，安装 Flutter/Dart 技能、规则、自定义智能体与 Dart MCP 服务器，用于从单一代码库构建面向移动端、Web、桌面及嵌入式设备的原生编译高质感应用。';
      }
      if (/^This plugin provides a specialized suite of skills for data engineers/i.test(text) || /^This plugin provides a specialized suite of skill(?:\.\.\.|…)?$/i.test(text)) {
        return '此插件为在 Google Cloud 上工作的数据工程师与数据库专家提供专属技能套件。它作为专家助手，让您能在喜爱的编程智能体中使用自然语言提示构建复杂数据流水线、使用 dbt 转换数据、编写 Spark 和 BigQuery SQL 笔记本，并在 GCP 数据生态中编排端到端工作流。';
      }
      if (/^Google Cloud guidance for coding agents/i.test(text)) {
        return '针对编程智能体的 Google Cloud 指南：首个项目快速上手、鉴权与凭据选择，以及 gcloud CLI 命令的安全关键验证。包含 Google Developer Knowledge MCP 服务器，以获取扎实、最新的 Google Cloud 文档。';
      }

      // 1.32 Gemini 3.8 Flash 升级与推荐卡片动态匹配
      if (/^Start using Gemini 3\.8 Flash,\s*our best Flash model\.?$/i.test(text)) {
        return '开始使用 Gemini 3.8 Flash，我们最强大的 Flash 模型。';
      }
      if (/^Use Gemini 3\.8 Flash!\s*As a newer model,\s*it delivers more intelligence at 2x the speed for 70% less cost than Gemini 3\.1 Pro\.?$/i.test(text)) {
        return '使用 Gemini 3.8 Flash！作为更新的模型，它比 Gemini 3.1 Pro 速度提升 2 倍，成本降低 70%，同时带来更出色的智能表现。';
      }

      // 1.33 配额与时间完全刷新动态匹配 (Quota limits and refresh duration localization)
      const quotaWeeklyRefreshMatch = text.match(/^You have used (some|all) of your weekly limit,\s*(?:it|which)?\s*will fully refresh in\s+(.+?)\.?$/i);
      if (quotaWeeklyRefreshMatch) {
        const isAll = quotaWeeklyRefreshMatch[1].toLowerCase() === 'all';
        const durationStr = quotaWeeklyRefreshMatch[2].trim();
        const zhDuration = durationStr
          .replace(/(\d+)\s*days?/gi, '$1 天')
          .replace(/(\d+)\s*hours?/gi, '$1 小时')
          .replace(/(\d+)\s*minutes?/gi, '$1 分钟')
          .replace(/(\d+)\s*seconds?/gi, '$1 秒')
          .replace(/,\s*/g, ' ')
          .trim();
        const prefix = isAll ? '您的每周配额已用尽' : '您已使用部分每周配额';
        return `${prefix}，将在 ${zhDuration}后完全刷新。`;
      }

      const quotaFiveHourRefreshMatch = text.match(/^You have used (some|all) of your (?:five\s*hour|5-hour)\s+limit,\s*(?:it|which)?\s*will fully refresh in\s+(.+?)\.?$/i);
      if (quotaFiveHourRefreshMatch) {
        const isAll = quotaFiveHourRefreshMatch[1].toLowerCase() === 'all';
        const durationStr = quotaFiveHourRefreshMatch[2].trim();
        const zhDuration = durationStr
          .replace(/(\d+)\s*hours?/gi, '$1 小时')
          .replace(/(\d+)\s*minutes?/gi, '$1 分钟')
          .replace(/(\d+)\s*seconds?/gi, '$1 秒')
          .replace(/,\s*/g, ' ')
          .trim();
        const prefix = isAll ? '您的 5 小时配额已用尽' : '您已使用部分 5 小时配额';
        return `${prefix}，将在 ${zhDuration}后完全刷新。`;
      }

      const quotaGeneralRefreshMatch = text.match(/^(?:it|which)?\s*will fully refresh in\s+(.+?)\.?$/i);
      if (quotaGeneralRefreshMatch) {
        const durationStr = quotaGeneralRefreshMatch[1].trim();
        const zhDuration = durationStr
          .replace(/(\d+)\s*days?/gi, '$1 天')
          .replace(/(\d+)\s*hours?/gi, '$1 小时')
          .replace(/(\d+)\s*minutes?/gi, '$1 分钟')
          .replace(/(\d+)\s*seconds?/gi, '$1 秒')
          .replace(/,\s*/g, ' ')
          .trim();
        return `将在 ${zhDuration}后完全刷新。`;
      }

      // 1.34 官方技能卡片动态前缀与截断匹配 (AlphaFold, AlphaGenome, Android CLI, Automation, ChEMBL)
      if (/^Retrieve and analyze AlphaFold predicted structures for a protein/i.test(text)) {
        return '获取并分析蛋白质的 AlphaFold 预测结构。当用户提供特定 UniProt ID 并需要结构置信度指标 (pLDDT)、结构域边界分析或无序评估时使用。若用户仅提供蛋白质名称、基因名称或氨基酸序列，请先要求提供 UniProt ID。';
      }
      if (/^Constructs deep-links and URLs for the AlphaGenome Atlas website/i.test(text)) {
        return '为 AlphaGenome Atlas 网站构建深层链接与 URL。支持生成单变异体探索链接 (基于 1 的 chr:pos:ref>alt)、基因组位点视图 (基于 1 的闭区间 chr:start-end)、候选摘要表以及 AlphaGenome 参考序列与备选预测比对。';
      }
      if (/^Analyzes genetic variant effects on gene expression/i.test(text)) {
        return '使用 AlphaGenome API 分析遗传变异对基因表达 (RNA-seq)、染色质可及性 (DNASE)、组蛋白标记 (ChIP) 和转录因子的影响。当用户询问非编码变异效应、致病性、临床意义、疾病关联、功能效应、基因表达变化、剪接破坏或启动子与增强子中的调控效应时使用。';
      }
      if (/^Score,\s*annotate,\s*and analyze the functional impact of genetic variants/i.test(text)) {
        return '使用 AlphaGenome 变异影响 (AVI) 分数评估、注释和分析遗传变异的功能影响。通过 AlphaGenome Atlas API 以 chr:pos:ref>alt 格式查询变异、注释 VCF/表格检出集、执行饱和诱变窗口扫描以及提取 GENCODE v46 GTF 基因/外显子/连接点坐标。';
      }
      if (/^Provides instructions for installing and using the ['`]?android['`]? CLI/i.test(text)) {
        return '提供安装和使用 \'android\' CLI 的指南。\'android\' 命令行工具是 Android 开发的关键工具，可帮助您创建新的 Android 项目、在设备上运行 Android 应用程序、管理 Android 虚拟设备并与之交互（包括截图和 UI 检查）、管理 Android SDK 组件、查阅官方 Android 文档，以及发现和安装官方 Android 技能。';
      }
      if (/^Interactive guide to design and create a scheduled background automation/i.test(text)) {
        return '设计和创建定时后台自动化任务的交互式指南。当用户希望创建自动化或周期性定时任务时（如“每天早晨总结我的邮件”、“每周一向我发送待办列表”）使用此技能。亦可通过 /automation 斜杠命令触发。';
      }
      if (/^Query the ChEMBL database for bioactive molecules/i.test(text)) {
        return '查询 ChEMBL 数据库以获取生物活性分子、药物靶点、生物活性数据、已批准药物和化学结构。当用户询问化合物、靶点、IC50/Ki 值、药物机制或结构搜索时使用。';
      }

      // 1.35 Google 文档官方插件详情页动态模式匹配 (Google Docs Plugin Page)
      if (/^This is a preview of the plugin's source/i.test(text)) {
        return '这是该插件源代码的预览。在您安装之前，以下内容均未激活。';
      }
      if (/^Install this plugin to use this prompt/i.test(text)) {
        return '安装此插件以使用此提示词';
      }
      if (/^Summarize this design doc/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 50
          ? '总结此设计文档并列出...'
          : '总结此设计文档并列出关键要点';
      }
      if (/^Draft a launch announcement in a new doc/i.test(text)) {
        return '根据我的笔记在新文档中起草发布公告';
      }
      if (/^Reply to the open comments on my doc/i.test(text)) {
        return '回复我文档中的待处理评论并将其解决';
      }
      if (/^Read and write your Google Docs/i.test(text)) {
        return '读取并编辑您的 Google 文档。通过链接总结任意文档、在新文档中起草提案与公告，以及回复并解决待处理评论。';
      }
      if (/^Read,\s*create,\s*edit,\s*and manage Google Docs/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 90
          ? '读取、创建、编辑和管理 Google 文档。当用户分享 docs.google.com 网址，或要求搜索、阅读、撰写、创建...'
          : '读取、创建、编辑和管理 Google 文档。当用户分享 docs.google.com 网址，或要求搜索、阅读、撰写、创建、评论及编辑 Google 文档时使用。';
      }

      // 1.36 科学计算插件技能自适应截断动态匹配 (Science Plugin Skills Auto-complete)
      if (/^Fetch Evolutionary Conservation scores \(phyloP,\s*phastCons\)/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 150
          ? '从 UCSC 基因组浏览器获取进化保守性评分 (phyloP, phastCons) 与转录因子结合位点...'
          : '从 UCSC 基因组浏览器获取进化保守性评分 (phyloP, phastCons) 和转录因子结合位点 (TFBS)。在分析基因组变异或区域是否具有进化保守性、重要功能或受转录因子调控时使用。';
      }
      if (/^Queries the UniBind database for experimentally validated/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 150
          ? '查询 UniBind 数据库以获取经实验验证的转录因子 (TF) 结合位点...'
          : '查询 UniBind 数据库以获取经过实验验证的转录因子 (TF) 结合位点。用于检索直接的 TF-DNA 相互作用数据集、下载结合位点坐标进行本地分析，或按物种、细胞系或 TF 名称列出可用数据集。';
      }
      if (/^Access protein metadata,\s*function,\s*taxonomy/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 150
          ? '访问涵盖 UniProtKB、UniParc 和 UniRef 的蛋白质元数据、功能与序列...'
          : '访问涵盖 UniProtKB、UniParc 和 UniRef 的蛋白质元数据、功能、分类学与序列。用于搜索蛋白质、映射标识符或检索功能注释与发表文献。';
      }
      if (/^Checks whether the uv Python package manager is installed/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 100
          ? '检查是否已安装 uv Python 包管理器，若缺失则自动安装。确保 uv 存在于环境变量中...'
          : '检查是否已安装 uv Python 包管理器，若缺失则自动安装。确保 uv 存在于系统环境变量 PATH 中。当其他技能需要 uv 作为前置依赖时使用。';
      }
      if (/^Distills a completed user workflow or interaction into a reusable/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 120
          ? '将已完成的用户工作流或交互提炼为可复用的智能体技能...'
          : '将已完成的用户工作流或交互提炼为可复用的智能体技能。当用户要求将其工作流、交互或多步骤过程转为技能时使用。';
      }
      if (/^Retrieve and analyze AlphaFold predicted structures for a/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 150
          ? '获取并分析蛋白质的 AlphaFold 预测结构...'
          : '获取并分析蛋白质的 AlphaFold 预测结构。当用户提供特定 UniProt ID 并需要结构置信度指标 (pLDDT)、结构域边界分析或无序评估时使用。若用户仅提供蛋白质名称、基因名称或氨基酸序列，请先要求提供 UniProt ID。';
      }
      if (/^Constructs deep-links and URLs for the AlphaGenome Atlas/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 150
          ? '为 AlphaGenome Atlas 网站构建深层链接与 URL...'
          : '为 AlphaGenome Atlas 网站构建深层链接与 URL。支持生成单变异体探索链接 (基于 1 的 chr:pos:ref>alt)、基因组位点视图 (基于 1 的闭区间 chr:start-end)、候选摘要表以及 AlphaGenome 参考序列与备选预测比对。';
      }
      if (/^Analyzes genetic variant effects on gene expression/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 150
          ? '使用 AlphaGenome API 分析遗传变异对基因表达的影响...'
          : '使用 AlphaGenome API 分析遗传变异对基因表达 (RNA-seq)、染色质可及性 (DNASE)、组蛋白标记 (ChIP) 和转录因子的影响。当用户询问非编码变异效应、致病性、临床意义、疾病关联、功能效应、基因表达变化、剪接破坏或启动子与增强子中的调控效应时使用。';
      }
      if (/^Score,\s*annotate,\s*and analyze the functional impact of genetic/i.test(text)) {
        return text.endsWith('...') || text.endsWith('…') || text.length < 150
          ? '使用 AlphaGenome 变异影响 (AVI) 分数评估遗传变异...'
          : '使用 AlphaGenome 变异影响 (AVI) 分数评估、注释和分析遗传变异的功能影响。通过 AlphaGenome Atlas API 以 chr:pos:ref>alt 格式查询变异、注释 VCF/表格检出集、执行饱和诱变窗口扫描以及提取 GENCODE v46 GTF 基因/外显子/连接点坐标。';
      }

      // 1.37 科学计算等插件标签清洗匹配
      if (/^(?:插件[:：]\s*)?科学计算\s*\((?:Science|science)\)$/i.test(text)) {
        return text.includes('插件') ? '插件: 科学计算' : '科学计算';
      }

      // 2. 正则动态匹配
      for (let i = 0; i < RULES.length; i++) {
        const item = RULES[i];
        try {
          const reg = item[0] instanceof RegExp ? item[0] : new RegExp(item[0]);
          const repl = item[1];
          if (reg.test(text)) {
            let res = text.replace(reg, repl);
            if (/后完全刷新/.test(res)) {
              res = res
                .replace(/(\d+)\s*days?/gi, '$1 天')
                .replace(/(\d+)\s*hours?/gi, '$1 小时')
                .replace(/(\d+)\s*minutes?/gi, '$1 分钟')
                .replace(/(\d+)\s*seconds?/gi, '$1 秒')
                .replace(/,\s*/g, ' ');
            }
            return res;
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

        // 0.2 【操作控件与悬浮气泡特赦】无论处于何种代码块、编辑器或正文容器内，交互操作按钮、复制提示及气泡菜单绝对允许汉化！
        const rawContent = (node.nodeValue || el.textContent || '').trim();
        if (/^copy(?:\s+(?:code|link|path|all|text|content|markdown|file\s+path|full\s+path|citation))?$/i.test(rawContent) || /^copied$/i.test(rawContent)) {
          return false;
        }

        // 若元素自身或直接父级是明确的操作按钮、复制控件、气泡浮层或 Tooltip，且不是代码文本行自身
        if (el.closest('button, [role="button"], [role="tooltip"], [role="menuitem"], [class*="copy"], [class*="tooltip"], [class*="popover"], [class*="popup"], [class*="bubble"], [class*="hover-card"], [class*="hovercard"], [class*="floating"], [data-floating-ui-portal], [data-radix-popper-content-wrapper]')) {
          if (!el.closest('.cm-line, .view-line')) {
            return false;
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
        if (el.closest('.find-widget, .monaco-findInput, [class*="find-widget"], [class*="search-widget"], [class*="customization"], [class*="budget"], [class*="progress"], [class*="segmented"], [class*="toggle"], [class*="badge"], [role="tooltip"], [class*="tooltip"], button, [role="button"], [class*="copy"], [class*="popover"], [class*="popup"], [class*="hover-card"], [class*="bubble"]')) return false;
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

    // 专门处理安全须知、服务条款与数据使用同意复选框容器
    const translateConsentContainers = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const labels = root.querySelectorAll('label, [class*="checkbox"], [class*="terms"], span, p');
        for (let i = 0; i < labels.length; i++) {
          const el = labels[i];
          if (translatedNodeSet.has(el) || isProtectedTextNode(el)) continue;
          const text = norm(el.textContent || '');
          if (!text) continue;

          if (/^Yes,\s+I\s+agree\s+to\s+help\s+improve/i.test(text) && /Interactions\s+data/i.test(text)) {
            for (let j = 0; j < el.childNodes.length; j++) {
              const node = el.childNodes[j];
              if (node.nodeType === 3) {
                const val = norm(node.nodeValue);
                if (/^Yes,\s+I\s+agree\s+to\s+help\s+improve\s*$/i.test(val)) {
                  node.nodeValue = '是的，我同意协助改进 ';
                  count++;
                } else if (/^by\s+allowing\s+Google\s+to\s+collect\s+and\s+use\s+my\s+Interactions\s+data,\s*subject\s+to\s+the$/i.test(val)) {
                  node.nodeValue = '（通过允许 Google 收集并使用我的互动数据），须遵守 ';
                  count++;
                } else if (/^\.?\s*I\s+understand\s+I\s+can\s+choose\s+to\s+opt\s+out\s+later\s+whenever\s+I\s+want\s+via\s+my\s+settings\.?$/i.test(val)) {
                  node.nodeValue = '。我知道我可以随时通过个人设置选择停用。';
                  count++;
                } else if (/^\s*and\s*$/i.test(val)) {
                  node.nodeValue = ' 和 ';
                  count++;
                }
              } else if (node.nodeType === 1 && node.tagName === 'A') {
                const linkText = norm(node.textContent);
                if (/Google\s+Privacy\s+Policy/i.test(linkText)) {
                  node.textContent = 'Google 隐私权政策';
                  count++;
                } else if (/Terms\s+of\s+Service/i.test(linkText)) {
                  node.textContent = node.textContent.replace(/Terms\s+of\s+Service/i, '服务条款');
                  count++;
                }
              }
            }
            try { translatedNodeSet.add(el); } catch (_) {}
          }

          if (/Visit\s+(?:Legal\s+Help|法律帮助)/i.test(text)) {
            for (let j = 0; j < el.childNodes.length; j++) {
              const node = el.childNodes[j];
              if (node.nodeType === 3) {
                const val = norm(node.nodeValue);
                if (/^Visit$/i.test(val)) {
                  node.nodeValue = '访问 ';
                  count++;
                } else if (/^to\s+ask\s+for\s+content\s+changes\s+for\s+legal\s+reasons\.?$/i.test(val)) {
                  node.nodeValue = '以申请因法律原因更改内容。';
                  count++;
                }
              } else if (node.nodeType === 1 && (node.tagName === 'A' || (node.matches && node.matches('a, [class*="link"]')))) {
                const linkText = norm(node.textContent);
                if (/Legal\s+Help/i.test(linkText)) {
                  node.textContent = '法律帮助';
                  count++;
                }
              }
            }
            try { translatedNodeSet.add(el); } catch (_) {}
          }
        }
      } catch (_) {}
      return count;
    };

    // 专门处理会话历史迁移与检索提示卡片复合容器 (This page is going away soon)
    const translateHistoryNoticeContainers = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const containers = root.querySelectorAll('div, section, [role="alert"], [class*="notice"], [class*="banner"]');
        for (let i = 0; i < containers.length; i++) {
          const el = containers[i];
          if (translatedNodeSet.has(el) || isProtectedTextNode(el)) continue;
          const text = norm(el.textContent || '');
          if (text.includes('This page is going away soon') || (text.includes('Search conversations with') && text.includes('in the top left'))) {
            const spans = el.querySelectorAll('span, p, div');
            for (let j = 0; j < spans.length; j++) {
              const sp = spans[j];
              const spText = norm(sp.textContent || '');
              if (spText === 'This page is going away soon') {
                sp.textContent = '此页面即将停用';
                count++;
              } else if (spText.startsWith('Search conversations with') && spText.endsWith('in the top left.')) {
                for (let k = 0; k < sp.childNodes.length; k++) {
                  const node = sp.childNodes[k];
                  if (node.nodeType === 3) {
                    const nv = norm(node.nodeValue);
                    if (nv.startsWith('Search conversations with')) {
                      node.nodeValue = '使用左上角的 ';
                      count++;
                    } else if (nv.endsWith('in the top left.')) {
                      node.nodeValue = ' 搜索会话。';
                      count++;
                    }
                  }
                }
              } else if (spText.startsWith('View archived in the sidebar') && spText.includes('menu)')) {
                for (let k = 0; k < sp.childNodes.length; k++) {
                  const node = sp.childNodes[k];
                  if (node.nodeType === 3) {
                    const nv = norm(node.nodeValue);
                    if (nv.startsWith('View archived in the sidebar')) {
                      node.nodeValue = '在侧边栏中查看已归档会话';
                      count++;
                    } else if (nv.startsWith('(') || nv.startsWith(' (')) {
                      node.nodeValue = '（';
                      count++;
                    } else if (nv.includes('menu).')) {
                      node.nodeValue = ' 菜单）。';
                      count++;
                    }
                  }
                }
              }
            }
            try { translatedNodeSet.add(el); } catch (_) {}
          }
        }
      } catch (_) {}
      return count;
    };

    // 专门处理悬浮气泡、复制按钮与快速操作浮窗 (Floating Copy Widgets & Hover Cards)
    const translateFloatingCopyWidgets = (root) => {
      if (!root) return 0;
      let count = 0;
      try {
        const candidates = root.querySelectorAll ? root.querySelectorAll('button, a, span, div, [role="button"], [class*="copy"], [class*="popup"], [class*="popover"], [class*="hover"], [class*="bubble"], [class*="card"], [class*="floating"], [data-radix-popper-content-wrapper]') : [];
        for (let i = 0; i < candidates.length; i++) {
          const el = candidates[i];
          if (el.children.length === 0 || (el.children.length === 1 && el.children[0].tagName === 'SVG')) {
            const txt = (el.textContent || '').trim();
            if (/^copy$/i.test(txt)) {
              for (let child = el.firstChild; child; child = child.nextSibling) {
                if (child.nodeType === 3 && child.nodeValue.trim().toLowerCase() === 'copy') {
                  const lead = (child.nodeValue.match(/^\s*/) || [''])[0];
                  const trail = (child.nodeValue.match(/\s*$/) || [''])[0];
                  child.nodeValue = lead + '复制' + trail;
                  try { translatedNodeSet.add(child); } catch (_) {}
                  count++;
                }
              }
            } else if (/^copied$/i.test(txt)) {
              for (let child = el.firstChild; child; child = child.nextSibling) {
                if (child.nodeType === 3 && child.nodeValue.trim().toLowerCase() === 'copied') {
                  const lead = (child.nodeValue.match(/^\s*/) || [''])[0];
                  const trail = (child.nodeValue.match(/\s*$/) || [''])[0];
                  child.nodeValue = lead + '已复制' + trail;
                  try { translatedNodeSet.add(child); } catch (_) {}
                  count++;
                }
              }
            } else if (/^copy\s+(code|link|path|all|text|file\s+path|full\s+path|citation)$/i.test(txt)) {
              const tr = translate(txt);
              if (tr && norm(txt) !== norm(tr)) {
                for (let child = el.firstChild; child; child = child.nextSibling) {
                  if (child.nodeType === 3) {
                    child.nodeValue = tr;
                    try { translatedNodeSet.add(child); } catch (_) {}
                    count++;
                  }
                }
              }
            }
          }
        }
      } catch (_) {}
      return count;
    };

    // 专门处理弹出菜单与上下文菜单项瞬时汉化 (Context Menus, Dropdown Menus & Submenus)
    const translateMenuContainers = (root) => {
      if (!root || !root.querySelectorAll) return 0;
      let count = 0;
      try {
        const menuSelectors = '[role="menu"], [role="menubar"], [role="menuitem"], [data-radix-menu-content], [data-radix-popper-content-wrapper], [class*="context-menu"], [class*="dropdown-menu"]';
        const menus = root.querySelectorAll(menuSelectors);
        for (let i = 0; i < menus.length; i++) {
          const item = menus[i];
          count += translateTextNodes(item);
          count += translateAttributes(item);
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
          textCount += translateFloatingCopyWidgets(currentRoot);
          thinkingCount += translateThinkingTriggers(currentRoot);
          thinkingCount += translateThinkingContainers(currentRoot);
          budgetCount += translateBudgetContainers(currentRoot);
          budgetCount += translateNotificationContainers(currentRoot);
          budgetCount += translateConsentContainers(currentRoot);
          budgetCount += translateHistoryNoticeContainers(currentRoot);
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

    // 全局用户交互感知窗口（点击/悬停/按压/选区变化/右键时开启 300ms 零延迟同步直出通道）
    let isUserInteracting = false;
    let interactExpiry = 0;
    const markInteraction = (e) => {
      isUserInteracting = true;
      interactExpiry = (typeof performance !== 'undefined' ? performance.now() : Date.now()) + 300;
      if (e && e.target && e.target.nodeType === 1) {
        translateFloatingCopyWidgets(e.target);
        translateMenuContainers(e.target);
      }
      // 针对选区变化与右键上下文弹窗，在微任务中对全局浮层执行即时极速扫描
      if (e && (e.type === 'mouseup' || e.type === 'contextmenu' || e.type === 'selectionchange' || e.type === 'pointerdown')) {
        setTimeout(() => {
          const body = document.body || document.documentElement;
          translateFloatingCopyWidgets(body);
          translateMenuContainers(body);
        }, 5);
      }
    };

    ['pointerdown', 'mousedown', 'mouseup', 'keydown', 'touchstart', 'touchend', 'pointerover', 'mouseover', 'contextmenu', 'selectionchange'].forEach((evtType) => {
      try {
        const target = (evtType === 'selectionchange') ? document : window;
        target.addEventListener(evtType, markInteraction, { capture: true, passive: true });
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
                syncCount += translateFloatingCopyWidgets(node);
                syncCount += translateMenuContainers(node);
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
                    syncCount += translateFloatingCopyWidgets(sr);
                    syncCount += translateMenuContainers(sr);
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


    // 挂载暴露启动动画全局控制开关
    try {
      window.__AGY_TOGGLE_SPLASH__ = (enable) => {
        try {
          if (enable) localStorage.removeItem('__AGY_DISABLE_SPLASH__');
          else localStorage.setItem('__AGY_DISABLE_SPLASH__', 'true');
          console.log('[AGY-SPLASH] 启动动画状态已更新为:', enable ? '开启' : '关闭');
        } catch (_) {}
      };
    } catch (_) {}

  } catch (e) {
    console.warn('[AGY-ZH] Runtime translation failed to bootstrap:', e);
  }
})();
