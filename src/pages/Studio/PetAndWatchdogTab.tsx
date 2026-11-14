import React, { useEffect, useState } from 'react';
import {
  Activity,
  Compass,
  Disc3,
  Heart,
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
} from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
import { studioService } from '../../services/studioService';
import type { MediaStatus, StudioStatus } from '../../types/studio';

interface TabProps {
  status: StudioStatus;
  onRefresh: () => Promise<void>;
}

export const PetCenterTab: React.FC<TabProps> = ({ status, onRefresh }) => {
  const [character, setCharacter] = useState<'nezuko' | 'prince'>('nezuko');
  const [alwaysOnTop, setAlwaysOnTop] = useState(true);
  const [media, setMedia] = useState<MediaStatus>({
    isPlaying: false,
    title: '',
    artist: '',
    rawTitle: '',
    source: '',
    lrc: '',
  });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const refreshMedia = () => {
      studioService.getMediaStatus().then(setMedia).catch(() => {});
    };
    refreshMedia();
    const timer = window.setInterval(refreshMedia, 3000);
    return () => window.clearInterval(timer);
  }, []);

  const handleTogglePet = async () => {
    setBusy(true);
    try {
      if (status.pet_window_open) {
        await studioService.closePet();
        showToast('已收起透明桌面伴侣视窗', 'info');
      } else {
        await studioService.launchPet(character);
        showToast(
          `已召唤灵动伴侣「${character === 'nezuko' ? '灶门祢豆子' : 'B612 小王子'}」`,
          'success',
        );
      }
      await onRefresh();
    } catch (err: unknown) {
      showToast(`伴侣控制失败: ${String(err)}`, 'error');
    } finally {
      setBusy(false);
    }
  };

  const handleSwitchCharacter = async (next: 'nezuko' | 'prince') => {
    setCharacter(next);
    if (status.pet_window_open) {
      await studioService.launchPet(next).catch(() => {});
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* 左侧场景与伴侣控制台 */}
      <div className="lg:col-span-7 space-y-5">
        <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-gray-900 dark:text-white">
              <Sparkles className="h-4 w-4 text-pink-500" />
              3D 视差生态透明伴侣系统 (Living Terrarium)
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
              {status.pet_window_open ? '桌面伴侣伴随中' : '休眠未开启'}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => handleSwitchCharacter('nezuko')}
              className={`group relative rounded-2xl border p-4 text-left transition-all overflow-hidden ${
                character === 'nezuko'
                  ? 'border-pink-500/70 bg-gradient-to-br from-pink-500/10 via-rose-500/5 to-transparent ring-2 ring-pink-500/20'
                  : 'border-gray-200/80 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-pink-500/15 text-pink-500">
                  <Heart className="h-4 w-4" />
                </span>
                <span className="text-[10px] font-mono text-pink-400 uppercase tracking-wider">
                  Kimetsu · Sakura
                </span>
              </div>
              <div className="text-sm font-bold text-gray-900 dark:text-white">
                灶门祢豆子 · 绯樱生态
              </div>
              <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                3D 鼠标视差交互、矢量樱花爆血微粒、竹箱旋转冲击波、竹篓休眠及音频律动伴舞。
              </p>
            </button>

            <button
              type="button"
              onClick={() => handleSwitchCharacter('prince')}
              className={`group relative rounded-2xl border p-4 text-left transition-all overflow-hidden ${
                character === 'prince'
                  ? 'border-sky-500/70 bg-gradient-to-br from-sky-500/10 via-indigo-500/5 to-transparent ring-2 ring-sky-500/20'
                  : 'border-gray-200/80 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-sky-500/15 text-sky-400">
                  <Sparkles className="h-4 w-4" />
                </span>
                <span className="text-[10px] font-mono text-sky-400 uppercase tracking-wider">
                  Asteroid B612
                </span>
              </div>
              <div className="text-sm font-bold text-gray-900 dark:text-white">
                B612 小王子 · 星辰玫瑰
              </div>
              <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                前景玫瑰与驯服小狐狸多层独立视差，一键切换深空星河与四十四次金色日落。
              </p>
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-gray-100 dark:border-white/10">
            <button
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
              onClick={() =>
                studioService
                  .resetPetPosition()
                  .then(() => showToast('已平滑归位至屏幕右下角安全区', 'info'))
              }
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-white/15 px-3.5 py-2 text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/5"
            >
              <Compass className="h-3.5 w-3.5 text-sky-500" />
              右下角归位
            </button>

            <button
              onClick={() => {
                const next = !alwaysOnTop;
                setAlwaysOnTop(next);
                studioService.setPetAlwaysOnTop(next).catch(() => {});
              }}
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-white/15 px-3.5 py-2 text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/5"
            >
              <Pin className={`h-3.5 w-3.5 ${alwaysOnTop ? 'text-amber-400' : 'text-gray-400'}`} />
              {alwaysOnTop ? '置顶悬浮：开启' : '置顶悬浮：关闭'}
            </button>
          </div>
        </div>
      </div>

      {/* 右侧黑胶声学与歌词同步舱 */}
      <div className="lg:col-span-5">
        <div className="rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-gray-900 dark:text-white">
              <Music className="h-4 w-4 text-emerald-500" />
              声学嗅探与酷狗 LRC 桥接
            </div>
            <span className="rounded-full bg-gray-100 dark:bg-white/5 px-2.5 py-0.5 text-[10px] font-mono text-gray-500">
              {media.source || 'STANDBY'}
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
                    : 'Windows 下启动 QQ 音乐 / 网易云即自动激活黑胶动效'}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => studioService.sendMediaCommand('prev').catch(() => {})}
                className="rounded-xl border border-white/15 bg-white/5 p-2 hover:bg-white/15 transition-colors"
                title="上一首"
              >
                <SkipBack className="h-4 w-4" />
              </button>
              <button
                onClick={() => studioService.sendMediaCommand('play_pause').catch(() => {})}
                className="flex-1 rounded-xl bg-emerald-500 px-4 py-2 text-slate-950 hover:bg-emerald-400 inline-flex items-center justify-center gap-1.5 text-xs font-bold transition-colors"
              >
                {media.isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {media.isPlaying ? '暂停播放' : '继续播放'}
              </button>
              <button
                onClick={() => studioService.sendMediaCommand('next').catch(() => {})}
                className="rounded-xl border border-white/15 bg-white/5 p-2 hover:bg-white/15 transition-colors"
                title="下一首"
              >
                <SkipForward className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="rounded-xl bg-slate-950/90 border border-white/10 text-emerald-300/90 p-3.5 text-[11px] font-mono h-36 overflow-y-auto whitespace-pre-wrap leading-relaxed">
            {media.lrc
              ? media.lrc
              : '// 检测到桌面音乐播放器活动曲目后，将自动通过酷狗歌词开放通道拉取并缓存 LRC 滚动轴'}
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
                Agent Client Core
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
                IDE Workbench CSS & Checksum
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
              Tokio 异步守卫协程 (Anti-Overwrite Watchdog)
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              无需外部 Python 脚本常驻：随宿主进程每 120 秒巡检一次指纹；若官方更新覆写且客户端进程已退出，立即原位自动重构补丁与校验和。
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
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
            onClick={() => handleManualCheck(false)}
            disabled={busy}
            className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 dark:bg-sky-500 px-4 py-2 text-xs font-semibold text-white dark:text-slate-950 hover:opacity-90 disabled:opacity-60"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${busy ? 'animate-spin' : ''}`} />
            立即巡检并自动修复
          </button>
          <button
            onClick={() => handleManualCheck(true)}
            disabled={busy}
            className="rounded-xl border border-amber-500/35 bg-amber-500/10 px-4 py-2 text-xs font-medium text-amber-600 dark:text-amber-300 hover:bg-amber-500/20"
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
