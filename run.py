# coding:utf-8
from util_olimp import *
from util_fonbet import *
import util_pinnacle
from proxy_worker import get_proxy_from_file, start_proxy_saver, createBatchGenerator, get_next_proxy
import time
from json import loads, dumps
import threading
from difflib import SequenceMatcher
import re
from exceptions import *
from server import run_server
from utils import prnts, DEBUG, find_max_mode, opposition, add_if_draw, add_if_not_draw, serv_log, get_param, sport_list, if_exists, print_j, max_min_prematch, if_exists_by_sport
from utils import TIMEOUT_LIST, TIMEOUT_MATCH, TIMEOUT_MATCH_MINUS, TIMEOUT_PRE_LIST, TIMEOUT_PRE_MATCH, TIMEOUT_PRE_MATCH_MINUS, SERVER_IP, SERVER_PORT, time_sleep_proc
from utils import bk_working
from proxy_switcher import ProxySwitcher
import json
import os.path
import os
from statistics import median
from datetime import datetime
import copy
import math
import pandas as pd
import itertools

import cupon
import bot

import sys
import traceback


def get_olimp(resp, arr_matchs, place='live', sport_id=None, arr_top_matchs=None, my_top=None, my_middle=None, my_slag=None, liga_unknown=None):
    # Очистим дстарые данные
    for key in list(arr_matchs):
        if arr_matchs.get('olimp', '') != '':
            arr_matchs.pop(key)
    if place == 'live':
        key_name = 'cn'
    else:
        key_name = 'n'
        resp = [resp]
    if resp:
        for liga_info in resp:
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
            v_sport_id = int(liga_info.get('sport_id', sport_id))
            liga_id = liga_info.get('id')
            liga_name = liga_info[key_name]
            if 'statistics' not in liga_name.lower() and 'outrights' not in liga_name.lower() and 'special offers' not in liga_name.lower() and 'head-to-head' not in liga_name.lower():
                if if_exists(sport_list, 'olimp', v_sport_id) and if_exists_by_sport(sport_list, 'olimp', v_sport_id, 'place', place):
                    for math_info in liga_info.get('it'):
                        match_id = math_info.get('id')
                        match_id_str = str(match_id)
                        start_time = math_info.get('t', 0)
                        start_after_min = math.floor((start_time - int(time.time())) / 60)
                        if start_after_min < max_min_prematch:
                            arr_matchs[match_id_str] = {
                                'bk_name': 'olimp',
                                'place': place,
                                'sport_id': v_sport_id,
                                'sport_name': if_exists(sport_list, 'olimp', v_sport_id, 'name'),
                                'name': liga_name,
                                'team1': math_info.get('c1', ''),
                                'team2': math_info.get('c2', ''),
                                'start_time': start_time,
                                # 'start_time_str': start_time_str,
                                'start_after_min': start_after_min,
                            }
                        if v_sport_id in (1, 2):
                            # if liga_name in my_top and match_id not in arr_top_matchs.get('top', []):
                            if max(list(map(lambda s: 1 if liga_name.lower() in s.lower()[0:len(liga_name)] else 0, my_top))) == 1 and match_id not in arr_top_matchs.get('top', []):
                                prnts('my_top ' + place + ' Event added: ' + str(match_id_str) + ', liga_name ' + str(liga_name) + ', liga_id: ' + str(liga_id))
                                arr_top_matchs['top'].append(match_id)
                            # elif liga_name in my_middle and match_id not in arr_top_matchs.get('middle', []):
                            elif max(list(map(lambda s: 1 if liga_name.lower() in s.lower()[0:len(liga_name)] else 0, my_middle))) == 1 and match_id not in arr_top_matchs.get('middle', []):
                                prnts('my_middle ' + place + ' Event added: ' + str(match_id_str) + ', liga_name ' + str(liga_name) + ', liga_id: ' + str(liga_id))
                                arr_top_matchs['middle'].append(match_id)
                            # elif liga_name in my_slag and match_id not in arr_top_matchs.get('slag', []):
                            elif max(list(map(lambda s: 1 if liga_name.lower() in s.lower()[0:len(liga_name)] else 0, my_slag))) == 1 and match_id not in arr_top_matchs.get('slag', []):
                                prnts('my_slag ' + place + ' Event added: ' + str(match_id_str) + ', liga_name ' + str(liga_name) + ', liga_id: ' + str(liga_id))
                                arr_top_matchs['slag'].append(match_id)
                            # elif liga_name not in my_top + my_middle + my_slag:
                            elif max(list(map(lambda s: 1 if liga_name.lower() in s.lower()[0:len(liga_name)] else 0,  my_top + my_middle + my_slag))) == 0:
                                if liga_name not in liga_unknown:
                                    liga_unknown.append(liga_name)
                                    v_str = if_exists(sport_list, 'olimp', v_sport_id, 'name') + ';' + str(liga_name) + ';\n'
                                    with open('liga_not_found.csv', 'r+') as file:
                                        for line in list(file):
                                            if v_str in line:
                                                break
                                        else:  # not found, we are at the eof
                                            file.write(v_str)  # append missing data
                        else:
                            if DEBUG:
                                prnts('Собитие исключено т.к. время начала больше: {}, мин:{}\ndata:{}'.format(max_min_prematch, start_after_min, str(math_info)), 'hide')
    # print_j(arr_matchs) # 50940691


def get_fonbet(resp, arr_matchs, place):
    # with open('resp.json', 'w') as f:
    #     s = str(resp).replace('\'', '"').replace('False', '"False"').replace('True', '"True"')
    #     f.write(s)
    # print(str(resp)[0:10000])

    # for val in resp.get('sports'):
    #     if val.get('kind') == 'sport':
    #         prnts(str(val.get('id')) + ' ' + val.get('name'))
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
    for key in list(arr_matchs):
        if arr_matchs.get('fonbet', '') != '':
            arr_matchs.pop(key)

    # получим все события по футболу
    events = [
        {
            'event_bk': 'fonbet',
            'event_name': sport['name'],
            'event_id': sport['id'],
            'event_sportId': sport['parentId']
        } for sport in resp['sports'] if sport['kind'] == 'segment' and if_exists(sport_list, 'fonbet', sport.get('parentId')) and if_exists_by_sport(sport_list, 'fonbet', sport.get('parentId'), 'place', place)
    ]

    # получим список ид всех матчей по событиям
    idMatches = list()
    idEvents = [{'event_id': e.get('event_id'), 'event_sportId': e.get('event_sportId')} for e in events]

    for idEvent in idEvents:
        # prnts(idEvent['event_id'])

        # for event in resp['events']:
        #     print(event)

        # prnts([{'id': event['id'], 'sportId': idEvent['event_sportId']} for event in resp['events'] if event.get('parentId', -1) == -1])
        for x in [{'id': event['id'], 'sportId': idEvent['event_sportId'], 'isHot': event.get('state', {}).get('inHotList', False), 'place': event['place']} for event in resp['events'] if
                  event['sportId'] == idEvent['event_id'] and event.get('parentId', -1) == -1]:
            idMatches.append(x)
        # полчим все инфу по ид матча
    # print_j(resp['events'])
    if idEvents and idMatches:
        for mid in idMatches:
            for event in resp['events']:
                # Только главные события
                if event['id'] == mid.get('id'):  # and event.get('parentId', -1) == -1 # Пока вырезал все дочерние события выше see row: 123
                    # prnts(sport_list)
                    # prnts(if_exists(sport_list, 'fonbet', mid.get('sportId'), 'name'))
                    # print(event)
                    start_after_min = math.floor((int(event.get('startTime', 0)) - int(time.time())) / 60)
                    if start_after_min < max_min_prematch:
                        arr_matchs[str(event['id'])] = {
                            'bk_name': 'fonbet',
                            'place': place,
                            # 'place': event.get('place'),
                            'sport_id': mid.get('sportId'),
                            'sport_name': if_exists(sport_list, 'fonbet', mid.get('sportId'), 'name'),
                            'name': event['name'],
                            'team1': event.get('team1', ''),
                            'team2': event.get('team2', ''),
                            'start_time': event.get('startTime', 0),
                            'start_after_min': start_after_min,
                            'isHot': mid.get('isHot')
                        }
                        # if mid.get('isHot'):
                        #     prnts('hot: ' + str(event['priority']) + ' ' + str(arr_matchs[str(event['id'])]))
                        # else:
                        #     prnts('no: ' + str(event['priority']) + ' ' + str(arr_matchs[str(event['id'])]))
                    else:
                        if DEBUG:
                            prnts('Собитие исключено т.к. время начла больше: {}, мин.:{}\ndata:{}'.format(max_min_prematch, start_after_min, str(event)), 'hide')

        # for mid in idMatches:
        # for event in resp['events']:
        # if event['id'] == mid and event['kind'] > 1 and event['name'] in ['1st half', '2nd half', 'corners']:
    # print_j(len(arr_matchs))
    # ['16453828': {'bk_name': 'fonbet', 'sport_id': 1, 'sport_name': 'Football', 'name': '', 'team1': 'Nadi', 'team2': 'Suva'}, ....]
    
