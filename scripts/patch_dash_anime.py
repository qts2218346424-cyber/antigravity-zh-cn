# -*- coding: utf-8 -*-
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_JS = REPO_ROOT / "resources" / "nezuko-pet.js"

content = TARGET_JS.read_text(encoding="utf-8")

# 1. 扩充 PetAudioSynth
old_sound = """    // 奔跑轻快卡通小脚步
    playFootstep() {
      try {
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(450, now);
        gain.gain.setValueAtTime(0.035, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.connect(gain); gain.connect(this.ctx.destination);
        osc.start(now); osc.stop(now + 0.06);
      } catch (_) {}
    }"""

new_sound = """    // 奔跑轻快卡通小脚步
    playFootstep() {
      try {
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(450, now);
        gain.gain.setValueAtTime(0.035, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.connect(gain); gain.connect(this.ctx.destination);
        osc.start(now); osc.stop(now + 0.06);
      } catch (_) {}
    }
    // 动漫爆发疾冲破风音效 (Dash Whoosh)
    playDashWhoosh() {
      try {
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(140, now);
        osc.frequency.exponentialRampToValueAtTime(780, now + 0.12);
        osc.frequency.exponentialRampToValueAtTime(220, now + 0.42);
        gain.gain.setValueAtTime(0.01, now);
        gain.gain.linearRampToValueAtTime(0.16, now + 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
        osc.connect(gain); gain.connect(this.ctx.destination);
        osc.start(now); osc.stop(now + 0.46);

        const osc2 = this.ctx.createOscillator();
        const gain2 = this.ctx.createGain();
        osc2.type = 'triangle';
        osc2.frequency.setValueAtTime(420, now);
        osc2.frequency.linearRampToValueAtTime(180, now + 0.38);
        gain2.gain.setValueAtTime(0.08, now);
        gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.38);
        osc2.connect(gain2); gain2.connect(this.ctx.destination);
        osc2.start(now); osc2.stop(now + 0.4);
      } catch (_) {}
    }
    // 动漫急刹车地面摩擦制动音效 (Skid Brake)
    playSkidBrake() {
      try {
        this.ensureCtx();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(620, now);
        osc.frequency.exponentialRampToValueAtTime(160, now + 0.28);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.32);
        osc.connect(gain); gain.connect(this.ctx.destination);
        osc.start(now); osc.stop(now + 0.33);
      } catch (_) {}
    }"""

if old_sound in content:
    content = content.replace(old_sound, new_sound, 1)
    print("✅ 成功注入 PetAudioSynth 动漫飞奔与急刹车音效")
else:
    print("⚠️ 未找到 old_sound，尝试规范换行后匹配")
    content_normalized = content.replace("\r\n", "\n")
    if old_sound.replace("\r\n", "\n") in content_normalized:
        content = content_normalized.replace(old_sound.replace("\r\n", "\n"), new_sound.replace("\r\n", "\n"), 1)
        print("✅ 规范换行后成功注入音效")
    else:
        print("❌ 无法匹配 old_sound")
        sys.exit(1)

# 2. 升级 CSS 样式
old_css_anchor_start = "    /* 核心 3：风火轮狂奔冲刺与急刹车滑行 (Run Dash & Skid Brake) */"
old_css_anchor_end = "    /* ========================================================= */\n    /* 核心 4：大正雾云杉木箱"

