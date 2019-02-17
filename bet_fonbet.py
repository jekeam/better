# coding:utf-8
from random import choice, random
import hmac
from hashlib import sha512
import urllib3
from utils import *
from math import floor
import time
from retry_requests import requests_retry_session

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# "deviceid":"c2c1c82f1b9e1b8299fc3ab10e1960c8"

browser_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
}


def get_dumped_payload(payload):
    dumped = dumps(payload)
    dumped = dumped.replace(": ", ":")  # remove spaces between items
    dumped = dumped.replace(", ", ",")
    return dumped


def get_random_str():
    result = ''
    alph_num = '0123456789'
    alph = 'abcdefghijklmnopqrstuvwxyz'
    alph = alph + alph.upper() + alph_num
    for _idx in range(48):
        result += choice(alph)
    return result


DEFAULT_ACCOUNT = {"login": 5296215, "password": "Aa123456"}
url_test = "http://httpbin.org/delay/3"


class FonbetBot:
    """Use to place bets on fonbet site."""

    def __init__(self, account: dict = DEFAULT_ACCOUNT) -> None:
        self.attempt_login = 0
        self.account = account
        self.balance = 0.0
        # self.session = get_session_with_proxy('fonbet')
        self.reg_id = None
        self.wager = None
        self.cnt_bet_attempt = 1
        self.amount = None
        self.fsid = None
        self.operations = None
        self.sell_sum = None
        self.cnt_sale_attempt = 0

        with open(os.path.join(package_dir, "proxies.json")) as file:
            proxies = load(file)
        session_proxies = proxies.get('fonbet')

        if session_proxies:
            self.proxies = session_proxies
        else:
            self.proxies = None

        self.common_url = self.get_common_url()

        self.base_payload = {
            "appVersion": "5.1.3b",
            "lang": "ru",
            "rooted": "false",
            "sdkVersion": 21,
            "sysId": 4
        }

        self.payload_bet = {
            "coupon":
                {
                    "flexBet": "any",  # Изменения коэф-в, any - все, up - вверх
                    "flexParam": False,  # Изменения фор и тоталов, True - принимать, False - не принимать
                    "bets":
                        [
                            {
                                "lineType": "LIVE",
                                "score": "",
                                "value": 0,
                                "event": 0,
                                "factor": 0,
                                "num": 0
                            },
                        ],
                    "amount": 0.0,
                    "system": 0
                },
            "appVersion": "5.1.3b",
            "carrier": "MegaFon",
            "deviceManufacturer": "LENOVO",
            "deviceModel": "Lenovo A5000",
            "fsid": "",
            "lang": "ru",
            "platform": "mobile_android",
            "rooted": "false",
            "sdkVersion": 21,
            "sysId": 4,
            "clientId": 0
        }

        self.payload_req = {
            "client": {"id": 0},
            "appVersion": "5.1.3b",
            "carrier": "MegaFon",
            "deviceManufacturer": "LENOVO",
            "deviceModel": "Lenovo A5000",
            "fsid": "",
            "lang": "ru",
            "platform": "mobile_android",
            "rooted": "false",
            "sdkVersion": 21,
            "sysId": 4,
            "clientId": 0
        }

        self.fonbet_headers = {
            "User-Agent": "Fonbet/5.1.3b (Android 21; Phone; com.bkfonbet)",
            "Content-Type": "application/json; charset=UTF-8",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        # self.sign_in(account)

        self.payload_coupon_sum = {
            "clientId": "",
            "fsid": "",
            "lang": "ru",
            "platform": "mobile_android",
            "sysId": 4
        }

        self.payload_coupon_sell = {
            "flexSum": "up",
            "regId": 0,
            "requestId": 0,
            "sellSum": 0.0,
            "clientId": "",
            "fsid": "",
            "lang": "ru",
            "platform": "mobile_android",
            "sysId": 4
        }

        self.payload_sell_check_result = {
            "requestId": 0,
            "clientId": "",
            "fsid": "",
            "lang": "ru",
            "platform": "mobile_android",
            "sysId": 4
        }

        self.payload_hist = {
            "maxCount": 45,
            "fsid": "",
            "sysId": 4,
            "clientId": ""
        }

        self.coupon_info = {
            "regId": 0,
            "appVersion": "5.1.3b",
            "carrier": "MegaFon",
            "deviceManufacturer": "LENOVO",
            "deviceModel": "Lenovo A5000",
            "fsid": "",
            "lang": "ru",
            "platform": "mobile_android",
            "rooted": False,
            "sdkVersion": 21,
            "sysId": 4,
            "clientId": 0,
            "random": "",
            "sign": ""
        }

    def get_urls(self):
        url = get_account_info('fonbet', 'mirror')
        if url == '':
            url = 'www.fonbet.com'
        url = "https://" + url + "/urls.json?{}".format(random())
        resp = requests_retry_session().get(
            url,
            headers=browser_headers,
            verify=False,
            timeout=15,
            proxies=self.proxies
        )
        check_status_with_resp(resp)
        return resp.json()

    def get_common_url(self):
        urls = self.get_urls()
        client_url = urls["clients-api"][0]

        return "https:{url}/session/".format(url=client_url) + "{}"

    def get_reg_id(self):
        return self.reg_id

    def set_session_state(self):
        f = open('fonbet_session.txt', 'w+')
        f.write(self.fsid)

    def get_session_state(self):
        f = open('fonbet_session.txt', 'r')
        print(f.read().strip())

    def sign_in(self):
        try:
            self.base_payload["platform"] = "mobile_android"

            self.base_payload["clientId"] = self.account['login']

            payload = self.base_payload
            payload["random"] = get_random_str()
            payload["sign"] = "secret password"

            msg = get_dumped_payload(payload)
            sign = hmac.new(key=self.account['password'].encode(), msg=msg.encode(), digestmod=sha512).hexdigest()
            payload["sign"] = sign
            data = get_dumped_payload(payload)
            resp = requests_retry_session().post(
                self.common_url.format("login"),
                headers=self.fonbet_headers,
                data=data,
                verify=False,
                timeout=30,
                proxies=self.proxies
            )
            check_status_with_resp(resp)
            res = resp.json()
            prnt('BET_FONBET.PY: Fonbet, sign_in request: ' + str(resp.status_code))
            if "fsid" not in res:
                prnt('BET_FONBET.PY: error (fsid): ' + str(res))
                raise LoadException("BET_FONBET.PY: key 'fsid' not found in response")

            payload["fsid"] = res["fsid"]
            self.fsid = res["fsid"]

            self.balance = float(res.get("saldo"))
            self.payload = payload

            if False:
                bal_minus = 2432
                if bal_minus:
                    prnt('Баланс уменьшен искуственно на -' + str(bal_minus))
                    self.balance = self.balance - bal_minus

            prnt('BET_FONBET.PY: balance: ' + str(self.balance))

            # self._check_in_bounds(payload, 30)
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

    def _check_in_bounds(self, wager: dict, amount: int) -> None:
        """Check if amount is in allowed bounds"""
        url = self.common_url.format("coupon/getMinMax")

        payload = self.payload_bet.copy()
        headers = self.fonbet_headers

        if wager.get('param'):
            payload["coupon"]["bets"][0]["param"] = int(wager['param'])
        payload["coupon"]["bets"][0]["score"] = wager['score']
        payload["coupon"]["bets"][0]["value"] = float(wager['value'])
        payload["coupon"]["bets"][0]["event"] = int(wager['event'])
        payload["coupon"]["bets"][0]["factor"] = int(wager['factor'])

        payload['fsid'] = self.payload['fsid']
        payload['clientId'] = self.base_payload["clientId"]

        prnt('BET_FONBET.PY: check bet to bk fonbet, time: ' + str(datetime.datetime.now()))
        resp = requests_retry_session().post(
            url,
            headers=headers,
            json=payload,
            verify=False,
            timeout=15,
            proxies=self.proxies
        )
        check_status_with_resp(resp)
        res = resp.json()
        prnt('BET_FONBET.PY: Fonbet, check in bound request:' + str(resp.status_code))
        if "min" not in res:
            prnt('BET_FONBET.PY: error (min): ' + str(res))
            raise LoadException("BET_FONBET.PY: key 'min' not found in response")

        min_amount, max_amount = res["min"] // 100, res["max"] // 100
        if not (min_amount <= amount <= self.balance) or not (min_amount <= amount <= max_amount):
            prnt('BET_FONBET.PY: balance:' + str(self.balance))
            prnt('BET_FONBET.PY: error (min_amount <= amount <= max_amount|self.balance): ' + str(res))
            raise LoadException("BET_FONBET.PY: amount is not in bounds")
        prnt('BET_FONBET.PY: Min_amount=' + str(min_amount) + ' Max_amount=' + str(max_amount))

    def _get_request_id(self) -> int:
        """request_id is generated every time we placing bet"""
        url = self.common_url.format("coupon/requestId")

        headers = self.fonbet_headers

        payload_req = self.payload_req.copy()
        payload_req['fsid'] = self.payload['fsid']
        payload_req['clientId'] = self.base_payload["clientId"]
        payload_req['client']['id'] = self.base_payload["clientId"]

        resp = requests_retry_session().post(url, headers=headers, json=payload_req, verify=False, timeout=10)
        check_status_with_resp(resp)
        res = resp.json()
        if "requestId" not in res:
            prnt('BET_FONBET.PY: rror in def:_get_request_id' + str(res))
            raise LoadException("BET_FONBET.PY: key 'requestId' not found in response")
        else:
            prnt('BET_FONBET.PY: Success get requestId=' + str(res["requestId"]))
        self.payload['requestId'] = res["requestId"]
        return res["requestId"]

    def place_bet(self, amount: int, wager) -> None:
        self._get_request_id()

        if not self.wager:
            self.wager = wager
        if not self.amount:
            self.amount = amount

        url = self.common_url.format("coupon/register")

        payload = self.payload_bet.copy()
        headers = self.fonbet_headers

        payload["client"] = {"id": self.base_payload["clientId"]}

        payload["requestId"] = self.payload['requestId']

        if self.wager.get('param'):
            payload["coupon"]["bets"][0]["param"] = int(self.wager['param'])

        payload["coupon"]["bets"][0]["score"] = self.wager['score']
        payload["coupon"]["bets"][0]["value"] = float(self.wager['value'])
        payload["coupon"]["bets"][0]["event"] = int(self.wager['event'])
        payload["coupon"]["bets"][0]["factor"] = int(self.wager['factor'])

        payload['fsid'] = self.payload['fsid']
        payload['clientId'] = self.base_payload["clientId"]

        self._check_in_bounds(self.wager, self.amount)
        payload["coupon"]["amount"] = self.amount

        prnt('BET_FONBET.PY: send bet to bk fonbet, time: ' + str(datetime.datetime.now()))
        resp = requests_retry_session().post(
            url,
            headers=headers,
            json=payload,
            verify=False,
            timeout=15,
            proxies=self.proxies
        )
        prnt('BET_FONBET.PY: response fonbet: ' + str(resp.text), 'hide')
        check_status_with_resp(resp)
        res = resp.json()
        # {"result":"betDelay","betDelay":3000}
        result = res.get('result')

        if result == "betDelay":
            bet_delay_sec = (float(res.get('betDelay')) / 1000)
            prnt('BET_FONBET.PY: bet_delay: ' + str(bet_delay_sec) + ' sec...')
            time.sleep(bet_delay_sec)

        try:
            self._check_result(payload)
        except LoadException:
            prnt('BET_FONBET.PY: Get temporary unknown result, replay after 3 sec...')
            time.sleep(3)
            self._check_result(payload)

    def _check_result(self, payload: dict) -> None:
        """Check if bet is placed successfully"""
        url = self.common_url.format("coupon/result")
        try:
            del payload["coupon"]
        except:
            pass

        '''
        del wager["appVersion"]
        del wager["deviceManufacturer"]
        del wager["deviceModel"]
        del wager["platform"]
        '''

        headers = self.fonbet_headers
        resp = requests_retry_session().post(
            url,
            headers=headers,
            json=payload,
            verify=False,
            timeout=15
        )
        check_status_with_resp(resp)
        res = resp.json()

        # 100 - Блокировка по матчу: 'Ставки на событие XXX временно не принимаются'
        # 2 - Коэффициента вообще нет или котировка поменялась: 'Изменена котировка на событие XXX' - делаем выкуп
        if res.get('result') == 'couponResult' and res.get('coupon').get('resultCode') == 100:

            # self.cnt_bet_attempt = self.cnt_bet_attempt + 1
            #
            # if self.cnt_bet_attempt > 20:
            #     prnt('BET_FONBET.PY: error place bet in Fonbet: ' + str(res.get('coupon').get('errorMessageRus')))
            #     raise LoadException(
            #         "BET_FONBET.PY: error while placing the bet, attempts>" + str(self.cnt_bet_attempt))

            # n_sleep = 10
            if res.get('coupon').get('bets')[0]['value'] == 0:
                prnt('BET_FONBET.PY: error place bet in Fonbet, value is zero: '
                     + str(res.get('coupon').get('errorMessageRus')))
                raise LoadException("BET_FONBET.PY: error while placing the bet, current bet is hide!")

            # Убрал долбежку, кажется она себя не оправдывает, нужна более можщная логика.
            # prnt('BET_FONBET.PY: ' + str(res.get('coupon').get('errorMessageRus')) + ', новая котировка:'
            #      + str(res.get('coupon').get('bets')[0]['value']) + ', попытка #'
            #      + str(self.cnt_bet_attempt) + ' через ' + str(n_sleep) + ' сек')
            # time.sleep(n_sleep)
            # self.place_bet(self.amount, self.wager)
            str_err = 'BET_FONBET.PY: ' + str(res.get('coupon').get('errorMessageRus'))
            prnt(str_err)
            raise LoadException(str_err)

        # {'result': 'couponResult', 'coupon': {'resultCode': 2, 'errorMessage': 'Изменена котировка на событие "LIVE 0:0 Грузия U17 - Словакия U17 < 0.5"', 'errorMessageRus': 'Изменена котировка на событие "LIVE 0:0 Грузия U17 - Словакия U17 < 0.5"', 'errorMessageEng': 'Odds changed "LIVE 0:0 Georgia U17 - Slovakia U17 < 0.5"', 'amountMin': 30, 'amountMax': 81100, 'amount': 100, 'bets': [{'event': 13013805, 'factor': 1697, 'value': 1.37, 'param': 150, 'paramText': '1.5', 'paramTextRus': '1.5', 'paramTextEng': '1.5', 'score': '0:0'}]}}
        elif res.get('result') == 'couponResult' and str(res.get('coupon').get('resultCode')) in ('1', '2'):
            prnt('BET_FONBET.PY: error bet place result: ' + str(res.get('coupon').get('errorMessageRus')))
            raise LoadException("BET_FONBET.PY: error:" + str(res.get('coupon').get('errorMessageRus')))

        elif res.get('result') == 'couponResult' and str(res.get('coupon').get('resultCode')) == '0':
            regId = res.get('coupon').get('regId')
            prnt('BET_FONBET.PY: Fonbet bet successful, regId: ' + str(regId))
            self.reg_id = regId

        else:
            # if res.get("errorCode") != "0":
            prnt('BET_FONBET.PY: error bet place result: ' + str(res))
            raise LoadException("BET_FONBET.PY: response came with an error")

        # there's situations where "temporary unknown result" means successful response
        # if "temporary unknown result" in resp.text:
        #     prnt('BET_FONBET.PY: error bet place result: ' + str(res))
        #     raise LoadException("BET_FONBET.PY: response came with an error")

    def sale_bet(self, reg_id=None):
        """Bet return by requestID"""
        if reg_id:
            self.reg_id = reg_id

        if self.reg_id:

            # step1 get from version and sell sum
            url = self.common_url.format("coupon/sell/conditions/getFromVersion")

            url = url.replace('session/', '')

            payload = self.payload_coupon_sum.copy()
            headers = self.fonbet_headers

            payload['clientId'] = self.base_payload["clientId"]
            payload['fsid'] = self.payload['fsid']

            resp = requests_retry_session().post(
                url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=15
            )
            check_status_with_resp(resp)
            res = resp.json()
            # payload['version'] = res.get('version')

            timer_update = float(res.get('recommendedUpdateFrequency'))

            for coupon in res.get('conditions'):
                if str(coupon.get('regId')) == str(self.reg_id):
                    if str(coupon.get('canSell')) == 'True':  # TODO: coupon.get('tempBlock')
                        self.sell_sum = float(coupon.get('completeSellSum'))
                        prnt('BET_FONBET.PY: sell sum: ' + str(self.sell_sum))
                    else:
                        if self.cnt_sale_attempt > 20:
                            prnt('BET_FONBET.PY: error sale bet in Fonbet(coupon is lock): '
                                 + str(res.get('coupon').get('errorMessageRus')))
                            raise LoadException(
                                "BET_FONBET.PY: error while placing the bet, attempts>" + str(self.cnt_bet_attempt))
                        # raise LoadException("BET_FONBET.PY: coupon is lock")
                        prnt('BET_FONBET.PY: coupon is lock, time sleep ' + str(timer_update) + ' sec...')
                        self.cnt_sale_attempt = self.cnt_sale_attempt + 1
                        time.sleep(timer_update)
                        self.sale_bet()
                        return False

            if not self.sell_sum:
                if self.cnt_sale_attempt > 20:
                    prnt('BET_OLIMP.PY: error sale bet in Fonbet: ' + str(res))
                    raise LoadException("BET_OLIMP.PY: error sale bet, attempts>" + str(self.cnt_sale_attempt))
                prnt('BET_FONBET.PY: coupon is BAG (TODO), time sleep ' + str(timer_update) + ' sec...')
                prnt('BET_FONBET.PY: ' + str(res.get('conditions')))
                time.sleep(timer_update)
                self.cnt_sale_attempt = self.cnt_sale_attempt + 1
                self.sale_bet()
                return False
                # raise LoadException("BET_FONBET.PY: reg_id is not found")

            # step2 get rqid for sell coupn
            url = self.common_url.format("coupon/sell/requestId")
            url = url.replace('session/', '')

            payload = self.payload_coupon_sum.copy()
            headers = self.fonbet_headers

            payload['clientId'] = self.base_payload["clientId"]
            payload['fsid'] = self.payload['fsid']

            resp = requests_retry_session().post(
                url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=15,
                proxies=self.proxies
            )
            check_status_with_resp(resp)
            res = resp.json()
            if res.get('result') == 'requestId':
                requestId = res.get('requestId')

            # step3 sell
            url = self.common_url.format("coupon/sell/completeSell")
            url = url.replace('session/', '')

            payload = self.payload_coupon_sell.copy()
            headers = self.fonbet_headers

            payload['regId'] = int(self.reg_id)
            payload['requestId'] = int(requestId)
            payload['sellSum'] = self.sell_sum
            payload['clientId'] = self.base_payload["clientId"]
            payload['fsid'] = self.payload['fsid']

            resp = requests_retry_session().post(
                url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=15,
                proxies=self.proxies
            )
            check_status_with_resp(resp)
            res = resp.json()

            result = res.get('result')

            if result == "sellDelay":
                sell_delay_sec = (float(res.get('sellDelay')) / 1000)
                prnt('BET_FONBET.PY: sell_delay: ' + str(sell_delay_sec) + ' sec...')
                time.sleep(sell_delay_sec)

            try:
                self._check_sell_result(requestId)
            except:
                prnt('BET_FONBET.PY: error _check_sell_result: ' + str(res))
                pass

    def _check_sell_result(self, requestId: int) -> None:
        """Check if bet is placed successfully"""

        url = self.common_url.format("coupon/sell/result")
        url = url.replace('session/', '')

        payload = self.payload_sell_check_result.copy()
        headers = self.fonbet_headers

        payload['requestId'] = requestId
        payload['clientId'] = self.base_payload["clientId"]
        payload['fsid'] = self.payload['fsid']

        resp = requests_retry_session().post(
            url,
            headers=headers,
            json=payload,
            verify=False,
            timeout=15,
            proxies=self.proxies
        )
        check_status_with_resp(resp)
        res = resp.json()
        
        if res.get('result') == "sellDelay":
            sell_delay_sec = (float(res.get('sellDelay')) / 1000)
            prnt('BET_FONBET.PY: sell_delay: ' + str(sell_delay_sec) + ' sec...')
            time.sleep(sell_delay_sec)
            return self._check_sell_result(res.get('requestId'))

        if res.get('result') == 'couponCompletelySold':
            sold_sum = res.get('soldSum')
            prnt('BET_FONBET.PY: Fonbet sell successful, sold_sum: ' + str(sold_sum / 100))
            return True
        else:
            # if res.get("errorCode") != "0":
            prnt('BET_FONBET.PY: error sell result: ' + str(res))
            raise LoadException("BET_FONBET.PY: response came with an error")

    def get_operations(self, count: 45):

        url = self.common_url.format("client/lastOperations?lang=ru")

        payload = self.payload_hist.copy()
        headers = self.fonbet_headers

        payload['maxCount'] = count
        payload['clientId'] = self.base_payload["clientId"]
        payload['fsid'] = self.payload['fsid']

        resp = requests_retry_session().post(
            url,
            headers=headers,
            json=payload,
            verify=False,
            timeout=15,
            proxies=self.proxies
        )
        check_status_with_resp(resp)
        res = resp.json()

        if res.get('operations'):
            return res
        else:
            prnt('BET_FONBET.PY: error get history: ' + str(res))
            raise LoadException("BET_FONBET.PY: " + str(resp))

    def get_coupon_info(self, reg_id):
        url = self.common_url.format("coupon/info?lang")

        self.coupon_info["clientId"] = self.account['login']

        payload = self.coupon_info
        payload["random"] = get_random_str()
        payload["sign"] = "secret password"
        payload["regId"] = reg_id
        payload['fsid'] = self.payload['fsid']

        msg = get_dumped_payload(payload)
        sign = hmac.new(key=self.account['password'].encode(), msg=msg.encode(), digestmod=sha512).hexdigest()
        payload["sign"] = sign
        data = get_dumped_payload(payload)
        resp = requests_retry_session().post(
            url,
            headers=self.fonbet_headers,
            data=data,
            verify=False,
            timeout=10,
            proxies=self.proxies
        )
        check_status_with_resp(resp)
        res = resp.json()

        # if res.get("result") == "error":
        # prnt('BET_FONBET.PY: error get coupon info: ' + str(res))
        # raise LoadException("BET_FONBET.PY: " + str(res.get('errorMessage')))

        return res


if __name__ == '__main__':
    FONBET_USER = {"login": 5699838, "password": "NTe2904H11"}
    amount_fonbet = 30
    wager_fonbet = {'event': '12276286', 'factor': '921', 'param': '', 'score': '1:0', 'value': '1.2'}
    fonbet = FonbetBot(FONBET_USER)
    fonbet.sign_in()
    # fonbet.place_bet(amount_fonbet, wager_fonbet)
    # fonbet.sale_bet()
    # fonbet_reg_id = fonbet.place_bet(amount_fonbet, wager_fonbet)
    # {'e': 12264423, 'f': 931, 'v': 1.4, 'p': 250, 'pt': '2.5', 'isLive': True}