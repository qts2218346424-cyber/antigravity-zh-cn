#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理器界面基础设施（只依赖 tkinter，Pillow 可选）

- JobRunner      后台线程 + 主线程 after() 轮询队列：所有耗时操作都不在 Tk 主线程执行，
                 工作线程只碰 queue.Queue，从不直接调用任何 Tk 方法（Tk 不是线程安全的）。
- OutputRouter   把指定工作线程的 print 输出转到日志面板；其他线程照常输出（打包版窗口程序为 None）。
- Theme          手工 ttk 主题（基于 clam）：浅色 / 深色，跟随系统；中文字体自动回退。
- ImageCache     预览图在后台解码并缩放（Pillow 可用时用 LANCZOS，否则 Tk subsample），按文件指纹缓存。
- Tooltip / Toast / Debouncer 等小组件。
"""

from __future__ import annotations

import base64
import io
import os
import queue
import subprocess
import sys
import threading
import traceback
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# 1. 输出重定向（按线程）
# ---------------------------------------------------------------------------


class OutputRouter(io.TextIOBase):
    """替换 sys.stdout / sys.stderr：正在“捕获”的工作线程按行写入 sink，其余线程写回原始流。

    旧实现在工作线程里用 contextlib.redirect_stdout 临时替换全局 sys.stdout，
    同一时间主线程或其他线程的输出也会被卷进去，结束时还可能把别的线程设置的流恢复错。
    """

    def __init__(self, fallback, sink: Callable[[str], None]):
        super().__init__()
        self.fallback = fallback
        self.sink = sink
        self._capturing: set[int] = set()
        self._buf: dict[int, str] = {}
        self._lock = threading.Lock()

    def capture(self, on: bool) -> None:
        tid = threading.get_ident()
        with self._lock:
            if on:
                self._capturing.add(tid)
                self._buf[tid] = ""
            else:
                self._capturing.discard(tid)
                rest = self._buf.pop(tid, "")
        if not on and rest.strip():
            self.sink(rest.rstrip("\n"))

    def writable(self) -> bool:  # noqa: D401
        return True

    @property
    def encoding(self):  # print() 与第三方库会读取
        return "utf-8"

    def write(self, s: str) -> int:
        if not isinstance(s, str):
            s = str(s)
        tid = threading.get_ident()
        if tid in self._capturing:
            with self._lock:
                data = self._buf.get(tid, "") + s
                *lines, rest = data.split("\n")
                self._buf[tid] = rest
            for line in lines:
                if line.strip():
                    self.sink(line)
            return len(s)
        fb = self.fallback
        if fb is not None:
            try:
                fb.write(s)
            except Exception:
                pass
        return len(s)

    def flush(self) -> None:
        fb = self.fallback
        if fb is not None:
            try:
                fb.flush()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 2. 后台任务
# ---------------------------------------------------------------------------


class JobRunner:
    """两条串行工作通道：

    - "task"：会修改文件的用户操作（打补丁、切换材质包、导入导出……），一次只跑一个；
    - "io"  ：只读查询（状态检测、列出材质包、解码预览图），不会被长任务堵住。

    结果放回 results 队列，由主线程 poll() 取出后在主线程回调。
    """

    LANES = ("task", "io")

    def __init__(self, router: OutputRouter | None = None):
        self.results: "queue.Queue[tuple]" = queue.Queue()
        self.router = router
        self.pending = {lane: 0 for lane in self.LANES}  # 只在主线程读写
        self._queues = {lane: queue.Queue() for lane in self.LANES}
        for lane in self.LANES:
            t = threading.Thread(target=self._loop, args=(lane,), name=f"agzh-{lane}", daemon=True)
            t.start()

    def submit(self, lane: str, fn: Callable, *args, on_done: Callable | None = None,
               capture: bool = False, **kwargs) -> None:
        self.pending[lane] += 1
        self._queues[lane].put((fn, args, kwargs, on_done, capture))

    def busy(self, lane: str | None = None) -> bool:
        if lane:
            return self.pending[lane] > 0
        return any(self.pending.values())

    def _loop(self, lane: str) -> None:
        q = self._queues[lane]
        while True:
            fn, args, kwargs, on_done, capture = q.get()
            result, err, tb = None, None, ""
            if capture and self.router is not None:
                self.router.capture(True)
            try:
                result = fn(*args, **kwargs)
            except Exception as e:  # noqa: BLE001
                err, tb = e, traceback.format_exc()
            finally:
                if capture and self.router is not None:
                    self.router.capture(False)
            self.results.put((lane, on_done, result, err, tb))

    def poll(self, max_items: int = 50) -> int:
        """主线程调用：执行已完成任务的回调。返回处理的数量。"""
        n = 0
        while n < max_items:
            try:
                lane, on_done, result, err, tb = self.results.get_nowait()
            except queue.Empty:
                break
            self.pending[lane] -= 1
            n += 1
            if on_done is not None:
                try:
                    on_done(result, err, tb)
                except Exception:  # noqa: BLE001
                    traceback.print_exc()
        return n


class Debouncer:
    """在主线程上合并频繁触发的回调（如输入框逐字修改触发实时预览）。"""

    def __init__(self, widget, delay_ms: int, fn: Callable[[], None]):
        self.widget, self.delay, self.fn = widget, delay_ms, fn
        self._id = None

    def __call__(self, *_):
        if self._id is not None:
            try:
                self.widget.after_cancel(self._id)
            except Exception:
                pass
        self._id = self.widget.after(self.delay, self._fire)

    def _fire(self):
        self._id = None
        self.fn()


# ---------------------------------------------------------------------------
# 3. 主题
# ---------------------------------------------------------------------------

PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#f3f4f8", "surface": "#ffffff", "surface2": "#f0f1f6", "border": "#e0e3ec",
        "text": "#1c2030", "muted": "#6b7186", "accent": "#d94a7b", "accent_hover": "#c23a69",
        "accent_fg": "#ffffff", "accent_soft": "#fce8ef", "danger": "#d64545", "success": "#23915f",
        "warning": "#b7791f", "sidebar": "#e9ebf2", "nav_hover": "#dfe2ec", "input": "#ffffff",
        "log_bg": "#fafbfd", "shadow": "#d8dbe5", "tip_bg": "#2a2e3c", "tip_fg": "#f5f6fa",
    },
    "dark": {
        "bg": "#15171e", "surface": "#1e212c", "surface2": "#262a37", "border": "#30354a",
        "text": "#e7e9f1", "muted": "#9298ac", "accent": "#f06b98", "accent_hover": "#ff86ad",
        "accent_fg": "#1b0d13", "accent_soft": "#3a2230", "danger": "#ff6b6b", "success": "#4cc38a",
        "warning": "#e6a23c", "sidebar": "#11131a", "nav_hover": "#1d202b", "input": "#262a37",
        "log_bg": "#12141a", "shadow": "#0b0c10", "tip_bg": "#f1f2f6", "tip_fg": "#1c2030",
    },
}

UI_FONTS = {
    "win32": ("Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI"),
    "darwin": ("PingFang SC", "Hiragino Sans GB", "Helvetica Neue"),
    "linux": ("Noto Sans CJK SC", "Noto Sans SC", "Source Han Sans SC", "WenQuanYi Micro Hei", "Droid Sans Fallback",
              "DejaVu Sans"),
}
MONO_FONTS = {
    "win32": ("Cascadia Mono", "Consolas", "Courier New"),
    "darwin": ("SF Mono", "Menlo", "Monaco"),
    "linux": ("Noto Sans Mono CJK SC", "DejaVu Sans Mono", "Liberation Mono", "Monospace"),
}


def _plat() -> str:
    return "win32" if sys.platform == "win32" else ("darwin" if sys.platform == "darwin" else "linux")


def pick_font(root, candidates) -> str:
    """返回第一个真实存在的字体族名。用 Font.actual() 逐个确认，避免枚举全部字体（Windows 上可能上千种）。"""
    import tkinter.font as tkfont
    for fam in candidates:
        try:
            if tkfont.Font(root=root, family=fam, size=10).actual("family").lower() == fam.lower():
                return fam
        except Exception:
            continue
    return "TkDefaultFont"


def system_prefers_dark() -> bool:
    """检测系统是否为深色模式（失败时返回 False）。环境变量 AGZH_THEME=dark/light 可强制。"""
    env = (os.environ.get("AGZH_THEME") or "").lower()
    if env in ("dark", "light"):
        return env == "dark"
    try:
        if sys.platform == "win32":
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
                return winreg.QueryValueEx(k, "AppsUseLightTheme")[0] == 0
        if sys.platform == "darwin":
            r = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=1)
            return "dark" in (r.stdout or "").lower()
        if "dark" in (os.environ.get("GTK_THEME") or "").lower():
            return True
        r = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1)
        return "dark" in (r.stdout or "").lower()
    except Exception:
        return False


def enable_windows_hidpi() -> None:
    """Windows 高分屏：必须在创建 Tk 窗口之前声明 DPI 感知，否则界面会被系统位图拉伸而发虚。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 系统级 DPI 感知（Tk 8.6 不支持逐显示器缩放）
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()  # Windows 7/8 回退
    except Exception:
        pass


