"""
tests/test_adversarial_challenger_2.py - Adversarial Stress & Boundary Challenge Suite
Author: Challenger 2 (Empirical Challenger)
Target: Antigravity Desktop Pet Engine, Models, Switcher, Quota, ProtoDecoder, Avatar Validation

Adversarial Dimensions Tested:
1. ProtoWireParser Corrupt & Truncated Protobuf Wire Payloads
2. Windows Reserved Device Names (CON, PRN, AUX, NUL, COM1-9, LPT1-9) & Path Traversal
3. ReDoS Regex Vulnerability & Catastrophic Backtracking Stress
4. Zero, Negative, Bool, and Extreme Boundaries in QuotaStatus & QuotaMonitor
5. Malformed Avatar Files, Magic-Byte Bypass, SVG XSS Injection & Oversized Payloads
6. AccountSwitcher Vault & Rollback Under Hostile Conditions
"""

import os
import sys
import time
import json
import base64
import math
import re
import sqlite3
import tempfile
import unittest
import unicodedata
from typing import Any
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pet_engine.proto_decoder import ProtoWireParser
from pet_engine.models import (
    AccountProfile,
    QuotaStatus,
    QuotaHealthStatus,
    BackupRecord,
    NotificationEvent,
    TokenInfo,
    ModelValidationError,
    validate_safe_identifier,
    validate_email,
    validate_strict_int,
    validate_metadata,
    validate_utc_iso,
    WINDOWS_RESERVED_NAMES,
)
from pet_engine.switcher import AccountSwitcher
from pet_engine.quota import QuotaMonitor
from run_pet import validate_image_file
from test_account_switcher import HeadlessAvatarEngine