new_css = """    /* 核心 3：电影级动漫爆发飞奔冲刺与急刹车滑行制动 (Anime Dash & Skid Brake) */
    /* ========================================================= */
    /* 起跑蓄力压缩前摇 (Anticipation) */
    .is-anticipating {
      transform: translateY(6px) rotate(4deg) scale(1.12, 0.88) !important;
      transition: transform 0.1s cubic-bezier(0.2, 0.9, 0.4, 1) !important;
    }
    .prince-pet-rig.is-anticipating {
      transform: translateX(-50%) translateY(7px) rotate(5deg) scale(1.1, 0.88) !important;
      transition: transform 0.1s cubic-bezier(0.2, 0.9, 0.4, 1) !important;
    }

    /* 祢豆子飞奔冲刺主体态 (告别扭曲平移，前倾俯冲 + 高频起伏颠簸) */
    .nezuko-pet-rig.is-running {
      animation: nezukoAnimeDash 0.13s infinite alternate ease-in-out !important;
    }
    @keyframes nezukoAnimeDash {
      0% {
        transform: translateY(1px) rotate(-11deg) scale(1.04, 0.96);
      }
      100% {
        transform: translateY(-7px) rotate(-14deg) scale(0.96, 1.04);
      }
    }

    /* 祢豆子经典动漫飞机跑：双臂向后展翅飞拂，双手自然随风扑腾 */
    .nezuko-pet-rig.is-running #bone-arm-l {
      animation: nezukoDashArmL 0.13s infinite alternate ease-in-out !important;
      z-index: 5 !important;
    }
    .nezuko-pet-rig.is-running #bone-arm-r {
      animation: nezukoDashArmR 0.13s infinite alternate ease-in-out !important;
      z-index: 5 !important;
    }
    @keyframes nezukoDashArmL {
      0% { transform: rotate(72deg) translateY(-2px); }
      100% { transform: rotate(84deg) translateY(3px); }
    }
    @keyframes nezukoDashArmR {
      0% { transform: rotate(76deg) translateY(-3px); }
      100% { transform: rotate(88deg) translateY(2px); }
    }

    /* 祢豆子小短腿极速倒腾高频踏步循环 (告别穿模圆规，萌感风火轮) */
    .nezuko-pet-rig.is-running #bone-leg-l {
      animation: nezukoDashLegL 0.13s infinite alternate ease-in-out !important;
    }
    .nezuko-pet-rig.is-running #bone-leg-r {
      animation: nezukoDashLegR 0.13s infinite alternate ease-in-out !important;
    }
    @keyframes nezukoDashLegL {
      0% { transform: rotate(-24deg) translateY(-4px); }
      50% { transform: rotate(0deg) translateY(2px); }
      100% { transform: rotate(26deg) translateY(-3px); }
    }
    @keyframes nezukoDashLegR {
      0% { transform: rotate(26deg) translateY(-3px); }
      50% { transform: rotate(0deg) translateY(2px); }
      100% { transform: rotate(-24deg) translateY(-4px); }
    }

    /* 冲刺飞奔时头部微抬专注注视前方 */
    .nezuko-pet-rig.is-running #bone-head {
      transform: rotate(9deg) translateY(1px) !important;
    }

    /* 祢豆子电影级急刹车滑行制动 (Skid Brake with Overshoot & Settle) */
    .nezuko-pet-rig.action-skid {
      animation: nezukoSkidBrake 0.38s cubic-bezier(0.2, 0.8, 0.3, 1) forwards !important;
    }
    @keyframes nezukoSkidBrake {
      0% {
        transform: translateY(4px) rotate(16deg) scale(1.08, 0.92);
      }
      45% {
        transform: translateY(-3px) rotate(-5deg) scale(0.97, 1.03);
      }
      100% {
        transform: translateY(0) rotate(0deg) scale(1, 1);
      }
    }
    .nezuko-pet-rig.action-skid #bone-arm-l {
      transform: rotate(-22deg) translateY(-2px) !important;
      transition: transform 0.25s ease-out;
    }
    .nezuko-pet-rig.action-skid #bone-arm-r {
      transform: rotate(22deg) translateY(-2px) !important;
      transition: transform 0.25s ease-out;
    }
    .nezuko-pet-rig.action-skid #bone-leg-l {
      transform: rotate(18deg) translateY(-2px) !important;
    }
    .nezuko-pet-rig.action-skid #bone-leg-r {
      transform: rotate(26deg) translateY(2px) !important;
    }

    /* 小王子专属御风踏空飞奔态 (保持 translateX(-50%) 居中与 15° 俯冲动势) */
    .prince-pet-rig.is-running {
      animation: princeDashRig 0.13s infinite alternate ease-in-out !important;
    }
    @keyframes princeDashRig {
      0% {
        transform: translateX(-50%) translateY(-2px) rotate(-13deg) scale(1.04, 0.96);
      }
      100% {
        transform: translateX(-50%) translateY(-9px) rotate(-16deg) scale(0.96, 1.04);
      }
    }
    .prince-pet-rig.action-skid {
      animation: princeSkidBrake 0.38s cubic-bezier(0.2, 0.8, 0.3, 1) forwards !important;
    }
    @keyframes princeSkidBrake {
      0% {
        transform: translateX(-50%) translateY(5px) rotate(14deg) scale(1.08, 0.92);
      }
      45% {
        transform: translateX(-50%) translateY(-3px) rotate(-4deg) scale(0.97, 1.03);
      }
      100% {
        transform: translateX(-50%) translateY(0) rotate(0deg) scale(1, 1);
      }
    }

    /* 动漫动态半透明残影 (Motion Blur Ghost Trail) */
    .dash-ghost-shadow {
      position: absolute;
      bottom: 0;
      width: 130px;
      height: 215px;
      pointer-events: none;
      z-index: 3;
      transform-origin: 50% 100%;
      animation: ghostFadeOut 0.36s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
    }
    @keyframes ghostFadeOut {
      0% { opacity: 0.72; transform: scale(1); }
      100% { opacity: 0; transform: scale(1.08) translateY(-6px); filter: blur(3px); }
    }

    /* 冲刺连续扬尘与急刹滑行烟云粒子 */
    .dash-dust-container {
      position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
      pointer-events: none; width: 130px; height: 40px; z-index: 2;
    }
    .dust-puff {
      position: absolute; bottom: 0; width: 18px; height: 18px; border-radius: 50%;
      background: radial-gradient(circle at 35% 35%, rgba(245, 230, 215, 0.9) 0%, rgba(210, 190, 170, 0.6) 60%, transparent 80%);
      opacity: 0;
      animation: dustAnimeRise 0.5s ease-out forwards;
    }
    @keyframes dustAnimeRise {
      0% { transform: translate(0, 0) scale(0.4); opacity: 0.9; }
      50% { opacity: 0.8; }
      100% { transform: translate(var(--dust-x, 30px), -24px) scale(1.8); opacity: 0; }
    }
    .skid-smoke-puff {
      position: absolute; bottom: 2px; width: 22px; height: 22px; border-radius: 50%;
      background: radial-gradient(circle at 40% 40%, rgba(255, 255, 255, 0.95) 0%, rgba(245, 235, 225, 0.7) 50%, transparent 80%);
      opacity: 0;
      animation: skidSmokeDrift 0.42s ease-out forwards;
    }
    @keyframes skidSmokeDrift {
      0% { transform: translate(0, 0) scale(0.5); opacity: 0.95; }
      100% { transform: translate(var(--skid-dx, 36px), -12px) scale(2.2); opacity: 0; filter: blur(2px); }
    }\n\n"""

