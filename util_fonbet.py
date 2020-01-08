# coding:utf-8
import requests
from proxy_worker import del_proxy
import time
from exceptions import FonbetMatchСompleted
from utils import prnts, get_vector, print_j, if_exists, sport_list
import re
import sys
import traceback
import copy

url_fonbet = 'https://line-01.ccf4ab51771cacd46d.com'
url_fonbet_matchs = url_fonbet + '/live/currentLine/en/?2lzf1earo8wjksbh22s'
url_fonbet_pre_matchs = url_fonbet + '/line/mobile/showSports?lineType=full_line&skId=1&lang=en'
url_fonbet_top_matchs = url_fonbet + '/line/topEvents3?place=live&sysId=1&lang=en&salt=2miqtggxzksk0amacau'
# url_fonbet_match = 'https://23.111.80.222/line/eventView?eventId='
url_fonbet_match = url_fonbet + '/line/eventView?eventId='
UA = 'Mozilla/5.0 (Windows NT 10; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.3163.100 Safari/537.36'
fonbet_header = {
    'User-Agent': 'Fonbet/5.2.2b (Android 21; Phone; com.bkfonbet)',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip'
}
base_payload = {
    "appVersion": "5.1.3b",
    "lang": "ru",
    "rooted": "false",
    "sdkVersion": 21,
    "sysId": 4
}

BASE_LINE = [921, 922, 923, 924, 1571, 925]

# VICTORIES
VICTS = [['П1', 921], ['Н', 922], ['П2', 923], ['П1Н', 924], ['12', 1571], ['П2Н', 925],
         ['ОЗД', 4241], ['ОЗН', 4242], ['КЗ1', 4235], ['КНЗ1', 4236], ['КЗ2', 4238], ['КНЗ2', 4239]]
# Обе забьют:да/Обе забьют:нет/Команда 1 забьет/Команда 1 не забьет/Команда 2 забьет/Команда 2 не забьет
# TOTALS
TTO = [['ТБ({})', 930], ['ТБ({})', 1696], ['ТБ({})', 1727], ['ТБ({})', 1730], ['ТБ({})', 1733]]
TTU = [['ТМ({})', 931], ['ТМ({})', 1697], ['ТМ({})', 1728], ['ТМ({})', 1731], ['ТМ({})', 1734]]
# TEAM TOTALS-1
TT1O = [['ТБ1({})', 1809], ['ТБ1({})', 1812], ['ТБ1({})', 1815]]
TT1U = [['ТМ1({})', 1810], ['ТМ1({})', 1813], ['ТМ1({})', 1816]]
# TEAM TOTALS-2
TT2O = [['ТБ2({})', 1854], ['ТБ2({})', 1873], ['ТБ2({})', 1880]]
TT2U = [['ТМ2({})', 1871], ['ТМ2({})', 1874], ['ТМ2({})', 1881]]
# FORA
FORA = [['Ф1({})', 927], ['Ф2({})', 928],
        ['Ф1({})', 910], ['Ф1({})', 989], ['Ф1({})', 1569],
        ['Ф2({})', 991], ['Ф2({})', 1572], ['Ф2({})', 1572]
        ]


def get_matches_fonbet(proxy, time_out, type=''):
    global url_fonbet
    global UA

    if type == 'top':
        url = url_fonbet_top_matchs
    elif type == 'pre':
        url = url_fonbet_pre_matchs
    else:
        url = url_fonbet_matchs

    try:
        proxies = {'http': proxy}
        # prnts('Fonbet set proxy: ' + proxy, 'hide')
    except Exception as e:
        err_str = 'Fonbet error set proxy: ' + str(e)
        prnts(err_str)
        raise ValueError(err_str)

    try:
        resp = requests.get(
            url,
            headers={'User-Agent': UA},
            timeout=time_out,
            verify=False,
            proxies=proxies,
        )
        try:
            res = resp.json()
        except Exception as e:
            err_str = 'Fonbet error : ' + str(e)
            prnts(err_str)
            raise ValueError('Exception: ' + str(e))

        if res.get("result") != "error":
            return res, resp.elapsed.total_seconds()
        else:
            raise ValueError(res.get("errorMessage"))

    except requests.exceptions.ConnectionError as e:
        err_str = 'Фонбет, код ошибки 0: ' + str(e)
        prnts(err_str)
        proxies = del_proxy(proxy, proxies)
        raise ValueError(err_str)
    except requests.exceptions.RequestException as e:
        err_str = 'Фонбет, код ошибки 1: ' + str(e)
        prnts(err_str)
        proxies = del_proxy(proxy, proxies)
        raise ValueError(err_str)
    except Exception as e:
        err_str = 'Фонбет, код ошибки 2: ' + str(e)
        prnts(err_str)
        # proxi_list = del_proxy(proxy, proxies)
        raise ValueError(err_str)


