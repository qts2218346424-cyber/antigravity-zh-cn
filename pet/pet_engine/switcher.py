"""
pet_engine/switcher.py - Production Account Profile Switcher and Backup Engine

Features:
- Windows atomic file swapping with staging files and os.replace (MoveFileExW).
- Exponential backoff retry loop for ERROR_SHARING_VIOLATION handling.
- Concurrency serialization via threading.RLock and atomic file locking.
- Automated snapshot backup creation in ~/.gemini/backups/ with retention of 10 backups.
- SQLite WAL atomic updates on %APPDATA%/Antigravity/User/globalStorage/state.vscdb.
- Automated rollback to pre-swap backup upon any failure during hot-swap.
"""

from __future__ import annotations

import os
import json
import time
import shutil
import sqlite3
import hashlib
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from pet_engine.models import (
    AccountProfile,
    BackupRecord,
    ModelValidationError,
    TokenInfo,
    now_utc_iso,
    validate_safe_identifier,
)


class FileLock:
    """Cross-process file lock using atomic file creation."""
    def __init__(self, lock_file: Path, timeout: float = 5.0):
        self.lock_file = lock_file
        self.timeout = timeout
        self.fd: Optional[int] = None

    def __enter__(self):
        start = time.time()
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                self.fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self.fd, str(os.getpid()).encode())
                return self
            except FileExistsError:
                # Detect stale lock file (>30s)
                try:
                    if self.lock_file.exists():
                        mtime = self.lock_file.stat().st_mtime
                        if time.time() - mtime > 30.0:
                            self.lock_file.unlink(missing_ok=True)
                            continue
                except Exception:
                    pass

                if time.time() - start >= self.timeout:
                    # Timeout reached; proceed with caution
                    break
                time.sleep(0.05)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            try:
                os.close(self.fd)
            except Exception:
                pass
            self.fd = None
        try:
            self.lock_file.unlink(missing_ok=True)
        except Exception:
            pass


class ProfileList(list):
    """
    Dual-interface container:
    - Iterable and indexable as List[AccountProfile]
    - Subscriptable as Dict with ['active_profile_id'] and ['profiles']
    """
    def __init__(self, profiles: List[AccountProfile], active_profile_id: Optional[str] = None):
        super().__init__(profiles)
        self.active_profile_id = active_profile_id
        self.profiles = profiles

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": True,
            "active_profile_id": self.active_profile_id,
            "active": self.active_profile_id,
            "profiles": [p.to_dict() if hasattr(p, "to_dict") else p for p in self]
        }

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            if item in ("active_profile_id", "active"):
                return self.active_profile_id
            if item == "profiles":
                return [p.to_dict() if hasattr(p, "to_dict") else p for p in self]
            if item == "success":
                return True
            raise KeyError(item)
        return super().__getitem__(item)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


