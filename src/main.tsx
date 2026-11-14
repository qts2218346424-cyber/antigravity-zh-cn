import React from "react";
import ReactDOM from "react-dom/client";
import App from './App';
import './i18n'; // Import i18n config
import "./App.css";

import { isTauri } from "./utils/env";
// 启动时显式调用 Rust 命令显示主窗口（仅在主窗口上下文触发，悬浮窗不调用）
// 配合 visible:false 使用，解决启动黑屏问题
if (isTauri()) {
  const winLabel = (window as any).__TAURI_INTERNALS__?.metadata?.currentWindow?.label;
  const isMini =
    (typeof window !== 'undefined' && window.location.search.includes('mini')) ||
    winLabel === 'mini';
  const isPet =
    (typeof window !== 'undefined' && window.location.search.includes('pet')) ||
    winLabel === 'pet';
  if (!isMini && !isPet) {
    import("@tauri-apps/api/core").then(({ invoke }) => {
      invoke("show_main_window").catch(console.error);
    });
  }
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />

  </React.StrictMode>,
);
