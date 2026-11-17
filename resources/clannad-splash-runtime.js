/* __AGZH_CLANNAD_SPLASH_RUNTIME__
 * 《CLANNAD》60fps 纯矢量/Canvas 启动序幕引擎（零外部媒体文件依赖）
 * 支持主题: clannad-orbs | clannad-sakura | clannad-sunflower | clannad-starfish
 */
(function () {
  function mountClannadSplash(root, cfg) {
    if (!root) return { destroy: function () {} };
    var opts = cfg || {};
    var theme = opts.theme || 'clannad-orbs';
    var title = opts.title || 'CLANNAD · 幻想世界与星海光玉';
    var subtitle = opts.subtitle || 'ILLUSIONARY WORLD // 奇迹星轨';
    var quote = opts.quote || '「这座小镇，承载着无数温柔的心愿与奇迹」';
    var accent = opts.accent || '#f6c453';
    var isLight = theme === 'clannad-sakura' || theme === 'clannad-sunflower';
    var steps = opts.steps || [
      '正在唤醒小镇星轨与汉化词典...',
      '正在编织高定光学材质管线...',
      '微风拂过坡道，即将步入工作台...'
    ];

    var reducedMotion = false;
    try {
      reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (_) {}

    root.innerHTML = '';
    root.style.cssText = 'position:fixed;inset:0;overflow:hidden;user-select:none;font-family:"HarmonyOS Sans SC","PingFang SC","Microsoft YaHei UI",sans-serif;';

    var canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;';
    root.appendChild(canvas);

    var overlay = document.createElement('div');
    var fgMain = isLight ? '#362730' : '#f8fafc';
    var fgSub = isLight ? 'rgba(54,39,48,0.72)' : 'rgba(226,232,240,0.78)';
    var cardBg = isLight ? 'rgba(255,255,255,0.62)' : 'rgba(10,15,29,0.52)';
    var borderCol = isLight ? 'rgba(229,115,153,0.28)' : 'rgba(255,255,255,0.14)';

    overlay.style.cssText = 'position:relative;z-index:2;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:32px;box-sizing:border-box;text-align:center;';
    overlay.innerHTML =
      '<button id="ag-clannad-skip" type="button" style="position:absolute;top:22px;right:24px;padding:6px 14px;border-radius:999px;border:1px solid ' + borderCol + ';background:' + cardBg + ';color:' + fgMain + ';font-size:12px;cursor:pointer;backdrop-filter:blur(10px);">跳过序幕 (ESC)</button>' +
      '<div style="padding:28px 38px;border-radius:24px;background:' + cardBg + ';border:1px solid ' + borderCol + ';backdrop-filter:blur(16px);max-width:560px;box-shadow:0 24px 60px rgba(0,0,0,0.22);">' +
        '<div style="font-size:11px;letter-spacing:0.22em;font-weight:700;color:' + accent + ';margin-bottom:10px;">' + subtitle + '</div>' +
        '<div style="font-size:26px;font-weight:700;letter-spacing:0.04em;color:' + fgMain + ';margin-bottom:12px;">' + title + '</div>' +
        '<div style="font-size:13.5px;line-height:1.7;color:' + fgSub + ';margin-bottom:22px;">' + quote + '</div>' +
        '<div style="width:100%;height:4px;border-radius:999px;background:rgba(148,163,184,0.24);overflow:hidden;margin-bottom:10px;">' +
          '<div id="ag-clannad-bar" style="width:18%;height:100%;border-radius:999px;background:' + accent + ';transition:width 0.25s ease;"></div>' +
        '</div>' +
        '<div id="ag-clannad-step" style="font-size:11.5px;color:' + fgSub + ';">' + steps[0] + '</div>' +
      '</div>';
    root.appendChild(overlay);

    var skipBtn = document.getElementById('ag-clannad-skip');
    var barEl = document.getElementById('ag-clannad-bar');
    var stepEl = document.getElementById('ag-clannad-step');

    var triggerSkip = function () {
      if (typeof opts.onSkip === 'function') opts.onSkip();
    };
    if (skipBtn) skipBtn.addEventListener('click', function (e) { e.stopPropagation(); triggerSkip(); });
    root.addEventListener('dblclick', triggerSkip);

    var ctx = canvas.getContext('2d');
    var particles = [];
    var count = reducedMotion ? 16 : 42;
    for (var i = 0; i < count; i++) {
      particles.push({
        x: Math.random(),
        y: Math.random(),
        r: 2.5 + Math.random() * 7.5,
        vx: (Math.random() - 0.5) * 0.0008,
        vy: theme === 'clannad-sakura' ? (0.0009 + Math.random() * 0.0014) : -(0.0006 + Math.random() * 0.0012),
        phase: Math.random() * Math.PI * 2,
        alt: i % 3 === 0
      });
    }

    var rafId = 0;
    var startTs = Date.now();
    function resize() {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var w = root.clientWidth || window.innerWidth || 960;
      var h = root.clientHeight || window.innerHeight || 600;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener('resize', resize);

    function render() {
      if (!ctx) return;
      var w = root.clientWidth || window.innerWidth || 960;
      var h = root.clientHeight || window.innerHeight || 600;
      var elapsed = Date.now() - startTs;
      var t = elapsed * 0.001;

      var grad = ctx.createLinearGradient(0, 0, 0, h);
      if (theme === 'clannad-sakura') {
        grad.addColorStop(0, '#ffeef5');
        grad.addColorStop(0.55, '#fff8fb');
        grad.addColorStop(1, '#fbd8e6');
      } else if (theme === 'clannad-sunflower') {
        grad.addColorStop(0, '#38bdf8');
        grad.addColorStop(0.55, '#e0f2fe');
        grad.addColorStop(1, '#fef08a');
      } else if (theme === 'clannad-starfish') {
        grad.addColorStop(0, '#100c1a');
        grad.addColorStop(0.55, '#221738');
        grad.addColorStop(1, '#3b2048');
      } else {
        grad.addColorStop(0, '#050811');
        grad.addColorStop(0.58, '#0d162c');
        grad.addColorStop(1, '#182a4f');
      }
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        if (!reducedMotion) {
          p.x += p.vx + Math.sin(t + p.phase) * 0.0004;
          p.y += p.vy;
          if (p.y < -0.08) p.y = 1.08;
          if (p.y > 1.08) p.y = -0.08;
          if (p.x < -0.05) p.x = 1.05;
          if (p.x > 1.05) p.x = -0.05;
        }
        var px = p.x * w;
        var py = p.y * h;
        var alpha = 0.45 + 0.35 * Math.sin(t * 1.8 + p.phase);

        if (theme === 'clannad-sakura') {
          ctx.save();
          ctx.translate(px, py);
          ctx.rotate(t * 0.8 + p.phase);
          ctx.fillStyle = p.alt ? 'rgba(244,143,177,' + alpha + ')' : 'rgba(251,207,232,' + (alpha + 0.15) + ')';
          ctx.beginPath();
          ctx.ellipse(0, 0, p.r * 1.15, p.r * 0.62, 0, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        } else {
          var rg = ctx.createRadialGradient(px, py, 0, px, py, p.r * 3.2);
          var cMain = theme === 'clannad-sunflower'
            ? 'rgba(251,191,36,' + alpha + ')'
            : theme === 'clannad-starfish'
              ? (p.alt ? 'rgba(251,146,60,' + alpha + ')' : 'rgba(192,132,252,' + alpha + ')')
              : (p.alt ? 'rgba(125,211,252,' + alpha + ')' : 'rgba(246,196,83,' + alpha + ')');
          rg.addColorStop(0, 'rgba(255,255,255,' + Math.min(1, alpha + 0.25) + ')');
          rg.addColorStop(0.4, cMain);
          rg.addColorStop(1, 'rgba(0,0,0,0)');
          ctx.fillStyle = rg;
          ctx.beginPath();
          ctx.arc(px, py, p.r * 3.2, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      var pct = Math.min(100, Math.round((elapsed / 2400) * 100));
      if (barEl) barEl.style.width = Math.max(15, pct) + '%';
      if (stepEl && steps.length > 0) {
        var idx = Math.min(steps.length - 1, Math.floor((pct / 100) * steps.length));
        stepEl.textContent = steps[idx];
      }

      if (!reducedMotion) {
        rafId = requestAnimationFrame(render);
      }
    }

    render();
    return {
      destroy: function () {
        if (rafId) cancelAnimationFrame(rafId);
        window.removeEventListener('resize', resize);
      }
    };
  }

  window.ClannadSplashEngine = { mount: mountClannadSplash };
})();