# 查找 CSS 范围替换
pos_start = content.find(old_css_anchor_start)
pos_end = content.find(old_css_anchor_end)
if pos_start != -1 and pos_end != -1:
    content = content[:pos_start] + new_css + content[pos_end:]
    print("✅ 成功替换 CSS 飞奔与急刹车样式")
else:
    print(f"❌ 查找 CSS 锚点失败: start={pos_start}, end={pos_end}")
    sys.exit(1)

# 3. 升级 JS 冲刺逻辑 (包含 spawnDashGhost, spawnSkidSmoke 与 runDash)
old_js_anchor_start = "  function spawnDustPuff() {"
old_js_anchor_end = "  // 自主漫步巡航心跳"

new_js = """  // 极速冲刺动态半透明残影生成 (Ghost Trail)
  function spawnDashGhost(activeRig, facingDir) {
    if (!activeRig || !root || !root.parentElement) return;
    const ghost = document.createElement('div');
    ghost.className = 'dash-ghost-shadow';
    ghost.style.right = (root.style.right || '24px');
    ghost.style.transform = `scaleX(${facingDir})`;

    if (activePet === 'nezuko') {
      ghost.innerHTML = `
        <div style="width:100%; height:100%; background:radial-gradient(ellipse at center, rgba(244,114,182,0.48) 0%, rgba(225,29,72,0.2) 65%, transparent 85%); filter:blur(1.5px) drop-shadow(0 0 8px rgba(244,114,182,0.6)); border-radius:28px;"></div>
      `;
    } else {
      ghost.innerHTML = `
        <div style="width:100%; height:100%; background:radial-gradient(ellipse at center, rgba(251,191,36,0.52) 0%, rgba(245,158,11,0.24) 65%, transparent 85%); filter:blur(1.5px) drop-shadow(0 0 10px rgba(251,191,36,0.75)); border-radius:28px;"></div>
      `;
    }

    root.parentElement.appendChild(ghost);
    setTimeout(() => {
      if (ghost.parentElement) ghost.remove();
    }, 360);
  }

  // 急刹车滑痕烟雾喷射
  function spawnSkidSmoke(facingDir) {
    if (!dustContainer) return;
    const smoke = document.createElement('div');
    smoke.className = 'skid-smoke-puff';
    smoke.style.left = (facingDir > 0 ? '60%' : '40%');
    const driftX = (facingDir > 0 ? (28 + Math.random() * 20) : -(28 + Math.random() * 20)) + 'px';
    smoke.style.setProperty('--skid-dx', driftX);
    dustContainer.appendChild(smoke);
    setTimeout(() => smoke.remove(), 420);
  }

  function spawnDustPuff() {
    const puff = document.createElement('div');
    puff.className = 'dust-puff';
    puff.style.left = (facingDirection > 0 ? '70%' : '30%');
    puff.style.setProperty('--dust-x', (facingDirection > 0 ? '30px' : '-30px'));
    dustContainer.appendChild(puff);
    setTimeout(() => puff.remove(), 550);
  }

  // 极速动漫爆发冲刺与电影级急刹制动 (Anime Dash & Sprint Pipeline)
  function runDash(customDist = 0) {
    if (isActionPlaying) return;
    isActionPlaying = true;
    const maxRight = Math.min(window.innerWidth - 180, 850);
    const minRight = 24;

    const sprintDist = 360;
    let targetDist = customDist !== 0 ? customDist : (facingDirection > 0 ? sprintDist : -sprintDist);
    let targetRight = curRight + targetDist;

    if (targetRight > maxRight) {
      targetRight = Math.max(minRight, curRight - sprintDist);
      updateFacing(-1);
    } else if (targetRight < minRight) {
      targetRight = Math.min(maxRight, curRight + sprintDist);
      updateFacing(1);
    }

    const dist = targetRight - curRight;
    const finalDir = dist > 0 ? 1 : -1;
    updateFacing(finalDir);

    const activeRig = activePet === 'nezuko' ? petNezuko : petPrince;

    // Phase 1: 蓄力前摇压缩 (100ms Anticipation)
    activeRig.classList.add('is-anticipating');
    petAudio.playAlertSound();
    spawnDustPuff();

    setTimeout(() => {
      activeRig.classList.remove('is-anticipating');
      activeRig.classList.add('is-running');
      petAudio.playDashWhoosh();

      // 冲刺期间高频残影定时器 (45ms)
      const ghostTimer = setInterval(() => {
        spawnDashGhost(activeRig, finalDir);
      }, 45);

      // 扬尘与小王子围巾风力冲量
      const dustTimer = setInterval(() => {
        spawnDustPuff();
        if (activePet === 'prince' && window.__PRINCE_SCARF_ENGINE__) {
          window.__PRINCE_SCARF_ENGINE__.injectImpulse(-18 * finalDir, (Math.random() - 0.5) * 6);
          if (typeof spawnPrinceStardust === 'function') spawnPrinceStardust();
        }
      }, 55);

      // Phase 2: 爆发位移 (0.42s 弹射曲线)
      const burstDurationSec = 0.42;
      root.style.transition = `right ${burstDurationSec}s cubic-bezier(0.16, 1, 0.3, 1)`;
      root.style.right = targetRight + 'px';
      curRight = targetRight;

      // Phase 3: 急刹车制动与惯性回弹 (Skid Brake & Settle)
      setTimeout(() => {
        clearInterval(ghostTimer);
        clearInterval(dustTimer);
        activeRig.classList.remove('is-running');
        activeRig.classList.add('action-skid');
        petAudio.playSkidBrake();

        for (let i = 0; i < 4; i++) {
          setTimeout(() => spawnSkidSmoke(finalDir), i * 35);
        }

        setTimeout(() => {
          activeRig.classList.remove('action-skid');
          isActionPlaying = false;
        }, 380);
      }, burstDurationSec * 1000);

    }, 100);
  }

"""

pos_js_start = content.find(old_js_anchor_start)
pos_js_end = content.find(old_js_anchor_end)
if pos_js_start != -1 and pos_js_end != -1:
    # 注意保留 walkTo 函数！
    # 先检查 walkTo 是否在 pos_js_start 和 pos_js_end 之间
    walk_start = content.find("  // 动画级行走小碎步", pos_js_start)
    run_dash_start = content.find("  // 极速风火轮狂奔冲刺与急刹车 (Run Dash)", walk_start)
    walk_code = content[walk_start:run_dash_start]

    # 拼接新的 JS：包含残影、烟雾、原有的 walkTo 和全新 runDash
    content = content[:pos_js_start] + new_js.replace(
        "  // 极速动漫爆发冲刺与电影级急刹制动",
        walk_code + "  // 极速动漫爆发冲刺与电影级急刹制动"
    ) + content[pos_js_end:]
    print("✅ 成功替换 JS 冲刺动力学管线与残影生成逻辑")
else:
    print(f"❌ 查找 JS 锚点失败: start={pos_js_start}, end={pos_js_end}")
    sys.exit(1)

# 写回 TARGET_JS
TARGET_JS.write_text(content, encoding="utf-8")
print(f"🎉 成功更新 {TARGET_JS}！")
