(function (root) {
  "use strict";

  var STYLE_ID = "ag-kimetsu-theater-style";

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
        { at: 0.00, banner: "竹笼破封 · 鬼化觉醒", move: "破箱突袭" },
        { at: 0.22, banner: "狂袭乱蹴 · 三连爪裂", move: "赤爪空翻踢" },
        { at: 0.50, banner: "血鬼术 · 爆血！！", move: "红莲鬼炎绽放" },
        { at: 0.78, banner: "余烬归护 · 破晓之时", move: "黎明守护" }
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
        { at: 0.18, banner: "水之呼吸 拾之型 · 生生流转", move: "巨浪水龙连斩" },
        { at: 0.52, banner: "火之神神乐 · 日晕之龙！！", move: "赫刀满月回旋" },
        { at: 0.80, banner: "碧罗之天 · 残火收刀", move: "破晓归鞘" }
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
        { at: 0.00, banner: "雷之呼吸 壹之型 · 居合屏息", move: "雨夜子弹时间" },
        { at: 0.22, banner: "霹雳一闪 · 神速六连！！", move: "折线极速瞬杀" },
        { at: 0.56, banner: "神速奥义 · 火雷神！！", move: "黄金天雷破壁" },
        { at: 0.82, banner: "万籁俱寂 · 咔哒归鞘", move: "电弧收刃" }
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
        { at: 0.00, banner: "兽之呼吸 漆之型 · 空间识觉", move: "声呐锁定猎物" },
        { at: 0.22, banner: "猪突猛进 · 双牙狂乱！！", move: "野性双刀暴冲" },
        { at: 0.54, banner: "伍之牙 · 狂牙撕裂 × 圆转牙", move: "交叉 X 破屏斩" },
        { at: 0.80, banner: "双刀扛肩 · 野性咆哮", move: "霸气定格" }
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
        { at: 0.00, banner: "炭治郎 · 生生流转前锋破局", move: "第一幕 · 水龙起手" },
        { at: 0.22, banner: "善逸 · 霹雳一闪三连瞬步切入", move: "第二幕 · 雷闪横穿" },
        { at: 0.44, banner: "伊之助 · 狂牙双刃斜切破防", move: "第三幕 · 兽牙猛进" },
        { at: 0.64, banner: "祢豆子爆血 × 四象呼吸大合击！！", move: "第四幕 · 终极四象奥义" },
        { at: 0.86, banner: "羁绊同心 · 四人分镜定格集结", move: "破晓全员入列" }
      ]
    }
  };

  function injectStyles() {
    if (typeof document === "undefined" || document.getElementById(STYLE_ID)) return;
    var css = [
      ".ag-kt-root{position:relative;width:100%;height:100%;overflow:hidden;background:#04060b;color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei UI',sans-serif;user-select:none;}",
      ".ag-kt-canvas{position:absolute;inset:0;width:100%;height:100%;display:block;z-index:2;}",
      ".ag-kt-letterbox{position:absolute;left:0;right:0;background:#020306;z-index:5;pointer-events:none;transition:height 0.4s cubic-bezier(0.16,1,0.3,1);}",
      ".ag-kt-letterbox.top{top:0;height:6%;border-bottom:1px solid rgba(255,255,255,0.08);}",
      ".ag-kt-letterbox.bot{bottom:0;height:6%;border-top:1px solid rgba(255,255,255,0.08);}",
      ".ag-kt-root.climax .ag-kt-letterbox{height:9%;}",
      ".ag-kt-hud-top{position:absolute;top:16px;left:22px;right:22px;z-index:8;display:flex;align-items:center;justify-content:space-between;pointer-events:none;}",
      ".ag-kt-brand{display:flex;align-items:center;gap:10px;}",
      ".ag-kt-crest{width:28px;height:28px;border-radius:50%;border:2px solid var(--kt-primary,#38bdf8);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;background:rgba(5,7,14,0.8);box-shadow:0 0 14px var(--kt-primary,#38bdf8);font-family:'KaiTi','STKaiti',serif;}",
      ".ag-kt-title{font-size:12px;font-weight:800;letter-spacing:0.22em;text-shadow:0 2px 10px rgba(0,0,0,0.9);}",
      ".ag-kt-pill{padding:4px 12px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:0.08em;background:rgba(8,12,24,0.78);border:1px solid rgba(255,255,255,0.22);backdrop-filter:blur(6px);}",
      ".ag-kt-hud-bot{position:absolute;bottom:16px;left:24px;right:24px;z-index:8;display:flex;flex-direction:column;gap:7px;pointer-events:none;}",
      ".ag-kt-act-row{display:flex;align-items:center;justify-content:space-between;gap:12px;}",
      ".ag-kt-step-text{font-size:12.5px;font-weight:600;letter-spacing:0.04em;color:#f1f5f9;text-shadow:0 2px 8px rgba(0,0,0,0.95);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}",
      ".ag-kt-move-badge{flex-shrink:0;padding:2px 9px;border-radius:6px;font-size:11px;font-weight:800;background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.25);color:#fef08a;}",
      ".ag-kt-bar-track{width:100%;height:5px;border-radius:999px;background:rgba(255,255,255,0.14);overflow:hidden;box-shadow:inset 0 1px 2px rgba(0,0,0,0.6);}",
      ".ag-kt-bar-fill{height:100%;width:0%;border-radius:999px;background:linear-gradient(90deg,var(--kt-primary,#38bdf8),var(--kt-accent,#f472b6),#ffffff);box-shadow:0 0 12px var(--kt-primary,#38bdf8);transition:width 0.08s linear;}"
    ].join("\n");
    var el = document.createElement("style");
    el.id = STYLE_ID;
    el.textContent = css;
    document.head.appendChild(el);
  }

  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function easeOutCubic(t) { return 1 - Math.pow(1 - clamp(t, 0, 1), 3); }
  function easeInOutQuad(t) { t = clamp(t, 0, 1); return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }
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
      img.src = src;
      map[k] = img;
    }
    return map;
  }

  function imgReady(img) {
    return img && img.complete && img.naturalWidth > 0;
  }

  // 生成分形闪电路径（主干 + 分支）
  function buildLightning(x1, y1, x2, y2, displace, depth) {
    var segs = [];
    function subdivide(ax, ay, bx, by, disp, d) {
      if (d <= 0) {
        segs.push([ax, ay, bx, by]);
        return;
      }
      var mx = (ax + bx) * 0.5 + (Math.random() - 0.5) * disp;
      var my = (ay + by) * 0.5 + (Math.random() - 0.5) * disp;
      subdivide(ax, ay, mx, my, disp * 0.54, d - 1);
      subdivide(mx, my, bx, by, disp * 0.54, d - 1);
      if (d >= 2 && Math.random() < 0.45) {
        var ang = Math.atan2(by - ay, bx - ax) + (Math.random() - 0.5) * 1.4;
        var len = Math.hypot(bx - ax, by - ay) * (0.3 + Math.random() * 0.35);
        subdivide(mx, my, mx + Math.cos(ang) * len, my + Math.sin(ang) * len, disp * 0.4, d - 2);
      }
    }
    subdivide(x1, y1, x2, y2, displace, depth || 4);
    return segs;
  }

  function drawLightningSegs(ctx, segs, coreColor, glowColor, width) {
    if (!segs || !segs.length) return;
    ctx.save();
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.shadowBlur = 22;
    ctx.shadowColor = glowColor;
    ctx.strokeStyle = glowColor;
    ctx.lineWidth = width * 2.4;
    ctx.beginPath();
    for (var i = 0; i < segs.length; i++) {
      ctx.moveTo(segs[i][0], segs[i][1]);
      ctx.lineTo(segs[i][2], segs[i][3]);
    }
    ctx.stroke();

    ctx.shadowBlur = 8;
    ctx.shadowColor = "#ffffff";
    ctx.strokeStyle = coreColor;
    ctx.lineWidth = width;
    ctx.stroke();
    ctx.restore();
  }

  // 透视无限城/夜战空间背景
  function drawDynamicBattleStage(ctx, W, H, tSec, charKey, intensity) {
    var meta = CHAR_META[charKey] || CHAR_META.tanjiro;
    var grd = ctx.createRadialGradient(W * 0.5, H * 0.46, 10, W * 0.5, H * 0.5, Math.max(W, H) * 0.85);
    if (charKey === "zenitsu") {
      grd.addColorStop(0, "rgba(251,191,36," + (0.14 + intensity * 0.22) + ")");
      grd.addColorStop(0.55, "rgba(18,14,8,0.96)");
      grd.addColorStop(1, "#030408");
    } else if (charKey === "nezuko") {
      grd.addColorStop(0, "rgba(244,114,182," + (0.16 + intensity * 0.25) + ")");
      grd.addColorStop(0.55, "rgba(28,8,20,0.96)");
      grd.addColorStop(1, "#060208");
    } else if (charKey === "inosuke") {
      grd.addColorStop(0, "rgba(96,165,250," + (0.16 + intensity * 0.22) + ")");
      grd.addColorStop(0.55, "rgba(8,18,36,0.96)");
      grd.addColorStop(1, "#03060d");
    } else if (charKey === "all") {
      grd.addColorStop(0, "rgba(192,132,252," + (0.18 + intensity * 0.26) + ")");
      grd.addColorStop(0.5, "rgba(22,10,32,0.95)");
      grd.addColorStop(1, "#04030b");
    } else {
      grd.addColorStop(0, "rgba(56,189,248," + (0.16 + intensity * 0.24) + ")");
      grd.addColorStop(0.55, "rgba(7,18,32,0.96)");
      grd.addColorStop(1, "#02050a");
    }
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);

    // 动态透视地板网格 & 无限城纵深廊柱
    ctx.save();
    var vpX = W * 0.5 + Math.sin(tSec * 2.1) * W * 0.03;
    var vpY = H * 0.44 + Math.cos(tSec * 1.7) * H * 0.02;
    ctx.strokeStyle = meta.primary;
    ctx.globalAlpha = 0.09 + intensity * 0.12;
    ctx.lineWidth = 1;

    var rays = charKey === "all" ? 16 : 12;
    for (var i = 0; i < rays; i++) {
      var a = (i / rays) * Math.PI * 2 + tSec * (charKey === "all" ? 0.22 : 0.06);
      ctx.beginPath();
      ctx.moveTo(vpX, vpY);
      ctx.lineTo(vpX + Math.cos(a) * W * 1.2, vpY + Math.sin(a) * H * 1.2);
      ctx.stroke();
    }

    // 纵深推进方框（高速向前飞掠感）
    var boxCount = 6;
    for (var b = 0; b < boxCount; b++) {
      var z = ((b / boxCount) + tSec * (0.45 + intensity * 0.7)) % 1;
      var sc = Math.pow(z, 2.2) * 1.45;
      var bw = W * sc;
      var bh = H * sc * 0.86;
      ctx.globalAlpha = Math.sin(z * Math.PI) * (0.12 + intensity * 0.16);
      ctx.strokeRect(vpX - bw * 0.5, vpY - bh * 0.5, bw, bh);
    }
    ctx.restore();

    // 全屏高速放射集中速度线 (Anime Speed Lines)
    if (intensity > 0.12) {
      ctx.save();
      var cx = W * 0.5, cy = H * 0.48;
      var lineCount = Math.floor(32 + intensity * 56);
      ctx.strokeStyle = "#ffffff";
      for (var k = 0; k < lineCount; k++) {
        var ang = (k / lineCount) * Math.PI * 2 + Math.sin(tSec * 29 + k * 7) * 0.04;
        var rIn = Math.min(W, H) * (0.28 + ((k * 37) % 19) * 0.014 - intensity * 0.08);
        var rOut = Math.max(W, H) * 0.95;
        ctx.globalAlpha = (0.05 + ((k * 13) % 10) * 0.018) * intensity;
        ctx.lineWidth = (k % 5 === 0) ? 2.4 : 1.1;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(ang) * rIn, cy + Math.sin(ang) * rIn);
        ctx.lineTo(cx + Math.cos(ang) * rOut, cy + Math.sin(ang) * rOut);
        ctx.stroke();
      }
      ctx.restore();
    }
  }

  // 鬼灭之刃高精动态剑士剪影演武绘制（支持旋转/冲刺前倾/挥刀/羽织飘动/残影）
  function drawFighterActor(ctx, kind, opts) {
    var x = opts.x || 0;
    var y = opts.y || 0;
    var scale = opts.scale || 1;
    var dir = opts.dir || 1; // 1 向右，-1 向左
    var lean = opts.lean || 0; // 前倾角度 (rad)
    var slashAngle = opts.slashAngle || -0.7; // 刀臂角度
    var crouch = opts.crouch || 0; // 0 站立，1 极低蹲伏
    var alpha = opts.alpha !== undefined ? opts.alpha : 1;
    var auraColor = opts.auraColor || "#38bdf8";
    var bladeColor = opts.bladeColor || "#e0f2fe";
    var phase = opts.phase || 0;
    var isSilhouette = !!opts.isSilhouette;

    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(x, y);
    ctx.scale(dir * scale, scale);
    ctx.rotate(lean);

    var hipY = lerp(0, 22, crouch);
    var torsoTopY = hipY - lerp(44, 30, crouch);

    // 呼吸法背光气场
    if (!isSilhouette) {
      ctx.save();
      ctx.shadowBlur = 24;
      ctx.shadowColor = auraColor;
      ctx.fillStyle = auraColor;
      ctx.globalAlpha = alpha * 0.25;
      ctx.beginPath();
      ctx.ellipse(0, hipY - 22, 34, 48, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // 飘扬羽织披风/兽皮（贝塞尔二次随动）
    var flutter = Math.sin(phase * 18) * 10 + 18;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(-6, torsoTopY + 4);
    ctx.quadraticCurveTo(-38 - flutter * 0.4, torsoTopY + 20, -56 - flutter, hipY + 18 + Math.cos(phase * 14) * 6);
    ctx.lineTo(-16 - flutter * 0.3, hipY + 14);
    ctx.closePath();
    if (isSilhouette) {
      ctx.fillStyle = auraColor;
    } else if (kind === "zenitsu") {
      ctx.fillStyle = "#f59e0b";
      ctx.strokeStyle = "#fef3c7";
      ctx.lineWidth = 2;
    } else if (kind === "tanjiro") {
      ctx.fillStyle = "#10b981";
      ctx.strokeStyle = "#064e3b";
      ctx.lineWidth = 2;
    } else if (kind === "inosuke") {
      ctx.fillStyle = "#78350f";
      ctx.strokeStyle = "#93c5fd";
      ctx.lineWidth = 1.6;
    } else {
      ctx.fillStyle = "#311024";
      ctx.strokeStyle = "#f472b6";
      ctx.lineWidth = 2;
    }
    ctx.fill();
    if (!isSilhouette) ctx.stroke();

    // 炭治郎市松格子纹细节 / 善逸三角纹细节
    if (!isSilhouette && kind === "tanjiro") {
      ctx.fillStyle = "#090d12";
      ctx.fillRect(-38 - flutter * 0.3, torsoTopY + 14, 12, 10);
      ctx.fillRect(-26 - flutter * 0.2, torsoTopY + 24, 10, 10);
    } else if (!isSilhouette && kind === "zenitsu") {
      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.moveTo(-36 - flutter * 0.4, torsoTopY + 18);
      ctx.lineTo(-28 - flutter * 0.4, torsoTopY + 26);
      ctx.lineTo(-42 - flutter * 0.4, torsoTopY + 26);
      ctx.fill();
    }
    ctx.restore();

    // 双腿弓步/飞踢动作
    ctx.strokeStyle = isSilhouette ? auraColor : "#0f172a";
    ctx.lineWidth = 10;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    // 前腿
    ctx.beginPath();
    ctx.moveTo(4, hipY);
    ctx.lineTo(24, hipY + lerp(22, 10, crouch));
    ctx.lineTo(18, hipY + lerp(48, 28, crouch));
    ctx.stroke();
    // 后腿蹬地
    ctx.beginPath();
    ctx.moveTo(-6, hipY);
    ctx.lineTo(-26, hipY + lerp(18, 14, crouch));
    ctx.lineTo(-44, hipY + lerp(44, 28, crouch));
    ctx.stroke();

    // 躯干
    ctx.beginPath();
    ctx.moveTo(0, hipY);
    ctx.lineTo(6, torsoTopY);
    ctx.lineWidth = 16;
    ctx.strokeStyle = isSilhouette ? auraColor : (kind === "inosuke" ? "#e2b49a" : "#111827");
    ctx.stroke();

    // 头部与发型 / 猪头面具
    ctx.save();
    ctx.translate(10, torsoTopY - 12);
    ctx.fillStyle = isSilhouette ? auraColor : (kind === "inosuke" ? "#9ca3af" : "#1f2937");
    ctx.beginPath();
    ctx.arc(0, 0, 13, 0, Math.PI * 2);
    ctx.fill();

    if (!isSilhouette) {
      if (kind === "zenitsu") {
        // 黄金刺猬头发 + 发光眉眼
        ctx.fillStyle = "#fbbf24";
        ctx.beginPath();
        ctx.moveTo(-14, -4);
        ctx.lineTo(-10, -17);
        ctx.lineTo(0, -15);
        ctx.lineTo(11, -18);
        ctx.lineTo(16, -3);
        ctx.lineTo(8, 2);
        ctx.closePath();
        ctx.fill();
      } else if (kind === "tanjiro") {
        // 红棕色刺发 + 日轮花牌耳饰
        ctx.fillStyle = "#7f1d1d";
        ctx.beginPath();
        ctx.moveTo(-14, -2);
        ctx.lineTo(-8, -16);
        ctx.lineTo(3, -15);
        ctx.lineTo(14, -12);
        ctx.lineTo(11, 2);
        ctx.closePath();
        ctx.fill();
        ctx.fillStyle = "#f8fafc";
        ctx.fillRect(-8, 4, 4, 9);
      } else if (kind === "inosuke") {
        // 灰野猪耳+青眼+獠牙
        ctx.fillStyle = "#4b5563";
        ctx.beginPath();
        ctx.moveTo(-8, -10); ctx.lineTo(-15, -22); ctx.lineTo(-2, -13);
        ctx.moveTo(4, -12); ctx.lineTo(10, -23); ctx.lineTo(12, -10);
        ctx.fill();
        ctx.fillStyle = "#38bdf8";
        ctx.beginPath(); ctx.arc(7, -1, 3.2, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#f8fafc";
        ctx.beginPath(); ctx.moveTo(11, 4); ctx.lineTo(18, 0); ctx.lineTo(13, 8); ctx.fill();
      }
    }
    // 锐利发光视线点
    ctx.fillStyle = "#ffffff";
    ctx.shadowBlur = 10;
    ctx.shadowColor = auraColor;
    ctx.beginPath();
    ctx.ellipse(7, -1, 4, 1.8, -0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // 挥刀手臂与日轮刀（伊之助双刀，其他单刀）
    function drawBladeArm(angle, isSecond) {
      ctx.save();
      ctx.translate(6, torsoTopY + 6);
      ctx.rotate(angle);
      ctx.strokeStyle = isSilhouette ? auraColor : (kind === "inosuke" ? "#e2b49a" : "#111827");
      ctx.lineWidth = 7;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(24, 2);
      ctx.stroke();

      // 刀柄与护手
      ctx.translate(24, 2);
      ctx.strokeStyle = "#fbbf24";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(0, -6); ctx.lineTo(0, 6);
      ctx.stroke();

      // 日轮刀锋与强发光刀气
      ctx.shadowBlur = 18;
      ctx.shadowColor = auraColor;
      ctx.strokeStyle = bladeColor;
      ctx.lineWidth = isSecond ? 3.5 : 4.5;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      if (kind === "inosuke") {
        // 锯齿缺口刀刃
        for (var s = 8; s <= 76; s += 11) {
          ctx.lineTo(s, (s % 22 === 0) ? -3 : 1);
        }
      } else {
        ctx.quadraticCurveTo(44, -6, 86, -2);
      }
      ctx.stroke();

      // 刀尖高光剑芒
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.6;
      ctx.stroke();
      ctx.restore();
    }

    drawBladeArm(slashAngle, false);
    if (kind === "inosuke") {
      drawBladeArm(-slashAngle - 0.55, true);
    }

    ctx.restore();
  }

  // 祢豆子真实 6 部件高清骨骼演武渲染（若资源未就绪自动降级矢量版）
  function drawNezukoBonesActor(ctx, imgs, opts) {
    var x = opts.x || 0, y = opts.y || 0;
    var scale = opts.scale || 1;
    var dir = opts.dir || 1;
    var kickAngle = opts.kickAngle || 0;
    var alpha = opts.alpha !== undefined ? opts.alpha : 1;
    var isSilhouette = !!opts.isSilhouette;

    var head = imgs && imgs.nezuko_bone_head;
    var torso = imgs && imgs.nezuko_bone_torso;
    var armL = imgs && imgs.nezuko_bone_arm_l;
    var armR = imgs && imgs.nezuko_bone_arm_r;
    var legL = imgs && imgs.nezuko_bone_leg_l;
    var legR = imgs && imgs.nezuko_bone_leg_r;

    if (!imgReady(head) || !imgReady(torso)) {
      drawFighterActor(ctx, "nezuko", {
        x: x, y: y, scale: scale, dir: dir,
        lean: opts.lean || 0.25, slashAngle: kickAngle, crouch: opts.crouch || 0.3,
        alpha: alpha, auraColor: "#f472b6", bladeColor: "#fb7185",
        phase: opts.phase || 0, isSilhouette: isSilhouette
      });
      return;
    }

    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(x, y);
    ctx.scale(dir * scale * 0.72, scale * 0.72);
    ctx.rotate(opts.lean || 0);

    if (isSilhouette) {
      ctx.filter = "brightness(1.8) hue-rotate(-10deg) drop-shadow(0 0 12px #f472b6)";
    } else {
      ctx.shadowBlur = 18;
      ctx.shadowColor = "#ec4899";
    }

    // 腿部（右腿飞踢抬起）
    if (imgReady(legL)) {
      ctx.save();
      ctx.translate(-14, 34);
      ctx.rotate(-0.35 + (opts.phase || 0) * 0.2);
      ctx.drawImage(legL, -21, 0, 42, 55);
      ctx.restore();
    }
    if (imgReady(legR)) {
      ctx.save();
      ctx.translate(16, 28);
      ctx.rotate(kickAngle);
      ctx.drawImage(legR, -21, -8, 42, 55);
      // 爆血足底火焰拖尾
      ctx.strokeStyle = "#fb7185";
      ctx.lineWidth = 6;
      ctx.beginPath(); ctx.arc(0, 44, 16, 0, Math.PI * 1.4); ctx.stroke();
      ctx.restore();
    }

    // 左臂后展
    if (imgReady(armL)) {
      ctx.save();
      ctx.translate(-26, -24);
      ctx.rotate(-0.6 - Math.sin((opts.phase || 0) * 10) * 0.3);
      ctx.drawImage(armL, -37, -10, 75, 105);
      ctx.restore();
    }

    // 躯干
    ctx.drawImage(torso, -46, -42, 92, 115);

    // 右臂利爪突刺
    if (imgReady(armR)) {
      ctx.save();
      ctx.translate(28, -22);
      ctx.rotate(opts.armAngle || 0.7);
      ctx.drawImage(armR, -36, -12, 73, 105);
      ctx.restore();
    }

    // 头部（前倾凶萌鬼化盯视）
    ctx.save();
    ctx.translate(0, -68);
    ctx.rotate(-0.08 + Math.sin((opts.phase || 0) * 8) * 0.06);
    ctx.drawImage(head, -96, -110, 193, 180);
    ctx.restore();

    ctx.restore();
  }

  // 高燃斜切原画 Cut-in 漫画条（使用高清原画立绘 + 速度线 + 日文/汉字大字爆发）
  function drawCutInBanner(ctx, W, H, img, progress, opts) {
    if (progress <= 0 || progress >= 1) return;
    var enter = easeOutCubic(smoothStep(0, 0.22, progress));
    var exit = 1 - smoothStep(0.78, 1.0, progress);
    var open = enter * exit;
    if (open <= 0.01) return;

    var bandH = Math.min(H * 0.44, 230) * open;
    var cy = (opts.yRatio || 0.47) * H;
    var tilt = opts.tilt !== undefined ? opts.tilt : -0.11;
    var glow = opts.glow || "#fbbf24";
    var slideX = (1 - enter) * W * 0.45 * (opts.fromRight ? 1 : -1);

    ctx.save();
    ctx.translate(W * 0.5 + slideX, cy);
    ctx.rotate(tilt);

    // 外框发光白边剪切条
    var stripW = W * 1.35;
    ctx.beginPath();
    ctx.rect(-stripW * 0.5, -bandH * 0.5, stripW, bandH);
    ctx.save();
    ctx.clip();

    // 暗底 + 原画大图极速平移推镜特写
    ctx.fillStyle = "#05070c";
    ctx.fillRect(-stripW * 0.5, -bandH * 0.5, stripW, bandH);

    if (imgReady(img)) {
      var zoom = 1.18 + progress * 0.16;
      var drawW = Math.max(W * 0.9, bandH * (img.naturalWidth / img.naturalHeight)) * zoom;
      var drawH = drawW * (img.naturalHeight / img.naturalWidth);
      var panX = (opts.fromRight ? -1 : 1) * (progress - 0.5) * 48;
      ctx.globalAlpha = 0.95;
      ctx.drawImage(img, -drawW * 0.5 + panX, -drawH * 0.42, drawW, drawH);
    }

    // 动态横向高速白光速度线刷屏
    ctx.globalAlpha = 0.32;
    ctx.strokeStyle = "#ffffff";
    for (var i = 0; i < 18; i++) {
      var ly = -bandH * 0.45 + (i / 18) * bandH * 0.9;
      var lx = ((progress * 1800 + i * 173) % (stripW)) - stripW * 0.5;
      ctx.lineWidth = (i % 3 === 0) ? 2.5 : 1;
      ctx.beginPath();
      ctx.moveTo(lx, ly);
      ctx.lineTo(lx + 160, ly);
      ctx.stroke();
    }

    // 炫目渐变压暗边缘增强可读性
    var grad = ctx.createLinearGradient(-stripW * 0.35, 0, stripW * 0.35, 0);
    grad.addColorStop(0, "rgba(0,0,0,0.72)");
    grad.addColorStop(0.35, "rgba(0,0,0,0.08)");
    grad.addColorStop(0.65, "rgba(0,0,0,0.08)");
    grad.addColorStop(1, "rgba(0,0,0,0.75)");
    ctx.fillStyle = grad;
    ctx.globalAlpha = 1;
    ctx.fillRect(-stripW * 0.5, -bandH * 0.5, stripW, bandH);

    // 毛笔书法招式标题切入
    if (opts.title) {
      ctx.font = "900 " + Math.round(clamp(bandH * 0.24, 22, 48)) + "px 'KaiTi','STKaiti','Microsoft YaHei UI',sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.shadowBlur = 18;
      ctx.shadowColor = glow;
      ctx.fillStyle = "#ffffff";
      ctx.fillText(opts.title, -W * 0.42, bandH * 0.16);
      if (opts.sub) {
        ctx.font = "700 " + Math.round(clamp(bandH * 0.09, 12, 16)) + "px sans-serif";
        ctx.fillStyle = glow;
        ctx.fillText(opts.sub, -W * 0.42, -bandH * 0.16);
      }
    }
    ctx.restore();

    // 漫画分割框上下锐利白金边框
    ctx.strokeStyle = "#ffffff";
    ctx.shadowBlur = 16;
    ctx.shadowColor = glow;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(-stripW * 0.5, -bandH * 0.5);
    ctx.lineTo(stripW * 0.5, -bandH * 0.5);
    ctx.moveTo(-stripW * 0.5, bandH * 0.5);
    ctx.lineTo(stripW * 0.5, bandH * 0.5);
    ctx.stroke();

    ctx.restore();
  }

  // 全屏大招剑气斩裂线（Slash Tear + Spatter）
  function drawSlashArc(ctx, x1, y1, cx, cy, x2, y2, width, colorCore, colorGlow, progress) {
    if (progress <= 0 || progress >= 1) return;
    var fade = 1 - smoothStep(0.45, 1.0, progress);
    var head = easeOutCubic(smoothStep(0, 0.35, progress));
    ctx.save();
    ctx.globalAlpha = fade;
    ctx.lineCap = "round";
    ctx.shadowBlur = 26;
    ctx.shadowColor = colorGlow;
    ctx.strokeStyle = colorGlow;
    ctx.lineWidth = width * (1.5 - progress * 0.6);

    var hx = lerp(x1, x2, head);
    var hy = lerp(y1, y2, head);
    var hcx = lerp(x1, cx, head);
    var hcy = lerp(y1, cy, head);

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo(hcx, hcy, hx, hy);
    ctx.stroke();

    ctx.shadowBlur = 6;
    ctx.shadowColor = "#ffffff";
    ctx.strokeStyle = colorCore;
    ctx.lineWidth = Math.max(2, width * 0.36);
    ctx.stroke();
    ctx.restore();
  }

  // 浮世绘水龙涡流曲线（炭治郎核心视觉）
  function drawWaterFlowVortex(ctx, x1, y1, cx, cy, x2, y2, progress, isFire) {
    if (progress <= 0) return;
    var tail = smoothStep(0.35, 1.0, progress);
    var steps = 28;
    ctx.save();
    var cGlow = isFire ? "#fb923c" : "#0ea5e9";
    var cMid = isFire ? "#ef4444" : "#38bdf8";
    var cFoam = isFire ? "#fef08a" : "#e0f2fe";

    for (var layer = 0; layer < 2; layer++) {
      ctx.beginPath();
      for (var i = 0; i <= steps; i++) {
        var s = lerp(tail, clamp(progress * 1.15, 0, 1), i / steps);
        var inv = 1 - s;
        var px = inv * inv * x1 + 2 * inv * s * cx + s * s * x2;
        var py = inv * inv * y1 + 2 * inv * s * cy + s * s * y2;
        var wave = Math.sin(s * 18 + progress * 12 + layer * 1.8) * (layer === 0 ? 12 : 7);
        px += wave * 0.6;
        py += wave;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.lineCap = "round";
      ctx.shadowBlur = layer === 0 ? 24 : 8;
      ctx.shadowColor = cGlow;
      ctx.strokeStyle = layer === 0 ? cMid : cFoam;
      ctx.lineWidth = (layer === 0 ? 22 : 7) * (1 - progress * 0.35);
      ctx.globalAlpha = (1 - smoothStep(0.75, 1.0, progress)) * (layer === 0 ? 0.85 : 0.95);
      ctx.stroke();
    }
    ctx.restore();
  }

  // 血鬼术·爆血 火焰彼岸花莲爆裂
  function drawBloodLotus(ctx, cx, cy, radius, rot, progress) {
    if (progress <= 0 || progress >= 1) return;
    var r = radius * easeOutCubic(progress);
    var alpha = 1 - smoothStep(0.55, 1.0, progress);
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(rot + progress * 0.8);
    ctx.globalAlpha = alpha;
    ctx.shadowBlur = 20;
    ctx.shadowColor = "#ec4899";

    var petals = 8;
    for (var i = 0; i < petals; i++) {
      ctx.save();
      ctx.rotate((i / petals) * Math.PI * 2);
      ctx.fillStyle = i % 2 === 0 ? "#f43f5e" : "#f472b6";
      ctx.beginPath();
      ctx.moveTo(0, r * 0.15);
      ctx.quadraticCurveTo(r * 0.25, r * 0.55, 0, r);
      ctx.quadraticCurveTo(-r * 0.25, r * 0.55, 0, r * 0.15);
      ctx.fill();
      ctx.restore();
    }
    ctx.fillStyle = "#fff1f2";
    ctx.beginPath();
    ctx.arc(0, 0, r * 0.16, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // 动漫角色“终结收招战魂切镜”（在终结段以斜切高光菱形透出高清立绘与呼吸余晖）
  function drawFinisherPortrait(ctx, W, H, img, glowColor, title, p) {
    if (!imgReady(img)) return;
    var enter = easeOutCubic(clamp(p * 1.6, 0, 1));
    var cardW = Math.min(W * 0.42, 340);
    var cardH = Math.min(H * 0.48, 220);
    var cx = W * 0.64;
    var cy = H * 0.47;
    ctx.save();
    ctx.globalAlpha = enter * 0.94;
    ctx.translate(cx + (1 - enter) * 60, cy);
    ctx.transform(1, 0, -0.14, 1, 0, 0);

    ctx.beginPath();
    ctx.rect(-cardW * 0.5, -cardH * 0.5, cardW, cardH);
    ctx.save();
    ctx.clip();
    var iw = img.naturalWidth, ih = img.naturalHeight;
    var sc = Math.max(cardW * 1.15 / iw, cardH * 1.15 / ih) * (1.06 - enter * 0.04);
    var dw = iw * sc, dh = ih * sc;
    ctx.drawImage(img, -dw * 0.5, -dh * 0.46, dw, dh);
    var vGrad = ctx.createLinearGradient(0, -cardH * 0.5, 0, cardH * 0.5);
    vGrad.addColorStop(0, "rgba(0,0,0,0.08)");
    vGrad.addColorStop(1, "rgba(0,0,0,0.75)");
    ctx.fillStyle = vGrad;
    ctx.fillRect(-cardW * 0.5, -cardH * 0.5, cardW, cardH);
    ctx.restore();

    ctx.strokeStyle = glowColor;
    ctx.shadowBlur = 22;
    ctx.shadowColor = glowColor;
    ctx.lineWidth = 3;
    ctx.strokeRect(-cardW * 0.5, -cardH * 0.5, cardW, cardH);

    if (title) {
      ctx.transform(1, 0, 0.14, 1, 0, 0);
      ctx.font = "900 " + Math.round(clamp(W * 0.02, 14, 20)) + "px 'KaiTi','STKaiti','Microsoft YaHei UI',sans-serif";
      ctx.textAlign = "right";
      ctx.fillStyle = "#ffffff";
      ctx.fillText(title, cardW * 0.44, cardH * 0.40);
    }
    ctx.restore();
  }

  // 全明星结尾：4 人动态倾斜动漫漫画分镜同屏集合
  function drawQuartetMangaFinish(ctx, W, H, imgs, progress) {
    var p = easeOutCubic(clamp(progress, 0, 1));
    var chars = [
      { img: imgs.tanjiro, color: "#38bdf8", name: "炭治郎 · 水火神乐", dx: -0.36 },
      { img: imgs.zenitsu, color: "#fbbf24", name: "善逸 · 霹雳一闪", dx: -0.12 },
      { img: imgs.inosuke, color: "#60a5fa", name: "伊之助 · 狂牙裂斩", dx: 0.12 },
      { img: imgs.nezuko, color: "#f472b6", name: "祢豆子 · 血鬼术爆血", dx: 0.36 }
    ];
    var panelW = W * 0.21;
    var panelH = H * 0.62;
    var skew = -0.14;

    ctx.save();
    for (var i = 0; i < chars.length; i++) {
      var item = chars[i];
      var enterDelay = i * 0.08;
      var localP = easeOutCubic(clamp((p - enterDelay) / 0.65, 0, 1));
      if (localP <= 0) continue;

      var targetX = W * (0.5 + item.dx);
      var offsetY = (i % 2 === 0 ? -1 : 1) * (1 - localP) * H * 0.45;
      var cy = H * 0.48 + offsetY;

      ctx.save();
      ctx.translate(targetX, cy);
      ctx.transform(1, 0, skew, 1, 0, 0);
      ctx.globalAlpha = localP;

      ctx.beginPath();
      ctx.rect(-panelW * 0.5, -panelH * 0.5, panelW, panelH);
      ctx.save();
      ctx.clip();
      ctx.fillStyle = "#080b14";
      ctx.fillRect(-panelW * 0.5, -panelH * 0.5, panelW, panelH);

      if (imgReady(item.img)) {
        var iw = item.img.naturalWidth, ih = item.img.naturalHeight;
        var scale = Math.max(panelW * 1.28 / iw, panelH * 1.05 / ih);
        var dw = iw * scale, dh = ih * scale;
        ctx.drawImage(item.img, -dw * 0.5, -dh * 0.48, dw, dh);
      }

      var overlay = ctx.createLinearGradient(0, -panelH * 0.5, 0, panelH * 0.5);
      overlay.addColorStop(0, "rgba(0,0,0,0.15)");
      overlay.addColorStop(0.65, "rgba(0,0,0,0.08)");
      overlay.addColorStop(1, "rgba(0,0,0,0.88)");
      ctx.fillStyle = overlay;
      ctx.fillRect(-panelW * 0.5, -panelH * 0.5, panelW, panelH);
      ctx.restore();

      ctx.strokeStyle = item.color;
      ctx.shadowBlur = 14;
      ctx.shadowColor = item.color;
      ctx.lineWidth = 2.5;
      ctx.strokeRect(-panelW * 0.5, -panelH * 0.5, panelW, panelH);

      ctx.transform(1, 0, -skew, 1, 0, 0);
      ctx.fillStyle = "#ffffff";
      ctx.font = "800 " + Math.round(clamp(W * 0.015, 11, 15)) + "px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(item.name, -panelH * 0.14 * skew, panelH * 0.42);
      ctx.restore();
    }
    ctx.restore();
  }

  // 主挂载入口：同时被 Electron 启动遮罩与 Studio React 预览组件共同调用
  function mount(container, options) {
    if (!container) return null;
    injectStyles();

    var opts = options || {};
    var charKey = CHAR_META[opts.character] ? opts.character : "nezuko";
    var meta = CHAR_META[charKey];
    var durationMs = opts.durationMs || 5600;
    var loop = opts.loop !== undefined ? !!opts.loop : true;
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
      "<div class='ag-kt-pill'>" + meta.breath + "</div>";

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

    var ctx = canvas.getContext("2d");
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

    // 剧本运行时瞬态系统（残影队列 / 震屏 / 顿帧 Impact / 爆裂粒子）
    var state = {
      startAt: performance.now(),
      shake: 0,
      impactTimer: 0,
      lastBoltAt: -1,
      activeBolts: [],
      trails: [],
      particles: [],
      lotuses: [],
      lastImpactBucket: -1,
      rafId: 0,
      destroyed: false
    };

    function spawnParticles(px, py, count, color, speed, sizeBase) {
      for (var i = 0; i < count; i++) {
        var ang = Math.random() * Math.PI * 2;
        var spd = speed * (0.35 + Math.random() * 0.9);
        state.particles.push({
          x: px, y: py,
          vx: Math.cos(ang) * spd,
          vy: Math.sin(ang) * spd,
          life: 1,
          decay: 0.018 + Math.random() * 0.025,
          r: (sizeBase || 3) * (0.6 + Math.random() * 1.1),
          color: color
        });
      }
    }

    function triggerImpact(uKey, shakeVal, flashMs) {
      if (state.lastImpactBucket === uKey) return;
      state.lastImpactBucket = uKey;
      state.shake = Math.max(state.shake, shakeVal);
      state.impactTimer = flashMs;
    }

    function resetEpisode() {
      state.startAt = performance.now();
      state.shake = 0;
      state.impactTimer = 0;
      state.lastBoltAt = -1;
      state.activeBolts = [];
      state.trails = [];
      state.particles = [];
      state.lotuses = [];
      state.lastImpactBucket = -1;
    }

    function renderFrame(now) {
      if (state.destroyed) return;
      syncSize();

      var elapsed = now - state.startAt;
      if (loop && elapsed >= durationMs) {
        resetEpisode();
        elapsed = 0;
      }
      var u = clamp(elapsed / durationMs, 0, 1);
      var tSec = elapsed / 1000;

      // 更新 HUD 招式步序与进度
      var sIdx = Math.min(steps.length - 1, Math.floor(u * steps.length));
      if (stepEl && stepEl.textContent !== steps[sIdx]) stepEl.textContent = steps[sIdx];
      var curAct = meta.acts[0];
      for (var ai = 0; ai < meta.acts.length; ai++) {
        if (u >= meta.acts[ai].at) curAct = meta.acts[ai];
      }
      if (moveEl && moveEl.textContent !== curAct.move) moveEl.textContent = curAct.move;
      if (fillEl) fillEl.style.width = (u * 100).toFixed(1) + "%";

      var isClimax = (u >= 0.45 && u <= 0.85);
      if (rootEl.classList.contains("climax") !== isClimax) {
        rootEl.classList.toggle("climax", isClimax);
      }

      // 物理更新：粒子 & 震屏衰减
      state.shake *= 0.86;
      if (state.shake < 0.2) state.shake = 0;
      if (state.impactTimer > 0) state.impactTimer -= 16.6;

      for (var pi = state.particles.length - 1; pi >= 0; pi--) {
        var pt = state.particles[pi];
        pt.x += pt.vx;
        pt.y += pt.vy;
        pt.vx *= 0.96;
        pt.vy *= 0.96;
        pt.life -= pt.decay;
        if (pt.life <= 0) state.particles.splice(pi, 1);
      }

      ctx.save();
      ctx.scale(dpr, dpr);

      // 相机震屏偏移
      var sx = state.shake ? (Math.random() - 0.5) * state.shake * 2 : 0;
      var sy = state.shake ? (Math.random() - 0.5) * state.shake * 2 : 0;
      ctx.translate(sx, sy);

      var intensity = isClimax ? 0.92 : (u > 0.2 ? 0.58 : 0.2);
      drawDynamicBattleStage(ctx, W, H, tSec, charKey, intensity);

      var unit = Math.min(W, H) / 480;

      // ==================== 5 大专属动漫打斗导演剧本 ====================
      if (charKey === "tanjiro") {
        if (u < 0.18) {
          // 幕1：静水蹲身蓄力 + 呼出白雾
          var p1 = u / 0.18;
          drawFighterActor(ctx, "tanjiro", {
            x: W * 0.26, y: H * 0.56, scale: 1.28 * unit, dir: 1,
            lean: 0.22, slashAngle: -1.9 + p1 * 0.3, crouch: 0.7,
            auraColor: "#38bdf8", bladeColor: "#bae6fd", phase: tSec
          });
          if (Math.random() < 0.35) spawnParticles(W * 0.28, H * 0.45, 1, "rgba(224,242,254,0.65)", 1.6, 5);
        } else if (u < 0.52) {
          // 幕2：拾之型 生生流转 3 连高速穿梭盘旋水龙斩
          var p2 = (u - 0.18) / 0.34;
          var seg = Math.floor(p2 * 3);
          var sub = (p2 * 3) % 1;
          var pts = [
            [0.18, 0.62, 0.78, 0.36, 1],
            [0.80, 0.36, 0.22, 0.66, -1],
            [0.20, 0.64, 0.72, 0.44, 1]
          ];
          var cur = pts[Math.min(2, seg)];
          var ax = W * lerp(cur[0], cur[2], easeOutCubic(sub));
          var ay = H * lerp(cur[1], cur[3], easeOutCubic(sub)) - Math.sin(sub * Math.PI) * 55 * unit;

          drawWaterFlowVortex(ctx, W * cur[0], H * cur[1], W * 0.5, H * (seg === 1 ? 0.18 : 0.78), W * cur[2], H * cur[3], sub, false);
          drawSlashArc(ctx, W * cur[0], H * cur[1], W * 0.5, H * 0.45, W * cur[2], H * cur[3], 20 * unit, "#ffffff", "#0ea5e9", sub);

          if (Math.random() < 0.75) {
            state.trails.push({ kind: "tanjiro", x: ax, y: ay, dir: cur[4], lean: 0.45, slashAngle: -0.4 + sub * 3.1, life: 1, color: "#38bdf8" });
            spawnParticles(ax, ay, 2, "#7dd3fc", 4.5, 3);
          }
          if (seg === 1 && sub < 0.12) triggerImpact(101, 8, 0);
          if (seg === 2 && sub < 0.12) triggerImpact(102, 10, 40);

          drawFighterActor(ctx, "tanjiro", {
            x: ax, y: ay, scale: 1.35 * unit, dir: cur[4],
            lean: 0.48, slashAngle: -0.8 + sub * 3.8, crouch: 0.25,
            auraColor: "#38bdf8", bladeColor: "#e0f2fe", phase: tSec
          });
        } else if (u < 0.82) {
          // 幕3：火之神神乐 Cut-in 睁眼觉醒 -> 赫刀日轮圆舞大斩
          var p3 = (u - 0.52) / 0.30;
          if (p3 < 0.36) {
            drawCutInBanner(ctx, W, H, imgs.tanjiro, p3 / 0.36, {
              title: "火之神神乐 · 日晕之龙", sub: "HINOKAMI KAGURA", glow: "#f97316", tilt: -0.09
            });
          } else {
            var k3 = (p3 - 0.36) / 0.64;
            if (k3 < 0.12) triggerImpact(103, 18, 65);
            drawWaterFlowVortex(ctx, W * 0.1, H * 0.72, W * 0.48, H * 0.14, W * 0.92, H * 0.58, k3, true);
            drawSlashArc(ctx, W * 0.12, H * 0.76, W * 0.52, H * 0.12, W * 0.94, H * 0.48, 36 * unit, "#fef08a", "#ef4444", k3);
            var tx = W * lerp(0.2, 0.76, easeOutCubic(k3));
            var ty = H * (0.52 - Math.sin(k3 * Math.PI) * 0.22);
            if (Math.random() < 0.85) {
              state.trails.push({ kind: "tanjiro", x: tx, y: ty, dir: 1, lean: 0.55, slashAngle: k3 * 6.2, life: 1, color: "#fb923c" });
              spawnParticles(tx, ty, 3, "#fb923c", 6, 3.5);
            }
            drawFighterActor(ctx, "tanjiro", {
              x: tx, y: ty, scale: 1.48 * unit, dir: 1,
              lean: 0.55, slashAngle: -2.4 + k3 * 5.6, crouch: 0.2,
              auraColor: "#f97316", bladeColor: "#fef08a", phase: tSec
            });
          }
        } else {
          // 幕4：余烬散落、帅气收刀定格 + 战魂特写融合
          var p4 = (u - 0.82) / 0.18;
          if (Math.random() < 0.55) spawnParticles(Math.random() * W, H * 0.82, 1, "#fb923c", 2.4, 2.8);
          drawFinisherPortrait(ctx, W, H, imgs.tanjiro, "#38bdf8", "水火神乐 · 碧罗之天", p4);
          drawFighterActor(ctx, "tanjiro", {
            x: W * 0.30, y: H * 0.56, scale: 1.38 * unit, dir: 1,
            lean: lerp(0.3, 0.04, easeOutCubic(p4)), slashAngle: lerp(1.8, 2.5, easeOutCubic(p4)), crouch: 0.35,
            auraColor: "#38bdf8", bladeColor: "#e0f2fe", phase: tSec
          });
        }
      } else if (charKey === "zenitsu") {
        if (u < 0.22) {
          // 幕1：雷之呼吸 居合低蹲屏息（雨滴慢动作 + 脚底爆裂电弧）
          var zp1 = u / 0.22;
          // 悬浮雨滴
          ctx.save();
          ctx.strokeStyle = "rgba(186,230,253,0.45)";
          ctx.lineWidth = 1.4;
          for (var r = 0; r < 24; r++) {
            var rx = ((r * 97) % 100) * 0.01 * W;
            var ry = (((r * 61) % 100) * 0.01 * H + zp1 * 18) % H;
            ctx.beginPath(); ctx.moveTo(rx, ry); ctx.lineTo(rx - 2, ry + 14); ctx.stroke();
          }
          ctx.restore();
          drawFighterActor(ctx, "zenitsu", {
            x: W * 0.24, y: H * 0.62, scale: 1.35 * unit, dir: 1,
            lean: 0.45, slashAngle: 2.75, crouch: 0.92,
            auraColor: "#fbbf24", bladeColor: "#fef08a", phase: tSec
          });
          if (zp1 > 0.4 && Math.random() < 0.5) {
            var blt = buildLightning(W * 0.24, H * 0.65, W * (0.1 + Math.random() * 0.35), H * (0.45 + Math.random() * 0.3), 28, 3);
            drawLightningSegs(ctx, blt, "#ffffff", "#fbbf24", 1.8);
          }
        } else if (u < 0.58) {
          // 幕2：霹雳一闪 神速六连 Z字全屏折返瞬杀
          var zp2 = (u - 0.22) / 0.36;
          var hops = [
            [0.14, 0.72], [0.84, 0.34], [0.22, 0.26], [0.86, 0.68], [0.18, 0.48], [0.78, 0.22], [0.30, 0.56]
          ];
          var hIdx = Math.min(5, Math.floor(zp2 * 6));
          var hSub = (zp2 * 6) % 1;
          var pA = hops[hIdx], pB = hops[hIdx + 1];

          // 绘制已经劈过的金雷折痕网
          for (var hi = 0; hi <= hIdx; hi++) {
            var pa = hops[hi], pb = hops[hi + 1];
            var endP = hi === hIdx ? easeOutCubic(hSub) : 1;
            var bSegs = buildLightning(W * pa[0], H * pa[1], W * lerp(pa[0], pb[0], endP), H * lerp(pa[1], pb[1], endP), 26, 3);
            drawLightningSegs(ctx, bSegs, "#ffffff", "#f59e0b", hi === hIdx ? 3.8 : 1.6);
          }
          var zx = W * lerp(pA[0], pB[0], easeOutCubic(hSub));
          var zy = H * lerp(pA[1], pB[1], easeOutCubic(hSub));
          var zDir = pB[0] >= pA[0] ? 1 : -1;
          if (hSub < 0.16) {
            triggerImpact(200 + hIdx, 12, hIdx % 2 === 1 ? 45 : 0);
            state.trails.push({ kind: "zenitsu", x: zx, y: zy, dir: zDir, lean: 0.6, slashAngle: (hIdx % 2 ? -0.9 : 0.7), life: 1, color: "#fbbf24" });
            spawnParticles(zx, zy, 6, "#fef08a", 7, 3);
          }
          drawFighterActor(ctx, "zenitsu", {
            x: zx, y: zy, scale: 1.38 * unit, dir: zDir,
            lean: 0.62, slashAngle: -0.3 + hSub * 2.2, crouch: 0.45,
            auraColor: "#fbbf24", bladeColor: "#ffffff", phase: tSec
          });
        } else if (u < 0.84) {
          // 幕3：Cut-in 金瞳睁眼 + 火雷神天雷斜贯大斩
          var zp3 = (u - 0.58) / 0.26;
          if (zp3 < 0.38) {
            drawCutInBanner(ctx, W, H, imgs.zenitsu, zp3 / 0.38, {
              title: "霹雳一闪 · 火雷神！！", sub: "THUNDERCLAP AND FLASH // GOD SPEED", glow: "#fbbf24", tilt: -0.12, fromRight: true
            });
          } else {
            var zk = (zp3 - 0.38) / 0.62;
            if (zk < 0.12) triggerImpact(210, 22, 75);
            var megaBolt = buildLightning(W * 0.08, H * 0.85, W * 0.94, H * 0.16, 48, 4);
            drawLightningSegs(ctx, megaBolt, "#ffffff", "#fbbf24", 5.5);
            drawSlashArc(ctx, W * 0.06, H * 0.86, W * 0.48, H * 0.42, W * 0.94, H * 0.14, 34 * unit, "#ffffff", "#fbbf24", zk);
            drawFighterActor(ctx, "zenitsu", {
              x: W * lerp(0.18, 0.80, easeOutCubic(zk)), y: H * lerp(0.75, 0.28, easeOutCubic(zk)),
              scale: 1.52 * unit, dir: 1, lean: 0.66, slashAngle: -0.6, crouch: 0.4,
              auraColor: "#fbbf24", bladeColor: "#ffffff", phase: tSec
            });
          }
        } else {
          // 幕4：雷光汇聚静立咔哒归鞘 + 战魂特写
          var zp4 = (u - 0.84) / 0.16;
          drawFinisherPortrait(ctx, W, H, imgs.zenitsu, "#fbbf24", "雷之呼吸 · 霹雳一闪", zp4);
          drawFighterActor(ctx, "zenitsu", {
            x: W * 0.30, y: H * 0.56, scale: 1.38 * unit, dir: 1,
            lean: 0.08, slashAngle: lerp(0.4, 2.7, easeOutCubic(zp4)), crouch: 0.25,
            auraColor: "#fbbf24", bladeColor: "#fef08a", phase: tSec
          });
          if (zp4 > 0.3 && zp4 < 0.7) {
            ctx.save();
            ctx.strokeStyle = "#ffffff";
            ctx.shadowBlur = 16; ctx.shadowColor = "#fbbf24";
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.moveTo(W * 0.30 - 22, H * 0.54); ctx.lineTo(W * 0.30 + 34, H * 0.54);
            ctx.stroke();
            ctx.restore();
          }
        }
      } else if (charKey === "inosuke") {
        if (u < 0.22) {
          // 幕1：漆之型 空间识觉蓝色声呐脉冲锁定暗点
          var ip1 = u / 0.22;
          for (var w = 0; w < 3; w++) {
            var wp = (ip1 * 2.2 - w * 0.35);
            if (wp > 0 && wp < 1) {
              ctx.save();
              ctx.strokeStyle = "#60a5fa";
              ctx.globalAlpha = (1 - wp) * 0.75;
              ctx.lineWidth = 2.5;
              ctx.beginPath();
              ctx.ellipse(W * 0.5, H * 0.56, wp * W * 0.58, wp * H * 0.45, 0, 0, Math.PI * 2);
              ctx.stroke();
              ctx.restore();
            }
          }
          // 声呐扫到的目标红十字靶标
          if (ip1 > 0.45) {
            var tgs = [[0.22, 0.36], [0.78, 0.34], [0.28, 0.68], [0.76, 0.66]];
            ctx.save();
            ctx.strokeStyle = "#f43f5e"; ctx.lineWidth = 2;
            for (var ti = 0; ti < tgs.length; ti++) {
              var tx2 = W * tgs[ti][0], ty2 = H * tgs[ti][1];
              ctx.beginPath();
              ctx.arc(tx2, ty2, 16 * unit, 0, Math.PI * 2);
              ctx.moveTo(tx2 - 22 * unit, ty2); ctx.lineTo(tx2 + 22 * unit, ty2);
              ctx.moveTo(tx2, ty2 - 22 * unit); ctx.lineTo(tx2, ty2 + 22 * unit);
              ctx.stroke();
            }
            ctx.restore();
          }
          drawFighterActor(ctx, "inosuke", {
            x: W * 0.5, y: H * 0.58, scale: 1.35 * unit, dir: 1,
            lean: 0.25, slashAngle: 1.35, crouch: 0.78,
            auraColor: "#60a5fa", bladeColor: "#cbd5e1", phase: tSec
          });
        } else if (u < 0.56) {
          // 幕2：猪突猛进 双锯齿牙在锁定靶点间疯狂弹跳连斩
          var ip2 = (u - 0.22) / 0.34;
          var leg = Math.floor(ip2 * 4);
          var subI = (ip2 * 4) % 1;
          var route = [[0.5, 0.58], [0.22, 0.36], [0.78, 0.34], [0.28, 0.68], [0.76, 0.66]];
          var ra = route[Math.min(3, leg)], rb = route[Math.min(4, leg + 1)];
          var ix = W * lerp(ra[0], rb[0], easeOutCubic(subI));
          var iy = H * lerp(ra[1], rb[1], easeOutCubic(subI));
          var idir = rb[0] >= ra[0] ? 1 : -1;

          // 绘制 X 锯齿破空斩痕
          drawSlashArc(ctx, ix - 65 * unit, iy - 45 * unit, ix, iy, ix + 65 * unit, iy + 45 * unit, 16 * unit, "#ffffff", "#3b82f6", subI);
          drawSlashArc(ctx, ix + 65 * unit, iy - 45 * unit, ix, iy, ix - 65 * unit, iy + 45 * unit, 16 * unit, "#ffffff", "#60a5fa", subI);

          if (subI < 0.15) {
            triggerImpact(300 + leg, 11, leg === 3 ? 45 : 0);
            state.trails.push({ kind: "inosuke", x: ix, y: iy, dir: idir, lean: 0.55, slashAngle: subI * 5, life: 1, color: "#60a5fa" });
            spawnParticles(ix, iy, 6, "#93c5fd", 6.5, 3);
          }
          drawFighterActor(ctx, "inosuke", {
            x: ix, y: iy, scale: 1.38 * unit, dir: idir,
            lean: 0.52, slashAngle: -1.4 + tSec * 14, crouch: 0.35,
            auraColor: "#60a5fa", bladeColor: "#e2e8f0", phase: tSec
          });
        } else if (u < 0.84) {
          // 幕3：猪突猛进 Cut-in + 狂牙撕裂全屏 X 型双刃风暴
          var ip3 = (u - 0.56) / 0.28;
          if (ip3 < 0.38) {
            drawCutInBanner(ctx, W, H, imgs.inosuke, ip3 / 0.38, {
              title: "伍之牙 · 狂牙撕裂！！", sub: "BEAST BREATHING // CRAZY CUTTING", glow: "#60a5fa", tilt: 0.10
            });
          } else {
            var ik = (ip3 - 0.38) / 0.62;
            if (ik < 0.12) triggerImpact(310, 20, 70);
            drawSlashArc(ctx, W * 0.1, H * 0.18, W * 0.5, H * 0.5, W * 0.9, H * 0.84, 34 * unit, "#ffffff", "#3b82f6", ik);
            drawSlashArc(ctx, W * 0.9, H * 0.18, W * 0.5, H * 0.5, W * 0.1, H * 0.84, 34 * unit, "#ffffff", "#60a5fa", ik);
            drawFighterActor(ctx, "inosuke", {
              x: W * 0.5, y: H * lerp(0.32, 0.56, easeOutCubic(ik)), scale: 1.56 * unit, dir: 1,
              lean: 0.2, slashAngle: ik * 8, crouch: 0.25,
              auraColor: "#60a5fa", bladeColor: "#ffffff", phase: tSec
            });
          }
        } else {
          // 幕4：扛刀白气咆哮定格 + 战魂特写
          var ip4 = (u - 0.84) / 0.16;
          if (Math.random() < 0.55) spawnParticles(W * 0.32, H * 0.44, 1, "rgba(226,232,240,0.8)", 2.8, 4.5);
          drawFinisherPortrait(ctx, W, H, imgs.inosuke, "#60a5fa", "兽之呼吸 · 猪突猛进", ip4);
          drawFighterActor(ctx, "inosuke", {
            x: W * 0.30, y: H * 0.56, scale: 1.42 * unit, dir: 1,
            lean: -0.05, slashAngle: -2.2 + ip4 * 0.15, crouch: 0.2,
            auraColor: "#60a5fa", bladeColor: "#e2e8f0", phase: tSec
          });
        }
      } else if (charKey === "nezuko") {
        if (u < 0.22) {
          // 幕1：竹篮/木箱震颤轰然爆破 (`nezuko_basket` + `box_impact_shockwave`)
          var np1 = u / 0.22;
          if (np1 < 0.55) {
            var vib = Math.sin(tSec * 65) * 6 * np1;
            if (imgReady(imgs.nezuko)) {
              ctx.save();
              ctx.translate(W * 0.5 + vib, H * 0.5);
              ctx.scale(1 + np1 * 0.12, 1 - np1 * 0.08);
              ctx.drawImage(imgs.nezuko, -110 * unit, -74 * unit, 220 * unit, 148 * unit);
              ctx.restore();
            }
          } else {
            var burst = (np1 - 0.55) / 0.45;
            if (burst < 0.2) triggerImpact(401, 14, 40);
            if (imgReady(imgs.box_impact_shockwave)) {
              ctx.save();
              ctx.globalAlpha = 1 - burst;
              var sw = 260 * unit * (0.5 + burst * 1.8);
              ctx.drawImage(imgs.box_impact_shockwave, W * 0.5 - sw * 0.5, H * 0.5 - sw * 0.5, sw, sw);
              ctx.restore();
            }
            drawNezukoBonesActor(ctx, imgs, {
              x: W * 0.5, y: H * lerp(0.62, 0.48, easeOutCubic(burst)),
              scale: 1.35 * unit, dir: 1, kickAngle: -0.8 * burst, armAngle: 0.4, phase: tSec
            });
          }
        } else if (u < 0.52) {
          // 幕2：真实骨骼空翻连踢 + 三连血爪撕裂屏幕
          var np2 = (u - 0.22) / 0.30;
          var nLeg = Math.floor(np2 * 3);
          var nSub = (np2 * 3) % 1;
          var nPts = [[0.24, 0.58, 1], [0.76, 0.40, -1], [0.34, 0.52, 1]];
          var curN = nPts[Math.min(2, nLeg)];
          var nx = W * curN[0] + curN[2] * nSub * 80 * unit;
          var ny = H * curN[1] - Math.sin(nSub * Math.PI) * 65 * unit;

          // 绯红三爪裂痕
          for (var cl = -1; cl <= 1; cl++) {
            drawSlashArc(ctx, nx - 70 * unit, ny + cl * 18 * unit - 35, nx, ny + cl * 18 * unit, nx + 80 * unit, ny + cl * 18 * unit + 30, 12 * unit, "#fff1f2", "#e11d48", nSub);
          }
          if (nSub < 0.16) {
            triggerImpact(410 + nLeg, 10, nLeg === 2 ? 40 : 0);
            state.trails.push({ kind: "nezuko", x: nx, y: ny, dir: curN[2], lean: 0.3, slashAngle: -1.1, life: 1, color: "#f472b6" });
            spawnParticles(nx, ny, 6, "#fb7185", 5.5, 3);
          }
          drawNezukoBonesActor(ctx, imgs, {
            x: nx, y: ny, scale: 1.4 * unit, dir: curN[2],
            lean: 0.28 * curN[2], kickAngle: -1.25 + nSub * 0.6, armAngle: -0.9 + nSub * 1.4, phase: tSec
          });
        } else if (u < 0.82) {
          // 幕3：Cut-in 觉醒 + 血鬼术·爆血全屏彼岸火莲狂爆
          var np3 = (u - 0.52) / 0.30;
          if (np3 < 0.35) {
            drawCutInBanner(ctx, W, H, imgs.nezuko, np3 / 0.35, {
              title: "血鬼术 · 爆血！！", sub: "BLOOD DEMON ART // EXPLODING BLOOD", glow: "#ec4899", tilt: -0.10
            });
          } else {
            var nk = (np3 - 0.35) / 0.65;
            if (nk < 0.12) {
              triggerImpact(420, 20, 70);
              state.lotuses = [
                [0.25, 0.42, 160, 0.2], [0.72, 0.38, 180, 0.9], [0.5, 0.52, 230, 0.0],
                [0.34, 0.70, 145, 0.6], [0.68, 0.66, 155, 1.1]
              ];
            }
            for (var li = 0; li < state.lotuses.length; li++) {
              var lt = state.lotuses[li];
              drawBloodLotus(ctx, W * lt[0], H * lt[1], lt[2] * unit, lt[3], clamp(nk * 1.2 - li * 0.06, 0, 1));
            }
            drawNezukoBonesActor(ctx, imgs, {
              x: W * 0.5, y: H * 0.52, scale: 1.46 * unit, dir: 1,
              lean: -0.08, kickAngle: -0.2, armAngle: -1.3, phase: tSec
            });
          }
        } else {
          // 幕4：樱炎轻飘守护收势 + 战魂特写
          var np4 = (u - 0.82) / 0.18;
          if (Math.random() < 0.55) spawnParticles(Math.random() * W, H * 0.85, 1, "#f472b6", 2.4, 3);
          drawFinisherPortrait(ctx, W, H, imgs.nezuko, "#ec4899", "血鬼术 · 爆血觉醒", np4);
          drawNezukoBonesActor(ctx, imgs, {
            x: W * 0.30, y: H * lerp(0.50, 0.56, easeOutCubic(np4)),
            scale: 1.38 * unit, dir: 1, lean: 0, kickAngle: 0.1, armAngle: 0.25, phase: tSec
          });
        }
      } else {
        // ==================== all：鬼灭全明星 4 连携合击大片 ====================
        if (u < 0.22) {
          // 幕1：炭治郎水龙前锋破壁
          var ap1 = u / 0.22;
          drawWaterFlowVortex(ctx, W * 0.1, H * 0.72, W * 0.48, H * 0.22, W * 0.88, H * 0.44, ap1, false);
          drawSlashArc(ctx, W * 0.12, H * 0.72, W * 0.5, H * 0.3, W * 0.86, H * 0.44, 24 * unit, "#ffffff", "#38bdf8", ap1);
          drawFighterActor(ctx, "tanjiro", {
            x: W * lerp(0.2, 0.76, easeOutCubic(ap1)), y: H * lerp(0.65, 0.42, easeOutCubic(ap1)),
            scale: 1.38 * unit, dir: 1, lean: 0.5, slashAngle: -0.6 + ap1 * 2.5, crouch: 0.3,
            auraColor: "#38bdf8", bladeColor: "#bae6fd", phase: tSec
          });
          if (ap1 > 0.75) triggerImpact(501, 10, 0);
        } else if (u < 0.44) {
          // 幕2：善逸霹雳一闪 3 折接力横穿
          var ap2 = (u - 0.22) / 0.22;
          var hopsA = [[0.85, 0.36], [0.16, 0.58], [0.84, 0.62], [0.24, 0.32]];
          var hA = Math.min(2, Math.floor(ap2 * 3));
          var hSubA = (ap2 * 3) % 1;
          var bA = buildLightning(W * hopsA[hA][0], H * hopsA[hA][1], W * hopsA[hA + 1][0], H * hopsA[hA + 1][1], 32, 3);
          drawLightningSegs(ctx, bA, "#ffffff", "#fbbf24", 4.2);
          drawFighterActor(ctx, "zenitsu", {
            x: W * lerp(hopsA[hA][0], hopsA[hA + 1][0], easeOutCubic(hSubA)),
            y: H * lerp(hopsA[hA][1], hopsA[hA + 1][1], easeOutCubic(hSubA)),
            scale: 1.42 * unit, dir: hopsA[hA + 1][0] >= hopsA[hA][0] ? 1 : -1,
            lean: 0.64, slashAngle: -0.2, crouch: 0.4, auraColor: "#fbbf24", bladeColor: "#ffffff", phase: tSec
          });
          if (hSubA < 0.18) triggerImpact(510 + hA, 12, hA === 2 ? 45 : 0);
        } else if (u < 0.64) {
          // 幕3：伊之助双牙狂旋撕裂 + 祢豆子飞踢协同破防
          var ap3 = (u - 0.44) / 0.20;
          drawSlashArc(ctx, W * 0.14, H * 0.24, W * 0.5, H * 0.5, W * 0.86, H * 0.76, 26 * unit, "#ffffff", "#60a5fa", ap3);
          drawSlashArc(ctx, W * 0.86, H * 0.24, W * 0.5, H * 0.5, W * 0.14, H * 0.76, 26 * unit, "#fff1f2", "#f472b6", ap3);
          drawFighterActor(ctx, "inosuke", {
            x: W * lerp(0.75, 0.36, easeOutCubic(ap3)), y: H * 0.44,
            scale: 1.35 * unit, dir: -1, lean: 0.45, slashAngle: ap3 * 9, crouch: 0.3,
            auraColor: "#60a5fa", bladeColor: "#e2e8f0", phase: tSec
          });
          drawNezukoBonesActor(ctx, imgs, {
            x: W * lerp(0.24, 0.62, easeOutCubic(ap3)), y: H * 0.56,
            scale: 1.32 * unit, dir: 1, lean: 0.2, kickAngle: -1.1 + ap3 * 0.8, armAngle: -0.7, phase: tSec
          });
          if (ap3 < 0.16) triggerImpact(520, 14, 0);
        } else if (u < 0.84) {
          // 幕4：四色呼吸螺旋中央合流爆炸 + Impact Frame
          var ap4 = (u - 0.64) / 0.20;
          if (ap4 < 0.16) triggerImpact(530, 24, 80);
          var quadColors = ["#38bdf8", "#fbbf24", "#60a5fa", "#f472b6"];
          for (var q = 0; q < 4; q++) {
            var angQ = (q / 4) * Math.PI * 2 + ap4 * 4.5;
            var rxQ = W * 0.5 + Math.cos(angQ) * 180 * unit * (1 - ap4 * 0.4);
            var ryQ = H * 0.5 + Math.sin(angQ) * 130 * unit * (1 - ap4 * 0.4);
            drawBloodLotus(ctx, rxQ, ryQ, 120 * unit, angQ, ap4);
            drawSlashArc(ctx, W * 0.5, H * 0.5, (W * 0.5 + rxQ) * 0.5, (H * 0.5 + ryQ) * 0.5 - 60, rxQ, ryQ, 22 * unit, "#ffffff", quadColors[q], ap4);
          }
          drawBloodLotus(ctx, W * 0.5, H * 0.5, 250 * unit, ap4 * 2, ap4);
        } else {
          // 幕5：四人高清斜切漫画分镜定格集结！！
          var ap5 = (u - 0.84) / 0.16;
          drawQuartetMangaFinish(ctx, W, H, imgs, ap5);
        }
      }

      // 渲染高速残影队列 (Motion Afterimages)
      for (var ti2 = state.trails.length - 1; ti2 >= 0; ti2--) {
        var tr = state.trails[ti2];
        tr.life -= 0.055;
        if (tr.life <= 0) {
          state.trails.splice(ti2, 1);
          continue;
        }
        if (tr.kind === "nezuko") {
          drawNezukoBonesActor(ctx, imgs, {
            x: tr.x, y: tr.y, scale: 1.32 * unit, dir: tr.dir, lean: tr.lean,
            kickAngle: tr.slashAngle, alpha: tr.life * 0.42, isSilhouette: true
          });
        } else {
          drawFighterActor(ctx, tr.kind, {
            x: tr.x, y: tr.y, scale: 1.32 * unit, dir: tr.dir, lean: tr.lean,
            slashAngle: tr.slashAngle, crouch: 0.35, alpha: tr.life * 0.42,
            auraColor: tr.color, bladeColor: tr.color, isSilhouette: true
          });
        }
      }

      // 渲染粒子（水花 / 火星 / 电火花 / 血樱）
      for (var pIdx = 0; pIdx < state.particles.length; pIdx++) {
        var pObj = state.particles[pIdx];
        ctx.save();
        ctx.globalAlpha = clamp(pObj.life, 0, 1);
        ctx.fillStyle = pObj.color;
        ctx.shadowBlur = 10;
        ctx.shadowColor = pObj.color;
        ctx.beginPath();
        ctx.arc(pObj.x, pObj.y, pObj.r * unit, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      // 动漫杀招经典「黑白高对比 Impact Frame」闪屏叠加
      if (state.impactTimer > 0) {
        ctx.save();
        ctx.globalCompositeOperation = "difference";
        ctx.fillStyle = "#ffffff";
        ctx.globalAlpha = clamp(state.impactTimer / 75, 0.25, 0.85);
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
        container.innerHTML = "";
      }
    };
  }

  root.KimetsuTheater = {
    mount: mount,
    CHARACTERS: CHAR_META
  };
})(typeof window !== "undefined" ? window : globalThis);
