import React, { useMemo, useState } from 'react';
import { emit } from '@tauri-apps/api/event';
import {
  Activity,
  CheckCircle2,
  Clock,
  FlaskConical,
  Music2,
  Play,
  RefreshCw,
  Sparkles,
  Volume2,
  XCircle,
  Zap,
} from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
import { petAudio } from '../../components/pet/petAudio';
import {
  evaluateLowQuotaAlert,
  findActiveLyricIndex,
  parseLrcTimeline,
  type PetAction,
} from '../../components/pet/petLogic';
import { studioService } from '../../services/studioService';
import { useAccountStore } from '../../stores/useAccountStore';
import type { StudioDiagnosticReport, StudioStatus } from '../../types/studio';
import { isTauri } from '../../utils/env';
import { request } from '../../utils/request';

interface DiagnosticsTabProps {
  status: StudioStatus;
  onRefresh: () => Promise<void>;
}

const SAMPLE_LRC = `[ti:星海漫游演练曲]
[ar:Antigravity Studio]
[offset:0]
[00:00.00]♪ 前奏：黑曜石光学与星尘序曲 ♪
[00:04.50]穿过深邃夜空 听见算力脉搏跳动
[00:09.20]B612 的玫瑰在玻璃罩下静静绽放
[00:14.80]水之呼吸化作清泉 抚平每一行复杂逻辑
[00:20.00]霹雳一闪破晓而至 全部测试绿灯通行 ✨`;

const SOUND_SAMPLES: Array<{ label: string; desc: string; trigger: () => void }> = [
  { label: '温暖叮咚', desc: '摸头 / 投喂双和弦', trigger: () => petAudio.playCare() },
  { label: '团子八音盒', desc: '冈崎汐五音前奏微旋律', trigger: () => petAudio.playDangoMelody() },
  { label: '愿望光玉', desc: 'CLANNAD 空灵水晶琶音', trigger: () => petAudio.playLightOrb() },
  { label: '木箱旋风', desc: '带通滤波风声合成', trigger: () => petAudio.playSpinWind() },
  { label: '震地回响', desc: '低频落地物理锤击', trigger: () => petAudio.playWoodThud() },
  { label: '爆血绯晶', desc: '高频泛音晶体迸发', trigger: () => petAudio.playBloodBurst() },
  { label: 'B612 星尘', desc: '玫瑰与狐狸清脆谐音', trigger: () => petAudio.playStardust() },
  { label: '许愿流星', desc: '双滑音高空划过', trigger: () => petAudio.playShootingStar() },
  { label: '水之呼吸', desc: '炭治郎三段清泉泛音', trigger: () => petAudio.playWaterBreath() },
  { label: '霹雳一闪', desc: '善逸瞬发金雷脉冲', trigger: () => petAudio.playThunderSpark() },
  { label: '猪突猛进', desc: '伊之助低频战鼓冲锋', trigger: () => petAudio.playBeastRoar() },
  { label: '算力预警', desc: '低配额双音温和风铃', trigger: () => petAudio.playQuotaAlert() },
];

const REMOTE_PET_ACTIONS: Array<{
  action: PetAction;
  label: string;
  message: string;
  sub?: string;
  voiceKey?: string;
}> = [
  { action: 'pat', label: '轻抚摸头', message: '来自测试台的远程摸头互动 ✨' },
  {
    action: 'dango_song',
    label: '团子大家族原声',
    message: '「团子，团子，团子大家族 ♪ 要一直在一起哦！」',
    sub: 'だんご、だんご、だんご大家族！ずっと一緒だよ！',
    voiceKey: 'ushio_dango',
  },
  {
    action: 'box_spin',
    label: '祢豆子克服阳光原声',
    message: '「早…早上好！平安无事真是太好了呢 ✨」',
    sub: 'お…おはよう！よかったね、本当によかったね！',
    voiceKey: 'nezuko_ohayou',
  },
  {
    action: 'water_slash',
    label: '水之呼吸原声',
    message: '「全集中·水之呼吸！拾之型——生生流转 🌊」',
    sub: '全集中、水の呼吸！拾ノ型、生生流転！！',
    voiceKey: 'tanjiro_water',
  },
  {
    action: 'thunder_dash',
    label: '霹雳一闪原声',
    message: '「雷之呼吸·壹之型——霹雳一闪·六连 ⚡」',
    sub: '雷の呼吸、壱ノ型——霹靂一閃、六連！！',
    voiceKey: 'zenitsu_thunder',
  },
  {
    action: 'beast_rush',
    label: '猪突猛进原声',
    message: '「兽之呼吸！猪突猛进！！猪突猛进 🐗」',
    sub: '獣の呼吸！猪突猛進！！猪突猛進！！',
    voiceKey: 'inosuke_rush',
  },
  {
    action: 'stars',
    label: 'B612 法语金句',
    message: '「只有用心才能看得清。真正重要的东西，用眼睛是看不见的 ✨」',
    sub: "On ne voit bien qu'avec le cœur. L'essentiel est invisible pour les yeux.",
    voiceKey: 'prince_essential',
  },
  { action: 'dance', label: '黑胶律动热舞', message: '声波律动热舞测试开启 ♪' },
];

