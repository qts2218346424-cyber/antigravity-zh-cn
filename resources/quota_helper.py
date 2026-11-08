# -*- coding: utf-8 -*-
"""
基于 Cockpit Tools 原理的 Antigravity 官方模型配额解析与同步引擎 (v2.0 账号自适应版)
功能：
1. 优先从 Antigravity 核心系统数据库中动态嗅探当前活跃登录账号 (支持 qts2218346424@gmail.com 等多账号)
2. 匹配并读取 ~/.antigravity_cockpit 对应当前账号的权威配额缓存
3. 智能兼容 quota_summary 桶聚合 与 models 独立模型集两种官方配额结构
4. 计算人性化重置倒计时 (天/小时/分钟)
5. 输出标准 JSON 格式供前端与桌宠主进程使用
"""
import os
import sys
import json
import sqlite3
import re
import base64
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def detect_current_active_email():
    """从 Antigravity 核心系统数据库中动态嗅探当前正在登录的账号"""
    try:
        appdata = os.environ.get('APPDATA', '')
        db_path = Path(appdata) / 'Antigravity' / 'User' / 'globalStorage' / 'state.vscdb'
        if db_path.exists():
            conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
            cur = conn.cursor()
            cur.execute("SELECT value FROM ItemTable WHERE key = 'jetskiStateSync.agentManagerInitState';")
            row = cur.fetchone()
            if row and row[0]:
                val = row[0]
                try:
                    decoded = base64.b64decode(val)
                    emails = re.findall(rb'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', decoded)
                    if emails:
                        return emails[0].decode('utf-8', errors='ignore')
                except Exception:
                    pass
    except Exception:
        pass

    # 备选：从 Cockpit current_account.json
    try:
        cur_acc = Path.home() / ".antigravity_cockpit" / "current_account.json"
        if cur_acc.exists():
            d = json.loads(cur_acc.read_text(encoding="utf-8"))
            if d.get("email"):
                return d.get("email")
    except Exception:
        pass

    return "qts2218346424@gmail.com"

def format_reset_time(iso_str):
    if not iso_str:
        return "额度充裕"
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = dt - now
        total_seconds = int(delta.total_seconds())
        if total_seconds <= 0:
            return "已重置 / 额度已全满"
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        if days > 0:
            return f"{days} 天 {hours} 小时后重置"
        elif hours > 0:
            return f"{hours} 小时 {minutes} 分钟后重置"
        else:
            return f"{minutes} 分钟后重置"
    except Exception:
        return "计算中..."

