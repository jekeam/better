# coding:utf-8
from util_olimp import *
from util_fonbet import *
from proxy_worker import get_proxy_from_file, start_proxy_saver, createBatchGenerator, get_next_proxy
import time
from json import loads, dumps
import threading
from difflib import SequenceMatcher
import re
from exceptions import *
from server import run_server
from utils import prnts
import os
from sys import exit
from datetime import datetime

opposition = {
    '1ТБ': '1ТМ',
    '1ТМ': '1ТБ',
    '2ТБ': '2ТМ',
    '2ТМ': '2ТБ',
    'ТБ': 'ТМ',
    'ТМ': 'ТБ',
    '1ТБ1': '1ТМ1',
    '1ТМ1': '1ТБ1',
    '1ТБ2': '1ТМ2',
    '1ТМ2': '1ТБ2',
    '2ТБ1': '2ТМ1',
    '2ТМ1': '2ТБ1',
    '2ТБ2': '2ТМ2',
    '2ТМ2': '2ТБ2',
    'ТБ1': 'ТМ1',
    'ТМ1': 'ТБ1',
    'ТБ2': 'ТМ2',
    'ТМ2': 'ТБ2',
    # '1УГЛТБ': '1УГЛТМ',
    # '1УГЛТМ': '1УГЛТБ',
    # '2УГЛТБ': '2УГЛТМ',
    # '2УГЛТМ': '2УГЛТБ',
    # 'УГЛТБ': 'УГЛТМ',
    # 'УГЛТМ': 'УГЛТБ',
    'П1': 'П2Н',
    'П2': 'П1Н',
    'П1Н': 'П2',
    'П2Н': 'П1',
    'Н': '12',
    '12': 'Н',
    '1КЗ1': '1КНЗ1',
    '1КНЗ1': '1КЗ1',
    '1КЗ2': '1КНЗ2',
    '1КНЗ2': '1КЗ2',
    '2КЗ1': '2КНЗ1',
    '2КНЗ1': '2КЗ1',
    '2КЗ2': '2КНЗ2',
    '2КНЗ2': '2КЗ2',
    'КЗ1': 'КНЗ1',
    'КНЗ1': 'КЗ1',
    'КЗ2': 'КНЗ2',
    'КНЗ2': 'КЗ2',
    'ОЗД': 'ОЗН',
    'ОЗН': 'ОЗД',
    'ННД': 'ННН',
    'ННН': 'ННД'
}


def get_olimp(resp, arr_matchs):
    # Очистим дстарые данные
    arr_matchs_copy = arr_matchs.copy()
    for key in arr_matchs_copy.keys():
        arr_matchs.pop(key)
    if resp:
        for liga_info in resp:
            for math_info in liga_info.get('it'):
                match_id_str = str(math_info.get('id'))
                # math_block = True if math_info.get('ms') == 1 else False
                arr_matchs[match_id_str] = {
                    'team1': math_info.get('c1', ''),
                    'team2': math_info.get('c2', ''),
                }


def get_fonbet(resp, arr_matchs):
    arr_matchs_copy = arr_matchs.copy()
    for key in arr_matchs_copy.keys():
        arr_matchs.pop(key)
    # получим все события по футболу
    events = [[sport['name'], sport['id']] for sport in resp['sports'] if
              'Football' in sport['name'] and sport['id'] != 1]
    idEvents = [e[1] for e in events]

    # получим список ид всех матчей по событиям
    if idEvents:
        idMatches = [event['id'] for event in resp['events'] if event.get('sportId') in idEvents]

    # полчим все инфу по ид матча
    if idEvents and idMatches:
        for mid in idMatches:
            for event in resp['events']:
                if event['id'] == mid and event['kind'] == 1:
                    arr_matchs[str(event['id'])] = {
                        'team1': event.get('team1', ''),
                        'team2': event.get('team2', ''),
                    }
        # for mid in idMatches:
        # for event in resp['events']:
        # if event['id'] == mid and event['kind'] > 1 and event['name'] in ['1st half', '2nd half', 'corners']:


def start_seeker_matchs_olimp(proxies, gen_proxi_olimp, arr_matchs):
    proxy = gen_proxi_olimp.next()
    time_out = 5.51
    while True:
        try:
            resp, time_resp = get_matches_olimp(proxies, proxy)
            get_olimp(resp, arr_matchs)
        except TimeOut as e:
            proxy = gen_proxi_olimp.next()
            err_str = 'Timeout: Олимп, ошибка призапросе списока матчей'
            prnts(err_str)
            time_resp = time_out
        except Exception as e:
            proxy = gen_proxi_olimp.next()
            prnts('Exception: Олимп, ошибка при запросе списка матчей: ' + str(e) + ' ' + proxy)
            time_resp = time_out

        time_sleep = max(0, (time_out - time_resp))

        prnts('Олимп, поиск матчей, время ответа: ' + str(time_resp) + ', запрос через ' + str(
            time_sleep) + ' ' + proxy, 'hide')
        time.sleep(time_sleep)


def start_seeker_matchs_fonbet(proxies, gen_proxi_fonbet, arr_matchs):
    time_out = 5.51
    proxy = gen_proxi_fonbet.next()
    while True:
        try:
            resp, time_resp = get_matches_fonbet(proxies, proxy)
            get_fonbet(resp, arr_matchs)
        except Exception as e:
            prnts('Фонбет, ошибка при запросе списка матчей: ' + str(e) + ' ' + proxy)
            proxy = gen_proxi_fonbet.next()
            time_resp = time_out

        time_sleep = max(0, (time_out - time_resp))

        prnts('Фонбет, поиск матчей, время ответа: ' + str(time_resp) + ', запрос через '
              + str(time_sleep) + ' ' + proxy, 'hide')
        time.sleep(time_sleep)


def start_seeker_bets_olimp(bets_olimp, match_id_olimp, proxies_olimp, gen_proxi_olimp, pair_mathes):
    time_out = 3.51
    proxy = gen_proxi_olimp.next()

    while True:
        try:
            time_resp = get_bets_olimp(bets_olimp, match_id_olimp, proxies_olimp, proxy)
        except TimeOut as e:
            proxy = gen_proxi_olimp.next()
            err_str = 'Timeout: Олимп, ошибка при запросе матча ' + str(match_id_olimp)
            prnts(err_str)
            time_resp = time_out
        except OlimpMatchСompleted as e:
            cnt = 0
            for pair_match in pair_mathes:
                if pair_match[0] == str(match_id_olimp):
                    pair_mathes.remove(pair_mathes[cnt])
                cnt += 1
            print(e)
            prnts(e)
            raise ValueError(e)
        except Exception as e:
            prnts('Exception: Олимп, ошибка при запросе матча ' + str(match_id_olimp) + ': ' + str(e) + ' ' + proxy)
            proxy = gen_proxi_olimp.next()
            time_resp = time_out

        time_sleep = max(0, (time_out - time_resp))

        prnts('Олимп, матч ' + str(match_id_olimp) + '. Время ответа: ' + str(time_resp) + ', запрос через '
              + str(time_sleep) + ' ' + proxy, 'hide')
        time.sleep(time_sleep)


def start_seeker_bets_fonbet(bets_fonbet, match_id_fonbet, proxies_fonbet, gen_proxi_fonbet, pair_mathes):
    time_out = 3.51
    proxy = gen_proxi_fonbet.next()

    while True:
        try:
            time_resp = get_bets_fonbet(bets_fonbet, match_id_fonbet, proxies_fonbet, proxy)
        except FonbetMatchСompleted as e:
            cnt = 0
            for pair_match in pair_mathes:
                if pair_match[1] == str(match_id_fonbet):
                    pair_mathes.remove(pair_mathes[cnt])
                cnt += 1
            prnts(e)
            raise ValueError(e)
        # except Exception as e:
        #     prnts('Фонбет, ошибка при запросе матча ' + str(match_id_fonbet) + ': ' + str(e) + ' ' + proxy)
        #     proxy = gen_proxi_fonbet.next()
        #     time_resp = time_out

        time_sleep = max(0, (time_out - time_resp))

        prnts(str('Фонбет, матч ' + str(match_id_fonbet) + '. Время ответа: ' + str(
            time_resp) + ', повторный запрос через ' + str(time_sleep)) + ' ' + proxy, 'hide')
        time.sleep(time_sleep)


