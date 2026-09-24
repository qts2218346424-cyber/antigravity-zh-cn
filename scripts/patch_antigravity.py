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
PET_HOOK_START = "/* __ANTIGRAVITY_PET_AUTOSTART_BEGIN__ */"
PET_HOOK_END = "/* __ANTIGRAVITY_PET_AUTOSTART_END__ */"
ASAR_INTEGRITY_BLOCK_SIZE = 4 * 1024 * 1024


def generate_pet_autostart_hook() -> str:
    """生成桌面宠物随 Antigravity 启动的守护 Hook 代码"""
    return f"""{PET_HOOK_START}
// 自动随 Antigravity 启动桌面宠物守护进程（可随时在宠物设置、托盘或通过卸载菜单关闭）
(function() {{
  try {{
    const _fs = require('fs');
    const _path = require('path');
    const _os = require('os');
    const _cp = require('child_process');
    const _cfgPath = _path.join(_os.homedir(), '.gemini', 'pet_config.json');
    if (!_fs.existsSync(_cfgPath)) return;
    const _cfg = JSON.parse(_fs.readFileSync(_cfgPath, 'utf8'));
    // 严格白名单校验：仅在显式为 true 时自启动
    if (!_cfg || _cfg.auto_start_with_antigravity !== true) return;
    const _pyScript = _cfg.pet_script_path;
    if (!_pyScript || !_fs.existsSync(_pyScript)) return;

    let _pythonBin = process.platform === 'win32' ? 'pythonw' : 'python3';
    if (_cfg.python_bin_path && _fs.existsSync(_cfg.python_bin_path)) {{
      _pythonBin = _cfg.python_bin_path;
    }}
    const _child = _cp.spawn(_pythonBin, [_pyScript], {{
      detached: true,
      stdio: 'ignore',
      windowsHide: true
    }});
    _child.unref();
  }} catch (_e) {{}}
}})();
{PET_HOOK_END}"""


def stop_antigravity_processes():
    """终止正在运行的 Antigravity 宿主进程以防 ASAR 文件占用"""
    if sys.platform == "win32":
        try:
            import subprocess
            cmd = (
                "Get-Process -Name 'Antigravity', 'language_server' -ErrorAction SilentlyContinue | "
                "Stop-Process -Force -ErrorAction SilentlyContinue"
            )
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=5)
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            import subprocess
            subprocess.run(["pkill", "-f", "Antigravity"], capture_output=True, timeout=5)
        except Exception:
            pass
    else:
        try:
            import subprocess
            subprocess.run(["pkill", "-f", "antigravity"], capture_output=True, timeout=5)
        except Exception:
            pass


def stop_running_pet_processes():
    """终止正在运行的桌面宠物进程（按命令行精准匹配，排除自身 PID）"""
    current_pid = os.getpid()
    if sys.platform == "win32":
        try:
            import subprocess
            cmd = (
                f"Get-CimInstance Win32_Process | "
                f"Where-Object {{ $_.CommandLine -like '*run_pet.py*' -and $_.ProcessId -ne {current_pid} }} | "
                f"ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}"
            )
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=8)
            print("  [OK] 桌面宠物后台进程已关闭。")
        except Exception as e:
            print(f"  [!] 关闭桌面宠物进程提示: {e}")
    else:
        try:
            import subprocess
            subprocess.run(["pkill", "-f", "run_pet.py"], capture_output=True, timeout=5)
            print("  [OK] 桌面宠物后台进程已关闭。")
        except Exception as e:
            print(f"  [!] 关闭桌面宠物进程提示: {e}")


