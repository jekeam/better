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
from utils import prnts, DEBUG, find_max_mode, opposition, serv_log, get_param, sport_list, if_exists, print_j
from proxy_switcher import ProxySwitcher
import json
import os.path
import os
from statistics import median
from datetime import datetime
import copy

import sys
import traceback

TIMEOUT_MATCHS = 10
TIMEOUT_MATCH = 10
TIMEOUT_MATCH_MINUS = 9

if not DEBUG:
    SERVER_IP = get_param('server_ip')
else:
    SERVER_IP = get_param('server_ip_test')

SERVER_PORT = get_param('server_port')

prnts('TIMEOUT_MATCHS: ' + str(TIMEOUT_MATCHS))
prnts('TIMEOUT_MATCH: ' + str(TIMEOUT_MATCH))
prnts('TIMEOUT_MATCH_MINUS: ' + str(TIMEOUT_MATCH_MINUS))
prnts('SERVER_IP: ' + str(SERVER_IP))
prnts('SERVER_PORT: ' + str(SERVER_PORT))
prnts('SPORT_LIST: ' + print_j(sport_list, 'return var'))


def get_olimp(resp, arr_matchs):
    # Очистим дстарые данные
    arr_matchs_copy = copy.deepcopy(arr_matchs)
    for key in arr_matchs_copy.keys():
        if arr_matchs.get('olimp', '') != '':
            arr_matchs.pop(key)
    if resp:
        for liga_info in resp:

            # print(str(liga_info.get('sport_id')) + ' ' + liga_info.get('sn'))
            # 1 Soccer
            # 3 Tennis
            # 5 Basketball
            # 2 Ice Hockey
            # 10 Volleyball
            # 112 eSports
            # 40 Table Tennis
            # 9 Handball
            # 41 Water Polo
            # 11 Futsal
            # 8 Bandy
            # 51 Badminton
            # 60 Beach Volleyball
            # 126 Pool
            if if_exists(sport_list, 'olimp', liga_info.get('sport_id')):
                for math_info in liga_info.get('it'):
                    match_id_str = str(math_info.get('id'))
                    # math_block = True if math_info.get('ms') == 1 else False
                    # print_j(liga_info)
                    arr_matchs[match_id_str] = {
                        'bk_name': 'olimp',
                        'sport_id': liga_info.get('sport_id'),
                        'sport_name': if_exists(sport_list, 'olimp', liga_info.get('sport_id'), 'name'),
                        'name': liga_info['cn'],
                        'team1': math_info.get('c1', ''),
                        'team2': math_info.get('c2', ''),
                        'start_timestamp': math_info.get('t', 0)
                    }
    # print_j(arr_matchs) # 50940691


def get_fonbet(resp, arr_matchs):
    # with open('resp.json', 'w') as f:
    #     f.write(json.dumps(resp, ensure_ascii=False))

    # for val in resp.get('sports'):
    #     if val.get('kind') == 'sport':
    #         print(str(val.get('id')) + ' ' + val.get('name'))
    #         # 1 Football
    #         # 2 Hockey
    #         # 3 Basketball
    #         # 4 Tennis
    #         # 9 Volleyball
    #         # 1434 Futsal
    #         # 41963 Lottery
    #         # 11624 Beach volley
    #         # 29086 Esports
    #         # 3088 Table tennis
    #         # 1439 Field hockey
    #         # 19936 Sports simulators
    #         # 11630 Badminton
    #         # 44943 Rocket League
    #         # 40479 Cyberfootball
    #         # 45827 Cybertennis
    #         # 11627 Floorball
    #         # 40481 Cyberbasket

    arr_matchs_copy = copy.deepcopy(arr_matchs)
    for key in arr_matchs_copy.keys():
        if arr_matchs.get('fonbet', '') != '':
            arr_matchs.pop(key)

    # получим все события по футболу
    events = [
        {
            'event_bk': 'fonbet',
            'event_name': sport['name'],
            'event_id': sport['id'],
            'event_sportId': sport['parentId']
        } for sport in resp['sports'] if sport['kind'] == 'segment' and if_exists(sport_list, 'fonbet', sport.get('parentId'))
    ]

    # получим список ид всех матчей по событиям
    idMatches = list()
    idEvents = [{'event_id': e.get('event_id'), 'event_sportId': e.get('event_sportId')} for e in events]

    for idEvent in idEvents:
        # print(idEvent['event_id'])
        # print([{'id': event['id'], 'sportId': idEvent['event_sportId']} for event in resp['events'] if event.get('parentId', -1) == -1])
        for x in [{'id': event['id'], 'sportId': idEvent['event_sportId'], 'isHot': event.get('state', {}).get('inHotList', False)} for event in resp['events'] if
                  event['sportId'] == idEvent['event_id'] and event.get('parentId', -1) == -1]:
            idMatches.append(x)
        # полчим все инфу по ид матча
    # print_j(resp['events'])
    if idEvents and idMatches:
        for mid in idMatches:
            for event in resp['events']:
                # Только главные события
                if event['id'] == mid.get('id'):  # and event.get('parentId', -1) == -1 # Пока вырезал все дочерние события выше see row: 123
                    # print(sport_list)
                    # print(if_exists(sport_list, 'fonbet', mid.get('sportId'), 'name'))
                    arr_matchs[str(event['id'])] = {
                        'bk_name': 'fonbet',
                        'sport_id': mid.get('sportId'),
                        'sport_name': if_exists(sport_list, 'fonbet', mid.get('sportId'), 'name'),
                        'name': event['name'],
                        'team1': event.get('team1', ''),
                        'team2': event.get('team2', ''),
                        'start_timestamp': event.get('startTime', 0),
                        'isHot': mid.get('isHot')
                    }
                    # if mid.get('isHot'):
                    #     print('hot: ' + str(event['priority']) + ' ' + str(arr_matchs[str(event['id'])]))
                    # else:
                    #     print('no: ' + str(event['priority']) + ' ' + str(arr_matchs[str(event['id'])]))

        # for mid in idMatches:
        # for event in resp['events']:
        # if event['id'] == mid and event['kind'] > 1 and event['name'] in ['1st half', '2nd half', 'corners']:
    # print_j(arr_matchs)
    # ['16453828': {'bk_name': 'fonbet', 'sport_id': 1, 'sport_name': 'Football', 'name': '', 'team1': 'Nadi', 'team2': 'Suva'}, ....]


