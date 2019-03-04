# coding: utf-8
from random import choice, random
from json import dumps
import requests
from utils import check_status_with_resp, prnt
import time


fb_payload = {
    "appVersion": "5.1.3b",
    "lang": "ru",
    "rooted": False,
    "sdkVersion": 21,
    "sysId": 4
}

fb_browser_head = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
}

fb_headers = {
    "User-Agent": "Fonbet/5.1.3b (Android 21; Phone; com.bkfonbet)",
    "Content-Type": "application/json; charset=UTF-8",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip"
}

fb_payload_bet = {
    "coupon":
        {
            "flexBet": "any",  # Изменения коэф-в, any - все, up - вверх
            "flexParam": False,  # Изменения фор и тоталов, True - принимать, False - не принимать
            "bets":
                [
                    {
                        "lineType": "LIVE",
                        "score": "",
                        "value": 0,
                        "event": 0,
                        "factor": 0,
                        "num": 0
                    },
                ],
            "amount": 0.0,
            "system": 0
        },
    "appVersion": "5.1.3b",
    "carrier": "MegaFon",
    "deviceManufacturer": "LENOVO",
    "deviceModel": "Lenovo A5000",
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "rooted": False,
    "sdkVersion": 21,
    "sysId": 4,
    "clientId": 0
}

fb_payload_max_bet = {
    "coupon":
        {
            "flexBet": "any",  # Изменения коэф-в, any - все, up - вверх
            "flexParam": False,  # Изменения фор и тоталов, True - принимать, False - не принимать
            "bets":
                [
                    {
                        "lineType": "LIVE",
                        "score": "",
                        "value": 0,
                        "event": 0,
                        "factor": 0,
                        "num": 0
                    },
                ],
            "amount": 0.0,
            "system": 0
        },
    "appVersion": "5.1.3b",
    "carrier": "MegaFon",
    "deviceManufacturer": "LENOVO",
    "deviceModel": "Lenovo A5000",
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "rooted": False,
    "sdkVersion": 21,
    "sysId": 4,
    "clientId": 0
}

payload_req = {
    "client": {"id": 0},
    "appVersion": "5.1.3b",
    "carrier": "MegaFon",
    "deviceManufacturer": "LENOVO",
    "deviceModel": "Lenovo A5000",
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "rooted": False,
    "sdkVersion": 21,
    "sysId": 4,
    "clientId": 0
}

payload_coupon_sum = {
    "clientId": "",
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "sysId": 4
}


payload_sell_check_result = {
    "requestId": 0,
    "clientId": "",
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "sysId": 4
}

payload_coupon_sell = {
    "flexSum": "up",
    "regId": 0,
    "requestId": 0,
    "sellSum": 0.0,
    "clientId": "",
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "sysId": 4
}


def get_random_str():
    result = ''
    alph_num = '0123456789'
    alph = 'abcdefghijklmnopqrstuvwxyz'
    alph = alph + alph.upper() + alph_num
    for _idx in range(48):
        result += choice(alph)
    return result

def get_dumped_payload(payload):
    dumped = dumps(payload)
    dumped = dumped.replace(": ", ":")  # remove spaces between items
    dumped = dumped.replace(", ", ",")
    return dumped
    

def get_urls(mirror, proxies):
    global fb_browser_head
    url = "https://" + mirror + "/urls.json?{}".format(random())
    resp = requests_retry_session().get(
        url,
        headers=fb_browser_head,
        verify=False,
        timeout=50,
        proxies=proxies
    )
    check_status_with_resp(resp)
    return resp.json()    

def get_common_url(data_urls):
    client_url = data_urls["clients-api"][0]
    timeout = data_urls["timeout"] / 100
    return "https:{url}/session/".format(url=client_url) + "{}", timeout
    


