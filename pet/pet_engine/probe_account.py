# -*- coding: utf-8 -*-
"""
pet_engine/probe_account.py - Real Antigravity Account & Quota Inspector (Windows)
References Cockpit Tools architecture for live Windows Credential Manager & CloudCode integration.
"""

import sys
import os
import json
import time
import ssl
import urllib.request
from typing import Dict, Any, Optional, List, Tuple
import ctypes
from ctypes import wintypes

CRED_TYPE_GENERIC = 1

class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD),
        ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR),
        ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME),
        ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_char)),
        ('Persist', wintypes.DWORD),
        ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.c_void_p),
        ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR),
    ]

PCREDENTIAL = ctypes.POINTER(CREDENTIAL)
advapi32 = ctypes.windll.advapi32 if sys.platform == 'win32' else None

# In-memory quota cache to prevent spamming Google CloudCode API
_QUOTA_CACHE: Dict[str, Any] = {
    "timestamp": 0.0,
    "data": None
}
_CACHE_TTL_SECONDS = 30.0


def read_system_credential(target_name: str = "gemini:antigravity") -> Optional[Dict[str, Any]]:
    """Reads Generic Credential from Windows Credential Manager safely."""
    if not advapi32:
        return None

    cred_ptr = PCREDENTIAL()
    res = advapi32.CredReadW(target_name, CRED_TYPE_GENERIC, 0, ctypes.byref(cred_ptr))
    if not res:
        return None

    try:
        cred = cred_ptr.contents
        raw_bytes = ctypes.string_at(cred.CredentialBlob, cred.CredentialBlobSize)
        text = raw_bytes.decode('utf-8', errors='ignore')
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"[probe_account] Failed to decode credential: {e}")
        return None
    finally:
        advapi32.CredFree(cred_ptr)


def fetch_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """Calls Google OAuth2 userinfo to retrieve name and email."""
    if not access_token:
        return None
    try:
        req = urllib.request.Request("https://www.googleapis.com/oauth2/v2/userinfo")
        req.add_header("Authorization", f"Bearer {access_token}")
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                return {
                    "email": data.get("email", ""),
                    "name": data.get("name", ""),
                    "picture": data.get("picture", "")
                }
    except Exception as e:
        print(f"[probe_account] fetch_user_info error: {e}")
    return None


def fetch_real_quota(access_token: Optional[str] = None, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """
    Calls CloudCode retrieveUserQuotaSummary to get real-time Claude & Gemini dual quotas.
    Returns structured buckets aligned with Cockpit Tools.
    """
    global _QUOTA_CACHE
    now = time.monotonic()
    if not force_refresh and _QUOTA_CACHE["data"] and (now - _QUOTA_CACHE["timestamp"] < _CACHE_TTL_SECONDS):
        return _QUOTA_CACHE["data"]

    if not access_token:
        cred = read_system_credential()
        if not cred:
            return None
        t = cred.get("token", {})
        access_token = t.get("access_token")

    if not access_token:
        return None

    try:
        url = "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "antigravity/1.20.5 windows/amd64"
        }
        req = urllib.request.Request(url, data=b"{}", headers=headers)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            if resp.status == 200:
                raw_data = json.loads(resp.read().decode('utf-8'))
                
                # Parse structured dual-track quotas (Gemini & Claude)
                parsed = {
                    "raw": raw_data,
                    "gemini_5h_pct": 100.0,
                    "gemini_5h_reset": "",
                    "gemini_weekly_pct": 100.0,
                    "gemini_weekly_reset": "",
                    "claude_5h_pct": 100.0,
                    "claude_5h_reset": "",
                    "claude_weekly_pct": 100.0,
                    "claude_weekly_reset": "",
                    "min_remaining_pct": 100.0,
                    "avg_remaining_pct": 100.0
                }

                all_pcts = []
                for group in raw_data.get("groups", []):
                    g_name = (group.get("displayName") or "").lower()
                    is_gemini = "gemini" in g_name
                    is_claude = "claude" in g_name or "gpt" in g_name

                    for b in group.get("buckets", []):
                        b_name = (b.get("displayName") or "").lower()
                        pct = round(float(b.get("remainingFraction", 0.0)) * 100.0, 1)
                        reset_time = b.get("resetTime", "")
                        all_pcts.append(pct)

                        if is_gemini:
                            if "five hour" in b_name or "5 hour" in b_name or "5h" in b_name:
                                parsed["gemini_5h_pct"] = pct
                                parsed["gemini_5h_reset"] = reset_time
                            elif "week" in b_name:
                                parsed["gemini_weekly_pct"] = pct
                                parsed["gemini_weekly_reset"] = reset_time
                        elif is_claude:
                            if "five hour" in b_name or "5 hour" in b_name or "5h" in b_name:
                                parsed["claude_5h_pct"] = pct
                                parsed["claude_5h_reset"] = reset_time
                            elif "week" in b_name:
                                parsed["claude_weekly_pct"] = pct
                                parsed["claude_weekly_reset"] = reset_time

                if all_pcts:
                    parsed["min_remaining_pct"] = min(all_pcts)
                    parsed["avg_remaining_pct"] = round(sum(all_pcts) / len(all_pcts), 1)

                _QUOTA_CACHE["timestamp"] = now
                _QUOTA_CACHE["data"] = parsed
                return parsed
    except Exception as e:
        print(f"[probe_account] fetch_real_quota error: {e}")
    return None


if __name__ == "__main__":
    cred = read_system_credential()
    print("Found Antigravity Credential:", bool(cred))
    if cred:
        token = cred.get("token", {}).get("access_token", "")
        info = fetch_user_info(token)
        print("User Info:", info)
        quota = fetch_real_quota(token)
        print("Real Dual Quota:", json.dumps(quota, indent=2, ensure_ascii=False))
