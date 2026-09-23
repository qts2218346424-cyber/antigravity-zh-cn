/**
 * Antigravity Desktop Pet — Frontend Mascot Controller & IPC Bridge
 * Fully reactive, zero external dependencies, ultra-lightweight (<40MB RAM)
 */

(function () {
  'use strict';

  // --------------------------------------------------------------------------
  // 1. Constants & State Definitions
  // --------------------------------------------------------------------------
  const MASCOT_STATES = ['idle', 'thinking', 'task_finished', 'quota_low'];
  const MAX_AVATAR_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
  const LOW_QUOTA_COOLDOWN_MS = 15 * 60 * 1000; // 15 minutes cooldown

  // Storage Keys
  const STORAGE_KEY_AVATAR = 'antigravity_pet_avatar_v1';
  const STORAGE_KEY_CONFIG = 'antigravity_pet_config_v1';

  // State Store
  const appState = {
    currentState: 'idle',
    previousState: 'idle',
    stateTimer: null,
    avatarMode: 'default', // 'default' | 'preset' | 'custom'
    customAvatarData: null,
    activeProfileId: null,
    profiles: [],
    quota: null,
    isAlwaysOnTop: true,
    isClickThrough: false,
    lastQuotaAlertTimestamp: 0,
    activeToastQueue: [],
    lastNotificationHash: null,
    lastNotificationTime: 0
  };

  // --------------------------------------------------------------------------
  // 2. Dual-Shell Universal IPC Bridge (Tauri v2 + pywebview + Browser Mock)
  // --------------------------------------------------------------------------
  class IPCBridge {
    constructor() {
      this.isTauri = typeof window !== 'undefined' && Boolean(window.__TAURI__);
      this.isPyWebView = typeof window !== 'undefined' && Boolean(window.pywebview && window.pywebview.api);
    }

    async invoke(cmd, payload = {}) {
      // 1. Check if Tauri v2 is active
      if (this.isTauri && window.__TAURI__.core) {
        try {
          return await window.__TAURI__.core.invoke(cmd, payload);
        } catch (err) {
          console.warn(`[Tauri IPC] ${cmd} failed:`, err);
          throw err;
        }
      }

      // 2. Check if pywebview API is active
      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api[cmd] === 'function') {
        try {
          return await window.pywebview.api[cmd](payload);
        } catch (err) {
          console.warn(`[pywebview IPC] ${cmd} failed:`, err);
          throw err;
        }
      }

      // 3. Fallback to Local Mock Engine
      return this._mockInvoke(cmd, payload);
    }

    async _mockInvoke(cmd, payload) {
      // Deterministic mock fallback for offline browser testing
      switch (cmd) {
        case 'get_quota_status': {
          return {
            success: true,
            account_email: 'qts2218346424@gmail.com',
            profile_id: appState.activeProfileId || 'profile-primary',
            total_tokens: 1000000,
            used_tokens: 154000,
            remaining_tokens: 846000,
            remaining_percentage: 84.6,
            status: 'healthy',
            reset_time_utc: new Date(Date.now() + 86400000).toISOString(),
            is_cached: false,
            models: {
              'gemini-1.5-pro': { remaining_requests: 48, total_requests: 50, percentage: 96.0 },
              'gemini-1.5-flash': { remaining_requests: 950, total_requests: 1000, percentage: 95.0 }
            }
          };
        }
        case 'list_profiles': {
          return {
            success: true,
            active_profile_id: appState.activeProfileId || 'profile-primary',
            profiles: [
              {
                id: 'profile-primary',
                label: 'Main Account',
                email: 'qts2218346424@gmail.com',
                tier: 'pay_as_you_go',
                last_used: new Date().toISOString(),
                created_at: new Date(Date.now() - 7 * 86400000).toISOString()
              },
              {
                id: 'profile-backup',
                label: 'Work Workspace',
                email: 'workspace-dev@antigravity.io',
                tier: 'enterprise',
                last_used: new Date(Date.now() - 3600000).toISOString(),
                created_at: new Date(Date.now() - 14 * 86400000).toISOString()
              }
            ]
          };
        }
        case 'switch_profile': {
          appState.activeProfileId = payload.profile_id;
          const quota = await this._mockInvoke('get_quota_status');
          return {
            success: true,
            switched_to: payload.profile_id,
            email: payload.profile_id === 'profile-backup' ? 'workspace-dev@antigravity.io' : 'qts2218346424@gmail.com',
            backup_path: '~/.gemini/backups/credential_backup_mock.json',
            timestamp: new Date().toISOString(),
            quota: quota
          };
        }
        case 'import_avatar': {
          return {
            success: true,
            asset_id: 'custom-' + Date.now(),
            format: 'png',
            cached_path: payload.source_path || 'local_cache',
            is_animated: false
          };
        }
        case 'toggle_always_on_top': {
          const newState = typeof payload.enabled === 'boolean' ? payload.enabled : !appState.isAlwaysOnTop;
          appState.isAlwaysOnTop = newState;
          return { success: true, always_on_top: newState };
        }
        case 'toggle_click_through': {
          const newState = typeof payload.enabled === 'boolean' ? payload.enabled : !appState.isClickThrough;
          appState.isClickThrough = newState;
          return { success: true, click_through: newState };
        }
        case 'set_pet_state': {
          return { success: true, current_state: payload.state || 'idle' };
        }
        case 'send_notification': {
          return { success: true, notification_id: 'notif-' + Date.now() };
        }
        case 'open_external_url': {
          if (payload && payload.url) {
            try { window.open(payload.url, '_blank'); } catch (e) {}
          }
          return { success: true };
        }
        case 'check_for_updates': {
          return { success: true, checked: true };
        }
        default:
          return { success: false, error: `Unknown mock command: ${cmd}` };
      }
    }
  }

  const bridge = new IPCBridge();

  // --------------------------------------------------------------------------
  // 3. Magic-Byte Image Validation & Sanitization
  // --------------------------------------------------------------------------
  const MagicByteValidator = {
    async validateBuffer(buffer) {
      if (!buffer || buffer.byteLength === 0) {
        return { valid: false, error: 'INVALID_FILE_EMPTY' };
      }
      if (buffer.byteLength > MAX_AVATAR_SIZE_BYTES) {
        return { valid: false, error: 'FILE_EXCEEDS_MAX_SIZE_10MB' };
      }

      const bytes = new Uint8Array(buffer.slice(0, 16));

      // 1. PNG: 89 50 4E 47 0D 0A 1A 0A
      if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47 &&
          bytes[4] === 0x0D && bytes[5] === 0x0A && bytes[6] === 0x1A && bytes[7] === 0x0A) {
        return { valid: true, format: 'png', isAnimated: false };
      }

      // 2. GIF: 47 49 46 38 (37|39) 61 ("GIF87a" or "GIF89a")
      if (bytes[0] === 0x47 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x38 &&
          (bytes[4] === 0x37 || bytes[4] === 0x39) && bytes[5] === 0x61) {
        return { valid: true, format: 'gif', isAnimated: true };
      }

      // 3. WebP: 52 49 46 46 (RIFF) ... 57 45 42 50 (WEBP)
      if (bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46 &&
          bytes[8] === 0x57 && bytes[9] === 0x45 && bytes[10] === 0x42 && bytes[11] === 0x50) {
        return { valid: true, format: 'webp', isAnimated: false };
      }

      // 4. SVG: Detect XML text starting with or containing <svg
      try {
        const textDecoder = new TextDecoder('utf-8');
        const headerText = textDecoder.decode(buffer.slice(0, Math.min(1024, buffer.byteLength)));
        if (headerText.toLowerCase().includes('<svg')) {
          return { valid: true, format: 'svg', isAnimated: false };
        }
      } catch (e) {
        // Not a valid UTF-8 SVG string
      }

      return { valid: false, error: 'INVALID_MAGIC_BYTES' };
    },

    sanitizeSvg(svgText) {
      // Strip script tags and event handlers to prevent XSS (E7 compliance)
      return svgText
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/\son\w+="[^"]*"/gi, '')
        .replace(/\son\w+='[^']*'/gi, '')
        .replace(/javascript:/gi, '');
    }
  };

  // --------------------------------------------------------------------------
  // 4. Mascot State Machine & Presentation
  // --------------------------------------------------------------------------
  const PRESET_ANIMATIONS = {
    default: {
      nameZh: 'Gemini 灵动星灵（动态像素）',
      idle: 'assets/pet_idle.gif',
      thinking: 'assets/pet_thinking.gif',
      task_finished: 'assets/pet_celebrate.gif',
      quota_low: 'assets/pet_worry.gif'
    },
    paimon: {
      nameZh: '派蒙（Codex Pet 原神经典）',
      idle: 'assets/presets/paimon/idle.webp',
      thinking: 'assets/presets/paimon/waving.webp',
      task_finished: 'assets/presets/paimon/jumping.webp',
      quota_low: 'assets/presets/paimon/waving.webp'
    },
    doraemon: {
      nameZh: '哆啦A梦（Codex Pet 经典）',
      idle: 'assets/presets/doraemon/idle.webp',
      thinking: 'assets/presets/doraemon/waving.webp',
      task_finished: 'assets/presets/doraemon/jumping.webp',
      quota_low: 'assets/presets/doraemon/waving.webp'
    },
    gemini_chibi: {
      nameZh: 'Gemini 绒绒棉花糖',
      idle: 'assets/gemini_chibi.png',
      thinking: 'assets/gemini_chibi.png',
      task_finished: 'assets/gemini_chibi.png',
      quota_low: 'assets/gemini_chibi.png'
    }
  };

  const SPEECH_LINES = {
    idle: [
      "主人，我在！额度还很充足~",
      "今天也是元气满满的敲代码一天！",
      "代码写累了？记得喝杯水休息一下~",
      "随时待命！拖动我可以换个舒服的位置~",
      "有什么新的开发任务需要我协助吗？"
    ],
    thinking: [
      "正在全速思考与处理任务中...",
      "别着急，灵感马上就来！",
      "智能体联邦正在交叉会诊方案..."
    ],
    task_finished: [
      "耶！任务已经顺利完成啦！",
      "大功告成！代码已合并落地~",
      "太棒了！今天也是超高效的一天！"
    ],
    quota_low: [
      "报告主人！额度快见底了，记得切号~",
      "警告：当前 Token 额度不足 20%！",
      "建议及时切换备用账号继续工作！"
    ]
  };

  class MascotController {
    constructor() {
      this.appEl = document.getElementById('pet-app');
      this.mascotContainer = document.getElementById('mascot-container');
      this.spriteWrapper = document.getElementById('svg-mascot-wrapper');
      this.spriteImg = document.getElementById('mascot-sprite-img');
      this.customWrapper = document.getElementById('custom-avatar-wrapper');
      this.customImg = document.getElementById('custom-avatar-img');
      this.speechBubble = document.getElementById('pet-speech-bubble');
      this.speechText = document.getElementById('speech-bubble-text');
      this.currentPreset = 'default';
      this.speechTimer = null;
    }

    showSpeechBubble(text = null, durationMs = 2800) {
      if (!this.speechBubble) return;
      if (this.speechTimer) {
        clearTimeout(this.speechTimer);
      }
      if (!text) {
        const lines = SPEECH_LINES[appState.currentState] || SPEECH_LINES.idle;
        text = lines[Math.floor(Math.random() * lines.length)];
      }
      if (this.speechText) this.speechText.textContent = text;
      this.speechBubble.classList.add('show');
      this.speechTimer = setTimeout(() => {
        this.speechBubble.classList.remove('show');
      }, durationMs);
    }

    setState(newState, durationMs = 0) {
      if (!MASCOT_STATES.includes(newState)) {
        newState = 'idle';
      }

      MASCOT_STATES.forEach(st => this.appEl.classList.remove(`state-${st}`));
      this.appEl.classList.add(`state-${newState}`);

      appState.previousState = appState.currentState;
      appState.currentState = newState;

      // Update animated sprite if using preset mode or default
      if (appState.avatarMode === 'default' || appState.avatarMode === 'preset') {
        const preset = PRESET_ANIMATIONS[this.currentPreset] || PRESET_ANIMATIONS.default;
        const targetSrc = preset[newState] || preset.idle;
        if (this.spriteImg && this.spriteImg.getAttribute('src') !== targetSrc) {
          this.spriteImg.src = targetSrc;
        }
      }

      if (appState.stateTimer) {
        clearTimeout(appState.stateTimer);
        appState.stateTimer = null;
      }

      if (durationMs > 0) {
        appState.stateTimer = setTimeout(() => {
          const revertState = (appState.quota && appState.quota.remaining_percentage < 20) ? 'quota_low' : 'idle';
          this.setState(revertState);
        }, durationMs);
      }
    }

    setPreset(presetName) {
      this.currentPreset = presetName;
      appState.avatarMode = (presetName === 'default') ? 'default' : 'preset';
      appState.customAvatarData = null;

      if (this.spriteWrapper) this.spriteWrapper.style.display = 'flex';
      if (this.customWrapper) this.customWrapper.style.display = 'none';

      const preset = PRESET_ANIMATIONS[presetName] || PRESET_ANIMATIONS.default;
      const targetSrc = preset[appState.currentState] || preset.idle;
      if (this.spriteImg) {
        this.spriteImg.src = targetSrc;
      }

      try {
        localStorage.setItem(STORAGE_KEY_AVATAR, JSON.stringify({ mode: 'preset', preset: presetName }));
      } catch (e) {}

      this.showSpeechBubble(`已切换至形象：${preset.nameZh || presetName}`);
    }

    setAvatarMode(mode, dataUrl = null) {
      appState.avatarMode = mode;
      appState.customAvatarData = dataUrl;

      if (mode === 'default') {
        this.setPreset('default');
      } else {
        if (this.spriteWrapper) this.spriteWrapper.style.display = 'none';
        if (this.customWrapper) this.customWrapper.style.display = 'flex';
        this.customImg.src = dataUrl;
        this.customImg.onerror = () => {
          console.error('Failed to render custom avatar. Reverting to default mascot.');
          toastManager.showToast({
            title: '形象渲染失败',
            body: '自定义形象无法渲染，已自动恢复至默认 Gemini 星灵形象。',
            level: 'warning'
          });
          this.setPreset('default');
        };
        try {
          localStorage.setItem(STORAGE_KEY_AVATAR, JSON.stringify({ mode, dataUrl }));
        } catch (e) {}
      }
    }

    restorePersistedAvatar() {
      try {
        const saved = localStorage.getItem(STORAGE_KEY_AVATAR);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed.preset && PRESET_ANIMATIONS[parsed.preset]) {
            this.setPreset(parsed.preset);
            const thumb = document.querySelector(`[data-preset="${parsed.preset}"]`);
            if (thumb) {
              document.querySelectorAll('.preset-thumb').forEach(t => t.classList.remove('active'));
              thumb.classList.add('active');
            }
            return;
          }
          if (parsed.dataUrl) {
            this.setAvatarMode(parsed.mode, parsed.dataUrl);
            return;
          }
        }
      } catch (err) {}
      this.setPreset('default');
    }
  }

  // --------------------------------------------------------------------------
  // 5. Toast Notification Manager
  // --------------------------------------------------------------------------
  class ToastManager {
    constructor() {
      this.container = document.getElementById('toast-container');
    }

    showToast({ title = '反重力桌面提醒', body = '', level = 'info', duration_ms = 5000, action_url = '', action_text = '' }) {
      // E5 Boundary & Deduplication check
      const hash = `${title}:${body}:${level}:${action_url}`;
      const now = Date.now();
      if (appState.lastNotificationHash === hash && (now - appState.lastNotificationTime < 3000)) {
        return; // Suppress duplicate burst
      }
      appState.lastNotificationHash = hash;
      appState.lastNotificationTime = now;

      // Limit concurrent toasts
      if (this.container.children.length >= 3) {
        const oldest = this.container.children[0];
        if (oldest) oldest.remove();
      }

      const card = document.createElement('div');
      card.className = `toast-card ${level}`;

      let icon = '✦';
      if (level === 'success') icon = '✔';
      if (level === 'warning') icon = '⚠';
      if (level === 'error') icon = '✖';

      const actionHtml = action_url ? `
        <div class="toast-action-row">
          <button class="toast-action-btn no-drag" type="button">${this._escapeHtml(action_text || '立即查看')} ↗</button>
        </div>
      ` : '';

      card.innerHTML = `
        <div class="toast-header">
          <div class="toast-title-group">
            <span class="toast-icon">${icon}</span>
            <span class="toast-title">${this._escapeHtml(title)}</span>
          </div>
          <button class="toast-close-btn no-drag" aria-label="Dismiss">&times;</button>
        </div>
        <div class="toast-body">${this._escapeHtml(body)}</div>
        ${actionHtml}
        <div class="toast-progress-bar">
          <div class="toast-progress-fill"></div>
        </div>
      `;

      const closeBtn = card.querySelector('.toast-close-btn');
      const progressFill = card.querySelector('.toast-progress-fill');
      const actionBtn = card.querySelector('.toast-action-btn');

      let isDismissed = false;
      const dismiss = () => {
        if (isDismissed) return;
        isDismissed = true;
        card.classList.add('dismissing');
        setTimeout(() => card.remove(), 250);
      };

      closeBtn.addEventListener('click', dismiss);

      if (actionBtn && action_url) {
        actionBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          bridge.invoke('open_external_url', { url: action_url });
        });
      }

      // Auto-dismiss countdown
      progressFill.style.transition = `transform ${duration_ms}ms linear`;
      progressFill.style.transform = 'scaleX(1)';
      requestAnimationFrame(() => {
        progressFill.style.transform = 'scaleX(0)';
      });

      const timer = setTimeout(dismiss, duration_ms);
      card.addEventListener('mouseenter', () => {
        clearTimeout(timer);
        progressFill.style.transition = 'none';
      });

      this.container.appendChild(card);
    }

    _escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }
  }

  // --------------------------------------------------------------------------
  // 6. Quota Tracker & Presenter
  // --------------------------------------------------------------------------
  class QuotaTracker {
    constructor(mascotCtrl, toastMgr) {
      this.mascotCtrl = mascotCtrl;
      this.toastMgr = toastMgr;
      this.badge = document.getElementById('quota-badge');
      this.dot = document.getElementById('quota-indicator-dot');
      this.text = document.getElementById('quota-text');
      this.profileLabel = document.getElementById('quota-profile-label');
      this.card = document.getElementById('quota-details-card');
      this.cardTitle = document.getElementById('quota-card-title');
      this.cardEmail = document.getElementById('quota-card-email');
      this.tokensUsed = document.getElementById('quota-tokens-used');
      this.tokensTotal = document.getElementById('quota-tokens-total');
      this.barFill = document.getElementById('quota-bar-fill');
      this.resetTime = document.getElementById('quota-reset-time');
      this.modelsList = document.getElementById('quota-models-list');

      this._setupListeners();
    }

    _setupListeners() {
      // Toggle detailed popover card
      this.badge.addEventListener('click', (e) => {
        e.stopPropagation();
        this.card.classList.toggle('show');
      });

      document.addEventListener('click', (e) => {
        if (!this.card.contains(e.target) && !this.badge.contains(e.target)) {
          this.card.classList.remove('show');
        }
      });
    }

    async refreshQuota(forceRefresh = false) {
      try {
        const quota = await bridge.invoke('get_quota_status', { force_refresh: forceRefresh });
        if (quota && quota.success !== false) {
          appState.quota = quota;
          this.render(quota);
          this._checkLowQuotaAlert(quota);
        }
      } catch (err) {
        console.warn('Failed to refresh quota:', err);
      }
    }

    render(quota) {
      // Calculate clamped percentage safely (prevent division by zero, E9/E10)
      let percentage = 0;
      if (quota.total_tokens && quota.total_tokens > 0) {
        percentage = ((quota.remaining_tokens || 0) / quota.total_tokens) * 100;
      } else if (typeof quota.remaining_percentage === 'number') {
        percentage = quota.remaining_percentage;
      }
      percentage = Math.max(0, Math.min(100, Math.round(percentage * 10) / 10));

      // Color coding & class setup
      this.badge.classList.remove('healthy', 'warning', 'critical');
      let statusClass = 'healthy';
      let fillColor = 'var(--quota-healthy)';
      let statusTextZh = '额度充足';

      if (percentage <= 0) {
        statusClass = 'critical';
        statusTextZh = '已耗尽';
        fillColor = 'var(--quota-critical)';
        this.text.textContent = '0% 已耗尽';
      } else if (percentage < 20) {
        statusClass = 'critical';
        statusTextZh = '告急';
        fillColor = 'var(--quota-critical)';
        this.text.textContent = `${percentage}% 告急`;
      } else if (percentage <= 50) {
        statusClass = 'warning';
        statusTextZh = '适中';
        fillColor = 'var(--quota-warning)';
        this.text.textContent = `${percentage}%`;
      } else {
        statusClass = 'healthy';
        statusTextZh = '充足';
        fillColor = 'var(--quota-healthy)';
        this.text.textContent = `${percentage}%`;
      }

      this.badge.classList.add(statusClass);
      this.profileLabel.textContent = quota.account_email ? quota.account_email.split('@')[0] : '当前账号';

      // Detailed Card Content
      this.cardTitle.textContent = `反重力模型额度 (${statusTextZh})`;
      this.cardEmail.textContent = quota.account_email || '当前活跃账号';
      this.tokensUsed.textContent = (quota.used_tokens || 0).toLocaleString();
      this.tokensTotal.textContent = (quota.total_tokens || 0).toLocaleString();

      this.barFill.style.width = `${percentage}%`;
      this.barFill.style.background = fillColor;

      if (quota.reset_time_utc) {
        try {
          const resetDate = new Date(quota.reset_time_utc);
          this.resetTime.textContent = resetDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
          this.resetTime.textContent = quota.reset_time_utc;
        }
      } else {
        this.resetTime.textContent = '暂无记录';
      }

      // Models breakdown
      if (quota.models && Object.keys(quota.models).length > 0) {
        this.modelsList.innerHTML = Object.entries(quota.models)
          .map(([model, info]) => `
            <div class="model-item">
              <span>${model}</span>
              <span>${info.remaining_requests}/${info.total_requests} 请求 (${info.percentage}%)</span>
            </div>
          `).join('');
      } else {
        this.modelsList.innerHTML = '<div class="model-item"><span>状态</span><span>标准配额</span></div>';
      }
    }

    _checkLowQuotaAlert(quota) {
      const pct = typeof quota.remaining_percentage === 'number' ? quota.remaining_percentage : 100;
      if (pct < 20) {
        const now = Date.now();
        // Cooldown check (15 minutes, F2.5 / E14)
        if (now - appState.lastQuotaAlertTimestamp > LOW_QUOTA_COOLDOWN_MS) {
          appState.lastQuotaAlertTimestamp = now;
          this.mascotCtrl.setState('quota_low');
          this.toastMgr.showToast({
            title: '额度告急提醒',
            body: `反重力模型额度已不足 (${pct.toFixed(1)}%)，建议及时切换账号备用。`,
            level: 'warning',
            duration_ms: 7000
          });
        }
      }
    }
  }

  // --------------------------------------------------------------------------
  // 7. Profile Switcher Modal Controller
  // --------------------------------------------------------------------------
  class ProfileModalController {
    constructor(mascotCtrl, quotaTracker, toastMgr) {
      this.mascotCtrl = mascotCtrl;
      this.quotaTracker = quotaTracker;
      this.toastMgr = toastMgr;
      this.backdrop = document.getElementById('modal-profiles');
      this.listContainer = document.getElementById('profile-list-container');
      this.btnOpen = document.getElementById('btn-profile-switcher');
      this.btnClose = document.getElementById('btn-close-profiles');

      this._setupListeners();
    }

    _setupListeners() {
      this.btnOpen.addEventListener('click', () => this.open());
      this.btnClose.addEventListener('click', () => this.close());
      this.backdrop.addEventListener('click', (e) => {
        if (e.target === this.backdrop) this.close();
      });
    }

    async open() {
      this.backdrop.classList.add('open');
      await this.loadProfiles();
    }

    close() {
      this.backdrop.classList.remove('open');
    }

    async loadProfiles() {
      this.listContainer.innerHTML = '<div style="text-align:center; padding:12px; color:var(--color-text-muted);">Loading profiles...</div>';
      try {
        const res = await bridge.invoke('list_profiles');
        if (res && res.success) {
          appState.profiles = res.profiles || [];
          appState.activeProfileId = res.active_profile_id;
          this.renderProfiles();
        } else {
          this.listContainer.innerHTML = '<div style="text-align:center; padding:12px; color:var(--toast-error);">Failed to load profiles.</div>';
        }
      } catch (err) {
        this.listContainer.innerHTML = `<div style="text-align:center; padding:12px; color:var(--toast-error);">${err.message || 'Error loading profiles'}</div>`;
      }
    }

    renderProfiles() {
      if (appState.profiles.length === 0) {
        this.listContainer.innerHTML = '<div style="text-align:center; padding:12px; color:var(--color-text-muted);">No profiles found in store.</div>';
        return;
      }

      this.listContainer.innerHTML = appState.profiles.map(p => {
        const isActive = p.id === appState.activeProfileId;
        return `
          <div class="profile-item ${isActive ? 'active' : ''}">
            <div class="profile-info">
              <div class="profile-label-row">
                <span class="profile-label-text">${this._escape(p.label)}</span>
                ${isActive ? '<span class="active-pill">当前使用</span>' : ''}
              </div>
              <div class="profile-email-text">${this._escape(p.email)}</div>
            </div>
            ${!isActive ? `<button class="btn-switch-profile" data-profile-id="${p.id}">切换</button>` : ''}
          </div>
        `;
      }).join('');

      // Attach switch handlers
      this.listContainer.querySelectorAll('.btn-switch-profile').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          const profileId = e.currentTarget.getAttribute('data-profile-id');
          await this.executeSwitch(profileId);
        });
      });
    }

    async executeSwitch(profileId) {
      this.toastMgr.showToast({
        title: '正在切换账号...',
        body: `正在无缝切换至配置：${profileId}`,
        level: 'info',
        duration_ms: 2500
      });

      try {
        const res = await bridge.invoke('switch_profile', { profile_id: profileId, create_backup: true });
        if (res && res.success) {
          appState.activeProfileId = profileId;
          this.toastMgr.showToast({
            title: '账号切换成功！',
            body: `已生效新账号：${res.email || profileId}`,
            level: 'success',
            duration_ms: 4000
          });
          this.close();
          // Immediately refresh quota and mascot state
          await this.quotaTracker.refreshQuota(true);
          this.mascotCtrl.setState('task_finished', 3000);
        } else {
          this.toastMgr.showToast({
            title: '切换失败',
            body: res.error || '无法完成原子级凭据切换',
            level: 'error'
          });
        }
      } catch (err) {
        this.toastMgr.showToast({
          title: '切换发生异常',
          body: err.message || '账号切换执行异常',
          level: 'error'
        });
      }
    }

    _escape(s) {
      return (s || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
  }

  // --------------------------------------------------------------------------
  // 8. Avatar Importer & Settings Controller
  // --------------------------------------------------------------------------
  class AvatarModalController {
    constructor(mascotCtrl, toastMgr) {
      this.mascotCtrl = mascotCtrl;
      this.toastMgr = toastMgr;
      this.backdrop = document.getElementById('modal-avatar');
      this.btnOpen = document.getElementById('btn-avatar-picker');
      this.btnClose = document.getElementById('btn-close-avatar');
      this.dropZone = document.getElementById('avatar-drop-zone');
      this.fileInput = document.getElementById('avatar-file-input');
      this.presetThumbs = document.querySelectorAll('.preset-thumb');

      this._setupListeners();
    }

    _setupListeners() {
      this.btnOpen.addEventListener('click', () => this.open());
      this.btnClose.addEventListener('click', () => this.close());
      this.backdrop.addEventListener('click', (e) => {
        if (e.target === this.backdrop) this.close();
      });

      // Drop zone click triggers file input
      this.dropZone.addEventListener('click', () => this.fileInput.click());

      // File input change
      this.fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          this.handleFile(e.target.files[0]);
        }
      });

      // Drag and drop events on dropzone
      ['dragenter', 'dragover'].forEach(name => {
        this.dropZone.addEventListener(name, (e) => {
          e.preventDefault();
          this.dropZone.classList.add('dragover');
        });
      });

      ['dragleave', 'drop'].forEach(name => {
        this.dropZone.addEventListener(name, (e) => {
          e.preventDefault();
          this.dropZone.classList.remove('dragover');
        });
      });

      this.dropZone.addEventListener('drop', (e) => {
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
          this.handleFile(e.dataTransfer.files[0]);
        }
      });

      // Drag and drop onto pet viewport directly!
      const mascotViewport = document.getElementById('mascot-viewport');
      mascotViewport.addEventListener('dragover', (e) => e.preventDefault());
      mascotViewport.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
          this.handleFile(e.dataTransfer.files[0]);
        }
      });

      // Preset avatar choices
      this.presetThumbs.forEach(thumb => {
        thumb.addEventListener('click', () => {
          const presetName = thumb.getAttribute('data-preset');
          this.loadPreset(presetName);
        });
      });

      // External Link to Codex Pet community gallery
      const linkCodexpet = document.getElementById('link-open-codexpet');
      if (linkCodexpet) {
        linkCodexpet.addEventListener('click', (e) => {
          e.preventDefault();
          bridge.invoke('open_external_url', { url: 'https://codexpet.top' });
        });
      }
    }

    open() {
      this.backdrop.classList.add('open');
    }

    close() {
      this.backdrop.classList.remove('open');
    }

    loadPreset(presetName) {
      this.presetThumbs.forEach(t => t.classList.remove('active'));
      const activeThumb = document.querySelector(`[data-preset="${presetName}"]`);
      if (activeThumb) activeThumb.classList.add('active');

      this.mascotCtrl.setPreset(presetName);
      this.toastMgr.showToast({
        title: '桌宠已切换',
        body: `当前形象已更新至：${(PRESET_ANIMATIONS[presetName] && PRESET_ANIMATIONS[presetName].nameZh) || presetName}`,
        level: 'success',
        duration_ms: 2500
      });
      this.close();
    }

    async handleFile(file) {
      if (!file) return;

      // 1. Check size guard (10MB limit, E6)
      if (file.size === 0) {
        this.toastMgr.showToast({ title: '无效文件', body: '所选文件为空 (0 字节)。', level: 'error' });
        return;
      }
      if (file.size > MAX_AVATAR_SIZE_BYTES) {
        this.toastMgr.showToast({ title: '文件过大', body: '形象图片大小不得超过 10MB。', level: 'error' });
        return;
      }

      // 2. Read array buffer for magic-byte check
      const reader = new FileReader();
      reader.onload = async () => {
        const buffer = reader.result;
        const validation = await MagicByteValidator.validateBuffer(buffer);

        if (!validation.valid) {
          this.toastMgr.showToast({
            title: '不支持的文件格式',
            body: `文件魔数校验未通过 (${validation.error})。请选用 PNG、GIF、WebP 或 SVG。`,
            level: 'error'
          });
          return;
        }

        // 3. Process valid image into data URL
        if (validation.format === 'svg') {
          const textDecoder = new TextDecoder('utf-8');
          const rawSvg = textDecoder.decode(buffer);
          const cleanSvg = MagicByteValidator.sanitizeSvg(rawSvg);
          const dataUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(cleanSvg);
          this.mascotCtrl.setAvatarMode('custom', dataUrl);
        } else {
          const blob = new Blob([buffer], { type: `image/${validation.format}` });
          const blobUrl = URL.createObjectURL(blob);
          this.mascotCtrl.setAvatarMode('custom', blobUrl);
        }

        this.toastMgr.showToast({
          title: '形象更新成功！',
          body: `已成功导入自定义 ${validation.format.toUpperCase()} 形象。`,
          level: 'success'
        });
        this.close();
      };

      reader.onerror = () => {
        this.toastMgr.showToast({ title: '读取异常', body: '无法读取所选图片文件。', level: 'error' });
      };

      reader.readAsArrayBuffer(file);
    }
  }

  // --------------------------------------------------------------------------
  // 9. State Simulator & Quick Actions Controller
  // --------------------------------------------------------------------------
  class SimulatorController {
    constructor(mascotCtrl, toastMgr, quotaTracker) {
      this.mascotCtrl = mascotCtrl;
      this.toastMgr = toastMgr;
      this.quotaTracker = quotaTracker;
      this.backdrop = document.getElementById('modal-simulator');
      this.btnOpen = document.getElementById('btn-state-sim');
      this.btnClose = document.getElementById('btn-close-sim');

      this._setupListeners();
    }

    _setupListeners() {
      this.btnOpen.addEventListener('click', () => this.backdrop.classList.add('open'));
      this.btnClose.addEventListener('click', () => this.backdrop.classList.remove('open'));
      this.backdrop.addEventListener('click', (e) => {
        if (e.target === this.backdrop) this.backdrop.classList.remove('open');
      });

      // Quick State Buttons
      document.querySelectorAll('.btn-sim-state').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const state = e.currentTarget.getAttribute('data-state');
          this.mascotCtrl.setState(state);
          const stateNamesZh = {
            idle: '空闲待机',
            thinking: '深度思考',
            task_finished: '任务完成',
            quota_low: '额度告急'
          };
          this.toastMgr.showToast({ title: '动作状态切换', body: `宠物已切换至状态：“${stateNamesZh[state] || state}”`, level: 'info' });
          this.backdrop.classList.remove('open');
        });
      });

      // Task Completion Event Simulation
      document.getElementById('sim-task-complete').addEventListener('click', () => {
        this.mascotCtrl.setState('task_finished', 5000);
        this.toastMgr.showToast({
          title: '智能体任务已完成！',
          body: '代码构建与汉化审查任务已成功执行完毕（耗时 12.4 秒）。',
          level: 'success',
          duration_ms: 5000
        });
        this.backdrop.classList.remove('open');
      });

      // Task Failure Simulation
      document.getElementById('sim-task-failed').addEventListener('click', () => {
        this.mascotCtrl.setState('quota_low', 4000);
        this.toastMgr.showToast({
          title: '任务执行失败',
          body: '智能体执行异常：网络连接超时或上游服务拒绝。',
          level: 'error',
          duration_ms: 5000
        });
        this.backdrop.classList.remove('open');
      });

      // Low Quota Simulation
      document.getElementById('sim-quota-drop').addEventListener('click', () => {
        const simulatedQuota = {
          success: true,
          account_email: 'qts2218346424@gmail.com',
          total_tokens: 1000000,
          used_tokens: 880000,
          remaining_tokens: 120000,
          remaining_percentage: 12.0,
          status: 'critical',
          reset_time_utc: new Date(Date.now() + 3600000).toISOString(),
          models: {
            'gemini-1.5-pro': { remaining_requests: 3, total_requests: 50, percentage: 6.0 }
          }
        };
        this.quotaTracker.render(simulatedQuota);
        this.mascotCtrl.setState('quota_low');
        this.toastMgr.showToast({
          title: '额度告急提醒',
          body: '反重力模型额度已降至 12.0%（已触发黄色紧急告警）。',
          level: 'warning',
          duration_ms: 6000
        });
        this.backdrop.classList.remove('open');
      });
    }
  }

  // --------------------------------------------------------------------------
  // 10. Window Controls & Dragging Support
  // --------------------------------------------------------------------------
  class WindowControls {
    constructor(toastMgr) {
      this.toastMgr = toastMgr;
      this.appEl = document.getElementById('pet-app');
      this.btnPin = document.getElementById('btn-toggle-pin');
      this.btnGhost = document.getElementById('btn-toggle-ghost');
      this.btnMin = document.getElementById('btn-minimize');

      this._setupControls();
      this._setupMouseDragFallback();
      this._setupHotkeys();
    }

    _setupControls() {
      // Toggle Always on Top
      this.btnPin.addEventListener('click', async () => {
        try {
          const res = await bridge.invoke('toggle_always_on_top');
          if (res && res.success) {
            appState.isAlwaysOnTop = res.always_on_top;
            this.btnPin.classList.toggle('active', res.always_on_top);
            this.toastMgr.showToast({
              title: '窗口置顶',
              body: res.always_on_top ? '始终置顶：已开启' : '始终置顶：已关闭',
              level: 'info',
              duration_ms: 2000
            });
          }
        } catch (e) {
          console.warn('Could not toggle always on top:', e);
        }
      });

      // Toggle Click-Through Mode
      this.btnGhost.addEventListener('click', async () => {
        await this.setClickThrough(!appState.isClickThrough);
      });

      // Minimize to Tray / Hide
      this.btnMin.addEventListener('click', async () => {
        if (window.__TAURI__ && window.__TAURI__.window) {
          window.__TAURI__.window.getCurrentWindow().hide();
        } else if (window.pywebview && window.pywebview.api && window.pywebview.api.hide_window) {
          window.pywebview.api.hide_window();
        } else {
          this.toastMgr.showToast({ title: '隐藏至托盘', body: '已最小化至右下角系统托盘。', level: 'info' });
        }
      });
    }

    async setClickThrough(enable) {
      try {
        const res = await bridge.invoke('toggle_click_through', { enabled: enable });
        appState.isClickThrough = Boolean(res && res.click_through !== undefined ? res.click_through : enable);
        this.appEl.classList.toggle('click-through-active', appState.isClickThrough);
        this.btnGhost.classList.toggle('active', appState.isClickThrough);

        if (appState.isClickThrough) {
          this.toastMgr.showToast({
            title: '鼠标穿透模式已开启',
            body: '光标已穿透宠物。按快捷键 Ctrl+Alt+P 或右键托盘图标可恢复交互。',
            level: 'info',
            duration_ms: 4000
          });
        }
      } catch (err) {
        console.warn('Failed to toggle click through:', err);
      }
    }

    _setupMouseDragFallback() {
      let isMouseDown = false;
      let startX = 0, startY = 0;
      let hasMoved = false;

      const mascotViewport = document.getElementById('mascot-viewport');
      if (!mascotViewport) return;

      mascotViewport.addEventListener('mousedown', async (e) => {
        if (e.button === 0 && !e.target.closest('.no-drag, button, input, a')) {
          isMouseDown = true;
          hasMoved = false;
          startX = e.clientX;
          startY = e.clientY;

          // 1. Instant native Win32 window drag (144Hz zero-lag drag)
          try {
            bridge.invoke('start_drag');
          } catch (err) {}

          // 2. Tauri v2 fallback
          if (window.__TAURI__ && window.__TAURI__.window) {
            try {
              await window.__TAURI__.window.getCurrentWindow().startDragging();
              return;
            } catch (err) {}
          }
        }
      });

      window.addEventListener('mousemove', (e) => {
        if (isMouseDown) {
          if (Math.abs(e.clientX - startX) > 4 || Math.abs(e.clientY - startY) > 4) {
            hasMoved = true;
          }
        }
      });

      window.addEventListener('mouseup', () => {
        if (isMouseDown && !hasMoved) {
          // Click mascot: instant playful happy jump reaction + Chinese speech bubble!
          if (window.__ANTIGRAVITY_PET__) {
            const pet = window.__ANTIGRAVITY_PET__;
            const cur = pet.getAppState().currentState;
            if (cur === 'idle') {
              pet.setState('task_finished', 2200);
            }
            if (pet.mascotCtrl && typeof pet.mascotCtrl.showSpeechBubble === 'function') {
              pet.mascotCtrl.showSpeechBubble();
            }
          }
        }
        isMouseDown = false;
      });

      // Hover over mascot triggers friendly speech bubble
      mascotViewport.addEventListener('mouseenter', () => {
        if (window.__ANTIGRAVITY_PET__ && window.__ANTIGRAVITY_PET__.mascotCtrl) {
          window.__ANTIGRAVITY_PET__.mascotCtrl.showSpeechBubble(null, 2500);
        }
      });

      // Right-click mascot: toggle thinking/idle state
      mascotViewport.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        if (window.__ANTIGRAVITY_PET__) {
          const cur = window.__ANTIGRAVITY_PET__.getAppState().currentState;
          const next = cur === 'idle' ? 'thinking' : 'idle';
          window.__ANTIGRAVITY_PET__.setState(next, next === 'thinking' ? 3000 : 0);
        }
      });
    }

    _setupHotkeys() {
      // Global shortcut listener to exit click-through (Ctrl+Alt+P or Escape)
      window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey && e.altKey && (e.key === 'p' || e.key === 'P')) || e.key === 'Escape') {
          if (appState.isClickThrough) {
            this.setClickThrough(false);
          }
        }
      });
    }
  }

  // --------------------------------------------------------------------------
  // 11. Main App Initialization
  // --------------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', async () => {
    const mascotCtrl = new MascotController();
    const toastMgr = new ToastManager();
    const quotaTracker = new QuotaTracker(mascotCtrl, toastMgr);
    const profileModal = new ProfileModalController(mascotCtrl, quotaTracker, toastMgr);
    const avatarModal = new AvatarModalController(mascotCtrl, toastMgr);
    const simCtrl = new SimulatorController(mascotCtrl, toastMgr, quotaTracker);
    const winControls = new WindowControls(toastMgr);

    // Restore saved avatar preference
    mascotCtrl.restorePersistedAvatar();

    // Initial Quota Refresh
    await quotaTracker.refreshQuota();

    // Periodic Quota Polling (every 30 seconds)
    setInterval(() => {
      quotaTracker.refreshQuota();
    }, 30000);

    // Reveal Tauri window once fully initialized (eliminates white-flash glitch on Windows)
    if (window.__TAURI__ && window.__TAURI__.window) {
      try {
        await window.__TAURI__.window.getCurrentWindow().show();
      } catch (e) {
        // window already visible
      }
    }

    // Expose global controller API for external automation / pywebview bridge
    window.__ANTIGRAVITY_PET__ = {
      mascotCtrl: mascotCtrl,
      setState: (st, dur) => mascotCtrl.setState(st, dur),
      refreshQuota: () => quotaTracker.refreshQuota(true),
      showToast: (opts) => toastMgr.showToast(opts),
      switchProfile: (id) => profileModal.executeSwitch(id),
      setClickThrough: (en) => winControls.setClickThrough(en),
      getAppState: () => ({ ...appState })
    };

    console.log('[Antigravity Desktop Pet] Initialized successfully.');
  });
})();
