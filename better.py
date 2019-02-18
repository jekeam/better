# coding:utf-8
from bet_fonbet import *
from bet_olimp import *
import datetime
from fork_recheck import get_kof_olimp, get_kof_fonbet
from utils import prnt, get_account_info, DEBUG
# from client import run_client
import threading
from multiprocessing import Manager, Process, Pipe
from math import floor, ceil
import time
from random import randint
import platform
from sys import exit
from exceptions import Shutdown
import http.client
import json

shutdown = False


def get_sum_bets(k1, k2, total_bet, print_hide=True):
    k1 = float(k1)
    k2 = float(k2)
    l = (1 / k1) + (1 / k2)

    # Округление проставления в БК1 происходит по правилам математики
    bet_1 = round(total_bet / (k1 * l) / 5) * 5
    bet_2 = total_bet - bet_1
    prnt('L: ' + str(round((1 - l) * 100, 2)) + '% (' + str(l) + ') ', print_hide)
    prnt(
        'bet1: ' + str(bet_1) + ' руб, bet2: ' + str(bet_2) + ' руб.|' +
        ' bet_sum: ' + str(bet_1 + bet_2) + ' руб.', print_hide
    )

    return bet_1, bet_2


def bet_fonbet_cl(obj, amount_fonbet, wager_fonbet):
    global FONBET_USER
    try:
        fonbet = FonbetBot(FONBET_USER)
        fonbet.sign_in()
        fonbet_reg_id = fonbet.place_bet(amount_fonbet, wager_fonbet, obj)
        obj['fonbet_err'] = 'ok'
    except Exception as e:
        obj['fonbet'] = fonbet
        obj['fonbet_err'] = str(e)
    finally:
        obj['fonbet'] = fonbet


def bet_olimp_cl(obj, amount_olimp, wager_olimp):
    global OLIMP_USER
    try:
        olimp = OlimpBot(OLIMP_USER)
        olimp.sign_in()
        olimp.place_bet(amount_olimp, wager_olimp, obj)
        obj['olimp_err'] = 'ok'
    except Exception as e:
        obj['olimp_err'] = str(e)
    finally:
        obj['olimp'] = olimp


def check_l(L):
    l_exclude_text = ''
    if L <= 0.90:
        l_exclude_text = l_exclude_text + 'Вилка ' + str(L) + ' (' + str(round((1 - L) * 100, 2)) + \
                         '%), вилка исключена т.к. доходноть высокая >= 10%\n'
    if L > 0.995:
        l_exclude_text = l_exclude_text + 'Вилка ' + str(L) + ' (' + str(round((1 - L) * 100, 3)) + \
                         '%), беру вилки только >= 0.5%\n'

    if l_exclude_text != '':
        return l_exclude_text
    else:
        return ''


def check_fork(key, L, k1, k2, bk1_score, bk2_score, minute, time_break_fonbet, is_2nd_half, info=''):
    fork_exclude_text = ''
    v = True
    global bal1, bal2, balance_line

    if success.count(key) >= 1:
        fork_exclude_text = fork_exclude_text + 'Вилка не проставлена, т.к. уже проставляли на эту вилку: ' + key + '\n'

    # Проверяем корректная ли сумма
    if bet1 < 30 or bet2 < 30:
        fork_exclude_text = fork_exclude_text + 'Сумма одной из ставок меньше 30р.\n'

    # Проверяем хватить денег для ставки
    if (bal1 < bet1) or (bal2 < bet2):
        fork_exclude_text = fork_exclude_text + 'Для проставления вилки ' + str(round((1 - L) * 100, 2)) \
                            + '% недостаточно средств, bal1=' \
                            + str(bal1) + ', bet1=' + str(bet1) \
                            + ', bal2=' + str(bal2) + ', bet2=' + str(bet2) + '\n'

    # Если баланс меньше 30% то берем плече только с коэф-м меньше 1,5
    if bal1 <= balance_line and k1 >= 1.3:
        fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) \
                            + '% исключена: баланс БК Олимп меньше 30%, а коэф-т >= 1.3 (' + str(k1) + ')\n'
    elif bal2 <= balance_line and k2 >= 1.3:
        fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) \
                            + '% исключена: баланс БК фонбет меньше 30%, а коэф-т >= 1.3 (' + str(k2) + ')\n'

    if bk1_score != bk2_score:
        fork_exclude_text = fork_exclude_text + 'Вилка ' \
                            + str(round((1 - L) * 100, 2)) \
                            + '% исключена т.к. счет не совпадает: olimp(' + bk1_score + ') fonbet(' + bk2_score + ')\n'

    if 43.0 < float(minute) < 50.0 and not time_break_fonbet and not is_2nd_half:  # Больше 43 минуты и не идет перерыв
        fork_exclude_text = \
            fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + '% исключена т.к. идет ' \
            + str(minute) + ' минута матча и это не перерыв и это не 2-й период \n'

    if float(minute) > 88.0:
        fork_exclude_text = \
            fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + '% исключена т.к. идет ' \
            + str(minute) + ' минута матча \n'

    fork_exclude_text = fork_exclude_text + check_l(L)

    if fork_exclude_text != '':
        prnt(info + '\n' + fork_exclude_text + '\n')
        v = False
    return v


