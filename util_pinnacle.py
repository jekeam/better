import requests
import utils
import proxy_worker
import exceptions
import datetime
import sys
import traceback
import time
import json

list_matches_head = {
    'accept': 'application/json',
    'content-type': 'application/json',
    # 'origin': 'https://www.pinnacle.com',
    # 'referer': 'https://www.pinnacle.com',
    # 'sec-fetch-mode': 'cors',
    # 'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (WindoWs nt 10.0; wiN64; X64) applewebkiT/537.36 (khTml, liKe gecko) chrome/78.0.3904.108 safari/537.36',
}
url_live = 'https://guest.api.arcadia.pinnacle.com/0.1/sports/{}/matchups/live'
url_pre = 'https://guest.api.arcadia.pinnacle.com/0.1/sports/{}/matchups/'

head_odds = {
    'accept': 'application/json',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ru,en;q=0.9,mg;q=0.8,cy;q=0.7',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    # 'origin': 'https://www.pinnacle.com',
    # 'referer': 'https://www.pinnacle.com/en/',
    # 'sec-fetch-mode': 'cors',
    # 'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (WindoWs nt 10.0; wiN64; X64) applewebkiT/537.36 (khTml, liKe gecko) chrome/78.0.3904.108 safari/537.36',
}
url_live_odds = 'https://guest.api.arcadia.pinnacle.com/0.1/sports/{}/markets/live/straight?primaryOnly=false'  
url_pre_odds = 'https://guest.api.arcadia.pinnacle.com/0.1/sports/{}/markets/straight?primaryOnly=false'  
x_device_uuid_temp = 'f46d6637-4581a07c-36898a69-87694cf6'
# x_session = '8rnHMqfFTy5osJ59q9vytaWgGytFiW0v'


# api_key = requests.get(
#     url='https://www.pinnacle.com/config/app.json',
#     verify=False,
#     timeout=10,
# ).json()['api']['haywire']['apiKey']


def american_to_decimal(odd, status):
    if status != 'open':
        return 0
    if odd:
        if odd > 0:
            return round((odd / 100) + 1, 3)
        elif odd < 0:
            return round(100 / abs(odd) + 1, 3)
        else:
            return 0
    else:
        return None


def straight_normalize(data):
    designations = {'over': 'Б', 'under': 'М', 'home': '1', 'away': '2', 'draw': 'Н', None: ''}
    periods = {1: '1', 2: '2', 0: '', None: ''}
    types = {'team_total': 'Т', 'total': 'Т', 'moneyline': '', 'spread': 'Ф', None: ''}
    sides = {'home': '1', 'away': '2', None: ''}

    norm_designations = lambda x: x if x == 'Н' else 'П' + x
    norm_periods = lambda x: '' if ~x else x if x != '0' else ''

    unit = 'У' if data.get('units', '') == 'Corners' else ''
    try:
        if data.get('type', '') == 'team_total':
            return {norm_periods(data.get('period')) + unit + types[data.get('type')] + designations[data.get('designation')] + sides[data.get('side')] + '({})'.format(data.get('points')).replace('+', ''): data}
        if data.get('type', '') == 'total':
            return {norm_periods(data.get('period')) + unit + types[data.get('type')] + designations[data.get('designation')] + '({})'.format(data.get('points')).replace('+', ''): data}
        if data.get('type', '') == 'moneyline':
            return {unit + norm_designations(designations[data.get('designation')]): data}
        if data.get('type', '') == 'spread':
            return {norm_periods(data.get('period')) + unit + types[data.get('type')] + designations[data.get('designation')] + '({})'.format(
                '+' + str(data.get('points', '')) if data.get('points') > 0 != '-' else data.get('points')).replace('+', ''): data}
        else:
            return {}
    except Exception as e:
        return {'error': str(e)}


