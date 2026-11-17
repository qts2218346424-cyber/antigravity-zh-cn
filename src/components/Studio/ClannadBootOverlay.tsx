import React, { useCallback, useEffect, useState } from 'react';
import {
  type ClannadSplashThemeId,
  SPLASH_SESSION_PLAYED_KEY,
  loadStudioSplashPrefs,
  normalizeSplashThemeId,
} from './clannadSplashData';
import { ClannadSplashStage } from './ClannadSplashStage';

export interface FullscreenSplashRequest {
  themeId: Exclude<ClannadSplashThemeId, 'none'>;
  durationMs?: number;
  musicEnabled?: boolean;
}

/**
 * Antigravity Studio 主窗口《CLANNAD》启动序幕与全屏剧场放映层
 * - 首次进入主窗口时按用户偏好播放一次，绝不阻塞底部主界面的异步数据加载
 * - 支持通过 CustomEvent('studio:trigger-fullscreen-splash') 随时从剧场页唤起全屏沉浸预览
 */
export const ClannadBootOverlay: React.FC = () => {
  const [activeState, setActiveState] = useState<{
    visible: boolean;
    fading: boolean;
    themeId: Exclude<ClannadSplashThemeId, 'none'>;
    durationMs: number;
    musicEnabled: boolean;
  } | null>(() => {
    try {
      if (typeof window === 'undefined') return null;
      if (
        window.location.search.includes('mini') ||
        window.location.search.includes('pet')
      ) {
        return null;
      }
      if (sessionStorage.getItem(SPLASH_SESSION_PLAYED_KEY) === '1') {
        return null;
      }
      const prefs = loadStudioSplashPrefs();
      if (!prefs.studioBootEnabled || prefs.themeId === 'none') {
        return null;
      }
      sessionStorage.setItem(SPLASH_SESSION_PLAYED_KEY, '1');
      return {
        visible: true,
        fading: false,
        themeId: prefs.themeId,
        durationMs: prefs.durationMs,
        musicEnabled: prefs.musicBoxEnabled,
      };
    } catch {
      return null;
    }
  });

  const dismissNow = useCallback(() => {
    setActiveState((prev) => (prev ? { ...prev, fading: true } : null));
    window.setTimeout(() => {
      setActiveState(null);
    }, 380);
  }, []);

  // 自动定时退场守卫
  useEffect(() => {
    if (!activeState || !activeState.visible || activeState.fading) return;
    const timer = window.setTimeout(() => {
      dismissNow();
    }, activeState.durationMs);
    return () => window.clearTimeout(timer);
  }, [activeState, dismissNow]);

  // 监听来自「启动动画剧场」的全屏沉浸放映请求
  useEffect(() => {
    const handler = (ev: Event) => {
      const detail = (ev as CustomEvent<FullscreenSplashRequest>).detail;
      if (!detail) return;
      const normalized = normalizeSplashThemeId(detail.themeId);
      if (normalized === 'none') return;
      setActiveState({
        visible: true,
        fading: false,
        themeId: normalized,
        durationMs: detail.durationMs || 3200,
        musicEnabled: Boolean(detail.musicEnabled),
      });
    };
    window.addEventListener('studio:trigger-fullscreen-splash', handler);
    return () => window.removeEventListener('studio:trigger-fullscreen-splash', handler);
  }, []);

  if (!activeState || !activeState.visible) return null;

  return (
    <div
      className={`fixed inset-0 z-[120] transition-all duration-300 ease-out ${
        activeState.fading ? 'opacity-0 scale-[1.015] pointer-events-none' : 'opacity-100 scale-100'
      }`}
    >
      <ClannadSplashStage
        themeId={activeState.themeId}
        mode="overlay"
        durationMs={activeState.durationMs}
        musicEnabled={activeState.musicEnabled}
        onSkip={dismissNow}
      />
    </div>
  );
};
