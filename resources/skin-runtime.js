/* __AGZH_SKIN_RUNTIME__
 * Google Antigravity 桌面应用（AGY Hub）光学材质包渲染层全动态引擎 v4.0
 * - 输入：window.__AGZH_SKIN__ = { skin_id, base, colors, surfaces, prism, css, pet } 或 null（关闭材质）
 * - 支持热重载卸载钩子 window.__AGZH_SKIN_DISPOSE__，配合主进程双热重载架构零重启升级 JS 引擎
 * - 7 大真动态光学引擎（空闲/失焦/浏览器透视孔自动 0fps 休眠）：
 *   1. PrismRimCanvasEngine：全屏 DPR Canvas 近场棱镜激光折光边框
 *   2. HorizonRippleEngine：欢迎页字符波纹矩阵 + 物理水波涟漪 + 对话地平线极光
 *   3. InkStreamEngine：CSS.highlights 五级水墨流式淡入（零 DOM 侵入）
 *   4. SmoothCaretAndComposerEngine：旋转棱镜流光输入舱 + 阻尼跟随光标
 *   5. ContextVialWidget：512K 液态波动上下文试管 + 悬停详情 + 一键切换预设
 *   6. CrystalAuraEngine：思考/待决策/完成三态切工水晶光束
 *   7. LiveCharmEngine：活体伴读角色呼吸律动、鼠标注视与点击 Q 弹星芒彩蛋
 */
