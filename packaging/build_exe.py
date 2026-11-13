#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键打包一体化管理器为单文件可执行程序 (packaging/build_exe.py)

    python -m pip install -r packaging/requirements-app.txt
    python packaging/build_exe.py

产物位于 dist/：Windows 为 AntigravityZhCN.exe，macOS 为 AntigravityZhCN.app，Linux 为 AntigravityZhCN。
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    spec = ROOT / "packaging" / "agzh_app.spec"
    cmd = [sys.executable, "-m", "PyInstaller", str(spec), "--noconfirm", "--clean",
           "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build")]
    print(" ".join(cmd))
    rc = subprocess.call(cmd, cwd=str(ROOT))
    if rc == 0:
        for p in sorted((ROOT / "dist").iterdir()):
            size = p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            print(f"  ✔ {p.name}  {size / 1024 / 1024:.1f} MB")
    return rc


if __name__ == "__main__":
    sys.exit(main())
