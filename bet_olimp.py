# coding:utf-8
from utils import *
from hashlib import md5
import urllib3
from math import floor
import time
from retry_requests import requests_retry_session
from exceptions import FonbetBetError
from util_olimp import get_xtoken_bet

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_ACCOUNT = {"login": 5523988, "passw": "E506274m"}

olimp_url = "https://176.223.130.242/api/{}"
olimp_url2 = "https://10.olimp-proxy.ru/api/{}"
base_url = "https://olimp.com/api/{}"

url_test = "http://httpbin.org/delay/3"

base_payload = {"time_shift": 0, "lang_id": "0", "platforma": "ANDROID1"}

secret_key = "b2c59ba4-7702-4b12-bef5-0908391851d9"

base_headers = {
    'Accept-Encoding': 'gzip',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'okhttp/3.9.1'
}





class OlimpBot:
    """Use to place bets on olimp site."""

    def __init__(self, account: dict = DEFAULT_ACCOUNT) -> None:
        # self.session = get_session_with_proxy('')
        self.attempt_login = 0
        self.session_payload = base_payload.copy()
        self._account = account
        self.balance = 0.0
        self.matchid = None
        self.cnt_bet_attempt = 1
        self.cnt_sale_attempt = 1
        self.reg_id = None
        self.wager = None
        self.amount = None
        self.sleep = 11
        self.timeout = 50

        with open(os.path.join(package_dir, "proxies.json")) as file:
            proxies = load(file)
        session_proxies = proxies.get("olimp")

        if session_proxies:
            self.proxies = session_proxies
        else:
            self.proxies = None

    def get_reg_id(self):
        return self.reg_id

    def sign_in(self) -> None:
        try:
            """Sign in to olimp, remember session id."""
            req_url = olimp_url2.format("autorize")

            olimp_payload = {"lang_id": "0", "platforma": "ANDROID1"}
            payload = olimp_payload.copy()
            payload.update(self._account)

            headers = base_headers.copy()
            headers.update(get_xtoken_bet(payload))
            headers.update({'X-XERPC': '1'})
            resp = requests.post(
                req_url,
                headers=headers,
                data=payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies
            )
            check_status_with_resp(resp)
            prnt('BET_OLIMP.PY: Olimp, sign_in request: ' + str(resp.status_code))

            self.session_payload["session"] = resp.json()["data"]["session"]
            login_info = dict(resp.json()['data'])
            self.login_info = login_info
            self.balance = float(self.login_info.get('s'))
            prnt('BET_OLIMP.PY: balance: ' + str(self.balance))
        except Exception as e:
            self.attempt_login += 1
            if self.attempt_login > 5:
                str_err = 'Attempt login many: ' + str(self.attempt_login) + \
                          ', err: ' + str(e) + \
                          ', resp: ' + str(resp.text)
                prnt(str_err)
                time.sleep(3)
                raise ValueError(str_err)
            prnt(e)
            return self.sign_in()

    def get_balance(self):
        if self.balance == 0.0:
            self.sign_in()
            return floor(self.balance / 100) * 100
        else:
            return self.balance

    def place_bet(self, obj={}) -> None:
        """
        :param amount: amount of money to be placed (RUB)
        :param wager: defines on which wager bet is to be placed (could be either OlimpWager or OlimpCondWager)
        """
        wager = obj.get('wager_olimp')
        amount = obj.get('amount_olimp')
        if self.wager is None and wager:
            self.wager = wager
        if self.amount is None and amount:
            self.amount = amount

        if obj.get('fonbet_err', 'ok') != 'ok':
            err_str = 'BET_OLIMP.PY: Олимп получил ошибку от Фонбета: ' + str(obj.get('fonbet_err'))
            prnt(err_str)
            raise FonbetBetError(err_str)

        url = olimp_url2.format("basket/fast")

        payload = self.session_payload.copy()

        payload.update({
            "coefs_ids": '[["{apid}",{factor},1]]'.format(
                apid=self.wager.get('apid'), factor=self.wager.get('factor')),
            "sport_id": self.wager.get('sport_id'),
            "sum": self.amount,
            "save_any": 3,
            "fast": 1,
            "any_handicap": 1
        })
        # Принимать с изменёнными коэффициентами:
        # save_any: 1 - никогда, 2 - при повышении, 3 - всегда

        # Принимать с измененными тоталами/форами:
        # any_handicap: 1 - Нет, 2 - Да

        headers = base_headers.copy()
        headers.update(get_xtoken_bet(payload))

        if not self.amount <= self.balance:
            err_str = 'BET_OLIMP.PY: error amount > balance, balance:' + str(self.balance)
            prnt(err_str)
            raise LoadException(err_str)

        prnt('BET_OLIMP.PY: send bet to bk olimp, time: ' + str(datetime.datetime.now()))
        prnt('BET_OLIMP.PY: rq olimp: ' + str(payload), 'hide')
        try:
            resp = requests.post(
                url,
                headers=headers,
                data=payload,
                verify=False,
                timeout=15,
                proxies=self.proxies
            )
        except Exception as e:
            prnt('BET_OLIMP.PY: rs timeout: ' + str(e))
            self.place_bet(obj=obj)
            
        prnt('BET_OLIMP.PY: rs olimp: ' + str(resp.text), 'hide')
        
        if resp.status_code in (504, 500):
            return self.place_bet(obj=obj)
        
        check_status_with_resp(resp, True)
        res = resp.json()
        prnt('BET_OLIMP.PY: rs js olimp: ' + str(res), 'hide')

        req_time = round(resp.elapsed.total_seconds(), 2)
        n_sleep = max(0, (self.sleep - req_time))

        err_code = res.get("error", {}).get('err_code')
        err_msg = res.get("error", {}).get('err_desc')

        # {"error": {"err_code": 400, "err_desc": "Выбранный Вами исход недоступен"}, "data": null}
        # {"error": {"err_code": 417, "err_desc": "Невозможно принять ставку на указанный исход!"}, "ata": null}
        # Прием ставок приостановлен

        # {'error': {'err_code': 417, 'err_desc': 'Такой исход не существует'}, 'data': None}
        # тут ничего сделать не сможем

        # {"error": {"err_code": 417, "err_desc": "Сменился коэффициент на событие (5=>1.24)"}, "data": null}

        if err_code == 0:
            #  {'isCache': 0, 'error': {'err_code': 0, 'err_desc': None}, 'data': 'Ваша ставка успешно принята!'}
            self.matchid = self.wager['event']
            self.get_cur_max_bet_id(self.matchid)
            prnt('BET_OLIMP.PY: bet successful, reg_id: ' + str(self.reg_id))
        elif err_code in (400, 417):
            if err_code == 417 and 'Такой исход не существует' in err_msg:
                err_str = 'BET_OLIMP.PY: error place bet: ' + \
                          str(res.get("error", {}).get('err_desc'))
                prnt(err_str)
                raise LoadException(err_str)
            # MaxBet
            elif 'максимальная ставка' in err_msg:
                err_str = 'BET_OLIMP.PY: error max bet: ' + \
                          str(res.get("error", {}).get('err_desc'))
                prnt(err_str)
                raise LoadException(err_str)
            else:
                if self.cnt_bet_attempt > (60 * 0.4) / self.sleep:
                    err_str = 'BET_OLIMP.PY: error place bet: ' + \
                              str(res.get("error", {}).get('err_desc'))
                    prnt(err_str)
                    raise LoadException(err_str)

                self.cnt_bet_attempt = self.cnt_bet_attempt + 1
                prnt('BET_OLIMP.PY: ' + str(res.get("error", {}).get('err_desc')) + '. попытка #'
                     + str(self.cnt_bet_attempt) + ' через ' + str(n_sleep) + ' сек')
                time.sleep(n_sleep)
                return self.place_bet(obj=obj)
        elif "data" not in res or res.get("data") != "Ваша ставка успешно принята!":
            # res["data"] != "Your bet is successfully accepted!" :
            err_str = 'BET_OLIMP.PY: error place bet: ' + str(res)
            prnt(err_str)
            raise LoadException(err_str)
        else:
            err_str = 'BET_OLIMP.PY: error place bet: ' + str(res)
            prnt(err_str)
            raise LoadException(err_str)

    def get_cur_max_bet_id(self, event_id=None, filter="0100", offset="0"):

        if not self.session_payload.get("session"):
            self.sign_in()

        req_url = olimp_url2.format("user/history")

        payload = {}

        payload["filter"] = filter  # только не расчитанные
        payload["offset"] = offset
        payload["session"] = self.session_payload["session"]
        payload["lang_id"] = "0"
        payload["platforma"] = "ANDROID1"
        payload["time_shift"] = "0"

        headers = base_headers.copy()
        headers.update(get_xtoken_bet(payload))
        headers.update({'X-XERPC': '1'})
        prnt('BET_OLIMP.PY - get_cur_bet_id rq: ' + str(payload), 'hide')
        resp = requests.post(
            req_url,
            headers=headers,
            data=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies
        )
        prnt('BET_OLIMP.PY - get_cur_bet_id rs: ' + str(resp.text), 'hide')
        check_status_with_resp(resp)
        res = resp.json()
        prnt('BET_OLIMP.PY - get_cur_bet_id rs js: ' + str(res), 'hide')

        if res.get('error').get('err_code') != 0:
            err_str = 'BET_OLIMP.PY: error get_cur_bet_id: ' + str(res)
            prnt(err_str)
            raise LoadException(err_str)

        max_bet_id = 0
        coupon_data = {}
        # reg_id - мы знаем заранее - только при ручном выкупе как правило
        if self.reg_id:
            coupon_found = False
            for bet_list in res.get('data').get('bet_list', []):
                cur_bet_id = bet_list.get('bet_id')
                if cur_bet_id == self.reg_id:
                    coupon_found = True
                    max_bet_id = cur_bet_id
                    coupon_data = bet_list
            if not coupon_found:
                err_str = 'BET_OLIMP.PY: coupon reg_id ' + str(self.reg_id) + ' not found: ' + str(res)
                prnt(err_str)
                raise LoadException(err_str)

        # Мы не знаем reg_id и берем последний по матчу
        elif event_id:
            for bet_list in res.get('data').get('bet_list', []):
                if str(bet_list.get('events')[0].get('matchid')) == str(event_id):
                    cur_bet_id = bet_list.get('bet_id')
                    if cur_bet_id > max_bet_id:
                        max_bet_id = cur_bet_id
                        coupon_data = bet_list
        # Мы не знаем мата и берем просто последний
        else:
            for bet_list in res.get('data').get('bet_list', []):
                cur_bet_id = bet_list.get('bet_id')
                if cur_bet_id > max_bet_id:
                    max_bet_id = cur_bet_id
                    coupon_data = bet_list

        if max_bet_id:
            self.reg_id = max_bet_id
            return coupon_data

    def get_history_bet(self, event_id=None, filter="0100", offset="0"):

        if event_id and not self.matchid:
            self.matchid = event_id

        if not self.session_payload.get("session"):
            self.sign_in()

        req_url = olimp_url2.format("user/history")

        payload = {}

        payload["filter"] = filter  # только не расчитанные
        payload["offset"] = offset
        payload["session"] = self.session_payload["session"]
        payload["lang_id"] = "0"
        payload["platforma"] = "ANDROID1"
        payload["time_shift"] = "0"

        headers = base_headers.copy()
        headers.update(get_xtoken_bet(payload))
        headers.update({'X-XERPC': '1'})
        prnt('BET_OLIMP.PY - sale_bet rq hist: ' + str(payload), 'hide')
        resp = requests.post(
            req_url,
            headers=headers,
            data=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies
        )
        prnt('BET_OLIMP.PY - sale_bet rs hist: ' + str(resp.text), 'hide')
        check_status_with_resp(resp)
        res = resp.json()
        prnt('BET_OLIMP.PY - sale_bet rs js hist: ' + str(res), 'hide')
        if res.get('error').get('err_code') != 0:
            prnt('BET_OLIMP.PY: error get history: ' + str(res))
            raise LoadException("BET_OLIMP.PY: " + str(res.get('error').get('err_desc')))

        if event_id is not None:
            for bet_list in res.get('data').get('bet_list'):
                if str(bet_list.get('events')[0].get('matchid')) == str(event_id):
                    self.reg_id = bet_list.get('bet_id')
                    return {
                        'bet_id': bet_list.get('bet_id'),
                        'amount': bet_list.get('cashout_amount'),
                        'cashout_allowed': bet_list.get('cashout_allowed')
                    }
        else:
            return res.get('data')

    def sale_bet(self, reg_id=None):
        # Перезапишем ИД если он указан явно
        if not self.reg_id:
            self.reg_id = reg_id

        coupon = self.get_cur_max_bet_id(self.matchid)
        cashout_allowed = coupon.get('cashout_allowed', False)
        cashout_amount = coupon.get('cashout_amount', 0)
        prnt('BET_OLIMP: get coupon: ' + str(coupon), 'hide')
        prnt('BET_OLIMP: get coupon cashout_allowed: ' + str(cashout_allowed))
        prnt('BET_OLIMP: get coupon amount: ' + str(cashout_amount))

        if cashout_allowed is True and cashout_amount != 0:

            req_url = olimp_url2.format("user/cashout")

            payload = {}
            payload["bet_id"] = self.reg_id
            payload["amount"] = cashout_amount
            payload["session"] = self.session_payload["session"]
            payload["lang_id"] = "0"
            payload["platforma"] = "ANDROID1"

            headers = base_headers.copy()
            headers.update(get_xtoken_bet(payload))
            headers.update({'X-XERPC': '1'})
            prnt('BET_OLIMP: sale_bet rq: ' + str(payload), 'hide')
            resp = requests.post(
                req_url,
                headers=headers,
                data=payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies
            )
            prnt('BET_OLIMP: sale_bet rs: ' + str(resp.text), 'hide')
            req_time = round(resp.elapsed.total_seconds(), 2)
            check_status_with_resp(resp, True)
            res = resp.json()
            prnt('BET_OLIMP: sale_bet rs js: ' + str(res), 'hide')

            if str(res.get('error').get('err_code')) in ('406', '403'):
                if self.cnt_sale_attempt < 5:
                    prnt('BET_OLIMP.PY: error sale bet olimp: ' +
                         str(res.get('error').get('err_desc')))
                    timer_update = 4
                    prnt('BET_OLIMP.PY: wait ' + str(timer_update) + ' sec...')
                    time.sleep(timer_update)
                    self.cnt_sale_attempt = self.cnt_sale_attempt + 1
                    return self.sale_bet(self.reg_id)
                else:
                    str_err = 'BET_OLIMP.PY: error sell result: ' + str(res.get('error').get('err_desc'))
                    prnt(str_err)
                    raise LoadException(str_err)

            if str(res.get('error').get('err_code')) != str('0'):
                prnt('BET_OLIMP.PY: error sell result: ' + str(res))
                raise LoadException("BET_OLIMP.PY: response came with an error")

            if res.get('data').get('status') == 'ok':
                prnt(res.get('data').get('msg'))
        else:
            prnt('BET_OLIMP.PY: error sale bet_id ' + str(self.reg_id))
            timer_update = 5
            prnt('BET_OLIMP.PY: coupon ' + str(self.reg_id) + ' is lock, time sleep ' + str(timer_update) + ' sec...')
            time.sleep(timer_update)
            return self.sale_bet(self.reg_id)


if __name__ == '__main__':
    OLIMP_USER = {"login": "eva.yushkova.81@mail.ru", "passw": "qvF3BwrNcRcJtB6"}
    wager_olimp = {'apid': '1162886444:46453134:1:3:-9999:2:0:0:1', 'factor': '1.06', 'sport_id': 1,
                   'event': '46453134'}
    obj = {}
    obj['wager_olimp'] = wager_olimp
    obj['amount_olimp'] = 30

    olimp = OlimpBot(OLIMP_USER)
    olimp.sign_in()
    olimp.place_bet(obj)
    olimp.sale_bet()
