# coding: utf-8
from hashlib import md5
import requests
from proxy_worker import del_proxy
import re
import time
from utils import prnts, get_vector, get_param, if_exists, sport_list, print_j
from exceptions import *
import sys
import traceback
import math
import run

url_autorize = "https://{}.olimp-proxy.ru/api/{}"
payload = {"lang_id": "0", "platforma": "ANDROID1"}
head = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'okhttp/3.9.1'
}


def get_xtoken_bet(payload):
    sorted_values = [str(payload[key]) for key in sorted(payload.keys())]
    to_encode = ";".join(sorted_values + [olimp_secret_key])
    return {"X-TOKEN": md5(to_encode.encode()).hexdigest()}


olimp_url = 'http://' + get_param('server_olimp')
olimp_url_https = 'https://' + get_param('server_olimp')
olimp_url_random = 'https://{}.olimp-proxy.ru'  # c 13 по 18й

olimp_secret_key = 'b2c59ba4-7702-4b12-bef5-0908391851d9'

olimp_head = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'okhttp/3.9.1'
}

olimp_data = {
    "live": 1,
    "platforma": "ANDROID1",
    "lang_id": 0,
    "time_shift": 0
}

abbreviations = {
    "Победапервой": "П1",
    "Победавторой": "П2",

    "Ничья": "Н",
    "Перваянепроиграет": "П1Н",
    "Втораянепроиграет": "П2Н",
    "Ничьейнебудет": "12",

    "Обезабьют:да": "ОЗД",
    "Обезабьют:нет": "ОЗН",
    "Т1забьет:да": "КЗ1",
    "Т1забьет:нет": "КНЗ1",
    "Т2забьет:да": "КЗ2",
    "Т2забьет:нет": "КНЗ2",
    "Тоталбол": "ТБ({})",
    "Тоталмен": "ТМ({})",
    "Тотал1-готаймабол": "1ТБ({})",
    "Тотал1-готаймамен": "1ТМ({})",
    "Тотал2-готаймабол": "2ТБ({})",
    "Тотал2-готаймамен": "2ТМ({})",
    # "Т1бол":"ИТБ1({})",
    # "Т1мен":"ИТМ1({})",
    # "Т2бол":"ИТБ2({})",
    # "Т2мен":"ИТМ2({})"
    "Т1бол": "ТБ1({})",
    "Т1мен": "ТМ1({})",
    "Т2бол": "ТБ2({})",
    "Т2мен": "ТМ2({})",

    "П1сфорой": "Ф1({})",
    "П2сфорой": "Ф2({})",

    "П1в1-мт.сфорой": "1Ф1({})",
    "П2в1-мт.сфорой": "1Ф2({})",
}


def olimp_get_xtoken(payload, olimp_secret_key):
    sorted_values = [str(payload[key]) for key in sorted(payload.keys())]
    to_encode = ";".join(sorted_values + [olimp_secret_key])
    return {"X-TOKEN": md5(to_encode.encode()).hexdigest()}


