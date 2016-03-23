import logging

__version__ = "0.0.1"
logging.basicConfig()
logger = logging.getLogger("auth_backend")
logger.setLevel(logging.DEBUG)


def handler(event, context):
    json_version = {"version": __version__}
    logger.debug("Received event: %s" % event)
    resource_path = event.get('resource-path')
    handle_event(event, context, resource_path)
    return json_version


def handle_event(event, context, resource_path):
    logger.debug("Received a request on the %s endpoint" % resource_path)
    if resource_path == "/auth/token":
        logger.debug("Handled a new token request")
    elif resource_path == "/auth/refresh":
        logger.debug("Handled a refresh token request")
    else:
        logger.debug("Unknown path: %s" % resource_path)