def remove_pet_shortcuts():
    """清理桌面、开始菜单及 Startup 启动目录下的桌面宠物快捷方式"""
    candidates = []
    # 桌面快捷方式
    user_desktop = Path.home() / "Desktop"
    candidates.append(user_desktop / "Antigravity 桌面宠物.lnk")
    candidates.append(user_desktop / "Antigravity 桌面小宠物.lnk")
    pub = os.environ.get("PUBLIC", r"C:\Users\Public")
    public_desktop = Path(pub) / "Desktop"
    candidates.append(public_desktop / "Antigravity 桌面宠物.lnk")
    candidates.append(public_desktop / "Antigravity 桌面小宠物.lnk")

    # Startup 启动目录与开始菜单
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        candidates.append(startup_dir / "Antigravity 桌面宠物.lnk")
        candidates.append(startup_dir / "Antigravity 桌面小宠物.lnk")
        start_menu_prog = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        candidates.append(start_menu_prog / "Antigravity 桌面宠物.lnk")

    removed = 0
    for lnk in candidates:
        if lnk.is_file():
            try:
                lnk.unlink(missing_ok=True)
                removed += 1
            except Exception:
                pass
    if removed > 0:
        print(f"  [OK] 已清理 {removed} 个快捷方式 (含桌面/开始菜单/Startup)。")
    else:
        print("  [i] 未发现快捷方式残留。")



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


