#!/usr/bin/env bash
# Antigravity Linux 汉化补丁一键运行脚本
set -e

cd "$(dirname "$0")"

echo "============================================================"
echo "         Antigravity Linux 简体中文汉化补丁                 "
echo "============================================================"
echo ""

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
pkill -f "antigravity" 2>/dev/null || true

python3 scripts/patch_antigravity.py "$ACTION" --lang "$LANG_CHOICE"

echo ""
echo "✔ 操作已完成！"
