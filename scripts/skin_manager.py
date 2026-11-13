#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 材质包 / 皮肤系统核心模块 (skin_manager.py)

职责：
1. 用户配置目录定位（独立于 Antigravity 安装目录，官方更新不会覆盖）；
2. skin.json 清单解析、字段校验与资源路径安全检查；
3. 多层合并：材质包 ← 全局用户覆盖层 ← 单包用户覆盖层；
4. 编译为运行时载荷 (compiled/active-skin.json + active-skin.css)，
   由 app.asar 主进程钩子实时读取（切换材质包无需重新打补丁）；
5. 材质包管理：内置包同步、列出、切换、导入/导出 .zip、删除、覆盖层读写。

本模块只依赖 Python 标准库，可被 CLI、图形界面与自动重注入守护共同复用。
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
APP_DIR_NAME = "antigravity-zh-cn"
MANIFEST_NAME = "skin.json"
GLOBAL_OVERRIDE_ID = "_global"

# 资源限制，防止误导入超大或恶意压缩包
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_CSS_CHARS = 200_000
MAX_ZIP_TOTAL_BYTES = 64 * 1024 * 1024
MAX_ZIP_FILES = 500

IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}
FONT_MIME = {
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
}

BACKGROUND_TARGETS = ("window", "editor", "sidebar", "panel", "terminal", "chat")
PET_CHARACTERS = ("auto", "nezuko", "prince")

# 背景挂载目标 → 默认选择器（同时覆盖 Agent 桌面端与基于 VS Code 的 IDE 工作台）
DEFAULT_SELECTORS: dict[str, str] = {
    "window": "body",
    "editor": ".monaco-workbench .part.editor > .content",
    "sidebar": ".monaco-workbench .part.sidebar, .monaco-workbench .part.auxiliarybar",
    "panel": ".monaco-workbench .part.panel",
    "terminal": ".monaco-workbench .terminal-wrapper",
    "chat": "main, [role='main']",
}

# 语义化颜色键 → CSS 变量（--agzh-* 为本项目统一变量，--vscode-* 覆盖 IDE 工作台）
COLOR_VARIABLES: dict[str, list[str]] = {
    "background": ["--agzh-bg", "--vscode-editor-background", "--vscode-editorGutter-background"],
    "foreground": ["--agzh-fg", "--vscode-foreground", "--vscode-editor-foreground"],
    "accent": ["--agzh-accent", "--vscode-focusBorder", "--vscode-button-background",
               "--vscode-progressBar-background", "--vscode-activityBarBadge-background",
               "--vscode-textLink-foreground"],
    "accentForeground": ["--agzh-accent-fg", "--vscode-button-foreground", "--vscode-activityBarBadge-foreground"],
    "sidebar": ["--agzh-sidebar", "--vscode-sideBar-background", "--vscode-sideBarSectionHeader-background"],
    "activityBar": ["--agzh-activitybar", "--vscode-activityBar-background"],
    "titleBar": ["--agzh-titlebar", "--vscode-titleBar-activeBackground", "--vscode-titleBar-inactiveBackground"],
    "statusBar": ["--agzh-statusbar", "--vscode-statusBar-background"],
    "panel": ["--agzh-panel", "--vscode-panel-background", "--vscode-terminal-background"],
    "border": ["--agzh-border", "--vscode-panel-border", "--vscode-sideBar-border", "--vscode-editorGroup-border"],
    "selection": ["--agzh-selection", "--vscode-editor-selectionBackground", "--vscode-list-activeSelectionBackground"],
    "input": ["--agzh-input", "--vscode-input-background", "--vscode-dropdown-background"],
    "muted": ["--agzh-muted", "--vscode-descriptionForeground"],
}

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_VERSION_RE = re.compile(r"^\d+(\.\d+){0,3}([-+][0-9A-Za-z.-]+)?$")
_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_FUNC_COLOR_RE = re.compile(r"^(rgb|rgba|hsl|hsla)\(\s*[0-9.,%\s/+-]+\)$")
_NAMED_COLOR_RE = re.compile(r"^[a-zA-Z]{3,30}$")
_VAR_NAME_RE = re.compile(r"^--[A-Za-z0-9_-]{1,80}$")
_POSITION_RE = re.compile(r"^[a-z0-9%.\s-]{1,40}$")
_SIZE_RE = re.compile(r"^(cover|contain|auto|[0-9.]+(px|%|vw|vh)(\s+[0-9.]+(px|%|vw|vh)|\s+auto)?)$")
_REPEAT_VALUES = ("no-repeat", "repeat", "repeat-x", "repeat-y", "round", "space")
_BLEND_VALUES = ("normal", "multiply", "screen", "overlay", "soft-light", "hard-light", "luminosity", "color")
_FONT_FAMILY_RE = re.compile(r"^[^;{}<>\\]{1,200}$")
_FILTER_RE = re.compile(r"^[a-z0-9().,%\s-]{1,200}$")
_CODICON_RE = re.compile(r"^[a-z0-9-]{1,60}$")
_UNSAFE_VALUE_RE = re.compile(r"[;{}<>\\]|/\*|\*/")


class SkinError(Exception):
    """材质包加载/校验失败"""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


# ---------------------------------------------------------------------------
# 1. 路径
# ---------------------------------------------------------------------------
def config_dir() -> Path:
    """用户配置根目录（材质包、当前选择、覆盖层、编译产物、状态文件）。

    - 环境变量 AGZH_CONFIG_DIR 优先（测试与便携模式）；
    - Windows: %APPDATA%\\antigravity-zh-cn
    - macOS:   ~/Library/Application Support/antigravity-zh-cn
    - Linux:   $XDG_CONFIG_HOME/antigravity-zh-cn (默认 ~/.config/antigravity-zh-cn)
    """
    env = os.environ.get("AGZH_CONFIG_DIR")
    if env:
        return Path(env).expanduser()
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_DIR_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_DIR_NAME


def skins_dir() -> Path:
    return config_dir() / "skins"


def overrides_dir() -> Path:
    return config_dir() / "overrides"


def compiled_dir() -> Path:
    return config_dir() / "compiled"


