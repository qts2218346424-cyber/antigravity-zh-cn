#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 跨平台汉化补丁核心引擎 (patch_antigravity.py)
支持 Windows、macOS 和 Linux。
特性：
1. 原位（In-place）无损修补 ASAR 归档，无需提取到磁盘，100% 保留 app.asar.unpacked/ 下所有解包索引（如 chrome-devtools-mcp）；
2. 毫秒级执行，不依赖 node、npm 或 npx；
3. 修补原生菜单 (menu.js)、系统托盘 (tray.js)、更新提示 (updater.js) 与预加载脚本 (preload.js)；
4. 自动备份 app.asar.bak，支持一键还原与更新管理。
"""

import os
import sys
import json
import shutil
import struct
import hashlib
from pathlib import Path

# UTF-8 控制台编码兼容
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# 补丁注入特征标记
PATCH_MARKER = "/* __ANTIGRAVITY_ZH_CN_PATCHED__ */"
ASAR_INTEGRITY_BLOCK_SIZE = 4 * 1024 * 1024


def align4(size: int) -> int:
    return (size + 3) & ~3


def calculate_file_integrity(data: bytes) -> dict:
    blocks = [
        hashlib.sha256(data[i : i + ASAR_INTEGRITY_BLOCK_SIZE]).hexdigest()
        for i in range(0, len(data), ASAR_INTEGRITY_BLOCK_SIZE)
    ]
    if not blocks:
        blocks.append(hashlib.sha256(data).hexdigest())
    return {
        "algorithm": "SHA256",
        "hash": hashlib.sha256(data).hexdigest(),
        "blockSize": ASAR_INTEGRITY_BLOCK_SIZE,
        "blocks": blocks,
    }


def read_asar_header(data: bytes | bytearray) -> tuple[int, str, dict]:
    if len(data) < 16:
        raise ValueError("ASAR 文件损坏或格式不支持（小于 16 字节）")
    header_size = struct.unpack_from("<I", data, 4)[0]
    header_pickle = data[8 : 8 + header_size]
    header_str_size = struct.unpack_from("<i", header_pickle, 4)[0]
    header_str = header_pickle[8 : 8 + header_str_size].decode("utf-8")
    return header_size, header_str, json.loads(header_str)


def encode_asar_header_dynamic(header_string: str) -> bytes:
    hb = header_string.encode("utf-8")
    payload_size = align4(4 + len(hb))
    pickle = (
        struct.pack("<I", payload_size)
        + struct.pack("<i", len(hb))
        + hb
        + b"\0" * (payload_size - 4 - len(hb))
    )
    return struct.pack("<I", 4) + struct.pack("<I", len(pickle)) + pickle


def get_asar_file_entry(header: dict, file_path: str) -> dict:
    node = header
    for part in file_path.split("/"):
        files = node.get("files")
        if not isinstance(files, dict) or part not in files:
            raise KeyError(f"ASAR 索引中未找到文件: {file_path}")
        node = files[part]
    if "offset" not in node or "size" not in node:
        raise ValueError(f"文件条目缺少 offset 或 size 字段: {file_path}")
    return node


def iter_asar_file_entries(header: dict) -> list[dict]:
    entries = []
    def walk(node):
        files = node.get("files")
        if not isinstance(files, dict):
            return
        for child in files.values():
            if not isinstance(child, dict):
                continue
            if "files" in child:
                walk(child)
            elif "offset" in child and "size" in child:
                entries.append(child)
    walk(header)
    return entries


def read_asar_file_content(asar_data: bytes | bytearray, file_path: str) -> bytes:
    header_size, _, header = read_asar_header(asar_data)
    entry = get_asar_file_entry(header, file_path)
    offset = 8 + header_size + int(entry["offset"])
    size = int(entry["size"])
    return bytes(asar_data[offset : offset + size])


def replace_asar_file_content(asar_data: bytearray, file_path: str, new_content: bytes) -> bytearray:
    """
    原位替换 ASAR 归档内部特定文件的内容，并动态更新偏移量与头部哈希。
    保留所有 unpacked: true 的外部文件索引，完全避免丢失 app.asar.unpacked/。
    """
    header_size, _, header = read_asar_header(asar_data)
    entry = get_asar_file_entry(header, file_path)

    old_offset = int(entry["offset"])
    old_size = int(entry["size"])
    content_offset = 8 + header_size + old_offset
    content_end = content_offset + old_size

    old_content = bytes(asar_data[content_offset:content_end])
    if old_content == new_content:
        return asar_data

    delta = len(new_content) - old_size
    asar_data[content_offset:content_end] = new_content

    entry["size"] = len(new_content)
    if "integrity" in entry:
        entry["integrity"] = calculate_file_integrity(new_content)

    if delta != 0:
        for other in iter_asar_file_entries(header):
            if other is not entry and int(other["offset"]) > old_offset:
                other["offset"] = str(int(other["offset"]) + delta)

    updated_header_string = json.dumps(header, ensure_ascii=False, separators=(",", ":"))
    updated_header = encode_asar_header_dynamic(updated_header_string)
    body = bytes(asar_data[8 + header_size :])

    return bytearray(updated_header + body)


def get_default_install_path() -> Path | None:
    """自动检测当前操作系统的 Antigravity 安装目录"""
    if sys.platform == 'win32':
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if local_app_data:
            candidate = Path(local_app_data) / "Programs" / "antigravity"
            if (candidate / "resources" / "app.asar").is_file():
                return candidate
    elif sys.platform == 'darwin':
        candidate = Path("/Applications/Antigravity.app")
        if (candidate / "Contents" / "Resources" / "app.asar").is_file():
            return candidate
    else:  # Linux
        candidates = [
            Path("/opt/antigravity"),
            Path(os.path.expanduser("~/.local/share/antigravity")),
            Path("/usr/lib/antigravity")
        ]
        for c in candidates:
            if (c / "resources" / "app.asar").is_file():
                return c
    return None


def get_asar_path(install_dir: Path) -> Path:
    if sys.platform == 'darwin':
        return install_dir / "Contents" / "Resources" / "app.asar"
    return install_dir / "resources" / "app.asar"


def apply_patch(install_dir: Path, lang: str = "zh-CN", repo_root: Path = None):
    """
    完整安装补丁流程：
    采用原位无损修改技术，精准替换 menu.js、tray.js、updater.js 和 preload.js。
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    asar_path = get_asar_path(install_dir)
    if not asar_path.is_file():
        raise FileNotFoundError(f"未找到 app.asar: {asar_path}")

    backup_path = asar_path.with_suffix('.asar.bak')

    # 1. 备份原版 asar（如果尚未存在备份）
    if not backup_path.exists():
        print(f"[1/4] 正在创建原版备份: {backup_path.name}...")
        shutil.copy2(asar_path, backup_path)
    else:
        print(f"[1/4] 发现已有原版备份: {backup_path.name}")

    # 载入本地化资源
    res_dir = repo_root / "resources"
    dict_file = res_dir / f"antigravity-{lang}.json"
    if not dict_file.is_file():
        dict_file = res_dir / "antigravity-zh-CN.json"

    with open(dict_file, "r", encoding="utf-8") as f:
        lang_dict = json.load(f)

    with open(res_dir / "desktop-zh-CN.json", "r", encoding="utf-8") as f:
        desktop_dict = json.load(f)

    with open(res_dir / "rules-zh-CN.json", "r", encoding="utf-8") as f:
        rules_list = json.load(f)

    with open(res_dir / "runtime-zh.js", "r", encoding="utf-8") as f:
        runtime_js_code = f.read()

    # 始终基于纯净备份读取，确保多次重复运行不受影响
    source_asar = backup_path if backup_path.exists() else asar_path
    print(f"[2/4] 正在读取并解析 ASAR 索引 (源: {source_asar.name})...")
    asar_data = bytearray(source_asar.read_bytes())

    print("[3/4] 正在原位修补原生菜单、托盘及注入 DOM 翻译引擎...")

    # 构建运行时注入脚本
    injection_code = f"""
(function() {{
  try {{
    window.__AGY_ZH_LANG__ = {json.dumps(lang)};
    window.__AGY_ZH_DICT__ = {json.dumps(lang_dict, ensure_ascii=False)};
    window.__AGY_ZH_RULES__ = {json.dumps(rules_list, ensure_ascii=False)};
    {runtime_js_code}
  }} catch(e) {{
    console.error("[AGY-ZH] Failed to bootstrap translation:", e);
  }}
}})();
"""

    # (1) 修补 dist/menu.js (深度递归翻译菜单 + 开放开发者工具)
    try:
        menu_content = read_asar_file_content(asar_data, "dist/menu.js").decode("utf-8")
        menu_dict_json = json.dumps(desktop_dict.get("menu", {}), ensure_ascii=False)
        menu_patch = f"""
{PATCH_MARKER}
const __AGY_MENU_DICT__ = {menu_dict_json};
function __agyTranslateMenu(m) {{
    if (!m) return;
    if (m.items) {{
        m.items.forEach(item => {{
            if (item.label && __AGY_MENU_DICT__[item.label]) {{
                item.label = __AGY_MENU_DICT__[item.label];
            }}
            if (item.submenu) {{
                __agyTranslateMenu(item.submenu);
            }}
        }});
    }}
}}
"""
        if PATCH_MARKER not in menu_content:
            menu_content = menu_patch + "\n" + menu_content
            menu_content = menu_content.replace(
                "electron_1.Menu.setApplicationMenu(menu);",
                "__agyTranslateMenu(menu); electron_1.Menu.setApplicationMenu(menu);"
            )
            menu_content = menu_content.replace("item.visible = false;", "item.visible = true;")
            asar_data = replace_asar_file_content(asar_data, "dist/menu.js", menu_content.encode("utf-8"))
            print("  [OK] 原生菜单 (dist/menu.js) 递归汉化与调试支持修补完成")
    except Exception as e:
        print(f"  [!] 忽略非致命项 dist/menu.js: {e}")

    # (2) 修补 dist/tray.js
    try:
        tray_content = read_asar_file_content(asar_data, "dist/tray.js").decode("utf-8")
        tray_dict = desktop_dict.get("tray", {})
        for en, zh in tray_dict.items():
            tray_content = tray_content.replace(f"'{en}'", f"'{zh}'")
            tray_content = tray_content.replace(f'"{en}"', f'"{zh}"')
        tray_content = tray_content.replace("`Open ${electron_1.app.getName()}`", "`打开 ${electron_1.app.getName()}`")
        tray_content = tray_content.replace("' agent'", "' 个代理'")
        tray_content = tray_content.replace("' agents'", "' 个代理'")
        tray_content = tray_content.replace("' running'", "' 正在运行'")
        asar_data = replace_asar_file_content(asar_data, "dist/tray.js", tray_content.encode("utf-8"))
        print("  [OK] 系统托盘 (dist/tray.js) 修补完成")
    except Exception as e:
        print(f"  [!] 忽略非致命项 dist/tray.js: {e}")

    # (3) 修补 dist/updater.js
    try:
        updater_content = read_asar_file_content(asar_data, "dist/updater.js").decode("utf-8")
        updater_content = updater_content.replace('"Check for Updates"', '"检查更新"')
        updater_content = updater_content.replace('"Checking for Updates..."', '"正在检查更新..."')
        updater_content = updater_content.replace('"Downloading Update..."', '"正在下载更新..."')
        updater_content = updater_content.replace('"Restart to Update"', '"重启以更新"')
        asar_data = replace_asar_file_content(asar_data, "dist/updater.js", updater_content.encode("utf-8"))
        print("  [OK] 更新提示 (dist/updater.js) 修补完成")
    except Exception as e:
        print(f"  [!] 忽略非致命项 dist/updater.js: {e}")

    # (4) 修补 dist/preload.js (预加载阶段 DOM 翻译引擎)
    try:
        preload_content = read_asar_file_content(asar_data, "dist/preload.js").decode("utf-8")
        if PATCH_MARKER not in preload_content:
            preload_content += f"\n{PATCH_MARKER}\n{injection_code}\n"
            asar_data = replace_asar_file_content(asar_data, "dist/preload.js", preload_content.encode("utf-8"))
            print("  [OK] DOM 翻译引擎预加载通道注入完成 (dist/preload.js)")
    except Exception as e:
        print(f"  [!] 预加载环境注入失败: {e}")
        raise

    # (5) 修补 dist/utils.js (主世界 executeJavaScript 强保通道 + DevTools + 日志回传)
    try:
        utils_content = read_asar_file_content(asar_data, "dist/utils.js").decode("utf-8")
        if PATCH_MARKER not in utils_content:
            utils_content = utils_content.replace(
                "devTools: !electron_1.app.isPackaged,",
                "devTools: true,"
            )
            js_raw = json.dumps(injection_code)
            hook_code = f"""
/* __ANTIGRAVITY_ZH_CN_PATCHED__ */
const __AGY_ZH_CODE__ = {js_raw};
"""
            utils_content = hook_code + "\n" + utils_content

            target_str = "void win.loadURL(url);"
            replacement_str = """
    win.webContents.on('console-message', (_event, level, message, line, sourceId) => {
        console.log(`[Renderer L${level}] ${message}`);
    });
    const __agyTriggerInject = () => {
        win.webContents.executeJavaScript(__AGY_ZH_CODE__).catch((err) => {
            console.log('[AGY-ZH] executeJavaScript error:', err);
        });
    };
    win.webContents.on('dom-ready', __agyTriggerInject);
    win.webContents.on('did-finish-load', __agyTriggerInject);
    void win.loadURL(url);
"""
            if target_str in utils_content:
                utils_content = utils_content.replace(target_str, replacement_str, 1)
                asar_data = replace_asar_file_content(asar_data, "dist/utils.js", utils_content.encode("utf-8"))
                print("  [OK] 主世界注入通道与日志回传系统挂载完成 (dist/utils.js)")
            else:
                print("  [!] 未在 dist/utils.js 中找到 void win.loadURL(url); 锚点")
    except Exception as e:
        print(f"  [!] 主世界注入通道修补失败: {e}")

    # (6) 修补 dist/loadingOverlay.js (消除启动白屏卡顿与翻译启动文本)
    try:
        overlay_content = read_asar_file_content(asar_data, "dist/loadingOverlay.js").decode("utf-8")
        overlay_content = overlay_content.replace(
            '<div class="text">Loading Antigravity</div>',
            '<div class="text">正在加载 Antigravity...</div>'
        )
        old_remove_str = """    win.webContents.once('did-finish-load', () => {
        try {
            win.contentView.removeChildView(view);
        }
        catch (_) {
            // In case window was closed quickly
        }
        win.off('resize', updateBounds);
    });"""
        new_remove_str = """    let __agyOverlayRemoved = false;
    const __agyRemoveOverlay = () => {
        if (__agyOverlayRemoved) return;
        __agyOverlayRemoved = true;
        try {
            win.contentView.removeChildView(view);
        } catch (_) {}
        win.off('resize', updateBounds);
    };
    win.webContents.once('dom-ready', __agyRemoveOverlay);
    win.webContents.once('did-finish-load', __agyRemoveOverlay);
    setTimeout(__agyRemoveOverlay, 1500);"""
        if old_remove_str in overlay_content:
            overlay_content = overlay_content.replace(old_remove_str, new_remove_str)
            asar_data = replace_asar_file_content(asar_data, "dist/loadingOverlay.js", overlay_content.encode("utf-8"))
            print("  [OK] 启动加载遮罩 (dist/loadingOverlay.js) 防白屏卡顿优化完成")
    except Exception as e:
        print(f"  [!] 忽略非致命项 dist/loadingOverlay.js: {e}")

    # 4. 安全写入目标文件
    print(f"[4/4] 正在安全写入汉化文件: {asar_path.name}...")
    temp_dest = asar_path.with_suffix('.asar.tmp')
    try:
        temp_dest.write_bytes(asar_data)
        shutil.move(str(temp_dest), str(asar_path))
    except Exception:
        asar_path.write_bytes(asar_data)
        if temp_dest.exists():
            try:
                temp_dest.unlink(missing_ok=True)
            except Exception:
                pass

    print("[OK] Antigravity 汉化补丁无损安装成功！所有解包索引 100% 保留！")


