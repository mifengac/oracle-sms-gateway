from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


USERPORT_RE = re.compile(r"^\d{4}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def load_env_file(path: str | Path = ".env") -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _get(mapping: Mapping[str, str], name: str, default: str = "") -> str:
    value = mapping.get(name, default)
    return str(value).strip()


def _parse_userports(raw: str, default_userport: str) -> dict[str, str]:
    result: dict[str, str] = {"default": default_userport}
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(f"Invalid SMS_BIZ_USERPORTS item: {item}")
        key, value = item.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError("SMS_BIZ_USERPORTS contains an empty business key")
        if not USERPORT_RE.fullmatch(value):
            raise ValueError(f"Invalid userport for {key}: {value}")
        result[key] = value
    return result


def _validate_identifier(value: str, name: str) -> str:
    if not IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a simple Oracle identifier")
    return value


@dataclass(frozen=True)
class Settings:
    oracle_user: str
    oracle_password: str
    oracle_dsn: str
    oracle_client_lib_dir: str
    oracle_schema: str
    sms_table: str
    sms_sequence: str
    sms_userid: str
    sms_password: str
    sms_default_userport: str
    sms_biz_userports: dict[str, str]
    api_token: str
    dedup_hours_default: int

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, str]) -> "Settings":
        default_userport = _get(mapping, "SMS_DEFAULT_USERPORT", "0006")
        if not USERPORT_RE.fullmatch(default_userport):
            raise ValueError("SMS_DEFAULT_USERPORT must be 4 digits")

        userports = _parse_userports(
            _get(mapping, "SMS_BIZ_USERPORTS", f"default:{default_userport}"),
            default_userport,
        )

        return cls(
            oracle_user=_get(mapping, "ORACLE_USER"),
            oracle_password=_get(mapping, "ORACLE_PASSWORD"),
            oracle_dsn=_get(mapping, "ORACLE_DSN", "10.45.100.147:1521/yfgxpt"),
            oracle_client_lib_dir=_get(mapping, "ORACLE_CLIENT_LIB_DIR"),
            oracle_schema=_validate_identifier(_get(mapping, "ORACLE_SCHEMA", "yfgadb"), "ORACLE_SCHEMA"),
            sms_table=_validate_identifier(_get(mapping, "SMS_TABLE", "dfsdl"), "SMS_TABLE"),
            sms_sequence=_validate_identifier(_get(mapping, "SMS_SEQUENCE", "seq_sendsms"), "SMS_SEQUENCE"),
            sms_userid=_get(mapping, "SMS_USERID", "admin"),
            sms_password=_get(mapping, "SMS_PASSWORD"),
            sms_default_userport=default_userport,
            sms_biz_userports=userports,
            api_token=_get(mapping, "API_TOKEN"),
            dedup_hours_default=int(_get(mapping, "DEDUP_HOURS_DEFAULT", "12")),
        )

    @classmethod
    def from_env(cls, env_path: str | Path = ".env") -> "Settings":
        merged = load_env_file(env_path)
        merged.update(os.environ)
        return cls.from_mapping(merged)

    def userport_for(self, biz: str) -> str:
        key = str(biz or "").strip()
        return self.sms_biz_userports.get(key) or self.sms_biz_userports.get("default") or self.sms_default_userport

    @property
    def table_name(self) -> str:
        return f"{self.oracle_schema}.{self.sms_table}"

    @property
    def sequence_name(self) -> str:
        return f"{self.oracle_schema}.{self.sms_sequence}"
