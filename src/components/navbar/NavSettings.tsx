import { Sun, Moon, LogOut, Minimize2, Cat } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { LanguageDropdown, MoreDropdown } from './NavDropdowns';
import { LANGUAGES } from './constants';
import { isTauri } from '../../utils/env';
import { invoke } from '@tauri-apps/api/core';
import { useViewStore } from '../../stores/useViewStore';

interface NavSettingsProps {
    theme: 'light' | 'dark';
    currentLanguage: string;
    petOpen?: boolean;
    onTogglePet?: () => void;
    onThemeToggle: (event: React.MouseEvent<HTMLButtonElement>) => void;
    onLanguageChange: (langCode: string) => void;
}

/**
 * 设置按钮组件 - 独立处理响应式
 *
 * 响应式策略:
 * - ≥ 480px: 独立快捷按钮（灵动伴侣 + 迷你视图 + 主题 + 语言）
 * - < 480px: 更多下拉菜单
 */
export function NavSettings({
    theme,
    currentLanguage,
    petOpen = false,
    onTogglePet,
    onThemeToggle,
    onLanguageChange
}: NavSettingsProps) {
    const { t } = useTranslation();
    const { setMiniView } = useViewStore();

    const handleLogout = () => {
        sessionStorage.removeItem('abv_admin_api_key');
        localStorage.removeItem('abv_admin_api_key');
        window.location.reload();
    };

    const petLabel = petOpen
        ? t('nav.pet_close', '关闭灵动桌面伴侣')
        : t('nav.pet_open', '呼出灵动桌面伴侣');

    return (
        <>
            {/* 独立按钮 (≥ 480px) */}
            <div className="hidden min-[480px]:flex items-center gap-1.5 xl:gap-2">
                {/* 灵动桌面伴侣一键开关 */}
                {onTogglePet && (
                    <button
                        type="button"
                        onClick={onTogglePet}
                        aria-pressed={petOpen}
                        aria-label={petLabel}
                        title={petLabel}
                        className={`relative w-9 h-9 xl:w-10 xl:h-10 rounded-full flex items-center justify-center transition-all ${
                            petOpen
                                ? 'bg-pink-50 text-pink-600 ring-1 ring-pink-200 hover:bg-pink-100 dark:bg-pink-500/15 dark:text-pink-300 dark:ring-pink-400/30 dark:hover:bg-pink-500/25'
                                : 'bg-gray-100 dark:bg-base-200 hover:bg-gray-200 dark:hover:bg-base-100 text-gray-700 dark:text-gray-300'
                        }`}
                    >
                        <Cat className="w-4 h-4 xl:w-5 xl:h-5" />
                        {petOpen && (
                            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-base-300" />
                        )}
                    </button>
                )}

                {/* 迷你视图切换按钮 */}
                <button
                    type="button"
                    onClick={() => {
                        if (isTauri()) {
                            invoke('show_mini_view').catch(() => {});
                        } else {
                            setMiniView(true);
                        }
                    }}
                    className="w-9 h-9 xl:w-10 xl:h-10 rounded-full bg-gray-100 dark:bg-base-200 hover:bg-gray-200 dark:hover:bg-base-100 flex items-center justify-center transition-colors"
                    title={t('nav.mini_view', '迷你悬浮窗')}
                    aria-label={t('nav.mini_view', '迷你悬浮窗')}
                >
                    <Minimize2 className="w-4 h-4 xl:w-5 xl:h-5 text-gray-700 dark:text-gray-300" />
                </button>

                {/* 主题切换按钮 */}
                <button
                    type="button"
                    onClick={onThemeToggle}
                    className="w-9 h-9 xl:w-10 xl:h-10 rounded-full bg-gray-100 dark:bg-base-200 hover:bg-gray-200 dark:hover:bg-base-100 flex items-center justify-center transition-colors"
                    title={theme === 'light' ? t('nav.theme_to_dark') : t('nav.theme_to_light')}
                    aria-label={theme === 'light' ? t('nav.theme_to_dark') : t('nav.theme_to_light')}
                >
                    {theme === 'light' ? (
                        <Moon className="w-4 h-4 xl:w-5 xl:h-5 text-gray-700 dark:text-gray-300" />
                    ) : (
                        <Sun className="w-4 h-4 xl:w-5 xl:h-5 text-gray-700 dark:text-gray-300" />
                    )}
                </button>

                {/* 语言切换下拉菜单 */}
                <LanguageDropdown
                    currentLanguage={currentLanguage}
                    languages={LANGUAGES}
                    onLanguageChange={onLanguageChange}
                />

                {/* 登出按钮 - 仅 Web 模式显示 */}
                {!isTauri() && (
                    <button
                        type="button"
                        onClick={handleLogout}
                        className="w-9 h-9 xl:w-10 xl:h-10 rounded-full bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 flex items-center justify-center transition-colors"
                        title={t('nav.logout', '退出登录')}
                        aria-label={t('nav.logout', '退出登录')}
                    >
                        <LogOut className="w-4 h-4 xl:w-5 xl:h-5 text-red-600 dark:text-red-400" />
                    </button>
                )}
            </div>

            {/* 更多菜单 (< 480px) */}
            <div className="min-[480px]:hidden">
                <MoreDropdown
                    theme={theme}
                    currentLanguage={currentLanguage}
                    languages={LANGUAGES}
                    petOpen={petOpen}
                    onTogglePet={onTogglePet}
                    onThemeToggle={onThemeToggle}
                    onLanguageChange={onLanguageChange}
                />
            </div>
        </>
    );
}
