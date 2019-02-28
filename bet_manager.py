from exceptions import BetIsLost, SessionNotDefined, BkOppBetError, NoMoney, BetError, SessionExpired, SaleError, \
    CouponBlocked, BetIsLost
from math import floor
from utils import prnt, package_dir, write_file, read_file, DEBUG
from time import time, sleep
from os import path
from json import load, dumps
import requests
import inspect
import sys
import traceback
from threading import Thread
import hmac
from hashlib import sha512
from meta_ol import ol_url_api, ol_payload, ol_headers, get_xtoken_bet
from meta_fb import fb_payload, fb_payload_bet, get_random_str, get_dumped_payload, get_urls, get_common_url, \
    fb_headers, get_new_bets_fonbet

prnt('DEBUG: ' + str(DEBUG))

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
        self.my_name = inspect.stack()[0][3]
        self.timeout = 50
        self.match_id = None
        self.reg_id = None
        self.reqId = None
        self.payload = None
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
        self.my_name = inspect.stack()[0][3]
        self.server_olimp = 12
        self.server_fb = {}
        self.msg_err = self.bk + '. {}, err: {}'
        self.msg = self.bk + '. {}, msg: {}'
        self.mirror = self.get_account_info().get('mirror')
        self.my_name = inspect.stack()[0][3]
        self.session_file = 'session.' + self.bk
        self.session = {}

        err_msg = ''

        bk_work = ('olimp', 'fonbet')
        if (self.bk not in bk_work or self.bk_opposite not in bk_work) and 1 == 0:
            err_msg = 'bk not defined: bk1={}, bk2={}'.format(self.bk, self.bk_opposite)

        elif self.mirror is None:
            err_msg = 'mirror not defined: {}'.format(self.mirror)

        if err_msg != '':
            err_str = self.msg_err.format(self.my_name, err_msg)
            prnt(err_str)
            raise ValueError(err_str)

        bk_obj[self.bk] = self

        self.manager(bk_obj, obj)
        self.my_name = inspect.stack()[0][3]

    def manager(self, bk_obj: dict, obj: dict) -> None:
        self.my_name = inspect.stack()[0][3]
        # obj['fonbet_err'] = 'bla bla bla'
        # obj['olimp_err'] = 'bla bla bla'

        # bk_obj[self.bk].sign_in(obj)

        try:
            bk_obj[self.bk].place_bet(obj)
            # self.reg_id = 1300
            bk_obj[self.bk].sale_bet()
        except CouponBlocked as e:
            prnt(e)
        except BetIsLost as e:
            prnt(e)
        except NoMoney as e:
            prnt(e)
        except BkOppBetError as e:
            prnt(e)
        except SessionExpired as e:
            prnt(e)
            self.sign_in(obj)
        except BetError as e:
            prnt(e)
            pass
            # bk_obj[self.bk].place_bet(obj)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_msg = 'unknown err: ' + str(e) + '. ' + \
                      str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            err_str = self.msg_err.format(self.my_name, err_msg)
            prnt(err_str)
            raise ValueError(err_str)

        # bk1.sale_bet()

    def check_responce(self, err_msg):
        self.my_name = inspect.stack()[0][3]

        if err_msg:
            if 'не вошли в систему' in err_msg or \
                    'Not token access' in err_msg or \
                    'invalid session id' in err_msg:
                err_str = self.msg_err.format(
                    self.my_name, 'session expired: ' + self.session['session']
                )
                raise SessionExpired(err_str)

    def get_proxy(self) -> str:
        self.my_name = inspect.stack()[0][3]
        with open(path.join(package_dir, 'proxies.json')) as file:
            proxies = load(file)
        return proxies.get(self.bk)

    def get_account_info(self) -> str:
        self.my_name = inspect.stack()[0][3]
        with open(path.join(package_dir, 'account.json')) as file:
            account = load(file)
        return account.get(self.bk, {})

    def wait_sign_in_opp(self):
        self.my_name = inspect.stack()[0][3]
        if not DEBUG:
            self.my_name = inspect.stack()[0][3]
            msg_push = True

            obj['sign_in_' + self.bk] = 'ok'

            while obj.get('sign_in_' + self.bk_opposite) != 'ok':
                if msg_push:
                    err_str = self.msg_err.format(
                        self.my_name,
                        self.bk + ' wait sign in from ' + self.bk_opposite
                    )
                    prnt(err_str)
                    msg_push = False

    def sign_in(self, obj: dict) -> None:
        self.my_name = inspect.stack()[0][3]
        try:
            if self.bk == 'olimp':
                payload = ol_payload.copy()
                payload.update({
                    'login': self.account['login'],
                    'password': self.account['password']
                })

                headers = ol_headers.copy()
                headers.update(get_xtoken_bet(payload))
                headers.update({'X-XERPC': '1'})

                prnt(self.msg.format(self.my_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests.post(
                    ol_url_api.format(str(self.server_olimp), 'autorize'),
                    headers=headers,
                    data=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies
                )
                prnt(self.msg.format(self.my_name, 'rs: ' + str(resp.text.strip())), 'hide')

                data = resp.json()['data']

                self.session['session'] = data.get('session')
                self.session['balance'] = float(dict(data).get('s'))
                self.session['currency'] = dict(data).get('cur')

            elif self.bk == 'fonbet':

                fb_payload['platform'] = 'mobile_android'
                fb_payload['clientId'] = self.account['login']

                payload = fb_payload
                payload['random'] = get_random_str()
                payload['sign'] = 'secret password'

                msg = get_dumped_payload(payload)
                sign = hmac.new(key=self.account['password'].encode(), msg=msg.encode(), digestmod=sha512).hexdigest()
                payload['sign'] = sign
                data = get_dumped_payload(payload)

                self.server_fb = get_urls(self.mirror, self.proxies)
                url, self.timeout = get_common_url(self.server_fb)

                prnt(self.msg.format(self.my_name, 'rq: ' + str(data)), 'hide')
                resp = requests.post(
                    url.format('login'),
                    headers=fb_headers,
                    data=data,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies
                )
                prnt(self.msg.format(self.my_name, 'rs: ' + str(resp.text.strip())), 'hide')
                res = resp.json()

                self.session['session'] = res.get('fsid')
                self.session['balance'] = float(res.get('saldo'))
                self.session['currency'] = res.get('currency').get('currency')

            if not self.session.get('session'):
                err_msg = 'session_id not defined'
                err_str = self.msg_err.format(self.my_name, err_msg)
                raise SessionNotDefined(err_str)

            prnt(self.msg.format(self.my_name, 'session: ' + str(self.session['session'])))
            prnt(
                self.msg.format(
                    self.my_name, 'balance: ' + \
                                  str(self.session.get('balance')) + ' ' +
                                  str(self.session.get('currency'))
                )
            )
            write_file(self.session_file, self.session['session'].strip())
            self.wait_sign_in_opp()
            self.my_name = inspect.stack()[0][3]

            if not self.session.get('session'):
                err_msg = 'session_id not defined'
                err_str = self.msg_err.format(self.my_name, err_msg)
                raise SessionNotDefined(err_str)

        except SessionNotDefined as e:
            prnt(err_str)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_msg = 'unknown err: ' + str(e) + '. ' + \
                      str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            err_str = self.msg_err.format(self.my_name, err_msg)
            prnt(err_str)
            raise ValueError(err_str)

    def get_opposite_stat(self, obj):
        self.my_name = inspect.stack()[0][3]

        opposite_stat = str(obj.get(self.bk_opposite + '_err', 'ok'))
        if opposite_stat != 'ok':
            err_str = self.msg_err.format(self.my_name,
                                          self.bk + ' get error from ' + self.bk_opposite + ': ' + opposite_stat
                                          )
            raise BkOppBetError(err_str)

    def check_max_bet(self, obj):
        self.get_opposite_stat(obj)
        self.my_name = inspect.stack()[0][3]

        url, timeout = get_common_url(self.server_fb)

        payload = fb_payload_bet.copy()
        headers = fb_headers.copy()

        if self.wager.get('param'):
            payload['coupon']['bets'][0]['param'] = int(self.wager['param'])
        payload['coupon']['bets'][0]['score'] = self.wager['score']
        payload['coupon']['bets'][0]['value'] = float(self.wager['value'])
        payload['coupon']['bets'][0]['event'] = int(self.wager['event'])
        payload['coupon']['bets'][0]['factor'] = int(self.wager['factor'])

        payload['fsid'] = self.session['session']
        payload['clientId'] = self.account['login']

        prnt(self.msg.format(self.my_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
        resp = requests.post(
            url.format('coupon/getMinMax'),
            headers=headers,
            json=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies
        )
        prnt(self.msg.format(self.my_name, 'rs: ' + str(resp.text.strip())), 'hide')
        res = resp.json()

        result = res.get('result')
        msg_str = res.get('errorMessage')
        self.check_responce(msg_str)
        self.my_name = inspect.stack()[0][3]

        if 'min' not in res:
            err_str = self.msg_err.format(
                self.my_name,
                'min sum not found'
            )
            raise BetIsLost(err_str)

        min_amount, max_amount = res['min'] // 100, res['max'] // 100
        if not (min_amount <= self.sum_bet <= self.session['balance']) or \
                not (min_amount <= self.sum_bet <= max_amount):
            err_str = self.msg_err.format(
                self.my_name,
                'no money: min_amount:{}, sum_bet:{}, max_amount:{}'.format(min_amount, self.sum_bet, max_amount)
            )
            raise NoMoney(err_str)
        prnt(self.msg(self.my_name, 'min_amount=' + str(min_amount) + ', max_amount=' + str(max_amount)))

    def check_result(self, obj) -> None:
        self.get_opposite_stat(obj)
        self.my_name = inspect.stack()[0][3]

        payload = self.payload

        url, timeout = get_common_url(self.server_fb)
        self.my_name = inspect.stack()[0][3]

        try:
            del payload["coupon"]
        except:
            pass

        headers = fb_headers.copy()

        prnt(self.msg.format(self.my_name, 'rs: ' + str(payload)), 'hide')
        resp = requests.post(
            url.format("coupon/result"),
            headers=headers,
            json=payload,
            verify=False,
            timeout=self.timeout
        )
        prnt(self.msg.format(self.my_name, 'rs: ' + str(resp.text.strip())), 'hide')
        res = resp.json()

        result = res.get('result')
        msg_str = res.get('errorMessage')
        self.check_responce(msg_str)
        self.my_name = inspect.stack()[0][3]

        err_code = res.get('coupon', {}).get('resultCode')
        err_msg = res.get('coupon', {}).get('errorMessageRus')

        if result == 'couponResult':
            if err_code == 0:
                self.reg_id = res.get('coupon').get('regId')
                prnt(self.msg.format(self.my_name, 'bet successful, reg_id: ' + str(self.reg_id)))
            elif err_code == 100:
                if 'Слишком частые ставки на событие' in err_msg:
                    err_str = self.msg_err.format(self.my_name, err_msg)
                    raise BetIsLost(err_str)
                else:
                    err_str = err_msg + ', новая котировка:' + str(res.get('coupon', {}).get('bets')[0].get('value', 0))
                    sleep(self.sleep_bet)
                    err_str = self.msg_err.format(self.my_name, err_msg)
                    raise BetError(err_str)
            elif err_code == 2:
                # Котировка вообще ушла
                if res.get('coupon', {}).get('bets')[0]['value'] == 0:
                    err_str = "current bet is lost: " + str(err_msg)
                    raise BetIsLost(err_str)
                # Изменился ИД тотола
                else:
                    new_wager = res.get('coupon').get('bets')[0]

                    if str(new_wager.get('param', '')) == str(self.wager.get('param', '')) and \
                            int(self.wager.get('factor', 0)) != int(new_wager.get('factor', 0)):

                        prnt(
                            self.msg.format(
                                self.my_name,
                                'Изменилась ИД ставки: old: ' + str(self.wager) + ', new: ' + str(new_wager)
                            )
                        )
                        self.wager.update(new_wager)
                        return self.place_bet(obj=obj)

                    elif str(new_wager.get('param', '')) != str(self.wager.get('param', '')) and \
                            int(self.wager.get('factor', 0)) == int(new_wager.get('factor', 0)):

                        prnt(
                            self.msg_err.format(
                                self.my_name,
                                'Изменилась тотал ставки, param не совпадает: ' + \
                                'new_wager: ' + str(new_wager) + ', old_wager: ' + str(self.wager)
                            )
                        )

                        if obj.get('fonbet_bet_type'):

                            self.msg.format(
                                self.my_name,
                                'поиск нового id тотала: ' + obj.get('fonbet_bet_type')
                            )
                            match_id = self.wager.get('event')
                            new_wager = get_new_bets_fonbet(match_id, self.proxies, self.timeout)
                            new_wager = new_wager.get(str(match_id), {}).get('kofs', {}).get(obj.get('fonbet_bet_type'))
                            if new_wager:
                                self.msg.format(self.my_name, 'Тотал найден: ' + str(new_wager))
                                self.wager.update(new_wager)
                                return self.place_bet(obj=obj)
                            else:
                                err_str = self.msg_err.format(self.my_name, 'Тотал не найден' + str(new_wager))
                                raise BetIsLost(err_str)
                        else:
                            err_str = self.msg_err.format(self.my_name,
                                                          'Тип ставки, например 1ТМ(2.5) - не задан, выдаю ошибку.')
                            raise BetIsLost(err_str)
                    else:
                        err_str = self.msg_err.format(
                            self.my_name, "неизвестная ошибка: " + \
                                          str(err_msg) + ', new_wager: ' + str(new_wager) + ', old_wager: ' + str(
                                self.wager)
                        )
                        prnt(err_str)
                        raise BetIsLost(err_str)
        elif result == 'error' and "temporary unknown result" in resp.text:
            err_str = 'Get temporary unknown result: ' + str(res)
            prnt(err_str)
            sleep(3)
            return self.check_result(obj)
        else:
            err_str = self.msg_err.format(self.my_name, err_msg)
            raise BetError(err_str)

    def set_session_state(self):
        self.my_name = inspect.stack()[0][3]
        if not self.session.get('session'):
            self.session['session'] = read_file(self.session_file)

    def place_bet(self, obj: dict) -> None:
        self.set_session_state()
        self.my_name = inspect.stack()[0][3]

        self.get_opposite_stat(obj)

        self.wager = obj.get('wager')
        self.sum_bet = obj.get('amount')

        cur_bal = self.session.get('balance')
        if cur_bal and cur_bal < self.sum_bet:
            err_str = self.msg_err.format(
                self.my_name,
                self.bk + ' balance ({}) < sum_bet({})'.format(str(cur_bal), str(self.sum_bet))
            )
            raise NoMoney(err_str)

        if self.bk == 'olimp':

            payload = ol_payload.copy()

            payload.update({
                'coefs_ids': '[["{apid}",{factor},1]]'.format(
                    apid=self.wager.get('apid'), factor=self.wager.get('factor')),
                'sport_id': self.wager.get('sport_id'),
                'sum': self.sum_bet,
                'save_any': 3,
                'fast': 1,
                'any_handicap': 1,
                'session': self.session['session']
            })
            # Принимать с изменёнными коэффициентами:
            # save_any: 1 - никогда, 2 - при повышении, 3 - всегда

            # Принимать с измененными тоталами/форами:
            # any_handicap: 1 - Нет, 2 - Да

            headers = ol_headers.copy()
            headers.update(get_xtoken_bet(payload))

            prnt(self.msg.format(self.my_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
            resp = requests.post(
                ol_url_api.format(str(self.server_olimp), 'basket/fast'),
                headers=headers,
                data=payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies
            )
            prnt(self.msg.format(self.my_name, 'rs: ' + str(resp.text.strip())), 'hide')
            res = resp.json()

            err_code = res.get('error', {}).get('err_code')
            err_msg = res.get('error', {}).get('err_desc')
            self.check_responce(err_msg)
            self.my_name = inspect.stack()[0][3]

            if err_code == 0:
                self.match_id = self.wager['event']

                self.get_cur_max_bet_id()
                self.my_name = inspect.stack()[0][3]

                prnt(self.msg.format(self.my_name, 'bet successful, reg_id: ' + str(self.reg_id)))

            elif 'Такой исход не существует' in err_msg:
                raise BetIsLost(err_msg)

            elif 'максимальная ставка' in err_msg:
                raise BetIsLost(err_msg)

            elif res.get('data') is None:
                err_str = self.msg_err.format(self.my_name, err_msg)
                raise BetError(err_str)

        elif self.bk == 'fonbet':
            if not self.server_fb:
                self.server_fb = get_urls(self.mirror, self.proxies)

            url, self.timeout = get_common_url(self.server_fb)

            payload = fb_payload_bet.copy()
            headers = fb_headers.copy()

            payload['client'] = {'id': self.account['login']}

            payload['requestId'] = self.reqId

            if self.wager.get('param'):
                payload['coupon']['bets'][0]['param'] = int(self.wager['param'])

            payload['coupon']['bets'][0]['score'] = self.wager['score']
            payload['coupon']['bets'][0]['value'] = float(self.wager['value'])
            payload['coupon']['bets'][0]['event'] = int(self.wager['event'])
            payload['coupon']['bets'][0]['factor'] = int(self.wager['factor'])
            payload['fsid'] = self.session['session']
            payload['clientId'] = self.account['login']
            payload['coupon']['amount'] = self.sum_bet

            self.payload = payload

            self.check_max_bet(obj)
            self.my_name = inspect.stack()[0][3]

            prnt(self.msg.format(self.my_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
            resp = requests.post(
                url.format('coupon/register'),
                headers=headers,
                json=payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies
            )
            prnt(self.msg.format(self.my_name, 'rs: ' + str(resp.text.strip())), 'hide')
            res = resp.json()

            result = res.get('result')
            msg_str = res.get('errorMessage')
            self.check_responce(msg_str)
            self.my_name = inspect.stack()[0][3]

            if result == 'betDelay':
                bet_delay_sec = (float(res.get('betDelay')) / 1000)
                prnt(self.msg(self.my_name, 'bet_delay: ' + str(bet_delay_sec) + ' sec.'))
                sleep(bet_delay_sec)

            self.check_result(obj)
            self.my_name = inspect.stack()[0][3]

    def sale_bet(self) -> None:
        self.set_session_state()
        self.my_name = inspect.stack()[0][3]

        if self.bk == 'olimp':

            coupon = self.get_cur_max_bet_id()
            self.my_name = inspect.stack()[0][3]

            cashout_allowed = coupon.get('cashout_allowed', False)
            self.sum_sell = coupon.get('cashout_amount', 0)
            prnt(self.msg.format(self.my_name, 'coupon cashout_allowed: ' + str(cashout_allowed)))
            prnt(self.msg.format(self.my_name, 'coupon amount: ' + str(self.sum_sell)))

            if cashout_allowed is True and self.sum_sell > 0:
                payload = {}
                payload['bet_id'] = self.reg_id
                payload['amount'] = self.sum_sell
                payload['session'] = self.session['session']
                payload.update(ol_payload.copy())
                payload.pop('time_shift')

                headers = ol_headers.copy()
                headers.update(get_xtoken_bet(payload))
                headers.update({'X-XERPC': '1'})

                prnt(self.msg.format(self.my_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests.post(
                    ol_url_api.format(str(self.server_olimp), 'user/cashout'),
                    headers=headers,
                    data=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies
                )
                prnt(self.msg.format(self.my_name, 'rs: ' + str(resp.text.strip())), 'hide')
                res = resp.json()

                err_code = res.get('error', {}).get('err_code')
                err_msg = res.get('error', {}).get('err_desc')
                self.check_responce(err_msg)
                self.my_name = inspect.stack()[0][3]

                if res.get('data') and res.get('data').get('status', 'err') == 'ok':
                    prnt(
                        self.msg.format(self.my_name, 'code: ' +
                                        str(err_code) + ', ' +
                                        res.get('data', {}).get('msg'))
                    )
                else:
                    raise SaleError(err_msg)

            else:
                err_msg = 'coupon ' + str(self.reg_id) + ' blocked'
                raise CouponBlocked(err_msg)

        elif self.bk == 'fonbet':
            pass

    def finishing(self, obj: dict, vector: str, sc1: int, sc2: int, cur_total: float) -> None:
        self.my_name = inspect.stack()[0][3]

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

    def get_cur_max_bet_id(self, filter='0100', offset='0'):
        self.my_name = inspect.stack()[0][3]

        req_url = ol_url_api.format(str(self.server_olimp), 'user/history')

        payload = ol_payload.copy()
        payload['filter'] = filter  # только не расчитанные
        payload['offset'] = offset
        payload['session'] = self.session['session']

        headers = ol_headers.copy()
        headers.update(get_xtoken_bet(payload))
        headers.update({'X-XERPC': '1'})

        prnt(self.msg.format(self.my_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
        resp = requests.post(
            req_url,
            headers=headers,
            data=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies
        )
        prnt(self.msg.format(self.my_name, 'rs: ' + str(resp.text.strip())), 'hide')
        res = resp.json()

        err_code = res.get('error', {}).get('err_code')
        err_msg = res.get('error', {}).get('err_desc')
        self.check_responce(err_msg)
        self.my_name = inspect.stack()[0][3]

        max_bet_id = 0
        coupon_data = {}

        # reg_id - мы знаем заранее - только при ручном выкупе как правило
        if self.reg_id:
            coupon_found = False
            for bet_list in res.get('data').get('bet_list', {}):
                cur_bet_id = bet_list.get('bet_id')
                if cur_bet_id == self.reg_id:
                    coupon_found = True
                    max_bet_id = cur_bet_id
                    coupon_data = bet_list
            if not coupon_found:
                err_str = 'coupon reg_id: ' + str(self.reg_id) + ', not found'
                raise BetIsLost(err_str)

        # Мы не знаем reg_id и берем последний по матчу
        elif self.match_id:
            for bet_list in res.get('data').get('bet_list', []):
                if str(bet_list.get('events')[0].get('matchid')) == str(self.match_id):
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


if __name__ == '__main__':
    bk_obj = {}

    # OLIMP_USER = {'login': 'eva.yushkova.81@mail.ru', 'passw': 'qvF3BwrNcRcJtB6'}
    # wager_olimp = {'apid': '1181740951:47030887:1:3:-9999:2:0:0:1', 'factor': '1.06', 'sport_id': 1,
    #                'event': '47030887'}

    FONBET_USER = {"login": 5699838, "password": "NTe2904H11"}
    wager_fonbet = {'event': '13395343', 'factor': '1809', 'param': '250', 'score': '0:0', 'value': '1.42'}

    obj = {}
    obj['wager'] = wager_fonbet  # wager_olimp
    obj['amount'] = 30

    # bk1 = Thread(target=BetManager, args=(bk_obj, obj, 'olimp', 'fonbet'))
    bk2 = Thread(target=BetManager, args=(bk_obj, obj, 'fonbet', 'olimp'))
    # bk1.start()
    bk2.start()
    # bk1.join()
    bk2.join()
