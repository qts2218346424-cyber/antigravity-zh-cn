# -*- coding: utf-8 -*-
"""
材质包清单解析 / 校验 / 多层合并 / 编译 / 导入导出 专项测试
"""
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import skin_manager as sm  # noqa: E402

BUILTIN = REPO_ROOT / "resources" / "skins"
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360f8cf000000030001b7c1b6e10000000049454e44ae426082"
)


@pytest.fixture()
def cfg(tmp_path, monkeypatch):
    d = tmp_path / "cfg"
    monkeypatch.setenv("AGZH_CONFIG_DIR", str(d))
    return d


def _pack(root: Path, manifest: dict, files: dict | None = None) -> Path:
    d = root / manifest.get("id", "p")
    d.mkdir(parents=True, exist_ok=True)
    for rel, data in (files or {}).items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_bytes(data)
    (d / "skin.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return d


def _base(**kw):
    m = {"schema": 1, "id": "demo", "name": "演示", "version": "1.0.0"}
    m.update(kw)
    return m


# ---------------------------------------------------------------- 校验
def test_builtin_packs_are_valid():
    ids = []
    for d in sorted(BUILTIN.iterdir()):
        if (d / "skin.json").is_file():
            pack = sm.load_pack(d)
            ids.append(pack.id)
            assert pack.id == d.name, "内置包目录名应与 id 一致"
            assert pack.preview_path() is not None, f"{pack.id} 缺少预览图"
    assert {"midnight-dark", "sakura-light", "nezuko-bamboo"} <= set(ids)


def test_minimal_manifest_ok(tmp_path):
    d = _pack(tmp_path, _base())
    assert sm.load_pack(d).name == "演示"


@pytest.mark.parametrize("patch,needle", [
    ({"id": "Bad ID"}, "id:"),
    ({"id": "_global"}, "id:"),
    ({"version": "v1"}, "version:"),
    ({"name": ""}, "name:"),
    ({"schema": 99}, "schema:"),
    ({"base": "grey"}, "base:"),
    ({"colors": {"accent": "red; background:url(x)"}}, "colors.accent"),
    ({"colors": {"nope": "#fff"}}, "colors.nope"),
    ({"variables": {"--x": "1}body{display:none"}}, "variables.--x"),
    ({"variables": {"x": "1"}}, "variables:"),
    ({"background": {"image": "bg.png", "opacity": 2}}, "opacity"),
    ({"background": {"image": "bg.png", "blur": -1}}, "blur"),
    ({"background": {"image": "bg.png", "target": "everywhere"}}, "target"),
    ({"background": {"image": "../secret.png"}}, "相对路径"),
    ({"background": {"image": "C:/Windows/x.png"}}, "相对路径"),
    ({"background": {"image": "missing.png"}}, "找不到"),
    ({"background": {"image": "bg.exe"}}, "不支持的文件类型"),
    ({"font": {"size": 100}}, "font.size"),
    ({"font": {"family": "x;}"}}, "font.family"),
    ({"pet": {"character": "tanjiro"}}, "pet.character"),
    ({"pet": {"scale": 9}}, "pet.scale"),
    ({"pet": {"filter": "url(javascript:x)"}}, "pet.filter"),
    ({"icons": {"codicons": {"Bad Name": "bg.png"}}}, "icons.codicons"),
    ({"css": "a{}</style><script>"}, "css"),
])
def test_invalid_manifests_rejected(tmp_path, patch, needle):
    d = _pack(tmp_path, _base(**patch), {"bg.png": PNG_1PX, "bg.exe": b"MZ"})
    with pytest.raises(sm.SkinError) as ei:
        sm.load_pack(d)
    assert any(needle in e for e in ei.value.errors), ei.value.errors


def test_invalid_json_reports_position(tmp_path):
    d = tmp_path / "broken"
    d.mkdir()
    (d / "skin.json").write_text('{"id": "x",,}', encoding="utf-8")
    with pytest.raises(sm.SkinError) as ei:
        sm.load_pack(d)
    assert "第 1 行" in str(ei.value)


def test_css_color_forms():
    for ok in ("#fff", "#ffff", "#a1b2c3", "#a1b2c3d4", "rgb(1, 2, 3)", "rgba(1,2,3,0.5)", "hsl(10 20% 30%)", "transparent"):
        assert sm.is_css_color(ok), ok
    for bad in ("#ggg", "red;", "url(x)", "", None, 3):
        assert not sm.is_css_color(bad), bad


# ---------------------------------------------------------------- 合并
def test_deep_merge_semantics():
    base = {"colors": {"a": 1, "b": 2}, "background": [{"image": "x", "opacity": 0.1}, {"image": "y"}], "css": "p"}
    assert sm.deep_merge(base, {"colors": {"b": None, "c": 3}})["colors"] == {"a": 1, "c": 3}
    # 单个对象覆盖对象数组：只改第一项
    m = sm.deep_merge(base, {"background": {"opacity": 0.5}})
    assert m["background"][0] == {"image": "x", "opacity": 0.5} and m["background"][1] == {"image": "y"}
    # 数组按下标合并，null 删除对应项
    m = sm.deep_merge(base, {"background": [None, {"opacity": 0.3}]})
    assert m["background"] == [{"image": "y", "opacity": 0.3}]
    assert base["background"][0]["opacity"] == 0.1, "合并不得修改原对象"


def test_override_layers_and_css_append(cfg):
    src = _pack(cfg / "skins", _base(id="demo", colors={"accent": "#111111", "background": "#000000"},
                                     background={"image": "bg.png", "opacity": 0.1}, css=".pack{}"),
                {"bg.png": PNG_1PX})
    assert src.parent == sm.skins_dir()
    sm.save_override(None, {"colors": {"accent": "#222222"}, "css": ".global{}"})
    sm.save_override("demo", {"colors": {"background": "#333333"}, "background": {"opacity": 0.6}, "css": ".mine{}"})
    m = sm.effective_manifest(sm.get_pack("demo"))
    assert m["colors"] == {"accent": "#222222", "background": "#333333"}
    assert m["background"]["opacity"] == 0.6 and m["background"]["image"].endswith("bg.png")
    assert m["css"].index(".pack{}") < m["css"].index(".global{}") < m["css"].index(".mine{}")


def test_override_validation_and_assets(cfg, tmp_path):
    with pytest.raises(sm.SkinError):
        sm.save_override("demo", {"background": {"opacity": 5}})
    img = tmp_path / "我的 背景.png"
    img.write_bytes(PNG_1PX)
    rel = sm.import_override_asset(img)
    assert rel.startswith("assets/") and (sm.overrides_dir() / rel).is_file()
    sm.set_override_value("demo", "background.image", rel)
    assert sm.load_override("demo")["background"]["image"] == rel


# ---------------------------------------------------------------- 编译
def test_compile_builds_css_and_pet_payload(cfg):
    _pack(cfg / "skins", _base(
        colors={"accent": "#e86a92", "background": "#fff8fb"},
        variables={"--my-var": "12px"},
        background=[{"image": "bg.png", "target": "editor", "opacity": 0.25, "blur": 3}],
        font={"family": "Microsoft YaHei UI, sans-serif", "size": 13, "monoFamily": "Consolas", "ligatures": False},
        icons={"filter": "hue-rotate(30deg)", "codicons": {"heart": "bg.png"}},
        pet={"character": "nezuko", "sprite": "bg.png", "scale": 1.2},
    ), {"bg.png": PNG_1PX})
    payload = sm.activate("demo")
    css = payload["css"]
    assert "--vscode-button-background: #e86a92 !important;" in css
    assert "--my-var: 12px !important;" in css
    assert "data:image/png;base64," in css and "opacity: 0.25;" in css and "filter: blur(3px);" in css
    assert ".part.editor > .content::before" in css
    assert '"Microsoft YaHei UI", sans-serif' in css
    assert "font-variant-ligatures: none" in css
    assert ".codicon.codicon-heart::before" in css
    assert payload["pet"]["sprite"].startswith("data:image/png;base64,")
    assert payload["pet"]["accent"] == "#e86a92", "桌宠强调色默认继承主题强调色"
    assert sm.read_compiled()["hash"] == payload["hash"]
    assert sm.compiled_css_path().read_text(encoding="utf-8") == css
    assert sm.load_state()["active_skin"] == "demo"
    # 编译结果稳定（相同输入 → 相同哈希），用于 IDE 变更检测
    assert sm.activate("demo")["hash"] == payload["hash"]
    off = sm.deactivate()
    assert off["disabled"] and sm.read_compiled()["disabled"]


def test_all_builtin_packs_compile(cfg):
    sm.sync_builtin_packs()
    for p in sm.list_packs():
        payload = sm.compile_skin(p)
        assert payload["css"].startswith("/* antigravity-zh-cn skin")
        assert "</style" not in payload["css"].lower()


# ---------------------------------------------------------------- 内置同步 / 导入导出
def test_sync_builtin_respects_user_changes(cfg):
    assert set(sm.sync_builtin_packs()) >= {"midnight-dark", "sakura-light", "nezuko-bamboo"}
    mf = sm.skins_dir() / "sakura-light" / "skin.json"
    data = json.loads(mf.read_text(encoding="utf-8"))
    data["builtin"] = False  # 用户已接管该包
    data["name"] = "我改过的樱花"
    mf.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    assert "sakura-light" not in sm.sync_builtin_packs()
    assert sm.get_pack("sakura-light").name == "我改过的樱花"
    assert sm.sync_builtin_packs() == [], "版本未升级时不应重复复制"


def test_export_import_roundtrip_with_override(cfg, tmp_path):
    sm.sync_builtin_packs()
    img = tmp_path / "pet.png"
    img.write_bytes(PNG_1PX)
    sm.set_override_value("nezuko-bamboo", "pet.sprite", sm.import_override_asset(img))
    z = sm.export_pack("nezuko-bamboo", tmp_path / "out")
    assert z.name == "nezuko-bamboo-1.0.0.zip"
    with zipfile.ZipFile(z) as zf:
        m = json.loads(zf.read("skin.json"))
        assert "builtin" not in m
        assert m["pet"]["sprite"].startswith("override-assets/")
        assert m["pet"]["sprite"] in zf.namelist()
    sm.remove_pack("nezuko-bamboo")
    pack = sm.import_pack(z)
    assert pack.id == "nezuko-bamboo" and (pack.path / pack.manifest["pet"]["sprite"]).is_file()
    with pytest.raises(sm.SkinError):
        sm.import_pack(z)  # 已存在
    assert sm.import_pack(z, overwrite=True).id == "nezuko-bamboo"


def test_import_zip_in_subfolder_and_zip_slip(cfg, tmp_path):
    good = tmp_path / "good.zip"
    with zipfile.ZipFile(good, "w") as zf:
        zf.writestr("my-pack/skin.json", json.dumps(_base(id="my-pack")))
        zf.writestr("my-pack/bg.png", PNG_1PX)
    assert sm.import_pack(good).id == "my-pack"

    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr("skin.json", json.dumps(_base(id="evil")))
        zf.writestr("../../escape.txt", b"x")
    with pytest.raises(sm.SkinError):
        sm.import_pack(evil)
    assert not (cfg.parent / "escape.txt").exists()

    noman = tmp_path / "noman.zip"
    with zipfile.ZipFile(noman, "w") as zf:
        zf.writestr("readme.txt", b"x")
    with pytest.raises(sm.SkinError):
        sm.import_pack(noman)


def test_create_pack_from_template(cfg):
    sm.sync_builtin_packs()
    sm.set_override_value("midnight-dark", "colors.accent", "#ff8800")
    p = sm.create_pack_from("midnight-dark", "my-midnight", "我的午夜")
    assert p.manifest["colors"]["accent"] == "#ff8800" and p.name == "我的午夜"
    assert not p.manifest.get("builtin")


# ---------------------------------------------------------------- 运行时 JS
@pytest.mark.skipif(shutil.which("node") is None, reason="未安装 node")
def test_runtime_js_syntax(tmp_path):
    js = tmp_path / "rt.js"
    js.write_text(sm.build_pet_window_snippet({"id": "x", "css": "a{}", "pet": {"sprite": "data:,", "scale": 1}}),
                  encoding="utf-8")
    r = subprocess.run(["node", "-c", str(js)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_config_dir_platform_defaults(monkeypatch, tmp_path):
    monkeypatch.delenv("AGZH_CONFIG_DIR", raising=False)
    monkeypatch.setattr(sm.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    assert sm.config_dir() == tmp_path / "Roaming" / "antigravity-zh-cn"
    monkeypatch.setattr(sm.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert sm.config_dir() == tmp_path / "xdg" / "antigravity-zh-cn"
