import { useEffect, useState } from 'react';
import { LayoutDashboard, Users, Network, Activity, BarChart3, Settings, Lock, Sparkles, KeyRound } from 'lucide-react';
import { listen } from '@tauri-apps/api/event';
import { useTranslation } from 'react-i18next';
import { useConfigStore } from '../../stores/useConfigStore';
import { isTauri, isLinux } from '../../utils/env';
import { studioService } from '../../services/studioService';
import { NavLogo } from './NavLogo';
import { NavMenu } from './NavMenu';
import { NavSettings } from './NavSettings';
import type { NavItem } from './constants';

/**
 * Navbar 主组件
 *
 * 职责: 全局布局、真实明暗主题同步与灵动伴侣快捷开关状态管理
 */
function Navbar() {
    const { t } = useTranslation();
    const { config, updateLanguage, updateTheme } = useConfigStore();
    const [systemDark, setSystemDark] = useState<boolean>(() => {
        if (typeof window === 'undefined' || !window.matchMedia) return false;
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });
    const [petOpen, setPetOpen] = useState<boolean>(false);

    // 监听操作系统级深浅主题变化，确保 config.theme === 'system' 时图标与实际界面一致
    useEffect(() => {
        if (typeof window === 'undefined' || !window.matchMedia) return;
        const mql = window.matchMedia('(prefers-color-scheme: dark)');
        const onChange = (e: MediaQueryListEvent) => setSystemDark(e.matches);
        mql.addEventListener('change', onChange);
        return () => mql.removeEventListener('change', onChange);
    }, []);

    // 同步灵动桌面伴侣窗口状态（兼容 Tauri 跨窗口广播与浏览器预览事件）
    useEffect(() => {
        let disposed = false;
        studioService
            .getStatus()
            .then((status) => {
                if (!disposed) setPetOpen(Boolean(status.pet_window_open));
            })
            .catch(() => {});

        const handleBrowserEvent = (ev: Event) => {
            const detail = (ev as CustomEvent<{ open?: boolean }>).detail;
            if (detail && typeof detail.open === 'boolean') {
                setPetOpen(detail.open);
            }
        };
        window.addEventListener('studio:pet-state-changed', handleBrowserEvent);

        let unlistenTauri: (() => void) | undefined;
        if (isTauri()) {
            listen<{ open?: boolean }>('studio:pet-state-changed', (event) => {
                if (!disposed && event.payload && typeof event.payload.open === 'boolean') {
                    setPetOpen(event.payload.open);
                }
            })
                .then((fn) => {
                    if (disposed) fn();
                    else unlistenTauri = fn;
                })
                .catch(() => {});
        }

        return () => {
            disposed = true;
            window.removeEventListener('studio:pet-state-changed', handleBrowserEvent);
            unlistenTauri?.();
        };
    }, []);

    const effectiveTheme: 'light' | 'dark' =
        config?.theme === 'dark'
            ? 'dark'
            : config?.theme === 'light'
                ? 'light'
                : systemDark || (typeof document !== 'undefined' && document.documentElement.classList.contains('dark'))
                    ? 'dark'
                    : 'light';

    // 创建导航项(包含翻译后的标签，使用区分度清晰的专属图标)
    const navItems: NavItem[] = [
        { path: '/', label: t('nav.dashboard'), icon: LayoutDashboard, priority: 'high' },
        { path: '/accounts', label: t('nav.accounts'), icon: Users, priority: 'high' },
        { path: '/api-proxy', label: t('nav.proxy'), icon: Network, priority: 'high' },
        { path: '/monitor', label: t('nav.call_records'), icon: Activity, priority: 'medium' },
        { path: '/token-stats', label: t('nav.token_stats', 'Token 统计'), icon: BarChart3, priority: 'low' },
        { path: '/user-token', label: t('nav.user_token', '访问令牌'), icon: KeyRound, priority: 'low' },
        { path: '/security', label: t('nav.security'), icon: Lock, priority: 'low' },
        { path: '/studio', label: t('nav.studio', '汉化与美化'), icon: Sparkles, priority: 'high' },
        { path: '/settings', label: t('nav.settings'), icon: Settings, priority: 'high' },
    ];

    // 主题切换逻辑(带 View Transition 圆形扩散动画，正确支持从 system 模式一键切换)
    const toggleTheme = async (event: React.MouseEvent<HTMLButtonElement>) => {
        if (!config) return;

        const newTheme: 'light' | 'dark' = effectiveTheme === 'light' ? 'dark' : 'light';

        if ('startViewTransition' in document && !isLinux()) {
            const x = event.clientX;
            const y = event.clientY;
            const endRadius = Math.hypot(
                Math.max(x, window.innerWidth - x),
                Math.max(y, window.innerHeight - y)
            );

            // @ts-ignore
            const transition = document.startViewTransition(async () => {
                await updateTheme(newTheme);
            });

            transition.ready.then(() => {
                const isDarkMode = newTheme === 'dark';
                const clipPath = isDarkMode
                    ? [`circle(${endRadius}px at ${x}px ${y}px)`, `circle(0px at ${x}px ${y}px)`]
                    : [`circle(0px at ${x}px ${y}px)`, `circle(${endRadius}px at ${x}px ${y}px)`];

                document.documentElement.animate(
                    {
                        clipPath: clipPath
                    },
                    {
                        duration: 500,
                        easing: 'ease-in-out',
                        fill: 'forwards',
                        pseudoElement: isDarkMode ? '::view-transition-old(root)' : '::view-transition-new(root)'
                    }
                );
            });
        } else {
            await updateTheme(newTheme);
        }
    };

    const handleTogglePet = async () => {
        try {
            if (petOpen) {
                await studioService.closePet();
                setPetOpen(false);
            } else {
                await studioService.launchPet();
                setPetOpen(true);
            }
        } catch (err) {
            console.error('切换灵动桌面伴侣状态失败:', err);
        }
    };

    // 语言切换逻辑 (即时乐观更新 + 串行尾随持久化)
    const handleLanguageChange = (langCode: string) => {
        updateLanguage(langCode).catch(err => {
            console.error('Failed to update language:', err);
        });
    };

    return (
        <header
            style={{ position: 'sticky', top: 0, zIndex: 40 }}
            className={`${isTauri() ? 'pt-9' : 'pt-2'} transition-all duration-200 bg-[#FAFBFC]/95 dark:bg-base-300/95 backdrop-blur-md border-b border-gray-200/50 dark:border-white/5`}
        >
            {/* 窗口拖拽区域 - Tauri 专用 */}
            {isTauri() && (
                <div
                    className="absolute top-9 left-0 right-0 h-16"
                    style={{ zIndex: 5, backgroundColor: 'rgba(0,0,0,0.001)' }}
                    data-tauri-drag-region
                />
            )}

            <div className="w-full px-4 sm:px-6 xl:px-8 relative" style={{ zIndex: 10 }}>
                <div className="flex items-center justify-between h-16 gap-2 sm:gap-4">
                    {/* Logo - 稳固呈现，绝不压缩隐匿 */}
                    <div className="shrink-0 flex items-center">
                        <NavLogo />
                    </div>

                    {/* 导航菜单 - 智能响应式自适应居中 */}
                    <div className="flex-1 flex justify-center min-w-0 px-1 sm:px-2">
                        <NavMenu navItems={navItems} />
                    </div>

                    {/* 快捷开关与设置按钮 */}
                    <div className="shrink-0 flex items-center">
                        <NavSettings
                            theme={effectiveTheme}
                            currentLanguage={config?.language || 'zh'}
                            petOpen={petOpen}
                            onTogglePet={handleTogglePet}
                            onThemeToggle={toggleTheme}
                            onLanguageChange={handleLanguageChange}
                        />
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Navbar;
