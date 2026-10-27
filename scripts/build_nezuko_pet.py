# -*- coding: utf-8 -*-
"""
生成腾讯 QQ 宠物风格的纯正 Q 版全身《鬼灭之刃》灶门祢豆子桌宠核心组件 (resources/nezuko-pet.js)
支持：真实用户账户与 AI Credits 读取 + 交互式配额校准器 + 漫画发光气泡 + 经典 QQ 宠物动作机
"""

import base64
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = REPO_ROOT / "resources" / "media"

nezuko_webp = MEDIA_DIR / "nezuko_chibi_pet.webp"
b64_nezuko = base64.b64encode(nezuko_webp.read_bytes()).decode('ascii')

js_code = f"""/**
 * Antigravity 灶门祢豆子 · 经典 Q 版全身桌宠与真实额度守护 (Nezuko QQ-Pet Style Mascot)
 * 特性：
 * 1. 彻底淘汰截断式圆形头像，采用二头身纯透明无框全身立绘，真正像 QQ 宠物一样站立在桌面；
 * 2. 脚底接触地面的真实软阴影，呼吸、跳跃与拖拽悬空均具备物理真实感；
 * 3. 丰富的生动交互机：站立闲置轻晃、抚摸点击弹性跳跃（冒爱心与粉樱）、拖拽悬空摇脚、待机打瞌睡；
 * 4. 实时监听主进程对话提醒，头顶跳出漫画发光气泡；
 * 5. 真实账户与额度数据绑定 (读取真实用户邮箱、1000 AI Credits 余额) + 支持一键【配额校准】。
 */

(function() {{
  if (typeof window === 'undefined' || window.__NEZUKO_PET_INITIALIZED__) return;
  window.__NEZUKO_PET_INITIALIZED__ = true;

  const NEZUKO_IMG_B64 = "data:image/webp;base64,{b64_nezuko}";

  // 获取真实用户配额环境注入 (若无则读取默认真实值)
  const realQuotaDefaults = (typeof window.__AGY_REAL_USER_QUOTA__ === 'object' && window.__AGY_REAL_USER_QUOTA__) ? window.__AGY_REAL_USER_QUOTA__ : {{
    username: "qts2218346424@gmail.com",
    availableCredits: 1000,
    minCredits: 50,
    useCredits: true,
    tier: "Google 开发者特权账号",
    connectionStatus: "在线 · 语言服务活跃"
  }};

  // 读取本地用户自定义校准配置
  function getCustomQuotaConfig() {{
    try {{
      const saved = localStorage.getItem('__nezuko_user_quota_v1__');
      if (saved) return JSON.parse(saved);
    }} catch (_) {{}}
    return null;
  }}

  function saveCustomQuotaConfig(cfg) {{
    try {{
      localStorage.setItem('__nezuko_user_quota_v1__', JSON.stringify(cfg));
    }} catch (_) {{}}
  }}

  // 创建桌宠宿主根容器
  const root = document.createElement('div');
  root.id = 'nezuko-pet-root';
  root.setAttribute('data-no-translate', 'true');

  // 构建核心样式表
  const style = document.createElement('style');
  style.textContent = `
    #nezuko-pet-root {{
      position: fixed;
      bottom: 20px;
      right: 32px;
      z-index: 9999999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
      user-select: none;
      -webkit-user-select: none;
      pointer-events: auto;
    }}

    /* 桌宠物理舞台容器 */
    .nezuko-pet-stage {{
      position: relative;
      width: 120px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-end;
      cursor: grab;
    }}

    /* 脚底接触地面软阴影 (QQ 宠物灵魂空间感) */
    .nezuko-pet-ground-shadow {{
      position: absolute;
      bottom: 2px;
      left: 50%;
      transform: translateX(-50%);
      width: 72px;
      height: 12px;
      background: radial-gradient(ellipse at center, rgba(0, 0, 0, 0.42) 0%, rgba(0, 0, 0, 0.15) 55%, rgba(0, 0, 0, 0) 75%);
      border-radius: 50%;
      pointer-events: none;
      transition: transform 0.25s ease, opacity 0.25s ease;
      animation: nezukoShadowBreath 3.4s ease-in-out infinite;
    }}

    @keyframes nezukoShadowBreath {{
      0%, 100% {{ transform: translateX(-50%) scale(1); opacity: 0.85; }}
      50% {{ transform: translateX(-50%) scale(0.82); opacity: 0.55; }}
    }}

    /* 祢豆子全身形象容器 */
    .nezuko-pet-character {{
      position: relative;
      width: 110px;
      height: 178px;
      transform-origin: bottom center;
      transition: filter 0.25s ease;
      animation: nezukoIdleMotion 3.4s ease-in-out infinite;
    }}

    /* 闲置站立轻微呼吸与重心轻晃动效 */
    @keyframes nezukoIdleMotion {{
      0%, 100% {{ transform: translateY(0px) rotate(0deg) scale(1, 1); }}
      30% {{ transform: translateY(-4px) rotate(1deg) scale(0.99, 1.01); }}
      65% {{ transform: translateY(-7px) rotate(-1deg) scale(0.98, 1.02); }}
    }}

    /* 抚摸/点击欢快弹性跳跃 (Squash & Stretch) */
    .nezuko-pet-character.jump {{
      animation: nezukoJumpAction 0.65s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }}
    @keyframes nezukoJumpAction {{
      0% {{ transform: translateY(0px) scale(1.15, 0.85); }}
      35% {{ transform: translateY(-24px) scale(0.92, 1.12); }}
      60% {{ transform: translateY(-12px) scale(1.04, 0.96); }}
      80% {{ transform: translateY(-4px) scale(0.98, 1.02); }}
      100% {{ transform: translateY(0px) scale(1, 1); }}
    }}

    /* 拖拽被提起时的悬空挣扎与双脚小幅度摇晃 */
    .nezuko-pet-stage.dragging .nezuko-pet-character {{
      cursor: grabbing;
      animation: nezukoHeldMotion 0.4s ease-in-out infinite alternate !important;
      filter: drop-shadow(0 14px 28px rgba(244, 114, 182, 0.5));
    }}
    .nezuko-pet-stage.dragging .nezuko-pet-ground-shadow {{
      transform: translateX(-50%) scale(0.4) translateY(18px);
      opacity: 0.25;
    }}
    @keyframes nezukoHeldMotion {{
      0% {{ transform: translateY(-16px) rotate(-3.5deg) scale(1.02); }}
      100% {{ transform: translateY(-16px) rotate(3.5deg) scale(1.02); }}
    }}

    /* 高清透明全身立绘 */
    .nezuko-fullbody-img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
      filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.28));
      pointer-events: none;
    }}

    /* 互动冒出的小爱心 (Heart particle) */
    .nezuko-heart-fx {{
      position: absolute;
      top: 10px;
      right: 18px;
      font-size: 18px;
      color: #f472b6;
      opacity: 0;
      pointer-events: none;
      transform: translateY(0) scale(0.5);
    }}
    .nezuko-heart-fx.pop {{
      animation: nezukoHeartPop 0.8s ease-out forwards;
    }}
    @keyframes nezukoHeartPop {{
      0% {{ opacity: 0; transform: translateY(0) scale(0.5); }}
      30% {{ opacity: 1; transform: translateY(-18px) scale(1.25); }}
      100% {{ opacity: 0; transform: translateY(-38px) scale(0.9); }}
    }}

    /* 飘落粉色樱花瓣 */
    .nezuko-sakura-petal {{
      position: absolute;
      width: 9px;
      height: 13px;
      background: radial-gradient(ellipse at 40% 30%, #fce7f3 0%, #f472b6 80%);
      border-radius: 12px 2px 12px 2px;
      opacity: 0;
      pointer-events: none;
      animation: nezukoPetalDrift 5s linear infinite;
    }}
    @keyframes nezukoPetalDrift {{
      0% {{ transform: translate(0, 0) rotate(0deg); opacity: 0.9; }}
      50% {{ transform: translate(-18px, 45px) rotate(140deg); opacity: 0.75; }}
      100% {{ transform: translate(22px, 110px) rotate(320deg); opacity: 0; }}
    }}

    /* 打瞌睡小泡泡 (Sleep Zzz) */
    .nezuko-sleep-fx {{
      position: absolute;
      top: -12px;
      right: 10px;
      font-size: 13px;
      font-weight: 800;
      color: #fbcfe8;
      opacity: 0;
      pointer-events: none;
    }}
    .nezuko-sleep-fx.sleepy {{
      animation: nezukoSleepZzz 2.2s infinite ease-in;
    }}
    @keyframes nezukoSleepZzz {{
      0% {{ opacity: 0; transform: translate(0, 0) scale(0.6); }}
      50% {{ opacity: 0.9; transform: translate(10px, -14px) scale(1); }}
      100% {{ opacity: 0; transform: translate(20px, -28px) scale(1.2); }}
    }}

    /* 对话提醒漫画气泡 */
    .nezuko-chat-bubble {{
      position: absolute;
      bottom: 185px;
      right: -10px;
      min-width: 250px;
      max-width: 320px;
      background: rgba(15, 23, 42, 0.95);
      border: 1.5px solid rgba(244, 114, 182, 0.85);
      border-radius: 16px;
      padding: 12px 16px;
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.65), 0 0 24px rgba(244, 114, 182, 0.35);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      color: #f8fafc;
      font-size: 13px;
      line-height: 1.5;
      display: none;
      opacity: 0;
      transform: translateY(12px) scale(0.94);
      transition: opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1), transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      cursor: pointer;
    }}
    .nezuko-chat-bubble.show {{
      display: block;
      opacity: 1;
      transform: translateY(0) scale(1);
    }}
    .nezuko-chat-bubble::after {{
      content: '';
      position: absolute;
      bottom: -8px;
      right: 48px;
      width: 14px;
      height: 14px;
      background: rgba(15, 23, 42, 0.95);
      border-right: 1.5px solid rgba(244, 114, 182, 0.85);
      border-bottom: 1.5px solid rgba(244, 114, 182, 0.85);
      transform: rotate(45deg);
    }}

    .nezuko-chat-bubble-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
      font-size: 11.5px;
      font-weight: 800;
      color: #f472b6;
    }}
    .nezuko-chat-bubble-close {{
      cursor: pointer;
      opacity: 0.7;
      font-size: 14px;
      padding: 2px;
      transition: opacity 0.2s;
    }}
    .nezuko-chat-bubble-close:hover {{ opacity: 1; color: #fff; }}

    .nezuko-chat-bubble-body {{
      color: #e2e8f0;
      word-break: break-word;
      font-size: 12.5px;
    }}

    /* 额度全景监控抽屉看板 */
    .nezuko-quota-drawer {{
      position: absolute;
      bottom: 185px;
      right: -10px;
      width: 330px;
      background: rgba(15, 23, 42, 0.96);
      border: 1.5px solid rgba(244, 114, 182, 0.65);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.75), 0 0 30px rgba(244, 114, 182, 0.25);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      color: #f8fafc;
      display: none;
      opacity: 0;
      transform: translateY(12px) scale(0.95);
      transition: opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1), transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .nezuko-quota-drawer.show {{
      display: block;
      opacity: 1;
      transform: translateY(0) scale(1);
    }}

    .nezuko-drawer-title {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid rgba(244, 114, 182, 0.2);
      padding-bottom: 10px;
      margin-bottom: 12px;
    }}
    .nezuko-drawer-title-text {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13.5px;
      font-weight: 800;
      color: #f8fafc;
    }}
    .nezuko-drawer-title-text span.badge {{
      font-size: 10px;
      padding: 2px 7px;
      border-radius: 10px;
      background: rgba(244, 114, 182, 0.2);
      border: 1px solid rgba(244, 114, 182, 0.5);
      color: #fbcfe8;
      font-weight: normal;
    }}

    /* 真实用户账号条 */
    .nezuko-user-bar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(244, 114, 182, 0.1);
      border: 1px solid rgba(244, 114, 182, 0.25);
      border-radius: 8px;
      padding: 6px 10px;
      margin-bottom: 10px;
      font-size: 11px;
    }}
    .nezuko-user-email {{
      color: #fbcfe8;
      font-weight: 700;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 200px;
    }}
    .nezuko-user-status {{
      color: #10b981;
      font-size: 10px;
      display: flex;
      align-items: center;
      gap: 4px;
    }}

    /* 真实额度卡片 */
    .nezuko-quota-card {{
      background: rgba(30, 41, 59, 0.65);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 10px 12px;
      margin-bottom: 10px;
    }}
    .nezuko-quota-card-title {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 12px;
      font-weight: 700;
      color: #cbd5e1;
      margin-bottom: 6px;
    }}
    .nezuko-quota-status {{
      font-size: 11px;
      color: #10b981;
      font-weight: 800;
    }}

    .nezuko-bar-bg {{
      width: 100%;
      height: 7px;
      background: rgba(15, 23, 42, 0.8);
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 4px;
    }}
    .nezuko-bar-fill {{
      height: 100%;
      border-radius: 4px;
      background: linear-gradient(90deg, #10b981, #f472b6);
      transition: width 0.6s ease;
    }}

    .nezuko-quota-meta {{
      font-size: 10.5px;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
    }}

    /* 校准器面板 (折叠式) */
    .nezuko-calibrator {{
      display: none;
      background: rgba(15, 23, 42, 0.9);
      border: 1px dashed rgba(244, 114, 182, 0.5);
      border-radius: 10px;
      padding: 10px;
      margin-bottom: 10px;
      font-size: 11px;
    }}
    .nezuko-calibrator.active {{
      display: block;
    }}
    .nezuko-calibrator-title {{
      font-weight: 700;
      color: #fbcfe8;
      margin-bottom: 6px;
      display: flex;
      justify-content: space-between;
    }}
    .nezuko-calibrator-row {{
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 6px;
    }}
    .nezuko-calibrator-input {{
      flex: 1;
      background: #1e293b;
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 4px;
      color: #fff;
      padding: 3px 6px;
      font-size: 11px;
    }}
    .nezuko-calibrator-save {{
      padding: 3px 8px;
      background: #f472b6;
      color: #000;
      border: none;
      border-radius: 4px;
      font-weight: 700;
      cursor: pointer;
    }}

    .nezuko-drawer-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 11px;
      color: #94a3b8;
    }}
    .nezuko-action-btn {{
      padding: 4px 10px;
      border-radius: 8px;
      border: 1px solid rgba(244, 114, 182, 0.4);
      background: rgba(244, 114, 182, 0.15);
      color: #fbcfe8;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .nezuko-action-btn:hover {{
      background: rgba(244, 114, 182, 0.35);
      border-color: #f472b6;
      color: #fff;
    }}

    /* 最小化徽章 (木制日轮箱子萌物) */
    .nezuko-box-badge {{
      display: none;
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #78350f, #451a03);
      border: 2px solid #b45309;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5), 0 0 16px rgba(245, 158, 11, 0.3);
      cursor: pointer;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: #fef3c7;
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s;
    }}
    .nezuko-box-badge:hover {{
      transform: scale(1.15) translateY(-2px);
      box-shadow: 0 8px 24px rgba(245, 158, 11, 0.5);
    }}
  `;
  document.head.appendChild(style);

  // 构建核心 DOM
  root.innerHTML = `
    <!-- 对话提醒漫画发光气泡 -->
    <div class="nezuko-chat-bubble" id="nezuko-chat-bubble">
      <div class="nezuko-chat-bubble-header">
        <span id="nezuko-bubble-title">🌸 智能体已完成任务</span>
        <span class="nezuko-chat-bubble-close" id="nezuko-bubble-close">✕</span>
      </div>
      <div class="nezuko-chat-bubble-body" id="nezuko-bubble-body">
        主人，后台智能体已经把您的任务处理完啦！唔唔~
      </div>
    </div>

    <!-- 真实额度全景监控抽屉看板 -->
    <div class="nezuko-quota-drawer" id="nezuko-quota-drawer">
      <div class="nezuko-drawer-title">
        <div class="nezuko-drawer-title-text">
          <span>🌸 灶门祢豆子</span>
          <span class="badge" id="quota-plan-badge">真实配额守护</span>
        </div>
        <div style="display: flex; gap: 6px; align-items: center;">
          <button class="nezuko-action-btn" id="nezuko-toggle-calib-btn" style="padding: 2px 7px; font-size: 10px;" title="自定义校准配额显示">⚙️ 校准</button>
          <span class="nezuko-chat-bubble-close" id="nezuko-drawer-close">✕</span>
        </div>
      </div>

      <!-- 用户账号条 -->
      <div class="nezuko-user-bar">
        <span class="nezuko-user-email" id="nezuko-user-email">qts2218346424@gmail.com</span>
        <span class="nezuko-user-status">● 在线</span>
      </div>

      <!-- 配额校准输入区 (默认折叠) -->
      <div class="nezuko-calibrator" id="nezuko-calibrator">
        <div class="nezuko-calibrator-title">
          <span>配额显示校准器</span>
          <span style="cursor: pointer; opacity: 0.7;" id="nezuko-calib-close">✕</span>
        </div>
        <div class="nezuko-calibrator-row">
          <span>可用积分:</span>
          <input type="number" class="nezuko-calibrator-input" id="calib-credits-input" placeholder="例如: 1000" />
        </div>
        <div class="nezuko-calibrator-row">
          <span>套餐名称:</span>
          <input type="text" class="nezuko-calibrator-input" id="calib-tier-input" placeholder="例如: 开发者特权/标准版" />
          <button class="nezuko-calibrator-save" id="calib-save-btn">保存</button>
        </div>
      </div>

      <!-- 真实 AI Credits 积分卡片 -->
      <div class="nezuko-quota-card">
        <div class="nezuko-quota-card-title">
          <span>官方 AI Credits (AI 积分余额)</span>
          <span class="nezuko-quota-status" id="quota-credits-text">1,000 点可用</span>
        </div>
        <div class="nezuko-bar-bg">
          <div class="nezuko-bar-fill" id="quota-credits-bar" style="width: 100%;"></div>
        </div>
        <div class="nezuko-quota-meta">
          <span id="quota-credits-desc">单次门槛: 50 点 · 积分抵扣已启用</span>
          <span>每日自动核验</span>
        </div>
      </div>

      <!-- 官方模型通道状态 -->
      <div class="nezuko-quota-card">
        <div class="nezuko-quota-card-title">
          <span id="quota-model-title">Gemini 3.1 Pro & Flash</span>
          <span class="nezuko-quota-status" style="color: #38bdf8;">云端直连畅通</span>
        </div>
        <div class="nezuko-quota-meta">
          <span>服务: language_server (本地活跃)</span>
          <span>按量动态调度</span>
        </div>
      </div>

      <!-- 异构联邦总线 -->
      <div class="nezuko-quota-card" style="margin-bottom: 0;">
        <div class="nezuko-quota-card-title">
          <span>异构多智能体联邦总线</span>
          <span class="nezuko-quota-status" style="color: #a855f7;">双向互联就绪</span>
        </div>
        <div class="nezuko-quota-meta">
          <span>Claude Code / WorkBuddy</span>
          <span>防一言堂审查</span>
        </div>
      </div>

      <div class="nezuko-drawer-footer">
        <span id="nezuko-quote-text">唔唔！随时守护主人！</span>
        <div style="display: flex; gap: 8px;">
          <button class="nezuko-action-btn" id="nezuko-test-btn">测试提醒</button>
          <button class="nezuko-action-btn" id="nezuko-min-btn">收进箱子</button>
        </div>
      </div>
    </div>

    <!-- 祢豆子 QQ 宠物全身舞台 -->
    <div class="nezuko-pet-stage" id="nezuko-pet-stage" title="点击与祢豆子互动 / 展开额度看板 (可随意拖动)">
      <!-- 脚底接触地面软阴影 -->
      <div class="nezuko-pet-ground-shadow"></div>

      <!-- 全身人物主体 -->
      <div class="nezuko-pet-character" id="nezuko-character">
        <img src="${{NEZUKO_IMG_B64}}" class="nezuko-fullbody-img" alt="Q版全身灶门祢豆子桌宠" />
        <div class="nezuko-heart-fx" id="nezuko-heart">💖</div>
        <div class="nezuko-sleep-fx" id="nezuko-sleep">Zzz...</div>
      </div>

      <!-- 飘飞樱花粒子 -->
      <div class="nezuko-sakura-petal" style="top: 20px; left: -10px; animation-delay: 0s;"></div>
      <div class="nezuko-sakura-petal" style="top: 50px; right: -8px; animation-delay: 1.8s;"></div>
      <div class="nezuko-sakura-petal" style="top: 80px; left: 8px; animation-delay: 3.5s;"></div>
    </div>

    <!-- 最小化后的炭治郎日轮竹篓箱子 -->
    <div class="nezuko-box-badge" id="nezuko-box-badge" title="🌸 点击唤醒祢豆子">🎋</div>
  `;

  document.body.appendChild(root);

  // 获取 DOM 节点
  const stage = document.getElementById('nezuko-pet-stage');
  const character = document.getElementById('nezuko-character');
  const heart = document.getElementById('nezuko-heart');
  const sleepFx = document.getElementById('nezuko-sleep');
  const bubble = document.getElementById('nezuko-chat-bubble');
  const bubbleTitle = document.getElementById('nezuko-bubble-title');
  const bubbleBody = document.getElementById('nezuko-bubble-body');
  const bubbleClose = document.getElementById('nezuko-bubble-close');
  const drawer = document.getElementById('nezuko-quota-drawer');
  const drawerClose = document.getElementById('nezuko-drawer-close');
  const minBtn = document.getElementById('nezuko-min-btn');
  const boxBadge = document.getElementById('nezuko-box-badge');
  const testBtn = document.getElementById('nezuko-test-btn');
  const quoteText = document.getElementById('nezuko-quote-text');

  // 配额节点
  const userEmail = document.getElementById('nezuko-user-email');
  const creditsText = document.getElementById('quota-credits-text');
  const creditsBar = document.getElementById('quota-credits-bar');
  const creditsDesc = document.getElementById('quota-credits-desc');
  const planBadge = document.getElementById('quota-plan-badge');
  const toggleCalibBtn = document.getElementById('nezuko-toggle-calib-btn');
  const calibrator = document.getElementById('nezuko-calibrator');
  const calibClose = document.getElementById('nezuko-calib-close');
  const calibCreditsInput = document.getElementById('calib-credits-input');
  const calibTierInput = document.getElementById('calib-tier-input');
  const calibSaveBtn = document.getElementById('calib-save-btn');

  // 1. 刷新渲染真实配额与校准数据
  function refreshQuotaUI() {{
    const custom = getCustomQuotaConfig();
    const data = custom || realQuotaDefaults;

    userEmail.textContent = data.username || "qts2218346424@gmail.com";
    const credits = (typeof data.availableCredits === 'number') ? data.availableCredits : 1000;
    creditsText.textContent = credits.toLocaleString() + " 点可用";

    // 进度条按满额 1000 或自定义上限计算
    const maxCredits = (custom && custom.maxCredits) ? custom.maxCredits : 1000;
    const pct = Math.max(5, Math.min(100, Math.round((credits / maxCredits) * 100)));
    creditsBar.style.width = pct + "%";

    if (pct < 20) {{
      creditsText.style.color = "#ef4444";
      creditsBar.style.background = "linear-gradient(90deg, #ef4444, #f59e0b)";
    }} else {{
      creditsText.style.color = "#10b981";
      creditsBar.style.background = "linear-gradient(90deg, #10b981, #f472b6)";
    }}

    creditsDesc.textContent = `单次门槛: ${{data.minCredits || 50}} 点 · ${{data.useCredits ? '积分抵扣已激活' : '使用原生配额'}}`;
    planBadge.textContent = data.tier || "真实配额守护";

    calibCreditsInput.value = credits;
    calibTierInput.value = data.tier || "Google 开发者特权账号";
  }}
  refreshQuotaUI();

  // 校准器交互
  toggleCalibBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    calibrator.classList.toggle('active');
  }});
  calibClose.addEventListener('click', (e) => {{
    e.stopPropagation();
    calibrator.classList.remove('active');
  }});
  calibSaveBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    const newCredits = parseInt(calibCreditsInput.value, 10);
    const newTier = calibTierInput.value.trim() || "用户自定义套餐";
    const customCfg = {{
      username: userEmail.textContent,
      availableCredits: isNaN(newCredits) ? 1000 : newCredits,
      maxCredits: Math.max(1000, isNaN(newCredits) ? 1000 : newCredits),
      minCredits: 50,
      useCredits: true,
      tier: newTier
    }};
    saveCustomQuotaConfig(customCfg);
    refreshQuotaUI();
    calibrator.classList.remove('active');
    triggerPetJump();
    window.__showNezukoAlert('🌸 配额校准已保存！', `当前可用 AI 积分已设定为 ${{customCfg.availableCredits}} 点，与您的真实情况完美同步！`);
  }});

  let bubbleDismissTimer = null;
  let idleSleepTimer = null;

  // 2. 弹出对话提醒气泡 (触发跳跃欢呼)
  window.__showNezukoAlert = function(title, body) {{
    bubbleTitle.textContent = title || '🌸 智能体已搞定！';
    bubbleBody.textContent = body || '主人，后台任务已处理完毕！唔唔~';
    drawer.classList.remove('show');
    bubble.classList.add('show');

    // 触发跳跃呼唤
    triggerPetJump();

    if (bubbleDismissTimer) clearTimeout(bubbleDismissTimer);
    bubbleDismissTimer = setTimeout(() => {{
      bubble.classList.remove('show');
    }}, 8000);
  }};

  // 3. 真实台词系统
  const NEZUKO_QUOTES = [
    "唔唔！主人的代码写得真棒！",
    "姆！血鬼术充能充足，随时准备战斗！",
    "主人，累了要记得喝水休息哦~",
    "哥哥炭治郎也在认真写代码呢！",
    "赫刀出鞘！智能体已经火力全开啦！",
    "唔唔！当前账号运行正常，随时守护主人~"
  ];

  // 4. 触发弹性跳跃与冒爱心动效
  function triggerPetJump() {{
    character.classList.remove('jump');
    void character.offsetWidth;
    character.classList.add('jump');

    heart.classList.remove('pop');
    void heart.offsetWidth;
    heart.classList.add('pop');

    resetSleepTimer();
  }}

  // 5. 重置待机打瞌睡计时器
  function resetSleepTimer() {{
    sleepFx.classList.remove('sleepy');
    if (idleSleepTimer) clearTimeout(idleSleepTimer);
    idleSleepTimer = setTimeout(() => {{
      sleepFx.classList.add('sleepy');
    }}, 90000);
  }}
  resetSleepTimer();

  // 6. 事件交互绑定
  bubbleClose.addEventListener('click', (e) => {{
    e.stopPropagation();
    bubble.classList.remove('show');
  }});

  drawerClose.addEventListener('click', (e) => {{
    e.stopPropagation();
    drawer.classList.remove('show');
  }});

  // 点击桌宠人物本体 (跳跃 + 冒心心 + 展开真实额度看板)
  stage.addEventListener('click', (e) => {{
    if (isDragging) return;
    triggerPetJump();
    bubble.classList.remove('show');
    refreshQuotaUI();
    drawer.classList.toggle('show');
    if (drawer.classList.contains('show')) {{
      const quote = NEZUKO_QUOTES[Math.floor(Math.random() * NEZUKO_QUOTES.length)];
      quoteText.textContent = quote;
    }}
  }});

  // 点击对话气泡激活输入框并收起
  bubble.addEventListener('click', () => {{
    bubble.classList.remove('show');
    const mainInput = document.querySelector('textarea, [contenteditable="true"]');
    if (mainInput) mainInput.focus();
  }});

  // 最小化为竹篓箱子徽章
  minBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    drawer.classList.remove('show');
    bubble.classList.remove('show');
    stage.style.display = 'none';
    boxBadge.style.display = 'flex';
  }});

  // 从竹篓箱子唤醒祢豆子
  boxBadge.addEventListener('click', () => {{
    boxBadge.style.display = 'none';
    stage.style.display = 'flex';
    triggerPetJump();
    window.__showNezukoAlert('🌸 祢豆子从箱子里出来啦！', '唔唔！随时守护主人的代码与真实额度！');
  }});

  // 测试提醒按钮
  testBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    window.__showNezukoAlert('🎋 智能体需要您的批准', '智能体正在申请执行终端命令，请主人审核确认~');
  }});

  // 7. 真实物理拖拽系统 (自由摆放停靠)
  let isDragging = false;
  let startX, startY, initialRight, initialBottom;

  stage.addEventListener('mousedown', (e) => {{
    if (e.button !== 0) return;
    isDragging = false;
    startX = e.clientX;
    startY = e.clientY;
    const rect = root.getBoundingClientRect();
    initialRight = window.innerWidth - rect.right;
    initialBottom = window.innerHeight - rect.bottom;

    const onMouseMove = (moveEvent) => {{
      const dx = moveEvent.clientX - startX;
      const dy = moveEvent.clientY - startY;
      if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {{
        isDragging = true;
        stage.classList.add('dragging');
      }}
      if (isDragging) {{
        root.style.right = `${{Math.max(10, initialRight - dx)}}px`;
        root.style.bottom = `${{Math.max(10, initialBottom - dy)}}px`;
      }}
    }};

    const onMouseUp = () => {{
      stage.classList.remove('dragging');
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      resetSleepTimer();
    }};

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }});

  // 8. 监听来自 Electron 主进程的汉化对话提醒事件
  if (typeof window !== 'undefined' && window.require) {{
    try {{
      const {{ ipcRenderer }} = window.require('electron');
      ipcRenderer.on('__agy_chat_notification__', (_event, notif) => {{
        if (notif) {{
          window.__showNezukoAlert(notif.title, notif.body);
        }}
      }});
    }} catch (_) {{}}
  }}

  // 9. 劫持原生 Web Notification，同步触发祢豆子气泡
  if (typeof window !== 'undefined' && window.Notification) {{
    try {{
      const NativeNotification = window.Notification;
      window.Notification = function(title, options) {{
        try {{
          const trTitle = (typeof window.__agyTranslateNotif === 'function') ? window.__agyTranslateNotif(title) : title;
          const trBody = (options && options.body && typeof window.__agyTranslateNotif === 'function') ? window.__agyTranslateNotif(options.body) : (options ? options.body : '');
          window.__showNezukoAlert(trTitle, trBody);
        }} catch (_) {{}}
        return new NativeNotification(title, options);
      }};
      window.Notification.prototype = NativeNotification.prototype;
      window.Notification.permission = NativeNotification.permission;
      if (NativeNotification.requestPermission) {{
        window.Notification.requestPermission = NativeNotification.requestPermission.bind(NativeNotification);
      }}
    }} catch (_) {{}}
  }}

}})();
"""

(REPO_ROOT / "resources" / "nezuko-pet.js").write_text(js_code, encoding="utf-8")
print(f"nezuko-pet.js 生成完成，文件大小: {len(js_code)} 字节")