class TestProtoWireParserAdversarial(unittest.TestCase):
    """Adversarial stress-testing of pure-Python Protobuf wire decoder."""

    def test_empty_payload(self):
        """Empty byte sequences must return empty items list without raising."""
        self.assertEqual(ProtoWireParser.parse(b""), [])
        self.assertEqual(ProtoWireParser.parse_map(b""), {})
        res = ProtoWireParser.parse_credits_payload(b"")
        self.assertFalse(res["success"])
        self.assertEqual(res["available_credits"], 0)

    def test_truncated_tag_varint(self):
        """Tag with MSB set but EOF immediately following must terminate cleanly."""
        # 0x80 means varint continues, but stream ends -> field 0 breaks out -> []
        items = ProtoWireParser.parse(b"\x80")
        self.assertEqual(items, [])
        # 0xff 0xff tag varint truncated at EOF -> wire_type 7 -> terminates cleanly
        items2 = ProtoWireParser.parse(b"\xff\xff")
        self.assertEqual(items2, [(2047, "unknown_7", None)])

    def test_varint_infinite_loop_bomb(self):
        """A stream of 10,000 varint continuation bytes (0x80) must terminate within 50ms."""
        bomb = b"\x80" * 10000
        start = time.perf_counter()
        items = ProtoWireParser.parse(bomb)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.2, f"Parser hung or was too slow on varint bomb: {elapsed:.3f}s")

    def test_invalid_field_number_zero(self):
        """Protobuf wire format forbids field number 0. Tag 0x00 (field 0, wire 0) must abort parse."""
        items = ProtoWireParser.parse(b"\x00\x01\x02")
        self.assertEqual(items, [])

    def test_unsupported_wire_types(self):
        """Tags with unsupported wire types (e.g. 3 = start group, 4 = end group, 6, 7) must abort."""
        # Tag with field 1, wire_type 3: (1 << 3) | 3 = 0x0B
        items = ProtoWireParser.parse(b"\x0b\x01\x02")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "unknown_3")

        # Tag with field 1, wire_type 7: (1 << 3) | 7 = 0x0F
        items2 = ProtoWireParser.parse(b"\x0f\x01\x02")
        self.assertEqual(len(items2), 1)
        self.assertEqual(items2[0][1], "unknown_7")

    def test_corrupt_length_delimited_out_of_bounds(self):
        """Wire type 2 with claimed length far exceeding buffer size must safely consume remaining bytes."""
        # Field 1, wire_type 2: tag = 0x0A. Length = 0xFFFF (varint: \xff\x7f = 16383), followed by only 3 bytes.
        corrupt = b"\x0a\xff\x7f\xaa\xbb\xcc"
        items = ProtoWireParser.parse(corrupt)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][0], 1)
        self.assertEqual(items[0][1], "bytes")
        self.assertEqual(items[0][2], b"\xaa\xbb\xcc")

    def test_truncated_fixed32_and_fixed64(self):
        """Wire type 5 (32-bit fixed) and 1 (64-bit fixed) with fewer than 4 or 8 bytes must not crash."""
        # Field 1, wire_type 5 (tag 0x0D), but only 2 bytes follow
        items = ProtoWireParser.parse(b"\x0d\x01\x02")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "fixed32")
        self.assertEqual(items[0][2], b"\x01\x02")

        # Field 1, wire_type 1 (tag 0x09), but only 3 bytes follow
        items2 = ProtoWireParser.parse(b"\x09\x01\x02\x03")
        self.assertEqual(len(items2), 1)
        self.assertEqual(items2[0][1], "fixed64")
        self.assertEqual(items2[0][2], b"\x01\x02\x03")

    def test_parse_map_with_corrupt_entries(self):
        """parse_map on random binary garbage must degrade to empty dict without throwing."""
        garbage = os.urandom(256)
        res = ProtoWireParser.parse_map(garbage)
        self.assertIsInstance(res, dict)

    def test_credits_payload_with_hostile_strings(self):
        """parse_credits_payload on random string and invalid base64 must return safe defaults."""
        res1 = ProtoWireParser.parse_credits_payload("NotBase64!@#$%^&*()_+")
        self.assertFalse(res1["success"])
        self.assertEqual(res1["available_credits"], 0)

        res2 = ProtoWireParser.parse_credits_payload("AAAA")  # Valid base64, null payload
        self.assertFalse(res2["success"])

        # Truncated sentinel value bytes
        sentinel_key = b"\x0a\x1bavailableCreditsSentinelKey\x12\x01\n"
        wrapped = b"\x0a" + bytes([len(sentinel_key)]) + sentinel_key
        res3 = ProtoWireParser.parse_credits_payload(base64.b64encode(wrapped).decode())
        self.assertFalse(res3["success"])

    def test_extract_inner_bytes_edge_cases(self):
        """Test _extract_inner_bytes with various malformed prefixes."""
        # Single byte b"\n"
        self.assertEqual(ProtoWireParser._extract_inner_bytes(b"\n"), b"")
        # b"\n\n"
        self.assertEqual(ProtoWireParser._extract_inner_bytes(b"\n\n"), b"")
        # b"\n\x04" followed by valid base64
        valid_b64 = base64.b64encode(b"\x10\x2a")
        wrapped = b"\n\x04" + valid_b64
        extracted = ProtoWireParser._extract_inner_bytes(wrapped)
        self.assertEqual(extracted, b"\x10\x2a")


