from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request

from .config import Settings
from .oracle_repo import OracleSmsRepository
from .schemas import ValidationError, parse_send_payload
from .security import is_authorized
from .sms_service import SmsService


settings = Settings.from_env()
app = FastAPI(title="Oracle SMS Gateway", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"success": True, "status": "ok"}


@app.get("/ready")
def ready(request: Request) -> dict:
    if not is_authorized(request.headers, settings.api_token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    repo = OracleSmsRepository(settings)
    try:
        repo.ping()
        return {"success": True, "oracle": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        repo.close()


@app.post("/api/v1/sms/send")
async def send_sms(request: Request) -> dict:
    if not is_authorized(request.headers, settings.api_token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = await request.json()
        send_request = parse_send_payload(payload, settings)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc

    repo = OracleSmsRepository(settings)
    service = SmsService(repo)
    try:
        rows = send_request.to_insert_rows(settings)
        result = service.send_rows(rows, dedup_hours=send_request.dedup_hours)
        return {
            "success": len(result.failed) == 0,
            "inserted": result.inserted,
            "skipped": result.skipped,
            "failed": [item.__dict__ for item in result.failed],
            "total": len(rows),
        }
    finally:
        repo.close()
