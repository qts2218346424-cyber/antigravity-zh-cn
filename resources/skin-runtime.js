/* __AGZH_SKIN_RUNTIME__
 * Google Antigravity 桌面应用（AGY Hub）光学材质包渲染层运行时 v3.0
 * - 输入：window.__AGZH_SKIN__ = { skin_id, base, colors, surfaces, prism, css, pet } 或 null（关闭材质）
 * - 同步宿主深浅色模式类名（.dark / .dark-theme / .theme-dark / .theme-light），杜绝浅色宿主下黑底白块与黑字代码冲突
 * - 集成零侵入棱镜光学交互：近场指针边框高光（空闲 0fps）、长代码块手动折叠防跳动、会话轮次导轨与语义边缘余晖
 * - 停用材质时 100% 无损还原宿主原始主题类名、color-scheme 并卸载全部监听器与注入节点
 */
(function () {
  try {
    var STYLE_ID = 'agzh-skin-style';
    var PET_STYLE_ID = 'agzh-skin-pet-style';
    var SPRITE_ID = 'agzh-skin-pet-sprite';
    var AURA_BAR_ID = 'agzh-aura-bar';
    var RAIL_ID = 'agzh-rail-hud';
    var THEME_CLASSES = ['dark', 'light', 'dark-theme', 'theme-dark', 'theme-light'];
    var RIM_SELECTOR =
      '.surface-composer > .surface-composer-card, .artifact-card, .agy-card, .agy-callout, .agy-user-bubble, [data-testid*="user-message"]';
    var TURN_SELECTOR =
      '.agy-user-bubble, [data-testid*="user-message"], [data-message-author-role="user"]';

    var hostSnapshot = null;
    var classGuardObserver = null;
    var syncingClasses = false;
    var activeBaseMode = null;
    var symObserver = null;
    var symTimer = null;

    // 棱镜光学控制器状态
    var prismOptions = { facets: true, rimGlow: true, codeEnhance: true, ambientAura: true };
    var prismActive = false;
    var prismObserver = null;
    var prismScanTimer = null;
    var rimRaf = 0;
    var rimTarget = null;
    var pendingPointer = null;
    var rimListenersBound = false;
    var keyNavBound = false;
    var activeTurnIdx = -1;
    var codeLengthCache = typeof WeakMap === 'function' ? new WeakMap() : null;

    function rm(id) {
      var n = document.getElementById(id);
      if (n && n.parentNode) n.parentNode.removeChild(n);
    }

    function addStyle(id, css) {
      if (!css) return;
      var st = document.createElement('style');
      st.id = id;
      st.setAttribute('data-agzh', 'skin');
      st.textContent = css;
      (document.head || document.documentElement).appendChild(st);
    }

    function hasBrowserHole() {
      try {
        var body = document.body;
        if (!body) return false;
        if (body.getAttribute('data-has-browser-hole') === 'true') return true;
        return Boolean(document.querySelector('[data-browser-hole]:not([data-browser-hole="false"])'));
      } catch (_) {
        return false;
      }
    }

    function isEditableTarget(el) {
      if (!el) return false;
      var tag = (el.tagName || '').toUpperCase();
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
      if (el.isContentEditable) return true;
      return Boolean(el.closest && el.closest('[contenteditable="true"], [role="textbox"]'));
    }

    function getPrismOptions(S) {
      var p = (S && S.prism) || {};
      var surf = (S && S.surfaces) || {};
      return {
        facets: p.facets !== undefined ? p.facets !== false : surf.prism_facets !== false,
        rimGlow: p.rim_glow !== undefined ? p.rim_glow !== false : surf.rim_glow !== false,
        codeEnhance: p.code_enhance !== undefined ? p.code_enhance !== false : surf.code_enhance !== false,
        ambientAura: p.ambient_aura !== undefined ? p.ambient_aura !== false : surf.ambient_aura !== false,
      };
    }

    function tagSymbolElements() {
      try {
        var nodes = document.querySelectorAll(
          'aside .google-symbols, header .google-symbols, [data-testid] .google-symbols'
        );
        for (var i = 0; i < nodes.length; i++) {
          var el = nodes[i];
          var raw = (el.textContent || '').trim();
          if (raw && raw.length <= 36 && /^[a-z0-9_]+$/i.test(raw)) {
            var norm = raw.toLowerCase();
            if (el.getAttribute('data-agzh-sym') !== norm) {
              el.setAttribute('data-agzh-sym', norm);
            }
          }
        }
      } catch (_) {}
    }

    function clearSymbolTags() {
      try {
        if (symObserver) {
          symObserver.disconnect();
          symObserver = null;
        }
        if (symTimer) {
          clearTimeout(symTimer);
          symTimer = null;
        }
        var tagged = document.querySelectorAll('[data-agzh-sym]');
        for (var i = 0; i < tagged.length; i++) {
          tagged[i].removeAttribute('data-agzh-sym');
        }
      } catch (_) {}
    }

    function ensureSymbolObserver() {
      tagSymbolElements();
      if (symObserver || typeof MutationObserver === 'undefined') return;
      var target = document.body || document.documentElement;
      if (!target) return;
      symObserver = new MutationObserver(function () {
        if (symTimer) return;
        symTimer = setTimeout(function () {
          symTimer = null;
          tagSymbolElements();
        }, 180);
      });
      symObserver.observe(target, { childList: true, subtree: true });
    }

    function captureHostThemeSnapshot() {
      if (hostSnapshot) return;
      var root = document.documentElement;
      var body = document.body;
      if (!root || !body) return;
      var rootMap = {};
      var bodyMap = {};
      for (var i = 0; i < THEME_CLASSES.length; i++) {
        var cls = THEME_CLASSES[i];
        rootMap[cls] = root.classList.contains(cls);
        bodyMap[cls] = body.classList.contains(cls);
      }
      hostSnapshot = {
        rootClasses: rootMap,
        bodyClasses: bodyMap,
        colorScheme: root.style.colorScheme || '',
      };
    }

    function enforceBaseClasses(mode) {
      if (!mode) return;
      var root = document.documentElement;
      var body = document.body;
      if (!root) return;
      syncingClasses = true;
      try {
        var isDark = mode !== 'light';
        root.style.colorScheme = isDark ? 'dark' : 'light';
        if (root.classList.contains('dark') !== isDark) root.classList.toggle('dark', isDark);
        if (root.classList.contains('light') !== !isDark) root.classList.toggle('light', !isDark);
        if (body) {
          captureHostThemeSnapshot();
          if (body.classList.contains('dark') !== isDark) body.classList.toggle('dark', isDark);
          if (body.classList.contains('dark-theme') !== isDark) {
            body.classList.toggle('dark-theme', isDark);
          }
          if (body.classList.contains('theme-dark') !== isDark) {
            body.classList.toggle('theme-dark', isDark);
          }
          if (body.classList.contains('theme-light') !== !isDark) {
            body.classList.toggle('theme-light', !isDark);
          }
        }
      } finally {
        syncingClasses = false;
      }
    }

    function startClassGuard() {
      if (classGuardObserver || typeof MutationObserver === 'undefined') return;
      var root = document.documentElement;
      if (!root) return;
      classGuardObserver = new MutationObserver(function () {
        if (syncingClasses || !activeBaseMode) return;
        var body = document.body;
        var wantDark = activeBaseMode !== 'light';
        var drifted =
          root.classList.contains('dark') !== wantDark ||
          (body &&
            (body.classList.contains('dark') !== wantDark ||
              body.classList.contains('theme-dark') !== wantDark ||
              body.classList.contains('theme-light') !== !wantDark));
        if (drifted) {
          enforceBaseClasses(activeBaseMode);
        }
      });
      classGuardObserver.observe(root, { attributes: true, attributeFilter: ['class'] });
      if (document.body) {
        classGuardObserver.observe(document.body, {
          attributes: true,
          attributeFilter: ['class'],
        });
      }
    }

    function stopClassGuardAndRestore() {
      activeBaseMode = null;
      if (classGuardObserver) {
        try {
          classGuardObserver.disconnect();
        } catch (_) {}
        classGuardObserver = null;
      }
      if (!hostSnapshot) return;
      var root = document.documentElement;
      var body = document.body;
      syncingClasses = true;
      try {
        if (root) {
          for (var i = 0; i < THEME_CLASSES.length; i++) {
            var rc = THEME_CLASSES[i];
            root.classList.toggle(rc, !!hostSnapshot.rootClasses[rc]);
          }
          root.style.colorScheme = hostSnapshot.colorScheme;
        }
        if (body) {
          for (var j = 0; j < THEME_CLASSES.length; j++) {
            var bc = THEME_CLASSES[j];
            body.classList.toggle(bc, !!hostSnapshot.bodyClasses[bc]);
          }
        }
      } finally {
        syncingClasses = false;
        hostSnapshot = null;
      }
    }

    // === 1. 近场指针边框高光控制器（空闲 0fps） ===
    function clearRimState() {
      if (rimRaf) {
        try {
          cancelAnimationFrame(rimRaf);
        } catch (_) {}
        rimRaf = 0;
      }
      pendingPointer = null;
      if (rimTarget) {
        try {
          rimTarget.removeAttribute('data-agzh-rim-active');
          if (rimTarget.style && typeof rimTarget.style.removeProperty === 'function') {
            rimTarget.style.removeProperty('--agzh-mx');
            rimTarget.style.removeProperty('--agzh-my');
          }
        } catch (_) {}
        rimTarget = null;
      }
    }

    function flushRimPointer() {
      rimRaf = 0;
      var pt = pendingPointer;
      pendingPointer = null;
      if (!pt || !prismActive || !prismOptions.rimGlow || hasBrowserHole()) {
        clearRimState();
        return;
      }
      var el = pt.target && pt.target.closest ? pt.target.closest(RIM_SELECTOR) : null;
      if (!el || typeof el.getBoundingClientRect !== 'function') {
        clearRimState();
        return;
      }
      if (rimTarget && rimTarget !== el) {
        try {
          rimTarget.removeAttribute('data-agzh-rim-active');
          if (rimTarget.style && typeof rimTarget.style.removeProperty === 'function') {
            rimTarget.style.removeProperty('--agzh-mx');
            rimTarget.style.removeProperty('--agzh-my');
          }
        } catch (_) {}
      }
      rimTarget = el;
      var rect = el.getBoundingClientRect();
      var x = Math.round(pt.x - rect.left);
      var y = Math.round(pt.y - rect.top);
      el.setAttribute('data-agzh-rim-active', '1');
      if (el.style && typeof el.style.setProperty === 'function') {
        el.style.setProperty('--agzh-mx', x + 'px');
        el.style.setProperty('--agzh-my', y + 'px');
      }
    }

    function onPointerMoveRim(ev) {
      if (!prismActive || !prismOptions.rimGlow) return;
      pendingPointer = { target: ev.target, x: ev.clientX, y: ev.clientY };
      if (!rimRaf && typeof requestAnimationFrame === 'function') {
        rimRaf = requestAnimationFrame(flushRimPointer);
      } else if (!rimRaf) {
        flushRimPointer();
      }
    }

    function bindRimListeners() {
      if (rimListenersBound) return;
      rimListenersBound = true;
      document.addEventListener('pointermove', onPointerMoveRim, { passive: true });
      document.addEventListener('pointerleave', clearRimState, { passive: true });
      window.addEventListener('blur', clearRimState);
      document.addEventListener('visibilitychange', function () {
        if (document.hidden) clearRimState();
      });
    }

    function unbindRimListeners() {
      clearRimState();
      if (!rimListenersBound) return;
      rimListenersBound = false;
      document.removeEventListener('pointermove', onPointerMoveRim);
      document.removeEventListener('pointerleave', clearRimState);
      window.removeEventListener('blur', clearRimState);
      try {
        var leftover = document.querySelectorAll('[data-agzh-rim-active]');
        for (var i = 0; i < leftover.length; i++) {
          leftover[i].removeAttribute('data-agzh-rim-active');
          if (leftover[i].style && typeof leftover[i].style.removeProperty === 'function') {
            leftover[i].style.removeProperty('--agzh-mx');
            leftover[i].style.removeProperty('--agzh-my');
          }
        }
      } catch (_) {}
    }

    // === 2. 超长代码块手动折叠控制器（不自动截断、防滚动跳动） ===
    function findScrollableAncestor(el) {
      var cur = el ? el.parentElement : null;
      while (cur && cur !== document.body && cur !== document.documentElement) {
        try {
          var st = typeof getComputedStyle === 'function' ? getComputedStyle(cur) : null;
          if (st && /(auto|scroll)/.test(st.overflowY || '') && cur.scrollHeight > cur.clientHeight + 4) {
            return cur;
          }
        } catch (_) {}
        cur = cur.parentElement;
      }
      return document.scrollingElement || document.documentElement || document.body;
    }

    function enhanceLongCodeBlocks() {
      if (!prismActive || !prismOptions.codeEnhance || hasBrowserHole()) return;
      try {
        var pres = document.querySelectorAll('main pre, [data-main-content-body] pre, .agy-sheet pre');
        if (!pres || pres.length === 0) {
          pres = document.querySelectorAll('pre');
        }
        for (var i = 0; i < pres.length; i++) {
          var pre = pres[i];
          if (!pre || pre.getAttribute('data-agzh-code-ready') === '1') continue;
          var text = pre.textContent || '';
          var lines = text ? text.split('\n').length : 0;
          if (lines < 48) continue;

          // 若仍在流式增长则等待下一轮防抖扫描稳定后再注入按钮
          if (codeLengthCache) {
            var prevLen = codeLengthCache.get(pre);
            codeLengthCache.set(pre, text.length);
            if (prevLen !== undefined && prevLen !== text.length) {
              continue;
            }
          }

          pre.setAttribute('data-agzh-code-ready', '1');
          pre.setAttribute('data-agzh-code-lines', String(lines));

          var btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'agzh-code-fold-btn';
          btn.textContent = '收起代码 (' + lines + '行)';
          btn.setAttribute('aria-expanded', 'true');
          btn.addEventListener('click', (function (targetPre, toggleBtn, lineCount) {
            return function (ev) {
              if (ev && ev.stopPropagation) ev.stopPropagation();
              var beforeTop = toggleBtn.getBoundingClientRect ? toggleBtn.getBoundingClientRect().top : 0;
              var scroller = findScrollableAncestor(targetPre);
              var folded = targetPre.getAttribute('data-agzh-code-folded') === '1';
              if (folded) {
                targetPre.removeAttribute('data-agzh-code-folded');
                toggleBtn.textContent = '收起代码 (' + lineCount + '行)';
                toggleBtn.setAttribute('aria-expanded', 'true');
              } else {
                targetPre.setAttribute('data-agzh-code-folded', '1');
                toggleBtn.textContent = '展开代码 (' + lineCount + '行)';
                toggleBtn.setAttribute('aria-expanded', 'false');
              }
              if (scroller && toggleBtn.getBoundingClientRect) {
                var afterTop = toggleBtn.getBoundingClientRect().top;
                var delta = afterTop - beforeTop;
                if (Math.abs(delta) > 2 && typeof scroller.scrollTop === 'number') {
                  scroller.scrollTop += delta;
                }
              }
            };
          })(pre, btn, lines));
          pre.appendChild(btn);
        }
      } catch (_) {}
    }

    function clearCodeEnhancements() {
      try {
        var btns = document.querySelectorAll('.agzh-code-fold-btn');
        for (var i = 0; i < btns.length; i++) {
          if (btns[i].parentNode) btns[i].parentNode.removeChild(btns[i]);
        }
        var pres = document.querySelectorAll('[data-agzh-code-ready], [data-agzh-code-folded], [data-agzh-code-lines]');
        for (var j = 0; j < pres.length; j++) {
          pres[j].removeAttribute('data-agzh-code-ready');
          pres[j].removeAttribute('data-agzh-code-folded');
          pres[j].removeAttribute('data-agzh-code-lines');
        }
      } catch (_) {}
    }

    // === 3. 会话轮次导轨与 Alt+↑/↓ 快捷跳转 ===
    function collectUserTurns() {
      try {
        var nodes = document.querySelectorAll(TURN_SELECTOR);
        var out = [];
        for (var i = 0; i < nodes.length; i++) {
          var n = nodes[i];
          if (n && (n.textContent || '').trim()) out.push(n);
        }
        return out;
      } catch (_) {
        return [];
      }
    }

    function jumpToTurn(index) {
      var turns = collectUserTurns();
      if (!turns.length) return;
      var nextIdx = Math.max(0, Math.min(turns.length - 1, index));
      activeTurnIdx = nextIdx;
      var target = turns[nextIdx];
      if (target && typeof target.scrollIntoView === 'function') {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      syncTurnRail();
    }

    function syncTurnRail() {
      if (!prismActive || !prismOptions.codeEnhance || hasBrowserHole() || !document.body) {
        rm(RAIL_ID);
        return;
      }
      var turns = collectUserTurns();
      if (turns.length < 3) {
        rm(RAIL_ID);
        return;
      }
      if (activeTurnIdx < 0 || activeTurnIdx >= turns.length) {
        activeTurnIdx = turns.length - 1;
      }
      var rail = document.getElementById(RAIL_ID);
      if (!rail) {
        rail = document.createElement('div');
        rail.id = RAIL_ID;
        rail.className = 'agzh-rail-hud';
        rail.setAttribute('data-agzh', 'skin');

        var prevBtn = document.createElement('button');
        prevBtn.type = 'button';
        prevBtn.className = 'agzh-rail-btn';
        prevBtn.title = '上一轮提问 (Alt+↑)';
        prevBtn.textContent = '↑';
        prevBtn.addEventListener('click', function () {
          jumpToTurn(activeTurnIdx - 1);
        });

        var countEl = document.createElement('span');
        countEl.className = 'agzh-rail-count';

        var nextBtn = document.createElement('button');
        nextBtn.type = 'button';
        nextBtn.className = 'agzh-rail-btn';
        nextBtn.title = '下一轮提问 (Alt+↓)';
        nextBtn.textContent = '↓';
        nextBtn.addEventListener('click', function () {
          jumpToTurn(activeTurnIdx + 1);
        });

        var listEl = document.createElement('div');
        listEl.className = 'agzh-rail-popover';

        rail.appendChild(prevBtn);
        rail.appendChild(countEl);
        rail.appendChild(nextBtn);
        rail.appendChild(listEl);
        document.body.appendChild(rail);
      }

      var countNode = rail.querySelector('.agzh-rail-count');
      if (countNode) {
        countNode.textContent = (activeTurnIdx + 1) + '/' + turns.length;
      }
      var pop = rail.querySelector('.agzh-rail-popover');
      if (pop) {
        while (pop.firstChild) pop.removeChild(pop.firstChild);
        var start = Math.max(0, turns.length - 12);
        for (var i = start; i < turns.length; i++) {
          var item = document.createElement('button');
          item.type = 'button';
          item.className = 'agzh-rail-item' + (i === activeTurnIdx ? ' is-active' : '');
          var snippet = (turns[i].textContent || '').replace(/\s+/g, ' ').trim();
          if (snippet.length > 26) snippet = snippet.slice(0, 26) + '…';
          item.textContent = (i + 1) + '. ' + snippet;
          item.addEventListener('click', (function (idx) {
            return function () {
              jumpToTurn(idx);
            };
          })(i));
          pop.appendChild(item);
        }
      }
    }

    function onTurnKeyDown(ev) {
      if (!prismActive || !prismOptions.codeEnhance || !ev.altKey || ev.ctrlKey || ev.metaKey || ev.shiftKey) {
        return;
      }
      if (ev.key !== 'ArrowUp' && ev.key !== 'ArrowDown') return;
      if (isEditableTarget(document.activeElement)) return;
      var turns = collectUserTurns();
      if (!turns.length) return;
      ev.preventDefault();
      var baseIdx = activeTurnIdx >= 0 && activeTurnIdx < turns.length ? activeTurnIdx : turns.length - 1;
      jumpToTurn(ev.key === 'ArrowUp' ? baseIdx - 1 : baseIdx + 1);
    }

    function bindTurnNav() {
      if (keyNavBound) return;
      keyNavBound = true;
      document.addEventListener('keydown', onTurnKeyDown);
    }

    function unbindTurnNav() {
      if (keyNavBound) {
        keyNavBound = false;
        document.removeEventListener('keydown', onTurnKeyDown);
      }
      activeTurnIdx = -1;
      rm(RAIL_ID);
    }

    // === 4. 语义状态边缘余晖（静态/空闲 0fps） ===
    function syncAmbientAura() {
      var root = document.documentElement;
      if (!root) return;
      if (!prismActive || !prismOptions.ambientAura || hasBrowserHole()) {
        root.removeAttribute('data-agzh-aura');
        rm(AURA_BAR_ID);
        return;
      }
      if (document.body && !document.getElementById(AURA_BAR_ID)) {
        var bar = document.createElement('div');
        bar.id = AURA_BAR_ID;
        bar.setAttribute('aria-hidden', 'true');
        bar.setAttribute('data-agzh', 'skin');
        document.body.appendChild(bar);
      }
      var state = 'idle';
      try {
        if (document.querySelector('[data-testid*="ask-question"], [data-testid="ask-question-header-icon"]')) {
          state = 'attention';
        } else if (document.querySelector('[data-testid*="stop-generation"], [data-testid*="cancel-turn"], button[aria-label*="Stop"]')) {
          state = 'thinking';
        }
      } catch (_) {}
      root.setAttribute('data-agzh-aura', state);
    }

    function runPrismScan() {
      if (!prismActive) return;
      enhanceLongCodeBlocks();
      syncTurnRail();
      syncAmbientAura();
    }

    function ensurePrismControllers() {
      var root = document.documentElement;
      if (!root) return;
      prismActive = true;
      root.setAttribute('data-agzh-prism', '1');
      if (prismOptions.rimGlow) bindRimListeners();
      else unbindRimListeners();

      if (prismOptions.codeEnhance) bindTurnNav();
      else {
        unbindTurnNav();
        clearCodeEnhancements();
      }

      runPrismScan();

      if (!prismObserver && typeof MutationObserver !== 'undefined') {
        var target = document.body || root;
        prismObserver = new MutationObserver(function () {
          if (prismScanTimer) return;
          prismScanTimer = setTimeout(function () {
            prismScanTimer = null;
            runPrismScan();
          }, 260);
        });
        prismObserver.observe(target, { childList: true, subtree: true });
      }
    }

    function teardownPrismControllers() {
      prismActive = false;
      if (prismObserver) {
        try {
          prismObserver.disconnect();
        } catch (_) {}
        prismObserver = null;
      }
      if (prismScanTimer) {
        clearTimeout(prismScanTimer);
        prismScanTimer = null;
      }
      unbindRimListeners();
      unbindTurnNav();
      clearCodeEnhancements();
      rm(AURA_BAR_ID);
      if (document.documentElement) {
        document.documentElement.removeAttribute('data-agzh-prism');
        document.documentElement.removeAttribute('data-agzh-aura');
      }
    }

    function applySkinPayload(payload) {
      if (payload !== undefined) {
        window.__AGZH_SKIN__ = payload;
      }
      var S = typeof window !== 'undefined' ? window.__AGZH_SKIN__ || null : null;
      var GEN = (window.__AGZH_SKIN_GEN__ = (window.__AGZH_SKIN_GEN__ || 0) + 1);

      function applyOnce() {
        if (GEN !== window.__AGZH_SKIN_GEN__) return true;
        rm(STYLE_ID);
        rm(PET_STYLE_ID);
        rm(SPRITE_ID);
        var root = document.documentElement;
        if (!root) return false;
        if (!S || (!S.skin_id && !S.id && !S.css)) {
          root.removeAttribute('data-agzh-skin');
          root.removeAttribute('data-agzh-base');
          stopClassGuardAndRestore();
          clearSymbolTags();
          teardownPrismControllers();
          return true;
        }
        var baseMode = S.base === 'light' ? 'light' : 'dark';
        activeBaseMode = baseMode;
        prismOptions = getPrismOptions(S);
        root.setAttribute('data-agzh-skin', S.skin_id || S.id || 'custom');
        root.setAttribute('data-agzh-base', baseMode);
        enforceBaseClasses(baseMode);
        if (document.body) {
          startClassGuard();
          ensureSymbolObserver();
        }

        // 渲染层同步挂载编译样式表，确保冷启动首帧与 IPC 热更新零延迟生效
        if (S.css) addStyle(STYLE_ID, S.css);

        var pet = S.pet || {};
        var css = '';
        if (pet.accent) css += ':root{--agzh-pet-accent:' + pet.accent + ';}\n';
        if (pet.css) css += pet.css + '\n';
        if (css) addStyle(PET_STYLE_ID, css);

        if (document.body) {
          ensurePrismControllers();
        }
        return Boolean(document.body);
      }

      if (!applyOnce()) {
        var tries = 0;
        var timer = setInterval(function () {
          tries += 1;
          if (GEN !== window.__AGZH_SKIN_GEN__ || applyOnce() || tries > 40) clearInterval(timer);
        }, 120);
      }
    }

    function start() {
      var initialPayload = typeof window !== 'undefined' ? window.__AGZH_SKIN__ : undefined;
      try {
        var req = typeof require === 'function' ? require : null;
        var el = req ? req('electron') : null;
        if (el && el.ipcRenderer) {
          try {
            var syncLive = el.ipcRenderer.sendSync('agzh:get-skin-runtime-sync');
            if (syncLive !== undefined) {
              initialPayload = syncLive;
            }
          } catch (_) {
            el.ipcRenderer
              .invoke('agzh:get-skin-runtime')
              .then(function (live) {
                if (live !== undefined) applySkinPayload(live);
              })
              .catch(function () {});
          }
          if (!window.__AGZH_SKIN_IPC_BOUND__) {
            window.__AGZH_SKIN_IPC_BOUND__ = true;
            el.ipcRenderer.on('agzh:skin-updated', function (_ev, live) {
              applySkinPayload(live);
            });
          }
        }
      } catch (_) {}
      applySkinPayload(initialPayload);
    }

    if (document.readyState === 'loading') {
      start();
      document.addEventListener(
        'DOMContentLoaded',
        function () {
          if (activeBaseMode) {
            enforceBaseClasses(activeBaseMode);
            startClassGuard();
            ensureSymbolObserver();
            ensurePrismControllers();
          }
        },
        { once: true }
      );
    } else {
      start();
    }
  } catch (e) {
    try {
      console.log('[AGZH-SKIN] runtime error: ' + (e && e.message));
    } catch (_) {}
  }
})();
