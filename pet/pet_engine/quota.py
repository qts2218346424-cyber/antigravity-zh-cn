"""
pet_engine/quota.py - Quota Monitoring and Dual-Source Inspection Service

Features:
- Live SQLite state.vscdb inspection using PRAGMA busy_timeout = 5000.
- Protobuf wire decoding of model credits and user status via ProtoWireParser.
- Deterministic mock driver for isolated offline CI/CD and testing.
- Status classification: healthy (>50%), warning (20-50%), critical (<20%), exhausted (0%).
- Task completion and low-quota alert generation with rate-limiting cooldowns.
"""

from __future__ import annotations

import os
import json
import time
import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from pet_engine.models import (
    QuotaStatus,
    QuotaHealthStatus,
    NotificationEvent,
    NotificationLevel,
    now_utc_iso,
)
from pet_engine.proto_decoder import ProtoWireParser

try:
    from pet_engine.probe_account import read_system_credential, fetch_user_info, fetch_real_quota
except ImportError:
    try:
        from pet.pet_engine.probe_account import read_system_credential, fetch_user_info, fetch_real_quota
    except ImportError:
        read_system_credential = None
        fetch_user_info = None
        fetch_real_quota = None


class QuotaMonitor:
    """
    Monitors Antigravity model quota from local SQLite state.vscdb or mock source.
    """
    def __init__(
        self,
        mode: str = "auto",
        mock_file: Optional[Union[str, Path]] = None,
        vscdb_path: Optional[Union[str, Path]] = None,
        gemini_dir: Optional[Union[str, Path]] = None,
        warning_threshold: float = 20.0,
        critical_threshold: float = 5.0,
    ):
        self.mode = mode.lower().strip()
        self.mock_file = Path(mock_file) if mock_file else None
        self.warning_threshold = float(warning_threshold)
        self.critical_threshold = float(critical_threshold)

        if gemini_dir:
            self.gemini_dir = Path(gemini_dir)
        else:
            self.gemini_dir = Path.home() / ".gemini"

        if vscdb_path:
            self.vscdb_path = Path(vscdb_path)
        else:
            appdata = os.environ.get("APPDATA")
            if appdata:
                cand = Path(appdata) / "Antigravity" / "User" / "globalStorage" / "state.vscdb"
                self.vscdb_path = cand if cand.exists() else None
            else:
                self.vscdb_path = None

        self._cached_status: Optional[QuotaStatus] = None
        self._cache_time: float = 0.0
        self._cache_ttl: float = 5.0  # 5-second in-memory cache
        self._api_cached_status: Optional[QuotaStatus] = None
        self._api_last_fetch_time: float = 0.0
        self._api_cache_ttl: float = 300.0  # 5-minute lazy-load cache for Google API
        self._lock = threading.Lock()

        # Alert tracking
        self._last_low_quota_alert_time: float = 0.0
        self._last_alert_percentage: Optional[float] = None
        self._seen_tasks: Dict[str, float] = {}

    def _read_from_system_credential_api(self, force_refresh: bool = False) -> Optional[QuotaStatus]:
        """
        Reads real Antigravity live quota from Windows Credential Manager and CloudCode API.
        Enforces a 5-minute lazy-load cache and never rotates tokens to protect host IDE session.
        """
        if not read_system_credential or not fetch_real_quota:
            return None

        now = time.monotonic()
        if not force_refresh and self._api_cached_status and (now - self._api_last_fetch_time < self._api_cache_ttl):
            return self._api_cached_status

        try:
            cred = read_system_credential()
            if not cred or not isinstance(cred, dict):
                return None

            token_data = cred.get("token", {})
            access_token = token_data.get("access_token", "")
            if not access_token:
                return None

            user_info = fetch_user_info(access_token) if fetch_user_info else {}
            user_name = user_info.get("name", "") if user_info else ""
            user_email = user_info.get("email", "") if user_info else ""
            user_pic = user_info.get("picture", "") if user_info else ""

            quota_json = fetch_real_quota(access_token)
            if not quota_json or not isinstance(quota_json, dict):
                return None

            raw_groups = quota_json.get("groups", [])
            parsed_groups = []
            models_list = []
            primary_percentage = 100.0
            primary_reset_time = None

            for g in raw_groups:
                g_display = g.get("displayName", "Model Group")
                g_desc = g.get("description", "")
                parsed_buckets = []
                for b in g.get("buckets", []):
                    b_id = b.get("bucketId", "")
                    b_name = b.get("displayName", b_id)
                    b_rem = float(b.get("remainingFraction", 1.0))
                    b_pct = round(b_rem * 100.0, 1)
                    b_reset = b.get("resetTime")
                    b_desc = b.get("description", "")

                    parsed_buckets.append({
                        "bucketId": b_id,
                        "displayName": b_name,
                        "remainingFraction": b_rem,
                        "percentage": b_pct,
                        "resetTime": b_reset,
                        "description": b_desc,
                    })

                    # If this is Gemini 5h bucket or 3p 5h bucket, use for health classification
                    if "5h" in b_id.lower() or "rolling" in b_id.lower():
                        if "gemini" in b_id.lower() or primary_percentage == 100.0:
                            primary_percentage = b_pct
                            primary_reset_time = b_reset

                parsed_groups.append({
                    "displayName": g_display,
                    "description": g_desc,
                    "buckets": parsed_buckets
                })

                models_list.append({
                    "name": g_display,
                    "available": True,
                    "percentage": primary_percentage,
                    "remaining_requests": int(primary_percentage),
                    "total_requests": 100,
                })

            total = 1000
            used = int(round((100.0 - primary_percentage) * 10))
            status = self._classify_status(total, used)

            res = QuotaStatus(
                total_tokens=total,
                used_tokens=used,
                remaining_tokens=max(0, total - used),
                remaining_percentage=round(primary_percentage, 2),
                status=status,
                reset_time_utc=primary_reset_time,
                models=models_list,
                groups=parsed_groups,
                user_name=user_name,
                user_picture=user_pic,
                fetched_at=now_utc_iso(),
                remaining_basis_points=int(primary_percentage * 100),
                account_email=user_email,
                profile_id="antigravity-system",
                is_cached=False,
            )

            self._api_cached_status = res
            self._api_last_fetch_time = now
            return res

        except Exception:
            return None

    def _read_from_sqlite(self) -> Optional[QuotaStatus]:
        """Inspect state.vscdb and decode unified state sync records."""
        if not self.vscdb_path or not self.vscdb_path.exists():
            return None

        conn = None
        try:
            conn = sqlite3.connect(str(self.vscdb_path), timeout=5.0)
            conn.execute("PRAGMA busy_timeout = 5000")
            cursor = conn.cursor()

            # Query credits, user status, and auth info
            cursor.execute(
                "SELECT key, value FROM ItemTable WHERE key IN (?, ?, ?)",
                (
                    "antigravityUnifiedStateSync.modelCredits",
                    "antigravityUnifiedStateSync.userStatus",
                    "antigravityAuthStatus",
                )
            )
            rows = dict(cursor.fetchall())
            if not rows:
                return None

            credits_b64 = rows.get("antigravityUnifiedStateSync.modelCredits", "")
            status_b64 = rows.get("antigravityUnifiedStateSync.userStatus", "")
            auth_val = rows.get("antigravityAuthStatus", "{}")

            account_email = ""
            try:
                auth_obj = json.loads(auth_val)
                account_email = auth_obj.get("email", "")
            except Exception:
                pass

            parsed = ProtoWireParser.parse_unified_state(credits_b64, status_b64)
            if not parsed["has_credits"] and not parsed["has_status"]:
                return None

            available = parsed["credits"]
            total = 1000
            if "Ultra" in parsed["tier"]:
                total = 5000
            elif available > total:
                total = available

            used = max(0, total - available)

            model_names = parsed["models"] or ["gemini-1.5-pro", "gemini-1.5-flash", "claude-3-5-sonnet"]
            models_list = []
            for m_name in model_names:
                models_list.append({
                    "name": m_name,
                    "available": True,
                    "credits_per_usage": parsed["min_credits_per_usage"],
                    "remaining_requests": available // max(1, parsed["min_credits_per_usage"]),
                    "total_requests": total // max(1, parsed["min_credits_per_usage"]),
                    "percentage": round((available / total) * 100.0, 2) if total > 0 else 0.0,
                })

            status = self._classify_status(total, used)
            pct = round(((total - used) * 100.0) / total, 2) if total > 0 else 0.0

            return QuotaStatus(
                total_tokens=total,
                used_tokens=used,
                remaining_tokens=max(0, total - used),
                remaining_percentage=pct,
                status=status,
                models=models_list,
                fetched_at=now_utc_iso(),
                remaining_basis_points=int(pct * 100),
                account_email=account_email or parsed.get("email", ""),
                profile_id="",
                is_cached=False,
            )

        except Exception:
            return None
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _read_from_mock(self) -> QuotaStatus:
        """Produce deterministic mock quota data."""
        if self.mock_file and self.mock_file.exists():
            try:
                with open(self.mock_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return QuotaStatus.from_dict(data)
            except Exception:
                pass

        total = 1000
        used = 200
        rem = total - used
        pct = round((rem * 100.0) / total, 2)
        status = self._classify_status(total, used)

        models_list = [
            {"name": "gemini-1.5-pro", "available": True, "remaining_requests": 16, "total_requests": 20, "percentage": 80.0},
            {"name": "gemini-1.5-flash", "available": True, "remaining_requests": 80, "total_requests": 100, "percentage": 80.0},
            {"name": "claude-3-5-sonnet", "available": True, "remaining_requests": 16, "total_requests": 20, "percentage": 80.0},
        ]

        return QuotaStatus(
            total_tokens=total,
            used_tokens=used,
            remaining_tokens=rem,
            remaining_percentage=pct,
            status=status,
            reset_time_utc=None,
            models=models_list,
            fetched_at=now_utc_iso(),
            remaining_basis_points=int(pct * 100),
            account_email="developer@example.com",
            profile_id="default",
            is_cached=False,
        )

    def _classify_status(self, total: int, used: int) -> str:
        """
        Classifies health level:
        - > 50%: healthy
        - 20% - 50%: warning
        - < 20%: critical
        - 0%: exhausted
        """
        if total <= 0:
            return QuotaHealthStatus.EXHAUSTED.value
        rem = max(0, total - used)
        if rem == 0:
            return QuotaHealthStatus.EXHAUSTED.value

        bps = (rem * 10000) // total
        if bps <= 0:
            return QuotaHealthStatus.EXHAUSTED.value
        elif bps < 2000:
            return QuotaHealthStatus.CRITICAL.value
        elif bps <= 5000:
            return QuotaHealthStatus.WARNING.value
        else:
            return QuotaHealthStatus.HEALTHY.value

    def get_quota_status(self, force_refresh: bool = False) -> QuotaStatus:
        """
        Retrieves current QuotaStatus, utilizing TTL caching unless force_refresh is True.
        """
        with self._lock:
            now = time.monotonic()
            if not force_refresh and self._cached_status and (now - self._cache_time < self._cache_ttl):
                return self._cached_status

            status: Optional[QuotaStatus] = None

            if self.mode in ("live", "auto"):
                status = self._read_from_system_credential_api(force_refresh)
                if not status:
                    status = self._read_from_sqlite()

            if not status and self.mode in ("mock", "auto"):
                status = self._read_from_mock()

            if not status:
                status = self._read_from_mock()

            self._cached_status = status
            self._cache_time = now
            return status

    def evaluate_task_notification(
        self,
        task_id: str,
        status: str,
        duration_s: float,
    ) -> Optional[NotificationEvent]:
        """
        Evaluates task completed or failed events with 3-second debounce window.
        """
        with self._lock:
            now = time.monotonic()
            clean_task = str(task_id).strip()
            # 3-second debounce per task
            if clean_task in self._seen_tasks:
                if now - self._seen_tasks[clean_task] < 3.0:
                    return None
            self._seen_tasks[clean_task] = now

            status_norm = str(status).lower().strip()
            if status_norm in ("completed", "success"):
                return NotificationEvent(
                    title="Agent Task Completed",
                    body=f"Task '{clean_task}' completed successfully in {duration_s:.1f}s.",
                    level=NotificationLevel.SUCCESS.value,
                    channel="toast",
                    dedupe_key=f"task:{clean_task}",
                    metadata={"task_id": clean_task, "duration_s": duration_s, "status": "completed"},
                )
            elif status_norm in ("failed", "error"):
                return NotificationEvent(
                    title="Agent Task Failed",
                    body=f"Task '{clean_task}' failed after {duration_s:.1f}s.",
                    level=NotificationLevel.ERROR.value,
                    channel="toast",
                    dedupe_key=f"task:{clean_task}",
                    metadata={"task_id": clean_task, "duration_s": duration_s, "status": "failed"},
                )
            return None

    def check_low_quota_alert(self, current_percentage: float) -> Optional[NotificationEvent]:
        """
        Proactive low-quota alerting with 15-minute cooldown to prevent notification spam.
        """
        with self._lock:
            now = time.monotonic()
            pct = float(current_percentage)

            if pct > self.warning_threshold:
                # Reset alert state when quota is healthy
                self._last_alert_percentage = None
                return None

            # Check 15-minute cooldown (900 seconds)
            if now - self._last_low_quota_alert_time < 900.0:
                return None

            self._last_low_quota_alert_time = now
            self._last_alert_percentage = pct

            level = NotificationLevel.WARNING.value if pct > self.critical_threshold else NotificationLevel.ERROR.value
            return NotificationEvent(
                title="Low Quota Alert",
                body=f"Antigravity quota is running low ({pct:.1f}% remaining).",
                level=level,
                channel="toast",
                dedupe_key=f"quota_alert_{int(pct)}",
                metadata={"percentage": pct, "warning_threshold": self.warning_threshold},
            )
