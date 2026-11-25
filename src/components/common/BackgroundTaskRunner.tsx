import { useEffect, useRef } from 'react';
import { useConfigStore } from '../../stores/useConfigStore';
import { useAccountStore } from '../../stores/useAccountStore';

function BackgroundTaskRunner() {
    const { config } = useConfigStore();
    const { refreshAllQuotas, syncAccountFromDb } = useAccountStore();

    // Use refs to track previous state to detect "off -> on" transitions
    const prevAutoRefreshRef = useRef(false);
    const hasMountedRef = useRef(false);
    const lastSyncTimeRef = useRef(0);

    // Auto Refresh Quota Effect
    useEffect(() => {
        if (!config) return;

        const { auto_refresh } = config;

        // [FIX #3726 & #3958] 仅在用户手动从关闭 (false) 切换为开启 (true) 时触发即时刷新。
        // 定时全量刷新已完全下沉至 Rust 后端常驻调度器 (modules::auto_refresh)：
        // 确保无论在无头模式 (--headless) 还是桌面客户端模式下均能独立且定时执行，
        // 并彻底消除多前端窗口（如主窗口 + 悬浮窗）并发重复轮询全量配额的问题。
        const isFirstMount = !hasMountedRef.current;
        hasMountedRef.current = true;

        if (auto_refresh && !prevAutoRefreshRef.current && !isFirstMount) {
            console.log('[BackgroundTask] Auto-refresh manually toggled on, executing once...');
            refreshAllQuotas().catch((err) => {
                console.error('[BackgroundTask] Manual toggle quota refresh failed:', err);
            });
        }
        prevAutoRefreshRef.current = auto_refresh;
    }, [config?.auto_refresh, refreshAllQuotas]);

    // Auto Sync Current Local Account Effect (对齐原项目本机凭据自动感知与同步)
    useEffect(() => {
        if (!config?.auto_sync) return;

        const intervalMinutes = Math.max(1, config.sync_interval || 2);
        const runSyncSafely = () => {
            const now = Date.now();
            if (now - lastSyncTimeRef.current < 15000) return;
            lastSyncTimeRef.current = now;
            syncAccountFromDb().catch(() => {});
        };

        const initTimer = setTimeout(runSyncSafely, 3000);
        const intervalId = setInterval(
            runSyncSafely,
            Math.min(intervalMinutes * 60 * 1000, 2147483647)
        );

        const handleWindowFocus = () => {
            if (Date.now() - lastSyncTimeRef.current >= 30000) {
                runSyncSafely();
            }
        };
        window.addEventListener('focus', handleWindowFocus);

        return () => {
            clearTimeout(initTimer);
            clearInterval(intervalId);
            window.removeEventListener('focus', handleWindowFocus);
        };
    }, [config?.auto_sync, config?.sync_interval, syncAccountFromDb]);

    // Render nothing
    return null;
}

export default BackgroundTaskRunner;
