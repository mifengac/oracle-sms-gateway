from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SmsInsertRow:
    mobile: str
    content: str
    eid: str
    userid: str
    password: str
    userport: str


@dataclass(frozen=True)
class SmsFailedItem:
    mobile: str
    eid: str
    reason: str


@dataclass(frozen=True)
class SmsSendResult:
    inserted: int = 0
    skipped: int = 0
    failed: list[SmsFailedItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "inserted": self.inserted,
            "skipped": self.skipped,
            "failed": [item.__dict__ for item in self.failed],
        }
