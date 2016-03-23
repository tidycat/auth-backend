import BaseHTTPServer
import sys
import time
import json
from auth_backend.entrypoint import handler


HOST_NAME = sys.argv[1]
PORT_NUMBER = int(sys.argv[2])


class LocalAuthenticationBackend(BaseHTTPServer.BaseHTTPRequestHandler):

    server_version = "LocalAuthBackend/0.1"

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Nothing to see here!")

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(length)
        payload = json.loads(post_data)
        result = handle_request(payload, self.headers, self.path)
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(result)


def handle_request(payload, headers, resource_path):
    event = {
        "resource-path": resource_path,
        "payload": payload
    }
    return handler(event, {})


if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), LocalAuthenticationBackend)
    print(time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
