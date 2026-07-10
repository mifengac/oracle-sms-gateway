import unittest

from app.security import is_authorized


class SecurityTests(unittest.TestCase):
    def test_empty_configured_token_allows_internal_request(self):
        self.assertTrue(is_authorized({}, ""))

    def test_x_api_key_authorizes_request(self):
        self.assertTrue(is_authorized({"x-api-key": "secret"}, "secret"))

    def test_bearer_token_authorizes_request(self):
        self.assertTrue(is_authorized({"authorization": "Bearer secret"}, "secret"))

    def test_wrong_token_rejects_request(self):
        self.assertFalse(is_authorized({"x-api-key": "wrong"}, "secret"))


if __name__ == "__main__":
    unittest.main()