def get_new_bets_fonbet(match_id, proxies, time_out):
    from util_fonbet import url_fonbet_match, fonbet_header, VICTS, TTO, TTU, TT1O, TT1U, TT2O, TT2U
    key_id = str(match_id)
    bets_fonbet = {}
    try:
        resp = requests_retry_session().get(
            url_fonbet_match + str(match_id) + "&lang=en",
            headers=fonbet_header,
            timeout=time_out,
            verify=False,
            proxies=proxies,
        )
        resp = resp.json()

        TT = []
        for bet in [TTO, TTU, TT1O, TT1U, TT2O, TT2U]:
            TT.extend(bet)

        for event in resp.get("events"):
            # prnts(jsondumps(event, ensure_ascii=False))
            # exit()

            score = event.get('score', '0:0').replace('-', ':')
            timer = event.get('timer')
            minute = event.get('timerSeconds', 0) / 60
            skId = event.get('skId')
            skName = event.get('skName')
            sport_name = event.get('sportName')
            name = event.get('name')
            priority = event.get('priority')
            score_1st = event.get('scoreComment', '').replace('-', ':')

            if event.get('parentId') == 0 or event.get('name') in ('1st half', '2nd half'):
                if event.get('parentId') == 0:
                    try:
                        bets_fonbet[key_id].update({
                            'sport_id': skId,
                            'sport_name': skName,
                            'league': sport_name,
                            'name': name,
                            'priority': priority,
                            'score': score,
                            'score_1st': score_1st,
                            'time': timer,
                            'minute': minute,
                            'time_req': round(time.time())
                        })
                    except Exception as e:
                        # print(e)
                        bets_fonbet[key_id] = {
                            'sport_id': skId,
                            'sport_name': skName,
                            'league': sport_name,
                            'name': name,
                            'priority': priority,
                            'score': score,
                            'score_1st': score_1st,
                            'time': timer,
                            'minute': minute,
                            'time_req': round(time.time()),
                            'time_change_total': round(time.time()),
                            'avg_change_total': [],
                            'kofs': {}
                        }

                # prnts('event_name', event.get('name'))

                half = ''
                if event.get('name') == '1st half':
                    half = '1'
                elif event.get('name') == '2nd half':
                    half = '2'

                for cat in event.get('subcategories'):

                    cat_name = cat.get('name')
                    # prnts('cat_name', cat_name)
                    if cat_name in (
                            '1X2 (90 min)',
                            '1X2',
                            'Goal - no goal',
                            'Total', 'Totals', 'Team Totals-1', 'Team Totals-2'):  # , '1st half', '2nd half'

                        for kof in cat.get('quotes'):

                            factorId = str(kof.get('factorId'))
                            pValue = kof.get('pValue', '')
                            p = kof.get('p', '')
                            kof_is_block = kof.get('blocked', False)
                            if kof_is_block:
                                value = 0
                            else:
                                value = kof.get('value')
                            # {'event': '12788610', 'factor': '921', 'param': '', 'score': '1:0', 'value': '1.25'}
                            for vct in VICTS:
                                coef = half + str(vct[0])  # + num_team
                                if str(vct[1]) == factorId:
                                    bets_fonbet[key_id]['kofs'].update(
                                        {
                                            coef:
                                                {
                                                    'time_req': round(time.time()),
                                                    'event': event.get('id'),
                                                    'value': value,
                                                    'param': '',
                                                    'factor': factorId,
                                                    'score': score
                                                }
                                        }
                                    )

                            for stake in TT:
                                coef = half + str(stake[0].format(p))  # + num_team
                                if str(stake[1]) == factorId:
                                    bets_fonbet[key_id]['kofs'].update(
                                        {
                                            coef:
                                                {
                                                    'time_req': round(time.time()),
                                                    'event': event.get('id'),
                                                    'value': value,
                                                    'param': pValue,
                                                    'factor': factorId,
                                                    'score': score
                                                }}
                                    )
        return bets_fonbet
    except Exception as e:
        prnt(e)
        raise ValueError(e)    
