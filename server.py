#coding:utf-8
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import platform
from utils import get_param

shutdown = False
if get_param('debug'):
    DEBUG = True
else:
    DEBUG = False


def run_server(data_json):
    class HttpProcessor(BaseHTTPRequestHandler):
        def __init__(self, data_json, bar, qux, *args, **kwargs):
            self.data = json.dumps(data_json, ensure_ascii=False)
            self.bar = bar
            self.qux = qux
            # BaseHTTPRequestHandler calls do_GET **inside** __init__ !!!
            # So we have to call super().__init__ after setting attributes.
            super().__init__(*args, **kwargs)

        def do_GET(self):
            self.send_response(200)
            self.send_header('content-type', 'application/json')
            self.end_headers()
            # print('resp: ' + str(self.jstr))
            self.wfile.write(str(self.data).encode('utf-8'))

    handler = partial(HttpProcessor, data_json, 0, 0)
    if 'Windows' == platform.system() or DEBUG:
        serv = HTTPServer(("localhost", 80), handler)
    else:
        serv = HTTPServer(("149.154.70.53", 80), handler)
    serv.serve_forever()

if __name__=='__main__':
    run_server({})