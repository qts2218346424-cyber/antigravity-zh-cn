import React, { useCallback, useEffect, useState } from 'react';
import { listen } from '@tauri-apps/api/event';
import {
  Heart,
  Languages,
  Palette,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { showToast } from '../../components/common/ToastContainer';
import { studioService } from '../../services/studioService';
import type { ReapplyCheckResult, SkinInfo, StudioStatus } from '../../types/studio';
import { isTauri } from '../../utils/env';
import { CustomizerTab } from './CustomizerTab';
import { L10nTab } from './L10nTab';
import { PetCenterTab, WatchdogTab } from './PetAndWatchdogTab';
import { SkinGalleryTab } from './SkinGalleryTab';

type StudioTabKey = 'skins' | 'customizer' | 'l10n' | 'pet' | 'watchdog';

const EMPTY_STATUS: StudioStatus = {
  install_dir: null,
  ide_root: null,
  agent_status: 'not_found',
  ide_status: 'not_found',
  active_skin: null,
  skin_enabled: false,
  ide_enabled: false,
  auto_reapply: true,
  autostart_enabled: false,
  updates_disabled: false,
  splash_character: 'nezuko',
  lang: 'zh-cn',
  enable_pet: true,
  enable_skin: true,
  pet_window_open: false,
  config_dir: '',
  resource_dir: '',
  reapply_logs: [],
};

const Studio: React.FC = () => {
  const [activeTab, setActiveTab] = useState<StudioTabKey>('skins');
  const [status, setStatus] = useState<StudioStatus>(EMPTY_STATUS);
  const [skins, setSkins] = useState<SkinInfo[]>([]);
  const [customizeSkinId, setCustomizeSkinId] = useState<string>('obsidian-glass');
  const [loading, setLoading] = useState(true);

  const refreshAll = useCallback(async () => {
    try {
      const [st, skList] = await Promise.all([
        studioService.getStatus(),
        studioService.listSkins(),
      ]);
      setStatus(st);
      setSkins(skList);
      if (st.active_skin && skList.some((s) => s.id === st.active_skin)) {
        setCustomizeSkinId((prev) => prev || st.active_skin || skList[0]?.id || 'obsidian-glass');
      } else if (skList.length > 0) {
        setCustomizeSkinId((prev) => (skList.some((s) => s.id === prev) ? prev : skList[0].id));
      }
    } catch (err) {
      console.error('刷新 Studio 工作台状态失败:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshAll();
    let unlisten: (() => void) | undefined;
    if (isTauri()) {
      listen<ReapplyCheckResult>('studio:reapplied', (ev) => {
        if (ev.payload?.actions?.length) {
          showToast(`后台看门狗：${ev.payload.actions.join('；')}`, 'info');
        }
        refreshAll();
      })
        .then((fn) => {
          unlisten = fn;
        })
        .catch(() => {});
    }
    return () => {
      if (unlisten) unlisten();
    };
  }, [refreshAll]);

  const tabs: Array<{ key: StudioTabKey; label: string; icon: React.ComponentType<{ className?: string }> }> = [
    { key: 'skins', label: '光学材质画廊', icon: Sparkles },
    { key: 'customizer', label: 'Color DNA 实验室', icon: Palette },
    { key: 'l10n', label: '全量汉化引擎', icon: Languages },
    { key: 'pet', label: '灵动桌面伴侣', icon: Heart },
    { key: 'watchdog', label: '自动维护哨兵', icon: ShieldCheck },
  ];

  const quickTogglePet = async () => {
    try {
      if (status.pet_window_open) {
        await studioService.closePet();
      } else {
        await studioService.launchPet();
      }
      await refreshAll();
    } catch (err) {
      showToast(`切换桌面伴侣失败: ${String(err)}`, 'error');
    }
  };

  return (
    <div className="h-full overflow-y-auto px-6 py-6 max-w-7xl mx-auto space-y-6">
      {/* 顶部工作台横幅（黑曜石磨玻璃高定风格） */}
      <div className="relative overflow-hidden rounded-2xl border border-gray-200/80 dark:border-white/10 bg-white/80 dark:bg-[#0B0F17]/80 backdrop-blur-xl p-5 shadow-sm">
        <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="pointer-events-none absolute left-1/3 -bottom-20 h-44 w-44 rounded-full bg-emerald-500/10 blur-3xl" />
        <div className="relative flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-slate-800 via-indigo-900 to-indigo-600 text-white shadow-md ring-1 ring-white/15">
                <Sparkles className="h-4 w-4" />
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold tracking-tight text-gray-900 dark:text-base-content">
                    Antigravity Studio · 光学美化工坊
                  </h1>
                  {status.active_skin && (
                    <span className="inline-flex items-center gap-1 rounded-full border border-indigo-500/25 bg-indigo-500/10 px-2.5 py-0.5 text-[10px] font-medium text-indigo-600 dark:text-indigo-300">
                      <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" />
                      当前材质：{status.active_skin}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  融合高定光学材质引擎、Color DNA 物理表面实验室、官方客户端全量中文化、3D 视差灵动伴侣与 Tokio 自动防更新哨兵。
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {!isTauri() && (
              <span className="rounded-xl bg-amber-500/10 border border-amber-500/25 px-3 py-1.5 text-[11px] font-medium text-amber-600 dark:text-amber-400">
                Web 预览态（系统级注入需运行桌面端）
              </span>
            )}
            <button
              onClick={quickTogglePet}
              className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-medium border backdrop-blur-md transition-all ${
                status.pet_window_open
                  ? 'border-pink-400/50 bg-pink-500/15 text-pink-600 dark:text-pink-300 shadow-sm shadow-pink-500/10'
                  : 'border-gray-200 dark:border-white/10 bg-white/70 dark:bg-white/5 hover:bg-gray-100 dark:hover:bg-white/10'
              }`}
            >
              <Heart className={`h-3.5 w-3.5 ${status.pet_window_open ? 'fill-pink-500 text-pink-500' : ''}`} />
              {status.pet_window_open ? '伴侣视窗运行中' : '召出灵动伴侣'}
            </button>
            <button
              onClick={refreshAll}
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-white/10 bg-white/70 dark:bg-white/5 px-3 py-2 text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/10 transition-colors"
              title="刷新全部探测状态"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              刷新探测
            </button>
          </div>
        </div>
      </div>

      {/* 五大功能区导航标签 */}
      <div className="inline-flex flex-wrap gap-1.5 rounded-2xl border border-gray-200/80 dark:border-white/10 bg-gray-100/70 dark:bg-[#0B0F17]/60 p-1.5 backdrop-blur-md">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                active
                  ? 'bg-white dark:bg-white/15 text-gray-900 dark:text-white shadow-sm ring-1 ring-black/5 dark:ring-white/15'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-white/50 dark:hover:bg-white/5'
              }`}
            >
              <Icon className={`h-3.5 w-3.5 ${active ? 'text-indigo-500 dark:text-indigo-400' : ''}`} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* 标签内容视图 */}
      <div>
        {activeTab === 'skins' && (
          <SkinGalleryTab
            skins={skins}
            status={status}
            onRefresh={refreshAll}
            onSelectForCustomize={(id) => {
              setCustomizeSkinId(id);
              setActiveTab('customizer');
            }}
          />
        )}
        {activeTab === 'customizer' && (
          <CustomizerTab
            skins={skins}
            selectedSkinId={customizeSkinId}
            onSelectSkinId={setCustomizeSkinId}
            onRefresh={refreshAll}
          />
        )}
        {activeTab === 'l10n' && <L10nTab status={status} onRefresh={refreshAll} />}
        {activeTab === 'pet' && <PetCenterTab status={status} onRefresh={refreshAll} />}
        {activeTab === 'watchdog' && <WatchdogTab status={status} onRefresh={refreshAll} />}
      </div>
    </div>
  );
};

export default Studio;
