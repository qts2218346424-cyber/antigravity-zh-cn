/* __AGZH_CLANNAD_SPLASH_RUNTIME__
 * 《CLANNAD》原版催泪名场面宽银幕启动序幕引擎（支持内嵌原动画剧照 DataURL + 60fps 粒子 + 电影双语台词 + 柔和配乐）
 * 支持主题: clannad-sunflower | clannad-sakura | clannad-orbs | clannad-starfish
 */
(function () {
  function midiToFreq(m) {
    return 440 * Math.pow(2, (m - 69) / 12);
  }

  function startMiniMusicBox(theme) {
    var AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return function () {};
    var ctx = null;
    try {
      ctx = new AudioCtx();
      if (ctx.state === 'suspended') ctx.resume().catch(function () {});

      var master = ctx.createGain();
      master.gain.setValueAtTime(0.0001, ctx.currentTime);
      master.gain.linearRampToValueAtTime(0.14, ctx.currentTime + 0.25);
      master.connect(ctx.destination);

      var motifs = {
        'clannad-sunflower': [74, 79, 81, 83, 81, 79, 76, 79, 83, 86, 81, 79],
        'clannad-sakura': [77, 81, 84, 81, 79, 77, 76, 74, 77, 81, 86, 84],
        'clannad-orbs': [76, 79, 81, 79, 76, 74, 72, 74, 76, 79, 84, 81],
        'clannad-starfish': [74, 81, 79, 77, 76, 72, 74, 84, 81, 79, 77, 74]
      };
      var notes = motifs[theme] || motifs['clannad-sunflower'];
      var tStart = ctx.currentTime + 0.06;
      var step = 0.36;

      for (var i = 0; i < notes.length; i++) {
        var t0 = tStart + i * step;
        var f = midiToFreq(notes[i]);
        var osc = ctx.createOscillator();
        var g = ctx.createGain();
        osc.type = theme === 'clannad-sunflower' ? 'triangle' : 'sine';
        osc.frequency.setValueAtTime(f, t0);
        g.gain.setValueAtTime(0.0001, t0);
        g.gain.linearRampToValueAtTime(0.22, t0 + 0.018);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + 1.15);
        osc.connect(g);
        g.connect(master);
        osc.start(t0);
        osc.stop(t0 + 1.2);
      }

      return function () {
        if (!ctx || ctx.state === 'closed') return;
        try {
          var now = ctx.currentTime;
          master.gain.cancelScheduledValues(now);
          master.gain.setValueAtTime(Math.max(0.0001, master.gain.value), now);
          master.gain.exponentialRampToValueAtTime(0.0001, now + 0.25);
        } catch (_) {}
        setTimeout(function () {
          if (ctx && ctx.state !== 'closed') ctx.close().catch(function () {});
        }, 280);
      };
    } catch (_) {
      return function () {};
    }
  }

  function decodeDataUriToBytes(dataUri) {
    if (!dataUri || typeof dataUri !== 'string') return null;
    var idx = dataUri.indexOf(',');
    if (idx < 0) return null;
    try {
      var raw = window.atob(dataUri.slice(idx + 1));
      var arr = new Uint8Array(raw.length);
      for (var i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
      return arr.buffer;
    } catch (_) {
      return null;
    }
  }

  function startSplashSoundtrack(theme, bgmDataUrl) {
    if (bgmDataUrl) {
      var AudioCtx = window.AudioContext || window.webkitAudioContext;
      var buf = decodeDataUriToBytes(bgmDataUrl);
      if (AudioCtx && buf) {
        try {
          var ctx = new AudioCtx();
          var unlock = function () {
            if (ctx && ctx.state === 'suspended') ctx.resume().catch(function () {});
          };
          if (ctx.state === 'suspended') {
            unlock();
            window.addEventListener('pointerdown', unlock, { once: true });
            window.addEventListener('keydown', unlock, { once: true });
          }
          var gain = ctx.createGain();
          gain.gain.setValueAtTime(0.0001, ctx.currentTime);
          gain.gain.linearRampToValueAtTime(0.75, ctx.currentTime + 0.3);
          gain.connect(ctx.destination);
          var srcNode = null;
          var stopped = false;

          ctx.decodeAudioData(
            buf.slice(0),
            function (audioBuffer) {
              if (stopped || ctx.state === 'closed') return;
              srcNode = ctx.createBufferSource();
              srcNode.buffer = audioBuffer;
              srcNode.loop = true;
              srcNode.connect(gain);
              srcNode.start(0);
            },
            function () {}
          );

          return function () {
            if (stopped) return;
            stopped = true;
            try {
              var now = ctx.currentTime;
              gain.gain.cancelScheduledValues(now);
              gain.gain.setValueAtTime(Math.max(0.0001, gain.gain.value), now);
              gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.28);
            } catch (_) {}
            setTimeout(function () {
              try { if (srcNode) srcNode.stop(); } catch (_) {}
              if (ctx && ctx.state !== 'closed') ctx.close().catch(function () {});
            }, 310);
          };
        } catch (_) {}
      }
    }
    return startMiniMusicBox(theme);
  }
  function drawPetal(ctx, r) {
    ctx.beginPath();
    ctx.moveTo(0, -r);
    ctx.bezierCurveTo(r * 0.85, -r * 0.75, r * 0.95, r * 0.35, 0, r);
    ctx.bezierCurveTo(-r * 0.95, r * 0.35, -r * 0.85, -r * 0.75, 0, -r);
    ctx.closePath();
    ctx.fill();
  }

  function mountClannadSplash(root, cfg) {
    if (!root) return { destroy: function () {} };
    var opts = cfg || {};
    var theme = opts.theme || 'clannad-sunflower';
    var title = opts.title || '盛夏花海 · 在爸爸怀里哭泣';
    var episodeTag = opts.episodeTag || 'CLANNAD ~After Story~ · EP.18「大地の果て」';
    var accent = opts.accent || '#fbbf24';
    var secondaryAccent = opts.secondaryAccent || '#38bdf8';
    var artworkDataUrl = opts.artworkDataUrl || '';
    var dialogues = opts.dialogues || [
      {
        speaker: '冈崎汐',
        zh: opts.quote || '「早苗阿姨说过……能哭的地方，只有厕所，和爸爸的怀里。」',
        en: "The only places I can cry are the bathroom, and in Daddy's arms."
      }
    ];
    var steps = opts.steps || [
      '正在唤醒核心服务与中文语义词典...',
      '正在编织高定光学材质渲染管线...',
      '微风拂过小镇，即将展开工作台...'
    ];

    var reducedMotion = false;
    try {
      reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (_) {}

    root.innerHTML = '';
    root.style.cssText = 'position:fixed;inset:0;overflow:hidden;user-select:none;background:#050811;color:#fff;font-family:"HarmonyOS Sans SC","PingFang SC","Microsoft YaHei UI",sans-serif;';

    var imgEl = null;
    if (artworkDataUrl) {
      imgEl = document.createElement('img');
      imgEl.src = artworkDataUrl;
      imgEl.alt = title;
      imgEl.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center;pointer-events:none;transform:scale(1.02);transition:transform 0.25s linear;';
      root.appendChild(imgEl);
    }

    var canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none;';
    root.appendChild(canvas);

    var shade = document.createElement('div');
    shade.style.cssText = 'position:absolute;inset:0;pointer-events:none;background:linear-gradient(180deg,rgba(4,7,15,0.62) 0%,rgba(4,7,15,0.05) 24%,rgba(4,7,15,0.04) 62%,rgba(4,7,15,0.86) 100%);';
    root.appendChild(shade);

    var topBar = document.createElement('div');
    topBar.style.cssText = 'position:absolute;top:0;left:0;right:0;height:5.2%;min-height:18px;background:rgba(0,0,0,0.9);pointer-events:none;z-index:3;';
    var botBar = document.createElement('div');
    botBar.style.cssText = 'position:absolute;bottom:0;left:0;right:0;height:5.2%;min-height:18px;background:rgba(0,0,0,0.92);pointer-events:none;z-index:3;';
    root.appendChild(topBar);
    root.appendChild(botBar);

    var ui = document.createElement('div');
    ui.style.cssText = 'position:absolute;inset:0;z-index:4;display:flex;flex-direction:column;justify-content:space-between;padding:6.8% 28px;box-sizing:border-box;';
    ui.innerHTML =
      '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;">' +
        '<div>' +
          '<div style="display:inline-flex;align-items:center;gap:7px;padding:4px 12px;border-radius:999px;background:rgba(0,0,0,0.52);border:1px solid rgba(255,255,255,0.16);backdrop-filter:blur(10px);font-size:11px;font-weight:600;letter-spacing:0.06em;">' +
            '<span style="width:7px;height:7px;border-radius:50%;background:' + accent + ';box-shadow:0 0 8px ' + accent + ';"></span>' +
            '<span>' + episodeTag + '</span>' +
          '</div>' +
          '<div style="margin-top:6px;padding-left:4px;font-size:16px;font-weight:700;text-shadow:0 2px 8px rgba(0,0,0,0.9);">' + title + '</div>' +
        '</div>' +
        '<div style="display:flex;align-items:center;gap:8px;">' +
          '<button id="ag-clannad-audio" type="button" style="padding:6px 13px;border-radius:999px;border:1px solid rgba(255,255,255,0.2);background:rgba(0,0,0,0.55);color:#fff;font-size:12px;cursor:pointer;backdrop-filter:blur(10px);">♪ 静音</button>' +
          '<button id="ag-clannad-skip" type="button" style="padding:6px 14px;border-radius:999px;border:1px solid rgba(255,255,255,0.24);background:rgba(0,0,0,0.65);color:#fff;font-size:12px;font-weight:600;cursor:pointer;backdrop-filter:blur(10px);">跳过序幕 (ESC)</button>' +
        '</div>' +
      '</div>' +
      '<div style="display:flex;flex-direction:column;align-items:center;text-align:center;">' +
        '<div id="ag-clannad-speaker" style="padding:2px 10px;border-radius:999px;background:rgba(0,0,0,0.48);border:1px solid rgba(255,255,255,0.15);font-size:10.5px;font-weight:600;color:#fde68a;margin-bottom:6px;">' + (dialogues[0] ? dialogues[0].speaker : '') + '</div>' +
        '<div id="ag-clannad-zh" style="max-width:780px;font-size:19px;font-weight:700;line-height:1.55;letter-spacing:0.03em;text-shadow:0 2px 10px rgba(0,0,0,0.96),0 0 3px #000;margin-bottom:4px;">' + (dialogues[0] ? dialogues[0].zh : '') + '</div>' +
        '<div id="ag-clannad-en" style="max-width:720px;font-size:11.5px;font-style:italic;color:rgba(226,232,240,0.86);text-shadow:0 1px 6px #000;margin-bottom:14px;">' + (dialogues[0] ? dialogues[0].en : '') + '</div>' +
        '<div style="width:100%;max-width:640px;">' +
          '<div style="width:100%;height:3.5px;border-radius:999px;background:rgba(255,255,255,0.22);overflow:hidden;margin-bottom:6px;">' +
            '<div id="ag-clannad-bar" style="width:12%;height:100%;border-radius:999px;background:linear-gradient(90deg,' + accent + ',' + secondaryAccent + ');transition:width 0.2s ease;"></div>' +
          '</div>' +
          '<div style="display:flex;justify-content:space-between;font-size:11px;color:rgba(226,232,240,0.82);text-shadow:0 1px 3px #000;">' +
            '<span id="ag-clannad-step">' + steps[0] + '</span>' +
            '<span id="ag-clannad-pct">12%</span>' +
          '</div>' +
        '</div>' +
      '</div>';
    root.appendChild(ui);

    var stopMusic = startSplashSoundtrack(theme, opts.bgmDataUrl);
    var muted = false;

    var audioBtn = document.getElementById('ag-clannad-audio');
    if (audioBtn) {
      audioBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        if (!muted) {
          muted = true;
          stopMusic();
          audioBtn.textContent = '♪ 开启配乐';
        } else {
          muted = false;
          stopMusic = startSplashSoundtrack(theme, opts.bgmDataUrl);
          audioBtn.textContent = '♪ 静音';
        }
      });
    }

    var skipBtn = document.getElementById('ag-clannad-skip');
    var barEl = document.getElementById('ag-clannad-bar');
    var stepEl = document.getElementById('ag-clannad-step');
    var pctEl = document.getElementById('ag-clannad-pct');
    var speakerEl = document.getElementById('ag-clannad-speaker');
    var zhEl = document.getElementById('ag-clannad-zh');
    var enEl = document.getElementById('ag-clannad-en');

    var triggerSkip = function () {
      stopMusic();
      if (typeof opts.onSkip === 'function') opts.onSkip();
    };
    if (skipBtn) skipBtn.addEventListener('click', function (e) { e.stopPropagation(); triggerSkip(); });
    root.addEventListener('dblclick', triggerSkip);

    var ctx = canvas.getContext('2d');
    var particles = [];
    var count = reducedMotion ? 12 : 30;
    for (var i = 0; i < count; i++) {
      particles.push({
        x: Math.random(),
        y: Math.random(),
        r: 2.2 + Math.random() * 5.2,
        vx: theme === 'clannad-sakura' ? (0.00035 + Math.random() * 0.0007) : (Math.random() - 0.5) * 0.0005,
        vy: theme === 'clannad-sakura' ? (0.0007 + Math.random() * 0.0011) : -(0.0004 + Math.random() * 0.0009),
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

      ctx.clearRect(0, 0, w, h);
      if (!artworkDataUrl) {
        var grad = ctx.createLinearGradient(0, 0, 0, h);
        if (theme === 'clannad-sakura') {
          grad.addColorStop(0, '#ffdde9');
          grad.addColorStop(1, '#f48fb1');
        } else if (theme === 'clannad-sunflower') {
          grad.addColorStop(0, '#0284c7');
          grad.addColorStop(0.55, '#bae6fd');
          grad.addColorStop(1, '#fde047');
        } else if (theme === 'clannad-starfish') {
          grad.addColorStop(0, '#170f26');
          grad.addColorStop(1, '#6b21a8');
        } else {
          grad.addColorStop(0, '#040814');
          grad.addColorStop(1, '#182a4f');
        }
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);
      }

      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        if (!reducedMotion) {
          p.x += p.vx + Math.sin(t + p.phase) * 0.0003;
          p.y += p.vy;
          if (p.y < -0.08) p.y = 1.08;
          if (p.y > 1.08) p.y = -0.08;
          if (p.x < -0.06) p.x = 1.06;
          if (p.x > 1.06) p.x = -0.06;
        }
        var px = p.x * w;
        var py = p.y * h;
        var alpha = 0.42 + 0.28 * Math.sin(t * 1.4 + p.phase);

        if (theme === 'clannad-sakura') {
          ctx.save();
          ctx.translate(px, py);
          ctx.rotate(t * 0.7 + p.phase);
          ctx.fillStyle = p.alt ? 'rgba(251,182,206,' + alpha + ')' : 'rgba(255,228,238,' + (alpha + 0.15) + ')';
          drawPetal(ctx, p.r * 1.15);
          ctx.restore();
        } else {
          var rg = ctx.createRadialGradient(px, py, 0, px, py, p.r * 2.6);
          var cMain = theme === 'clannad-sunflower'
            ? 'rgba(253,224,71,' + (alpha * 0.75) + ')'
            : theme === 'clannad-starfish'
              ? (p.alt ? 'rgba(251,146,60,' + alpha + ')' : 'rgba(216,180,254,' + alpha + ')')
              : (p.alt ? 'rgba(125,211,252,' + alpha + ')' : 'rgba(246,196,83,' + alpha + ')');
          rg.addColorStop(0, 'rgba(255,255,255,' + Math.min(0.95, alpha + 0.2) + ')');
          rg.addColorStop(0.4, cMain);
          rg.addColorStop(1, 'rgba(0,0,0,0)');
          ctx.fillStyle = rg;
          ctx.beginPath();
          ctx.arc(px, py, p.r * 2.6, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      var pct = Math.min(100, Math.round((elapsed / 4200) * 100));
      var safePct = Math.max(12, pct);
      if (barEl) barEl.style.width = safePct + '%';
      if (pctEl) pctEl.textContent = safePct + '%';

      if (imgEl && !reducedMotion) {
        var sc = 1.02 + 0.07 * (safePct / 100);
        imgEl.style.transform = 'scale(' + sc.toFixed(4) + ')';
      }

      if (steps.length > 0 && stepEl) {
        var sIdx = Math.min(steps.length - 1, Math.floor((safePct / 100) * steps.length));
        stepEl.textContent = steps[sIdx];
      }

      if (dialogues.length > 0) {
        var dIdx = Math.min(dialogues.length - 1, Math.floor((safePct / 100) * dialogues.length));
        var d = dialogues[dIdx];
        if (d) {
          if (speakerEl) speakerEl.textContent = d.speaker || '';
          if (zhEl) zhEl.textContent = d.zh || '';
          if (enEl) enEl.textContent = d.en || '';
        }
      }

      if (!reducedMotion) {
        rafId = requestAnimationFrame(render);
      }
    }

    render();
    return {
      destroy: function () {
        stopMusic();
        if (rafId) cancelAnimationFrame(rafId);
        window.removeEventListener('resize', resize);
      }
    };
  }

  window.ClannadSplashEngine = { mount: mountClannadSplash };
})();