def compiled_payload_path() -> Path:
    return compiled_dir() / "active-skin.json"


def compiled_css_path() -> Path:
    return compiled_dir() / "active-skin.css"


def state_path() -> Path:
    return config_dir() / "state.json"


def resource_root() -> Path:
    """仓库或打包程序的资源根目录（含 resources/、scripts/）。"""
    env = os.environ.get("AGZH_REPO_ROOT")
    if env:
        return Path(env)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def builtin_skins_dir() -> Path:
    return resource_root() / "resources" / "skins"


# ---------------------------------------------------------------------------
# 2. 状态文件
# ---------------------------------------------------------------------------
def _atomic_write_text(path: Path, text: str) -> None:
    """原子写入。

    - 临时文件名带进程号与线程号：图形界面与后台守护进程同时写 state.json 时不会互相覆盖临时文件；
    - Windows 上目标文件正被其他进程（例如 Antigravity 主进程读取 active-skin.json）短暂打开时，
      os.replace 会抛 PermissionError，这里做短暂重试而不是直接失败。
    """
    import threading
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    last: Exception | None = None
    for attempt in range(20):
        try:
            os.replace(tmp, path)
            return
        except PermissionError as e:  # pragma: no cover - 仅 Windows 文件共享冲突
            last = e
            time.sleep(0.05 * (attempt + 1))
    try:
        tmp.unlink()
    except OSError:
        pass
    raise last  # type: ignore[misc]


class FileLock:
    """跨进程文件锁（Windows 使用 msvcrt.locking，Unix 使用 fcntl.flock）。

    用于保护 state.json 的“读-改-写”以及 app.asar 的重新注入，
    防止图形界面、命令行与开机后台守护同时操作时互相覆盖。
    内核级锁机制，进程退出或崩溃时由操作系统自动安全释放。
    """

    def __init__(self, path: Path, timeout: float = 20.0, stale: float = 30.0):
        self.path = Path(path)
        self.timeout = timeout
        self.stale = stale
        self._fd: int | None = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._fd = os.open(str(self.path), os.O_RDWR | os.O_CREAT)
                locked = False
                try:
                    import msvcrt
                    msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
                    locked = True
                except (ImportError, AttributeError):
                    pass
                if not locked:
                    try:
                        import fcntl
                        fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except (ImportError, AttributeError):
                        pass
                return True
            except (OSError, IOError):
                if self._fd is not None:
                    try:
                        os.close(self._fd)
                    except OSError:
                        pass
                    self._fd = None
                if time.monotonic() >= deadline:
                    return False
                time.sleep(0.005)

    def release(self) -> None:
        if self._fd is not None:
            unlocked = False
            try:
                import msvcrt
                msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
                unlocked = True
            except (ImportError, AttributeError, OSError):
                pass
            if not unlocked:
                try:
                    import fcntl
                    fcntl.flock(self._fd, fcntl.LOCK_UN)
                except (ImportError, AttributeError, OSError):
                    pass
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
            try:
                self.path.unlink(missing_ok=True)
            except OSError:
                pass

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"等待文件锁超时: {self.path}")
        return self

    def __exit__(self, *exc):
        self.release()
        return False


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return False
            code = ctypes.c_ulong()
            ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
            ctypes.windll.kernel32.CloseHandle(h)
            return code.value == 259  # STILL_ACTIVE
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def load_state() -> dict:
    p = state_path()
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def save_state(state: dict) -> None:
    _atomic_write_text(state_path(), json.dumps(state, ensure_ascii=False, indent=2))


def update_state(**changes: Any) -> dict:
    """读-改-写 state.json；跨进程加锁，避免界面与后台守护同时更新时丢失字段。"""
    lock = FileLock(config_dir() / ".state.lock", timeout=20.0, stale=30.0)
    with lock:
        st = load_state()
        for k, v in changes.items():
            if isinstance(v, dict) and isinstance(st.get(k), dict):
                st[k].update(v)
            else:
                st[k] = v
        save_state(st)
        return st