def start_seeker_matchs_olimp(gen_proxi_olimp, arr_matchs):
    global TIMEOUT_MATCHS
    proxy = gen_proxi_olimp.next()
    fail_proxy = 0
    while True:
        try:
            resp, time_resp = get_matches_olimp(proxy, TIMEOUT_MATCHS)
            get_olimp(resp, arr_matchs)
        except TimeOut as e:
            err_str = 'Timeout: Олимп, ошибка призапросе списока матчей'
            prnts(err_str)
            time_resp = TIMEOUT_MATCHS

            if fail_proxy >= 3:
                proxy = gen_proxi_olimp.next()
            else:
                fail_proxy = fail_proxy + 1
                time.sleep(3)

        except Exception as e:
            prnts('Exception: Олимп, ошибка при запросе списка матчей: ' + proxy + str(e))
            time_resp = TIMEOUT_MATCHS

            if fail_proxy >= 3:
                proxy = gen_proxi_olimp.next()
                fail_proxy = 0
            else:
                fail_proxy = fail_proxy + 1
                time.sleep(3)

        time_sleep = max(0, (TIMEOUT_MATCHS - time_resp))

        if DEBUG:
            pass
            # prnts('Олимп, поиск матчей, время ответа: ' + str(time_resp) + ', запрос через ' +
            #       str(time_sleep) + ' ' + proxy)

        time.sleep(time_sleep)


def start_seeker_matchs_fonbet(gen_proxi_fonbet, arr_matchs):
    global TIMEOUT_MATCHS
    proxy = gen_proxi_fonbet.next()
    while True:
        try:
            resp, time_resp = get_matches_fonbet(proxy, TIMEOUT_MATCHS)
            get_fonbet(resp, arr_matchs)
        except Exception as e:
            prnts('Фонбет, ошибка при запросе списка матчей: ' + str(e) + ' ' + proxy)
            proxy = gen_proxi_fonbet.next()
            time_resp = TIMEOUT_MATCHS

        time_sleep = max(0, (TIMEOUT_MATCHS - time_resp))

        if DEBUG:
            pass
            # prnts('Фонбет, поиск матчей, время ответа: ' + str(time_resp) + ', запрос через ' +
            #       str(time_sleep) + ' ' + proxy)

        time.sleep(time_sleep)


def start_seeker_top_matchs_fonbet(gen_proxi_fonbet, arr_fonbet_top_matchs, pair_mathes, arr_fonbet_top_kofs):
    global TIMEOUT_MATCHS
    proxy = gen_proxi_fonbet.next()
    while True:
        try:
            list_pair_mathes = [int(item) for sublist in pair_mathes for item in sublist if item.isdigit()]
        except Exception as e:
            prnts('Фонбет, ошибка при запросе списка TOP матчей: ' + str(e) + ' ' + proxy)
            raise ValueError(e)
        try:
            resp, time_resp = get_matches_fonbet(proxy, TIMEOUT_MATCHS, top=True)
            for event in resp.get('events'):
                match_id = event.get('id')
                if match_id not in arr_fonbet_top_matchs and match_id in list_pair_mathes:
                    prnts('TOP Event added: ' + str(event.get('skId', '')) + '-' + str(event.get('skName', '')) + ': ' + str(match_id) + ', ' + event.get('eventName', ''))
                    arr_fonbet_top_matchs.append(match_id)
                elif match_id in arr_fonbet_top_matchs and match_id not in list_pair_mathes:
                    prnts('TOP Event deleted: ' + str(event.get('skId', '')) + '-' + str(event.get('skName', '')) + ': ' + str(match_id) + ', ' + event.get('eventName', ''))
                    arr_fonbet_top_matchs.remove(match_id)

                for row in event.get('markets'):
                    for cell in row.get('rows'):
                        for c in cell.get('cells'):
                            factor_id = c.get('factorId')
                            event_id_str = str(c.get('eventId'))
                            if factor_id:
                                if not arr_fonbet_top_kofs.get(event_id_str, []):
                                    arr_fonbet_top_kofs[event_id_str] = []
                                arr_fonbet_top_kofs[event_id_str].append(factor_id)

        except Exception as e:
            prnts('Фонбет, ошибка при запросе списка TOP матчей: ' + str(e) + ' ' + proxy)
            proxy = gen_proxi_fonbet.next()
            time_resp = TIMEOUT_MATCHS

        time_sleep = max(0, (TIMEOUT_MATCHS - time_resp))

        if DEBUG:
            pass
            # prnts('Фонбет, поиск TOP матчей, время ответа: ' + str(time_resp) + ', запрос через ' +
            #       str(time_sleep) + ' ' + proxy)

        time.sleep(time_sleep)


