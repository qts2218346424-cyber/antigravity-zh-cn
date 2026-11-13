#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
材质包注入器 (skin_injector.py)

两个注入目标：
1. Agent 桌面端 (app.asar)：由 patch_antigravity.py 在 dist/utils.js 主进程钩子中
   嵌入一段“皮肤加载器”。加载器在每次 dom-ready 时读取用户配置目录下的
   compiled/active-skin.json，通过 webContents.insertCSS 注入样式，并用
   fs.watchFile 监听文件变化实时热切换 —— 切换材质包不需要重新打补丁。
2. 基于 VS Code 的 Antigravity IDE 工作台：在 workbench.desktop.main.css 末尾追加
   带标记的样式块（幂等：先剥离旧块再追加），同时更新 product.json 中对应文件的
   checksums，避免出现“安装似乎已损坏 (installation appears to be corrupt)”提示。
   支持一键剥离还原。
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skin_manager as sm  # noqa: E402

SKIN_LOADER_MARKER = "/* __AGZH_SKIN_LOADER__ */"
IDE_BLOCK_BEGIN = "/* __AGZH_SKIN_BEGIN__"
IDE_BLOCK_END = "/* __AGZH_SKIN_END__ */"
IDE_CSS_REL = "out/vs/workbench/workbench.desktop.main.css"
IDE_CSS_CHECKSUM_KEY = "vs/workbench/workbench.desktop.main.css"
BACKUP_SUFFIX = ".agzh.bak"


# ---------------------------------------------------------------------------
# 1. Agent 桌面端主进程皮肤加载器
# ---------------------------------------------------------------------------
def build_agent_main_hook(embedded_config_dir: str | None = None) -> str:
    """返回注入 dist/utils.js 顶部的主进程 JS（定义 __agzhSkin.apply(webContents)）。"""
    runtime = sm.skin_runtime_js()
    embedded = embedded_config_dir if embedded_config_dir is not None else str(sm.config_dir())
    return f"""
{SKIN_LOADER_MARKER}
const __agzhSkin = (() => {{
  const noop = {{ apply: () => {{}} }};
  try {{
    const fs = require('fs');
    const path = require('path');
    const os = require('os');
    const RUNTIME = {json.dumps(runtime)};
    const APP = {json.dumps(sm.APP_DIR_NAME)};
    const dirs = [];
    if (process.env.AGZH_CONFIG_DIR) dirs.push(process.env.AGZH_CONFIG_DIR);
    dirs.push({json.dumps(embedded)});
    if (process.platform === 'win32') dirs.push(path.join(process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming'), APP));
    else if (process.platform === 'darwin') dirs.push(path.join(os.homedir(), 'Library', 'Application Support', APP));
    else dirs.push(path.join(process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'), APP));
    const files = [...new Set(dirs.filter(Boolean).map(d => path.join(d, 'compiled', 'active-skin.json')))];
    const pick = () => files.find(f => {{ try {{ return fs.existsSync(f); }} catch (_) {{ return false; }} }}) || files[0];
    let cache = null, cacheKey = '';
    const load = () => {{
      const f = pick();
      try {{
        const st = fs.statSync(f);
        const key = f + ':' + st.mtimeMs + ':' + st.size;
        if (key !== cacheKey) {{ cache = JSON.parse(fs.readFileSync(f, 'utf8')); cacheKey = key; }}
      }} catch (_) {{ cache = null; cacheKey = ''; }}
      return cache;
    }};
    const keys = new WeakMap();
    const chains = new WeakMap();
    const tracked = new Set();
    const applyNow = async (wc) => {{
      try {{
        if (!wc || wc.isDestroyed()) return;
        const p = load();
        const prev = keys.get(wc);
        if (prev) {{ keys.delete(wc); try {{ await wc.removeInsertedCSS(prev); }} catch (_) {{}} }}
        const active = p && !p.disabled ? p : null;
        if (active && active.css && !wc.isDestroyed()) keys.set(wc, await wc.insertCSS(active.css));
        const slim = active ? {{ id: active.id, pet: active.pet || {{}} }} : null;
        if (!wc.isDestroyed()) await wc.executeJavaScript('window.__AGZH_SKIN__ = ' + JSON.stringify(slim) + ';\\n' + RUNTIME);
      }} catch (e) {{ try {{ console.log('[AGZH-SKIN] apply failed:', e && e.message); }} catch (_) {{}} }}
    }};
    // dom-ready 与 did-finish-load 几乎同时触发：两次 apply 并发时都会 insertCSS，
    // 其中一份样式的 key 被覆盖丢失，之后切换皮肤再也移除不掉（旧皮肤残留）。
    // 这里按 webContents 串行化，并合并排队中的重复请求。
    const applyTo = (wc) => {{
      if (!wc) return Promise.resolve();
      const st = chains.get(wc) || {{ tail: Promise.resolve(), queued: false }};
      chains.set(wc, st);
      if (st.queued) return st.tail;
      st.queued = true;
      st.tail = st.tail.then(() => {{ st.queued = false; return applyNow(wc); }});
      return st.tail;
    }};
    let watching = false;
    const watch = () => {{
      if (watching) return;
      watching = true;
      files.forEach(f => {{
        try {{
          fs.watchFile(f, {{ interval: 1500 }}, (cur, prev) => {{
            // 文件不存在时 node 会以全零 stat 回调一次，忽略这种“伪变化”
            if (cur.mtimeMs === prev.mtimeMs && cur.size === prev.size) return;
            cacheKey = '';
            tracked.forEach(wc => applyTo(wc));
          }});
        }} catch (_) {{}}
      }});
    }};
    return {{
      apply: (wc) => {{
        try {{
          if (!wc) return;
          if (!tracked.has(wc)) {{ tracked.add(wc); wc.once('destroyed', () => tracked.delete(wc)); }}
          watch();
          applyTo(wc);
        }} catch (_) {{}}
      }}
    }};
  }} catch (_) {{ return noop; }}
}})();
"""


