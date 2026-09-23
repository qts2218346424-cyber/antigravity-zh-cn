"""
pet_engine/notification.py - Task and Quota Alert Evaluator Service

Features:
- Proactive low-quota alerting with 15-minute cooldown deduplication.
- Task completion and task failure event evaluation with 3-second debounce.
- Formats structured NotificationEvent payloads ready for Tauri IPC, WebView2, or tray.
- Thread-safe history buffer with capacity cap.
"""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional, Any, Union

from pet_engine.models import (
    NotificationEvent,
    NotificationLevel,
    NotificationChannel,
    now_utc_iso,
    validate_metadata,
)


class NotificationService:
    """
    Manages alert evaluation, deduplication, rate limiting, and event dispatch.
    """
    def __init__(
        self,
        warning_threshold: float = 20.0,
        critical_threshold: float = 5.0,
        low_quota_cooldown_s: float = 900.0,  # 15 minutes
        task_debounce_s: float = 3.0,
        max_history: int = 100,
    ):
        self.warning_threshold = float(warning_threshold)
        self.critical_threshold = float(critical_threshold)
        self.low_quota_cooldown_s = float(low_quota_cooldown_s)
        self.task_debounce_s = float(task_debounce_s)
        self.max_history = int(max_history)

        self._lock = threading.Lock()
        self._last_low_quota_alert_time: float = 0.0
        self._last_alert_percentage: Optional[float] = None
        self._task_timestamps: Dict[str, float] = {}
        self._history: List[NotificationEvent] = []

    def evaluate_task_event(
        self,
        task_id: str,
        status: str,
        duration_s: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[NotificationEvent]:
        """
        Evaluates task finished or failed event.
        Debounces repeated invocations for the same task_id within task_debounce_s.
        """
        with self._lock:
            now = time.monotonic()
            clean_id = str(task_id).strip()
            if not clean_id:
                clean_id = "unnamed_task"

            # Debounce check
            last_time = self._task_timestamps.get(clean_id)
            if last_time and (now - last_time < self.task_debounce_s):
                return None
            self._task_timestamps[clean_id] = now

            status_norm = str(status).lower().strip()
            meta = dict(metadata or {})
            meta.update({"task_id": clean_id, "duration_s": duration_s, "status": status_norm})

            event: Optional[NotificationEvent] = None
            if status_norm in ("completed", "success", "finished"):
                dur_str = f" in {duration_s:.1f}s" if duration_s > 0 else ""
                event = NotificationEvent(
                    title="Agent Task Completed",
                    body=f"Task '{clean_id}' finished successfully{dur_str}.",
                    level=NotificationLevel.SUCCESS.value,
                    channel=NotificationChannel.TOAST.value,
                    dedupe_key=f"task:{clean_id}",
                    metadata=meta,
                )
            elif status_norm in ("failed", "error"):
                dur_str = f" after {duration_s:.1f}s" if duration_s > 0 else ""
                event = NotificationEvent(
                    title="Agent Task Failed",
                    body=f"Task '{clean_id}' failed{dur_str}.",
                    level=NotificationLevel.ERROR.value,
                    channel=NotificationChannel.TOAST.value,
                    dedupe_key=f"task:{clean_id}",
                    metadata=meta,
                )

            if event:
                self._record_history(event)
            return event

    def evaluate_quota_alert(
        self,
        percentage: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[NotificationEvent]:
        """
        Evaluates whether current quota percentage warrants a low-quota alert.
        Enforces a 15-minute cooldown between alerts.
        """
        with self._lock:
            now = time.monotonic()
            pct = float(percentage)

            if pct > self.warning_threshold:
                # Quota recovered above warning threshold
                self._last_alert_percentage = None
                return None

            # Cooldown check
            if now - self._last_low_quota_alert_time < self.low_quota_cooldown_s:
                return None

            self._last_low_quota_alert_time = now
            self._last_alert_percentage = pct

            level = NotificationLevel.WARNING.value if pct > self.critical_threshold else NotificationLevel.ERROR.value
            meta = dict(metadata or {})
            meta.update({"percentage": pct, "warning_threshold": self.warning_threshold})

            event = NotificationEvent(
                title="Low Quota Warning",
                body=f"Antigravity quota is running low ({pct:.1f}% remaining).",
                level=level,
                channel=NotificationChannel.TOAST.value,
                dedupe_key=f"quota_alert_{int(pct)}",
                metadata=meta,
            )
            self._record_history(event)
            return event

    def create_custom_notification(
        self,
        title: str,
        body: str,
        level: str = "info",
        channel: str = "toast",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NotificationEvent:
        """Create and record an ad-hoc notification event."""
        with self._lock:
            event = NotificationEvent(
                title=title,
                body=body,
                level=level,
                channel=channel,
                metadata=metadata or {},
            )
            self._record_history(event)
            return event

    def _record_history(self, event: NotificationEvent):
        """Append to in-memory notification history, trimming to max_history."""
        self._history.append(event)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent notification history."""
        with self._lock:
            return [ev.to_dict() for ev in reversed(self._history[-limit:])]

    def clear_history(self):
        """Clear notification history."""
        with self._lock:
            self._history.clear()