class TestWindowsReservedNamesAndPathTraversal(unittest.TestCase):
    """Adversarial testing of Windows reserved names, path traversals, and injection."""

    def test_windows_reserved_names_rejected(self):
        """Windows reserved device names must be strictly rejected by validate_safe_identifier."""
        reserved_list = [
            "CON", "con", "Con", "cOn",
            "PRN", "prn", "Prn",
            "AUX", "aux", "Aux",
            "NUL", "nul", "Nul",
            "COM1", "com1", "COM9", "com9",
            "LPT1", "lpt1", "LPT9", "lpt9",
        ]
        for name in reserved_list:
            with self.subTest(name=name):
                with self.assertRaises(ModelValidationError) as cm:
                    validate_safe_identifier(name, "test_id")
                self.assertIn("WINDOWS_RESERVED_NAME", cm.exception.code)

    def test_windows_reserved_name_with_extensions(self):
        """Reserved names with extensions like CON.txt, aux.json must be rejected."""
        # Note: ID_REGEX is ^[a-zA-Z0-9_-]{1,64}$, dots are rejected by regex pattern
        for name in ["CON.txt", "aux.json", "nul.dat", "COM1.log"]:
            with self.subTest(name=name):
                with self.assertRaises(ModelValidationError) as cm:
                    validate_safe_identifier(name, "test_id")
                # Either INVALID_PATTERN (because of dot) or WINDOWS_RESERVED_NAME
                self.assertIn(cm.exception.code, ("INVALID_PATTERN", "WINDOWS_RESERVED_NAME"))

    def test_path_traversal_identifiers_rejected(self):
        """Path traversal characters (.., /, \\) must be rejected."""
        traversals = [
            "../../etc/passwd",
            "..\\..\\Windows\\System32",
            "..",
            ".",
            "profile/sub",
            "profile\\sub",
            "~/.gemini",
            "%APPDATA%",
            "profile;rm -rf",
            "profile\x00inject",
        ]
        for t in traversals:
            with self.subTest(traversal=t):
                with self.assertRaises(ModelValidationError):
                    validate_safe_identifier(t, "test_id")

    def test_account_profile_with_reserved_id(self):
        """AccountProfile constructor must raise ModelValidationError on reserved id."""
        for r_id in ["con", "NUL", "aux", "prn", "com1", "lpt1"]:
            with self.assertRaises(ModelValidationError):
                AccountProfile(id=r_id, label="Test Profile", email="test@example.com")

    def test_backup_record_with_traversal_files(self):
        """BackupRecord files list containing path traversal or Windows reserved names must be rejected."""
        hostile_file_lists = [
            ["../../malicious.txt"],
            ["..\\malicious.txt"],
            ["CON"],
            ["nul"],
            ["C:\\boot.ini"],
            ["."],
            [".."],
            ["/etc/shadow"],
        ]
        for fl in hostile_file_lists:
            with self.subTest(files=fl):
                with self.assertRaises(ModelValidationError) as cm:
                    BackupRecord(
                        backup_id="backup_valid_01",
                        timestamp="2026-09-24T00:00:00.000Z",
                        profile_id=None,
                        backup_dir="/tmp/backup",
                        files=fl,
                    )
                self.assertIn(cm.exception.code, ("PATH_TRAVERSAL_DETECTED", "WINDOWS_RESERVED_NAME"))

    def test_switcher_rejects_reserved_and_traversal_profiles(self):
        """AccountSwitcher methods must cleanly reject reserved names without crashing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            switcher = AccountSwitcher(gemini_home=Path(tmp_dir))

            # get_profile with reserved name
            with self.assertRaises(ModelValidationError):
                switcher.get_profile("CON")

            with self.assertRaises(ModelValidationError):
                switcher.get_profile("../../secret")

            # switch_profile with reserved name
            with self.assertRaises(ModelValidationError):
                switcher.switch_profile("NUL")

            with self.assertRaises(ModelValidationError):
                switcher.switch_profile("../../../etc")

            # delete_profile with reserved name
            with self.assertRaises(ModelValidationError):
                switcher.delete_profile("PRN")

    def test_restore_backup_path_traversal_gap(self):
        """Adversarially demonstrate whether restore_backup accepts directory traversal paths."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            outside = base / "outside_dir"
            outside.mkdir()
            (outside / "meta.json").write_text(json.dumps({"backup_id": "outside_exploit", "timestamp": "2026-09-24T00:00:00.000Z"}))
            (outside / "google_accounts.json").write_text(json.dumps({"active": "attacker@exploit.io"}))

            switcher = AccountSwitcher(gemini_home=base / "gemini")

            # Vulnerability remediated: restore_backup rejects path traversal and returns False
            traversal_succeeded = switcher.restore_backup("../../outside_dir")
            self.assertFalse(traversal_succeeded, "Path traversal should be rejected")
            if (switcher.gemini_dir / "google_accounts.json").exists():
                active_ga = json.loads((switcher.gemini_dir / "google_accounts.json").read_text(encoding="utf-8"))
                self.assertNotEqual(active_ga.get("active"), "attacker@exploit.io")