def starter_bets(
        bets_olimp,
        bets_fonbet,
        pair_mathes,
        mathes_id_is_work,
        proxies_olimp,
        gen_proxi_olimp,
        proxies_fonbet,
        gen_proxi_fonbet,
):
    while True:
        for pair_match in pair_mathes:
            match_id_olimp, match_id_fonbet = pair_match

            if match_id_olimp not in mathes_id_is_work:
                mathes_id_is_work.append(match_id_olimp)
                start_seeker_olimp_bets_by_id = threading.Thread(
                    target=start_seeker_bets_olimp,
                    args=(bets_olimp, match_id_olimp, proxies_olimp, gen_proxi_olimp, pair_mathes)
                )
                start_seeker_olimp_bets_by_id.start()

            if match_id_fonbet not in mathes_id_is_work:
                mathes_id_is_work.append(match_id_fonbet)

                start_seeker_fonbet_bets_by_id = threading.Thread(
                    target=start_seeker_bets_fonbet,
                    args=(bets_fonbet, match_id_fonbet, proxies_fonbet, gen_proxi_fonbet, pair_mathes)
                )
                start_seeker_fonbet_bets_by_id.start()
        time.sleep(5)


def compare_teams(team1_bk1, team2_bk1, team1_bk2, team2_bk2):
    team1_bk1 = re.sub('[^A-z 0-9]', '', team1_bk1.lower()).replace(' ', '')
    team2_bk1 = re.sub('[^A-z 0-9]', '', team2_bk1.lower()).replace(' ', '')
    team1_bk2 = re.sub('[^A-z 0-9]', '', team1_bk2.lower()).replace(' ', '')
    team2_bk2 = re.sub('[^A-z 0-9]', '', team2_bk2.lower()).replace(' ', '')
    if 1.7 < \
            SequenceMatcher(None, team1_bk1, team1_bk2).ratio() + \
            SequenceMatcher(None, team2_bk1, team2_bk2).ratio():
        return True
    else:
        return False


def start_compare_matches(pair_mathes, json_bk1, json_bk2):
    while True:
        try:
            # Проверим какие матчи завершились
            cnt = 0
            for bk1_match_id, bk2_match_id in pair_mathes:
                if bk1_match_id not in json_bk1.keys() or \
                        bk2_match_id not in json_bk2.keys():
                    prnts('Матч исключен: [' + str(bk1_match_id) + ', ' + str(bk2_match_id) + ']')
                    pair_mathes.remove(pair_mathes[cnt])
                cnt = cnt + 1

            prnts('Найдено матчей: ' + str(len(pair_mathes)) + ' ' + str(pair_mathes))
            for bk1_match_id, bk1_match_info in json_bk1.items():
                if bk1_match_info:
                    # Проверим что ид матча 1 нет в списке
                    if 'yes' not in list(map(lambda id: 'yes' if bk1_match_id in id else 'no', pair_mathes)):
                        for bk2_match_id, bk2_match_info in json_bk2.items():
                            if bk2_match_info:
                                # Проверим что ид матча 2 нет в списке
                                if 'yes' not in list(
                                        map(lambda id: 'yes' if bk2_match_id in id else 'no', pair_mathes)):
                                    if compare_teams(
                                            bk1_match_info.get('team1'),
                                            bk1_match_info.get('team2'),
                                            bk2_match_info.get('team1'),
                                            bk2_match_info.get('team2')
                                    ):
                                        prnts(
                                            'Матч добавлен: ' + str(bk1_match_id) + ' ' +
                                            bk1_match_info.get('team1') + ' vs ' +
                                            bk1_match_info.get('team2') + ' | ' +
                                            str(bk2_match_id) + ' ' +
                                            bk2_match_info.get('team1') + ' vs ' +
                                            bk2_match_info.get('team2')
                                        )
                                        pair_mathes.append([bk1_match_id, bk2_match_id])

            time.sleep(15)
        except Exception as e:
            prnts('Error start_compare_matches: ' + str(e))


