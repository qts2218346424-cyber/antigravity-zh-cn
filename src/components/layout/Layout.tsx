import { Outlet } from 'react-router-dom';
import { getCurrentWindow } from '@tauri-apps/api/window';
import Navbar from '../navbar/Navbar';
import BackgroundTaskRunner from '../common/BackgroundTaskRunner';
import ToastContainer from '../common/ToastContainer';
import { useViewStore } from '../../stores/useViewStore';
import { useAccountStore } from '../../stores/useAccountStore';
import { usePedalModeStore } from '../../stores/usePedalModeStore';
import { PedalNoticeModal } from '../pedal/PedalNoticeModal';
import { PedalBanner } from '../pedal/PedalBanner';
import MiniView from './MiniView';
import { useEffect } from 'react';
import { isTauri } from '../../utils/env';
import { ensureFullViewState } from '../../utils/windowManager';

function Layout() {
    const { isMiniView } = useViewStore();
    const { accounts, updateAccountPriority, toggleProxyStatus } = useAccountStore();
    const { active, checkCandidates, checkAndAutoRecover } = usePedalModeStore();

    // 蹬额度模式：账号状态变化或配额刷新时自动检测
    useEffect(() => {
        if (!accounts || accounts.length === 0) return;
        if (active) {
            checkAndAutoRecover(accounts, updateAccountPriority, toggleProxyStatus);
        } else {
            checkCandidates(accounts);
        }
    }, [accounts, active, checkCandidates, checkAndAutoRecover, updateAccountPriority, toggleProxyStatus]);

    // 蹬额度模式：每 60 秒定期心跳校验临期与重置倒计时
    useEffect(() => {
        const timer = setInterval(() => {
            const currentAccounts = useAccountStore.getState().accounts;
            if (!currentAccounts || currentAccounts.length === 0) return;
            const pedal = usePedalModeStore.getState();
            if (pedal.active) {
                pedal.checkAndAutoRecover(currentAccounts, updateAccountPriority, toggleProxyStatus);
            } else {
                pedal.checkCandidates(currentAccounts);
            }
        }, 60000);
        return () => clearInterval(timer);
    }, [updateAccountPriority, toggleProxyStatus]);

    // Ensure correct window state when in Full View (not Mini View)
    // This handles the case where the app was closed in Mini View (small size, no decorations)
    // and restarted (defaults to Full View state but keeps last window properties)
    useEffect(() => {
        if (!isMiniView && isTauri()) {
            ensureFullViewState();
        }
    }, [isMiniView]);

    if (!isTauri() && isMiniView) {
        return (
            <>
                <BackgroundTaskRunner />
                <ToastContainer />
                <PedalNoticeModal />
                <MiniView />
            </>
        );
    }

    return (
        <div className="h-screen flex flex-col bg-[#FAFBFC] dark:bg-base-300">
            {/* 仅在 Tauri 桌面端挂载标题栏拖拽区：留出右上角原生窗口控制按钮，层级低于全局弹窗 (z-30 < z-50) */}
            {isTauri() && (
                <div
                    className="fixed top-0 left-0 right-36 h-9 z-30 select-none"
                    style={{
                        backgroundColor: 'rgba(0,0,0,0.001)',
                        cursor: 'default',
                        WebkitUserSelect: 'none'
                    }}
                    data-tauri-drag-region
                    onMouseDown={(e) => {
                        if (e.button === 0 && e.detail === 1) {
                            getCurrentWindow().startDragging().catch(() => {});
                        }
                    }}
                    onDoubleClick={() => {
                        getCurrentWindow().toggleMaximize().catch(() => {});
                    }}
                />
            )}
            <BackgroundTaskRunner />
            <ToastContainer />
            <PedalNoticeModal />
            <Navbar />
            <PedalBanner />
            <main className="flex-1 overflow-hidden flex flex-col relative">
                <Outlet />
            </main>
        </div>
    );
}

export default Layout;
