from exceptions import BetIsLost, SessionNotDefined
from math import floor
from utils import prnt, package_dir, check_status_with_resp
from time import time
from os import path
from json import load, dumps
import requests
import inspect
import sys
import traceback

# disable:
# /usr/local/lib/python3.6/site-packages/urllib3/connectionpool.py:847: 
# InsecureRequestWarning: Unverified HTTPS request is being made. 
# Adding certificate verification is strongly advised. 
# See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warningsInsecureRequestWarning)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

package_dir = path.dirname(path.abspath(__file__))

class Bk:
    
    def __init__(self, bk: str) -> None:
        self.bk = bk
        self.account = self.get_account_info()
        self.session = {}
        self.timeout = 50
        self.match_id = None
        self.reg_id = None
        self.wager = None
        self.sum_bet = None
        self.sum_sell = None
        self.attempt_login = 1
        self.attempt_bet = 1
        self.attempt_sale = 1
        self.sleep_bet = 3.51
        self.sleep_add = 0
        self.bet_type = None
        self.proxies = self.get_proxy()
        self.mirror = self.get_account_info()['mirror']
        self.server_olimp = 12
        self.err_def = self.bk+'. {}, err: {}'
        self.msg = self.bk+'. {}, msg: {}'
        self.my_name = ''
        
    def get_proxy(self) -> str:
        with open(path.join(package_dir, 'proxies.json')) as file:
            proxies = load(file)
        return proxies.get(self.bk)
        
    def get_account_info(self) -> str:
        with open(path.join(package_dir, 'account.json')) as file:
            account = load(file)
        return account.get(self.bk)
        
    def sign_in(self) -> None:
        self.my_name = inspect.stack()[0][3]
        if self.bk == 'olimp':
            try:
                from meta_ol import url_autorize, payload, head, get_xtoken_bet
                
                payload = payload.copy()
                payload.update(self.account)
    
                headers = head.copy()
                headers.update(get_xtoken_bet(payload))
                headers.update({'X-XERPC': '1'})
                
                prnt(self.msg.format(self.my_name, 'rq data: '+str(payload)), 'hide')
                resp = requests.post(
                    url_autorize.format(str(self.server_olimp),'autorize'),
                    headers=headers,
                    data=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies
                )
                prnt(self.msg.format(self.my_name, 'rs: '+str(resp.text)), 'hide')
                check_status_with_resp(resp)
                
                data = resp.json()['data']
                session_id = data.get('session')
                
                if session_id:
                    self.session['session'] = session_id
                    self.session['balance'] = float(dict(data).get('s'))
                    prnt(self.msg.format(self.my_name, 'session: '+str(self.session['session'])))
                    prnt(self.msg.format(self.my_name, 'balance: '+str(self.session['balance'])))
                else:
                    err_msg = 'session_id not defined'
                    err_str = self.err_def.format(self.my_name, err_msg)
                    raise SessionNotDefined(err_str)
            except SessionNotDefined as e:
                prnt(err_str)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_msg = 'unknown err: ' + str(e) + '. ' + \
                    str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                err_str = self.err_def.format(self.my_name, err_msg)
                prnt(err_str)
                raise ValueError(err_str)
        
        elif self.bk == 'fonbet':
            try:
                from meta_fb import base_payload, get_random_str, get_dumped_payload, get_urls, get_common_url, head
                import hmac
                from hashlib import sha512
                
                base_payload["platform"] = "mobile_android"
                base_payload["clientId"] = self.account['login']
    
                payload = base_payload
                payload["random"] = get_random_str()
                payload["sign"] = "secret password"
    
                msg = get_dumped_payload(payload)
                sign = hmac.new(key=self.account['password'].encode(), msg=msg.encode(), digestmod=sha512).hexdigest()
                payload["sign"] = sign
                data = get_dumped_payload(payload)
                
                data_urls = get_urls(self.mirror, self.proxies)
                url, self.timeout = get_common_url(data_urls)
                
                prnt(self.msg.format(self.my_name, 'rq data: '+str(data)), 'hide')
                resp = requests.post(
                    url.format("login"),
                    headers=head,
                    data=data,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies
                )
                prnt(self.msg.format(self.my_name, 'rs: '+str(resp.text)), 'hide')
                check_status_with_resp(resp)
                res = resp.json()
                
                self.session['session'] = res.get("fsid")
                self.session['balance'] = float(res.get("saldo"))
                self.session['currency'] = res.get("currency").get('currency')
                
                if not self.session.get('session'):
                    err_msg = 'session_id not defined'
                    err_str = self.err_def.format(self.my_name, err_msg)
                    raise SessionNotDefined(err_str)
                
                prnt(self.msg.format(self.my_name, 'session: '+str(self.session['session'])))
                prnt(
                    self.msg.format(
                        self.my_name, 'balance: '+ \
                        str(self.session['balance']) + ' ' + 
                        self.session['currency']
                    )
                )

            except SessionNotDefined as e:
                prnt(err_str)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_msg = 'unknown err: ' + str(e) + '. ' + \
                    str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                err_str = self.err_def.format(self.my_name, err_msg)
                prnt(err_str)
                raise ValueError(err_str)
                


