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


def run_server(SERVER_IP, SERVER_PORT, forks, pair_mathes, arr_fonbet_top_matchs):
    class HttpProcessor(BaseHTTPRequestHandler):
        def __init__(self, forks, bar, qux, *args, **kwargs):
            self.data_str = json.dumps(forks, ensure_ascii=False)
            self.bar = bar
            self.qux = qux
            
            super().__init__(*args, **kwargs)

        def do_GET(self):
            ip_adr = ''
            try:
                ip_adr = str(self.client_address[0])
            except Exception as e:
                prnts(str(e))
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
            elif '/set/' in self.path:
                prnts(self.path)
                status = 'ok'
                try:
                    if 'fonbet_maxbet_fact' in self.path:
                        # expected format request like "/set/fonbet_maxbet_fact/4/100"
                        blank, action, param_name, key, group_id, value = self.path.split('/')
                        prnts('action: {}, param_name: {}, key: {}, group_id: {}, value: {}'.format(action, param_name, key, group_id, value))
                        forks[key][param_name].update({str(group_id) : int(value)})
                except Exception as e:
                    status = 'err'
                    prnts(e)
                finally:
                    self.send_response(200)
                    self.send_header('content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(str(status).encode('utf-8'))
            else:
                mutex.acquire()
                with open('access.log', 'a+', encoding='utf-8') as f:
                    f.write('ip: ' + ip_adr + ', path: ' + self.path + '\n')
                mutex.release()

    handler = partial(HttpProcessor, forks, 0, 0)
    serv = HTTPServer((SERVER_IP, SERVER_PORT), handler)
    serv.serve_forever()
