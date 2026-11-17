import { useEffect, useRef } from 'react';
import { useConfigStore } from '../../stores/useConfigStore';
import { useAccountStore } from '../../stores/useAccountStore';

function BackgroundTaskRunner() {
    const { config } = useConfigStore();
    const { refreshAllQuotas, syncAccountFromDb } = useAccountStore();

    // Use refs to track previous state to detect "off -> on" transitions
    const prevAutoRefreshRef = useRef(false);
    const hasMountedRef = useRef(false);
    const startupRefreshDoneRef = useRef(false);
    const lastSyncTimeRef = useRef(0);

    // Auto Refresh Quota Effect
    useEffect(() => {
        if (!config) return;

        let intervalId: ReturnType<typeof setInterval> | null = null;
        let startupTimerId: ReturnType<typeof setTimeout> | null = null;
        const { auto_refresh, refresh_interval } = config;

        const isFirstMount = !hasMountedRef.current;
        hasMountedRef.current = true;

        if (auto_refresh && !prevAutoRefreshRef.current && !isFirstMount) {
            console.log('[BackgroundTask] Auto-refresh manually toggled on, executing once...');
            refreshAllQuotas().catch(() => {});
        }
        prevAutoRefreshRef.current = auto_refresh;

        // 启动后延迟检查：若开启了自动刷新，且存在无配额或配额已超过刷新间隔未更新的账号，静默补刷一次
        if (auto_refresh && !startupRefreshDoneRef.current) {
            startupRefreshDoneRef.current = true;
            startupTimerId = setTimeout(() => {
                const { accounts } = useAccountStore.getState();
                if (!accounts || accounts.length === 0) return;
                const nowSec = Math.floor(Date.now() / 1000);
                const staleThresholdSec = Math.max(1, refresh_interval || 10) * 60;
                const hasStaleOrMissing = accounts.some(
                    (acc) =>
                        !acc.disabled &&
                        (!acc.quota || !acc.quota.last_updated || nowSec - acc.quota.last_updated >= staleThresholdSec)
                );
                if (hasStaleOrMissing) {
                    console.log('[BackgroundTask] Startup stale quota detected, refreshing in background...');
                    refreshAllQuotas().catch(() => {});
                }
            }, 5000);
        }

        if (auto_refresh && refresh_interval > 0) {
            console.log(`[BackgroundTask] Starting auto-refresh quota timer: ${refresh_interval} mins`);
            intervalId = setInterval(() => {
                console.log('[BackgroundTask] Auto-refreshing all quotas...');
                refreshAllQuotas().catch(() => {});
            }, Math.min(refresh_interval * 60 * 1000, 2147483647));
        }

        return () => {
            if (startupTimerId) {
                clearTimeout(startupTimerId);
            }
            if (intervalId) {
                console.log('[BackgroundTask] Clearing auto-refresh timer');
                clearInterval(intervalId);
            }
        };
    }, [config?.auto_refresh, config?.refresh_interval, refreshAllQuotas]);

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
