import React from 'react';
import { AlertTriangle, Hourglass, Activity, ShieldAlert, Unlock } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface QoSStatusBadgeProps {
    status?: 'suspicious' | 'jailed' | 'probing' | 'half_open' | null;
    resetSeconds?: number | null;
    size?: 'xs' | 'sm' | 'md';
    onRelease?: () => void;
}

export const QoSStatusBadge: React.FC<QoSStatusBadgeProps> = ({
    status,
    resetSeconds,
    size = 'sm',
    onRelease,
}) => {
    const { t } = useTranslation();

    if (!status) return null;

    const sizeClass =
        size === 'xs'
            ? 'text-[8px] leading-tight px-1 py-0.5'
            : size === 'md'
                ? 'text-[10px] px-2 py-0.5'
                : 'text-[9px] px-1.5 py-0.5';

    const iconClass = size === 'xs' ? 'w-2 h-2 shrink-0' : 'w-2.5 h-2.5 shrink-0';

    const formatRemaining = (secs: number | null | undefined) => {
        if (!secs || secs <= 0) return '';
        if (secs >= 3600) {
            const h = Math.floor(secs / 3600);
            const m = Math.floor((secs % 3600) / 60);
            return `${h}h ${m}m`;
        }
        if (secs >= 60) {
            const m = Math.floor(secs / 60);
            const s = secs % 60;
            return s > 0 ? `${m}m ${s}s` : `${m}m`;
        }
        return `${secs}s`;
    };

    const remainingStr = formatRemaining(resetSeconds);

    switch (status) {
        case 'suspicious':
            return (
                <span
                    className={`flex items-center gap-0.5 rounded-md bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 font-bold shadow-sm border border-yellow-500/30 shrink-0 ${sizeClass}`}
                    title={t('accounts.qos.suspicious_hint')}
                >
                    <AlertTriangle className={iconClass} />
                    <span>{t('accounts.qos.suspicious')}</span>
                </span>
            );
        case 'jailed':
            return (
                <span
                    className={`inline-flex items-center gap-1 rounded-md bg-amber-500/20 text-amber-700 dark:text-amber-300 font-bold shadow-sm border border-amber-500/50 ring-1 ring-amber-400/30 shrink-0 ${sizeClass}`}
                    title={
                        remainingStr
                            ? `${t('accounts.qos.jailed_hint')}\n剩余冷却时间: ${remainingStr} (可随时点击解除恢复调度)`
                            : t('accounts.qos.jailed_hint')
                    }
                >
                    <Hourglass className={`${iconClass} text-amber-600 dark:text-amber-400 animate-pulse`} />
                    <span>
                        {t('accounts.qos.jailed')}
                        {remainingStr && (
                            <span className="ml-1 text-[9px] font-mono opacity-90">({remainingStr})</span>
                        )}
                    </span>
                    {onRelease && (
                        <button
                            type="button"
                            onClick={(e) => {
                                e.stopPropagation();
                                onRelease();
                            }}
                            className="ml-0.5 px-1.5 py-0.2 rounded bg-amber-500 hover:bg-amber-600 active:scale-95 text-white dark:bg-amber-600 dark:hover:bg-amber-500 font-bold text-[9px] shadow-xs transition-all flex items-center gap-0.5 shrink-0 cursor-pointer"
                            title={t('accounts.qos.release_tooltip', '点击立即手动移除小黑屋限制，恢复账号正常调度')}
                        >
                            <Unlock className="w-2.5 h-2.5" />
                            <span>{t('accounts.qos.release_btn', '解除')}</span>
                        </button>
                    )}
                </span>
            );
        case 'probing':
            return (
                <span
                    className={`flex items-center gap-0.5 rounded-md bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 font-bold shadow-sm border border-yellow-500/30 shrink-0 ${sizeClass}`}
                    title={t('accounts.qos.probing_hint')}
                >
                    <Activity className={`${iconClass} animate-pulse`} />
                    <span>{t('accounts.qos.probing')}</span>
                </span>
            );
        case 'half_open':
            return (
                <span
                    className={`flex items-center gap-0.5 rounded-md bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 font-bold shadow-sm border border-yellow-500/30 shrink-0 ${sizeClass}`}
                    title={t('accounts.qos.half_open_hint')}
                >
                    <ShieldAlert className={iconClass} />
                    <span>{t('accounts.qos.half_open')}</span>
                </span>
            );
        default:
            return null;
    }
};
