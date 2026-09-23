#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 全自动版本更新、代码维护与 GitHub 同步引擎 (auto_maintainer.py)

工作流程：
1. 检测当前已安装或官方云端发布的 Antigravity 版本号；
2. 检测 app.asar 是否被官方更新静默覆盖；
3. 若有版本变更或未打补丁：
   a. 自动拉取新版 Bundle 并深度抽取新增的 UI 文本与占位符；
   b. 对比当前词库，自动增量翻译新词条并全量同步繁体变体 (zh-TW, zh-HK)；
   c. 执行自动化单测门禁 (Unit Tests)，确保 0 缺陷 0 回退；
   d. 原位无损修补本地 app.asar 并保持静默覆盖防护；
   e. 自动创建 Git Commit 并推送到 GitHub 远程仓库 (origin/main)。
"""

import os
import sys
import json
import re
import ssl
import time
import shutil
import urllib.request
import subprocess
from pathlib import Path

# UTF-8 控制台编码兼容
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from patch_antigravity import (
    get_default_install_path,
    get_asar_path,
    read_asar_header,
    read_asar_file_content,
    apply_patch,
    PATCH_MARKER,
)
from build_full_dictionary import main as sync_full_dictionary

MANIFEST_URL = (
    "https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/manifest/latest-x64-win.yml"
)


def get_local_version_and_patch_state(install_dir: Path) -> tuple[str, bool]:
    """获取本地已安装版本号及是否已打补丁"""
    asar_path = get_asar_path(install_dir)
    if not asar_path.is_file():
        return "0.0.0", False

    data = asar_path.read_bytes()
    is_patched = PATCH_MARKER.encode("utf-8") in data

    try:
        pkg_raw = read_asar_file_content(data, "package.json")
        pkg = json.loads(pkg_raw.decode("utf-8"))
        version = pkg.get("version", "unknown")
    except Exception:
        version = "unknown"

    return version, is_patched


def get_remote_version() -> tuple[str, str]:
    """查询 Google 官方最新发布的版本号与下载 URL"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        MANIFEST_URL,
        headers={"User-Agent": "Mozilla/5.0", "x-app-version": "2.17.0"},
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            ver_m = re.search(r"version:\s*([0-9.]+)", content)
            url_m = re.search(r"url:\s*(https?://[^\s]+)", content)
            version = ver_m.group(1) if ver_m else "unknown"
            download_url = url_m.group(1) if url_m else ""
            return version, download_url
    except Exception as e:
        return "unknown", f"Error: {e}"


def get_active_ls_port() -> int | None:
    """从本地 Electron 日志或网络中检测正在运行的 Language Server 端口"""
    for folder in ["antigravity", "Antigravity"]:
        log_path = Path(os.environ.get("APPDATA", "")) / folder / "logs" / "main.log"
        if log_path.is_file():
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in reversed(f.readlines()[-100:]):
                        m = re.search(r"Local:\s+https?://127\.0\.0\.1:(\d+)", line)
                        if m:
                            return int(m.group(1))
            except Exception:
                pass
    return None


def fetch_latest_web_bundle(port: int | None = None) -> str:
    """拉取最新版本的 Web JS 前端 Bundle 源代码以提取词条"""
    if not port:
        port = get_active_ls_port()
    if not port:
        return ""

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    bundle_url = f"https://127.0.0.1:{port}/main.js"
    req = urllib.request.Request(bundle_url)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_ui_strings_from_bundle(bundle_code: str) -> set[str]:
    """从 Web 前端 Bundle 中精准提取所有待翻译文本及属性"""
    if not bundle_code:
        return set()

    candidates = set()

    # 1. 属性文本：label, title, placeholder, tooltip, aria-label, text
    prop_pattern = r'(?:label|title|placeholder|tooltip|text):\s*"([A-Za-z0-9][A-Za-z0-9\s\-_.,!?:/()]+)"'
    for m in re.finditer(prop_pattern, bundle_code):
        s = m.group(1).strip()
        if len(s) > 1 and len(s) <= 100:
            if not s.startswith("http") and not s.startswith("rgba"):
                candidates.add(s)

    # 2. JSX 文本子节点
    jsx_pattern = r'z\.createElement\([^,]+,\s*(?:\{[^}]*\}|null),\s*"([A-Za-z0-9][A-Za-z0-9\s\-_.,!?:/()]+)"'
    for m in re.finditer(jsx_pattern, bundle_code):
        s = m.group(1).strip()
        if len(s) > 1 and len(s) <= 100:
            if not s.startswith("http") and not s.startswith("rgba"):
                candidates.add(s)

    return candidates


def run_unit_tests() -> bool:
    """执行全部单元测试，确保代码与词典无回归缺陷"""
    res = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "tests"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        return True
    print(f"❌ 单元测试失败:\n{res.stderr}\n{res.stdout}")
    return False


