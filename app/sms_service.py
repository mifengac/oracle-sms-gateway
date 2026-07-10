from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Protocol

from .models import SmsFailedItem, SmsInsertRow, SmsSendResult


class SmsRepository(Protocol):
    def last_deadtime(self, eid: str, mobile: str) -> datetime | None:
        ...

    def insert_sms(self, row: SmsInsertRow) -> None:
        ...

    def commit(self) -> None:
        ...


class SmsService:
    def __init__(self, repository: SmsRepository, now_func: Callable[[], datetime] | None = None):
        self.repository = repository
        self.now_func = now_func or datetime.now

    def send_rows(self, rows: list[SmsInsertRow], dedup_hours: int) -> SmsSendResult:
        now = self.now_func()
        dedup_delta = timedelta(hours=dedup_hours)
        inserted = 0
        skipped = 0
        failed: list[SmsFailedItem] = []

        for row in rows:
            try:
                last_deadtime = self.repository.last_deadtime(row.eid, row.mobile) if dedup_hours > 0 else None
                if last_deadtime is not None and now - last_deadtime <= dedup_delta:
                    skipped += 1
                    continue

                self.repository.insert_sms(row)
                inserted += 1
            except Exception as exc:
                failed.append(SmsFailedItem(mobile=row.mobile, eid=row.eid, reason=str(exc)))

        if inserted:
            self.repository.commit()

        return SmsSendResult(inserted=inserted, skipped=skipped, failed=failed)
