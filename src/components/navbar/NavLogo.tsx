import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LogoIcon from '../../../src-tauri/icons/icon.png';

export function NavLogo() {
  const { t } = useTranslation();

  return (
    <Link
      to="/"
      draggable="false"
      className="flex w-full min-w-0 items-center gap-2 text-lg font-bold tracking-tight text-gray-900 dark:text-base-content"
    >
      <div className="relative flex items-center justify-center shrink-0">
        <img
          src={LogoIcon}
          alt="Antigravity Studio"
          className="w-8 h-8 cursor-pointer active:scale-95 transition-transform relative z-10"
          draggable="false"
        />
      </div>

      <span className="hidden @[176px]/logo:inline text-nowrap truncate">
        {t('common.app_name', 'Antigravity Studio')}
      </span>
    </Link>
  );
}