def go_bets(wager_olimp, wager_fonbet, total_bet, key, deff_max):
    global bal1
    global bal2
    olimp_bet_type = str(go_bet_key.split('@')[-2])
    fonbet_bet_type = str(go_bet_key.split('@')[-1])
    # Проверяем ставили ли мы на этот матч, пока в ручную

    L = ((1 / float(wager_olimp['factor'])) + (1 / float(wager_fonbet['value'])))
    cur_proc = round((1 - L) * 100, 2)

    amount_olimp, amount_fonbet = get_sum_bets(wager_olimp['factor'], wager_fonbet['value'], total_bet, 'show')

    if __name__ == '__main__':
        wait_sec = 3.51  # max(0, (3.5 - deff_max))
        prnt('Wait sec: ' + str(wait_sec))
        time.sleep(wait_sec)
        with Manager() as manager:
            obj = manager.dict()

            recheck_o = Process(target=get_kof_olimp, args=(obj, wager_olimp['event'], olimp_bet_type,))
            recheck_fb = Process(
                target=get_kof_fonbet,
                args=(
                    obj,
                    wager_fonbet['event'],
                    int(wager_fonbet['factor']),
                    wager_fonbet['param']
                )
            )

            recheck_fb.start()
            recheck_o.start()

            recheck_fb.join()
            recheck_o.join()

            deff_max = max(obj['olimp_time_req'], obj['fonbet_time_req'])

            prnt('deff_max: ' + str(deff_max) + ', O ' + olimp_bet_type + ': ' + str(wager_olimp['factor']) + ' -> ' +
                 str(obj['olimp']) + '| F ' + fonbet_bet_type + ': ' + str(wager_fonbet['value']) + ' -> ' + str(
                obj['fonbet']))

            wager_fonbet['value'] = obj['fonbet']
            wager_olimp['value'] = obj['olimp']
            wager_olimp['factor'] = obj['olimp']

            # Проверяем что полученный коэфициент больше 1
            if float(obj['olimp']) > 1 < float(obj['fonbet']):

                # пересчетаем суммы ставок
                amount_olimp, amount_fonbet = get_sum_bets(float(obj['olimp']), float(obj['fonbet']), total_bet, 'show')

                # Выведем текую доходность вилки
                prnt('cur proc: ' + str(cur_proc) + '%')
                L = (1 / float(obj['olimp'])) + (1 / float(obj['fonbet']))
                new_proc = round((1 - L) * 100, 2)
                change_proc = round(new_proc - cur_proc, 2)
                prnt('new proc: ' + str(new_proc) + '%, change: ' + str(change_proc))

                if check_l(L) == '' or DEBUG:

                    is_recheck = True
                    fork_id = int(time.time())
                    fork_info = {
                        fork_id: {
                            "olimp": {
                                "id": wager_olimp["event"],
                                "kof": wager_olimp["factor"],
                                "amount": amount_olimp,
                                "reg_id": 0,
                                "bet_type": olimp_bet_type,
                                "balance": bal1,
                            },
                            "fonbet": {
                                "id": wager_fonbet["event"],
                                "kof": wager_fonbet["value"],
                                "amount": amount_fonbet,
                                "reg_id": 0,
                                "bet_type": fonbet_bet_type,
                                "balance": bal2
                            },
                        }
                    }
                else:
                    is_recheck = False

                prnt('Recheck fork result: ' + str(is_recheck))
                if is_recheck is False:
                    prnt('Fork is lost =(')
                    return False
            else:
                prnt('One of the coefficients is not available')
                return False

        if DEBUG:
            amount_olimp = 30
            amount_fonbet = 30
            return False

        with Manager() as manager:
            obj = manager.dict()

            pid_olimp = Process(target=bet_olimp_cl, args=(obj, amount_olimp, wager_olimp))
            pid_fonbet = Process(target=bet_fonbet_cl, args=(obj, amount_fonbet, wager_fonbet))

            pid_olimp.start()
            pid_fonbet.start()

            pid_fonbet.join()
            pid_olimp.join()

            prnt('obj: ' + str(obj))
            sale_timeout = 0  # randint(1, 3)
            if obj.get('fonbet_err') != 'ok' and obj.get('olimp_err') == 'ok':
                prnt('Ошибка при проставлении ставки в фонбет, делаю выкуп ставки в олимпе, через '
                     + str(sale_timeout) + ' сек.')
                obj['olimp'].sale_bet()

            if obj.get('olimp_err') != 'ok' and obj.get('fonbet_err') == 'ok':
                prnt('Ошибка при проставлении ставки в олимпе, делаю выкуп ставки в фонбет, через '
                     + str(sale_timeout) + ' сек.')
                obj['fonbet'].sale_bet()

            if obj.get('olimp_err') == 'ok' and obj.get('fonbet_err') == 'ok':
                prnt('Ставки проставлены успешно!')
                bal1 = bal1 - amount_olimp
                prnt('bal1: ' + str(bal1))
                bal2 = bal2 - amount_fonbet
                prnt('bal2: ' + str(bal2))

            # Добавим инфу о проставлении
            success.append(key)

            fork_info[fork_id]['olimp']['reg_id'] = obj['olimp'].get_reg_id()
            fork_info[fork_id]['fonbet']['reg_id'] = obj['fonbet'].get_reg_id()
            save_fork(fork_info)
            prnt('Matchs exclude: ' + str(success))
            sleep_post_work = 30
            prnt('Ожидание ' + str(sleep_post_work) + ' сек.')
            time.sleep(sleep_post_work)

            return True


