# -*- coding: utf-8 -*-
"""
pytest 全局隔离：把材质包/自动重注入的用户配置目录与启动动画角色配置
重定向到临时目录，避免测试写入真实的 %APPDATA% / ~/.config 或仓库内文件。
（在任何测试模块导入 scripts/* 之前执行）
"""
import os
import sys
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="agzh-tests-"))
os.environ.setdefault("AGZH_CONFIG_DIR", str(_TMP / "config"))
os.environ.setdefault("AGZH_SPLASH_CONFIG", str(_TMP / "splash_config.json"))

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