(function () {
  try {
    if (typeof window.__AGZH_SKIN_DISPOSE__ === 'function') {
      try {
        window.__AGZH_SKIN_DISPOSE__();
      } catch (_) {}
    }

    var STYLE_ID = 'agzh-skin-style';
    var PET_STYLE_ID = 'agzh-skin-pet-style';
    var SPRITE_ID = 'agzh-skin-pet-sprite';
    var AURA_BAR_ID = 'agzh-aura-bar';
    var RAIL_ID = 'agzh-rail-hud';
    var RIM_CANVAS_ID = 'agzh-rim-canvas';
    var HORIZON_CANVAS_ID = 'agzh-horizon-canvas';
    var CARET_ID = 'agzh-smooth-caret';
    var VIAL_ID = 'agzh-context-vial';
    var CHARM_ID = 'agzh-live-charm';

    var THEME_CLASSES = ['dark', 'light', 'dark-theme', 'theme-dark', 'theme-light'];
    var RIM_SELECTOR =
      '.surface-composer > .surface-composer-card, .artifact-card, .agy-card, .agy-callout, .agy-user-bubble, [data-testid*="user-message"], [data-testid="new-conversation-button"], main pre';
    var TURN_SELECTOR =
      '.agy-user-bubble, [data-testid*="user-message"], [data-message-author-role="user"]';

    var hostSnapshot = null;
    var classGuardObserver = null;
    var syncingClasses = false;
    var activeBaseMode = null;
    var symObserver = null;
    var symTimer = null;

    var prismOptions = {
      facets: true,
      rimGlow: true,
      codeEnhance: true,
      ambientAura: true,
      motionPreset: 'full',
      horizonRipple: true,
      inkStream: true,
      contextVial: true,
      liveCharm: true,
    };
    var runtimePresetOverride = null;
    var prismActive = false;
    var prismObserver = null;
    var prismScanTimer = null;

    // CSS 坐标高光 + Canvas 激光边框状态
    var rimRaf = 0;
    var rimIdleTimer = null;
    var rimTarget = null;
    var pendingPointer = null;
    var lastPointer = { x: -9999, y: -9999, active: false };
    var rimCanvasAlpha = 0;
    var rimListenersBound = false;

    // 字符波纹矩阵状态
    var horizonRaf = 0;
    var horizonLastDraw = 0;
    var horizonIdleTimer = null;
    var horizonPhase = 0;
    var horizonRipples = [];
    var horizonBound = false;

    // 水墨流式淡入状态
    var inkObserver = null;
    var inkRaf = 0;
    var inkClearTimer = null;
    var inkQueue = [];

    // 丝滑光标与输入舱状态
    var caretBound = false;
    var typingTimer = null;

    // 轮次导轨状态
    var keyNavBound = false;
    var activeTurnIdx = -1;
    var codeLengthCache = typeof WeakMap === 'function' ? new WeakMap() : null;

    // 语义余晖状态
    var prevAuraState = 'idle';
    var doneAuraTimer = null;

    // 活体伴读交互状态
    var charmBound = false;
    var charmElRef = null;

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

    function isReducedMotion() {
      try {
        if (prismOptions.motionPreset === 'silent') return true;
        if (typeof window.matchMedia === 'function') {
          return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        }
      } catch (_) {}
      return false;
    }

    function isEditableTarget(el) {
      if (!el) return false;
      var tag = (el.tagName || '').toUpperCase();
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
      if (el.isContentEditable) return true;
      return Boolean(el.closest && el.closest('[contenteditable="true"], [role="textbox"]'));
    }

    function getAccentColor() {
      try {
        var S = window.__AGZH_SKIN__;
        if (S && S.colors && S.colors.accent) return S.colors.accent;
        if (typeof getComputedStyle === 'function' && document.documentElement) {
          var v = getComputedStyle(document.documentElement).getPropertyValue('--agzh-accent').trim();
          if (v) return v;
        }
      } catch (_) {}
      return '#38bdf8';
    }

    function parseHexOrRgb(color) {
      var fallback = { r: 56, g: 189, b: 248 };
      if (!color || typeof color !== 'string') return fallback;
      var c = color.trim();
      var mHex = /^#([0-9a-f]{6})$/i.exec(c);
      if (mHex) {
        return {
          r: parseInt(mHex[1].slice(0, 2), 16),
          g: parseInt(mHex[1].slice(2, 4), 16),
          b: parseInt(mHex[1].slice(4, 6), 16),
        };
      }
      var mRgb = /^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i.exec(c);
      if (mRgb) {
        return { r: Number(mRgb[1]), g: Number(mRgb[2]), b: Number(mRgb[3]) };
      }
      return fallback;
    }

    function getPrismOptions(S) {
      var p = (S && S.prism) || {};
      var surf = (S && S.surfaces) || {};
      var preset = runtimePresetOverride || p.motion_preset || surf.motion_preset || 'full';
      var base = {
        facets: p.facets !== undefined ? p.facets !== false : surf.prism_facets !== false,
        rimGlow: p.rim_glow !== undefined ? p.rim_glow !== false : surf.rim_glow !== false,
        codeEnhance: p.code_enhance !== undefined ? p.code_enhance !== false : surf.code_enhance !== false,
        ambientAura: p.ambient_aura !== undefined ? p.ambient_aura !== false : surf.ambient_aura !== false,
        motionPreset: preset,
        horizonRipple: p.horizon_ripple !== undefined ? p.horizon_ripple !== false : surf.horizon_ripple !== false,
        inkStream: p.ink_stream !== undefined ? p.ink_stream !== false : surf.ink_stream !== false,
        contextVial: p.context_vial !== undefined ? p.context_vial !== false : surf.context_vial !== false,
        liveCharm: p.live_charm !== undefined ? p.live_charm !== false : surf.live_charm !== false,
      };
      if (preset === 'silent') {
        base.rimGlow = false;
        base.horizonRipple = false;
        base.inkStream = false;
        base.liveCharm = false;
      } else if (preset === 'focus') {
        base.horizonRipple = false;
        base.liveCharm = false;
      }
      return base;
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

    // === 引擎 1：PrismRimCanvasEngine（近场棱镜激光折光边框 + CSS 坐标高光） ===
    function ensureRimCanvas() {
      if (!document.body || isReducedMotion() || !prismOptions.rimGlow || hasBrowserHole()) {
        rm(RIM_CANVAS_ID);
        return null;
      }
      var cv = document.getElementById(RIM_CANVAS_ID);
      if (!cv) {
        cv = document.createElement('canvas');
        cv.id = RIM_CANVAS_ID;
        cv.setAttribute('aria-hidden', 'true');
        cv.setAttribute('data-agzh', 'skin');
        document.body.appendChild(cv);
      }
      return cv;
    }

    function drawRoundedRectPath(ctx, x, y, w, h, r) {
      var rad = Math.max(2, Math.min(r, w / 2, h / 2));
      ctx.beginPath();
      ctx.moveTo(x + rad, y);
      ctx.lineTo(x + w - rad, y);
      ctx.quadraticCurveTo(x + w, y, x + w, y + rad);
      ctx.lineTo(x + w, y + h - rad);
      ctx.quadraticCurveTo(x + w, y + h, x + w - rad, y + h);
      ctx.lineTo(x + rad, y + h);
      ctx.quadraticCurveTo(x, y + h, x, y + h - rad);
      ctx.lineTo(x, y + rad);
      ctx.quadraticCurveTo(x, y, x + rad, y);
      ctx.closePath();
    }

    function clearRimState() {
      if (rimRaf) {
        try {
          cancelAnimationFrame(rimRaf);
        } catch (_) {}
        rimRaf = 0;
      }
      if (rimIdleTimer) {
        clearTimeout(rimIdleTimer);
        rimIdleTimer = null;
      }
      pendingPointer = null;
      lastPointer.active = false;
      rimCanvasAlpha = 0;
      var cv = document.getElementById(RIM_CANVAS_ID);
      if (cv && typeof cv.getContext === 'function') {
        try {
          var c2d = cv.getContext('2d');
          if (c2d) c2d.clearRect(0, 0, cv.width, cv.height);
        } catch (_) {}
      }
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

    function renderRimCanvasFrame() {
      rimRaf = 0;
      if (!prismActive || !prismOptions.rimGlow || isReducedMotion() || hasBrowserHole() || document.hidden) {
        clearRimState();
        return;
      }
      if (pendingPointer) {
        var pt = pendingPointer;
        pendingPointer = null;
        lastPointer.x = pt.x;
        lastPointer.y = pt.y;
        lastPointer.active = true;
        rimCanvasAlpha = 1;

        var el = pt.target && pt.target.closest ? pt.target.closest(RIM_SELECTOR) : null;
        if (rimTarget && rimTarget !== el) {
          try {
            rimTarget.removeAttribute('data-agzh-rim-active');
            if (rimTarget.style && typeof rimTarget.style.removeProperty === 'function') {
              rimTarget.style.removeProperty('--agzh-mx');
              rimTarget.style.removeProperty('--agzh-my');
            }
          } catch (_) {}
          rimTarget = null;
        }
        if (el && typeof el.getBoundingClientRect === 'function') {
          rimTarget = el;
          var r = el.getBoundingClientRect();
          el.setAttribute('data-agzh-rim-active', '1');
          if (el.style && typeof el.style.setProperty === 'function') {
            el.style.setProperty('--agzh-mx', Math.round(pt.x - r.left) + 'px');
            el.style.setProperty('--agzh-my', Math.round(pt.y - r.top) + 'px');
          }
        }
      }

      var cv = ensureRimCanvas();
      if (!cv || typeof cv.getContext !== 'function') return;
      var dpr = Math.min(2, window.devicePixelRatio || 1);
      var vw = window.innerWidth || 0;
      var vh = window.innerHeight || 0;
      if (vw <= 0 || vh <= 0) return;
      if (cv.width !== Math.round(vw * dpr) || cv.height !== Math.round(vh * dpr)) {
        cv.width = Math.round(vw * dpr);
        cv.height = Math.round(vh * dpr);
      }
      var ctx = cv.getContext('2d');
      if (!ctx) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, vw, vh);

      if (!lastPointer.active || rimCanvasAlpha <= 0.02) return;

      var rgb = parseHexOrRgb(getAccentColor());
      var nodes = document.querySelectorAll(RIM_SELECTOR);
      var maxDist = 230;
      for (var i = 0; i < nodes.length && i < 64; i++) {
        var card = nodes[i];
        if (!card || typeof card.getBoundingClientRect !== 'function') continue;
        var rect = card.getBoundingClientRect();
        if (rect.width < 24 || rect.height < 18 || rect.bottom < 0 || rect.top > vh) continue;

        var cx = Math.max(rect.left, Math.min(lastPointer.x, rect.right));
        var cy = Math.max(rect.top, Math.min(lastPointer.y, rect.bottom));
        var dist = Math.hypot(lastPointer.x - cx, lastPointer.y - cy);
        if (dist > maxDist) continue;

        var intensity = (1 - dist / maxDist) * rimCanvasAlpha;
        var grad = ctx.createRadialGradient(
          lastPointer.x,
          lastPointer.y,
          4,
          lastPointer.x,
          lastPointer.y,
          210
        );
        grad.addColorStop(0, 'rgba(' + rgb.r + ',' + rgb.g + ',' + rgb.b + ',' + (0.85 * intensity).toFixed(3) + ')');
        grad.addColorStop(0.45, 'rgba(' + rgb.r + ',' + rgb.g + ',' + rgb.b + ',' + (0.28 * intensity).toFixed(3) + ')');
        grad.addColorStop(1, 'rgba(' + rgb.r + ',' + rgb.g + ',' + rgb.b + ',0)');

        var rad = 12;
        try {
          var cs = typeof getComputedStyle === 'function' ? getComputedStyle(card) : null;
          if (cs && cs.borderRadius) {
            var parsedR = parseFloat(cs.borderRadius);
            if (!isNaN(parsedR)) rad = parsedR;
          }
        } catch (_) {}

        ctx.save();
        drawRoundedRectPath(ctx, rect.left + 0.5, rect.top + 0.5, rect.width - 1, rect.height - 1, rad);
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.5;
        ctx.shadowColor = 'rgba(' + rgb.r + ',' + rgb.g + ',' + rgb.b + ',' + (0.45 * intensity).toFixed(3) + ')';
        ctx.shadowBlur = 10 * intensity;
        ctx.stroke();
        ctx.restore();
      }
    }

    function onPointerMoveRim(ev) {
      if (!prismActive || !prismOptions.rimGlow || isReducedMotion()) return;
      pendingPointer = { target: ev.target, x: ev.clientX, y: ev.clientY };
      if (!rimRaf && typeof requestAnimationFrame === 'function') {
        rimRaf = requestAnimationFrame(renderRimCanvasFrame);
      } else if (!rimRaf) {
        renderRimCanvasFrame();
      }
      if (rimIdleTimer) clearTimeout(rimIdleTimer);
      rimIdleTimer = setTimeout(function () {
        rimCanvasAlpha = 0;
        var cv = document.getElementById(RIM_CANVAS_ID);
        if (cv && typeof cv.getContext === 'function') {
          try {
            var c2d = cv.getContext('2d');
            if (c2d) c2d.clearRect(0, 0, cv.width, cv.height);
          } catch (_) {}
        }
      }, 320);
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
      rm(RIM_CANVAS_ID);
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

    // === 引擎 2：HorizonRippleEngine（首页字符波纹矩阵 + 物理水波涟漪） ===
    function spawnHorizonRipple(x, y) {
      if (!prismActive || !prismOptions.horizonRipple || isReducedMotion()) return;
      horizonRipples.push({ x: x, y: y, r: 6, alpha: 0.95 });
      if (horizonRipples.length > 8) horizonRipples.shift();
      kickHorizonLoop();
    }

    function onHorizonPointer(ev) {
      if (ev.type === 'click') {
        spawnHorizonRipple(ev.clientX, ev.clientY);
      } else if (Math.random() < 0.16) {
        spawnHorizonRipple(ev.clientX, ev.clientY);
      }
    }

    function drawHorizonFrame(ts) {
      horizonRaf = 0;
      if (!prismActive || !prismOptions.horizonRipple || isReducedMotion() || hasBrowserHole() || document.hidden) {
        rm(HORIZON_CANVAS_ID);
        return;
      }
      if (ts && ts - horizonLastDraw < 32) {
        horizonRaf = requestAnimationFrame(drawHorizonFrame);
        return;
      }
      horizonLastDraw = ts || Date.now();

      var cv = document.getElementById(HORIZON_CANVAS_ID);
      if (!cv && document.body) {
        cv = document.createElement('canvas');
        cv.id = HORIZON_CANVAS_ID;
        cv.setAttribute('aria-hidden', 'true');
        cv.setAttribute('data-agzh', 'skin');
        document.body.appendChild(cv);
      }
      if (!cv || typeof cv.getContext !== 'function') return;

      var dpr = Math.min(1.5, window.devicePixelRatio || 1);
      var vw = window.innerWidth || 0;
      var vh = window.innerHeight || 0;
      if (vw <= 0 || vh <= 0) return;
      if (cv.width !== Math.round(vw * dpr) || cv.height !== Math.round(vh * dpr)) {
        cv.width = Math.round(vw * dpr);
        cv.height = Math.round(vh * dpr);
      }
      var ctx = cv.getContext('2d');
      if (!ctx) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, vw, vh);

      var rgb = parseHexOrRgb(getAccentColor());
      var turns = collectUserTurns();
      var isHome = turns.length === 0;
      horizonPhase += 0.045;

      // 首页欢迎空画布呈现柔和交互字符矩阵，多轮对话中收敛为顶部/底沿极光地平线
      var glyphs = ['·', '∘', '✦', '◇', '⊹'];
      var stepX = 36;
      var stepY = 34;
      var startX = Math.min(280, Math.round(vw * 0.2));
      ctx.font = '12px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      for (var y = 64; y < vh - 84; y += stepY) {
        if (!isHome && y > 136 && y < vh - 150) continue;
        for (var x = startX; x < vw - 36; x += stepX) {
          var wave = Math.sin(x * 0.014 + y * 0.012 + horizonPhase) * 0.5 + 0.5;
          var boost = 0;
          for (var rIdx = 0; rIdx < horizonRipples.length; rIdx++) {
            var rp = horizonRipples[rIdx];
            var d = Math.abs(Math.hypot(x - rp.x, y - rp.y) - rp.r);
            if (d < 46) {
              boost = Math.max(boost, (1 - d / 46) * rp.alpha);
            }
          }
          var baseAlpha = isHome ? 0.05 + wave * 0.08 : 0.03 + wave * 0.04;
          var alpha = Math.min(0.72, baseAlpha + boost * 0.6);
          if (alpha < 0.035) continue;
          var gIdx = Math.min(glyphs.length - 1, Math.floor((wave + boost) * 2.6));
          ctx.fillStyle = 'rgba(' + rgb.r + ',' + rgb.g + ',' + rgb.b + ',' + alpha.toFixed(3) + ')';
          ctx.fillText(glyphs[gIdx], x, y);
        }
      }

      for (var k = horizonRipples.length - 1; k >= 0; k--) {
        horizonRipples[k].r += 7.5;
        horizonRipples[k].alpha *= 0.94;
        if (horizonRipples[k].alpha < 0.04) {
          horizonRipples.splice(k, 1);
        }
      }

      if (horizonRipples.length > 0 || isHome) {
        horizonRaf = requestAnimationFrame(drawHorizonFrame);
      }
    }

    function kickHorizonLoop() {
      if (!prismActive || !prismOptions.horizonRipple || isReducedMotion() || hasBrowserHole()) return;
      if (!horizonRaf && typeof requestAnimationFrame === 'function') {
        horizonRaf = requestAnimationFrame(drawHorizonFrame);
      }
      if (horizonIdleTimer) clearTimeout(horizonIdleTimer);
      horizonIdleTimer = setTimeout(function () {
        if (horizonRaf && horizonRipples.length === 0) {
          try {
            cancelAnimationFrame(horizonRaf);
          } catch (_) {}
          horizonRaf = 0;
        }
      }, 2800);
    }

    function bindHorizonEngine() {
      if (!prismOptions.horizonRipple || isReducedMotion()) {
        unbindHorizonEngine();
        return;
      }
      if (!horizonBound) {
        horizonBound = true;
        document.addEventListener('click', onHorizonPointer, { passive: true });
        document.addEventListener('pointermove', onHorizonPointer, { passive: true });
      }
      kickHorizonLoop();
    }

    function unbindHorizonEngine() {
      if (horizonRaf) {
        try {
          cancelAnimationFrame(horizonRaf);
        } catch (_) {}
        horizonRaf = 0;
      }
      if (horizonIdleTimer) {
        clearTimeout(horizonIdleTimer);
        horizonIdleTimer = null;
      }
      horizonRipples = [];
      if (horizonBound) {
        horizonBound = false;
        document.removeEventListener('click', onHorizonPointer);
        document.removeEventListener('pointermove', onHorizonPointer);
      }
      rm(HORIZON_CANVAS_ID);
    }

    // === 引擎 3：InkStreamEngine（CSS.highlights 五级水墨流式淡入） ===
    function clearInkHighlights() {
      inkQueue = [];
      if (inkRaf) {
        try {
          cancelAnimationFrame(inkRaf);
        } catch (_) {}
        inkRaf = 0;
      }
      if (inkClearTimer) {
        clearTimeout(inkClearTimer);
        inkClearTimer = null;
      }
      try {
        if (typeof CSS !== 'undefined' && CSS.highlights) {
          for (var i = 0; i < 5; i++) {
            CSS.highlights.delete('agzh-ink-' + i);
          }
        }
      } catch (_) {}
    }

    function tickInkHighlights() {
      inkRaf = 0;
      if (!prismActive || !prismOptions.inkStream || isReducedMotion() || typeof CSS === 'undefined' || !CSS.highlights) {
        clearInkHighlights();
        return;
      }
      var now = Date.now();
      var buckets = [[], [], [], [], []];
      var nextQueue = [];
      for (var i = 0; i < inkQueue.length; i++) {
        var entry = inkQueue[i];
        var age = now - entry.t;
        if (age < 280 && entry.range) {
          var stage = Math.min(4, Math.max(0, Math.floor((age / 280) * 5)));
          buckets[stage].push(entry.range);
          nextQueue.push(entry);
        }
      }
      inkQueue = nextQueue;
      try {
        for (var s = 0; s < 5; s++) {
          if (buckets[s].length > 0 && typeof Highlight === 'function') {
            var hl = new Highlight();
            for (var bIdx = 0; bIdx < buckets[s].length; bIdx++) {
              if (typeof hl.add === 'function') hl.add(buckets[s][bIdx]);
            }
            CSS.highlights.set('agzh-ink-' + s, hl);
          } else {
            CSS.highlights.delete('agzh-ink-' + s);
          }
        }
      } catch (_) {
        clearInkHighlights();
        return;
      }
      if (inkQueue.length > 0 && typeof requestAnimationFrame === 'function') {
        inkRaf = requestAnimationFrame(tickInkHighlights);
      }
    }

    function bindInkStreamEngine() {
      if (!prismOptions.inkStream || isReducedMotion() || typeof MutationObserver === 'undefined' || typeof CSS === 'undefined' || !CSS.highlights || typeof Highlight !== 'function') {
        unbindInkStreamEngine();
        return;
      }
      if (inkObserver) return;
      var root = document.querySelector('main, [data-main-content-body]') || document.body;
      if (!root) return;
      inkObserver = new MutationObserver(function (mutations) {
        if (!prismActive || !prismOptions.inkStream || hasBrowserHole()) return;
        var now = Date.now();
        for (var i = 0; i < mutations.length; i++) {
          var m = mutations[i];
          if (m.type === 'characterData' && m.target && m.target.nodeType === 3) {
            var len = (m.target.nodeValue || '').length;
            if (len > 0 && typeof document.createRange === 'function') {
              try {
                var r = document.createRange();
                r.setStart(m.target, Math.max(0, len - 18));
                r.setEnd(m.target, len);
                inkQueue.push({ range: r, t: now });
              } catch (_) {}
            }
          }
        }
        if (inkQueue.length > 40) inkQueue = inkQueue.slice(-40);
        if (inkQueue.length > 0 && !inkRaf && typeof requestAnimationFrame === 'function') {
          inkRaf = requestAnimationFrame(tickInkHighlights);
        }
      });
      inkObserver.observe(root, { characterData: true, subtree: true });
    }

    function unbindInkStreamEngine() {
      if (inkObserver) {
        try {
          inkObserver.disconnect();
        } catch (_) {}
        inkObserver = null;
      }
      clearInkHighlights();
    }

    // === 引擎 4：SmoothCaretAndComposerEngine（输入舱脉冲 + 阻尼光标） ===
    function syncCaretOrTyping() {
      if (!prismActive || isReducedMotion() || hasBrowserHole()) return;
      var active = document.activeElement;
      var card = active && active.closest ? active.closest('.surface-composer > .surface-composer-card') : null;
      if (card) {
        card.setAttribute('data-agzh-typing', '1');
        if (typingTimer) clearTimeout(typingTimer);
        typingTimer = setTimeout(function () {
          try {
            card.removeAttribute('data-agzh-typing');
          } catch (_) {}
        }, 1200);
      }
      if (prismOptions.motionPreset === 'silent') {
        rm(CARET_ID);
        return;
      }
      try {
        if (active && isEditableTarget(active) && typeof window.getSelection === 'function') {
          var sel = window.getSelection();
          if (sel && sel.rangeCount > 0) {
            var range = sel.getRangeAt(0).cloneRange();
            range.collapse(true);
            var rect = range.getBoundingClientRect ? range.getBoundingClientRect() : null;
            if (rect && rect.height > 4 && rect.width >= 0 && document.body) {
              var caret = document.getElementById(CARET_ID);
              if (!caret) {
                caret = document.createElement('div');
                caret.id = CARET_ID;
                caret.setAttribute('aria-hidden', 'true');
                caret.setAttribute('data-agzh', 'skin');
                document.body.appendChild(caret);
              }
              caret.style.height = Math.round(rect.height) + 'px';
              caret.style.transform = 'translate3d(' + Math.round(rect.left) + 'px,' + Math.round(rect.top) + 'px,0)';
              caret.style.opacity = '0.9';
              return;
            }
          }
        }
      } catch (_) {}
      var existing = document.getElementById(CARET_ID);
      if (existing) existing.style.opacity = '0';
    }

    function bindCaretEngine() {
      if (caretBound) return;
      caretBound = true;
      document.addEventListener('input', syncCaretOrTyping, { passive: true });
      document.addEventListener('selectionchange', syncCaretOrTyping, { passive: true });
    }

    function unbindCaretEngine() {
      if (typingTimer) {
        clearTimeout(typingTimer);
        typingTimer = null;
      }
      if (caretBound) {
        caretBound = false;
        document.removeEventListener('input', syncCaretOrTyping);
        document.removeEventListener('selectionchange', syncCaretOrTyping);
      }
      rm(CARET_ID);
      try {
        var nodes = document.querySelectorAll('[data-agzh-typing]');
        for (var i = 0; i < nodes.length; i++) nodes[i].removeAttribute('data-agzh-typing');
      } catch (_) {}
    }

    // === 引擎 5：ContextVialWidget（512K 液态波动上下文试管） ===
    function syncContextVial() {
      if (!prismActive || !prismOptions.contextVial || hasBrowserHole() || !document.body) {
        rm(VIAL_ID);
        return;
      }
      var turns = collectUserTurns();
      var bodyTextLen = 0;
      try {
        var mainNode = document.querySelector('main, [data-main-content-body]');
        bodyTextLen = mainNode ? (mainNode.textContent || '').length : 0;
      } catch (_) {}
      var estK = Math.min(512, Math.max(4, Math.round(bodyTextLen / 900 + turns.length * 6)));
      var pct = Math.min(100, Math.max(8, Math.round((estK / 512) * 100)));
      var liquidColor = pct >= 85 ? '#fb7185' : pct >= 60 ? '#f59e0b' : getAccentColor();

      var vial = document.getElementById(VIAL_ID);
      if (!vial) {
        vial = document.createElement('button');
        vial.id = VIAL_ID;
        vial.type = 'button';
        vial.setAttribute('data-agzh', 'skin');
        vial.title = '点击切换光效模式（完整 / 专注 / 静默）';
        vial.addEventListener('click', function () {
          var order = ['full', 'focus', 'silent'];
          var cur = prismOptions.motionPreset || 'full';
          var next = order[(order.indexOf(cur) + 1) % order.length];
          runtimePresetOverride = next;
          applySkinPayload(window.__AGZH_SKIN__);
        });
        document.body.appendChild(vial);
      }

      var waveY = Math.round(22 - (pct / 100) * 18);
      var presetLabel =
        prismOptions.motionPreset === 'silent'
          ? '静默省电'
          : prismOptions.motionPreset === 'focus'
            ? '专注编码'
            : '完整光效';

      while (vial.firstChild) vial.removeChild(vial.firstChild);

      var tube = document.createElement('span');
      tube.className = 'agzh-vial-tube';
      tube.innerHTML =
        '<svg viewBox="0 0 14 22" width="14" height="22" aria-hidden="true">' +
        '<g class="agzh-vial-wave-group">' +
        '<path d="M0 ' + waveY + ' Q 3.5 ' + (waveY - 2) + ' 7 ' + waveY + ' T 14 ' + waveY + ' T 21 ' + waveY + ' T 28 ' + waveY + ' V 22 H 0 Z" fill="' + liquidColor + '" opacity="0.88"/>' +
        '</g>' +
        '<circle class="agzh-vial-bubble" cx="5" cy="' + Math.min(19, waveY + 5) + '" r="1" fill="#ffffff" opacity="0.7"/>' +
        '<circle class="agzh-vial-bubble" cx="10" cy="' + Math.min(20, waveY + 7) + '" r="0.8" fill="#ffffff" opacity="0.5" style="animation-delay:1.1s"/>' +
        '</svg>';

      var text = document.createElement('span');
      text.textContent = estK + 'K';

      var pop = document.createElement('div');
      pop.className = 'agzh-vial-popover';
      pop.innerHTML =
        '<div style="font-weight:700;margin-bottom:4px;color:' + liquidColor + '">512K 上下文液位 · ' + pct + '%</div>' +
        '<div>当前轮次：' + turns.length + ' 轮 · 估算 ~' + estK + 'K tokens</div>' +
        '<div>光效场景：<b>' + presetLabel + '</b>（点击试管切换）</div>';

      vial.appendChild(tube);
      vial.appendChild(text);
      vial.appendChild(pop);
    }

    // === 引擎 6：LiveCharmEngine（活体伴读角色呼吸、注视与点击 Q 弹星芒彩蛋） ===
    function spawnCharmSparks(host) {
      if (!host) return;
      var angles = [-140, -110, -80, -50, -25, -165, -95, -65];
      for (var i = 0; i < angles.length; i++) {
        var sp = document.createElement('span');
        sp.className = 'agzh-charm-spark';
        var rad = (angles[i] * Math.PI) / 180;
        var dist = 20 + (i % 3) * 8;
        sp.style.left = '34px';
        sp.style.top = '10px';
        sp.style.setProperty('--sx', Math.round(Math.cos(rad) * dist) + 'px');
        sp.style.setProperty('--sy', Math.round(Math.sin(rad) * dist) + 'px');
        host.appendChild(sp);
        setTimeout(
          (function (node) {
            return function () {
              if (node && node.parentNode) node.parentNode.removeChild(node);
            };
          })(sp),
          680
        );
      }
    }

    function syncLiveCharm() {
      var root = document.documentElement;
      if (!root) return;
      if (!prismActive || !prismOptions.liveCharm || isReducedMotion() || hasBrowserHole()) {
        root.removeAttribute('data-agzh-live-charm');
        rm(CHARM_ID);
        charmElRef = null;
        return;
      }
      var hasCharmAsset = false;
      try {
        var S = window.__AGZH_SKIN__;
        if (S && S.icons && S.icons.composer_charm) hasCharmAsset = true;
      } catch (_) {}
      if (!hasCharmAsset) {
        root.removeAttribute('data-agzh-live-charm');
        rm(CHARM_ID);
        return;
      }

      var card = document.querySelector('.surface-composer-card') || document.querySelector('form:has(textarea)');
      if (!card) return;
      root.setAttribute('data-agzh-live-charm', '1');

      var charm = document.getElementById(CHARM_ID);
      if (!charm) {
        charm = document.createElement('div');
        charm.id = CHARM_ID;
        charm.title = '戳戳伴读团子 ✨';
        charm.setAttribute('data-agzh', 'skin');
        charm.addEventListener('click', function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          charm.classList.remove('is-hopping');
          void charm.offsetWidth;
          charm.classList.add('is-hopping');
          spawnCharmSparks(charm);
          setTimeout(function () {
            charm.classList.remove('is-hopping');
          }, 600);
        });
      }
      if (charm.parentNode !== card) {
        card.appendChild(charm);
      }
      charmElRef = charm;
      if (!charmBound) {
        charmBound = true;
        document.addEventListener('pointermove', function (ev) {
          if (!charmElRef || !prismActive || !prismOptions.liveCharm) return;
          try {
            var r = charmElRef.getBoundingClientRect();
            var dx = ev.clientX - (r.left + r.width / 2);
            var dy = ev.clientY - (r.top + r.height / 2);
            if (Math.abs(dx) < 220 && Math.abs(dy) < 180) {
              var deg = Math.max(-8, Math.min(8, Math.round(dx / 24)));
              charmElRef.style.transform = 'rotate(' + deg + 'deg)';
            } else if (charmElRef.style.transform) {
              charmElRef.style.transform = '';
            }
          } catch (_) {}
        }, { passive: true });
      }
    }

    // === 7. 超长代码块手动折叠控制器 ===
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

    // === 8. 会话轮次导轨与 Alt+↑/↓ 快捷跳转 ===
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

    // === 9. CrystalAuraEngine（思考/待决策/完成三态切工水晶光束） ===
    function syncAmbientAura() {
      var root = document.documentElement;
      if (!root) return;
      if (!prismActive || !prismOptions.ambientAura || hasBrowserHole()) {
        root.removeAttribute('data-agzh-aura');
        rm(AURA_BAR_ID);
        prevAuraState = 'idle';
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

      if (prevAuraState === 'thinking' && state === 'idle') {
        root.setAttribute('data-agzh-aura', 'done');
        if (doneAuraTimer) clearTimeout(doneAuraTimer);
        doneAuraTimer = setTimeout(function () {
          if (prismActive && root.getAttribute('data-agzh-aura') === 'done') {
            root.setAttribute('data-agzh-aura', 'idle');
          }
        }, 1400);
      } else if (state !== 'idle' || root.getAttribute('data-agzh-aura') !== 'done') {
        root.setAttribute('data-agzh-aura', state);
      }
      prevAuraState = state;
    }

    function runPrismScan() {
      if (!prismActive) return;
      enhanceLongCodeBlocks();
      syncTurnRail();
      syncAmbientAura();
      syncContextVial();
      syncLiveCharm();
    }

    function ensurePrismControllers() {
      var root = document.documentElement;
      if (!root) return;
      prismActive = true;
      root.setAttribute('data-agzh-prism', '1');
      root.setAttribute('data-agzh-motion', prismOptions.motionPreset || 'full');

      if (prismOptions.rimGlow) bindRimListeners();
      else unbindRimListeners();

      if (prismOptions.codeEnhance) bindTurnNav();
      else {
        unbindTurnNav();
        clearCodeEnhancements();
      }

      bindHorizonEngine();
      bindInkStreamEngine();
      bindCaretEngine();
      runPrismScan();

      if (!prismObserver && typeof MutationObserver !== 'undefined') {
        var target = document.body || root;
        prismObserver = new MutationObserver(function () {
          if (prismScanTimer) return;
          prismScanTimer = setTimeout(function () {
            prismScanTimer = null;
            runPrismScan();
          }, 240);
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
      if (doneAuraTimer) {
        clearTimeout(doneAuraTimer);
        doneAuraTimer = null;
      }
      unbindRimListeners();
      unbindHorizonEngine();
      unbindInkStreamEngine();
      unbindCaretEngine();
      unbindTurnNav();
      clearCodeEnhancements();
      rm(AURA_BAR_ID);
      rm(VIAL_ID);
      rm(CHARM_ID);
      charmElRef = null;
      if (document.documentElement) {
        document.documentElement.removeAttribute('data-agzh-prism');
        document.documentElement.removeAttribute('data-agzh-aura');
        document.documentElement.removeAttribute('data-agzh-motion');
        document.documentElement.removeAttribute('data-agzh-live-charm');
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

    window.__AGZH_SKIN_DISPOSE__ = function () {
      try {
        rm(STYLE_ID);
        rm(PET_STYLE_ID);
        rm(SPRITE_ID);
        stopClassGuardAndRestore();
        clearSymbolTags();
        teardownPrismControllers();
      } catch (_) {}
    };

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
