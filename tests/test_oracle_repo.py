import unittest
from datetime import datetime

from app.config import Settings
from app.models import SmsInsertRow
from app.oracle_repo import OracleSmsRepository


class FakeCursor:
    def __init__(self, row=None):
        self.row = row
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, params or {}))

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row=None):
        self.cursor_obj = FakeCursor(row=row)
        self.committed = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


class OracleRepositoryTests(unittest.TestCase):
    def make_settings(self) -> Settings:
        return Settings.from_mapping(
            {
                "ORACLE_USER": "dxpt",
                "ORACLE_PASSWORD": "dxpt",
                "ORACLE_DSN": "10.45.100.147:1521/yfgxpt",
                "SMS_USERID": "admin",
                "SMS_PASSWORD": "yfga8130018",
                "SMS_DEFAULT_USERPORT": "0006",
                "SMS_BIZ_USERPORTS": "default:0006",
            }
        )

    def test_insert_sms_uses_sequence_sysdate_status_zero_and_bound_params(self):
        conn = FakeConnection()
        repo = OracleSmsRepository(self.make_settings(), connection=conn)
        row = SmsInsertRow(
            mobile="13800138000",
            content="测试短信",
            eid="JQ202607110004",
            userid="admin",
            password="yfga8130018",
            userport="0006",
        )

        repo.insert_sms(row)

        sql, params = conn.cursor_obj.calls[0]
        self.assertIn("insert into yfgadb.dfsdl", sql)
        self.assertIn("yfgadb.seq_sendsms.nextval", sql)
        self.assertIn("sysdate", sql)
        self.assertIn(":mobile", sql)
        self.assertIn(":content", sql)
        self.assertEqual(params["mobile"], "13800138000")
        self.assertEqual(params["content"], "测试短信")
        self.assertEqual(params["eid"], "JQ202607110004")
        self.assertEqual(params["userid"], "admin")
        self.assertEqual(params["password"], "yfga8130018")
        self.assertEqual(params["userport"], "0006")

    def test_last_deadtime_reads_max_deadtime_by_eid_and_mobile(self):
        expected = datetime(2026, 7, 11, 9, 30, 0)
        conn = FakeConnection(row=(expected,))
        repo = OracleSmsRepository(self.make_settings(), connection=conn)

        actual = repo.last_deadtime("JQ202607110005", "13800138000")

        sql, params = conn.cursor_obj.calls[0]
        self.assertIn("SELECT MAX(deadtime)", sql)
        self.assertIn("WHERE eid = :eid AND mobile = :mobile", sql)
        self.assertEqual(params, {"eid": "JQ202607110005", "mobile": "13800138000"})
        self.assertEqual(actual, expected)

    def test_commit_and_close_delegate_to_connection(self):
        conn = FakeConnection()
        repo = OracleSmsRepository(self.make_settings(), connection=conn)

        repo.commit()
        repo.close()

        self.assertTrue(conn.committed)
        self.assertTrue(conn.closed)


if __name__ == "__main__":
    unittest.main()
