from exceptions import BetIsLost, SessionNotDefined, BkOppBetError, NoMoney, BetError, SessionExpired
from math import floor
from utils import prnt, package_dir, write_file, read_file
from time import time, sleep
from os import path
from json import load, dumps
import requests
import inspect
import sys
import traceback
from threading import Thread

# disable:
# /usr/local/lib/python3.6/site-packages/urllib3/connectionpool.py:847: 
# InsecureRequestWarning: Unverified HTTPS request is being made. 
# Adding certificate verification is strongly advised. 
# See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warningsInsecureRequestWarning)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

package_dir = path.dirname(path.abspath(__file__))

class BetManager:
    
    def __init__(self, bk_obj: dict, obj: dict, bk1: str, bk2: str) -> None:
        self.my_name = inspect.stack()[0][3]
        
        self.bk = bk1
        self.bk_opposite = bk2
        self.wager = {}
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
        self.server_olimp = 12
        self.err_def = self.bk+'. {}, err: {}'
        self.msg = self.bk+'. {}, msg: {}'
        self.mirror = self.get_account_info().get('mirror')
        self.session_file = 'session.' + self.bk
        
        err_msg = ''
        
        bk_work = ('olimp', 'fonbet')
        if (self.bk not in bk_work or self.bk_opposite not in bk_work) and 1==0:
            err_msg = 'bk not defined: bk1={}, bk2={}'.format(self.bk, self.bk_opposite)
        
        elif self.mirror is None:
            err_msg = 'mirror not defined: {}'.format(self.mirror)
        
        if err_msg != '':
            err_str = self.err_def.format(self.my_name, err_msg)
            prnt(err_str)
            raise ValueError(err_str)
        
        bk_obj[self.bk] = self
        
        self.manager(bk_obj, obj)
            
        
    def get_proxy(self) -> str:
        with open(path.join(package_dir, 'proxies.json')) as file:
            proxies = load(file)
        return proxies.get(self.bk)
        
    def get_account_info(self) -> str:
        with open(path.join(package_dir, 'account.json')) as file:
            account = load(file)
        return account.get(self.bk, {})
    
    def manager(self, bk_obj: dict, obj: dict) -> None:
        #obj['fonbet_err'] = 'bla bla bla'
        #obj['olimp_err'] = 'bla bla bla'
        
        bk_obj[self.bk].sign_in(obj)
        
        try:
            bk_obj[self.bk].place_bet(obj)
        except NoMoney as e:
            prnt(e)
        except BkOppBetError as e:
            prnt(e)
        except SessionExpired as e:
            prnt(e)
            self.sign_in(obj)
            bk_obj[self.bk].place_bet(obj)
        except Exception as e:
            prnt(e)
            
        #bk1.sale_bet()
        
    def wait_sign_in_opp(self):
        self.my_name = inspect.stack()[0][3]
        msg_push = True
        
        obj['sign_in_' + self.bk] = 'ok'
        
        while obj.get('sign_in_' + self.bk_opposite) != 'ok':
            if msg_push:
                err_str = self.err_def.format(
                    self.my_name, 
                    self.bk + ' wait sign in from ' + self.bk_opposite
                )
                prnt(err_str)
                msg_push = False
    
    def sign_in(self, obj: dict) -> None:
        self.my_name = inspect.stack()[0][3]
        if self.bk == 'olimp':
            try:
                from meta_ol import url_api, payload, head, get_xtoken_bet
                
                payload = payload.copy()
                payload.update({
                    'login' : self.account['login'],
                    'password': self.account['password']
                })
    
                headers = head.copy()
                headers.update(get_xtoken_bet(payload))
                headers.update({'X-XERPC': '1'})
                
                prnt(self.msg.format(self.my_name, 'rq: '+str(payload)), 'hide')
                resp = requests.post(
                    url_api.format(str(self.server_olimp),'autorize'),
                    headers=headers,
                    data=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies
                )
                prnt(self.msg.format(self.my_name, 'rs: '+str(resp.text.strip())), 'hide')
                
                data = resp.json()['data']
                session_id = data.get('session')
                
                if session_id:
                    self.session['session'] = session_id
                    self.session['balance'] = float(dict(data).get('s'))
                    self.session['currency'] = dict(data).get('cur')
                    prnt(self.msg.format(self.my_name, 'session: '+str(self.session['session'])))
                    prnt(
                        self.msg.format(
                            self.my_name, 
                            'balance: '+str(self.session['balance']) + ' ' + \
                            self.session['currency']
                        )
                    )
                    write_file(self.session_file, self.session['session'].strip())
                    self.wait_sign_in_opp()
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
                
                prnt(self.msg.format(self.my_name, 'rq: '+str(data)), 'hide')
                resp = requests.post(
                    url.format("login"),
                    headers=head,
                    data=data,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies
                )
                prnt(self.msg.format(self.my_name, 'rs: '+str(resp.text.strip())), 'hide')
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
                write_file(self.session_file, self.session['session'].strip())
                
                self.wait_sign_in_opp()

            except SessionNotDefined as e:
                prnt(err_str)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_msg = 'unknown err: ' + str(e) + '. ' + \
                    str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                err_str = self.err_def.format(self.my_name, err_msg)
                prnt(err_str)
                raise ValueError(err_str)
        
    def place_bet(self, obj: dict)->None:
        self.my_name = inspect.stack()[0][3]
        
        if self.bk == 'olimp':
            from meta_ol import url_api, payload, head, get_xtoken_bet
            
            self.wager = obj.get('wager')
            self.sum_bet = obj.get('amount')
            
            cur_bal = self.session.get('balance')
            if cur_bal and self.sum_bet < cur_bal:
                err_str = self.err_def.format(
                    self.my_name, 
                    self.bk + ' balance < sum_bet, balance: ' + cur_bal
                )
                raise NoMoney(err_str)
    
    
            opposite_stat = str(obj.get(self.bk_opposite + '_err', 'ok'))
            if opposite_stat != 'ok':
                err_str = self.err_def.format(
                    self.my_name, 
                    self.bk + ' get error from ' + self.bk_opposite + ': ' + opposite_stat
                )
                raise BkOppBetError(err_str)
    
            url = url_api.format(self.server_olimp, "basket/fast")
    
            payload = payload.copy()
            
            self.session['session'] = None
            if not self.session['session']:
                self.session['session'] = read_file(self.session_file)
    
            payload.update({
                "coefs_ids": '[["{apid}",{factor},1]]'.format(
                    apid=self.wager.get('apid'), factor=self.wager.get('factor')),
                "sport_id": self.wager.get('sport_id'),
                "sum": self.sum_bet,
                "save_any": 3,
                "fast": 1,
                "any_handicap": 1,
                'session': self.session['session']
            })
            # Принимать с изменёнными коэффициентами:
            # save_any: 1 - никогда, 2 - при повышении, 3 - всегда
            
            # Принимать с измененными тоталами/форами:
            # any_handicap: 1 - Нет, 2 - Да
        
            headers = head.copy()
            headers.update(get_xtoken_bet(payload))
            
            prnt(self.msg.format(self.my_name, 'rq: '+str(payload)), 'hide')
            resp = requests.post(
                url,
                headers=headers,
                data=payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies
            )
            prnt(self.msg.format(self.my_name, 'rs: '+str(resp.text.strip())), 'hide')
            res = resp.json()
    
            req_time = round(resp.elapsed.total_seconds(), 2)
    
            err_code = res.get("error", {}).get('err_code')
            err_msg = res.get("error", {}).get('err_desc')
            
            if err_code == 401 and 'не вошли в систему' in err_msg:
                err_str = self.err_def.format(
                    self.my_name, 
                    self.bk + ' session expired: ' + self.session['session']
                )
                prnt(err_str)
                raise SessionExpired(err_str)
            
            #{"error":{"err_code":401,"err_desc":"У Вас нет доступа к этой зоне, т.к. Вы не вошли в систему!"},"data":null}
            
            '''
    
            if err_code == 0:
                self.matchid = self.wager['event']
                self.get_cur_max_bet_id(self.matchid)
                prnt('BET_OLIMP.PY: bet successful, reg_id: ' + str(self.reg_id))
            elif err_code in (400, 417):
                if err_code == 417 and 'Такой исход не существует' in err_msg:
                    err_str = 'BET_OLIMP.PY: error place bet: ' + \
                              str(res.get("error", {}).get('err_desc'))
                    prnt(err_str)
                    raise BetError(err_str)
                # MaxBet
                elif 'максимальная ставка' in err_msg:
                    err_str = 'BET_OLIMP.PY: error max bet: ' + \
                              str(res.get("error", {}).get('err_desc'))
                    prnt(err_str)
                    raise BetError(err_str)
                else:
                    if self.cnt_bet_attempt > (60 * 0.4) / self.sleep:
                        err_str = 'BET_OLIMP.PY: error place bet: ' + \
                                  str(res.get("error", {}).get('err_desc'))
                        prnt(err_str)
                        raise BetError(err_str)
    
                    self.cnt_bet_attempt = self.cnt_bet_attempt + 1
                    prnt('BET_OLIMP.PY: ' + str(res.get("error", {}).get('err_desc')) + '. попытка #'
                         + str(self.cnt_bet_attempt) + ' через ' + str(n_sleep) + ' сек')
                    time.sleep(n_sleep)
                    return self.place_bet(obj=obj)
            elif "data" not in res or res.get("data") != "Ваша ставка успешно принята!":
                err_str = 'BET_OLIMP.PY: error place bet: ' + str(res)
                prnt(err_str)
                raise BetError(err_str)
                    
        if self.bk == 'fonbet':
            pass
        '''

    def finishing(self, obj: dict, vector: str, sc1: int, sc2: int, cur_total: float) -> None:
    
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

    bk_obj = {}
    
    
    OLIMP_USER = {"login": "eva.yushkova.81@mail.ru", "passw": "qvF3BwrNcRcJtB6"}
    wager_olimp = {'apid': '1162886444:46453134:1:3:-9999:2:0:0:1', 'factor': '1.06', 'sport_id': 1,
                   'event': '46453134'}
    obj = {}
    obj['wager'] = wager_olimp
    obj['amount'] = 30
    
    bk1 = Thread(target=BetManager, args=(bk_obj, obj, 'olimp', 'fonbet'))
    bk2 = Thread(target=BetManager, args=(bk_obj, obj, 'fonbet', 'olimp'))
    
    bk1.start()
    bk2.start()
    
    bk1.join()
    bk2.join()