def get_matches(bk_name, proxy, timeout, api_key, x_session, x_device_uuid, proxy_list, session):
    if bk_name == 'pinnacle':
        head = list_matches_head
    if api_key:
        head.update({'x-api-key': api_key})
    if x_device_uuid:        
        head.update({'x-device-uuid': x_device_uuid})
    if x_session:
        head.update({'x-session': x_session})
    if 'live' == 'live':
        url = url_live
    else:
        url = url_pre
    proxies = {'https': proxy}
    data = {}
    for sport in utils.sport_list:
        sport_id = sport.get('pinnacle')
        sport_name = sport.get('name')
        if sport_id:
            try:
                if session:
                    # utils.prnts('session get_matches: ' + str(session))
                    resp = session.get(
                        url.format(sport_id),
                        headers=head,
                        timeout=timeout,
                        verify=False,
                        proxies=proxies,
                    )
                else:
                    resp = requests.get(
                        url.format(sport_id),
                        headers=head,
                        timeout=timeout,
                        verify=False,
                        proxies=proxies,
                    )
                # print('get_matches head: ' + str(head))
                try:
                    res = resp.json()
                    # {'detail': 'The requested URL was not found on the server.  If you entered the URL manually please check your spelling and try again.', 'status': 404, 'title': 'Not Found', 'type': 'about:blank'}
                    # print(json.dumps(res))
                    # print('---')
                    res_status = 200
                    if type(res) != list:
                        res_status = res.get('status', 404)
                    if res_status != 200:
                        err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error, res_status: ' + str(res_status) + ', res: ' + str(res)
                        utils.prnts(err_str)
                        pass
                    else:
                        for l in filter(
                                lambda x: (
                                                  x.get('league', {}).get('sport', {}).get('name', '') != 'Hockey' and x.get('liveMode', '') == 'live_delay'
                                                  and x.get('units', '') == 'Regular'  # разкомментить для удаления угловых
                                                  and (x.get('parent') if x.get('parent') else {}).get('participants', [{}])[0].get('name', '') == x.get('participants', [{}])[0].get('name', '')
                                                  # закомментить для добавления сетов и геймов
                                          ) or (x.get('league', {}).get('sport', {}).get('name', '') == 'Hockey'),
                                res):
                            if str(l.get('id')) in '123':
                                print(json.dumps(l))
                            # {'ageLimit': 0, 'altTeaser': False, 'external': {}, 'hasLive': True, 'hasMarkets': True, 'id': 1094249412, 'isHighlighted': False, 'isLive': True, 'isPromoted': False, 
                            # 'league': {'ageLimit': 0, 'external': {}, 'featureOrder': -1, 'group': 'World', 'id': 1863, 'isFeatured': False, 'isHidden': False, 'isPromoted': False, 'isSticky': False, 
                            # 'matchupCount': 3, 'name': 'Club Friendlies', 'sport': {'featureOrder': 0, 'id': 29, 'isFeatured': True, 'isHidden': False, 'isSticky': False, 'matchupCount': 532, 
                            # 'name': 'Soccer', 'primaryMarketType': 'moneyline'}}, 'liveMode': 'live_delay', 'parent': {'id': 1094249362, 'participants': [{'alignment': 'home', 'name': 'Club Sport Emelec', 'score': None}, 
                            # {'alignment': 'away', 'name': 'LDU de Portoviejo', 'score': None}], 'startTime': '2020-01-31T01:30:00+00:00'}, 'parentId': 1094249362, 'parlayRestriction': 'unique_matchups', 'participants':
                            # [{'alignment': 'home', 'name': 'Club Sport Emelec', 'order': 0, 'state': {'score': 2}}, {'alignment': 'away', 'name': 'LDU de Portoviejo', 'order': 1, 'state': {'score': 0}}], 
                            # 'periods': [{'cutoffAt': '2020-01-31T04:14:42Z', 'period': 0, 'status': 'open'}, {'cutoffAt': None, 'period': 1, 'status': 'settled'}], 'rotation': 1301, 'startTime': '2020-01-31T01:30:00Z',
                            # 'state': {'minutes': 39, 'state': 3}, 'status': 'started', 'totalMarketCount': 2, 'type': 'matchup', 'units': 'Regular', 'version': 256440882}
                            participants = l.get('participants', [{}])
                            participant_0 = participants[0]
                            participant_1 = participants[1]
                            if participant_0.get('alignment') == 'home':
                                team1 = participant_0.get('name')
                                score1 = participant_0.get('state', {}).get('score', participant_0.get('score'))
                                team2 = participant_1.get('name')
                                score2 = participant_1.get('state', {}).get('score', participant_1.get('score'))
                            elif participant_0.get('alignment') == 'away':
                                team2 = participant_0.get('name')
                                score2 = participant_0.get('state', {}).get('score', participant_0.get('score'))
                                team1 = participant_1.get('name')
                                score1 = participant_1.get('state', {}).get('score', participant_1.get('score'))
                            data[l.get('id')] = {
                                'time_req': int(datetime.datetime.now().timestamp()),
                                'bk_name': bk_name,
                                'match_id': l.get('id'),
                                'league': l.get('league', {}).get('group') + '-' + l.get('league', {}).get('name'),
                                'team1': team1,
                                'team2': team2,
                                'name': team1 + '-' + team2,
                                'score': str(score1) + ':' + str(score2),
                                'state': l.get('state', {}).get('state'),
                                'minute': float(l.get('state', {}).get('minutes', 0)),
                                'sport_id': sport_id,
                                'sport_name': sport_name,
                                'start_timestamp': int(datetime.datetime.strptime(l.get('startTime'), '%Y-%m-%dT%H:%M:%SZ').timestamp()),
                                'units': l.get('units'),
                                'liveMode': l.get('liveMode')
                            }
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                    utils.prnts(err_str)
                    raise ValueError('Exception: ' + str(e))
                if resp.status_code != 200:
                    err_str = res.get("error")
                    err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error : ' + str(err_str)
                    utils.prnts(err_str)
                    raise ValueError(str(err_str))

            except requests.exceptions.Timeout as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                utils.prnts(err_str)
                proxies = proxy_worker.del_proxy(proxy, proxy_list)
                raise exceptions.TimeOut(err_str)
            except requests.exceptions.ConnectionError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                utils.prnts(err_str)
                proxies = proxy_worker.del_proxy(proxy, proxy_list)
                raise ValueError(err_str)
            except requests.exceptions.RequestException as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                utils.prnts(err_str)
                proxies = proxy_worker.del_proxy(proxy, proxy_list)
                raise ValueError(err_str)
            except ValueError as e:
                if resp.text:
                    text = resp.text
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error1: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                utils.prnts(err_str)
                proxi_list = proxy_worker.del_proxy(proxy, proxy_list)
                raise ValueError(err_str)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                utils.prnts(err_str)
                proxies = proxy_worker.del_proxy(proxy, proxy_list)
                raise ValueError(err_str)
    return data, resp.elapsed.total_seconds()


