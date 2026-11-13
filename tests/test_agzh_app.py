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
        root.update()
        assert len(app.skins) >= 3
        app.skin_list.selection_clear(0, "end")
        app.skin_list.selection_set(0)
        app.show_skin_detail()
        app.load_custom_form()
        app.form["colors.accent"].set("#ff00aa")
        app.form["pet.scale"].set("1.3")
        ov = app.collect_override()
        assert ov["colors"]["accent"] == "#ff00aa" and ov["pet"]["scale"] == 1.3
        assert "background" not in ov, "未改动背景时不应写入背景覆盖"
        for i in range(5):
            app.nb.select(i)
            root.update()
    finally:
        root.destroy()
