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
from utils import prnts, DEBUG, find_max_mode, opposition, MINUTE_COMPLITE
from proxy_switcher import ProxySwitcher
import json
import os.path
import os
from statistics import median
from datetime import datetime

import sys
import traceback

TIMEOUT_MATCHS = 10
TIMEOUT_MATCH = 10
TIMEOUT_MATCH_MINUS = 9

prnts('TIMEOUT_MATCHS: ' + str(TIMEOUT_MATCHS))
prnts('TIMEOUT_MATCH: ' + str(TIMEOUT_MATCH))
prnts('TIMEOUT_MATCH_MINUS: ' + str(TIMEOUT_MATCH_MINUS))
prnts('MINUTE_COMPLITE: ' + str(MINUTE_COMPLITE))


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
    global TIMEOUT_MATCHS
    proxy = gen_proxi_olimp.next()
    while True:
        try:
            resp, time_resp = get_matches_olimp(proxies, proxy, TIMEOUT_MATCHS)
            get_olimp(resp, arr_matchs)
        except TimeOut as e:
            proxy = gen_proxi_olimp.next()
            err_str = 'Timeout: Олимп, ошибка призапросе списока матчей'
            prnts(err_str)
            time_resp = TIMEOUT_MATCHS
        except Exception as e:
            proxy = gen_proxi_olimp.next()
            prnts('Exception: Олимп, ошибка при запросе списка матчей: ' + str(e) + ' ' + proxy)
            time_resp = TIMEOUT_MATCHS

        time_sleep = max(0, (TIMEOUT_MATCHS - time_resp))

        if DEBUG:
            pass
            # prnts('Олимп, поиск матчей, время ответа: ' + str(time_resp) + ', запрос через ' +
            #       str(time_sleep) + ' ' + proxy)

        time.sleep(time_sleep)


def start_seeker_matchs_fonbet(proxies, gen_proxi_fonbet, arr_matchs):
    global TIMEOUT_MATCHS
    proxy = gen_proxi_fonbet.next()
    while True:
        try:
            resp, time_resp = get_matches_fonbet(proxies, proxy, TIMEOUT_MATCHS)
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


def start_seeker_bets_olimp(bets_olimp, match_id_olimp, proxies_olimp, gen_proxi_olimp,
                            pair_mathes, mathes_complite, stat_req_ol):
    global TIMEOUT_MATCH, TIMEOUT_MATCH_MINUS

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
            ps.rep_cur_proxy(gen_proxi_olimp.next())
            time_resp = TIMEOUT_MATCH

        time_sleep = max(0, (TIMEOUT_MATCH - abs(TIMEOUT_MATCH_MINUS + time_resp)))

        if DEBUG:
            prnts('Олимп, матч ' + str(match_id_olimp) + '. Время ответа: ' + str(time_resp) +
                  ', запрос через ' + str(time_sleep) + ' ' + ps.get_cur_proxy())

        time.sleep(time_sleep)


def start_seeker_bets_fonbet(bets_fonbet, match_id_fonbet, proxies_fonbet, gen_proxi_fonbet,
                             pair_mathes, mathes_complite, stat_req_fb):
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
            time_resp = get_bets_fonbet(bets_fonbet, match_id_fonbet, proxies_fonbet,
                                        ps.get_next_proxy(), TIMEOUT_MATCH, pair_mathes)
            stat_req_fb.append(round(time_resp, 2))
        except FonbetMatchСompleted as e:
            cnt = 0
            for pair_match in pair_mathes:
                if match_id_fonbet in pair_match:
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


