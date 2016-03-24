import json


def format_response(http_status_code, payload):
    response = {
        "http_status": http_status_code,
        "data": payload
    }
    return json.dumps(response)