def apply_patch(install_dir: Path, lang: str = "zh-CN", repo_root: Path = None, with_pet: bool = False):
    """
    完整安装补丁流程：
    采用原位无损修改技术，精准替换 menu.js、tray.js、updater.js 和 preload.js。
    支持可选安装灵动桌面宠物自启动 Hook (with_pet)。
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

    # 记录桌宠脚本路径与默认自启配置（仅在启用桌面宠物模式时注入）
    if with_pet:
        pet_script_file = repo_root / "pet" / "run_pet.py"
        if pet_script_file.is_file():
            try:
                config_dir = Path.home() / ".gemini"
                config_dir.mkdir(parents=True, exist_ok=True)
                cfg_path = config_dir / "pet_config.json"
                cfg_data = {}
                if cfg_path.is_file():
                    try:
                        cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
                    except Exception:
                        cfg_data = {}
                cfg_data["pet_script_path"] = str(pet_script_file.resolve())
                cfg_data["auto_start_with_antigravity"] = True
                python_bin = sys.executable
                if sys.platform == "win32":
                    py_dir = Path(sys.executable).parent
                    pythonw_cand = py_dir / "pythonw.exe"
                    if pythonw_cand.is_file():
                        python_bin = str(pythonw_cand.resolve())
                cfg_data["python_bin_path"] = python_bin
                cfg_path.write_text(json.dumps(cfg_data, indent=2, ensure_ascii=False), encoding="utf-8")
                print("  [OK] 灵动桌面小宠物自启配置已记录 (~/.gemini/pet_config.json)")
            except Exception as e:
                print(f"  [!] 记录桌宠自启配置失败 (非致命): {e}")

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
            menu_content = menu_content.replace("'Connect to WSL'", "'连接到 WSL'")
            menu_content = menu_content.replace('"Connect to WSL"', '"连接到 WSL"')
            menu_content = menu_content.replace("'Reopen Locally'", "'在本地重新打开'")
            menu_content = menu_content.replace('"Reopen Locally"', '"在本地重新打开"')
            asar_data = replace_asar_file_content(asar_data, "dist/menu.js", menu_content.encode("utf-8"))
            print("  [OK] 原生菜单与 WSL 项 (dist/menu.js) 汉化与调试支持修补完成")
    except Exception as e:
        print(f"  [!] 忽略非致命项 dist/menu.js: {e}")

    # (2) 修补 dist/tray.js (彻底重构智能体运行状态，根除 2 个代理s 正在运行 拼接 bug)
    try:
        tray_content = read_asar_file_content(asar_data, "dist/tray.js").decode("utf-8")
        tray_dict = desktop_dict.get("tray", {})
        for en, zh in tray_dict.items():
            tray_content = tray_content.replace(f"'{en}'", f"'{zh}'")
            tray_content = tray_content.replace(f'"{en}"', f'"{zh}"')
        tray_content = tray_content.replace("`Open ${electron_1.app.getName()}`", "`打开 ${electron_1.app.getName()}`")
        tray_content = tray_content.replace("'Connect to WSL'", "'连接到 WSL'")
        tray_content = tray_content.replace('"Connect to WSL"', '"连接到 WSL"')
        # 精准重构 updateTrayAgentCount 动态拼接函数，彻底消除英文复数 s 残留
        import re
        tray_content = re.sub(
            r"countItem\.label\s*=\s*\(count\s*>\s*0\s*\?\s*`\$\{count\}`\s*:\s*'No'\)\s*\+\s*' agent'\s*\+\s*\(count\s*===\s*1\s*\?\s*''\s*:\s*'s'\)\s*\+\s*' running';",
            r"countItem.label = count > 0 ? `${count} 个智能体正在运行` : '无正在运行的智能体';",
            tray_content
        )
        asar_data = replace_asar_file_content(asar_data, "dist/tray.js", tray_content.encode("utf-8"))
        print("  [OK] 系统托盘动态状态 (dist/tray.js) 彻底重构修补完成")
    except Exception as e:
        print(f"  [!] 忽略非致命项 dist/tray.js: {e}")

    # (2.1) 修补 dist/main.js (原生托盘上下文菜单项模板与退出确认对话框)
    try:
        main_content = read_asar_file_content(asar_data, "dist/main.js").decode("utf-8")
        main_content = main_content.replace("label: 'No agents running'", "label: '无正在运行的智能体'")
        main_content = main_content.replace('label: "No agents running"', 'label: "无正在运行的智能体"')
        main_content = main_content.replace("`Open ${electron_1.app.getName()}`", "`打开 ${electron_1.app.getName()}`")
        main_content = main_content.replace("label: 'Quit'", "label: '退出'")
        main_content = main_content.replace('label: "Quit"', 'label: "退出"')
        main_content = main_content.replace("buttons: ['Cancel', 'Quit']", "buttons: ['取消', '退出']")
        main_content = main_content.replace("title: 'Confirm Quit'", "title: '确认退出'")
        main_content = main_content.replace("'Connect to WSL'", "'连接到 WSL'")
        asar_data = replace_asar_file_content(asar_data, "dist/main.js", main_content.encode("utf-8"))
        print("  [OK] 主进程托盘模板与系统对话框 (dist/main.js) 汉化修补完成")
    except Exception as e:
        print(f"  [!] 忽略非致命项 dist/main.js: {e}")

    # (3) 修补 dist/updater.js
    try:
        updater_content = read_asar_file_content(asar_data, "dist/updater.js").decode("utf-8")
        updater_content = updater_content.replace('"Check for Updates"', '"检查更新"')
        updater_content = updater_content.replace('"Checking for Updates..."', '"正在检查更新..."')
        updater_content = updater_content.replace('"Downloading Update..."', '"正在下载更新..."')
        updater_content = updater_content.replace('"Restart to Update"', '"重启以更新"')
        # 禁止后台静默自动下载与退出时静默覆盖安装，防止破坏汉化
        updater_content = updater_content.replace(
            "electron_updater_1.autoUpdater.autoDownload = true;",
            "electron_updater_1.autoUpdater.autoDownload = false;"
        )
        updater_content = updater_content.replace(
            "electron_updater_1.autoUpdater.autoInstallOnAppQuit = electron_1.app.isPackaged;",
            "electron_updater_1.autoUpdater.autoInstallOnAppQuit = false;"
        )
        asar_data = replace_asar_file_content(asar_data, "dist/updater.js", updater_content.encode("utf-8"))
        print("  [OK] 更新提示与自动静默覆盖防护 (dist/updater.js) 修补完成")
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
            pet_hook_str = ("\n" + generate_pet_autostart_hook() + "\n") if with_pet else ""
            hook_code = f"""