def get_cockpit_quota_data():
    home_dir = Path.home()
    base_dir = home_dir / ".antigravity_cockpit"
    cache_dir = base_dir / "cache" / "quota_api_v1_desktop" / "authorized"

    target_email = detect_current_active_email()

    candidates = []
    if cache_dir.exists():
        for fp in cache_dir.glob("*.json"):
            try:
                d = json.loads(fp.read_text(encoding="utf-8"))
                email = d.get("email")
                updated_at = d.get("updatedAt", 0)
                mtime = fp.stat().st_mtime
                candidates.append((fp, email, updated_at, mtime, d))
            except Exception:
                pass

    best_candidate = None
    # 优先精确匹配当前活跃账号 (如 qts2218346424@gmail.com)
    if target_email:
        for c in candidates:
            if c[1] == target_email:
                best_candidate = c
                break

    # 若未精准匹配，按最新更新时间排序回退
    if not best_candidate and candidates:
        candidates.sort(key=lambda x: (x[2], x[3]), reverse=True)
        best_candidate = candidates[0]

    if not best_candidate:
        return {
            "email": target_email,
            "source": "fallback",
            "geminiWeeklyPct": 100,
            "geminiWeeklyReset": "已重置 / 额度已全满",
            "gemini5hPct": 100,
            "gemini5hReset": "已重置 / 额度已全满",
            "claudeWeeklyPct": 100,
            "claudeWeeklyReset": "已重置 / 额度已全满",
            "claude5hPct": 100,
            "claude5hReset": "已重置 / 额度已全满",
            "lastSynced": "刚刚"
        }

    fp, email, updated_at, mtime, d = best_candidate
    payload = d.get("payload", {})
    
    time_str = "刚刚"
    if updated_at:
        try:
            time_str = datetime.fromtimestamp(updated_at / 1000.0).strftime('%H:%M:%S')
        except Exception:
            pass

    result = {
        "email": email or target_email,
        "updatedAt": updated_at,
        "source": "cockpit_cache",
        "geminiWeeklyPct": 100,
        "geminiWeeklyReset": "已重置 / 额度已全满",
        "gemini5hPct": 100,
        "gemini5hReset": "已重置 / 额度已全满",
        "claudeWeeklyPct": 100,
        "claudeWeeklyReset": "已重置 / 额度已全满",
        "claude5hPct": 100,
        "claude5hReset": "已重置 / 额度已全满",
        "lastSynced": time_str
    }

    # 方式一：如果包含 quota_summary.groups 桶数据
    quota_summary = payload.get("quota_summary")
    if quota_summary and quota_summary.get("groups"):
        for g in quota_summary.get("groups", []):
            buckets = g.get("buckets", [])
            for b in buckets:
                bid = (b.get("bucketId") or "").lower()
                rem_frac = b.get("remainingFraction", 1.0)
                pct = max(0, min(100, round(rem_frac * 100)))
                reset_txt = format_reset_time(b.get("resetTime"))

                if "gemini-weekly" in bid:
                    result["geminiWeeklyPct"] = pct
                    result["geminiWeeklyReset"] = reset_txt
                elif "gemini-5h" in bid:
                    result["gemini5hPct"] = pct
                    result["gemini5hReset"] = reset_txt
                elif "3p-weekly" in bid or "claude-weekly" in bid:
                    result["claudeWeeklyPct"] = pct
                    result["claudeWeeklyReset"] = reset_txt
                elif "3p-5h" in bid or "claude-5h" in bid:
                    result["claude5hPct"] = pct
                    result["claude5hReset"] = reset_txt
        return result

    # 方式二：如果 quota_summary 为空，从 models 集合中精准聚合
    models = payload.get("models", {})
    gemini_pcts = []
    claude_pcts = []
    gemini_reset = ""
    claude_reset = ""

    for mid, mdata in models.items():
        qinfo = mdata.get("quotaInfo")
        if not qinfo:
            continue
        frac = qinfo.get("remainingFraction", 1.0)
        pct = max(0, min(100, round(frac * 100)))
        rt = qinfo.get("resetTime")

        mid_lower = mid.lower()
        if "gemini" in mid_lower:
            gemini_pcts.append(pct)
            if rt and not gemini_reset:
                gemini_reset = format_reset_time(rt)
        elif "claude" in mid_lower or "gpt" in mid_lower:
            claude_pcts.append(pct)
            if rt and not claude_reset:
                claude_reset = format_reset_time(rt)

    if gemini_pcts:
        result["geminiWeeklyPct"] = min(gemini_pcts)
        result["gemini5hPct"] = min(gemini_pcts)
        result["geminiWeeklyReset"] = gemini_reset or "已重置 / 额度已全满"
        result["gemini5hReset"] = gemini_reset or "已重置 / 额度已全满"

    if claude_pcts:
        result["claudeWeeklyPct"] = min(claude_pcts)
        result["claude5hPct"] = min(claude_pcts)
        result["claudeWeeklyReset"] = claude_reset or "已重置 / 额度已全满"
        result["claude5hReset"] = claude_reset or "已重置 / 额度已全满"

    return result

if __name__ == "__main__":
    quota = get_cockpit_quota_data()
    print(json.dumps(quota, ensure_ascii=False))
