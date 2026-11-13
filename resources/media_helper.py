# -*- coding: utf-8 -*-
"""
多媒体与 QQ 音乐客户端双向联动助手 (Antigravity Media Helper)
功能：
1. 媒体按键模拟 (播放/暂停/上一首/下一首) 与直接投递
2. 进程与桌面窗口标题嗅探 (实时获取当前正在播放的歌名与歌手)
3. 歌词在线匹配检索与格式化输出
"""
import sys
import os
import json
import ctypes
from ctypes import wintypes
import urllib.request
import urllib.parse
import base64

import tempfile
import time

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# 非 Windows 平台没有 ctypes.windll：模块仍可导入，status 返回“未在播放”的空状态
IS_WINDOWS = sys.platform == 'win32'
user32 = ctypes.windll.user32 if IS_WINDOWS else None

# 歌词缓存：状态每 4 秒轮询一次，同一首歌不再重复联网检索（否则每次轮询最多 4 次 3.5 秒的网络请求）
_LRC_CACHE_FILE = os.path.join(tempfile.gettempdir(), 'agzh-media-lrc-cache.json')
_LRC_CACHE_MAX = 40

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

def ensure_desktop_access():
    """确保当前进程拥有访问交互式桌面的权限 (WinSta0\\Default)"""
    try:
        import win32service, win32con
        hw = win32service.OpenWindowStation('WinSta0', False, win32con.MAXIMUM_ALLOWED)
        hw.SetProcessWindowStation()
        hd = win32service.OpenDesktop('Default', 0, False, win32con.MAXIMUM_ALLOWED)
        return hd
    except Exception:
        return None

def fetch_lrc_online(keyword):
    """在线检索歌曲 LRC 歌词 (优先尝试免密公开歌词库)"""
    if not keyword or not keyword.strip():
        return None
    
    # 过滤掉括号中的副标题，提高检索命中率
    clean_kw = keyword.strip()
    idx = clean_kw.find('(')
    if idx > 2:
        search_kw = clean_kw[:idx].strip()
    else:
        search_kw = clean_kw

    try:
        url = 'http://lyrics.kugou.com/search?ver=1&man=yes&client=pc&keyword=' + urllib.parse.quote(search_kw) + '&duration=&hash='
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        cand = data.get('candidates', [])
        if not cand:
            # 尝试用原始关键词
            if search_kw != clean_kw:
                url = 'http://lyrics.kugou.com/search?ver=1&man=yes&client=pc&keyword=' + urllib.parse.quote(clean_kw) + '&duration=&hash='
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                cand = data.get('candidates', [])

        if cand:
            c = cand[0]
            cid = c.get('id')
            ckey = c.get('accesskey')
            down_url = f'http://lyrics.kugou.com/download?ver=1&client=pc&id={cid}&accesskey={ckey}&fmt=lrc&charset=utf8'
            req2 = urllib.request.Request(down_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req2, timeout=3.5) as r2:
                d2 = json.loads(r2.read().decode('utf-8'))
            b64_content = d2.get('content', '')
            if b64_content:
                lrc = base64.b64decode(b64_content).decode('utf-8', errors='ignore')
                if lrc and len(lrc.strip()) > 20:
                    return lrc
    except Exception:
        pass
    return None

def _load_lrc_cache():
    try:
        with open(_LRC_CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_lrc_cache(cache):
    try:
        if len(cache) > _LRC_CACHE_MAX:
            keep = sorted(cache.items(), key=lambda kv: kv[1].get('t', 0))[-_LRC_CACHE_MAX:]
            cache = dict(keep)
        tmp = _LRC_CACHE_FILE + '.%d.tmp' % os.getpid()
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)
        os.replace(tmp, _LRC_CACHE_FILE)
    except Exception:
        pass


def fetch_lrc_cached(title, artist):
    """按“歌名 + 歌手”缓存歌词检索结果（含“未找到”），返回 LRC 文本或 None。"""
    key = ('%s|%s' % (title or '', artist or '')).strip()
    cache = _load_lrc_cache()
    hit = cache.get(key)
    if hit is not None:
        return hit.get('lrc') or None
    query = ('%s %s' % (title or '', artist or '')).strip()
    lrc = fetch_lrc_online(query)
    if not lrc and title:
        lrc = fetch_lrc_online(title)
    cache[key] = {'lrc': lrc or '', 't': time.time()}
    _save_lrc_cache(cache)
    return lrc