def run_client():
    global server_forks
    global shutdown
    try:
        if 'Windows' == platform.system() or DEBUG:
            conn = http.client.HTTPConnection("localhost", 80, timeout=3.51)
        else:
            conn = http.client.HTTPConnection("149.154.70.53", 80, timeout=60)

        while True:
            if shutdown:
                err_str = 'Основной поток завершен, я тоже офф'
                conn.close()
                raise Shutdown(err_str)
            conn.request("GET", "")
            rs = conn.getresponse()
            data = rs.read().decode('utf-8')
            data_json = json.loads(data)
            server_forks = data_json
            time.sleep(0.5)
    except Shutdown as e:
        prnt(e)
        raise ValueError(e)
    except Exception as e:
        prnt(e)
        server_forks = {}
        conn.close()
        time.sleep(10)
        return run_client()


FONBET_USER = {"login": get_account_info('fonbet', 'login'), "password": get_account_info('fonbet', 'password')}
OLIMP_USER = {"login": get_account_info('olimp', 'login'), "password": get_account_info('olimp', 'password')}

bet1 = 0.  # Сумма ставки в БК1
bet2 = 0.  # Сумма ставки в БК2
total_bet = 0.  # Величина общей ставки;
betMax1 = 3000.  # Максимальная ставка в БК1 на данную позицию
betMax2 = 3000.  # Максимальная ставка в БК2 на данную позицию
betMin1 = 30.  # Минимальная ставка в БК1 на данную позицию
betMin2 = 30.  # Минимальная ставка в БК2 на данную позицию
pf1 = 0.  # Прибыль в БК1
pf2 = 0.  # Прибыль в БК2
pf = 0.  # минимальная прибыль;
bal1 = 0
bal2 = 0
N = 0  # счетчик (количество, проставленных вилок)
F = 0  # счетчик (количество, найденых вилок)
balance_line = 0  # (bal1 + bal2) / 2 / 100 * 60
time_get_balance = datetime.datetime.now()
time_live = datetime.datetime.now()

# wager_fonbet:{'event': '12797479', 'factor': '921', 'param': '', 'score': '0:0', 'value': '2.35'}
# wager_fonbet:{'apid': '1144260386:45874030:1:3:-9999:3:NULL:NULL:1', 'factor': '1.66', 'sport_id': 1, 'event': '45874030'}

