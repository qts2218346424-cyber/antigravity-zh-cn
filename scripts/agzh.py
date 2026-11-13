#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 汉化 + 材质包 统一命令行 (agzh.py)

示例：
    python scripts/agzh.py status
    python scripts/agzh.py skin list
    python scripts/agzh.py skin use sakura-light
    python scripts/agzh.py skin override set background.opacity 0.25
    python scripts/agzh.py skin import my-skin.zip
    python scripts/agzh.py skin export nezuko-bamboo ./out/
    python scripts/agzh.py l10n install --lang zh-CN
    python scripts/agzh.py reapply enable
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agzh_core as core  # noqa: E402
import auto_reapply as ar  # noqa: E402
import skin_injector as si  # noqa: E402
import skin_manager as sm  # noqa: E402


def _parse_value(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="agzh", description="Antigravity 汉化与材质包管理")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="查看汉化 / 皮肤 / 自动重注入状态")

    sk = sub.add_parser("skin", help="材质包管理").add_subparsers(dest="action", required=True)
    sk.add_parser("list", help="列出材质包")
    sk.add_parser("current", help="当前材质包")
    u = sk.add_parser("use", help="切换材质包")
    u.add_argument("id")
    u.add_argument("--no-ide", action="store_true", help="不写入 IDE 工作台")
    u.add_argument("--ide-dir", help="手动指定 IDE 安装目录")
    sk.add_parser("off", help="关闭皮肤（保留材质包）")
    v = sk.add_parser("validate", help="校验材质包目录或 zip")
    v.add_argument("path")
    i = sk.add_parser("import", help="导入 .zip 材质包")
    i.add_argument("zip")
    i.add_argument("--overwrite", action="store_true")
    i.add_argument("--use", action="store_true", help="导入后立即启用")
    e = sk.add_parser("export", help="导出材质包为 .zip")
    e.add_argument("id")
    e.add_argument("dest")
    e.add_argument("--no-override", action="store_true", help="不把个人覆盖层烘焙进导出包")
    r = sk.add_parser("remove", help="删除材质包")
    r.add_argument("id")
    n = sk.add_parser("new", help="以现有包为模板新建")
    n.add_argument("source")
    n.add_argument("id")
    n.add_argument("name")
    sk.add_parser("sync-builtin", help="重新同步内置示例包").add_argument("--force", action="store_true")
    ov = sk.add_parser("override", help="用户覆盖层").add_subparsers(dest="ov_action", required=True)
    for name in ("show", "reset"):
        p = ov.add_parser(name)
        p.add_argument("--skin", help="材质包 id（默认当前包）")
        p.add_argument("--global", dest="is_global", action="store_true", help="作用于所有材质包的全局覆盖层")
    s = ov.add_parser("set", help="设置覆盖项，例如 background.opacity 0.2 / colors.accent '\"#ff0\"'")
    s.add_argument("key")
    s.add_argument("value")
    s.add_argument("--skin")
    s.add_argument("--global", dest="is_global", action="store_true")
    a = ov.add_parser("asset", help="把本地图片/字体复制进覆盖层并设置到某个键")
    a.add_argument("key")
    a.add_argument("file")
    a.add_argument("--skin")
    a.add_argument("--global", dest="is_global", action="store_true")

    ide = sub.add_parser("ide", help="IDE 工作台皮肤").add_subparsers(dest="action", required=True)
    for name in ("apply", "remove", "status"):
        ide.add_parser(name).add_argument("--dir", help="IDE 安装目录")

    l10n = sub.add_parser("l10n", help="汉化补丁").add_subparsers(dest="action", required=True)
    ins = l10n.add_parser("install")
    ins.add_argument("--lang", choices=["zh-CN", "zh-TW", "zh-HK"], default="zh-CN")
    ins.add_argument("--character", choices=["tanjiro", "zenitsu", "inosuke", "nezuko", "all"])
    ins.add_argument("--dir")
    ins.add_argument("--no-pet", action="store_true")
    ins.add_argument("--no-skin", action="store_true")
    rs = l10n.add_parser("restore")
    rs.add_argument("--dir")
    rs.add_argument("--keep-ide", action="store_true", help="保留 IDE 皮肤")

    rp = sub.add_parser("reapply", help="更新后自动重新注入").add_subparsers(dest="action", required=True)
    c = rp.add_parser("check")
    c.add_argument("--apply", action="store_true")
    c.add_argument("--force-running", action="store_true", help="即使 Antigravity 正在运行也写入")
    w = rp.add_parser("watch")
    w.add_argument("--interval", type=int, default=120)
    rp.add_parser("enable", help="开启开机自启后台检测")
    rp.add_parser("disable")
    rp.add_parser("status")

    pet = sub.add_parser("pet", help="桌面桌宠").add_subparsers(dest="action", required=True)
    pet.add_parser("launch")
    return ap


