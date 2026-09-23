"""
pet_engine/cli.py - Standalone CLI Interface for Account Switcher & Quota Engine

Provides CLI subcommands:
- list: List all available profiles and active profile
- switch: Atomically swap credentials to target profile
- add: Register a new profile into the vault
- delete: Remove a profile from the vault
- backup: Create an immediate timestamped backup snapshot
- restore: Restore credentials from snapshot
- quota: Inspect Antigravity model quota
- notify: Send/evaluate task or quota notification alerts

Exit codes:
0: Success
1: Generic error / Invalid arguments / Not found
2: File locked / Sharing violation
3: IO / Backup / Rollback error
4: Already exists (for add)
5: Cannot delete active profile without --force
6: Quota parsing failure
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path
from typing import List, Optional

from pet_engine.models import (
    AccountProfile,
    TokenInfo,
    ModelValidationError,
)
from pet_engine.switcher import AccountSwitcher
from pet_engine.quota import QuotaMonitor
from pet_engine.notification import NotificationService


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pet_engine",
        description="Antigravity Desktop Pet Core CLI runner",
    )
    parser.add_argument(
        "--gemini-home",
        "--gemini-dir",
        dest="gemini_home",
        type=str,
        default=None,
        help="Path to .gemini home directory (for sandbox testing)",
    )
    parser.add_argument(
        "--vscdb-path",
        dest="vscdb_path",
        type=str,
        default=None,
        help="Path to state.vscdb SQLite database",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # list
    subparsers.add_parser("list", help="List all account profiles and active profile")

    # switch
    switch_p = subparsers.add_parser("switch", help="Switch active account profile")
    switch_p.add_argument("profile_id", type=str, help="Target profile ID")
    switch_p.add_argument("--no-backup", action="store_true", help="Skip pre-swap backup snapshot")

    # add
    add_p = subparsers.add_parser("add", help="Add a new account profile")
    add_p.add_argument("--id", "--profile-id", dest="id", type=str, required=True, help="Profile ID")
    add_p.add_argument("--label", "--name", dest="label", type=str, required=True, help="Display label/name")
    add_p.add_argument("--email", type=str, required=True, help="Google account email")
    add_p.add_argument("--token", "--access-token", dest="token", type=str, default="", help="Access token")
    add_p.add_argument("--refresh-token", dest="refresh_token", type=str, default="", help="Refresh token")
    add_p.add_argument("--tier", type=str, default="Google AI Pro", help="Subscription tier")
    add_p.add_argument("--credits", type=int, default=1000, help="Initial credit balance")
    add_p.add_argument("--avatar-url", dest="avatar_url", type=str, default="", help="Avatar URL")
    add_p.add_argument("--overwrite", action="store_true", help="Overwrite if profile already exists")

    # delete
    del_p = subparsers.add_parser("delete", help="Delete an account profile")
    del_p.add_argument("profile_id", type=str, help="Profile ID to delete")
    del_p.add_argument("--force", action="store_true", help="Force deletion even if active")

    # backup
    bak_p = subparsers.add_parser("backup", help="Create an immediate backup snapshot")
    bak_p.add_argument("--reason", type=str, default="manual", help="Reason for backup")
    bak_p.add_argument("--dest", type=str, default=None, help="Optional destination path")

    # restore
    res_p = subparsers.add_parser("restore", help="Restore credentials from a backup")
    res_p.add_argument("backup_id", type=str, help="Backup ID or name to restore")

    # quota
    q_p = subparsers.add_parser("quota", help="Inspect model quota and remaining tokens")
    q_p.add_argument("--mock", action="store_true", help="Use mock quota source")
    q_p.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # notify
    not_p = subparsers.add_parser("notify", help="Dispatch task notification or quota alert")
    not_p.add_argument("--title", type=str, required=True, help="Notification title")
    not_p.add_argument("--body", type=str, required=True, help="Notification body")
    not_p.add_argument("--level", choices=["info", "success", "warning", "error"], default="info", help="Urgency level")
    not_p.add_argument("--channel", choices=["toast", "tray", "modal", "all"], default="toast", help="Delivery channel")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help(sys.stderr)
        return 1

    switcher = AccountSwitcher(
        gemini_home=args.gemini_home,
        vscdb_path=args.vscdb_path,
    )

    try:
        if args.subcommand == "list":
            profile_list = switcher.list_profiles()
            out = profile_list.to_dict()
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0

        elif args.subcommand == "switch":
            try:
                res = switcher.switch_profile(args.profile_id, create_backup=not args.no_backup)
                print(json.dumps(res, indent=2, ensure_ascii=False))
                return 0
            except ValueError as ve:
                err_msg = str(ve)
                print(json.dumps({"success": False, "error": err_msg}), file=sys.stderr)
                return 1
            except PermissionError as pe:
                print(json.dumps({"success": False, "error": f"File locked: {pe}"}), file=sys.stderr)
                return 2
            except RuntimeError as re:
                print(json.dumps({"success": False, "error": str(re)}), file=sys.stderr)
                return 3

        elif args.subcommand == "add":
            # Check if profile already exists
            existing = switcher.get_profile(args.id)
            if existing and not args.overwrite:
                print(json.dumps({"success": False, "error": f"Profile '{args.id}' already exists"}), file=sys.stderr)
                return 4

            profile = AccountProfile(
                id=args.id,
                label=args.label,
                email=args.email,
                tier=args.tier,
                credits=args.credits,
                avatar_url=args.avatar_url,
                tokens=TokenInfo(access_token=args.token, refresh_token=args.refresh_token),
            )
            switcher.add_profile(profile)
            print(json.dumps({"success": True, "profile": profile.to_dict()}, indent=2, ensure_ascii=False))
            return 0

        elif args.subcommand == "delete":
            try:
                switcher.delete_profile(args.profile_id, force=args.force)
                print(json.dumps({"success": True, "deleted": args.profile_id}, indent=2, ensure_ascii=False))
                return 0
            except ValueError as ve:
                msg = str(ve)
                if "Cannot delete active" in msg:
                    print(json.dumps({"success": False, "error": msg}), file=sys.stderr)
                    return 5
                print(json.dumps({"success": False, "error": msg}), file=sys.stderr)
                return 1

        elif args.subcommand == "backup":
            try:
                backup_dir = switcher.create_backup(reason=args.reason)
                meta_file = backup_dir / "meta.json"
                if meta_file.exists():
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                else:
                    meta = {"backup_id": backup_dir.name, "backup_dir": str(backup_dir)}
                meta["success"] = True
                print(json.dumps(meta, indent=2, ensure_ascii=False))
                return 0
            except Exception as e:
                print(json.dumps({"success": False, "error": str(e)}), file=sys.stderr)
                return 3

        elif args.subcommand == "restore":
            ok = switcher.restore_backup(args.backup_id)
            if ok:
                print(json.dumps({"success": True, "restored": args.backup_id}, indent=2, ensure_ascii=False))
                return 0
            else:
                print(json.dumps({"success": False, "error": f"Backup '{args.backup_id}' not found"}), file=sys.stderr)
                return 1

        elif args.subcommand == "quota":
            mode = "mock" if args.mock else "auto"
            monitor = QuotaMonitor(
                mode=mode,
                vscdb_path=args.vscdb_path,
                gemini_dir=args.gemini_home,
            )
            quota_status = monitor.get_quota_status()
            if not quota_status:
                print(json.dumps({"success": False, "error": "Failed to parse quota status"}), file=sys.stderr)
                return 6

            if args.format == "text":
                print(f"Status: {quota_status.status.upper()}")
                print(f"Remaining: {quota_status.remaining_tokens}/{quota_status.total_tokens} ({quota_status.remaining_percentage}%)")
            else:
                print(quota_status.to_json(indent=2))
            return 0

        elif args.subcommand == "notify":
            notifier = NotificationService()
            ev = notifier.create_custom_notification(
                title=args.title,
                body=args.body,
                level=args.level,
                channel=args.channel,
            )
            print(json.dumps({"success": True, "notified": True, "notification": ev.to_dict()}, indent=2, ensure_ascii=False))
            return 0

    except ModelValidationError as mve:
        print(json.dumps({"success": False, "error": str(mve), "validation": mve.to_dict()}), file=sys.stderr)
        return 1
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
