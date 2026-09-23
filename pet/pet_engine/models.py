"""
pet_engine/models.py - Core Data Models and Boundary Validation Schemas
Antigravity Desktop Pet.

Features:
- Zero external runtime dependencies (Standard Library only).
- Strict boundary validation against path traversal, Windows reserved names (CON, NUL, AUX, etc.),
  ReDoS, bool-int subtyping traps, and floating point drift.
- Full compatibility with Tauri v2 serde_json and WebView2 RPC.
- Backwards compatibility with survey prototypes (id <-> profile_id, label <-> name).
- Schema versioning (schema_version: int) and unknown field retention for lossless round-trips.
"""

from __future__ import annotations

import re
import json
import math
import uuid
import unicodedata
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parseaddr
from typing import Dict, List, Optional, Any, Union, Set


# ============================================================================
# Constants & Enums
# ============================================================================

WINDOWS_RESERVED_NAMES: Set[str] = {
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
}

ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
SIMPLE_DOMAIN_REGEX = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)+$")


class QuotaHealthStatus(str, Enum):
    """Quota health levels matching Tauri and Mascot state machine."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    EXHAUSTED = "exhausted"


class NotificationLevel(str, Enum):
    """Notification urgency levels."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationChannel(str, Enum):
    """Delivery destination for notification alerts."""
    TOAST = "toast"
    TRAY = "tray"
    MODAL = "modal"
    ALL = "all"


# ============================================================================
# Exceptions
# ============================================================================

class ModelValidationError(ValueError):
    """
    Structured validation error for data model boundaries.
    Easily serialized across IPC boundaries to Tauri or WebView2.
    """
    def __init__(self, field: str, code: str, message: str):
        super().__init__(f"Validation failed on '{field}' [{code}]: {message}")
        self.field = field
        self.code = code
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {
            "field": self.field,
            "code": self.code,
            "message": self.message,
        }


# ============================================================================
# Validation & Normalization Helpers
# ============================================================================