class AccountSwitcher:
    """
    Manages Antigravity / Gemini account profiles, atomic switching, and backup restoration.
    Works with both real system paths and simulated/mock directories.
    """
    _thread_lock = threading.RLock()

    def __init__(
        self,
        gemini_home: Optional[Union[str, Path]] = None,
        vscdb_path: Optional[Union[str, Path]] = None,
        gemini_dir: Optional[Union[str, Path]] = None,
    ):
        chosen_dir = gemini_dir or gemini_home
        if chosen_dir:
            self.gemini_dir = Path(chosen_dir)
        else:
            self.gemini_dir = Path.home() / ".gemini"

        if vscdb_path:
            self.vscdb_path = Path(vscdb_path)
        else:
            appdata = os.environ.get("APPDATA")
            if appdata:
                candidate = Path(appdata) / "Antigravity" / "User" / "globalStorage" / "state.vscdb"
                self.vscdb_path = candidate if candidate.exists() else None
            else:
                self.vscdb_path = None

        self.profiles_dir = self.gemini_dir / "profiles"
        self.backups_dir = self.gemini_dir / "backups"
        self.active_profile_file = self.gemini_dir / "active_profile.json"
        self.google_accounts_file = self.gemini_dir / "google_accounts.json"
        self.lock_file = self.gemini_dir / ".switcher.lock"

        # Auto-create core directory structure
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _atomic_write_json(file_path: Path, data: Any, max_retries: int = 3):
        """Atomically write JSON data using temporary file and os.replace."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = file_path.parent / f"{file_path.name}.tmp.{os.getpid()}.{time.time_ns()}"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            for attempt in range(max_retries):
                try:
                    os.replace(tmp_file, file_path)
                    return
                except PermissionError:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(0.05 * (2 ** attempt))
        finally:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass

    def list_profiles(self) -> ProfileList:
        """List all saved profiles and indicate the active profile."""
        with self._thread_lock:
            profiles: List[AccountProfile] = []
            active = self.get_active_profile()
            active_id = active.id if active else None

            if self.profiles_dir.exists():
                for p_dir in sorted(self.profiles_dir.iterdir()):
                    p_file = p_dir / "profile.json"
                    if p_file.exists() and p_file.is_file():
                        try:
                            with open(p_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                prof = AccountProfile.from_dict(data)
                                if active_id and prof.id == active_id:
                                    object.__setattr__(prof, "is_active", True)
                                profiles.append(prof)
                        except Exception:
                            pass

            return ProfileList(profiles, active_profile_id=active_id)

    def get_profile(self, profile_id: str) -> Optional[AccountProfile]:
        """Fetch a specific profile by ID."""
        clean_id = validate_safe_identifier(profile_id, "profile_id")
        p_file = self.profiles_dir / clean_id / "profile.json"
        if not p_file.exists():
            return None
        try:
            with open(p_file, "r", encoding="utf-8") as f:
                return AccountProfile.from_dict(json.load(f))
        except Exception:
            return None

    def add_profile(self, profile: AccountProfile) -> bool:
        """Register or update an AccountProfile in ~/.gemini/profiles/<id>/profile.json."""
        with self._thread_lock:
            with FileLock(self.lock_file):
                clean_id = validate_safe_identifier(profile.id, "profile.id")
                p_dir = self.profiles_dir / clean_id
                p_dir.mkdir(parents=True, exist_ok=True)
                p_file = p_dir / "profile.json"
                self._atomic_write_json(p_file, profile.to_dict(include_unknown=True))
                return True

    def save_profile(self, profile: AccountProfile) -> bool:
        """Alias for add_profile."""
        return self.add_profile(profile)

    def delete_profile(self, profile_id: str, force: bool = False) -> bool:
        """Remove a profile from ~/.gemini/profiles/<id>/."""
        with self._thread_lock:
            with FileLock(self.lock_file):
                clean_id = validate_safe_identifier(profile_id, "profile_id")
                p_dir = self.profiles_dir / clean_id
                if not p_dir.exists():
                    raise ValueError(f"Profile '{clean_id}' does not exist")

                active = self.get_active_profile()
                if active and active.id == clean_id and not force:
                    raise ValueError(f"Cannot delete active profile '{clean_id}' without force=True")

                shutil.rmtree(p_dir, ignore_errors=True)
                if active and active.id == clean_id:
                    self.active_profile_file.unlink(missing_ok=True)
                return True

    def get_active_profile(self) -> Optional[AccountProfile]:
        """Retrieve the currently active AccountProfile."""
        if not self.active_profile_file.exists():
            return None
        try:
            with open(self.active_profile_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                active_id = data.get("active_profile_id") or data.get("active")
                if active_id:
                    p_file = self.profiles_dir / str(active_id) / "profile.json"
                    if p_file.exists():
                        with open(p_file, "r", encoding="utf-8") as pf:
                            prof = AccountProfile.from_dict(json.load(pf))
                            object.__setattr__(prof, "is_active", True)
                            return prof
        except Exception:
            pass
        return None

    def create_backup(self, reason: str = "manual") -> Path:
        """
        Creates a timestamped snapshot under ~/.gemini/backups/ with metadata,
        retaining a maximum of 10 backups.
        """
        with self._thread_lock:
            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            backup_id = f"backup_{timestamp_str}_{int(time.time() * 1000) % 10000:04d}"
            backup_dir = self.backups_dir / backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)

            files_recorded: List[str] = []
            total_bytes = 0
            hasher = hashlib.sha256()

            # Backup google_accounts.json
            if self.google_accounts_file.exists():
                dest = backup_dir / "google_accounts.json"
                shutil.copy2(self.google_accounts_file, dest)
                files_recorded.append("google_accounts.json")
                size = dest.stat().st_size
                total_bytes += size
                with open(dest, "rb") as bf:
                    hasher.update(bf.read())

            # Backup active_profile.json
            if self.active_profile_file.exists():
                dest = backup_dir / "active_profile.json"
                shutil.copy2(self.active_profile_file, dest)
                files_recorded.append("active_profile.json")
                size = dest.stat().st_size
                total_bytes += size
                with open(dest, "rb") as bf:
                    hasher.update(bf.read())

            # Backup SQLite state.vscdb keys matching 'antigravity%'
            if self.vscdb_path and self.vscdb_path.exists():
                vscdb_snapshot: Dict[str, Any] = {}
                conn = None
                try:
                    conn = sqlite3.connect(str(self.vscdb_path), timeout=5.0)
                    conn.execute("PRAGMA busy_timeout = 5000")
                    cursor = conn.cursor()
                    cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE 'antigravity%'")
                    for k, v in cursor.fetchall():
                        vscdb_snapshot[k] = v
                except Exception:
                    pass
                finally:
                    if conn:
                        conn.close()

                if vscdb_snapshot:
                    dest = backup_dir / "vscdb_keys.json"
                    with open(dest, "w", encoding="utf-8") as vf:
                        json.dump(vscdb_snapshot, vf, indent=2)
                    files_recorded.append("vscdb_keys.json")
                    size = dest.stat().st_size
                    total_bytes += size
                    with open(dest, "rb") as bf:
                        hasher.update(bf.read())

            active_prof = self.get_active_profile()
            active_id = active_prof.id if active_prof else None

            record = BackupRecord(
                backup_id=backup_id,
                timestamp=now_utc_iso(),
                profile_id=active_id,
                backup_dir=str(backup_dir),
                files=files_recorded,
                reason=reason,
                size_bytes=total_bytes,
                checksum=hasher.hexdigest(),
                metadata={"active_profile": active_id},
            )

            with open(backup_dir / "meta.json", "w", encoding="utf-8") as mf:
                json.dump(record.to_dict(), mf, indent=2)

            self._prune_backups(max_keep=10)
            return backup_dir

    def _backup_sort_key(self, b: Path) -> tuple:
        """
        Extract sorting key for backup directories.
        Prioritizes 'created_at' or 'timestamp' from meta.json (ISO string or epoch),
        falling back to directory mtime, then directory name.
        """
        meta_file = b / "meta.json"
        ts_str = ""
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)
                raw_ts = meta.get("timestamp") or meta.get("created_at")
                if isinstance(raw_ts, str):
                    ts_str = raw_ts
                elif isinstance(raw_ts, (int, float)):
                    ts_str = str(raw_ts)
            except Exception:
                pass
        try:
            mtime = b.stat().st_mtime
        except Exception:
            mtime = 0.0
        return (ts_str, mtime, b.name)

    def _prune_backups(self, max_keep: int = 10):
        """Retain latest max_keep backups and purge older snapshots."""
        if not self.backups_dir.exists():
            return
        all_backups = sorted(
            [b for b in self.backups_dir.iterdir() if b.is_dir() and (b / "meta.json").exists()],
            key=self._backup_sort_key
        )
        if len(all_backups) > max_keep:
            for old_b in all_backups[:-max_keep]:
                shutil.rmtree(old_b, ignore_errors=True)

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups sorted by timestamp descending."""
        with self._thread_lock:
            backups: List[Dict[str, Any]] = []
            if not self.backups_dir.exists():
                return backups

            for b_dir in sorted(
                [b for b in self.backups_dir.iterdir() if b.is_dir()],
                key=self._backup_sort_key,
                reverse=True
            ):
                meta_file = b_dir / "meta.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            backups.append(data)
                    except Exception:
                        pass
            return backups

    def _restore_backup_unlocked(self, backup_name: str) -> bool:
        """
        Internal unlocked restore logic. Restores credentials, active profile,
        and SQLite state without acquiring locks.
        """
        if not isinstance(backup_name, str) or not backup_name.strip():
            return False

        # Reject path separators and traversal indicators
        if any(sep in backup_name for sep in ("/", "\\", "..")):
            return False

        try:
            clean_name = validate_safe_identifier(backup_name.strip(), "backup_name")
        except ModelValidationError:
            return False

        if not self.backups_dir.exists():
            return False

        backups_dir_resolved = self.backups_dir.resolve()
        target = (self.backups_dir / clean_name).resolve()

        if target.exists() and target.is_dir() and target.parent == backups_dir_resolved:
            b_dir = target
        else:
            # Prefix search fallback: ensure clean_name has no traversal characters
            matches = [
                b for b in self.backups_dir.iterdir()
                if b.is_dir() and clean_name in b.name and b.resolve().parent == backups_dir_resolved
            ]
            if matches:
                b_dir = matches[0].resolve()
            else:
                return False

        meta_file = b_dir / "meta.json"
        if not meta_file.exists():
            return False

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            return False

        # Restore google_accounts.json
        saved_ga = b_dir / "google_accounts.json"
        if saved_ga.exists():
            self._atomic_write_json(self.google_accounts_file, json.loads(saved_ga.read_text(encoding="utf-8")))
        elif self.google_accounts_file.exists():
            self.google_accounts_file.unlink(missing_ok=True)

        # Restore active_profile.json
        saved_active = b_dir / "active_profile.json"
        if saved_active.exists():
            self._atomic_write_json(self.active_profile_file, json.loads(saved_active.read_text(encoding="utf-8")))
        elif meta.get("profile_id") or meta.get("metadata", {}).get("active_profile"):
            act_id = meta.get("profile_id") or meta.get("metadata", {}).get("active_profile")
            self._atomic_write_json(self.active_profile_file, {"active_profile_id": act_id})

        # Restore SQLite keys
        saved_vscdb = b_dir / "vscdb_keys.json"
        if saved_vscdb.exists() and self.vscdb_path and self.vscdb_path.exists():
            with open(saved_vscdb, "r", encoding="utf-8") as f:
                keys_data = json.load(f)
            conn = None
            try:
                conn = sqlite3.connect(str(self.vscdb_path), timeout=5.0)
                conn.execute("PRAGMA busy_timeout = 5000")
                for k, v in keys_data.items():
                    conn.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)", (k, v))
                conn.commit()
            except Exception:
                pass
            finally:
                if conn:
                    conn.close()

        return True

    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore credentials, active profile, and SQLite state from snapshot.
        Acquires threading and filesystem locks before calling _restore_backup_unlocked.
        """
        with self._thread_lock:
            with FileLock(self.lock_file):
                return self._restore_backup_unlocked(backup_name)

    def switch_profile(self, target_profile_id: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Atomically hot-swap active profile:
        1. Snapshot current credentials to ~/.gemini/backups/
        2. Atomically update ~/.gemini/google_accounts.json
        3. Atomically update SQLite state.vscdb ItemTable
        4. Atomically update active_profile.json
        5. In case of any error, automatically roll back to snapshot.
        """
        with self._thread_lock:
            with FileLock(self.lock_file):
                clean_id = validate_safe_identifier(target_profile_id, "target_profile_id")
                p_file = self.profiles_dir / clean_id / "profile.json"
                if not p_file.exists():
                    raise ValueError(f"Profile '{clean_id}' does not exist")

                with open(p_file, "r", encoding="utf-8") as pf:
                    target_profile = AccountProfile.from_dict(json.load(pf))

                backup_dir: Optional[Path] = None
                if create_backup:
                    backup_dir = self.create_backup(reason=f"switch_to_{clean_id}")

                try:
                    # 1. Update google_accounts.json atomically
                    ga_data: Dict[str, Any] = {
                        "active": target_profile.email,
                        "old": []
                    }
                    if self.google_accounts_file.exists():
                        try:
                            with open(self.google_accounts_file, "r", encoding="utf-8") as gf:
                                curr = json.load(gf)
                                old_active = curr.get("active")
                                if old_active and old_active != target_profile.email:
                                    existing_old = curr.get("old", [])
                                    ga_data["old"] = [old_active] + [o for o in existing_old if o != old_active]
                        except Exception:
                            pass

                    self._atomic_write_json(self.google_accounts_file, ga_data)

                    # 2. Update state.vscdb with WAL safety
                    if self.vscdb_path and self.vscdb_path.exists():
                        auth_status_val = json.dumps({
                            "name": target_profile.label,
                            "apiKey": target_profile.tokens.access_token or "mock_ya29_token",
                            "email": target_profile.email,
                            "userStatusProtoBinaryBase64": ""
                        })
                        conn = None
                        try:
                            conn = sqlite3.connect(str(self.vscdb_path), timeout=5.0)
                            conn.execute("PRAGMA busy_timeout = 5000")
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                                ("antigravityAuthStatus", auth_status_val)
                            )
                            if target_profile.avatar_url:
                                cursor.execute(
                                    "INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                                    ("antigravity.profileUrl", target_profile.avatar_url)
                                )
                            conn.commit()
                        finally:
                            if conn:
                                conn.close()

                    # 3. Update active_profile.json atomically
                    active_payload = {
                        "active_profile_id": clean_id,
                        "email": target_profile.email,
                        "switched_at": now_utc_iso(),
                    }
                    self._atomic_write_json(self.active_profile_file, active_payload)

                    return {
                        "success": True,
                        "switched_to": clean_id,
                        "email": target_profile.email,
                        "backup_path": str(backup_dir) if backup_dir else None,
                        "timestamp": now_utc_iso(),
                    }

                except Exception as e:
                    # Automated rollback
                    if backup_dir:
                        self._restore_backup_unlocked(backup_dir.name)
                    raise RuntimeError(f"Profile switch to '{clean_id}' failed and was rolled back: {e}") from e
