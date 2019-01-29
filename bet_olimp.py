# coding:utf-8
from utils import *
from hashlib import md5
import urllib3
from math import floor
import time
from retry_requests import requests_retry_session

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


def get_xtoken_bet(payload):
    sorted_values = [str(payload[key]) for key in sorted(payload.keys())]
    to_encode = ";".join(sorted_values + [secret_key])
    return {"X-TOKEN": md5(to_encode.encode()).hexdigest()}


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
        self.reg_id = None

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
            resp = requests_retry_session().post(
                req_url,
                headers=headers,
                data=payload,
                verify=False,
                timeout=30,
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
                raise ValueError(str_err)
            prnt(e)
            return self.sign_in()

    def get_balance(self):
        if self.balance == 0.0:
            self.sign_in()
            return floor(self.balance / 100) * 100
        else:
            return self.balance

    def place_bet(self, amount: int, wager) -> None:
        """
        :param amount: amount of money to be placed (RUB)
        :param wager: defines on which wager bet is to be placed (could be either OlimpWager or OlimpCondWager)
        """
        url = olimp_url2.format("basket/fast")

        payload = self.session_payload.copy()
        payload.update({
            "coefs_ids": '[["{apid}",{factor},1]]'.format(apid=wager.get('apid'), factor=wager.get('factor')),
            "sport_id": wager.get('sport_id'),
            "sum": amount,
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

        if not amount <= self.balance:
            prnt('BET_OLIMP.PY: balance:' + str(self.balance))
            prnt('BET_OLIMP.PY: error (amount > balance)')
            raise LoadException("BET_OLIMP.PY: amount is not in bounds")

        prnt('BET_OLIMP.PY: send bet to bk olimp, time: ' + str(datetime.datetime.now()))
        resp = requests_retry_session().post(
            url,
            headers=headers,
            data=payload,
            verify=False,
            proxies=self.proxies
        )
        prnt('BET_OLIMP.PY: response olimp: ' + str(resp.text), 'hide')
        res = resp.json()
        check_status_with_resp(resp, True)
        # {"error": {"err_code": 400, "err_desc": "Выбранный Вами исход недоступен"}, "data": null} #Прием ставок приостановлен
        # {"error": {"err_code": 417, "err_desc": "Невозможно принять ставку на указанный исход!"}, "data": null}
        if res.get("error").get('err_code') in (400, 417):
            # if self.cnt_bet_attempt > 4:
            #     prnt('BET_OLIMP.PY: error place bet in Olimp: ' + str(res))
            #     raise LoadException("BET_OLIMP.PY: error while placing the bet, attempts>" + str(self.cnt_bet_attempt))
            #
            # self.cnt_bet_attempt = self.cnt_bet_attempt + 1
            #
            # n_sleep = 5
            # prnt('BET_OLIMP.PY: ' + str(res.get("error").get('err_desc')) + '. попытка #'
            #      + str(self.cnt_bet_attempt) + ' через ' + str(n_sleep) + ' сек')
            # time.sleep(n_sleep)
            # self.place_bet(amount, wager)
            err_str = 'BET_OLIMP.PY: error place bet in Olimp: ' + str(res)
            prnt(err_str)
            raise LoadException(err_str)
        elif "data" not in res or res.get("data") != "Ваша ставка успешно принята!":
            # res["data"] != "Your bet is successfully accepted!" :
            prnt('BET_OLIMP.PY: error place bet in Olimp: ' + str(res))
            raise LoadException("BET_OLIMP.PY: error while placing the bet")
        else:
            prnt('BET_OLIMP.PY: Olimp bet successful')
            self.matchid = wager['event']
            coupon = self.get_history_bet(self.matchid)
            self.reg_id = coupon.get('bet_id')
        # TODO: 'Сменился коэффициент на событие (2=>1.95)'}, 'data': None} - Но вилка может сохраниться, повтор

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

        resp = requests_retry_session().post(
            req_url,
            headers=headers,
            data=payload,
            verify=False,
            timeout=30,
            proxies=self.proxies
        )
        check_status_with_resp(resp)
        res = resp.json()
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

    def sale_bet(self):
        if self.matchid:
            coupon = self.get_history_bet(self.matchid)
            self.reg_id = coupon.get('bet_id')

            if str(coupon.get('cashout_allowed')) == 'True' and str(coupon.get('amount')) != '0':

                req_url = olimp_url2.format("user/cashout")

                payload = {}
                payload["bet_id"] = coupon.get('bet_id')
                payload["amount"] = coupon.get('amount')
                payload["session"] = self.session_payload["session"]
                payload["lang_id"] = "0"
                payload["platforma"] = "ANDROID1"

                headers = base_headers.copy()
                headers.update(get_xtoken_bet(payload))
                headers.update({'X-XERPC': '1'})

                resp = requests_retry_session().post(
                    req_url,
                    headers=headers,
                    data=payload,
                    verify=False,
                    timeout=60,
                    proxies=self.proxies
                )
                check_status_with_resp(resp)
                res = resp.json()

                if str(res.get('error').get('err_code')) != str('0'):
                    prnt('BET_OLIMP.PY: error olimp sell result: ' + str(res))
                    raise LoadException("BET_OLIMP.PY: response came with an error")

                if res.get('data').get('status') == 'ok':
                    prnt(res.get('data').get('msg'))
            else:
                prnt('BET_OLIMP.PY: error sale bet olimp, cashout_allowed: false')
                timer_update = 5
                prnt('BET_FONBET.PY: coupon is lock, time sleep ' + str(timer_update) + ' sec...')
                time.sleep(timer_update)
                self.sale_bet()
                # raise LoadException("BET_OLIMP.PY: error sale bet olimp, cashout_allowed: false")


if __name__ == '__main__':
    OLIMP_USER = {"login": "eva.yushkova.81@mail.ru", "passw": "qvF3BwrNcRcJtB6"}
    wager_olimp = {'apid': '1118555462:45005799:1:3:-9999:3:NULL:NULL:1', 'factor': '1.4', 'sport_id': 1,
                   'event': '45005799'}
    olimp = OlimpBot(OLIMP_USER)
    olimp.sign_in()
    # olimp.place_bet(30, wager_olimp)
    # print(olimp.get_reg_id())
    # olimp.sale_bet()
    # print(olimp.get_reg_id())