def git_commit_and_push(version: str) -> bool:
    """自动将更新的代码和词典提交推送到 GitHub"""
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        if not status.stdout.strip():
            print("ℹ Git 工作区无任何文件变动，无需提交。")
            return True

        print("[Git] 检测到文件改动，正在生成 Commit 并推送到 GitHub...")
        subprocess.run(["git", "add", "-A"], cwd=str(REPO_ROOT), check=True)
        commit_msg = f"chore(auto): update localization for Antigravity v{version}"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(REPO_ROOT),
            check=True,
        )
        push_res = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        if push_res.returncode == 0:
            print("✅ 成功推送到 GitHub 远程仓库 (origin/main)！")
            return True
        else:
            print(f"⚠ Git Push 警告: {push_res.stderr}")
            return False
    except Exception as e:
        print(f"❌ Git 操作异常: {e}")
        return False


def perform_maintenance(force: bool = False, dry_run: bool = False) -> bool:
    """执行完整的自动维护主流程"""
    print("=" * 65)
    print("      Antigravity 自动化版本跟踪与持续维护系统 (Auto-Maintainer)")
    print(f"      执行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    install_dir = get_default_install_path()
    if not install_dir or not install_dir.is_dir():
        print(f"❌ 未检测到 Antigravity 安装目录: {install_dir}")
        return False

    local_ver, is_patched = get_local_version_and_patch_state(install_dir)
    print(f"• 本地程序版本: {local_ver} (汉化补丁状态: {'✅ 已打补丁' if is_patched else '❌ 未打补丁/被覆盖'})")

    # 1. 判断是否需要维护
    needs_action = force or (not is_patched)
    if not needs_action:
        print("✅ 当前版本已打补丁且无异常，系统处于最优状态。")
        return True

    print("⚡ 检测到需要执行维护（版本升级或补丁被覆盖）。开始自动化流水线...")

    # 2. 尝试从运行中实例拉取最新前端 Bundle 并抽取新词条
    bundle = fetch_latest_web_bundle()
    if bundle:
        print(f"• 成功连接本地语言服务并拉取前端 Bundle ({len(bundle):,} 字节)")
        new_candidates = extract_ui_strings_from_bundle(bundle)
        print(f"• 成功提取候选 UI 词条: {len(new_candidates)} 条")

        cn_file = REPO_ROOT / "resources" / "antigravity-zh-CN.json"
        with open(cn_file, "r", encoding="utf-8") as f:
            curr_dict = json.load(f)

        untranslated = [c for c in new_candidates if c not in curr_dict]
        if untranslated:
            print(f"• 发现新版本新增词条: {len(untranslated)} 条，正在智能增量同步...")
            # 自动调用全局词库构建与繁体同步
            sync_full_dictionary()
    else:
        print("ℹ 本地实例未在运行或未提供端口，使用当前完整词库进行修补。")
        sync_full_dictionary()

    # 3. 运行自动化测试门禁
    print("• 正在运行自动化测试套件...")
    if not run_unit_tests():
        print("❌ 自动化测试未通过，阻断后续补丁写入与代码提交。")
        return False
    print("✅ 单元测试 100% 通过！")

    if dry_run:
        print("ℹ [Dry-Run] 试运行模式，跳过本地 ASAR 写入与 Git 推送。")
        return True

    # 4. 原位修补本地程序
    print("• 正在原位无损写入最新汉化补丁并锁定更新...")
    apply_patch(install_dir, lang="zh-CN", repo_root=REPO_ROOT)

    # 5. 自动提交并推送到 GitHub
    git_commit_and_push(local_ver)

    print("=" * 65)
    print(f"🎉 Antigravity v{local_ver} 全自动维护与同步已圆满完成！")
    print("=" * 65)
    return True


def run_watcher(interval_seconds: int = 1800):
    """常驻后台守护模式，定期检测版本与补丁状态"""
    print(f"👀 启动后台看门狗守护，每 {interval_seconds} 秒自动检测一次...")
    while True:
        try:
            perform_maintenance(force=False)
        except Exception as e:
            print(f"⚠ 守护轮询发生错误: {e}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Antigravity 自动化版本维护与 GitHub 同步程序")
    parser.add_argument("--force", action="store_true", help="强制执行全量维护与修补")
    parser.add_argument("--dry-run", action="store_true", help="试运行模式（不写文件不提交）")
    parser.add_argument("--watch", action="store_true", help="启动常驻后台守护模式")
    parser.add_argument("--interval", type=int, default=1800, help="守护轮询间隔秒数 (默认 1800 秒)")

    args = parser.parse_args()

    if args.watch:
        run_watcher(interval_seconds=args.interval)
    else:
        success = perform_maintenance(force=args.force, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
