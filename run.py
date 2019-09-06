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
from utils import prnts, DEBUG, find_max_mode, opposition, MINUTE_COMPLITE, serv_log, get_param, sport_list
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

prnts('TIMEOUT_MATCHS: ' + str(TIMEOUT_MATCHS))
prnts('TIMEOUT_MATCH: ' + str(TIMEOUT_MATCH))
prnts('TIMEOUT_MATCH_MINUS: ' + str(TIMEOUT_MATCH_MINUS))
prnts('MINUTE_COMPLITE: ' + str(MINUTE_COMPLITE))
prnts('SERVER_IP: ' + str(SERVER_IP))

def if_exists(jsos_list: dict, key_name: str, val: str, get_key: str=None):
    for m in jsos_list:
        if m.get(key_name) == val:
            if not get_key:
                return True
            else:
                return m.get(get_key, 'error: key name:{} in {} not found'.format(get_key, m))
    return False
    
    


def get_olimp(resp, arr_matchs):
    # Очистим дстарые данные
    arr_matchs_copy = copy.deepcopy(arr_matchs)
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
        arr_matchs.pop(key)
    # получим все события по футболу
    events = [
        {
            'bk': 'fonbet', 
            'name': sport['name'], 
            'id': sport['id'], 
            'sportId': sport['parentId']
        } for sport in resp['sports'] if sport['kind'] == 'segment' and if_exists(sport_list, 'fonbet', sport['parentId'])
    ]
    
    # получим список ид всех матчей по событиям
    idEvents = [{'id' : e.get('id'), 'sportId': e.get('sportId')} for e in events]
    for idEvent in idEvents:
        idMatches = [{'id': event['id'], 'sportId': idEvent['sportId']} for event in resp['events'] if if_exists(idEvents, 'id', event.get('sportId'))]

    # полчим все инфу по ид матча
    if idEvents and idMatches:
        for mid in idMatches:
            for event in resp['events']:
                if event['id'] == mid.get('id') and if_exists(idEvents, 'id', event['sportId']):
                    arr_matchs[str(event['id'])] = {
                        'bk_name': 'fonbet',
                        'sport_id': mid.get('sportId'),
                        'sport_name': if_exists(sport_list, 'fonbet', mid.get('sportId'), 'name'),
                        'name': event['name'],
                        'team1': event.get('team1', ''),
                        'team2': event.get('team2', ''),
                    }
        # for mid in idMatches:
        # for event in resp['events']:
        # if event['id'] == mid and event['kind'] > 1 and event['name'] in ['1st half', '2nd half', 'corners']:
    print(arr_matchs)


def start_seeker_matchs_olimp(proxies, gen_proxi_olimp, arr_matchs):
    global TIMEOUT_MATCHS
    proxy = gen_proxi_olimp.next()
    fail_proxy = 0
    while True:
        try:
            resp, time_resp = get_matches_olimp(proxies, proxy, TIMEOUT_MATCHS)
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


def start_seeker_top_matchs_fonbet(gen_proxi_fonbet, arr_fonbet_top_matchs, pair_mathes):
    global TIMEOUT_MATCHS
    proxy = gen_proxi_fonbet.next()
    while True:
        list_pair_mathes = [int(item) for sublist in pair_mathes for item in sublist]
        try:
            resp, time_resp = get_matches_fonbet(proxy, TIMEOUT_MATCHS, top=True)
            for event in resp.get('events'):
                if event.get('skId') == 1:
                    match_id = event.get('id')
                    if match_id not in arr_fonbet_top_matchs and match_id in list_pair_mathes:
                        prnts('TOP матч добавлен: ' + str(match_id) + ', ' + event.get('eventName'))
                        arr_fonbet_top_matchs.append(match_id)
                    elif match_id in arr_fonbet_top_matchs and match_id not in list_pair_mathes:
                        prnts('TOP матч удален: ' + str(match_id) + ', ' + event.get('eventName'))
                        arr_fonbet_top_matchs.remove(match_id)
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
            time_resp = get_bets_olimp(bets_olimp, match_id_olimp, proxies_olimp,
                                       ps.get_next_proxy(), TIMEOUT_MATCH, pair_mathes)
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


def start_seeker_bets_fonbet(bets_fonbet, match_id_fonbet, proxies_fonbet, gen_proxi_fonbet, pair_mathes, mathes_complite, stat_req_fb):
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
            time_resp = get_bets_fonbet(bets_fonbet, match_id_fonbet, proxies_fonbet, ps.get_next_proxy(), TIMEOUT_MATCH, pair_mathes)
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
            prnts(str('Фон��ет, матч ' + str(match_id_fonbet) + '. Время ответа: ' + str(time_resp) +
                      ', запрос через ' + str(time_sleep)) + ' ' + ps.get_cur_proxy())

        time.sleep(time_sleep)


