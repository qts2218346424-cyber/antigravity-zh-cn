# -*- coding: utf-8 -*-
"""
一体化管理器：命令行入口与图形界面冒烟测试（无图形环境时自动跳过 GUI 部分）
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "app"))

import agzh  # noqa: E402
import skin_manager as sm  # noqa: E402


@pytest.fixture()
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("AGZH_CONFIG_DIR", str(tmp_path / "cfg"))
    import skin_injector as si
    monkeypatch.setattr(si, "_ide_candidates", lambda: [])
    return tmp_path / "cfg"


def test_cli_skin_flow(cfg, tmp_path, capsys):
    assert agzh.main(["skin", "list"]) == 0
    out = capsys.readouterr().out
    assert "sakura-light" in out and "nezuko-bamboo" in out and "midnight-dark" in out
    assert agzh.main(["skin", "use", "nezuko-bamboo"]) == 0
    assert sm.read_compiled()["id"] == "nezuko-bamboo"
    assert agzh.main(["skin", "override", "set", "background.opacity", "0.33"]) == 0
    assert "opacity: 0.33;" in sm.read_compiled()["css"]
    assert agzh.main(["skin", "override", "set", "colors.accent", "red; x"]) == 1, "非法覆盖值应被拒绝"
    assert agzh.main(["skin", "export", "nezuko-bamboo", str(tmp_path / "out") + "/"]) == 0
    z = tmp_path / "out" / "nezuko-bamboo-1.0.0.zip"
    assert agzh.main(["skin", "validate", str(z)]) == 0
    assert agzh.main(["skin", "off"]) == 0
    assert sm.read_compiled()["disabled"] is True
    capsys.readouterr()
    assert agzh.main(["status"]) == 0
    st = json.loads(capsys.readouterr().out)
    assert st["skin_enabled"] is False and st["config_dir"] == str(cfg)


def test_app_headless_cli_dispatch(cfg, capsys):
    import agzh_app
    assert agzh_app.run_headless(["cli", "skin", "current"]) == 0
    assert agzh_app.run_headless([]) is None, "无参数时应进入图形界面"


def _tk_available():
    try:
        import tkinter
        r = tkinter.Tk()
        r.destroy()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _tk_available(), reason="无可用的 Tk 图形环境")
def test_gui_smoke(cfg):
    import tkinter as tk
    import agzh_app
    agzh_app.core.bootstrap()
    root = tk.Tk()
    try:
        app = agzh_app.App(root)
        assert app.wait_idle(10)
        assert len(app.skins) >= 3
        app.select_skin_index(0)
        app.show_skin_detail()
        app.select_tab(1)
        assert app.wait_idle(10)
        app.form["colors.accent"].set("#ff00aa")
        app.form["pet.scale"].set("1.3")
        ov = app.collect_override()
        assert ov["colors"]["accent"] == "#ff00aa" and ov["pet"]["scale"] == 1.3
        assert "background" not in ov, "未改动背景时不应写入背景覆盖"
        for i in range(5):
            app.select_tab(i)
            root.update()
        for mode in ("dark", "light", "system"):
            app.set_theme(mode)
            root.update()
        assert app.wait_idle(10)
    finally:
        root.destroy()


@pytest.mark.skipif(not _tk_available(), reason="无可用的 Tk 图形环境")
def test_gui_slow_work_runs_off_main_thread(cfg, monkeypatch):
    """状态检测 / 打补丁等耗时操作必须在后台线程执行：主线程调用立即返回，界面不卡。"""
    import threading
    import time
    import tkinter as tk
    import agzh_app
    agzh_app.core.bootstrap()
    real_status = agzh_app.core.status
    seen = {}

    def slow_status():
        seen["status_thread"] = threading.current_thread() is threading.main_thread()
        time.sleep(0.6)
        return real_status()

    monkeypatch.setattr(agzh_app.core, "status", slow_status)
    root = tk.Tk()
    try:
        app = agzh_app.App(root)
        assert app.wait_idle(10)
        t0 = time.perf_counter()
        app.refresh_all()
        assert time.perf_counter() - t0 < 0.1, "refresh_all 不应阻塞主线程"
        assert seen["status_thread"] is False

        def task():
            print("来自工作线程的输出")
            seen["task_thread"] = threading.current_thread() is threading.main_thread()
            return 42

        got = {}
        app.run_task("测试任务", task, on_done=lambda r, e: got.setdefault("r", r))
        assert app.wait_idle(10)
        assert got["r"] == 42 and seen["task_thread"] is False
        assert any("来自工作线程的输出" in line for line in app.log_lines), "任务内 print 应进入日志面板"
        # 未捕获的线程（主线程）输出不应进入日志
        print("主线程输出不进日志")
        assert app.wait_idle(5)
        assert not any("主线程输出不进日志" in line for line in app.log_lines)
    finally:
        root.destroy()
    assert type(sys.stdout).__name__ != "OutputRouter", "窗口销毁后应恢复原始 stdout"


@pytest.mark.skipif(not _tk_available(), reason="无可用的 Tk 图形环境")
def test_gui_lazy_tabs_and_preview_cache(cfg):
    import tkinter as tk
    import agzh_app
    agzh_app.core.bootstrap()
    root = tk.Tk()
    try:
        app = agzh_app.App(root)
        assert app.wait_idle(10)
        assert app._built.get(0) and not app._built.get(1) and not app._built.get(2), "只应构建首页"
        n0 = len(app.images)
        assert n0 >= 1, "预览图应已解码并缓存"
        for i in range(len(app.skins) * 3):
            app.select_skin_index(i)
        assert app.wait_idle(10)
        n1 = len(app.images)
        for i in range(len(app.skins) * 3):
            app.select_skin_index(i)
        assert app.wait_idle(10)
        assert len(app.images) == n1, "重复选择不应重新解码预览图"
    finally:
        root.destroy()


def test_media_mode_outputs_json(cfg, capsys):
    import agzh_app
    assert agzh_app.run_headless(["--media", "status"]) == 0
    data = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert data["isPlaying"] is False and "title" in data
    assert agzh_app.run_headless(["--media", "rm -rf"]) == 2, "未知动作应被拒绝"


def test_build_override_pure(cfg, tmp_path):
    import agzh_app
    img = tmp_path / "bg.png"
    img.write_bytes((REPO_ROOT / "resources" / "skins" / "midnight-dark" / "preview.png").read_bytes())
    raw = {"colors": {"accent": " #123456 ", "background": ""},
           "bg": {"image": str(img), "opacity": 0.3, "blur": 2, "target": "编辑区", "position": "", "size": ""},
           "font": {"family": "Noto Sans", "size": "13", "monoFamily": "", "monoSize": ""},
           "icons": {"filter": "", "color": ""}, "pet": {"hidden": True, "scale": "", "sprite": ""},
           "css": "  \n", "loaded_bg": None}
    ov = agzh_app.build_override(raw)
    assert ov["colors"] == {"accent": "#123456"}
    assert ov["background"]["image"].startswith("assets/") and ov["background"]["target"] == "editor"
    assert ov["font"] == {"family": "Noto Sans", "size": 13} and ov["pet"] == {"hidden": True}
    assert "css" not in ov
