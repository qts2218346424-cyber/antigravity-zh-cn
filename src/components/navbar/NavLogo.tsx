import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LogoIcon from '../../../src-tauri/icons/icon.png';

export function NavLogo() {
  const { t } = useTranslation();

  return (
    <Link
      to="/"
      draggable="false"
      className="flex items-center gap-2.5 text-base sm:text-lg font-bold tracking-tight text-gray-900 dark:text-base-content select-none shrink-0"
    >
      <div className="relative flex items-center justify-center shrink-0">
        <img
          src={LogoIcon}
          alt="Antigravity Studio"
          className="w-7 h-7 sm:w-8 sm:h-8 cursor-pointer active:scale-95 transition-transform relative z-10 rounded-md"
          draggable="false"
        />
      </div>

      <span className="hidden sm:inline whitespace-nowrap">
        {t('common.app_name', 'Antigravity Studio')}
      </span>
    </Link>
  );
}
