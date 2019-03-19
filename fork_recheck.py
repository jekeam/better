# -*- coding: utf-8 -*-
import requests
from olimp import to_abb, abbreviations
from meta_ol import get_xtoken_bet, olimp_secret_key, ol_url_api, ol_payload, ol_headers
from meta_fb import fb_headers, get_new_bets_fonbet
import re
from utils import prnt
import copy
from retry_requests import requests_retry_session
from exceptions import BetIsLost, BetError


def get_olimp_info(id_matche, olimp_k):
    bet_into = {}
    olimp_data = copy.deepcopy(ol_payload)
    olimp_data.update({
        "live": "1",
        "sport_id": "1"
    })
    olimp_data.update({'id': id_matche})

    olimp_stake_head = copy.deepcopy(ol_headers)
    olimp_stake_head.update(get_xtoken_bet(olimp_data))
    olimp_stake_head.pop('Accept-Language', None)

    prnt('FORK_RECHECK.PY: get_olimp_info rq: ' + str(olimp_data), 'hide')
    res = requests_retry_session().post(
        ol_url_api.format('10', 'stakes/'),
        data=olimp_data,
        headers=olimp_stake_head,
        timeout=10,
        verify=False
    )
    prnt('FORK_RECHECK.PY: get_olimp_info rs: ' + str(res.text), 'hide')

    stake = res.json()
    if not stake.get('error', {}).get('err_code', 0):
        bet_into['ID'] = id_matche

        is_block = ''
        if str(stake.get('ms', '')) == '1':
            is_block = 'BLOCKED'  # 1 - block, 2 - available
            prnt('Олимп: ставки приостановлены: http://olimp.com/app/event/live/1/' + str(stake.get('id', '')))
            prnt('kof is blocked: ' + str(stake))
        bet_into['BLOCKED'] = is_block

        minutes = "-1"
        try:
            minutes = re.findall('\d{1,2}\"', stake.get('scd', ''))[0].replace('"', '')
        except:
            pass
        bet_into['MINUTES'] = minutes

        # startTime=datetime.datetime.strptime(stake.get('dt',''), "%d.%m.%Y %H:%M:%S")
        # currentTime=datetime.datetime.strptime(datetime.datetime.now(pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
        # timeDif = currentTime-startTime

        # minuts
        bet_into['SCORE'] = stake.get('sc', '0:0')  # .get('sc', '0:0').split(' ')[0]
        for c in stake.get('data', {}).get('it', []):
            # if c.get('n','') in ['Main Bets', 'Goals', 'Corners', 'Individual total', 'Additional total']:
            if c.get('n', '') in ['Основные', 'Голы', 'Угловые', 'Инд.тотал', 'Доп.тотал', 'Исходы по таймам']:
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
                        # prnt(key_r)
                        key_r = d.get('n', '').replace(stake.get('data').get('c1', ''), 'Т1') \
                            .replace(stake.get('data').get('c2', ''), 'Т2')
                        olimp_factor_short = str([
                                                     abbreviations[c.replace(' ', '')]
                                                     if c.replace(' ', '') in abbreviations.keys()
                                                     else c.replace(' ', '')
                                                     if '(' not in c.replace(' ', '')
                                                     else to_abb(c.replace(' ', ''))
                                                     for c in [key_r]
                                                 ][0])
                        bet_into[olimp_factor_short] = d.get('v', '')
    else:
        raise ValueError(stake)
    k = bet_into.get(olimp_k, 0)
    sc = bet_into.get('SCORE', '0:0').split(' ')[0]
    prnt('olimp score: ' + sc)
    prnt('FORK_RECHECK.PY: get_olimp_info end work', 'hide')
    return k, sc, round(res.elapsed.total_seconds(), 2)