def set_matches_pinnacle(bk_name, resp, arr_matchs, match_id_work):
    for match_id, match_data in resp.items():
        for key in list(match_data):
            if key not in ('bk_name', 'sport_id', 'sport_name', 'name', 'team1', 'team2', 'start_time', 'minute', 'score', 'place', 'time_req'):
                match_data.pop(key)
        arr_matchs[str(match_id)] = match_data
        # print(str(match_id) + ' ' + match_data.get('sport_name') + ' ' + match_data.get('name'))


def set_api(bk_name, proxy, session):
    global pinn_session_data
    try:
        if bk_name == 'pinnacle':
            head = {
                'accept': 'application/json',
                'content-type': 'application/json',
                # 'origin': 'https://www.pinnacle.com',
                # 'referer': 'https://www.pinnacle.com',
                # 'sec-fetch-mode': 'cors',
                # 'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            }
            res = requests.get(url='https://www.pinnacle.com/config/app.json', proxies={'https': proxy}, timeout=10, verify=False)
            try:
                api_key = res.json()['api']['haywire']['apiKey']
            except Exception as e:
                # print(res.status_code, res.text)
                raise ValueError(bk_name + ', возникла ошибка при запросе ключа, код ответа ' + str(res.status_code) + ': ' + str(e))
    
            head.update({'x-api-key': api_key})
            head.update({'x-device-uuid': util_pinnacle.x_device_uuid_temp})
            if session:
                xs = session.post
            else:
                xs = requests.post
            res = xs(
                url='https://api.arcadia.pinnacle.com/0.1/sessions',
                # url='http://192.168.1.143:8888',
                proxies={'https': proxy},
                timeout=10,
                verify=False,
                headers=head,
                json={
                    # "username": "ES1096942",
                    # "password": "11112007_A"
                    "username": "IS1204996",
                    "password": "p1962Abce"
                }
            )
            resp = res.json()
            prnts(resp)
            x_session = resp.get('token')
            # ??? = resp.get('transactionId')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        raise ValueError(bk_name + ', возникла ошибка при запросе ключа, код ответа ' + str(res.status_code) + ': ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
    if api_key:
        pinn_session_data.update({'api_key': api_key})
    if util_pinnacle.x_device_uuid_temp:
        pinn_session_data.update({'x_device_uuid': util_pinnacle.x_device_uuid_temp})
    if x_session:
        pinn_session_data.update({'x_session': x_session})    

def start_seeker_matchs(bk_name, proxies_container, arr_matchs, place, session):
    global TIMEOUT_LIST, TIMEOUT_PRE_LIST, pinn_session_data
    
    proxy = proxies_container[bk_name]['gen_proxi'].next()
    fail_proxy = 0
    
    if 'pinnacle' == bk_name:
        api_key = pinn_session_data.get('api_key')
        x_session = pinn_session_data.get('x_session')
        x_device_uuid = pinn_session_data.get('x_device_uuid')
    
    if 'olimp' == bk_name:
        try:
            df = pd.read_csv('top_by_name.csv', encoding='utf-8', sep=';')
            my_top = list(df[(df['is_top'] == 2)]['liga_name'])
            my_middle = list(df[(df['is_top'] == 1)]['liga_name'])
            my_slag = list(df[(df['is_top'] == 0)]['liga_name'])
            if place == 'live':
                prnts('my_top: ' + str(my_top))
                prnts('my_middle: ' + str(my_middle))
                prnts('my_slag: ' + str(my_slag))
        except Exception as e:
            prnts('err liga_top: ' + str(e))
                
    while True:
        match_id_work = []
        if place == 'pre':
            time_out = TIMEOUT_PRE_LIST
        else:
            time_out = TIMEOUT_LIST
        proxy = proxies_container[bk_name]['gen_proxi'].next()
        fail_proxy = 0
        arr_leagues = {}
        liga_unknown = []
        time_resp = 0
        try:
            if bk_name == 'olimp':
                if place == 'pre':
                    # get leagues
                    for sport in sport_list:
                        if 'pre' in sport.get('place'):
                            sport_id = sport.get('olimp')
                            resp_leagues = {}
                            try:
                                resp_leagues, time_resp = get_matches_olimp(proxy, time_out, 'champs', sport_id, max_min_prematch / 60)
                                # print_j(resp_leagues)                            
                                if resp_leagues:
                                    l = 0
                                    for leagues_arr in resp_leagues:
                                        l = l + 1
                                        prnts('sport_id: {}, get leagues: {}/{}'.format(sport_id, len(resp_leagues), l))
                                        liga_id_str = str(leagues_arr.get('id'))
                                        if liga_id_str not in arr_leagues.get(sport_id, {}):
                                            if arr_leagues.get(sport_id) is not None:
                                                arr_leagues[sport_id].append(liga_id_str)
                                            else:
                                                arr_leagues[sport_id] = []
                                                arr_leagues[sport_id].append(liga_id_str)
                                            try:
                                                prnts('request: sport_id:{}, liga_id:{}'.format(sport_id, liga_id_str))
                                                resp_matches, time_resp = get_matches_olimp(proxy, time_out, 'matches', sport_id, max_min_prematch / 60, liga_id_str)
                                                get_olimp(resp_matches, arr_matchs, 'pre', sport_id, arr_top_matchs, my_top, my_middle, my_slag, liga_unknown)
                                                # print_j(resp_matches)
                                                prnts('sport_id: {}, liga_id:{}, add matches: {}, liga name:{}'.format(sport_id, liga_id_str, len(resp_matches.get('it')), resp_matches.get('n')))
                                            except Exception as e:
                                                if 'We are updating betting line'.lower() in str(e).lower():
                                                    pass
                                                    prnts(e)
                                                else:
                                                    pass
                                                    # raise ValueError(str(e))
                                                    exc_type, exc_value, exc_traceback = sys.exc_info()
                                                    prnts(str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
                                                if liga_id_str in arr_leagues[sport_id]:
                                                    del arr_leagues[sport_id][arr_leagues[sport_id].index(liga_id_str)]
                                                    prnts('sport_id:{}, Возникала ошибка при запросе списка пре матчей по лиге {}, лига удалена из списка: {}'.format(sport_id, liga_id_str, arr_leagues))
                                                else:
                                                    prnts('sport_id:{}, Возникала ошибка при запросе списка пре матчей по лиге {}, но лига не найдена в списке: {}'.format(sport_id, liga_id_str, arr_leagues))
                            except Exception as e:
                                if 'scan error: We are updating betting line'.lower() in str(e).lower():
                                    pass
                                    prnts(e)
                                else:
                                    exc_type, exc_value, exc_traceback = sys.exc_info()
                                    prnts(str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
                                    pass
                                    # raise ValueError(str(e))
                            if DEBUG:
                                prnts('sport ' + str(sport_id) + ': ' + str(len(resp_leagues)))
                    # # get matches by liga_id
                    # ligu = {}
                    # l = 0
                    # for sport_id in list(arr_leagues):
                    #     l = l + 1
                    #     m = 0
                    #     for liga_id in arr_leagues[sport_id]:
                    #         # print(liga_id)
                    #
                    #
                    #         # print_j(arr_matchs)
                    #         # print(len(arr_matchs))
                    #         # time.sleep(5)
                else:
                    resp, time_resp = get_matches_olimp(proxy, time_out, place)
                    get_olimp(resp, arr_matchs, 'live', None, arr_top_matchs, my_top, my_middle, my_slag, liga_unknown)
                time_sleep = max(0, (time_out - time_resp))
                if DEBUG:
                    pass
                    # prnts('Олимп, поиск матчей, время ответа: ' + str(time_resp) + ', запрос через ' +
                    #       str(time_sleep) + ' ' + proxy)
                time.sleep(time_sleep)
            elif bk_name == 'fonbet':
                resp, time_resp = get_matches_fonbet(proxy, time_out, place)
                get_fonbet(resp, arr_matchs, place)
                time_sleep = max(0, (time_out - time_resp))
                if DEBUG:
                    pass
                    # prnts('Фонбет, поиск матчей, время ответа: ' + str(time_resp) + ', запрос через ' +
                    #       str(time_sleep) + ' ' + proxy)
                time.sleep(time_sleep)
            elif bk_name == 'pinnacle':
                resp, time_resp = util_pinnacle.get_matches(bk_name, proxy, TIMEOUT_LIST, api_key, x_session, x_device_uuid, proxies_container[bk_name]['proxy_list'], session, place)
                set_matches_pinnacle(bk_name, resp, arr_matchs, match_id_work)
            # print(bk_name, place, str(arr_matchs))
        except TimeOut as e:
            err_str = 'Timeout: ошибка призапросе списока матчей из ' + bk_name
            prnts(err_str)
            time_resp = TIMEOUT_LIST

            if fail_proxy >= 3:
                proxy = proxies_container[bk_name]['gen_proxi'].next()
            else:
                fail_proxy = fail_proxy + 1
                time.sleep(3)

        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            e = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            prnts('Exception: ошибка при запросе списка матчей из ' + bk_name + ':' + str(e))
            time_resp = TIMEOUT_LIST

            if fail_proxy >= 3:
                proxy = proxies_container[bk_name]['gen_proxi'].next()
                fail_proxy = 0
            else:
                fail_proxy = fail_proxy + 1
                time.sleep(3)

        time_sleep = max(0, (TIMEOUT_LIST - time_resp))

        # if DEBUG:
        # pass
        # prnts('Олимп, поиск матчей, время ответа: ' + str(time_resp) + ', запрос через ' + str(time_sleep) + ' ' + proxy)

        time.sleep(time_sleep)        


def start_seeker_top_matchs_fonbet(proxies_container, arr_top_matchs, pair_mathes, arr_fonbet_top_kofs):
    global TIMEOUT_LIST
    bk_name = 'fonbet'
    proxy = proxies_container[bk_name]['gen_proxi'].next()

    while True:
        try:
            list_pair_mathes = []
            for m in pair_mathes:
                list_pair_mathes.append(int(m[0]))
                list_pair_mathes.append(int(m[1]))
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            e = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            prnts('Фонбет, ошибка при запросе списка TOP матчей: ' + str(e) + ' ' + proxy)
            raise ValueError(e)
        try:
            for place in ('top:live', 'top:pre'):
                resp, time_resp = get_matches_fonbet(proxy, TIMEOUT_LIST, place)
                # print(str(resp)[0:10000])
                for event in resp.get('events'):
                    match_id = event.get('id')
                    liga_id = event.get('competitionId')
                    # liga_name = event.get('competitionName')
                    sport_id = event.get('skId', '')
                    sport_name = event.get('skName', '')
                    if str(event.get('skId')) in ('1', '2'):  # and place == 'top:pre':
                        pass
                    else:
                        if match_id not in arr_top_matchs.get('top', []) and match_id in list_pair_mathes:
                            prnts('TOP ' + place.split(':')[1] + ' Event added: ' + str(sport_id) + '-' + str(sport_name) + ': ' + str(match_id) + ', ' + event.get('eventName', '') + ', ' + str(liga_id))
                            arr_top_matchs['top'].append(match_id)
                        elif match_id in arr_top_matchs.get('top', []) and match_id not in list_pair_mathes:
                            prnts('TOP ' + place.split(':')[1] + 'Event deleted: ' + str(sport_id) + '-' + str(sport_name) + ': ' + str(match_id) + ', ' + event.get('eventName', '') + ', ' + str(liga_id))
                            top_temp = list(arr_top_matchs['top'])
                            top_temp.remove(match_id)
                            arr_top_matchs['top'] = list(top_temp)

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
            exc_type, exc_value, exc_traceback = sys.exc_info()
            e = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            prnts('Фонбет, ошибка при запросе списка TOP матчей: ' + str(e) + ' ' + proxy)
            proxy = proxies_container[bk_name]['gen_proxi'].next()
            time_resp = TIMEOUT_LIST

        time_sleep = max(0, (TIMEOUT_LIST - time_resp))

        if DEBUG:
            pass
            # prnts('Фонбет, поиск TOP матчей, время ответа: ' + str(time_resp) + ', запрос через ' +
            #       str(time_sleep) + ' ' + proxy)

        time.sleep(time_sleep)


def start_seeker_bets_olimp(bets, match_id_olimp, proxies_container, pair_mathes, mathes_complite, stat_reqs, place):
    global TIMEOUT_MATCH, TIMEOUT_MATCH_MINUS
    global TIMEOUT_PRE_MATCH, TIMEOUT_PRE_MATCH_MINUS
    bk_name = 'olimp'
    fail_proxy = 0
    proxy_size = 10
    proxy = []
    i = 0
    n = 1
    while i < proxy_size:
        proxy.append(proxies_container[bk_name]['gen_proxi'].next())
        i = i + 1
    ps = ProxySwitcher(proxy_size, proxy)

    while True:
        try:
            time_resp = get_bets_olimp(bets, match_id_olimp, proxies_container[bk_name]['proxy_list'], ps.get_next_proxy(), TIMEOUT_MATCH, pair_mathes, place, str(n))
            # print(bets)
            set_stat_reqs(stat_reqs, bk_name, time_resp)
        except OlimpMatchСompleted as e:
            cnt = 0
            prnts(e)
            try:
                for pair_match in pair_mathes:
                    if match_id_olimp in pair_match:
                        if bets.get(str(match_id_olimp)):
                            bets.pop(str(match_id_olimp))
                        prnts('Olim (OlimpMatchСompleted), pair mathes remove: ' + str(pair_mathes[cnt]))
                        pair_mathes.remove(pair_mathes[cnt])
                        mathes_complite[place].append(match_id_olimp)
                    cnt += 1
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                prnts('Exception: Олимп, ошибка при удалении матча ' + str(match_id_olimp) + ':' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
            raise ValueError('start_seeker_bets_olimp:' + str(e))
        except Exception as e:
            set_stat_reqs(stat_reqs, bk_name)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('Exception: Олимп, ошибка при запросе матча ' + str(match_id_olimp) + ': ' +
                  str(e) + ' ' + ps.get_cur_proxy() + ' ' +
                  str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
            time_resp = TIMEOUT_MATCH

            if fail_proxy >= 3:
                ps.rep_cur_proxy(proxies_container[bk_name]['gen_proxi'].next())
                fail_proxy = 0
            else:
                fail_proxy = fail_proxy + 1
                time.sleep(3)
        if place == 'pre':
            time_sleep = max(0, (TIMEOUT_PRE_MATCH - (TIMEOUT_PRE_MATCH_MINUS + time_resp)))
        else:
            time_sleep = max(0, (TIMEOUT_MATCH - (TIMEOUT_MATCH_MINUS + time_resp)))
        if DEBUG:
            pass
            # prnts('Олимп, матч ' + str(match_id_olimp) + '. Время ответа: ' + str(time_resp) + ', запрос через ' + str(time_sleep) + ' ' + ps.get_cur_proxy(), 'hide')
            # prnts('Олимп, матч ' + str(match_id_olimp) + '. Время ответа: ' + str(time_resp) + ', запрос через ' + str(time_sleep) + ' ' + ps.get_cur_proxy())
        n = n + 1
        time.sleep(time_sleep)

def start_seeker_bets_fonbet(bets, match_id_fonbet, proxies_container, pair_mathes, mathes_complite, stat_reqs, arr_fonbet_top_kofs, place):
    global TIMEOUT_MATCH, TIMEOUT_MATCH_MINUS
    global TIMEOUT_PRE_MATCH, TIMEOUT_PRE_MATCH_MINUS
    bk_name = 'fonbet'
    proxy_size = 5
    proxy = []
    i = 0
    while i < proxy_size:
        proxy.append(proxies_container[bk_name]['gen_proxi'].next())
        i = i + 1
    ps = ProxySwitcher(proxy_size, proxy)
    while True:
        try:
            time_resp = get_bets_fonbet(bets, match_id_fonbet, proxies_container[bk_name]['proxy_list'], ps.get_next_proxy(), TIMEOUT_MATCH, pair_mathes, arr_fonbet_top_kofs, place)
            set_stat_reqs(stat_reqs, bk_name, time_resp)
        except FonbetMatchСompleted as e:
            cnt = 0
            prnts(e)
            try:
                for pair_match in pair_mathes:
                    if match_id_fonbet in pair_match:
                        if bets.get(str(match_id_fonbet)):
                            bets.pop(str(match_id_fonbet))
                        prnts('Fonbet (FonbetMatchСompleted), pair mathes remove: ' + str(pair_mathes[cnt]))
                        pair_mathes.remove(pair_mathes[cnt])
                        mathes_complite[place].append(match_id_fonbet)
                    cnt += 1
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                prnts('Exception: Фонбет, ошибка при удалении матча ' + str(match_id_fonbet) + ':' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
            raise ValueError('start_seeker_bets_fonbet:' + str(e))
        except Exception as e:
            set_stat_reqs(stat_reqs, bk_name)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('Exception: Фонбет, ошибка при запросе матча ' + str(match_id_fonbet) + ': ' +
                  str(e) + ' ' + ps.get_cur_proxy() + ' ' +
                  str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
            ps.rep_cur_proxy(proxies_container[bk_name]['gen_proxi'].next())
            time_resp = TIMEOUT_MATCH
        if place == 'live':
            time_sleep = max(0, (TIMEOUT_MATCH - (TIMEOUT_MATCH_MINUS + time_resp)))
        else:
            time_sleep = max(0, (TIMEOUT_PRE_MATCH - (TIMEOUT_PRE_MATCH_MINUS + time_resp)))
        if DEBUG:
            pass
            # prnts(str('Фонбет, матч ' + str(match_id_fonbet) + '. Время ответа: ' + str(time_resp) + ', запрос через ' + str(time_sleep)) + ' ' + ps.get_cur_proxy(), 'hide')
            # prnts(str('Фонбет, матч ' + str(match_id_fonbet) + '. Время ответа: ' + str(time_resp) + ', запрос через ' + str(time_sleep)) + ' ' + ps.get_cur_proxy())
        time.sleep(time_sleep)


def start_seeker_bets(bk_name, def_bk, bets, sport_id, proxies_container, pair_mathes, stat_reqs, arr_matchs, session, place):
    global TIMEOUT_MATCH, TIMEOUT_MATCH_MINUS, pinn_session_data
    api_key = pinn_session_data.get('api_key')
    x_session = pinn_session_data.get('x_session')
    x_device_uuid = pinn_session_data.get('x_device_uuid')
    proxy_size = 5
    proxy = []
    i = 0
    while i < proxy_size:
        proxy.append(proxies_container[bk_name]['gen_proxi'].next())
        i = i + 1
    ps = ProxySwitcher(proxy_size, proxy)

    prnts(bk_name + ', start sport_id: ' + str(sport_id))
    while True:
        try:
            time_resp = def_bk(bets, api_key, x_session, x_device_uuid, pair_mathes, sport_id, proxies_container[bk_name]['gen_proxi'], ps.get_next_proxy(), TIMEOUT_MATCH, arr_matchs, session, place)
            set_stat_reqs(stat_reqs, bk_name, time_resp)
        # TODO Удаления котировок при завершении матча
        # Удалять катировки будем глубще в def_bk?
        except Exception as e:
            set_stat_reqs(stat_reqs, bk_name)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('Exception: ' + bk_name + ', ошибка при запросе котировок по спорту ' + str(sport_id) + ': ' +
                  str(e) + ' ' + ps.get_cur_proxy() + ' ' +
                  str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
            ps.rep_cur_proxy(proxies_container[bk_name]['gen_proxi'].next())
            time_resp = TIMEOUT_MATCH

        time_sleep = max(0, (TIMEOUT_MATCH - (TIMEOUT_MATCH_MINUS + time_resp)))
        if DEBUG:
            pass
            # prnts(str(bk_name + ', матч ' + str(match_id) + '. Время ответа: ' + str(time_resp) + ', запрос через ' + str(time_sleep)) + ' ' + ps.get_cur_proxy(), 'hide')
        time.sleep(time_sleep)


def starter_bets(bets, pair_mathes, mathes_complite, mathes_id_is_work, proxies_container, stat_reqs, arr_fonbet_top_kofs, arr_matchs, session):
    global pinn_session_data, bk_working
    while True:
        matchs_id = None
        for pair_match in pair_mathes:
            # print(pair_match)
            # pair_match: ['55486968', '19530853', 'volleyball', 'live', 'volleyball;55486968;Metallurg (W);Chromtau Women;19530853;Metallurg Temirtau (w);Hromtay (w);', 1.381, 'olimp', 'fonbet']
            match_id_bk1, match_id_bk2, event_type, place, event_name, kof_compare, bk_name1, bk_name2 = pair_match
            
            if bk_name1 == 'olimp':
                matchs_id = match_id_bk1
            elif bk_name2 == 'olimp':
                matchs_id = match_id_bk2
            if 'olimp' in bk_name1+bk_name2:
                if matchs_id:
                    if matchs_id not in mathes_id_is_work:
                        mathes_id_is_work.append(matchs_id)
                        start_seeker_olimp_bets_by_id = threading.Thread(
                            target=start_seeker_bets_olimp,
                            args=(bets, matchs_id, proxies_container, pair_mathes, mathes_complite, stat_reqs, place)
                        )
                        start_seeker_olimp_bets_by_id.start()
                        
            if bk_name1 == 'fonbet':
                matchs_id = match_id_bk1
            elif bk_name2 == 'fonbet':
                matchs_id = match_id_bk2
            if 'fonbet' in bk_name1+bk_name2:
                if matchs_id not in mathes_id_is_work:
                    mathes_id_is_work.append(matchs_id)
    
                    start_seeker_fonbet_bets_by_id = threading.Thread(
                        target=start_seeker_bets_fonbet,
                        args=(bets, matchs_id, proxies_container, pair_mathes, mathes_complite, stat_reqs, arr_fonbet_top_kofs, place))
                    start_seeker_fonbet_bets_by_id.start()
        
            v_bk_name = 'pinnacle'
            if v_bk_name in bk_working:
                # TODO onle exists successfull compare matches
                for sport_arr in sport_list:
                    sport_id = sport_arr.get(v_bk_name)
                    if sport_id and sport_id not in mathes_id_is_work:
                        mathes_id_is_work.append(sport_id)
                        start_seeker_fonbet_bets_by_id = threading.Thread(
                            target=start_seeker_bets,
                            args=('pinnacle', util_pinnacle.get_odds, bets, sport_id, proxies_container, pair_mathes, stat_reqs, arr_matchs, session, place)
                        )
                        start_seeker_fonbet_bets_by_id.start()
        time.sleep(20)


def get_rate(team1_bk1, team2_bk1, team1_bk2, team2_bk2, debug=False):
    if debug:
        fstr = team1_bk1 + '->{};' + team2_bk1 + '->{};' + team1_bk2 + '->{};' + team2_bk2 + '->{};'
    team1_bk1 = str(team1_bk1).lower()
    team2_bk1 = str(team2_bk1).lower()
    team1_bk2 = str(team1_bk2).lower()

    team2_bk2 = str(team2_bk2).lower()

    if 'corners'.lower() in team1_bk1 + team2_bk1 + team1_bk2 + team2_bk2:
        # prnts('corners exclude: ' + team1_bk1 + team2_bk1 + team1_bk2 + team2_bk2, 'hide')
        return 0, 0, 0
    elif 'yellow cards'.lower() in team1_bk1 + team2_bk1 + team1_bk2 + team2_bk2:
        # prnts('yellow cards exclude: ' + team1_bk1 + team2_bk1 + team1_bk2 + team2_bk2, 'hide')
        return 0, 0, 0
    elif team1_bk1 == '' or team2_bk1 == '' or team1_bk2 == '' or team2_bk2 == '':
        # prnts('Название одной из команд не определено, team1_bk1:{}, team2_bk1:{}, team1_bk2:{}, team2_bk2:{}'.format(team1_bk1, team2_bk1, team1_bk2, team2_bk2))
        return 0, 0, 0

    if team1_bk1 and team2_bk1 and team1_bk2 and team2_bk2:
        team1_bk1 = re.sub('[^A-z 0-9]', '', team1_bk1).replace(' ', '')
        team2_bk1 = re.sub('[^A-z 0-9]', '', team2_bk1).replace(' ', '')
        team1_bk2 = re.sub('[^A-z 0-9]', '', team1_bk2).replace(' ', '')
        team2_bk2 = re.sub('[^A-z 0-9]', '', team2_bk2).replace(' ', '')
        if debug:
            fstr = fstr.format(team1_bk1, team2_bk1, team1_bk2, team2_bk2)
            prnts(fstr)

        r1 = round(SequenceMatcher(None, team1_bk1, team1_bk2).ratio(), 3)
        r2 = round(SequenceMatcher(None, team2_bk1, team2_bk2).ratio(), 3)
        rate = round(r1 + r2, 3)

        if debug:
            prnts('k1: {}, k2: {}. All: {}'.format(r1, r2, rate))

        return r1, r2, rate


def start_event_mapping(pair_mathes, arr_matchs, mathes_complite):
    need = 1.5
    prnts('start_event_mapping, need: ' + str(need))
    # for id, js in arr_matchs.items():
    #     print(id, str(js))
    
    while True:
        try:
            pair_bk = list(itertools.combinations(bk_working, 2))
            # print('pair_bk: ' + str(pair_bk))
            # pair_bk.pop(2)
            for bk_name1, bk_name2 in pair_bk:
                not_compare = list()
                pair_mathes_found = dict()
                bk_rate_list = list()
                bk_rate_sorted = list()
                json_bk1_copy = dict()
                json_bk2_copy = dict()
                for j in list(arr_matchs):
                    if arr_matchs[j].get('bk_name', '') == bk_name1:
                        json_bk1_copy[j] = arr_matchs[j]
                    elif arr_matchs[j].get('bk_name', '') == bk_name2:
                        json_bk2_copy[j] = arr_matchs[j]
                for bk1_match_id, bk1_match_info in json_bk1_copy.items():
                    if [bk_name1 for bk_name1 in bk1_match_info.values() if bk_name1 is not None]:
    
                        for bk2_match_id, bk2_match_info in json_bk2_copy.items():
                            if [bk_name2 for bk_name2 in bk2_match_info.values() if bk_name2 is not None]:
                                # Проверим что матч не завершен:
                                if bk1_match_id in mathes_complite.get(bk1_match_info.get('place'), []) or bk2_match_id in mathes_complite.get(bk2_match_info.get('place'), []):
                                    pass
                                else:
    
                                    match_name = str(bk1_match_info.get('sport_name')) + ';' + \
                                                 str(bk1_match_id) + ';' + \
                                                 str(bk1_match_info.get('team1')) + ';' + \
                                                 str(bk1_match_info.get('team2')) + ';' + \
                                                 str(bk2_match_id) + ';' + \
                                                 str(bk2_match_info.get('team1')) + ';' + \
                                                 str(bk2_match_info.get('team2')) + ';'
                                    # print(match_name)
                                    # print(bk2_match_info)
                                    # print(bk2_match_info.get('place'))
                                    # print(bk1_match_info.get('sport_name'), bk2_match_info.get('sport_name') )
                                    if bk1_match_info.get('sport_name') == bk2_match_info.get('sport_name') and bk1_match_info.get('place') == bk2_match_info.get('place'):
                                        place = bk1_match_info.get('place')
                                        r1, r2, rate = get_rate(
                                            bk1_match_info.get('team1', ''),
                                            bk1_match_info.get('team2', ''),
                                            bk2_match_info.get('team1', ''),
                                            bk2_match_info.get('team2', '')
                                        )
                                        deff_time = abs((bk1_match_info.get('start_time') - bk2_match_info.get('start_time')) / 60)
                                        # print(deff_time)
                                        if rate < 2.0 and rate > need and (
                                                (bk1_match_info.get('sport_name') == 'football' and deff_time > 12)
                                                or (bk1_match_info.get('sport_name') == 'hockey' and deff_time > 30)
                                                or (bk1_match_info.get('sport_name') == 'tennis' and deff_time > 40)
                                                or (bk1_match_info.get('sport_name') == 'volleyball' and deff_time > 30)
                                                or (deff_time > 300)
                                        ):
                                            prnts('Обнаружено различие во времени матча: {}, {}, {}'.format(deff_time, match_name, rate))
                                        else:
                                            if rate > 0:
                                                bk_rate_list.append({
                                                    str(bk1_match_id): {
                                                        'bk1_t1': bk1_match_info.get('team1'),
                                                        'bk1_t2': bk1_match_info.get('team2'),
                                                        'rate': r1,
                                                        'sport_name': bk1_match_info.get('sport_name'),
                                                        'place': place,
                                                    },
                                                    str(bk2_match_id): {
                                                        'bk2_t1': bk2_match_info.get('team1'),
                                                        'bk2_t2': bk2_match_info.get('team2'),
                                                        'rate': r2,
                                                        'sport_name': bk2_match_info.get('sport_name'),
                                                        'place': place,
                                                    },
                                                    'rate': rate,
                                                    'match_name': match_name,
                                                    'place': place,
                                                })
                for bkr in bk_rate_list:
                    if bkr.get('rate', 0) > need:
                        bk_rate_sorted.append(bkr)
                    else:
                        if 'del;' + bkr.get('match_name') not in not_compare:
                            serv_log('compare_teams', 'del;' + bkr.get('match_name'))
                            not_compare.append('del;' + bkr.get('match_name'))
                bk_rate_sorted = list(filter(lambda x: x is not None, bk_rate_sorted))
                bk_rate_sorted.sort(key=lambda val: val.get('rate', 0), reverse=True)
                for e in bk_rate_sorted:
                    pair = []
                    # main_rate = e.get('rate', 0)
                    for m, v in e.items():
                        try:
                            if v.get('sport_name'):
                                pair.append(m)
                                if v.get('sport_name') not in pair:
                                    pair.append(v.get('sport_name'))
                                if v.get('place') not in pair:
                                    pair.append(v.get('place'))
                        except:
                            pass
                    pair.sort(key=lambda p: 'z' if p in ('live', 'pre') else p)
                    
                    # print('pair: ' + str(pair))
                    pair = [pair[0], pair[1], pair[2], pair[3]]
                    pair.append(e.get('match_name'))
                    pair.append(e.get('rate'))
                    pair.append(bk_name1)
                    pair.append(bk_name2)
                    # ['55492410', '19534237', 'volleyball', 'live', 'volleyball;55492410;BGPU Minsk (W);Immanuel Kant Baltic Federal University (W);19534237;BGPU Minsk (w);BFU im. I. Kant (w);', 1.298, 'olimp', 'fonbet']
                    
                    if pair[0] in mathes_complite.get(pair[3], []) or pair[1] in mathes_complite.get(pair[3], []):
                        pass
                    else:
                        poz_rate = 5
                        poz_bk1 = -2
                        poz_bk2 = -1
                        if pair not in pair_mathes:
                            print('pair: ' + str(pair))
                            conflict = False
                            is_exists = False
                            for p in pair_mathes:
                                id1, id2 = pair[0], pair[1]
                                if id1 in p:
                                    if float(pair[poz_rate]) > float(p[poz_rate]) and pair[poz_bk1] == p[poz_bk1] and pair[poz_bk2] == p[poz_bk2]:
                                        prnts('Math conflict: ' + str(id1) + ', p: ' + str(p) + ', need: ' + str(pair))
                                        conflict = True
                                    else:
                                        is_exists = True
                                if id2 in p:
                                    if float(pair[poz_rate]) > float(p[poz_rate]) and pair[poz_bk1] == p[poz_bk1] and pair[poz_bk2] == p[poz_bk2]:
                                        prnts('Math conflict: ' + str(id2) + ', p: ' + str(p) + ', need: ' + str(pair))
                                        conflict = True
                                    else:
                                        is_exists = True
                                if conflict:
                                    pair_mathes.remove(p)
                                    serv_log('compare_teams', 'del;' + str(p[poz_rate-1]) + 'conflict')
                                    pair_mathes.append(pair)
                                    serv_log('compare_teams', 'add;' + pair[poz_rate-1] + 'conflict')
                                
                                    pair_key = str(pair[0])+ '-' + str(pair[1])
                                    if not pair_mathes_found.get(pair_key):
                                        pair_mathes_found.update({pair_key: 0})
                            if not conflict and not is_exists:
                                pair_mathes.append(pair)
                                serv_log('compare_teams', 'add;' + pair[poz_rate-1])
                                
                                pair_key = str(pair[0])+ '-' + str(pair[1])
                                if not pair_mathes_found.get(pair_key):
                                    pair_mathes_found.update({pair_key: 0})
                # for x in pair_mathes:
                #     print(x)
                for key in list(pair_mathes_found):
                    if pair_mathes_found.get(key) == 0:
                        prnts('Event add: ' + str(key))
                        pair_mathes_found.update({key: 1})
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('scan error start_event_mapping: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
        finally:
            time.sleep(time_sleep_proc)


def get_forks(forks, forks_meta, pair_mathes, bets, arr_top_matchs, arr_values):
    global opposition
    def forks_meta_upd(forks_meta, forks):
        # Перед удалением сохраним время жизни вылки
        live_fork_total = forks_meta.get(bet_key, {}).get('live_fork_total', 0) + forks.get(bet_key, {}).get('live_fork', 0)
        forks_meta[bet_key] = {'live_fork_total': live_fork_total}

    while True:
        try:
            for pair_math in pair_mathes:

                is_top = 'slag'
                if int(pair_math[0]) in arr_top_matchs.get('top', []) or int(pair_math[1]) in arr_top_matchs.get('top', []):
                    is_top = 'top'
                elif int(pair_math[0]) in arr_top_matchs.get('middle', []) or int(pair_math[1]) in arr_top_matchs.get('middle', []):
                    is_top = 'middle'
                
                # BK1 - old - olimp
                math_json_bk1 = bets.copy().get(pair_math[0], {})
                math_json_bk2 = bets.copy().get(pair_math[1], {})
                event_type = pair_math[2]
                type_time = pair_math[3]  # pre/live
                name_bk1 = pair_math[-2]
                name_bk2 = pair_math[-1]

                curr_opposition = opposition.copy()

                # prnts(pair_math)
                # prnts(math_json_bk1)
                # prnts(math_json_bk2)

                for kof_type in list(math_json_bk1.get('kofs', {})):
                    if '(' in kof_type:
                        tot_abrr = re.sub('\((.*)\)', '', kof_type)
                        tot_val = re.findall('\((.*)\)', kof_type)[0]
                        for opposition_keys in curr_opposition:
                            tot_abrr_opp = opposition_keys.get(tot_abrr)
                            if tot_abrr_opp:
                                if 'Ф' in kof_type:
                                    tot_val_float = float(tot_val)
                                    if tot_val_float > 0:
                                        curr_opposition.append({tot_abrr + '({})'.format(tot_val_float): tot_abrr_opp + '(-{})'.format(tot_val_float)})
                                    else:
                                        curr_opposition.append({tot_abrr + '({})'.format(abs(tot_val_float)): tot_abrr_opp + '({})'.format(tot_val_float)})
                                else:
                                    curr_opposition.append({tot_abrr + '({})'.format(tot_val): tot_abrr_opp + '({})'.format(tot_val)})
                # print(event_type)
                draw_bk1 = math_json_bk1.get('kofs', {}).get('Н', {}).get('value', 0.0)
                draw_bk2 = math_json_bk2.get('kofs', {}).get('Н', {}).get('value', 0.0)
                if event_type in ('volleyball', 'tennis', 'basketball', 'esports', 'table-tennis') and draw_bk1 == 0 and draw_bk2 == 0:
                    curr_opposition.append({'П1': 'П2'})
                    curr_opposition.append({'П2': 'П1'})
                    for pair in add_if_not_draw:
                        curr_opposition.append(pair)
                else:
                    for pair in add_if_draw:
                        curr_opposition.append(pair)
                # if 18967944 == int(pair_math[0]) or 18967944 == int(pair_math[1]):
                for opposition_pair in curr_opposition:
                    for kof_type_bk1, kof_type_bk2 in opposition_pair.items():
                        # print(kof_type_bk1, kof_type_bk2)
                        bet_key = str(pair_math[0]) + '@' + str(pair_math[1]) + '@' + kof_type_bk1 + '@' + kof_type_bk2

                        bk1_start = math_json_bk1.get('start_time', 0)
                        bk2_start = math_json_bk2.get('start_time', 0)
                        start_after_min = max(math_json_bk2.get('start_after_min', 0), math_json_bk1.get('start_after_min', 0))

                        k_bk1 = math_json_bk1.get('kofs', {}).get(kof_type_bk1, {})
                        k_bk2 = math_json_bk2.get('kofs', {}).get(kof_type_bk2, {})
                        
                        v_bk1 = k_bk1.get('value', 0.0) # 1
                        v_bk1_2 = math_json_bk1.get('kofs', {}).get(kof_type_bk2, {}).get('value', 0.0) # X2
                        if v_bk1 and v_bk1_2:
                            v_bk1_margin = round((1/v_bk1+1/v_bk1_2-1) * 100, 2)
                        else:
                            v_bk1_margin = None
                            
                        v_bk2 = k_bk2.get('value', 0.0) # X2
                        v_bk2_2 = math_json_bk2.get('kofs', {}).get(kof_type_bk1, {}).get('value', 0.0) # 1
                        if v_bk2 and v_bk2_2:
                            v_bk2_margin = round((1/v_bk2+1/v_bk2_2-1) * 100, 2)
                        else:
                            v_bk2_margin = None
                            
                        v_name = math_json_bk1.get('name', '')
                        
                        try:
                            if type_time == 'pre' and 1==0:
                            # if event_type in ('football', 'hockey'):
                                # ОП=В*(К-1)*С-(1-В)*С
                                value_arr = [
                                    [v_bk1, v_bk2_2, 'Олимп на {}\nсобытие:' + kof_type_bk1 + '={}\nзавышен ~ на: {}\nожидаемая прибыль: {}%', kof_type_bk1],
                                    [v_bk2, v_bk1_2, 'Фонбет на {}\nсобытие:' + kof_type_bk2 + '={}\nзавышен ~ на: {}\nожидаемая прибыль: {}%', kof_type_bk2], 
                                    # [v_bk2_2, v_bk1, 'Валуйная ставка в\nФонбет на {}\nсобытие:' + kof_type_bk1 + '={}\nзавышен ~ на: {}\nожидаемая прибыль: {}%', kof_type_bk1], 
                                    # [v_bk1_2, v_bk2, 'Валуйная ставка в\nОлимп на {}\nсобытие:' + kof_type_bk2 + '={}\nзавышен ~ на: {}\nожидаемая прибыль: {}%', kof_type_bk2]
                                ]
                                msg = ''
                                for p_vals in value_arr:
                                    K = p_vals[0] # Коф в одной БК
                                    V = p_vals[1] # Коф в другой БК (считаем как нашу вероятность)
                                    if K and V and K <= 2.3 and start_after_min <= 60*20:
                                        # ОП=В*(К-1)*С-(1-В)*С, где
                                        # ОП — ожидаемая прибыль;
                                        # В — математическая вероятность наступления исхода (выражается значением от 0 до 1);
                                        # С — сумма ставки;
                                        # К — котировка события.
                                        B = 1/V
                                        C = 1000
                                        val = round((B*(K-1)*C) -((1-B)*C), 2)
                                        if val >= 150:
                                            if msg!='':
                                                msg = msg + '\n\nили\n\n'
                                            else:
                                                msg = 'Валуйная ставка в\n'
                                            msg = msg + p_vals[2].format(event_type[0:1].upper() + event_type[1:] + ', лига:' + str(is_top) + '\n' + 
                                              v_name + '\n' + 
                                              'Старт через: ' + str(round(start_after_min/60, 1)) + 'ч.',
                                              K, 
                                              round(K-V, 2), 
                                              round(val/C*100, 2)
                                            )
                                            # TODO_REF
                                            # bet_key_values = v_name + ' ' + str(K) + '/' + str(V)
                                            # skolko stavit (КхV-1)/(К-1)=% от банка.
                                if msg != '':
                                    temp_key = v_name+p_vals[3]
                                    if temp_key not in arr_values and msg not in arr_values:
                                        arr_values.append(temp_key)
                                        arr_values.append(msg)
                                        bot.send_msg(msg)
                        except Exception:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            prnts('scan error values: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
                        # print(kof_type_bk2, str(v_bk2), kof_type_bk1, str(v_bk1), sep=";")

                        if DEBUG and (kof_type_bk1 in 'П1' or kof_type_bk2 in 'П1'):
                            pass
                            v_bk1 = v_bk1 * 2
                            v_bk2 = v_bk2 * 2

                        if v_bk1 > 0.0 and v_bk2 > 0.0:

                            bk1_time_req = math_json_bk1.get('time_req', 0)
                            bk2_time_req = math_json_bk2.get('time_req', 0)
                            cur_time = round(time.time())
                            deff_time = max((cur_time - bk1_time_req), (cur_time - bk2_time_req))

                            L = (1 / float(v_bk1)) + (1 / float(v_bk2))

                            if type_time == 'pre':
                                fork_hide_time = TIMEOUT_PRE_MATCH + 4
                            else:
                                fork_hide_time = 4
                            is_fork = True if L < 1 and deff_time < fork_hide_time else False
                            if is_fork:  # or True
                                
                                # TODO ID BK_NAME = FONBET
                                time_break_fonbet = False
                                period = 0

                                if event_type == 'football':
                                    period = 1
                                    if re.match('\(\d+:\d+\)', math_json_bk2.get('score_1st', '').replace(' ', '')) and \
                                            str(math_json_bk2.get('time', '')) == '45:00' and \
                                            round(math_json_bk2.get('minute', ''), 2) == 45.0:
                                        time_break_fonbet = True
                                    elif re.match('\(\d+:\d+\)', math_json_bk2.get('score_1st', '').replace(' ', '')) and \
                                            round(math_json_bk2.get('minute', ''), 2) > 45.0:
                                        period = 2
                                elif event_type in ['basketball', 'volleyball']:
                                    if 'timeout' in math_json_bk2.get('score_1st', '').lower():
                                        time_break_fonbet = True

                                if forks.get(bet_key, '') != '':
                                    live_fork = round(time.time() - forks.get(bet_key, {}).get('create_fork'))
                                    # print('live_fork: ' + str(live_fork))
                                    forks[bet_key].update({
                                        # 'created_fork': created_fork,
                                        'time_last_upd': cur_time,
                                        'name': math_json_bk2.get('name', ''),
                                        'name_rus': v_name,
                                        'time_req_' + name_bk1: bk1_time_req,
                                        'time_req_' + name_bk2: bk2_time_req,
                                        'l': L,
                                        'pair_math': pair_math,
                                        'bk1_score': math_json_bk1.get('score', ''),
                                        'bk2_score': math_json_bk2.get('score', ''),
                                        'time': math_json_bk2.get('time', '00:00'),
                                        'minute': math_json_bk2.get('minute', 0),
                                        'kof_' + name_bk1: k_bk1,
                                        'kof_' + name_bk2: k_bk2,
                                        'time_break_' + name_bk2: time_break_fonbet,
                                        'period': period,
                                        'live_fork': live_fork,
                                        'live_fork_total': forks_meta.get(bet_key, dict()).get('live_fork_total', 0) + live_fork,
                                    })

                                    if True:  # and '46136612' in bet_key:
                                        file_forks = 'forks.csv'

                                        if DEBUG:
                                            pass
                                            prnts('\n')
                                            str_js = json.dumps(forks.get(bet_key), ensure_ascii=False)
                                            prnts('forks: ' + bet_key + ' ' + str(str_js))
                                            prnts('\n')

                                        if not os.path.isfile(file_forks):
                                            with open(file_forks, 'w', encoding='utf-8') as csv:
                                                csv.write(
                                                    'name_bk1;name_bk2;event_type;place;time;time_create;created_fork;cut_time;bk1_time;bk2_time;live_fork;live_fork_total;'
                                                    'match_bk1;match_bk2;name;l;l_first;bk1_score;bk2_score;'
                                                    'vect_bk1;vect_bk2;time;'
                                                    'minute;kof_bk1;bk1_kof_val;kof_bk1_2;bk1_kof2_val;bk1_margin;bk1_avg_change;kof_bk2;bk2_kof_val;kof_bk2_2;bk2_kof2_val;bk2_margin;bk2_avg_change;'
                                                    'time_break_fonbet;is_top;is_hot;base_line;'
                                                    'period;'
                                                    # 'bk1_avg_change_total;bk2_avg_change_total;'
                                                    'bk1_time_change;'
                                                    'bk1_kof_order;'
                                                    'bk2_time_change;'
                                                    'bk2_kof_order;'
                                                    'bk1_start;'
                                                    'bk2_start'
                                                    '\n'
                                                )
                                        else:
                                            with open(file_forks, 'a', encoding='utf-8') as csv:
                                                csv.write(
                                                    name_bk1 + ';' +
                                                    name_bk2 + ';' +
                                                    event_type + ';' +
                                                    type_time + ';' +
                                                    str(datetime.fromtimestamp(int(round(time.time()))).strftime('%d.%m.%Y %H:%M:%S')) + ';' +
                                                    str(datetime.fromtimestamp(int(forks.get(bet_key).get('create_fork'))).strftime('%d.%m.%Y %H:%M:%S')) + ';' +
                                                    str(forks.get(bet_key).get('created_fork')) + ';' +
                                                    str(datetime.fromtimestamp(int(cur_time)).strftime('%d.%m.%Y %H:%M:%S')) + ';' +
                                                    str(datetime.fromtimestamp(int(math_json_bk1.get('time_req', ''))).strftime('%d.%m.%Y %H:%M:%S')) + ';' +
                                                    str(datetime.fromtimestamp(int(math_json_bk2.get('time_req', ''))).strftime('%d.%m.%Y %H:%M:%S')) + ';' +
                                                    str(live_fork) + ';' +
                                                    str(forks_meta.get(bet_key, dict()).get('live_fork_total', 0) + live_fork) + ';' +
                                                    str(bet_key.split('@')[0]) + ';' + str(bet_key.split('@')[1]) + ';' +
                                                    v_name + ';' + str(L) + ';' + str(forks.get(bet_key).get('l_fisrt')) + ';' +
                                                    math_json_bk1.get('score', '') + ';' +
                                                    math_json_bk2.get('score', '') + ';' +
                                                    str(k_bk1.get('vector')) + ';' +
                                                    str(k_bk2.get('vector')) + ';' +
                                                    str(math_json_bk2.get('time', '00:00')) + ';' +
                                                    str(math_json_bk2.get('minute', 0)) + ';' +
                                                    str(bet_key.split('@')[2]) + ';' +
                                                    str(v_bk1) + ';' +
                                                    str(bet_key.split('@')[3]) + ';' +
                                                    str(v_bk1_2) + ';' +
                                                    str(v_bk1_margin) + ';' +
                                                    str(k_bk1.get('hist', {}).get('avg_change', [])) + ';' +
                                                    str(bet_key.split('@')[3]) + ';' +
                                                    str(v_bk2) + ';' +
                                                    str(bet_key.split('@')[2]) + ';' +
                                                    str(v_bk2_2) + ';' +
                                                    str(v_bk2_margin) + ';' +
                                                    str(k_bk2.get('hist', {}).get('avg_change', [])) + ';' +
                                                    str(time_break_fonbet) + ';' +
                                                    str(is_top) + ';' +
                                                    str(k_bk2.get('is_hot', False)) + ';' +
                                                    str(k_bk2.get('base_line', False)) + ';' +
                                                    str(period) + ';' +
                                                    # str(math_json_bk1.get('avg_change_total', [])) + ';' +
                                                    # str(math_json_bk2.get('avg_change_total', [])) + ';' +
                                                    str(k_bk1.get('hist', {}).get('time_change', '')) + ';' +
                                                    str(k_bk1.get('hist', {}).get('order', [])) + ';' +
                                                    str(k_bk2.get('hist', {}).get('time_change', '')) + ';' +
                                                    str(k_bk2.get('hist', {}).get('order', [])) + ';' +
                                                    str(datetime.fromtimestamp(int(bk1_start)).strftime('%d.%m.%Y %H:%M:%S')) + ';' +
                                                    str(datetime.fromtimestamp(int(bk2_start)).strftime('%d.%m.%Y %H:%M:%S')) +
                                                    '\n'
                                                )
                                else:
                                    created_fork = ''
                                    bk1_time_chage = k_bk1.get('hist', {}).get('time_change', 0)
                                    bk2_time_chage = k_bk2.get('hist', {}).get('time_change', 0)
                                    # prnts('{}, {}, {}, {}, {}'.format(event_type, bk2_time_chage, bk1_time_chage, k_bk2, k_bk1))
                                    if bk1_time_chage and bk2_time_chage:
                                        if bk1_time_chage > bk2_time_chage:
                                            created_fork = name_bk1
                                        if bk2_time_chage > bk1_time_chage:
                                            created_fork = name_bk2

                                    forks[bet_key] = {
                                        'name_bk1': name_bk1,
                                        'name_bk2': name_bk2,
                                        'time_last_upd': cur_time,
                                        'start_after_min': start_after_min,
                                        'name': math_json_bk2.get('name', ''),
                                        'name_rus': v_name,
                                        'time_req_' + name_bk1: bk1_time_req,
                                        'time_req_' + name_bk2: bk2_time_req,
                                        'l': L,
                                        'l_fisrt': L,
                                        'pair_math': pair_math,
                                        'bk1_score': math_json_bk1.get('score', ''),
                                        'bk2_score': math_json_bk2.get('score', ''),
                                        'time': math_json_bk2.get('time', '00:00'),
                                        'minute': math_json_bk2.get('minute', 0),
                                        'kof_' + name_bk1: k_bk1,
                                        'kof_' + name_bk2: k_bk2,
                                        'time_break_' + name_bk2: time_break_fonbet,
                                        'period': period,
                                        'live_fork': 0,
                                        'live_fork_total': forks_meta.get(bet_key, dict()).get('live_fork_total', 0),
                                        'create_fork': round(max(bk1_time_chage, bk2_time_chage)),
                                        'created_fork': created_fork,
                                        'is_top': is_top,
                                        'is_hot': k_bk2.get('is_hot'),
                                        'base_line': k_bk2.get('base_line'),
                                        'event_type': event_type,
                                        'fonbet_maxbet_fact': {},
                                        'place': type_time,
                                    }
                            else:
                                try:
                                    # print('del: ' + str(bet_key) + ' fork_hide_time: ' + str(fork_hide_time) + ' deff_time:' + str(deff_time))
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
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('scan error forks: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
        finally:
            time.sleep(1)

def set_stat_reqs(stat_reqs, bk_name, time_resp=None):
    if stat_reqs.get(bk_name) is None:
        stat_reqs[bk_name] = [[], 0]
    else:
        if time_resp:
            stat_reqs[bk_name][0].append(round(time_resp, 2))
        else:
            stat_reqs[bk_name][1] = stat_reqs[bk_name][1] + 1


def stat_req(stat_reqs):
    while True:
        try:
            for bk_name, cnt in stat_reqs.items():
                if cnt:
                    err_cnt = cnt[1]
                    req_cnt = list(cnt[0])
                    if req_cnt:
                        prnts(bk_name + ' cnt:' + str(len(req_cnt)) + 
                              '/' + str(err_cnt) +
                              ' err: ' + str(round(err_cnt / len(req_cnt) * 100)) +
                              '% avg:' + str(round(sum(req_cnt) / len(req_cnt), 2)) +
                              ' max:' + str(max(req_cnt)) +
                              ' mode:' + str(round(find_max_mode(req_cnt), 2)) +
                              ' median:' + str(round(median(req_cnt), 2))
                        )
            time.sleep(time_sleep_proc)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('scan error stat_req: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
            time.sleep(time_sleep_proc/3)


def mon_cupon(arr_cupon):
    global max_min_prematch
    file_name = 'cupon_hist.csv'
    minute = 30
    while True:
        try:
            cur_time = int(round(time.time()))
            curr_id = cupon.get_id()
            df = pd.read_csv(file_name, encoding='utf-8', sep=';')
            df2 = pd.DataFrame(
                {
                    "time": [cur_time],
                    "cupon_id": [curr_id],
                })
            df = df.append(df2, ignore_index=True)
            df.to_csv(file_name, encoding='utf-8', index=False, sep=';')
            id_old = df[(df['time'] >= (cur_time - (60 * minute)))]['cupon_id'].min()
            arr_cupon[0] = str(int((curr_id - id_old) / minute)) + ' куп./мин.\n' + 'Прематч доступен на ' + str(round(max_min_prematch / 60)) + ' ч.'
            prnts('activity ' + str(arr_cupon[0]) + ' coupons per/min')
            time.sleep( (minute * 60 - 20) / 3 )
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            prnts('scan error mon_cupon: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))))
        finally:
            time.sleep(10)


if __name__ == '__main__':
    try:
        if not DEBUG:
            bot.send_msg('Перезапуск сканера...')
        prnts('DEBUG: ' + str(DEBUG))
        prnts('BK WORKING: ' + str(bk_working))
        prnts(str(list(itertools.combinations(bk_working, 2))))
        prnts('SPORT_LIST: ' + str(sport_list))
        prnts('TIMEOUT_LIST: ' + str(TIMEOUT_LIST))
        prnts('TIMEOUT_MATCH: ' + str(TIMEOUT_MATCH))
        prnts('TIMEOUT_MATCH_MINUS: ' + str(TIMEOUT_MATCH_MINUS))
        prnts('TIMEOUT_PRE_MATCHS: ' + str(TIMEOUT_PRE_LIST))
        prnts('TIMEOUT_PRE_MATCH: ' + str(TIMEOUT_PRE_MATCH))
        prnts('TIMEOUT_PRE_MATCH_MINUS: ' + str(TIMEOUT_PRE_MATCH_MINUS))
        prnts('SERVER_IP: ' + str(SERVER_IP))
        prnts('SERVER_PORT: ' + str(SERVER_PORT))
        prnts('time_sleep_proc: ' + str(time_sleep_proc))
        prnts('max_hour_prematch: ' + str(max_min_prematch / 60))
        time.sleep(3)
        
        proxies_container = dict()
        for bk_name in bk_working:
            proxies_container[bk_name] = {}
            proxies_container[bk_name]['proxy_filename'] = bk_name + '.proxy'
            if bk_name in ('olimp', 'pinnacle'):
                proxies_container[bk_name]['proxy_list'] = get_proxy_from_file(proxies_container[bk_name]['proxy_filename'], uniq=False)
            else:
                proxies_container[bk_name]['proxy_list'] = get_proxy_from_file(proxies_container[bk_name]['proxy_filename'])
            proxies_container[bk_name]['gen_proxi'] = createBatchGenerator(get_next_proxy(copy.deepcopy(proxies_container[bk_name]['proxy_list'])))
            
        pinn_session_data = {}
        session = requests.session()
        if 'pinnacle' in bk_working:
            x = 0
            while True:
                try:
                    set_api('pinnacle', proxies_container['pinnacle']['gen_proxi'].next(), session)
                    api_key = pinn_session_data.get('api_key')
                    x_session = pinn_session_data.get('x_session')
                    x_device_uuid = pinn_session_data.get('x_device_uuid')
                    prnts('get api_key from pinnacle: ' + str(api_key))
                    prnts('get x_session(token) from pinnacle: ' + str(x_session))
                    prnts('get x_device_uuid from pinnacle: ' + str(x_device_uuid))
                    prnts('session: ' + str(session) + '\n')
                    if x_session:
                        break
                except Exception as e:
                    x += 1
                    err_msg = 'scan error, set_api: ' + str(e) + ', attempt: ' + str(x)
                    if x > 5:
                        raise ValueError(err_msg)
                    else:
                        prnts(err_msg)
        time.sleep(3)

        proxy_saver = threading.Thread(target=start_proxy_saver, args=(proxies_container, ))
        proxy_saver.start()
        prnts(' ')
        prnts('START: proxy_saver')

        arr_matchs = dict()
        arr_cupon = [0]

        arr_top_matchs = {'top': [], 'middle': [], 'slag': []}
        arr_fonbet_top_kofs = {}
        # Completed Events
        mathes_complite = {'live': [], 'pre': []}
        
        # univers
        bets = dict()
        forks = dict()
        forks_meta = dict()
        stat_reqs = {}
        pair_mathes = []
        
        bk_seeker_matchs = []
        for bk_name in bk_working:
            for place in ['pre', 'live']:
            # for place in ['live']:
                seeker_matchs = threading.Thread(target=start_seeker_matchs, args=(bk_name, proxies_container, arr_matchs, place, session))
                bk_seeker_matchs.append(seeker_matchs)
                seeker_matchs.start()
        time.sleep(4)
        prnts(' ')
        prnts('START: seeker_matchs')
        time.sleep(time_sleep_proc / 3)

        # List of TOP events
        fonbet_seeker_top_matchs = threading.Thread(target=start_seeker_top_matchs_fonbet, args=(proxies_container, arr_top_matchs, pair_mathes, arr_fonbet_top_kofs))
        fonbet_seeker_top_matchs.start()
        prnts(' ')
        prnts('START: fonbet_seeker_top_matchs')
        time.sleep(time_sleep_proc / 3)
        
        # Event mapping
        event_mapping = threading.Thread(target=start_event_mapping, args=(pair_mathes, arr_matchs, mathes_complite))
        event_mapping.start()
        prnts(' ')
        prnts('START: event_mapping')
        time.sleep(time_sleep_proc / 3)
        
        mathes_id_is_work = []
        starter_bets = threading.Thread(
            target=starter_bets, 
            args=(bets, pair_mathes, mathes_complite, mathes_id_is_work, proxies_container, stat_reqs, arr_fonbet_top_kofs, arr_matchs, session)
        )
        starter_bets.start()
        prnts(' ')
        prnts('START: starter_bets')
    
        started_stat_req = threading.Thread(target=stat_req, args=(stat_reqs, ))
        started_stat_req.start()
        prnts(' ')
        prnts('START: started_stat_req')
    
        arr_values = []
        starter_forks = threading.Thread(target=get_forks, args=(forks, forks_meta, pair_mathes, bets, arr_top_matchs, arr_values))
        starter_forks.start()
        prnts(' ')
        prnts('START: starter_forks')
        
        if not DEBUG:
            started_mon_cupon = threading.Thread(target=mon_cupon, args=(arr_cupon,))
            started_mon_cupon.start()
            prnts(' ')
            prnts('START: mon_cupon')

        server = threading.Thread(target=run_server, args=(SERVER_IP, SERVER_PORT, forks, pair_mathes, arr_top_matchs, bets, mathes_complite, arr_cupon))
        server.start()
        prnts(' ')
        prnts('START: server')
        if not DEBUG:
            bot.send_msg('Сканер начал работу.')

        # proxy_saver.join()
        # event_mapping.join()
        # starter_forks.join()
        # started_stat_req.join()
        # # bk_seeker_matchs
        # started_mon_cupon.join()
        # server.join()
        # bot.send_msg('Сканнер выключен')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_msg = str(traceback.format_exception(exc_type, exc_value, exc_traceback))
        prnts('scan error:' + err_msg)
        if not DEBUG:
            bot.send_msg('Сканнер упал с ошибкой: ' + str(e))