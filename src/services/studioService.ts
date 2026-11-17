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
  StudioDiagnosticReport,
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
  {
    id: 'clannad-illusionary-orbs',
    name: 'CLANNAD · 幻想世界光玉',
    version: '2.0.0',
    author: 'Antigravity Studio',
    description: '深宵幻想世界苍穹蓝基底搭配暖金光玉高亮、22px 液态亚克力折射与静谧星尘。',
    base: 'dark',
    path: 'resources/skins/clannad-illusionary-orbs',
    builtin: true,
    colors: {
      background: '#090d18',
      foreground: '#e8eef9',
      accent: '#f6c453',
      sidebar: '#0d1324',
      activityBar: '#070a13',
      titleBar: '#080c16',
      statusBar: '#172542',
      panel: '#0c1221',
      border: '#1f2d4a',
      input: '#11192e',
      muted: '#8294b8',
    },
    active: false,
  },
  {
    id: 'clannad-sakura-hill',
    name: 'CLANNAD · 光坂坡道与团子',
    version: '2.0.0',
    author: 'Antigravity Studio',
    description: '春季樱花坡道与团子大家族：晨曦奶油樱白护眼底色、柔粉樱花缎带状态栏与微笑团子暗纹。',
    base: 'light',
    path: 'resources/skins/clannad-sakura-hill',
    builtin: true,
    colors: {
      background: '#fdf8fa',
      foreground: '#3b2c35',
      accent: '#e57399',
      sidebar: '#f9eff3',
      activityBar: '#f3e2e9',
      titleBar: '#f5e6ec',
      statusBar: '#d96b90',
      panel: '#fcf3f7',
      border: '#edd0dd',
      input: '#ffffff',
      muted: '#947684',
    },
    active: false,
  },
  {
    id: 'clannad-after-sunflower',
    name: 'CLANNAD · 汐与晴空花田',
    version: '2.0.0',
    author: 'Antigravity Studio',
    description: '致敬黄金向日葵花海与冈崎汐的草帽晴日：温暖麦穗米白阅读基底、向日葵琥珀金高光与盛夏晴空蓝状态栏。',
    base: 'light',
    path: 'resources/skins/clannad-after-sunflower',
    builtin: true,
    colors: {
      background: '#fdfbf4',
      foreground: '#332a1d',
      accent: '#e08e14',
      sidebar: '#f8f3e3',
      activityBar: '#f1ead3',
      titleBar: '#f3edd8',
      statusBar: '#0284c7',
      panel: '#fbf7ea',
      border: '#e8dec3',
      input: '#ffffff',
      muted: '#8a7a5f',
    },
    active: false,
  },
  {
    id: 'clannad-starfish-library',
    name: 'CLANNAD · 图书室海星与提琴',
    version: '2.0.0',
    author: 'Antigravity Studio',
    description: '一之濑琴美静谧黄昏图书室与伊吹风子木雕海星：暮色紫檀深空底色与薰衣草提琴弦光。',
    base: 'dark',
    path: 'resources/skins/clannad-starfish-library',
    builtin: true,
    colors: {
      background: '#120f1c',
      foreground: '#efeaf8',
      accent: '#c084fc',
      sidebar: '#181326',
      activityBar: '#0e0b16',
      titleBar: '#100d19',
      statusBar: '#3b235a',
      panel: '#161122',
      border: '#2f2447',
      input: '#1e1730',
      muted: '#9b8cb8',
    },
    active: false,
  },
];

let previewStatusState: StudioStatus = {
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
  pet_character: 'nezuko',
  pet_roaming: true,
  pet_always_on_top: true,
  pet_scale_idx: 1,
  pet_muted: false,
  custom_pet_avatar: null,
  lang: 'zh-cn',
  enable_pet: false,
  enable_skin: true,
  pet_window_open: false,
  has_legacy_pet: false,
  config_dir: '%APPDATA%\\antigravity-zh-cn',
  resource_dir: 'resources',
  reapply_logs: ['[浏览器预览模式] 完整文件修补与独立窗口控制在 Tauri 桌面客户端中运行'],
};

async function callStudio<T>(
  cmd: string,
  args: Record<string, unknown> = {},
  fallback?: () => T,
): Promise<T> {
  if (!isTauri()) {
    if (fallback) return fallback();
    throw new Error(`当前处于纯浏览器预览模式，无法调用桌面原生接口 ${cmd}`);
  }
  return invoke<T>(cmd, args);
}

