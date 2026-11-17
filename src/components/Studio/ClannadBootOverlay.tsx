import React, { useCallback, useEffect, useState } from 'react';
import {
  type ClannadBgmTrackId,
  loadCustomArtworkBlob,
  loadCustomArtworkMetaSync,
  stopActiveSplashBgm,
} from './clannadAudioEngine';
import {
  type ClannadSplashThemeId,
  SPLASH_SESSION_PLAYED_KEY,
  loadStudioSplashPrefs,
  normalizeSplashThemeId,
  pickBootSceneThemeId,
} from './clannadSplashData';
import { ClannadSplashStage } from './ClannadSplashStage';

export interface FullscreenSplashRequest {
  themeId: Exclude<ClannadSplashThemeId, 'none'>;
  durationMs?: number;
  musicEnabled?: boolean;
  bgmTrackId?: ClannadBgmTrackId;
  bgmVolume?: number;
  bgmStartOffsetSec?: number;
  cinemaLetterbox?: boolean;
  customArtworkUrl?: string | null;
}

/**
 * Antigravity Studio 主窗口《CLANNAD》原版名场面启动序幕与全屏剧场放映层
 * - 首次进入主窗口时按用户偏好（支持指定或随机邂逅名场面 + 背景音乐）播放一次，绝不阻塞主界面异步加载
 * - 支持通过 CustomEvent('studio:trigger-fullscreen-splash') 随时从剧场页唤起全屏沉浸放映
 */
export const ClannadBootOverlay: React.FC = () => {
  const [activeState, setActiveState] = useState<{
    visible: boolean;
    fading: boolean;
    themeId: Exclude<ClannadSplashThemeId, 'none'>;
    durationMs: number;
    musicEnabled: boolean;
    bgmTrackId: ClannadBgmTrackId;
    bgmVolume: number;
    bgmStartOffsetSec: number;
    cinemaLetterbox: boolean;
    customArtworkUrl?: string | null;
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
      const bootTheme = pickBootSceneThemeId(prefs);
      if (!prefs.studioBootEnabled || bootTheme === 'none') {
        return null;
      }
      sessionStorage.setItem(SPLASH_SESSION_PLAYED_KEY, '1');
      return {
        visible: true,
        fading: false,
        themeId: bootTheme,
        durationMs: prefs.durationMs,
        musicEnabled: prefs.musicBoxEnabled,
        bgmTrackId: prefs.bgmTrackId || 'follow-scene',
        bgmVolume: prefs.bgmVolume ?? 0.7,
        bgmStartOffsetSec: prefs.bgmStartOffsetSec ?? 0,
        cinemaLetterbox: prefs.cinemaLetterbox ?? true,
      };
    } catch {
      return null;
    }
  });

  const dismissNow = useCallback(() => {
    stopActiveSplashBgm();
    setActiveState((prev) => (prev ? { ...prev, fading: true } : null));
    window.setTimeout(() => {
      setActiveState(null);
    }, 380);
  }, []);

  // 自动加载可能存在的用户自定义原画截图（若无则默认使用内置京都动画原版剧照）
  useEffect(() => {
    if (!activeState || !activeState.visible || activeState.customArtworkUrl !== undefined) return;
    if (!loadCustomArtworkMetaSync()) return;
    let urlToClean: string | null = null;
    loadCustomArtworkBlob().then((blob) => {
      if (!blob) return;
      urlToClean = URL.createObjectURL(blob);
      setActiveState((prev) => (prev ? { ...prev, customArtworkUrl: urlToClean } : null));
    });
    return () => {
      if (urlToClean) URL.revokeObjectURL(urlToClean);
    };
  }, [activeState]);

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
      const prefs = loadStudioSplashPrefs();
      setActiveState({
        visible: true,
        fading: false,
        themeId: normalized,
        durationMs: detail.durationMs || prefs.durationMs || 4800,
        musicEnabled: detail.musicEnabled ?? prefs.musicBoxEnabled,
        bgmTrackId: detail.bgmTrackId ?? prefs.bgmTrackId ?? 'follow-scene',
        bgmVolume: detail.bgmVolume ?? prefs.bgmVolume ?? 0.7,
        bgmStartOffsetSec: detail.bgmStartOffsetSec ?? prefs.bgmStartOffsetSec ?? 0,
        cinemaLetterbox: detail.cinemaLetterbox ?? prefs.cinemaLetterbox ?? true,
        customArtworkUrl: detail.customArtworkUrl,
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
        bgmTrackId={activeState.bgmTrackId}
        bgmVolume={activeState.bgmVolume}
        bgmStartOffsetSec={activeState.bgmStartOffsetSec}
        cinemaLetterbox={activeState.cinemaLetterbox}
        customArtworkUrl={activeState.customArtworkUrl}
        onSkip={dismissNow}
      />
    </div>
  );
};