def now_utc_iso() -> str:
    """Return standard UTC ISO 8601 timestamp with millisecond precision and 'Z' suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def validate_utc_iso(ts_str: str, field_name: str) -> str:
    """Validate and normalize a timestamp to standard UTC ISO 8601 string."""
    if not isinstance(ts_str, str) or not ts_str.strip():
        raise ModelValidationError(field_name, "INVALID_DATETIME", "Timestamp string cannot be empty")
    ts = ts_str.strip()
    try:
        normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            raise ModelValidationError(
                field_name, "NAIVE_DATETIME_FORBIDDEN",
                f"Timestamp '{ts}' must include explicit UTC timezone offset ('Z' or '+00:00')"
            )
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    except (ValueError, TypeError) as e:
        raise ModelValidationError(field_name, "INVALID_DATETIME", f"Cannot parse '{ts}' as ISO 8601: {e}")


def validate_safe_identifier(val: str, field_name: str, max_len: int = 64) -> str:
    """
    Validates identifier against path traversal, Windows reserved device names, and regex.
    """
    if not isinstance(val, str):
        raise ModelValidationError(field_name, "TYPE_ERROR", f"Expected string, got {type(val).__name__}")

    val_norm = unicodedata.normalize("NFC", val.strip())
    if not val_norm:
        raise ModelValidationError(field_name, "EMPTY", "Identifier cannot be empty")

    if len(val_norm) > max_len:
        raise ModelValidationError(field_name, "LENGTH_EXCEEDED", f"Identifier exceeds max length {max_len}")

    if not ID_REGEX.match(val_norm):
        raise ModelValidationError(
            field_name, "INVALID_PATTERN",
            f"Identifier '{val_norm}' contains invalid characters. Must match ^[a-zA-Z0-9_-]{{1,{max_len}}}$"
        )

    # Check Windows reserved device names (CON, NUL, AUX, etc.)
    base_name = val_norm.split(".")[0].casefold()
    if base_name in WINDOWS_RESERVED_NAMES:
        raise ModelValidationError(
            field_name, "WINDOWS_RESERVED_NAME",
            f"Identifier '{val_norm}' is a reserved Windows device name"
        )

    return val_norm


def validate_email(email_str: str, field_name: str = "email") -> str:
    """
    ReDoS-safe email validation without catastrophic backtracking.
    """
    if not isinstance(email_str, str):
        raise ModelValidationError(field_name, "TYPE_ERROR", f"Expected string, got {type(email_str).__name__}")

    email = unicodedata.normalize("NFC", email_str.strip()).lower()
    if len(email) < 3 or len(email) > 254:
        raise ModelValidationError(field_name, "LENGTH_INVALID", f"Email length must be between 3 and 254 chars (got {len(email)})")

    _, parsed_addr = parseaddr(email)
    if not parsed_addr or "@" not in parsed_addr or parsed_addr != email:
        raise ModelValidationError(field_name, "INVALID_FORMAT", f"'{email}' is not a valid email address")

    parts = email.split("@")
    if len(parts) != 2:
        raise ModelValidationError(field_name, "INVALID_FORMAT", "Email must contain exactly one '@'")

    local, domain = parts[0], parts[1]
    if not local or len(local) > 64:
        raise ModelValidationError(field_name, "LOCAL_PART_INVALID", "Email local part must be 1-64 characters")
    if not domain or len(domain) > 255:
        raise ModelValidationError(field_name, "DOMAIN_PART_INVALID", "Email domain part must be 1-255 characters")

    if not SIMPLE_DOMAIN_REGEX.match(domain):
        raise ModelValidationError(field_name, "DOMAIN_INVALID", f"Domain '{domain}' is invalid")

    return email


def validate_strict_int(val: Any, field_name: str, min_val: int = 0) -> int:
    """
    Strict integer validator. Explicitly disallows bool instances (bool is a subclass of int in Python).
    """
    if isinstance(val, bool) or type(val) is not int:
        raise ModelValidationError(field_name, "TYPE_ERROR", f"Expected strict int, got {type(val).__name__} ({val!r})")
    if val < min_val:
        raise ModelValidationError(field_name, "OUT_OF_BOUNDS", f"Value must be >= {min_val}, got {val}")
    return val


def validate_metadata(meta: Any, field_name: str = "metadata", max_depth: int = 5, max_bytes: int = 16384) -> Dict[str, Any]:
    """
    Deep verification of metadata dictionary to prevent NaN, infinite recursion, and IPC bloat.
    """
    if not isinstance(meta, dict):
        raise ModelValidationError(field_name, "TYPE_ERROR", f"Expected dict, got {type(meta).__name__}")

    def _check_node(node: Any, depth: int):
        if depth > max_depth:
            raise ModelValidationError(field_name, "DEPTH_EXCEEDED", f"Metadata exceeds max nesting depth of {max_depth}")
        if isinstance(node, float):
            if math.isnan(node) or math.isinf(node):
                raise ModelValidationError(field_name, "INVALID_FLOAT", "Metadata contains NaN or Infinity")
        elif isinstance(node, dict):
            for k, v in node.items():
                if not isinstance(k, str):
                    raise ModelValidationError(field_name, "KEY_TYPE_ERROR", "All dict keys in metadata must be strings")
                _check_node(v, depth + 1)
        elif isinstance(node, list):
            for item in node:
                _check_node(item, depth + 1)
        elif node is not None and not isinstance(node, (str, int, bool)):
            raise ModelValidationError(field_name, "UNSUPPORTED_TYPE", f"Unsupported type in metadata: {type(node).__name__}")

    _check_node(meta, depth=1)

    try:
        serialized = json.dumps(meta, allow_nan=False, ensure_ascii=False)
        if len(serialized.encode("utf-8")) > max_bytes:
            raise ModelValidationError(field_name, "SIZE_EXCEEDED", f"Metadata serialized size exceeds {max_bytes} bytes")
    except (TypeError, ValueError) as e:
        raise ModelValidationError(field_name, "SERIALIZATION_ERROR", f"Metadata cannot be serialized to JSON: {e}")

    return meta


# ============================================================================
# Data Models
# ============================================================================

@dataclass(frozen=True, slots=True)
class TokenInfo:
    """Authentication tokens holder."""
    access_token: str = ""
    refresh_token: str = ""
    token_type: str = "Bearer"
    expiry: Optional[int] = None
    id_token: str = ""

    def __post_init__(self):
        if self.expiry is not None:
            validate_strict_int(self.expiry, "expiry", min_val=0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expiry": self.expiry,
            "id_token": self.id_token,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TokenInfo":
        if not isinstance(d, dict):
            raise ModelValidationError("tokens", "TYPE_ERROR", f"Expected dict for tokens, got {type(d).__name__}")
        return cls(
            access_token=str(d.get("access_token") or ""),
            refresh_token=str(d.get("refresh_token") or ""),
            token_type=str(d.get("token_type") or "Bearer"),
            expiry=d.get("expiry"),
            id_token=str(d.get("id_token") or ""),
        )


@dataclass(frozen=True, slots=True)
class AccountProfile:
    """
    Account authentication and persona profile.
    Maintained under ~/.gemini/profiles/<id>/profile.json.
    """
    id: str
    label: str
    email: str
    tier: str = "Google AI Pro"
    credits: int = 1000
    tokens: TokenInfo = field(default_factory=TokenInfo)
    created_at: str = field(default_factory=now_utc_iso)
    updated_at: str = field(default_factory=now_utc_iso)

    # Lifecycle & UI extensions
    is_active: bool = False
    avatar_url: str = ""
    min_credits_per_usage: int = 50
    schema_version: int = 1

    # Internal retention for unmapped fields during migrations
    _unknown_fields: Dict[str, Any] = field(default_factory=dict, hash=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "id", validate_safe_identifier(self.id, "id", max_len=64))

        label_norm = unicodedata.normalize("NFC", str(self.label or "").strip())
        if not label_norm:
            raise ModelValidationError("label", "EMPTY", "Profile label/name cannot be empty")
        if len(label_norm) > 128:
            raise ModelValidationError("label", "LENGTH_EXCEEDED", "Profile label exceeds 128 characters")
        object.__setattr__(self, "label", label_norm)

        object.__setattr__(self, "email", validate_email(self.email, "email"))
        object.__setattr__(self, "credits", validate_strict_int(self.credits, "credits", min_val=0))
        object.__setattr__(self, "min_credits_per_usage", validate_strict_int(self.min_credits_per_usage, "min_credits_per_usage", min_val=0))
        object.__setattr__(self, "created_at", validate_utc_iso(self.created_at, "created_at"))
        object.__setattr__(self, "updated_at", validate_utc_iso(self.updated_at, "updated_at"))

        if isinstance(self.tokens, dict):
            object.__setattr__(self, "tokens", TokenInfo.from_dict(self.tokens))
        elif not isinstance(self.tokens, TokenInfo):
            raise ModelValidationError("tokens", "TYPE_ERROR", "tokens must be TokenInfo or dict")

    # Backwards compatibility properties
    @property
    def profile_id(self) -> str:
        return self.id

    @property
    def name(self) -> str:
        return self.label

    def to_dict(self, include_unknown: bool = False) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "profile_id": self.id,
            "label": self.label,
            "name": self.label,
            "email": self.email,
            "tier": self.tier,
            "credits": self.credits,
            "tokens": self.tokens.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
            "avatar_url": self.avatar_url,
            "min_credits_per_usage": self.min_credits_per_usage,
            "schema_version": self.schema_version,
        }
        if include_unknown and self._unknown_fields:
            d.update(self._unknown_fields)
        return d

    def to_json(self, indent: Optional[int] = None) -> str:
        if indent is not None:
            return json.dumps(self.to_dict(include_unknown=True), indent=indent, ensure_ascii=False, allow_nan=False)
        return json.dumps(self.to_dict(include_unknown=False), separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AccountProfile":
        if not isinstance(data, dict):
            raise ModelValidationError("root", "TYPE_ERROR", f"Expected dict for AccountProfile, got {type(data).__name__}")

        raw_id = data.get("id")
        raw_pid = data.get("profile_id")
        if raw_id is not None and raw_pid is not None and raw_id != raw_pid:
            raise ModelValidationError("id", "ALIAS_CONFLICT", f"Conflicting values for 'id' ({raw_id!r}) and 'profile_id' ({raw_pid!r})")
        resolved_id = raw_id if raw_id is not None else raw_pid
        if resolved_id is None:
            raise ModelValidationError("id", "MISSING_FIELD", "Missing required field 'id'")

        raw_label = data.get("label")
        raw_name = data.get("name")
        if raw_label is not None and raw_name is not None and raw_label != raw_name:
            raise ModelValidationError("label", "ALIAS_CONFLICT", f"Conflicting values for 'label' ({raw_label!r}) and 'name' ({raw_name!r})")
        resolved_label = raw_label if raw_label is not None else raw_name
        if resolved_label is None:
            raise ModelValidationError("label", "MISSING_FIELD", "Missing required field 'label'")

        if "email" not in data:
            raise ModelValidationError("email", "MISSING_FIELD", "Missing required field 'email'")

        known_keys = {
            "id", "profile_id", "label", "name", "email", "tier", "credits", "tokens",
            "created_at", "updated_at", "is_active", "avatar_url", "min_credits_per_usage",
            "schema_version"
        }
        unknown_fields = {k: v for k, v in data.items() if k not in known_keys}

        raw_tokens = data.get("tokens") or {}
        tokens_obj = TokenInfo.from_dict(raw_tokens) if isinstance(raw_tokens, dict) else raw_tokens

        return cls(
            id=str(resolved_id),
            label=str(resolved_label),
            email=str(data["email"]),
            tier=str(data.get("tier", "Google AI Pro")),
            credits=data.get("credits", 1000),
            tokens=tokens_obj,
            created_at=data.get("created_at") or now_utc_iso(),
            updated_at=data.get("updated_at") or now_utc_iso(),
            is_active=bool(data.get("is_active", False)),
            avatar_url=str(data.get("avatar_url", "")),
            min_credits_per_usage=data.get("min_credits_per_usage", 50),
            schema_version=data.get("schema_version", 1),
            _unknown_fields=unknown_fields,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "AccountProfile":
        try:
            parsed = json.loads(json_str)
        except Exception as e:
            raise ModelValidationError("json", "JSON_PARSE_ERROR", f"Invalid JSON string: {e}")
        return cls.from_dict(parsed)


@dataclass(frozen=True, slots=True)
class BackupRecord:
    """
    Snapshot metadata for rollback and retention rotation.
    Maintained under ~/.gemini/backups/<backup_id>/meta.json.
    """
    backup_id: str
    timestamp: str
    profile_id: Optional[str]
    backup_dir: str
    files: List[str]
    reason: str = "manual"
    size_bytes: int = 0
    checksum: str = ""
    created_by_version: str = "1.0.0"
    schema_version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    _unknown_fields: Dict[str, Any] = field(default_factory=dict, hash=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "backup_id", validate_safe_identifier(self.backup_id, "backup_id", max_len=64))
        object.__setattr__(self, "timestamp", validate_utc_iso(self.timestamp, "timestamp"))

        if self.profile_id is not None:
            object.__setattr__(self, "profile_id", validate_safe_identifier(self.profile_id, "profile_id", max_len=64))

        if not isinstance(self.files, list):
            raise ModelValidationError("files", "TYPE_ERROR", "files must be a list of relative file names")
        if len(self.files) > 200:
            raise ModelValidationError("files", "LENGTH_EXCEEDED", "files list exceeds max 200 items")

        validated_files = []
        for idx, f in enumerate(self.files):
            if not isinstance(f, str) or not f.strip():
                raise ModelValidationError("files", "INVALID_FILE_NAME", f"File entry at index {idx} is empty or not string")
            f_norm = unicodedata.normalize("NFC", f.strip())
            if "/" in f_norm or "\\" in f_norm or ":" in f_norm or f_norm in (".", "..") or f_norm.startswith("\\\\"):
                raise ModelValidationError("files", "PATH_TRAVERSAL_DETECTED", f"Dangerous path component in file name '{f_norm}'")
            base = f_norm.split(".")[0].casefold()
            if base in WINDOWS_RESERVED_NAMES:
                raise ModelValidationError("files", "WINDOWS_RESERVED_NAME", f"File entry '{f_norm}' is a Windows reserved name")
            validated_files.append(f_norm)
        object.__setattr__(self, "files", validated_files)

        object.__setattr__(self, "size_bytes", validate_strict_int(self.size_bytes, "size_bytes", min_val=0))
        object.__setattr__(self, "metadata", validate_metadata(self.metadata, "metadata"))

    def to_dict(self, include_unknown: bool = False) -> Dict[str, Any]:
        d = {
            "backup_id": self.backup_id,
            "timestamp": self.timestamp,
            "profile_id": self.profile_id,
            "backup_dir": self.backup_dir,
            "files": list(self.files),
            "reason": self.reason,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "created_by_version": self.created_by_version,
            "schema_version": self.schema_version,
            "metadata": dict(self.metadata),
        }
        if include_unknown and self._unknown_fields:
            d.update(self._unknown_fields)
        return d

    def to_json(self, indent: Optional[int] = None) -> str:
        if indent is not None:
            return json.dumps(self.to_dict(include_unknown=True), indent=indent, ensure_ascii=False, allow_nan=False)
        return json.dumps(self.to_dict(include_unknown=False), separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupRecord":
        if not isinstance(data, dict):
            raise ModelValidationError("root", "TYPE_ERROR", f"Expected dict for BackupRecord, got {type(data).__name__}")
        for req in ("backup_id", "timestamp", "backup_dir", "files"):
            if req not in data:
                raise ModelValidationError(req, "MISSING_FIELD", f"Missing required field '{req}'")

        known_keys = {
            "backup_id", "timestamp", "profile_id", "backup_dir", "files", "reason",
            "size_bytes", "checksum", "created_by_version", "schema_version", "metadata"
        }
        unknown = {k: v for k, v in data.items() if k not in known_keys}

        return cls(
            backup_id=str(data["backup_id"]),
            timestamp=str(data["timestamp"]),
            profile_id=str(data["profile_id"]) if data.get("profile_id") is not None else None,
            backup_dir=str(data["backup_dir"]),
            files=list(data["files"]),
            reason=str(data.get("reason", "manual")),
            size_bytes=data.get("size_bytes", 0),
            checksum=str(data.get("checksum", "")),
            created_by_version=str(data.get("created_by_version", "1.0.0")),
            schema_version=data.get("schema_version", 1),
            metadata=dict(data.get("metadata") or {}),
            _unknown_fields=unknown,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "BackupRecord":
        try:
            parsed = json.loads(json_str)
        except Exception as e:
            raise ModelValidationError("json", "JSON_PARSE_ERROR", f"Invalid JSON string: {e}")
        return cls.from_dict(parsed)


@dataclass(frozen=True, slots=True)
class ModelQuota:
    """Individual model quota allocation details."""
    name: str
    available: bool = True
    credits_per_usage: int = 50
    remaining_requests: int = 0
    total_requests: int = 0
    percentage: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "credits_per_usage": self.credits_per_usage,
            "remaining_requests": self.remaining_requests,
            "total_requests": self.total_requests,
            "percentage": self.percentage,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ModelQuota":
        if not isinstance(d, dict):
            raise ModelValidationError("models", "TYPE_ERROR", "Model quota item must be a dict")
        return cls(
            name=str(d.get("name", "Unknown Model")),
            available=bool(d.get("available", True)),
            credits_per_usage=validate_strict_int(d.get("credits_per_usage", 50), "credits_per_usage", min_val=0),
            remaining_requests=validate_strict_int(d.get("remaining_requests", 0), "remaining_requests", min_val=0),
            total_requests=validate_strict_int(d.get("total_requests", 0), "total_requests", min_val=0),
            percentage=float(d.get("percentage", 100.0)),
        )


@dataclass(frozen=True, slots=True)
class QuotaStatus:
    """
    Antigravity quota status and threshold evaluator.
    Exposed across IPC to Mascot UI and CLI.
    """
    total_tokens: int
    used_tokens: int
    remaining_tokens: int
    remaining_percentage: float
    status: str
    reset_time_utc: Optional[str] = None
    models: List[Dict[str, Any]] = field(default_factory=list)
    groups: List[Dict[str, Any]] = field(default_factory=list)
    user_name: str = ""
    user_picture: str = ""
    fetched_at: str = field(default_factory=now_utc_iso)
    remaining_basis_points: int = 10000
    schema_version: int = 1
    account_email: str = ""
    profile_id: str = ""
    is_cached: bool = False
    _unknown_fields: Dict[str, Any] = field(default_factory=dict, hash=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "total_tokens", validate_strict_int(self.total_tokens, "total_tokens", min_val=0))
        object.__setattr__(self, "used_tokens", validate_strict_int(self.used_tokens, "used_tokens", min_val=0))
        object.__setattr__(self, "remaining_tokens", validate_strict_int(self.remaining_tokens, "remaining_tokens", min_val=0))

        pct = float(self.remaining_percentage)
        if math.isnan(pct) or math.isinf(pct) or pct < 0.0 or pct > 100.0:
            raise ModelValidationError("remaining_percentage", "OUT_OF_BOUNDS", f"Percentage must be in [0.0, 100.0], got {pct}")
        object.__setattr__(self, "remaining_percentage", round(pct, 2))

        valid_statuses = {s.value for s in QuotaHealthStatus}
        status_norm = str(self.status).lower().strip()
        if status_norm not in valid_statuses:
            raise ModelValidationError("status", "INVALID_STATUS", f"Status '{self.status}' must be one of {valid_statuses}")
        object.__setattr__(self, "status", status_norm)

        if self.reset_time_utc is not None:
            object.__setattr__(self, "reset_time_utc", validate_utc_iso(self.reset_time_utc, "reset_time_utc"))

        object.__setattr__(self, "fetched_at", validate_utc_iso(self.fetched_at, "fetched_at"))
        object.__setattr__(self, "remaining_basis_points", validate_strict_int(self.remaining_basis_points, "remaining_basis_points", min_val=0))

    @classmethod
    def calculate(
        cls,
        total_tokens: int,
        used_tokens: int,
        reset_time_utc: Optional[str] = None,
        models: Optional[List[Dict[str, Any]]] = None,
        fetched_at: Optional[str] = None,
        account_email: str = "",
        profile_id: str = "",
        is_cached: bool = False,
        warning_threshold: float = 50.0,
        critical_threshold: float = 20.0,
    ) -> "QuotaStatus":
        """
        Rock-solid single-source-of-truth factory preventing ZeroDivisionError and floating point drift.
        Uses exact integer basis points (0..10000).
        """
        t = validate_strict_int(total_tokens, "total_tokens", min_val=0)
        u = validate_strict_int(used_tokens, "used_tokens", min_val=0)
        r = max(0, t - u)

        if t == 0:
            basis_points = 0
            percentage = 0.0
            status = QuotaHealthStatus.EXHAUSTED.value
        else:
            basis_points = min(10000, (r * 10000) // t)
            percentage = round(basis_points / 100.0, 2)

            crit_bps = int(critical_threshold * 100)
            warn_bps = int(warning_threshold * 100)

            if r == 0 or basis_points == 0:
                status = QuotaHealthStatus.EXHAUSTED.value
            elif basis_points <= crit_bps:
                status = QuotaHealthStatus.CRITICAL.value
            elif basis_points <= warn_bps:
                status = QuotaHealthStatus.WARNING.value
            else:
                status = QuotaHealthStatus.HEALTHY.value

        return cls(
            total_tokens=t,
            used_tokens=u,
            remaining_tokens=r,
            remaining_percentage=percentage,
            status=status,
            reset_time_utc=reset_time_utc,
            models=models or [],
            fetched_at=fetched_at or now_utc_iso(),
            remaining_basis_points=basis_points,
            account_email=account_email,
            profile_id=profile_id,
            is_cached=is_cached,
        )

    def to_dict(self, include_unknown: bool = False) -> Dict[str, Any]:
        d = {
            "success": True,
            "account_email": self.account_email,
            "profile_id": self.profile_id,
            "total_tokens": self.total_tokens,
            "used_tokens": self.used_tokens,
            "remaining_tokens": self.remaining_tokens,
            "remaining_percentage": self.remaining_percentage,
            "remaining_basis_points": self.remaining_basis_points,
            "status": self.status,
            "reset_time_utc": self.reset_time_utc,
            "is_cached": self.is_cached,
            "models": list(self.models),
            "groups": list(self.groups),
            "user_name": self.user_name,
            "user_picture": self.user_picture,
            "fetched_at": self.fetched_at,
            "schema_version": self.schema_version,
        }
        if include_unknown and self._unknown_fields:
            d.update(self._unknown_fields)
        return d

    def to_json(self, indent: Optional[int] = None) -> str:
        if indent is not None:
            return json.dumps(self.to_dict(include_unknown=True), indent=indent, ensure_ascii=False, allow_nan=False)
        return json.dumps(self.to_dict(include_unknown=False), separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuotaStatus":
        if not isinstance(data, dict):
            raise ModelValidationError("root", "TYPE_ERROR", f"Expected dict for QuotaStatus, got {type(data).__name__}")
        for req in ("total_tokens", "used_tokens", "remaining_tokens", "remaining_percentage", "status"):
            if req not in data:
                raise ModelValidationError(req, "MISSING_FIELD", f"Missing required field '{req}'")

        known_keys = {
            "success", "account_email", "profile_id", "total_tokens", "used_tokens",
            "remaining_tokens", "remaining_percentage", "status", "reset_time_utc",
            "is_cached", "models", "groups", "user_name", "user_picture", "fetched_at",
            "remaining_basis_points", "schema_version"
        }
        unknown = {k: v for k, v in data.items() if k not in known_keys}

        bps = data.get("remaining_basis_points")
        if bps is None:
            tot = data["total_tokens"]
            rem = data["remaining_tokens"]
            bps = (rem * 10000 // tot) if tot > 0 else 0

        return cls(
            total_tokens=data["total_tokens"],
            used_tokens=data["used_tokens"],
            remaining_tokens=data["remaining_tokens"],
            remaining_percentage=data["remaining_percentage"],
            status=str(data["status"]),
            reset_time_utc=data.get("reset_time_utc"),
            models=list(data.get("models") or []),
            groups=list(data.get("groups") or []),
            user_name=str(data.get("user_name") or ""),
            user_picture=str(data.get("user_picture") or ""),
            fetched_at=data.get("fetched_at") or now_utc_iso(),
            remaining_basis_points=bps,
            account_email=str(data.get("account_email") or ""),
            profile_id=str(data.get("profile_id") or ""),
            is_cached=bool(data.get("is_cached", False)),
            schema_version=data.get("schema_version", 1),
            _unknown_fields=unknown,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "QuotaStatus":
        try:
            parsed = json.loads(json_str)
        except Exception as e:
            raise ModelValidationError("json", "JSON_PARSE_ERROR", f"Invalid JSON string: {e}")
        return cls.from_dict(parsed)


@dataclass(frozen=True, slots=True)
class NotificationEvent:
    """
    Desktop Pet notification alert event.
    Dispatched to Tauri toast, tray notification, or preview runner.
    """
    title: str
    body: str
    level: str = "info"
    timestamp: str = field(default_factory=now_utc_iso)
    channel: str = "toast"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dedupe_key: Optional[str] = None
    read_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1
    _unknown_fields: Dict[str, Any] = field(default_factory=dict, hash=False, repr=False, compare=False)

    def __post_init__(self):
        try:
            uuid.UUID(self.id)
        except (ValueError, TypeError):
            raise ModelValidationError("id", "INVALID_UUID", f"Notification id '{self.id}' must be a valid UUID string")

        title_norm = unicodedata.normalize("NFC", str(self.title or "").strip())
        if not title_norm:
            raise ModelValidationError("title", "EMPTY", "Notification title cannot be empty")
        if len(title_norm) > 128:
            raise ModelValidationError("title", "LENGTH_EXCEEDED", "Notification title exceeds 128 characters")
        object.__setattr__(self, "title", title_norm)

        body_norm = unicodedata.normalize("NFC", str(self.body or "").strip())
        if not body_norm:
            raise ModelValidationError("body", "EMPTY", "Notification body cannot be empty")
        if len(body_norm) > 1024:
            raise ModelValidationError("body", "LENGTH_EXCEEDED", "Notification body exceeds 1024 characters")
        object.__setattr__(self, "body", body_norm)

        valid_levels = {lvl.value for lvl in NotificationLevel}
        lvl_norm = str(self.level).lower().strip()
        if lvl_norm not in valid_levels:
            raise ModelValidationError("level", "INVALID_LEVEL", f"Level '{self.level}' must be one of {valid_levels}")
        object.__setattr__(self, "level", lvl_norm)

        valid_channels = {ch.value for ch in NotificationChannel}
        ch_norm = str(self.channel).lower().strip()
        if ch_norm not in valid_channels:
            raise ModelValidationError("channel", "INVALID_CHANNEL", f"Channel '{self.channel}' must be one of {valid_channels}")
        object.__setattr__(self, "channel", ch_norm)

        object.__setattr__(self, "timestamp", validate_utc_iso(self.timestamp, "timestamp"))
        if self.read_at is not None:
            object.__setattr__(self, "read_at", validate_utc_iso(self.read_at, "read_at"))

        object.__setattr__(self, "metadata", validate_metadata(self.metadata, "metadata"))

    def to_dict(self, include_unknown: bool = False) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "level": self.level,
            "timestamp": self.timestamp,
            "channel": self.channel,
            "dedupe_key": self.dedupe_key,
            "read_at": self.read_at,
            "metadata": dict(self.metadata),
            "schema_version": self.schema_version,
        }
        if include_unknown and self._unknown_fields:
            d.update(self._unknown_fields)
        return d

    def to_json(self, indent: Optional[int] = None) -> str:
        if indent is not None:
            return json.dumps(self.to_dict(include_unknown=True), indent=indent, ensure_ascii=False, allow_nan=False)
        return json.dumps(self.to_dict(include_unknown=False), separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationEvent":
        if not isinstance(data, dict):
            raise ModelValidationError("root", "TYPE_ERROR", f"Expected dict for NotificationEvent, got {type(data).__name__}")
        for req in ("title", "body"):
            if req not in data:
                raise ModelValidationError(req, "MISSING_FIELD", f"Missing required field '{req}'")

        known_keys = {
            "id", "title", "body", "level", "timestamp", "channel",
            "dedupe_key", "read_at", "metadata", "schema_version"
        }
        unknown = {k: v for k, v in data.items() if k not in known_keys}

        return cls(
            id=str(data.get("id") or str(uuid.uuid4())),
            title=str(data["title"]),
            body=str(data["body"]),
            level=str(data.get("level", "info")),
            timestamp=data.get("timestamp") or now_utc_iso(),
            channel=str(data.get("channel", "toast")),
            dedupe_key=str(data["dedupe_key"]) if data.get("dedupe_key") is not None else None,
            read_at=str(data["read_at"]) if data.get("read_at") is not None else None,
            metadata=dict(data.get("metadata") or {}),
            schema_version=data.get("schema_version", 1),
            _unknown_fields=unknown,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "NotificationEvent":
        try:
            parsed = json.loads(json_str)
        except Exception as e:
            raise ModelValidationError("json", "JSON_PARSE_ERROR", f"Invalid JSON string: {e}")
        return cls.from_dict(parsed)
