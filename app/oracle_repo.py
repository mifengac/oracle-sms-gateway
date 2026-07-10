from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from .config import Settings
from .models import SmsInsertRow


_oracle_client_initialized = False


def _load_oracledb(settings: Settings) -> Any:
    global _oracle_client_initialized

    try:
        import oracledb  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing dependency: oracledb") from exc

    if settings.oracle_client_lib_dir and not _oracle_client_initialized:
        oracledb.init_oracle_client(lib_dir=settings.oracle_client_lib_dir)
        _oracle_client_initialized = True

    return oracledb


class OracleSmsRepository:
    def __init__(
        self,
        settings: Settings,
        connection: Any | None = None,
        connection_factory: Callable[[], Any] | None = None,
    ):
        self.settings = settings
        self._connection = connection
        self._connection_factory = connection_factory

    @property
    def insert_sql(self) -> str:
        return (
            f"insert into {self.settings.table_name}("
            "id,mobile,content,deadtime,status,eid,userid,password,userport"
            f") values ({self.settings.sequence_name}.nextval,:mobile,:content,sysdate,0,:eid,"
            ":userid,:password,:userport)"
        )

    @property
    def last_deadtime_sql(self) -> str:
        return (
            "SELECT MAX(deadtime) AS last_deadtime "
            f"FROM {self.settings.table_name} "
            "WHERE eid = :eid AND mobile = :mobile"
        )

    def _connect(self) -> Any:
        if self._connection_factory is not None:
            return self._connection_factory()

        oracledb = _load_oracledb(self.settings)
        return oracledb.connect(
            user=self.settings.oracle_user,
            password=self.settings.oracle_password,
            dsn=self.settings.oracle_dsn,
        )

    def connection(self) -> Any:
        if self._connection is None:
            self._connection = self._connect()
        return self._connection

    def last_deadtime(self, eid: str, mobile: str) -> datetime | None:
        with self.connection().cursor() as cur:
            cur.execute(self.last_deadtime_sql, {"eid": eid, "mobile": mobile})
            row = cur.fetchone()
        if not row or row[0] is None:
            return None
        if isinstance(row[0], datetime):
            return row[0]
        return None

    def insert_sms(self, row: SmsInsertRow) -> None:
        params = {
            "mobile": row.mobile,
            "content": row.content,
            "eid": row.eid,
            "userid": row.userid,
            "password": row.password,
            "userport": row.userport,
        }
        with self.connection().cursor() as cur:
            cur.execute(self.insert_sql, params)

    def commit(self) -> None:
        self.connection().commit()

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def ping(self) -> None:
        with self.connection().cursor() as cur:
            cur.execute("select 1 from dual")
            cur.fetchone()
