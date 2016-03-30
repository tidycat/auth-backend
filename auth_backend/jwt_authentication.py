import logging
import requests
import jwt
import datetime
import boto3
from auth_backend.http import format_response


logger = logging.getLogger("auth_backend")


class JWTAuthentication(object):

    def __init__(self, lambda_event):
        for prop in ["payload",
                     "jwt_signing_secret",
                     "oauth_client_id",
                     "oauth_client_secret",
                     "auth_dynamodb_endpoint_url",
                     "dynamodb_table_name"]:
            setattr(self, prop, lambda_event.get(prop))
        self.expected_oauth_scopes = ['user']

    def dispense_new_jwt(self):
        temp_access_code = self.payload.get("password")

        if not temp_access_code:
            error_msg = "\'password\' field not found: %s" % self.payload
            logger.warning(error_msg)
            return format_response(400, {"error": error_msg})

        bearer_token = self.retrieve_bearer_token(temp_access_code)
        if not bearer_token:
            error_msg = "Not Authorized"
            logger.info(error_msg)
            return format_response(401, {"error": error_msg})

        userid, login = self.retrieve_gh_user_info(bearer_token)
        if not (userid and login):
            error_msg = "Could not find GitHub user information"
            logger.info(error_msg)
            return format_response(401, {"error": error_msg})

        if not self.store_bearer_token(userid, bearer_token):
            error_msg = "Unable to persist bearer token"
            logger.error(error_msg)
            return format_response(500, {"error": error_msg})

        return self.format_jwt(userid, login, bearer_token)

    def refresh_jwt(self):
        current_jwt = self.payload.get("token")
        decoded_token = ""
        try:
            decoded_token = jwt.decode(current_jwt, self.jwt_signing_secret)
        except jwt.exceptions.InvalidTokenError:
            error_msg = "Invalid JSON Web Token"
            logger.info(error_msg)
            return format_response(401, {"error": error_msg})

        userid = decoded_token.get('sub')
        if not userid:
            error_msg = "sub field not present in JWT"
            logger.info(error_msg)
            return format_response(401, {"error": error_msg})

        bearer_token = self.lookup_bearer_token(userid)
        if not bearer_token:
            error_msg = "Could not find bearer token in datastore"
            logger.info(error_msg)
            return format_response(401, {"error": error_msg})

        userid, login = self.retrieve_gh_user_info(bearer_token)
        if not (userid and login):
            error_msg = "Could not validate bearer token"
            logger.info(error_msg)
            return format_response(401, {"error": error_msg})

        return self.format_jwt(userid, login, bearer_token)

    def retrieve_bearer_token(self, access_code):
        payload = {
            "client_id": self.oauth_client_id,
            "client_secret": self.oauth_client_secret,
            "code": access_code
        }
        r = requests.post("https://github.com/login/oauth/access_token",
                          data=payload,
                          headers={"Accept": "application/json"})
        if not r.status_code == 200:
            logger.info("Could not exchange access code %s for bearer token"
                        % access_code)
            logger.info("HTTP response code from GitHub: %s" % r.status_code)
            logger.debug("URL: %s" % r.url)
            logger.debug("Headers: %s" % r.headers)
            logger.debug("Response: %s" % r.text)
            return None

        gh_response = r.json()
        if not self.are_scopes_sufficient(gh_response['scope']):
            error_msg = "Need the following GitHub scopes: %s" % ','.join(self.expected_oauth_scopes)  # NOQA
            logger.info(error_msg)
            return None

        return gh_response['access_token']

    def are_scopes_sufficient(self, scopes):
        scope_list = scopes.split(',')
        return set(self.expected_oauth_scopes).issubset(set(scope_list))

    def retrieve_gh_user_info(self, bearer_token):
        r = requests.get(
            'https://api.github.com/applications/%s/tokens/%s' % (self.oauth_client_id, bearer_token),  # NOQA
            auth=(self.oauth_client_id, self.oauth_client_secret)
        )
        if not r.status_code == 200:
            logger.info("Could not retrieve user information")
            logger.info("HTTP response code from GitHub: %s" % r.status_code)
            logger.debug("URL: %s" % r.url)
            logger.debug("Headers: %s" % r.headers)
            logger.debug("Response: %s" % r.text)
            return (None, None)
        gh_response = r.json()
        return (gh_response.get('user').get('id'),
                gh_response.get('user').get('login'))

    def format_jwt(self, userid, login, bearer_token):
        data = {
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
            "sub": userid,
            "github_login": login,
            "github_token": bearer_token
        }
        encoded = jwt.encode(data, self.jwt_signing_secret, algorithm='HS256')
        return format_response(200, {"token": encoded})

    def lookup_bearer_token(self, user_id):  # pragma: no cover
        try:
            dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=self.auth_dynamodb_endpoint_url
            )
            table = dynamodb.Table(self.dynamodb_table_name)
            response = table.get_item(Key={"user_id": user_id})
            return response['Item'].get('bearer_token')
        except boto3.exceptions.Boto3Error as e:
            logger.error("Error querying the datastore: %s" % str(e))
        return None

    def store_bearer_token(self, user_id, bearer_token):  # pragma: no cover
        try:
            dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=self.auth_dynamodb_endpoint_url
            )
            table = dynamodb.Table(self.dynamodb_table_name)
            item = {
                "user_id": user_id,
                "bearer_token": bearer_token
            }
            table.put_item(Item=item)
        except boto3.exceptions.Boto3Error as e:
            logger.error("Error persisting bearer token: %s" % str(e))
            return False
        return True