def get_forks(all_bets, pair_mathes, bets_olimp, bets_fonbet):
    while True:
        # if False:
        #     f = open('bets.log', 'a+')
        #     f.write('------------------------')
        #     f.write('\n')
        #     f.write('bets_fonbet: ' + str(json.dumps(bets_fonbet, ensure_ascii=False)))
        #     f.write('\n')
        #     f.write('bets_olimp: ' + str(json.dumps(bets_olimp, ensure_ascii=False)))
        #     f.write('\n')
        #     prnts(all_bets)
        for key, val in all_bets.copy().items():
            if round(float(time.time() - float(val.get('time_req_olimp', 0)))) > 8 or \
                    round(float(time.time() - float(val.get('time_req_fonbet', 0)))) > 8:
                import json
                prnts('all_bets: ' + str(json.dumps(all_bets, ensure_ascii=False)))
                try:
                    all_bets.pop(key)
                    prnts(
                        'Данные по вилке из БК не получены более 8 сек., вилка удалена: ' + str(key) + ' '
                        + str(val)  # ,
                        # 'hide'
                    )
                except Exception as e:
                    prnts(e)
                    pass

        for pair_math in pair_mathes:

            math_json_olimp = bets_olimp.get(pair_math[0], {})
            math_json_fonbet = bets_fonbet.get(pair_math[1], {})
            # prnts('------------------------')
            # prnts('math_json_olimp:'+str(json.dumps(math_json_olimp, ensure_ascii=False)))
            # prnts('')
            # prnts('math_json_fonbet:'+str(json.dumps(math_json_fonbet, ensure_ascii=False)))
            curr_opposition = opposition.copy()

            for kof_type in math_json_olimp.get('kofs', {}):
                if '(' in kof_type:
                    tot_abrr = re.sub('\((.*)\)', '', kof_type)
                    tot_val = re.findall('\((.*)\)', kof_type)[0]
                    curr_opposition.update({
                        tot_abrr + '({})'.format(tot_val):
                            opposition[tot_abrr] + '({})'.format(tot_val)
                    })

            for kof_type_olimp, kof_type_fonbet in curr_opposition.items():

                bet_key = str(pair_math[0]) + '@' + str(pair_math[1]) + '@' + \
                          kof_type_olimp + '@' + kof_type_fonbet

                k_olimp = math_json_olimp.get('kofs', {}).get(kof_type_olimp, {})
                k_fonbet = math_json_fonbet.get('kofs', {}).get(kof_type_fonbet, {})

                v_olimp = k_olimp.get('value', 0.0)
                v_fonbet = k_fonbet.get('value', 0.0)

                if v_olimp > 0.0 and v_fonbet > 0.0:
                    L = (1 / float(v_olimp)) + (1 / float(v_fonbet))
                    is_fork = True if L < 1 else False

                    if is_fork:  # or True
                        # if pair_math == ['46027276', '12832237'] or True:
                        time_break_fonbet = False
                        if '(' + math_json_fonbet.get('score', '') + ')' == \
                                math_json_fonbet.get('score_1st', '') and \
                                str(math_json_fonbet.get('time', '')) == '45:00' and \
                                str(round(math_json_fonbet.get('minute', ''), 2)) == '45.0':
                            time_break_fonbet = True

                        # if str(pair_math[1]) == '12801247':
                        #     print('')
                        #     print(str(time.time()) + str(k_fonbet))
                        #     print('')

                        if all_bets.get(bet_key, '') != '':
                            all_bets[bet_key].update({
                                'time_last_upd': time.time(),
                                'name': math_json_olimp.get('name', ''),
                                'time_req_olimp': math_json_olimp.get('time_req', 0),
                                'time_req_fonbet': math_json_fonbet.get('time_req', 0),
                                'l': L,
                                'pair_math': pair_math,
                                'bk1_score': math_json_olimp.get('score', ''),
                                'bk2_score': math_json_fonbet.get('score', ''),
                                'time': math_json_fonbet.get('time', ''),
                                'minute': math_json_fonbet.get('minute', ''),
                                'kof_olimp': k_olimp,
                                'kof_fonbet': k_fonbet,
                                'time_break_fonbet': time_break_fonbet
                            })
                        else:
                            all_bets[bet_key] = {
                                'time_last_upd': time.time(),
                                'name': math_json_olimp.get('name', ''),
                                'time_req_olimp': math_json_olimp.get('time_req', 0),
                                'time_req_fonbet': math_json_fonbet.get('time_req', 0),
                                'l': L,
                                'pair_math': pair_math,
                                'bk1_score': math_json_olimp.get('score', ''),
                                'bk2_score': math_json_fonbet.get('score', ''),
                                'time': math_json_fonbet.get('time', ''),
                                'minute': math_json_fonbet.get('minute', ''),
                                'kof_olimp': k_olimp,
                                'kof_fonbet': k_fonbet,
                                'time_break_fonbet': time_break_fonbet
                            }
                    else:
                        try:
                            all_bets.pop(bet_key)
                        except:
                            pass
                else:
                    try:
                        all_bets.pop(bet_key)
                    except:
                        pass
        time.sleep(0.95)