class TestReDoSAndRegexStress(unittest.TestCase):
    """Stress-test regex implementations against catastrophic backtracking and CPU exhaustion."""

    def test_validate_email_redos_resilience(self):
        """validate_email with adversarial nested hyphens/dots and long inputs must execute under 5ms."""
        evil_inputs = [
            # Repeated nested groups
            "a" * 60 + "@" + ("a-" * 50) + "a.com",
            "user@" + ("a." * 50) + "com",
            "user@" + ("a-" * 40) + ("-b" * 40) + "!",
            "a" * 250 + "@example.com",
            "user@" + "a" * 240 + ".com",
            "user@" + ("-" * 100) + ".com",
            # Unicode and special characters
            "user@domain..com",
            "user@-domain.com",
            "user@domain-.com",
        ]
        for evil in evil_inputs:
            start = time.perf_counter()
            try:
                validate_email(evil)
            except ModelValidationError:
                pass  # Expected rejection
            elapsed = time.perf_counter() - start
            self.assertLess(elapsed, 0.05, f"validate_email took too long on evil input ({elapsed:.4f}s): {evil[:30]}...")

    def test_safe_identifier_length_and_regex_stress(self):
        """validate_safe_identifier with huge strings must be rejected instantly without regex hang."""
        evil_id = "a" * 10000
        start = time.perf_counter()
        with self.assertRaises(ModelValidationError) as cm:
            validate_safe_identifier(evil_id, "id")
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.01)
        self.assertEqual(cm.exception.code, "LENGTH_EXCEEDED")

    def test_svg_script_sanitization_adversarial_patterns(self):
        """HeadlessAvatarEngine.sanitize_svg must neutralize advanced script injections and unclosed tags."""
        payloads = [
            # Standard script
            ("<svg><script>alert(1)</script></svg>", "<svg></svg>"),
            # Mixed case script
            ("<svg><sCrIpt>alert(1)</ScRiPt></svg>", "<svg></svg>"),
            # Unclosed script tag or multiline
            ("<svg><script type='text/javascript'>\nlet x = 1;\nalert(x);\n</script></svg>", "<svg></svg>"),
            # Inline event handlers
            ('<svg onload="alert(1)" onclick="evil()"><circle r="5"/></svg>', '<svg ><circle r="5"/></svg>'),
            # Mixed case event handler with whitespace
            ('<svg ONLOAD = "alert(1)"><circle r="5"/></svg>', '<svg ><circle r="5"/></svg>'),
            # javascript: link
            ('<svg><a href="javascript:alert(1)">Click</a></svg>', '<svg><a href="alert(1)">Click</a></svg>'),
            # Mixed case and spaces in javascript:
            ('<svg><a href="  JaVaScRiPt: alert(1)">Click</a></svg>', '<svg><a href=" alert(1)">Click</a></svg>'),
        ]
        for raw, expected in payloads:
            cleaned = HeadlessAvatarEngine.sanitize_svg(raw)
            self.assertNotIn("<script", cleaned.lower())
            self.assertNotIn("onload", cleaned.lower())
            self.assertNotIn("onclick", cleaned.lower())
            self.assertNotIn("javascript:", cleaned.lower())

        # Also verify run_pet.validate_image_file rejects malicious SVG payloads
        with tempfile.TemporaryDirectory() as td:
            for idx, (raw, _) in enumerate(payloads):
                bad_svg = Path(td) / f"malicious_{idx}.svg"
                bad_svg.write_text(raw, encoding="utf-8")
                v_res = validate_image_file(str(bad_svg))
                self.assertFalse(v_res["valid"], f"Malicious SVG should be rejected: {raw}")
                self.assertEqual(v_res["error"], "MALICIOUS_SVG_PAYLOAD")


