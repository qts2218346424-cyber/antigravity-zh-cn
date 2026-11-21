import { Link, useLocation } from 'react-router-dom';
import { NavigationDropdown } from './NavDropdowns';
import { isActive, getCurrentNavItem, type NavItem } from './constants';
import { useConfigStore } from '../../stores/useConfigStore';

interface NavMenuProps {
    navItems: NavItem[];
}

/**
 * 导航菜单组件 - 智能自适应阶梯响应式架构
 *
 * 响应式分级策略:
 * - ≥ 1240px: 舒展全文字胶囊（≥ 1380px 展开前置微图标）
 * - 640px - 1239px: 智能聚焦胶囊（当前选中国民级图文展开，未选中国民级图标 + 悬停 Tooltip，
 *   总宽度控制在 ~400px 内，彻底杜绝 1120px 默认主窗口与 Windows DPI 缩放下的挤压截断问题）
 * - < 640px: 折叠式下拉导航菜单（移动端/超窄视口体验）
 */
export function NavMenu({ navItems }: NavMenuProps) {
    const location = useLocation();
    const { isMenuItemHidden } = useConfigStore();

    // 过滤隐藏的菜单项
    const visibleNavItems = navItems.filter(item => !isMenuItemHidden(item.path));

    return (
        <>
            {/* 舒展全文字胶囊 (≥ 1240px 大屏模式) */}
            <nav
                aria-label="主导航"
                className="hidden min-[1240px]:flex items-center gap-0.5 xl:gap-1 max-w-full min-w-0 bg-gray-100/90 dark:bg-base-200/90 border border-gray-200/60 dark:border-white/5 rounded-full p-1 shadow-xs"
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
                                shrink-0
                                px-2.5 xl:px-3.5
                                py-1.5
                                rounded-full
                                text-xs xl:text-sm
                                font-medium
                                transition-all duration-200
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

            {/* 智能聚焦胶囊 (640px - 1239px，完美适配 1120px 默认窗口与各类 DPI 缩放) */}
            <nav
                aria-label="主导航"
                className="hidden min-[640px]:flex max-[1239px]:flex items-center gap-1 bg-gray-100/90 dark:bg-base-200/90 border border-gray-200/60 dark:border-white/5 rounded-full p-1 shadow-xs"
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
                            title={item.label}
                            className={`
                                shrink-0
                                rounded-full
                                transition-all duration-200
                                inline-flex items-center gap-1.5
                                ${active
                                    ? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900 px-3 py-1.5 text-xs font-medium'
                                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/80 dark:text-gray-400 dark:hover:text-base-content dark:hover:bg-base-100 p-2'
                                }
                            `}
                        >
                            <item.icon className="w-4 h-4 shrink-0" />
                            {active && (
                                <span className="whitespace-nowrap tracking-wide">{item.label}</span>
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* 折叠下拉菜单 (380px - 639px 显示带文字模块名) */}
            <div className="max-[379px]:hidden min-[640px]:hidden block">
                <NavigationDropdown
                    navItems={visibleNavItems}
                    isActive={(path) => isActive(location.pathname, path)}
                    getCurrentNavItem={() => getCurrentNavItem(location.pathname, visibleNavItems)}
                    onNavigate={() => { }}
                    showLabel={true}
                />
            </div>

            {/* 超窄屏下拉菜单 (< 380px 仅图标) */}
            <div className="min-[380px]:hidden block">
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