# ---------------------------------------------------------------------------
# 3. 清单校验
# ---------------------------------------------------------------------------
def is_css_color(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip()
    return bool(_HEX_RE.match(v) or _FUNC_COLOR_RE.match(v) or _NAMED_COLOR_RE.match(v))


def _safe_rel_path(value: Any) -> bool:
    """资源路径必须是材质包内部的相对路径（拒绝绝对路径与 .. 穿越）。"""
    if not isinstance(value, str) or not value.strip():
        return False
    v = value.replace("\\", "/")
    if v.startswith("/") or re.match(r"^[A-Za-z]:", v) or "://" in v:
        return False
    return ".." not in v.split("/")


def _num_in(value: Any, lo: float, hi: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and lo <= value <= hi


def _normalize_backgrounds(bg: Any) -> list:
    if bg is None:
        return []
    if isinstance(bg, list):
        return bg
    return [bg]


def validate_manifest(data: Any, base_dir: Path | None = None, *, partial: bool = False) -> list[str]:
    """校验 skin.json，返回中文错误列表（空列表表示合法）。

    partial=True 用于用户覆盖层：不要求 id/name/version 等元数据。
    base_dir 提供时会检查引用的资源文件是否存在、大小是否超限。
    """
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["清单根节点必须是 JSON 对象"]

    def check_file(field: str, value: Any, allowed: dict[str, str]):
        if not _safe_rel_path(value):
            errors.append(f"{field}: 资源路径必须是材质包内的相对路径（不允许绝对路径或 ..）: {value!r}")
            return
        ext = Path(str(value)).suffix.lower()
        if ext not in allowed:
            errors.append(f"{field}: 不支持的文件类型 {ext or '(无扩展名)'}，允许: {', '.join(sorted(allowed))}")
            return
        if base_dir is not None:
            fp = (base_dir / str(value)).resolve()
            try:
                fp.relative_to(base_dir.resolve())
            except ValueError:
                errors.append(f"{field}: 资源路径越出材质包目录: {value!r}")
                return
            if not fp.is_file():
                errors.append(f"{field}: 找不到资源文件 {value}")
            elif fp.stat().st_size > MAX_IMAGE_BYTES:
                errors.append(f"{field}: 文件过大 ({fp.stat().st_size // 1024} KB)，上限 {MAX_IMAGE_BYTES // 1024 // 1024} MB")

    if not partial:
        schema = data.get("schema", SCHEMA_VERSION)
        if schema != SCHEMA_VERSION:
            errors.append(f"schema: 不支持的清单版本 {schema!r}（当前支持 {SCHEMA_VERSION}）")
        sid = data.get("id")
        if not isinstance(sid, str) or not _ID_RE.match(sid) or sid == GLOBAL_OVERRIDE_ID:
            errors.append("id: 必填，只能包含小写字母、数字、点、下划线和短横线（1-64 位）")
        name = data.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 80:
            errors.append("name: 必填，1-80 个字符")
        ver = data.get("version")
        if not isinstance(ver, str) or not _VERSION_RE.match(ver):
            errors.append("version: 必填，形如 1.0.0")
    for key in ("author", "description"):
        if key in data and not isinstance(data[key], str):
            errors.append(f"{key}: 必须是字符串")
    if "base" in data and data["base"] not in ("dark", "light"):
        errors.append("base: 只能是 dark 或 light")
    if "preview" in data and data["preview"] is not None:
        check_file("preview", data["preview"], IMAGE_MIME)

    colors = data.get("colors")
    if colors is not None:
        if not isinstance(colors, dict):
            errors.append("colors: 必须是对象")
        else:
            for k, v in colors.items():
                if v is None:
                    continue
                if k not in COLOR_VARIABLES:
                    errors.append(f"colors.{k}: 未知颜色键，可用: {', '.join(COLOR_VARIABLES)}")
                elif not is_css_color(v):
                    errors.append(f"colors.{k}: 不是合法的 CSS 颜色: {v!r}")

    variables = data.get("variables")
    if variables is not None:
        if not isinstance(variables, dict):
            errors.append("variables: 必须是对象")
        else:
            for k, v in variables.items():
                if v is None:
                    continue
                if not isinstance(k, str) or not _VAR_NAME_RE.match(k):
                    errors.append(f"variables: 变量名必须以 -- 开头: {k!r}")
                elif not isinstance(v, (str, int, float)) or _UNSAFE_VALUE_RE.search(str(v)):
                    errors.append(f"variables.{k}: 取值不能包含 ; {{ }} < > \\ 或注释符")

    selectors = data.get("selectors")
    if selectors is not None:
        if not isinstance(selectors, dict):
            errors.append("selectors: 必须是对象")
        else:
            for k, v in selectors.items():
                if k not in BACKGROUND_TARGETS:
                    errors.append(f"selectors.{k}: 未知目标，可用: {', '.join(BACKGROUND_TARGETS)}")
                elif v is not None and (not isinstance(v, str) or re.search(r"[{};<]", v)):
                    errors.append(f"selectors.{k}: 选择器不能包含 {{ }} ; <")

    for i, bg in enumerate(_normalize_backgrounds(data.get("background"))):
        f = f"background[{i}]"
        if not isinstance(bg, dict):
            errors.append(f"{f}: 必须是对象")
            continue
        if "image" in bg and bg["image"] is not None:
            check_file(f"{f}.image", bg["image"], IMAGE_MIME)
        elif not partial:
            errors.append(f"{f}.image: 必填")
        if "target" in bg and bg["target"] not in BACKGROUND_TARGETS:
            errors.append(f"{f}.target: 只能是 {', '.join(BACKGROUND_TARGETS)}")
        if "opacity" in bg and not _num_in(bg["opacity"], 0, 1):
            errors.append(f"{f}.opacity: 必须是 0~1 之间的数字")
        if "blur" in bg and not _num_in(bg["blur"], 0, 100):
            errors.append(f"{f}.blur: 必须是 0~100 之间的数字 (px)")
        if "position" in bg and (not isinstance(bg["position"], str) or not _POSITION_RE.match(bg["position"])):
            errors.append(f"{f}.position: 形如 center / top right / 50% 30%")
        if "size" in bg and (not isinstance(bg["size"], str) or not _SIZE_RE.match(bg["size"])):
            errors.append(f"{f}.size: 只能是 cover / contain / auto / 具体尺寸")
        if "repeat" in bg and bg["repeat"] not in _REPEAT_VALUES:
            errors.append(f"{f}.repeat: 只能是 {', '.join(_REPEAT_VALUES)}")
        if "blend" in bg and bg["blend"] not in _BLEND_VALUES:
            errors.append(f"{f}.blend: 只能是 {', '.join(_BLEND_VALUES)}")

    font = data.get("font")
    if font is not None:
        if not isinstance(font, dict):
            errors.append("font: 必须是对象")
        else:
            for k in ("family", "monoFamily"):
                if font.get(k) is not None and (not isinstance(font[k], str) or not _FONT_FAMILY_RE.match(font[k])):
                    errors.append(f"font.{k}: 字体名不能为空或包含 ; {{ }} < > \\")
            for k, lo, hi in (("size", 8, 40), ("monoSize", 8, 40)):
                if font.get(k) is not None and not _num_in(font[k], lo, hi):
                    errors.append(f"font.{k}: 必须是 {lo}~{hi} 之间的数字")
            if font.get("ligatures") is not None and not isinstance(font["ligatures"], bool):
                errors.append("font.ligatures: 必须是 true 或 false")
            if font.get("file") is not None:
                check_file("font.file", font["file"], FONT_MIME)

    icons = data.get("icons")
    if icons is not None:
        if not isinstance(icons, dict):
            errors.append("icons: 必须是对象")
        else:
            if icons.get("filter") is not None and (not isinstance(icons["filter"], str) or not _FILTER_RE.match(icons["filter"])):
                errors.append("icons.filter: 必须是 CSS filter 表达式，例如 hue-rotate(300deg) saturate(1.4)")
            if icons.get("color") is not None and not is_css_color(icons["color"]):
                errors.append("icons.color: 不是合法的 CSS 颜色")
            cmap = icons.get("codicons")
            if cmap is not None:
                if not isinstance(cmap, dict):
                    errors.append("icons.codicons: 必须是对象 {图标名: 图片路径}")
                else:
                    for name, path in cmap.items():
                        if not _CODICON_RE.match(str(name)):
                            errors.append(f"icons.codicons: 图标名不合法: {name!r}")
                        elif path is not None:
                            check_file(f"icons.codicons.{name}", path, IMAGE_MIME)
            smap = icons.get("selectors")
            if smap is not None:
                if not isinstance(smap, dict):
                    errors.append("icons.selectors: 必须是对象 {CSS 选择器: 图片路径}")
                else:
                    for sel, path in smap.items():
                        if re.search(r"[{};<]", str(sel)):
                            errors.append(f"icons.selectors: 选择器不能包含 {{ }} ; <: {sel!r}")
                        elif path is not None:
                            check_file(f"icons.selectors[{sel}]", path, IMAGE_MIME)

    if data.get("css") is not None:
        if not isinstance(data["css"], str):
            errors.append("css: 必须是字符串")
        elif len(data["css"]) > MAX_CSS_CHARS:
            errors.append(f"css: 超过 {MAX_CSS_CHARS} 字符上限")
        elif "</style" in data["css"].lower():
            errors.append("css: 不能包含 </style")
    if data.get("cssFile") is not None:
        check_file("cssFile", data["cssFile"], {".css": "text/css"})

    pet = data.get("pet")
    if pet is not None:
        if not isinstance(pet, dict):
            errors.append("pet: 必须是对象")
        else:
            if pet.get("character") is not None and pet["character"] not in PET_CHARACTERS:
                errors.append(f"pet.character: 只能是 {', '.join(PET_CHARACTERS)}")
            if pet.get("sprite") is not None:
                check_file("pet.sprite", pet["sprite"], IMAGE_MIME)
            if pet.get("filter") is not None and (not isinstance(pet["filter"], str) or not _FILTER_RE.match(pet["filter"])):
                errors.append("pet.filter: 必须是 CSS filter 表达式")
            if pet.get("accent") is not None and not is_css_color(pet["accent"]):
                errors.append("pet.accent: 不是合法的 CSS 颜色")
            if pet.get("scale") is not None and not _num_in(pet["scale"], 0.3, 3):
                errors.append("pet.scale: 必须是 0.3~3 之间的数字")
            if pet.get("hidden") is not None and not isinstance(pet["hidden"], bool):
                errors.append("pet.hidden: 必须是 true 或 false")
            if pet.get("css") is not None and (not isinstance(pet["css"], str) or len(pet["css"]) > MAX_CSS_CHARS):
                errors.append("pet.css: 必须是字符串且不超过上限")
    return errors


# ---------------------------------------------------------------------------
# 4. 材质包对象、资源解析与多层合并
# ---------------------------------------------------------------------------
def _resolve_assets(data: dict, base_dir: Path) -> dict:
    """把一层清单中的相对资源路径解析为绝对路径（合并前逐层执行，保证各层资源相对各自目录）。"""
    out = copy.deepcopy(data)
    base = base_dir.resolve()

    def r(v):
        return str((base / str(v)).resolve()) if isinstance(v, str) and v else v

    if out.get("preview"):
        out["preview"] = r(out["preview"])
    bgs = out.get("background")
    if isinstance(bgs, dict):
        if bgs.get("image"):
            bgs["image"] = r(bgs["image"])
    elif isinstance(bgs, list):
        for bg in bgs:
            if isinstance(bg, dict) and bg.get("image"):
                bg["image"] = r(bg["image"])
    if isinstance(out.get("font"), dict) and out["font"].get("file"):
        out["font"]["file"] = r(out["font"]["file"])
    icons = out.get("icons")
    if isinstance(icons, dict):
        for key in ("codicons", "selectors"):
            if isinstance(icons.get(key), dict):
                icons[key] = {k: r(v) for k, v in icons[key].items()}
    if isinstance(out.get("pet"), dict) and out["pet"].get("sprite"):
        out["pet"]["sprite"] = r(out["pet"]["sprite"])
    if out.get("cssFile"):
        css_path = Path(r(out.pop("cssFile")))
        extra = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
        out["css"] = (out.get("css") or "") + ("\n" if out.get("css") else "") + extra
    return out


def deep_merge(base: Any, override: Any) -> Any:
    """深度合并：对象递归合并，数组与标量整体替换；覆盖层中的 null 表示删除该键。"""
    if not isinstance(base, dict) or not isinstance(override, dict):
        return copy.deepcopy(override)
    out = copy.deepcopy(base)
    for k, v in override.items():
        cur = out.get(k)
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(cur, dict):
            out[k] = deep_merge(cur, v)
        elif isinstance(cur, list) and cur and all(isinstance(x, dict) for x in cur) and isinstance(v, dict):
            # 对象数组（如多张背景）被单个对象覆盖：只调整第一项（主背景）
            out[k] = [deep_merge(cur[0], v)] + copy.deepcopy(cur[1:])
        elif isinstance(cur, list) and isinstance(v, list) and all(isinstance(x, dict) for x in cur):
            # 对象数组按下标逐项合并；覆盖层中某项为 null 表示删除该项
            merged = []
            for idx in range(max(len(cur), len(v))):
                b = cur[idx] if idx < len(cur) else None
                o = v[idx] if idx < len(v) else {}
                if idx < len(v) and o is None:
                    continue
                if b is None:
                    merged.append(copy.deepcopy(o))
                elif isinstance(o, dict):
                    merged.append(deep_merge(b, o))
                else:
                    merged.append(copy.deepcopy(o))
            out[k] = merged
        else:
            out[k] = copy.deepcopy(v)
    return out


class SkinPack:
    def __init__(self, path: Path, manifest: dict):
        self.path = path
        self.manifest = manifest

    @property
    def id(self) -> str:
        return self.manifest["id"]

    @property
    def name(self) -> str:
        return self.manifest.get("name", self.id)

    @property
    def version(self) -> str:
        return self.manifest.get("version", "0")

    def preview_path(self) -> Path | None:
        p = self.manifest.get("preview")
        if p and (self.path / p).is_file():
            return self.path / p
        return None

    def to_info(self) -> dict:
        m = self.manifest
        return {
            "id": self.id, "name": self.name, "version": self.version,
            "author": m.get("author", ""), "description": m.get("description", ""),
            "base": m.get("base", "dark"), "path": str(self.path),
            "builtin": bool(m.get("builtin")),
            "preview": str(self.preview_path()) if self.preview_path() else None,
            "colors": dict(m.get("colors") or {}),
        }


def load_pack(pack_dir: Path) -> SkinPack:
    pack_dir = Path(pack_dir)
    mf = pack_dir / MANIFEST_NAME
    if not mf.is_file():
        raise SkinError(f"未找到 {MANIFEST_NAME}: {pack_dir}")
    try:
        data = json.loads(mf.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise SkinError(f"{MANIFEST_NAME} 不是合法 JSON: 第 {e.lineno} 行第 {e.colno} 列: {e.msg}", [str(e)])
    errors = validate_manifest(data, pack_dir)
    if errors:
        raise SkinError(f"材质包 {pack_dir.name} 校验失败：\n  - " + "\n  - ".join(errors), errors)
    return SkinPack(pack_dir, data)


def list_packs() -> list[SkinPack]:
    """列出用户目录中所有可用材质包（无效包被跳过）。"""
    root = skins_dir()
    packs: list[SkinPack] = []
    if not root.is_dir():
        return packs
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d / MANIFEST_NAME).is_file():
            try:
                packs.append(load_pack(d))
            except SkinError:
                continue
    return packs


def get_pack(skin_id: str) -> SkinPack:
    d = skins_dir() / skin_id
    if not _ID_RE.match(skin_id or "") or not d.is_dir():
        raise SkinError(f"未找到材质包: {skin_id}")
    return load_pack(d)


def _version_tuple(v: str) -> tuple:
    nums = re.findall(r"\d+", v.split("-")[0].split("+")[0])
    return tuple(int(n) for n in nums[:4])


def sync_builtin_packs(force: bool = False) -> list[str]:
    """把仓库/程序内置的示例材质包复制到用户目录。

    已存在的同名包只在内置版本更新且该包仍标记为 builtin 时覆盖，避免冲掉用户修改。
    """
    src_root = builtin_skins_dir()
    installed: list[str] = []
    if not src_root.is_dir():
        return installed
    dst_root = skins_dir()
    dst_root.mkdir(parents=True, exist_ok=True)
    removed = set(load_state().get("removed_builtin") or [])
    for src in sorted(src_root.iterdir()):
        if not (src / MANIFEST_NAME).is_file():
            continue
        try:
            pack = load_pack(src)
        except SkinError:
            continue
        dst = dst_root / pack.id
        if not force and not dst.exists() and pack.id in removed:
            continue  # 用户主动删除过的内置包，不在每次启动时“复活”
        if dst.exists() and not force:
            try:
                cur = json.loads((dst / MANIFEST_NAME).read_text(encoding="utf-8-sig"))
            except Exception:
                cur = {}
            if not cur.get("builtin") or _version_tuple(cur.get("version", "0")) >= _version_tuple(pack.version):
                continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        m = dict(pack.manifest)
        m["builtin"] = True
        (dst / MANIFEST_NAME).write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
        installed.append(pack.id)
    if force and removed:
        update_state(removed_builtin=[])
    return installed


# ---------------------------------------------------------------------------
# 5. 用户覆盖层
# ---------------------------------------------------------------------------
def override_path(skin_id: str | None) -> Path:
    return overrides_dir() / f"{skin_id or GLOBAL_OVERRIDE_ID}.json"


def load_override(skin_id: str | None) -> dict:
    p = override_path(skin_id)
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def save_override(skin_id: str | None, data: dict) -> None:
    errors = validate_manifest(data, overrides_dir(), partial=True)
    if errors:
        raise SkinError("覆盖层校验失败：\n  - " + "\n  - ".join(errors), errors)
    _atomic_write_text(override_path(skin_id), json.dumps(data, ensure_ascii=False, indent=2))


def reset_override(skin_id: str | None) -> None:
    p = override_path(skin_id)
    if p.exists():
        p.unlink()


def import_override_asset(src: Path) -> str:
    """把用户在界面中选择的图片/字体复制进覆盖层资源目录，返回可写入覆盖层的相对路径。"""
    src = Path(src)
    if not src.is_file():
        raise SkinError(f"文件不存在: {src}")
    ext = src.suffix.lower()
    if ext not in IMAGE_MIME and ext not in FONT_MIME:
        raise SkinError(f"不支持的文件类型: {ext}")
    if src.stat().st_size > MAX_IMAGE_BYTES:
        raise SkinError("文件过大（上限 8 MB）")
    digest = hashlib.sha256(src.read_bytes()).hexdigest()[:12]
    dst_dir = overrides_dir() / "assets"
    dst_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^A-Za-z0-9._-]", "_", src.stem)[:40] or "asset"
    dst = dst_dir / f"{safe_stem}-{digest}{ext}"
    if not dst.exists():
        shutil.copy2(src, dst)
    return f"assets/{dst.name}"


def set_override_value(skin_id: str | None, dotted_key: str, value: Any) -> dict:
    """命令行便捷写法：skin override set background.opacity 0.2"""
    data = load_override(skin_id)
    node = data
    parts = dotted_key.split(".")
    for p in parts[:-1]:
        if not isinstance(node.get(p), dict):
            node[p] = {}
        node = node[p]
    node[parts[-1]] = value
    save_override(skin_id, data)
    return data


def effective_manifest(pack: SkinPack) -> dict:
    """材质包 ← 全局覆盖层 ← 单包覆盖层，逐层解析资源后深度合并。"""
    merged = _resolve_assets(pack.manifest, pack.path)
    for layer_id in (None, pack.id):
        layer = load_override(layer_id)
        if layer:
            layer = _resolve_assets(layer, overrides_dir())
            # 覆盖层的 css 追加在材质包 css 之后（而不是替换），便于“在别人的包上再微调”
            extra_css = layer.pop("css", None)
            merged = deep_merge(merged, layer)
            if extra_css:
                merged["css"] = (merged.get("css") or "") + "\n/* user override */\n" + extra_css
    return merged


# ---------------------------------------------------------------------------
# 6. 编译：manifest → CSS + 运行时载荷
# ---------------------------------------------------------------------------
def _data_uri(path: str | Path) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    mime = IMAGE_MIME.get(ext) or FONT_MIME.get(ext) or "application/octet-stream"
    data = p.read_bytes()
    if len(data) > MAX_IMAGE_BYTES:
        raise SkinError(f"资源过大: {p.name}")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _css_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _font_stack(family: str) -> str:
    parts = [f.strip() for f in family.split(",") if f.strip()]
    generic = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-monospace"}
    return ", ".join(p if (p in generic or p.startswith(("'", '"'))) else _css_str(p) for p in parts)


def build_css(m: dict, *, embed_fonts: bool = True) -> str:
    """把合并后的清单编译为一段可注入的 CSS。

    背景采用 ::before/::after 伪元素“覆盖层”方案（pointer-events:none），
    不需要把原界面各层改为透明即可获得半透明背景，兼容性最好。
    """
    out: list[str] = [f"/* antigravity-zh-cn skin: {m.get('id', 'override')} {m.get('version', '')} */"]
    selectors = dict(DEFAULT_SELECTORS)
    for k, v in (m.get("selectors") or {}).items():
        if v:
            selectors[k] = v

    # 6.1 颜色与变量
    decls: list[str] = []
    for key, value in (m.get("colors") or {}).items():
        if value is None or key not in COLOR_VARIABLES:
            continue
        for var in COLOR_VARIABLES[key]:
            decls.append(f"{var}: {value} !important;")
    for var, value in (m.get("variables") or {}).items():
        if value is not None:
            decls.append(f"{var}: {value} !important;")
    font = m.get("font") or {}
    if font.get("family"):
        decls.append(f"--agzh-font: {_font_stack(font['family'])} !important;")
        decls.append(f"--vscode-font-family: {_font_stack(font['family'])} !important;")
    if font.get("monoFamily"):
        decls.append(f"--agzh-mono-font: {_font_stack(font['monoFamily'])} !important;")
        decls.append(f"--vscode-editor-font-family: {_font_stack(font['monoFamily'])} !important;")
    if font.get("size"):
        decls.append(f"--vscode-font-size: {font['size']}px !important;")
    if decls:
        out.append(":root, body, .monaco-workbench {\n  " + "\n  ".join(decls) + "\n}")

    colors = m.get("colors") or {}
    if colors.get("background") or colors.get("foreground"):
        rule = []
        if colors.get("background"):
            rule.append(f"background-color: {colors['background']} !important;")
        if colors.get("foreground"):
            rule.append(f"color: {colors['foreground']};")
        out.append("html, body {\n  " + "\n  ".join(rule) + "\n}")
    if colors.get("selection"):
        out.append(f"::selection {{ background: {colors['selection']}; }}")
    if colors.get("accent"):
        out.append(f"::-webkit-scrollbar-thumb {{ background-color: color-mix(in srgb, {colors['accent']} 45%, transparent) !important; }}")

    # 6.2 字体
    if font.get("file") and embed_fonts:
        out.append("@font-face {\n  font-family: \"AGZH Skin Font\";\n"
                   f"  src: url(\"{_data_uri(font['file'])}\");\n  font-display: swap;\n}}")
    if font.get("family") or font.get("size"):
        rule = []
        if font.get("family"):
            fam = _font_stack(font["family"])
            if font.get("file") and embed_fonts:
                fam = '"AGZH Skin Font", ' + fam
            rule.append(f"font-family: {fam} !important;")
        if font.get("size"):
            rule.append(f"font-size: {font['size']}px;")
        out.append("body, .monaco-workbench, button, input, select {\n  " + "\n  ".join(rule) + "\n}")
    if font.get("monoFamily") or font.get("monoSize") or font.get("ligatures") is not None:
        rule = []
        if font.get("monoFamily"):
            rule.append(f"font-family: {_font_stack(font['monoFamily'])} !important;")
        if font.get("monoSize"):
            rule.append(f"font-size: {font['monoSize']}px !important;")
        if font.get("ligatures") is not None:
            rule.append(f"font-variant-ligatures: {'normal' if font['ligatures'] else 'none'} !important;")
        out.append("pre, code, .monaco-editor .view-lines, .xterm-rows {\n  " + "\n  ".join(rule) + "\n}")

    # 6.3 背景图（可多张，分别挂到 window / editor / sidebar ...）
    used_pseudo: dict[str, str] = {}
    for bg in _normalize_backgrounds(m.get("background")):
        if not isinstance(bg, dict) or not bg.get("image"):
            continue
        target = bg.get("target", "window")
        sel = selectors.get(target, DEFAULT_SELECTORS["window"])
        pseudo = "::after" if used_pseudo.get(sel) == "::before" else "::before"
        used_pseudo[sel] = pseudo
        opacity = bg.get("opacity", 0.15)
        blur = bg.get("blur", 0)
        position = bg.get("position", "center")
        size = bg.get("size", "cover")
        repeat = bg.get("repeat", "no-repeat")
        fixed = "fixed" if target == "window" else "absolute"
        sel_list = [s.strip() for s in sel.split(",") if s.strip()]
        host = ", ".join(sel_list)
        pseudo_sel = ", ".join(s + pseudo for s in sel_list)
        lines = [
            'content: "";', f"position: {fixed};", "inset: 0;" if blur == 0 else f"inset: -{blur * 2}px;",
            f'background-image: url("{_data_uri(bg["image"])}");',
            f"background-position: {position};", f"background-size: {size};", f"background-repeat: {repeat};",
            f"opacity: {opacity};", "pointer-events: none;", "z-index: 2147483000;",
        ]
        if blur:
            lines.append(f"filter: blur({blur}px);")
        if bg.get("blend"):
            lines.append(f"mix-blend-mode: {bg['blend']};")
        if target != "window":
            out.append(f"{host} {{ position: relative; }}")
        out.append(f"{pseudo_sel} {{\n  " + "\n  ".join(lines) + "\n}")

    # 6.4 图标
    icons = m.get("icons") or {}
    if icons.get("filter"):
        out.append(f".codicon, .monaco-icon-label::before, svg.agzh-icon {{ filter: {icons['filter']}; }}")
    if icons.get("color"):
        out.append(f".codicon {{ color: {icons['color']} !important; }}")
    for name, path in (icons.get("codicons") or {}).items():
        if not path:
            continue
        out.append(
            f".codicon.codicon-{name}::before {{ content: \"\" !important; display: inline-block; width: 16px; height: 16px; "
            f'background: url("{_data_uri(path)}") center / contain no-repeat; }}'
        )
    for sel, path in (icons.get("selectors") or {}).items():
        if not path:
            continue
        out.append(f'{sel} {{ background-image: url("{_data_uri(path)}") !important; background-size: contain !important; background-repeat: no-repeat !important; }}')

    # 6.5 自定义 CSS 放最后，优先级最高
    if m.get("css"):
        out.append("/* custom css */\n" + m["css"])
    return "\n".join(out) + "\n"


def build_pet_payload(m: dict) -> dict:
    pet = dict(m.get("pet") or {})
    if pet.get("sprite"):
        pet["sprite"] = _data_uri(pet["sprite"])
    if not pet.get("accent") and (m.get("colors") or {}).get("accent"):
        pet["accent"] = m["colors"]["accent"]
    return pet


def compile_skin(pack: SkinPack) -> dict:
    m = effective_manifest(pack)
    errors = validate_manifest(_strip_abs_for_validation(m), None, partial=True)
    if errors:
        raise SkinError("合并覆盖层后校验失败：\n  - " + "\n  - ".join(errors), errors)
    css = build_css(m)
    pet = build_pet_payload(m)
    digest = hashlib.sha256((css + json.dumps(pet, sort_keys=True)).encode("utf-8")).hexdigest()
    return {
        "schema": SCHEMA_VERSION,
        "id": pack.id,
        "name": pack.name,
        "version": pack.version,
        "base": m.get("base", "dark"),
        "css": css,
        "pet": pet,
        "hash": digest,
        "generatedAt": int(time.time()),
        "disabled": False,
    }


def _strip_abs_for_validation(m: dict) -> dict:
    """合并结果中资源已是绝对路径，二次校验时只检查值域，跳过路径检查。"""
    m = copy.deepcopy(m)
    for k in ("preview",):
        m.pop(k, None)
    for bg in _normalize_backgrounds(m.get("background")):
        if isinstance(bg, dict):
            bg.pop("image", None)
    if isinstance(m.get("font"), dict):
        m["font"].pop("file", None)
    if isinstance(m.get("icons"), dict):
        m["icons"].pop("codicons", None)
        m["icons"].pop("selectors", None)
    if isinstance(m.get("pet"), dict):
        m["pet"].pop("sprite", None)
    return m


def write_compiled(payload: dict) -> Path:
    _atomic_write_text(compiled_css_path(), payload.get("css", ""))
    _atomic_write_text(compiled_payload_path(), json.dumps(payload, ensure_ascii=False))
    return compiled_payload_path()


def read_compiled() -> dict | None:
    p = compiled_payload_path()
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def activate(skin_id: str) -> dict:
    """切换材质包：编译并写入运行时载荷。Agent 桌面端通过文件监听实时生效。"""
    pack = get_pack(skin_id)
    payload = compile_skin(pack)
    write_compiled(payload)
    update_state(active_skin=skin_id, skin_enabled=True)
    return payload


def recompile_active() -> dict | None:
    st = load_state()
    sid = st.get("active_skin")
    if not sid or st.get("skin_enabled") is False:
        return None
    return activate(sid)


def deactivate() -> dict:
    """关闭皮肤（保留选择），写入 disabled 载荷让运行中的界面移除样式。"""
    payload = {"schema": SCHEMA_VERSION, "id": None, "css": "", "pet": {}, "hash": "", "disabled": True,
               "generatedAt": int(time.time())}
    write_compiled(payload)
    update_state(skin_enabled=False)
    return payload


def remove_pack(skin_id: str) -> None:
    d = skins_dir() / skin_id
    if not _ID_RE.match(skin_id or "") or not d.is_dir():
        raise SkinError(f"未找到材质包: {skin_id}")
    was_builtin = False
    try:
        was_builtin = bool(json.loads((d / MANIFEST_NAME).read_text(encoding="utf-8-sig")).get("builtin"))
    except Exception:
        pass
    shutil.rmtree(d)
    reset_override(skin_id)
    st = load_state()
    if was_builtin:
        removed = list(dict.fromkeys(list(st.get("removed_builtin") or []) + [skin_id]))
        update_state(removed_builtin=removed)
    if st.get("active_skin") == skin_id:
        deactivate()
        update_state(active_skin=None)


# ---------------------------------------------------------------------------
# 7. 导入 / 导出 .zip
# ---------------------------------------------------------------------------
def export_pack(skin_id: str, dest: Path, include_override: bool = True) -> Path:
    """导出材质包为 .zip；可选把当前单包覆盖层一起烘焙进 skin.json。"""
    pack = get_pack(skin_id)
    raw = str(dest)
    dest = Path(dest)
    if dest.is_dir() or raw.endswith(("/", "\\")) or dest.suffix.lower() != ".zip":
        dest.mkdir(parents=True, exist_ok=True)
        dest = dest / f"{pack.id}-{pack.version}.zip"
    manifest = dict(pack.manifest)
    manifest.pop("builtin", None)
    extra_files: dict[str, Path] = {}
    if include_override:
        layer = load_override(pack.id)
        if layer:
            # 覆盖层引用的 assets/ 资源一并打包到 override-assets/
            layer = copy.deepcopy(layer)

            def remap(v):
                if isinstance(v, str) and v.startswith("assets/"):
                    src = overrides_dir() / v
                    if src.is_file():
                        new = "override-assets/" + src.name
                        extra_files[new] = src
                        return new
                return v

            for bg in _normalize_backgrounds(layer.get("background")):
                if isinstance(bg, dict) and bg.get("image"):
                    bg["image"] = remap(bg["image"])
            if isinstance(layer.get("pet"), dict) and layer["pet"].get("sprite"):
                layer["pet"]["sprite"] = remap(layer["pet"]["sprite"])
            if isinstance(layer.get("font"), dict) and layer["font"].get("file"):
                layer["font"]["file"] = remap(layer["font"]["file"])
            if isinstance(layer.get("icons"), dict):
                for key in ("codicons", "selectors"):
                    if isinstance(layer["icons"].get(key), dict):
                        layer["icons"][key] = {k: remap(v) for k, v in layer["icons"][key].items()}
            manifest = deep_merge(manifest, layer)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(pack.path.rglob("*")):
            if f.is_file() and f.name != MANIFEST_NAME:
                zf.write(f, f.relative_to(pack.path).as_posix())
        for arc, src in extra_files.items():
            zf.write(src, arc)
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))
    return dest