if __name__ == '__main__':
    prnt('DEBUG: ' + str(DEBUG))

    time_get_balance = datetime.datetime.now()
    time_live = datetime.datetime.now()

    if DEBUG:
        bal1 = 20000
        bal2 = 20000
        total_bet = round(0.10 * (bal1 + bal2))  # Общая масксимальная сумма ставки
    else:
        bal1 = OlimpBot(OLIMP_USER).get_balance()  # Баланс в БК1
        bal2 = FonbetBot(FONBET_USER).get_balance()  # Баланс в БК2
        total_bet = 280  # round(0.10 * (bal1 + bal2))  # Общая масксимальная сумма ставки
    balance_line = (bal1 + bal2) / 2 / 100 * 30

    prnt('bal1: ' + str(bal1) + ' руб.')
    prnt('bal2: ' + str(bal2) + ' руб.')
    prnt('total bet: ' + str(total_bet) + ' руб.')
    prnt('balance line: ' + str(balance_line))

    server_forks = dict()
    success = []
    start_see_fork = threading.Thread(target=run_client)  # , args=(server_forks,))
    start_see_fork.start()

    while True:

        balance_line = (bal1 + bal2) / 2 / 100 * 30

        shutdown_minutes = 60 * (60 * 5)  # секунды * на кол-во (60*1) - это час
        if (datetime.datetime.now() - time_live).total_seconds() > (shutdown_minutes):
            err_str = 'Прошло ' + str(shutdown_minutes / 60 / 60) + ' ч., я выключился...'
            prnt(err_str)
            shutdown = True
            raise ValueError(err_str)

        # Обновление баланса каждые 35-45 минут
        ref_balace = randint(35, 45)
        if (datetime.datetime.now() - time_get_balance).total_seconds() > (60 * ref_balace):
            prnt('It took more than ' + str(ref_balace) + ' minutes, the refresh balances:')
            time_get_balance = datetime.datetime.now()
            bal1 = OlimpBot(OLIMP_USER).get_balance()  # Баланс в БК1
            bal2 = FonbetBot(FONBET_USER).get_balance()  # Баланс в БК2

        if server_forks:
            go_bet_key = ''
            l = 0.0
            go_bet_json = {}
            for key, val_json in server_forks.items():
                # print(json.dumps(val_json, ensure_ascii=False))
                l_temp = val_json.get('l', 0.0)

                k1_type = key.split('@')[-1]
                k2_type = key.split('@')[-2]

                name = val_json.get('name', 'name')
                pair_math = val_json.get('pair_math', 'pair_math')

                bk1_score = str(val_json.get('bk1_score', 'bk1_score'))
                bk2_score = str(val_json.get('bk2_score', 'bk2_score'))

                score = '[' + bk1_score + '|' + bk2_score + ']'
                v_time = val_json.get('time', 'v_time')
                minute = val_json.get('minute', 0)
                time_break_fonbet = val_json.get('time_break_fonbet')
                is_2nd_half = val_json.get('is_2nd_half')
                time_last_upd = val_json.get('time_last_upd', 1)

                deff_olimp = round(float(time.time() - float(val_json.get('time_req_olimp', 0))))
                deff_fonbet = round(float(time.time() - float(val_json.get('time_req_fonbet', 0))))
                deff_max = max(0, deff_olimp, deff_fonbet)

                bk1_bet_json = val_json.get('kof_olimp')
                bk2_bet_json = val_json.get('kof_fonbet')

                bk1_hist = bk1_bet_json.get('hist', {})
                bk2_hist = bk2_bet_json.get('hist', {})

                k1 = bk1_bet_json.get('factor', 0)
                k2 = bk2_bet_json.get('value', 0)

                try:
                    info = key + ': ' + name + \
                           ' ' + k1_type + '=' + str(k1) + '/' + k2_type + '=' + str(k2) + ', ' + \
                           v_time + ' (' + str(minute) + ') ' + \
                           score + ' ' + str(pair_math) + \
                           ', max deff: ' + str(deff_max)
                except Exception as e:
                    prnts('error: ' + str(e))
                    info = ''

                if 0.0 <= l < l_temp and deff_max < 10 or DEBUG:
                    bet1, bet2 = get_sum_bets(k1, k2, total_bet)
                    # Проверим вилку на исключения
                    if check_fork(
                            key, l_temp, k1, k2, bk1_score, bk2_score,
                            minute, time_break_fonbet, is_2nd_half, info
                    ) or DEBUG:
                        go_bet_key = key
                        l = l_temp
                        go_bet_json = val_json
                elif deff_max >= 10:
                    prnt('deff_max=' + str(deff_max) + ': ' + str(key) + str(val_json), 'hide')
            if go_bet_key:
                prnt('')
                prnt('Go bets: ' + info)
                fork_success = go_bets(
                    go_bet_json.get('kof_olimp'),
                    go_bet_json.get('kof_fonbet'),
                    total_bet,
                    go_bet_key,
                    deff_max
                )
            else:
                prnt('not fork: ' + str(val_json), 'hide')
        else:
            pass
