#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 跨平台汉化补丁核心引擎 (patch_antigravity.py)
支持 Windows、macOS 和 Linux。
功能：
1. 自动定位 Antigravity 安装目录与 app.asar；
2. 安全备份原始 app.asar；
3. 修补 app.asar（原生菜单 menu.js、托盘 tray.js、更新器 updater.js、预加载 preload.js 注入 DOM 翻译引擎）；
4. 提供一键还原 (restore/uninstall) 与自动更新管理。
"""

import os
import sys
import json
import shutil
import struct
import tempfile
import subprocess
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

class AsarArchive:
    """
    轻量级原生 Python 实现的 Electron ASAR 解构与打包工具。
    无需依赖全局 node/npm/npx，可在纯 Python 环境下完成 asar 打包与解包。
    """
    @staticmethod
    def extract(asar_path: Path, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(asar_path, 'rb') as f:
            # 读取 asar 头部
            magic = struct.unpack('<I', f.read(4))[0]
            header_size = struct.unpack('<I', f.read(4))[0]
            header_str_size = struct.unpack('<I', f.read(4))[0]
            header_json_size = struct.unpack('<I', f.read(4))[0]
            
            header_json_bytes = f.read(header_json_size)
            header_str = header_json_bytes.decode('utf-8').rstrip('\x00')
            header = json.loads(header_str)
            
            base_offset = f.tell()
            
            def extract_files(files_dict, current_dir):
                for name, info in files_dict.items():
                    target_path = current_dir / name
                    if 'files' in info:
                        target_path.mkdir(exist_ok=True)
                        extract_files(info['files'], target_path)
                    elif 'offset' in info and 'size' in info:
                        file_offset = base_offset + int(info['offset'])
                        file_size = int(info['size'])
                        curr = f.tell()
                        f.seek(file_offset)
                        data = f.read(file_size)
                        f.seek(curr)
                        with open(target_path, 'wb') as out_f:
                            out_f.write(data)
                            
            if 'files' in header:
                extract_files(header['files'], output_dir)

    @staticmethod
    def pack(source_dir: Path, output_asar: Path):
        files_data = []
        
        def build_header_tree(dir_path: Path):
            files = {}
            for item in sorted(dir_path.iterdir(), key=lambda p: p.name):
                if item.is_dir():
                    files[item.name] = {
                        "files": build_header_tree(item)
                    }
                elif item.is_file():
                    with open(item, 'rb') as f:
                        data = f.read()
                    offset = len(files_data)
                    files_data.extend(data)
                    files[item.name] = {
                        "size": len(data),
                        "offset": str(offset)
                    }
            return files

        file_tree = {"files": build_header_tree(source_dir)}
        header_json = json.dumps(file_tree, separators=(',', ':')).encode('utf-8')
        
        # 4字节对齐填充
        padding = 4 - (len(header_json) % 4)
        if padding == 4:
            padding = 0
        header_json += b'\0' * padding

        header_json_size = len(header_json)
        header_str_size = header_json_size + 4
        header_size = header_str_size + 4
        magic = 4

        with open(output_asar, 'wb') as f:
            f.write(struct.pack('<I', magic))
            f.write(struct.pack('<I', header_size))
            f.write(struct.pack('<I', header_str_size))
            f.write(struct.pack('<I', header_json_size))
            f.write(header_json)
            f.write(bytes(files_data))


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


def patch_dist_files(dist_dir: Path, lang: str, repo_root: Path):
    """修补解包后 dist 目录内的关键脚本"""
    res_dir = repo_root / "resources"
    
    # 1. 载入词典
    dict_file = res_dir / f"antigravity-{lang}.json"
    if not dict_file.is_file():
        dict_file = res_dir / "antigravity-zh-CN.json"
        
    with open(dict_file, 'r', encoding='utf-8') as f:
        lang_dict = json.load(f)

    with open(res_dir / "desktop-zh-CN.json", 'r', encoding='utf-8') as f:
        desktop_dict = json.load(f)

    with open(res_dir / "rules-zh-CN.json", 'r', encoding='utf-8') as f:
        rules_list = json.load(f)

    with open(res_dir / "runtime-zh.js", 'r', encoding='utf-8') as f:
        runtime_js_code = f.read()

    # 2. 修补 menu.js (应用主菜单)
    menu_file = dist_dir / "menu.js"
    if menu_file.is_file():
        content = menu_file.read_text(encoding='utf-8')
        for en, zh in desktop_dict.get("menu", {}).items():
            content = content.replace(f"'{en}'", f"'{zh}'")
            content = content.replace(f'"{en}"', f'"{zh}"')
        menu_file.write_text(content, encoding='utf-8')
        print("  [OK] 已修补原生菜单: dist/menu.js")

    # 3. 修补 tray.js (系统托盘)
    tray_file = dist_dir / "tray.js"
    if tray_file.is_file():
        content = tray_file.read_text(encoding='utf-8')
        content = content.replace("'No agents running'", "'无运行中的代理'")
        content = content.replace('"No agents running"', '"无运行中的代理"')
        content = content.replace("'Quit'", "'退出'")
        content = content.replace('"Quit"', '"退出"')
        content = content.replace("`Open ${electron_1.app.getName()}`", "`打开 ${electron_1.app.getName()}`")
        content = content.replace("' agent'", "' 个代理'")
        content = content.replace("' agents'", "' 个代理'")
        content = content.replace("' running'", "' 正在运行'")
        tray_file.write_text(content, encoding='utf-8')
        print("  [OK] 已修补系统托盘: dist/tray.js")

    # 4. 修补 updater.js (自动更新步骤文字)
    updater_file = dist_dir / "updater.js"
    if updater_file.is_file():
        content = updater_file.read_text(encoding='utf-8')
        content = content.replace('"Check for Updates"', '"检查更新"')
        content = content.replace('"Checking for Updates..."', '"正在检查更新..."')
        content = content.replace('"Downloading Update..."', '"正在下载更新..."')
        content = content.replace('"Restart to Update"', '"重启以更新"')
        updater_file.write_text(content, encoding='utf-8')
        print("  [OK] 已修补更新提示: dist/updater.js")

    # 5. 修补 preload.js (注入 DOM 翻译引擎)
    preload_file = dist_dir / "preload.js"
    if preload_file.is_file():
        content = preload_file.read_text(encoding='utf-8')
        if PATCH_MARKER not in content:
            injection = f"""
{PATCH_MARKER}
(function() {{
  try {{
    window.__AGY_ZH_LANG__ = {json.dumps(lang)};
    window.__AGY_ZH_DICT__ = {json.dumps(lang_dict, ensure_ascii=False)};
    window.__AGY_ZH_RULES__ = {json.dumps(rules_list, ensure_ascii=False)};
    {runtime_js_code}
  }} catch(e) {{
    console.error("[antigravity-zh-cn] Failed to bootstrap translation:", e);
  }}
}})();
"""
            preload_file.write_text(content + injection, encoding='utf-8')
            print("  [OK] 已向预加载环境注入 DOM 翻译引擎: dist/preload.js")


def apply_patch(install_dir: Path, lang: str = "zh-CN", repo_root: Path = None):
    """完整安装补丁流程"""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    asar_path = get_asar_path(install_dir)
    if not asar_path.is_file():
        raise FileNotFoundError(f"未找到 app.asar: {asar_path}")

    backup_path = asar_path.with_suffix('.asar.bak')
    
    # 1. 备份原版 asar（如果尚未存在备份）
    if not backup_path.exists():
        print(f"正在创建原版备份: {backup_path.name}...")
        shutil.copy2(asar_path, backup_path)
    else:
        print(f"发现已有原版备份: {backup_path.name}")

    # 2. 检查是否使用系统已有 npx asar 还是内置纯 Python 打包解包
    has_npx_asar = False
    try:
        res = subprocess.run(["npx", "asar", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if res.returncode == 0:
            has_npx_asar = True
    except Exception:
        has_npx_asar = False

    print(f"开始解包 app.asar ({'使用 npx asar' if has_npx_asar else '使用内置 Python asar 引擎'})...")
    with tempfile.TemporaryDirectory(prefix="antigravity_zh_") as temp_dir:
        temp_dir_path = Path(temp_dir)
        extract_dir = temp_dir_path / "app"

        # 解包始终基于原版备份解包，确保无论重打多少次补丁都不会脏污染
        source_asar = backup_path if backup_path.exists() else asar_path

        if has_npx_asar:
            subprocess.run(["npx", "asar", "extract", str(source_asar), str(extract_dir)], check=True, shell=True)
        else:
            AsarArchive.extract(source_asar, extract_dir)

        # 修补文件
        dist_dir = extract_dir / "dist"
        if not dist_dir.is_dir():
            raise RuntimeError(f"解包后的目录结构异常，缺少 dist 目录: {extract_dir}")

        patch_dist_files(dist_dir, lang, repo_root)

        # 打包回临时 asar
        temp_asar = temp_dir_path / "patched.asar"
        print("正在打包新版 app.asar...")
        if has_npx_asar:
            subprocess.run(["npx", "asar", "pack", str(extract_dir), str(temp_asar)], check=True, shell=True)
        else:
            AsarArchive.pack(extract_dir, temp_asar)

        # 原子化覆盖目标 app.asar
        print(f"写入汉化文件到: {asar_path}...")
        shutil.copy2(temp_asar, asar_path)

    print("[OK] Antigravity 汉化补丁安装成功！")


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
