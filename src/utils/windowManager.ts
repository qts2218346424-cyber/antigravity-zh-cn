import { getCurrentWindow, LogicalSize } from '@tauri-apps/api/window';
import { isTauri } from './env';

/**
 * 确保主窗口处于标准完整视图状态（自愈恢复逻辑）
 */
export const ensureFullViewState = async () => {
  if (!isTauri()) return;
  try {
    const win = getCurrentWindow();
    const size = await win.outerSize();
    if (size.width < 500) {
      await win.setSize(new LogicalSize(1200, 800));
      await win.center();
    }
    await win.setDecorations(true);
    await win.setResizable(true);
    await win.setAlwaysOnTop(false);
  } catch (error) {
    console.error('恢复主窗口完整视图状态失败:', error);
  }
};
