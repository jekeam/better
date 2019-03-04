# coding: utf-8
from hashlib import md5
import requests
# if __name__=='__main__':
from proxy_worker import del_proxy
import re
import time
from exceptions import OlimpMatchСompleted, TimeOut
from utils import prnts, get_vector, MINUTE_COMPLITE

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


olimp_url = 'http://10.olimp-proxy.ru:10600'
olimp_url_https = 'https://10.olimp-proxy.ru'
olimp_url_random = 'https://{}.olimp-proxy.ru'  # c 10 по 18й

olimp_secret_key = 'b2c59ba4-7702-4b12-bef5-0908391851d9'

olimp_head = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'okhttp/3.9.1'
}

olimp_data = {
    "live": 1,
    # "sport_id": 1,
    "sport_id": 1,
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
    "Т2мен": "ТМ2({})"
}


def olimp_get_xtoken(payload, olimp_secret_key):
    sorted_values = [str(payload[key]) for key in sorted(payload.keys())]
    to_encode = ";".join(sorted_values + [olimp_secret_key])
    return {"X-TOKEN": md5(to_encode.encode()).hexdigest()}


def get_matches_olimp(proxies, proxy, time_out):
    global olimp_data
    global olimp_head

    try:
        http_type = 'http' if 'https' in proxy else 'http'
        url = olimp_url_https if 'https' in proxy else olimp_url
        proxies = {http_type: proxy}
        # prnts('Olimp set proxy: ' + proxy, 'hide')
    except Exception as e:
        err_str = 'Olimp error set proxy: ' + str(e)
        prnts(err_str)
        raise ValueError(err_str)

    olimp_data_ll = olimp_data.copy()
    olimp_data_ll.update({'lang_id': 2})

    olimp_head_ll = olimp_head
    olimp_head_ll.update(olimp_get_xtoken(olimp_data_ll, olimp_secret_key))
    olimp_head_ll.pop('Accept-Language', None)
    try:
        resp = requests.post(
            url + '/api/slice/',
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

        if res.get("error").get('err_code') == 0:
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
    value = re.findall('\((.*)\)', sbet)[0]
    key = re.sub('\((.*)\)', '', sbet)
    abr = ''
    # error to_add("ХунтеларК.(Аякс)(0.5)бол"), value=Аякс)(0.5, key=ХунтеларК.бол
    try:
        abr = abbreviations[key].format(value)
    except:
        # pass
        prnts('error to_add("' + sbet + '"), value=' + value + ', key=' + key)
    return abr


def get_match_olimp(match_id, proxi_list, proxy, time_out, pair_mathes):
    global olimp_url
    global olimp_url_https
    global olimp_data

    match_exists = False
    for pair_match in pair_mathes:
        if match_id in pair_match:
            match_exists = True
    if match_exists is False:
        err_str = 'Олимп: матч ' + str(match_id) + ' не найден в спике активных, поток get_match_olimp завершен.'
        raise OlimpMatchСompleted(err_str)

    olimp_data_m = olimp_data.copy()

    olimp_data_m.update({'id': match_id})
    olimp_data_m.update({'lang_id': 0})

    olimp_stake_head = olimp_head.copy()

    token = get_xtoken(olimp_data_m, olimp_secret_key)

    olimp_stake_head.update(token)
    olimp_stake_head.pop('Accept-Language', None)

    try:
        http_type = 'http' if 'https' in proxy else 'http'
        url = olimp_url_https if 'https' in proxy else olimp_url
        proxies = {http_type: proxy}
        # prnts('Olimp: set proxy by ' + str(match_id) + ': ' + str(proxy), 'hide')
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
        except Exception as e:
            err_str = 'Olimp error by ' + str(match_id) + ': ' + str(e)
            prnts(err_str)
            raise ValueError(err_str)
        # {"error": {"err_code": 404, "err_desc": "Прием ставок приостановлен"}, "data": null}
        if res.get("error").get('err_code', 999) in (0, 404):
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


def get_bets_olimp(bets_olimp, match_id, proxies_olimp, proxy, time_out, pair_mathes):
    global MINUTE_COMPLITE
    key_id = str(match_id)

    match_exists = False
    for pair_match in pair_mathes:
        if match_id in pair_match:
            match_exists = True
    if match_exists is False:
        err_str = 'Олимп: матч ' + str(match_id) + ' не найден в спике активных, поток get_bets_olimp завершен.'
        raise OlimpMatchСompleted(err_str)

    try:
        resp, time_resp = get_match_olimp(match_id, proxies_olimp, proxy, time_out, pair_mathes)
        # Очистим дстарые данные
        # if bets_olimp.get(key_id):
        # bets_olimp[key_id] = dict()

        time_start_proc = time.time()

        # print(resp)
        # if key_id == '46953789':
        #     import json
        #     prnts(json.dumps(resp, ensure_ascii=False))
        # f = open('olimp.txt', 'a+')
        # f.write(json.dumps(resp, ensure_ascii=False))

        # prnts(json.dumps(resp, ensure_ascii=False, indent=4))
        # prnts(json.dumps(resp, ensure_ascii=False))
        # exit()
        math_block = \
            True \
                if not resp \
                   or str(resp.get('ms', '1')) != '2' \
                   or resp.get('error', {'err_code': 0}).get('err_code') == 404 \
                else False \
            # 1 - block, 2 - available
        if not math_block:

            timer = resp.get('t', '')

            minute = -1
            try:
                minute = int(re.findall('\d{1,2}\\"', resp.get('sc', ''))[0].replace('"', ''))
            except:
                pass

            if minute >= MINUTE_COMPLITE:
                err_str = 'Олимп: матч ' + str(match_id) + ' завершен, т.к. больше 88 минуты прошло.'
                raise OlimpMatchСompleted(err_str)

            skId = resp.get('sport_id')
            skName = resp.get('sn')
            sport_name = resp.get('cn')
            name = resp.get('n')
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
                prnts('err util_olimp error split: ' + str(resp.get('sc', '0:0')))

            try:
                bets_olimp[key_id].update({
                    'sport_id': skId,
                    'sport_name': skName,
                    'league': sport_name,
                    'name': name,
                    'score': score,
                    'time_start': timer,
                    'time_req': round(time.time())
                })
            except:
                bets_olimp[key_id] = {
                    'sport_id': skId,
                    'sport_name': skName,
                    'league': sport_name,
                    'name': name,
                    'score': score,
                    'time_start': timer,
                    'time_req': round(time.time()),
                    'time_change_total': round(time.time()),
                    'avg_change_total': [],
                    'kofs': {}
                }

            for c in resp.get('it', []):
                if c.get('n', '') in ['Основные', 'Голы', 'Инд.тотал', 'Доп.тотал', 'Исходы по таймам']:  # 'Угловые'
                    for d in c.get('i', []):
                        if 'Обе забьют: ' \
                                in d.get('n', '') \
                                or 'забьет: ' \
                                in d.get('n', '') \
                                or 'Никто не забьет: ' \
                                in d.get('n', '') \
                                or 'Победа ' \
                                in d.get('n', '') \
                                or d.get('n', '').endswith(' бол') \
                                or d.get('n', '').endswith(' мен') \
                                or 'Первая не проиграет' \
                                in d.get('n', '') \
                                or 'Вторая не проиграет' \
                                in d.get('n', '') \
                                or 'Ничьей не будет' \
                                in d.get('n', '') \
                                or 'Ничья' \
                                in d.get('n', ''):
                            key_r = d.get('n', '').replace(resp.get('c1', ''), 'Т1') \
                                .replace(resp.get('c2', ''), 'Т2')
                            coef = str([
                                           abbreviations[c.replace(' ', '')]
                                           if c.replace(' ', '') in abbreviations.keys()
                                           else c.replace(' ', '')
                                           if '(' not in c.replace(' ', '')
                                           else to_abb(c.replace(' ', ''))
                                           for c in [key_r]
                                       ][0])
                            hist5 = bets_olimp[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('4', 0)
                            hist4 = bets_olimp[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('3', 0)
                            hist3 = bets_olimp[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('2', 0)
                            hist2 = bets_olimp[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('1', 0)
                            hist1 = bets_olimp[key_id].get('kofs', {}).get(coef, {}).get('value', 0)

                            cof_is_change = True if hist1 != d.get('v', '') else False

                            if cof_is_change:
                                avg_change = \
                                    bets_olimp[key_id]. \
                                        get('kofs', {}). \
                                        get(coef, {}). \
                                        get('hist', {}). \
                                        get('avg_change', [])
                                avg_change.append(round(time.time() -
                                                        bets_olimp[key_id].
                                                        get('kofs', {}).
                                                        get(coef, {}).
                                                        get('hist', {}).
                                                        get('time_change', time.time())))
                                time_change = round(time.time())
                            else:
                                avg_change = \
                                    bets_olimp[key_id]. \
                                        get('kofs', {}). \
                                        get(coef, {}). \
                                        get('hist', {}). \
                                        get('avg_change', [])
                                time_change = \
                                    bets_olimp[key_id]. \
                                        get('kofs', {}). \
                                        get(coef, {}). \
                                        get('hist', {}). \
                                        get('time_change', round(time.time()))

                            try:
                                bets_olimp[key_id]['kofs'].update(
                                    {
                                        coef:
                                            {
                                                'time_req': round(time.time()),
                                                'value': d.get('v', ''),
                                                'apid': d.get('apid', ''),
                                                'factor': d.get('v', ''),  # d.get('p', ''),
                                                'sport_id': skId,
                                                'event': match_id,
                                                'vector': get_vector(coef, sc1, sc2),
                                                'hist': {
                                                    'time_change': time_change,
                                                    'avg_change': avg_change,
                                                    '1': hist1,
                                                    '2': hist2,
                                                    '3': hist3,
                                                    '4': hist4,
                                                    '5': hist5
                                                }
                                            }
                                    }
                                )
                            except:
                                pass
                                # print('---error---')
                                # import json
                                # print(json.dumps(bets_olimp[key_id], ensure_ascii=False))
                                # print('------------')
        else:
            try:
                bets_olimp.pop(key_id)
            except:
                pass

        for val in bets_olimp.get(key_id, {}).get('kofs', {}).values():
            time_change_kof = val.get('hist', {}).get('time_change')
            time_change_tot = bets_olimp.get(key_id, {}).get('time_change_total')
            avg_change_total = bets_olimp.get(key_id, {}).get('avg_change_total', [])
            if round(time_change_tot) < round(time_change_kof):
                avg_change_total.append(round(time_change_kof - time_change_tot))
                bets_olimp[key_id].update({'time_change_total': round(time_change_kof)})
                bets_olimp[key_id].update({'avg_change_total': avg_change_total})

        try:
            for i, j in bets_olimp.get(key_id, {}).get('kofs', {}).copy().items():
                if round(float(time.time() - float(j.get('time_req', 0)))) > 8:
                    try:
                        bets_olimp[key_id]['kofs'][i]['value'] = 0
                        prnts(
                            'Олимп, данные по котировке из БК не получены более 8 сек., знач. выставил в 0: ' +
                            key_id + ' ' + str(i) + ' ' + str(j), 'hide'
                        )
                    except Exception as e:
                        prnts('Олимп, ошибка 1 при удалении старой котирофки: ' + str(e))
        except Exception as e:
            prnts('Олимп, ошибка 2 при удалении старой котирофки: ' + str(e))
        # if key_id == '46204691':
        #     import json
        #     print('------о----------')
        #     # print(json.dumps(resp, ensure_ascii=False))
        #     print('')
        #     print('')
        #     print(key_id, json.dumps(bets_olimp.get(key_id), ensure_ascii=False))
        #     print('')
        #     print('')
        #     print('--------о--------')
        #     time.sleep(10)
        return time_resp + (time.time() - time_start_proc)
    except OlimpMatchСompleted as e:
        raise OlimpMatchСompleted('4 ' + str(e))
    except Exception as e:
        prnts(e)
        if bets_olimp.get(key_id):
            bets_olimp.pop(key_id)
        raise ValueError(e)


if __name__ == "__main__":
    pass