def starter_bets(bets_olimp, bets_fonbet, pair_mathes, mathes_complite, mathes_id_is_work,
                 proxies_olimp, gen_proxi_olimp, proxies_fonbet, gen_proxi_fonbet, stat_req_olimp, stat_req_fonbet):
    while True:
        for pair_match in pair_mathes:
            match_id_olimp, match_id_fonbet = pair_match

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
                    args=(bets_fonbet, match_id_fonbet, proxies_fonbet, gen_proxi_fonbet, pair_mathes, mathes_complite, stat_req_fonbet))
                start_seeker_fonbet_bets_by_id.start()

        time.sleep(20)


def compare_teams(team1_bk1, team2_bk1, team1_bk2, team2_bk2):
    # TODO add event group
    if team1_bk1 and team2_bk1 and team1_bk2 and team2_bk2:
        team1_bk1 = re.sub('[^A-z 0-9]', '', team1_bk1.lower()).replace(' ', '')
        team2_bk1 = re.sub('[^A-z 0-9]', '', team2_bk1.lower()).replace(' ', '')
        team1_bk2 = re.sub('[^A-z 0-9]', '', team1_bk2.lower()).replace(' ', '')
        team2_bk2 = re.sub('[^A-z 0-9]', '', team2_bk2.lower()).replace(' ', '')
        if 1.7 < \
                SequenceMatcher(None, team1_bk1, team1_bk2).ratio() + \
                SequenceMatcher(None, team2_bk1, team2_bk2).ratio():
            # print(team1_bk1, team2_bk1, team1_bk2, team2_bk2, sep=';')
            return True
    else:
        return False


