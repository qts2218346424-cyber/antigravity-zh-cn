import { invoke } from '@tauri-apps/api/core';
import { isTauri } from '../utils/env';
import type {
  CompiledSkin,
  L10nPatchResult,
  MediaStatus,
  PetAssets,
  ReapplyCheckResult,
  SkillLocalizeResult,
  SkinInfo,
  SkinManifest,
  StudioStatus,
} from '../types/studio';

const PREVIEW_SKINS: SkinInfo[] = [
  {
    id: 'obsidian-glass',
    name: '黑曜石 · 液态光学',
    version: '2.0.0',
    author: 'Antigravity Studio',
    description: '深邃黑曜石基底搭配 20px 液态亚克力模糊、微距钛银折射边框与冰川蓝信号光束。',
    base: 'dark',
    path: 'resources/skins/obsidian-glass',
    builtin: true,
    colors: {
      background: '#080a0f',
      foreground: '#e6edf7',
      accent: '#38bdf8',
      sidebar: '#0c1018',
      activityBar: '#06080c',
      titleBar: '#07090e',
      statusBar: '#0e1726',
      panel: '#0f141f',
      border: '#1f293b',
      input: '#131a27',
      muted: '#7e8ca6',
    },
    active: true,
  },
  {
    id: 'vermilion-lacquer',
    name: '朱漆 · 黑金莳绘',
    version: '2.0.0',
    author: 'Antigravity Studio',
    description: '中国传统大漆与宋刻美学：碳墨漆黑底、故宫朱砂红与赤金流光边框。',
    base: 'dark',
    path: 'resources/skins/vermilion-lacquer',
    builtin: true,
    colors: {
      background: '#110c0d',
      foreground: '#f5ebe4',
      accent: '#e15b47',
      sidebar: '#160f11',
      activityBar: '#0d090a',
      titleBar: '#0e0a0b',
      statusBar: '#3b1715',
      panel: '#1a1214',
      border: '#362320',
      input: '#211719',
      muted: '#a88f88',
    },
    active: false,
  },
  {
    id: 'nordic-aurora',
    name: '北境极光 · 冰川矿',
    version: '2.0.0',
    author: 'Antigravity Studio',
    description: '斯堪的纳维亚低饱和护眼视觉方案：冷杉深潭岩灰底色辅以极光青翠高亮。',
    base: 'dark',
    path: 'resources/skins/nordic-aurora',
    builtin: true,
    colors: {
      background: '#0b1417',
      foreground: '#dbe8eb',
      accent: '#2dd4bf',
      sidebar: '#0e1a1e',
      activityBar: '#081013',
      titleBar: '#091114',
      statusBar: '#112b30',
      panel: '#111f24',
      border: '#1e333a',
      input: '#14262c',
      muted: '#7b9ba3',
    },
    active: false,
  },
  {
    id: 'nezuko-bamboo',
    name: '祢豆子 · 竹筒与麻叶',
    version: '1.0.0',
    author: 'antigravity-zh-cn',
    description: '以祢豆子和服麻叶纹与粉墨配色为灵感的暗色主题，桌宠默认联动灶门祢豆子。',
    base: 'dark',
    path: 'resources/skins/nezuko-bamboo',
    builtin: true,
    colors: {
      background: '#1a0e14',
      foreground: '#f6e3ea',
      accent: '#f06292',
      sidebar: '#24111b',
      input: '#2a1520',
      muted: '#b98aa0',
      border: '#4a1f33',
    },
    active: false,
  },
  {
    id: 'midnight-dark',
    name: '午夜深空 · 暗色',
    version: '1.0.0',
    author: 'antigravity-zh-cn',
    description: '低饱和深蓝星空夜色主题，适合长时间夜间沉浸式编程，联动 B612 小王子。',
    base: 'dark',
    path: 'resources/skins/midnight-dark',
    builtin: true,
    colors: {
      background: '#0d1220',
      foreground: '#d5dcef',
      accent: '#5cc8ff',
      sidebar: '#0a0f1b',
      statusBar: '#0f2a44',
      border: '#1b2540',
    },
    active: false,
  },
  {
    id: 'sakura-light',
    name: '樱花 · 浅色',
    version: '1.0.0',
    author: 'antigravity-zh-cn',
    description: '柔和温暖的樱花粉浅色风格，自带樱花图标映射与圆润滚动条微调。',
    base: 'light',
    path: 'resources/skins/sakura-light',
    builtin: true,
    colors: {
      background: '#fff8fb',
      foreground: '#3b2a33',
      accent: '#e86a92',
      sidebar: '#fdeef3',
      statusBar: '#e86a92',
      border: '#f3c6d6',
    },
    active: false,
  },
];

const PREVIEW_STATUS: StudioStatus = {
  install_dir: 'C:\\Users\\Demo\\AppData\\Local\\Programs\\Antigravity',
  ide_root: 'C:\\Users\\Demo\\AppData\\Local\\Programs\\Antigravity\\resources\\app',
  agent_status: 'clean',
  ide_status: 'clean',
  active_skin: 'obsidian-glass',
  skin_enabled: false,
  ide_enabled: false,
  auto_reapply: true,
  autostart_enabled: false,
  updates_disabled: false,
  splash_character: 'nezuko',
  lang: 'zh-cn',
  enable_pet: true,
  enable_skin: true,
  pet_window_open: false,
  config_dir: '%APPDATA%\\antigravity-zh-cn',
  resource_dir: 'resources',
  reapply_logs: ['[浏览器预览模式] 完整文件修补与桌宠控制请在 Tauri 桌面客户端中运行'],
};

