import { Zap, Check, Sparkles, Bot } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ClassicAutoSwitchConfig } from '../../types/config';

interface ClassicAutoSwitchProps {
    config?: ClassicAutoSwitchConfig;
    onChange: (config: ClassicAutoSwitchConfig) => void;
}

const DEFAULT_CONFIG: ClassicAutoSwitchConfig = {
    enabled: false,
    threshold_percentage: 0,
    monitored_models: ['gemini', 'claude'],
};

const ClassicAutoSwitch = ({ config = DEFAULT_CONFIG, onChange }: ClassicAutoSwitchProps) => {
    const { t } = useTranslation();

    const currentModels = config.monitored_models && config.monitored_models.length > 0
        ? config.monitored_models
        : DEFAULT_CONFIG.monitored_models;

    // 兼容历史具体模型名称，平滑收敛为两类算力池
    const isGeminiSelected = currentModels.some(
        (m) => m === 'gemini' || m.includes('gemini') || m.includes('flash') || m.includes('pro')
    );
    const isClaudeSelected = currentModels.some(
        (m) => m === 'claude' || m === 'third_party' || m.includes('claude') || m.includes('gpt')
    );

    const handleEnabledChange = (enabled: boolean) => {
        const newModels: string[] = [];
        if (isGeminiSelected) newModels.push('gemini');
        if (isClaudeSelected) newModels.push('claude');
        if (newModels.length === 0) {
            newModels.push('gemini', 'claude');
        }

        onChange({
            ...config,
            enabled,
            monitored_models: newModels,
        });
    };

    const handlePercentageChange = (value: string) => {
        const percentage = parseInt(value);
        const clamped = isNaN(percentage) ? 0 : Math.max(0, Math.min(99, percentage));
        onChange({ ...config, threshold_percentage: clamped });
    };

    const toggleCategory = (categoryId: 'gemini' | 'claude') => {
        let newGemini = isGeminiSelected;
        let newClaude = isClaudeSelected;

        if (categoryId === 'gemini') {
            if (isGeminiSelected && isClaudeSelected) {
                newGemini = false;
            } else if (!isGeminiSelected) {
                newGemini = true;
            }
        } else {
            if (isClaudeSelected && isGeminiSelected) {
                newClaude = false;
            } else if (!isClaudeSelected) {
                newClaude = true;
            }
        }

        const newModels: string[] = [];
        if (newGemini) newModels.push('gemini');
        if (newClaude) newModels.push('claude');
        if (newModels.length === 0) return; // 至少保留一个监控池

        onChange({ ...config, monitored_models: newModels });
    };

    const categoryOptions = [
        {
            id: 'gemini' as const,
            isSelected: isGeminiSelected,
            label: t('settings.account.auto_switch_gemini', 'Gemini 算力池'),
            desc: t('settings.account.auto_switch_gemini_desc', '包含 Pro / Flash / 绘图'),
            icon: Sparkles,
        },
        {
            id: 'claude' as const,
            isSelected: isClaudeSelected,
            label: t('settings.account.auto_switch_third_party', '第三方模型池'),
            desc: t('settings.account.auto_switch_third_party_desc', '包含 Claude 3.7 / 3.5 / GPT'),
            icon: Bot,
        },
    ];

    return (
        <div className="animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-violet-50 dark:bg-violet-900/20 flex items-center justify-center text-violet-500 group-hover:bg-violet-500 group-hover:text-white transition-all duration-300">
                        <Zap size={20} />
                    </div>
                    <div>
                        <div className="font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                            <span>{t('settings.account.auto_switch_classic')}</span>
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-violet-100 dark:bg-violet-900/40 text-violet-600 dark:text-violet-300">
                                {t('settings.account.auto_switch_classic_badge', '仅限经典款')}
                            </span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {t('settings.account.auto_switch_classic_desc')}
                        </p>
                    </div>
                </div>

                <label className="relative inline-flex items-center cursor-pointer">
                    <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={config.enabled}
                        onChange={(e) => handleEnabledChange(e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-gray-200 dark:bg-base-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-500 shadow-inner"></div>
                </label>
            </div>

            {config.enabled && (
                <div className="mt-5 pt-5 border-t border-gray-100 dark:border-base-200 space-y-6 animate-in slide-in-from-top-1 duration-200">
                    {/* 百分比阈值设置 */}
                    <div className="flex items-center gap-4">
                        <label className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            {t('settings.account.auto_switch_threshold_label')}
                        </label>
                        <div className="relative flex items-center gap-2">
                            <input
                                type="number"
                                className="w-24 px-3 py-2 bg-gray-50 dark:bg-base-200 border border-gray-100 dark:border-base-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm font-bold text-violet-600 dark:text-violet-400"
                                min="0"
                                max="99"
                                value={config.threshold_percentage}
                                onChange={(e) => handlePercentageChange(e.target.value)}
                            />
                            <span className="text-sm font-bold text-gray-400">%</span>
                        </div>
                        <span className="text-xs text-gray-400">
                            {t('settings.account.auto_switch_threshold_hint', {
                                pct: config.threshold_percentage,
                            })}
                        </span>
                    </div>

                    {/* 监控额度池选择：仅保留 Gemini 和 第三方模型 两个核心算力池 */}
                    <div>
                        <div className="flex items-center justify-between mb-3">
                            <label className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                {t('settings.account.auto_switch_models_label')}
                            </label>
                            <span className="text-xs text-gray-400">
                                {t('settings.account.auto_switch_models_hint')}
                            </span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {categoryOptions.map((opt) => {
                                const Icon = opt.icon;
                                return (
                                    <button
                                        key={opt.id}
                                        type="button"
                                        onClick={() => toggleCategory(opt.id)}
                                        className={`p-3.5 rounded-xl border text-left transition-all duration-200 cursor-pointer flex items-start gap-3 ${
                                            opt.isSelected
                                                ? 'bg-violet-50/70 dark:bg-violet-950/30 border-violet-200 dark:border-violet-700/60 shadow-xs'
                                                : 'bg-gray-50/60 dark:bg-base-200/50 border-gray-100 dark:border-base-300 hover:border-gray-200 opacity-60'
                                        }`}
                                    >
                                        <div
                                            className={`mt-0.5 p-1.5 rounded-lg transition-colors ${
                                                opt.isSelected
                                                    ? 'bg-violet-600 text-white'
                                                    : 'bg-gray-200 dark:bg-base-300 text-gray-500'
                                            }`}
                                        >
                                            {opt.isSelected ? (
                                                <Check size={14} className="stroke-[3]" />
                                            ) : (
                                                <Icon size={14} />
                                            )}
                                        </div>
                                        <div>
                                            <div className="text-xs font-bold text-gray-900 dark:text-gray-100 flex items-center gap-1.5">
                                                {opt.label}
                                            </div>
                                            <div className="text-[11px] text-gray-400 dark:text-gray-400 mt-0.5">
                                                {opt.desc}
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ClassicAutoSwitch;