class BetManager:

    def __init__(self, bk: str):
        
        if bk in ('fonbet', 'olimp'):
            self.bk = bk
        else:
            raise ValueError('bk not defined, bk=' + bk)
            
        bk = Bk(self.bk).sign_in()
        sys.exit()
 

    def trasher(self, obj: dict, vector: str, sc1: int, sc2: int, cur_total: float):
    
        self.vector = vector
        self.sc1 = int(sc1)
        self.sc2 = int(sc2)
        self.new_sc1 = None
        self.new_sc2 = None
        self.cur_total = cur_total
        self.time_start = time()

        if self.cur_total:
            self.diff_total = max(0, floor(self.cur_total - (self.sc1 + self.sc2)))
        
        if self.diff_total:
            prnt('cur diff_total: ' + str(self.diff_total))

        # update param
        new_obj = {}

        timeout_up = 60 * 10
        timeout_down = 60 * 2.5

        try:
            new_sc1 = int(new_obj['sc1'])
        except Exception as e:
            err_str = 'sc1 not not defined, {} - {}'.format(str(new_obj), str(e))
            prnt(err_str)
            raise ValueError(err_str)
        try:
            new_sc2 = int(new_obj['sc2'])
        except Exception as e:
            err_str = 'sc2 not not defined, {} - {}'.format(str(new_obj), str(e))
            prnt(err_str)
            raise ValueError(err_str)

        # check: score changed?
        if self.sc1 == new_sc1 and self.sc2 == new_sc2 and self.diff_total == 0:
            if self.vector == 'UP':
                if self.cur_total < new_sc1 + new_sc2:
                    err_str = ' cur_total:{}, new_sc1:{}, new_sc2: {}. Current bet lost... Im sorry...' \
                        .format(str(self.cur_total), str(new_sc1), str(new_sc2))
                    prnt(err_str)
                    BetIsLost(err_str)
                else:
                    # recalc sum
                    # go bets
                    pass
            elif self.vector == 'DOWN':
                if self.cur_total <= new_sc1 + new_sc2:
                    err_str = ' cur_total:{}, new_sc1:{}, new_sc2: {}. Current bet lost... Im sorry...' \
                        .format(str(self.cur_total), str(new_sc1), str(new_sc2))
                    prnt(err_str)
                    BetIsLost(err_str)
                else:
                    pass
                    # recalc sum
                    # go bets
        else:
            if self.vector == 'UP':
                pass
                # recalc sum
                # go bets
            elif self.vector == 'DOWN':
                pass
                # recalc sum
                # go bets

if __name__=='__main__':
    BetManager('fonbet')