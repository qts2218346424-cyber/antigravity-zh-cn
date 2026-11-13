# -*- coding: utf-8 -*-
"""
启动遮罩「鎹鸦巡检」版本号回归测试：
1. 面向用户的文件中不得再残留写死的 v2.xx.x 版本号；
2. 生成器必须从 resources/version.json 注入汉化包版本作为回退；
3. 生成的遮罩 JS 在运行时优先显示实际安装的 Antigravity 版本（app.getVersion()）。
"""
import json
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

import splash_generator as sg

REPO_ROOT = Path(__file__).resolve().parent.parent
HARDCODED_VER_RE = re.compile(r"v2\.\d+\.\d+")

USER_FACING_FILES = [
    "resources/loadingOverlay-zh.js",
    "resources/splash/index.html",
    "scripts/splash_generator.py",
    "scripts/build_kimetsu_characters_splash.py",
]

PACK_VERSION = json.loads((REPO_ROOT / "resources" / "version.json").read_text(encoding="utf-8"))["version"]


@pytest.mark.parametrize("rel", USER_FACING_FILES)
def test_no_hardcoded_version_in_user_facing_files(rel):
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    # 静态预览 index.html 中允许出现的唯一版本号，是生成器从 version.json 注入的那一处
    injected = f'const crowVersion = "汉化包 v{PACK_VERSION}";'
    hits = [line.strip() for line in text.splitlines()
            if HARDCODED_VER_RE.search(line.replace(injected, ""))]
    assert not hits, f"{rel} 仍包含写死的版本号: {hits}"


def test_sanitize_version():
    assert sg.sanitize_version("v2.31.2") == "2.31.2"
    assert sg.sanitize_version(" 2.31.2-beta+1 ") == "2.31.2-beta+1"
    assert sg.sanitize_version('2.31.2"</script><x>') == "2.31.2scriptx"
    assert sg.sanitize_version(None) == ""


def test_read_pack_version_from_version_json(tmp_path):
    assert sg.read_pack_version() == PACK_VERSION
    vf = tmp_path / "version.json"
    vf.write_text(json.dumps({"version": "9.8.7"}), encoding="utf-8")
    assert sg.read_pack_version(vf) == "9.8.7"
    assert sg.read_pack_version(tmp_path / "missing.json") == ""


def test_static_html_injects_pack_version():
    html = sg.build_splash_html_template("zenitsu", "")
    assert f'const crowVersion = "汉化包 v{PACK_VERSION}";' in html
    html = sg.build_splash_html_template("zenitsu", "", pack_version="9.8.7")
    assert 'const crowVersion = "汉化包 v9.8.7";' in html
    assert not HARDCODED_VER_RE.search(html.replace("v9.8.7", "").replace(f"v{PACK_VERSION}", ""))


@pytest.mark.parametrize("theme", ["zenitsu", "tanjiro", "all"])
def test_overlay_js_injects_fallback_and_runtime_placeholder(theme):
    js = sg.build_overlay_js(theme, pack_version="9.8.7")
    assert 'const AGZH_PACK_VERSION = "9.8.7";' in js
    assert "electron_1.app.getVersion()" in js
    assert "const crowVersion = ${crowVersion};" in js
    assert "getLoadingHtml(videoUrl, crowVersion)" in js
    assert "v2.26.1" not in js


def test_committed_overlay_matches_generator():
    """resources/ 下的产物必须由生成器产生（禁止只手改产物）。"""
    js = sg.build_overlay_js("zenitsu")
    html = sg.build_splash_html_template("zenitsu", "")
    assert (REPO_ROOT / "resources" / "loadingOverlay-zh.js").read_text(encoding="utf-8") == js
    assert (REPO_ROOT / "resources" / "splash" / "index.html").read_text(encoding="utf-8") == html


_NODE_HARNESS = textwrap.dedent(r"""
    const Module = require("module");
    const fs = require("fs");
    const appVersion = process.argv[3];
    let captured = null;
    const fakeView = { webContents: {
        loadFile: () => Promise.resolve(), loadURL: (u) => { captured = decodeURIComponent(u.split(",").slice(1).join(",")); return Promise.resolve(); },
        executeJavaScript: () => Promise.resolve(true) }, setBounds: () => {} };
    const electron = {
      app: { getAppPath: () => "/nonexistent/app.asar", getVersion: () => appVersion },
      WebContentsView: function () { return fakeView; },
    };
    const origLoad = Module._load;
    Module._load = function (req, ...rest) { return req === "electron" ? electron : origLoad.call(this, req, ...rest); };
    const origWrite = fs.writeFileSync;
    fs.writeFileSync = (p, data, ...rest) => { if (String(p).endsWith("antigravity_splash.html")) { captured = data; return; } return origWrite(p, data, ...rest); };
    const mod = require(process.argv[2]);
    const win = { isDestroyed: () => true, getContentSize: () => [800, 600], on() {}, off() {},
      contentView: { addChildView() {}, removeChildView() {} }, webContents: { once() {} } };
    mod.attachLoadingOverlay(win, "#fff", "#000");
    const m = captured.match(/const crowVersion = (.*);/);
    process.stdout.write(JSON.stringify({ crowVersion: m ? JSON.parse(m[1]) : null }));
    process.exit(0);
""")


def _run_overlay(js_path: Path, app_version: str, tmp_path: Path) -> str:
    harness = tmp_path / "harness.js"
    harness.write_text(_NODE_HARNESS, encoding="utf-8")
    out = subprocess.run(["node", str(harness), str(js_path), app_version],
                         capture_output=True, text=True, timeout=30, check=True)
    return json.loads(out.stdout)["crowVersion"]


@pytest.mark.skipif(shutil.which("node") is None, reason="需要 node")
def test_overlay_runtime_prefers_installed_version(tmp_path):
    js_path = tmp_path / "overlay.js"
    js_path.write_text(sg.build_overlay_js("zenitsu", pack_version="9.8.7"), encoding="utf-8")
    assert _run_overlay(js_path, "2.40.0", tmp_path) == "Antigravity v2.40.0"
    # 取不到安装版本时回退到注入的汉化包版本
    assert _run_overlay(js_path, "", tmp_path) == "汉化包 v9.8.7"
    # 运行时版本中的危险字符会被清洗
    assert _run_overlay(js_path, '2.40.0"</script>', tmp_path) == "Antigravity v2.40.0script"
