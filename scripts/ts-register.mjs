import { register } from 'node:module';

// 为纯 Node 单元测试环境提供轻量内存版 localStorage 垫片（供 Zustand persist 等模块安全读写）
if (typeof globalThis.localStorage === 'undefined') {
  const store = new Map();
  globalThis.localStorage = {
    getItem: (key) => (store.has(String(key)) ? store.get(String(key)) : null),
    setItem: (key, value) => {
      store.set(String(key), String(value));
    },
    removeItem: (key) => {
      store.delete(String(key));
    },
    clear: () => {
      store.clear();
    },
    key: (index) => Array.from(store.keys())[index] ?? null,
    get length() {
      return store.size;
    },
  };
}

register('./ts-loader-hooks.mjs', import.meta.url);
