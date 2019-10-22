# coding:utf-8
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import platform
import threading
import time
from utils import prnts

mutex = threading.Lock()
# json_empt = 'json_empt'


def run_server(SERVER_IP, SERVER_PORT, data_json, pair_mathes, arr_fonbet_top_matchs):
    class HttpProcessor(BaseHTTPRequestHandler):
        def __init__(self, data_json, bar, qux, *args, **kwargs):
            # global json_empt

            # prnts('pre data_str: ' + str(len(data_json)) + ', ' + str(data_json))

            # if self.path == '/get_forks':
            #     self.end_time = int(time.time()) + 20
            #     while int(time.time()) < self.end_time and not data_json:
            #         if int(time.time()) % 5 == 0:
            #             # prnts('wait...' + str(self.end_time-int(time.time())))
            #             time.sleep(0.5)
            self.data_str = json.dumps(data_json, ensure_ascii=False)
            # prnts('post data_str: ' + str(len(self.data_str)) + ', ' + str(self.data_str))
            
            # empty params
            self.bar = bar
            self.qux = qux
            
            # BaseHTTPRequestHandler calls do_GET **inside** __init__ !!!
            # So we have to call super().__init__ after setting attributes.
            super().__init__(*args, **kwargs)

        def do_GET(self):
            ip_adr = ''
            try:
                ip_adr = str(self.client_address[0])
            except Exception as e:
                print(str(e))
            if self.path == '/get_forks':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(self.data_str).encode('utf-8'))
            elif self.path == '/get_cnt_matches':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(pair_mathes).encode('utf-8'))
            elif self.path == '/get_cnt_top_matches':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(arr_fonbet_top_matchs).encode('utf-8'))
            else:
                mutex.acquire()
                with open('access.log', 'a+', encoding='utf-8') as f:
                    f.write('ip: ' + ip_adr + ', path: ' + self.path + '\n')
                mutex.release()

    handler = partial(HttpProcessor, data_json, 0, 0)
    serv = HTTPServer((SERVER_IP, SERVER_PORT), handler)
    serv.serve_forever()
