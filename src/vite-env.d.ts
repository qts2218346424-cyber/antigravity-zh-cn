/// <reference types="vite/client" />

declare module '../../../resources/kimetsu_theater_engine.js' {
  const _sideEffect: void;
  export default _sideEffect;
}

interface KimetsuTheaterInstance {
  replay: () => void;
  destroy: () => void;
}

interface KimetsuTheaterMountOptions {
  character: string;
  durationMs?: number;
  loop?: boolean;
  steps?: string[];
  version?: string;
  assets?: Record<string, string>;
}

interface Window {
  KimetsuTheater?: {
    mount: (container: HTMLElement, options: KimetsuTheaterMountOptions) => KimetsuTheaterInstance | null;
    CHARACTERS?: Record<string, { name: string; breath: string; kanji: string; primary: string }>;
  };
}