def get_matches_olimp(proxy, time_out, place, sport_id=None, time=6, liga_id=None):
    global olimp_data
    global olimp_head

    try:
        http_type = 'https' if 'https' in proxy else 'http'
        url = olimp_url_https if 'https' in proxy else olimp_url
        proxies = {http_type: proxy}
        # prnts('Olimp set proxy: ' + proxy, 'hide')
    except Exception as e:
        err_str = 'Olimp error set proxy: ' + str(e)
        prnts(err_str)
        raise ValueError(err_str)
    olimp_data_ll = olimp_data.copy()
    v_url = ''
    if place == 'live':
        v_url = url + '/api/slice/'
    else:
        v_url = url + '/api/' + place + '/'
        olimp_data_ll.update({'live': 0})
        olimp_data_ll.update({'sport_id': sport_id})

        if place == 'matches':
            olimp_data_ll.update({'id': liga_id})
        else:
            olimp_data_ll.pop('time_shift', None)
        olimp_data_ll['time'] = max(time, 6)  # in app avalible 6 min hours

    olimp_data_ll.update({'lang_id': 2})
    olimp_head_ll = olimp_head
    olimp_head_ll.update(olimp_get_xtoken(olimp_data_ll, olimp_secret_key))
    olimp_head_ll.pop('Accept-Language', None)
    # print(v_url, olimp_data_ll, proxies)
    try:
        resp = requests.post(
            v_url,
            data=olimp_data_ll,
            headers=olimp_head_ll,
            timeout=time_out,
            verify=False,
            proxies=proxies,
        )
        try:
            res = resp.json()
        except Exception as e:
            err_str = 'Olimp error : ' + str(e)
            prnts(err_str)
            raise ValueError('Exception: ' + str(e))

        if res.get("error").get('err_code', 999) in (0, 511, 423):
            return res.get('data'), resp.elapsed.total_seconds()
        else:
            err_str = res.get("error")
            err_str = 'Olimp error : ' + str(err_str)
            prnts(err_str)
            raise ValueError(str(err_str))

    except requests.exceptions.Timeout as e:
        err_str = 'Олимп, код ошибки Timeout: ' + str(e)
        prnts(err_str)
        proxies = del_proxy(proxy, proxies)
        raise TimeOut(err_str)
    except requests.exceptions.ConnectionError as e:
        err_str = 'Олимп, код ошибки ConnectionError: ' + str(e)
        prnts(err_str)
        proxies = del_proxy(proxy, proxies)
        raise ValueError(err_str)
    except requests.exceptions.RequestException as e:
        err_str = 'Олимп, код ошибки RequestException: ' + str(e)
        prnts(err_str)
        proxies = del_proxy(proxy, proxies)
        raise ValueError(err_str)
    except ValueError as e:
        if str(e) == '404':
            raise OlimpMatchСompleted('Олимп, матч завершен, поток выключен!')

        if resp.text:
            text = resp.text
        err_str = 'Олимп, код ошибки ValueError: ' + str(e) + str(text)
        prnts(err_str)
        proxi_list = del_proxy(proxy, proxies)
        raise ValueError(err_str)
    except Exception as e:
        err_str = 'Олимп, код ошибки Exception: ' + str(e)
        prnts(err_str)
        proxies = del_proxy(proxy, proxies)
        raise ValueError(err_str)


def get_xtoken(payload, olimp_secret_key):
    sorted_values = [str(payload[key]) for key in sorted(payload.keys())]
    to_encode = ";".join(sorted_values + [olimp_secret_key])

    X_TOKEN = md5(to_encode.encode()).hexdigest()
    return {"X-TOKEN": X_TOKEN}


def to_abb(sbet):
    sbet = sbet.replace(' ', '').replace('\t', '')
    value = re.findall('\((.*)\)', sbet)[0]
    key = re.sub('\((.*)\)', '', sbet)
    abr = ''
    try:
        abr = abbreviations[key].format(value)
    except Exception as e:
        if run.DEBUG:
            prnts('error: ' + str(e) + ', to_abb("' + sbet + '"), value=' + value + ', key=' + key, 'hide')
    return abr