def get_fonbet_info(match_id, factor_id, param, bet_tepe=None):
    prnt('match_id:{}, factor_id:{}, param:{}, bet_tepe:{}'.format(match_id, factor_id, param, bet_tepe))
    
    header = copy.deepcopy(fb_headers)
    url = "https://23.111.80.222/line/eventView?eventId=" + str(match_id) + "&lang=ru"
    prnt('FORK_RECHECK.PY: get_fonbet_info rq: ' + url + ' ' + str(header), 'hide')
    resp = requests_retry_session().get(
        url,
        headers=header,
        timeout=10,
        verify=False
    )
    prnt('FORK_RECHECK.PY: get_fonbet_info rs: ' + str(resp.text), 'hide')
    res = resp.json()
    
    result = res.get('result')
    
    wager = {}
    
    if result == "error":
        raise ValueError(resp.get("errorMessage"))
        
    for event in res.get("events"):
        if event.get('id') == match_id:
            sc = event.get('score', '0:0').replace('-', ':')
            period = 1
            time_break_fonbet = False
            
            if re.match('\([\d|\d\d]:[\d|\d\d]\)', event.get('scoreComment', '').replace('-',':')) and \
               str(event.get('timer', '')) == '45:00' and \
               round(event.get('timerSeconds', 0)/60, 2) == 45.0:
                time_break_fonbet = True
                period = 2
            elif re.match('\([\d|\d\d]:[\d|\d\d]\)', event.get('scoreComment', '').replace('-',':')) and \
                 round(event.get('timerSeconds', 0)/60, 2) > 45.0:
                period = 2
                
            prnt('current score: ' + str(sc))
            prnt('1st half score: ' + str(event.get('scoreComment')))
            prnt('timerSeconds: ' + str(event.get('timerSeconds')))
            prnt('timer: ' + str(event.get('timer')))
            prnt('calc period: '+str(period))
            prnt('calc timebreak: ' + str(time_break_fonbet))
            
            for cat in event.get('subcategories'):
                for kof in cat.get('quotes'):
                    if kof.get('factorId') == factor_id:

                        if kof.get('blocked'):
                            prnt('kof is blocked ' + str(kof))

                        if param:
                            if kof.get('pValue') != param:
                                prnt('Изменилась тотал ставки, param не совпадает: ' +'new: ' + str(kof.get('pValue')) + ', old: ' + str(param))
            
                                if bet_tepe:
                                    prnt('поиск нового id тотала: ' + bet_tepe)
                                    new_wager = get_new_bets_fonbet(match_id, proxies={})
                                    new_wager = new_wager.get(str(match_id), {}).get('kofs', {}).get(bet_tepe)
                                    if new_wager:
                                        prnt('Тотал найден: ' + str(new_wager))
                                        k = new_wager.get('value', 0)
                                        sc = new_wager.get('score', '0:0').replace('-', ':')
                                        return k, sc, round(resp.elapsed.total_seconds(), 2)
                                    else:
                                        err_str = 'Тотал не найден' + str(new_wager)
                                        raise BetIsLost(err_str)
                                else:
                                    err_str = 'Тип ставки, например 1ТМ(2.5) - не задан, выдаю ошибку: bet_type:' + bet_tepe
                                    raise BetIsLost(err_str)
                            if kof.get('blocked'):
                                prnt('kof is blocked ' + str(kof))

                        k = kof.get('value', 0)
                        prnt('FORK_RECHECK.PY: get_olimp_info end work', 'hide')
                        return k, sc, round(resp.elapsed.total_seconds(), 2)


def get_kof_fonbet(obj, match_id, factor_id, param):
    match_id = int(match_id)
    factor_id = int(factor_id)
    obj['fonbet'] = 0
    obj['fonbet_time_req'] = 0
    sc = ''
    if param:
        param = int(param)

    try:
        obj['fonbet'], sc, rime_req = get_fonbet_info(match_id, factor_id, param)
        obj['fonbet_time_req'] = rime_req
    except Exception as e:
        prnt('FORK_RECHECK.PY - fonbet-error: ошибка при повторной проверке коэф-та: ' + str(e))
        obj['fonbet'] = 0
    if obj['fonbet'] is None:
        obj['fonbet'] = 0

    return obj


def get_kof_olimp(obj, olimp_match, olimp_k):
    obj['olimp'] = 0
    obj['olimp_time_req'] = 0
    sc = ''
    try:
        r_olimp_coef1, sc, rime_req = get_olimp_info(olimp_match, olimp_k)
        obj['olimp_time_req'] = rime_req
        obj['olimp'] = r_olimp_coef1
    except Exception as e:
        prnt('FORK_RECHECK.PY - olimp-error: ошибка при повторной проверке коэф-та: ' + str(e))
    if obj['olimp'] is None:
        obj['olimp'] = 0
    return obj


if __name__ == "__main__":
    x, y, z = get_fonbet_info(13798881, 1871, 50, 'ТМ2(1.5)')
