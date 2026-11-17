import React, { Suspense, lazy } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";
import { isTauri } from "./utils/env";

const winLabel =
  typeof window !== "undefined"
    ? (window as unknown as { __TAURI_INTERNALS__?: { metadata?: { currentWindow?: { label?: string } } } })
        .__TAURI_INTERNALS__?.metadata?.currentWindow?.label
    : undefined;

const isMini =
  (typeof window !== "undefined" && window.location.search.includes("mini")) ||
  winLabel === "mini";

const isPet =
  (typeof window !== "undefined" && window.location.search.includes("pet")) ||
  winLabel === "pet";

// 独立桌宠窗口轻量化直通加载：避免拉取主控制台路由树、图表库与重型组件库，内存与启动耗时降低 90%+
if (isPet && typeof document !== "undefined") {
  document.documentElement.classList.add("pet-window");
  document.documentElement.style.setProperty("background-color", "transparent", "important");
  document.documentElement.style.setProperty("background", "transparent", "important");
  if (document.body) {
    document.body.classList.add("pet-window");
    document.body.style.setProperty("background-color", "transparent", "important");
    document.body.style.setProperty("background", "transparent", "important");
  }
  const rootEl = document.getElementById("root");
  if (rootEl) {
    rootEl.classList.add("pet-root");
    rootEl.style.setProperty("background-color", "transparent", "important");
    rootEl.style.setProperty("background", "transparent", "important");
  }
}

// 启动时显式调用 Rust 命令显示主窗口（仅在主窗口上下文触发，悬浮窗与桌宠窗不调用）
if (isTauri() && !isMini && !isPet) {
  import("@tauri-apps/api/core").then(({ invoke }) => {
    invoke("show_main_window").catch(console.error);
  });
}

const LazyPetWindowView = lazy(() => import("./components/pet/PetWindowView"));
const LazyFullApp = lazy(async () => {
  await import("./i18n");
  return import("./App");
});

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <Suspense fallback={null}>
      {isPet ? <LazyPetWindowView /> : <LazyFullApp />}
    </Suspense>
  </React.StrictMode>,
);