def set_windows_dark_titlebar(root, dark: bool) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        val = ctypes.c_int(1 if dark else 0)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE（新 / 旧版本号）
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)) == 0:
                break
    except Exception:
        pass


class Theme:
    def __init__(self, root):
        from tkinter import ttk
        self.root = root
        self.style = ttk.Style(root)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.font_family = pick_font(root, UI_FONTS[_plat()])
        self.mono_family = pick_font(root, MONO_FONTS[_plat()])
        self.mode = "light"
        self.c = dict(PALETTES["light"])
        self._tk_widgets: list[tuple[Any, Callable[[dict], None]]] = []
        self._listeners: list[Callable[[], None]] = []

    # 字体元组
    def font(self, size: int = 10, weight: str = "normal"):
        return (self.font_family, size, weight)

    def mono(self, size: int = 9):
        return (self.mono_family, size)

    def _make_check_images(self, c: dict) -> None:
        """用 PhotoImage.put 逐像素绘制复选框（不依赖 Pillow），按 Tk 缩放比例适配高分屏。"""
        import tkinter as tk
        try:
            scale = float(self.root.tk.call("tk", "scaling")) / 1.333
        except Exception:
            scale = 1.0
        n = max(14, int(round(16 * scale)))
        gap = max(6, int(round(7 * scale)))  # 方框与文字之间的透明间距
        if not hasattr(self, "_chk"):
            self._chk = {k: tk.PhotoImage(master=self.root, width=n + gap, height=n)
                         for k in ("off", "on", "dis_off", "dis_on")}

        def hx(col):
            col = col.lstrip("#")
            return tuple(int(col[i:i + 2], 16) for i in (0, 2, 4))

        def mix(a, b, t):
            return "#%02x%02x%02x" % tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))

        def seg_dist(px, py, ax, ay, bx, by):
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
            return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5

        bgc = hx(c["surface"])
        r = n * 0.22
        for key, fill, border, check in (("off", c["input"], c["muted"], None),
                                         ("on", c["accent"], c["accent"], c["accent_fg"]),
                                         ("dis_off", c["surface2"], c["border"], None),
                                         ("dis_on", c["border"], c["border"], c["muted"])):
            f, b = hx(fill), hx(border)
            ck = hx(check) if check else None
            rows = []
            outside = []
            for y in range(n):
                row = []
                for x in range(n):
                    cx, cy = x + 0.5, y + 0.5
                    # 圆角矩形的有符号距离（<0 在内部）
                    qx = max(abs(cx - n / 2) - (n / 2 - 1 - r), 0)
                    qy = max(abs(cy - n / 2) - (n / 2 - 1 - r), 0)
                    d = (qx * qx + qy * qy) ** 0.5 - r
                    if d > 0.5:
                        row.append(mix(bgc, bgc, 0))
                        outside.append((x, y))  # 圆角外侧设为透明，卡片/页面两种底色上都干净
                        continue
                    col = b if d > -1.2 else f
                    out = mix(col, col, 0)
                    if d > -0.5:  # 边缘抗锯齿
                        out = mix(bgc, col, max(0.0, min(1.0, 0.5 - d)))
                    if ck:
                        dist = min(seg_dist(cx, cy, n * 0.26, n * 0.52, n * 0.43, n * 0.69),
                                   seg_dist(cx, cy, n * 0.43, n * 0.69, n * 0.75, n * 0.33))
                        w = n * 0.085
                        if dist < w + 0.6:
                            out = mix(f, ck, max(0.0, min(1.0, w + 0.6 - dist)))
                    row.append(out)
                rows.append("{" + " ".join(row) + "}")
            img = self._chk[key]
            img.blank()
            img.put(" ".join(rows), to=(0, 0))
            for (x, y) in outside:
                try:
                    img.transparency_set(x, y, True)
                except Exception:
                    break
        # 复选框所在背景有两种（页面底色 / 卡片底色）：卡片更常见，透明处用卡片色

    def register(self, widget, painter: Callable[[dict], None]) -> None:
        """登记非 ttk 控件（Text/Canvas…）的配色函数，切换主题时统一重绘。"""
        self._tk_widgets.append((widget, painter))
        try:
            painter(self.c)
        except Exception:
            pass

    def on_change(self, fn: Callable[[], None]) -> None:
        self._listeners.append(fn)

    def apply(self, mode: str) -> None:
        self.mode = mode
        c = self.c = dict(PALETTES[mode])
        s = self.style
        f = self.font
        root = self.root
        root.configure(background=c["bg"])
        s.configure(".", background=c["bg"], foreground=c["text"], font=f(10), bordercolor=c["border"],
                    lightcolor=c["surface"], darkcolor=c["border"], troughcolor=c["surface2"],
                    focuscolor=c["accent"], selectbackground=c["accent"], selectforeground=c["accent_fg"],
                    insertcolor=c["text"], fieldbackground=c["input"])
        for name, bg in (("TFrame", c["bg"]), ("Card.TFrame", c["surface"]), ("Sidebar.TFrame", c["sidebar"]),
                         ("CardSel.TFrame", c["accent_soft"]), ("Status.TFrame", c["surface"])):
            s.configure(name, background=bg)
        s.configure("Card.TFrame", relief="solid", borderwidth=1, bordercolor=c["border"])
        s.configure("CardSel.TFrame", relief="solid", borderwidth=2, bordercolor=c["accent"])
        s.configure("Status.TFrame", relief="flat", borderwidth=0)
        lbl = {
            "TLabel": (c["bg"], c["text"], f(10)),
            "H1.TLabel": (c["bg"], c["text"], f(17, "bold")),
            "Sub.TLabel": (c["bg"], c["muted"], f(10)),
            "Muted.TLabel": (c["bg"], c["muted"], f(9)),
            "Card.TLabel": (c["surface"], c["text"], f(10)),
            "CardTitle.TLabel": (c["surface"], c["text"], f(12, "bold")),
            "CardH.TLabel": (c["surface"], c["text"], f(11, "bold")),
            "CardMuted.TLabel": (c["surface"], c["muted"], f(9)),
            "CardSel.TLabel": (c["accent_soft"], c["text"], f(10, "bold")),
            "CardSelMuted.TLabel": (c["accent_soft"], c["muted"], f(9)),
            "Sidebar.TLabel": (c["sidebar"], c["text"], f(12, "bold")),
            "SidebarMuted.TLabel": (c["sidebar"], c["muted"], f(9)),
            "Status.TLabel": (c["surface"], c["muted"], f(9)),
            "Badge.TLabel": (c["accent_soft"], c["accent"], f(9, "bold")),
            "Ok.TLabel": (c["surface"], c["success"], f(10, "bold")),
            "Warn.TLabel": (c["surface"], c["warning"], f(10, "bold")),
            "Err.TLabel": (c["surface"], c["danger"], f(10, "bold")),
        }
        for name, (bg, fg, font) in lbl.items():
            s.configure(name, background=bg, foreground=fg, font=font)
        s.configure("Badge.TLabel", padding=(8, 2))

        # 按钮
        s.configure("TButton", background=c["surface2"], foreground=c["text"], borderwidth=1,
                    bordercolor=c["border"], lightcolor=c["surface2"], darkcolor=c["surface2"],
                    padding=(12, 6), font=f(10), focusthickness=0, relief="flat")
        s.map("TButton", background=[("disabled", c["surface2"]), ("pressed", c["border"]), ("active", c["nav_hover"])],
              foreground=[("disabled", c["muted"])],
              bordercolor=[("focus", c["accent"]), ("active", c["border"])])
        s.configure("Accent.TButton", background=c["accent"], foreground=c["accent_fg"], bordercolor=c["accent"],
                    lightcolor=c["accent"], darkcolor=c["accent"], font=f(10, "bold"), padding=(16, 7))
        s.map("Accent.TButton", background=[("disabled", c["border"]), ("pressed", c["accent_hover"]),
                                            ("active", c["accent_hover"])],
              foreground=[("disabled", c["muted"])], bordercolor=[("active", c["accent_hover"])])
        s.configure("Danger.TButton", foreground=c["danger"])
        s.map("Danger.TButton", foreground=[("disabled", c["muted"])])
        s.configure("Ghost.TButton", background=c["bg"], bordercolor=c["bg"], lightcolor=c["bg"], darkcolor=c["bg"],
                    padding=(8, 4))
        s.map("Ghost.TButton", background=[("active", c["nav_hover"])])
        s.configure("Swatch.TButton", padding=(4, 2))
        # 侧边导航
        for name, bg in (("Nav.TButton", c["sidebar"]), ("NavActive.TButton", c["accent_soft"])):
            s.configure(name, background=bg, bordercolor=bg, lightcolor=bg, darkcolor=bg, anchor="w",
                        padding=(14, 9), font=f(11), foreground=c["accent"] if "Active" in name else c["text"])
        s.map("Nav.TButton", background=[("active", c["nav_hover"])], bordercolor=[("active", c["nav_hover"])])
        s.map("NavActive.TButton", background=[("active", c["accent_soft"])])
        s.configure("NavActive.TButton", font=f(11, "bold"))
        s.configure("SidebarFoot.TButton", background=c["sidebar"], bordercolor=c["sidebar"], lightcolor=c["sidebar"],
                    darkcolor=c["sidebar"], foreground=c["muted"], padding=(14, 6), anchor="w", font=f(9))
        s.map("SidebarFoot.TButton", background=[("active", c["nav_hover"])])

        # 输入控件
        for name in ("TEntry", "TCombobox", "TSpinbox"):
            s.configure(name, fieldbackground=c["input"], background=c["surface2"], foreground=c["text"],
                        bordercolor=c["border"], lightcolor=c["input"], darkcolor=c["input"], arrowcolor=c["muted"],
                        padding=(6, 4), insertcolor=c["text"])
            s.map(name, bordercolor=[("focus", c["accent"])], lightcolor=[("focus", c["accent"])],
                  fieldbackground=[("readonly", c["input"]), ("disabled", c["surface2"])],
                  foreground=[("disabled", c["muted"])], selectbackground=[("!focus", c["input"])],
                  selectforeground=[("!focus", c["text"])])
        for name, bg in (("TCheckbutton", c["bg"]), ("Card.TCheckbutton", c["surface"])):
            s.configure(name, background=bg, foreground=c["text"], indicatorbackground=c["input"],
                        indicatorforeground=c["accent_fg"], indicatormargin=(0, 0, 6, 0), font=f(10), focusthickness=0)
            s.map(name, background=[("active", bg)],
                  indicatorbackground=[("selected", c["accent"]), ("active", c["surface2"])],
                  indicatorforeground=[("selected", c["accent_fg"])])
        s.configure("Vertical.TScrollbar", background=c["surface2"], troughcolor=c["bg"], bordercolor=c["bg"],
                    lightcolor=c["surface2"], darkcolor=c["surface2"], arrowcolor=c["muted"], gripcount=0,
                    arrowsize=11)
        s.map("Vertical.TScrollbar", background=[("active", c["border"])])
        s.configure("Accent.Horizontal.TProgressbar", background=c["accent"], troughcolor=c["surface2"],
                    bordercolor=c["surface"], lightcolor=c["accent"], darkcolor=c["accent"], thickness=4)
        # 隐藏 Notebook 自带的标签页（导航改由侧边栏承担，Notebook 只负责页面切换），并去掉内容区边框
        s.layout("Pages.TNotebook.Tab", [])
        s.layout("Pages.TNotebook", [("Notebook.client", {"sticky": "nswe"})])
        s.configure("Pages.TNotebook", background=c["bg"], borderwidth=0, tabmargins=0, padding=0,
                    bordercolor=c["bg"], lightcolor=c["bg"], darkcolor=c["bg"])
        # 复选框：自绘圆角方框 + 对勾（clam 默认是叉号）
        self._make_check_images(c)
        try:
            s.element_create("Agzh.Checkbutton.indicator", "image", self._chk["off"],
                             ("disabled", "selected", self._chk["dis_on"]), ("disabled", self._chk["dis_off"]),
                             ("selected", self._chk["on"]), border=0, sticky="w")
        except Exception:
            pass  # 已创建过：图片对象原地更新即可
        for name in ("TCheckbutton", "Card.TCheckbutton"):
            s.layout(name, [("Checkbutton.padding", {"sticky": "nswe", "children": [
                ("Agzh.Checkbutton.indicator", {"side": "left", "sticky": ""}),
                ("Checkbutton.focus", {"side": "left", "sticky": "w", "children": [
                    ("Checkbutton.label", {"sticky": "nswe"})]})]})])
        s.configure("Horizontal.TScale", gripcount=0, bordercolor=c["border"], lightcolor=c["surface2"],
                    darkcolor=c["surface2"], troughcolor=c["surface2"], background=c["accent"], sliderlength=18)
        s.map("Horizontal.TScale", background=[("active", c["accent_hover"])])
        s.configure("Small.TButton", padding=(10, 5))
        s.configure("SmallDanger.TButton", padding=(10, 5), foreground=c["danger"])
        s.configure("TLabelframe", background=c["surface"], bordercolor=c["border"], relief="solid", borderwidth=1)
        s.configure("TLabelframe.Label", background=c["surface"], foreground=c["text"], font=f(10, "bold"))
        # 下拉列表 / 菜单（tk 原生部分）
        root.option_add("*TCombobox*Listbox.background", c["surface"])
        root.option_add("*TCombobox*Listbox.foreground", c["text"])
        root.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
        root.option_add("*TCombobox*Listbox.selectForeground", c["accent_fg"])
        root.option_add("*TCombobox*Listbox.font", f(10))
        for w, painter in list(self._tk_widgets):
            try:
                if w.winfo_exists():
                    painter(c)
            except Exception:
                pass
        self._tk_widgets = [(w, p) for (w, p) in self._tk_widgets if _alive(w)]
        set_windows_dark_titlebar(root, mode == "dark")
        for fn in list(self._listeners):
            try:
                fn()
            except Exception:
                traceback.print_exc()