def starter_bets(
        bets_olimp,
        bets_fonbet,
        pair_mathes,
        mathes_complite,
        mathes_id_is_work,
        proxies_olimp,
        gen_proxi_olimp,
        proxies_fonbet,
        gen_proxi_fonbet,
        stat_req_olimp,
        stat_req_fonbet
):
    while True:
        for pair_match in pair_mathes:
            match_id_olimp, match_id_fonbet = pair_match

            if match_id_olimp not in mathes_id_is_work:
                mathes_id_is_work.append(match_id_olimp)

                start_seeker_olimp_bets_by_id = threading.Thread(
                    target=start_seeker_bets_olimp,
                    args=(bets_olimp, match_id_olimp, proxies_olimp, gen_proxi_olimp,
                          pair_mathes, mathes_complite, stat_req_olimp)
                )
                start_seeker_olimp_bets_by_id.start()

            if match_id_fonbet not in mathes_id_is_work:
                mathes_id_is_work.append(match_id_fonbet)

                start_seeker_fonbet_bets_by_id = threading.Thread(
                    target=start_seeker_bets_fonbet,
                    args=(bets_fonbet, match_id_fonbet, proxies_fonbet, gen_proxi_fonbet,
                          pair_mathes, mathes_complite, stat_req_fonbet)
                )
                start_seeker_fonbet_bets_by_id.start()

        time.sleep(5)


def compare_teams(team1_bk1, team2_bk1, team1_bk2, team2_bk2):
    if team1_bk1 and team2_bk1 and team1_bk2 and team2_bk2:
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


def start_compare_matches(pair_mathes, json_bk1, json_bk2, mathes_complite):
    while True:
        try:
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
                                    # Проверим что матч не завершен:
                                    if bk1_match_id in mathes_complite or bk2_match_id in mathes_complite:
                                        # prnts('Матчи завершены: ' + str(bk1_match_id) + '-' + str(bk2_match_id))
                                        pass
                                    else:
                                        if compare_teams(
                                                bk1_match_info.get('team1'),
                                                bk1_match_info.get('team2'),
                                                bk2_match_info.get('team1'),
                                                bk2_match_info.get('team2')
                                        ):
                                            if DEBUG and str(bk2_match_id) == '13706718':
                                            #if 1==0:
                                                prnts(
                                                    'Матч добавлен: ' + str(bk1_match_id) + ' ' +
                                                    bk1_match_info.get('team1') + ' vs ' +
                                                    bk1_match_info.get('team2') + ' | ' +
                                                    str(bk2_match_id) + ' ' +
                                                    bk2_match_info.get('team1') + ' vs ' +
                                                    bk2_match_info.get('team2')
                                                )
                                                pair_mathes.append([bk1_match_id, bk2_match_id])
                                            #elif not DEBUG:
                                            elif 1==0:
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


