#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 汉化 & 材质包管理器（一体化轻量图形界面）

一个程序包含：
  · 材质包：列表 + 预览 + 一键切换、导入/导出 .zip、以现有包为模板新建、删除
  · 自定义：颜色 / 背景图(透明度、模糊、位置) / 字体 / 图标 / 桌宠外观 / 自定义 CSS（写入用户覆盖层）
  · 汉化：安装/重打汉化补丁、还原原版、禁止/恢复官方自动更新
  · 桌宠：启动独立桌面桌宠（Windows）
  · 自动维护：开机后台检测 Antigravity 更新并自动重新注入

运行模式：
  agzh_app.py                 打开图形界面
  agzh_app.py --background    后台常驻检测（开机自启使用，无窗口）
  agzh_app.py --check-once    检测一次并按需重新注入（macOS LaunchAgent 使用）
  agzh_app.py --pet           启动独立桌面桌宠（Windows）
  agzh_app.py cli <参数...>   等同于 scripts/agzh.py 命令行

界面基于 Python 自带的 tkinter：无需 Electron / 浏览器内核，打包后体积最小。
"""

from __future__ import annotations

import io
import json
import os
import queue
import sys
import threading
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
_BASE = Path(getattr(sys, "_MEIPASS", HERE.parent))
for _p in (_BASE / "scripts", HERE.parent / "scripts"):
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import agzh_core as core  # noqa: E402
import auto_reapply as ar  # noqa: E402
import skin_injector as si  # noqa: E402
import skin_manager as sm  # noqa: E402

APP_TITLE = "Antigravity 汉化 & 材质包管理器"

COLOR_LABELS = {
    "background": "编辑器背景", "foreground": "前景文字", "accent": "强调色", "accentForeground": "强调色上的文字",
    "sidebar": "侧边栏", "activityBar": "活动栏", "titleBar": "标题栏", "statusBar": "状态栏",
    "panel": "面板/终端", "border": "边框", "selection": "选中背景", "input": "输入框", "muted": "次要文字",
}
TARGET_LABELS = {"window": "整个窗口", "editor": "编辑区", "sidebar": "侧边栏", "panel": "底部面板",
                 "terminal": "终端", "chat": "对话区"}
STATUS_TEXT = {
    "patched": "✅ 已汉化", "never": "⚪ 未汉化", "disabled": "⏸ 已还原（不自动重打）",
    "needs_reapply": "⚠ 已被官方更新覆盖，待重新注入", "missing": "❌ 未找到安装目录",
    "applied": "✅ 已应用", "stale": "⚠ 皮肤已变更，待同步", "not_applied": "⚪ 未应用",
}


# ---------------------------------------------------------------------------
# 非图形模式
# ---------------------------------------------------------------------------
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
    if argv and argv[0] == "cli":
        import agzh
        return agzh.main(argv[1:])
    return None


# ---------------------------------------------------------------------------
# 图形界面
# ---------------------------------------------------------------------------
class App:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk
        self.tk, self.ttk = tk, ttk
        self.root = root
        root.title(APP_TITLE)
        root.geometry("980x660")
        root.minsize(860, 560)
        self.log_q: queue.Queue[str] = queue.Queue()
        self.busy = False
        self._preview_img = None
        self.form: dict = {}

        style = ttk.Style()
        try:
            style.theme_use("vista" if sys.platform == "win32" else "clam")
        except Exception:
            pass
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 13, "bold"))
        style.configure("Hint.TLabel", foreground="#666")

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        self.nb = nb
        self.tab_skins = ttk.Frame(nb, padding=10)
        self.tab_custom = ttk.Frame(nb, padding=10)
        self.tab_l10n = ttk.Frame(nb, padding=10)
        self.tab_pet = ttk.Frame(nb, padding=10)
        self.tab_auto = ttk.Frame(nb, padding=10)
        nb.add(self.tab_skins, text="  材质包  ")
        nb.add(self.tab_custom, text="  自定义  ")
        nb.add(self.tab_l10n, text="  汉化补丁  ")
        nb.add(self.tab_pet, text="  桌宠  ")
        nb.add(self.tab_auto, text="  自动维护  ")

        logf = ttk.LabelFrame(root, text="日志", padding=4)
        logf.pack(fill="x", padx=8, pady=8)
        self.log = tk.Text(logf, height=7, wrap="word", state="disabled", font=("Consolas", 9))
        self.log.pack(fill="x")

        self._build_skins()
        self._build_custom()
        self._build_l10n()
        self._build_pet()
        self._build_auto()
        self.refresh_all()
        root.after(150, self._drain_log)

    # ---------------- 工具 ----------------
    def write_log(self, text: str):
        self.log_q.put(text)

    def _drain_log(self):
        try:
            while True:
                t = self.log_q.get_nowait()
                self.log.configure(state="normal")
                self.log.insert("end", t if t.endswith("\n") else t + "\n")
                self.log.see("end")
                self.log.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(150, self._drain_log)

    def run_task(self, title: str, fn, *args, on_done=None, **kwargs):
        """在后台线程执行耗时操作，并把 print 输出转到日志框。"""
        if self.busy:
            self.msg("请稍候", "上一个操作仍在进行中。")
            return
        self.busy = True
        self.write_log(f"▶ {title}...")

        class _W(io.TextIOBase):
            def __init__(s, cb):
                s.cb = cb

            def write(s, x):
                if x and x.strip():
                    s.cb(x.rstrip("\n"))
                return len(x)

        def worker():
            w = _W(self.write_log)
            result, err = None, None
            try:
                with redirect_stdout(w), redirect_stderr(w):
                    result = fn(*args, **kwargs)
            except Exception as e:  # noqa: BLE001
                err = e
                self.write_log(traceback.format_exc())
            self.busy = False

            def done():
                if err:
                    self.msg("操作失败", f"{title}失败：\n{err}", error=True)
                else:
                    self.write_log(f"✔ {title}完成")
                if on_done:
                    on_done(result, err)
                self.refresh_all()
            self.root.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def msg(self, title, text, error=False):
        from tkinter import messagebox
        (messagebox.showerror if error else messagebox.showinfo)(title, text, parent=self.root)

    def ask(self, title, text) -> bool:
        from tkinter import messagebox
        return messagebox.askyesno(title, text, parent=self.root)

    # ---------------- 材质包页 ----------------
    def _build_skins(self):
        tk, ttk = self.tk, self.ttk
        f = self.tab_skins
        left = ttk.Frame(f)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="已安装材质包", style="Title.TLabel").pack(anchor="w")
        self.skin_list = tk.Listbox(left, width=30, height=20, exportselection=False, font=("Microsoft YaHei UI", 10))
        self.skin_list.pack(fill="y", expand=True, pady=6)
        self.skin_list.bind("<<ListboxSelect>>", lambda e: self.show_skin_detail())
        self.skin_list.bind("<Double-Button-1>", lambda e: self.use_selected())
        bar = ttk.Frame(left)
        bar.pack(fill="x")
        for text, cmd in (("导入 .zip", self.import_zip), ("导出 .zip", self.export_zip),
                          ("复制为新包", self.clone_pack), ("删除", self.delete_pack)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=2, pady=2)

        right = ttk.Frame(f, padding=(14, 0, 0, 0))
        right.pack(side="left", fill="both", expand=True)
        self.skin_title = ttk.Label(right, text="", style="Title.TLabel")
        self.skin_title.pack(anchor="w")
        self.skin_meta = ttk.Label(right, text="", style="Hint.TLabel")
        self.skin_meta.pack(anchor="w")
        self.preview = tk.Canvas(right, width=360, height=220, highlightthickness=1, highlightbackground="#ccc")
        self.preview.pack(anchor="w", pady=8)
        self.skin_desc = ttk.Label(right, text="", wraplength=520, justify="left")
        self.skin_desc.pack(anchor="w")
        btns = ttk.Frame(right)
        btns.pack(anchor="w", pady=10)
        ttk.Button(btns, text="✨ 一键应用此材质包", command=self.use_selected).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="关闭皮肤", command=self.skin_off).pack(side="left", padx=6)
        ttk.Button(btns, text="打开材质包文件夹", command=lambda: self.open_path(sm.skins_dir())).pack(side="left", padx=6)
        self.ide_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, text="同时应用到 Antigravity IDE 编辑器（修改工作台样式并修正校验和）",
                        variable=self.ide_var).pack(anchor="w")
        ttk.Label(right, style="Hint.TLabel", wraplength=520, justify="left",
                  text="提示：Agent 桌面端在打过汉化补丁（含皮肤加载器）后切换即实时生效；"
                       "IDE 编辑器需执行“重新加载窗口”或重启。").pack(anchor="w", pady=(6, 0))

    def refresh_skins(self):
        self.skins = core.list_skins()
        sel = self.selected_skin_id()
        self.skin_list.delete(0, "end")
        for i, s in enumerate(self.skins):
            self.skin_list.insert("end", ("● " if s["active"] else "   ") + s["name"])
            if s["id"] == sel or (sel is None and s["active"]):
                self.skin_list.selection_set(i)
        if not self.skin_list.curselection() and self.skins:
            self.skin_list.selection_set(0)
        self.show_skin_detail()
        st = sm.load_state()
        ide_enabled = (st.get("ide") or {}).get("enabled")
        self.ide_var.set(ide_enabled is not False)

    def selected_skin_id(self):
        cur = self.skin_list.curselection() if hasattr(self, "skin_list") else ()
        if cur and getattr(self, "skins", None) and cur[0] < len(self.skins):
            return self.skins[cur[0]]["id"]
        return None

    def selected_info(self):
        sid = self.selected_skin_id()
        return next((s for s in self.skins if s["id"] == sid), None)

    def show_skin_detail(self):
        info = self.selected_info()
        self.preview.delete("all")
        if not info:
            self.skin_title.configure(text="（暂无材质包）")
            return
        self.skin_title.configure(text=info["name"] + ("    [当前使用]" if info["active"] else ""))
        self.skin_meta.configure(text=f"id: {info['id']}   版本: {info['version']}   作者: {info['author'] or '未知'}"
                                      f"   {'浅色' if info['base'] == 'light' else '暗色'}   {'内置' if info['builtin'] else ''}")
        self.skin_desc.configure(text=info["description"])
        self._preview_img = None
        if info.get("preview") and info["preview"].lower().endswith(".png"):
            try:
                self._preview_img = self.tk.PhotoImage(file=info["preview"])
                w, h = self._preview_img.width(), self._preview_img.height()
                if w > 360 or h > 220:
                    factor = max((w + 359) // 360, (h + 219) // 220)
                    self._preview_img = self._preview_img.subsample(factor, factor)
                self.preview.create_image(0, 0, anchor="nw", image=self._preview_img)
                return
            except Exception:
                self._preview_img = None
        self.draw_palette(info["colors"])

    def draw_palette(self, colors: dict):
        """没有 PNG 预览图时按配色画一个示意工作台。"""
        c = self.preview
        def col(k, d):
            v = colors.get(k) or d
            return v[:7] if isinstance(v, str) and v.startswith("#") and len(v) in (4, 7, 9) else d
        bg, fg, ac = col("background", "#1e1e1e"), col("foreground", "#d4d4d4"), col("accent", "#3794ff")
        c.create_rectangle(0, 0, 360, 220, fill=bg, outline="")
        c.create_rectangle(0, 0, 360, 18, fill=col("titleBar", "#333333"), outline="")
        c.create_rectangle(0, 18, 26, 206, fill=col("activityBar", "#333333"), outline="")
        c.create_rectangle(26, 18, 110, 206, fill=col("sidebar", "#252526"), outline="")
        for i in range(9):
            c.create_rectangle(124, 30 + i * 18, 124 + 60 + (i * 37) % 160, 36 + i * 18,
                               fill=ac if i % 3 == 0 else fg, outline="")
        c.create_rectangle(0, 206, 360, 220, fill=col("statusBar", ac), outline="")

    def use_selected(self):
        sid = self.selected_skin_id()
        if not sid:
            return
        self.run_task(f"切换材质包 {sid}", core.use_skin, sid, apply_ide=self.ide_var.get(),
                      on_done=lambda r, e: r and self.write_log(f"IDE 状态: {r.get('ide')}"))

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
            if r and r[0] == "exists" and self.ask("覆盖导入", r[1] + "\n\n是否覆盖已有材质包？"):
                self.run_task("覆盖导入材质包", sm.import_pack, Path(p), True)
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
        self.run_task("复制材质包", sm.create_pack_from, sid, new_id.strip(), name.strip())

    def delete_pack(self):
        sid = self.selected_skin_id()
        if sid and self.ask("删除材质包", f"确定删除材质包 {sid} 及其个人覆盖设置吗？"):
            self.run_task("删除材质包", sm.remove_pack, sid)

    def open_path(self, p: Path):
        p.mkdir(parents=True, exist_ok=True)
        import subprocess
        if sys.platform == "win32":
            os.startfile(str(p))  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])

    # ---------------- 自定义页 ----------------
    def _build_custom(self):
        tk, ttk = self.tk, self.ttk
        f = self.tab_custom
        top = ttk.Frame(f)
        top.pack(fill="x")
        self.custom_title = ttk.Label(top, text="", style="Title.TLabel")
        self.custom_title.pack(side="left")
        self.global_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="作为全局设置（作用于所有材质包）", variable=self.global_var,
                        command=self.load_custom_form).pack(side="left", padx=12)
        ttk.Button(top, text="恢复材质包默认", command=self.reset_custom).pack(side="right")
        ttk.Button(top, text="💾 保存并应用", command=self.save_custom).pack(side="right", padx=6)

        canvas = tk.Canvas(f, highlightthickness=0)
        sb = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        body = ttk.Frame(canvas)
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True, pady=6)
        sb.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        F = self.form
        # 颜色
        cf = ttk.LabelFrame(body, text="配色（留空 = 使用材质包默认）", padding=8)
        cf.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        for i, (key, label) in enumerate(COLOR_LABELS.items()):
            r, c = divmod(i, 2)
            ttk.Label(cf, text=label).grid(row=r, column=c * 3, sticky="w", padx=(0, 4))
            var = tk.StringVar()
            ttk.Entry(cf, textvariable=var, width=11).grid(row=r, column=c * 3 + 1, pady=1)
            ttk.Button(cf, text="🎨", width=3, command=lambda v=var: self.pick_color(v)).grid(row=r, column=c * 3 + 2, padx=(2, 14))
            F[f"colors.{key}"] = var

        # 背景
        bf = ttk.LabelFrame(body, text="背景图（作用于材质包的主背景）", padding=8)
        bf.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        F["bg.image"] = tk.StringVar()
        ttk.Label(bf, text="图片").grid(row=0, column=0, sticky="w")
        ttk.Entry(bf, textvariable=F["bg.image"], width=46).grid(row=0, column=1, columnspan=3, sticky="w")
        ttk.Button(bf, text="选择…", command=lambda: self.pick_file(F["bg.image"], "image")).grid(row=0, column=4, padx=4)
        F["bg.target"] = tk.StringVar()
        ttk.Label(bf, text="位置").grid(row=1, column=0, sticky="w")
        ttk.Combobox(bf, textvariable=F["bg.target"], values=list(TARGET_LABELS.values()), width=12,
                     state="readonly").grid(row=1, column=1, sticky="w")
        F["bg.position"] = tk.StringVar()
        ttk.Label(bf, text="对齐").grid(row=1, column=2, sticky="e")
        ttk.Combobox(bf, textvariable=F["bg.position"], width=14,
                     values=["center", "top", "bottom", "left", "right", "right bottom", "left bottom", "top right"]
                     ).grid(row=1, column=3, sticky="w")
        F["bg.size"] = tk.StringVar()
        ttk.Label(bf, text="缩放").grid(row=2, column=0, sticky="w")
        ttk.Combobox(bf, textvariable=F["bg.size"], values=["cover", "contain", "auto", "160px"], width=12).grid(row=2, column=1, sticky="w")
        F["bg.opacity"] = tk.DoubleVar(value=0.15)
        F["bg.blur"] = tk.DoubleVar(value=0)
        ttk.Label(bf, text="不透明度").grid(row=3, column=0, sticky="w")
        ttk.Scale(bf, from_=0, to=1, variable=F["bg.opacity"], length=220).grid(row=3, column=1, columnspan=2, sticky="w")
        ttk.Label(bf, textvariable=F["bg.opacity"], width=6).grid(row=3, column=3, sticky="w")
        ttk.Label(bf, text="模糊 (px)").grid(row=4, column=0, sticky="w")
        ttk.Scale(bf, from_=0, to=40, variable=F["bg.blur"], length=220).grid(row=4, column=1, columnspan=2, sticky="w")
        ttk.Label(bf, textvariable=F["bg.blur"], width=6).grid(row=4, column=3, sticky="w")

        # 字体
        ff = ttk.LabelFrame(body, text="字体", padding=8)
        ff.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)
        try:
            import tkinter.font as tkfont
            families = sorted(set(tkfont.families(self.root)))
        except Exception:
            families = []
        for r, (key, label) in enumerate((("font.family", "界面字体"), ("font.monoFamily", "代码字体"))):
            F[key] = tk.StringVar()
            ttk.Label(ff, text=label).grid(row=r, column=0, sticky="w")
            ttk.Combobox(ff, textvariable=F[key], values=families, width=40).grid(row=r, column=1, sticky="w", pady=1)
        F["font.size"] = tk.StringVar()
        F["font.monoSize"] = tk.StringVar()
        ttk.Label(ff, text="界面字号").grid(row=2, column=0, sticky="w")
        ttk.Spinbox(ff, from_=8, to=40, textvariable=F["font.size"], width=6).grid(row=2, column=1, sticky="w")
        ttk.Label(ff, text="代码字号").grid(row=3, column=0, sticky="w")
        ttk.Spinbox(ff, from_=8, to=40, textvariable=F["font.monoSize"], width=6).grid(row=3, column=1, sticky="w")

        # 图标
        icf = ttk.LabelFrame(body, text="图标", padding=8)
        icf.grid(row=3, column=0, sticky="nsew", padx=4, pady=4)
        F["icons.filter"] = tk.StringVar()
        F["icons.color"] = tk.StringVar()
        ttk.Label(icf, text="滤镜").grid(row=0, column=0, sticky="w")
        ttk.Combobox(icf, textvariable=F["icons.filter"], width=34,
                     values=["", "hue-rotate(300deg) saturate(1.3)", "grayscale(1)", "saturate(1.5)", "sepia(0.6)"]
                     ).grid(row=0, column=1, sticky="w")
        ttk.Label(icf, text="颜色").grid(row=1, column=0, sticky="w")
        ttk.Entry(icf, textvariable=F["icons.color"], width=12).grid(row=1, column=1, sticky="w")
        ttk.Label(icf, style="Hint.TLabel", text="单个图标替换（codicons 映射）请在 skin.json 中配置，见 docs/skins.md").grid(row=2, column=0, columnspan=2, sticky="w")

        # 桌宠
        pf = ttk.LabelFrame(body, text="桌宠外观", padding=8)
        pf.grid(row=4, column=0, sticky="nsew", padx=4, pady=4)
        F["pet.character"] = tk.StringVar()
        ttk.Label(pf, text="角色").grid(row=0, column=0, sticky="w")
        ttk.Combobox(pf, textvariable=F["pet.character"], values=["", "nezuko", "prince", "auto"], width=10,
                     state="readonly").grid(row=0, column=1, sticky="w")
        F["pet.sprite"] = tk.StringVar()
        ttk.Label(pf, text="自定义形象图").grid(row=1, column=0, sticky="w")
        ttk.Entry(pf, textvariable=F["pet.sprite"], width=40).grid(row=1, column=1, sticky="w")
        ttk.Button(pf, text="选择…", command=lambda: self.pick_file(F["pet.sprite"], "image")).grid(row=1, column=2, padx=4)
        F["pet.filter"] = tk.StringVar()
        ttk.Label(pf, text="滤镜").grid(row=2, column=0, sticky="w")
        ttk.Combobox(pf, textvariable=F["pet.filter"], width=34,
                     values=["", "hue-rotate(180deg)", "saturate(1.4)", "grayscale(1)", "brightness(1.1)"]
                     ).grid(row=2, column=1, sticky="w")
        F["pet.accent"] = tk.StringVar()
        ttk.Label(pf, text="面板强调色").grid(row=3, column=0, sticky="w")
        ttk.Entry(pf, textvariable=F["pet.accent"], width=12).grid(row=3, column=1, sticky="w")
        F["pet.scale"] = tk.StringVar()
        ttk.Label(pf, text="默认缩放").grid(row=4, column=0, sticky="w")
        ttk.Spinbox(pf, from_=0.3, to=3.0, increment=0.1, textvariable=F["pet.scale"], width=6).grid(row=4, column=1, sticky="w")
        F["pet.hidden"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(pf, text="隐藏 Agent 窗口内桌宠", variable=F["pet.hidden"]).grid(row=5, column=1, sticky="w")

        # 自定义 CSS
        xf = ttk.LabelFrame(body, text="追加自定义 CSS（附加在材质包样式之后）", padding=8)
        xf.grid(row=5, column=0, sticky="nsew", padx=4, pady=4)
        self.css_text = tk.Text(xf, height=6, width=90, font=("Consolas", 9))
        self.css_text.pack(fill="both")

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
        if self.global_var.get():
            return None
        return self.selected_skin_id() or sm.load_state().get("active_skin")

    def load_custom_form(self):
        scope = self.custom_scope()
        F = self.form
        if not F:
            return
        self.custom_title.configure(text="全局覆盖层" if scope is None else f"自定义：{scope}")
        ov = sm.load_override(scope)
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
        base_bg = {}
        if scope:
            try:
                b = sm.get_pack(scope).manifest.get("background")
                base_bg = b[0] if isinstance(b, list) and b else (b or {})
            except sm.SkinError:
                pass
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

    def collect_override(self) -> dict:
        F = self.form
        ov: dict = {}
        colors = {k.split(".", 1)[1]: v.get().strip() for k, v in F.items() if k.startswith("colors.") and v.get().strip()}
        if colors:
            ov["colors"] = colors
        bg: dict = {}
        img = F["bg.image"].get().strip()
        if img:
            bg["image"] = sm.import_override_asset(Path(img)) if Path(img).is_absolute() else img
        cur = (round(F["bg.opacity"].get(), 2), round(F["bg.blur"].get(), 1), F["bg.target"].get(),
               F["bg.position"].get(), F["bg.size"].get())
        loaded = getattr(self, "_loaded_bg", None)
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
            for k, var in F.items():
                if not k.startswith(sect + "."):
                    continue
                key = k.split(".", 1)[1]
                v = var.get()
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
        css = self.css_text.get("1.0", "end").strip()
        if css:
            ov["css"] = css
        return ov

    def save_custom(self):
        try:
            ov = self.collect_override()
        except Exception as e:  # noqa: BLE001
            self.msg("无法保存", str(e), error=True)
            return
        scope = self.custom_scope()
        self.run_task("保存自定义设置", core.save_customization, scope, ov)

    def reset_custom(self):
        scope = self.custom_scope()
        if self.ask("恢复默认", "清除当前的个人覆盖设置，恢复为材质包原样？"):
            def do():
                sm.reset_override(scope)
                st = sm.load_state()
                if st.get("active_skin") and st.get("skin_enabled", True):
                    core.use_skin(st["active_skin"])
            self.run_task("恢复材质包默认", do, on_done=lambda r, e: self.load_custom_form())

    # ---------------- 汉化页 ----------------
    def _build_l10n(self):
        tk, ttk = self.tk, self.ttk
        f = self.tab_l10n
        ttk.Label(f, text="Agent 桌面端汉化补丁", style="Title.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        self.l10n_status = ttk.Label(f, text="")
        self.l10n_status.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 10))
        self.dir_var = tk.StringVar()
        ttk.Label(f, text="安装目录").grid(row=2, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.dir_var, width=60).grid(row=2, column=1, sticky="w")
        ttk.Button(f, text="浏览…", command=self.pick_dir).grid(row=2, column=2, padx=4)
        self.lang_var = tk.StringVar(value="zh-CN")
        ttk.Label(f, text="语言").grid(row=3, column=0, sticky="w")
        ttk.Combobox(f, textvariable=self.lang_var, values=["zh-CN", "zh-TW", "zh-HK"], width=10,
                     state="readonly").grid(row=3, column=1, sticky="w", pady=2)
        self.char_var = tk.StringVar(value="(沿用上次)")
        ttk.Label(f, text="启动动画角色").grid(row=4, column=0, sticky="w")
        ttk.Combobox(f, textvariable=self.char_var, width=14, state="readonly",
                     values=["(沿用上次)", "tanjiro", "zenitsu", "inosuke", "nezuko", "all"]).grid(row=4, column=1, sticky="w", pady=2)
        self.pet_var = tk.BooleanVar(value=True)
        self.skinload_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="挂载窗口内桌宠", variable=self.pet_var).grid(row=5, column=1, sticky="w")
        ttk.Checkbutton(f, text="注入材质包加载器（切换皮肤实时生效）", variable=self.skinload_var).grid(row=6, column=1, sticky="w")
        bar = ttk.Frame(f)
        bar.grid(row=7, column=0, columnspan=3, sticky="w", pady=12)
        ttk.Button(bar, text="安装 / 重新应用汉化", command=self.install_l10n).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="还原官方原版", command=self.restore_l10n).pack(side="left", padx=6)
        ttk.Button(bar, text="禁止官方自动更新", command=lambda: self.toggle_updates(True)).pack(side="left", padx=6)
        ttk.Button(bar, text="恢复官方自动更新", command=lambda: self.toggle_updates(False)).pack(side="left", padx=6)
        ttk.Label(f, style="Hint.TLabel", wraplength=760, justify="left",
                  text="安装时会关闭正在运行的 Antigravity 以释放 app.asar；首次安装会自动创建 app.asar.bak 原版备份。"
                       "macOS 打补丁后会自动进行本机 ad-hoc 重签名。IDE 编辑器界面汉化请使用官方中文语言包（见 README）。"
                  ).grid(row=8, column=0, columnspan=3, sticky="w")

    def pick_dir(self):
        from tkinter import filedialog
        p = filedialog.askdirectory(parent=self.root)
        if p:
            self.dir_var.set(p)

    def _install_dir(self):
        d = core.detect_install_dir(self.dir_var.get().strip() or None)
        if not d:
            self.msg("未找到", "未检测到 Antigravity 安装目录，请手动选择。", error=True)
        return d

    def install_l10n(self):
        d = self._install_dir()
        if not d:
            return
        if ar.is_antigravity_running() and not self.ask("需要关闭 Antigravity", "Antigravity 正在运行，安装时会将其关闭。继续吗？"):
            return
        ch = self.char_var.get()
        self.run_task("安装汉化补丁", core.install_localization, d, self.lang_var.get(),
                      None if ch.startswith("(") else ch, self.pet_var.get(), self.skinload_var.get())

    def restore_l10n(self):
        d = self._install_dir()
        if d and self.ask("还原原版", "将恢复官方原版 app.asar 并移除 IDE 皮肤，且不再自动重新注入。继续吗？"):
            self.run_task("还原官方原版", core.restore_localization, d)

    def toggle_updates(self, disable):
        d = self._install_dir()
        if d:
            self.run_task("禁止自动更新" if disable else "恢复自动更新", core.toggle_updates, d, disable)

    # ---------------- 桌宠页 ----------------
    def _build_pet(self):
        ttk = self.ttk
        f = self.tab_pet
        ttk.Label(f, text="独立桌面桌宠", style="Title.TLabel").pack(anchor="w")
        ttk.Label(f, wraplength=760, justify="left",
                  text="在 Windows 桌面上启动透明悬浮的祢豆子 / 小王子桌宠（托盘可管理）。"
                       "桌宠外观（角色、滤镜、强调色、自定义形象图、默认缩放）跟随当前材质包，"
                       "可在“自定义 → 桌宠外观”中单独调整。").pack(anchor="w", pady=6)
        ttk.Button(f, text="🐾 启动桌面桌宠", command=self.launch_pet).pack(anchor="w", pady=6)
        ttk.Button(f, text="调整桌宠外观…", command=lambda: self.nb.select(self.tab_custom)).pack(anchor="w")
        if sys.platform != "win32":
            ttk.Label(f, style="Hint.TLabel", text="当前系统不支持独立桌面桌宠，Antigravity 窗口内桌宠仍可使用。").pack(anchor="w", pady=8)

    def launch_pet(self):
        try:
            core.launch_pet()
            self.write_log("✔ 桌宠已启动")
        except Exception as e:  # noqa: BLE001
            self.msg("无法启动桌宠", str(e), error=True)

    # ---------------- 自动维护页 ----------------
    def _build_auto(self):
        tk, ttk = self.tk, self.ttk
        f = self.tab_auto
        ttk.Label(f, text="Antigravity 更新后自动重新注入", style="Title.TLabel").pack(anchor="w")
        ttk.Label(f, wraplength=760, justify="left",
                  text="开启后会添加一个当前用户级的开机自启项（Windows 注册表 Run / macOS LaunchAgent / Linux autostart），"
                       "在后台低频检测：一旦发现 Antigravity 被官方更新覆盖，会在 Antigravity 退出后自动重新打上汉化补丁、"
                       "重新注入材质包加载器并同步 IDE 皮肤。不会强行关闭正在使用的 Antigravity。"
                       "所有材质包与设置保存在用户配置目录，官方更新不会删除。").pack(anchor="w", pady=6)
        self.auto_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="开机自动检测并在更新后重新注入", variable=self.auto_var,
                        command=self.toggle_auto).pack(anchor="w", pady=6)
        ttk.Button(f, text="立即检测并修复", command=self.check_now).pack(anchor="w")
        self.auto_status = ttk.Label(f, text="", justify="left")
        self.auto_status.pack(anchor="w", pady=10)
        ttk.Button(f, text="打开配置目录", command=lambda: self.open_path(sm.config_dir())).pack(anchor="w")

    def toggle_auto(self):
        want = self.auto_var.get()
        self.run_task("开启自动重注入" if want else "关闭自动重注入",
                      (lambda: print(ar.enable_autostart())) if want else (lambda: print(ar.disable_autostart())))
        if want:
            # 立即在本进程外拉起一次后台检测，无需重启电脑
            try:
                import subprocess
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
                subprocess.Popen(ar.background_command(), creationflags=flags if sys.platform == "win32" else 0)
            except Exception as e:  # noqa: BLE001
                self.write_log(f"后台检测进程启动失败: {e}")

    def check_now(self):
        self.run_task("检测并修复", lambda: print(json.dumps(ar.check(apply=True), ensure_ascii=False)))

    # ---------------- 刷新 ----------------
    def refresh_all(self):
        try:
            self.refresh_skins()
        except Exception as e:  # noqa: BLE001
            self.write_log(f"读取材质包失败: {e}")
        self.load_custom_form()
        try:
            s = core.status()
        except Exception as e:  # noqa: BLE001
            self.write_log(f"状态读取失败: {e}")
            return
        if not self.dir_var.get() and s["install_dir"]:
            self.dir_var.set(s["install_dir"])
        self.l10n_status.configure(text=f"状态：{STATUS_TEXT.get(s['agent'], s['agent'])}")
        self.auto_var.set(bool(s["auto_reapply"] and s["autostart"]))
        self.auto_status.configure(text=(
            f"Agent 桌面端：{STATUS_TEXT.get(s['agent'], s['agent'])}\n"
            f"IDE 编辑器皮肤：{STATUS_TEXT.get(s['ide'], s['ide'])}  {s['ide_root'] or ''}\n"
            f"当前材质包：{s['active_skin'] or '无'}{'' if s['skin_enabled'] else '（已关闭）'}\n"
            f"配置目录：{s['config_dir']}"))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    rc = run_headless(argv)
    if rc is not None:
        return rc
    core.bootstrap()
    try:
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 高分屏清晰显示，需在创建窗口前调用
    except Exception:
        pass
    import tkinter as tk
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
