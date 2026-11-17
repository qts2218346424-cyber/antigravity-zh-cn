import React, { useState } from 'react';
import {
  Check,
  Film,
  Maximize2,
  Music,
  Palette,
  PowerOff,
  Send,
  Sparkles,
  Timer,
} from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
import {
  CLANNAD_SPLASH_THEMES,
  type ClannadSplashThemeId,
  type StudioSplashPrefs,
  getSplashThemeSpec,
  loadStudioSplashPrefs,
  normalizeSplashThemeId,
  playClannadMusicBox,
  saveStudioSplashPrefs,
} from '../../components/Studio/clannadSplashData';
import { ClannadSplashStage } from '../../components/Studio/ClannadSplashStage';
import { studioService } from '../../services/studioService';
import type { StudioStatus } from '../../types/studio';

interface SplashTabProps {
  status: StudioStatus;
  onRefresh: () => Promise<void>;
}

const DURATION_OPTIONS: Array<{ value: 1800 | 2600 | 3800; label: string; desc: string }> = [
  { value: 1800, label: '轻快 · 1.8s', desc: '高频打开无感过渡' },
  { value: 2600, label: '标准 · 2.6s', desc: '均衡节奏推荐档位' },
  { value: 3800, label: '沉浸 · 3.8s', desc: '完整聆听八音盒动机' },
];

