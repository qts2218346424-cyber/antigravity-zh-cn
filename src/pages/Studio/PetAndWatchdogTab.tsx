import React, { useEffect, useState } from 'react';
import { emit } from '@tauri-apps/api/event';
import { open } from '@tauri-apps/plugin-dialog';
import {
  Activity,
  Compass,
  Disc3,
  Footprints,
  Heart,
  ImagePlus,
  Music,
  Pause,
  Pin,
  Play,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  SkipBack,
  SkipForward,
  Sparkles,
  Terminal,
  Trash2,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
import { petAudio } from '../../components/pet/petAudio';
import {
  normalizePetCharacter,
  PET_CHARACTER_ORDER,
  PET_CHARACTER_PROFILES,
  type PetQuoteItem,
} from '../../components/pet/petLogic';
import { studioService } from '../../services/studioService';
import type { MediaStatus, PetAssets, PetCharacterId, StudioStatus } from '../../types/studio';
import { isTauri } from '../../utils/env';

interface TabProps {
  status: StudioStatus;
  onRefresh: () => Promise<void>;
}

export const PetCenterTab: React.FC<TabProps> = ({ status, onRefresh }) => {
  const [character, setCharacter] = useState<PetCharacterId>(() =>
    normalizePetCharacter(status.pet_character),
  );
  const [alwaysOnTop, setAlwaysOnTop] = useState(status.pet_always_on_top ?? true);
  const [roaming, setRoaming] = useState(status.pet_roaming ?? true);
  const [muted, setMuted] = useState(status.pet_muted ?? false);
  const [assets, setAssets] = useState<PetAssets>({});
  const [media, setMedia] = useState<MediaStatus>({
    isPlaying: false,
    title: '',
    artist: '',
    rawTitle: '',
    source: '',
    lrc: '',
  });
  const [busy, setBusy] = useState(false);
  const [playingVoiceKey, setPlayingVoiceKey] = useState<string | null>(null);

  useEffect(() => {
    setCharacter(normalizePetCharacter(status.pet_character));
    setAlwaysOnTop(status.pet_always_on_top ?? true);
    setRoaming(status.pet_roaming ?? true);
    setMuted(status.pet_muted ?? false);
  }, [status.pet_character, status.pet_always_on_top, status.pet_roaming, status.pet_muted]);

  useEffect(() => {
    studioService.getPetAssets().then(setAssets).catch(() => {});
    const refreshMedia = () => {
      studioService.getMediaStatus().then(setMedia).catch(() => {});
    };
    refreshMedia();
    const timer = window.setInterval(refreshMedia, 3000);
    return () => {
      window.clearInterval(timer);
      petAudio.stopVoice();
    };
  }, [status.custom_pet_avatar]);

  const handlePlayQuote = async (quote: PetQuoteItem) => {
    petAudio.muted = false;
    const isDangoSong = quote.voiceKey === 'ushio_dango';
    if (isTauri() && status.pet_window_open) {
      await emit('pet:remote-action', {
        action: isDangoSong ? 'dango_song' : 'pat',
        message: quote.zh,
        sub: quote.sub,
        voiceKey: quote.voiceKey,
      }).catch(() => {});
      showToast(
        isDangoSong
          ? '已在桌面伴侣触发《CLANNAD》原动画 ED《团子大家族》原曲'
          : `已在桌面伴侣触发原声金句：${quote.zh}`,
        'info',
      );
      return;
    }

    if (quote.voiceKey && playingVoiceKey === quote.voiceKey) {
      petAudio.stopVoice();
      setPlayingVoiceKey(null);
      return;
    }

    const uri = quote.voiceKey ? assets.voices?.[quote.voiceKey] : undefined;
    if (uri && quote.voiceKey) {
      const key = quote.voiceKey;
      petAudio.playVoice(
        uri,
        (playing) => {
          setPlayingVoiceKey(playing ? key : null);
        },
        key,
      );
    } else {
      petAudio.playCare();
      showToast(quote.zh, 'info');
    }
  };

  const previewSrcForCharacter = (cid: PetCharacterId): string | null | undefined => {
    if (cid === 'nezuko') return assets.nezuko_chibi;
    if (cid === 'prince') return assets.little_prince;
    if (cid === 'ushio') return assets.ushio_chibi;
    if (cid === 'tanjiro') return assets.tanjiro_chibi || assets.tanjiro_water;
    if (cid === 'zenitsu') return assets.zenitsu_chibi || assets.zenitsu_thunder;
    if (cid === 'inosuke') return assets.inosuke_chibi || assets.inosuke_beast;
    if (cid === 'custom') return assets.custom_avatar;
    return null;
  };

  const handleTogglePet = async () => {
    setBusy(true);
    try {
      if (status.pet_window_open) {
        await studioService.closePet();
        showToast('已收起透明桌面伴侣视窗', 'info');
      } else {
        await studioService.launchPet(character);
        const profile = PET_CHARACTER_PROFILES[character];
        showToast(`已召唤灵动伴侣「${profile.name}」`, 'success');
      }
      await onRefresh();
    } catch (err: unknown) {
      showToast(`伴侣控制失败: ${String(err)}`, 'error');
    } finally {
      setBusy(false);
    }
  };

  const handleSwitchCharacter = async (next: PetCharacterId) => {
    setCharacter(next);
    try {
      await studioService.updatePetPrefs({ character: next });
      if (status.pet_window_open) {
        await studioService.launchPet(next);
      }
      await onRefresh();
    } catch (err) {
      showToast(`切换角色失败: ${String(err)}`, 'error');
    }
  };

  const handleImportAvatar = async () => {
    if (!isTauri()) {
      showToast('请在桌面客户端中选择本地透明立绘文件', 'warning');
      return;
    }
    try {
      const selected = await open({
        multiple: false,
        title: '导入自定义桌面伴侣立绘 (PNG / WebP / GIF / SVG)',
        filters: [
          { name: '图片与动图立绘', extensions: ['png', 'webp', 'gif', 'svg', 'jpg', 'jpeg'] },
        ],
      });
      if (!selected || Array.isArray(selected)) return;
      setBusy(true);
      await studioService.importPetAvatar(selected);
      setCharacter('custom');
      showToast('已导入并切换至自定义专属伴侣立绘', 'success');
      await onRefresh();
    } catch (err) {
      showToast(`导入立绘失败: ${String(err)}`, 'error');
    } finally {
      setBusy(false);
    }
  };

  const handleClearAvatar = async () => {
    try {
      setBusy(true);
      await studioService.clearPetAvatar();
      showToast('已清除自定义立绘并恢复默认角色', 'info');
      await onRefresh();
    } catch (err) {
      showToast(`清除失败: ${String(err)}`, 'error');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* 左侧全明星场景与伴侣控制台 */}
      <div className="lg:col-span-7 space-y-5">
        <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-sm font-bold text-gray-900 dark:text-white">
              <Sparkles className="h-4 w-4 text-pink-500" />
              3D 视差全明星透明伴侣系统（7 角色生态 + 自定义立绘）
            </div>
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-0.5 text-[11px] font-semibold ${
                status.pet_window_open
                  ? 'bg-emerald-500/15 text-emerald-500 border border-emerald-500/30'
                  : 'bg-gray-100 dark:bg-white/5 text-gray-400 border border-gray-200/60 dark:border-white/10'
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  status.pet_window_open ? 'bg-emerald-400 animate-pulse' : 'bg-gray-400'
                }`}
              />
              {status.pet_window_open ? '桌面伴侣伴随中' : '休眠待命'}
            </span>
          </div>

          {/* 7 大角色生态矩阵 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {PET_CHARACTER_ORDER.map((cid) => {
              const item = PET_CHARACTER_PROFILES[cid];
              const isSelected = character === cid;
              return (
                <button
                  key={cid}
                  type="button"
                  onClick={() => handleSwitchCharacter(cid)}
                  className={`group relative rounded-2xl border p-4 text-left transition-all overflow-hidden ${
                    isSelected
                      ? 'border-sky-500/70 bg-gradient-to-br from-sky-500/10 via-indigo-500/5 to-transparent ring-2 ring-sky-500/20'
                      : 'border-gray-200/80 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {previewSrcForCharacter(cid) ? (
                        <img
                          src={previewSrcForCharacter(cid) || ''}
                          alt={item.shortName}
                          className="h-10 w-10 rounded-xl object-contain bg-slate-900/10 dark:bg-white/5 p-0.5 ring-1 ring-black/5 dark:ring-white/10"
                        />
                      ) : (
                        <span
                          className="inline-flex h-8 w-8 items-center justify-center rounded-xl text-white shadow-sm"
                          style={{ backgroundColor: `${item.accent}cc` }}
                        >
                          <Heart className="h-3.5 w-3.5" />
                        </span>
                      )}
                    </div>
                    <span
                      className="text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded-full border border-current/20"
                      style={{ color: item.accent }}
                    >
                      {item.badge}
                    </span>
                  </div>
                  <div className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                    <span>{item.name}</span>
                  </div>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 leading-relaxed line-clamp-2">
                    {item.description}
                  </p>
                </button>
              );
            })}
          </div>

          {/* 当前选中角色：动漫原生语音与经典金句点播舱 */}
          <div className="rounded-2xl border border-amber-500/25 bg-gradient-to-br from-amber-500/5 via-pink-500/5 to-sky-500/5 p-4 space-y-2.5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-xs font-bold text-gray-900 dark:text-white">
                <Volume2 className="h-4 w-4 text-pink-500" />
                <span>
                  {PET_CHARACTER_PROFILES[character].shortName} · 动漫原生语音与经典金句点播台
                </span>
              </div>
              <span className="text-[10.5px] text-gray-500 dark:text-gray-400">
                点击任意台词立即播放原生语音（伴侣开启时同步演绎）
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {PET_CHARACTER_PROFILES[character].quotes.map((q, idx) => {
                const isVoiceActive = Boolean(q.voiceKey && playingVoiceKey === q.voiceKey);
                return (
                  <button
                    key={`${character}-quote-${idx}`}
                    type="button"
                    onClick={() => handlePlayQuote(q)}
                    className={`group rounded-xl border px-3 py-2 text-left transition-all ${
                      isVoiceActive
                        ? 'border-pink-500/60 bg-pink-500/15 ring-1 ring-pink-500/30'
                        : 'border-gray-200/80 dark:border-white/10 bg-white/75 dark:bg-slate-950/55 hover:border-pink-400/50 hover:bg-pink-500/5'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-[11.5px] font-medium text-gray-800 dark:text-slate-100 leading-snug">
                        {q.zh}
                      </span>
                      <Volume2
                        className={`h-3.5 w-3.5 shrink-0 mt-0.5 transition-transform ${
                          isVoiceActive
                            ? 'text-pink-500 scale-110 animate-pulse'
                            : 'text-gray-400 group-hover:text-pink-500'
                        }`}
                      />
                    </div>
                    {q.sub && (
                      <div className="mt-1 text-[10px] italic text-amber-600/90 dark:text-amber-300/80 truncate">
                        {q.sub}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 自定义形象管理条 */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-purple-500/5 dark:bg-purple-500/10 border border-purple-500/20 px-4 py-3">
            <div className="text-xs text-gray-700 dark:text-gray-200">
              <span className="font-semibold text-purple-600 dark:text-purple-300">
                自定义专属立绘引擎：
              </span>{' '}
              {status.custom_pet_avatar
                ? `已挂载自定义资产（${status.custom_pet_avatar}）`
                : '支持导入 PNG / WebP / GIF / SVG 透明背景立绘，即时热更新'}
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleImportAvatar}
                disabled={busy}
                className="inline-flex items-center gap-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 px-3.5 py-1.5 text-xs font-semibold text-white transition-colors disabled:opacity-50"
              >
                <ImagePlus className="h-3.5 w-3.5" />
                上传自定义立绘
              </button>
              {status.custom_pet_avatar && (
                <button
                  type="button"
                  onClick={handleClearAvatar}
                  disabled={busy}
                  className="inline-flex items-center gap-1 rounded-xl border border-rose-400/40 px-2.5 py-1.5 text-xs text-rose-500 hover:bg-rose-500/10 transition-colors"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  清除
                </button>
              )}
            </div>
          </div>

          {/* 控制动作按钮栏 */}
          <div className="flex flex-wrap items-center gap-2.5 pt-3 border-t border-gray-100 dark:border-white/10">
            <button
              type="button"
              onClick={handleTogglePet}
              disabled={busy}
              className={`inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-xs font-semibold text-white shadow-lg transition-all ${
                status.pet_window_open
                  ? 'bg-rose-600 hover:bg-rose-700'
                  : 'bg-gradient-to-r from-pink-500 via-rose-500 to-indigo-600 hover:opacity-95'
              }`}
            >
              {status.pet_window_open ? '收起桌面透明伴侣' : '在桌面唤起透明伴侣'}
            </button>

            <button
              type="button"
              onClick={() =>
                studioService
                  .resetPetPosition()
                  .then(() => showToast('已平滑归位至屏幕右下角安全区', 'info'))
              }
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-white/15 px-3 py-2 text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/5"
            >
              <Compass className="h-3.5 w-3.5 text-sky-500" />
              右下角归位
            </button>

            <button
              type="button"
              onClick={() => {
                const next = !alwaysOnTop;
                setAlwaysOnTop(next);
                studioService.setPetAlwaysOnTop(next).then(onRefresh).catch(() => {});
              }}
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-white/15 px-3 py-2 text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/5"
            >
              <Pin className={`h-3.5 w-3.5 ${alwaysOnTop ? 'text-amber-400' : 'text-gray-400'}`} />
              {alwaysOnTop ? '置顶：开' : '置顶：关'}
            </button>

            <button
              type="button"
              onClick={() => {
                const next = !roaming;
                setRoaming(next);
                studioService.updatePetPrefs({ roaming: next }).then(onRefresh).catch(() => {});
              }}
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-white/15 px-3 py-2 text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/5"
            >
              <Footprints className={`h-3.5 w-3.5 ${roaming ? 'text-emerald-500' : 'text-gray-400'}`} />
              {roaming ? '漫步：开' : '漫步：关'}
            </button>

            <button
              type="button"
              onClick={() => {
                const next = !muted;
                setMuted(next);
                studioService.updatePetPrefs({ muted: next }).then(onRefresh).catch(() => {});
              }}
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-white/15 px-3 py-2 text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/5"
            >
              {muted ? (
                <VolumeX className="h-3.5 w-3.5 text-rose-500" />
              ) : (
                <Volume2 className="h-3.5 w-3.5 text-sky-500" />
              )}
              {muted ? '音效：静音' : '音效：开启'}
            </button>
          </div>
        </div>
      </div>

      {/* 右侧黑胶声学与毫秒级歌词同步舱 */}
      <div className="lg:col-span-5">
        <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-gray-900 dark:text-white">
              <Music className="h-4 w-4 text-emerald-500" />
              声学嗅探与酷狗 LRC 毫秒时间轴桥接
            </div>
            <span className="rounded-full bg-gray-100 dark:bg-white/5 px-2.5 py-0.5 text-[10px] font-mono text-gray-500">
              {media.source || '待机'}
            </span>
          </div>

          <div className="rounded-2xl bg-slate-950 text-white p-4 space-y-3.5 border border-white/10 shadow-inner">
            <div className="flex items-center gap-3.5">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-slate-800 to-black border border-white/20">
                <Disc3
                  className={`h-7 w-7 text-emerald-400 ${media.isPlaying ? 'animate-spin' : ''}`}
                  style={{ animationDuration: '4s' }}
                />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-bold truncate">
                  {media.isPlaying ? media.title || media.rawTitle : '等待媒体信号输入'}
                </div>
                <div className="text-xs text-slate-400 mt-0.5 truncate">
                  {media.isPlaying
                    ? media.artist || '未知艺术家'
                    : '启动 QQ 音乐 / 网易云播放即自动激活黑胶与精准时间轴同步'}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => studioService.sendMediaCommand('prev').catch(() => {})}
                className="rounded-xl border border-white/15 bg-white/5 p-2 hover:bg-white/15 transition-colors"
                title="上一首"
              >
                <SkipBack className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => studioService.sendMediaCommand('play_pause').catch(() => {})}
                className="flex-1 rounded-xl bg-emerald-500 px-4 py-2 text-slate-950 hover:bg-emerald-400 inline-flex items-center justify-center gap-1.5 text-xs font-bold transition-colors"
              >
                {media.isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {media.isPlaying ? '暂停播放' : '继续播放'}
              </button>
              <button
                type="button"
                onClick={() => studioService.sendMediaCommand('next').catch(() => {})}
                className="rounded-xl border border-white/15 bg-white/5 p-2 hover:bg-white/15 transition-colors"
                title="下一首"
              >
                <SkipForward className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="rounded-xl bg-slate-950/90 border border-white/10 text-emerald-300/90 p-3.5 text-[11px] font-mono h-44 overflow-y-auto whitespace-pre-wrap leading-relaxed">
            {media.lrc
              ? media.lrc
              : '// 检测到桌面音乐播放器活动曲目后，将自动通过酷狗歌词通道拉取并按 [mm:ss.xx] 时间戳二分同步渲染'}
          </div>
        </div>
      </div>
    </div>
  );
};

export const WatchdogTab: React.FC<TabProps> = ({ status, onRefresh }) => {
  const [busy, setBusy] = useState(false);

  const handleManualCheck = async (force: boolean) => {
    setBusy(true);
    try {
      const res = await studioService.reapplyCheck(force);
      if (res.error) {
        showToast(res.error, 'error');
      } else if (res.actions.length > 0) {
        showToast(res.actions.join('；'), 'success');
      } else {
        showToast('全链路巡检正常：汉化标识与 IDE 样式均已锁定', 'info');
      }
      await onRefresh();
    } catch (err: unknown) {
      showToast(`巡检执行异常: ${String(err)}`, 'error');
    } finally {
      setBusy(false);
    }
  };

  const handleToggleWatchdog = async () => {
    try {
      const next = !status.auto_reapply;
      await studioService.setAutoReapply(next);
      showToast(next ? '已恢复 Tokio 120 秒防更新后台巡检' : '已暂停后台巡检', 'info');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`切换失败: ${String(err)}`, 'error');
    }
  };

  const handleToggleAutostart = async () => {
    try {
      const next = !status.autostart_enabled;
      await studioService.toggleAutostart(next);
      showToast(next ? '已开启系统登录自启（随系统启动守护）' : '已关闭系统自启', 'success');
      await onRefresh();
    } catch (err: unknown) {
      showToast(`开机自启设置失败: ${String(err)}`, 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* 双轨核心健康状态遥测卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3.5">
            {status.agent_status === 'patched' ? (
              <div className="h-11 w-11 rounded-2xl bg-emerald-500/15 flex items-center justify-center text-emerald-500 border border-emerald-500/25">
                <ShieldCheck className="h-6 w-6" />
              </div>
            ) : (
              <div className="h-11 w-11 rounded-2xl bg-amber-500/15 flex items-center justify-center text-amber-500 border border-amber-500/25">
                <ShieldAlert className="h-6 w-6" />
              </div>
            )}
            <div>
              <div className="text-[11px] uppercase tracking-wider text-gray-400 font-semibold">
                客户端核心补丁状态
              </div>
              <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
                {status.agent_status === 'patched'
                  ? '中文内核与皮肤钩子完好'
                  : status.agent_status === 'clean'
                    ? '未打补丁或已被官方更新覆盖'
                    : '未探测到官方安装目录'}
              </div>
            </div>
          </div>
          <span className="rounded-lg bg-gray-100 dark:bg-white/5 px-2.5 py-1 text-[11px] font-mono text-gray-500">
            {status.agent_status}
          </span>
        </div>

        <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3.5">
            {status.ide_status === 'injected' ? (
              <div className="h-11 w-11 rounded-2xl bg-sky-500/15 flex items-center justify-center text-sky-400 border border-sky-500/25">
                <ShieldCheck className="h-6 w-6" />
              </div>
            ) : (
              <div className="h-11 w-11 rounded-2xl bg-slate-500/15 flex items-center justify-center text-slate-400 border border-slate-500/20">
                <Activity className="h-6 w-6" />
              </div>
            )}
            <div>
              <div className="text-[11px] uppercase tracking-wider text-gray-400 font-semibold">
                IDE 工作台样式与校验和
              </div>
              <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
                {status.ide_status === 'injected'
                  ? 'IDE 光学材质与 SHA-256 校验正常'
                  : status.ide_status === 'stale'
                    ? 'IDE 样式过期待重同步'
                    : status.ide_status === 'clean'
                      ? '原版洁净状态（未注入）'
                      : '未定位到 IDE 根目录'}
              </div>
            </div>
          </div>
          <span className="rounded-lg bg-gray-100 dark:bg-white/5 px-2.5 py-1 text-[11px] font-mono text-gray-500">
            {status.ide_status}
          </span>
        </div>
      </div>

      {/* 后台看门狗与自启策略 */}
      <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-sm font-bold text-gray-900 dark:text-white">
              Tokio 异步守卫协程（防更新自动重注哨兵）
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              随宿主进程每 120 秒巡检一次指纹；若官方更新覆写且客户端进程已退出，立即原位自动重构补丁与校验和。
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleToggleWatchdog}
              className={`rounded-xl px-3.5 py-2 text-xs font-semibold border transition-colors ${
                status.auto_reapply
                  ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                  : 'border-gray-300 dark:border-white/15 text-gray-500'
              }`}
            >
              {status.auto_reapply ? '后台看门狗：运行中' : '后台看门狗：已暂停'}
            </button>
            <button
              type="button"
              onClick={handleToggleAutostart}
              className={`rounded-xl px-3.5 py-2 text-xs font-semibold border transition-colors ${
                status.autostart_enabled
                  ? 'border-sky-500/40 bg-sky-500/15 text-sky-600 dark:text-sky-400'
                  : 'border-gray-300 dark:border-white/15 text-gray-500'
              }`}
            >
              {status.autostart_enabled ? '开机自动启动：已启用' : '开机自动启动：未开启'}
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 pt-3 border-t border-gray-100 dark:border-white/10">
          <button
            type="button"
            onClick={() => handleManualCheck(false)}
            disabled={busy}
            className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 dark:bg-sky-500 px-4 py-2 text-xs font-semibold text-white dark:text-slate-950 hover:opacity-90 disabled:opacity-60"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${busy ? 'animate-spin' : ''}`} />
            立即巡检并自动修复
          </button>
          <button
            type="button"
            onClick={() => handleManualCheck(true)}
            disabled={busy}
            className="rounded-xl border border-amber-500/35 bg-amber-500/10 px-4 py-2 text-xs font-medium text-amber-600 dark:text-amber-300 hover:bg-amber-500/20 disabled:opacity-60"
          >
            强制全量重刷所有补丁与皮肤
          </button>
        </div>
      </div>

      {/* 黑曜石日志流面板 */}
      <div className="rounded-2xl border border-white/10 bg-slate-950 p-4 text-xs font-mono text-gray-200 space-y-2.5 shadow-inner">
        <div className="flex items-center gap-2 text-gray-400 font-sans font-semibold text-xs">
          <Terminal className="h-3.5 w-3.5 text-emerald-400" />
          守护巡检事件遥测日志（保留最新 120 条）
        </div>
        <div className="max-h-56 overflow-y-auto space-y-1 text-[11px] leading-relaxed">
          {status.reapply_logs.length === 0 ? (
            <div className="text-slate-500">// 尚无触发事件，当前看门狗静默守护中</div>
          ) : (
            [...status.reapply_logs].reverse().map((line, i) => (
              <div key={`log-${i}`} className="text-emerald-300/90">
                {line}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
