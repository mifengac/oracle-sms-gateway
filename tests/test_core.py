import unittest
from datetime import datetime, timedelta

from app.config import Settings
from app.schemas import ValidationError, parse_send_payload
from app.sms_service import SmsService


class CoreSmsGatewayTests(unittest.TestCase):
    def make_settings(self) -> Settings:
        return Settings.from_mapping(
            {
                "ORACLE_USER": "dxpt",
                "ORACLE_PASSWORD": "dxpt",
                "ORACLE_DSN": "10.45.100.147:1521/yfgxpt",
                "SMS_USERID": "admin",
                "SMS_PASSWORD": "yfga8130018",
                "SMS_DEFAULT_USERPORT": "0006",
                "SMS_BIZ_USERPORTS": "yfjcgkzx:0006,jsckgz:0007,default:0006",
            }
        )

    def test_settings_resolve_business_userport(self):
        settings = self.make_settings()

        self.assertEqual(settings.userport_for("yfjcgkzx"), "0006")
        self.assertEqual(settings.userport_for("jsckgz"), "0007")
        self.assertEqual(settings.userport_for("unknown"), "0006")

    def test_payload_builds_insert_rows_and_ignores_client_credentials(self):
        settings = self.make_settings()
        request = parse_send_payload(
            {
                "biz": "yfjcgkzx",
                "eid": "JQ202607110001",
                "mobiles": ["138-0013-8000", " 13900139000 ", "13800138000"],
                "content": " 测试短信 ",
                "userid": "bad-user",
                "password": "bad-password",
                "userport": "9999",
            },
            settings,
        )

        rows = request.to_insert_rows(settings)

        self.assertEqual([row.mobile for row in rows], ["13800138000", "13900139000"])
        self.assertEqual(rows[0].content, "测试短信")
        self.assertEqual(rows[0].eid, "JQ202607110001")
        self.assertEqual(rows[0].userid, "admin")
        self.assertEqual(rows[0].password, "yfga8130018")
        self.assertEqual(rows[0].userport, "0006")

    def test_invalid_mobile_is_rejected(self):
        settings = self.make_settings()

        with self.assertRaises(ValidationError):
            parse_send_payload(
                {
                    "biz": "yfjcgkzx",
                    "eid": "JQ202607110002",
                    "mobiles": ["12345"],
                    "content": "测试短信",
                },
                settings,
            )

    def test_service_skips_recent_duplicates_by_eid_and_mobile(self):
        now = datetime(2026, 7, 11, 10, 0, 0)
        settings = self.make_settings()
        request = parse_send_payload(
            {
                "biz": "yfjcgkzx",
                "eid": "JQ202607110003",
                "mobiles": ["13800138000", "13900139000"],
                "content": "测试短信",
                "dedup_hours": 12,
            },
            settings,
        )
        rows = request.to_insert_rows(settings)

        class FakeRepository:
            def __init__(self):
                self.inserted = []
                self.committed = False

            def last_deadtime(self, eid, mobile):
                if mobile == "13800138000":
                    return now - timedelta(hours=2)
                return None

            def insert_sms(self, row):
                self.inserted.append(row)

            def commit(self):
                self.committed = True

        repo = FakeRepository()
        service = SmsService(repo, now_func=lambda: now)

        result = service.send_rows(rows, dedup_hours=request.dedup_hours)

        self.assertEqual(result.inserted, 1)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.failed, [])
        self.assertEqual([row.mobile for row in repo.inserted], ["13900139000"])
        self.assertTrue(repo.committed)


if __name__ == "__main__":
    unittest.main()
