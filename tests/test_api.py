import unittest
from unittest.mock import patch

try:
    from fastapi.testclient import TestClient
    from app import main as main_module

    HAS_FASTAPI = True
except (ModuleNotFoundError, RuntimeError):
    TestClient = None
    main_module = None
    HAS_FASTAPI = False


@unittest.skipUnless(HAS_FASTAPI, "FastAPI test client is not available")
class ApiTests(unittest.TestCase):
    def test_health_returns_ok(self):
        client = TestClient(main_module.app)

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "status": "ok"})

    def test_ready_returns_503_json_when_oracle_is_unavailable(self):
        class BrokenRepository:
            def __init__(self, settings):
                self.settings = settings

            def ping(self):
                raise RuntimeError("oracle client unavailable")

            def close(self):
                pass

        client = TestClient(main_module.app, raise_server_exceptions=False)

        with patch.object(main_module, "OracleSmsRepository", BrokenRepository):
            response = client.get(
                "/ready",
                headers={"X-API-Key": main_module.settings.api_token},
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("oracle client unavailable", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