# ---------------------------------------------------------------------------
# 2. IDE 工作台 (VS Code 架构) 注入
# ---------------------------------------------------------------------------
def _ide_candidates() -> list[Path]:
    """候选的 IDE 应用根目录（含 out/ 与 product.json 的 resources/app 目录）。"""
    roots: list[Path] = []
    if sys.platform == "win32":
        for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            if not base:
                continue
            for sub in ("Programs/Antigravity", "Programs/antigravity", "Programs/Antigravity IDE", "Antigravity", "Antigravity IDE"):
                roots.append(Path(base) / sub / "resources" / "app")
    elif sys.platform == "darwin":
        for app in (Path("/Applications/Antigravity.app"), Path.home() / "Applications" / "Antigravity.app",
                    Path("/Applications/Antigravity IDE.app")):
            roots.append(app / "Contents" / "Resources" / "app")
    else:
        for base in (Path("/usr/share/antigravity"), Path("/opt/Antigravity"), Path("/opt/antigravity"),
                     Path.home() / ".local" / "share" / "antigravity", Path("/usr/lib/antigravity")):
            roots.append(base / "resources" / "app")
    return roots


def normalize_ide_root(path: Path) -> Path | None:
    """接受安装目录 / .app / resources/app 任一层级，返回含 product.json 与工作台 CSS 的应用根。"""
    path = Path(path)
    for cand in (path, path / "resources" / "app", path / "Contents" / "Resources" / "app", path / "app"):
        if (cand / IDE_CSS_REL).is_file() and (cand / "product.json").is_file():
            return cand
    return None


def find_ide_app_root(explicit: Path | str | None = None) -> Path | None:
    if explicit:
        return normalize_ide_root(Path(explicit))
    st = sm.load_state()
    saved = (st.get("ide") or {}).get("app_root")
    if saved:
        r = normalize_ide_root(Path(saved))
        if r:
            return r
    for c in _ide_candidates():
        r = normalize_ide_root(c)
        if r:
            return r
    return None


def vscode_checksum(data: bytes) -> str:
    """VS Code product.json checksums 的算法：sha256 → base64 → 去掉尾部 '='。"""
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii").rstrip("=")


def strip_ide_block(css_text: str) -> str:
    pattern = re.compile(re.escape(IDE_BLOCK_BEGIN) + r".*?" + re.escape(IDE_BLOCK_END) + r"\n?", re.S)
    return pattern.sub("", css_text).rstrip("\n") + "\n" if IDE_BLOCK_BEGIN in css_text else css_text


def ide_block_hash(css_text: str) -> str | None:
    m = re.search(re.escape(IDE_BLOCK_BEGIN) + r" hash=([0-9a-f]*) ", css_text)
    return m.group(1) if m else None


