import { Link, useLocation } from 'react-router-dom';
import { NavigationDropdown } from './NavDropdowns';
import { isActive, getCurrentNavItem, type NavItem } from './constants';
import { useConfigStore } from '../../stores/useConfigStore';

interface NavMenuProps {
    navItems: NavItem[];
}

/**
 * 导航菜单组件 - 单套自适应流式响应式架构
 *
 * 核心策略:
 * - 彻底避免双 <nav> 媒体查询冲突导致的全屏并发渲染与挤占问题
 * - ≥ 768px: 桌面端单套弹性自适应胶囊 (当前激活项图文完整高亮展开；
 *   在 ≥ 1400px 全屏超宽视口平滑舒展为全文字，在 768px - 1399px 自动收拢非激活项为精致图标 + 悬停 Tooltip，
 *   总宽控制在 ~400px，两端保留超大呼吸缓冲空间，彻底告别挤占与截断)
 * - < 768px: 自动平滑折叠为下拉导航菜单 (窗口紧凑或应用大比例缩放时的安全兜底，100% 保证所有项完整可见)
 */
export function NavMenu({ navItems }: NavMenuProps) {
    const location = useLocation();
    const { isMenuItemHidden } = useConfigStore();

    // 过滤隐藏的菜单项
    const visibleNavItems = navItems.filter(item => !isMenuItemHidden(item.path));

    return (
        <>
            {/* 桌面端单套自适应主导航 (≥ 768px) */}
            <nav
                aria-label="主导航"
                className="hidden min-[768px]:flex items-center gap-1 bg-gray-100/90 dark:bg-base-200/90 border border-gray-200/60 dark:border-white/5 rounded-full p-1 shadow-xs max-w-full"
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
                                    ? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900 px-3.5 py-1.5 text-xs font-medium'
                                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-200/80 dark:text-gray-400 dark:hover:text-base-content dark:hover:bg-base-100 p-2 min-[1400px]:px-3 min-[1400px]:py-1.5 text-xs'
                                }
                            `}
                        >
                            <item.icon className="w-4 h-4 shrink-0" />
                            {/* 激活项始终显示文字；非激活项在 ≥ 1400px 超宽屏全屏时自适应展开文字 */}
                            <span className={`whitespace-nowrap ${active ? 'inline' : 'hidden min-[1400px]:inline'}`}>
                                {item.label}
                            </span>
                        </Link>
                    );
                })}
            </nav>

            {/* 紧凑视口折叠下拉导航 (< 768px，在窗口缩窄或大比例缩放时完美兜底) */}
            <div className="min-[768px]:hidden block">
                <NavigationDropdown
                    navItems={visibleNavItems}
                    isActive={(path) => isActive(location.pathname, path)}
                    getCurrentNavItem={() => getCurrentNavItem(location.pathname, visibleNavItems)}
                    onNavigate={() => { }}
                    showLabel={true}
                />
            </div>
        </>
    );
}