class _zip_errors:
    """把 zipfile / zlib 的底层异常（CRC 错误、数据损坏、头部大小被篡改）统一转换为可读的 SkinError。"""

    def __enter__(self):
        return self

    def __exit__(self, et, ev, tb):
        import zlib
        if et is not None and issubclass(et, (zipfile.BadZipFile, zlib.error, EOFError)):
            raise SkinError(f"压缩包已损坏或被篡改: {ev}") from ev
        return False


def import_pack(zip_path: Path, overwrite: bool = False) -> SkinPack:
    """从 .zip 导入材质包（防 zip-slip、限制体积与文件数，校验通过后才落盘）。"""
    zip_path = Path(zip_path)
    if not zipfile.is_zipfile(zip_path):
        raise SkinError(f"不是有效的 zip 文件: {zip_path}")
    with zipfile.ZipFile(zip_path) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        if len(infos) > MAX_ZIP_FILES:
            raise SkinError(f"压缩包文件过多（>{MAX_ZIP_FILES}）")
        if sum(i.file_size for i in infos) > MAX_ZIP_TOTAL_BYTES:
            raise SkinError("压缩包解压后体积过大（上限 64 MB）")
        names = [i.filename.replace("\\", "/") for i in infos]
        # 支持 skin.json 位于根目录或唯一的顶层文件夹内
        manifest_names = [n for n in names if n.split("/")[-1] == MANIFEST_NAME and n.count("/") <= 1]
        if not manifest_names:
            raise SkinError("压缩包中未找到 skin.json")
        prefix = manifest_names[0][: -len(MANIFEST_NAME)]
        for n in names:
            if n.startswith("/") or ".." in n.split("/") or re.match(r"^[A-Za-z]:", n):
                raise SkinError(f"压缩包包含不安全路径: {n}")
        staging = config_dir() / f".import-staging-{os.getpid()}"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        written = 0
        try:
            for info in infos:
                n = info.filename.replace("\\", "/")
                if not n.startswith(prefix):
                    continue
                rel = n[len(prefix):]
                if not rel or rel.startswith("__MACOSX/"):
                    continue
                target = (staging / rel).resolve()
                target.relative_to(staging.resolve())
                target.parent.mkdir(parents=True, exist_ok=True)
                with _zip_errors(), zf.open(info) as src, open(target, "wb") as dst:
                    # zip 头中的 file_size 可被伪造（zip 炸弹），按实际解压字节数限制
                    while True:
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > MAX_ZIP_TOTAL_BYTES:
                            raise SkinError("压缩包解压后体积过大（上限 64 MB）")
                        dst.write(chunk)
            pack = load_pack(staging)
            dst_dir = skins_dir() / pack.id
            if dst_dir.exists():
                if not overwrite:
                    raise SkinError(f"已存在同 id 的材质包: {pack.id}（使用覆盖导入以替换）")
                shutil.rmtree(dst_dir)
            dst_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(staging), str(dst_dir))
            m = json.loads((dst_dir / MANIFEST_NAME).read_text(encoding="utf-8-sig"))
            if m.pop("builtin", None) is not None:
                (dst_dir / MANIFEST_NAME).write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
            return load_pack(dst_dir)
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)


