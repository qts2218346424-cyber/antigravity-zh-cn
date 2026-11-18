/* __AGZH_SKIN_RUNTIME__
 * Google Antigravity 桌面应用（AGY Hub）光学材质包渲染层运行时 v2.2
 * - 输入：window.__AGZH_SKIN__ = { skin_id, base, colors, surfaces, css, pet } 或 null（关闭材质）
 * - 同步宿主深浅色模式类名（.dark / .dark-theme / .theme-dark / .theme-light），杜绝浅色宿主下黑底白块与黑字代码冲突
 * - 停用材质时 100% 无损还原宿主原始主题类名与 color-scheme
 */
(function () {
  try {
    var STYLE_ID = 'agzh-skin-style';
    var PET_STYLE_ID = 'agzh-skin-pet-style';
    var SPRITE_ID = 'agzh-skin-pet-sprite';
    var THEME_CLASSES = ['dark', 'light', 'dark-theme', 'theme-dark', 'theme-light'];
    var hostSnapshot = null;
    var classGuardObserver = null;
    var syncingClasses = false;
    var activeBaseMode = null;
    var symObserver = null;
    var symTimer = null;

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
          return true;
        }
        var baseMode = S.base === 'light' ? 'light' : 'dark';
        activeBaseMode = baseMode;
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
