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


def _is_running_inside_antigravity() -> bool:
    """检测当前 Python 进程是否由 Antigravity 宿主进程启动（即从 Antigravity 对话内部调用）。
    通过沿进程树向上遍历祖先进程，判断是否存在名为 Antigravity 的父进程。"""
    if sys.platform != "win32":
        # macOS/Linux: 检查进程树
        try:
            import subprocess
            pid = os.getpid()
            while pid and pid > 1:
                result = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "ppid=,comm="],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode != 0:
                    break
                parts = result.stdout.strip().split(None, 1)
                if len(parts) < 2:
                    break
                ppid, comm = int(parts[0]), parts[1].lower()
                if "antigravity" in comm:
                    return True
                pid = ppid
        except Exception:
            pass
        return False
    # Windows: 通过 WMI 查询进程父子链
    try:
        import subprocess
        # 使用 PowerShell 沿进程树向上查找 Antigravity
        ps_script = (
            f"$pid = {os.getpid()}; "
            "while ($pid -and $pid -ne 0) { "
            "  try { $p = Get-CimInstance Win32_Process -Filter \"ProcessId=$pid\" -ErrorAction Stop; "
            "    if ($p.Name -match 'Antigravity') { Write-Output 'FOUND'; exit 0 }; "
            "    $pid = $p.ParentProcessId "
            "  } catch { break } "
            "}; Write-Output 'NOTFOUND'"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=5
        )
        return "FOUND" in result.stdout
    except Exception:
        return False


