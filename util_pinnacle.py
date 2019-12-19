import requests
import utils
import proxy_worker
import exceptions
import datetime
import sys
import traceback
import time

list_matches_head = {
    'accept': 'application/json',
    'content-type': 'application/json',
    'origin': 'https://www.pinnacle.com',
    'referer': 'https://www.pinnacle.com',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'x-api-key': 'app_key'
}
list_matches_url = 'https://guest.api.arcadia.pinnacle.com/0.1/sports/{}/matchups/live'

head_odds = {
    'accept': 'application/json',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://www.pinnacle.com',
    'pragma': 'no-cache',
    'referer': 'https://www.pinnacle.com/en/soccer/matchups/live',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'x-api-key': 'app_key'
}
url_odds = 'https://guest.api.arcadia.pinnacle.com/0.1/sports/{}/markets/live/straight?primaryOnly=false'


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
            return round((100 / odd) + 1, 3)
        else:
            return 0
    else:
        return None


def straight_normalize(data):
    designations = {'over': 'Б', 'under': 'М', 'home': '1', 'away': '2', 'draw': 'Н', None: ''}
    periods = {1: '1', 2: '2', 0: '', None: ''}
    types = {'team_total': 'ИТ', 'total': 'Т', 'moneyline': '', 'spread': 'Ф', None: ''}
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


def get_matches(bk_name, proxy, timeout, api_key, proxy_list):
    if bk_name == 'pinnacle':
        head = list_matches_head
        head.update({'x-api-key': api_key})
        url = list_matches_url
    proxies = {'https': proxy}
    data = {}
    for sport in utils.sport_list:
        sport_id = sport.get('pinnacle')
        sport_name = sport.get('name')
        if sport_id:
            try:
                resp = requests.get(
                    url.format(sport_id),
                    headers=head,
                    timeout=timeout,
                    verify=False,
                    proxies=proxies,
                )
                try:
                    res = resp.json()
                    # {'detail': 'The requested URL was not found on the server.  If you entered the URL manually please check your spelling and try again.', 'status': 404, 'title': 'Not Found', 'type': 'about:blank'}
                    res_status = 200
                    # print(type(res))
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
                                                  and x.get('parent', {}).get('participants', [{}])[0].get('name', '') == x.get('participants', [{}])[0].get('name', '')
                                                  # закомментить для добавления сетов и геймов
                                          ) or (x.get('league', {}).get('sport', {}).get('name', '') == 'Hockey'),
                                res):
                            data[l.get('id')] = {
                                'bk_name': bk_name,
                                'match_id': l.get('id'),
                                'league': l.get('league', {}).get('group') + '-' + l.get('league', {}).get('name'),
                                'team_alignment1': l.get('participants', [{}])[0].get('alignment'),
                                'team1': l.get('participants', [{}])[0].get('name'),
                                'team_alignment2': l.get('participants', [{}, {}])[1].get('alignment'),
                                'team2': l.get('participants', [{}, {}])[1].get('name'),
                                'name': l.get('participants', [{}, {}])[0].get('name') + '-' + l.get('participants', [{}, {}])[0].get('name'),
                                'score': str(l.get('participants', [{}, {}])[0].get('score')) + ':' + str(l.get('participants', [{}, {}])[0].get('score')),
                                'state': l.get('state', {}).get('state'),
                                'minute': float(l.get('state', {}).get('minutes', 0)),
                                'cur_time': int(datetime.datetime.now().timestamp()),
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


MAX_VERSION = 0


def get_odds(bets, api_key, pair_mathes, sport_id, proxi_list, proxy, timeout):
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

    head = head_odds
    head.update({'x-api-key': api_key})
    url = url_odds
    proxies = {'https': proxy}
    data = {}

    resp = requests.get(
        url.format(sport_id),
        headers=head,
        timeout=timeout,
        verify=False,
        proxies=proxies,
    )
    data = resp.json()
    # print('data' + str(data))

    for match_id in match_id_list:
        res = {}
        # print('match_id: ' + str(match_id))
        for bet in filter(lambda x: x['matchupId'] == int(match_id), data):
            # print('bet: ' + str(bet))
            for price in bet.get('prices', []):
                version = bet.get('version')
                if version > MAX_VERSION:
                    MAX_VERSION = version
                    value = american_to_decimal(price.get('price'), bet.get('status'))
                    res.update(straight_normalize({
                        'time_req': round(time.time()),
                        'match_id': match_id,
                        'type': bet.get('type'),
                        'status': bet.get('status'),
                        'side': bet.get('side'),
                        'period': bet.get('period'),
                        'designation': price.get('designation'),
                        'points': price.get('points'),
                        'value': value,
                        # 'units':res[match_id]['units'], Нужно для угловых - они отключены
                        # 'vector':'UP' if price.get('price') > 0 else 'DOWN'
                    }))
                    # print('res: ' + str(res))
        if not bets.get(str(match_id)):
            bets[str(match_id)] = {}
        bets[str(match_id)]['time_req'] = round(time.time())
        if res:
            bets[str(match_id)]['kofs'] = res
    return resp.elapsed.total_seconds()
