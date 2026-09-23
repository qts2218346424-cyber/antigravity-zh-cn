# Project: Antigravity Desktop Pet

## Architecture

The Antigravity Desktop Pet is designed as a decoupled, multi-layered system prioritizing ultra-lightweight footprint, atomic credential safety on Windows, real-time quota visibility, and 100% headless testability:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Desktop Pet UI (Frontend Engine)                     │
│  - Modern HTML5/CSS3/Vanilla JS (No heavy framework, <40MB RAM)       │
│  - Animated Gemini Mascot (SVG + CSS Keyframes: idle/thinking/finish/low)│
│  - Custom Avatar Importer (PNG, GIF, WebP, SVG with magic-byte check) │
│  - Glassmorphic Toast Notifications & Color-Coded Quota Badge          │
│  - Drag-to-reposition, Always-on-top & Click-through controls          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ IPC / JSON Bridge
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Host Window Engine (Dual Shell Strategy)               │
│  1. Tauri v2 (Standard Production Shell):                              │
│     - src-tauri/ (Cargo.toml, tauri.conf.json, system tray, IPC)       │
│     - Frameless, transparent, shadow:false, set_ignore_cursor_events   │
│  2. Lightweight Python WebView2 Runner (run_pet.py):                   │
│     - Zero-install instant preview on Windows via pywebview + pystray │
│     - Native frameless transparent composition + system tray menu      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Python Engine API / CLI
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Core Backend Engine (pet_engine/)                      │
│  - models.py: AccountProfile, QuotaStatus, BackupRecord schemas        │
│  - proto_decoder.py: Pure-Python Protobuf wire-format parser           │
│  - switcher.py: 2-phase atomic hot-swap (os.replace) & backup rotation │
│  - quota.py: Live SQLite (state.vscdb) inspection & mock driver        │
│  - cli.py: Standalone CLI interface (list, switch, add, quota, notify) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Target Storage & State
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Credential & State Target Layer                     │
│  - ~/.gemini/google_accounts.json (Active Google account index)        │
│  - ~/.gemini/profiles/ (Saved account profiles vault)                  │
│  - ~/.gemini/backups/ (Timestamped snapshots, retention max 10)        │
│  - %APPDATA%\Antigravity\User\globalStorage\state.vscdb (WAL SQLite)   │
└────────────────────────────────────────────────────────────────────────┘
```

## Feature Inventory

Every feature discovered during the survey phase is assigned to a specific milestone:

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | F3.1 Profile Storage | Store & label multiple profiles under `~/.gemini/profiles/` with credentials | M1 | Survey / R3 |
| 2 | F3.2 Profile Listing | List all saved profiles with active profile indicator and last used time | M1 | Survey / R3 |
| 3 | F3.3 Pre-Swap Backup | Create timestamped snapshot in `~/.gemini/backups/` with pruning before swap | M1 | Survey / R3 |
| 4 | F3.4 Atomic Hot-Swap | Atomic credential swap using temp file + `os.replace` & SQLite WAL update | M1 | Survey / R3 |
| 5 | F3.5 Rollback on Error | Automatic rollback to pre-swap backup upon any exception during swap | M1 | Survey / R3 |
| 6 | F4.1 Standalone CLI | CLI interface for profile management, switching, backups, quota | M1 | Survey / R4 |
| 7 | F2.1 Dual Quota Parsing | Parse quota from local SQLite `state.vscdb` (protobuf) and mock provider | M2 | Survey / R2 |
| 8 | F2.2 Quota Status Model | Calculate token percentages, classify healthy/warning/critical/exhausted | M2 | Survey / R2 |
| 9 | F2.3 Warning Thresholds | Configurable low-quota threshold (default 20%) and critical (5%) | M2 | Survey / R2 |
| 10| F2.4 Task Notifications | Evaluate task complete/fail events and generate toast alert data | M2 | Survey / R2 |
| 11| F2.5 Low Quota Alerts | Proactive alerts on quota crossing warning threshold with cooldown | M2 | Survey / R2 |
| 12| F1.6 Gemini SVG Mascot | Animated vector mascot with 4 states (idle, thinking, task_finished, quota_low) | M3 | Survey / R1 |
| 13| F1.7 Custom Avatar Engine | Import PNG, animated GIF, WebP, SVG with magic-byte validation & live hot-swap | M3 | Survey / R1 |
| 14| F1.8 Toast UI Component | Non-intrusive floating glassmorphic notification toast with auto-dismiss | M3 | Survey / R1 |
| 15| F1.1 Transparent Window | Frameless transparent floating window on Windows (alpha composition) | M4 | Survey / R1 |
| 16| F1.2 Drag & Reposition | Drag-and-drop repositioning anywhere on single/multi-monitor screens | M4 | Survey / R1 |
| 17| F1.3 Always-on-Top Toggle | Toggle topmost floating window z-order dynamically | M4 | Survey / R1 |
| 18| F1.4 Click-Through Mode | Toggle cursor pass-through to underlying apps with tray/hotkey restore | M4 | Survey / R1 |
| 19| F1.5 System Tray Integration | Taskbar notification area icon with context menu (profiles, toggle, quit) | M4 | Survey / R1 |
| 20| F4.2 Test Suite Execution | 98-case automated test suite across Tiers 1-4 via `test_account_switcher.py` | M5 | Survey / R4 |

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Account Switcher Engine & CLI Runner | `pet_engine/models.py`, `switcher.py`, `cli.py`, atomic swap, backup retention & rollback | None | PLANNED |
| M2 | Quota Tracker & Notification Evaluation Service | `pet_engine/proto_decoder.py`, `quota.py`, SQLite `state.vscdb` parser, mock driver, alerts | M1 | PLANNED |
| M3 | Desktop Pet UI & Mascot Animation Engine | `frontend/index.html`, `styles.css`, `mascot.js`, animated Gemini SVG mascot, avatar importer, toast | None | PLANNED |
| M4 | Window & System Tray Integration Shell | Tauri v2 project structure (`src-tauri/`) and Python preview runner (`run_pet.py`) with tray | M2, M3 | PLANNED |
| M5 | 100% E2E Test Pass & Adversarial Hardening | E2E test runner `test_account_switcher.py`, Tiers 1-4 validation, Tier 5 adversarial hardening | M1, M2, M3, M4 | PLANNED |

## Interface Contracts

### 1. `pet_engine.switcher` ↔ Consumers (CLI / UI / Tests)
```python
class AccountSwitcher:
    def __init__(self, gemini_home: Optional[Path] = None, vscdb_path: Optional[Path] = None): ...
    def list_profiles(self) -> Dict[str, Any]: ...
    def add_profile(self, profile: AccountProfile) -> bool: ...
    def switch_profile(self, profile_id: str, create_backup: bool = True) -> Dict[str, Any]: ...
    def create_backup(self, reason: str = "manual") -> Path: ...
    def list_backups(self) -> List[Dict[str, Any]]: ...
    def restore_backup(self, backup_name: str) -> bool: ...
