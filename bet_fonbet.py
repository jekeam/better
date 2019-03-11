# coding:utf-8
from random import choice, random
import hmac
from hashlib import sha512
import urllib3
from utils import *
from math import floor
import time
from retry_requests import requests_retry_session
from exceptions import OlimpBetError

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
        self.sleep = 4
        self.cnt_test = 0
        self.add_sleep = 0
        self.timeout = 15
        self.fonbet_bet_type = None

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
            "rooted": False,
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
            "rooted": False,
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
            "rooted": False,
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
            timeout=self.timeout,
            proxies=self.proxies
        )
        check_status_with_resp(resp)
        return resp.json()

    def get_common_url(self):
        urls = self.get_urls()
        client_url = urls["clients-api"][0]
        self.timeout = urls["timeout"] / 100
        prnt('BET_FONBET.PY: set timeout: ' + str(self.timeout))

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
                timeout=self.timeout,
                proxies=self.proxies
            )
            check_status_with_resp(resp)
            res = resp.json()
            prnt('BET_FONBET.PY: Fonbet, sign_in request: ' + str(resp.status_code))
            if "fsid" not in res:
                err_str = 'BET_FONBET.PY: key "fsid" not found in response: ' + str(res)
                prnt(err_str)
                raise LoadException("BET_FONBET.PY: " + err_str)

            payload["fsid"] = res["fsid"]
            self.fsid = res["fsid"]

            self.balance = float(res.get("saldo"))
            self.payload = payload
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
            timeout=self.timeout,
            proxies=self.proxies
        )
        check_status_with_resp(resp)
        res = resp.json()
        prnt('BET_FONBET.PY: Fonbet, check in bound request:' + str(resp.status_code))
        if "min" not in res:
            err_str = 'BET_FONBET.PY: error (min): ' + str(res)
            prnt(err_str)
            raise LoadException(err_str)

        min_amount, max_amount = res["min"] // 100, res["max"] // 100
        if not (min_amount <= amount <= self.balance) or not (min_amount <= amount <= max_amount):
            prnt('BET_FONBET.PY: balance:' + str(self.balance))
            err_str = 'BET_FONBET.PY: error (min_amount <= amount <= max_amount|' + str(self.balance) + '): ' + str(res)
            prnt(err_str)
            raise LoadException(err_str)
        prnt('BET_FONBET.PY: Min_amount=' + str(min_amount) + ' Max_amount=' + str(max_amount))

    def _get_request_id(self) -> int:
        """request_id is generated every time we placing bet"""
        url = self.common_url.format("coupon/requestId")

        headers = self.fonbet_headers

        payload_req = self.payload_req.copy()
        payload_req['fsid'] = self.payload['fsid']
        payload_req['clientId'] = self.base_payload["clientId"]
        payload_req['client']['id'] = self.base_payload["clientId"]

        resp = requests_retry_session().post(url, headers=headers, json=payload_req, verify=False, timeout=self.timeout)
        check_status_with_resp(resp)
        res = resp.json()
        if "requestId" not in res:
            prnt('BET_FONBET.PY: rror in def:_get_request_id' + str(res))
            raise LoadException("BET_FONBET.PY: key 'requestId' not found in response")
        else:
            prnt('BET_FONBET.PY: Success get requestId=' + str(res["requestId"]))
        self.payload['requestId'] = res["requestId"]
        return res["requestId"]

    def check_stat_olimp(self, obj):
        if obj.get('olimp_err', 'ok') != 'ok':
            err_str = 'BET_FONBET.PY: Фонбет получил ошибку от Олимпа: ' + str(obj.get('olimp_err'))
            prnt(err_str)
            raise OlimpBetError(err_str)

    def place_bet(self, obj={}) -> None:

        self.check_stat_olimp(obj)
        self._get_request_id()

        wager = obj.get('wager_fonbet')
        amount = obj.get('amount_fonbet')
        if self.wager is None and wager:
            self.wager = wager
        if self.amount is None and amount:
            self.amount = amount

        fonbet_bet_type = obj['fonbet_bet_type']
        if self.fonbet_bet_type is None and fonbet_bet_type:
            self.fonbet_bet_type = fonbet_bet_type

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
        try:
            resp = requests_retry_session().post(
                url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=15,
                proxies=self.proxies
            )
        except Exception as e:
            prnt('BET_FONBET.PY: rs timeout: ' + str(e))
            self.place_bet(obj=obj)

        prnt('BET_FONBET.PY: response fonbet: ' + str(resp.text), 'hide')

        check_status_with_resp(resp)
        res = resp.json()
        prnt(res, 'hide')

        req_time = round(resp.elapsed.total_seconds(), 2)
        n_sleep = max(0, (self.sleep - req_time))

        result = res.get('result')

        if result == "betDelay":
            # {"result":"betDelay","betDelay":3000}
            bet_delay_sec = (float(res.get('betDelay')) / 1000) + self.add_sleep
            prnt('BET_FONBET.PY: bet_delay: ' + str(bet_delay_sec) + ' sec...')
            time.sleep(bet_delay_sec)

        self._check_result(payload, obj)

    def manager_sold(self) -> None:
        '''Менеджер, включается в работку если не прошла ставка, нужно знать:
           принимает текущее значение тотола и счет команды 1 и 2 
        '''
        pass

    def _check_result(self, payload: dict, obj) -> None:
        """Check if bet is placed successfully"""

        self.check_stat_olimp(obj)

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
            timeout=self.timeout
        )
        req_time = round(resp.elapsed.total_seconds(), 2)
        check_status_with_resp(resp)
        res = resp.json()
        prnt(res, 'hide')
        err_res = res.get('result')

        if self.cnt_bet_attempt > (60 * 0.4) / self.sleep:
            err_str = 'BET_FONBET.PY: error place bet in Fonbet: ' + str(res)
            prnt(err_str)
            raise LoadException(err_str)

        if err_res == 'couponResult':
            err_code = res.get('coupon').get('resultCode')

            # 100 - Блокировка по матчу: 'Ставки на событие XXX временно не принимаются'
            # 2 - Коэффициента вообще нет или котировка поменялась: 'Изменена котировка на событие XXX' - делаем выкуп
            if err_code == 0:
                regId = res.get('coupon').get('regId')
                prnt('BET_FONBET.PY: Fonbet bet successful, regId: ' + str(regId))
                self.reg_id = regId
            elif err_code == 100:
                if 'Слишком частые ставки на событие' in res.get('coupon').get('errorMessageRus'):
                    err_str = "BET_FONBET.PY error:" + str(res)
                    prnt(err_str)
                    raise LoadException(err_str)

                self.cnt_bet_attempt = self.cnt_bet_attempt + 1
                n_sleep = max(0, (self.sleep - req_time))
                prnt('BET_FONBET.PY: ' + str(res.get('coupon').get('errorMessageRus')) + ', новая котировка:'
                     + str(res.get('coupon').get('bets')[0]['value']) + ', попытка #'
                     + str(self.cnt_bet_attempt) + ' через ' + str(n_sleep) + ' сек')
                time.sleep(n_sleep)
                return self.place_bet(obj=obj)

            # Изменился ИД: {'result': 'couponResult', 'coupon': {'resultCode': 2, 'errorMessage': 'Изменена котировка на событие "LIVE 0:0 Грузия U17 - Словакия U17 < 0.5"', 'errorMessageRus': 'Изменена котировка на событие "LIVE 0:0 Грузия U17 - Словакия U17 < 0.5"', 'errorMessageEng': 'Odds changed "LIVE 0:0 Georgia U17 - Slovakia U17 < 0.5"', 'amountMin': 30, 'amountMax': 81100, 'amount': 100, 'bets': [{'event': 13013805, 'factor': 1697, 'value': 1.37, 'param': 150, 'paramText': '1.5', 'paramTextRus': '1.5', 'paramTextEng': '1.5', 'score': '0:0'}]}}
            # Вообще ушла: {"result":"couponResult","coupon":{"resultCode":2,"errorMessage":"Изменена котировка на событие \"LIVE 1:0 Берое - Ботев Галабово Поб 1\"","errorMessageRus":"Изменена котировка на событие \"LIVE 1:0 Берое - Ботев Галабово Поб 1\"","errorMessageEng":"Odds changed \"LIVE 1:0 Beroe - Botev Galabovo 1\"","amountMin":30,"amountMax":3000,"amount":30,"bets":[{"event":13197928,"factor":921,"value":0,"score":"0:0"}]}}
            elif err_code == 2:
                err_str = str(res.get('coupon').get('errorMessageRus'))
                # Котировка вообще ушла
                if res.get('coupon').get('bets')[0]['value'] == 0:
                    err_str = "BET_FONBET.PY: error while placing the bet, current bet is hide: " + str(err_str)
                    prnt(err_str)
                    raise LoadException(err_str)
                # Изменился ИД тотола(как правило)
                else:
                    new_wager = res.get('coupon').get('bets')[0]
                    # {'result': 'couponResult', 'coupon':
                    # {'resultCode': 2,
                    # 'errorMessage': 'Изменена котировка на событие "LIVE 0:0 1-й тайм Альбион Роверс (р) - Ливингстон (р) < 0.5"',
                    # 'errorMessageRus': 'Изменена котировка на событие "LIVE 0:0 1-й тайм Альбион Роверс (р) - Ливингстон (р) < 0.5"',
                    # 'errorMessageEng': 'Odds changed "LIVE 0:0 1st half Albion Rovers (r) - Livingston (r) < 0.5"',
                    # 'amountMin': 30,
                    # 'amountMax': 32300,
                    # 'amount': 180,
                    # 'bets': [{'event': 13223785,
                    # 'factor': 931, 'value': 1.35, 'param': 150, 'paramText': '1.5',
                    # 'paramTextRus': '1.5', 'paramTextEng': '1.5', 'score': '0:1'}]}}

                    if str(new_wager.get('param', '')) == str(self.wager.get('param', '')) and \
                            int(self.wager.get('factor', 0)) != int(new_wager.get('factor', 0)):
                        prnt('Изменилась ИД ставки: old: ' + str(self.wager)
                             + ', new: ' + str(new_wager) + ' ' + str(err_str))
                        self.wager.update(new_wager)
                        return self.place_bet(obj=obj)
                    # В данном случае мы не проверяем кофы на изменение, если добавм надо подумать нужно ли это
                    # if float(new_wager.get('value', 0)) < float(self.wager.get('value', 0)):
                    #     n_sleep = max(0, (self.sleep - req_time))
                    #     self.cnt_bet_attempt = self.cnt_bet_attempt + 1
                    #     prnt('Коф-меньше запрошенного: ' + str(self.wager)
                    #          + ', new: ' + str(new_wager) + ' ' + str(err_str) +
                    #          ', попытка #' + str(self.cnt_bet_attempt) + ' через ' + str(n_sleep) + ' сек')
                    #     time.sleep(n_sleep)
                    #     return self.place_bet(obj=obj)
                    elif str(new_wager.get('param', '')) != str(self.wager.get('param', '')) and \
                            int(self.wager.get('factor', 0)) == int(new_wager.get('factor', 0)):
                        err_str = "BET_FONBET.PY: error Изменилась тотал ставки, 'param' не совпадает: " + \
                                  str(err_str) + ', new_wager: ' + str(new_wager) + ', old_wager: ' + str(self.wager)
                        prnt(err_str)
                        if self.fonbet_bet_type:
                            prnt('BET_FONBET.PY: поиск нового ИД тотала: ' + str(self.fonbet_bet_type))
                            match_id = self.wager.get('event')
                            new_wager = get_new_bets_fonbet(match_id, self.proxies, self.timeout)
                            new_wager = new_wager.get(str(match_id), {}).get('kofs', {}).get(self.fonbet_bet_type)
                            if new_wager:
                                prnt('BET_FONBET.PY: Тотал найден: ' + str(new_wager))
                                self.wager.update(new_wager)
                                return self.place_bet(obj=obj)
                            else:
                                err_str = 'BET_FONBET.PY: Тотал не найден'
                                prnt(err_str)
                                raise LoadException(err_str)
                        else:
                            err_str = 'BET_FONBET.PY: Тип ставки, например 1ТМ(2.5) - не задан, выдаю ошибку.'
                            prnt(err_str)
                            raise LoadException(err_str)
                    else:
                        err_str = "BET_FONBET.PY: error неизвестная ошибка: " + \
                                  str(err_str) + ', new_wager: ' + str(new_wager) + ', old_wager: ' + str(self.wager)
                        prnt(err_str)
                        raise LoadException(err_str)
        elif err_res == 'error' and "temporary unknown result" in resp.text:
            # there's situations where "temporary unknown result" means successful response
            # {'result': 'error', 'errorCode': 200, 'errorMessage': 'temporary unknown result'}
            err_str = 'BET_FONBET.PY: Get temporary unknown result: ' + str(res)
            prnt(err_str)
            time.sleep(3)
            return self._check_result(payload, obj)
        else:
            err = 'BET_FONBET.PY: error bet place result: ' + str(res)
            prnt(err)
            raise LoadException("BET_FONBET.PY: response came with an error: " + str(err))

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
            prnt('BET_FONBET.PY - sale_bet rq 1: ' + str(payload), 'hide')
            resp = requests_retry_session().post(
                url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=self.timeout
            )
            check_status_with_resp(resp)
            res = resp.json()

            if self.cnt_sale_attempt > 40:
                err_str = 'BET_FONBET.PY: error sale bet in Fonbet(coupon is lock): ' + str(res)
                prnt(err_str)
                raise LoadException(err_str)

            prnt('BET_FONBET.PY - sale_bet rs 1: ' + str(res), 'hide')
            # payload['version'] = res.get('version')

            timer_update = float(res.get('recommendedUpdateFrequency', 3))

            coupon_found = False
            for coupon in res.get('conditions'):
                if str(coupon.get('regId')) == str(self.reg_id):
                    coupon_found = True
                    self.cnt_sale_attempt = self.cnt_sale_attempt + 1
                    prnt('BET_FONBET.PY: canSell: ' + str(coupon.get('canSell', True)))
                    prnt('BET_FONBET.PY: tempBlock: ' + str(coupon.get('tempBlock', False)))
                    if coupon.get('canSell', True) is True and coupon.get('tempBlock', False) is False:
                        self.sell_sum = float(coupon.get('completeSellSum'))
                    else:
                        prnt('BET_FONBET.PY: coupon is lock, time sleep ' + str(timer_update) + ' sec...')
                        time.sleep(timer_update)
                        return self.sale_bet()
            if not coupon_found:
                err_str = 'BET_FONBET.PY: coupon regId ' + str(self.reg_id) + ' not found: ' + str(res)
                prnt(err_str)
                raise LoadException(err_str)

            if not self.sell_sum:
                prnt('BET_FONBET.PY: coupon is BAG (TODO), time sleep ' + str(timer_update) + ' sec...')
                prnt('BET_FONBET.PY: ' + str(res.get('conditions')))
                time.sleep(timer_update)
                self.cnt_sale_attempt = self.cnt_sale_attempt + 1
                return self.sale_bet()
                # raise LoadException("BET_FONBET.PY: reg_id is not found")

            # step2 get rqid for sell coupn
            url = self.common_url.format("coupon/sell/requestId")
            url = url.replace('session/', '')

            payload = self.payload_coupon_sum.copy()
            headers = self.fonbet_headers

            payload['clientId'] = self.base_payload["clientId"]
            payload['fsid'] = self.payload['fsid']
            prnt('BET_FONBET.PY - sale_bet rq 2: ' + str(payload), 'hide')
            resp = requests_retry_session().post(
                url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies
            )
            check_status_with_resp(resp)
            res = resp.json()
            prnt('BET_FONBET.PY - sale_bet rs 2: ' + str(res), 'hide')
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
            prnt('BET_FONBET.PY - sale_bet rq 3: ' + str(payload), 'hide')
            resp = requests_retry_session().post(
                url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies
            )
            check_status_with_resp(resp)
            res = resp.json()
            prnt('BET_FONBET.PY - sale_bet rs 3: ' + str(res), 'hide')
            result = res.get('result')

            if result == "sellDelay":
                sell_delay_sec = (float(res.get('sellDelay')) / 1000) + self.add_sleep
                prnt('BET_FONBET.PY: sell_delay: ' + str(sell_delay_sec) + ' sec...')
                time.sleep(sell_delay_sec)

            try:
                self._check_sell_result(requestId)
            except Exception as e:
                prnt('BET_FONBET.PY: error _check_sell_result: ' + str(res) + ' ' + str(e))
                self.cnt_sale_attempt = self.cnt_sale_attempt + 1
                return self.sale_bet()

    def _check_sell_result(self, requestId: int) -> None:
        """Check if bet is placed successfully"""

        url = self.common_url.format("coupon/sell/result")
        url = url.replace('session/', '')

        payload = self.payload_sell_check_result.copy()
        headers = self.fonbet_headers

        payload['requestId'] = requestId
        payload['clientId'] = self.base_payload["clientId"]
        payload['fsid'] = self.payload['fsid']
        prnt('BET_FONBET.PY - _check_sell_result rq: ' + str(payload), 'hide')
        resp = requests_retry_session().post(
            url,
            headers=headers,
            json=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies
        )
        check_status_with_resp(resp)
        res = resp.json()
        prnt('BET_FONBET.PY _check_sell_result rs: ' + str(res), 'hide')

        if self.cnt_sale_attempt > 40:
            err_str = 'BET_FONBET.PY: error sale bet in Fonbet(coupon is lock): ' + str(res)
            prnt(err_str)
            raise LoadException(err_str)

        # {'result': 'unableToSellCoupon', 'requestId': 19920670, 'regId': 14273664108, 'reason': 4, 'actualSellSum': 4900}

        if res.get('result') == "sellDelay":
            sell_delay_sec = (float(res.get('sellDelay')) / 1000) + self.add_sleep
            prnt('BET_FONBET.PY: sell_delay: ' + str(sell_delay_sec) + ' sec...')
            time.sleep(sell_delay_sec)
            return self._check_sell_result(res.get('requestId'))

        elif res.get('result') == 'unableToSellCoupon':
            if res.get('reason') in (3, 2):
                sleep_tempblock = 3 + self.add_sleep
                err_str = 'BET_FONBET.PY, err sale bet, coupon tempBlock = True: ' + str(res) + ' ' + \
                          'sell_delay: ' + str(sleep_tempblock) + ' sec...'
                time.sleep(sleep_tempblock)
                print(err_str)
                return self.sale_bet()
            else:
                err_str = 'BET_FONBET.PY, err sale bet, new actualSellSum: ' + str(res.get('actualSellSum') / 10)
                print(err_str)
                return self.sale_bet()

        elif res.get('result') == 'couponCompletelySold':
            sold_sum = res.get('soldSum')
            prnt('BET_FONBET.PY: Fonbet sell successful, sold_sum: ' + str(sold_sum / 100))
            return True
        else:
            # if res.get("errorCode") != "0":
            err_str = 'BET_FONBET.PY: error sell result: ' + str(res)
            prnt(err_str)
            raise LoadException(err_str)

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
            timeout=self.timeout,
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
            timeout=self.timeout,
            proxies=self.proxies
        )
        check_status_with_resp(resp)
        res = resp.json()

        # if res.get("result") == "error":
        # prnt('BET_FONBET.PY: error get coupon info: ' + str(res))
        # raise LoadException("BET_FONBET.PY: " + str(res.get('errorMessage')))

        return res


