/* __AGZH_SKIN_RUNTIME__
 * Google Antigravity 桌面应用（AGY Hub）光学材质包渲染层运行时
 * - 输入：window.__AGZH_SKIN__ = { skin_id, base, colors, surfaces, css, pet } 或 null（关闭材质）
 * - 幂等：每次热更新先清理旧样式节点再原子挂载，与主进程 insertCSS 及幕布控制器无缝协同
 */
(function () {
  try {
    var STYLE_ID = 'agzh-skin-style';
    var PET_STYLE_ID = 'agzh-skin-pet-style';
    var SPRITE_ID = 'agzh-skin-pet-sprite';

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
          return true;
        }
        root.setAttribute('data-agzh-skin', S.skin_id || S.id || 'custom');
        root.setAttribute('data-agzh-base', S.base === 'light' ? 'light' : 'dark');

        // 渲染层同步挂载编译样式表，确保冷启动首帧与 IPC 热更新零延迟生效
        if (S.css) addStyle(STYLE_ID, S.css);

        var pet = S.pet || {};
        var css = '';
        if (pet.accent) css += ':root{--agzh-pet-accent:' + pet.accent + ';}\n';
        if (pet.css) css += pet.css + '\n';
        if (css) addStyle(PET_STYLE_ID, css);
        return true;
      }

      if (!applyOnce()) {
        var tries = 0;
        var timer = setInterval(function () {
          tries += 1;
          if (GEN !== window.__AGZH_SKIN_GEN__ || applyOnce() || tries > 40) clearInterval(timer);
        }, 250);
      }
    }

    function start() {
      applySkinPayload(window.__AGZH_SKIN__);
      try {
        var req = typeof require === 'function' ? require : null;
        var el = req ? req('electron') : null;
        if (el && el.ipcRenderer) {
          el.ipcRenderer
            .invoke('agzh:get-skin-runtime')
            .then(function (live) {
              if (live !== undefined) applySkinPayload(live);
            })
            .catch(function () {});
          if (!window.__AGZH_SKIN_IPC_BOUND__) {
            window.__AGZH_SKIN_IPC_BOUND__ = true;
            el.ipcRenderer.on('agzh:skin-updated', function (_ev, live) {
              applySkinPayload(live);
            });
          }
        }
      } catch (_) {}
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', start, { once: true });
    } else {
      start();
    }
  } catch (e) {
    try {
      console.log('[AGZH-SKIN] runtime error: ' + (e && e.message));
    } catch (_) {}
  }
})();
