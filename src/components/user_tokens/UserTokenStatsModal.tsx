import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
import {
    BarChart3,
    X,
    TrendingUp,
    Zap,
    Cpu,
    Globe,
    Copy,
    Check,
    Activity,
    Layers,
    Shield,
} from 'lucide-react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from 'recharts';
import { request as invoke } from '../../utils/request';
import { copyToClipboard } from '../../utils/clipboard';

export interface UserTokenSummaryItem {
    id: string;
    token: string;
    username: string;
    description?: string;
    enabled: boolean;
    expires_type: string;
    expires_at?: number;
    max_ips: number;
    total_requests: number;
    total_tokens_used: number;
}

export interface UserTokenDetailedSummary {
    total_requests: number;
    total_input_tokens: number;
    total_output_tokens: number;
    total_tokens: number;
    success_requests: number;
    failed_requests: number;
}

export interface UserTokenTrendPoint {
    timestamp_label: string;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    requests: number;
}

export interface UserTokenModelStat {
    model: string;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    requests: number;
    percentage: number;
}

export interface UserTokenRecentIp {
    id: string;
    token_id: string;
    ip_address: string;
    first_seen_at: number;
    last_seen_at: number;
    request_count: number;
    user_agent?: string;
}

export interface UserTokenDetailedStats {
    token: UserTokenSummaryItem;
    summary: UserTokenDetailedSummary;
    trend: UserTokenTrendPoint[];
    models: UserTokenModelStat[];
    recent_ips: UserTokenRecentIp[];
}

interface UserTokenStatsModalProps {
    isOpen: boolean;
    onClose: () => void;
    token: UserTokenSummaryItem | null;
}

type TimeRangeOption = '24h' | '7d' | '30d' | 'all';

const MODEL_PALETTE = [
    '#3B82F6', // Blue
    '#8B5CF6', // Purple
    '#10B981', // Emerald
    '#F59E0B', // Amber
    '#EC4899', // Pink
    '#06B6D4', // Cyan
    '#F97316', // Orange
    '#6366F1', // Indigo
];

function formatTokens(val: number): string {
    if (!val || val === 0) return '0';
    if (val >= 1_000_000_000) return (val / 1_000_000_000).toFixed(2) + 'B';
    if (val >= 1_000_000) return (val / 1_000_000).toFixed(2) + 'M';
    if (val >= 1_000) return (val / 1_000).toFixed(1) + 'k';
    return val.toLocaleString();
}

function formatTime(ts?: number): string {
    if (!ts) return '-';
    return new Date(ts * 1000).toLocaleString();
}