def start_compare_matches(pair_mathes, json_bk1, json_bk2, mathes_complite):
    while True:
        try:
            prnts('Найдено матчей: ' + str(len(pair_mathes)) + ' ' + str(pair_mathes))
            json_bk1_copy = copy.deepcopy(json_bk1)
            json_bk2_copy = copy.deepcopy(json_bk2)
            for bk1_match_id, bk1_match_info in json_bk1_copy.items():
                if [bk1_name for bk1_name in bk1_match_info.values() if bk1_name is not None]:
                    # Проверим что ид матча 1 нет в списке
                    if 'yes' not in list(map(lambda id: 'yes' if bk1_match_id in id else 'no', pair_mathes)):
                        for bk2_match_id, bk2_match_info in json_bk2_copy.items():
                            if [bk2_name for bk2_name in bk2_match_info.values() if bk2_name is not None]:
                                # Проверим что ид матча 2 нет в списке
                                if 'yes' not in list(map(lambda id: 'yes' if bk2_match_id in id else 'no', pair_mathes)):
                                    # Проверим что матч не завершен:
                                    if bk1_match_id in mathes_complite or bk2_match_id in mathes_complite:
                                        # prnts('Матчи завершены: ' + str(bk1_match_id) + '-' + str(bk2_match_id))
                                        pass
                                    else:
                                        match_name = str(bk1_match_id) + ' ' + \
                                                     bk1_match_info.get('team1') + ' vs ' + \
                                                     bk1_match_info.get('team2') + ' | ' + \
                                                     str(bk2_match_id) + ' ' + \
                                                     bk2_match_info.get('team1') + ' vs ' + \
                                                     bk2_match_info.get('team2')

                                        if compare_teams(
                                                bk1_match_info.get('team1'),
                                                bk1_match_info.get('team2'),
                                                bk2_match_info.get('team1'),
                                                bk2_match_info.get('team2')
                                        ):
                                            # if re.search('(u\d{2}|\(w\)|\(r\)|\(res\)|\(Reserves\)|-stud\.), match_name.lower()):
                                            #     serv_log('match_list', 'Матч исключен: ' + match_name)
                                            #     pass
                                            if DEBUG:  # and str(bk2_match_id) == '13706641':
                                                serv_log('match_list', 'Матч добавлен: ' + match_name)
                                                pair_mathes.append([bk1_match_id, bk2_match_id])
                                            elif not DEBUG:
                                                serv_log('match_list', 'Матч добавлен: ' + match_name)
                                                pair_mathes.append([bk1_match_id, bk2_match_id])

            time.sleep(15)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('Error start_compare_matches: ' +
                  str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))


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

            curr_opposition = copy.deepcopy(opposition)

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

                if DEBUG:
                    v_olimp = v_olimp + 1
                    v_fonbet = v_fonbet + 1

                if v_olimp > 0.0 and v_fonbet > 0.0:

                    ol_time_req = math_json_olimp.get('time_req', 0)
                    fb_time_req = math_json_fonbet.get('time_req', 0)
                    cur_time = round(time.time())
                    deff_time = max((cur_time - ol_time_req), (cur_time - fb_time_req))

                    L = (1 / float(v_olimp)) + (1 / float(v_fonbet))
                    is_fork = True if L < 1 and deff_time < 7 else False

                    if is_fork:  # or True
                        time_break_fonbet = False
                        period = 1
                        if re.match('\(\d+:\d+\)', math_json_fonbet.get('score_1st', '').replace(' ', '')) and \
                                str(math_json_fonbet.get('time', '')) == '45:00' and \
                                round(math_json_fonbet.get('minute', ''), 2) == 45.0:
                            time_break_fonbet = True
                        elif re.match('\(\d+:\d+\)', math_json_fonbet.get('score_1st', '').replace(' ', '')) and \
                                round(math_json_fonbet.get('minute', ''), 2) > 45.0:
                            period = 2

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
                                'live_fork_total': forks_meta.get(bet_key, dict()).get('live_fork_total', 0) + live_fork

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
                                                'time;time_create;created_fork;cut_time;ol_time;fb_time;live_fork;live_fork_total;'
                                                'match_ol;match_fb;kof_ol;kof_fb;name;l;bk1_score;bk2_score;'
                                                'vect_ol;vect_fb;time;'
                                                'minute;ol_kof;ol_avg_change;fb_kof;fb_avg_change;'
                                                'time_break_fonbet;is_top;'
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
                                                math_json_olimp.get('name', '') + ';' + str(L) + ';' +
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
                                'is_top': is_top
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

    proxy_saver = threading.Thread(target=start_proxy_saver, args=(proxies_olimp, proxies_fonbet, proxy_filename_olimp, proxy_filename_fonbet,))
    proxy_saver.start()

    # arr_BKNAME_matchs Список матчей, TODO, Педелать на универсальный формат, 1 для всех БК
    arr_olimp_matchs = dict() 
    arr_fonbet_matchs = dict()
    arr_matchs = dict()
    
    arr_fonbet_top_matchs = []
    mathes_complite = []

    # json by bets math
    bets_fonbet = dict()
    bets_olimp = dict()

    forks = dict()
    forks_meta = dict()

    stat_req_olimp = []
    stat_req_fonbet = []

    pair_mathes = []

    olimp_seeker_matchs = threading.Thread(target=start_seeker_matchs_olimp, args=(proxies_olimp, gen_proxi_olimp, arr_olimp_matchs))
    olimp_seeker_matchs.start()

    fonbet_seeker_matchs = threading.Thread(target=start_seeker_matchs_fonbet, args=(gen_proxi_fonbet, arr_fonbet_matchs))
    fonbet_seeker_matchs.start()

    fonbet_seeker_top_matchs = threading.Thread(target=start_seeker_top_matchs_fonbet, args=(gen_proxi_fonbet, arr_fonbet_top_matchs, pair_mathes))
    fonbet_seeker_top_matchs.start()

    compare_matches = threading.Thread(target=start_compare_matches, args=(pair_mathes, arr_olimp_matchs, arr_fonbet_matchs, mathes_complite))
    compare_matches.start()

    mathes_id_is_work = []
    starter_bets = threading.Thread(
        target=starter_bets,
        args=(bets_olimp, bets_fonbet, pair_mathes, mathes_complite, mathes_id_is_work,
              proxies_olimp, gen_proxi_olimp, proxies_fonbet, gen_proxi_fonbet, stat_req_olimp, stat_req_fonbet))
    starter_bets.start()

    starter_forks = threading.Thread(target=get_forks, args=(forks, forks_meta, pair_mathes, bets_olimp, bets_fonbet, arr_fonbet_top_matchs))
    starter_forks.start()

    started_stat_req = threading.Thread(target=stat_req, args=(stat_req_olimp, stat_req_fonbet))
    started_stat_req.start()

    server = threading.Thread(target=run_server, args=(SERVER_IP, forks, pair_mathes, arr_fonbet_top_matchs))
    server.start()

    proxy_saver.join()
    olimp_seeker_matchs.join()
    fonbet_seeker_matchs.join()
    compare_matches.join()
    starter_forks.join()
    started_stat_req.join()
    server.join()