def get_match_olimp(match_id, proxi_list, proxy, time_out, pair_mathes, type):
    global olimp_url
    global olimp_url_https
    global olimp_data

    match_exists = False
    for pair_match in pair_mathes:
        if match_id in pair_match:
            match_exists = True
            sport_id = if_exists(sport_list, 'name', pair_match[2], 'olimp')
    if match_exists is False:
        err_str = 'Олимп: матч ' + str(match_id) + ' не найден в спике активных, поток get_match_olimp завершен.'
        raise OlimpMatchСompleted(err_str)

    olimp_data_m = olimp_data.copy()

    olimp_data_m.update({'id': match_id})
    olimp_data_m.update({'lang_id': 0})
    olimp_data_m.update({'sport_id': sport_id})
    if type == 'pre':
        olimp_data_m.update({'live': 0})

    olimp_stake_head = olimp_head.copy()

    token = get_xtoken(olimp_data_m, olimp_secret_key)

    olimp_stake_head.update(token)
    olimp_stake_head.pop('Accept-Language', None)

    try:
        http_type = 'https' if 'https' in proxy else 'http'
        url = olimp_url_https if 'https' in proxy else olimp_url
        proxies = {http_type: proxy}
    except Exception as e:
        err_str = 'Olimp error set proxy by ' + str(match_id) + ': ' + str(e)
        prnts(err_str)
        raise ValueError(err_str)

    try:
        resp = requests.post(
            url + '/api/stakes/',
            data=olimp_data_m,
            headers=olimp_stake_head,
            timeout=time_out,
            verify=False,
            proxies=proxies
        )
        try:
            res = resp.json()
            # print('res: ' + str(res))
        except Exception as e:
            err_str = 'Olimp error by ' + str(match_id) + ': ' + str(e)
            prnts(err_str)
            raise ValueError(err_str)
        # {"error": {"err_code": 404, "err_desc": "Прием ставок приостановлен"}, "data": null}
        # {"error": {"err_code": 511, "err_desc": "Sign access denied"}, "data": null}
        # {'err_code': 423, 'err_desc': 'Переменная: id запрещена в данном методе!'}
        if res.get("error").get('err_code', 999) in (0, 404, 511, 423):
            return res.get('data'), resp.elapsed.total_seconds()
        else:
            err = res.get("error")
            prnts(str(err))
            raise ValueError(str(err.get('err_code')))

    except requests.exceptions.Timeout as e:
        err_str = 'Олимп, код ошибки Timeout: ' + str(e)
        prnts(err_str)
        proxi_list = del_proxy(proxy, proxi_list)
        raise TimeOut(err_str)

    except requests.exceptions.ConnectionError as e:
        err_str = 'Олимп ' + str(match_id) + ', код ошибки ConnectionError: ' + str(e)
        prnts(err_str)
        proxi_list = del_proxy(proxy, proxi_list)
        raise ValueError(err_str)
    except requests.exceptions.RequestException as e:
        err_str = 'Олимп ' + str(match_id) + ', код ошибки RequestException: ' + str(e)
        prnts(err_str)
        proxi_list = del_proxy(proxy, proxi_list)
        raise ValueError(err_str)
    except ValueError as e:
        if str(e) == '404':
            raise OlimpMatchСompleted('Олимп, матч ' + str(match_id) + ' завершен, поток выключен!')

        if resp.text:
            text = resp.text
        err_str = 'Олимп ' + str(match_id) + ', код ошибки ValueError: ' + str(e) + str(text)
        prnts(err_str)
        proxi_list = del_proxy(proxy, proxi_list)
        raise ValueError(err_str)
    except Exception as e:
        if str(e) == '404':
            raise OlimpMatchСompleted('Олимп, матч ' + str(match_id) + ' завершен, поток выключен!')
        err_str = 'Олимп ' + str(match_id) + ', код ошибки Exception: ' + str(e)
        prnts(err_str)
        proxi_list = del_proxy(proxy, proxi_list)
        raise ValueError(err_str)


