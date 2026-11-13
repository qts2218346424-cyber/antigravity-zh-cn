#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 汉化 & 材质包管理器（一体化轻量图形界面）

一个程序包含：
  · 材质包：卡片画廊 + 预览 + 一键切换、导入/导出 .zip、以现有包为模板新建、删除
  · 自定义：颜色 / 背景图(透明度、模糊、位置) / 字体 / 图标 / 桌宠外观 / 自定义 CSS（写入用户覆盖层），带实时预览
  · 汉化：安装/重打汉化补丁、还原原版、禁止/恢复官方自动更新
  · 桌宠：启动独立桌面桌宠（Windows）
  · 自动维护：开机后台检测 Antigravity 更新并自动重新注入

运行模式：
  agzh_app.py                 打开图形界面
  agzh_app.py --background    后台常驻检测（开机自启使用，无窗口）
  agzh_app.py --check-once    检测一次并按需重新注入（macOS LaunchAgent 使用）
  agzh_app.py --pet           启动独立桌面桌宠（Windows）
  agzh_app.py --media <动作>  多媒体助手（供打过补丁的 Antigravity 调用，输出一行 JSON）
  agzh_app.py cli <参数...>   等同于 scripts/agzh.py 命令行

界面基于 Python 自带的 tkinter + 手工 ttk 主题：无需 Electron / 浏览器内核，打包后体积最小。
所有耗时操作（打补丁、扫描、解码预览图、导入导出、状态检测）都在后台线程执行，主线程只负责界面。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_BASE = Path(getattr(sys, "_MEIPASS", HERE.parent))
for _p in (_BASE / "scripts", HERE.parent / "scripts", _BASE / "resources", HERE.parent / "resources", HERE,
           _BASE / "app"):
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import agzh_core as core  # noqa: E402
import auto_reapply as ar  # noqa: E402
import skin_injector as si  # noqa: E402
import skin_manager as sm  # noqa: E402

APP_TITLE = "Antigravity 汉化 & 材质包管理器"
ASSETS = next((p for p in (_BASE / "app" / "assets", HERE / "assets") if p.is_dir()), HERE / "assets")

COLOR_LABELS = {
    "background": "编辑器背景", "foreground": "前景文字", "accent": "强调色", "accentForeground": "强调色上的文字",
    "sidebar": "侧边栏", "activityBar": "活动栏", "titleBar": "标题栏", "statusBar": "状态栏",
    "panel": "面板/终端", "border": "边框", "selection": "选中背景", "input": "输入框", "muted": "次要文字",
}
TARGET_LABELS = {"window": "整个窗口", "editor": "编辑区", "sidebar": "侧边栏", "panel": "底部面板",
                 "terminal": "终端", "chat": "对话区"}
STATUS_TEXT = {
    "patched": "已汉化", "never": "未汉化", "disabled": "已还原（不自动重打）",
    "needs_reapply": "已被官方更新覆盖，待重新注入", "missing": "未找到安装目录",
    "applied": "已应用", "stale": "皮肤已变更，待同步", "not_applied": "未应用",
    "reapplied": "已重新注入", "deferred_running": "Antigravity 正在运行，退出后自动重新注入",
    "deferred_settling": "Antigravity 正在更新，完成后自动重新注入",
    "deferred_locked": "另一个进程正在重新注入", "error": "出错（详见日志）",
    "unchanged": "已是最新", "permission_denied": "没有写入权限", "not_found": "未找到 IDE", "cleared": "已清除",
}
STATUS_KIND = {"patched": "ok", "applied": "ok", "reapplied": "ok", "unchanged": "ok",
               "never": "muted", "not_applied": "muted", "disabled": "muted", "missing": "muted",
               "needs_reapply": "warn", "stale": "warn", "deferred_running": "warn", "deferred_settling": "warn",
               "deferred_locked": "warn", "error": "err", "permission_denied": "err"}
# 图标只用基本多文种平面 (BMP) 内的符号：Tk 8.6 无法可靠显示 emoji 等补充平面字符
NAV = (("材质包", "❖", "浏览、预览并一键切换材质包"),
       ("自定义", "✎", "在材质包之上微调颜色、背景、字体、图标与桌宠"),
       ("汉化补丁", "文", "为 Agent 桌面端安装 / 还原中文补丁"),
       ("桌宠", "❀", "在桌面上启动祢豆子 / 小王子"),
       ("自动维护", "⟳", "官方更新后自动重新注入汉化与皮肤"))


# ---------------------------------------------------------------------------
# 非图形模式
# ---------------------------------------------------------------------------
def _ensure_stdout() -> None:
    """打包成窗口程序 (console=False) 时 sys.stdout 为 None；被 Electron 以管道调用时仍需输出 JSON。"""
    if sys.stdout is not None:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        return
    try:
        sys.stdout = open(1, "w", encoding="utf-8", errors="replace", closefd=False)
        return
    except OSError:
        pass
    if sys.platform == "win32":
        try:
            import ctypes
            import msvcrt
            h = ctypes.windll.kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            if h and h != -1:
                fd = msvcrt.open_osfhandle(h, os.O_WRONLY)
                sys.stdout = open(fd, "w", encoding="utf-8", errors="replace", closefd=False)
        except Exception:
            pass


def run_headless(argv: list[str]) -> int | None:
    if "--background" in argv:
        core.bootstrap()
        ar.watch(interval=120)
        return 0
    if "--check-once" in argv:
        core.bootstrap()
        if sm.load_state().get("auto_reapply"):
            ar.check(apply=True)
        return 0
    if "--pet" in argv:
        core.bootstrap()
        import desktop_pet_app
        desktop_pet_app.main()
        return 0
    if argv and argv[0] == "--media":
        _ensure_stdout()
        import media_helper
        return media_helper.main(argv[1:], out=sys.stdout) if sys.stdout is not None else 1
    if argv and argv[0] == "cli":
        import agzh
        return agzh.main(argv[1:])
    return None


# ---------------------------------------------------------------------------
# 纯数据（无界面，可在工作线程执行）
# ---------------------------------------------------------------------------
def load_snapshot() -> dict:
    """一次性读取界面需要的全部状态（材质包列表 + 汉化/IDE/自动维护状态）。在 io 通道执行。"""
    snap: dict = {"skins": [], "status": None, "errors": []}
    try:
        snap["skins"] = core.list_skins()
    except Exception as e:  # noqa: BLE001
        snap["errors"].append(f"读取材质包失败: {e}")
    try:
        snap["status"] = core.status()
    except Exception as e:  # noqa: BLE001
        snap["errors"].append(f"状态读取失败: {e}")
    st = sm.load_state()
    snap["ide_enabled"] = (st.get("ide") or {}).get("enabled")
    snap["active_skin"] = st.get("active_skin")
    return snap


def load_custom_data(scope: str | None) -> dict:
    """读取覆盖层与材质包的默认背景。在 io 通道执行。"""
    ov = sm.load_override(scope)
    base_bg: dict = {}
    if scope:
        try:
            b = sm.get_pack(scope).manifest.get("background")
            base_bg = b[0] if isinstance(b, list) and b else (b or {})
        except sm.SkinError:
            pass
    return {"scope": scope, "override": ov, "base_bg": base_bg}


def build_override(raw: dict) -> dict:
    """把表单原始值（全是字符串/数字/布尔）转换为覆盖层 dict；会把本地图片复制进覆盖层资源目录。"""
    ov: dict = {}
    colors = {k: v.strip() for k, v in raw["colors"].items() if v.strip()}
    if colors:
        ov["colors"] = colors
    bg: dict = {}
    img = raw["bg"]["image"].strip()
    if img:
        bg["image"] = sm.import_override_asset(Path(img)) if Path(img).is_absolute() else img
    b = raw["bg"]
    cur = (round(float(b["opacity"]), 2), round(float(b["blur"]), 1), b["target"], b["position"], b["size"])
    loaded = raw.get("loaded_bg")
    if img or loaded is None or cur != (round(loaded[0], 2), round(loaded[1], 1), *loaded[2:]):
        bg["opacity"] = cur[0]
        bg["blur"] = cur[1]
        inv = {v: k for k, v in TARGET_LABELS.items()}
        if cur[2]:
            bg["target"] = inv.get(cur[2], "window")
        if cur[3]:
            bg["position"] = cur[3]
        if cur[4]:
            bg["size"] = cur[4]
    if bg:
        ov["background"] = bg
    for sect in ("font", "icons", "pet"):
        d = {}
        for key, v in raw[sect].items():
            if isinstance(v, bool):
                if v:
                    d[key] = True
                continue
            v = str(v).strip()
            if not v:
                continue
            if key in ("size", "monoSize"):
                d[key] = int(float(v))
            elif key == "scale":
                d[key] = float(v)
            elif key == "sprite":
                d[key] = sm.import_override_asset(Path(v)) if Path(v).is_absolute() else v
            else:
                d[key] = v
        if d:
            ov[sect] = d
    css = raw.get("css", "").strip()
    if css:
        ov["css"] = css
    return ov


