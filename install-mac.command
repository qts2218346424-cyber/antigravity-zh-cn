#!/usr/bin/env bash
# Antigravity macOS 汉化补丁一键运行脚本
set -e

cd "$(dirname "$0")"

echo "============================================================"
echo "         Antigravity macOS 简体中文汉化补丁                 "
echo "============================================================"
echo ""

APP_PATH="/Applications/Antigravity.app"
if [ ! -d "$APP_PATH" ]; then
    echo "❌ 未在 /Applications/Antigravity.app 找到应用！"
    echo "请确认 Antigravity 是否安装在应用程序文件夹中。"
    exit 1
fi

echo "请选择操作："
echo "[1] 安装简体中文补丁 (zh-CN)"
echo "[2] 安装繁体中文补丁 (zh-TW)"
echo "[3] 安装繁体中文补丁 (zh-HK)"
echo "[4] 还原原版备份 / 卸载补丁"
echo "[5] 禁止自动更新"
echo "[6] 恢复自动更新"
echo "[Q] 退出"
echo ""

read -p "请输入选项 [1-6 / Q]: " choice

LANG_CHOICE="zh-CN"
ACTION="install"

case "$choice" in
    1)
        ACTION="install"
        LANG_CHOICE="zh-CN"
        ;;
    2)
        ACTION="install"
        LANG_CHOICE="zh-TW"
        ;;
    3)
        ACTION="install"
        LANG_CHOICE="zh-HK"
        ;;
    4)
        ACTION="restore"
        ;;
    5)
        ACTION="disable-updates"
        ;;
    6)
        ACTION="enable-updates"
        ;;
    [qQ])
        echo "已退出。"
        exit 0
        ;;
    *)
        echo "无效选项。"
        exit 1
        ;;
esac

# 关闭运行中的 Antigravity
pkill -f "Antigravity" 2>/dev/null || true

# 调用核心修补脚本
python3 scripts/patch_antigravity.py "$ACTION" --lang "$LANG_CHOICE" --dir "$APP_PATH"

# macOS 特别处理：修补 asar 后需要重新进行 ad-hoc 代码签名，避免闪退或损坏提示
if [ "$ACTION" = "install" ]; then
    echo "正在对 Antigravity.app 进行本机 ad-hoc 重签名..."
    codesign --force --deep -s - "$APP_PATH" 2>/dev/null || true
    echo "✔ 重签名完成。"
fi

echo ""
echo "✔ 操作已完成！"
read -p "按回车键退出..."
