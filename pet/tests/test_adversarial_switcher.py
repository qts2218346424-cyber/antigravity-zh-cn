"""
tests/test_adversarial_switcher.py - Adversarial Stress & Chaos Test Suite
Target: pet_engine.switcher (AccountSwitcher, FileLock, _atomic_write_json)

Tests:
1. Multi-threaded & Multi-process rapid concurrent profile switching
2. Fault injection: disk failure, process crash during staging write, rollback validation
3. Windows NTFS file locking (PermissionError/SharingViolation), retry backoff, and cleanup
4. Backup rotation stress: exactly 10 backups retained after 20 swaps
"""

from __future__ import annotations

import os
import sys
import time
import json
import sqlite3
import tempfile
import unittest
import threading
import multiprocessing
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pet_engine.models import AccountProfile, TokenInfo
from pet_engine.switcher import AccountSwitcher, FileLock


class AdversarialSandbox:
    """Isolated environment for adversarial chaos testing."""
    def __init__(self):
        self._td: Optional[tempfile.TemporaryDirectory] = None
        self.root: Optional[Path] = None
        self.gemini_dir: Optional[Path] = None
        self.vscdb_path: Optional[Path] = None
        self.switcher: Optional[AccountSwitcher] = None

    def __enter__(self) -> "AdversarialSandbox":
        self._td = tempfile.TemporaryDirectory(prefix="adv_sandbox_")
        self.root = Path(self._td.name)
        self.gemini_dir = self.root / ".gemini"
        self.gemini_dir.mkdir(parents=True, exist_ok=True)
        (self.gemini_dir / "profiles").mkdir(parents=True, exist_ok=True)
        (self.gemini_dir / "backups").mkdir(parents=True, exist_ok=True)

        self.vscdb_path = self.root / "state.vscdb"
        self._init_sqlite()

        self.switcher = AccountSwitcher(
            gemini_dir=self.gemini_dir,
            vscdb_path=self.vscdb_path,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._td:
            try:
                self._td.cleanup()
            except Exception:
                pass

    def _init_sqlite(self):
        conn = sqlite3.connect(str(self.vscdb_path), timeout=5.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("CREATE TABLE IF NOT EXISTS ItemTable (key TEXT PRIMARY KEY, value TEXT);")
            conn.commit()
        finally:
            conn.close()

    def add_sample_profile(self, pid: str, email: str, label: str) -> AccountProfile:
        prof = AccountProfile(
            id=pid,
            label=label,
            email=email,
            tokens=TokenInfo(access_token=f"token_{pid}"),
        )
        self.switcher.add_profile(prof)
        return prof


# Subprocess worker for multi-process stress test
def _subprocess_switcher_worker(gemini_dir_str: str, vscdb_path_str: str, profile_ids: List[str], iterations: int, result_queue: multiprocessing.Queue):
    try:
        switcher = AccountSwitcher(
            gemini_dir=Path(gemini_dir_str),
            vscdb_path=Path(vscdb_path_str),
        )
        successes = 0
        errors = []
        for i in range(iterations):
            target = profile_ids[i % len(profile_ids)]
            try:
                res = switcher.switch_profile(target, create_backup=True)
                if res.get("success"):
                    successes += 1
            except Exception as e:
                errors.append(f"Switch to {target} failed: {e}")
            time.sleep(0.01)
        result_queue.put({"successes": successes, "errors": errors})
    except Exception as ex:
        result_queue.put({"successes": 0, "errors": [f"Worker crashed: {ex}"]})


class TestAdversarialSwitcher(unittest.TestCase):

    # =========================================================================
    # Task 1: Rapid Concurrent Profile Switches (Threads & Processes)
    # =========================================================================

    def test_concurrent_switches_multi_threaded(self):
        """Stress Test: 10 threads executing 50 concurrent profile switches."""
        with AdversarialSandbox() as sandbox:
            sandbox.add_sample_profile("p_alpha", "alpha@corp.com", "Alpha")
            sandbox.add_sample_profile("p_beta", "beta@corp.com", "Beta")
            sandbox.add_sample_profile("p_gamma", "gamma@corp.com", "Gamma")
            sandbox.switcher.switch_profile("p_alpha")

            profiles = ["p_alpha", "p_beta", "p_gamma"]
            errors = []
            completed = []

            def worker(thread_idx: int):
                for i in range(5):
                    target = profiles[(thread_idx + i) % 3]
                    try:
                        res = sandbox.switcher.switch_profile(target, create_backup=True)
                        if res.get("success"):
                            completed.append(target)
                    except Exception as e:
                        errors.append(f"Thread {thread_idx} err: {e}")
                    time.sleep(0.005)

            threads = [threading.Thread(target=worker, args=(t,)) for t in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=15.0)

            # In thread-safe mode with RLock, all operations must succeed without data corruption
            self.assertEqual(len(errors), 0, f"Encountered concurrency errors: {errors}")
            self.assertEqual(len(completed), 50)

            # Verify consistency of final active profile
            active = sandbox.switcher.get_active_profile()
            self.assertIsNotNone(active)
            self.assertIn(active.id, profiles)

            # Verify active_profile.json is valid JSON
            active_file = sandbox.gemini_dir / "active_profile.json"
            self.assertTrue(active_file.exists())
            with open(active_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertEqual(data.get("active_profile_id"), active.id)

            # Verify google_accounts.json matches active email
            ga_file = sandbox.gemini_dir / "google_accounts.json"
            self.assertTrue(ga_file.exists())
            with open(ga_file, "r", encoding="utf-8") as f:
                ga_data = json.load(f)
                self.assertEqual(ga_data.get("active"), active.email)

            # Verify no orphan temporary staging files remain
            tmp_files = list(sandbox.gemini_dir.glob("*.tmp.*"))
            self.assertEqual(len(tmp_files), 0, f"Found leaked tmp files: {tmp_files}")

    def test_concurrent_switches_multi_process(self):
        """Stress Test: 4 parallel OS processes contending for profile switch with FileLock."""
        with AdversarialSandbox() as sandbox:
            sandbox.add_sample_profile("p_x", "x@corp.com", "X")
            sandbox.add_sample_profile("p_y", "y@corp.com", "Y")
            sandbox.add_sample_profile("p_z", "z@corp.com", "Z")
            sandbox.switcher.switch_profile("p_x")

            profiles = ["p_x", "p_y", "p_z"]
            q = multiprocessing.Queue()
            processes = []

            for p_idx in range(4):
                p = multiprocessing.Process(
                    target=_subprocess_switcher_worker,
                    args=(str(sandbox.gemini_dir), str(sandbox.vscdb_path), profiles, 5, q),
                )
                processes.append(p)
                p.start()

            for p in processes:
                p.join(timeout=30.0)

            total_success = 0
            all_errors = []
            while not q.empty():
                res = q.get()
                total_success += res["successes"]
                all_errors.extend(res["errors"])

            # Verify state consistency
            self.assertGreater(total_success, 0, "At least some switches must succeed")
            active = sandbox.switcher.get_active_profile()
            self.assertIsNotNone(active)
            self.assertIn(active.id, profiles)

            # Check that files are not corrupted
            ga_data = json.loads((sandbox.gemini_dir / "google_accounts.json").read_text(encoding="utf-8"))
            self.assertEqual(ga_data.get("active"), active.email)

    # =========================================================================
    # Task 2: Fault Injection & Rollback Resilience
    # =========================================================================

    def test_staging_write_fault_injection_and_clean_rollback(self):
        """Fault Injection: Inject disk failure during staging write, verify complete rollback."""
        with AdversarialSandbox() as sandbox:
            sandbox.add_sample_profile("p_initial", "initial@test.com", "Initial Profile")
            sandbox.add_sample_profile("p_corrupt_target", "corrupt@test.com", "Corrupt Target")
            sandbox.switcher.switch_profile("p_initial")

            # Verify initial state
            init_active = sandbox.switcher.get_active_profile()
            self.assertEqual(init_active.id, "p_initial")
            init_ga = json.loads((sandbox.gemini_dir / "google_accounts.json").read_text(encoding="utf-8"))
            self.assertEqual(init_ga["active"], "initial@test.com")

            # Inject simulated disk write failure on active_profile.json during the swap
            original_atomic_write = AccountSwitcher._atomic_write_json
            fault_triggered = [False]

            def faulty_atomic_write(file_path: Path, data: Any, max_retries: int = 3):
                if file_path.name == "active_profile.json" and not fault_triggered[0]:
                    fault_triggered[0] = True
                    raise OSError("SIMULATED_DISK_WRITE_FAILURE: Disk I/O error or power loss")
                return original_atomic_write(file_path, data, max_retries)

            AccountSwitcher._atomic_write_json = staticmethod(faulty_atomic_write)
            try:
                t0 = time.time()
                with self.assertRaises(RuntimeError) as cm:
                    sandbox.switcher.switch_profile("p_corrupt_target")
                elapsed = time.time() - t0

                # Verify exception message indicates rollback
                self.assertIn("rolled back", str(cm.exception))

                # Verify rollback restored active_profile
                rolled_back_active = sandbox.switcher.get_active_profile()
                self.assertIsNotNone(rolled_back_active)
                self.assertEqual(rolled_back_active.id, "p_initial")

                # Verify rollback restored google_accounts.json
                restored_ga = json.loads((sandbox.gemini_dir / "google_accounts.json").read_text(encoding="utf-8"))
                self.assertEqual(restored_ga["active"], "initial@test.com")

                # Record rollback latency
                print(f"\n[EMPIRICAL METRIC] Rollback latency with FileLock contention: {elapsed:.2f}s")
            finally:
                AccountSwitcher._atomic_write_json = staticmethod(original_atomic_write)

    def test_sqlite_failure_injection_and_clean_rollback(self):
        """Fault Injection: SQLite database locked or corrupted during switch triggers rollback."""
        with AdversarialSandbox() as sandbox:
            sandbox.add_sample_profile("p_sql1", "sql1@test.com", "SQL1")
            sandbox.add_sample_profile("p_sql2", "sql2@test.com", "SQL2")
            sandbox.switcher.switch_profile("p_sql1")

            # Corrupt the SQLite database schema so INSERT fails
            conn = sqlite3.connect(str(sandbox.vscdb_path))
            conn.execute("DROP TABLE ItemTable;")
            conn.close()

            with self.assertRaises(RuntimeError) as cm:
                sandbox.switcher.switch_profile("p_sql2")

            self.assertIn("rolled back", str(cm.exception))

            # google_accounts.json must be rolled back to sql1
            ga_data = json.loads((sandbox.gemini_dir / "google_accounts.json").read_text(encoding="utf-8"))
            self.assertEqual(ga_data["active"], "sql1@test.com")

    def test_stale_lock_recovery(self):
        """Resilience: Stale lock file (>30s) automatically broken and recovered."""
        with AdversarialSandbox() as sandbox:
            lock_path = sandbox.gemini_dir / ".switcher.lock"
            lock_path.write_text("999999", encoding="utf-8")

            # Set mtime to 40 seconds in the past
            past_time = time.time() - 40.0
            os.utime(lock_path, (past_time, past_time))

            # Attempting to acquire lock should break stale lock
            t0 = time.time()
            with FileLock(lock_path, timeout=2.0) as fl:
                self.assertIsNotNone(fl.fd)
            elapsed = time.time() - t0
            self.assertLess(elapsed, 1.0, f"Stale lock took too long: {elapsed:.2f}s")

    # =========================================================================
    # Task 3: Windows NTFS File Locking & Retry Loops
    # =========================================================================

    def test_transient_locked_file_retry_success(self):
        """NTFS Lock: Transient file lock (50ms) is successfully retried and resolved."""
        with AdversarialSandbox() as sandbox:
            test_file = sandbox.gemini_dir / "test_retry.json"
            test_file.write_text('{"init": true}', encoding="utf-8")

            # Hold lock for 60ms in another thread
            def transient_locker():
                try:
                    with open(test_file, "r+b") as f:
                        time.sleep(0.06)
                except Exception:
                    pass

            locker_thread = threading.Thread(target=transient_locker)
            locker_thread.start()

            # Attempt atomic write with retry backoff
            time.sleep(0.01)
            AccountSwitcher._atomic_write_json(test_file, {"updated": True}, max_retries=5)
            locker_thread.join()

            # Verify file contains updated content
            data = json.loads(test_file.read_text(encoding="utf-8"))
            self.assertEqual(data.get("updated"), True)

    def test_persistent_locked_file_aborts_without_leaking_tmp(self):
        """NTFS Lock: Persistent locked file raises PermissionError and cleans up staging files."""
        with AdversarialSandbox() as sandbox:
            test_file = sandbox.gemini_dir / "locked_file.json"
            test_file.write_text('{"locked": true}', encoding="utf-8")

            # Open exclusively without sharing (exclusive on Windows)
            with open(test_file, "r+b") as locked_f:
                # Mock os.replace to simulate PermissionError
                orig_replace = os.replace
                replace_called = [0]

                def mock_replace(src, dst):
                    replace_called[0] += 1
                    raise PermissionError("[WinError 32] The process cannot access the file because it is being used by another process")

                os.replace = mock_replace
                try:
                    with self.assertRaises(PermissionError):
                        AccountSwitcher._atomic_write_json(test_file, {"new": 1}, max_retries=3)
                finally:
                    os.replace = orig_replace

                self.assertEqual(replace_called[0], 3, "Retry loop should attempt exactly max_retries=3")

            # Verify no temporary files leaked
            tmp_files = list(sandbox.gemini_dir.glob("*.tmp.*"))
            self.assertEqual(len(tmp_files), 0, f"Leaked tmp files: {tmp_files}")

    # =========================================================================
    # Task 4: Backup Rotation Stress Test (20 swaps -> exactly 10 backups)
    # =========================================================================

    def test_backup_rotation_20_swaps_retains_exactly_10(self):
        """Rotation Stress: Exactly 10 backups retained when 20 profile switches are performed."""
        with AdversarialSandbox() as sandbox:
            # Create two profiles to alternate between
            sandbox.add_sample_profile("prof_a", "a@test.com", "A")
            sandbox.add_sample_profile("prof_b", "b@test.com", "B")
            sandbox.switcher.switch_profile("prof_a", create_backup=False)

            # Perform 20 switches alternating between prof_a and prof_b
            for i in range(20):
                target = "prof_b" if i % 2 == 0 else "prof_a"
                res = sandbox.switcher.switch_profile(target, create_backup=True)
                self.assertTrue(res.get("success"))

            # Inspect ~/.gemini/backups/
            backups = sandbox.switcher.list_backups()
            backup_dirs = [b for b in (sandbox.gemini_dir / "backups").iterdir() if b.is_dir()]

            print(f"\n[EMPIRICAL METRIC] Backup directory count after 20 swaps: {len(backup_dirs)}")
            print(f"[EMPIRICAL METRIC] list_backups() count: {len(backups)}")

            # Assert retention limit is strictly 10
            self.assertEqual(
                len(backup_dirs),
                10,
                f"Expected exactly 10 backups retained, found {len(backup_dirs)}"
            )
            self.assertEqual(len(backups), 10)

            # Verify each retained backup has valid meta.json and files
            for b_dir in backup_dirs:
                meta_file = b_dir / "meta.json"
                self.assertTrue(meta_file.exists(), f"Backup missing meta.json: {b_dir}")
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                self.assertIn("backup_id", meta)
                self.assertIn("checksum", meta)
                self.assertIn("files", meta)
                self.assertGreater(meta["size_bytes"], 0)

    def test_rapid_burst_backup_creation_retention(self):
        """Rotation Stress: Rapid consecutive backup creation retains exactly 10 snapshots."""
        with AdversarialSandbox() as sandbox:
            sandbox.add_sample_profile("p_burst", "burst@test.com", "Burst")
            sandbox.switcher.switch_profile("p_burst", create_backup=False)

            # Create 25 backups in rapid succession
            for i in range(25):
                sandbox.switcher.create_backup(reason=f"burst_{i}")
                time.sleep(0.002)

            backup_dirs = [b for b in (sandbox.gemini_dir / "backups").iterdir() if b.is_dir()]
            self.assertEqual(
                len(backup_dirs),
                10,
                f"Expected exactly 10 backups after rapid burst, found {len(backup_dirs)}"
            )

    def test_filelock_nested_reentrancy_latency_penalty(self):
        """Concurrency Bug: Nested FileLock in switch_profile->restore_backup causes ~5.0s self-deadlock."""
        with AdversarialSandbox() as sandbox:
            sandbox.add_sample_profile("p_lat1", "lat1@test.com", "Lat1")
            sandbox.add_sample_profile("p_lat2", "lat2@test.com", "Lat2")
            sandbox.switcher.switch_profile("p_lat1", create_backup=False)

            # 1. Standalone restore latency (lock is free)
            b_dir = sandbox.switcher.create_backup("baseline")
            t0 = time.time()
            ok = sandbox.switcher.restore_backup(b_dir.name)
            standalone_latency = time.time() - t0
            self.assertTrue(ok)
            self.assertLess(standalone_latency, 0.5, f"Standalone restore took too long: {standalone_latency:.3f}s")

            # 2. Rollback latency inside switch_profile (lock is held by caller)
            fault_triggered = [False]
            orig_write = AccountSwitcher._atomic_write_json

            def faulty_write(fpath, data, max_retries=3):
                if fpath.name == "active_profile.json" and not fault_triggered[0]:
                    fault_triggered[0] = True
                    raise OSError("FORCED_ERROR_FOR_LATENCY_TEST")
                return orig_write(fpath, data, max_retries)

            AccountSwitcher._atomic_write_json = staticmethod(faulty_write)
            try:
                t1 = time.time()
                with self.assertRaises(RuntimeError):
                    sandbox.switcher.switch_profile("p_lat2")
                rollback_latency = time.time() - t1
            finally:
                AccountSwitcher._atomic_write_json = staticmethod(orig_write)

            print(f"\n[LATENCY COMPARISON] Standalone restore: {standalone_latency:.4f}s vs Switcher Rollback: {rollback_latency:.4f}s")
            # Rollback without FileLock deadlock completes instantaneously (<0.2s)
            self.assertLess(
                rollback_latency,
                0.2,
                f"Expected <0.2s rollback without FileLock reentrancy delay, got {rollback_latency:.2f}s"
            )

    def test_backup_id_millisecond_lexicographical_sorting_anomaly(self):
        """Chronological Pruning: Sort key inspects meta.json timestamp to retain newest backups."""
        with AdversarialSandbox() as sandbox:
            # Simulate backup directories created within the same second:
            # One at 99ms (suffix '99'), one at 1002ms (suffix '1002')
            b_dir1 = sandbox.gemini_dir / "backups" / "backup_20260924_120000_99"
            b_dir2 = sandbox.gemini_dir / "backups" / "backup_20260924_120000_1002"
            b_dir1.mkdir(parents=True, exist_ok=True)
            b_dir2.mkdir(parents=True, exist_ok=True)
            (b_dir1 / "meta.json").write_text(json.dumps({"backup_id": b_dir1.name, "timestamp": "2026-09-24T12:00:00.099Z"}), encoding="utf-8")
            (b_dir2 / "meta.json").write_text(json.dumps({"backup_id": b_dir2.name, "timestamp": "2026-09-24T12:00:01.002Z"}), encoding="utf-8")

            # Prune with max_keep=1
            sandbox.switcher._prune_backups(max_keep=1)

            # Chronological sort correctly retains the NEWER backup (b_dir2) and prunes the OLDER backup (b_dir1)
            surviving = [b.name for b in (sandbox.gemini_dir / "backups").iterdir() if b.is_dir()]
            print(f"\n[SORT ACCURACY RESULT] Surviving backup after pruning: {surviving}")
            self.assertIn(b_dir2.name, surviving, "Chronological sort must retain the newer backup")
            self.assertNotIn(b_dir1.name, surviving, "Chronological sort must prune the older backup")


if __name__ == "__main__":
    unittest.main(verbosity=2)

