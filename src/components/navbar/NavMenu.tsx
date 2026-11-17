import { Link, useLocation } from 'react-router-dom';
import { NavigationDropdown } from './NavDropdowns';
import { isActive, getCurrentNavItem, type NavItem } from './constants';
import { useConfigStore } from '../../stores/useConfigStore';

interface NavMenuProps {
    navItems: NavItem[];
}

/**
 * 导航菜单组件 - 精简响应式层级（零重复 DOM）
 *
 * 响应式策略:
 * - ≥ 1080px: 紧凑文字胶囊（适配 1120px 默认窗口宽度；≥ 1380px 自动展示前置微图标）
 * - 480px - 1079px: 单套图标胶囊（悬停展示完整模块名）
 * - < 480px: 折叠下拉导航菜单（≥ 375px 展示当前模块名）
 */
export function NavMenu({ navItems }: NavMenuProps) {
    const location = useLocation();
    const { isMenuItemHidden } = useConfigStore();

    // 过滤隐藏的菜单项
    const visibleNavItems = navItems.filter(item => !isMenuItemHidden(item.path));

    return (
        <>
            {/* 紧凑图文胶囊 (≥ 1080px，完美兼容 1120px 默认主窗口) */}
            <nav
                aria-label="主导航"
                className="max-[1079px]:hidden flex items-center gap-0.5 xl:gap-1 bg-gray-100/90 dark:bg-base-200/90 border border-gray-200/60 dark:border-white/5 rounded-full p-1 shadow-xs"
            >
                {visibleNavItems.map((item) => {
                    const active = isActive(location.pathname, item.path);
                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            draggable="false"
                            aria-current={active ? 'page' : undefined}
                            className={`
                                px-2.5 xl:px-3.5
                                py-1.5
                                rounded-full
                                text-xs xl:text-sm
                                font-medium
                                transition-all
                                whitespace-nowrap
                                inline-flex
                                items-center
                                gap-1.5
                                ${active
                                    ? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900'
                                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-200/80 dark:text-gray-400 dark:hover:text-base-content dark:hover:bg-base-100'
                                }
                            `}
                        >
                            <item.icon className="hidden min-[1380px]:block w-3.5 h-3.5 shrink-0" />
                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* 图标胶囊 (480px - 1079px，合并消除原先 3 套重复 DOM) */}
            <nav
                aria-label="主导航"
                className="max-[479px]:hidden min-[1080px]:hidden flex items-center gap-1 bg-gray-100/90 dark:bg-base-200/90 border border-gray-200/60 dark:border-white/5 rounded-full p-1"
            >
                {visibleNavItems.map((item) => {
                    const active = isActive(location.pathname, item.path);
                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            draggable="false"
                            aria-current={active ? 'page' : undefined}
                            aria-label={item.label}
                            className={`
                                p-2
                                rounded-full
                                transition-all
                                ${active
                                    ? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900'
                                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-200 dark:text-gray-400 dark:hover:text-base-content dark:hover:bg-base-100'
                                }
                            `}
                            title={item.label}
                        >
                            <item.icon className="w-4 h-4 sm:w-5 sm:h-5" />
                        </Link>
                    );
                })}
            </nav>

            {/* 折叠下拉菜单 (< 480px) */}
            <div className="max-[374px]:hidden min-[480px]:hidden block">
                <NavigationDropdown
                    navItems={visibleNavItems}
                    isActive={(path) => isActive(location.pathname, path)}
                    getCurrentNavItem={() => getCurrentNavItem(location.pathname, visibleNavItems)}
                    onNavigate={() => { }}
                    showLabel={true}
                />
            </div>

            <div className="min-[375px]:hidden">
                <NavigationDropdown
                    navItems={visibleNavItems}
                    isActive={(path) => isActive(location.pathname, path)}
                    getCurrentNavItem={() => getCurrentNavItem(location.pathname, visibleNavItems)}
                    onNavigate={() => { }}
                    showLabel={false}
                />
            </div>
        </>
    );
}
