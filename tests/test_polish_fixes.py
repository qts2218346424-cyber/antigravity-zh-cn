# -*- coding: utf-8 -*-
"""
fix/polish-perf-ui 回归测试：每个用例对应 PR 中修复的一个具体缺陷。
"""
import json
import multiprocessing
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "resources"))
sys.path.insert(0, str(REPO_ROOT / "app"))

import auto_reapply as ar  # noqa: E402
import patch_antigravity as pa  # noqa: E402
import skin_injector as si  # noqa: E402
import skin_manager as sm  # noqa: E402

HAS_NODE = shutil.which("node") is not None
NOTIF_ANCHOR = """        const notification = new electron_1.Notification({
            title: options.title,
            body: options.body,
            silent: options.silent ?? false,
        });"""


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("AGZH_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setattr(pa, "ensure_chinese_thinking_protocol", lambda: None)
    monkeypatch.setattr(pa, "stop_antigravity_processes", lambda: None)
    import splash_generator
    monkeypatch.setattr(splash_generator, "CONFIG_FILE", tmp_path / "splash_config.json")
    monkeypatch.setattr(ar, "is_antigravity_running", lambda: False)
    monkeypatch.setattr(ar, "is_updater_running", lambda: False)
    monkeypatch.setattr(si, "_ide_candidates", lambda: [])
    return tmp_path


def make_asar(path: Path) -> None:
    files = {
        "package.json": json.dumps({"name": "antigravity", "version": "2.31.2"}).encode(),
        "dist/menu.js": b"electron_1.Menu.setApplicationMenu(menu);",
        "dist/tray.js": b"tray = new Tray();",
        "dist/updater.js": b"autoUpdater = {};",
        "dist/preload.js": b"console.log('preload');",
        "dist/utils.js": b"devTools: !electron_1.app.isPackaged,\nfunction c(win, url) {\n    void win.loadURL(url);\n}\n",
        "dist/ipcHandlers.js": ("function h(options) {\n" + NOTIF_ANCHOR + "\n}\n").encode(),
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pa.encode_asar_header_dynamic(json.dumps(header, separators=(",", ":"))) + body)


def patched_file(asar: Path, name: str) -> str:
    return pa.read_asar_file_content(bytearray(asar.read_bytes()), name).decode("utf-8")


# ---------------------------------------------------------------- 1. 写死的盘符 / 用户路径
HARDCODED = re.compile(r"(?i)(?<![A-Za-z])[a-z]:\\{1,2}(antigravity-cn|users\\{1,2}|浏览器)|C:/Users/|/home/(?!runner|sandbox)[a-z]+/")


def test_no_hardcoded_personal_paths_in_repo():
    out = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        pytest.skip("不在 git 仓库中")
    bad = []
    for rel in out.stdout.splitlines():
        p = REPO_ROOT / rel
        if p.suffix not in (".py", ".js", ".html", ".ps1", ".bat", ".sh", ".command", ".yml", ".spec") or not p.is_file():
            continue
        if rel.startswith("tests/"):
            continue  # 测试用例里的示例路径是刻意构造的
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if HARDCODED.search(line):
                bad.append(f"{rel}:{i}: {line.strip()[:120]}")
    assert not bad, "发现写死的个人路径：\n" + "\n".join(bad)


def test_pet_js_has_no_drive_path_and_html_in_sync():
    js = (REPO_ROOT / "resources" / "nezuko-pet.js").read_text(encoding="utf-8")
    html = (REPO_ROOT / "resources" / "desktop_pet_window.html").read_text(encoding="utf-8")
    assert "media_helper.py\" status" not in js and "e:\\" not in js.lower()
    assert "__AGY_MEDIA_HELPER_CMD__" in js and "execFile" in js
    assert js.strip() in html, "desktop_pet_window.html 需用 scripts/build_desktop_pet_html.py 重新生成"


# ---------------------------------------------------------------- 2. 多媒体助手路径在打补丁时解析
def test_media_helper_command_source_mode(env):
    cmd = pa.resolve_media_helper_command(REPO_ROOT / "resources")
    assert Path(cmd[0]).is_absolute() and cmd[1:3] == ["-X", "utf8"]
    assert Path(cmd[3]) == (REPO_ROOT / "resources" / "media_helper.py").resolve()


def test_media_helper_command_frozen_mode(env, monkeypatch):
    fake_exe = env / "dist" / "AntigravityZhCN.exe"
    fake_exe.parent.mkdir(parents=True)
    fake_exe.write_bytes(b"")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    cmd = pa.resolve_media_helper_command(REPO_ROOT / "resources")
    assert cmd == [str(fake_exe.resolve()), "--media"]
    assert (sm.config_dir() / "media_helper.py").is_file(), "打包版应把助手复制到持久的配置目录"


def test_patch_ipc_and_preload_use_resolved_helper(env):
    install = env / "antigravity"
    asar = install / "resources" / "app.asar"
    make_asar(asar)
    pa.apply_patch(install, "zh-CN", REPO_ROOT, character="tanjiro", stop_processes=False)
    ipc = patched_file(asar, "dist/ipcHandlers.js")
    assert pa.PATCH_MARKER in ipc
    helper = json.dumps(str((REPO_ROOT / "resources" / "media_helper.py").resolve()))
    assert helper in ipc
    sanitized_ipc = ipc.replace(helper, '""')
    assert "电脑管家" not in ipc and not re.search(r"[A-Za-z]:\\\\+(浏览器|antigravity-cn)", sanitized_ipc)
    assert 'python -X utf8 "${' not in ipc, "不应再用 shell 拼接命令"
    assert "__agyExecFile(" in ipc and "__agyMediaActions.has(action)" in ipc
    assert "windowsHide: true" in ipc
    preload = patched_file(asar, "dist/preload.js")
    assert "window.__AGY_MEDIA_HELPER_CMD__ = [" in preload
    if HAS_NODE:
        for name, code in (("ipc", ipc), ("preload", preload)):
            f = env / f"{name}.js"
            f.write_text(code, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True, encoding="utf-8")
            assert r.returncode == 0, r.stderr


def test_patch_without_pet_injects_null_helper(env):
    install = env / "antigravity"
    asar = install / "resources" / "app.asar"
    make_asar(asar)
    pa.apply_patch(install, "zh-CN", REPO_ROOT, character="tanjiro", enable_pet=False, stop_processes=False)
    assert "window.__AGY_MEDIA_HELPER_CMD__ = null;" in patched_file(asar, "dist/preload.js")


@pytest.mark.skipif(not HAS_NODE, reason="需要 node")
def test_ipc_media_whitelist_runtime(env):
    """在 node 中执行补丁后的 ipcHandlers 片段：白名单外的动作不会触发任何子进程。"""
    install = env / "antigravity"
    asar = install / "resources" / "app.asar"
    make_asar(asar)
    pa.apply_patch(install, "zh-CN", REPO_ROOT, character="tanjiro", stop_processes=False)
    ipc = patched_file(asar, "dist/ipcHandlers.js")
    harness = env / "h.js"
    harness.write_text("""
const Module = require('module');
const calls = [];
let handler = null;
const origLoad = Module._load;
Module._load = function (req, parent, isMain) {
  if (req === 'electron') return { ipcMain: { on: (ch, fn) => { handler = fn; } }, BrowserWindow: { getAllWindows: () => [] }, Notification: function () {} };
  if (req === 'child_process') return { exec: (...a) => calls.push(['exec', a[0]]), execFile: (...a) => calls.push(['execFile', a[0], a[1]]) };
  return origLoad.apply(this, arguments);
};
""" + ipc + """
handler({ sender: { send() {} } }, 'status');
handler({ sender: { send() {} } }, 'status & calc.exe');
handler({ sender: { send() {} } }, '$(rm -rf ~)');
console.log(JSON.stringify(calls));
""", encoding="utf-8")
    r = subprocess.run(["node", str(harness)], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, r.stderr
    calls = json.loads(r.stdout.strip().splitlines()[-1])
    assert len(calls) == 1 and calls[0][0] == "execFile" and calls[0][2][-1] == "status"


def test_validate_js_syntax_decodes_utf8(monkeypatch):
    seen = {}
    real = subprocess.run

    def spy(*a, **kw):
        seen.update(kw)
        return real(*a, **kw)

    monkeypatch.setattr(subprocess, "run", spy)
    pa.validate_js_syntax("const 你好 = 1;", "t")
    if HAS_NODE:
        assert seen.get("encoding") == "utf-8" and seen.get("errors") == "replace"
        with pytest.raises(SyntaxError):
            pa.validate_js_syntax("const 你好 = ;", "t")


def test_reinstall_respects_user_disabled_updates(env):
    install = env / "antigravity"
    asar = install / "resources" / "app.asar"
    make_asar(asar)
    yml = install / "resources" / "app-update.yml"
    yml.write_text("provider: generic\n", encoding="utf-8")
    import agzh_core
    agzh_core.toggle_updates(install, True)
    assert not yml.exists()
    pa.apply_patch(install, "zh-CN", REPO_ROOT, character="tanjiro", stop_processes=False)
    assert not yml.exists() and (install / "resources" / "app-update.yml.disabled").exists(), \
        "用户禁止了自动更新，重新打补丁不应悄悄恢复"
    agzh_core.toggle_updates(install, False)
    assert yml.exists()


# ---------------------------------------------------------------- 3. media_helper / quota_helper / 桌宠宿主
def test_media_helper_cross_platform_and_lrc_cache(tmp_path, monkeypatch):
    import io
    import media_helper as mh
    monkeypatch.setattr(mh, "_LRC_CACHE_FILE", str(tmp_path / "lrc.json"))
    calls = []
    monkeypatch.setattr(mh, "fetch_lrc_online", lambda kw: calls.append(kw) or None)
    assert mh.fetch_lrc_cached("Song", "Artist") is None
    assert mh.fetch_lrc_cached("Song", "Artist") is None
    assert len(calls) == 2, "第二次应命中缓存（包括“未找到”的结果），不再联网"
    buf = io.StringIO()
    assert mh.main(["status"], out=buf) == 0
    assert "isPlaying" in json.loads(buf.getvalue())
    assert mh.main(["bogus"], out=io.StringIO()) == 2


def test_desktop_pet_bridge_calls_existing_helpers(monkeypatch):
    import desktop_pet_app as dp
    import media_helper
    import quota_helper
    monkeypatch.setattr(media_helper, "get_current_music_status", lambda: {"title": "x"})
    monkeypatch.setattr(quota_helper, "get_cockpit_quota_data", lambda: {"email": "a@b.c", "geminiWeeklyPct": 42})
    assert dp.DesktopPetBridge().get_media_status() == {"title": "x"}
    q = dp.get_local_quota_data()
    assert q["username"] == "a@b.c" and q["weeklyQuota"] == 42


def test_quota_helper_has_no_hardcoded_account(monkeypatch, tmp_path):
    import quota_helper
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert quota_helper.detect_current_active_email() == ""


# ---------------------------------------------------------------- 4. 材质包管理
def test_deleted_builtin_pack_is_not_resurrected(env):
    sm.sync_builtin_packs()
    assert (sm.skins_dir() / "sakura-light").is_dir()
    sm.remove_pack("sakura-light")
    sm.sync_builtin_packs()
    assert not (sm.skins_dir() / "sakura-light").exists(), "用户删除的内置包不应在下次启动时复活"
    sm.sync_builtin_packs(force=True)
    assert (sm.skins_dir() / "sakura-light").is_dir()
    assert sm.load_state().get("removed_builtin") == []


def test_zip_bomb_with_forged_size_is_rejected(env, monkeypatch):
    src = REPO_ROOT / "resources" / "skins" / "midnight-dark"
    z = env / "bomb.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in src.iterdir():
            zf.write(f, f.name)
        zf.writestr("big.bin", b"\0" * (3 * 1024 * 1024))
    monkeypatch.setattr(sm, "MAX_ZIP_TOTAL_BYTES", 2 * 1024 * 1024)
    # 伪造 file_size：让头部声称很小
    real_infolist = zipfile.ZipFile.infolist

    def lying(self):
        infos = real_infolist(self)
        for i in infos:
            if i.filename == "big.bin":
                i.file_size = 10
        return infos

    monkeypatch.setattr(zipfile.ZipFile, "infolist", lying)
    with pytest.raises(sm.SkinError, match="体积过大|损坏"):
        sm.import_pack(z)
    assert not list(sm.config_dir().glob(".import-staging*")), "失败后应清理临时目录"


def test_file_lock_excludes_and_recovers_stale(env):
    p = sm.config_dir() / "x.lock"
    a = sm.FileLock(p, timeout=0)
    assert a.acquire()
    b = sm.FileLock(p, timeout=0.2)
    assert not b.acquire()
    a.release()
    assert b.acquire()
    b.release()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("999999\n", encoding="utf-8")  # 已退出进程留下的锁
    c = sm.FileLock(p, timeout=0.5)
    assert c.acquire(), "持锁进程已不存在时应视为失效锁"
    c.release()


def _bump_state(cfg: str, key: str, n: int) -> None:
    os.environ["AGZH_CONFIG_DIR"] = cfg
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import skin_manager as m
    for i in range(n):
        m.update_state(**{f"{key}{i}": i})


def test_update_state_is_process_safe(env):
    ctx = multiprocessing.get_context("spawn")
    cfg = str(sm.config_dir())
    procs = [ctx.Process(target=_bump_state, args=(cfg, k, 25)) for k in ("a", "b", "c")]
    for p in procs:
        p.start()
    for p in procs:
        p.join(60)
    st = sm.load_state()
    missing = [f"{k}{i}" for k in "abc" for i in range(25) if f"{k}{i}" not in st]
    assert not missing, f"并发写 state.json 丢失了 {len(missing)} 个字段"


# ---------------------------------------------------------------- 5. 自动重注入
def _install_and_overwrite(env):
    install = env / "antigravity"
    asar = install / "resources" / "app.asar"
    make_asar(asar)
    pa.apply_patch(install, "zh-CN", REPO_ROOT, character="tanjiro", stop_processes=False)
    make_asar(asar)  # 模拟官方更新覆盖
    st = asar.stat()
    os.utime(asar, ns=(st.st_atime_ns, st.st_mtime_ns + 3_000_000_000))
    return asar


def test_reapply_waits_until_update_settles(env, monkeypatch):
    asar = _install_and_overwrite(env)
    monkeypatch.setattr(ar, "SETTLE_SECONDS", 3600)
    os.utime(asar, None)  # 刚刚被写入
    res = ar.check(apply=True, repo_root=REPO_ROOT)
    assert res["agent"] == "deferred_settling"
    assert pa.PATCH_MARKER.encode() not in asar.read_bytes(), "更新器可能仍在写入，不应立即打补丁"
    old = time.time() - 7200
    os.utime(asar, (old, old))
    assert ar.check(apply=True, repo_root=REPO_ROOT)["agent"] == "reapplied"


def test_reapply_defers_while_updater_running(env, monkeypatch):
    _install_and_overwrite(env)
    monkeypatch.setattr(ar, "SETTLE_SECONDS", 0)
    monkeypatch.setattr(ar, "is_updater_running", lambda: True)
    assert ar.check(apply=True, repo_root=REPO_ROOT)["agent"] == "deferred_settling"


def test_reapply_is_serialized_by_lock(env, monkeypatch):
    asar = _install_and_overwrite(env)
    monkeypatch.setattr(ar, "SETTLE_SECONDS", 0)
    held = ar._reapply_lock()
    assert held.acquire()
    try:
        assert ar.check(apply=True, repo_root=REPO_ROOT)["agent"] == "deferred_locked"
        assert pa.PATCH_MARKER.encode() not in asar.read_bytes()
    finally:
        held.release()
    assert ar.check(apply=True, repo_root=REPO_ROOT)["agent"] == "reapplied"


def test_marker_scan_is_cached(env, monkeypatch):
    asar = _install_and_overwrite(env)
    n = {"scan": 0}
    real = ar._contains_marker

    def counting(p, marker=ar.PATCH_MARKER):
        n["scan"] += 1
        return real(p, marker)

    monkeypatch.setattr(ar, "_contains_marker", counting)
    ar._MARKER_CACHE.clear()
    for _ in range(5):
        assert ar.agent_status() == "needs_reapply"
    assert n["scan"] == 1, "同一指纹的 app.asar 只应全文扫描一次"


def test_watch_exits_when_disabled_and_single_instance(env):
    sm.update_state(auto_reapply=False)
    t0 = time.time()
    ar.watch(interval=30)  # 关闭状态下应立即返回而不是永远空转
    assert time.time() - t0 < 5
    assert not (sm.config_dir() / "background.pid").exists(), "退出时应释放单实例锁"
    assert ar._acquire_single_instance()
    try:
        lock2 = sm.FileLock(sm.config_dir() / "background.pid", timeout=0, stale=10 ** 9)
        assert not lock2.acquire(), "第二个后台实例不应启动"
    finally:
        ar._release_single_instance()


# ---------------------------------------------------------------- 6. 主进程皮肤加载器并发
@pytest.mark.skipif(not HAS_NODE, reason="需要 node")
def test_agent_skin_loader_serializes_concurrent_apply(env):
    cfg = env / "skin-cfg"
    (cfg / "compiled").mkdir(parents=True)
    payload = cfg / "compiled" / "active-skin.json"
    payload.write_text(json.dumps({"id": "a", "css": "body{color:red}", "pet": {}, "disabled": False}), encoding="utf-8")
    hook = si.build_agent_main_hook(str(cfg))
    harness = env / "loader.js"
    harness.write_text(hook + """
const fs = require('fs');
let n = 0; const live = new Set(); const events = [];
const wc = {
  isDestroyed: () => false, once() {},
  insertCSS: (css) => new Promise(r => setTimeout(() => { const k = 'k' + (++n); live.add(k); events.push(css); r(k); }, 5)),
  removeInsertedCSS: (k) => new Promise(r => setTimeout(() => { live.delete(k); r(); }, 5)),
  executeJavaScript: () => Promise.resolve(),
};
(async () => {
  // dom-ready 与 did-finish-load 几乎同时触发
  __agzhSkin.apply(wc); __agzhSkin.apply(wc); __agzhSkin.apply(wc);
  await new Promise(r => setTimeout(r, 200));
  const afterFirst = live.size;
  fs.writeFileSync(%s, JSON.stringify({ id: 'b', css: 'body{color:blue}', pet: {}, disabled: false }));
  __agzhSkin.apply(wc);
  await new Promise(r => setTimeout(r, 200));
  console.log(JSON.stringify({ afterFirst, live: live.size, last: events[events.length - 1] }));
  process.exit(0);
})();
""" % json.dumps(str(payload)), encoding="utf-8")
    r = subprocess.run(["node", str(harness)], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["afterFirst"] == 1, "并发 apply 不应留下重复且无法移除的样式"
    assert out["live"] == 1 and "blue" in out["last"], "切换皮肤后旧样式必须被移除"


# ---------------------------------------------------------------- 7. 桌宠 JS 性能约束
def _keyframes(js: str) -> dict:
    out = {}
    for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", js):
        out[m.group(1)] = set(re.findall(r"([a-z-]+)\s*:", m.group(2)))
    return out


def test_pet_css_animations_are_compositor_friendly():
    js = (REPO_ROOT / "resources" / "nezuko-pet.js").read_text(encoding="utf-8")
    bad = {k: sorted(v - {"transform", "opacity", "offset", "animation-timing-function"})
           for k, v in _keyframes(js).items()}
    bad = {k: v for k, v in bad.items() if v}
    assert not bad, f"无限循环动画应只动画 transform/opacity：{bad}"


def test_scarf_engine_cancels_pending_frame():
    js = (REPO_ROOT / "resources" / "nezuko-pet.js").read_text(encoding="utf-8")
    stop = js[js.index("    stop() {\n      this.isRunning = false;"):][:400]
    assert "cancelAnimationFrame(this.rafId)" in stop, "stop() 需取消已排队的帧，否则快速切换会叠加多条 rAF 循环"


@pytest.mark.skipif(not HAS_NODE, reason="需要 node")
def test_js_resources_parse():
    for name in ("nezuko-pet.js", "skin-runtime.js", "runtime-zh.js", "loadingOverlay-zh.js"):
        r = subprocess.run(["node", "--check", str(REPO_ROOT / "resources" / name)], capture_output=True, text=True,
                           encoding="utf-8")
        assert r.returncode == 0, f"{name}: {r.stderr}"
