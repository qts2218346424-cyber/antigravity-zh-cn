"""
pet_engine - Core Backend Engine for Antigravity Desktop Pet
"""

from pet_engine.models import (
    AccountProfile,
    TokenInfo,
    BackupRecord,
    ModelQuota,
    QuotaStatus,
    QuotaHealthStatus,
    NotificationEvent,
    NotificationLevel,
    NotificationChannel,
    ModelValidationError,
    now_utc_iso,
    validate_safe_identifier,
    validate_email,
    validate_strict_int,
    validate_utc_iso,
)
from pet_engine.proto_decoder import ProtoWireParser
from pet_engine.switcher import AccountSwitcher, ProfileList
from pet_engine.quota import QuotaMonitor
from pet_engine.notification import NotificationService
from pet_engine.version_checker import VersionChecker

__version__ = "1.0.0"

__all__ = [
    "AccountProfile",
    "TokenInfo",
    "BackupRecord",
    "ModelQuota",
    "QuotaStatus",
    "QuotaHealthStatus",
    "NotificationEvent",
    "NotificationLevel",
    "NotificationChannel",
    "ModelValidationError",
    "ProtoWireParser",
    "AccountSwitcher",
    "ProfileList",
    "QuotaMonitor",
    "NotificationService",
    "VersionChecker",
    "now_utc_iso",
    "validate_safe_identifier",
    "validate_email",
    "validate_strict_int",
    "validate_utc_iso",
    "__version__",
]