def check_and_describe() -> str:
    r = ar.check(apply=True)
    parts = [f"Agent 桌面端：{STATUS_TEXT.get(r.get('agent'), r.get('agent'))}",
             f"IDE 皮肤：{STATUS_TEXT.get(r.get('ide'), r.get('ide'))}"]
    if r.get("error"):
        parts.append(f"错误：{r['error']}")
    print("；".join(parts))
    return "；".join(parts)


# ---------------------------------------------------------------------------
# 图形界面
# ---------------------------------------------------------------------------
class App:
    THUMB = (184, 113)
    PREVIEW = (300, 184)

    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk

        import ui_kit as ui
        self.tk, self.ttk, self.ui = tk, ttk, ui
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1100x720")
        root.minsize(920, 600)

        self.theme = ui.Theme(root)
        self._orig_streams = (sys.stdout, sys.stderr)
        self.log_lines: list[str] = []
        self._log_pending: list[str] = []
        self.router = ui.OutputRouter(sys.stdout, self._log_from_thread)
        self.router_err = ui.OutputRouter(sys.stderr, self._log_from_thread)
        self.router_err._capturing = self.router._capturing  # 共用同一组“正在捕获”的线程
        self.router_err._buf = self.router._buf
        self.router_err._lock = self.router._lock
        sys.stdout, sys.stderr = self.router, self.router_err
        self.jobs = ui.JobRunner(self.router)
        self.images = ui.ImageCache(root, self.jobs)
        self.toaster = ui.Toaster(root, self.theme)

        self.skins: list[dict] = []
        self.selected_id: str | None = None
        self.form: dict = {}
        self.status_data: dict | None = None
        self._built: dict[int, bool] = {}
        self._cards: dict[str, dict] = {}
        self._refresh_pending = False
        self._refresh_again = False
        self._polling = False
        self._task_title = ""
        self._loaded_bg = None
        self._custom_loaded_scope = "<none>"
        self._families: list[str] | None = None
        self._icon_img = None

        st = sm.load_state()
        self.theme_pref = st.get("ui_theme") or "system"
        self.theme.apply(self._resolve_theme())
        self.theme.on_change(self._on_theme_change)
        self._set_icon()

        self._build_shell()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind("<Destroy>", self._on_destroy, add="+")
        self.select_tab(0)
        self.refresh_all()
        if self.theme_pref == "system":
            root.after(30000, self._follow_system_theme)

    # ================================================================ 基础设施
    def _resolve_theme(self) -> str:
        if self.theme_pref in ("light", "dark"):
            return self.theme_pref
        return "dark" if self.ui.system_prefers_dark() else "light"

    def _follow_system_theme(self):
        if self.theme_pref != "system" or not self.ui._alive(self.root):
            return
        want = self._resolve_theme()
        if want != self.theme.mode:
            self.theme.apply(want)
        self.root.after(30000, self._follow_system_theme)

    def set_theme(self, pref: str):
        """pref: system / light / dark（保存到用户配置）。"""
        self.theme_pref = pref
        self.theme.apply(self._resolve_theme())
        self.jobs.submit("io", sm.update_state, ui_theme=pref)
        self._kick()
        self.theme_btn.configure(text=self._theme_label())

    def _theme_label(self) -> str:
        return {"system": "◐  外观：跟随系统", "light": "☀  外观：浅色", "dark": "☾  外观：深色"}[self.theme_pref]

    def cycle_theme(self):
        nxt = {"system": "light", "light": "dark", "dark": "system"}[self.theme_pref]
        self.set_theme(nxt)
        self.toast(f"已切换为{ {'system': '跟随系统', 'light': '浅色', 'dark': '深色'}[nxt] }外观")

    def _on_theme_change(self):
        # 卡片/预览画布是手绘的，换主题后重绘
        self._render_gallery(force=True)
        self.show_skin_detail()
        if self._built.get(1):
            self._update_custom_preview()

    def _set_icon(self):
        try:
            ico = ASSETS / "icon.ico"
            if sys.platform == "win32" and ico.is_file():
                self.root.iconbitmap(default=str(ico))
            png = ASSETS / "icon.png"
            if png.is_file():
                self._icon_img = self.tk.PhotoImage(master=self.root, file=str(png))
                self.root.iconphoto(True, self._icon_img)
        except Exception:
            pass

    def _log_from_thread(self, line: str):
        # 任意线程调用：只追加到列表（GIL 保证 append 原子），由主线程轮询写入日志框
        self._log_pending.append(line)

    def write_log(self, text: str):
        self._log_pending.append(text)
        self._kick()

    def _kick(self):
        """确保主线程轮询在运行（空闲时轮询自动停止，不占 CPU）。"""
        if not self._polling:
            self._polling = True
            try:
                self.root.after(15, self._poll)
            except Exception:
                self._polling = False

    def _poll(self):
        self.jobs.poll()
        if self._log_pending:
            lines, self._log_pending = self._log_pending, []
            self._append_log(lines)
        self._update_busy()
        if self.jobs.busy() or self._log_pending:
            self.root.after(40, self._poll)
        else:
            self._polling = False

    def _append_log(self, lines: list[str]):
        self.log_lines.extend(lines)
        if len(self.log_lines) > 2000:
            self.log_lines = self.log_lines[-1500:]
        t = self.log
        t.configure(state="normal")
        t.insert("end", "\n".join(x.rstrip("\n") for x in lines) + "\n")
        # 日志框只保留最近约 1500 行，避免长时间运行内存增长
        if int(t.index("end-1c").split(".")[0]) > 1600:
            t.delete("1.0", "200.0")
        t.see("end")
        t.configure(state="disabled")
        self.status_msg.configure(text=lines[-1][:120])

    def _update_busy(self):
        busy = self.jobs.busy("task")
        if busy and not self._busy_shown:
            self.progress.pack(side="right", padx=(0, 12))
            self.progress.start(12)
            self._busy_shown = True
            for b in self._task_buttons:
                b.state(["disabled"])
        elif not busy and self._busy_shown:
            self.progress.stop()
            self.progress.pack_forget()
            self._busy_shown = False
            for b in self._task_buttons:
                if self.ui._alive(b):
                    b.state(["!disabled"])

    def wait_idle(self, timeout: float = 10.0) -> bool:
        """（测试与截图用）处理事件直到后台任务全部完成。"""
        import time
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.root.update()
            self.jobs.poll()
            if not self.jobs.busy():
                self.root.update()
                if not self.jobs.busy():
                    return True
            time.sleep(0.01)
        return False

    def run_task(self, title: str, fn, *args, on_done=None, quiet: bool = False, **kwargs):
        """在后台 task 通道执行会修改文件的操作，print 输出进入日志；完成后刷新界面。"""
        if self.jobs.busy("task"):
            self.toast("上一个操作仍在进行中，请稍候。", "warn")
            return
        self._task_title = title
        self.write_log(f"▶ {title}…")
        self.status_msg.configure(text=f"{title}…")

        def done(result, err, tb):
            if err is not None:
                self.write_log(tb)
                self.msg("操作失败", f"{title}失败：\n{err}", error=True)
            else:
                self.write_log(f"✔ {title}完成")
                if not quiet:
                    self.toast(f"{title}完成", "ok")
            if on_done:
                on_done(result, err)
            self.refresh_all()

        self.jobs.submit("task", fn, *args, on_done=done, capture=True, **kwargs)
        self._kick()
        self._update_busy()

    def run_io(self, fn, *args, on_done=None, **kwargs):
        self.jobs.submit("io", fn, *args, on_done=on_done, **kwargs)
        self._kick()

    def toast(self, text: str, kind: str = "info"):
        try:
            self.toaster.show(text, kind)
        except Exception:
            pass

    def msg(self, title, text, error=False):
        from tkinter import messagebox
        (messagebox.showerror if error else messagebox.showinfo)(title, text, parent=self.root)

    def ask(self, title, text) -> bool:
        from tkinter import messagebox
        return messagebox.askyesno(title, text, parent=self.root)

    def tip(self, widget, text):
        self.ui.Tooltip(widget, text, self.theme)
        return widget

    def on_close(self):
        if self.jobs.busy("task") and not self.ask("仍有操作进行中", f"“{self._task_title}”尚未完成，强行退出可能导致文件写入不完整。确定退出吗？"):
            return
        self.root.destroy()

    def _on_destroy(self, e):
        if e.widget is self.root:
            sys.stdout, sys.stderr = self._orig_streams
            # 取消所有挂起的 after 回调（轮询、防抖、主题跟随），避免窗口销毁后再触发
            try:
                for aid in self.root.tk.splitlist(self.root.tk.call("after", "info")):
                    try:
                        self.root.after_cancel(aid)
                    except Exception:
                        pass
            except Exception:
                pass

    def open_path(self, p: Path):
        def do():
            p.mkdir(parents=True, exist_ok=True)
            import subprocess
            if sys.platform == "win32":
                os.startfile(str(p))  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
        self.run_io(do, on_done=lambda r, e, tb: e and self.toast(f"无法打开：{e}", "error"))

    # ================================================================ 外壳
    def _build_shell(self):
        tk, ttk = self.tk, self.ttk
        root = self.root
        self._task_buttons: list = []
        self._busy_shown = False

        # 状态栏（最底部）
        status = ttk.Frame(root, style="Status.TFrame", padding=(12, 5))
        status.pack(side="bottom", fill="x")
        self.status_msg = ttk.Label(status, text="就绪", style="Status.TLabel")
        self.status_msg.pack(side="left")
        self.log_btn = ttk.Button(status, text="日志 ▴", style="Ghost.TButton", command=self.toggle_log)
        self.log_btn.pack(side="right")
        self.theme.register(status, lambda c: None)
        self.progress = ttk.Progressbar(status, mode="indeterminate", length=140,
                                        style="Accent.Horizontal.TProgressbar")

        # 日志面板（可折叠）
        self.log_frame = ttk.Frame(root, padding=(12, 0, 12, 6))
        self.log = tk.Text(self.log_frame, height=7, wrap="word", state="disabled", relief="flat", borderwidth=0,
                           font=self.theme.mono(9), padx=10, pady=6)
        self.theme.register(self.log, lambda c: self.log.configure(background=c["log_bg"], foreground=c["muted"],
                                                                   insertbackground=c["text"],
                                                                   highlightthickness=1,
                                                                   highlightbackground=c["border"],
                                                                   highlightcolor=c["border"]))
        self.log.pack(fill="both", expand=True)
        self._log_visible = False

        # 侧边栏
        side = self.sidebar = ttk.Frame(root, style="Sidebar.TFrame", width=196)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        head = ttk.Frame(side, style="Sidebar.TFrame", padding=(16, 18, 12, 14))
        head.pack(fill="x")
        logo = tk.Canvas(head, width=34, height=34, highlightthickness=0, borderwidth=0)
        self.theme.register(logo, lambda c: logo.configure(background=c["sidebar"]))
        if self._icon_img is not None:
            try:
                img = self._icon_img.subsample(2, 2)
                logo._img = img  # 防止被回收
                logo.create_image(17, 17, image=img)
            except Exception:
                pass
        logo.pack(side="left")
        hl = ttk.Frame(head, style="Sidebar.TFrame")
        hl.pack(side="left", padx=(10, 0))
        ttk.Label(hl, text="Antigravity", style="Sidebar.TLabel").pack(anchor="w")
        ttk.Label(hl, text="汉化 & 材质包管理器", style="SidebarMuted.TLabel").pack(anchor="w")
        self.nav_buttons = []
        for i, (name, icon, _desc) in enumerate(NAV):
            b = ttk.Button(side, text=f"{icon}   {name}", style="Nav.TButton", command=lambda i=i: self.select_tab(i))
            b.pack(fill="x", padx=10, pady=1)
            self.nav_buttons.append(b)
        foot = ttk.Frame(side, style="Sidebar.TFrame")
        foot.pack(side="bottom", fill="x", pady=10)
        self.theme_btn = ttk.Button(foot, text=self._theme_label(), style="SidebarFoot.TButton",
                                    command=self.cycle_theme)
        self.theme_btn.pack(fill="x", padx=10)
        self.tip(self.theme_btn, "点击在 跟随系统 / 浅色 / 深色 之间切换")
        cfg_btn = ttk.Button(foot, text="▤  打开配置目录", style="SidebarFoot.TButton",
                             command=lambda: self.open_path(sm.config_dir()))
        cfg_btn.pack(fill="x", padx=10)
        self.tip(cfg_btn, "材质包、个人设置与日志都保存在这里，官方更新不会删除")

        # 主区域
        main = ttk.Frame(root, padding=(26, 20, 26, 10))
        main.pack(side="left", fill="both", expand=True)
        hdr = ttk.Frame(main)
        hdr.pack(fill="x")
        self.page_title = ttk.Label(hdr, text="", style="H1.TLabel")
        self.page_title.pack(side="left")
        self.header_badge = ttk.Label(hdr, text="", style="Badge.TLabel")
        self.header_badge.pack(side="right")
        self.tip(self.header_badge, "Agent 桌面端汉化状态")
        self.page_sub = ttk.Label(main, text="", style="Sub.TLabel")
        self.page_sub.pack(anchor="w", pady=(2, 14))

        self.nb = ttk.Notebook(main, style="Pages.TNotebook")
        self.nb.pack(fill="both", expand=True)
        self.pages = []
        for _ in NAV:
            f = ttk.Frame(self.nb)
            self.nb.add(f, text="")
            self.pages.append(f)
        self.tab_skins, self.tab_custom, self.tab_l10n, self.tab_pet, self.tab_auto = self.pages
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def toggle_log(self):
        if self._log_visible:
            self.log_frame.pack_forget()
            self.log_btn.configure(text="日志 ▴")
        else:
            # 必须排在侧边栏之前打包，否则只能分到侧边栏/主区域剩下的空间
            self.log_frame.pack(side="bottom", fill="x", before=self.sidebar)
            self.log_btn.configure(text="日志 ▾")
        self._log_visible = not self._log_visible

    def select_tab(self, i: int):
        self.nb.select(i)
        self._on_tab_changed()

    def _on_tab_changed(self, _e=None):
        try:
            i = self.nb.index(self.nb.select())
        except Exception:
            return
        self._ensure_built(i)
        name, icon, desc = NAV[i]
        self.page_title.configure(text=name)
        self.page_sub.configure(text=desc)
        for j, b in enumerate(self.nav_buttons):
            b.configure(style="NavActive.TButton" if j == i else "Nav.TButton")

    def _ensure_built(self, i: int):
        """懒加载：页面第一次显示时才创建控件（启动只构建首页）。"""
        if self._built.get(i):
            return
        self._built[i] = True
        builder = (self._build_skins, self._build_custom, self._build_l10n, self._build_pet, self._build_auto)[i]
        builder()
        if i == 1:
            self.load_custom_form()
        if self.status_data is not None:
            self._apply_status(self.status_data)

    # ================================================================ 刷新
    def refresh_all(self):
        """后台读取材质包与状态，完成后在主线程更新界面。连续调用会合并。"""
        if self._refresh_pending:
            self._refresh_again = True
            return
        self._refresh_pending = True

        def done(snap, err, tb):
            self._refresh_pending = False
            if err is not None:
                self.write_log(tb)
            else:
                for e in snap["errors"]:
                    self.write_log(e)
                self._apply_snapshot(snap)
            if self._refresh_again:
                self._refresh_again = False
                self.refresh_all()

        self.run_io(load_snapshot, on_done=done)

    def _apply_snapshot(self, snap: dict):
        self.skins = snap["skins"]
        ids = [s["id"] for s in self.skins]
        if self.selected_id not in ids:
            act = next((s["id"] for s in self.skins if s["active"]), None)
            self.selected_id = act or (ids[0] if ids else None)
        self._ide_pref = snap.get("ide_enabled")
        if self._built.get(0):
            self.ide_var.set(self._ide_pref is not False)
        self._render_gallery()
        self.show_skin_detail()
        if snap["status"] is not None:
            self.status_data = snap["status"]
            self._apply_status(snap["status"])
        if self._built.get(1):
            self.load_custom_form(only_if_scope_changed=True)

    def _apply_status(self, s: dict):
        agent = s["agent"]
        kind = STATUS_KIND.get(agent, "muted")
        self.header_badge.configure(text={"ok": "● ", "warn": "▲ ", "err": "✕ "}.get(kind, "○ ")
                                    + "Agent " + STATUS_TEXT.get(agent, agent))
        if self._built.get(2):
            if not self.dir_var.get() and s["install_dir"]:
                self.dir_var.set(s["install_dir"])
            self._set_status_label(self.l10n_status, agent)
            self.l10n_detail.configure(text=f"安装目录：{s['install_dir'] or '未检测到（可手动选择）'}")
        if self._built.get(4):
            self.auto_var.set(bool(s["auto_reapply"] and s["autostart"]))
            self._set_status_label(self.auto_agent, agent)
            ide = "not_found" if s["ide"] == "missing" else s["ide"]
            self._set_status_label(self.auto_ide, ide, extra=f"  {s['ide_root'] or ''}")
            self.auto_skin.configure(text=f"{s['active_skin'] or '无'}{'' if s['skin_enabled'] else '（已关闭）'}")
            self.auto_cfg.configure(text=s["config_dir"])

    def _set_status_label(self, lbl, code, extra=""):
        kind = STATUS_KIND.get(code, "muted")
        style = {"ok": "Ok.TLabel", "warn": "Warn.TLabel", "err": "Err.TLabel"}.get(kind, "CardMuted.TLabel")
        icon = {"ok": "● ", "warn": "▲ ", "err": "✕ "}.get(kind, "○ ")
        lbl.configure(text=icon + STATUS_TEXT.get(code, str(code)) + extra, style=style)

    # ================================================================ 材质包页
    def _build_skins(self):
        tk, ttk = self.tk, self.ttk
        f = self.tab_skins
        # 右侧详情
        detail = ttk.Frame(f, style="Card.TFrame", padding=16, width=self.PREVIEW[0] + 34)
        detail.pack(side="right", fill="y", padx=(16, 0))
        detail.pack_propagate(False)
        self.preview = tk.Canvas(detail, width=self.PREVIEW[0], height=self.PREVIEW[1], highlightthickness=0,
                                 borderwidth=0)
        self.theme.register(self.preview, lambda c: self.preview.configure(background=c["surface2"]))
        self.preview.pack(anchor="w")
        self.skin_title = ttk.Label(detail, text="", style="CardTitle.TLabel")
        self.skin_title.pack(anchor="w", pady=(12, 0))
        self.skin_meta = ttk.Label(detail, text="", style="CardMuted.TLabel", wraplength=self.PREVIEW[0])
        self.skin_meta.pack(anchor="w", pady=(2, 6))
        self.skin_desc = ttk.Label(detail, text="", style="Card.TLabel", wraplength=self.PREVIEW[0], justify="left")
        self.skin_desc.pack(anchor="w")
        acts = ttk.Frame(detail, style="Card.TFrame")
        acts.configure(borderwidth=0)
        acts.pack(fill="x", pady=(14, 6))
        self.apply_btn = ttk.Button(acts, text="应用此材质包", style="Accent.TButton", command=self.use_selected)
        self.apply_btn.pack(side="left")
        self.tip(self.apply_btn, "双击卡片也可以直接应用")
        off = ttk.Button(acts, text="关闭皮肤", command=self.skin_off)
        off.pack(side="left", padx=8)
        self._task_buttons += [self.apply_btn, off]
        self.ide_var = tk.BooleanVar(value=True)
        cb = ttk.Checkbutton(detail, text="同时应用到 Antigravity IDE 编辑器", variable=self.ide_var,
                             style="Card.TCheckbutton")
        cb.pack(anchor="w", pady=(4, 0))
        self.tip(cb, "修改 IDE 工作台样式并自动修正校验和；IDE 需“重新加载窗口”或重启后生效")
        ttk.Label(detail, style="CardMuted.TLabel", wraplength=self.PREVIEW[0], justify="left",
                  text="切换后在已打补丁的Agent桌面端中实时生效。").pack(anchor="w", pady=(8, 0))
        more = ttk.Frame(detail, style="Card.TFrame")
        more.configure(borderwidth=0)
        more.pack(side="bottom", fill="x")
        ttk.Separator(detail).pack(side="bottom", fill="x", pady=10)
        for text, cmd, tip, style in (("导出", self.export_zip, "导出为 .zip（包含你的个人调整）", "Small.TButton"),
                                      ("复制为新包", self.clone_pack, "以此包为模板创建一个新材质包", "Small.TButton"),
                                      ("删除", self.delete_pack, "删除该材质包及其个人设置", "SmallDanger.TButton")):
            b = ttk.Button(more, text=text, command=cmd, style=style)
            b.pack(side="left", padx=(0, 6))
            self.tip(b, tip)
            self._task_buttons.append(b)

        # 左侧画廊
        left = ttk.Frame(f)
        left.pack(side="left", fill="both", expand=True)
        bar = ttk.Frame(left)
        bar.pack(fill="x", pady=(0, 10))
        self.gallery_count = ttk.Label(bar, text="", style="Muted.TLabel")
        self.gallery_count.pack(side="left")
        b = ttk.Button(bar, text="打开文件夹", command=lambda: self.open_path(sm.skins_dir()))
        b.pack(side="right")
        self.tip(b, "打开材质包文件夹")
        b = ttk.Button(bar, text="＋ 导入 .zip", command=self.import_zip)
        b.pack(side="right", padx=6)
        self._task_buttons.append(b)
        self.gallery = self.ui.ScrollFrame(left, self.theme)
        self.gallery.outer.pack(fill="both", expand=True)
        self._gallery_cols = 0
        self.gallery.canvas.bind("<Configure>", self._on_gallery_resize, add="+")
        self._regrid = self.ui.Debouncer(self.root, 60, self._grid_cards)

    def _on_gallery_resize(self, e):
        cols = max(1, (e.width + 12) // (self.THUMB[0] + 30))
        if cols != self._gallery_cols:
            self._gallery_cols = cols
            self._regrid()

    def _render_gallery(self, force: bool = False):
        if not self._built.get(0):
            return
        sig = [(s["id"], s["name"], s["active"], s.get("preview"), s["version"]) for s in self.skins]
        if not force and sig == getattr(self, "_gallery_sig", None):
            self._highlight_cards()
            return
        self._gallery_sig = sig
        for card in self._cards.values():
            card["frame"].destroy()
        self._cards = {}
        for info in self.skins:
            self._cards[info["id"]] = self._make_card(info)
        n = len(self.skins)
        self.gallery_count.configure(text=f"共 {n} 个材质包 · 单击查看，双击应用")
        self._grid_cards()
        self._highlight_cards()

    def _make_card(self, info: dict) -> dict:
        tk, ttk = self.tk, self.ttk
        w, h = self.THUMB
        frame = ttk.Frame(self.gallery.body, style="Card.TFrame", padding=8)
        cv = tk.Canvas(frame, width=w, height=h, highlightthickness=0, borderwidth=0,
                       background=self.theme.c["surface2"])
        cv.pack()
        name = ttk.Label(frame, text=info["name"], style="Card.TLabel", font=self.theme.font(10, "bold"))
        name.pack(anchor="w", pady=(8, 0))
        tags = []
        if info["active"]:
            tags.append("● 当前使用")
        tags.append("浅色" if info["base"] == "light" else "暗色")
        if info["builtin"]:
            tags.append("内置")
        meta = ttk.Label(frame, text=" · ".join(tags), style="CardMuted.TLabel")
        meta.pack(anchor="w")
        card = {"frame": frame, "canvas": cv, "name": name, "meta": meta, "id": info["id"]}
        for wdg in (frame, cv, name, meta):
            wdg.bind("<Button-1>", lambda e, sid=info["id"]: self.select_skin(sid))
            wdg.bind("<Double-Button-1>", lambda e, sid=info["id"]: (self.select_skin(sid), self.use_selected()))
        self._paint_preview(cv, info, w, h)
        return card

    def _grid_cards(self):
        cols = max(1, self._gallery_cols or 2)
        for i, info in enumerate(self.skins):
            card = self._cards.get(info["id"])
            if card:
                card["frame"].grid(row=i // cols, column=i % cols, padx=(0, 12), pady=(0, 12), sticky="nw")

    def _highlight_cards(self):
        for sid, card in self._cards.items():
            sel = sid == self.selected_id
            card["frame"].configure(style="CardSel.TFrame" if sel else "Card.TFrame")
            card["name"].configure(style="CardSel.TLabel" if sel else "Card.TLabel")
            card["meta"].configure(style="CardSelMuted.TLabel" if sel else "CardMuted.TLabel")
            card["canvas"].configure(background=self.theme.c["surface2"])

    def _paint_preview(self, canvas, info: dict, w: int, h: int):
        """先画配色示意（同步、极快），有预览图时后台解码缩放后再覆盖上去。"""
        canvas.delete("all")
        self.draw_palette(info.get("colors") or {}, canvas, w, h)
        token = (info["id"], w, h)
        canvas._agzh_token = token

        def got(img):
            if img is None or not self.ui._alive(canvas) or getattr(canvas, "_agzh_token", None) != token:
                return
            canvas.delete("all")
            canvas.create_image(w // 2, h // 2, image=img)
            canvas._agzh_img = img

        self.images.get(info.get("preview"), w, h, got)
        self._kick()

    def draw_palette(self, colors: dict, c=None, W: int | None = None, H: int | None = None):
        """没有预览图时按配色画一个示意工作台（按尺寸等比缩放）。"""
        c = c or self.preview
        W = W or self.PREVIEW[0]
        H = H or self.PREVIEW[1]
        sx, sy = W / 360, H / 220

        def col(k, d):
            v = colors.get(k) or d
            ok = isinstance(v, str) and v.startswith("#") and len(v) in (4, 7, 9)
            return v[:7] if ok else d

        def R(x0, y0, x1, y1, fill):
            c.create_rectangle(x0 * sx, y0 * sy, x1 * sx, y1 * sy, fill=fill, outline="")

        bg, fg, ac = col("background", "#1e1e1e"), col("foreground", "#d4d4d4"), col("accent", "#3794ff")
        R(0, 0, 360, 220, bg)
        R(0, 0, 360, 18, col("titleBar", "#333333"))
        R(0, 18, 26, 206, col("activityBar", "#333333"))
        R(26, 18, 110, 206, col("sidebar", "#252526"))
        for i in range(9):
            R(124, 30 + i * 18, 124 + 60 + (i * 37) % 160, 36 + i * 18, ac if i % 3 == 0 else fg)
        R(0, 206, 360, 220, col("statusBar", ac))

    def select_skin(self, sid: str | None):
        self.selected_id = sid
        self._highlight_cards()
        self.show_skin_detail()
        if self._built.get(1) and not self.global_var.get():
            self.load_custom_form(only_if_scope_changed=True)

    def select_skin_index(self, i: int):
        if self.skins:
            self.select_skin(self.skins[i % len(self.skins)]["id"])

    def selected_skin_id(self):
        ids = [s["id"] for s in self.skins]
        return self.selected_id if self.selected_id in ids else None

    def selected_info(self):
        sid = self.selected_skin_id()
        return next((s for s in self.skins if s["id"] == sid), None)

    def show_skin_detail(self):
        if not self._built.get(0):
            return
        info = self.selected_info()
        if not info:
            self.preview.delete("all")
            self.skin_title.configure(text="（暂无材质包）")
            self.skin_meta.configure(text="")
            self.skin_desc.configure(text="点击“导入 .zip”添加材质包，或在“自定义”页微调。")
            return
        self.skin_title.configure(text=info["name"] + ("   · 当前使用" if info["active"] else ""))
        self.skin_meta.configure(text=f"{info['id']}  ·  v{info['version']}  ·  {info['author'] or '未知作者'}"
                                      f"  ·  {'浅色' if info['base'] == 'light' else '暗色'}"
                                      f"{'  ·  内置' if info['builtin'] else ''}")
        self.skin_desc.configure(text=info["description"] or "（无描述）")
        self._paint_preview(self.preview, info, *self.PREVIEW)

    def use_selected(self):
        sid = self.selected_skin_id()
        if not sid:
            return

        def done(r, e):
            if r and isinstance(r, dict) and r.get("ide"):
                self.write_log(f"IDE 状态: {STATUS_TEXT.get(r['ide'], r['ide'])}")

        self.run_task(f"切换材质包 {sid}", core.use_skin, sid, apply_ide=self.ide_var.get(), on_done=done)

    def skin_off(self):
        self.run_task("关闭皮肤", core.skin_off)

    def import_zip(self):
        from tkinter import filedialog
        p = filedialog.askopenfilename(title="选择材质包 .zip", filetypes=[("材质包", "*.zip")], parent=self.root)
        if not p:
            return

        def do():
            try:
                pack = sm.import_pack(Path(p))
            except sm.SkinError as e:
                if "已存在同 id" in str(e):
                    return ("exists", str(e))
                raise
            return ("ok", pack.id)

        def done(r, e):
            if r and r[0] == "ok":
                self.selected_id = r[1]
            if r and r[0] == "exists" and self.ask("覆盖导入", r[1] + "\n\n是否覆盖已有材质包？"):
                self.root.after(0, lambda: self.run_task("覆盖导入材质包", sm.import_pack, Path(p), True))

        self.run_task("导入材质包", do, on_done=done)

    def export_zip(self):
        from tkinter import filedialog
        sid = self.selected_skin_id()
        if not sid:
            return
        p = filedialog.asksaveasfilename(title="导出材质包", defaultextension=".zip", initialfile=f"{sid}.zip",
                                         filetypes=[("材质包", "*.zip")], parent=self.root)
        if p:
            self.run_task("导出材质包", sm.export_pack, sid, Path(p), True)

    def clone_pack(self):
        from tkinter import simpledialog
        sid = self.selected_skin_id()
        if not sid:
            return
        new_id = simpledialog.askstring("复制为新包", "新材质包 id（小写字母/数字/短横线）：", parent=self.root)
        if not new_id:
            return
        name = simpledialog.askstring("复制为新包", "显示名称：", parent=self.root) or new_id

        def done(r, e):
            if r is not None and e is None:
                self.selected_id = new_id.strip()

        self.run_task("复制材质包", sm.create_pack_from, sid, new_id.strip(), name.strip(), on_done=done)

    def delete_pack(self):
        sid = self.selected_skin_id()
        if sid and self.ask("删除材质包", f"确定删除材质包 {sid} 及其个人覆盖设置吗？"):
            self.run_task("删除材质包", sm.remove_pack, sid)

    # ================================================================ 自定义页
    def _build_custom(self):
        tk, ttk = self.tk, self.ttk
        f = self.tab_custom
        top = ttk.Frame(f)
        top.pack(fill="x", pady=(0, 10))
        self.custom_title = ttk.Label(top, text="", style="Title.TLabel", font=self.theme.font(12, "bold"))
        self.custom_title.pack(side="left")
        self.global_var = tk.BooleanVar(value=False)
        g = ttk.Checkbutton(top, text="作为全局设置", variable=self.global_var, command=self.load_custom_form)
        g.pack(side="left", padx=14)
        self.tip(g, "勾选后作用于所有材质包；不勾选则只作用于当前选中的材质包")
        save = ttk.Button(top, text="保存并应用", style="Accent.TButton", command=self.save_custom)
        save.pack(side="right")
        reset = ttk.Button(top, text="恢复材质包默认", command=self.reset_custom)
        reset.pack(side="right", padx=8)
        self._task_buttons += [save, reset]

        # 右侧：实时预览
        side = ttk.Frame(f, style="Card.TFrame", padding=14)
        side.pack(side="right", fill="y", padx=(14, 0))
        ttk.Label(side, text="实时预览", style="CardH.TLabel").pack(anchor="w")
        ttk.Label(side, text="修改配色、字体与桌宠强调色时即时更新", style="CardMuted.TLabel").pack(anchor="w",
                                                                                     pady=(0, 8))
        self.live = tk.Canvas(side, width=270, height=176, highlightthickness=0, borderwidth=0)
        self.theme.register(self.live, lambda c: self.live.configure(background=c["surface2"]))
        self.live.pack()
        self.live_note = ttk.Label(side, text="", style="CardMuted.TLabel", wraplength=270, justify="left")
        self.live_note.pack(anchor="w", pady=(8, 0))

        sf = self.ui.ScrollFrame(f, self.theme)
        sf.outer.pack(side="left", fill="both", expand=True)
        body = sf.body
        F = self.form
        self._preview_debounce = self.ui.Debouncer(self.root, 120, self._update_custom_preview)

        def section(title, row):
            lf = ttk.Frame(body, style="Card.TFrame", padding=(14, 10, 14, 12))
            lf.grid(row=row, column=0, sticky="ew", pady=(0, 10), padx=(0, 6))
            ttk.Label(lf, text=title, style="CardH.TLabel").grid(row=0, column=0, columnspan=8, sticky="w",
                                                                pady=(0, 6))
            return lf

        body.columnconfigure(0, weight=1)
        L = lambda parent, text, r, c=0: ttk.Label(parent, text=text, style="Card.TLabel").grid(  # noqa: E731
            row=r, column=c, sticky="w", padx=(0, 8), pady=3)

        # 颜色
        cf = section("配色  ·  留空 = 使用材质包默认", 0)
        self._swatches = {}
        for i, (key, label) in enumerate(COLOR_LABELS.items()):
            r, c = divmod(i, 2)
            r += 1
            L(cf, label, r, c * 4)
            var = tk.StringVar()
            ttk.Entry(cf, textvariable=var, width=10).grid(row=r, column=c * 4 + 1, pady=2)
            sw = tk.Label(cf, width=3, relief="flat", borderwidth=0, cursor="hand2")
            sw.grid(row=r, column=c * 4 + 2, padx=(4, 18), sticky="ns", pady=3)
            sw.bind("<Button-1>", lambda e, v=var: self.pick_color(v))
            self.tip(sw, "点击打开取色器")
            self._swatches[key] = sw
            F[f"colors.{key}"] = var
            var.trace_add("write", self._preview_debounce)

        # 背景
        bf = section("背景图  ·  作用于材质包的主背景", 1)
        F["bg.image"] = tk.StringVar()
        L(bf, "图片", 1)
        ttk.Entry(bf, textvariable=F["bg.image"], width=24).grid(row=1, column=1, columnspan=3, sticky="ew")
        ttk.Button(bf, text="选择…", command=lambda: self.pick_file(F["bg.image"], "image")).grid(row=1, column=4,
                                                                                               padx=6)
        F["bg.target"] = tk.StringVar()
        L(bf, "位置", 2)
        ttk.Combobox(bf, textvariable=F["bg.target"], values=list(TARGET_LABELS.values()), width=12,
                     state="readonly").grid(row=2, column=1, sticky="w")
        F["bg.position"] = tk.StringVar()
        L(bf, "对齐", 2, 2)
        ttk.Combobox(bf, textvariable=F["bg.position"], width=12,
                     values=["center", "top", "bottom", "left", "right", "right bottom", "left bottom", "top right"]
                     ).grid(row=2, column=3, sticky="w")
        F["bg.size"] = tk.StringVar()
        L(bf, "缩放", 3)
        ttk.Combobox(bf, textvariable=F["bg.size"], values=["cover", "contain", "auto", "160px"], width=12).grid(
            row=3, column=1, sticky="w")
        F["bg.opacity"] = tk.DoubleVar(value=0.15)
        F["bg.blur"] = tk.DoubleVar(value=0)
        self._scale_labels = {}
        for r, (key, label, hi, fmt) in enumerate((("bg.opacity", "不透明度", 1, "{:.2f}"),
                                                   ("bg.blur", "模糊 (px)", 40, "{:.0f}")), start=4):
            L(bf, label, r)
            ttk.Scale(bf, from_=0, to=hi, variable=F[key], length=200).grid(row=r, column=1, columnspan=2, sticky="w")
            lab = ttk.Label(bf, text="", style="Card.TLabel", width=6)
            lab.grid(row=r, column=3, sticky="w", padx=8)
            self._scale_labels[key] = (lab, fmt)
            F[key].trace_add("write", lambda *_a, k=key: self._update_scale_label(k))

        # 字体
        ff = section("字体", 2)
        self._font_boxes = []
        for r, (key, label) in enumerate((("font.family", "界面字体"), ("font.monoFamily", "代码字体")), start=1):
            F[key] = tk.StringVar()
            L(ff, label, r)
            cb = ttk.Combobox(ff, textvariable=F[key], width=32, postcommand=lambda: self._fill_fonts())
            cb.grid(row=r, column=1, columnspan=3, sticky="w", pady=2)
            self._font_boxes.append(cb)
            F[key].trace_add("write", self._preview_debounce)
        F["font.size"] = tk.StringVar()
        F["font.monoSize"] = tk.StringVar()
        L(ff, "界面字号", 3)
        ttk.Spinbox(ff, from_=8, to=40, textvariable=F["font.size"], width=6).grid(row=3, column=1, sticky="w")
        L(ff, "代码字号", 3, 2)
        ttk.Spinbox(ff, from_=8, to=40, textvariable=F["font.monoSize"], width=6).grid(row=3, column=3, sticky="w")

        # 图标
        icf = section("图标", 3)
        F["icons.filter"] = tk.StringVar()
        F["icons.color"] = tk.StringVar()
        L(icf, "滤镜", 1)
        ttk.Combobox(icf, textvariable=F["icons.filter"], width=34,
                     values=["", "hue-rotate(300deg) saturate(1.3)", "grayscale(1)", "saturate(1.5)", "sepia(0.6)"]
                     ).grid(row=1, column=1, sticky="w")
        L(icf, "颜色", 2)
        ttk.Entry(icf, textvariable=F["icons.color"], width=12).grid(row=2, column=1, sticky="w")
        ttk.Label(icf, style="CardMuted.TLabel", text="单个图标替换（codicons 映射）请在 skin.json 中配置，见 docs/skins.md"
                  ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(4, 0))

        # 桌宠
        pf = section("桌宠外观", 4)
        F["pet.character"] = tk.StringVar()
        L(pf, "角色", 1)
        ttk.Combobox(pf, textvariable=F["pet.character"], values=["", "nezuko", "prince", "auto"], width=10,
                     state="readonly").grid(row=1, column=1, sticky="w")
        F["pet.sprite"] = tk.StringVar()
        L(pf, "自定义形象图", 2)
        ttk.Entry(pf, textvariable=F["pet.sprite"], width=30).grid(row=2, column=1, columnspan=2, sticky="w")
        ttk.Button(pf, text="选择…", command=lambda: self.pick_file(F["pet.sprite"], "image")).grid(row=2, column=3,
                                                                                                 padx=6)
        F["pet.filter"] = tk.StringVar()
        L(pf, "滤镜", 3)
        ttk.Combobox(pf, textvariable=F["pet.filter"], width=34,
                     values=["", "hue-rotate(180deg)", "saturate(1.4)", "grayscale(1)", "brightness(1.1)"]
                     ).grid(row=3, column=1, columnspan=2, sticky="w")
        F["pet.accent"] = tk.StringVar()
        L(pf, "面板强调色", 4)
        ttk.Entry(pf, textvariable=F["pet.accent"], width=12).grid(row=4, column=1, sticky="w")
        F["pet.accent"].trace_add("write", self._preview_debounce)
        F["pet.scale"] = tk.StringVar()
        L(pf, "默认缩放", 5)
        ttk.Spinbox(pf, from_=0.3, to=3.0, increment=0.1, textvariable=F["pet.scale"], width=6).grid(
            row=5, column=1, sticky="w")
        F["pet.hidden"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(pf, text="隐藏 Agent 窗口内桌宠", variable=F["pet.hidden"], style="Card.TCheckbutton").grid(
            row=6, column=1, columnspan=2, sticky="w", pady=(4, 0))

        # 自定义 CSS
        xf = section("追加自定义 CSS  ·  附加在材质包样式之后", 5)
        self.css_text = tk.Text(xf, height=6, width=50, font=self.theme.mono(9), relief="flat", borderwidth=0,
                                padx=8, pady=6, undo=True)
        self.theme.register(self.css_text, lambda c: self.css_text.configure(
            background=c["input"], foreground=c["text"], insertbackground=c["text"], highlightthickness=1,
            highlightbackground=c["border"], highlightcolor=c["accent"], selectbackground=c["accent"],
            selectforeground=c["accent_fg"]))
        self.css_text.grid(row=1, column=0, columnspan=8, sticky="ew")
        xf.columnconfigure(0, weight=1)

    def _fill_fonts(self):
        """字体列表在第一次展开下拉框时才枚举（Windows 上枚举上千种字体较慢）。"""
        if self._families is None:
            import tkinter.font as tkfont
            try:
                self._families = sorted({f for f in tkfont.families(self.root) if not f.startswith("@")})
            except Exception:
                self._families = []
        for cb in self._font_boxes:
            cb.configure(values=self._families)

    def _update_scale_label(self, key):
        lab, fmt = self._scale_labels[key]
        try:
            lab.configure(text=fmt.format(float(self.form[key].get())))
        except Exception:
            pass

    def _valid_color(self, v: str) -> str | None:
        v = (v or "").strip()
        if not v:
            return None
        try:
            self.root.winfo_rgb(v[:7] if v.startswith("#") and len(v) == 9 else v)
            return v[:7] if v.startswith("#") and len(v) == 9 else v
        except Exception:
            return None

    def _update_custom_preview(self):
        """把材质包配色叠加表单中的修改，画一个迷你工作台（防抖后执行）。"""
        if not self._built.get(1):
            return
        c = self.theme.c
        scope = self.custom_scope()
        base = dict(next((s.get("colors") or {} for s in self.skins if s["id"] == scope), {}))
        for key in COLOR_LABELS:
            v = self._valid_color(self.form[f"colors.{key}"].get())
            sw = self._swatches[key]
            sw.configure(background=v or c["surface2"], text="" if v else "—", foreground=c["muted"])
            if v:
                base[key] = v
        cv = self.live
        cv.delete("all")
        W, H = 270, 176
        cols = {k: (self._valid_color(base.get(k, "")) or d) for k, d in (
            ("background", "#1e1e1e"), ("foreground", "#d4d4d4"), ("accent", "#3794ff"), ("titleBar", "#333333"),
            ("activityBar", "#2c2c2c"), ("sidebar", "#252526"), ("statusBar", ""), ("panel", "#1a1a1a"),
            ("border", "#3c3c3c"), ("selection", "#264f78"), ("muted", "#8b8b8b"))}
        cols["statusBar"] = cols["statusBar"] or cols["accent"]
        cv.create_rectangle(0, 0, W, H, fill=cols["background"], outline="")
        cv.create_rectangle(0, 0, W, 16, fill=cols["titleBar"], outline="")
        for i, dot in enumerate(("#ff5f57", "#febc2e", "#28c840")):
            cv.create_oval(6 + i * 11, 5, 13 + i * 11, 12, fill=dot, outline="")
        cv.create_rectangle(0, 16, 22, H - 14, fill=cols["activityBar"], outline="")
        cv.create_rectangle(22, 16, 92, H - 14, fill=cols["sidebar"], outline="")
        cv.create_line(92, 16, 92, H - 14, fill=cols["border"])
        for i in range(5):
            cv.create_rectangle(6, 26 + i * 18, 16, 36 + i * 18, fill=cols["accent"] if i == 0 else cols["muted"],
                                outline="")
            cv.create_rectangle(30, 28 + i * 14, 30 + 30 + (i * 13) % 28, 32 + i * 14, fill=cols["muted"], outline="")
        cv.create_rectangle(98, 46, W - 8, 58, fill=cols["selection"], outline="")
        fam = (self.form["font.monoFamily"].get().strip() or self.form["font.family"].get().strip()
               or self.theme.mono_family)
        try:
            cv.create_text(102, 28, anchor="w", text="const 你好 = 'Antigravity';", fill=cols["foreground"],
                           font=(fam, 9))
            cv.create_text(102, 52, anchor="w", text="if (skin.ok) apply();", fill=cols["foreground"], font=(fam, 9))
        except Exception:
            pass
        for i in range(4):
            cv.create_rectangle(102, 70 + i * 12, 102 + 40 + (i * 29) % 90, 74 + i * 12,
                                fill=cols["accent"] if i % 2 == 0 else cols["foreground"], outline="")
        cv.create_rectangle(92, 128, W, H - 14, fill=cols["panel"], outline="")
        cv.create_line(92, 128, W, 128, fill=cols["border"])
        cv.create_text(100, 140, anchor="w", text="终端 ›  agzh skin use", fill=cols["muted"], font=(fam, 8))
        cv.create_rectangle(0, H - 14, W, H, fill=cols["statusBar"], outline="")
        pet = self._valid_color(self.form["pet.accent"].get()) or cols["accent"]
        cv.create_oval(W - 40, 140, W - 14, 166, fill=pet, outline="")
        cv.create_text(W - 27, 153, text="❀", font=self.theme.font(9))
        op = self.form["bg.opacity"].get()
        img = self.form["bg.image"].get().strip()
        self.live_note.configure(text=(f"背景图：{Path(img).name}（不透明度 {op:.2f}）" if img else "背景图：使用材质包默认")
                                 + "。保存后在 Antigravity 中实时生效。")

    def pick_color(self, var):
        from tkinter import colorchooser
        init = var.get()[:7] if var.get().startswith("#") else None
        c = colorchooser.askcolor(color=init, parent=self.root)
        if c and c[1]:
            var.set(c[1])

    def pick_file(self, var, kind):
        from tkinter import filedialog
        types = [("图片", "*.png *.jpg *.jpeg *.webp *.gif *.svg")] if kind == "image" else [("所有文件", "*.*")]
        p = filedialog.askopenfilename(filetypes=types, parent=self.root)
        if p:
            var.set(p)

    def custom_scope(self):
        if self._built.get(1) and self.global_var.get():
            return None
        return self.selected_skin_id() or sm.load_state().get("active_skin")

    def load_custom_form(self, only_if_scope_changed: bool = False):
        """后台读取覆盖层，读完在主线程填表。"""
        if not self._built.get(1) or not self.form:
            return
        scope = self.custom_scope()
        if only_if_scope_changed and scope == self._custom_loaded_scope:
            return
        self._custom_loaded_scope = scope
        self.custom_title.configure(text="全局覆盖层" if scope is None else f"自定义：{scope}")

        def done(data, err, tb):
            if err is not None:
                self.write_log(tb)
                return
            if data["scope"] != self.custom_scope():
                return  # 用户已切换到别的材质包，丢弃过期结果
            self._fill_custom_form(data)

        self.run_io(load_custom_data, scope, on_done=done)

    def _fill_custom_form(self, data: dict):
        F = self.form
        ov, base_bg = data["override"], data["base_bg"]
        for k, var in F.items():
            if isinstance(var, self.tk.BooleanVar):
                var.set(False)
            elif isinstance(var, self.tk.DoubleVar):
                var.set(0.15 if k == "bg.opacity" else 0)
            else:
                var.set("")
        for key, val in (ov.get("colors") or {}).items():
            if f"colors.{key}" in F and val:
                F[f"colors.{key}"].set(val)
        bg = ov.get("background")
        bg = bg[0] if isinstance(bg, list) and bg else (bg if isinstance(bg, dict) else {})
        F["bg.image"].set(bg.get("image", ""))
        F["bg.target"].set(TARGET_LABELS.get(bg.get("target") or base_bg.get("target") or "window", "整个窗口"))
        F["bg.position"].set(bg.get("position", base_bg.get("position", "")))
        F["bg.size"].set(bg.get("size", base_bg.get("size", "")))
        F["bg.opacity"].set(round(float(bg.get("opacity", base_bg.get("opacity", 0.15))), 2))
        F["bg.blur"].set(round(float(bg.get("blur", base_bg.get("blur", 0))), 1))
        for sect in ("font", "icons", "pet"):
            for key, val in (ov.get(sect) or {}).items():
                k = f"{sect}.{key}"
                if k in F and val is not None:
                    F[k].set(val)
        self.css_text.delete("1.0", "end")
        self.css_text.insert("1.0", ov.get("css", ""))
        self._loaded_bg = (F["bg.opacity"].get(), F["bg.blur"].get(), F["bg.target"].get(),
                           F["bg.position"].get(), F["bg.size"].get())
        self._update_custom_preview()

    def collect_form(self) -> dict:
        """主线程：只读取控件值（纯数据），不做任何文件操作。"""
        F = self.form
        raw = {"colors": {k.split(".", 1)[1]: v.get() for k, v in F.items() if k.startswith("colors.")},
               "bg": {"image": F["bg.image"].get(), "opacity": F["bg.opacity"].get(), "blur": F["bg.blur"].get(),
                      "target": F["bg.target"].get(), "position": F["bg.position"].get(), "size": F["bg.size"].get()},
               "css": self.css_text.get("1.0", "end"), "loaded_bg": self._loaded_bg}
        for sect in ("font", "icons", "pet"):
            raw[sect] = {k.split(".", 1)[1]: v.get() for k, v in F.items() if k.startswith(sect + ".")}
        return raw

    def collect_override(self) -> dict:
        return build_override(self.collect_form())

    def save_custom(self):
        raw = self.collect_form()
        scope = self.custom_scope()

        def do():
            return core.save_customization(scope, build_override(raw))

        self.run_task("保存自定义设置", do)

    def reset_custom(self):
        scope = self.custom_scope()
        if self.ask("恢复默认", "清除当前的个人覆盖设置，恢复为材质包原样？"):
            def do():
                sm.reset_override(scope)
                st = sm.load_state()
                if st.get("active_skin") and st.get("skin_enabled", True):
                    core.use_skin(st["active_skin"])

            def done(r, e):
                self._custom_loaded_scope = "<none>"
                self.load_custom_form()

            self.run_task("恢复材质包默认", do, on_done=done)

    # ================================================================ 汉化页
    def _card(self, parent, title: str, sub: str | None = None, **pack):
        ttk = self.ttk
        card = ttk.Frame(parent, style="Card.TFrame", padding=(18, 14, 18, 16))
        card.pack(fill="x", pady=(0, 12), **pack)
        ttk.Label(card, text=title, style="CardH.TLabel").pack(anchor="w")
        if sub:
            ttk.Label(card, text=sub, style="CardMuted.TLabel", wraplength=640, justify="left").pack(anchor="w",
                                                                                                  pady=(2, 8))
        return card

    def _build_l10n(self):
        tk, ttk = self.tk, self.ttk
        f = self.tab_l10n
        st = self._card(f, "当前状态")
        self.l10n_status = ttk.Label(st, text="检测中…", style="CardMuted.TLabel")
        self.l10n_status.pack(anchor="w")
        self.l10n_detail = ttk.Label(st, text="", style="CardMuted.TLabel")
        self.l10n_detail.pack(anchor="w", pady=(2, 0))

        opt = self._card(f, "安装选项")
        grid = ttk.Frame(opt, style="Card.TFrame")
        grid.configure(borderwidth=0)
        grid.pack(fill="x")
        self.dir_var = tk.StringVar()
        ttk.Label(grid, text="安装目录", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Entry(grid, textvariable=self.dir_var, width=58).grid(row=0, column=1, sticky="ew")
        ttk.Button(grid, text="浏览…", command=self.pick_dir).grid(row=0, column=2, padx=6)
        self.lang_var = tk.StringVar(value="zh-CN")
        ttk.Label(grid, text="语言", style="Card.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Combobox(grid, textvariable=self.lang_var, values=["zh-CN", "zh-TW", "zh-HK"], width=10,
                     state="readonly").grid(row=1, column=1, sticky="w")
        self.char_var = tk.StringVar(value="(沿用上次)")
        ttk.Label(grid, text="启动动画角色", style="Card.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Combobox(grid, textvariable=self.char_var, width=14, state="readonly",
                     values=["(沿用上次)", "tanjiro", "zenitsu", "inosuke", "nezuko", "all"]).grid(row=2, column=1,
                                                                                               sticky="w")
        self.pet_var = tk.BooleanVar(value=True)
        self.skinload_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(grid, text="挂载窗口内桌宠", variable=self.pet_var, style="Card.TCheckbutton").grid(
            row=3, column=1, sticky="w", pady=(6, 0))
        ttk.Checkbutton(grid, text="注入材质包加载器（切换皮肤实时生效）", variable=self.skinload_var,
                        style="Card.TCheckbutton").grid(row=4, column=1, sticky="w")
        grid.columnconfigure(1, weight=1)

        act = self._card(f, "操作", "安装时会关闭正在运行的 Antigravity 以释放 app.asar；首次安装会自动创建 app.asar.bak 原版备份。"
                                   "macOS 打补丁后会自动进行本机 ad-hoc 重签名。IDE 编辑器界面汉化请使用官方中文语言包（见 README）。")
        bar = ttk.Frame(act, style="Card.TFrame")
        bar.configure(borderwidth=0)
        bar.pack(anchor="w")
        b1 = ttk.Button(bar, text="安装 / 重新应用汉化", style="Accent.TButton", command=self.install_l10n)
        b1.pack(side="left")
        b2 = ttk.Button(bar, text="还原官方原版", command=self.restore_l10n)
        b2.pack(side="left", padx=8)
        b3 = ttk.Button(bar, text="禁止官方自动更新", command=lambda: self.toggle_updates(True))
        b3.pack(side="left")
        b4 = ttk.Button(bar, text="恢复官方自动更新", command=lambda: self.toggle_updates(False))
        b4.pack(side="left", padx=8)
        self.tip(b3, "防止官方静默更新覆盖汉化；开启“自动维护”后一般无需禁止")
        self._task_buttons += [b1, b2, b3, b4]

    def pick_dir(self):
        from tkinter import filedialog
        p = filedialog.askdirectory(parent=self.root)
        if p:
            self.dir_var.set(p)

    def _with_install_dir(self, then):
        """后台检测安装目录（可能读注册表/扫描磁盘），然后在主线程继续。"""
        explicit = self.dir_var.get().strip() or None

        def done(d, err, tb):
            if err is not None or not d:
                self.msg("未找到", "未检测到 Antigravity 安装目录，请手动选择。", error=True)
                return
            then(d)

        self.run_io(core.detect_install_dir, explicit, on_done=done)

    def install_l10n(self):
        ch = self.char_var.get()
        args = (self.lang_var.get(), None if ch.startswith("(") else ch, self.pet_var.get(), self.skinload_var.get())

        def with_dir(d):
            # 进程检测（Windows tasklist 约数百毫秒）同样放到后台
            def running_done(running, err, tb):
                if running and not self.ask("需要关闭 Antigravity", "Antigravity 正在运行，安装时会将其关闭。继续吗？"):
                    return
                self.run_task("安装汉化补丁", core.install_localization, d, *args)

            self.run_io(ar.is_antigravity_running, on_done=running_done)

        self._with_install_dir(with_dir)

    def restore_l10n(self):
        def with_dir(d):
            if self.ask("还原原版", "将恢复官方原版 app.asar 并移除 IDE 皮肤，且不再自动重新注入。继续吗？"):
                self.run_task("还原官方原版", core.restore_localization, d)

        self._with_install_dir(with_dir)

    def toggle_updates(self, disable):
        self._with_install_dir(lambda d: self.run_task("禁止自动更新" if disable else "恢复自动更新",
                                                      core.toggle_updates, d, disable))

    # ================================================================ 桌宠页
    def _build_pet(self):
        ttk = self.ttk
        f = self.tab_pet
        card = self._card(f, "独立桌面桌宠",
                          "在 Windows 桌面上启动透明悬浮的祢豆子 / 小王子桌宠（托盘可管理）。"
                          "桌宠外观（角色、滤镜、强调色、自定义形象图、默认缩放）跟随当前材质包，"
                          "可在“自定义 → 桌宠外观”中单独调整。")
        bar = ttk.Frame(card, style="Card.TFrame")
        bar.configure(borderwidth=0)
        bar.pack(anchor="w", pady=(4, 0))
        self.pet_btn = ttk.Button(bar, text="启动桌面桌宠", style="Accent.TButton", command=self.launch_pet)
        self.pet_btn.pack(side="left")
        ttk.Button(bar, text="调整桌宠外观…", command=lambda: self.select_tab(1)).pack(side="left", padx=8)
        if sys.platform != "win32":
            self.pet_btn.state(["disabled"])
            ttk.Label(card, style="CardMuted.TLabel",
                      text="当前系统不支持独立桌面桌宠，Antigravity 窗口内桌宠仍可使用。").pack(anchor="w", pady=(10, 0))
        tips = self._card(f, "小提示")
        for t in ("按住角色拖动 · 单击互动 · 双击打开看板", "滚轮切歌，Ctrl + 滚轮缩放桌宠",
                  "托盘图标可切换角色、置顶与退出"):
            ttk.Label(tips, text="•  " + t, style="Card.TLabel").pack(anchor="w", pady=1)

    def launch_pet(self):
        def done(r, err, tb):
            if err is not None:
                self.msg("无法启动桌宠", str(err), error=True)
            else:
                self.write_log("✔ 桌宠已启动")
                self.toast("桌宠已启动，可在系统托盘中管理", "ok")

        self.run_io(core.launch_pet, on_done=done)

    # ================================================================ 自动维护页
    def _build_auto(self):
        tk, ttk = self.tk, self.ttk
        f = self.tab_auto
        card = self._card(f, "更新后自动重新注入",
                          "开启后会添加一个当前用户级的开机自启项（Windows 注册表 Run / macOS LaunchAgent / Linux autostart），"
                          "在后台低频检测：一旦发现 Antigravity 被官方更新覆盖，会等更新写完、Antigravity 退出后自动重新打上汉化补丁、"
                          "重新注入材质包加载器并同步 IDE 皮肤。不会强行关闭正在使用的 Antigravity。")
        self.auto_var = tk.BooleanVar(value=False)
        cb = ttk.Checkbutton(card, text="开机自动检测并在更新后重新注入", variable=self.auto_var,
                             style="Card.TCheckbutton", command=self.toggle_auto)
        cb.pack(anchor="w", pady=(2, 8))
        b = ttk.Button(card, text="立即检测并修复", command=self.check_now)
        b.pack(anchor="w")
        self._task_buttons += [cb, b]

        st = self._card(f, "状态")
        grid = ttk.Frame(st, style="Card.TFrame")
        grid.configure(borderwidth=0)
        grid.pack(fill="x")
        rows = (("Agent 桌面端", "auto_agent"), ("IDE 编辑器皮肤", "auto_ide"), ("当前材质包", "auto_skin"),
                ("配置目录", "auto_cfg"))
        for r, (label, attr) in enumerate(rows):
            ttk.Label(grid, text=label, style="CardMuted.TLabel").grid(row=r, column=0, sticky="w", padx=(0, 16),
                                                                       pady=3)
            lab = ttk.Label(grid, text="…", style="Card.TLabel")
            lab.grid(row=r, column=1, sticky="w")
            setattr(self, attr, lab)
        ttk.Button(st, text="打开配置目录", command=lambda: self.open_path(sm.config_dir())).pack(anchor="w",
                                                                                              pady=(10, 0))

    def toggle_auto(self):
        want = self.auto_var.get()

        def done(r, e):
            if e is None and r:
                self.write_log(str(r))
            if want and e is None:
                # 状态写入完成后再拉起后台检测（旧代码同时启动，后台进程可能读到旧状态后立即退出）
                def spawn():
                    import subprocess
                    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
                    subprocess.Popen(ar.background_command(), creationflags=flags if sys.platform == "win32" else 0,
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.run_io(spawn, on_done=lambda r2, e2, tb: e2 and self.write_log(f"后台检测进程启动失败: {e2}"))

        self.run_task("开启自动重注入" if want else "关闭自动重注入",
                      ar.enable_autostart if want else ar.disable_autostart, on_done=done)

    def check_now(self):
        def done(r, e):
            if e is None and r:
                self.toast(r, "info")

        self.run_task("检测并修复", check_and_describe, on_done=done, quiet=True)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    rc = run_headless(argv)
    if rc is not None:
        return rc
    core.bootstrap()
    import ui_kit
    ui_kit.enable_windows_hidpi()  # 高分屏清晰显示，需在创建窗口前调用
    import tkinter as tk
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