export const studioService = {
  getStatus: () =>
    callStudio<StudioStatus>('studio_get_status', {}, () => ({ ...previewStatusState })),

  updatePaths: (installDir?: string | null, ideDir?: string | null) =>
    callStudio<StudioStatus>(
      'studio_update_paths',
      { installDir: installDir ?? null, ideDir: ideDir ?? null },
      () => {
        previewStatusState = {
          ...previewStatusState,
          install_dir: installDir !== undefined ? installDir : previewStatusState.install_dir,
          ide_root: ideDir !== undefined ? ideDir : previewStatusState.ide_root,
        };
        return { ...previewStatusState };
      },
    ),

  applyL10n: (params: {
    install_dir?: string | null;
    lang: string;
    character: string;
    enable_pet: boolean;
    enable_skin: boolean;
  }) =>
    callStudio<L10nPatchResult>(
      'studio_apply_l10n',
      {
        installDir: params.install_dir ?? null,
        lang: params.lang,
        character: params.character,
        enablePet: params.enable_pet,
        enableSkin: params.enable_skin,
      },
      () => {
        previewStatusState = {
          ...previewStatusState,
          lang: params.lang,
          splash_character: params.character,
          enable_skin: params.enable_skin,
          agent_status: 'patched',
        };
        return {
          success: true,
          message: `[浏览器预览模拟] 已记录配置（语言: ${params.lang}, 启动序幕: ${params.character}）`,
          install_dir: previewStatusState.install_dir || '',
          lang: params.lang,
          character: params.character,
          patched_files: ['dist/main.js', 'dist/preload.js'],
          warnings: [],
        };
      },
    ),

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
          surfaces: {
            radius: '12px',
            glass_blur: 18,
            card_opacity: 0.78,
            border_glow: 'rgba(255, 255, 255, 0.16)',
            noise_grain: 0.03,
            shadow_elevation:
              hit.base === 'light'
                ? '0 16px 36px -12px rgba(232, 106, 146, 0.22)'
                : '0 20px 50px -12px rgba(0, 0, 0, 0.72)',
          },
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
    callStudio<boolean>('studio_set_auto_reapply', { enabled }, () => {
      previewStatusState = { ...previewStatusState, auto_reapply: enabled };
      return enabled;
    }),

  toggleAutostart: (enable: boolean) =>
    callStudio<void>('toggle_auto_launch', { enable }),

  getPetAssets: () =>
    callStudio<PetAssets>('studio_get_pet_assets', {}, () => ({
      custom_avatar: previewStatusState.custom_pet_avatar ?? null,
    })),

  launchPet: (character?: string) =>
    callStudio<boolean>(
      'studio_launch_pet',
      { character: character ?? null },
      () => {
        previewStatusState = {
          ...previewStatusState,
          pet_window_open: true,
          enable_pet: true,
          pet_character: character || previewStatusState.pet_character,
        };
        if (typeof window !== 'undefined') {
          window.dispatchEvent(
            new CustomEvent('studio:pet-state-changed', {
              detail: { open: true, character: previewStatusState.pet_character },
            }),
          );
        }
        return true;
      },
    ),

  closePet: () =>
    callStudio<boolean>('studio_close_pet', {}, () => {
      previewStatusState = {
        ...previewStatusState,
        pet_window_open: false,
        enable_pet: false,
      };
      if (typeof window !== 'undefined') {
        window.dispatchEvent(
          new CustomEvent('studio:pet-state-changed', {
            detail: { open: false, character: previewStatusState.pet_character },
          }),
        );
      }
      return false;
    }),

  resetPetPosition: () => callStudio<void>('studio_reset_pet_position', {}, () => undefined),

  setPetSize: (width: number, height: number) =>
    callStudio<void>('studio_set_pet_size', { width, height }, () => undefined),

  setPetAlwaysOnTop: (alwaysOnTop: boolean) =>
    callStudio<void>('studio_set_pet_always_on_top', { alwaysOnTop }, () => {
      previewStatusState = { ...previewStatusState, pet_always_on_top: alwaysOnTop };
    }),

  nudgePet: (dx: number) =>
    callStudio<number>('studio_nudge_pet', { dx }, () => 0),

  importPetAvatar: (filePath: string) =>
    callStudio<string>('studio_import_pet_avatar', { filePath }),

  clearPetAvatar: () =>
    callStudio<void>('studio_clear_pet_avatar', {}, () => {
      previewStatusState = {
        ...previewStatusState,
        custom_pet_avatar: null,
        pet_character: 'nezuko',
      };
    }),

  updatePetPrefs: (prefs: {
    character?: string;
    roaming?: boolean;
    alwaysOnTop?: boolean;
    scaleIdx?: number;
    muted?: boolean;
  }) =>
    callStudio<void>(
      'studio_update_pet_prefs',
      {
        character: prefs.character ?? null,
        roaming: prefs.roaming ?? null,
        alwaysOnTop: prefs.alwaysOnTop ?? null,
        scaleIdx: prefs.scaleIdx ?? null,
        muted: prefs.muted ?? null,
      },
      () => {
        previewStatusState = {
          ...previewStatusState,
          pet_character: prefs.character ?? previewStatusState.pet_character,
          pet_roaming: prefs.roaming ?? previewStatusState.pet_roaming,
          pet_always_on_top: prefs.alwaysOnTop ?? previewStatusState.pet_always_on_top,
          pet_scale_idx: prefs.scaleIdx ?? previewStatusState.pet_scale_idx,
          pet_muted: prefs.muted ?? previewStatusState.pet_muted,
        };
      },
    ),

  runDiagnostics: () =>
    callStudio<StudioDiagnosticReport>('studio_run_diagnostics', {}, () => ({
      all_passed: true,
      total_ms: 14,
      items: [
        {
          key: 'l10n_resources',
          name: '多语种汉化词典与运行时脚本核验',
          passed: true,
          duration_ms: 4,
          detail: '[浏览器预览模拟] 7 项汉化词典与运行时脚本配置完整',
        },
        {
          key: 'skin_compiler',
          name: '高定光学材质包 Schema 与安全沙盒校验',
          passed: true,
          duration_ms: 5,
          detail: `[浏览器预览模拟] 全部 ${PREVIEW_SKINS.length} 款内置材质包通过校验`,
        },
        {
          key: 'pet_assets',
          name: '桌面伴侣骨骼刚体与 5 大内置角色材质缓存',
          passed: true,
          duration_ms: 3,
          detail: '[浏览器预览模拟] 6 角色配置与声学合成器就绪',
        },
        {
          key: 'client_probe',
          name: 'Antigravity 客户端与 IDE 安装环境探测',
          passed: true,
          duration_ms: 2,
          detail: '桌面端启动后将实时读取真实本机环境状态',
        },
      ],
    })),

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
    callStudio<void>('studio_send_media_command', { cmd }, () => undefined),
};