def _alive(w) -> bool:
    try:
        return bool(w.winfo_exists())
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 4. 预览图缓存
# ---------------------------------------------------------------------------


def decode_image(path: str, max_w: int, max_h: int):
    """工作线程：读取并缩放图片，返回可在主线程快速转成 PhotoImage 的数据。"""
    p = Path(path)
    try:
        from PIL import Image
    except ImportError:
        Image = None
    if Image is not None:
        with Image.open(p) as im:
            im.draft("RGB", (max_w * 2, max_h * 2))  # JPEG 可在解码阶段直接缩小
            im = im.convert("RGBA")
            im.thumbnail((max_w, max_h), Image.LANCZOS)
            # 重新编码为 PNG 交给 Tk 原生解码：不依赖 PIL.ImageTk（打包版里它依赖的 Tk 桥接常被漏打包）
            buf = io.BytesIO()
            im.save(buf, format="PNG", compress_level=1)
            return ("png", base64.b64encode(buf.getvalue()).decode("ascii"))
    data = p.read_bytes()
    return ("raw", base64.b64encode(data).decode("ascii"))


def to_photo(root, decoded, max_w: int, max_h: int):
    """主线程：把 decode_image 的结果转成 PhotoImage。"""
    kind, payload = decoded
    import tkinter as tk
    if kind == "png":
        return tk.PhotoImage(master=root, data=payload)
    img = tk.PhotoImage(master=root, data=payload)
    w, h = img.width(), img.height()
    if w > max_w or h > max_h:
        factor = max((w + max_w - 1) // max_w, (h + max_h - 1) // max_h)
        img = img.subsample(factor, factor)
    return img


class ImageCache:
    """按 (路径, 修改时间, 尺寸) 缓存 PhotoImage；解码在 io 通道执行，同一张图的并发请求合并。"""

    def __init__(self, root, jobs: JobRunner, limit: int = 64):
        self.root, self.jobs, self.limit = root, jobs, limit
        self._cache: dict[tuple, Any] = {}
        self._waiting: dict[tuple, list[Callable]] = {}

    @staticmethod
    def key(path: str, w: int, h: int) -> tuple:
        try:
            m = Path(path).stat().st_mtime_ns
        except OSError:
            m = 0
        return (str(path), m, w, h)

    def get(self, path: str | None, w: int, h: int, cb: Callable[[Any], None]) -> None:
        if not path:
            cb(None)
            return
        k = self.key(path, w, h)
        if k in self._cache:
            cb(self._cache[k])
            return
        if k in self._waiting:
            self._waiting[k].append(cb)
            return
        self._waiting[k] = [cb]

        def done(decoded, err, _tb):
            img = None
            if err is None and decoded is not None:
                try:
                    img = to_photo(self.root, decoded, w, h)
                except Exception:
                    img = None
            if img is not None:
                if len(self._cache) >= self.limit:
                    self._cache.pop(next(iter(self._cache)))
                self._cache[k] = img
            for fn in self._waiting.pop(k, []):
                fn(img)

        self.jobs.submit("io", decode_image, str(path), w, h, on_done=done)

    def __len__(self) -> int:
        return len(self._cache)


# ---------------------------------------------------------------------------
# 5. 小组件
# ---------------------------------------------------------------------------


class Tooltip:
    def __init__(self, widget, text: str, theme: Theme, delay: int = 450):
        self.w, self.text, self.theme, self.delay = widget, text, theme, delay
        self._id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _e=None):
        self._cancel()
        self._id = self.w.after(self.delay, self._show)

    def _cancel(self):
        if self._id is not None:
            try:
                self.w.after_cancel(self._id)
            except Exception:
                pass
            self._id = None

    def _show(self):
        import tkinter as tk
        self._id = None
        if self._tip is not None or not _alive(self.w):
            return
        c = self.theme.c
        x = self.w.winfo_rootx() + 8
        y = self.w.winfo_rooty() + self.w.winfo_height() + 6
        tip = tk.Toplevel(self.w)
        tip.wm_overrideredirect(True)
        tip.configure(background=c["tip_bg"])
        tk.Label(tip, text=self.text, background=c["tip_bg"], foreground=c["tip_fg"], font=self.theme.font(9),
                 justify="left", wraplength=320, padx=8, pady=5).pack()
        tip.wm_geometry(f"+{x}+{y}")
        self._tip = tip

    def _hide(self, _e=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


class Toaster:
    """窗口右下角的轻提示，几秒后自动消失；多条提示依次向上堆叠。"""

    def __init__(self, root, theme: Theme):
        self.root, self.theme = root, theme
        self._toasts: list = []

    def show(self, text: str, kind: str = "info", ms: int = 3200) -> None:
        import tkinter as tk
        c = self.theme.c
        color = {"info": c["accent"], "ok": c["success"], "warn": c["warning"], "error": c["danger"]}.get(kind, c["accent"])
        icon = {"info": "ℹ", "ok": "✓", "warn": "!", "error": "✕"}.get(kind, "ℹ")
        try:
            t = tk.Toplevel(self.root)
        except Exception:
            return
        t.wm_overrideredirect(True)
        try:
            t.attributes("-topmost", True)
        except Exception:
            pass
        frame = tk.Frame(t, background=c["surface"], highlightthickness=1, highlightbackground=c["border"])
        frame.pack()
        tk.Frame(frame, background=color, width=4).pack(side="left", fill="y")
        tk.Label(frame, text=icon, background=c["surface"], foreground=color, font=self.theme.font(12, "bold"),
                 padx=10).pack(side="left")
        tk.Label(frame, text=text, background=c["surface"], foreground=c["text"], font=self.theme.font(10),
                 wraplength=340, justify="left", pady=10, padx=4).pack(side="left")
        tk.Label(frame, text=" ", background=c["surface"], width=1).pack(side="left")
        t.bind("<Button-1>", lambda e: self._close(t))
        self._toasts.append(t)
        self._layout()
        t.after(ms, lambda: self._close(t))

    def _layout(self):
        try:
            self.root.update_idletasks()
            rx, ry = self.root.winfo_rootx(), self.root.winfo_rooty()
            rw, rh = self.root.winfo_width(), self.root.winfo_height()
        except Exception:
            return
        y = ry + rh - 52
        for t in reversed(self._toasts):
            try:
                t.update_idletasks()
                w, h = t.winfo_reqwidth(), t.winfo_reqheight()
                y -= h + 8
                t.wm_geometry(f"+{rx + rw - w - 18}+{y}")
            except Exception:
                pass

    def _close(self, t):
        if t in self._toasts:
            self._toasts.remove(t)
            try:
                t.destroy()
            except Exception:
                pass
            self._layout()


class ScrollFrame:
    """可滚动容器：鼠标悬停在区域内时才响应滚轮（旧实现 bind_all 会让其他页面也滚动它）。

    兼容 Windows (delta=±120)、macOS (delta=±1..)、X11 (Button-4/5)。
    """

    def __init__(self, parent, theme: Theme, bg_key: str = "bg"):
        import tkinter as tk
        from tkinter import ttk
        self.outer = ttk.Frame(parent)
        self.canvas = tk.Canvas(self.outer, highlightthickness=0, borderwidth=0)
        theme.register(self.canvas, lambda c: self.canvas.configure(background=c[bg_key]))
        self.sb = ttk.Scrollbar(self.outer, orient="vertical", command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas)
        self._win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.sb.pack(side="right", fill="y")
        self.body.bind("<Configure>", self._on_body)
        self.canvas.bind("<Configure>", self._on_canvas)
        for w in (self.canvas, self.body):
            w.bind("<Enter>", self._bind_wheel, add="+")
            w.bind("<Leave>", self._unbind_wheel, add="+")

    def _on_body(self, _e=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, e):
        self.canvas.itemconfigure(self._win, width=e.width)

    def _bind_wheel(self, _e=None):
        c = self.canvas
        c.bind_all("<MouseWheel>", self._wheel)
        c.bind_all("<Button-4>", lambda e: self._scroll(-1))
        c.bind_all("<Button-5>", lambda e: self._scroll(1))

    def _unbind_wheel(self, _e=None):
        c = self.canvas
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            c.unbind_all(seq)

    def _wheel(self, e):
        d = e.delta
        if sys.platform == "darwin":
            step = -d
        else:
            step = -int(d / 120) if abs(d) >= 120 else (-1 if d > 0 else 1)
        self._scroll(step)

    def _scroll(self, units: int):
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(units, "units")
