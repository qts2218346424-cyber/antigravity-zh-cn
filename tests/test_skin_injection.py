# -*- coding: utf-8 -*-
"""
材质包注入幂等性 + 更新后自动重新注入检测 专项测试

覆盖：
1. Agent 桌面端 app.asar：主进程皮肤加载器注入、重复安装不叠加、还原后不被自动打回；
2. IDE 工作台：样式块幂等、切换皮肤替换、product.json 校验和同步、剥离还原字节级一致；
3. 更新检测：模拟官方更新覆盖 → needs_reapply → 自动重打；运行中延后；用户还原后不重打。
"""
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import auto_reapply as ar  # noqa: E402
import patch_antigravity as pa  # noqa: E402
import skin_injector as si  # noqa: E402
import skin_manager as sm  # noqa: E402

UTILS_JS = (
    "devTools: !electron_1.app.isPackaged,\n"
    "function create(win, url) {\n"
    "    const __x = 1;\n"
    "    void win.loadURL(url);\n"
    "}\n"
)


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("AGZH_CONFIG_DIR", str(tmp_path / "cfg"))
    # 避免测试写入真实主目录 / 仓库文件 / 结束真实进程
    monkeypatch.setattr(pa, "ensure_chinese_thinking_protocol", lambda: None)
    monkeypatch.setattr(pa, "stop_antigravity_processes", lambda: None)
    import splash_generator
    monkeypatch.setattr(splash_generator, "CONFIG_FILE", tmp_path / "splash_config.json")
    monkeypatch.setattr(ar, "is_antigravity_running", lambda: False)
    monkeypatch.setattr(ar, "is_updater_running", lambda: False)
    monkeypatch.setattr(ar, "SETTLE_SECONDS", 0)
    monkeypatch.setattr(si, "_ide_candidates", lambda: [])
    sm.sync_builtin_packs()
    return tmp_path


def make_asar(path: Path, version: str = "2.29.1", utils: str = UTILS_JS) -> bytes:
    files = {
        "package.json": json.dumps({"name": "antigravity", "version": version}).encode(),
        "dist/menu.js": b"electron_1.Menu.setApplicationMenu(menu);",
        "dist/tray.js": b"tray = new Tray();",
        "dist/updater.js": b"autoUpdater = {};",
        "dist/preload.js": b"console.log('preload');",
        "dist/utils.js": utils.encode(),
    }
    header: dict = {"files": {}}
    body = b""
    for name, data in files.items():
        node = header
        parts = name.split("/")
        for p in parts[:-1]:
            node = node["files"].setdefault(p, {"files": {}})
        node["files"][parts[-1]] = {"size": len(data), "offset": str(len(body))}
        body += data
    raw = pa.encode_asar_header_dynamic(json.dumps(header, separators=(",", ":"))) + body
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def make_install(root: Path, **kw) -> tuple[Path, Path]:
    install = root / "antigravity"
    asar = install / "resources" / "app.asar"
    make_asar(asar, **kw)
    return install, asar


def utils_of(asar: Path) -> str:
    return pa.read_asar_file_content(bytearray(asar.read_bytes()), "dist/utils.js").decode("utf-8")


def install(install_dir: Path, **kw):
    pa.apply_patch(install_dir, "zh-CN", REPO_ROOT, character="tanjiro", enable_pet=False,
                   stop_processes=False, **kw)


def bump_mtime(p: Path):
    st = p.stat()
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))


# ---------------------------------------------------------------- Agent 桌面端
def test_agent_skin_loader_injected_once_and_idempotent(env):
    install_dir, asar = make_install(env)
    install(install_dir)
    u1 = utils_of(asar)
    assert u1.count(si.SKIN_LOADER_MARKER) == 1
    assert "__agzhSkin.apply(win.webContents)" in u1
    assert "__agzhSkin.apply(webContents)" in u1
    assert json.dumps(str(sm.config_dir())) in u1, "加载器应内嵌当前用户配置目录"
    # 重复安装：始终基于纯净备份，不会叠加第二份
    install(install_dir)
    u2 = utils_of(asar)
    assert u2.count(si.SKIN_LOADER_MARKER) == 1 and u2.count(pa.PATCH_MARKER) == 1
    assert u1 == u2, "相同输入两次安装结果应完全一致（幂等）"