def create_pack_from(skin_id: str, new_id: str, new_name: str) -> SkinPack:
    """以现有材质包为模板复制出一个新包（含当前单包覆盖层），便于用户二次创作。"""
    if not _ID_RE.match(new_id or ""):
        raise SkinError("新材质包 id 不合法")
    if (skins_dir() / new_id).exists():
        raise SkinError(f"已存在: {new_id}")
    tmp_zip = config_dir() / f".tmp-{new_id}.zip"
    try:
        export_pack(skin_id, tmp_zip, include_override=True)
        with zipfile.ZipFile(tmp_zip) as zf:
            m = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
        m.update({"id": new_id, "name": new_name, "version": "1.0.0"})
        m.pop("builtin", None)
        rebuilt = config_dir() / f".tmp-{new_id}-2.zip"
        with zipfile.ZipFile(tmp_zip) as src, zipfile.ZipFile(rebuilt, "w", zipfile.ZIP_DEFLATED) as dst:
            for info in src.infolist():
                if info.filename != MANIFEST_NAME:
                    dst.writestr(info, src.read(info.filename))
            dst.writestr(MANIFEST_NAME, json.dumps(m, ensure_ascii=False, indent=2))
        try:
            return import_pack(rebuilt)
        finally:
            rebuilt.unlink(missing_ok=True)
    finally:
        tmp_zip.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 8. 渲染进程运行时（桌宠外观层）
# ---------------------------------------------------------------------------
def skin_runtime_js() -> str:
    p = resource_root() / "resources" / "skin-runtime.js"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def build_pet_window_snippet(payload: dict | None = None) -> str:
    """供独立桌面桌宠窗口 (pywebview) evaluate_js 使用：注入 CSS + 桌宠外观层。"""
    if payload is None:
        payload = read_compiled()
    rt = skin_runtime_js()
    if not rt:
        return ""
    data = payload if payload and not payload.get("disabled") else None
    slim = None
    if data:
        slim = {"id": data.get("id"), "pet": data.get("pet") or {}, "css": data.get("css", ""), "injectCss": True}
    return f"window.__AGZH_SKIN__ = {json.dumps(slim, ensure_ascii=False)};\n{rt}"
