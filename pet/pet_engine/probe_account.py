# -*- coding: utf-8 -*-
"""
pet_engine/probe_account.py - Real Antigravity Account & Quota Inspector (Windows)
References cockpit-tools architecture for live Credential Manager & CloudCode integration.
"""

import sys
import os
import json
import time
import ssl
import sqlite3
import urllib.request
from pathlib import Path
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


def read_system_credential(target_name: str = "gemini:antigravity") -> Optional[Dict[str, Any]]:
    """Reads Generic Credential from Windows Credential Manager."""
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


def write_system_credential(payload_dict: Dict[str, Any], target_name: str = "gemini:antigravity", user_name: str = "antigravity") -> bool:
    """Writes/Updates Generic Credential in Windows Credential Manager."""
    if not advapi32:
        return False

    raw_json = json.dumps(payload_dict, ensure_ascii=False)
    blob_bytes = raw_json.encode('utf-8')
    blob_buf = ctypes.create_string_buffer(blob_bytes, len(blob_bytes))

    cred = CREDENTIAL()
    cred.Flags = 0
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = target_name
    cred.Comment = "Antigravity Token Managed by Pet/Cockpit"
    cred.CredentialBlobSize = len(blob_bytes)
    cred.CredentialBlob = ctypes.cast(blob_buf, ctypes.POINTER(ctypes.c_char))
    cred.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE
    cred.AttributeCount = 0
    cred.Attributes = None
    cred.TargetAlias = None
    cred.UserName = user_name

    res = advapi32.CredWriteW(ctypes.byref(cred), 0)
    return bool(res)


def fetch_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """Calls Google OAuth2 userinfo to get name and email."""
    try:
        req = urllib.request.Request("https://www.googleapis.com/oauth2/v2/userinfo")
        req.add_header("Authorization", f"Bearer {access_token}")
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
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


def fetch_real_quota(access_token: str) -> Optional[Dict[str, Any]]:
    """Calls CloudCode retrieveUserQuotaSummary to get weekly and 5h buckets."""
    try:
        url = "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "antigravity/1.20.5 windows/amd64"
        }
        req = urllib.request.Request(url, data=b"{}", headers=headers)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                return data
    except Exception as e:
        print(f"[probe_account] fetch_real_quota error: {e}")
    return None


if __name__ == "__main__":
    cred = read_system_credential()
    print("Read Credential:", bool(cred))
    if cred:
        t = cred.get("token", {})
        acc = t.get("access_token", "")
        print("Access Token Prefix:", acc[:15] if acc else "None")
        info = fetch_user_info(acc)
        print("User Info:", info)
        q = fetch_real_quota(acc)
        if q:
            print("Groups found:", len(q.get("groups", [])))
            for g in q.get("groups", []):
                print(" -", g.get("displayName"))
                for b in g.get("buckets", []):
                    pct = round(b.get("remainingFraction", 0) * 100, 1)
                    print(f"    * {b.get('displayName')}: {pct}% (重置时间: {b.get('resetTime')})")
