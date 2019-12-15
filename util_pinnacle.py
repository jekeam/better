import requests
import utils
import proxy_worker
import exceptions
import datetime
import sys
import traceback

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


# api_key = requests.get(
#     url='https://www.pinnacle.com/config/app.json',
#     verify=False,
#     timeout=10,
# ).json()['api']['haywire']['apiKey']

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
                proxies = proxy_worker.del_proxy(proxy, proxies)
                raise exceptions.TimeOut(err_str)
            except requests.exceptions.ConnectionError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                utils.prnts(err_str)
                proxies = proxy_worker.del_proxy(proxy, proxies)
                raise ValueError(err_str)
            except requests.exceptions.RequestException as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                utils.prnts(err_str)
                proxies = proxy_worker.del_proxy(proxy, proxies)
                raise ValueError(err_str)
            except ValueError as e:
                if resp.text:
                    text = resp.text
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error1: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                utils.prnts(err_str)
                proxi_list = proxy_worker.del_proxy(proxy, proxies)
                raise ValueError(err_str)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = bk_name + ' ' + url.format(sport_id) + ' ' + 'error: ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                utils.prnts(err_str)
                proxies = proxy_worker.del_proxy(proxy, proxies)
                raise ValueError(err_str)
    return data, resp.elapsed.total_seconds()