def _scope(args) -> str | None:
    if getattr(args, "is_global", False):
        return None
    return args.skin or sm.load_state().get("active_skin")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    core.bootstrap()
    try:
        if args.cmd == "status":
            print(json.dumps(core.status(), ensure_ascii=False, indent=2))
        elif args.cmd == "skin":
            return _skin(args)
        elif args.cmd == "ide":
            root = si.find_ide_app_root(args.dir)
            if args.action == "status":
                print(si.ide_status(root), root or "")
            elif root is None:
                print("未找到 Antigravity IDE 工作台（可用 --dir 指定安装目录）", file=sys.stderr)
                return 2
            elif args.action == "apply":
                print(si.inject_ide(root))
            else:
                print("已移除" if si.remove_ide(root) else "无需移除")
        elif args.cmd == "l10n":
            d = core.detect_install_dir(args.dir)
            if not d:
                print("未检测到 Antigravity 安装目录，请用 --dir 指定。", file=sys.stderr)
                return 2
            if args.action == "install":
                core.install_localization(d, args.lang, args.character, not args.no_pet, not args.no_skin)
            else:
                core.restore_localization(d, also_ide=not args.keep_ide)
        elif args.cmd == "reapply":
            if args.action == "check":
                print(json.dumps(ar.check(apply=args.apply, allow_when_running=args.force_running),
                                 ensure_ascii=False, indent=2))
            elif args.action == "watch":
                sm.update_state(auto_reapply=True)
                ar.watch(args.interval)
            elif args.action == "enable":
                print(ar.enable_autostart())
            elif args.action == "disable":
                print(ar.disable_autostart())
            else:
                st = sm.load_state()
                print(json.dumps({"auto_reapply": bool(st.get("auto_reapply")), "autostart": ar.autostart_enabled(),
                                  "agent": ar.agent_status(), "command": ar.background_command()},
                                 ensure_ascii=False, indent=2))
        elif args.cmd == "pet":
            core.launch_pet()
            print("桌宠已启动")
    except sm.SkinError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    return 0


def _skin(args) -> int:
    a = args.action
    if a == "list":
        for info in core.list_skins():
            mark = "*" if info["active"] else " "
            print(f"{mark} {info['id']:<20} {info['name']}  v{info['version']}  {info['author']}")
    elif a == "current":
        st = sm.load_state()
        print(st.get("active_skin") if st.get("skin_enabled", True) else "(已关闭)")
    elif a == "use":
        r = core.use_skin(args.id, apply_ide=False if args.no_ide else None, ide_dir=args.ide_dir)
        print(f"已切换到 {args.id}（Agent 桌面端实时生效；IDE: {r['ide']}，IDE 需重新加载窗口）")
    elif a == "off":
        print(core.skin_off())
    elif a == "validate":
        p = Path(args.path)
        if p.suffix.lower() == ".zip":
            import tempfile
            import zipfile
            with tempfile.TemporaryDirectory() as t, zipfile.ZipFile(p) as zf:
                zf.extractall(t)
                cands = [Path(t)] + [d for d in Path(t).iterdir() if d.is_dir()]
                p = next((c for c in cands if (c / sm.MANIFEST_NAME).is_file()), Path(t))
                sm.load_pack(p)
        else:
            sm.load_pack(p)
        print("校验通过 ✔")
    elif a == "import":
        pack = sm.import_pack(Path(args.zip), overwrite=args.overwrite)
        print(f"已导入 {pack.id}")
        if args.use:
            core.use_skin(pack.id)
    elif a == "export":
        print(sm.export_pack(args.id, Path(args.dest), include_override=not args.no_override))
    elif a == "remove":
        sm.remove_pack(args.id)
        print(f"已删除 {args.id}")
    elif a == "new":
        print(sm.create_pack_from(args.source, args.id, args.name).path)
    elif a == "sync-builtin":
        print(sm.sync_builtin_packs(force=args.force))
    elif a == "override":
        scope = _scope(args)
        if args.ov_action == "show":
            print(json.dumps(sm.load_override(scope), ensure_ascii=False, indent=2))
        elif args.ov_action == "reset":
            sm.reset_override(scope)
            sm.recompile_active()
            core.sync_ide()
        elif args.ov_action == "set":
            sm.set_override_value(scope, args.key, _parse_value(args.value))
            sm.recompile_active()
            core.sync_ide()
        elif args.ov_action == "asset":
            rel = sm.import_override_asset(Path(args.file))
            sm.set_override_value(scope, args.key, rel)
            sm.recompile_active()
            core.sync_ide()
    return 0


if __name__ == "__main__":
    sys.exit(main())