export const SplashTab: React.FC<SplashTabProps> = ({ status, onRefresh }) => {
  const [prefs, setPrefs] = useState<StudioSplashPrefs>(() => loadStudioSplashPrefs());
  const [previewThemeId, setPreviewThemeId] = useState<Exclude<ClannadSplashThemeId, 'none'>>(() =>
    prefs.themeId === 'none' ? 'clannad-orbs' : prefs.themeId,
  );
  const [busyAction, setBusyAction] = useState<string | null>(null);

  const activeSpec = getSplashThemeSpec(previewThemeId);
  const clientSplashId = normalizeSplashThemeId(
    status.splash_character === 'none' ? 'none' : status.splash_character,
  );

  const updatePrefs = (patch: Partial<StudioSplashPrefs>) => {
    const next: StudioSplashPrefs = { ...prefs, ...patch };
    setPrefs(next);
    saveStudioSplashPrefs(next);
  };

  const handleSelectTheme = (id: ClannadSplashThemeId) => {
    if (id === 'none') {
      updatePrefs({ studioBootEnabled: false, themeId: 'none' });
      showToast('已关闭 Studio 启动序幕动画（保持极速直达）', 'info');
    } else {
      setPreviewThemeId(id);
      updatePrefs({ studioBootEnabled: true, themeId: id });
      showToast(`已切换 Studio 启动动画为「${getSplashThemeSpec(id).name}」`, 'success');
    }
  };

  const handleFullscreenPlay = () => {
    window.dispatchEvent(
      new CustomEvent('studio:trigger-fullscreen-splash', {
        detail: {
          themeId: previewThemeId,
          durationMs: prefs.durationMs,
          musicEnabled: prefs.musicBoxEnabled,
        },
      }),
    );
  };

  const handleSyncToClient = async (targetCharacter: ClannadSplashThemeId) => {
    setBusyAction('sync_client');
    try {
      const res = await studioService.applyL10n({
        install_dir: status.install_dir || null,
        lang: status.lang || 'zh-cn',
        character: targetCharacter,
        enable_pet: false,
        enable_skin: status.enable_skin ?? true,
      });
      await onRefresh();
      showToast(res.message, res.success ? 'success' : 'warning');
    } catch (err) {
      showToast(`同步客户端启动序幕失败: ${String(err)}`, 'error');
    } finally {
      setBusyAction(null);
    }
  };

  const handleActivateLinkedSkin = async () => {
    setBusyAction('activate_skin');
    try {
      await studioService.activateSkin(activeSpec.linkedSkinId);
      await onRefresh();
      showToast(`已同步启用配套材质包「${activeSpec.name}」`, 'success');
    } catch (err) {
      showToast(`启用配套材质包失败: ${String(err)}`, 'error');
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* 顶部控制总览卡片 */}
      <div className="rounded-2xl border border-gray-200 dark:border-base-300 bg-white dark:bg-base-100 p-5 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Film className="w-5 h-5 text-pink-500" />
              <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">
                《CLANNAD》四季光学启动动画剧场
              </h2>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-pink-50 text-pink-600 dark:bg-pink-500/15 dark:text-pink-300">
                60fps 纯矢量 · 零视频体积膨胀
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              所有分镜均支持按 <code className="font-mono">ESC</code> / 空格或点击跳过按钮 0ms 瞬时进入工作台，并自动适配系统无障碍减弱动态设置。
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={handleFullscreenPlay}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-pink-500 to-amber-500 text-white shadow-sm hover:opacity-95 transition-opacity"
            >
              <Maximize2 className="w-3.5 h-3.5" />
              全屏沉浸放映
            </button>

            <button
              type="button"
              onClick={handleActivateLinkedSkin}
              disabled={busyAction !== null}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border border-pink-200 dark:border-pink-500/30 bg-pink-50/70 dark:bg-pink-500/10 text-pink-700 dark:text-pink-300 hover:bg-pink-100/80 dark:hover:bg-pink-500/20 transition-colors disabled:opacity-50"
            >
              <Palette className="w-3.5 h-3.5" />
              一键套用同名《CLANNAD》材质包
            </button>
          </div>
        </div>

        {/* Studio 本机启动参数调节条 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-3 border-t border-gray-100 dark:border-base-300">
          <label className="flex items-center justify-between rounded-xl border border-gray-200/80 dark:border-base-300 px-3.5 py-2.5 cursor-pointer hover:bg-gray-50/60 dark:hover:bg-base-200/50">
            <div>
              <div className="text-xs font-semibold text-gray-800 dark:text-gray-100">
                Studio 启动序幕开关
              </div>
              <div className="text-[11px] text-gray-500 dark:text-gray-400">
                打开本控制台时呈现《CLANNAD》序幕
              </div>
            </div>
            <input
              type="checkbox"
              className="toggle toggle-sm toggle-primary"
              checked={prefs.studioBootEnabled && prefs.themeId !== 'none'}
              onChange={(e) => {
                if (e.target.checked) {
                  updatePrefs({ studioBootEnabled: true, themeId: previewThemeId });
                } else {
                  updatePrefs({ studioBootEnabled: false });
                }
              }}
            />
          </label>

          <label className="flex items-center justify-between rounded-xl border border-gray-200/80 dark:border-base-300 px-3.5 py-2.5 cursor-pointer hover:bg-gray-50/60 dark:hover:bg-base-200/50">
            <div className="flex items-center gap-2">
              <Music className="w-4 h-4 text-amber-500 shrink-0" />
              <div>
                <div className="text-xs font-semibold text-gray-800 dark:text-gray-100">
                  八音盒琶音伴奏
                </div>
                <div className="text-[11px] text-gray-500 dark:text-gray-400">
                  WebAudio 合成五声清脆钟琴动机
                </div>
              </div>
            </div>
            <input
              type="checkbox"
              className="toggle toggle-sm toggle-warning"
              checked={prefs.musicBoxEnabled}
              onChange={(e) => {
                const nextVal = e.target.checked;
                updatePrefs({ musicBoxEnabled: nextVal });
                if (nextVal) {
                  playClannadMusicBox(previewThemeId);
                }
              }}
            />
          </label>

          <div className="flex items-center justify-between rounded-xl border border-gray-200/80 dark:border-base-300 px-3.5 py-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-800 dark:text-gray-100">
              <Timer className="w-4 h-4 text-sky-500" />
              <span>序幕时长</span>
            </div>
            <div className="flex items-center gap-1">
              {DURATION_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  title={opt.desc}
                  onClick={() => updatePrefs({ durationMs: opt.value })}
                  className={`px-2 py-1 rounded-lg text-[11px] font-medium transition-colors ${
                    prefs.durationMs === opt.value
                      ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-base-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 4 大《CLANNAD》剧场主题选择矩阵 + 极速关闭项 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {CLANNAD_SPLASH_THEMES.map((item) => {
          const isSelected = prefs.studioBootEnabled && prefs.themeId === item.id;
          const isPreviewing = previewThemeId === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => handleSelectTheme(item.id)}
              className={`group relative rounded-2xl border p-4 text-left transition-all ${
                isPreviewing
                  ? 'border-pink-400 dark:border-pink-400/70 ring-2 ring-pink-400/20 bg-white dark:bg-base-100 shadow-sm'
                  : 'border-gray-200 dark:border-base-300 bg-white/80 dark:bg-base-100/80 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className="h-2.5 w-10 rounded-full"
                  style={{
                    background: `linear-gradient(90deg, ${item.accent}, ${item.secondaryAccent})`,
                  }}
                />
                {isSelected && (
                  <span className="inline-flex items-center gap-0.5 text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                    <Check className="w-3 h-3" /> 已启用
                  </span>
                )}
              </div>
              <div className="text-xs font-bold text-gray-900 dark:text-gray-100">{item.name}</div>
              <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                {item.badge}
              </div>
            </button>
          );
        })}

        <button
          type="button"
          onClick={() => handleSelectTheme('none')}
          className={`rounded-2xl border p-4 text-left transition-all ${
            !prefs.studioBootEnabled || prefs.themeId === 'none'
              ? 'border-slate-500 ring-2 ring-slate-500/20 bg-slate-50 dark:bg-base-200'
              : 'border-gray-200 dark:border-base-300 bg-white/80 dark:bg-base-100/80 hover:border-gray-300'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <PowerOff className="w-4 h-4 text-gray-400" />
            {(!prefs.studioBootEnabled || prefs.themeId === 'none') && (
              <span className="text-[10px] font-bold text-slate-600 dark:text-slate-300">
                当前直达
              </span>
            )}
          </div>
          <div className="text-xs font-bold text-gray-900 dark:text-gray-100">
            关闭序幕 · 极速直达
          </div>
          <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1">
            不展示启动动画，秒入主界面
          </div>
        </button>
      </div>

      {/* 16:9 实时 60fps 宽银幕预览舞台 */}
      <div className="rounded-2xl border border-gray-200 dark:border-base-300 bg-white dark:bg-base-100 p-3 shadow-sm">
        <div className="h-[360px] sm:h-[420px] w-full overflow-hidden rounded-xl">
          <ClannadSplashStage
            themeId={previewThemeId}
            mode="preview"
            musicEnabled={false}
            onReplayMusic={() => playClannadMusicBox(previewThemeId)}
          />
        </div>
      </div>

      {/* Antigravity 官方客户端启动遮罩可选同步面板 */}
      <div className="rounded-2xl border border-gray-200 dark:border-base-300 bg-white dark:bg-base-100 p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1 max-w-2xl">
          <div className="flex items-center gap-2 text-xs font-bold text-gray-900 dark:text-gray-100">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span>同步注入至 Antigravity 官方客户端开机序幕（可选）</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-gray-100 dark:bg-base-200 text-gray-600 dark:text-gray-300">
              客户端当前：{status.splash_character === 'none' || !status.splash_character ? '官方极速启动' : getSplashThemeSpec(clientSplashId).name}
            </span>
          </div>
          <p className="text-[11.5px] text-gray-500 dark:text-gray-400">
            可将当前预览的「{activeSpec.name}」写入客户端 <code className="font-mono">dist/loadingOverlay.js</code>（内置 <code className="font-mono">getHubWebContents</code> 精准就绪感知与 5 秒硬超时防死锁保护）；亦可随时一键恢复官方原版极速启动。
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            disabled={busyAction !== null}
            onClick={() => handleSyncToClient(previewThemeId)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gray-900 text-white dark:bg-white dark:text-gray-900 hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            {busyAction === 'sync_client' ? '正在注入客户端...' : `注入「${activeSpec.shortName}」至客户端`}
          </button>

          <button
            type="button"
            disabled={busyAction !== null}
            onClick={() => handleSyncToClient('none')}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium border border-gray-200 dark:border-base-300 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-base-200 transition-colors disabled:opacity-50"
          >
            恢复客户端原版极速启动
          </button>
        </div>
      </div>
    </div>
  );
};