def restore_backup(install_dir: Path):
    """还原原版 app.asar"""
    asar_path = get_asar_path(install_dir)
    backup_path = asar_path.with_suffix('.asar.bak')

    if not backup_path.exists():
        print("未检测到原版备份文件 (app.asar.bak)，无法执行还原。")
        return False

    print(f"正在从备份文件还原: {backup_path.name} -> {asar_path.name}...")
    shutil.copy2(backup_path, asar_path)
    print("[OK] 已成功还原为官方原版！")
    return True


def toggle_auto_updates(install_dir: Path, disable: bool):
    """切换自动更新开关状态"""
    update_yml = install_dir / "resources" / "app-update.yml"
    disabled_yml = install_dir / "resources" / "app-update.yml.disabled"

    if disable:
        if update_yml.is_file():
            shutil.move(str(update_yml), str(disabled_yml))
            print("[OK] 已成功禁止自动更新 (app-update.yml 已重命名为 app-update.yml.disabled)。")
        elif disabled_yml.is_file():
            print("ℹ 当前已处于禁止自动更新状态。")
        else:
            print("⚠ 未找到 app-update.yml 配置文件。")
    else:
        if disabled_yml.is_file():
            shutil.move(str(disabled_yml), str(update_yml))
            print("[OK] 已成功恢复官方自动更新 (app-update.yml.disabled 已恢复)。")
        elif update_yml.is_file():
            print("ℹ 当前已允许自动更新。")
        else:
            print("⚠ 未找到 app-update.yml.disabled 配置文件。")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Antigravity 中文汉化补丁管理程序")
    parser.add_argument("action", choices=["install", "restore", "disable-updates", "enable-updates"],
                        nargs="?", default="install", help="执行操作 (默认: install)")
    parser.add_argument("--lang", choices=["zh-CN", "zh-TW", "zh-HK"], default="zh-CN",
                        help="目标语言 (默认: zh-CN)")
    parser.add_argument("--dir", help="Antigravity 安装目录路径 (默认自动检测)")

    args = parser.parse_args()

    install_dir = Path(args.dir).resolve() if args.dir else get_default_install_path()
    if not install_dir or not install_dir.is_dir():
        print("错误: 未检测到 Antigravity 安装目录，请通过 --dir 参数手动指定。", file=sys.stderr)
        sys.exit(1)

    print(f"目标目录: {install_dir}")
    repo_root = Path(__file__).resolve().parent.parent

    if args.action == "install":
        apply_patch(install_dir, args.lang, repo_root)
    elif args.action == "restore":
        restore_backup(install_dir)
    elif args.action == "disable-updates":
        toggle_auto_updates(install_dir, disable=True)
    elif args.action == "enable-updates":
        toggle_auto_updates(install_dir, disable=False)


if __name__ == "__main__":
    main()
