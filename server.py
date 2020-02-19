# coding:utf-8
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import platform
import threading
import time
import datetime
from utils import prnts
from urllib.parse import unquote
import sys
import traceback

mutex = threading.Lock()


# json_empt = 'json_empt'
def get_state(arr):
    state = {}
    if arr:
        info = arr
        state['name'] = info.get('name')
        state['place'] = info.get('place')
        state['liga_id'] = info.get('liga_id')
        state['last_update'] = str((int(time.time() - info.get('time_req'))))
        state['start_after_min'] = info.get('start_after_min', 0)
        state['start_time_str'] = str(datetime.datetime.fromtimestamp(int(info.get('start_time'))).strftime('%d.%m.%Y %H:%M:%S'))
        state['kofs'] = {}
        for kof_name, kof_info in info.get('kofs', {}).items():
            val = kof_info.get('value')
            hist = kof_info.get('hist')
            if val == 0:
                try:
                    state['kofs'].pop(kof_name)
                except:
                    pass
            else:
                state['kofs'].update({kof_name: {
                    'last_update': str(int(time.time() - kof_info.get('time_req'))),
                    'val': val,
                    'hist': hist
                }})
    return state


def run_server(SERVER_IP, SERVER_PORT, forks, pair_mathes, arr_top_matchs, bets, mathes_complite, arr_cupon):
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
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = str(traceback.format_exception(exc_type, exc_value, exc_traceback))
                prnts(err_str)
            if self.path == '/get_forks':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(self.data_str).encode('utf-8'))
            elif self.path == '/get_cnt_matches':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(pair_mathes + arr_cupon).encode('utf-8'))
            elif self.path == '/get_cnt_top_matches':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(arr_top_matchs.get('top', [])).encode('utf-8'))
            elif self.path == '/get_middle':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(arr_top_matchs.get('middle', [])).encode('utf-8'))
            elif self.path == '/get_slag':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(arr_top_matchs.get('slag', [])).encode('utf-8'))
            elif self.path == '/end':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(mathes_complite).encode('utf-8'))
            elif self.path == '/end/live':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(mathes_complite.get('live', [])).encode('utf-8'))
            elif self.path == '/end/pre':
                self.send_response(200)
                self.send_header('content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str(mathes_complite.get('pre', [])).encode('utf-8'))
            elif '/fonbet/' in self.path or '/olimp/' in self.path:
                cnt_par = str(self.path).count('/')
                prnts('get path: {}, cnt_par: {}, arr: {}'.format(self.path, cnt_par, str(self.path.split('/'))))
                answer = 'ok'
                branch = ''
                try:
                    answer = None
                    if cnt_par == 2:
                        balnk, bk_name, match_id = self.path.split('/')
                        answer = get_state(bets.get(match_id, {}))
                    elif cnt_par == 3:
                        balnk, bk_name, match_id, kof = self.path.split('/')
                        kof = unquote(kof)
                        answer = bets.get(match_id, {}).get('kofs', {}).get(kof)
                    if answer:
                        try:
                            answer.pop('hist')
                        except:
                            pass
                        answer = json.dumps(answer, ensure_ascii=False, indent=4)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    answer = branch + ': ' + str(traceback.format_exception(exc_type, exc_value, exc_traceback))
                    prnts(answer)
                finally:
                    self.send_response(200)
                    self.send_header('content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(str(answer).encode('utf-8'))
            elif '/set/' in self.path:
                prnts(self.path)
                status = 'ok'
                branch = ''
                try:
                    branch = 'fonbet_maxbet_fact'
                    if branch in self.path:
                        # expected format request like "/set/fonbet_maxbet_fact/4/100"
                        blank, action, param_name, key, group_id, value = self.path.split('/')
                        key = unquote(key)
                        prnts(branch + ': action: {}, param_name: {}, key: {}, group_id: {}, value: {}'.format(action, param_name, key, group_id, value))
                        old_val = forks.get(key, {}).get(param_name, {}).get(group_id, 0)
                        max_val = max(old_val, int(float(value)))
                        forks[key][param_name].update({str(group_id): max_val})
                        prnts(branch + ': group_id:{}, old_val:{}, cur_val:{}, max_val: {}'.format(group_id, old_val, value, max_val))
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    status = branch + ': ' + str(traceback.format_exception(exc_type, exc_value, exc_traceback))
                    prnts(status)
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

    try:
        handler = partial(HttpProcessor, forks, 0, 0)
        serv = HTTPServer((SERVER_IP, SERVER_PORT), handler)
        serv.serve_forever()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        prnts('server error:' + str(traceback.format_exception(exc_type, exc_value, exc_traceback)))