def test_agent_no_skin_flag(env):
    install_dir, asar = make_install(env)
    install(install_dir, enable_skin=False)
    assert si.SKIN_LOADER_MARKER not in utils_of(asar)
    assert "__AGY_ZH_CODE__" in utils_of(asar)


@pytest.mark.skipif(shutil.which("node") is None, reason="未安装 node")
def test_agent_main_hook_is_valid_js(env, tmp_path):
    js = tmp_path / "hook.js"
    js.write_text(si.build_agent_main_hook("C:\\Users\\测试\\AppData\\Roaming\\antigravity-zh-cn"), encoding="utf-8")
    r = subprocess.run(["node", "-c", str(js)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


@pytest.mark.skipif(shutil.which("node") is None, reason="未安装 node")
def test_agent_main_hook_applies_css_with_fake_webcontents(env, tmp_path):
    """用 node 模拟 Electron webContents：验证加载器读取编译载荷并 insertCSS / 切换时移除旧样式。"""
    sm.activate("sakura-light")
    harness = tmp_path / "harness.js"
    harness.write_text(si.build_agent_main_hook() + r"""
const calls = [];
let n = 0;
const wc = {
  isDestroyed: () => false,
  once: () => {},
  insertCSS: async (css) => { calls.push(['insert', css.length]); return 'k' + (++n); },
  removeInsertedCSS: async (k) => { calls.push(['remove', k]); },
  executeJavaScript: async (code) => { calls.push(['exec', code.indexOf('__AGZH_SKIN__') >= 0]); },
};
__agzhSkin.apply(wc);
setTimeout(() => {
  __agzhSkin.apply(wc);
  setTimeout(() => { console.log(JSON.stringify(calls)); process.exit(0); }, 100);
}, 100);
""", encoding="utf-8")
    r = subprocess.run(["node", str(harness)], capture_output=True, text=True, timeout=20,
                       env=dict(os.environ, AGZH_CONFIG_DIR=str(sm.config_dir())))
    assert r.returncode == 0, r.stderr
    calls = json.loads(r.stdout.strip().splitlines()[-1])
    kinds = [c[0] for c in calls]
    assert kinds == ["insert", "exec", "remove", "insert", "exec"], calls
    assert calls[0][1] > 1000 and calls[1][1] is True


# ---------------------------------------------------------------- IDE 工作台
def make_ide(root: Path) -> Path:
    app = root / "Antigravity" / "resources" / "app"
    css = app / si.IDE_CSS_REL
    css.parent.mkdir(parents=True)
    css.write_text(".monaco-workbench{color:red}\n", encoding="utf-8")
    product = {
        "nameShort": "Antigravity",
        "checksums": {
            si.IDE_CSS_CHECKSUM_KEY: si.vscode_checksum(css.read_bytes()),
            "vs/workbench/workbench.desktop.main.js": "unchanged",
        },
    }
    (app / "product.json").write_text(json.dumps(product, indent="\t"), encoding="utf-8")
    return app


def product_sum(app: Path) -> str:
    return json.loads((app / "product.json").read_text(encoding="utf-8"))["checksums"][si.IDE_CSS_CHECKSUM_KEY]


def test_vscode_checksum_algorithm():
    data = b"hello"
    expected = base64.b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
    assert si.vscode_checksum(data) == expected and not expected.endswith("=")


def test_ide_injection_idempotent_and_reversible(env):
    app = make_ide(env)
    css_path = app / si.IDE_CSS_REL
    original = css_path.read_bytes()
    assert si.normalize_ide_root(env / "Antigravity") == app, "应能从安装根目录定位到 resources/app"

    sm.activate("midnight-dark")
    r1 = si.inject_ide(env / "Antigravity")
    text1 = css_path.read_text(encoding="utf-8")
    assert r1["changed"] and text1.count(si.IDE_BLOCK_BEGIN) == 1
    assert product_sum(app) == si.vscode_checksum(css_path.read_bytes()), "校验和必须同步，避免“安装已损坏”提示"
    assert json.loads((app / "product.json").read_text())["checksums"]["vs/workbench/workbench.desktop.main.js"] == "unchanged"
    assert si.ide_status(app) == "applied"

    r2 = si.inject_ide(app)
    assert not r2["changed"] and css_path.read_text(encoding="utf-8") == text1, "重复注入不应改变文件"

    sm.activate("sakura-light")
    assert si.ide_status(app) == "stale"
    si.inject_ide(app)
    text3 = css_path.read_text(encoding="utf-8")
    assert text3.count(si.IDE_BLOCK_BEGIN) == 1 and "skin: sakura-light" in text3 and "midnight-dark" not in text3

    assert si.remove_ide(app)
    assert css_path.read_bytes() == original, "剥离后应与官方原版字节级一致"
    assert product_sum(app) == si.vscode_checksum(original)
    assert si.ide_status(app) == "disabled"


def test_ide_skin_off_clears_block_but_keeps_enabled(env):
    app = make_ide(env)
    sm.activate("midnight-dark")
    si.inject_ide(app)
    sm.deactivate()
    si.inject_ide(app)
    assert si.IDE_BLOCK_BEGIN not in (app / si.IDE_CSS_REL).read_text(encoding="utf-8")
    assert si.ide_status(app) == "not_applied", "关闭皮肤后不应被判定为需要重新注入"


# ---------------------------------------------------------------- 更新后自动重注入
def test_agent_status_lifecycle_and_auto_reapply(env):
    install_dir, asar = make_install(env, version="2.29.1")
    assert ar.agent_status(asar) == "never"
    install(install_dir)
    st = sm.load_state()["agent"]
    assert st["enabled"] and st["version"] == "2.29.1" and st["lang"] == "zh-CN"
    assert len(st["fingerprint"]["sha256"]) == 64
    assert ar.agent_status() == "patched"

    # 模拟官方更新：安装器用新版未打补丁的 app.asar 覆盖
    time.sleep(0.01)
    make_asar(asar, version="2.30.0")
    bump_mtime(asar)
    assert ar.agent_status() == "needs_reapply"

    # 只检测不应用
    assert ar.check(apply=False)["agent"] == "needs_reapply"
    assert pa.PATCH_MARKER.encode() not in asar.read_bytes()

    res = ar.check(apply=True, repo_root=REPO_ROOT)
    assert res["agent"] == "reapplied", res
    assert ar.agent_status() == "patched"
    u = utils_of(asar)
    assert u.count(si.SKIN_LOADER_MARKER) == 1
    assert sm.load_state()["agent"]["version"] == "2.30.0", "重打后应记录新版本"
    # 新版本的原版备份应被刷新为 2.30.0（基于新版重打，而不是回退旧版）
    bak = pa.read_asar_file_content(bytearray((asar.with_suffix(".asar.bak")).read_bytes()), "package.json")
    assert json.loads(bak)["version"] == "2.30.0"


def test_reapply_deferred_while_running(env, monkeypatch):
    install_dir, asar = make_install(env)
    install(install_dir)
    make_asar(asar, version="2.30.0")
    bump_mtime(asar)
    monkeypatch.setattr(ar, "is_antigravity_running", lambda: True)
    res = ar.check(apply=True, repo_root=REPO_ROOT)
    assert res["agent"] == "deferred_running"
    assert pa.PATCH_MARKER.encode() not in asar.read_bytes(), "程序运行中不得写入"
    res = ar.check(apply=True, allow_when_running=True, repo_root=REPO_ROOT)
    assert res["agent"] == "reapplied"


def test_fingerprint_change_without_update_is_not_reapplied(env):
    install_dir, asar = make_install(env)
    install(install_dir)
    bump_mtime(asar)  # 仅 mtime 变化（例如被杀毒软件扫描/复制），标记仍在
    assert ar.agent_status() == "patched"


def test_user_restore_disables_auto_reapply(env):
    install_dir, asar = make_install(env)
    install(install_dir)
    assert pa.restore_backup(install_dir)
    assert ar.agent_status() == "disabled"
    res = ar.check(apply=True, repo_root=REPO_ROOT)
    assert res["agent"] == "disabled"
    assert pa.PATCH_MARKER.encode() not in asar.read_bytes(), "用户主动还原后不能被自动打回"


def test_ide_reapply_after_update(env, monkeypatch):
    app = make_ide(env)
    monkeypatch.setattr(si, "_ide_candidates", lambda: [app])
    sm.activate("nezuko-bamboo")
    si.inject_ide(app)
    # 模拟 IDE 更新：工作台 CSS 与 product.json 被官方新版覆盖
    css = app / si.IDE_CSS_REL
    css.write_text(".monaco-workbench{color:blue}\n", encoding="utf-8")
    prod = json.loads((app / "product.json").read_text())
    prod["checksums"][si.IDE_CSS_CHECKSUM_KEY] = si.vscode_checksum(css.read_bytes())
    (app / "product.json").write_text(json.dumps(prod), encoding="utf-8")
    assert si.ide_status(app) == "needs_reapply"
    res = ar.check(apply=True, repo_root=REPO_ROOT)
    assert res["ide"] == "reapplied", res
    text = css.read_text(encoding="utf-8")
    assert text.startswith(".monaco-workbench{color:blue}") and text.count(si.IDE_BLOCK_BEGIN) == 1
    assert product_sum(app) == si.vscode_checksum(css.read_bytes())
    # 备份应刷新为新版原文件
    assert (css.with_name(css.name + si.BACKUP_SUFFIX)).read_text(encoding="utf-8") == ".monaco-workbench{color:blue}\n"


def test_recompile_when_payload_missing(env):
    sm.activate("midnight-dark")
    sm.compiled_payload_path().unlink()
    res = ar.check(apply=True, repo_root=REPO_ROOT)
    assert "recompiled_skin" in res["actions"]
    assert sm.read_compiled()["id"] == "midnight-dark"


def test_process_detection_uses_exact_names(monkeypatch):
    class R:
        stdout = "/usr/bin/python3\n/home/u/antigravity-zh-cn/app/agzh_app.py\nbash\n"
    monkeypatch.setattr(ar.sys, "platform", "linux")
    monkeypatch.setattr(ar.subprocess, "run", lambda *a, **k: R())
    assert ar.is_antigravity_running() is False, "不能把本工具（路径含 antigravity）误判为 Antigravity"
    R.stdout += "/opt/antigravity/antigravity\n"
    assert ar.is_antigravity_running() is True


def test_linux_autostart_roundtrip(env, monkeypatch, tmp_path):
    monkeypatch.setattr(ar.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    msg = ar.enable_autostart(["/usr/bin/python3", "/opt/my app/agzh_app.py", "--background"])
    assert "autostart" in msg and ar.autostart_enabled()
    desktop = (tmp_path / "xdg" / "autostart" / "antigravity-zh-cn-autoreapply.desktop").read_text(encoding="utf-8")
    assert 'Exec=/usr/bin/python3 "/opt/my app/agzh_app.py" --background' in desktop
    assert sm.load_state()["auto_reapply"] is True
    ar.disable_autostart()
    assert not ar.autostart_enabled() and sm.load_state()["auto_reapply"] is False


@pytest.mark.skipif(shutil.which("node") is None, reason="未安装 node")
def test_agent_main_hook_hot_switch_on_file_change(env, tmp_path):
    """切换材质包 = 改写 compiled/active-skin.json；加载器通过 fs.watchFile 自动对已打开窗口重新注入。"""
    sm.activate("midnight-dark")
    target = sm.compiled_payload_path()
    harness = tmp_path / "hot.js"
    harness.write_text(si.build_agent_main_hook() + r"""
const fs = require('fs');
const calls = [];
let n = 0;
const wc = {
  isDestroyed: () => false, once: () => {},
  insertCSS: async (css) => { calls.push(['insert', css.slice(0, 60)]); return 'k' + (++n); },
  removeInsertedCSS: async (k) => { calls.push(['remove', k]); },
  executeJavaScript: async () => {},
};
__agzhSkin.apply(wc);
setTimeout(() => {
  const p = JSON.parse(fs.readFileSync(process.env.TARGET, 'utf8'));
  p.css = '/* switched */ body{}'; p.id = 'switched';
  fs.writeFileSync(process.env.TARGET, JSON.stringify(p));
}, 300);
setTimeout(() => { console.log(JSON.stringify(calls)); process.exit(0); }, 4000);
""", encoding="utf-8")
    r = subprocess.run(["node", str(harness)], capture_output=True, text=True, timeout=30,
                       env=dict(os.environ, AGZH_CONFIG_DIR=str(sm.config_dir()), TARGET=str(target)))
    assert r.returncode == 0, r.stderr
    calls = json.loads(r.stdout.strip().splitlines()[-1])
    assert calls[0][0] == "insert" and "midnight-dark" in calls[0][1]
    assert ["remove", "k1"] in calls and any(c[0] == "insert" and "switched" in c[1] for c in calls), calls
