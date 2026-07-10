from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .config import Settings
from .models import SmsInsertRow


MOBILE_RE = re.compile(r"^1[3-9]\d{9}$")
MAX_CONTENT_LENGTH = 4000


class ValidationError(ValueError):
    pass


def normalize_mobile(value: Any) -> str:
    mobile = re.sub(r"[\s\-]", "", str(value or ""))
    if not MOBILE_RE.fullmatch(mobile):
        raise ValidationError(f"Invalid mobile: {value}")
    return mobile


def _require_text(payload: dict[str, Any], name: str) -> str:
    value = str(payload.get(name) or "").strip()
    if not value:
        raise ValidationError(f"Missing field: {name}")
    return value


def _validate_content(content: str) -> str:
    value = str(content or "").strip()
    if not value:
        raise ValidationError("Missing field: content")
    if len(value) > MAX_CONTENT_LENGTH:
        raise ValidationError("content is longer than 4000 characters")
    return value


@dataclass(frozen=True)
class SendItem:
    mobile: str
    content: str
    eid: str


@dataclass(frozen=True)
class SendRequest:
    biz: str
    dedup_hours: int
    items: list[SendItem]

    def to_insert_rows(self, settings: Settings) -> list[SmsInsertRow]:
        userport = settings.userport_for(self.biz)
        return [
            SmsInsertRow(
                mobile=item.mobile,
                content=item.content,
                eid=item.eid,
                userid=settings.sms_userid,
                password=settings.sms_password,
                userport=userport,
            )
            for item in self.items
        ]


def _dedupe_items(items: list[SendItem]) -> list[SendItem]:
    seen: set[tuple[str, str, str]] = set()
    result: list[SendItem] = []
    for item in items:
        key = (item.eid, item.mobile, item.content)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _parse_item_list(payload: dict[str, Any], default_eid: str) -> list[SendItem]:
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        return []

    items: list[SendItem] = []
    for index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, dict):
            raise ValidationError(f"items[{index}] must be an object")
        eid = str(raw_item.get("eid") or default_eid).strip()
        if not eid:
            raise ValidationError(f"items[{index}] missing eid")
        items.append(
            SendItem(
                mobile=normalize_mobile(raw_item.get("mobile")),
                content=_validate_content(str(raw_item.get("content") or "")),
                eid=eid,
            )
        )
    return items


def _parse_shared_content(payload: dict[str, Any], eid: str) -> list[SendItem]:
    content = _validate_content(str(payload.get("content") or ""))
    raw_mobiles = payload.get("mobiles")
    if raw_mobiles is None and payload.get("mobile") is not None:
        raw_mobiles = [payload.get("mobile")]
    if not isinstance(raw_mobiles, list) or not raw_mobiles:
        raise ValidationError("Missing field: mobiles")

    return [SendItem(mobile=normalize_mobile(mobile), content=content, eid=eid) for mobile in raw_mobiles]


def parse_send_payload(payload: dict[str, Any], settings: Settings) -> SendRequest:
    if not isinstance(payload, dict):
        raise ValidationError("Payload must be an object")

    biz = str(payload.get("biz") or "default").strip() or "default"
    dedup_hours = int(payload.get("dedup_hours") or settings.dedup_hours_default)
    if dedup_hours < 0:
        raise ValidationError("dedup_hours must be greater than or equal to 0")

    default_eid = str(payload.get("eid") or "").strip()
    items = _parse_item_list(payload, default_eid)
    if not items:
        eid = _require_text(payload, "eid")
        items = _parse_shared_content(payload, eid)

    return SendRequest(biz=biz, dedup_hours=dedup_hours, items=_dedupe_items(items))