export const DiagnosticsTab: React.FC<DiagnosticsTabProps> = ({ status, onRefresh }) => {
  const [report, setReport] = useState<StudioDiagnosticReport | null>(null);
  const [runningDiag, setRunningDiag] = useState(false);
  const [proxyHealth, setProxyHealth] = useState<{
    checked: boolean;
    running: boolean;
    port: number;
    activeAccounts: number;
    latencyMs: number;
    error?: string;
  } | null>(null);
  const [checkingProxy, setCheckingProxy] = useState(false);

  const [lrcInput, setLrcInput] = useState(SAMPLE_LRC);
  const [simTimeMs, setSimTimeMs] = useState(9500);

  const { accounts } = useAccountStore();

  const parsedLrc = useMemo(() => parseLrcTimeline(lrcInput), [lrcInput]);
  const activeLrcIdx = useMemo(
    () => findActiveLyricIndex(parsedLrc, simTimeMs),
    [parsedLrc, simTimeMs],
  );

  const handleRunStudioDiag = async () => {
    setRunningDiag(true);
    try {
      const res = await studioService.runDiagnostics();
      setReport(res);
      showToast(
        res.all_passed
          ? `全链路引擎自检全部通过（耗时 ${res.total_ms}ms）`
          : '部分诊断项发现异常，请查看报告详情',
        res.all_passed ? 'success' : 'warning',
      );
      await onRefresh();
    } catch (err) {
      showToast(`诊断执行失败: ${String(err)}`, 'error');
    } finally {
      setRunningDiag(false);
    }
  };

  const handleCheckGateway = async () => {
    setCheckingProxy(true);
    const t0 = performance.now();
    try {
      const st = await request<{
        running: boolean;
        port: number;
        base_url: string;
        active_accounts: number;
      }>('get_proxy_status');
      const latencyMs = Math.max(1, Math.round(performance.now() - t0));
      setProxyHealth({
        checked: true,
        running: st.running,
        port: st.port,
        activeAccounts: st.active_accounts,
        latencyMs,
      });
      showToast(
        st.running
          ? `本地反代网关在线（端口 ${st.port}，耗时 ${latencyMs}ms）`
          : '本地反代网关当前未启动，可在「API 反代」页一键开启',
        st.running ? 'success' : 'info',
      );
    } catch (err) {
      setProxyHealth({
        checked: true,
        running: false,
        port: 0,
        activeAccounts: 0,
        latencyMs: Math.round(performance.now() - t0),
        error: String(err),
      });
    } finally {
      setCheckingProxy(false);
    }
  };

  const handleRemotePetAction = async (item: {
    action: PetAction;
    message: string;
    sub?: string;
    voiceKey?: string;
  }) => {
    if (!isTauri()) {
      petAudio.playCare();
      showToast(`[预览模拟] 已触发伴侣动作「${item.action}」：${item.message}`, 'info');
      return;
    }
    try {
      if (!status.pet_window_open) {
        await studioService.launchPet();
        await onRefresh();
        await new Promise((r) => setTimeout(r, 320));
      }
      await emit('pet:remote-action', {
        action: item.action,
        message: item.message,
        sub: item.sub,
        voiceKey: item.voiceKey,
      });
      showToast(`已向桌面伴侣下发原声动作指令：${item.message}`, 'success');
    } catch (err) {
      showToast(`伴侣指令发送失败: ${String(err)}`, 'error');
    }
  };

  const handleSimulateLowQuotaToast = async () => {
    const mockAlert = evaluateLowQuotaAlert(
      [{ name: 'claude-sonnet-4-6', display_name: 'Claude Sonnet 4.6', percentage: 12 }],
      20,
    );
    petAudio.playQuotaAlert();
    if (isTauri() && status.pet_window_open) {
      await emit('pet:remote-action', {
        action: 'stomp',
        message: mockAlert.alertMessage,
      }).catch(() => {});
    }
    showToast(mockAlert.alertMessage, 'warning');
  };

  return (
    <div className="space-y-6">
      {/* 第一区：Studio 核心子系统与网关一键体检 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 text-sm font-bold text-gray-900 dark:text-white">
                <FlaskConical className="h-4 w-4 text-indigo-500" />
                Studio 核心子系统健康自检
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                一键核验汉化词典完整性、全部材质包安全沙盒编译、骨骼 WebP 缓存与原子文件读写权限。
              </p>
            </div>
            <button
              type="button"
              onClick={handleRunStudioDiag}
              disabled={runningDiag}
              className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-sky-500 px-4 py-2 text-xs font-semibold text-white shadow hover:opacity-95 disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${runningDiag ? 'animate-spin' : ''}`} />
              {runningDiag ? '正在执行全量体检...' : '运行全量引擎自检'}
            </button>
          </div>

          {report ? (
            <div className="space-y-2.5 pt-2">
              <div className="flex items-center justify-between text-xs px-1">
                <span
                  className={`font-semibold ${
                    report.all_passed ? 'text-emerald-500' : 'text-amber-500'
                  }`}
                >
                  {report.all_passed ? '✓ 全部核心检查项通过' : '⚠ 存在待关注检查项'}
                </span>
                <span className="font-mono text-gray-400 flex items-center gap-1">
                  <Clock className="h-3 w-3" /> 总耗时 {report.total_ms}ms
                </span>
              </div>
              {report.items.map((item) => (
                <div
                  key={item.key}
                  className="flex items-start justify-between gap-3 rounded-xl border border-gray-200/70 dark:border-white/10 bg-gray-50/70 dark:bg-black/25 px-3.5 py-2.5"
                >
                  <div className="flex items-start gap-2.5 min-w-0">
                    {item.passed ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
                    )}
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-gray-900 dark:text-white">
                        {item.name}
                      </div>
                      <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5 break-all">
                        {item.detail}
                      </div>
                    </div>
                  </div>
                  <span className="shrink-0 rounded-md bg-gray-200/70 dark:bg-white/10 px-2 py-0.5 text-[10px] font-mono text-gray-600 dark:text-gray-300">
                    {item.duration_ms}ms
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-gray-200 dark:border-white/10 py-8 text-center text-xs text-gray-400">
              点击右上角「运行全量引擎自检」生成实时体检报告
            </div>
          )}
        </div>

        {/* 本地反代网关与账号池快检 */}
        <div className="lg:col-span-5 rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-4 shadow-sm flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-gray-900 dark:text-white">
                <Activity className="h-4 w-4 text-emerald-500" />
                本地反代网关与账号池快检
              </div>
              <button
                type="button"
                onClick={handleCheckGateway}
                disabled={checkingProxy}
                className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-white/15 px-3 py-1.5 text-xs font-semibold hover:bg-gray-100 dark:hover:bg-white/5"
              >
                <Zap className="h-3.5 w-3.5 text-amber-500" />
                {checkingProxy ? '探测中...' : '探测网关状态'}
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="rounded-xl bg-gray-50 dark:bg-black/25 border border-gray-200/60 dark:border-white/10 p-3">
                <div className="text-[11px] text-gray-400">录入总账号数</div>
                <div className="text-lg font-bold text-gray-900 dark:text-white mt-0.5 font-mono">
                  {accounts.length}
                </div>
              </div>
              <div className="rounded-xl bg-gray-50 dark:bg-black/25 border border-gray-200/60 dark:border-white/10 p-3">
                <div className="text-[11px] text-gray-400">反代服务状态</div>
                <div className="text-sm font-bold mt-1">
                  {proxyHealth ? (
                    proxyHealth.running ? (
                      <span className="text-emerald-500">运行中 (:{proxyHealth.port})</span>
                    ) : (
                      <span className="text-amber-500">未启动</span>
                    )
                  ) : (
                    <span className="text-gray-400">待探测</span>
                  )}
                </div>
              </div>
            </div>

            {proxyHealth && (
              <div className="rounded-xl bg-slate-950 text-slate-200 p-3.5 text-xs font-mono space-y-1 border border-white/10">
                <div>IPC 往返延迟: {proxyHealth.latencyMs} ms</div>
                <div>活跃轮换池账号: {proxyHealth.activeAccounts} 个</div>
                {proxyHealth.error && (
                  <div className="text-rose-400 break-all">异常详情: {proxyHealth.error}</div>
                )}
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-gray-100 dark:border-white/10 flex items-center justify-between gap-2">
            <span className="text-[11px] text-gray-500 dark:text-gray-400">
              配额阈值告警链路演练
            </span>
            <button
              type="button"
              onClick={handleSimulateLowQuotaToast}
              className="inline-flex items-center gap-1.5 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 px-3 py-1.5 text-xs font-semibold text-amber-600 dark:text-amber-300 transition-colors"
            >
              模拟低配额预警通知
            </button>
          </div>
        </div>
      </div>

      {/* 第二区：桌面伴侣动作遥控与 WebAudio 治愈音效沙盒 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-gray-900 dark:text-white">
              <Volume2 className="h-4 w-4 text-sky-500" />
              WebAudio 零依赖治愈合成器试听室（12 组实时波形）
            </div>
            <span className="text-[11px] text-gray-400">点击任意音色立即合成播放</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
            {SOUND_SAMPLES.map((snd) => (
              <button
                key={snd.label}
                type="button"
                onClick={() => {
                  petAudio.muted = false;
                  snd.trigger();
                }}
                className="group rounded-xl border border-gray-200/80 dark:border-white/10 bg-gray-50/80 dark:bg-black/25 hover:border-sky-500/50 hover:bg-sky-500/10 p-2.5 text-left transition-all"
              >
                <div className="flex items-center justify-between text-xs font-bold text-gray-800 dark:text-white group-hover:text-sky-500">
                  <span>{snd.label}</span>
                  <Play className="h-3 w-3 opacity-60 group-hover:opacity-100" />
                </div>
                <div className="text-[10px] text-gray-400 mt-1 line-clamp-1">{snd.desc}</div>
              </button>
            ))}
          </div>

          <div className="pt-3 border-t border-gray-100 dark:border-white/10 space-y-2.5">
            <div className="flex items-center gap-2 text-xs font-bold text-gray-800 dark:text-gray-200">
              <Sparkles className="h-3.5 w-3.5 text-pink-500" />
              桌面伴侣远程动作联调（若伴侣未开启将自动唤起并演绎）
            </div>
            <div className="flex flex-wrap gap-2">
              {REMOTE_PET_ACTIONS.map((item) => (
                <button
                  key={item.action}
                  type="button"
                  onClick={() => handleRemotePetAction(item)}
                  className="rounded-xl border border-gray-200 dark:border-white/15 bg-white dark:bg-white/5 hover:bg-pink-500/15 hover:border-pink-500/40 px-3 py-1.5 text-xs font-medium transition-colors"
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* LRC 时间轴解析与二分命中演练场 */}
        <div className="lg:col-span-5 rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/85 dark:bg-slate-900/65 backdrop-blur-xl p-5 space-y-3.5 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-gray-900 dark:text-white">
              <Music2 className="h-4 w-4 text-emerald-500" />
              LRC 毫秒时间轴解析沙盒
            </div>
            <span className="text-[11px] font-mono text-emerald-500">
              {(simTimeMs / 1000).toFixed(1)}s · 共 {parsedLrc.length} 句
            </span>
          </div>

          <div>
            <input
              type="range"
              min={0}
              max={24000}
              step={100}
              value={simTimeMs}
              onChange={(e) => setSimTimeMs(Number(e.target.value))}
              className="w-full accent-emerald-500"
            />
            <div className="rounded-xl bg-slate-950 text-center px-3 py-2.5 border border-white/10 mt-1">
              <div className="text-xs font-bold text-amber-300 truncate">
                {activeLrcIdx >= 0 ? parsedLrc[activeLrcIdx]?.text : '暂无可解析歌词'}
              </div>
              {activeLrcIdx >= 0 && parsedLrc[activeLrcIdx + 1] && (
                <div className="text-[10.5px] text-slate-400 mt-0.5 truncate">
                  下一句：{parsedLrc[activeLrcIdx + 1].text}
                </div>
              )}
            </div>
          </div>

          <textarea
            rows={4}
            value={lrcInput}
            onChange={(e) => setLrcInput(e.target.value)}
            className="w-full rounded-xl border border-gray-200 dark:border-white/10 bg-slate-950 p-2.5 text-[11px] font-mono text-emerald-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
          />
        </div>
      </div>
    </div>
  );
};