def start_seeker_bets_olimp(bets_olimp, match_id_olimp, proxies_olimp, gen_proxi_olimp, pair_mathes, mathes_complite, stat_req_ol):
    global TIMEOUT_MATCH, TIMEOUT_MATCH_MINUS

    fail_proxy = 0
    proxy_size = 10
    proxy = []
    i = 0
    while i < proxy_size:
        proxy.append(gen_proxi_olimp.next())
        i = i + 1
    ps = ProxySwitcher(proxy_size, proxy)

    while True:
        try:
            time_resp = get_bets_olimp(bets_olimp, match_id_olimp, proxies_olimp, ps.get_next_proxy(), TIMEOUT_MATCH, pair_mathes)
            stat_req_ol.append(round(time_resp, 2))
        except OlimpMatchСompleted as e:
            cnt = 0
            for pair_match in pair_mathes:
                if match_id_olimp in pair_match:
                    if bets_olimp.get(str(match_id_olimp)):
                        bets_olimp.pop(str(match_id_olimp))
                    prnts('Olimp, pair mathes remove: ' + str(pair_mathes[cnt]))
                    pair_mathes.remove(pair_mathes[cnt])
                    mathes_complite.append(match_id_olimp)
                cnt += 1
            prnts(e)
            raise ValueError('start_seeker_bets_olimp:' + str(e))
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('Exception: Олимп, ошибка при запросе матча ' + str(match_id_olimp) + ': ' +
                  str(e) + ' ' + ps.get_cur_proxy() + ' ' +
                  str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
            time_resp = TIMEOUT_MATCH

            if fail_proxy >= 3:
                ps.rep_cur_proxy(gen_proxi_olimp.next())
                fail_proxy = 0
            else:
                fail_proxy = fail_proxy + 1
                time.sleep(3)

        time_sleep = max(0, (TIMEOUT_MATCH - abs(TIMEOUT_MATCH_MINUS + time_resp)))

        if DEBUG:
            prnts('Олимп, матч ' + str(match_id_olimp) + '. Время ответа: ' + str(time_resp) + ', запрос через ' + str(time_sleep) + ' ' + ps.get_cur_proxy())

        time.sleep(time_sleep)


def start_seeker_bets_fonbet(bets_fonbet, match_id_fonbet, proxies_fonbet, gen_proxi_fonbet, pair_mathes, mathes_complite, stat_req_fb, arr_fonbet_top_kofs):
    global TIMEOUT_MATCH, TIMEOUT_MATCH_MINUS

    proxy_size = 5
    proxy = []
    i = 0
    while i < proxy_size:
        proxy.append(gen_proxi_fonbet.next())
        i = i + 1
    ps = ProxySwitcher(proxy_size, proxy)

    while True:
        try:
            time_resp = get_bets_fonbet(bets_fonbet, match_id_fonbet, proxies_fonbet, ps.get_next_proxy(), TIMEOUT_MATCH, pair_mathes, arr_fonbet_top_kofs)
            stat_req_fb.append(round(time_resp, 2))
        except FonbetMatchСompleted as e:
            cnt = 0
            for pair_match in pair_mathes:
                if match_id_fonbet in pair_match:
                    if bets_fonbet.get(str(match_id_fonbet)):
                        bets_fonbet.pop(str(match_id_fonbet))
                    prnts('Fonbet, pair mathes remove: ' + str(pair_mathes[cnt]))
                    pair_mathes.remove(pair_mathes[cnt])
                    mathes_complite.append(match_id_fonbet)
                cnt += 1
            prnts(e)
            raise ValueError('start_seeker_bets_fonbet:' + str(e))
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('Exception: Фонбет, ошибка при запросе матча ' + str(match_id_fonbet) + ': ' +
                  str(e) + ' ' + ps.get_cur_proxy() + ' ' +
                  str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
            ps.rep_cur_proxy(gen_proxi_fonbet.next())
            time_resp = TIMEOUT_MATCH

        time_sleep = max(0, (TIMEOUT_MATCH - (TIMEOUT_MATCH_MINUS + time_resp)))

        if DEBUG:
            prnts(str('Фонбет, матч ' + str(match_id_fonbet) + '. Время ответа: ' + str(time_resp) +
                      ', запрос через ' + str(time_sleep)) + ' ' + ps.get_cur_proxy())

        time.sleep(time_sleep)


def starter_bets(bets_olimp, bets_fonbet, pair_mathes, mathes_complite, mathes_id_is_work,
                 proxies_olimp, gen_proxi_olimp, proxies_fonbet, gen_proxi_fonbet, stat_req_olimp, stat_req_fonbet,
                 arr_fonbet_top_kofs):
    while True:
        for pair_match in pair_mathes:
            # print(pair_match)
            match_id_olimp, match_id_fonbet, event_type, passs = pair_match

            if match_id_olimp not in mathes_id_is_work:
                mathes_id_is_work.append(match_id_olimp)

                start_seeker_olimp_bets_by_id = threading.Thread(
                    target=start_seeker_bets_olimp,
                    args=(bets_olimp, match_id_olimp, proxies_olimp, gen_proxi_olimp, pair_mathes, mathes_complite, stat_req_olimp))
                start_seeker_olimp_bets_by_id.start()

            if match_id_fonbet not in mathes_id_is_work:
                mathes_id_is_work.append(match_id_fonbet)

                start_seeker_fonbet_bets_by_id = threading.Thread(
                    target=start_seeker_bets_fonbet,
                    args=(bets_fonbet, match_id_fonbet, proxies_fonbet, gen_proxi_fonbet, pair_mathes, mathes_complite, stat_req_fonbet, arr_fonbet_top_kofs))
                start_seeker_fonbet_bets_by_id.start()

        time.sleep(20)


def sort_by_rate(val):
    return val.get('rate', 0)


def get_rate(team1_bk1, team2_bk1, team1_bk2, team2_bk2, debug=False):
    if debug:
        fstr = team1_bk1 + '->{};' + team2_bk1 + '->{};' + team1_bk2 + '->{};' + team2_bk2 + '->{};'
    team1_bk1 = str(team1_bk1).lower()
    team2_bk1 = str(team2_bk1).lower()
    team1_bk2 = str(team1_bk2).lower()
    team2_bk2 = str(team2_bk2).lower()

    if 'corners'.lower() in team1_bk1 + team2_bk1 + team1_bk2 + team2_bk2:
        # prnts('corners exclude: ' + team1_bk1 + team2_bk1 + team1_bk2 + team2_bk2)
        return 0, 0, 0

    if team1_bk1 and team2_bk1 and team1_bk2 and team2_bk2:
        team1_bk1 = re.sub('[^A-z 0-9]', '', team1_bk1).replace(' ', '')
        team2_bk1 = re.sub('[^A-z 0-9]', '', team2_bk1).replace(' ', '')
        team1_bk2 = re.sub('[^A-z 0-9]', '', team1_bk2).replace(' ', '')
        team2_bk2 = re.sub('[^A-z 0-9]', '', team2_bk2).replace(' ', '')
        if debug:
            fstr = fstr.format(team1_bk1, team2_bk1, team1_bk2, team2_bk2)
            print(fstr)

        r1 = round(SequenceMatcher(None, team1_bk1, team1_bk2).ratio(), 3)
        r2 = round(SequenceMatcher(None, team2_bk1, team2_bk2).ratio(), 3)
        rate = round(r1 + r2, 3)

        if debug:
            print('k1: {}, k2: {}. All: {}'.format(r1, r2, rate))

        return r1, r2, rate


def start_event_mapping(pair_mathes, arr_matchs, mathes_complite):
    json_bk1_copy = dict()
    json_bk2_copy = dict()

    need = 1.5
    prnts('start_event_mapping, need: ' + str(need))

    not_compare = list()

    # print(arr_matchs)
    while True:
        try:
            prnts('Events found: ' + str(len(pair_mathes)) + ' ' + str(pair_mathes))
            bk_rate_list = list()
            bk_rate_sorted = list()
            for key, val in arr_matchs.items():
                if val.get('bk_name', '') == 'olimp':
                    json_bk1_copy[key] = val

            for key, val in arr_matchs.items():
                if val.get('bk_name', '') == 'fonbet':
                    json_bk2_copy[key] = val

            for bk1_match_id, bk1_match_info in json_bk1_copy.items():
                if [bk1_name for bk1_name in bk1_match_info.values() if bk1_name is not None]:

                    for bk2_match_id, bk2_match_info in json_bk2_copy.items():
                        if [bk2_name for bk2_name in bk2_match_info.values() if bk2_name is not None]:

                            # Проверим что матч не завершен:
                            if bk1_match_id in mathes_complite or bk2_match_id in mathes_complite:
                                pass
                            else:

                                match_name = str(bk1_match_info.get('sport_name')) + ';' + \
                                             str(bk1_match_id) + ';' + \
                                             str(bk1_match_info.get('team1')) + ';' + \
                                             str(bk1_match_info.get('team2')) + ';' + \
                                             str(bk2_match_id) + ';' + \
                                             str(bk2_match_info.get('team1')) + ';' + \
                                             str(bk2_match_info.get('team2')) + ';'

                                if bk1_match_info.get('sport_name') == bk2_match_info.get('sport_name'):
                                    r1, r2, rate = get_rate(
                                        bk1_match_info.get('team1'),
                                        bk1_match_info.get('team2'),
                                        bk2_match_info.get('team1'),
                                        bk2_match_info.get('team2')
                                    )
                                    bk_rate_list.append({
                                        str(bk1_match_id): {
                                            'bk1_t1': bk1_match_info.get('team1'),
                                            'bk1_t2': bk1_match_info.get('team2'),
                                            'rate': r1,
                                            'sport_name': bk1_match_info.get('sport_name')
                                        },
                                        str(bk2_match_id): {
                                            'bk2_t1': bk2_match_info.get('team1'),
                                            'bk2_t2': bk2_match_info.get('team2'),
                                            'rate': r2,
                                            'sport_name': bk2_match_info.get('sport_name')
                                        },
                                        'rate': rate,
                                        'match_name': match_name
                                    })

            for bkr in bk_rate_list:
                if bkr.get('rate', 0) > need:
                    bk_rate_sorted.append(bkr)
                else:
                    if 'del;' + bkr.get('match_name') not in not_compare:
                        serv_log('compare_teams', 'del;' + bkr.get('match_name'))
                        not_compare.append('del;' + bkr.get('match_name'))

            bk_rate_sorted = list(filter(lambda x: x is not None, bk_rate_sorted))
            bk_rate_sorted.sort(key=sort_by_rate, reverse=True)

            for e in bk_rate_sorted:
                pair = []
                main_rate = e.get('rate', 0)
                for m, v in e.items():
                    try:
                        if v.get('sport_name'):
                            pair.append(m)
                            if v.get('sport_name') not in pair:
                                pair.append(v.get('sport_name'))
                    except:
                        pass
                pair.sort()
                pair = [pair[1], pair[0], pair[2]]
                pair.append(e.get('match_name'))
                pair.append(e.get('rate'))

                if pair[0] in mathes_complite or pair[1] in mathes_complite:
                    pass
                else:
                    if pair not in pair_mathes:
                        conflict = False
                        is_exists = False
                        for p in pair_mathes:
                            id1, id2 = pair[0], pair[1]
                            if id1 in p:
                                if pair[4] > p[4]:
                                    print('Math conflict: ' + str(id1) + ', p: ' + str(p) + ', need: ' + str(pair))
                                    conflict = True
                                else:
                                    is_exists = True
                            if id2 in p:
                                if pair[4] > p[4]:
                                    print('Math conflict: ' + str(id2) + ', p: ' + str(p) + ', need: ' + str(pair))
                                    conflict = True
                                else:
                                    is_exists = True
                            if conflict:
                                pair_mathes.remove(p)
                                serv_log('compare_teams', 'del;' + str(p[3]) + 'conflict')
                                pair_mathes.append(pair)
                                serv_log('compare_teams', 'add;' + pair[3] + 'conflict')
                        if not conflict and not is_exists:
                            pair_mathes.append(pair)
                            serv_log('compare_teams', 'add;' + pair[3])

        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('Error start_event_mapping: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
        finally:
            time.sleep(15)


def get_forks(forks, forks_meta, pair_mathes, bets_olimp, bets_fonbet, arr_fonbet_top_matchs):
    global opposition

    def forks_meta_upd(forks_meta, forks):
        # Перед удалением сохраним время жизни вылки
        live_fork_total = forks_meta.get(bet_key, {}).get('live_fork_total', 0) + \
                          forks.get(bet_key, {}).get('live_fork', 0)
        forks_meta[bet_key] = {'live_fork_total': live_fork_total}

    while True:
        for pair_math in pair_mathes:

            is_top = False
            if int(pair_math[0]) in arr_fonbet_top_matchs or int(pair_math[1]) in arr_fonbet_top_matchs:
                is_top = True

            # print(bets_fonbet)
            # time.sleep(15)
            # see exp/bets_olimp.json

            math_json_olimp = bets_olimp.get(pair_math[0], {})
            math_json_fonbet = bets_fonbet.get(pair_math[1], {})
            event_type = pair_math[2]

            curr_opposition = copy.deepcopy(opposition)

            # print(pair_math)
            # print(math_json_olimp)
            # print(math_json_fonbet)

            for kof_type in math_json_olimp.get('kofs', {}):
                if '(' in kof_type:
                    tot_abrr = re.sub('\((.*)\)', '', kof_type)
                    tot_val = re.findall('\((.*)\)', kof_type)[0]
                    curr_opposition.update({
                        tot_abrr + '({})'.format(tot_val):
                            opposition[tot_abrr] + '({})'.format(tot_val)
                    })

            for kof_type_olimp, kof_type_fonbet in curr_opposition.items():

                bet_key = str(pair_math[0]) + '@' + str(pair_math[1]) + '@' + kof_type_olimp + '@' + kof_type_fonbet

                k_olimp = math_json_olimp.get('kofs', {}).get(kof_type_olimp, {})
                k_fonbet = math_json_fonbet.get('kofs', {}).get(kof_type_fonbet, {})

                v_olimp = k_olimp.get('value', 0.0)
                v_fonbet = k_fonbet.get('value', 0.0)
                # print(kof_type_fonbet, str(v_fonbet), kof_type_olimp, str(v_olimp), sep=";")

                if DEBUG:
                    v_olimp = v_olimp * 2
                    v_fonbet = v_fonbet * 2

                if v_olimp > 0.0 and v_fonbet > 0.0:

                    ol_time_req = math_json_olimp.get('time_req', 0)
                    fb_time_req = math_json_fonbet.get('time_req', 0)
                    cur_time = round(time.time())
                    deff_time = max((cur_time - ol_time_req), (cur_time - fb_time_req))

                    L = (1 / float(v_olimp)) + (1 / float(v_fonbet))
                    is_fork = True if L < 1 and deff_time < 7 else False
                    if is_fork:  # or True

                        time_break_fonbet = False
                        period = 0

                        if event_type == 'football':
                            period = 1
                            if re.match('\(\d+:\d+\)', math_json_fonbet.get('score_1st', '').replace(' ', '')) and \
                                    str(math_json_fonbet.get('time', '')) == '45:00' and \
                                    round(math_json_fonbet.get('minute', ''), 2) == 45.0:
                                time_break_fonbet = True
                            elif re.match('\(\d+:\d+\)', math_json_fonbet.get('score_1st', '').replace(' ', '')) and \
                                    round(math_json_fonbet.get('minute', ''), 2) > 45.0:
                                period = 2
                        elif event_type in ['basketball', 'volleyball']:
                            if 'timeout' in math_json_fonbet.get('score_1st', '').lower():
                                time_break_fonbet = True

                        # prnts('{}, {}, {}, {}, {}'.format(
                        #     pair_math,
                        #     math_json_fonbet.get('time', ''),
                        #     round(math_json_fonbet.get('minute', ''), 2),
                        #     math_json_fonbet.get('score_1st', ''),
                        #     time_break_fonbet),
                        #     filename='timebreake.log'
                        # )
                        # created_fork = forks.get(bet_key, {}).get('created_fork', '')
                        # ol_time_chage = k_olimp.get('hist', {}).get('time_change')
                        # fb_time_chage = k_fonbet.get('hist', {}).get('time_change')
                        # if ol_time_chage and fb_time_chage:
                        #     if ol_time_chage > fb_time_chage:
                        #         created_fork = 'olimp'
                        #     elif fb_time_chage > ol_time_chage:
                        #         created_fork = 'fonbet'

                        # TODO: котровка, например с олимпа ушла, и осталась брошена не в 0, в результате в bets_olimp, показывает неактуальную вилку. Надо или тут разбирать и удалять либо там?
                        # UPD 02/05/19 - Вроде не актуально
                        if forks.get(bet_key, '') != '' and deff_time < 3.8:

                            live_fork = round(time.time() - forks.get(bet_key, {}).get('create_fork'))

                            forks[bet_key].update({
                                # 'created_fork': created_fork,
                                'time_last_upd': cur_time,
                                'name': math_json_fonbet.get('name', ''),
                                'name_rus': math_json_olimp.get('name', ''),
                                'time_req_olimp': ol_time_req,
                                'time_req_fonbet': fb_time_req,
                                'l': L,
                                'pair_math': pair_math,
                                'bk1_score': math_json_olimp.get('score', ''),
                                'bk2_score': math_json_fonbet.get('score', ''),
                                'time': math_json_fonbet.get('time', '00:00'),
                                'minute': math_json_fonbet.get('minute', 0),
                                'kof_olimp': k_olimp,
                                'kof_fonbet': k_fonbet,
                                'time_break_fonbet': time_break_fonbet,
                                'period': period,
                                # 'ol_time_change_total': math_json_olimp.get('time_change_total', 0),
                                # 'ol_avg_change_total': math_json_olimp.get('avg_change_total', []),
                                # 'fb_time_change_total': math_json_fonbet.get('time_change_total', 0),
                                # 'fb_avg_change_total': math_json_fonbet.get('avg_change_total', []),
                                'live_fork': live_fork,
                                'live_fork_total': forks_meta.get(bet_key, dict()).get('live_fork_total', 0) + live_fork,
                            })

                            if True:
                                if True:  # and '46136612' in bet_key:
                                    file_forks = 'forks.csv'

                                    if DEBUG:
                                        prnts('\n')
                                        str_js = json.dumps(forks.get(bet_key), ensure_ascii=False)
                                        prnts('forks: ' + bet_key + ' ' + str(str_js))
                                        prnts('\n')

                                    if not os.path.isfile(file_forks):
                                        with open(file_forks, 'w', encoding='utf-8') as csv:
                                            csv.write(
                                                'event_type;time;time_create;created_fork;cut_time;ol_time;fb_time;live_fork;live_fork_total;'
                                                'match_ol;match_fb;kof_ol;kof_fb;name;l;l_first;bk1_score;bk2_score;'
                                                'vect_ol;vect_fb;time;'
                                                'minute;ol_kof;ol_avg_change;fb_kof;fb_avg_change;'
                                                'time_break_fonbet;is_top;is_hot;base_line;'
                                                'period;'
                                                # 'ol_avg_change_total;fb_avg_change_total;'
                                                'ol_time_change;'
                                                'ol_kof_order;'
                                                'fb_time_change;'
                                                'fb_kof_order'
                                                '\n'
                                            )
                                    if os.path.isfile(file_forks):
                                        with open(file_forks, 'a', encoding='utf-8') as csv:
                                            csv.write(
                                                event_type + ';' +
                                                str(round(time.time())) + ';' +
                                                str(forks.get(bet_key).get('create_fork')) + ';' +
                                                str(forks.get(bet_key).get('created_fork')) + ';' +
                                                str(cur_time) + ';' +
                                                str(math_json_olimp.get('time_req', '')) + ';' +
                                                str(math_json_fonbet.get('time_req', '')) + ';' +
                                                str(live_fork) + ';' +
                                                str(forks_meta.get(bet_key, dict()).get('live_fork_total', 0) + live_fork) + ';' +
                                                str(bet_key.split('@')[0]) + ';' + str(bet_key.split('@')[1]) + ';' +
                                                str(bet_key.split('@')[2]) + ';' + str(bet_key.split('@')[3]) + ';' +
                                                math_json_olimp.get('name', '') + ';' + str(L) + ';' + str(forks.get(bet_key).get('l_fisrt')) + ';' +
                                                math_json_olimp.get('score', '') + ';' +
                                                math_json_fonbet.get('score', '') + ';' +
                                                str(k_olimp.get('vector')) + ';' +
                                                str(k_fonbet.get('vector')) + ';' +
                                                str(math_json_fonbet.get('time', '00:00')) + ';' +
                                                str(math_json_fonbet.get('minute', 0)) + ';' +
                                                str(k_olimp.get('value')) + ';' +
                                                str(k_olimp.get('hist', {}).get('avg_change', [])) + ';' +
                                                str(k_fonbet.get('value')) + ';' +
                                                str(k_fonbet.get('hist', {}).get('avg_change', [])) + ';' +
                                                str(time_break_fonbet) + ';' +
                                                str(is_top) + ';' +
                                                str(k_fonbet.get('is_hot', False)) + ';' +
                                                str(k_fonbet.get('base_line', False)) + ';' +
                                                str(period) + ';' +
                                                # str(math_json_olimp.get('avg_change_total', [])) + ';' +
                                                # str(math_json_fonbet.get('avg_change_total', [])) + ';' +
                                                str(k_olimp.get('hist', {}).get('time_change', '')) + ';' +
                                                str(k_olimp.get('hist', {}).get('order', [])) + ';' +
                                                str(k_fonbet.get('hist', {}).get('time_change', '')) + ';' +
                                                str(k_fonbet.get('hist', {}).get('order', [])) +
                                                '\n'
                                            )
                        else:
                            created_fork = ''
                            ol_time_chage = k_olimp.get('hist', {}).get('time_change')
                            fb_time_chage = k_fonbet.get('hist', {}).get('time_change')
                            # print('{}, {}, {}, {}, {}'.format(event_type, fb_time_chage, ol_time_chage, k_fonbet, k_olimp))
                            if ol_time_chage and fb_time_chage:
                                if ol_time_chage > fb_time_chage:
                                    created_fork = 'olimp'
                                if fb_time_chage > ol_time_chage:
                                    created_fork = 'fonbet'

                            forks[bet_key] = {
                                'time_last_upd': cur_time,
                                'name': math_json_fonbet.get('name', ''),
                                'name_rus': math_json_olimp.get('name', ''),
                                'time_req_olimp': ol_time_req,
                                'time_req_fonbet': fb_time_req,
                                'l': L,
                                'l_fisrt': L,
                                'pair_math': pair_math,
                                'bk1_score': math_json_olimp.get('score', ''),
                                'bk2_score': math_json_fonbet.get('score', ''),
                                'time': math_json_fonbet.get('time', '00:00'),
                                'minute': math_json_fonbet.get('minute', 0),
                                'kof_olimp': k_olimp,
                                'kof_fonbet': k_fonbet,
                                'time_break_fonbet': time_break_fonbet,
                                'period': period,
                                'live_fork': 0,
                                'live_fork_total': forks_meta.get(bet_key, dict()).get('live_fork_total', 0),
                                'create_fork': round(max(ol_time_chage, fb_time_chage)),
                                'created_fork': created_fork,
                                'is_top': is_top,
                                'is_hot': k_fonbet.get('is_hot'),
                                'base_line': k_fonbet.get('base_line'),
                                'event_type': event_type
                            }
                    else:
                        try:
                            forks_meta_upd(forks_meta, forks)
                            forks.pop(bet_key)
                        except:
                            pass
                else:
                    try:
                        forks_meta_upd(forks_meta, forks)
                        forks.pop(bet_key)
                    except:
                        pass
        time.sleep(1)


def stat_req(stat_req_olimp, stat_req_fonbet):
    while True:
        if stat_req_olimp and stat_req_fonbet:
            prnts('fb cnt:' + str(len(stat_req_fonbet)) +
                  ' avg:' + str(round(sum(stat_req_fonbet) / len(stat_req_fonbet), 2)) +
                  ' max:' + str(max(stat_req_fonbet)) +
                  ' mode:' + str(round(find_max_mode(stat_req_fonbet), 2)) +
                  ' median:' + str(round(median(stat_req_fonbet), 2)))

            prnts('ol cnt:' + str(len(stat_req_olimp)) +
                  ' avg:' + str(round(sum(stat_req_olimp) / len(stat_req_olimp), 2)) +
                  ' max:' + str(max(stat_req_olimp)) +
                  ' mode:' + str(round(find_max_mode(stat_req_olimp), 2)) +
                  ' median:' + str(round(median(stat_req_olimp), 2)))
        time.sleep(60)


if __name__ == '__main__':
    prnts('DEBUG: ' + str(DEBUG))
    proxy_filename_olimp = 'olimp.proxy'
    proxy_filename_fonbet = 'fonbet.proxy'

    proxies_olimp = get_proxy_from_file(proxy_filename_olimp, uniq=False)
    proxies_fonbet = get_proxy_from_file(proxy_filename_fonbet)

    gen_proxi_olimp = createBatchGenerator(get_next_proxy(copy.deepcopy(proxies_olimp)))
    gen_proxi_fonbet = createBatchGenerator(get_next_proxy(copy.deepcopy(proxies_fonbet)))

    proxy_saver = threading.Thread(target=start_proxy_saver, args=(proxies_olimp, proxies_fonbet, proxy_filename_olimp, proxy_filename_fonbet))
    proxy_saver.start()

    arr_matchs = dict()

    arr_fonbet_top_matchs = []
    arr_fonbet_top_kofs = {}
    # Completed Events
    mathes_complite = []

    # json by bets event
    bets_fonbet = dict()
    bets_olimp = dict()

    forks = dict()
    forks_meta = dict()

    stat_req_olimp = []
    stat_req_fonbet = []

    # List of event "at work"
    pair_mathes = []

    # get event list by olimp
    olimp_seeker_matchs = threading.Thread(target=start_seeker_matchs_olimp, args=(gen_proxi_olimp, arr_matchs))
    olimp_seeker_matchs.start()

    # get event list by fonbet
    fonbet_seeker_matchs = threading.Thread(target=start_seeker_matchs_fonbet, args=(gen_proxi_fonbet, arr_matchs))
    fonbet_seeker_matchs.start()
    time.sleep(4)

    # while True:
    #     print_j(arr_matchs)
    #     time.sleep(15)

    # List of TOP events
    fonbet_seeker_top_matchs = threading.Thread(target=start_seeker_top_matchs_fonbet, args=(gen_proxi_fonbet, arr_fonbet_top_matchs, pair_mathes, arr_fonbet_top_kofs))
    fonbet_seeker_top_matchs.start()

    # Event mapping
    event_mapping = threading.Thread(target=start_event_mapping, args=(pair_mathes, arr_matchs, mathes_complite))
    event_mapping.start()

    mathes_id_is_work = []
    starter_bets = threading.Thread(
        target=starter_bets,
        args=(bets_olimp, bets_fonbet, pair_mathes, mathes_complite, mathes_id_is_work,
              proxies_olimp, gen_proxi_olimp, proxies_fonbet, gen_proxi_fonbet, stat_req_olimp, stat_req_fonbet,
              arr_fonbet_top_kofs))
    starter_bets.start()

    starter_forks = threading.Thread(target=get_forks, args=(forks, forks_meta, pair_mathes, bets_olimp, bets_fonbet, arr_fonbet_top_matchs))
    starter_forks.start()

    started_stat_req = threading.Thread(target=stat_req, args=(stat_req_olimp, stat_req_fonbet))
    started_stat_req.start()

    server = threading.Thread(target=run_server, args=(SERVER_IP, SERVER_PORT, forks, pair_mathes, arr_fonbet_top_matchs))
    server.start()

    proxy_saver.join()
    olimp_seeker_matchs.join()
    fonbet_seeker_matchs.join()
    event_mapping.join()
    starter_forks.join()
    started_stat_req.join()
    server.join()