def get_match_fonbet(match_id, proxi_list, proxy, time_out, pair_mathes):
    global url_fonbet_match
    global fonbet_header

    match_exists = False
    for pair_match in pair_mathes:
        if match_id in pair_match:
            match_exists = True
    if match_exists is False:
        err_str = 'Фонбет: матч ' + str(match_id) + ' не найден в спике активных, поток get_match_fonbet завершен.'
        raise FonbetMatchСompleted(err_str)

    try:
        proxies = {'http': proxy}
    except Exception as e:
        err_str = 'Fonbet error set proxy by ' + str(match_id) + ': ' + str(e)
        prnts(err_str)
        raise ValueError(err_str)

    try:
        resp = requests.get(
            url_fonbet_match + str(match_id) + "&lang=en",
            headers=fonbet_header,
            timeout=time_out,
            verify=False,
            proxies=proxies,
        )
        try:
            res = resp.json()
            # print_j(res)
        except Exception as e:
            err_str = 'Fonbet error by ' + str(match_id) + ': ' + str(e)
            prnts(err_str)
            raise ValueError(err_str)

        if res.get("result") != "error":
            return res, resp.elapsed.total_seconds()
        elif res.get("place", "live") == "notActive":
            raise FonbetMatchСompleted('0 Фонбет, матч ' + str(match_id) + ' завершен, поток выключен!')
        else:
            if 'Event not found' in res.get("errorMessage"):
                raise FonbetMatchСompleted('1 Фонбет, матч ' + str(match_id) + ' завершен, поток выключен!')
            err = res.get("errorMessage")
            prnts(str(err))
            raise ValueError(str(err))

    except requests.exceptions.ConnectionError as e:
        err_str = 'Фонбет ' + str(match_id) + ', код ошибки 0: ' + str(e)
        prnts(err_str)
        proxi_list = del_proxy(proxy, proxi_list)
        raise ValueError(err_str)
    except requests.exceptions.RequestException as e:
        err_str = 'Фонбет ' + str(match_id) + ', код ошибки 1: ' + str(e)
        prnts(err_str)
        proxi_list = del_proxy(proxy, proxi_list)
        raise ValueError(err_str)
    except FonbetMatchСompleted as e:
        raise FonbetMatchСompleted('2 ' + str(e))
    except Exception as e:
        if 'Event not found' in str(e):
            raise FonbetMatchСompleted('3 Фонбет, матч ' + str(match_id) + ' завершен, поток выключен! ' + str(e))
        err_str = 'Фонбет ' + str(match_id) + ', код ошибки 2: ' + str(e)
        prnts(err_str)
        # proxi_list = del_proxy(proxy, proxi_list)
        raise ValueError(err_str)