export const UserTokenStatsModal: React.FC<UserTokenStatsModalProps> = ({
    isOpen,
    onClose,
    token,
}) => {
    const { t } = useTranslation();
    const [timeRange, setTimeRange] = useState<TimeRangeOption>('7d');
    const [stats, setStats] = useState<UserTokenDetailedStats | null>(null);
    const [loading, setLoading] = useState(false);
    const [copied, setCopied] = useState(false);

    const loadStats = useCallback(async () => {
        if (!token) return;
        setLoading(true);
        try {
            const data = await invoke<UserTokenDetailedStats>('get_user_token_stats', {
                id: token.id,
                timeRange,
            });
            setStats(data);
        } catch (e) {
            console.error('Failed to load user token stats', e);
        } finally {
            setLoading(false);
        }
    }, [token, timeRange]);

    useEffect(() => {
        if (isOpen && token) {
            loadStats();
        } else {
            setStats(null);
        }
    }, [isOpen, token, timeRange, loadStats]);

    const handleCopy = () => {
        if (!token) return;
        copyToClipboard(token.token);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (!isOpen || !token) return null;

    const summary = stats?.summary || {
        total_requests: token.total_requests,
        total_input_tokens: 0,
        total_output_tokens: 0,
        total_tokens: token.total_tokens_used,
        success_requests: 0,
        failed_requests: 0,
    };

    const successRate = summary.total_requests > 0
        ? Math.round((summary.success_requests / summary.total_requests) * 100)
        : 100;

    const avgTokensPerReq = summary.total_requests > 0
        ? Math.round(summary.total_tokens / summary.total_requests)
        : 0;

    return createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-5 overflow-hidden">
            {/* 半透明遮罩层 */}
            <div
                className="fixed inset-0 bg-black/60 dark:bg-black/80 backdrop-blur-md transition-opacity"
                onClick={onClose}
            />

            {/* 模态框主体卡片 */}
            <div className="relative z-10 bg-white dark:bg-[#181a20] text-gray-900 dark:text-gray-100 rounded-3xl max-w-4xl w-full p-5 sm:p-6 shadow-2xl border border-gray-200/90 dark:border-white/10 flex flex-col max-h-[90vh] overflow-hidden transition-all animate-in fade-in zoom-in-95 duration-200">
                {/* 顶部标题区 */}
                <div className="flex items-center justify-between pb-3.5 border-b border-gray-100 dark:border-white/10 shrink-0 gap-3">
                    {/* 左侧身份区 */}
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                        <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-blue-500/20 shrink-0">
                            {token.username.substring(0, 2).toUpperCase()}
                        </div>
                        <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2 min-w-0">
                                <h3
                                    className="text-base sm:text-lg font-bold text-gray-900 dark:text-white uppercase tracking-wider truncate"
                                    title={token.username}
                                >
                                    {token.username}
                                </h3>
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium whitespace-nowrap shrink-0 ${
                                    token.enabled
                                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                                        : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                                }`}>
                                    {token.enabled ? t('user_token.enabled', '启用') : t('user_token.disabled', '禁用')}
                                </span>
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                                <code className="bg-gray-100 dark:bg-base-200 px-2 py-0.5 rounded text-[11px] font-mono text-gray-600 dark:text-gray-400 shrink-0">
                                    {token.token.substring(0, 8)}••••••••
                                </code>
                                <button
                                    onClick={handleCopy}
                                    className="p-1 hover:bg-gray-200 dark:hover:bg-white/10 rounded-md transition-all text-gray-400 hover:text-gray-600 dark:hover:text-white shrink-0"
                                    title={t('common.copy', '复制')}
                                >
                                    {copied ? <Check size={12} className="text-emerald-500" /> : <Copy size={12} />}
                                </button>
                                {token.description && (
                                    <span className="text-[11px] text-gray-400 truncate hidden sm:inline" title={token.description}>
                                        • {token.description}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* 右侧控制区 */}
                    <div className="flex items-center gap-2 shrink-0">
                        {/* 时间范围切换 */}
                        <div className="inline-flex items-center bg-gray-100 dark:bg-white/5 p-1 rounded-xl text-xs font-medium shrink-0">
                            {(['24h', '7d', '30d', 'all'] as TimeRangeOption[]).map((range) => (
                                <button
                                    key={range}
                                    onClick={() => setTimeRange(range)}
                                    className={`px-2.5 py-1 rounded-lg transition-all whitespace-nowrap shrink-0 ${
                                        timeRange === range
                                            ? 'bg-white dark:bg-blue-600 text-blue-600 dark:text-white shadow-sm font-semibold'
                                            : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                                    }`}
                                >
                                    {range === '24h' && t('user_token.range_24h', '24小时')}
                                    {range === '7d' && t('user_token.range_7d', '近7天')}
                                    {range === '30d' && t('user_token.range_30d', '近30天')}
                                    {range === 'all' && t('user_token.range_all', '全部')}
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={onClose}
                            className="p-2 rounded-xl text-gray-400 hover:text-gray-700 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors shrink-0"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* 内容区域（滚动容器） */}
                <div className="flex-1 overflow-y-auto pt-4 pb-2 space-y-4 pr-1 scrollbar-thin">
                    {/* KPI 4 宫格 */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        {/* 总 Token */}
                        <div className="bg-gradient-to-br from-blue-50/50 to-indigo-50/30 dark:from-blue-950/20 dark:to-indigo-950/10 p-3.5 rounded-2xl border border-blue-100/80 dark:border-blue-900/30">
                            <div className="flex items-center justify-between text-blue-600 dark:text-blue-400 mb-1.5">
                                <span className="text-[11px] font-medium">{t('token_stats.total_tokens', '总 Token')}</span>
                                <Zap className="w-4 h-4 opacity-70" />
                            </div>
                            <div className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-gray-900 dark:text-white">
                                {formatTokens(summary.total_tokens)}
                            </div>
                            <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-1 flex items-center justify-between whitespace-nowrap">
                                <span>{t('token_stats.input', '输入')}: {formatTokens(summary.total_input_tokens)}</span>
                                <span>{t('token_stats.output', '输出')}: {formatTokens(summary.total_output_tokens)}</span>
                            </div>
                        </div>

                        {/* 总请求数 */}
                        <div className="bg-gradient-to-br from-purple-50/50 to-pink-50/30 dark:from-purple-950/20 dark:to-pink-950/10 p-3.5 rounded-2xl border border-purple-100/80 dark:border-purple-900/30">
                            <div className="flex items-center justify-between text-purple-600 dark:text-purple-400 mb-1.5">
                                <span className="text-[11px] font-medium">{t('token_stats.requests', '请求数')}</span>
                                <TrendingUp className="w-4 h-4 opacity-70" />
                            </div>
                            <div className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-gray-900 dark:text-white">
                                {summary.total_requests.toLocaleString()}
                            </div>
                            <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-1 whitespace-nowrap">
                                {t('user_token.success_rate', '成功率')}: <span className="font-semibold text-emerald-600 dark:text-emerald-400">{successRate}%</span>
                            </div>
                        </div>

                        {/* 平均 Token/请求 */}
                        <div className="bg-gradient-to-br from-emerald-50/50 to-teal-50/30 dark:from-emerald-950/20 dark:to-teal-950/10 p-3.5 rounded-2xl border border-emerald-100/80 dark:border-emerald-900/30">
                            <div className="flex items-center justify-between text-emerald-600 dark:text-emerald-400 mb-1.5">
                                <span className="text-[11px] font-medium">{t('user_token.avg_per_request', '平均单次 Token')}</span>
                                <Activity className="w-4 h-4 opacity-70" />
                            </div>
                            <div className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-gray-900 dark:text-white">
                                {formatTokens(avgTokensPerReq)}
                            </div>
                            <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-1 whitespace-nowrap">
                                {t('user_token.est_throughput', '每请求吞吐估算')}
                            </div>
                        </div>

                        {/* 活跃 IP 绑定 */}
                        <div className="bg-gradient-to-br from-amber-50/50 to-orange-50/30 dark:from-amber-950/20 dark:to-orange-950/10 p-3.5 rounded-2xl border border-amber-100/80 dark:border-amber-900/30">
                            <div className="flex items-center justify-between text-amber-600 dark:text-amber-400 mb-1.5">
                                <span className="text-[11px] font-medium">{t('user_token.bound_ips', '客户端 IP 数')}</span>
                                <Globe className="w-4 h-4 opacity-70" />
                            </div>
                            <div className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-gray-900 dark:text-white">
                                {stats?.recent_ips.length || 0}
                                {token.max_ips > 0 && (
                                    <span className="text-xs font-normal text-gray-400 ml-1">/ {token.max_ips}</span>
                                )}
                            </div>
                            <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-1 whitespace-nowrap">
                                {token.max_ips === 0 ? t('user_token.unlimited', '无限制') : `${token.max_ips} IP`}
                            </div>
                        </div>
                    </div>

                    {/* 图表主区域：走势图 + 模型分布 */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                        {/* 走势折线/面积图 (占 2 栏) */}
                        <div className="lg:col-span-2 bg-gray-50/70 dark:bg-white/[0.02] p-4 rounded-2xl border border-gray-100 dark:border-white/5 flex flex-col min-h-[280px]">
                            <div className="flex items-center justify-between mb-3 shrink-0">
                                <div className="flex items-center gap-2">
                                    <BarChart3 className="w-4 h-4 text-blue-500" />
                                    <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                                        {t('token_stats.usage_trend', 'Token 消耗趋势')}
                                    </h4>
                                </div>
                                <div className="flex items-center gap-3 text-[11px]">
                                    <span className="flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-medium whitespace-nowrap">
                                        <span className="w-2 h-2 rounded-full bg-blue-500" />
                                        {t('token_stats.input_tokens', '输入 Token')}
                                    </span>
                                    <span className="flex items-center gap-1.5 text-purple-600 dark:text-purple-400 font-medium whitespace-nowrap">
                                        <span className="w-2 h-2 rounded-full bg-purple-500" />
                                        {t('token_stats.output_tokens', '输出 Token')}
                                    </span>
                                </div>
                            </div>

                            <div className="flex-1 w-full h-[220px]">
                                {stats && stats.trend.length > 0 ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart
                                            data={stats.trend}
                                            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                                        >
                                            <defs>
                                                <linearGradient id="userTokenInputGrad" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
                                                </linearGradient>
                                                <linearGradient id="userTokenOutputGrad" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" opacity={0.15} vertical={false} />
                                            <XAxis
                                                dataKey="timestamp_label"
                                                tickLine={false}
                                                axisLine={false}
                                                tick={{ fontSize: 10, fill: '#888' }}
                                            />
                                            <YAxis
                                                tickLine={false}
                                                axisLine={false}
                                                tickFormatter={formatTokens}
                                                tick={{ fontSize: 10, fill: '#888' }}
                                            />
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: 'rgba(24, 26, 32, 0.95)',
                                                    borderColor: 'rgba(255, 255, 255, 0.1)',
                                                    borderRadius: '12px',
                                                    fontSize: '11px',
                                                    color: '#fff',
                                                    boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
                                                }}
                                                formatter={(val: any, name: any) => [
                                                    formatTokens(Number(val)),
                                                    name === 'input_tokens' ? t('token_stats.input', '输入') : name === 'output_tokens' ? t('token_stats.output', '输出') : name,
                                                ]}
                                                labelFormatter={(label) => `${t('common.time', '时间')}: ${label}`}
                                            />
                                            <Area
                                                type="monotone"
                                                dataKey="input_tokens"
                                                stroke="#3B82F6"
                                                strokeWidth={2}
                                                fillOpacity={1}
                                                fill="url(#userTokenInputGrad)"
                                            />
                                            <Area
                                                type="monotone"
                                                dataKey="output_tokens"
                                                stroke="#8B5CF6"
                                                strokeWidth={2}
                                                fillOpacity={1}
                                                fill="url(#userTokenOutputGrad)"
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
                                        <Activity className="w-8 h-8 opacity-20" />
                                        <span className="text-xs">
                                            {loading ? t('common.loading', '加载中...') : t('user_token.no_trend_data', '该时段内暂无走势数据')}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* 模型消耗分布 (占 1 栏) */}
                        <div className="bg-gray-50/70 dark:bg-white/[0.02] p-4 rounded-2xl border border-gray-100 dark:border-white/5 flex flex-col min-h-[280px]">
                            <div className="flex items-center gap-2 mb-3 shrink-0">
                                <Cpu className="w-4 h-4 text-purple-500" />
                                <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                                    {t('token_stats.model_share', '模型消耗占比')}
                                </h4>
                            </div>

                            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 scrollbar-thin">
                                {stats && stats.models.length > 0 ? (
                                    stats.models.map((m, idx) => {
                                        const color = MODEL_PALETTE[idx % MODEL_PALETTE.length];
                                        return (
                                            <div key={m.model} className="p-2 rounded-xl bg-white dark:bg-white/5 border border-gray-100 dark:border-white/5">
                                                <div className="flex items-center justify-between text-xs mb-1">
                                                    <span className="font-mono font-medium text-gray-800 dark:text-gray-200 truncate max-w-[140px]" title={m.model}>
                                                        {m.model}
                                                    </span>
                                                    <span className="font-semibold text-gray-900 dark:text-white font-mono text-[11px]">
                                                        {m.percentage}%
                                                    </span>
                                                </div>
                                                {/* 进度条 */}
                                                <div className="w-full bg-gray-100 dark:bg-white/10 h-1.5 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full rounded-full transition-all duration-500"
                                                        style={{ width: `${Math.min(100, m.percentage)}%`, backgroundColor: color }}
                                                    />
                                                </div>
                                                <div className="flex items-center justify-between text-[10px] text-gray-400 mt-1">
                                                    <span>{formatTokens(m.total_tokens)}</span>
                                                    <span>{m.requests} {t('user_token.calls_unit', '次调用')}</span>
                                                </div>
                                            </div>
                                        );
                                    })
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
                                        <Layers className="w-8 h-8 opacity-20" />
                                        <span className="text-xs">
                                            {loading ? t('common.loading', '加载中...') : t('user_token.no_model_data', '暂无模型数据')}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* 活跃 IP 与客户端列表 */}
                    <div className="bg-gray-50/70 dark:bg-white/[0.02] p-4 rounded-2xl border border-gray-100 dark:border-white/5">
                        <div className="flex items-center justify-between mb-2.5">
                            <div className="flex items-center gap-2">
                                <Shield className="w-4 h-4 text-emerald-500" />
                                <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                                    {t('user_token.recent_ips', '活跃客户端 IP 与最近活动')}
                                </h4>
                            </div>
                            <span className="text-[11px] text-gray-400">
                                {stats?.recent_ips.length || 0} {t('user_token.records_unit', '个记录')}
                            </span>
                        </div>

                        {stats && stats.recent_ips.length > 0 ? (
                            <div className="divide-y divide-gray-100 dark:divide-white/5">
                                {stats.recent_ips.map((ip) => (
                                    <div key={ip.ip_address} className="py-2.5 flex items-center justify-between text-xs">
                                        <div className="flex items-center gap-3">
                                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                                            <div>
                                                <div className="font-mono font-medium text-gray-800 dark:text-gray-200">
                                                    {ip.ip_address}
                                                </div>
                                                {ip.user_agent && (
                                                    <div className="text-[10px] text-gray-400 truncate max-w-sm" title={ip.user_agent}>
                                                        {ip.user_agent}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <div className="text-right shrink-0">
                                            <div className="font-semibold text-gray-700 dark:text-gray-300">
                                                {ip.request_count} <span className="text-[10px] font-normal text-gray-400">reqs</span>
                                            </div>
                                            <div className="text-[10px] text-gray-400 mt-0.5">
                                                {formatTime(ip.last_seen_at)}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="py-4 text-center text-xs text-gray-400">
                                {t('user_token.no_ips', '暂无 IP 绑定记录')}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>,
        document.body
    );
};