def generate_melodic_lrc(title, artist):
    """当曲目为纯音乐或未检索到歌词时，生成意境优雅的伴奏歌词流"""
    artist_display = f" - {artist}" if artist else ""
    return f"""[00:00.00] 正在播放: {title}{artist_display}
[00:04.00] 🎵 纯音乐 · 请静心聆听这美妙流淌的旋律
[00:12.00] 🎹 阳光洒落，微风吹拂过金色的琴弦
[00:24.00] 💫 每一个跃动的音符，都是心灵最温柔的对话
[00:38.00] 🌸 玫瑰花在玻璃罩中静静绽放，守护着彼此的约定
[00:52.00] ✨ 星辰在远方低语，陪伴是最长情的告白
[01:10.00] 🍃 旋律如清泉流淌，洗去所有疲惫与喧嚣
[01:30.00] 🌙 愿这片刻的音韵，带给你宁静与灵感"""

def get_current_music_status():
    """实时探测当前系统所有正在播放音乐的窗口状态 (重点覆盖 QQ 音乐 Daemon 窗口)"""
    hd = ensure_desktop_access()
    status = {
        'isPlaying': False,
        'title': '',
        'artist': '',
        'rawTitle': '',
        'source': 'unknown',
        'lrc': ''
    }

    music_windows = []
    if not IS_WINDOWS:
        return status

    def enum_cb(hwnd, extra):
        try:
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()

                cls_buff = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buff, 256)
                cls = cls_buff.value

                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

                # 重点 1: QQ 音乐官方服务窗口
                if cls == 'QQMusic_Daemon_Wnd' and title and title != 'QQ音乐':
                    music_windows.append(('qqmusic_daemon', title, pid.value))
                # 重点 2: 其它媒体窗口标题 (通常带有 " - ")
                elif ' - ' in title and any(k in cls.lower() or k in title.lower() for k in ['music', 'qq', 'cloud', 'kugou', 'player']):
                    music_windows.append(('general_music', title, pid.value))
        except Exception:
            pass
        return True

    try:
        if hd:
            import win32gui
            win32gui.EnumDesktopWindows(hd, enum_cb, None)
        else:
            CMP = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(CMP(enum_cb), 0)
    except Exception:
        pass

    if music_windows:
        # 优先选用 qqmusic_daemon
        best = music_windows[0]
        for item in music_windows:
            if item[0] == 'qqmusic_daemon':
                best = item
                break

        raw_title = best[1]
        status['rawTitle'] = raw_title
        status['source'] = best[0]
        status['isPlaying'] = True

        # 解析 "歌曲名 - 歌手名"
        if ' - ' in raw_title:
            parts = raw_title.split(' - ', 1)
            status['title'] = parts[0].strip()
            status['artist'] = parts[1].strip()
        else:
            status['title'] = raw_title
            status['artist'] = 'QQ 音乐'

        # 尝试检索歌词
        lrc = fetch_lrc_cached(status['title'], status['artist'])
        if not lrc:
            lrc = generate_melodic_lrc(status['title'], status['artist'])
        status['lrc'] = lrc

    return status

def send_control_action(action):
    """向 QQ 音乐及系统媒体发送按键指令"""
    if not IS_WINDOWS:
        return
    app_cmd, vk = cmd_map.get(action, (APPCOMMAND_MEDIA_PLAY_PAUSE, 0xB3))

    def enum_post_cb(hwnd, extra):
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
        user32.EnumWindows(CMP(enum_post_cb), 0)
    except Exception:
        pass

    try:
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002
        user32.keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY, 0)
        user32.keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
    except Exception:
        pass

ACTIONS = ('status', 'info', 'get_status', 'play_pause', 'next', 'prev', 'search_lrc')


def main(argv=None, out=None):
    """命令行入口：输出一行 JSON。供 Electron 主进程 / 打包版 --media 模式调用。"""
    argv = list(sys.argv[1:] if argv is None else argv)
    out = out or sys.stdout
    action = argv[0] if argv else 'status'
    if action in ('status', 'info', 'get_status'):
        result = get_current_music_status()
    elif action == 'search_lrc' and len(argv) > 1:
        kw = ' '.join(argv[1:])
        lrc = fetch_lrc_online(kw) or generate_melodic_lrc(kw, '')
        result = {'title': kw, 'lrc': lrc}
    elif action in cmd_map:
        send_control_action(action)
        # 执行操作后紧接着返回最新状态
        try:
            result = get_current_music_status()
        except Exception:
            result = {'status': 'ok'}
    else:
        result = {'error': 'unknown action', 'action': action}
        out.write(json.dumps(result, ensure_ascii=False) + '\n')
        out.flush()
        return 2
    out.write(json.dumps(result, ensure_ascii=False) + '\n')
    out.flush()
    return 0


if __name__ == '__main__':
    sys.exit(main())
