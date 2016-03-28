import json


def format_response(http_status_code, payload):
    response = {
        "http_status": http_status_code,
        "data": payload
    }
    if http_status_code == 200:
        return response
    raise TypeError(json.dumps(response))