MAX_VERSION = {}


def get_odds(bets, api_key, x_session, x_device_uuid, pair_mathes, sport_id, proxi_list, proxy, timeout, arr_matchs, session):
    global MAX_VERSION
    match_id_list = []
    bk_mame = 'pinnacle'
    for pair_math in pair_mathes:
        bk_name1 = pair_math[-2]
        match_id1 = pair_math[0]
        bk_name2 = pair_math[-1]
        match_id2 = pair_math[1]
        if bk_name1 == bk_mame and match_id1 not in match_id_list:
            match_id_list.append(match_id1)
        elif bk_name2 == bk_mame and match_id2 not in match_id_list:
            match_id_list.append(match_id2)
    # print('match_id_list: ' + str(match_id_list))

    # head = head_odds
    head = list_matches_head
    if api_key:
        pass
        head.update({'x-api-key': api_key})
    if x_device_uuid:        
        pass
        head.update({'x-device-uuid': x_device_uuid})
    if x_session:
        pass
        head.update({'x-session': x_session})
    if 'live' == 'live':
        url = url_live_odds
    else:
        url = url_pre_odds
    proxies = {'https': proxy}
    data = {}
    # print('get_odds head: ' + str(head))
    if session:
        # utils.prnts('session get_odds: ' + str(session))
        resp = session.get(
            url.format(sport_id),
            # 'http://192.168.1.143:8888/',
            headers=head,
            timeout=timeout,
            verify=False,
            proxies=proxies,
        )
    else:
        resp = requests.get(
            url.format(sport_id),
            # 'http://192.168.1.143:8888/',
            headers=head,
            timeout=timeout,
            verify=False,
            proxies=proxies,
        )
    data = resp.json()
    # print('data:' + str(resp.text)[0:300])
    # {'detail': 'API key is not valid', 'status': 403, 'title': 'BAD_APIKEY', 'type': 'about:blank'}
    # {'detail': 'Session superseded by a login on another device', 'status': 401, 'title': 'AUTH_SUPERSEDED', 'type': 'about:blank'} -- SESSION EXPIRED
    if type(data) == dict and data.get('status'):
        utils.prnts('data: ' + str(data))
        title_err = data.get('title')
        if title_err == 'BAD_APIKEY':
            utils.prnts('api_key: ' + str(api_key))
        elif title_err == 'AUTH_SUPERSEDED':
            utils.prnts('Session expired! TODO: relogin')

    for match_id in match_id_list:
        check_vertion = True
        res = {}
        version = None
        # print('match_id: ' + str(match_id))
        for bet in filter(lambda x: x['matchupId'] == int(match_id), data):
            version = bet.get('version', -1)
            if str(match_id) == '123':
                print(json.dumps(bet))
            if (check_vertion and version > MAX_VERSION.get(str(sport_id), 0)) or not check_vertion:
                MAX_VERSION.update({str(sport_id): version})
                for price in bet.get('prices', []):
                    status = bet.get('status')
                    # if status == 'open':
                    # v_kof = str(price.get('price')) + ' -> ' + str(american_to_decimal(price.get('price'), status))
                    v_kof = str(american_to_decimal(price.get('price'), status))
                    # else:
                        # v_kof = 0
                    res.update(straight_normalize({
                        'time_req': round(time.time()),
                        'match_id': match_id,
                        # 'name': arr_matchs.get(match_id, {}).get('name', ''),
                        'type': bet.get('type'),
                        'status': status,
                        'side': bet.get('side'),
                        'period': bet.get('period'),
                        'designation': price.get('designation'),
                        'points': price.get('points'),
                        'value': v_kof,
                        'version': version,
                        # 'units':res[match_id]['units'], Нужно для угловых - они отключены
                        # 'vector':'UP' if price.get('price') > 0 else 'DOWN'
                    }))
                    # print('res: ' + str(res))
        if version and check_vertion:
            if version < MAX_VERSION.get(str(sport_id), 0):
                print('sport_id:{}, get version is old: {}, max:{}'.format(sport_id, version, MAX_VERSION.get(str(sport_id), 0)))
        if not bets.get(str(match_id)):
            bets[str(match_id)] = {}
        # bets[str(match_id)]['time_req'] = round(time.time())
        if res:
            bets[str(match_id)]['kofs'] = res
            if arr_matchs.get(match_id, {}):
                bets[str(match_id)].update(arr_matchs.get(match_id, {}))
            bets[str(match_id)]['kofs'] = res
            # print(bets)
            # time.sleep(5)
            # print('----')
    return resp.elapsed.total_seconds()