/* __ANTIGRAVITY_ZH_CN_PATCHED__ */
const __AGY_ZH_CODE__ = {js_raw};
{pet_hook_str}"""
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
                if with_pet:
                    print("  [OK] 主世界注入通道与灵动桌面宠物自启组件挂载完成 (dist/utils.js)")
                else:
                    print("  [OK] 主世界注入通道挂载完成 (纯净汉化模式，未注入桌面宠物) (dist/utils.js)")
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
    # 默认自动禁止静默更新，防止重启后被官方静默覆盖
    try:
        toggle_auto_updates(install_dir, disable=True)
    except Exception as e:
        print(f"  [!] 自动禁用更新提示: {e}")


def uninstall_pet(install_dir: Path, stop_host: bool = False):
    """
    彻底卸载桌面宠物：
    1. 终止桌面宠物后台进程（若 stop_host=True 则可选终止 Antigravity 宿主）；
    2. 从 resources/app.asar (dist/utils.js) 中循环幂等剥离自启 Hook 代码（保留其他汉化逻辑）；
    3. 将 ~/.gemini/pet_config.json 中的 auto_start_with_antigravity 设置为 false；
    4. 删除桌面快捷方式与开机自启动项；
    5. 清理临时渲染沙盒缓存 (~/.gemini/pet_webview_data)。
    """
    print("============================================================")
    print("        正在彻底卸载与清理 Antigravity 灵动桌面宠物         ")
    print("============================================================")

    # 1. 终止桌宠进程（非单元测试临时目录且明确需要时才停止宿主，防止 IDE 闪退）
    print("[1/5] 正在停止桌面宠物后台进程...")
    stop_running_pet_processes()
    if stop_host:
        real_install_dir = find_antigravity_dir()
        if real_install_dir and real_install_dir.resolve() == install_dir.resolve():
            print("  正在安全停止 Antigravity 宿主进程以防文件锁定...")
            stop_antigravity_processes()

    # 2. 从 app.asar 循环幂等剥离自启 Hook
    print("[2/5] 正在检查并剥离 app.asar 中的桌面宠物自启 Hook...")
    asar_path = get_asar_path(install_dir)
    if asar_path.is_file():
        try:
            asar_data = bytearray(asar_path.read_bytes())
            try:
                utils_content = read_asar_file_content(asar_data, "dist/utils.js").decode("utf-8")
                cleaned_content = utils_content
                import re

                # 循环剥离所有成对标记块（防多次叠加注入）
                pattern_paired = re.compile(re.escape(PET_HOOK_START) + r".*?" + re.escape(PET_HOOK_END) + r"\n?", re.DOTALL)
                while PET_HOOK_START in cleaned_content and PET_HOOK_END in cleaned_content:
                    cleaned_content = pattern_paired.sub("", cleaned_content)

                # 兜底清理孤立残片
                if PET_HOOK_START in cleaned_content:
                    pattern_orphan = re.compile(re.escape(PET_HOOK_START) + r".*?(?=\n\S|\Z)", re.DOTALL)
                    cleaned_content = pattern_orphan.sub("", cleaned_content)

                # 剥离旧版可能存在的旧特征块（循环）
                old_marker = "// 自动随 Antigravity 启动桌面宠物守护进程（可随时在宠物设置或托盘关闭）"
                while old_marker in cleaned_content:
                    pattern_old = re.compile(re.escape(old_marker) + r"\s*\(function\(\)\s*\{[\s\S]*?\}\)\(\);\n?", re.DOTALL)
                    cleaned_content = pattern_old.sub("", cleaned_content)

                if cleaned_content != utils_content:
                    asar_data = replace_asar_file_content(asar_data, "dist/utils.js", cleaned_content.encode("utf-8"))
                    temp_dest = asar_path.with_suffix('.asar.tmp')
                    temp_dest.write_bytes(asar_data)
                    shutil.move(str(temp_dest), str(asar_path))
                    print("  [OK] 已成功从 dist/utils.js 中移除桌面宠物自启 Hook！")
                else:
                    print("  [i] 当前 app.asar 中未发现桌面宠物自启 Hook，无需清理。")
            except Exception as e:
                print(f"  [!] 检查/修改 dist/utils.js 时发生提示: {e}")
        except Exception as e:
            print(f"  [!] 读取 app.asar 异常: {e}")
    else:
        print(f"  [!] 未找到 app.asar: {asar_path}")

    # 3. 更新配置
    print("[3/5] 正在重置桌宠配置文件...")
    try:
        cfg_path = Path.home() / ".gemini" / "pet_config.json"
        if cfg_path.is_file():
            try:
                cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
            except Exception:
                cfg_data = {}
            cfg_data["auto_start_with_antigravity"] = False
            cfg_path.write_text(json.dumps(cfg_data, indent=2, ensure_ascii=False), encoding="utf-8")
            print("  [OK] 已将 pet_config.json 中的自启动开关永久关闭。")
    except Exception as e:
        print(f"  [!] 更新 pet_config.json 提示: {e}")

    # 4. 删除快捷方式
    print("[4/5] 正在清理桌面快捷方式...")
    remove_pet_shortcuts()

    # 5. 清理临时缓存
    print("[5/5] 正在清理桌面宠物临时缓存目录...")
    try:
        cache_dir = Path.home() / ".gemini" / "pet_webview_data"
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir, ignore_errors=True)
            print("  [OK] 临时缓存目录已清除 (~/.gemini/pet_webview_data)。")
        else:
            print("  [i] 未发现临时缓存目录。")
    except Exception as e:
        print(f"  [!] 清理临时缓存提示: {e}")

    print("\n[OK] 桌面宠物已彻底卸载并清理完成！当前 Antigravity 运行在纯净汉化模式下。")


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

        # 清除本地缓存中的 pending 安装包，彻底杜绝重启静默安装
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if local_app_data:
            cache_dir = Path(local_app_data) / "antigravity-updater"
            if cache_dir.is_dir():
                try:
                    shutil.rmtree(cache_dir, ignore_errors=True)
                    print("[OK] 已清空后台静默更新缓存 (antigravity-updater)。")
                except Exception as e:
                    print(f"⚠ 清理更新缓存失败: {e}")
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
    parser.add_argument("action", choices=["install", "restore", "disable-updates", "enable-updates", "uninstall-pet"],
                        nargs="?", default="install", help="执行操作 (默认: install)")
    parser.add_argument("--lang", choices=["zh-CN", "zh-TW", "zh-HK"], default="zh-CN",
                        help="目标语言 (默认: zh-CN)")
    parser.add_argument("--dir", help="Antigravity 安装目录路径 (默认自动检测)")

    pet_group = parser.add_mutually_exclusive_group()
    pet_group.add_argument("--with-pet", dest="with_pet", action="store_true", default=False,
                           help="同时安装并挂载灵动桌面小宠物 (汉化 + 宠物)")
    pet_group.add_argument("--no-pet", dest="with_pet", action="store_false",
                           help="安装纯净汉化补丁，不包含任何桌面宠物自启组件 (默认)")

    args = parser.parse_args()

    install_dir = Path(args.dir).resolve() if args.dir else get_default_install_path()
    if not install_dir or not install_dir.is_dir():
        print("错误: 未检测到 Antigravity 安装目录，请通过 --dir 参数手动指定。", file=sys.stderr)
        sys.exit(1)

    print(f"目标目录: {install_dir}")
    repo_root = Path(__file__).resolve().parent.parent

    if args.action == "install":
        apply_patch(install_dir, args.lang, repo_root, with_pet=args.with_pet)
    elif args.action == "uninstall-pet":
        uninstall_pet(install_dir, stop_host=True)
    elif args.action == "restore":
        restore_backup(install_dir)
    elif args.action == "disable-updates":
        toggle_auto_updates(install_dir, disable=True)
    elif args.action == "enable-updates":
        toggle_auto_updates(install_dir, disable=False)


if __name__ == "__main__":
    main()