if __name__ == '__main__':
    proxy_filename_olimp = 'proxy_by_olimp.txt'
    proxy_filename_fonbet = 'proxy_by_fonbet.txt'

    proxies_olimp = get_proxy_from_file(proxy_filename_olimp)
    proxies_fonbet = get_proxy_from_file(proxy_filename_fonbet)

    gen_proxi_olimp = createBatchGenerator(get_next_proxy(proxies_olimp.copy()))
    gen_proxi_fonbet = createBatchGenerator(get_next_proxy(proxies_fonbet.copy()))

    proxy_saver = threading.Thread(
        target=start_proxy_saver,
        args=(proxies_olimp, proxies_fonbet, proxy_filename_olimp, proxy_filename_fonbet,)
    )
    proxy_saver.start()

    # json by mathes
    arr_olimp_matchs = dict()
    arr_fonbet_matchs = dict()

    # json by bets math
    bets_fonbet = dict()
    bets_olimp = dict()

    all_bets = dict()

    olimp_seeker_matchs = threading.Thread(
        target=start_seeker_matchs_olimp,
        args=(proxies_olimp, gen_proxi_olimp, arr_olimp_matchs,)
    )
    olimp_seeker_matchs.start()

    fonbet_seeker_matchs = threading.Thread(
        target=start_seeker_matchs_fonbet,
        args=(proxies_fonbet, gen_proxi_fonbet, arr_fonbet_matchs)
    )
    fonbet_seeker_matchs.start()

    pair_mathes = []
    compare_matches = threading.Thread(
        target=start_compare_matches,
        args=(pair_mathes, arr_olimp_matchs, arr_fonbet_matchs)
    )
    compare_matches.start()

    mathes_id_is_work = []
    starter_bets = threading.Thread(
        target=starter_bets,
        args=(
            bets_olimp,
            bets_fonbet,
            pair_mathes,
            mathes_id_is_work,
            proxies_olimp,
            gen_proxi_olimp,
            proxies_fonbet,
            gen_proxi_fonbet,
        )
    )
    starter_bets.start()

    starter_forks = threading.Thread(target=get_forks, args=(all_bets, pair_mathes, bets_olimp, bets_fonbet))
    starter_forks.start()

    server = threading.Thread(target=run_server, args=(all_bets,))
    server.start()

    proxy_saver.join()
    olimp_seeker_matchs.join()
    fonbet_seeker_matchs.join()
    compare_matches.join()
    starter_forks.join()
    server.join()
