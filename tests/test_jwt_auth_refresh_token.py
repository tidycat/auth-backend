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
            "auth_dynamodb_endpoint_url": "http://example.com",
            "dynamodb_table_name": "faker"
        }

    def test_invalid_jwt(self):
        payload = {"token": "fake"}
        self.lambda_event['payload'] = payload
        auth = JWTAuthentication(self.lambda_event)
        auth.jwt_signing_secret = self.jwt_signing_secret
        with self.assertRaises(TypeError) as cm:
            auth.refresh_jwt()
        result_json = json.loads(str(cm.exception))
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
        with self.assertRaises(TypeError) as cm:
            auth.refresh_jwt()
        result_json = json.loads(str(cm.exception))
        self.assertEqual(result_json.get('http_status'), 401)
        self.assertEqual(result_json.get('data').get('error'),
                         "sub field not present in JWT")
        self.assertEqual(len(self.mock_requests.mock_calls), 0)

    def test_bearer_token_not_available(self):
        auth = JWTAuthentication(self.lambda_event)
        auth.jwt_signing_secret = self.jwt_signing_secret
        auth.lookup_bearer_token = MagicMock()
        auth.lookup_bearer_token.return_value = None
        with self.assertRaises(TypeError) as cm:
            auth.refresh_jwt()
        result_json = json.loads(str(cm.exception))
        self.assertEqual(result_json.get('http_status'), 401)
        self.assertEqual(result_json.get('data').get('error'),
                         "Could not find bearer token in datastore")
        self.assertEqual(len(self.mock_requests.mock_calls), 0)

    def test_invalid_user_id(self):
        auth = JWTAuthentication(self.lambda_event)
        auth.jwt_signing_secret = self.jwt_signing_secret
        auth.lookup_bearer_token = MagicMock()
        auth.lookup_bearer_token.return_value = "suchtoken"
        auth.retrieve_gh_user_info = MagicMock()
        auth.retrieve_gh_user_info.return_value = (None, None)
        with self.assertRaises(TypeError) as cm:
            auth.refresh_jwt()
        result_json = json.loads(str(cm.exception))
        self.assertEqual(result_json.get('http_status'), 401)
        self.assertEqual(result_json.get('data').get('error'),
                         "Could not validate bearer token")
        self.assertEqual(len(self.mock_requests.mock_calls), 0)

    def test_refresh_jwt(self):
        auth = JWTAuthentication(self.lambda_event)
        auth.jwt_signing_secret = self.jwt_signing_secret
        auth.lookup_bearer_token = MagicMock()
        auth.lookup_bearer_token.return_value = "suchtoken"
        auth.retrieve_gh_user_info = MagicMock()
        auth.retrieve_gh_user_info.return_value = ("manytokenseven", "bob")
        result = auth.refresh_jwt()
        self.assertEqual(result.get('http_status'), 200)
        self.assertTrue("token" in result.get('data'))

    def test_github_token_field_presence(self):
        token = jwt.encode({"sub": "user1"},
                           self.jwt_signing_secret,
                           algorithm='HS256')
        payload = {"token": token}
        self.lambda_event['payload'] = payload
        auth = JWTAuthentication(self.lambda_event)
        result = auth.format_jwt("123", "bob", "bobstoken")
        self.assertEqual(result.get('http_status'), 200)
        jwt_token = result.get('data').get('token')
        decoded_token = jwt.decode(jwt_token, verify=False)
        self.assertEqual(decoded_token.get('github_login'), "bob")
        self.assertEqual(decoded_token.get('github_token'), "bobstoken")
