/* __AGZH_SKIN_RUNTIME__
 * Antigravity 材质包渲染层运行时（桌宠外观 + 可选 CSS 注入）
 * - 输入：window.__AGZH_SKIN__ = { id, pet: {...}, css?, injectCss? } 或 null（表示关闭皮肤）
 * - 幂等：每次执行先移除上一次注入的节点再重新应用，可重复执行
 * - 不修改 nezuko-pet.js 的动作代码，只通过 CSS 覆盖与外层叠加节点改变外观
 */
(function () {
  try {
    var S = (typeof window !== 'undefined') ? (window.__AGZH_SKIN__ || null) : null;
    var STYLE_ID = 'agzh-skin-style';
    var PET_STYLE_ID = 'agzh-skin-pet-style';
    var SPRITE_ID = 'agzh-skin-pet-sprite';
    var LS_KEY = '__AGZH_SKIN_PET_APPLIED__';
    // 每次执行递增代号：切换皮肤时旧一轮的重试定时器发现代号变了就自行停止，
    // 避免旧定时器在新皮肤应用后又把旧皮肤的样式写回来。
    var GEN = (window.__AGZH_SKIN_GEN__ = (window.__AGZH_SKIN_GEN__ || 0) + 1);

    function rm(id) { var n = document.getElementById(id); if (n && n.parentNode) n.parentNode.removeChild(n); }
    function addStyle(id, css) {
      if (!css) return;
      var st = document.createElement('style');
      st.id = id;
      st.setAttribute('data-agzh', 'skin');
      st.textContent = css;
      (document.head || document.documentElement).appendChild(st);
    }

    function applyOnce() {
      if (GEN !== window.__AGZH_SKIN_GEN__) return true;  // 已被更新的一轮取代
      rm(STYLE_ID); rm(PET_STYLE_ID); rm(SPRITE_ID);
      var root = document.documentElement;
      if (!S) { root.removeAttribute('data-agzh-skin'); return true; }
      root.setAttribute('data-agzh-skin', S.id || 'custom');

      // 主窗口由 Electron 主进程 insertCSS 注入；独立桌宠窗口等场景由这里注入
      if (S.injectCss && S.css) addStyle(STYLE_ID, S.css);

      var pet = S.pet || {};
      var css = '';
      if (pet.accent) css += ':root{--agzh-pet-accent:' + pet.accent + ';}\n' +
        '#nezuko-main-card,#nezuko-action-capsule{border-color:' + pet.accent + ' !important;}\n' +
        '.nezuko-ctrl-btn{box-shadow:0 0 0 1px ' + pet.accent + ' inset;}\n';
      if (pet.filter) css += '#pet-character-viewport{filter:' + pet.filter + ' !important;}\n';
      if (pet.hidden) css += '#nezuko-pet-stage{display:none !important;}\n';
      if (pet.sprite) {
        css += '#pet-character-viewport > *:not(#' + SPRITE_ID + '){visibility:hidden !important;}\n' +
          '#' + SPRITE_ID + '{position:absolute;inset:0;pointer-events:none;visibility:visible !important;' +
          'background:url("' + pet.sprite + '") center bottom / contain no-repeat;}\n';
      }
      if (pet.css) css += pet.css + '\n';
      addStyle(PET_STYLE_ID, css);

      var viewport = document.getElementById('pet-character-viewport');
      if (pet.sprite && viewport) {
        var d = document.createElement('div');
        d.id = SPRITE_ID;
        viewport.appendChild(d);
      }

      // 角色与缩放只在切换到该材质包时应用一次，之后尊重用户在桌宠面板里的手动调整
      var stamp = (S.id || '') + '|' + (pet.character || '') + '|' + (pet.scale || '');
      var applied = '';
      try { applied = localStorage.getItem(LS_KEY) || ''; } catch (_) {}
      var stage = document.getElementById('nezuko-pet-stage');
      var pending = stamp !== applied && !!(pet.character || pet.scale);
      if (stamp !== applied && stage) {
        if (pet.character === 'nezuko' || pet.character === 'prince') {
          var btn = document.getElementById('btn-select-' + pet.character);
          if (btn) { try { btn.click(); } catch (_) {} }
        }
        if (typeof pet.scale === 'number' && typeof window.__AGY_SET_PET_SCALE__ === 'function') {
          try { window.__AGY_SET_PET_SCALE__(pet.scale); } catch (_) {}
        }
        try { localStorage.setItem(LS_KEY, stamp); } catch (_) {}
      }
      // 桌宠节点尚未渲染时返回 false，等待重试（自定义形象图或待应用的角色/缩放）
      return !((pet.sprite && !viewport) || (pending && !stage));
    }

    function start() {
      if (applyOnce()) return;
      var tries = 0;
      var timer = setInterval(function () {
        tries += 1;
        if (GEN !== window.__AGZH_SKIN_GEN__ || applyOnce() || tries > 60) clearInterval(timer);
      }, 500);
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', start, { once: true });
    } else {
      start();
    }
  } catch (e) {
    try { console.log('[AGZH-SKIN] runtime error: ' + (e && e.message)); } catch (_) {}
  }
})();
