import logging
from auth_backend.jwt_authentication import JWTAuthentication
from auth_backend.http import format_response

__version__ = "0.0.4"
logging.basicConfig()
logger = logging.getLogger("auth_backend")
logger.setLevel(logging.DEBUG)


def handler(event, context):
    logger.debug("Received event: %s" % event)
    resource_path = event.get('resource-path')

    if resource_path == "/auth/token":
        logger.debug("Received a new JWT token request")
        auth = JWTAuthentication(event)
        return auth.dispense_new_jwt()

    elif resource_path == "/auth/refresh":
        logger.debug("Handling a REFRESH TOKEN request")
        auth = JWTAuthentication(event)
        return auth.refresh_jwt()

    elif resource_path == "/auth/ping":
        payload = {"version": __version__}
        return format_response(200, payload)

    payload = {"error": "Invalid path %s" % resource_path}
    return format_response(400, payload)