```

### 2. `pet_engine.quota` ↔ Consumers
```python
class QuotaMonitor:
    def __init__(self, mode: str = "auto", mock_file: Optional[Path] = None): ...
    def get_quota_status(self, force_refresh: bool = False) -> QuotaStatus: ...
    def evaluate_task_notification(self, task_id: str, status: str, duration_s: float) -> Optional[NotificationEvent]: ...
    def check_low_quota_alert(self, current_percentage: float) -> Optional[NotificationEvent]: ...
```

### 3. Tauri IPC / Preview Runner RPC ↔ Frontend
- `get_quota_status()` -> `QuotaStatusResponse`
- `switch_profile(profile_id: str)` -> `ProfileSwitchResult`
- `list_profiles()` -> `ProfileListResponse`
- `import_avatar(source_path: str)` -> `AvatarImportResult`
- `toggle_always_on_top(enabled?: bool)` -> `{ success: bool, always_on_top: bool }`
- `toggle_click_through(enabled?: bool)` -> `{ success: bool, click_through: bool }`
- `set_pet_state(state: str, message?: str)` -> `{ success: bool, current_state: str }`
- `send_notification(req: NotificationRequest)` -> `{ success: bool, notification_id: str }`

## Code Layout

```
antigravity_pet/
├── PROJECT.md                                # Project blueprint & master index
├── TEST_INFRA.md                             # E2E test infrastructure specification
├── TEST_READY.md                             # Published upon E2E test suite readiness
├── test_account_switcher.py                  # Primary automated test suite (R4 entry point)
├── run_pet.py                                # Zero-install desktop preview runner (WebView2 + pystray)
├── pet_engine/                               # Core Python engine package
│   ├── __init__.py
│   ├── models.py                             # Schemas for Profile, Quota, Notification, Backup
│   ├── proto_decoder.py                      # Pure-Python Protobuf wire format decoder
│   ├── switcher.py                           # Atomic profile switcher, backup rotator, rollback
│   ├── quota.py                              # SQLite state.vscdb inspector & mock quota provider
│   ├── notification.py                       # Alert evaluator, cooldown rate-limiter, toast trigger
│   └── cli.py                                # Standalone CLI implementation
├── frontend/                                 # Ultra-lightweight Mascot UI
│   ├── index.html                            # Transparent HTML5 shell
│   ├── styles.css                            # Glassmorphism, animations, responsive layout
│   ├── mascot.js                             # SVG state machine, avatar switcher, toast presenter
│   └── assets/                               # Preset avatars (Gemini SVG, animated samples)
│       ├── gemini_mascot.svg
│       └── presets/
└── src-tauri/                                # Standards-compliant Tauri v2 application
    ├── Cargo.toml
    ├── tauri.conf.json
    ├── capabilities/
    │   └── default.json
    ├── icons/
    └── src/
        ├── main.rs
        └── lib.rs
```
