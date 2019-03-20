import urllib3

from math import floor
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
import copy
import re

from retry_requests import requests_retry_session, requests_retry_session_post

from meta_ol import ol_url_api, ol_payload, ol_headers, get_xtoken_bet
from meta_fb import fb_payload, fb_payload_bet, get_random_str, get_dumped_payload, get_urls, get_common_url
from meta_fb import fb_headers, get_new_bets_fonbet, payload_req, payload_coupon_sum, payload_coupon_sell
from meta_fb import payload_sell_check_result
from utils import prnt, package_dir, write_file, read_file, get_account_info, get_param
from fork_recheck import get_olimp_info, get_fonbet_info

from exceptions import BetIsLost, SessionNotDefined, BkOppBetError, NoMoney, BetError, SessionExpired, SaleError
from exceptions import CouponBlocked, BetIsLost

if get_param('debug'):
    DEBUG = True
else:
    DEBUG = False

# disable: InsecureRequestWarning: Unverified HTTPS request is being made.
# See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warningsInsecureRequestWarning)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

package_dir = path.dirname(path.abspath(__file__))


def run_bets(shared: dict):
    ps = []
    for bk_name, bk_container in shared.items():
        bk = Thread(target=BetManager, args=(shared, bk_name, bk_container))
        ps.append(bk)
        bk.start()

    for bk in ps:
        bk.join()