async function callStudio<T>(cmd: string, args: Record<string, unknown> = {}, fallback?: () => T): Promise<T> {
  if (!isTauri()) {
    if (fallback) return fallback();
    throw new Error(`当前处于纯浏览器预览模式，无法调用系统命令 ${cmd}`);
  }
  return invoke<T>(cmd, args);
}

export const studioService = {
  getStatus: () => callStudio<StudioStatus>('studio_get_status', {}, () => PREVIEW_STATUS),

  updatePaths: (installDir?: string | null, ideDir?: string | null) =>
    callStudio<StudioStatus>(
      'studio_update_paths',
      { installDir: installDir ?? null, ideDir: ideDir ?? null },
      () => ({ ...PREVIEW_STATUS, install_dir: installDir ?? null, ide_root: ideDir ?? null }),
    ),

  applyL10n: (params: {
    install_dir?: string | null;
    lang: string;
    character: string;
    enable_pet: boolean;
    enable_skin: boolean;
  }) =>
    callStudio<L10nPatchResult>('studio_apply_l10n', {
      installDir: params.install_dir ?? null,
      lang: params.lang,
      character: params.character,
      enablePet: params.enable_pet,
      enableSkin: params.enable_skin,
    }),

  restoreL10n: (installDir?: string | null) =>
    callStudio<string>('studio_restore_l10n', { installDir: installDir ?? null }),

  toggleUpdates: (installDir: string | null | undefined, disable: boolean) =>
    callStudio<boolean>('studio_toggle_updates', {
      installDir: installDir ?? null,
      disable,
    }),

  localizeSkills: () => callStudio<SkillLocalizeResult>('studio_localize_skills'),

  ensureProtocol: () => callStudio<boolean>('studio_ensure_protocol'),

  listSkins: () => callStudio<SkinInfo[]>('studio_list_skins', {}, () => PREVIEW_SKINS),

  getSkinManifest: (skinId: string) =>
    callStudio<SkinManifest>(
      'studio_get_skin_manifest',
      { skinId },
      () => {
        const hit = PREVIEW_SKINS.find((s) => s.id === skinId) || PREVIEW_SKINS[0];
        return {
          schema: 1,
          id: hit.id,
          name: hit.name,
          author: hit.author,
          version: hit.version,
          description: hit.description,
          base: hit.base,
          colors: hit.colors,
        };
      },
    ),

  activateSkin: (skinId: string) =>
    callStudio<CompiledSkin>('studio_activate_skin', { skinId }),

  disableSkin: () => callStudio<void>('studio_disable_skin'),

  saveOverride: (scope: 'global' | 'skin', skinId: string | null, patch: Record<string, unknown>) =>
    callStudio<void>('studio_save_override', { scope, skinId, patch }),

  resetOverride: (scope: 'global' | 'skin', skinId: string | null) =>
    callStudio<void>('studio_reset_override', { scope, skinId }),

  duplicateSkin: (sourceId: string, newId: string, newName: string) =>
    callStudio<SkinInfo>('studio_duplicate_skin', { sourceId, newId, newName }),

  deleteSkin: (skinId: string) => callStudio<void>('studio_delete_skin', { skinId }),

  importSkinZip: (zipPath: string, overwrite: boolean) =>
    callStudio<SkinInfo>('studio_import_skin_zip', { zipPath, overwrite }),

  exportSkinZip: (skinId: string, outZipPath: string, includeOverrides: boolean) =>
    callStudio<string>('studio_export_skin_zip', {
      skinId,
      outZipPath,
      includeOverrides,
    }),

  injectIde: (skinId?: string | null, ideRoot?: string | null) =>
    callStudio<string>('studio_inject_ide', {
      skinId: skinId ?? null,
      ideRoot: ideRoot ?? null,
    }),

  removeIde: (ideRoot?: string | null) =>
    callStudio<string>('studio_remove_ide', { ideRoot: ideRoot ?? null }),

  reapplyCheck: (force: boolean) =>
    callStudio<ReapplyCheckResult>('studio_reapply_check', { force }),

  setAutoReapply: (enabled: boolean) =>
    callStudio<boolean>('studio_set_auto_reapply', { enabled }),

  toggleAutostart: (enable: boolean) =>
    callStudio<void>('toggle_auto_launch', { enable }),

  getPetAssets: () =>
    callStudio<PetAssets>('studio_get_pet_assets', {}, () => ({})),

  launchPet: (character?: string) =>
    callStudio<boolean>('studio_launch_pet', { character: character ?? null }),

  closePet: () => callStudio<boolean>('studio_close_pet'),

  resetPetPosition: () => callStudio<void>('studio_reset_pet_position'),

  setPetSize: (width: number, height: number) =>
    callStudio<void>('studio_set_pet_size', { width, height }),

  setPetAlwaysOnTop: (alwaysOnTop: boolean) =>
    callStudio<void>('studio_set_pet_always_on_top', { alwaysOnTop }),

  getMediaStatus: () =>
    callStudio<MediaStatus>(
      'studio_get_media_status',
      {},
      () => ({
        isPlaying: false,
        title: '',
        artist: '',
        rawTitle: '',
        source: '',
        lrc: '',
      }),
    ),

  sendMediaCommand: (cmd: 'play_pause' | 'next' | 'prev' | 'vol_up' | 'vol_down') =>
    callStudio<void>('studio_send_media_command', { cmd }),
};