def get_forks(forks, forks_meta, pair_mathes, bets_olimp, bets_fonbet):
    global opposition

    def forks_meta_upd(forks_meta, forks):
        # Перед удалением сохраним время жизни вылки
        live_fork_total = forks_meta.get(bet_key, {}).get('live_fork_total', 0) + \
                          forks.get(bet_key, {}).get('live_fork', 0)
        forks_meta[bet_key] = {'live_fork_total': live_fork_total}

    while True:
        for key, val in forks.copy().items():
            if round(float(time.time() - float(val.get('time_req_olimp', 0)))) > 8 or \
                    round(float(time.time() - float(val.get('time_req_fonbet', 0)))) > 8:
                try:
                    forks_meta_upd(forks_meta, forks)
                    forks.pop(key)
                    prnts('Данные по вилке из БК не получены более 8 сек., вилка удалена: ' + str(key))
                    prnts(str(val), 'hide')
                except Exception as e:
                    prnts(e)
                    pass

        for pair_math in pair_mathes:

            math_json_olimp = bets_olimp.get(pair_math[0], {})
            math_json_fonbet = bets_fonbet.get(pair_math[1], {})

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

                if DEBUG:
                    v_olimp = v_olimp + 1
                    v_fonbet = v_fonbet + 1

                if v_olimp > 0.0 and v_fonbet > 0.0:
                    L = (1 / float(v_olimp)) + (1 / float(v_fonbet))
                    is_fork = True if L < 1 else False

                    if is_fork:  # or True
                        time_break_fonbet = False
                        period = 1
                        if re.match('\([\d|\d\d]:[\d|\d\d]\)', math_json_fonbet.get('score_1st', '')) and \
                                str(math_json_fonbet.get('time', '')) == '45:00' and \
                                round(math_json_fonbet.get('minute', ''), 2) == 45.0:
                            time_break_fonbet = True
                        elif re.match('\([\d|\d\d]:[\d|\d\d]\)', math_json_fonbet.get('score_1st', '')) and \
                                round(math_json_fonbet.get('minute', ''), 2) > 45.0:
                            period = 2

                        if forks.get(bet_key, '') != '':

                            live_fork = round(time.time() - forks.get(bet_key, {}).get('create_fork'))

                            forks[bet_key].update({
                                'time_last_upd': round(time.time()),
                                'name': math_json_olimp.get('name', ''),
                                'time_req_olimp': math_json_olimp.get('time_req', 0),
                                'time_req_fonbet': math_json_fonbet.get('time_req', 0),
                                'l': L,
                                'pair_math': pair_math,
                                'bk1_score': math_json_olimp.get('score', ''),
                                'bk2_score': math_json_fonbet.get('score', ''),
                                'time': math_json_fonbet.get('time', '0:0'),
                                'minute': math_json_fonbet.get('minute', 0),
                                'kof_olimp': k_olimp,
                                'kof_fonbet': k_fonbet,
                                'time_break_fonbet': time_break_fonbet,
                                'period': period,
                                'ol_time_change_total': math_json_olimp.get('time_change_total', 0),
                                'ol_avg_change_total': math_json_olimp.get('avg_change_total', []),
                                'fb_time_change_total': math_json_fonbet.get('time_change_total', 0),
                                'fb_avg_change_total': math_json_fonbet.get('avg_change_total', []),
                                'live_fork': live_fork,
                                'live_fork_total': forks_meta.get(bet_key, dict()).get('live_fork_total', 0) + live_fork

                            })

                            if True:
                                if True:  # and '46136612' in bet_key:
                                    file_forks = 'forks.csv'

                                    prnts('\n')
                                    str_js = json.dumps(forks.get(bet_key), ensure_ascii=False)
                                    prnts('forks: ' + bet_key + ' ' + str(str_js))
                                    prnts('\n')

                                    if not os.path.isfile(file_forks):
                                        with open(file_forks, 'w', encoding='utf-8') as csv:
                                            csv.write(
                                                'create_fork;cut_time;ol_time;fb_time;live_fork;live_fork_total;'
                                                'match_ol;match_fb;kof_ol;kof_fb;name;l;bk1_score;bk2_score;'
                                                'vect_ol;vect_fb;time;'
                                                'minute;ol_kof;ol_avg_change;fb_kof;fb_avg_change;'
                                                'time_break_fonbet;'
                                                'period;'
                                                'ol_avg_change_total;fb_avg_change_total;'
                                                'ol_hist1;ol_hist2;ol_hist3;ol_hist4;ol_hist5;'
                                                'fb_hist1;fb_hist2;fbl_hist3;fb_hist4;fb_hist5'
                                                '\n'
                                            )
                                    if os.path.isfile(file_forks):
                                        with open(file_forks, 'a', encoding='utf-8') as csv:
                                            csv.write(
                                                str(forks.get(bet_key).get('create_fork')) + ';' +
                                                str(round(time.time())) + ';' +
                                                str(math_json_olimp.get('time_req', '')) + ';' +
                                                str(math_json_fonbet.get('time_req', '')) + ';' +
                                                str(live_fork) + ';' +
                                                str(forks_meta.get(bet_key, dict()).get('live_fork_total', 0)
                                                    + live_fork) + ';' +
                                                str(bet_key.split('@')[0]) + ';' + str(bet_key.split('@')[1]) + ';' +
                                                str(bet_key.split('@')[2]) + ';' + str(bet_key.split('@')[3]) + ';' +
                                                math_json_olimp.get('name', '') + ';' + str(L) + ';' +
                                                math_json_olimp.get('score', '') + ';' +
                                                math_json_fonbet.get('score', '') + ';' +
                                                str(k_olimp.get('vector')) + ';' +
                                                str(k_fonbet.get('vector')) + ';' +
                                                str(math_json_fonbet.get('time', '0:0')) + ';' +
                                                str(math_json_fonbet.get('minute', 0)) + ';' +
                                                str(k_olimp.get('value')) + ';' +
                                                str(k_olimp.get('hist', {}).get('avg_change', [])) + ';' +
                                                str(k_fonbet.get('value')) + ';' +
                                                str(k_fonbet.get('hist', {}).get('avg_change', [])) + ';' +
                                                str(time_break_fonbet) + ';' +
                                                str(period) + ';' +
                                                str(math_json_olimp.get('avg_change_total', [])) + ';' +
                                                str(math_json_fonbet.get('avg_change_total', [])) + ';' +
                                                str(k_olimp.get('hist', {}).get('1', [])) + ';' +
                                                str(k_olimp.get('hist', {}).get('2', [])) + ';' +
                                                str(k_olimp.get('hist', {}).get('3', [])) + ';' +
                                                str(k_olimp.get('hist', {}).get('4', [])) + ';' +
                                                str(k_olimp.get('hist', {}).get('5', [])) + ';' +
                                                str(k_fonbet.get('hist', {}).get('1', [])) + ';' +
                                                str(k_fonbet.get('hist', {}).get('2', [])) + ';' +
                                                str(k_fonbet.get('hist', {}).get('3', [])) + ';' +
                                                str(k_fonbet.get('hist', {}).get('4', [])) + ';' +
                                                str(k_fonbet.get('hist', {}).get('5', [])) +
                                                '\n'
                                            )
                        else:

                            ol_time_req = math_json_olimp.get('time_req', 0)
                            fb_time_req = math_json_fonbet.get('time_req', 0)

                            forks[bet_key] = {
                                'time_last_upd': round(time.time()),
                                'name': math_json_olimp.get('name', ''),
                                'time_req_olimp': ol_time_req,
                                'time_req_fonbet': fb_time_req,
                                'l': L,
                                'pair_math': pair_math,
                                'bk1_score': math_json_olimp.get('score', ''),
                                'bk2_score': math_json_fonbet.get('score', ''),
                                'time': math_json_fonbet.get('time', '0:0'),
                                'minute': math_json_fonbet.get('minute', 0),
                                'kof_olimp': k_olimp,
                                'kof_fonbet': k_fonbet,
                                'time_break_fonbet': time_break_fonbet,
                                'period': period,
                                'live_fork': 0,
                                'live_fork_total': forks_meta.get(bet_key, dict()).get('live_fork_total', 0),
                                'create_fork': round(max(ol_time_req, fb_time_req))
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
        time.sleep(3)


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
        time.sleep(15)


if __name__ == '__main__':
    prnts('DEBUG: ' + str(DEBUG))
    proxy_filename_olimp = 'olimp.proxy'
    proxy_filename_fonbet = 'fonbet.proxy'

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
    mathes_complite = []

    # json by bets math
    bets_fonbet = dict()
    bets_olimp = dict()

    forks = dict()
    forks_meta = dict()

    stat_req_olimp = []
    stat_req_fonbet = []

    olimp_seeker_matchs = threading.Thread(
        target=start_seeker_matchs_olimp,
        args=(proxies_olimp, gen_proxi_olimp, arr_olimp_matchs)
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
        args=(pair_mathes, arr_olimp_matchs, arr_fonbet_matchs, mathes_complite)
    )
    compare_matches.start()

    mathes_id_is_work = []
    starter_bets = threading.Thread(
        target=starter_bets,
        args=(
            bets_olimp,
            bets_fonbet,
            pair_mathes,
            mathes_complite,
            mathes_id_is_work,
            proxies_olimp,
            gen_proxi_olimp,
            proxies_fonbet,
            gen_proxi_fonbet,
            stat_req_olimp,
            stat_req_fonbet
        )
    )
    starter_bets.start()

    time.sleep(15)

    starter_forks = threading.Thread(target=get_forks, args=(forks, forks_meta, pair_mathes, bets_olimp, bets_fonbet))
    starter_forks.start()

    started_stat_req = threading.Thread(target=stat_req, args=(stat_req_olimp, stat_req_fonbet))
    started_stat_req.start()

    server = threading.Thread(target=run_server, args=(forks,))
    server.start()

    proxy_saver.join()
    olimp_seeker_matchs.join()
    fonbet_seeker_matchs.join()
    compare_matches.join()
    starter_forks.join()
    started_stat_req.join()
    server.join()
