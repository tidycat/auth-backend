import unittest
from mock import patch
from mock import call
from auth_backend.entrypoint import handler
import json


class TestEntrypoint(unittest.TestCase):

    def setUp(self):
        patcher1 = patch('auth_backend.entrypoint.JWTAuthentication')
        self.addCleanup(patcher1.stop)
        self.mock_jwt_auth = patcher1.start()

    def test_invalid_path(self):
        with self.assertRaises(TypeError) as cm:
            handler({"resource-path": "/"}, {})
        result_json = json.loads(str(cm.exception))
        self.assertEqual(result_json.get('http_status'), 400)
        self.assertEqual(result_json.get('data').get('error'),
                         "Invalid path /")
        self.assertEqual(len(self.mock_jwt_auth.mock_calls), 0)

    def test_ping_endpoint(self):
        result = handler({"resource-path": "/auth/ping"}, {})
        self.assertEqual(result.get('http_status'), 200)
        self.assertTrue("version" in result.get('data'))
        self.assertEqual(len(self.mock_jwt_auth.mock_calls), 0)

    def test_token_endpoint(self):
        handler({"resource-path": "/auth/token"}, {})
        self.assertTrue(call({'resource-path': '/auth/token'}) in self.mock_jwt_auth.mock_calls)  # NOQA
        self.assertTrue(call().dispense_new_jwt() in self.mock_jwt_auth.mock_calls)  # NOQA
        self.assertEqual(len(self.mock_jwt_auth.mock_calls), 2)

    def test_refresh_endpoint(self):
        handler({"resource-path": "/auth/refresh"}, {})
        self.assertTrue(call({'resource-path': '/auth/refresh'}) in self.mock_jwt_auth.mock_calls)  # NOQA
        self.assertTrue(call().refresh_jwt() in self.mock_jwt_auth.mock_calls)  # NOQA
        self.assertEqual(len(self.mock_jwt_auth.mock_calls), 2)