def stop_antigravity_processes():
    """终止正在运行的 Antigravity 宿主进程以防 ASAR 文件占用。
    重要：如果检测到当前脚本是从 Antigravity 内部（对话/命令行）调用的，
    则跳过进程终止，避免 Antigravity 在运行汉化任务时"自杀"关闭。"""
    if _is_running_inside_antigravity():
        print("  [ℹ] 检测到当前正在 Antigravity 内部运行，跳过进程终止以避免程序关闭。")
        print("  [ℹ] 提示：补丁将在下次重启 Antigravity 时生效。如果写入失败，请手动关闭后重试。")
        return

    if sys.platform == "win32":
        try:
            import subprocess
            cmd = (
                "Get-Process -Name 'Antigravity', 'language_server' -ErrorAction SilentlyContinue | "
                "Stop-Process -Force -ErrorAction SilentlyContinue"
            )
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=5)
            import time; time.sleep(1)  # 等待文件锁释放
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            import subprocess
            subprocess.run(["pkill", "-f", "Antigravity"], capture_output=True, timeout=5)
            import time; time.sleep(1)
        except Exception:
            pass
    else:
        try:
            import subprocess
            subprocess.run(["pkill", "-f", "antigravity"], capture_output=True, timeout=5)
            import time; time.sleep(1)
        except Exception:
            pass



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

    # 1. 备份原版 asar（如果当前 asar 为全新官方未修补版本，或尚未存在备份）
    asar_bytes = asar_path.read_bytes()
    is_current_unpatched = PATCH_MARKER.encode("utf-8") not in asar_bytes
    if is_current_unpatched:
        print(f"[1/4] 检测到全新官方未修补版本，正在创建/更新原版备份: {backup_path.name}...")
        shutil.copy2(asar_path, backup_path)
    elif not backup_path.exists():
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

        # 注入主进程启动期技能说明全自动汉化自检钩子 (In-App Auto Skill Localizer)
        from localize_skills import SKILL_TRANSLATION_MAP
        skills_map_json = json.dumps(SKILL_TRANSLATION_MAP, ensure_ascii=False)
        skill_hook = f"""
/* __ANTIGRAVITY_SKILL_AUTO_LOCALIZER__ */
(function() {{
  try {{
    const fs = require('fs');
    const path = require('path');
    const os = require('os');
    const home = os.homedir();
    const roots = [
      path.join(home, '.gemini', 'skills'),
      path.join(home, '.gemini', 'config', 'plugins'),
      path.join(home, '.gemini', 'antigravity', 'builtin', 'skills')
    ];
    const skillMap = {skills_map_json};
    const scanDir = (dir, depth = 0) => {{
      if (depth > 4) return;
      try {{
        const entries = fs.readdirSync(dir, {{ withFileTypes: true }});
        for (const ent of entries) {{
          const fullPath = path.join(dir, ent.name);
          if (ent.isDirectory()) {{
            scanDir(fullPath, depth + 1);
          }} else if (ent.name === 'SKILL.md') {{
            const skillName = path.basename(dir);
            if (skillMap[skillName]) {{
              const targetZh = skillMap[skillName];
              const content = fs.readFileSync(fullPath, 'utf8');
              const match = content.match(/^description:\\s*(.*?)$/m);
              if (match && !/[\\u4e00-\\u9fa5]/.test(match[1])) {{
                const newContent = content.replace(match[0], 'description: "' + targetZh.replace(/"/g, '\\\\"') + '"');
                fs.writeFileSync(fullPath, newContent, 'utf8');
              }}
            }}
          }}
        }}
      }} catch (_) {{}}
    }};
    setTimeout(() => {{
      roots.forEach(r => {{ if (fs.existsSync(r)) scanDir(r); }});
    }}, 1000);
  }} catch (_) {{}}
}})();
"""
        if "/* __ANTIGRAVITY_SKILL_AUTO_LOCALIZER__ */" not in main_content:
            main_content = skill_hook + "\n" + main_content

        asar_data = replace_asar_file_content(asar_data, "dist/main.js", main_content.encode("utf-8"))
        print("  [OK] 主进程托盘模板与系统对话框及技能自检 (dist/main.js) 汉化修补完成")
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

    # (4) 修补 dist/preload.js (预加载阶段 DOM 翻译引擎 + 原生通知包装)
    try:
        preload_content = read_asar_file_content(asar_data, "dist/preload.js").decode("utf-8")
        if PATCH_MARKER not in preload_content:
            notif_preload_patch = """
try {
  const origNotifSend = notificationAPI.send;
  notificationAPI.send = function(options) {
    try {
      if (options) {
        const tr = (typeof window !== 'undefined' && window.__AGY_ZH_DICT__) ? window.__AGY_ZH_DICT__ : {};
        if (options.title && tr[options.title]) options.title = tr[options.title];
        if (options.body && tr[options.body]) options.body = tr[options.body];
      }
    } catch (_) {}
    return origNotifSend.call(this, options);
  };
} catch (_) {}
"""
            if "electron_1.contextBridge.exposeInMainWorld('nativeNotifications', notificationAPI);" in preload_content:
                preload_content = preload_content.replace(
                    "electron_1.contextBridge.exposeInMainWorld('nativeNotifications', notificationAPI);",
                    f"{notif_preload_patch}\nelectron_1.contextBridge.exposeInMainWorld('nativeNotifications', notificationAPI);"
                )
            preload_content += f"\n{PATCH_MARKER}\n{injection_code}\n"
            asar_data = replace_asar_file_content(asar_data, "dist/preload.js", preload_content.encode("utf-8"))
            print("  [OK] DOM 翻译引擎与原生通知预加载通道注入完成 (dist/preload.js)")
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
            utils_content = utils_content.replace(
                "contextIsolation: true,",
                "contextIsolation: true,\n            allFrames: true,"
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
    win.webContents.on('did-attach-webview', (_event, webContents) => {
        webContents.executeJavaScript(__AGY_ZH_CODE__).catch(() => {});
        webContents.on('dom-ready', () => {
            webContents.executeJavaScript(__AGY_ZH_CODE__).catch(() => {});
        });
    });
    void win.loadURL(url);
"""
            if target_str in utils_content:
                utils_content = utils_content.replace(target_str, replacement_str, 1)
                asar_data = replace_asar_file_content(asar_data, "dist/utils.js", utils_content.encode("utf-8"))
                print("  [OK] 主世界注入通道挂载完成 (dist/utils.js)")
            else:
                print("  [!] 未在 dist/utils.js 中找到 void win.loadURL(url); 锚点")
    except Exception as e:
        print(f"  [!] 主世界注入通道修补失败: {e}")

    # (5.1) 修补 dist/ipcHandlers.js (原生桌面通知全汉化拦截)
    try:
        ipc_content = read_asar_file_content(asar_data, "dist/ipcHandlers.js").decode("utf-8")
        if PATCH_MARKER not in ipc_content:
            notif_dict_json = json.dumps(lang_dict, ensure_ascii=False)
            ipc_header_patch = f"""
{PATCH_MARKER}
const __AGY_IPC_NOTIF_DICT__ = {notif_dict_json};
function __agyTranslateNotif(text) {{
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (__AGY_IPC_NOTIF_DICT__[trimmed]) return __AGY_IPC_NOTIF_DICT__[trimmed];
    const lower = trimmed.toLowerCase();
    for (const k in __AGY_IPC_NOTIF_DICT__) {{
        if (k.toLowerCase() === lower) return __AGY_IPC_NOTIF_DICT__[k];
    }}
    return text;
}}
"""
            ipc_content = ipc_header_patch + "\n" + ipc_content
            old_notif_target = """        const notification = new electron_1.Notification({
            title: options.title,
            body: options.body,
            silent: options.silent ?? false,
        });"""
            new_notif_target = """        const notification = new electron_1.Notification({
            title: __agyTranslateNotif(options.title),
            body: __agyTranslateNotif(options.body),
            silent: options.silent ?? false,
        });"""
            if old_notif_target in ipc_content:
                ipc_content = ipc_content.replace(old_notif_target, new_notif_target, 1)
                asar_data = replace_asar_file_content(asar_data, "dist/ipcHandlers.js", ipc_content.encode("utf-8"))
                print("  [OK] 原生桌面系统通知 (dist/ipcHandlers.js) 汉化拦截通道挂载完成")
            else:
                print("  [!] 未在 dist/ipcHandlers.js 中匹配到 notification:send 锚点")
    except Exception as e:
        print(f"  [!] 忽略非致命项 dist/ipcHandlers.js: {e}")

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
    stop_antigravity_processes()
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
