# coding:utf-8
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import platform


def run_server(SERVER_IP, data_json, pair_mathes):
    class HttpProcessor(BaseHTTPRequestHandler):
        def __init__(self, data_json, bar, qux, *args, **kwargs):
            self.data = json.dumps(data_json, ensure_ascii=False)
            self.bar = bar
            self.qux = qux
            # BaseHTTPRequestHandler calls do_GET **inside** __init__ !!!
            # So we have to call super().__init__ after setting attributes.
            super().__init__(*args, **kwargs)

        def do_GET(self):
            print(self.path)
            print(len(pair_mathes))
            self.send_response(200)
            self.send_header('content-type', 'application/json')
            self.end_headers()
            # print('resp: ' + str(self.jstr))
            self.wfile.write(str(self.data).encode('utf-8'))

    handler = partial(HttpProcessor, data_json, 0, 0)
    serv = HTTPServer((SERVER_IP, 80), handler)
    serv.serve_forever()