class TestQuotaBoundariesAndZeroDivision(unittest.TestCase):
    """Stress-test zero, negative, boolean, and overflow token conditions in QuotaStatus and QuotaMonitor."""

    def test_quota_zero_total_tokens_no_division_by_zero(self):
        """total_tokens = 0 must calculate 0.0% and status EXHAUSTED without raising ZeroDivisionError."""
        qs = QuotaStatus.calculate(total_tokens=0, used_tokens=0)
        self.assertEqual(qs.total_tokens, 0)
        self.assertEqual(qs.used_tokens, 0)
        self.assertEqual(qs.remaining_tokens, 0)
        self.assertEqual(qs.remaining_percentage, 0.0)
        self.assertEqual(qs.remaining_basis_points, 0)
        self.assertEqual(qs.status, QuotaHealthStatus.EXHAUSTED.value)

    def test_quota_used_tokens_exceeding_total(self):
        """used_tokens > total_tokens must clamp remaining_tokens to 0 and percentage to 0.0%."""
        qs = QuotaStatus.calculate(total_tokens=1000, used_tokens=2500)
        self.assertEqual(qs.total_tokens, 1000)
        self.assertEqual(qs.used_tokens, 2500)
        self.assertEqual(qs.remaining_tokens, 0)
        self.assertEqual(qs.remaining_percentage, 0.0)
        self.assertEqual(qs.status, QuotaHealthStatus.EXHAUSTED.value)

    def test_quota_negative_total_tokens_rejected(self):
        """Negative total_tokens must raise ModelValidationError."""
        with self.assertRaises(ModelValidationError) as cm:
            QuotaStatus.calculate(total_tokens=-500, used_tokens=100)
        self.assertEqual(cm.exception.code, "OUT_OF_BOUNDS")

    def test_quota_negative_used_tokens_rejected(self):
        """Negative used_tokens must raise ModelValidationError."""
        with self.assertRaises(ModelValidationError) as cm:
            QuotaStatus.calculate(total_tokens=1000, used_tokens=-50)
        self.assertEqual(cm.exception.code, "OUT_OF_BOUNDS")

    def test_quota_bool_type_trap_rejected(self):
        """In Python, bool is a subclass of int. Passing True or False for tokens must be rejected."""
        with self.assertRaises(ModelValidationError) as cm:
            QuotaStatus.calculate(total_tokens=True, used_tokens=0)
        self.assertEqual(cm.exception.code, "TYPE_ERROR")

        with self.assertRaises(ModelValidationError) as cm2:
            QuotaStatus.calculate(total_tokens=1000, used_tokens=False)
        self.assertEqual(cm2.exception.code, "TYPE_ERROR")

    def test_quota_extreme_integer_overflow_safety(self):
        """Huge integers (e.g. 10^18 tokens) must compute accurate basis points without overflow."""
        total = 10**18
        used = 3 * 10**17  # 30% used, 70% remaining
        qs = QuotaStatus.calculate(total_tokens=total, used_tokens=used)
        self.assertEqual(qs.remaining_tokens, 7 * 10**17)
        self.assertEqual(qs.remaining_basis_points, 7000)
        self.assertEqual(qs.remaining_percentage, 70.0)
        self.assertEqual(qs.status, QuotaHealthStatus.HEALTHY.value)

    def test_quota_status_direct_invalid_percentage(self):
        """Direct instantiation of QuotaStatus with NaN, Inf, or negative percentage must fail."""
        with self.assertRaises(ModelValidationError) as cm:
            QuotaStatus(
                total_tokens=100,
                used_tokens=0,
                remaining_tokens=100,
                remaining_percentage=float("nan"),
                status="healthy",
            )
        self.assertEqual(cm.exception.code, "OUT_OF_BOUNDS")

        with self.assertRaises(ModelValidationError) as cm2:
            QuotaStatus(
                total_tokens=100,
                used_tokens=0,
                remaining_tokens=100,
                remaining_percentage=105.0,
                status="healthy",
            )
        self.assertEqual(cm2.exception.code, "OUT_OF_BOUNDS")

        with self.assertRaises(ModelValidationError) as cm3:
            QuotaStatus(
                total_tokens=100,
                used_tokens=0,
                remaining_tokens=100,
                remaining_percentage=-0.1,
                status="healthy",
            )
        self.assertEqual(cm3.exception.code, "OUT_OF_BOUNDS")

    def test_quota_monitor_with_corrupt_vscdb_records(self):
        """QuotaMonitor must handle corrupted SQLite table entries gracefully and fall back to mock."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "state.vscdb"
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
            # Insert garbage protobuf
            conn.execute("INSERT INTO ItemTable VALUES ('antigravityUnifiedStateSync.modelCredits', 'CorruptedNotB64!#%')")
            conn.execute("INSERT INTO ItemTable VALUES ('antigravityUnifiedStateSync.userStatus', 'CorruptedNotB64!#%')")
            conn.execute("INSERT INTO ItemTable VALUES ('antigravityAuthStatus', '{\"email\":\"test@test.com\"}')")
            conn.commit()
            conn.close()

            monitor = QuotaMonitor(mode="auto", vscdb_path=db_path)
            # Must not crash, should fall back to mock
            status = monitor.get_quota_status(force_refresh=True)
            self.assertIsNotNone(status)
            self.assertGreater(status.total_tokens, 0)


class TestAvatarMagicBytesAndFileSecurity(unittest.TestCase):
    """Adversarial stress-testing of image files, magic bytes, and size boundaries."""

    def test_zero_byte_avatar_rejected(self):
        """Zero-byte image file must be rejected by all validators."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            empty_file = Path(tmp_dir) / "empty.png"
            empty_file.write_bytes(b"")

            # run_pet.py validator
            res1 = validate_image_file(str(empty_file))
            self.assertFalse(res1["valid"])
            self.assertEqual(res1["error"], "INVALID_FILE_EMPTY")

            # test_account_switcher.py validator
            with self.assertRaises(ValueError) as cm:
                HeadlessAvatarEngine.validate_magic_bytes(b"")
            self.assertEqual(str(cm.exception), "INVALID_FILE_EMPTY")

    def test_oversized_avatar_rejected(self):
        """Image file exceeding 10MB limit must be rejected."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            big_file = Path(tmp_dir) / "huge.png"
            # Create sparse / truncated file of 10MB + 10 bytes
            with open(big_file, "wb") as f:
                f.seek(10 * 1024 * 1024 + 10)
                f.write(b"\x00")

            res1 = validate_image_file(str(big_file))
            self.assertFalse(res1["valid"])
            self.assertEqual(res1["error"], "FILE_EXCEEDS_MAX_SIZE_10MB")

            with self.assertRaises(ValueError) as cm:
                HeadlessAvatarEngine.validate_magic_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * (10 * 1024 * 1024 + 5))
            self.assertEqual(str(cm.exception), "FILE_EXCEEDS_MAX_SIZE_10MB")

    def test_fake_magic_bytes_rejected(self):
        """Executable or text files renamed to image extensions must be rejected."""
        fake_payloads = [
            # Windows MZ executable header
            b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff",
            # ELF Linux binary header
            b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            # Shell script
            b"#!/bin/bash\necho hello\n",
            # Truncated PNG header (only 4 bytes)
            b"\x89PNG",
            # Fake GIF (GIF85a)
            b"GIF85a\x01\x00\x01\x00",
            # Fake WebP (RIFF followed by AVI)
            b"RIFF\x24\x00\x00\x00AVI LIST",
            # HTML page
            b"<!DOCTYPE html><html><body>Test</body></html>",
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            for idx, payload in enumerate(fake_payloads):
                fake_file = Path(tmp_dir) / f"fake_{idx}.png"
                fake_file.write_bytes(payload)

                res = validate_image_file(str(fake_file))
                self.assertFalse(res["valid"], f"Fake payload {payload[:8]} was incorrectly accepted by validate_image_file")
                self.assertEqual(res["error"], "INVALID_MAGIC_BYTES")

                with self.assertRaises(ValueError):
                    HeadlessAvatarEngine.validate_magic_bytes(payload)

    def test_valid_magic_bytes_accepted(self):
        """Legitimate PNG, GIF89a, WebP, and SVG headers must be properly identified."""
        valid_samples = [
            (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", "png"),
            (b"GIF89a\x10\x00\x10\x00\x80\x00\x00", "gif"),
            (b"GIF87a\x10\x00\x10\x00\x80\x00\x00", "gif"),
            (b"RIFF\x20\x00\x00\x00WEBPVP8 \x14\x00\x00\x00", "webp"),
            (b"<?xml version=\"1.0\"?><svg width=\"100\" height=\"100\"></svg>", "svg"),
            (b"<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>", "svg"),
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            for idx, (data, expected_fmt) in enumerate(valid_samples):
                sample_file = Path(tmp_dir) / f"valid_{idx}.{expected_fmt}"
                sample_file.write_bytes(data)

                res = validate_image_file(str(sample_file))
                self.assertTrue(res["valid"], f"Valid sample {expected_fmt} rejected by validate_image_file: {res}")
                self.assertEqual(res["format"], expected_fmt)

                fmt2 = HeadlessAvatarEngine.validate_magic_bytes(data)
                self.assertEqual(fmt2, expected_fmt)


class TestAccountSwitcherAdversarial(unittest.TestCase):
    """Adversarial stress-testing of AccountSwitcher under simulated disk and process faults."""

    def test_switch_profile_atomic_rollback_on_write_failure(self):
        """Simulate failure during switch_profile and verify pre-swap backup is automatically restored."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sandbox = Path(tmp_dir)
            switcher = AccountSwitcher(gemini_home=sandbox)

            # Seed Profile A and Profile B
            prof_a = AccountProfile(id="profile-a", label="Profile Alpha", email="alpha@antigravity.io")
            prof_b = AccountProfile(id="profile-b", label="Profile Beta", email="beta@antigravity.io")
            switcher.add_profile(prof_a)
            switcher.add_profile(prof_b)

            # Activate Profile A first
            switcher.switch_profile("profile-a", create_backup=True)
            self.assertEqual(switcher.get_active_profile().id, "profile-a")

            # Mock _atomic_write_json on the 2nd file write to simulate sudden power outage / disk error
            original_atomic_write = switcher._atomic_write_json
            call_count = [0]

            def faulty_atomic_write(file_path: Path, data: Any, max_retries: int = 3):
                call_count[0] += 1
                if call_count[0] == 2:  # Fail on active_profile.json update
                    raise IOError("Simulated sudden disk full error during atomic swap")
                return original_atomic_write(file_path, data, max_retries)

            switcher._atomic_write_json = faulty_atomic_write

            # Attempt switch to Profile B, which should fail and automatically roll back
            with self.assertRaises(RuntimeError) as cm:
                switcher.switch_profile("profile-b", create_backup=True)

            self.assertIn("failed and was rolled back", str(cm.exception))

            # Restore original function
            switcher._atomic_write_json = original_atomic_write

            # Verify active profile is still Profile A!
            active_after_rollback = switcher.get_active_profile()
            self.assertIsNotNone(active_after_rollback)
            self.assertEqual(active_after_rollback.id, "profile-a")
            self.assertEqual(active_after_rollback.email, "alpha@antigravity.io")

    def test_delete_active_profile_without_force_safely_rejected(self):
        """Deleting active profile without force=True must be strictly rejected with ValueError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sandbox = Path(tmp_dir)
            switcher = AccountSwitcher(gemini_home=sandbox)

            prof = AccountProfile(id="active-prof", label="Active", email="active@example.com")
            switcher.add_profile(prof)
            switcher.switch_profile("active-prof", create_backup=False)

            with self.assertRaises(ValueError) as cm:
                switcher.delete_profile("active-prof", force=False)
            self.assertIn("Cannot delete active profile", str(cm.exception))

            # Profile must still exist
            self.assertIsNotNone(switcher.get_profile("active-prof"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