class BetManager:

    def __init__(self, shared: dict, bk_name: str, bk_container: dict):

        self.bk_name = bk_name
        self.bk_container = bk_container
        self.wager = bk_container['wager']
        self.bk_name_opposite = bk_container['opposite']

        self.msg_err = self.bk_name + '. {}, err: {}'
        self.msg = self.bk_name + '. {}, msg: {}'

        self.total_bet = bk_container.get('bet_total')
        self.side_team = bk_container['side_team']
        self.bet_type = bk_container['bet_type']
        self.set_param()  # set self.side_bet, self.side_bet_half
        self.dop_stat = dict()
        # dynamic params
        self.cur_sc = None
        self.cur_sc_main = None
        self.cur_total = None
        self.cur_total_new = None
        self.cur_half = None
        self.cur_val_bet = None
        self.cur_minute = None
        self.total_stock = None

        self.account = self.get_account_info()
        self.timeout = 20
        self.match_id = None
        self.reg_id = None
        self.reqId = None
        self.reqIdSale = None
        self.payload = None
        self.sum_bet = None
        self.sum_sell = None
        self.attempt_login = 1
        self.attempt_bet = 1
        self.attempt_sale = 1
        self.sleep_bet = 3.51
        self.sleep_add = 0
        self.proxies = self.get_proxy()
        self.server_olimp = 10
        self.server_fb = {}
        self.mirror = self.get_account_info().get('mirror')

        self.session_file = 'session.' + self.bk_name
        self.session = {}

        self.time_start = round(time())

        err_msg = ''

        bk_work = ('olimp', 'fonbet')
        if self.bk_name not in bk_work or self.bk_name_opposite not in bk_work:
            err_msg = 'bk not defined: bk1={}, bk2={}'.format(self.bk_name, self.bk_name_opposite)

        elif self.mirror is None:
            err_msg = 'mirror not defined: {}'.format(self.mirror)

        if err_msg != '':
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
            prnt(err_str)
            raise ValueError(err_str)

        # self.manager(shared)
        shared[self.bk_name]['self'] = self
        self.bet_simple(shared)

    def wait_sign_in_opp(self, shared: dict):
        sign_stat = shared.get('sign_in_' + self.bk_name_opposite, 'wait')

        push_ok = False
        while sign_stat == 'wait':
            if not push_ok:
                prnt(self.msg.format(
                    sys._getframe().f_code.co_name,
                    self.bk_name + ' wait stat sign in from ' +
                    self.bk_name_opposite + ': ' + str(sign_stat) + '(' + str(type(sign_stat)) + ')'))
                push_ok = True
            sign_stat = shared.get('sign_in_' + self.bk_name_opposite, 'wait')

        if sign_stat not in ('ok', 'wait'):
            err_str = self.msg_err.format(
                sys._getframe().f_code.co_name,
                self.bk_name + ' get error from ' +
                self.bk_name_opposite + ': ' + sign_stat)
            raise BkOppBetError(err_str)

        prnt(self.msg.format(
            sys._getframe().f_code.co_name,
            self.bk_name + ' get sign in from ' +
            self.bk_name_opposite + ': ' + str(sign_stat) + '(' + str(type(sign_stat)) + ')'))

    def opposite_stat_get(self, shared: dict):

        opposite_stat = str(shared.get(self.bk_name_opposite + '_err', 'ok'))

        if opposite_stat != 'ok':
            err_str = self.msg_err.format(
                sys._getframe().f_code.co_name,
                self.bk_name + ' get error from ' +
                self.bk_name_opposite + ': ' + opposite_stat)
            raise BkOppBetError(err_str)

        prnt(self.msg.format(
            sys._getframe().f_code.co_name,
            self.bk_name + ' get status bet in from ' +
            self.bk_name_opposite + ': ' + str(opposite_stat) + '(' + str(type(opposite_stat)) + ')'))

    def opposite_stat_wait(self, shared: dict):
        # if not DEBUG:
        prnt(self.msg.format(
            sys._getframe().f_code.co_name,
            self.bk_name + ' wait status bet in from ' +
            self.bk_name_opposite))

        opp_stat = None
        while opp_stat is None:
            opp_stat = shared.get(self.bk_name_opposite + '_err')

        prnt(self.msg.format(
            sys._getframe().f_code.co_name,
            self.bk_name + ' get status bet in from ' +
            self.bk_name_opposite + ': ' + str(opp_stat) + '(' + str(type(opp_stat)) + ')'))

    def bet_simple(self, shared: dict):

        def sale_opp(e, shared):
            self.opposite_stat_wait(shared)
            self.opposite_stat_get(shared)
            prnt(self.msg.format(sys._getframe().f_code.co_name,
                                 'Ошибка при проставлении ставки в ' + self.bk_name +
                                 ', делаю выкуп ставки в ' + self.bk_name_opposite))

            self_opp = shared[self.bk_name_opposite].get('self', {})

            while True:
                try:
                    self_opp.sale_bet(shared)
                    break
                except (SaleError, CouponBlocked) as e:
                    prnt(self.msg.format(
                        sys._getframe().f_code.co_name,
                        'Ошибка: ' + e.__class__.__name__ + ' - ' + str(e) +
                        '. Пробую проставить и пробую выкупить еще!'))
                    sleep(3)

        def bet_done(shared):
            if not shared[self.bk_name].get('time_bet'):
                shared[self.bk_name]['time_bet'] = round(time() - self.time_start)
            shared[self.bk_name]['balance'] = self.session.get('balance')

        try:
            try:
                self.sign_in(shared)
                self.wait_sign_in_opp(shared)
                self.bet_place(shared)
                bet_done(shared)
            except BetError as e:
                shared[self.bk_name + '_err'] = str(e.__class__.__name__) + ': ' + str(e)
                prnt(e)

                self.opposite_stat_wait(shared)
                self.opposite_stat_get(shared)

                prnt(self.msg.format(
                    sys._getframe().f_code.co_name,
                    'Ошибка при проставлении ставки в ' + self.bk_name + ', передаю его завершающему'))
                self.bet_safe(shared)

            except BkOppBetError as e:
                raise BkOppBetError(e)
            except (BetIsLost, NoMoney, SessionExpired, Exception) as e:
                if not shared.get(self.bk_name_opposite, {}).get('reg_id'):
                    shared[self.bk_name + '_err'] = str(e.__class__.__name__) + ': ' + str(e)

                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    err_msg = 'Ошибка: ' + str(e.__class__.__name__) + ' - ' + str(e) + '. ' + \
                              str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                    err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
                    prnt(err_str)

                    sale_opp(e, shared)

                    raise ValueError(err_str)
        except BkOppBetError as e:
            # В обоих БК ошибки, выкидываем вилку
            shared[self.bk_name + '_err'] = str(e.__class__.__name__) + ': ' + str(e)
            shared[self.bk_name_opposite + '_err'] = str(e.__class__.__name__) + ': ' + str(e)
        finally:
            bet_done(shared)

    def set_param(self):
        self.side_bet = None
        self.side_bet_half = None

        bet_type_sub = re.sub('\(.*\)', '', self.bet_type)

        msk_match_per = '^\d\w.*\d$'
        msk_team = '^\w.*\d$'
        msk_period = '^\d\w.*'

        bet_depends = 'Уставки есть привязкa:'
        if re.match(msk_match_per, bet_type_sub):
            self.side_bet = bet_type_sub[-1]
            self.side_bet_helf = bet_type_sub[0:1]
            bet_depends = bet_depends + ' команада=' + self.side_bet + ' и период=' + self.side_bet_half
        elif re.match(msk_team, bet_type_sub):
            self.side_bet = bet_type_sub[-1]
            bet_depends = bet_depends + ' команада=' + self.side_bet
        elif re.match(msk_period, bet_type_sub):
            self.side_bet_half = bet_type_sub[0:1]
            bet_depends = bet_depends + ' период=' + self.side_bet_half
        else:
            bet_depends = 'Ставка не привязана ни к периоду, ни к команде'
        prnt(self.msg.format(sys._getframe().f_code.co_name, bet_depends))

    def bet_safe(self, shared: dict):

        self.vector = self.bk_container.get('wager', {})['vector']
        self.time_start = round(int(time()))
        self.time_left = -1

        if self.vector == 'UP':
            self.timeout_left = float(60 * 10)
        elif self.vector == 'DOWN':
            self.timeout_left = round(float(60 * 2.5))
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'Завершающий принял работу, время на работу(сек):' + str(self.timeout_left)))

        is_go = True
        while is_go:
            try:
                prnt('')
                # UPDATE TIME LEFT
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'UPDATE TIME LEFT'))
                cur_time = round(int(time()))
                self.time_left = (self.time_start + self.timeout_left) - cur_time
                if self.time_left < 0:
                    err_str = 'timeout: time_start:{}, time_left:{}, cur_time:{}'.format(self.time_start, self.time_left, cur_time)
                    raise BetIsLost(err_str)

                # UPDATE DATA
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'UPDATE DATA'))
                match_id = self.bk_container.get('wager', {})['event']
                param = self.bk_container.get('wager', {}).get('param')
                bet_id = int(self.bk_container.get('wager', {}).get('factor'))

                if self.bk_name == 'fonbet' or self.bk_name_opposite == 'fonbet':
                    try:
                        if self.bk_name_opposite == 'fonbet':
                            self_opp = shared[self.bk_name_opposite].get('self', {})
                            match_id_opp = self_opp.bk_container.get('wager', {})['event']
                            bet_id_opp = int(self_opp.bk_container.get('wager', {}).get('factor'))
                            param_opp = self_opp.bk_container.get('wager', {}).get('param')
                            bet_type_opp = self_opp.bk_container.get('bet_type')
                            k_val, self.cur_sc_main, time_req_opp, self.dop_stat = get_fonbet_info(match_id_opp, bet_id_opp, param_opp, bet_type_opp)
                        elif self.bk_name == 'fonbet':
                            self.cur_val_bet, self.cur_sc, time_req, self.dop_stat = get_fonbet_info(match_id, bet_id, param, self.bet_type)

                        prnt(self.msg.format(sys._getframe().f_code.co_name, 'get data from fonbet: ' + dumps(self.dop_stat, ensure_ascii=False)))

                    except Exception as e:
                        err_msg = 'recheck err (' + str(e.__class__.__name__) + '): ' + str(e)
                        prnt(self.msg_err.format(sys._getframe().f_code.co_name, err_msg))

                if self.bk_name == 'olimp':
                    try:
                        self.cur_val_bet, self.cur_sc, time_req = get_olimp_info(match_id, self.bet_type)
                    except Exception as e:
                        err_msg = 'recheck err (' + str(e.__class__.__name__) + '): ' + str(e)
                        prnt(self.msg_err.format(sys._getframe().f_code.co_name, err_msg))

                # new flag params
                if self.side_bet == '1':
                    self.cur_total = int(self.cur_sc_main.split(':')[0])
                elif self.side_bet == '2':
                    self.cur_total = int(self.cur_sc_main.split(':')[1])
                else:
                    self.cur_total = sum(map(int, self.cur_sc_main.split(':')))

                if not self.cur_total_new:
                    self.cur_total_new = self.cur_total

                self.cur_half = self.dop_stat['period']
                self.cur_minute = self.dop_stat['minutes']
                self.total_stock = self.total_bet - self.cur_total

                prnt(self.msg.format(
                    sys._getframe().f_code.co_name,
                    'Получил данные: bet_type:{}, vector:{}, total:{}, chalf:{}, val_bet:{}, minute:{}, sc_main:{}, sc:{}, total_stock:{}'.
                        format(self.bet_type, self.vector, self.cur_total, self.cur_half, self.cur_val_bet,
                               self.cur_minute, self.cur_sc_main, self.cur_sc, self.total_stock)))

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Запас тотала: total_stock:{}'.format(self.total_stock)))

                # CHECK FOR LOSS
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'CHECK FOR LOSS'))
                if self.side_bet_half == '1' and self.cur_minute > 45.0:
                    err_str = 'Bet is lost: side_bet_half={} and cur_minute many 45({})'.format(self.side_bet_half, self.cur_minute)
                    prnt(err_str)
                    raise BetIsLost(err_str)
                elif self.cur_minute > 90.0:
                    err_str = 'Bet is lost: side_bet_half={} and cur_minute many 90({})'.format(self.side_bet_half, self.cur_minute)
                    prnt(err_str)
                    raise BetIsLost(err_str)

                    # check: score changed?
                if self.cur_total != self.cur_total_new:
                    self.cur_total_new = self.cur_total
                    prnt(self.msg.format(sys._getframe().f_code.co_name, 'score changed!'))
                    if self.vector == 'UP':
                        # if self.total_bet <= self.cur_total_new:
                        if self.total_stock <= 0:
                            err_str = ' total_bet < cur_total ({} < {}), bet lost, im sorry =('.format(self.total_bet, self.cur_total)
                            prnt(err_str)
                            raise BetIsLost(err_str)
                        elif self.cur_total < self.bet_total:
                            # exmpl: SC1 + SC2 < Х
                            # recalc sum
                            self.bet_place(shared)
                            is_go = False
                    elif self.vector == 'DOWN':
                        if self.cur_total < self.bet_total:
                            # exmpl: SC1 + SC2 < Х
                            # recalc sum
                            self.bet_place(shared)
                            is_go = False
                        elif self.bet_total <= self.cur_total:
                            # exmpl: SC1 + SC2 >= Х
                            prnt(self.msg.format(sys._getframe().f_code.co_name, 'Greetings! You won, brain!'))
                            is_go = False
                else:
                    if self.vector == 'UP':
                        # recalc sum
                        self.bet_place(shared)
                        is_go = False

                    elif self.vector == 'DOWN':
                        # recalc sum
                        self.bet_place(shared)
                        is_go = False

            except BetIsLost as e:
                shared[self.bk_name + '_err'] = str(e.__class__.__name__) + ': ' + str(e)
                self_opp = shared[self.bk_name_opposite].get('self', {})

                prnt(self.msg.format(sys._getframe().f_code.co_name,
                                     'Ошибка при проставлении ставки в ' + self.bk_name +
                                     ', делаю выкуп ставки в ' + self.bk_name_opposite))
                while True:
                    try:
                        self_opp.sale_bet(shared)
                        is_go = False
                        break
                    except CouponBlocked as e:
                        prnt(self.msg.format(
                            sys._getframe().f_code.co_name,
                            'Ошибка: ' + e.__class__.__name__ + ' - ' + str(e) +
                            '. Пробую проставить и пробую выкупить еще!'))
                        sleep(3)

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                prnt(self.msg.format(
                    sys._getframe().f_code.co_name,
                    'Ошибка: (' + e.__class__.__name__ + ') ' + str(e) + ' ' +
                    str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))) +
                    '. Работаю еще: ' + str(self.time_left) + ' сек'))
            finally:
                sleep(3)

    def sign_in(self, shared: dict):

        try:
            if self.bk_name == 'olimp':
                # # for test
                # sleep(10)
                # try:
                #     1/0
                # except Exception as e:
                #     #raise SessionNotDefined(e)
                #     raise ValueError(e)

                payload = copy.deepcopy(ol_payload)
                payload.update({'login': self.account['login'], 'password': self.account['password']})

                headers = copy.deepcopy(ol_headers)
                headers.update(get_xtoken_bet(payload))
                headers.update({'X-XERPC': '1'})

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests_retry_session_post(
                    ol_url_api.format(str(self.server_olimp), 'autorize'),
                    headers=headers,
                    data=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')

                data = resp.json()['data']

                self.session['session'] = data.get('session')
                self.session['balance'] = float(dict(data).get('s'))
                self.session['currency'] = dict(data).get('cur')

            elif self.bk_name == 'fonbet':

                # # for test
                # sleep(5)
                # try:
                #     1/0
                # except Exception as e:
                #     #raise SessionNotDefined(e)
                #     raise ValueError(e)

                fb_payload['platform'] = 'mobile_android'
                fb_payload['clientId'] = self.account['login']

                payload = copy.deepcopy(fb_payload)
                payload['random'] = get_random_str()
                payload['sign'] = 'secret password'

                msg = get_dumped_payload(payload)
                sign = hmac.new(key=self.account['password'].encode(), msg=msg.encode(), digestmod=sha512).hexdigest()
                payload['sign'] = sign
                data = get_dumped_payload(payload)

                self.server_fb = get_urls(self.mirror, self.proxies)
                url, self.timeout = get_common_url(self.server_fb)

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(data)), 'hide')

                resp = requests_retry_session_post(
                    url.format('login'),
                    headers=fb_headers,
                    data=data,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
                res = resp.json()

                self.session['session'] = res.get('fsid')
                self.session['balance'] = float(res.get('saldo'))
                self.session['currency'] = res.get('currency').get('currency')

            if not self.session.get('session'):
                err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'session_id not defined')
                raise SessionNotDefined(err_str)

            prnt(self.msg.format(sys._getframe().f_code.co_name, 'session: ' + str(self.session['session'])))
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'balance: ' +
                                 str(self.session.get('balance')) + ' ' +
                                 str(self.session.get('currency'))))
            write_file(self.session_file, self.session['session'].strip())

            if not self.session.get('session'):
                err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'session_id not defined')
                raise SessionNotDefined(err_str)

            shared['sign_in_' + self.bk_name] = 'ok'

        except SessionNotDefined as e:
            shared['sign_in_' + self.bk_name] = str(e.__class__.__name__) + ': ' + str(e)
            raise SessionNotDefined(e)
        except Exception as e:
            shared['sign_in_' + self.bk_name] = str(e.__class__.__name__) + ': ' + str(e)

            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_msg = 'unknown err(' + str(e.__class__.__name__) + '): ' + str(e) + '. ' + \
                      str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

            err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
            raise ValueError(err_str)

    def bet_place(self, shared: dict):
        self.set_session_state()

        # # for test
        # if self.bk_name == 'fonbet':
        #     sleep(15)
        self.opposite_stat_get(shared)

        self.sum_bet = self.bk_container.get('amount')

        cur_bal = self.session.get('balance')

        if cur_bal:
            if cur_bal < self.sum_bet:
                err_str = self.msg_err.format(
                    sys._getframe().f_code.co_name,
                    self.bk_name + ' balance ({}) < sum_bet({})'.format(str(cur_bal), str(self.sum_bet)))
                raise NoMoney(err_str)

        if self.bk_name == 'olimp':

            # for test
            sleep(5)
            try:
                1/0
            except Exception as e:
                raise BetError(e)

            payload = copy.deepcopy(ol_payload)

            payload.update({
                'coefs_ids': '[["{apid}",{factor},1]]'.format(apid=self.wager.get('apid'), factor=self.wager.get('factor')),
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

            headers = copy.deepcopy(ol_headers)
            headers.update(get_xtoken_bet(payload))

            prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
            self.opposite_stat_get(shared)
            resp = requests_retry_session_post(
                ol_url_api.format(str(self.server_olimp), 'basket/fast'),
                headers=headers,
                data=payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies)
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
            res = resp.json()

            err_code = res.get('error', {}).get('err_code')
            err_msg = res.get('error', {}).get('err_desc')
            self.check_responce(err_msg)

            if err_code == 0:
                self.match_id = self.wager['event']

                self.get_cur_max_bet_id()

                shared[self.bk_name]['reg_id'] = self.reg_id
                shared[self.bk_name + '_err'] = 'ok'

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'bet successful, reg_id: ' + str(self.reg_id)))

            elif 'Такой исход не существует' in err_msg:
                raise BetIsLost(err_msg)

            elif 'максимальная ставка' in err_msg:
                raise BetIsLost(err_msg)

            elif res.get('data') is None:
                err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
                raise BetError(err_str)

        elif self.bk_name == 'fonbet':

            # # for test
            # sleep(2)
            # try:
            #     1/0
            # except Exception as e:
            #     raise BetError(e)

            if not self.server_fb:
                self.server_fb = get_urls(self.mirror, self.proxies)

            url, self.timeout = get_common_url(self.server_fb)

            payload = copy.deepcopy(fb_payload_bet)
            headers = copy.deepcopy(fb_headers)

            payload['client'] = {'id': self.account['login']}
            payload['coupon']['amount'] = self.sum_bet

            if self.wager.get('param'):
                payload['coupon']['bets'][0]['param'] = int(self.wager['param'])
            payload['coupon']['bets'][0]['score'] = self.wager['score']
            payload['coupon']['bets'][0]['value'] = float(self.wager['value'])
            payload['coupon']['bets'][0]['event'] = int(self.wager['event'])
            payload['coupon']['bets'][0]['factor'] = int(self.wager['factor'])
            payload['fsid'] = self.session['session']
            payload['clientId'] = self.account['login']

            self.payload = copy.deepcopy(payload)

            self.check_max_bet(shared)

            try:
                self.get_request_id()
            except BetError:
                self.get_request_id()

            self.payload['requestId'] = self.reqId

            prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')

            self.opposite_stat_get(shared)

            resp = requests_retry_session_post(
                url.format('coupon/register'),
                headers=headers,
                json=self.payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies)
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
            res = resp.json()

            result = res.get('result')
            msg_str = res.get('errorMessage')
            self.check_responce(msg_str)

            if result == 'betDelay':
                bet_delay_sec = (float(res.get('betDelay')) / 1000)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'bet_delay: ' + str(bet_delay_sec) + ' sec.'))
                sleep(bet_delay_sec)

            self.check_result(shared)

    def sale_bet(self, shared: dict):
        # добвить возможность перед выкупом еще раз попробовать проставить второе плечо, если оно было упущено по времени а не потерено

        self.set_session_state()
        # кажется это не нужно
        # self.opposite_stat_get(shared)

        if self.bk_name == 'olimp':

            coupon = self.get_cur_max_bet_id()

            cashout_allowed = coupon.get('cashout_allowed', False)
            self.sum_sell = coupon.get('cashout_amount', 0)
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'coupon cashout_allowed: ' + str(cashout_allowed)))
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'coupon amount: ' + str(self.sum_sell)))

            if cashout_allowed and self.sum_sell > 0:
                payload = {}
                payload['bet_id'] = self.reg_id
                if self.bk_name == 'olimp':
                    self.sum_bet = 0
                payload['amount'] = self.sum_sell
                payload['session'] = self.session['session']
                payload.update(copy.deepcopy(ol_payload))
                payload.pop('time_shift')

                headers = copy.deepcopy(ol_headers)
                headers.update(get_xtoken_bet(payload))
                headers.update({'X-XERPC': '1'})

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests_retry_session_post(
                    ol_url_api.format(str(self.server_olimp), 'user/cashout'),
                    headers=headers,
                    data=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
                res = resp.json()

                err_code = res.get('error', {}).get('err_code')
                err_msg = res.get('error', {}).get('err_desc')
                self.check_responce(err_msg)

                if res.get('data') and res.get('data').get('status', 'err') == 'ok':
                    prnt(self.msg.format(sys._getframe().f_code.co_name, 'code: ' + str(err_code) + ', ' + res.get('data', {}).get('msg')))
                else:
                    raise SaleError(err_msg)

            else:
                err_msg = 'coupon ' + str(self.reg_id) + ' blocked'
                raise CouponBlocked(err_msg)

        elif self.bk_name == 'fonbet':
            if self.reg_id:
                # step1 get from version and sell sum
                if not self.server_fb:
                    self.server_fb = get_urls(self.mirror, self.proxies)

                url, self.timeout = get_common_url(self.server_fb)

                url = url.replace('session/', '')

                payload = copy.deepcopy(payload_coupon_sum)
                headers = copy.deepcopy(fb_headers)

                payload['clientId'] = self.account['login']
                payload['fsid'] = self.session['session']

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests_retry_session_post(url.format('coupon/sell/conditions/getFromVersion'),
                                                   headers=headers,
                                                   json=payload,
                                                   verify=False,
                                                   timeout=self.timeout)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text)), 'hide')
                res = resp.json()
                result = res.get('result')
                msg_str = res.get('errorMessage')
                self.check_responce(msg_str)

                timer_update = float(res.get('recommendedUpdateFrequency', 3))

                coupon_found = False
                for coupon in res.get('conditions'):
                    if str(coupon.get('regId')) == str(self.reg_id):
                        coupon_found = True

                        prnt(self.msg.format(sys._getframe().f_code.co_name, 'canSell: ' + str(coupon.get('canSell', True))), 'hide')
                        prnt(self.msg.format(sys._getframe().f_code.co_name, 'tempBlock: ' + str(coupon.get('tempBlock', False))), 'hide')

                        if coupon.get('canSell', True) and not coupon.get('tempBlock', False):
                            self.sell_sum = float(coupon.get('completeSellSum'))
                        else:
                            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'coupon is lock, time sleep ' + str(timer_update) + ' sec.')
                            sleep(timer_update)
                            raise CouponBlocked(err_str)
                if not coupon_found:
                    err_str = self.msg_err.format(
                        sys._getframe().f_code.co_name,
                        'coupon regId ' + str(self.reg_id) +
                        ' not found, retry, after sec: ' + str(timer_update))
                    self.sale_bet(shared)

                # step2 get rqid for sell coupn
                payload = copy.deepcopy(payload_coupon_sum)
                headers = copy.deepcopy(fb_headers)

                payload['clientId'] = self.account['login']
                payload['fsid'] = self.session['session']

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests_retry_session_post(
                    url.format('coupon/sell/requestId'),
                    headers=headers,
                    json=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text)), 'hide')
                res = resp.json()
                result = res.get('result')
                msg_str = res.get('errorMessage')
                self.check_responce(msg_str)

                if res.get('result') == 'requestId':
                    self.reqIdSale = res.get('requestId')

                # step3 sell
                payload = copy.deepcopy(payload_coupon_sell)
                headers = copy.deepcopy(fb_headers)

                payload['regId'] = int(self.reg_id)
                payload['requestId'] = int(self.reqIdSale)
                payload['sellSum'] = self.sell_sum
                payload['clientId'] = self.account['login']
                payload['fsid'] = self.session['session']

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests_retry_session_post(
                    url.format('coupon/sell/completeSell'),
                    headers=headers,
                    json=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text)), 'hide')
                res = resp.json()
                result = res.get('result')
                msg_str = res.get('errorMessage')
                self.check_responce(msg_str)

                if result == 'sellDelay':
                    sell_delay_sec = (float(res.get('sellDelay')) / 1000)
                    prnt(self.msg.format(sys._getframe().f_code.co_name,
                                         'sell, delay: ' + str(sell_delay_sec) + ' sec.'))
                    sleep(sell_delay_sec)

                return self.check_sell_result()

    def check_responce(self, err_msg):

        if err_msg:
            if 'не вошли в систему'.lower() in err_msg.lower() or \
                    'Not token access'.lower() in err_msg.lower() or \
                    'invalid session id'.lower() in err_msg.lower():
                err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'session expired: ' + self.session['session'])
                raise SessionExpired(err_msg + ' ' + err_str)
            elif 'Продажа ставки недоступна'.lower() in err_msg.lower() or 'Изменилась сумма продажи ставки'.lower() in err_msg.lower():
                raise CouponBlocked(self.msg.format(sys._getframe().f_code.co_name, err_msg))

    def get_proxy(self) -> str:

        with open(path.join(package_dir, 'proxies.json')) as file:
            proxies = load(file)
        return proxies.get(self.bk_name)

    def get_account_info(self) -> str:

        with open(path.join(package_dir, 'account.json')) as file:
            account = load(file)
        return account.get(self.bk_name, {})

    def check_max_bet(self, shared: dict):
        self.opposite_stat_get(shared)

        url, timeout = get_common_url(self.server_fb)
        payload = copy.deepcopy(fb_payload_bet)
        headers = copy.deepcopy(fb_headers)

        if self.wager.get('param'):
            payload['coupon']['bets'][0]['param'] = int(self.wager['param'])

        payload['coupon']['bets'][0]['score'] = self.wager['score']
        payload['coupon']['bets'][0]['value'] = float(self.wager['value'])
        payload['coupon']['bets'][0]['event'] = int(self.wager['event'])
        payload['coupon']['bets'][0]['factor'] = int(self.wager['factor'])
        payload['coupon']['amount'] = 0.0

        payload['fsid'] = self.session['session']
        payload['clientId'] = self.account['login']

        payload['coupon'].pop('flexBet')
        payload['coupon'].pop('flexParam')
        payload['coupon']['bets'][0].pop('lineType')

        data = get_dumped_payload(payload)

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
        resp = requests_retry_session_post(
            'https://23.111.80.252/session/coupon/getMinMax',
            headers=headers,
            data=data,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
        res = resp.json()

        result = res.get('result')
        msg_str = res.get('errorMessage')
        self.check_responce(msg_str)

        if 'min' not in res:
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'min sum not found')
            raise BetIsLost(err_str)

        min_amount, max_amount = res['min'] // 100, res['max'] // 100

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'sum bet=' + str(self.sum_bet)))
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'min_amount=' + str(min_amount) + ', max_amount=' + str(max_amount)))
        if (self.sum_bet < min_amount) or (max_amount < self.sum_bet):
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'max or min bet')
            raise BetIsLost(err_str)
        if self.session.get('balance') and self.session['balance'] < self.sum_bet:
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'mo money')
            raise NoMoney(err_str)

    def check_result(self, shared: dict):

        payload = copy.deepcopy(self.payload)

        url, timeout = get_common_url(self.server_fb)

        try:
            del payload['coupon']
        except:
            pass

        headers = copy.deepcopy(fb_headers)

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(payload)), 'hide')
        resp = requests_retry_session_post(
            url.format('coupon/result'),
            headers=headers,
            json=payload,
            verify=False,
            timeout=self.timeout)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
        res = resp.json()

        result = res.get('result')
        msg_str = res.get('errorMessage')
        self.check_responce(msg_str)

        err_code = res.get('coupon', {}).get('resultCode')
        err_msg = res.get('coupon', {}).get('errorMessageRus')

        if result == 'couponResult':
            if err_code == 0:
                self.reg_id = res.get('coupon').get('regId')

                shared[self.bk_name]['reg_id'] = self.reg_id
                shared[self.bk_name + '_err'] = 'ok'

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'bet successful, reg_id: ' + str(self.reg_id)))
                # prnt(self.msg.format(sys._getframe().f_code.co_name, 'time sleep 3 sec.'))
                # sleep(3)
            if err_code == 1:
                self.opposite_stat_get(shared)
                err_str = self.msg.format(sys._getframe().f_code.co_name, err_msg)
                raise BetIsLost(err_str)
            elif err_code == 100:
                self.opposite_stat_get(shared)
                if 'Слишком частые ставки на событие' in err_msg:
                    err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
                    raise BetIsLost(err_str)
                else:
                    err_str = err_msg + ', новая котировка:' + str(res.get('coupon', {}).get('bets')[0].get('value', 0))
                    sleep(self.sleep_bet)
                    err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
                    raise BetError(err_str)
            elif err_code == 2:
                self.opposite_stat_get(shared)
                # Котировка вообще ушла
                if res.get('coupon', {}).get('bets')[0]['value'] == 0:
                    err_str = 'current bet is lost: ' + str(err_msg)
                    raise BetIsLost(err_str)
                # Изменился ИД тотола
                else:
                    new_wager = res.get('coupon').get('bets')[0]

                    if str(new_wager.get('param', '')) == str(self.wager.get('param', '')) and \
                            int(self.wager.get('factor', 0)) != int(new_wager.get('factor', 0)):

                        prnt(self.msg.format(
                            sys._getframe().f_code.co_name,
                            'Изменилась ИД ставки: old: ' + str(self.wager) +
                            ', new: ' + str(new_wager)))
                        self.wager.update(new_wager)
                        return self.bet_place(shared)

                    elif str(new_wager.get('param', '')) != str(self.wager.get('param', '')) and \
                            int(self.wager.get('factor', 0)) == int(new_wager.get('factor', 0)):

                        prnt(self.msg_err.format(sys._getframe().f_code.co_name,
                                                 'Изменилась тотал ставки, param не совпадает: ' +
                                                 'new_wager: ' + str(new_wager) + ', old_wager: ' + str(self.wager)))

                        if self.bk_container.get('bet_type'):

                            prnt(self.msg.format(sys._getframe().f_code.co_name, 'поиск нового id тотала: ' + self.bk_container.get('bet_type')))

                            match_id = self.wager.get('event')
                            new_wager = get_new_bets_fonbet(match_id, self.proxies, self.timeout)
                            new_wager = new_wager.get(str(match_id), {}).get('kofs', {}).get(self.bk_container.get('bet_type'))
                            if new_wager:
                                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Тотал найден: ' + str(new_wager)))
                                self.wager.update(new_wager)
                                return self.bet_place(shared)
                            else:
                                err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'Тотал не найден: ' + str(new_wager))
                                raise BetIsLost(err_str)
                        else:
                            err_str = self.msg_err.format(
                                sys._getframe().f_code.co_name,
                                'Тип ставки, например 1ТМ(2.5) - не задан, выдаю ошибку: bet_type:' +
                                self.bk_container.get('bet_type') + ', bk_container:' + str(self.bk_container))
                            raise BetIsLost(err_str)
                    else:
                        err_str = self.msg_err.format(
                            sys._getframe().f_code.co_name,
                            'неизвестная ошибка: ' + str(err_msg) +
                            ', new_wager: ' + str(new_wager) +
                            ', old_wager: ' + str(self.wager))
                        prnt(err_str)
                        raise BetIsLost(err_str)
        elif result == 'error' and 'temporary unknown result' in msg_str:
            err_str = 'Get temporary unknown result: ' + str(msg_str)
            prnt(self.msg.format(sys._getframe().f_code.co_name, err_str))
            return self.check_result(shared)
        else:
            self.opposite_stat_get(shared)
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
            raise BetError(err_str)

    def set_session_state(self):

        if not self.session.get('session'):
            self.session['session'] = read_file(self.session_file)

    def get_request_id(self) -> int:

        if not self.server_fb:
            self.server_fb = get_urls(self.mirror, self.proxies)

        url, self.timeout = get_common_url(self.server_fb)

        headers = copy.deepcopy(fb_headers)

        payload = copy.deepcopy(payload_req)
        payload['fsid'] = self.payload['fsid']
        payload['clientId'] = self.account['login']
        payload['client']['id'] = self.account['login']

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
        resp = requests_retry_session_post(
            url.format('coupon/requestId'),
            headers=headers,
            json=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text)), 'hide')
        res = resp.json()

        result = res.get('result')
        msg_str = res.get('errorMessage')
        self.check_responce(msg_str)

        if 'requestId' not in res:
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'key requestId not found in response')
            raise BetError(err_str)
        else:
            self.reqId = res['requestId']
            prnt(self.msg.format(sys._getframe().f_code.co_name,
                                 'get requestId=' + str(self.reqId)))
            return self.reqId

    def check_sell_result(self):
        if not self.server_fb:
            self.server_fb = get_urls(self.mirror, self.proxies)

        url, self.timeout = get_common_url(self.server_fb)
        url = url.replace('session/', '')

        payload = copy.deepcopy(payload_sell_check_result)
        headers = copy.deepcopy(fb_headers)

        payload['requestId'] = self.reqIdSale
        payload['clientId'] = self.account['login']
        payload['fsid'] = self.session['session']

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
        resp = requests_retry_session_post(
            url.format('coupon/sell/result'),
            headers=headers,
            json=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text)), 'hide')
        res = resp.json()
        result = res.get('result')
        msg_str = res.get('errorMessage')
        self.check_responce(msg_str)

        if result == 'error' and 'temporary unknown result' in msg_str:
            err_str = 'Get temporary unknown result: ' + str(msg_str)
            prnt(self.msg.format(sys._getframe().f_code.co_name, err_str))
            sleep(3)
            return self.check_sell_result()

        elif result == 'sellDelay':
            sell_delay_sec = (float(res.get('sellDelay')) / 1000)
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'sell, delay: ' + str(sell_delay_sec) + ' sec.'))
            sleep(sell_delay_sec)
            return self.check_sell_result()

        elif result == 'unableToSellCoupon':
            if res.get('reason') in (2, 3):
                err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'unable to sell coupon, reason=' + str(res.get('reason')))
                raise BetIsLost(err_str)
            else:
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'new actualSellSum: ' + str(res.get('actualSellSum') / 10)))
                return self.sale_bet(shared)

        elif result == 'couponCompletelySold':
            sold_sum = res.get('soldSum')
            prnt(self.msg.format(sys._getframe().f_code.co_name,
                                 'sell successful, sum sold: ' + str(sold_sum / 100)))
        else:
            raise BetIsLost

    def get_cur_max_bet_id(self, filter='0100', offset='0'):

        req_url = ol_url_api.format(str(self.server_olimp), 'user/history')

        payload = copy.deepcopy(ol_payload)
        payload['filter'] = filter  # только не расчитанные
        payload['offset'] = offset
        payload['session'] = self.session['session']

        headers = copy.deepcopy(ol_headers)
        headers.update(get_xtoken_bet(payload))
        headers.update({'X-XERPC': '1'})

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
        resp = requests_retry_session_post(
            req_url,
            headers=headers,
            data=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
        res = resp.json()

        err_code = res.get('error', {}).get('err_code')
        err_msg = res.get('error', {}).get('err_desc')
        self.check_responce(err_msg)

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
                raise BetError(err_str)

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
    shared = {}

    FONBET_USER = {"login": get_account_info('fonbet', 'login'), "password": get_account_info('fonbet', 'password')}

    OLIMP_USER = {"login": get_account_info('olimp', 'login'), "password": get_account_info('olimp', 'password')}

    wager_olimp = {
        'apid': '1174307310:46807570:1:3:-9999:2:0:0:1',
        'factor': '1.06',
        'sport_id': 1,
        'event': '46807570'}

    FONBET_USER = {'login': 5447708, 'password': 'tStseFuY'}
    wager_fonbet = {
        'event': '13446124',
        'factor': '922',
        'param': '',
        'score': '1:0',
        'value': '5'}

    shared = {}
    shared['wager'] = wager_olimp  # wager_olimp
    shared['amount'] = 30
    bk1 = Thread(target=BetManager, args=(shared, 'olimp', 'fonbet'))
    bk1.start()

    # shared = {}
    # shared['wager'] = wager_fonbet  # wager_olimp
    # shared['amount'] = 45
    # bk2 = Thread(target=BetManager, args=(shared, 'fonbet', 'olimp'))
    # bk2.start()

    bk1.join()
    bk2.join()