def _update_product_checksum(app_root: Path, css_bytes: bytes) -> bool:
    product = app_root / "product.json"
    try:
        raw = product.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return False
    checksums = data.get("checksums")
    if not isinstance(checksums, dict) or IDE_CSS_CHECKSUM_KEY not in checksums:
        return False
    new_sum = vscode_checksum(css_bytes)
    if checksums[IDE_CSS_CHECKSUM_KEY] == new_sum:
        return True
    backup = product.with_name(product.name + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(product, backup)
    # 只替换该键的值，尽量保持原文件格式不变
    old_sum = checksums[IDE_CSS_CHECKSUM_KEY]
    needle = json.dumps(IDE_CSS_CHECKSUM_KEY) + ": " + json.dumps(old_sum)
    alt = json.dumps(IDE_CSS_CHECKSUM_KEY) + ":" + json.dumps(old_sum)
    if needle in raw:
        raw = raw.replace(needle, json.dumps(IDE_CSS_CHECKSUM_KEY) + ": " + json.dumps(new_sum), 1)
    elif alt in raw:
        raw = raw.replace(alt, json.dumps(IDE_CSS_CHECKSUM_KEY) + ":" + json.dumps(new_sum), 1)
    else:
        checksums[IDE_CSS_CHECKSUM_KEY] = new_sum
        raw = json.dumps(data, indent="\t", ensure_ascii=False)
    product.write_text(raw, encoding="utf-8")
    return True


def _resign_macos_app(app_root: Path) -> None:
    """macOS：修改 .app 内文件后执行本机 ad-hoc 重签名，避免“已损坏/无法打开”。"""
    if sys.platform != "darwin":
        return
    for parent in [app_root, *app_root.parents]:
        if parent.suffix == ".app":
            try:
                import subprocess
                subprocess.run(["codesign", "--force", "--deep", "-s", "-", str(parent)], capture_output=True, timeout=120)
            except Exception:
                pass
            return


def inject_ide(app_root: Path, payload: dict | None = None) -> dict:
    """把当前编译好的皮肤 CSS 写入 IDE 工作台（幂等）。返回 {'changed': bool, 'hash': str}。"""
    app_root = normalize_ide_root(app_root) or Path(app_root)
    css_path = app_root / IDE_CSS_REL
    if not css_path.is_file():
        raise FileNotFoundError(f"未找到 IDE 工作台样式文件: {css_path}")
    if payload is None:
        payload = sm.read_compiled()
    original = css_path.read_text(encoding="utf-8")
    base_css = strip_ide_block(original)
    backup = css_path.with_name(css_path.name + BACKUP_SUFFIX)
    if IDE_BLOCK_BEGIN not in original:
        # 当前文件是官方原版（首次安装或官方更新后），刷新备份
        shutil.copy2(css_path, backup)
    if not payload or payload.get("disabled") or not payload.get("css"):
        new_text = base_css
        digest = ""
    else:
        digest = payload.get("hash", "")
        block = (f"{IDE_BLOCK_BEGIN} hash={digest} id={payload.get('id')} */\n"
                 f"{payload['css']}\n{IDE_BLOCK_END}\n")
        new_text = base_css.rstrip("\n") + "\n" + block
    changed = new_text != original
    if changed:
        tmp = css_path.with_name(css_path.name + ".agzh.tmp")
        tmp.write_text(new_text, encoding="utf-8")
        os.replace(tmp, css_path)
    _update_product_checksum(app_root, new_text.encode("utf-8"))
    if changed:
        _resign_macos_app(app_root)
    sm.update_state(ide={"app_root": str(app_root), "enabled": True, "hash": digest})
    return {"changed": changed, "hash": digest, "css_path": str(css_path)}


def remove_ide(app_root: Path, *, forget: bool = True) -> bool:
    """剥离 IDE 中的皮肤样式块并恢复校验和。"""
    app_root = normalize_ide_root(app_root) or Path(app_root)
    css_path = app_root / IDE_CSS_REL
    if not css_path.is_file():
        return False
    text = css_path.read_text(encoding="utf-8")
    changed = False
    if IDE_BLOCK_BEGIN in text:
        backup = css_path.with_name(css_path.name + BACKUP_SUFFIX)
        stripped = strip_ide_block(text)
        if backup.is_file() and IDE_BLOCK_BEGIN not in backup.read_text(encoding="utf-8"):
            stripped = backup.read_text(encoding="utf-8")
        css_path.write_text(stripped, encoding="utf-8")
        changed = True
    _update_product_checksum(app_root, css_path.read_bytes())
    if changed:
        _resign_macos_app(app_root)
    if forget:
        sm.update_state(ide={"app_root": str(app_root), "enabled": False, "hash": ""})
    return changed


def ide_status(app_root: Path | None) -> str:
    """IDE 皮肤状态：missing / disabled / applied / stale / needs_reapply / not_applied"""
    if app_root is None:
        return "missing"
    css_path = Path(app_root) / IDE_CSS_REL
    if not css_path.is_file():
        return "missing"
    st = sm.load_state()
    enabled = (st.get("ide") or {}).get("enabled")
    text = css_path.read_text(encoding="utf-8", errors="replace")
    payload = sm.read_compiled()
    want = payload.get("hash") if payload and not payload.get("disabled") else ""
    if enabled is False:
        return "disabled"
    have = ide_block_hash(text)
    if have is None:
        # 曾经注入过但标记消失 = 被官方更新覆盖
        return "needs_reapply" if (enabled and want) else "not_applied"
    if have != want:
        return "stale"
    return "applied"
