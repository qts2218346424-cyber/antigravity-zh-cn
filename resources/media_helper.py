# -*- coding: utf-8 -*-
import sys
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

WM_APPCOMMAND = 0x0319
APPCOMMAND_MEDIA_NEXTTRACK = 11
APPCOMMAND_MEDIA_PREVIOUSTRACK = 12
APPCOMMAND_MEDIA_STOP = 13
APPCOMMAND_MEDIA_PLAY_PAUSE = 14

cmd_map = {
    'play_pause': (APPCOMMAND_MEDIA_PLAY_PAUSE, 0xB3),
    'next': (APPCOMMAND_MEDIA_NEXTTRACK, 0xB0),
    'prev': (APPCOMMAND_MEDIA_PREVIOUSTRACK, 0xB1),
}

action = sys.argv[1] if len(sys.argv) > 1 else 'play_pause'
app_cmd, vk = cmd_map.get(action, (APPCOMMAND_MEDIA_PLAY_PAUSE, 0xB3))

# 1. 寻找 QQ 音乐进程相关窗口投递定向消息
def enum_cb(hwnd, extra):
    try:
        class_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buf, 256)
        cls = class_buf.value.lower()
        if 'qqmusic' in cls or 'txgui' in cls:
            user32.PostMessageW(hwnd, WM_APPCOMMAND, hwnd, app_cmd << 16)
    except Exception:
        pass
    return True

try:
    CMP = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(CMP(enum_cb), 0)
except Exception:
    pass

# 2. 发送全局系统级多媒体按键 (VK_MEDIA_*)
try:
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    user32.keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
except Exception:
    pass