def get_bets_fonbet(bets_fonbet, match_id, proxies_fonbet, proxy, time_out, pair_mathes, arr_fonbet_top_kofs):
    global VICTS, TTO, TTU, TT1O, TT1U, TT2O, TT2U, BASE_LINE, FORA
    global sport_list

    match_exists = False
    for pair_match in pair_mathes:
        if match_id in pair_match:
            match_exists = True
    if match_exists is False:
        err_str = 'Фонбет: матч ' + str(match_id) + ' не найден в спике активных, поток get_bets_fonbet завершен.'
        raise FonbetMatchСompleted(err_str)

    key_id = str(match_id)
    try:
        resp, time_resp = get_match_fonbet(match_id, proxies_fonbet, proxy, time_out, pair_mathes)

        time_start_proc = time.time()

        TT = []
        for bet in [TTO, TTU, TT1O, TT1U, TT2O, TT2U, FORA]:
            TT.extend(bet)

        for event in resp.get("events"):

            if event.get('parentId') == 0:
                # import json
                # print(json.dumps(event, ensure_ascii=False))
                score = event.get('score', '0:0').replace('-', ':')
                sc1 = 0
                sc2 = 0
                try:
                    scs = re.findall('[0-9]:[0-9]', score)[0]
                    try:
                        sc1 = int(scs.split(':')[0])
                    except Exception as e:
                        prnts('err util_fonbet sc1: ' + str(match_id) + ' score=' + str(score) + ' ' + str(e))
                    try:
                        sc2 = int(scs.split(':')[1])
                    except Exception as e:
                        prnts('err util_fonbet sc2: ' + str(match_id) + ' score=' + str(score) + ' ' + str(e))
                except Exception as e:
                    prnts('err util_fonbet scs: ' + str(match_id) + ' score=' + str(score) + ' ' + str(e))

                timer = event.get('timer', '00:00')
                minute = event.get('timerSeconds', 0) / 60

                skId = event.get('skId')
                skName = event.get('skName')

                minute_complite = if_exists(sport_list, 'fonbet', skId, 'min')
                if minute_complite:
                    if minute >= (minute_complite - 2):
                        err_str = 'Фонбет: матч, ' + skName + ' - ' + str(match_id) + ' завершен, т.к. ' + str(minute_complite - 2) + ' минут прошло.'
                        raise FonbetMatchСompleted(err_str)

                sport_name = event.get('sportName')
                name = event.get('name')
                priority = event.get('priority')
                score_1st = event.get('scoreComment', '').replace('-', ':')
                if event.get('parentId') == 0 or 'st half' in name or 'nd half' in name:
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
                                # 'time_change_total': round(time.time()),
                                # 'avg_change_total': [],
                                'kofs': {}
                            }

                    half = ''
                    if 'st half' in name or 'nd half' in name:
                        half = name.replace('st half', '').repoalce('nd half', '')

                    for cat in event.get('subcategories', {}):
                        cat_name = cat.get('name')
                        if cat_name in (
                                '1X2 (90 min)',
                                '1X2',
                                'Goal - no goal',
                                'Total', 'Totals', 'Team Totals-1', 'Team Totals-2',
                                'Hcap',
                        ):
                            for kof in cat.get('quotes'):

                                factorId = str(kof.get('factorId'))
                                pValue = kof.get('pValue', '')
                                p = kof.get('p', '').replace('+', '')

                                kof_is_block = kof.get('blocked', False)
                                if kof_is_block:
                                    value = 0
                                else:
                                    value = kof.get('value', 0)

                                for vct in VICTS:
                                    coef = half + str(vct[0])
                                    if str(vct[1]) == factorId:

                                        kof_order = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('order', [])
                                        time_change = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('time_change', time.time())
                                        avg_change = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('avg_change', [])

                                        try:
                                            if value != kof_order[-1]:
                                                kof_order.append(value)
                                                avg_change.append(round(time.time() - time_change))
                                                time_change = time.time()
                                            elif value == kof_order[-1]:
                                                avg_change[-1] = round(time.time() - time_change)
                                        except IndexError:
                                            # firs
                                            kof_order.append(value)
                                            avg_change.append(0)

                                        is_hot = False
                                        if int(factorId) in arr_fonbet_top_kofs.get(key_id, []):
                                            is_hot = True

                                        is_base_line = False
                                        if int(factorId) in BASE_LINE:
                                            is_base_line = True

                                        bets_fonbet[key_id]['kofs'].update(
                                            {
                                                coef:
                                                    {
                                                        'time_req': round(time.time()),
                                                        'event': event.get('id'),
                                                        'value': value,
                                                        'param': '',
                                                        'factor': factorId,
                                                        'base_line': is_base_line,
                                                        'score': score,
                                                        'vector': get_vector(coef, sc1, sc2),
                                                        'is_hot': is_hot,
                                                        'hist': {
                                                            'time_change': time_change,
                                                            'avg_change': avg_change,
                                                            'order': kof_order
                                                        }
                                                    }
                                            }
                                        )
                                        # if is_hot:
                                        #     print(bets_fonbet[key_id])

                                for stake in TT:
                                    coef = half + str(stake[0].format(p))  # + num_team
                                    if str(stake[1]) == factorId:

                                        kof_order = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('order', [])
                                        time_change = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('time_change', time.time())
                                        avg_change = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('avg_change', [])

                                        try:
                                            if value != kof_order[-1]:
                                                kof_order.append(value)
                                                avg_change.append(round(time.time() - time_change))
                                                time_change = time.time()
                                            elif value == kof_order[-1]:
                                                avg_change[-1] = round(time.time() - time_change)
                                        except IndexError:
                                            # firs
                                            kof_order.append(value)
                                            avg_change.append(0)

                                        is_hot = False
                                        if int(factorId) in arr_fonbet_top_kofs.get(key_id, []):
                                            is_hot = True

                                        bets_fonbet[key_id]['kofs'].update(
                                            {
                                                coef:
                                                    {
                                                        'time_req': round(time.time()),
                                                        'event': event.get('id'),
                                                        'value': value,
                                                        'param': pValue,
                                                        'factor': factorId,
                                                        'score': score,
                                                        'vector': get_vector(coef, sc1, sc2),
                                                        'is_hot': is_hot,
                                                        'hist': {
                                                            'time_change': time_change,
                                                            'avg_change': avg_change,
                                                            'order': kof_order
                                                        }
                                                    }}
                                        )

        # for val in bets_fonbet.get(key_id, {}).get('kofs', {}).values():
        #     time_change_kof = val.get('hist', {}).get('time_change')
        #     time_change_tot = bets_fonbet.get(key_id, {}).get('time_change_total')
        #     avg_change_total = bets_fonbet.get(key_id, {}).get('avg_change_total', [])
        #     if round(time_change_tot) < round(time_change_kof):
        #         avg_change_total.append(round(time_change_kof - time_change_tot))
        #         bets_fonbet[key_id].update({'time_change_total': time_change_kof})
        #         bets_fonbet[key_id].update({'avg_change_total': avg_change_total})

        try:
            for i in list(bets_fonbet):
                for j in list(bets_fonbet[i].get('kofs', {})):
                    if round(float(time.time() - float(bets_fonbet[i]['kofs'][j].get('time_req', 0)))) > 4 and bets_fonbet[i]['kofs'][j].get('value', 0) > 0:
                        try:
                            bets_fonbet[i]['kofs'][j]['value'] = 0
                            # prnts('Фонбет, данные по котировке из БК не получены более X сек., знач. выставил в 0: ' + key_id_in + ' ' + str(i), 'hide')
                        except Exception as e:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            err_str = 'error: ' + str(e) + ' (' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))) + ')'
                            prnts('Фонбет, ошибка 1 при удалении старой котирофки: ' + str(err_str))
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_str = 'error: ' + str(e) + ' (' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))) + ')'
            prnts('Фонбет, ошибка 2 при удалении старой котирофки: ' + str(err_str))
        return time_resp + (time.time() - time_start_proc)
    except FonbetMatchСompleted as e:
        if bets_fonbet.get(key_id):
            bets_fonbet.pop(key_id)
        raise FonbetMatchСompleted('4 ' + str(e))
    except Exception as e:
        prnts(e)
        if bets_fonbet.get(key_id):
            bets_fonbet.pop(key_id)
        raise ValueError(e)


if __name__ == '__main__':
    pass
