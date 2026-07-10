from __future__ import annotations

from typing import Mapping


def is_authorized(headers: Mapping[str, str], configured_token: str) -> bool:
    token = str(configured_token or "").strip()
    if not token:
        return True

    normalized = {str(key).lower(): str(value).strip() for key, value in headers.items()}

    if normalized.get("x-api-key") == token:
        return True

    authorization = normalized.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip() == token

    return False
