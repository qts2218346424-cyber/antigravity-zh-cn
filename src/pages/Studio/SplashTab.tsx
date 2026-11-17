import React, { useEffect, useId, useRef, useState } from 'react';
import {
  Check,
  Disc3,
  Film,
  FolderOpen,
  ImagePlus,
  Maximize2,
  Music,
  Palette,
  PowerOff,
  Send,
  Shuffle,
  Sparkles,
  Timer,
  Trash2,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
import {
  BUILTIN_BGM_TRACKS,
  type ClannadBgmTrackId,
  type CustomBgmStoredMeta,
  clearCustomArtworkFile,
  clearCustomBgmFile,
  loadCustomArtworkBlob,
  loadCustomArtworkMetaSync,
  loadCustomBgmMetaSync,
  saveCustomArtworkFile,
  saveCustomBgmFile,
  startSplashBgm,
  stopActiveSplashBgm,
} from '../../components/Studio/clannadAudioEngine';
import {
  CLANNAD_SPLASH_THEMES,
  type ClannadSplashThemeId,
  type SplashDurationOption,
  type StudioSplashPrefs,
  getSplashThemeSpec,
  loadStudioSplashPrefs,
  normalizeSplashThemeId,
  resolveEffectiveBgmTrack,
  saveStudioSplashPrefs,
} from '../../components/Studio/clannadSplashData';
import { ClannadSplashStage } from '../../components/Studio/ClannadSplashStage';
import { studioService } from '../../services/studioService';
import type { StudioStatus } from '../../types/studio';

interface SplashTabProps {
  status: StudioStatus;
  onRefresh: () => Promise<void>;
}

const DURATION_OPTIONS: Array<{ value: SplashDurationOption; label: string; desc: string }> = [
  { value: 2600, label: '轻快 · 2.6s', desc: '高频打开快速过场' },
  { value: 4800, label: '标准 · 4.8s', desc: '均衡体验台词与画面' },
  { value: 8000, label: '剧场 · 8.0s', desc: '完整感受三幕催泪台词' },
  { value: 12000, label: '沉浸 · 12s', desc: '静心聆听副歌与名场面' },
];

function formatSecondsMmSs(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${String(m).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
}

export const SplashTab: React.FC<SplashTabProps> = ({ status, onRefresh }) => {
  const volumeSliderId = useId();
  const offsetSliderId = useId();
  const audioInputRef = useRef<HTMLInputElement>(null);
  const artworkInputRef = useRef<HTMLInputElement>(null);

  const [prefs, setPrefs] = useState<StudioSplashPrefs>(() => loadStudioSplashPrefs());
  const [previewThemeId, setPreviewThemeId] = useState<Exclude<ClannadSplashThemeId, 'none'>>(() =>
    prefs.themeId === 'none' ? 'clannad-sunflower' : prefs.themeId,
  );
  const [customBgmMeta, setCustomBgmMeta] = useState<CustomBgmStoredMeta | null>(() =>
    loadCustomBgmMetaSync(),
  );
  const [customArtworkMeta, setCustomArtworkMeta] = useState<CustomBgmStoredMeta | null>(() =>
    loadCustomArtworkMetaSync(),
  );
  const [customArtworkUrl, setCustomArtworkUrl] = useState<string | null>(null);
  const [isPreviewPlayingMusic, setIsPreviewPlayingMusic] = useState(false);
  const [busyAction, setBusyAction] = useState<string | null>(null);

  useEffect(() => {
    if (!customArtworkMeta) {
      setCustomArtworkUrl(null);
      return;
    }
    let revoked = false;
    let objUrl: string | null = null;
    loadCustomArtworkBlob().then((blob) => {
      if (revoked || !blob) return;
      objUrl = URL.createObjectURL(blob);
      setCustomArtworkUrl(objUrl);
    });
    return () => {
      revoked = true;
      if (objUrl) URL.revokeObjectURL(objUrl);
    };
  }, [customArtworkMeta]);

  const activeSpec = getSplashThemeSpec(previewThemeId);
  const clientSplashId = normalizeSplashThemeId(
    status.splash_character === 'none' ? 'none' : status.splash_character,
  );

  // 离开本页签时自动停止预览试听音乐，避免后台残留发声
  useEffect(() => {
    return () => {
      stopActiveSplashBgm();
    };
  }, []);

  const updatePrefs = (patch: Partial<StudioSplashPrefs>): StudioSplashPrefs => {
    const merged: StudioSplashPrefs = { ...prefs, ...patch };
    const saved = saveStudioSplashPrefs(merged);
    setPrefs(saved);
    return saved;
  };

  const triggerPreviewBgm = (nextPrefs: StudioSplashPrefs, targetTheme = previewThemeId) => {
    const effective = resolveEffectiveBgmTrack(nextPrefs, targetTheme);
    if (effective === 'off') {
      stopActiveSplashBgm();
      setIsPreviewPlayingMusic(false);
      return;
    }
    startSplashBgm({
      trackId: effective,
      volume: nextPrefs.bgmVolume ?? 0.7,
      startOffsetSec: nextPrefs.bgmStartOffsetSec ?? 0,
      loop: true,
      fallbackTrackId: getSplashThemeSpec(targetTheme).recommendedBgmId,
    });
    setIsPreviewPlayingMusic(true);
  };

  const handleToggleMusicPreview = () => {
    if (isPreviewPlayingMusic) {
      stopActiveSplashBgm();
      setIsPreviewPlayingMusic(false);
      return;
    }
    const candidatePrefs: StudioSplashPrefs =
      prefs.bgmTrackId === 'off' || !prefs.musicBoxEnabled
        ? { ...prefs, musicBoxEnabled: true, bgmTrackId: 'follow-scene' }
        : prefs;
    triggerPreviewBgm(candidatePrefs, previewThemeId);
  };

  const handleSelectTheme = (id: ClannadSplashThemeId) => {
    if (id === 'none') {
      stopActiveSplashBgm();
      setIsPreviewPlayingMusic(false);
      updatePrefs({ studioBootEnabled: false, themeId: 'none' });
      showToast('已关闭 Studio 启动序幕动画（保持极速直达）', 'info');
    } else {
      setPreviewThemeId(id);
      const next = updatePrefs({ studioBootEnabled: true, themeId: id });
      if (isPreviewPlayingMusic && next.bgmTrackId === 'follow-scene') {
        triggerPreviewBgm(next, id);
      }
      showToast(`已切换启动名场面为「${getSplashThemeSpec(id).name}」`, 'success');
    }
  };

  const handleSelectBgmTrack = (trackId: ClannadBgmTrackId) => {
    if (trackId === 'off') {
      stopActiveSplashBgm();
      setIsPreviewPlayingMusic(false);
      updatePrefs({ musicBoxEnabled: false, bgmTrackId: 'off' });
      showToast('已将启动序幕设为静音模式', 'info');
      return;
    }

    if (trackId === 'custom-file' && !customBgmMeta) {
      audioInputRef.current?.click();
      return;
    }

    const next = updatePrefs({ musicBoxEnabled: true, bgmTrackId: trackId });
    triggerPreviewBgm(next, previewThemeId);
  };

  const handleUploadCustomAudio = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;

    try {
      const meta = await saveCustomBgmFile(file);
      setCustomBgmMeta(meta);
      const next = updatePrefs({ musicBoxEnabled: true, bgmTrackId: 'custom-file' });
      triggerPreviewBgm(next, previewThemeId);
      showToast(`已导入本地背景音乐「${meta.fileName}」并开始试听`, 'success');
    } catch (err) {
      showToast(`导入音频失败: ${err instanceof Error ? err.message : String(err)}`, 'error');
    }
  };

  const handleClearCustomAudio = async () => {
    stopActiveSplashBgm();
    setIsPreviewPlayingMusic(false);
    await clearCustomBgmFile();
    setCustomBgmMeta(null);
    if (prefs.bgmTrackId === 'custom-file') {
      updatePrefs({ musicBoxEnabled: true, bgmTrackId: 'follow-scene', bgmStartOffsetSec: 0 });
    }
    showToast('已移除自定义本地音乐，恢复随场面智能配乐', 'info');
  };

  const handleUploadCustomArtwork = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    try {
      const meta = await saveCustomArtworkFile(file);
      setCustomArtworkMeta(meta);
      showToast(`已替换启动画面截图为「${meta.fileName}」`, 'success');
    } catch (err) {
      showToast(`导入截图失败: ${err instanceof Error ? err.message : String(err)}`, 'error');
    }
  };

  const handleClearCustomArtwork = async () => {
    await clearCustomArtworkFile();
    setCustomArtworkMeta(null);
    showToast('已恢复内置《CLANNAD》原版动画名场面剧照', 'info');
  };

  const handleFullscreenPlay = () => {
    stopActiveSplashBgm();
    setIsPreviewPlayingMusic(false);
    window.dispatchEvent(
      new CustomEvent('studio:trigger-fullscreen-splash', {
        detail: {
          themeId: previewThemeId,
          durationMs: prefs.durationMs,
          musicEnabled: prefs.musicBoxEnabled,
          bgmTrackId: prefs.bgmTrackId || 'follow-scene',
          bgmVolume: prefs.bgmVolume ?? 0.7,
          bgmStartOffsetSec: prefs.bgmStartOffsetSec ?? 0,
          cinemaLetterbox: prefs.cinemaLetterbox ?? true,
          customArtworkUrl,
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

  const currentBgmSelection: ClannadBgmTrackId = !prefs.musicBoxEnabled
    ? 'off'
    : prefs.bgmTrackId || 'follow-scene';

  return (
    <div className="space-y-6">
      {/* 隐藏的本地音频与画面截图选择器 */}
      <input
        ref={audioInputRef}
        type="file"
        accept="audio/*,.mp3,.flac,.wav,.ogg,.m4a,.aac"
        className="hidden"
        onChange={handleUploadCustomAudio}
      />
      <input
        ref={artworkInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/avif"
        className="hidden"
        onChange={handleUploadCustomArtwork}
      />

      {/* 顶部剧场总览与放映控制栏 */}
      <div className="rounded-2xl border border-gray-200 dark:border-base-300 bg-white dark:bg-base-100 p-5 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <Film className="w-5 h-5 text-pink-500" />
              <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">
                《CLANNAD》原版催泪名场面 · 启动动画与配乐剧场
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
                原动画剧照 · 多曲目与本地原声自选
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              精选京都动画原版四大催泪名场面与双语原声台词，支持自由选择背景音乐或导入本地 OST 原曲；按 <code className="font-mono">ESC</code> / 空格可 0ms 瞬时跳过并平滑淡出音乐。
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={handleFullscreenPlay}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-pink-500 via-rose-500 to-amber-500 text-white shadow-sm hover:opacity-95 transition-opacity"
            >
              <Maximize2 className="w-3.5 h-3.5" />
              全屏沉浸放映（含配乐）
            </button>

            <button
              type="button"
              onClick={handleActivateLinkedSkin}
              disabled={busyAction !== null}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border border-pink-200 dark:border-pink-500/30 bg-pink-50/70 dark:bg-pink-500/10 text-pink-700 dark:text-pink-300 hover:bg-pink-100/80 dark:hover:bg-pink-500/20 transition-colors disabled:opacity-50"
            >
              <Palette className="w-3.5 h-3.5" />
              套用配套《CLANNAD》材质包
            </button>
          </div>
        </div>

        {/* 放映行为开关与时长设置 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-3 border-t border-gray-100 dark:border-base-300">
          <label className="flex items-center justify-between rounded-xl border border-gray-200/80 dark:border-base-300 px-3.5 py-2.5 cursor-pointer hover:bg-gray-50/60 dark:hover:bg-base-200/50">
            <div>
              <div className="text-xs font-semibold text-gray-800 dark:text-gray-100">
                启动名场面序幕
              </div>
              <div className="text-[11px] text-gray-500 dark:text-gray-400">
                打开主窗口时播放感人场面
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
              <Shuffle className="w-4 h-4 text-pink-500 shrink-0" />
              <div>
                <div className="text-xs font-semibold text-gray-800 dark:text-gray-100">
                  每次启动随机邂逅
                </div>
                <div className="text-[11px] text-gray-500 dark:text-gray-400">
                  在四大名场面间随机轮播
                </div>
              </div>
            </div>
            <input
              type="checkbox"
              className="toggle toggle-sm toggle-secondary"
              checked={Boolean(prefs.randomSceneOnBoot)}
              onChange={(e) => updatePrefs({ randomSceneOnBoot: e.target.checked })}
            />
          </label>

          <label className="flex items-center justify-between rounded-xl border border-gray-200/80 dark:border-base-300 px-3.5 py-2.5 cursor-pointer hover:bg-gray-50/60 dark:hover:bg-base-200/50">
            <div>
              <div className="text-xs font-semibold text-gray-800 dark:text-gray-100">
                影院宽银幕遮幅
              </div>
              <div className="text-[11px] text-gray-500 dark:text-gray-400">
                2.35:1 剧场上下胶片黑边
              </div>
            </div>
            <input
              type="checkbox"
              className="toggle toggle-sm toggle-accent"
              checked={prefs.cinemaLetterbox ?? true}
              onChange={(e) => updatePrefs({ cinemaLetterbox: e.target.checked })}
            />
          </label>

          <div className="flex flex-col justify-center rounded-xl border border-gray-200/80 dark:border-base-300 px-3 py-2">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-gray-700 dark:text-gray-200 mb-1">
              <Timer className="w-3.5 h-3.5 text-sky-500" />
              <span>放映时长</span>
            </div>
            <div className="grid grid-cols-4 gap-1">
              {DURATION_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  title={opt.desc}
                  onClick={() => updatePrefs({ durationMs: opt.value })}
                  className={`px-1.5 py-1 rounded-lg text-[10.5px] font-medium transition-colors truncate ${
                    prefs.durationMs === opt.value
                      ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-base-200'
                  }`}
                >
                  {opt.label.split(' · ')[1]}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 四大《CLANNAD》原版动画名场面画廊卡片 + 极速直达项 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
        {CLANNAD_SPLASH_THEMES.map((item) => {
          const isSelected = prefs.studioBootEnabled && prefs.themeId === item.id;
          const isPreviewing = previewThemeId === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => handleSelectTheme(item.id)}
              className={`group relative rounded-2xl border overflow-hidden text-left transition-all flex flex-col ${
                isPreviewing
                  ? 'border-pink-400 dark:border-pink-400/80 ring-2 ring-pink-400/25 bg-white dark:bg-base-100 shadow-md'
                  : 'border-gray-200 dark:border-base-300 bg-white/90 dark:bg-base-100/90 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <div className="relative aspect-video w-full overflow-hidden bg-slate-900">
                <img
                  src={item.artworkUrl}
                  alt={item.name}
                  className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
                />
                <div
                  aria-hidden="true"
                  className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/15 to-transparent"
                />
                {isSelected && (
                  <span className="absolute top-2 right-2 inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/90 text-white shadow-sm">
                    <Check className="w-3 h-3" /> 已启用
                  </span>
                )}
                <span className="absolute bottom-1.5 left-2 right-2 text-[10px] font-semibold text-amber-200 truncate">
                  {item.episodeTag}
                </span>
              </div>

              <div className="p-3 flex-1 flex flex-col justify-between">
                <div>
                  <div className="text-xs font-bold text-gray-900 dark:text-gray-100 line-clamp-1">
                    {item.name}
                  </div>
                  <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1 line-clamp-2 leading-relaxed">
                    {item.quote}
                  </div>
                </div>
              </div>
            </button>
          );
        })}

        <button
          type="button"
          onClick={() => handleSelectTheme('none')}
          className={`rounded-2xl border p-4 text-left transition-all flex flex-col justify-between ${
            !prefs.studioBootEnabled || prefs.themeId === 'none'
              ? 'border-slate-500 ring-2 ring-slate-500/20 bg-slate-50 dark:bg-base-200'
              : 'border-gray-200 dark:border-base-300 bg-white/80 dark:bg-base-100/80 hover:border-gray-300'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="w-9 h-9 rounded-xl bg-gray-100 dark:bg-base-300 flex items-center justify-center">
              <PowerOff className="w-4 h-4 text-gray-500" />
            </div>
            {(!prefs.studioBootEnabled || prefs.themeId === 'none') && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 dark:bg-base-300 text-slate-700 dark:text-slate-200">
                当前直达
              </span>
            )}
          </div>
          <div>
            <div className="text-xs font-bold text-gray-900 dark:text-gray-100">
              关闭序幕 · 极速直达
            </div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">
              不展示任何启动动画与配乐，直接秒入主控制台界面
            </div>
          </div>
        </button>
      </div>

      {/* 16:9 宽银幕实时预览舞台 + 可选自定义蓝光原画截图上传栏 */}
      <div className="rounded-2xl border border-gray-200 dark:border-base-300 bg-white dark:bg-base-100 p-3 shadow-sm space-y-2.5">
        <div className="h-[380px] sm:h-[460px] w-full overflow-hidden rounded-xl">
          <ClannadSplashStage
            themeId={previewThemeId}
            mode="preview"
            durationMs={prefs.durationMs}
            musicEnabled={isPreviewPlayingMusic}
            bgmTrackId={prefs.bgmTrackId || 'follow-scene'}
            bgmVolume={prefs.bgmVolume ?? 0.7}
            bgmStartOffsetSec={prefs.bgmStartOffsetSec ?? 0}
            cinemaLetterbox={prefs.cinemaLetterbox ?? true}
            customArtworkUrl={customArtworkUrl}
            isMusicPreviewPlaying={isPreviewPlayingMusic}
            onToggleMusicPreview={handleToggleMusicPreview}
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 px-1.5 pt-0.5 text-xs">
          <div className="text-gray-500 dark:text-gray-400">
            {customArtworkMeta ? (
              <span>
                当前使用自定义画面截图：<strong className="text-gray-800 dark:text-gray-100">{customArtworkMeta.fileName}</strong>
              </span>
            ) : (
              <span>当前使用内置京都动画原版剧照（您也可以上传自己收藏的 1080p/4K 原画截图覆盖背景）</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => artworkInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-200 dark:border-base-300 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-base-200 transition-colors"
            >
              <ImagePlus className="w-3.5 h-3.5 text-pink-500" />
              {customArtworkMeta ? '更换自定义截图...' : '上传自定义原画截图...'}
            </button>
            {customArtworkMeta && (
              <button
                type="button"
                onClick={handleClearCustomArtwork}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                恢复默认原版剧照
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 背景音乐 (BGM) 曲库选择与本地 OST 原声导入工作台 */}
      <div className="rounded-2xl border border-gray-200 dark:border-base-300 bg-white dark:bg-base-100 p-5 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-50 dark:bg-amber-500/15 flex items-center justify-center text-amber-600 dark:text-amber-300">
              <Disc3 className={`w-5 h-5 ${isPreviewPlayingMusic ? 'motion-safe:animate-spin' : ''}`} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100">
                启动背景音乐选择（内置多声部治愈乐曲 & 本地原声导入）
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                点击任一曲目即可立即试听并设为启动伴奏，或导入本地收藏的《CLANNAD》原声 MP3 / FLAC / WAV 文件
              </p>
            </div>
          </div>

          {/* 音量控制与试听开关 */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label
                htmlFor={volumeSliderId}
                className="text-xs font-medium text-gray-600 dark:text-gray-300 whitespace-nowrap"
              >
                配乐音量 {Math.round((prefs.bgmVolume ?? 0.7) * 100)}%
              </label>
              <input
                id={volumeSliderId}
                type="range"
                min={5}
                max={100}
                step={5}
                value={Math.round((prefs.bgmVolume ?? 0.7) * 100)}
                onChange={(e) => {
                  const vol = Number(e.target.value) / 100;
                  const next = updatePrefs({ bgmVolume: vol });
                  if (isPreviewPlayingMusic) {
                    triggerPreviewBgm(next, previewThemeId);
                  }
                }}
                className="range range-xs range-warning w-28"
              />
            </div>

            <button
              type="button"
              onClick={handleToggleMusicPreview}
              className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold transition-colors ${
                isPreviewPlayingMusic
                  ? 'bg-amber-500 text-slate-950 hover:bg-amber-400'
                  : 'bg-gray-900 text-white dark:bg-white dark:text-gray-900 hover:opacity-90'
              }`}
            >
              {isPreviewPlayingMusic ? (
                <>
                  <VolumeX className="w-3.5 h-3.5" />
                  停止试听
                </>
              ) : (
                <>
                  <Volume2 className="w-3.5 h-3.5" />
                  试听当前配乐
                </>
              )}
            </button>
          </div>
        </div>

        {/* 曲目选择网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {/* 1. 智能随场面匹配 */}
          <button
            type="button"
            onClick={() => handleSelectBgmTrack('follow-scene')}
            className={`rounded-xl border p-3.5 text-left transition-all ${
              currentBgmSelection === 'follow-scene'
                ? 'border-amber-400 bg-amber-50/50 dark:bg-amber-500/10 ring-1 ring-amber-400/40'
                : 'border-gray-200 dark:border-base-300 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="inline-flex items-center gap-1.5 text-xs font-bold text-gray-900 dark:text-gray-100">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                随名场面智能匹配（推荐）
              </span>
              {currentBgmSelection === 'follow-scene' && (
                <Check className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              )}
            </div>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">
              自动根据当前展示的名场面切换最契合情绪的钢琴或八音盒曲目
            </p>
          </button>

          {/* 2-5. 四首内置双声部治愈乐曲 */}
          {BUILTIN_BGM_TRACKS.map((track) => {
            const active = currentBgmSelection === track.id;
            return (
              <button
                key={track.id}
                type="button"
                onClick={() => handleSelectBgmTrack(track.id)}
                className={`rounded-xl border p-3.5 text-left transition-all ${
                  active
                    ? 'border-amber-400 bg-amber-50/50 dark:bg-amber-500/10 ring-1 ring-amber-400/40'
                    : 'border-gray-200 dark:border-base-300 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-gray-900 dark:text-gray-100 truncate">
                    <Music className="w-3.5 h-3.5 text-pink-500 shrink-0" />
                    <span className="truncate">{track.title}</span>
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-100 dark:bg-base-200 text-gray-600 dark:text-gray-300 shrink-0 ml-1">
                    {track.moodTag}
                  </span>
                </div>
                <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate">
                  {track.instrumentLabel} · {track.subtitle}
                </p>
              </button>
            );
          })}

          {/* 6. 静音模式 */}
          <button
            type="button"
            onClick={() => handleSelectBgmTrack('off')}
            className={`rounded-xl border p-3.5 text-left transition-all ${
              currentBgmSelection === 'off'
                ? 'border-slate-500 bg-slate-50 dark:bg-base-200 ring-1 ring-slate-400/40'
                : 'border-gray-200 dark:border-base-300 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="inline-flex items-center gap-1.5 text-xs font-bold text-gray-900 dark:text-gray-100">
                <VolumeX className="w-3.5 h-3.5 text-gray-400" />
                静音模式（不播放背景音乐）
              </span>
              {currentBgmSelection === 'off' && (
                <Check className="w-3.5 h-3.5 text-slate-600 dark:text-slate-300" />
              )}
            </div>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">
              仅静默呈现原动画感人名场面与台词字幕，保持安静办公环境
            </p>
          </button>
        </div>

        {/* 本地自定义原声音乐 (MP3 / FLAC / WAV) 专属导入栏 */}
        <div
          className={`rounded-xl border p-4 flex flex-wrap items-center justify-between gap-4 transition-colors ${
            currentBgmSelection === 'custom-file'
              ? 'border-pink-400 bg-pink-50/40 dark:bg-pink-500/10'
              : 'border-dashed border-gray-300 dark:border-base-300 bg-gray-50/60 dark:bg-base-200/40'
          }`}
        >
          <div className="space-y-1 min-w-[240px] flex-1">
            <div className="flex items-center gap-2">
              <FolderOpen className="w-4 h-4 text-pink-500 shrink-0" />
              <span className="text-xs font-bold text-gray-900 dark:text-gray-100">
                导入自定义本地原声音乐（例如《だんご大家族》《汐》《小さなてのひら》《時を刻む唄》）
              </span>
              {currentBgmSelection === 'custom-file' && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-pink-500 text-white">
                  当前使用本地原声
                </span>
              )}
            </div>

            {customBgmMeta ? (
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 pt-1">
                <span className="text-xs font-medium text-pink-700 dark:text-pink-300">
                  已保存音频：{customBgmMeta.fileName}（{(customBgmMeta.sizeBytes / 1024 / 1024).toFixed(2)} MB）
                </span>

                <div className="flex items-center gap-2">
                  <label
                    htmlFor={offsetSliderId}
                    className="text-[11px] text-gray-600 dark:text-gray-300 whitespace-nowrap"
                  >
                    副歌切入起点：{formatSecondsMmSs(prefs.bgmStartOffsetSec ?? 0)}
                  </label>
                  <input
                    id={offsetSliderId}
                    type="range"
                    min={0}
                    max={210}
                    step={1}
                    value={prefs.bgmStartOffsetSec ?? 0}
                    onChange={(e) => {
                      const sec = Number(e.target.value);
                      const next = updatePrefs({ bgmStartOffsetSec: sec });
                      if (isPreviewPlayingMusic && currentBgmSelection === 'custom-file') {
                        triggerPreviewBgm(next, previewThemeId);
                      }
                    }}
                    className="range range-xs range-secondary w-32"
                  />
                </div>
              </div>
            ) : (
              <p className="text-[11px] text-gray-500 dark:text-gray-400">
                支持 MP3 / FLAC / WAV / OGG / M4A，文件保存在本机 IndexedDB 中，重启软件自动生效，并可自由拖拽副歌高潮起始秒数。
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            {customBgmMeta && currentBgmSelection !== 'custom-file' && (
              <button
                type="button"
                onClick={() => handleSelectBgmTrack('custom-file')}
                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-pink-500 text-white hover:bg-pink-600 transition-colors"
              >
                启用已存音乐
              </button>
            )}

            <button
              type="button"
              onClick={() => audioInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border border-gray-300 dark:border-base-300 bg-white dark:bg-base-100 text-gray-800 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-base-200 transition-colors"
            >
              <FolderOpen className="w-3.5 h-3.5" />
              {customBgmMeta ? '更换音乐文件...' : '选择本地音乐文件...'}
            </button>

            {customBgmMeta && (
              <button
                type="button"
                onClick={handleClearCustomAudio}
                className="inline-flex items-center gap-1 px-2.5 py-2 rounded-xl text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                aria-label="移除本地自定义音乐"
              >
                <Trash2 className="w-3.5 h-3.5" />
                移除
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Antigravity 官方客户端启动遮罩可选同步面板 */}
      <div className="rounded-2xl border border-gray-200 dark:border-base-300 bg-white dark:bg-base-100 p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1 max-w-2xl">
          <div className="flex items-center gap-2 text-xs font-bold text-gray-900 dark:text-gray-100">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span>同步注入至 Antigravity 官方客户端开机序幕（可选）</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-gray-100 dark:bg-base-200 text-gray-600 dark:text-gray-300">
              客户端当前：
              {status.splash_character === 'none' || !status.splash_character
                ? '官方极速启动'
                : getSplashThemeSpec(clientSplashId).name}
            </span>
          </div>
          <p className="text-[11.5px] text-gray-500 dark:text-gray-400">
            可将当前预览的名场面「{activeSpec.name}」（含原动画高清剧照与经典台词字幕）写入客户端 <code className="font-mono">dist/loadingOverlay.js</code>；亦可随时一键恢复官方原版极速启动。
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
            {busyAction === 'sync_client'
              ? '正在注入客户端...'
              : `注入「${activeSpec.shortName}」至客户端`}
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
