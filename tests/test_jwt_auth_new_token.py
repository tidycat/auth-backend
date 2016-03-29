import unittest
from mock import patch
from mock import MagicMock
from auth_backend.jwt_authentication import JWTAuthentication
import json


class TestJWTAuthNewToken(unittest.TestCase):

    def setUp(self):
        patcher1 = patch('auth_backend.jwt_authentication.requests')
        self.addCleanup(patcher1.stop)
        self.mock_requests = patcher1.start()

        patcher2 = patch('auth_backend.jwt_authentication.boto3')
        self.addCleanup(patcher2.stop)
        self.mock_boto = patcher2.start()

        self.lambda_event = {
            "jwt_signing_secret": "sekr3t",
            "oauth_client_id": "c123",
            "oauth_client_secret": "shh!",
            "payload": {
                "password": "temptoken123"
            },
            "dynamodb_endpoint_url": "http://example.com",
            "dynamodb_table_name": "faker"
        }

    def test_empty_temp_access_code(self):
        payload = {"password": ""}
        self.lambda_event['payload'] = payload
        jwt = JWTAuthentication(self.lambda_event)
        with self.assertRaises(TypeError) as cm:
            jwt.dispense_new_jwt()
        result_json = json.loads(str(cm.exception))
        self.assertEqual(result_json.get('http_status'), 400)
        self.assertEqual(len(self.mock_requests.mock_calls), 0)

    def test_invalid_temp_access_code(self):
        self.mock_requests.post = MagicMock()
        self.mock_requests.post.return_value.status_code = 100
        payload = {"password": "code123"}
        self.lambda_event['payload'] = payload
        jwt = JWTAuthentication(self.lambda_event)
        with self.assertRaises(TypeError) as cm:
            jwt.dispense_new_jwt()
        result_json = json.loads(str(cm.exception))
        self.assertEqual(result_json.get('http_status'), 401)
        self.assertEqual(result_json.get('data').get('error'),
                         "Not Authorized")

    def test_insufficient_scopes(self):
        self.mock_requests.post = MagicMock()
        self.mock_requests.post.return_value.status_code = 200
        self.mock_requests.post.return_value.json.return_value = {
            "scope": "none"
        }
        payload = {"password": "code123"}
        self.lambda_event['payload'] = payload
        jwt = JWTAuthentication(self.lambda_event)
        jwt.expected_oauth_scopes = ['bob']
        with self.assertRaises(TypeError) as cm:
            jwt.dispense_new_jwt()
        result_json = json.loads(str(cm.exception))
        self.assertEqual(result_json.get('http_status'), 401)
        self.assertEqual(result_json.get('data').get('error'),
                         "Not Authorized")

    def test_invalid_user_id(self):
        self.mock_requests.post = MagicMock()
        self.mock_requests.post.return_value.status_code = 200
        self.mock_requests.post.return_value.json.return_value = {
            "scope": "user",
            "access_token": "verytoken"
        }
        payload = {"password": "code123"}
        self.lambda_event['payload'] = payload
        jwt = JWTAuthentication(self.lambda_event)
        jwt.expected_oauth_scopes = ['user']
        self.mock_requests.get = MagicMock()
        self.mock_requests.get.return_value.status_code = 100
        with self.assertRaises(TypeError) as cm:
            jwt.dispense_new_jwt()
        result_json = json.loads(str(cm.exception))
        self.assertEqual(result_json.get('http_status'), 401)
        self.assertEqual(result_json.get('data').get('error'),
                         "Could not find GitHub user information")

    def test_unable_to_persist_bearer_token(self):
        payload = {"password": "code123"}
        self.lambda_event['payload'] = payload
        jwt = JWTAuthentication(self.lambda_event)
        jwt.retrieve_bearer_token = MagicMock()
        jwt.retrieve_bearer_token.return_value = "suchtokenWow"
        self.mock_requests.get = MagicMock()
        self.mock_requests.get.return_value.status_code = 200
        self.mock_requests.get.return_value.json.return_value = {
            "user": {
                "id": "u123",
                "login": "bob"
            }
        }
        jwt.store_bearer_token = MagicMock()
        jwt.store_bearer_token.return_value = False
        with self.assertRaises(TypeError) as cm:
            jwt.dispense_new_jwt()
        result_json = json.loads(str(cm.exception))
        self.assertEqual(result_json.get('http_status'), 500)
        self.assertEqual(result_json.get('data').get('error'),
                         "Unable to persist bearer token")

    def test_get_new_jwt(self):
        payload = {"password": "code123"}
        self.lambda_event['payload'] = payload
        jwt = JWTAuthentication(self.lambda_event)
        jwt.retrieve_bearer_token = MagicMock()
        jwt.retrieve_bearer_token.return_value = "suchtokenWow"
        self.mock_requests.get = MagicMock()
        self.mock_requests.get.return_value.status_code = 200
        self.mock_requests.get.return_value.json.return_value = {
            "user": {
                "id": "u123",
                "login": "bob"
            }
        }
        jwt.store_bearer_token = MagicMock()
        jwt.store_bearer_token.return_value = True
        result = jwt.dispense_new_jwt()
        self.assertEqual(result.get('http_status'), 200)
        self.assertTrue("token" in result.get('data'))