def get_bets_olimp(bets_olimp, match_id, proxies_olimp, proxy, time_out, pair_mathes, place):
    global sport_list
    key_id = str(match_id)

    match_exists = False
    for pair_match in pair_mathes:
        if match_id in pair_match:
            match_exists = True
            minute_complite = if_exists(sport_list, 'name', pair_match[2], 'min')
            my_sport_name = pair_match[2]
    if match_exists is False:
        err_str = 'Олимп: матч ' + str(match_id) + ' не найден в спике активных, поток get_bets_olimp завершен.'
        raise OlimpMatchСompleted(err_str)
    resp_temp = ''
    try:
        resp, time_resp = get_match_olimp(match_id, proxies_olimp, proxy, time_out, pair_mathes, place)
        resp_temp = str(resp)
        time_start_proc = time.time()
        if place == 'pre':
            if resp:
                math_block = resp.get('ms', False)
            else:
                math_block = False
        else:
            math_block = True if not resp or str(resp.get('ms', '1')) != '2' or resp.get('error', {'err_code': 0}).get('err_code') == 404 else False
            # 1 - block, 2 - available
        if not math_block:
            timer = resp.get('t', '')
            minute = -1  # (2:0) Перерыв
            try:
                minute = int(re.findall('\d{1,2}\\"', resp.get('sc', ''))[0].replace('"', ''))
            except:
                pass

            if minute_complite:
                if minute >= (int(minute_complite) - 2):
                    err_str = 'Олимп: матч, ' + my_sport_name + ' - ' + str(match_id) + ' завершен, т.к. ' + str(minute_complite - 2) + ' минут прошло.'
                    raise OlimpMatchСompleted(err_str)
            skId = resp.get('sport_id')
            skName = resp.get('sn')
            sport_name = resp.get('cn')
            champid = sport_name  # NOT FOUND
            name = resp.get('n')
            if name == 'Ювентус - Удинезе':
                print('resp: ' + str(resp))
            start_time = int(resp.get('t', 0))
            start_after_min = math.floor((start_time - int(time.time())) / 60)
            if place == 'pre':
                if start_after_min:
                    if start_after_min <= 0:
                        err_str = 'Олимп: pre матч, ' + skName + ' - ' + str(match_id) + ' завершен, т.к. ' + str(start_after_min) + ' минут до начала матча.'
                        raise OlimpMatchСompleted(err_str)
            if not start_after_min:
                start_after_min = 0
            score = ''
            sc1 = 0
            sc2 = 0
            try:
                score = resp.get('sc', '0:0').split(' ')[0]
                try:
                    sc1 = int(score.split(':')[0])
                except Exception as e:
                    prnts('err util_olimp sc1: ' + str(e))
                try:
                    sc2 = int(score.split(':')[1])
                except Exception as e:
                    prnts('err util_olimp sc2: ' + str(e))
            except:
                if run.DEBUG:
                    prnts('err util_olimp error split: ' + str(resp.get('sc', '0:0')))

            try:
                bets_olimp[key_id].update({
                    'sport_id': skId,
                    'place': place,
                    'sport_name': skName,
                    'league': sport_name,
                    'liga_id': champid,
                    'name': name,
                    'score': score,
                    'time_start': timer,
                    'start_after_min': start_after_min,
                    'start_time': start_time,
                    'time_req': round(time.time())
                })
            except:
                bets_olimp[key_id] = {
                    'sport_id': skId,
                    'place': place,
                    'sport_name': skName,
                    'league': sport_name,
                    'liga_id': champid,
                    'name': name,
                    'score': score,
                    'time_start': timer,
                    'start_after_min': start_after_min,
                    'start_time': start_time,
                    'time_req': round(time.time()),
                    # 'time_change_total': round(time.time()),
                    # 'avg_change_total': [],
                    'kofs': {}
                }

            for c in resp.get('it', []):
                # del: угловые
                group_kof = c.get('n', '').replace(' ', '').lower()
                group_kof = group_kof.replace('азиатские', '')
                if group_kof in ['основные', 'голы', 'инд.тотал', 'доп.тотал', 'исходыпотаймам', 'победасучетомфоры', 'форы', 'тоталы', 'инд.тоталы']:
                    for d in c.get('i', []):
                        if 'обе забьют: '.lower() \
                                in d.get('n', '').lower() \
                                or 'забьет: '.lower() \
                                in d.get('n', '').lower() \
                                or 'никто не забьет: '.lower() \
                                in d.get('n', '').lower() \
                                or 'победа '.lower() \
                                in d.get('n', '').lower() \
                                or d.get('n', '').lower().endswith(' бол') \
                                or d.get('n', '').lower().endswith(' мен') \
                                or 'с форой'.lower() \
                                in d.get('n', '').lower() \
                                or 'первая не проиграет'.lower() \
                                in d.get('n', '').lower() \
                                or 'вторая не проиграет'.lower() \
                                in d.get('n', '').lower() \
                                or 'ничьей не будет' \
                                in d.get('n', '').lower() \
                                or 'ничья'.lower() \
                                in d.get('n', '').lower() \
                                or 'форы' in group_kof:
                            if 'форы' in group_kof:
                                key_r = d.get('n', '').replace(resp.get('c1', ''), 'П1сфорой').replace(resp.get('c2', ''), 'П2сфорой')
                                key_r = key_r.replace(' ', '')
                            else:
                                key_r = d.get('n', '').replace(resp.get('c1', ''), 'Т1').replace(resp.get('c2', ''), 'Т2')
                            coef = str([
                                           abbreviations[c.replace(' ', '')]
                                           if c.replace(' ', '') in abbreviations.keys()
                                           else c.replace(' ', '')
                                           if '(' not in c.replace(' ', '')
                                           else to_abb(c)
                                           for c in [key_r]
                                       ][0])
                            if coef:
                                value = d.get('v', 0)
                                kof_order = bets_olimp[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('order', [])
                                time_change = bets_olimp[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('time_change', time.time())
                                avg_change = bets_olimp[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('avg_change', [])

                                try:
                                    if value != kof_order[-1]:
                                        kof_order.append(value)
                                        avg_change.append(0)
                                        time_change = time.time()
                                    elif value == kof_order[-1]:
                                        avg_change[-1] = round(time.time() - time_change)
                                except IndexError:
                                    # firs
                                    kof_order.append(value)
                                    avg_change.append(0)
                                try:
                                    bets_olimp[key_id]['kofs'].update(
                                        {
                                            coef:
                                                {
                                                    'time_req': round(time.time()),
                                                    'value': value,
                                                    'apid': d.get('apid', ''),
                                                    'factor': d.get('v', 0),
                                                    'sport_id': skId,
                                                    'event': match_id,
                                                    'vector': get_vector(coef, sc1, sc2),
                                                    'hist': {
                                                        'time_change': time_change,
                                                        'avg_change': avg_change,
                                                        'order': kof_order
                                                    }
                                                }
                                        }
                                    )
                                except:
                                    pass
            # if key_id == '52495128':
            #     prnts(key_id)
            #     prnts(bets_olimp)
            #     prnts(resp)
        else:
            if bets_olimp.get(key_id):
                if run.DEBUG:
                    prnts('Олимп матч {}, {} заблокирован:{}'.format(place, key_id, math_block), 'hide')
            else:
                if run.DEBUG:
                    prnts('Олимп матч {}, {} заблокирован и это первое добаление:{}'.format(place, key_id, math_block), 'hide')
            if bets_olimp.get(key_id):
                bets_olimp[key_id].update({
                    'time_req': round(time.time())
                })
            else:
                pass
                # prnts('Олимп, не смог обновить время time_req, т.к. матч ' + str(key_id) + ' заблокирован и это первое добавление?')

            try:
                for j in list(bets_olimp[key_id].get('kofs', {})):
                    try:
                        kof_order = bets_olimp[key_id]['kofs'][j].get('hist', {}).get('order', [])
                        time_change = bets_olimp[key_id]['kofs'][j].get('hist', {}).get('time_change', time.time())
                        avg_change = bets_olimp[key_id]['kofs'][j].get('hist', {}).get('avg_change', [])
                        try:
                            if 0 != kof_order[-1]:
                                kof_order.append(0)
                                # avg_change.append(round(time.time() - time_change))
                                avg_change.append(0)
                                time_change = time.time()
                            elif 0 == kof_order[-1]:
                                avg_change[-1] = round(time.time() - time_change)
                        except IndexError:
                            # firs
                            kof_order.append(0)
                            avg_change.append(0)
                        if bets_olimp.get(key_id, {}).get('kofs', {}).get(j):
                            bets_olimp[key_id]['kofs'][j]['value'] = 0
                            bets_olimp[key_id]['kofs'][j]['factor'] = 0
                            bets_olimp[key_id]['kofs'][j]['time_req'] = round(time.time())
                            if bets_olimp[key_id]['kofs'][j].get('hist') is None:
                                bets_olimp[key_id]['kofs'][j]['hist'] = {}
                            bets_olimp[key_id]['kofs'][j]['hist']['avg_change'] = avg_change
                            bets_olimp[key_id]['kofs'][j]['hist']['time_change'] = time_change
                            bets_olimp[key_id]['kofs'][j]['hist']['kof_order'] = kof_order
                            if kof_order[-1]:
                                # prnts('Олимп x, матч заблокирован, знач. выставил в 0: ' + key_id + ' ' + str(j), 'hide')
                                prnts('Олимп x, матч заблокирован, знач. выставил в 0: ' + key_id + ' ' + str(j) + 'math_block: ' + str(math_block))
                        else:
                            pass
                            # prnts('Олимп x, матч заблокирован и это первое добавлени значение не выставляю в 0: ' + key_id + ' ' + str(j), 'hide')
                            prnts('Олимп x, матч заблокирован и это первое добавлени: ' + key_id + ' ' + str(j) + ' math_block: ' + str(math_block))
                    except Exception as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        err_str = 'error: ' + str(e) + ' (' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))) + ')'
                        prnts('Олимп x, матч:' + key_id + ' ошибка 00 при удалении старой котирофки: ' + str(err_str) + ' math_block: ' + str(math_block))
                        time.sleep(5)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = 'error: ' + str(e) + ' (' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))) + ')'
                prnts('Олимп x, матч:' + key_id + ' ошибка 0 при удалении установке в 0 котирофки: ' + str(err_str) + ' math_block: ' + str(math_block))
                time.sleep(5)
            return time_resp + (time.time() - time_start_proc)

        # for val in bets_olimp.get(key_id, {}).get('kofs', {}).values():
        #     time_change_kof = val.get('hist', {}).get('time_change')
        #     time_change_tot = bets_olimp.get(key_id, {}).get('time_change_total')
        #     avg_change_total = bets_olimp.get(key_id, {}).get('avg_change_total', [])
        #     if round(time_change_tot) < round(time_change_kof):
        #         avg_change_total.append(round(time_change_kof - time_change_tot))
        #         bets_olimp[key_id].update({'time_change_total': round(time_change_kof)})
        #         bets_olimp[key_id].update({'avg_change_total': avg_change_total})

        try:
            for i in list(bets_olimp):
                for j in list(bets_olimp[i].get('kofs', {})):
                    hide_time = 4
                    if bets_olimp[i].get('place') == 'pre':
                        hide_time = run.TIMEOUT_PRE_MATCH + hide_time
                    if round(float(time.time() - float(bets_olimp[i]['kofs'][j].get('time_req', 0)))) > hide_time and bets_olimp[i]['kofs'][j].get('value', 0) > 0:
                        try:
                            bets_olimp[i]['kofs'][j]['value'] = 0
                            bets_olimp[i]['kofs'][j]['factor'] = 0
                            if run.DEBUG:
                                prnts('2: ' + i + ' ' + j + ' - выставил в 0')
                                prnts('Олимп, матч:' + key_id + ' данные по котировке из БК не получены более ' + str(hide_time) + ' сек., знач. выставил в 0: ' + str(j) + ' ' + str(i))
                        except Exception as e:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            err_str = 'error: ' + str(e) + ' (' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))) + ')'
                            prnts('Олимп, матч:' + key_id + ' ошибка 1 при удалении старой котирофки: ' + str(err_str))
                            time.sleep(5)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_str = 'error: ' + str(e) + ' (' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))) + ')'
            prnts('Олимп, матч:' + key_id + ' ошибка 2 при удалении старой котирофки: ' + str(err_str))
            time.sleep(5)
        return time_resp + (time.time() - time_start_proc)
    except OlimpMatchСompleted as e:
        if bets_olimp.get(key_id):
            bets_olimp.pop(key_id)
        raise OlimpMatchСompleted('4 ' + str(e))
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        prnts(str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))) + '\ndata:' + str(resp_temp))
        if bets_olimp.get(key_id):
            bets_olimp.pop(key_id)
        raise ValueError(e)


if __name__ == "__main__":
    pass
