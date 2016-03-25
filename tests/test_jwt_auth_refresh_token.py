import unittest
from mock import patch
from mock import MagicMock
from auth_backend.jwt_authentication import JWTAuthentication
import json
import jwt


class TestJWTAuthRefreshToken(unittest.TestCase):

    def setUp(self):
        patcher1 = patch('auth_backend.jwt_authentication.requests')
        self.addCleanup(patcher1.stop)
        self.mock_requests = patcher1.start()

        patcher2 = patch('auth_backend.jwt_authentication.boto3')
        self.addCleanup(patcher2.stop)
        self.mock_boto = patcher2.start()

        self.jwt_signing_secret = "shh"

        token = jwt.encode({"sub": "user1"},
                           self.jwt_signing_secret,
                           algorithm='HS256')
        self.lambda_event = {
            "jwt_signing_secret": "sekr3t",
            "oauth_client_id": "c123",
            "oauth_client_secret": "shh!",
            "payload": {
                "token": token
            },
            "dynamodb_endpoint_url": "http://example.com",
            "dynamodb_table_name": "faker"
        }

    def test_invalid_jwt(self):
        payload = {"token": "fake"}
        self.lambda_event['payload'] = payload
        auth = JWTAuthentication(self.lambda_event)
        auth.jwt_signing_secret = self.jwt_signing_secret
        result = auth.refresh_jwt()
        result_json = json.loads(result)
        self.assertEqual(result_json.get('http_status'), 401)
        self.assertEqual(result_json.get('data').get('error'),
                         "Invalid JSON Web Token")
        self.assertEqual(len(self.mock_requests.mock_calls), 0)

    def test_jwt_invalid_subject_field(self):
        token = jwt.encode({"subs": "user1"},
                           self.jwt_signing_secret,
                           algorithm='HS256')
        payload = {"token": token}
        self.lambda_event['payload'] = payload
        auth = JWTAuthentication(self.lambda_event)
        auth.jwt_signing_secret = self.jwt_signing_secret
        result = auth.refresh_jwt()
        result_json = json.loads(result)
        self.assertEqual(result_json.get('http_status'), 401)
        self.assertEqual(result_json.get('data').get('error'),
                         "sub field not present in JWT")
        self.assertEqual(len(self.mock_requests.mock_calls), 0)

    def test_bearer_token_not_available(self):
        auth = JWTAuthentication(self.lambda_event)
        auth.jwt_signing_secret = self.jwt_signing_secret
        auth.lookup_bearer_token = MagicMock()
        auth.lookup_bearer_token.return_value = None
        result = auth.refresh_jwt()
        result_json = json.loads(result)
        self.assertEqual(result_json.get('http_status'), 401)
        self.assertEqual(result_json.get('data').get('error'),
                         "Could not find bearer token in datastore")
        self.assertEqual(len(self.mock_requests.mock_calls), 0)

    def test_invalid_user_id(self):
        auth = JWTAuthentication(self.lambda_event)
        auth.jwt_signing_secret = self.jwt_signing_secret
        auth.lookup_bearer_token = MagicMock()
        auth.lookup_bearer_token.return_value = "suchtoken"
        auth.retrieve_gh_user_id = MagicMock()
        auth.retrieve_gh_user_id.return_value = None
        result = auth.refresh_jwt()
        result_json = json.loads(result)
        self.assertEqual(result_json.get('http_status'), 401)
        self.assertEqual(result_json.get('data').get('error'),
                         "Could not validate bearer token")
        self.assertEqual(len(self.mock_requests.mock_calls), 0)

    def test_refresh_jwt(self):
        auth = JWTAuthentication(self.lambda_event)
        auth.jwt_signing_secret = self.jwt_signing_secret
        auth.lookup_bearer_token = MagicMock()
        auth.lookup_bearer_token.return_value = "suchtoken"
        auth.retrieve_gh_user_id = MagicMock()
        auth.retrieve_gh_user_id.return_value = "manytokenseven"
        result = auth.refresh_jwt()
        result_json = json.loads(result)
        self.assertEqual(result_json.get('http_status'), 200)
        self.assertTrue("token" in result_json.get('data'))
