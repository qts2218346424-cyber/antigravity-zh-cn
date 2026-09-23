"""
pet_engine/proto_decoder.py - Pure-Python Protobuf Wire-Format Decoder

Decodes Antigravity quota and user status state sync payloads stored in SQLite state.vscdb
(antigravityUnifiedStateSync.modelCredits and antigravityUnifiedStateSync.userStatus).
Zero external dependencies (pure Python standard library).
"""

from __future__ import annotations

import base64
import struct
from typing import Any, Dict, List, Tuple, Optional, Union


class ProtoWireParser:
    """Zero-dependency pure-Python Protobuf wire-format parser."""

    @staticmethod
    def parse(data: bytes) -> List[Tuple[int, str, Any]]:
        """
        Parses raw protobuf binary data into list of (field_number, wire_type_name, value).
        Handles multi-byte field numbers, varints, length-delimited bytes, fixed32, and fixed64.
        """
        items: List[Tuple[int, str, Any]] = []
        i = 0
        n = len(data)
        while i < n:
            # Decode tag as varint
            shift = 0
            tag = 0
            tag_start = i
            while i < n:
                b = data[i]
                i += 1
                tag |= (b & 0x7F) << shift
                if not (b & 0x80):
                    break
                shift += 7
                if shift > 35: # Prevent infinite loop on corrupt tag
                    break

            field_num = tag >> 3
            wire_type = tag & 0x07

            if field_num == 0:
                # Invalid field number 0 in protobuf
                break

            if wire_type == 0:  # varint
                shift = 0
                val_int = 0
                while i < n:
                    b = data[i]
                    i += 1
                    val_int |= (b & 0x7F) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                    if shift > 70:
                        break
                items.append((field_num, "varint", val_int))

            elif wire_type == 2:  # length-delimited (string, bytes, embedded message)
                shift = 0
                length = 0
                while i < n:
                    b = data[i]
                    i += 1
                    length |= (b & 0x7F) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                    if shift > 35:
                        break

                if length < 0 or i + length > n:
                    # Incomplete or corrupt length-delimited field
                    chunk = data[i:]
                    i = n
                else:
                    chunk = data[i : i + length]
                    i += length
                items.append((field_num, "bytes", chunk))

            elif wire_type == 5:  # 32-bit fixed
                chunk = data[i : i + 4]
                i += 4
                items.append((field_num, "fixed32", chunk))

            elif wire_type == 1:  # 64-bit fixed
                chunk = data[i : i + 8]
                i += 8
                items.append((field_num, "fixed64", chunk))

            else:
                items.append((field_num, f"unknown_{wire_type}", None))
                break

        return items

    @classmethod
    def parse_map(cls, data: bytes) -> Dict[str, bytes]:
        """
        Parses a protobuf map<string, bytes> message.
        In protobuf, map entries are repeated messages with field 1 = key, field 2 = value.
        """
        res: Dict[str, bytes] = {}
        for f_num, w_type, content in cls.parse(data):
            if w_type == "bytes":
                sub = cls.parse(content)
                key_str: Optional[str] = None
                val_bytes: Optional[bytes] = None
                for sf, sw, sc in sub:
                    if sf == 1 and sw == "bytes":
                        try:
                            key_str = sc.decode("utf-8")
                        except Exception:
                            key_str = sc.decode("latin-1", errors="replace")
                    elif sf == 2 and sw == "bytes":
                        val_bytes = sc
                if key_str and val_bytes is not None:
                    res[key_str] = val_bytes
        return res

    @staticmethod
    def _extract_inner_bytes(val: bytes) -> bytes:
        """
        Normalizes internal sentinel value bytes.
        Handles optional leading length prefixes (e.g. \n\x04...) and inner Base64 encoding.
        """
        candidate = val
        if candidate.startswith(b"\n"):
            candidate = candidate[2:]
        candidate = candidate.strip()
        if candidate.startswith(b"\n"):
            candidate = candidate[2:]

        # Attempt base64 decode
        try:
            decoded = base64.b64decode(candidate)
            if len(decoded) > 0:
                return decoded
        except Exception:
            pass

        # If candidate has a leading non-b64 length/header byte, try candidate[1:]
        if len(candidate) > 1:
            try:
                decoded = base64.b64decode(candidate[1:])
                if len(decoded) > 0:
                    return decoded
            except Exception:
                pass

        return candidate

    @classmethod
    def parse_credits_payload(cls, b64_str: Union[str, bytes]) -> Dict[str, Any]:
        """
        Extracts available_credits, min_credits_per_usage, and use_ai_credits from
        antigravityUnifiedStateSync.modelCredits Base64 string or bytes.
        """
        result: Dict[str, Any] = {
            "available_credits": 0,
            "min_credits_per_usage": 50,
            "use_ai_credits": False,
            "success": False,
        }

        if not b64_str:
            return result

        try:
            if isinstance(b64_str, str):
                raw = base64.b64decode(b64_str)
            else:
                raw = b64_str

            m = cls.parse_map(raw)

            if "availableCreditsSentinelKey" in m:
                inner_bytes = cls._extract_inner_bytes(m["availableCreditsSentinelKey"])
                inner = cls.parse(inner_bytes)
                for f, wt, v in inner:
                    if f == 2 and wt == "varint":
                        result["available_credits"] = v
                        result["success"] = True

            if "minimumCreditAmountForUsageKey" in m:
                inner_bytes = cls._extract_inner_bytes(m["minimumCreditAmountForUsageKey"])
                inner = cls.parse(inner_bytes)
                for f, wt, v in inner:
                    if f == 2 and wt == "varint":
                        result["min_credits_per_usage"] = v

            if "useAICreditsSentinelKey" in m:
                inner_bytes = cls._extract_inner_bytes(m["useAICreditsSentinelKey"])
                inner = cls.parse(inner_bytes)
                for f, wt, v in inner:
                    if f == 1 and wt == "varint":
                        result["use_ai_credits"] = bool(v)

        except Exception:
            # Safe degradation on malformed payload
            pass

        return result

    @classmethod
    def parse_user_status_payload(cls, b64_str: Union[str, bytes]) -> Dict[str, Any]:
        """
        Extracts name, email, tier_id, tier_name, and model list from
        antigravityUnifiedStateSync.userStatus Base64 string or bytes.
        """
        result: Dict[str, Any] = {
            "name": "",
            "email": "",
            "tier_id": "",
            "tier_name": "Google AI Pro",
            "models": [],
            "success": False,
        }

        if not b64_str:
            return result

        try:
            if isinstance(b64_str, str):
                raw = base64.b64decode(b64_str)
            else:
                raw = b64_str

            m = cls.parse_map(raw)

            if "userStatusSentinelKey" in m:
                inner_bytes = cls._extract_inner_bytes(m["userStatusSentinelKey"])
                inner = cls.parse(inner_bytes)
                for f, wt, v in inner:
                    if wt == "bytes":
                        sub = cls.parse(v)
                        for sf, sw, sc in sub:
                            if sf == 1 and sw == "bytes":
                                try:
                                    text = sc.decode("utf-8")
                                    if any(kw in text for kw in ["Gemini", "Claude", "GPT"]):
                                        if text not in result["models"]:
                                            result["models"].append(text)
                                            result["success"] = True
                                    elif text.endswith("-tier"):
                                        result["tier_id"] = text
                                    elif "AI Pro" in text or "AI Ultra" in text:
                                        if not result["tier_name"]:
                                            result["tier_name"] = text
                                except Exception:
                                    pass
                            elif sf == 2 and sw == "bytes":
                                try:
                                    text = sc.decode("utf-8")
                                    if ("AI Pro" in text or "AI Ultra" in text) and not result["tier_name"]:
                                        result["tier_name"] = text
                                except Exception:
                                    pass

        except Exception:
            pass

        return result

    @classmethod
    def parse_unified_state(
        cls,
        credits_b64: Optional[Union[str, bytes]] = None,
        user_status_b64: Optional[Union[str, bytes]] = None,
    ) -> Dict[str, Any]:
        """
        Convenience wrapper extracting unified quota and profile metadata.
        """
        credits_info = cls.parse_credits_payload(credits_b64 or "")
        status_info = cls.parse_user_status_payload(user_status_b64 or "")

        return {
            "credits": credits_info["available_credits"],
            "min_credits_per_usage": credits_info["min_credits_per_usage"],
            "use_ai_credits": credits_info["use_ai_credits"],
            "models": status_info["models"],
            "tier": status_info["tier_name"] or status_info["tier_id"] or "Google AI Pro",
            "name": status_info["name"],
            "email": status_info["email"],
            "has_credits": credits_info["success"],
            "has_status": status_info["success"],
        }