def get_new_bets_fonbet(match_id, proxies, time_out):
    from util_fonbet import url_fonbet_match, fonbet_header, VICTS, TTO, TTU, TT1O, TT1U, TT2O, TT2U
    key_id = str(match_id)
    bets_fonbet = {}
    try:
        resp = requests_retry_session().get(
            url_fonbet_match + str(match_id) + "&lang=en",
            headers=fonbet_header,
            timeout=time_out,
            verify=False,
            proxies=proxies,
        )
        resp = resp.json()

        TT = []
        for bet in [TTO, TTU, TT1O, TT1U, TT2O, TT2U]:
            TT.extend(bet)

        for event in resp.get("events"):
            # prnt(jsondumps(event, ensure_ascii=False))
            # exit()

            score = event.get('score', '0:0').replace('-', ':')
            timer = event.get('timer')
            minute = event.get('timerSeconds', 0) / 60
            skId = event.get('skId')
            skName = event.get('skName')
            sport_name = event.get('sportName')
            name = event.get('name')
            priority = event.get('priority')
            score_1st = event.get('scoreComment', '').replace('-', ':')

            if event.get('parentId') == 0 or event.get('name') in ('1st half', '2nd half'):
                if event.get('parentId') == 0:
                    try:
                        bets_fonbet[key_id].update({
                            'sport_id': skId,
                            'sport_name': skName,
                            'league': sport_name,
                            'name': name,
                            'priority': priority,
                            'score': score,
                            'score_1st': score_1st,
                            'time': timer,
                            'minute': minute,
                            'time_req': round(time.time())
                        })
                    except Exception as e:
                        # print(e)
                        bets_fonbet[key_id] = {
                            'sport_id': skId,
                            'sport_name': skName,
                            'league': sport_name,
                            'name': name,
                            'priority': priority,
                            'score': score,
                            'score_1st': score_1st,
                            'time': timer,
                            'minute': minute,
                            'time_req': round(time.time()),
                            'time_change_total': round(time.time()),
                            'avg_change_total': [],
                            'kofs': {}
                        }

                # prnt('event_name', event.get('name'))

                half = ''
                if event.get('name') == '1st half':
                    half = '1'
                elif event.get('name') == '2nd half':
                    half = '2'

                for cat in event.get('subcategories'):

                    cat_name = cat.get('name')
                    # prnt('cat_name', cat_name)
                    if cat_name in (
                            '1X2 (90 min)',
                            '1X2',
                            'Goal - no goal',
                            'Total', 'Totals', 'Team Totals-1', 'Team Totals-2'):  # , '1st half', '2nd half'

                        for kof in cat.get('quotes'):

                            factorId = str(kof.get('factorId'))
                            pValue = kof.get('pValue', '')
                            p = kof.get('p', '')
                            kof_is_block = kof.get('blocked', False)
                            if kof_is_block:
                                value = 0
                            else:
                                value = kof.get('value')
                            # {'event': '12788610', 'factor': '921', 'param': '', 'score': '1:0', 'value': '1.25'}
                            for vct in VICTS:
                                coef = half + str(vct[0])  # + num_team
                                if str(vct[1]) == factorId:
                                    bets_fonbet[key_id]['kofs'].update(
                                        {
                                            coef:
                                                {
                                                    'time_req': round(time.time()),
                                                    'event': event.get('id'),
                                                    'value': value,
                                                    'param': '',
                                                    'factor': factorId,
                                                    'score': score
                                                }
                                        }
                                    )

                            for stake in TT:
                                coef = half + str(stake[0].format(p))  # + num_team
                                if str(stake[1]) == factorId:
                                    bets_fonbet[key_id]['kofs'].update(
                                        {
                                            coef:
                                                {
                                                    'time_req': round(time.time()),
                                                    'event': event.get('id'),
                                                    'value': value,
                                                    'param': pValue,
                                                    'factor': factorId,
                                                    'score': score
                                                }}
                                    )
        return bets_fonbet
    except Exception as e:
        prnt(e)
        raise ValueError(e)


if __name__ == '__main__':
    FONBET_USER = {"login": 5447708, "password": "tStseFuY"}
    wager_fonbet = {'event': '13538626', 'factor': '1809', 'param': '250', 'score': '0:0', 'value': '1.42'}

    obj = {}
    obj['wager_fonbet'] = wager_fonbet
    obj['amount_fonbet'] = 45
    obj['fonbet_bet_type'] = None  # 'ТМ(2.5)'

    fonbet = FonbetBot(FONBET_USER)
    fonbet.sign_in()
    #fonbet.place_bet(obj)
    #time.sleep(3)
    fonbet.sale_bet(14859958889)
    # fonbet_reg_id = fonbet.place_bet(amount_fonbet, wager_fonbet)
    # {'e': 12264423, 'f': 931, 'v': 1.4, 'p': 250, 'pt': '2.5', 'isLive': True}
