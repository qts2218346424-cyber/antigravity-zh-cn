(function (root) {
  "use strict";

  var STYLE_ID = "ag-kimetsu-theater-style";
  var MAX_PARTICLES = 85;

  var CHAR_META = {
    nezuko: {
      name: "灶门祢豆子",
      breath: "血鬼术 · 爆血连蹴",
      kanji: "爆血",
      primary: "#f472b6",
      accent: "#e11d48",
      secondary: "#fda4af",
      bg: "#09040a",
      acts: [
        { at: 0.00, banner: "竹笼解封 · 鬼化觉醒", move: "初醒微光" },
        { at: 0.28, banner: "血鬼术 · 爆血绽放！！", move: "红莲彼岸花" },
        { at: 0.65, banner: "绯樱护阵 · 破晓之时", move: "爆血归护" },
        { at: 0.88, banner: "黎明守护 · 准备进入工作台", move: "全集中就绪" }
      ]
    },
    tanjiro: {
      name: "灶门炭治郎",
      breath: "水之呼吸 × 火之神神乐",
      kanji: "水火",
      primary: "#38bdf8",
      accent: "#f97316",
      secondary: "#bae6fd",
      bg: "#040812",
      acts: [
        { at: 0.00, banner: "全集中 · 常中吐息", move: "静水蓄势" },
        { at: 0.25, banner: "水之呼吸 拾之型 · 生生流转", move: "浮世绘水龙" },
        { at: 0.60, banner: "火之神神乐 · 日晕之龙！！", move: "炽焰日轮环" },
        { at: 0.86, banner: "碧罗之天 · 破晓归鞘", move: "全集中就绪" }
      ]
    },
    zenitsu: {
      name: "我妻善逸",
      breath: "雷之呼吸 壹之型 · 霹雳一闪",
      kanji: "雷闪",
      primary: "#fbbf24",
      accent: "#f59e0b",
      secondary: "#fef08a",
      bg: "#05060b",
      acts: [
        { at: 0.00, banner: "雷之呼吸 壹之型 · 居合屏息", move: "暴雨凝神" },
        { at: 0.26, banner: "霹雳一闪 · 神速六连！！", move: "金雷破空" },
        { at: 0.62, banner: "神速奥义 · 火雷神！！", move: "天雷斩裂" },
        { at: 0.86, banner: "万籁俱寂 · 咔哒归鞘", move: "全集中就绪" }
      ]
    },
    inosuke: {
      name: "嘴平伊之助",
      breath: "兽之呼吸 · 狂牙裂斩",
      kanji: "狂牙",
      primary: "#60a5fa",
      accent: "#2563eb",
      secondary: "#93c5fd",
      bg: "#050914",
      acts: [
        { at: 0.00, banner: "兽之呼吸 漆之型 · 空间识觉", move: "声呐锁定" },
        { at: 0.28, banner: "猪突猛进 · 双牙狂乱！！", move: "交叉破屏斩" },
        { at: 0.64, banner: "伍之牙 · 狂牙撕裂 × 圆转牙", move: "野性气浪" },
        { at: 0.86, banner: "双刀扛肩 · 霸气定格", move: "全集中就绪" }
      ]
    },
    all: {
      name: "鬼灭全明星 · 无限城决战",
      breath: "全集中 · 四象呼吸联携奥义",
      kanji: "合击",
      primary: "#c084fc",
      accent: "#f472b6",
      secondary: "#38bdf8",
      bg: "#06040e",
      acts: [
        { at: 0.00, banner: "第一象 · 炭治郎 水火神乐起势", move: "水龙破局" },
        { at: 0.18, banner: "第二象 · 善逸 霹雳一闪雷鸣切入", move: "金雷瞬步" },
        { at: 0.36, banner: "第三象 · 伊之助 狂牙双刃突击", move: "兽牙猛进" },
        { at: 0.54, banner: "第四象 · 祢豆子 血鬼术爆血共鸣", move: "爆血花莲" },
        { at: 0.74, banner: "羁绊同心 · 四象呼吸全员集结！！", move: "四象合一" }
      ]
    }
  };

  function injectStyles() {
    if (typeof document === "undefined" || document.getElementById(STYLE_ID)) return;
    var css = [
      ".ag-kt-root{position:relative;width:100%;height:100%;overflow:hidden;background:#04060b;color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei UI',sans-serif;user-select:none;}",
      ".ag-kt-canvas{position:absolute;inset:0;width:100%;height:100%;display:block;z-index:2;}",
      ".ag-kt-letterbox{position:absolute;left:0;right:0;background:linear-gradient(180deg,rgba(2,3,8,0.92),rgba(2,3,8,0.72));z-index:5;pointer-events:none;transition:transform 0.36s cubic-bezier(0.16,1,0.3,1);}",
      ".ag-kt-letterbox.top{top:0;height:44px;border-bottom:1px solid rgba(255,255,255,0.08);transform:translateY(-4px);}",
      ".ag-kt-letterbox.bot{bottom:0;height:52px;background:linear-gradient(0deg,rgba(2,3,8,0.95),rgba(2,3,8,0.72));border-top:1px solid rgba(255,255,255,0.08);transform:translateY(4px);}",
      ".ag-kt-root.climax .ag-kt-letterbox.top{transform:translateY(0);}",
      ".ag-kt-root.climax .ag-kt-letterbox.bot{transform:translateY(0);}",
      ".ag-kt-hud-top{position:absolute;top:12px;left:20px;right:20px;z-index:9;display:flex;align-items:center;justify-content:space-between;pointer-events:none;gap:12px;}",
      ".ag-kt-brand{display:flex;align-items:center;gap:10px;min-width:0;}",
      ".ag-kt-crest{width:28px;height:28px;flex-shrink:0;border-radius:50%;border:2px solid var(--kt-primary,#38bdf8);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;background:rgba(5,7,14,0.88);box-shadow:0 0 12px var(--kt-primary,#38bdf8);font-family:'KaiTi','STKaiti',serif;}",
      ".ag-kt-title{font-size:12px;font-weight:800;letter-spacing:0.18em;text-shadow:0 2px 10px rgba(0,0,0,0.95);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}",
      ".ag-kt-top-right{display:flex;align-items:center;gap:8px;flex-shrink:0;}",
      ".ag-kt-pill{padding:4px 12px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:0.06em;background:rgba(8,12,24,0.82);border:1px solid rgba(255,255,255,0.22);}",
      ".ag-kt-skip{-webkit-app-region:no-drag;pointer-events:auto;cursor:pointer;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:0.05em;color:#e2e8f0;background:rgba(15,23,42,0.85);border:1px solid rgba(255,255,255,0.25);transition:background 0.15s ease,transform 0.15s ease;}",
      ".ag-kt-skip:hover{background:rgba(255,255,255,0.18);color:#ffffff;transform:translateY(-1px);}",
      ".ag-kt-hud-bot{position:absolute;bottom:14px;left:22px;right:22px;z-index:9;display:flex;flex-direction:column;gap:7px;pointer-events:none;}",
      ".ag-kt-act-row{display:flex;align-items:center;justify-content:space-between;gap:12px;}",
      ".ag-kt-step-text{font-size:12.5px;font-weight:600;letter-spacing:0.03em;color:#f1f5f9;text-shadow:0 2px 8px rgba(0,0,0,0.98);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}",
      ".ag-kt-move-badge{flex-shrink:0;padding:2px 9px;border-radius:6px;font-size:11px;font-weight:800;background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.25);color:#fef08a;}",
      ".ag-kt-bar-track{width:100%;height:4px;border-radius:999px;background:rgba(255,255,255,0.14);overflow:hidden;}",
      ".ag-kt-bar-fill{height:100%;width:100%;border-radius:999px;transform-origin:left center;transform:scaleX(0);will-change:transform;background:linear-gradient(90deg,var(--kt-primary,#38bdf8),var(--kt-accent,#f472b6),#ffffff);}"
    ].join("\n");
    var el = document.createElement("style");
    el.id = STYLE_ID;
    el.textContent = css;
    document.head.appendChild(el);
  }

  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function easeOutCubic(t) { return 1 - Math.pow(1 - clamp(t, 0, 1), 3); }
  function easeOutBack(t) {
    t = clamp(t, 0, 1);
    var c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  }
  function smoothStep(edge0, edge1, x) {
    var t = clamp((x - edge0) / (edge1 - edge0), 0, 1);
    return t * t * (3 - 2 * t);
  }

  function loadImages(assets) {
    var map = {};
    if (!assets || typeof assets !== "object" || typeof Image === "undefined") return map;
    var keys = Object.keys(assets);
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      var src = assets[k];
      if (!src) continue;
      var img = new Image();
      img.decoding = "async";
      img.src = src;
      map[k] = img;
    }
    return map;
  }

  function imgReady(img) {
    return img && img.complete && img.naturalWidth > 0;
  }

  // 离屏软发光粒子纹理缓存（替代昂贵的 ctx.shadowBlur，性能提升 10x+）
  var glowSpriteCache = {};
  function getGlowSprite(color) {
    if (glowSpriteCache[color]) return glowSpriteCache[color];
    if (typeof document === "undefined") return null;
    var c = document.createElement("canvas");
    c.width = 48;
    c.height = 48;
    var gctx = c.getContext("2d");
    var g = gctx.createRadialGradient(24, 24, 1, 24, 24, 24);
    g.addColorStop(0, "#ffffff");
    g.addColorStop(0.28, color);
    g.addColorStop(1, "rgba(0,0,0,0)");
    gctx.fillStyle = g;
    gctx.fillRect(0, 0, 48, 48);
    glowSpriteCache[color] = c;
    return c;
  }

  // 高性能发光线段（双层叠加替代 shadowBlur）
  function drawNeonSegments(ctx, segs, coreColor, glowColor, width, alpha) {
    if (!segs || !segs.length) return;
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    ctx.beginPath();
    for (var i = 0; i < segs.length; i++) {
      ctx.moveTo(segs[i][0], segs[i][1]);
      ctx.lineTo(segs[i][2], segs[i][3]);
    }
    ctx.globalAlpha = 0.24 * alpha;
    ctx.strokeStyle = glowColor;
    ctx.lineWidth = width * 3.4;
    ctx.stroke();

    ctx.globalAlpha = 0.65 * alpha;
    ctx.lineWidth = width * 1.6;
    ctx.stroke();

    ctx.globalAlpha = 0.96 * alpha;
    ctx.strokeStyle = coreColor;
    ctx.lineWidth = Math.max(1.2, width * 0.55);
    ctx.stroke();
    ctx.restore();
  }

  function buildLightning(x1, y1, x2, y2, displace, depth) {
    var segs = [];
    function subdivide(ax, ay, bx, by, disp, d) {
      if (d <= 0) {
        segs.push([ax, ay, bx, by]);
        return;
      }
      var mx = (ax + bx) * 0.5 + (Math.random() - 0.5) * disp;
      var my = (ay + by) * 0.5 + (Math.random() - 0.5) * disp;
      subdivide(ax, ay, mx, my, disp * 0.55, d - 1);
      subdivide(mx, my, bx, by, disp * 0.55, d - 1);
      if (d >= 2 && Math.random() < 0.42) {
        var ang = Math.atan2(by - ay, bx - ax) + (Math.random() - 0.5) * 1.3;
        var len = Math.hypot(bx - ax, by - ay) * (0.28 + Math.random() * 0.3);
        subdivide(mx, my, mx + Math.cos(ang) * len, my + Math.sin(ang) * len, disp * 0.4, d - 2);
      }
    }
    subdivide(x1, y1, x2, y2, displace, depth || 3);
    return segs;
  }

  // 背景舞台：深邃暗调径向光晕 + 传统日轮纹罗盘 + 动态速度线
  function drawStageBackdrop(ctx, W, H, tSec, charKey, intensity, heroImg) {
    var meta = CHAR_META[charKey] || CHAR_META.nezuko;

    // 1. 若有主原画，先铺一层低透明度全景动态漫游底景（零黑屏、氛围感极强）
    ctx.fillStyle = meta.bg || "#05070c";
    ctx.fillRect(0, 0, W, H);

    if (imgReady(heroImg)) {
      ctx.save();
      var iw = heroImg.naturalWidth, ih = heroImg.naturalHeight;
      var bgScale = Math.max(W / iw, H / ih) * (1.12 + Math.sin(tSec * 0.6) * 0.03);
      var dw = iw * bgScale, dh = ih * bgScale;
      ctx.globalAlpha = 0.22 + intensity * 0.14;
      ctx.drawImage(heroImg, (W - dw) * 0.5, (H - dh) * 0.45, dw, dh);
      ctx.restore();
    }

    // 2. 暗角压暗与主色调氛围叠层
    var grd = ctx.createRadialGradient(W * 0.5, H * 0.48, 20, W * 0.5, H * 0.5, Math.max(W, H) * 0.78);
    grd.addColorStop(0, "rgba(4,6,12,0.18)");
    grd.addColorStop(0.58, "rgba(4,6,12,0.72)");
    grd.addColorStop(1, "rgba(2,3,8,0.96)");
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);

    // 3. 日轮刀镡几何法阵（细线慢转，彰显高级和风质感）
    var unit = Math.min(W, H) / 480;
    var cx = W * 0.5, cy = H * 0.49;
    var baseR = Math.min(W, H) * 0.36;

    ctx.save();
    ctx.translate(cx, cy);
    ctx.globalCompositeOperation = "lighter";
    ctx.strokeStyle = meta.primary;

    ctx.save();
    ctx.rotate(tSec * 0.18);
    ctx.globalAlpha = 0.18 + intensity * 0.14;
    ctx.lineWidth = 1.4;
    ctx.setLineDash([10 * unit, 8 * unit]);
    ctx.beginPath();
    ctx.arc(0, 0, baseR, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    ctx.save();
    ctx.rotate(-tSec * 0.28);
    ctx.globalAlpha = 0.14 + intensity * 0.12;
    ctx.strokeStyle = meta.accent;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.arc(0, 0, baseR * 0.84, 0, Math.PI * 2);
    ctx.stroke();
    // 8 芒星刻度
    for (var s = 0; s < 8; s++) {
      var a = (s / 8) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(Math.cos(a) * baseR * 0.79, Math.sin(a) * baseR * 0.79);
      ctx.lineTo(Math.cos(a) * baseR * 0.90, Math.sin(a) * baseR * 0.90);
      ctx.stroke();
    }
    ctx.restore();
    ctx.restore();

    // 4. 高潮放射集中速度线（轻量化 28 条，无 shadowBlur）
    if (intensity > 0.2) {
      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      ctx.strokeStyle = "#ffffff";
      var lineCount = 28;
      var rInBase = Math.min(W, H) * (0.34 - intensity * 0.06);
      var rOut = Math.max(W, H) * 0.9;
      for (var k = 0; k < lineCount; k++) {
        var ang = (k / lineCount) * Math.PI * 2 + Math.sin(tSec * 14 + k * 3) * 0.03;
        var rIn = rInBase + ((k * 29) % 13) * 4 * unit;
        ctx.globalAlpha = (0.04 + ((k * 7) % 5) * 0.015) * intensity;
        ctx.lineWidth = (k % 4 === 0) ? 2 : 1;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(ang) * rIn, cy + Math.sin(ang) * rIn);
        ctx.lineTo(cx + Math.cos(ang) * rOut, cy + Math.sin(ang) * rOut);
        ctx.stroke();
      }
      ctx.restore();
    }
  }

  // 绘制高清原画电影级主视窗（圆角宽屏银幕 + Ken Burns 呼吸运镜 + 扫光 + 冲击脉冲）
  function drawCinemaHeroCard(ctx, W, H, img, opts) {
    if (!imgReady(img)) return;
    var tSec = opts.tSec || 0;
    var enter = opts.enter !== undefined ? opts.enter : 1;
    var zoomPunch = opts.zoomPunch || 0;
    var primary = opts.primary || "#38bdf8";
    var accent = opts.accent || "#f472b6";
    var cardW = Math.min(W * 0.68, H * 1.18, 620);
    var cardH = cardW * 0.60;
    var cx = W * 0.5;
    var cy = H * 0.49 + (1 - enter) * 28;
    var radius = Math.max(12, Math.min(22, cardW * 0.036));
    var scale = (0.94 + enter * 0.06) * (1 + zoomPunch * 0.075);

    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(scale, scale);
    ctx.globalAlpha = clamp(enter, 0, 1);

    // 背后双色能量光环（无 shadowBlur，用径向渐变高性能模拟）
    var glowR = Math.max(cardW, cardH) * 0.72;
    var halo = ctx.createRadialGradient(0, 0, cardH * 0.25, 0, 0, glowR);
    halo.addColorStop(0, primary + "44");
    halo.addColorStop(0.55, accent + "18");
    halo.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = halo;
    ctx.fillRect(-glowR, -glowR, glowR * 2, glowR * 2);

    // 圆角裁切主画框
    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(-cardW * 0.5, -cardH * 0.5, cardW, cardH, radius);
    } else {
      ctx.rect(-cardW * 0.5, -cardH * 0.5, cardW, cardH);
    }
    ctx.save();
    ctx.clip();

    // 原画动态 Ken Burns 推镜呼吸（始终保持柔和移动，永不呆板）
    var iw = img.naturalWidth, ih = img.naturalHeight;
    var kenBurns = 1.03 + Math.sin(tSec * 0.9) * 0.025 + zoomPunch * 0.04;
    var imgScale = Math.max(cardW / iw, cardH / ih) * kenBurns;
    var dw = iw * imgScale, dh = ih * imgScale;
    var panX = Math.sin(tSec * 0.7) * 8;
    var panY = Math.cos(tSec * 0.55) * 4;
    ctx.drawImage(img, -dw * 0.5 + panX, -dh * 0.48 + panY, dw, dh);

    // 电影感边缘柔化渐变 + 呼吸色调光晕
    var vig = ctx.createLinearGradient(0, -cardH * 0.5, 0, cardH * 0.5);
    vig.addColorStop(0, "rgba(4,6,12,0.16)");
    vig.addColorStop(0.7, "rgba(4,6,12,0.04)");
    vig.addColorStop(1, "rgba(4,6,12,0.58)");
    ctx.fillStyle = vig;
    ctx.fillRect(-cardW * 0.5, -cardH * 0.5, cardW, cardH);

    // 周期性斜向流光扫过特效（Anime Sheen Sweep）
    var sweepCycle = (tSec * 0.55) % 1;
    if (sweepCycle < 0.45) {
      var sp = sweepCycle / 0.45;
      var sx = lerp(-cardW * 0.85, cardW * 0.85, sp);
      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      ctx.translate(sx, 0);
      ctx.rotate(0.42);
      var sg = ctx.createLinearGradient(-45, 0, 45, 0);
      sg.addColorStop(0, "rgba(255,255,255,0)");
      sg.addColorStop(0.5, "rgba(255,255,255,0.22)");
      sg.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = sg;
      ctx.fillRect(-45, -cardH, 90, cardH * 2);
      ctx.restore();
    }
    ctx.restore();

    // 双层精美边框（外层主题霓虹 + 内层极细白金亮边）
    ctx.strokeStyle = primary;
    ctx.globalAlpha = 0.65;
    ctx.lineWidth = 3.2;
    ctx.stroke();

    ctx.strokeStyle = "rgba(255,255,255,0.68)";
    ctx.globalAlpha = 0.85;
    ctx.lineWidth = 1.2;
    ctx.stroke();

    ctx.restore();
  }

  // 全屏剑气斩弧（无 shadowBlur，双层 lighter 叠加）
  function drawSlashArc(ctx, x1, y1, cx, cy, x2, y2, width, colorCore, colorGlow, progress) {
    if (progress <= 0 || progress >= 1) return;
    var fade = 1 - smoothStep(0.45, 1.0, progress);
    var head = easeOutCubic(smoothStep(0, 0.36, progress));
    var hx = lerp(x1, x2, head);
    var hy = lerp(y1, y2, head);
    var hcx = lerp(x1, cx, head);
    var hcy = lerp(y1, cy, head);

    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo(hcx, hcy, hx, hy);

    ctx.globalAlpha = fade * 0.28;
    ctx.strokeStyle = colorGlow;
    ctx.lineWidth = width * 2.1;
    ctx.stroke();

    ctx.globalAlpha = fade * 0.72;
    ctx.lineWidth = width * 1.1;
    ctx.stroke();

    ctx.globalAlpha = fade * 0.95;
    ctx.strokeStyle = colorCore;
    ctx.lineWidth = Math.max(2, width * 0.36);
    ctx.stroke();
    ctx.restore();
  }

  // 浮世绘水龙 / 日晕火龙流光轨（无 shadowBlur）
  function drawBreathStream(ctx, x1, y1, cx, cy, x2, y2, progress, isFire) {
    if (progress <= 0 || progress >= 1) return;
    var tail = smoothStep(0.32, 1.0, progress);
    var alpha = 1 - smoothStep(0.72, 1.0, progress);
    var steps = 22;
    var cGlow = isFire ? "#f97316" : "#0ea5e9";
    var cFoam = isFire ? "#fef08a" : "#e0f2fe";

    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    ctx.lineCap = "round";
    for (var layer = 0; layer < 2; layer++) {
      ctx.beginPath();
      for (var i = 0; i <= steps; i++) {
        var s = lerp(tail, clamp(progress * 1.12, 0, 1), i / steps);
        var inv = 1 - s;
        var px = inv * inv * x1 + 2 * inv * s * cx + s * s * x2;
        var py = inv * inv * y1 + 2 * inv * s * cy + s * s * y2;
        var wave = Math.sin(s * 16 + progress * 10 + layer * 1.6) * (layer === 0 ? 11 : 6);
        px += wave * 0.5;
        py += wave;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.strokeStyle = layer === 0 ? cGlow : cFoam;
      ctx.lineWidth = (layer === 0 ? 18 : 5) * (1 - progress * 0.3);
      ctx.globalAlpha = alpha * (layer === 0 ? 0.55 : 0.9);
      ctx.stroke();
    }
    ctx.restore();
  }

  // 血鬼术·彼岸火莲绽放
  function drawBloodLotus(ctx, cx, cy, radius, rot, progress) {
    if (progress <= 0 || progress >= 1) return;
    var r = radius * easeOutCubic(progress);
    var alpha = 1 - smoothStep(0.5, 1.0, progress);
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    ctx.translate(cx, cy);
    ctx.rotate(rot + progress * 0.7);
    ctx.globalAlpha = alpha * 0.82;

    var petals = 8;
    for (var i = 0; i < petals; i++) {
      ctx.save();
      ctx.rotate((i / petals) * Math.PI * 2);
      ctx.fillStyle = i % 2 === 0 ? "#f43f5e" : "#f472b6";
      ctx.beginPath();
      ctx.moveTo(0, r * 0.14);
      ctx.quadraticCurveTo(r * 0.24, r * 0.55, 0, r);
      ctx.quadraticCurveTo(-r * 0.24, r * 0.55, 0, r * 0.14);
      ctx.fill();
      ctx.restore();
    }
    ctx.fillStyle = "#fff1f2";
    ctx.beginPath();
    ctx.arc(0, 0, r * 0.15, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // 高清漫画斜切 Cut-in 横幅（仅在高潮切入，使用高清原画）
  function drawCutInBanner(ctx, W, H, img, progress, opts) {
    if (progress <= 0 || progress >= 1) return;
    var enter = easeOutCubic(smoothStep(0, 0.24, progress));
    var exit = 1 - smoothStep(0.76, 1.0, progress);
    var open = enter * exit;
    if (open <= 0.02) return;

    var bandH = Math.min(H * 0.36, 190) * open;
    var cy = (opts.yRatio || 0.49) * H;
    var tilt = opts.tilt !== undefined ? opts.tilt : -0.09;
    var glow = opts.glow || "#fbbf24";
    var slideX = (1 - enter) * W * 0.35 * (opts.fromRight ? 1 : -1);

    ctx.save();
    ctx.translate(W * 0.5 + slideX, cy);
    ctx.rotate(tilt);

    var stripW = W * 1.3;
    ctx.beginPath();
    ctx.rect(-stripW * 0.5, -bandH * 0.5, stripW, bandH);
    ctx.save();
    ctx.clip();

    ctx.fillStyle = "#05070c";
    ctx.fillRect(-stripW * 0.5, -bandH * 0.5, stripW, bandH);

    if (imgReady(img)) {
      var zoom = 1.12 + progress * 0.14;
      var drawW = Math.max(W * 0.85, bandH * (img.naturalWidth / img.naturalHeight)) * zoom;
      var drawH = drawW * (img.naturalHeight / img.naturalWidth);
      var panX = (opts.fromRight ? -1 : 1) * (progress - 0.5) * 40;
      ctx.globalAlpha = 0.94;
      ctx.drawImage(img, -drawW * 0.5 + panX, -drawH * 0.44, drawW, drawH);
    }

    var grad = ctx.createLinearGradient(-stripW * 0.35, 0, stripW * 0.35, 0);
    grad.addColorStop(0, "rgba(0,0,0,0.78)");
    grad.addColorStop(0.35, "rgba(0,0,0,0.12)");
    grad.addColorStop(0.65, "rgba(0,0,0,0.12)");
    grad.addColorStop(1, "rgba(0,0,0,0.78)");
    ctx.fillStyle = grad;
    ctx.globalAlpha = 1;
    ctx.fillRect(-stripW * 0.5, -bandH * 0.5, stripW, bandH);

    if (opts.title) {
      ctx.font = "900 " + Math.round(clamp(bandH * 0.24, 20, 42)) + "px 'KaiTi','STKaiti','Microsoft YaHei UI',sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#ffffff";
      ctx.fillText(opts.title, -W * 0.38, bandH * 0.14);
      if (opts.sub) {
        ctx.font = "700 " + Math.round(clamp(bandH * 0.095, 11, 15)) + "px sans-serif";
        ctx.fillStyle = glow;
        ctx.fillText(opts.sub, -W * 0.38, -bandH * 0.18);
      }
    }
    ctx.restore();

    ctx.strokeStyle = glow;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(-stripW * 0.5, -bandH * 0.5);
    ctx.lineTo(stripW * 0.5, -bandH * 0.5);
    ctx.moveTo(-stripW * 0.5, bandH * 0.5);
    ctx.lineTo(stripW * 0.5, bandH * 0.5);
    ctx.stroke();

    ctx.restore();
  }

  // 全明星模式：四象高清动态漫画分镜联携演出
  function drawQuartetStage(ctx, W, H, imgs, u, tSec) {
    var chars = [
      { img: imgs.tanjiro, color: "#38bdf8", name: "炭治郎 · 水火神乐", dx: -0.345, enterAt: 0.00 },
      { img: imgs.zenitsu, color: "#fbbf24", name: "善逸 · 霹雳一闪", dx: -0.115, enterAt: 0.18 },
      { img: imgs.inosuke, color: "#60a5fa", name: "伊之助 · 狂牙裂斩", dx: 0.115, enterAt: 0.36 },
      { img: imgs.nezuko, color: "#f472b6", name: "祢豆子 · 血鬼术爆血", dx: 0.345, enterAt: 0.54 }
    ];
    var panelW = Math.min(W * 0.205, 220);
    var panelH = Math.min(H * 0.60, 340);
    var skew = -0.12;
    var activeIdx = u >= 0.72 ? -1 : Math.min(3, Math.floor(u / 0.18));

    for (var i = 0; i < chars.length; i++) {
      var item = chars[i];
      var localRaw = clamp((u - item.enterAt) / 0.18, 0, 1);
      if (localRaw <= 0) continue;

      var enterP = easeOutBack(Math.min(1, localRaw * 1.1));
      var isFocused = (activeIdx === i) || (u >= 0.74);
      var focusScale = activeIdx === i ? 1.07 : (u >= 0.74 ? 1.01 + Math.sin(tSec * 2.2 + i) * 0.015 : 0.96);

      var targetX = W * (0.5 + item.dx);
      var slideY = (i % 2 === 0 ? -1 : 1) * (1 - clamp(enterP, 0, 1.06)) * H * 0.38;
      var cy = H * 0.49 + slideY;

      ctx.save();
      ctx.translate(targetX, cy);
      ctx.scale(focusScale, focusScale);
      ctx.transform(1, 0, skew, 1, 0, 0);
      ctx.globalAlpha = clamp(localRaw * 2.4, 0, 1);

      ctx.beginPath();
      ctx.rect(-panelW * 0.5, -panelH * 0.5, panelW, panelH);
      ctx.save();
      ctx.clip();

      ctx.fillStyle = "#080b14";
      ctx.fillRect(-panelW * 0.5, -panelH * 0.5, panelW, panelH);

      if (imgReady(item.img)) {
        var iw = item.img.naturalWidth, ih = item.img.naturalHeight;
        var kb = 1.12 + Math.sin(tSec * 0.9 + i * 1.4) * 0.03;
        var scale = Math.max(panelW * 1.24 / iw, panelH * 1.02 / ih) * kb;
        var dw = iw * scale, dh = ih * scale;
        ctx.drawImage(item.img, -dw * 0.5, -dh * 0.47, dw, dh);
      }

      var overlay = ctx.createLinearGradient(0, -panelH * 0.5, 0, panelH * 0.5);
      overlay.addColorStop(0, isFocused ? "rgba(0,0,0,0.08)" : "rgba(0,0,0,0.35)");
      overlay.addColorStop(0.6, "rgba(0,0,0,0.08)");
      overlay.addColorStop(1, "rgba(0,0,0,0.88)");
      ctx.fillStyle = overlay;
      ctx.fillRect(-panelW * 0.5, -panelH * 0.5, panelW, panelH);
      ctx.restore();

      ctx.strokeStyle = isFocused ? item.color : "rgba(255,255,255,0.28)";
      ctx.lineWidth = isFocused ? 2.8 : 1.5;
      ctx.strokeRect(-panelW * 0.5, -panelH * 0.5, panelW, panelH);

      ctx.transform(1, 0, -skew, 1, 0, 0);
      ctx.fillStyle = "#ffffff";
      ctx.font = "800 " + Math.round(clamp(W * 0.014, 11, 14)) + "px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(item.name, -panelH * 0.1 * skew, panelH * 0.42);
      ctx.restore();
    }

    // 合击光环与居中日轮徽光
    if (u >= 0.72) {
      var hp = (u - 0.72) / 0.28;
      var unit = Math.min(W, H) / 480;
      var pulse = Math.sin(tSec * 3.2) * 0.08 + 1;
      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      ctx.globalAlpha = easeOutCubic(Math.min(1, hp * 2)) * 0.55;
      ctx.strokeStyle = "#f472b6";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.arc(W * 0.5, H * 0.49, 110 * unit * pulse, 0, Math.PI * 2);
      ctx.stroke();
      ctx.strokeStyle = "#38bdf8";
      ctx.beginPath();
      ctx.arc(W * 0.5, H * 0.49, 140 * unit / pulse, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }
  }

  function mount(container, options) {
    if (!container) return null;
    injectStyles();

    var opts = options || {};
    var charKey = CHAR_META[opts.character] ? opts.character : "nezuko";
    var meta = CHAR_META[charKey];
    var durationMs = opts.durationMs || 4200;
    var loop = opts.loop !== undefined ? !!opts.loop : true;
    var allowSkip = !!opts.allowSkip;
    var onSkip = typeof opts.onSkip === "function" ? opts.onSkip : null;
    var steps = Array.isArray(opts.steps) && opts.steps.length ? opts.steps : meta.acts.map(function (a) { return a.banner; });
    var imgs = loadImages(opts.assets || {});

    container.innerHTML = "";
    var rootEl = document.createElement("div");
    rootEl.className = "ag-kt-root";
    rootEl.style.setProperty("--kt-primary", meta.primary);
    rootEl.style.setProperty("--kt-accent", meta.accent);

    var canvas = document.createElement("canvas");
    canvas.className = "ag-kt-canvas";

    var lbTop = document.createElement("div");
    lbTop.className = "ag-kt-letterbox top";
    var lbBot = document.createElement("div");
    lbBot.className = "ag-kt-letterbox bot";

    var hudTop = document.createElement("div");
    hudTop.className = "ag-kt-hud-top";
    hudTop.innerHTML =
      "<div class='ag-kt-brand'>" +
        "<div class='ag-kt-crest'>滅</div>" +
        "<div class='ag-kt-title'>ANTIGRAVITY // " + meta.name + "</div>" +
      "</div>" +
      "<div class='ag-kt-top-right'>" +
        "<div class='ag-kt-pill'>" + meta.breath + "</div>" +
        (allowSkip ? "<button type='button' class='ag-kt-skip' data-kt='skip'>跳过 · ESC</button>" : "") +
      "</div>";

    var hudBot = document.createElement("div");
    hudBot.className = "ag-kt-hud-bot";
    hudBot.innerHTML =
      "<div class='ag-kt-act-row'>" +
        "<div class='ag-kt-step-text' data-kt='step'></div>" +
        "<div class='ag-kt-move-badge' data-kt='move'>" + meta.kanji + "</div>" +
      "</div>" +
      "<div class='ag-kt-bar-track'><div class='ag-kt-bar-fill' data-kt='fill'></div></div>";

    rootEl.appendChild(canvas);
    rootEl.appendChild(lbTop);
    rootEl.appendChild(lbBot);
    rootEl.appendChild(hudTop);
    rootEl.appendChild(hudBot);
    container.appendChild(rootEl);

    var stepEl = hudBot.querySelector("[data-kt='step']");
    var moveEl = hudBot.querySelector("[data-kt='move']");
    var fillEl = hudBot.querySelector("[data-kt='fill']");
    var skipBtn = hudTop.querySelector("[data-kt='skip']");

    function handleSkipTrigger() {
      if (onSkip) onSkip();
    }
    function onKeyDown(e) {
      if (!allowSkip) return;
      if (e.key === "Escape" || e.key === " " || e.key === "Enter") {
        handleSkipTrigger();
      }
    }
    if (skipBtn) skipBtn.addEventListener("click", handleSkipTrigger);
    if (allowSkip && typeof window !== "undefined") {
      window.addEventListener("keydown", onKeyDown);
    }

    var ctx = canvas.getContext("2d", { alpha: false });
    var W = 960, H = 540, dpr = 1;

    function syncSize() {
      var rect = rootEl.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      var nw = Math.max(320, Math.round(rect.width || 960));
      var nh = Math.max(200, Math.round(rect.height || 540));
      if (canvas.width !== Math.round(nw * dpr) || canvas.height !== Math.round(nh * dpr)) {
        W = nw; H = nh;
        canvas.width = Math.round(nw * dpr);
        canvas.height = Math.round(nh * dpr);
      }
    }
    syncSize();

    var ro = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(function () { syncSize(); });
      ro.observe(rootEl);
    } else if (typeof window !== "undefined") {
      window.addEventListener("resize", syncSize);
    }

    var state = {
      startAt: performance.now(),
      lastAt: performance.now(),
      shake: 0,
      impactTimer: 0,
      zoomPunch: 0,
      particles: [],
      lotuses: [],
      cachedBolts: [],
      boltRefreshAt: 0,
      lastImpactBucket: -1,
      rafId: 0,
      destroyed: false
    };

    function spawnParticles(px, py, count, color, speed, sizeBase) {
      for (var i = 0; i < count; i++) {
        if (state.particles.length >= MAX_PARTICLES) {
          state.particles.shift();
        }
        var ang = Math.random() * Math.PI * 2;
        var spd = speed * (0.35 + Math.random() * 0.85);
        state.particles.push({
          x: px, y: py,
          vx: Math.cos(ang) * spd,
          vy: Math.sin(ang) * spd,
          life: 1,
          decay: 0.75 + Math.random() * 0.9,
          r: (sizeBase || 3) * (0.65 + Math.random() * 0.95),
          color: color
        });
      }
    }

    function triggerImpact(uKey, shakeVal, flashMs, punch) {
      if (state.lastImpactBucket === uKey) return;
      state.lastImpactBucket = uKey;
      state.shake = Math.max(state.shake, shakeVal);
      state.impactTimer = Math.max(state.impactTimer, flashMs || 0);
      state.zoomPunch = Math.max(state.zoomPunch, punch || 0);
    }

    function resetEpisode() {
      var now = performance.now();
      state.startAt = now;
      state.lastAt = now;
      state.shake = 0;
      state.impactTimer = 0;
      state.zoomPunch = 0;
      state.particles = [];
      state.lotuses = [];
      state.cachedBolts = [];
      state.boltRefreshAt = 0;
      state.lastImpactBucket = -1;
    }

    function renderFrame(now) {
      if (state.destroyed) return;

      var dt = Math.min(0.05, Math.max(0.001, (now - state.lastAt) / 1000));
      state.lastAt = now;

      var elapsed = now - state.startAt;
      if (loop && elapsed >= durationMs) {
        resetEpisode();
        elapsed = 0;
      }
      var u = clamp(elapsed / durationMs, 0, 1);
      // tSec 持续单调递增，确保即使 loop=false 到达 u=1 后背景呼吸/粒子仍流畅微动而不卡死
      var tSec = elapsed / 1000;

      // 更新 HUD
      var sIdx = Math.min(steps.length - 1, Math.floor(u * steps.length));
      if (stepEl && stepEl.textContent !== steps[sIdx]) stepEl.textContent = steps[sIdx];
      var curAct = meta.acts[0];
      for (var ai = 0; ai < meta.acts.length; ai++) {
        if (u >= meta.acts[ai].at) curAct = meta.acts[ai];
      }
      if (moveEl && moveEl.textContent !== curAct.move) moveEl.textContent = curAct.move;
      if (fillEl) fillEl.style.transform = "scaleX(" + u.toFixed(4) + ")";

      var isClimax = (u >= 0.26 && u <= 0.86);
      if (rootEl.classList.contains("climax") !== isClimax) {
        rootEl.classList.toggle("climax", isClimax);
      }

      // 基于 dt 的平滑阻尼衰减
      var damp = Math.pow(0.03, dt);
      state.shake *= damp;
      if (state.shake < 0.15) state.shake = 0;
      state.zoomPunch *= Math.pow(0.015, dt);
      if (state.zoomPunch < 0.002) state.zoomPunch = 0;
      if (state.impactTimer > 0) state.impactTimer = Math.max(0, state.impactTimer - dt * 1000);

      for (var pi = state.particles.length - 1; pi >= 0; pi--) {
        var pt = state.particles[pi];
        pt.x += pt.vx * dt * 60;
        pt.y += pt.vy * dt * 60;
        pt.vx *= Math.pow(0.25, dt);
        pt.vy *= Math.pow(0.25, dt);
        pt.life -= pt.decay * dt;
        if (pt.life <= 0) state.particles.splice(pi, 1);
      }

      ctx.save();
      ctx.scale(dpr, dpr);

      var sx = state.shake ? (Math.random() - 0.5) * state.shake * 2 : 0;
      var sy = state.shake ? (Math.random() - 0.5) * state.shake * 2 : 0;
      ctx.translate(sx, sy);

      var unit = Math.min(W, H) / 480;
      var intensity = isClimax ? 0.86 : (u > 0.15 ? 0.45 : 0.2);
      var heroImg = imgs[charKey] || imgs.nezuko || imgs.tanjiro;

      drawStageBackdrop(ctx, W, H, tSec, charKey, intensity, heroImg);

      // ==================== 5 大高清原画 + 剧场级特效剧本 ====================
      if (charKey === "tanjiro") {
        var enterT = easeOutCubic(clamp(u / 0.16, 0, 1));
        var isFire = u >= 0.60;
        drawCinemaHeroCard(ctx, W, H, imgs.tanjiro, {
          tSec: tSec,
          enter: enterT,
          zoomPunch: state.zoomPunch,
          primary: isFire ? "#f97316" : "#38bdf8",
          accent: isFire ? "#ef4444" : "#0ea5e9"
        });

        if (u < 0.25) {
          if (Math.random() < 0.45) spawnParticles(W * 0.5 + (Math.random() - 0.5) * W * 0.4, H * 0.68, 1, "#7dd3fc", 1.8, 3.2);
        } else if (u < 0.60) {
          var tp2 = (u - 0.25) / 0.35;
          var seg = Math.floor(tp2 * 2);
          var sub = (tp2 * 2) % 1;
          if (seg === 0 && sub < 0.15) triggerImpact(101, 7, 0, 0.5);
          if (seg === 1 && sub < 0.15) triggerImpact(102, 9, 30, 0.7);
          drawBreathStream(ctx, W * 0.1, H * 0.72, W * 0.5, H * 0.16, W * 0.9, H * 0.45, sub, false);
          drawSlashArc(ctx, W * 0.14, H * 0.72, W * 0.5, H * 0.34, W * 0.88, H * 0.48, 18 * unit, "#ffffff", "#38bdf8", sub);
          if (Math.random() < 0.6) spawnParticles(W * lerp(0.18, 0.82, sub), H * 0.48, 2, "#bae6fd", 3.5, 3);
        } else if (u < 0.86) {
          var tp3 = (u - 0.60) / 0.26;
          if (tp3 < 0.36) {
            drawCutInBanner(ctx, W, H, imgs.tanjiro, tp3 / 0.36, {
              title: "火之神神乐 · 日晕之龙", sub: "HINOKAMI KAGURA", glow: "#f97316", tilt: -0.07
            });
          } else {
            var fk = (tp3 - 0.36) / 0.64;
            if (fk < 0.15) triggerImpact(103, 14, 48, 1.0);
            drawBreathStream(ctx, W * 0.08, H * 0.74, W * 0.48, H * 0.14, W * 0.92, H * 0.52, fk, true);
            drawSlashArc(ctx, W * 0.12, H * 0.78, W * 0.52, H * 0.15, W * 0.92, H * 0.46, 26 * unit, "#fef08a", "#ef4444", fk);
            if (Math.random() < 0.7) spawnParticles(W * lerp(0.2, 0.85, fk), H * 0.46, 2, "#fb923c", 4.5, 3.2);
          }
        } else {
          // 收招常驻微火花，永不僵死
          if (Math.random() < 0.35) spawnParticles(W * (0.2 + Math.random() * 0.6), H * 0.76, 1, "#fb923c", 1.5, 2.5);
        }
      } else if (charKey === "zenitsu") {
        var enterZ = easeOutCubic(clamp(u / 0.16, 0, 1));
        drawCinemaHeroCard(ctx, W, H, imgs.zenitsu, {
          tSec: tSec,
          enter: enterZ,
          zoomPunch: state.zoomPunch,
          primary: "#fbbf24",
          accent: "#f59e0b"
        });

        if (u < 0.26) {
          // 慢动作雨滴 + 细微静电荷
          ctx.save();
          ctx.strokeStyle = "rgba(186,230,253,0.38)";
          ctx.lineWidth = 1.2;
          for (var r = 0; r < 18; r++) {
            var rx = ((r * 97) % 100) * 0.01 * W;
            var ry = (((r * 61) % 100) * 0.01 * H + tSec * 36) % H;
            ctx.beginPath(); ctx.moveTo(rx, ry); ctx.lineTo(rx - 2, ry + 12); ctx.stroke();
          }
          ctx.restore();
        } else if (u < 0.62) {
          var zp2 = (u - 0.26) / 0.36;
          var hops = [[0.10, 0.74], [0.88, 0.30], [0.18, 0.26], [0.86, 0.68], [0.22, 0.50], [0.84, 0.24]];
          var hIdx = Math.min(4, Math.floor(zp2 * 5));
          var hSub = (zp2 * 5) % 1;
          if (hSub < 0.18) triggerImpact(200 + hIdx, 10, hIdx % 2 === 1 ? 35 : 0, 0.65);

          if (now >= state.boltRefreshAt) {
            state.boltRefreshAt = now + 75;
            state.cachedBolts = [];
            for (var hi = Math.max(0, hIdx - 1); hi <= hIdx; hi++) {
              var pa = hops[hi], pb = hops[hi + 1];
              var ep = hi === hIdx ? easeOutCubic(hSub) : 1;
              state.cachedBolts.push(buildLightning(W * pa[0], H * pa[1], W * lerp(pa[0], pb[0], ep), H * lerp(pa[1], pb[1], ep), 26, 3));
            }
          }
          for (var bi = 0; bi < state.cachedBolts.length; bi++) {
            drawNeonSegments(ctx, state.cachedBolts[bi], "#ffffff", "#fbbf24", bi === state.cachedBolts.length - 1 ? 3.2 : 1.6, 1);
          }
          if (Math.random() < 0.55) {
            spawnParticles(W * lerp(hops[hIdx][0], hops[hIdx + 1][0], hSub), H * lerp(hops[hIdx][1], hops[hIdx + 1][1], hSub), 2, "#fef08a", 5, 2.8);
          }
        } else if (u < 0.86) {
          var zp3 = (u - 0.62) / 0.24;
          if (zp3 < 0.38) {
            drawCutInBanner(ctx, W, H, imgs.zenitsu, zp3 / 0.38, {
              title: "霹雳一闪 · 火雷神！！", sub: "THUNDERCLAP AND FLASH", glow: "#fbbf24", tilt: -0.09, fromRight: true
            });
          } else {
            var zk = (zp3 - 0.38) / 0.62;
            if (zk < 0.15) {
              triggerImpact(210, 16, 55, 1.0);
              state.cachedBolts = [buildLightning(W * 0.06, H * 0.85, W * 0.94, H * 0.15, 42, 4)];
            }
            if (state.cachedBolts.length) drawNeonSegments(ctx, state.cachedBolts[0], "#ffffff", "#fbbf24", 4.5, 1 - zk * 0.6);
            drawSlashArc(ctx, W * 0.06, H * 0.86, W * 0.48, H * 0.44, W * 0.94, H * 0.14, 24 * unit, "#ffffff", "#fbbf24", zk);
          }
        } else {
          // 柔和电火花余韵
          if (Math.random() < 0.32) spawnParticles(W * (0.25 + Math.random() * 0.5), H * (0.35 + Math.random() * 0.35), 1, "#fef08a", 2.2, 2.2);
        }
      } else if (charKey === "inosuke") {
        var enterI = easeOutCubic(clamp(u / 0.16, 0, 1));
        drawCinemaHeroCard(ctx, W, H, imgs.inosuke, {
          tSec: tSec,
          enter: enterI,
          zoomPunch: state.zoomPunch,
          primary: "#60a5fa",
          accent: "#2563eb"
        });

        if (u < 0.28) {
          // 空间识觉蓝波声呐脉冲
          var ip1 = u / 0.28;
          for (var w = 0; w < 3; w++) {
            var wp = ip1 * 1.8 - w * 0.35;
            if (wp > 0 && wp < 1) {
              ctx.save();
              ctx.globalCompositeOperation = "lighter";
              ctx.strokeStyle = "#60a5fa";
              ctx.globalAlpha = (1 - wp) * 0.68;
              ctx.lineWidth = 2.2;
              ctx.beginPath();
              ctx.ellipse(W * 0.5, H * 0.49, wp * W * 0.52, wp * H * 0.42, 0, 0, Math.PI * 2);
              ctx.stroke();
              ctx.restore();
            }
          }
        } else if (u < 0.64) {
          var ip2 = (u - 0.28) / 0.36;
          var leg = Math.floor(ip2 * 3);
          var subI = (ip2 * 3) % 1;
          if (subI < 0.16) {
            triggerImpact(300 + leg, 10, leg === 2 ? 36 : 0, 0.72);
            spawnParticles(W * 0.5, H * 0.49, 6, "#93c5fd", 5.5, 2.8);
          }
          drawSlashArc(ctx, W * 0.12, H * 0.22, W * 0.5, H * 0.49, W * 0.88, H * 0.78, 18 * unit, "#ffffff", "#3b82f6", subI);
          drawSlashArc(ctx, W * 0.88, H * 0.22, W * 0.5, H * 0.49, W * 0.12, H * 0.78, 18 * unit, "#ffffff", "#60a5fa", subI);
        } else if (u < 0.86) {
          var ip3 = (u - 0.64) / 0.22;
          if (ip3 < 0.42) {
            drawCutInBanner(ctx, W, H, imgs.inosuke, ip3 / 0.42, {
              title: "伍之牙 · 狂牙撕裂！！", sub: "BEAST BREATHING", glow: "#60a5fa", tilt: 0.08
            });
          } else {
            var ik = (ip3 - 0.42) / 0.58;
            if (ik < 0.18) triggerImpact(310, 15, 45, 0.95);
            drawSlashArc(ctx, W * 0.08, H * 0.18, W * 0.5, H * 0.49, W * 0.92, H * 0.82, 26 * unit, "#ffffff", "#3b82f6", ik);
            drawSlashArc(ctx, W * 0.92, H * 0.18, W * 0.5, H * 0.49, W * 0.08, H * 0.82, 26 * unit, "#ffffff", "#60a5fa", ik);
          }
        } else {
          if (Math.random() < 0.35) spawnParticles(W * (0.25 + Math.random() * 0.5), H * 0.74, 1, "#93c5fd", 1.8, 2.4);
        }
      } else if (charKey === "nezuko") {
        var enterN = easeOutCubic(clamp(u / 0.16, 0, 1));
        drawCinemaHeroCard(ctx, W, H, imgs.nezuko, {
          tSec: tSec,
          enter: enterN,
          zoomPunch: state.zoomPunch,
          primary: "#f472b6",
          accent: "#e11d48"
        });

        if (u < 0.28) {
          // 冲击波光环缓缓苏醒扩散
          var np1 = u / 0.28;
          if (np1 > 0.35 && imgReady(imgs.box_impact_shockwave)) {
            var swP = (np1 - 0.35) / 0.65;
            if (swP < 0.15) triggerImpact(401, 8, 25, 0.55);
            ctx.save();
            ctx.globalCompositeOperation = "lighter";
            ctx.globalAlpha = (1 - swP) * 0.8;
            var sw = 240 * unit * (0.6 + swP * 1.6);
            ctx.drawImage(imgs.box_impact_shockwave, W * 0.5 - sw * 0.5, H * 0.54 - sw * 0.5, sw, sw);
            ctx.restore();
          }
        } else if (u < 0.65) {
          var np2 = (u - 0.28) / 0.37;
          if (np2 < 0.36) {
            drawCutInBanner(ctx, W, H, imgs.nezuko, np2 / 0.36, {
              title: "血鬼术 · 爆血！！", sub: "EXPLODING BLOOD", glow: "#ec4899", tilt: -0.08
            });
          } else {
            var nk = (np2 - 0.36) / 0.64;
            if (nk < 0.15) {
              triggerImpact(410, 14, 48, 0.9);
              state.lotuses = [
                [0.20, 0.38, 125, 0.2], [0.80, 0.36, 135, 0.9],
                [0.24, 0.68, 115, 0.6], [0.76, 0.66, 125, 1.1]
              ];
            }
            for (var li = 0; li < state.lotuses.length; li++) {
              var lt = state.lotuses[li];
              drawBloodLotus(ctx, W * lt[0], H * lt[1], lt[2] * unit, lt[3], clamp(nk * 1.15 - li * 0.05, 0, 1));
            }
            drawSlashArc(ctx, W * 0.15, H * 0.68, W * 0.5, H * 0.24, W * 0.85, H * 0.68, 18 * unit, "#fff1f2", "#e11d48", nk);
            if (Math.random() < 0.65) spawnParticles(W * (0.2 + Math.random() * 0.6), H * (0.3 + Math.random() * 0.45), 2, "#f472b6", 3.5, 3);
          }
        } else {
          // 温柔绯樱火花持续缓缓上浮
          if (Math.random() < 0.45) spawnParticles(W * (0.18 + Math.random() * 0.64), H * 0.78, 1, "#fda4af", 1.8, 2.6);
        }
      } else {
        // all：四象联携高清分镜大舞台
        if (u < 0.72) {
          var stepIdx = Math.floor(u / 0.18);
          var stepLocal = (u % 0.18) / 0.18;
          if (stepLocal < 0.15) {
            triggerImpact(500 + stepIdx, 8, 24, 0.5);
            var stepColors = ["#38bdf8", "#fbbf24", "#60a5fa", "#f472b6"];
            spawnParticles(W * (0.18 + stepIdx * 0.21), H * 0.5, 8, stepColors[stepIdx % 4], 4.5, 3);
          }
        } else if (u < 0.78) {
          triggerImpact(520, 14, 48, 0.85);
        } else {
          if (Math.random() < 0.4) {
            var qCols = ["#38bdf8", "#fbbf24", "#60a5fa", "#f472b6"];
            spawnParticles(W * (0.15 + Math.random() * 0.7), H * 0.76, 1, qCols[Math.floor(Math.random() * 4)], 1.8, 2.5);
          }
        }
        drawQuartetStage(ctx, W, H, imgs, u, tSec);
      }

      // 渲染高性能发光粒子（使用离屏纹理贴图，零 shadowBlur）
      if (state.particles.length) {
        ctx.save();
        ctx.globalCompositeOperation = "lighter";
        for (var pIdx = 0; pIdx < state.particles.length; pIdx++) {
          var pObj = state.particles[pIdx];
          var sp = getGlowSprite(pObj.color);
          ctx.globalAlpha = clamp(pObj.life, 0, 1);
          if (sp) {
            var sz = pObj.r * 5.2 * unit;
            ctx.drawImage(sp, pObj.x - sz * 0.5, pObj.y - sz * 0.5, sz, sz);
          } else {
            ctx.fillStyle = pObj.color;
            ctx.beginPath();
            ctx.arc(pObj.x, pObj.y, pObj.r * unit, 0, Math.PI * 2);
            ctx.fill();
          }
        }
        ctx.restore();
      }

      // 轻量化瞬间高对比 Impact 闪屏
      if (state.impactTimer > 0) {
        ctx.save();
        ctx.globalCompositeOperation = "lighter";
        ctx.fillStyle = meta.primary;
        ctx.globalAlpha = clamp(state.impactTimer / 90, 0.08, 0.32);
        ctx.fillRect(0, 0, W, H);
        ctx.restore();
      }

      ctx.restore();
      state.rafId = requestAnimationFrame(renderFrame);
    }

    state.rafId = requestAnimationFrame(renderFrame);

    return {
      replay: function () { resetEpisode(); },
      destroy: function () {
        state.destroyed = true;
        if (state.rafId) cancelAnimationFrame(state.rafId);
        if (ro) ro.disconnect();
        else if (typeof window !== "undefined") window.removeEventListener("resize", syncSize);
        if (skipBtn) skipBtn.removeEventListener("click", handleSkipTrigger);
        if (allowSkip && typeof window !== "undefined") window.removeEventListener("keydown", onKeyDown);
        container.innerHTML = "";
      }
    };
  }

  root.KimetsuTheater = {
    mount: mount,
    CHARACTERS: CHAR_META
  };
})(typeof window !== "undefined" ? window : globalThis);
