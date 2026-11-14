export interface SkinColors {
  background?: string;
  foreground?: string;
  accent?: string;
  accentForeground?: string;
  sidebar?: string;
  activityBar?: string;
  titleBar?: string;
  statusBar?: string;
  panel?: string;
  border?: string;
  selection?: string;
  input?: string;
  muted?: string;
  [key: string]: string | undefined;
}

export interface SkinBackgroundRule {
  image?: string;
  file?: string;
  target?: string;
  selector?: string;
  opacity?: number;
  blur?: number;
  size?: string;
  position?: string;
  repeat?: string;
  blend_mode?: string;
  enabled?: boolean;
}

export interface SkinFontConfig {
  family?: string;
  monoFamily?: string;
  size?: number;
  file?: string;
  font_name?: string;
  ligatures?: boolean;
}

export interface SkinPetConfig {
  character?: string;
  accent?: string;
  scale?: number;
  filter?: string;
  hidden?: boolean;
  sprite?: string;
  css?: string;
}

export interface SkinManifest {
  schema?: number;
  schema_version?: number;
  id: string;
  name: string;
  author?: string;
  version?: string;
  description?: string;
  base?: string;
  preview?: string;
  colors?: SkinColors;
  variables?: Record<string, string>;
  background?: SkinBackgroundRule | SkinBackgroundRule[];
  backgrounds?: Record<string, SkinBackgroundRule>;
  font?: SkinFontConfig;
  typography?: SkinFontConfig;
  surfaces?: {
    radius?: string;
    glass_blur?: number;
    card_opacity?: number;
    border_glow?: string;
    noise_grain?: number;
    shadow_elevation?: string;
  };
  icons?: {
    filter?: string;
    color?: string;
    codicons?: Record<string, string>;
  };
  css?: string;
  custom_css?: string;
  pet?: SkinPetConfig;
}

export interface SkinInfo {
  id: string;
  name: string;
  version: string;
  author: string;
  description: string;
  base: string;
  path: string;
  builtin: boolean;
  preview_data_uri?: string | null;
  colors: SkinColors;
  active: boolean;
}

export interface CompiledSkin {
  skin_id: string;
  css: string;
  runtime_json: Record<string, unknown>;
  compiled_css_path: string;
  compiled_runtime_path: string;
}

export interface StudioStatus {
  install_dir?: string | null;
  ide_root?: string | null;
  agent_status: 'not_found' | 'clean' | 'patched' | string;
  ide_status: 'not_found' | 'clean' | 'injected' | 'stale' | string;
  active_skin?: string | null;
  skin_enabled: boolean;
  ide_enabled: boolean;
  auto_reapply: boolean;
  autostart_enabled: boolean;
  updates_disabled: boolean;
  splash_character: string;
  lang: string;
  enable_pet: boolean;
  enable_skin: boolean;
  pet_window_open: boolean;
  config_dir: string;
  resource_dir: string;
  reapply_logs: string[];
}

export interface L10nPatchResult {
  success: boolean;
  message: string;
  install_dir: string;
  lang: string;
  character: string;
  patched_files: string[];
  warnings: string[];
}

export interface SkillLocalizeResult {
  scanned: number;
  updated: number;
  skipped: number;
  details: string[];
}

export interface ReapplyCheckResult {
  agent: string;
  ide: string;
  actions: string[];
  error?: string | null;
}

export interface MediaStatus {
  isPlaying: boolean;
  title: string;
  artist: string;
  rawTitle: string;
  source: string;
  lrc: string;
}

export interface PetAssets {
  nezuko_chibi?: string | null;
  nezuko_basket?: string | null;
  nezuko_spin_sheet?: string | null;
  shockwave?: string | null;
  little_prince?: string | null;
  prince_fox?: string | null;
  prince_rose?: string | null;
  prince_stars?: string | null;
  prince_sunset?: string | null;
}
