#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity 界面词条自动抽取工具 (extract_strings.py)
面向开发者与维护者：
当 Antigravity 发布新版本时，运行本脚本可自动扫描运行中的 Antigravity 或本地 bundle，
抽取所有待翻译的新词条并与现有词典比对，生成 untranslated.json 供补充翻译。
"""

import os
import re
import ssl
import sys
import json
import urllib.request
from pathlib import Path

def extract_from_text(js_content: str) -> set[str]:
    """从 JavaScript / React bundle 中提取潜在的 UI 界面字符串"""
    patterns = [
        r'>([A-Z][A-Za-z0-9\s,\.\?\!\'\-]{2,50})<',
        r'placeholder="([^"]{3,50})"',
        r'title="([^"]{3,50})"',
        r'aria-label="([^"]{3,50})"',
        r'label:\s*"([^"]{3,50})"',
    ]
    
    extracted = set()
    for p in patterns:
        for m in re.finditer(p, js_content):
            val = m.group(1).strip()
            # 过滤明显是代码变量或 URL 的无效项
            if (len(val) >= 2 
                and not val.startswith('http') 
                and not val.startswith('var ') 
                and not val.startswith('const ')
                and not val.startswith('return ')
                and not val.endswith('.js')
                and not val.endswith('.css')):
                extracted.add(val)
                
    return extracted

def fetch_from_running_instance() -> str | None:
    """尝试从当前运行中的 Antigravity 语言服务器拉取 main.js"""
    # 查找本地开放的 HTTPS 端口
    import subprocess
    try:
        if sys.platform == 'win32':
            cmd = 'Get-NetTCPConnection -State Listen | Where-Object { $_.LocalAddress -eq "127.0.0.1" } | Select-Object -ExpandProperty LocalPort'
            ports = subprocess.check_output(["powershell", "-Command", cmd], text=True).strip().splitlines()
        else:
            ports = []
    except Exception:
        ports = []

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for p in ports:
        port = p.strip()
        if not port:
            continue
        url = f"https://127.0.0.1:{port}/main.js"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=1.5) as resp:
                if resp.status == 200:
                    data = resp.read().decode('utf-8', errors='ignore')
                    if "antigravity" in data.lower() or "workspace" in data.lower():
                        print(f"✔ 成功从运行中的服务获取前端 Bundle: {url}")
                        return data
        except Exception:
            continue

    return None

# UTF-8 控制台编码兼容
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def main():
    repo_root = Path(__file__).resolve().parent.parent
    resources_dir = repo_root / "resources"
    cn_dict_path = resources_dir / "antigravity-zh-CN.json"

    existing_dict = {}
    if cn_dict_path.is_file():
        with open(cn_dict_path, 'r', encoding='utf-8') as f:
            existing_dict = json.load(f)

    content = None
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        print(f"正在从本地文件读取 Bundle: {sys.argv[1]}")
        with open(sys.argv[1], 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    else:
        print("正在尝试从运行中的 Antigravity 实例扫描前端 Bundle...")
        content = fetch_from_running_instance()

    if not content:
        print("[!] 未检测到运行中的 Antigravity 实例，也未指定 bundle 文件。")
        print("用法: python extract_strings.py [bundle_path]")
        return

    candidates = extract_from_text(content)
    print(f"扫描完毕，共发现 {len(candidates)} 个候选词条。")

    # 找出尚未在词典中的新词条
    untranslated = {c: "" for c in sorted(candidates) if c not in existing_dict}
    print(f"比对现有词典，发现未收录词条: {len(untranslated)} 个。")

    output_path = resources_dir / "untranslated.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(untranslated, f, ensure_ascii=False, indent=2)

    print(f"[OK] 未翻译词条已导出至: {output_path}")

if __name__ == "__main__":
    main()
