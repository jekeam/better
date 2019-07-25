# -*- coding: utf-8 -*-
import requests
from olimp import get_xtoken, to_abb
import re
from utils import prnt, get_param

cnt_fail = 0

abbreviations = {
    "Победапервой": "П1",
    "Победавторой": "П2",
    "Ничья": "Н",
    "Перваянепроиграет": "П1Н",
    "Втораянепроиграет": "П2Н",
    "Ничьейнебудет": "12",

    "Обезабьют:да": "ОЗД",
    "Обезабьют:нет": "ОЗН",
    "Т1забьет:да": "КЗ1",
    "Т1забьет:нет": "КНЗ1",
    "Т2забьет:да": "КЗ2",
    "Т2забьет:нет": "КНЗ2",
    "Тоталбол": "ТБ({})",
    "Тоталмен": "ТМ({})",
    "Тотал1-готаймабол": "1ТБ({})",
    "Тотал1-готаймамен": "1ТМ({})",
    "Тотал2-готаймабол": "2ТБ({})",
    "Тотал2-готаймамен": "2ТМ({})",
    # "Т1бол":"ИТБ1({})",
    # "Т1мен":"ИТМ1({})",
    # "Т2бол":"ИТБ2({})",
    # "Т2мен":"ИТМ2({})"
    "Т1бол": "ТБ1({})",
    "Т1мен": "ТМ1({})",
    "Т2бол": "ТБ2({})",
    "Т2мен": "ТМ2({})"
}
olimp_stake_head = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'okhttp/3.9.1'
}
olimp_data = {
    "live": "1",
    "sport_id": "1",
    "session": "",
    "platforma": "ANDROID1",
    "lang_id": "0",
    "time_shift": 0
}

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
    '1УГЛТБ': '1УГЛТМ',
    '1УГЛТМ': '1УГЛТБ',
    '2УГЛТБ': '2УГЛТМ',
    '2УГЛТМ': '2УГЛТБ',
    'УГЛТБ': 'УГЛТМ',
    'УГЛТМ': 'УГЛТБ',
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


def get_olimp_info(id_matche, olimp_k):
    olimp_secret_key = 'b2c59ba4-7702-4b12-bef5-0908391851d9'
    olimp_new_url = 'http://' + get_param('server_olimp') + ':10674'
    bet_into = {}

    olimp_data.update({'id': id_matche})

    olimp_stake_head.update(get_xtoken(olimp_data, olimp_secret_key))
    olimp_stake_head.pop('Accept-Language', None)

    prnt('FORK_RECHECK.PY: get_olimp_info requests', 'hide')
    res = requests.post(
        olimp_new_url + '/api/stakes/',
        data=olimp_data,
        headers=olimp_stake_head,
        timeout=10,
        verify=False
    )
    prnt('FORK_RECHECK.PY: get_olimp_info response', 'hide')
    # prnt('FORK_RECHECK.PY olimp: ' + str(res), 'hide')
    stake = res.json()
    if not stake.get('error', {}).get('err_code', 0):
        bet_into['ID'] = id_matche

        is_block = ''
        if str(stake.get('ms', '')) == '1':
            is_block = 'BLOCKED'  # 1 - block, 2 - available
            prnt('Олимп: ставки приостановлены: http://olimp.com/app/event/live/1/' + str(stake.get('id', '')))
            raise ValueError('kof is blocked: ' + str(stake))
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
        bet_into['SCORE'] = stake.get('sc', '0:0')
        prnt('olimp score: ' + stake.get('data').get('sc'))
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
                        # print(key_r)
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
    prnt('FORK_RECHECK.PY: get_olimp_info end work', 'hide')
    return bet_into[olimp_k], round(res.elapsed.total_seconds(), 2)


def get_fonbet_info(match_id, factor_id, param):
    header = {
        'User-Agent': 'Fonbet/5.2.2b (Android 21; Phone; com.bkfonbet)',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }
    prnt('FORK_RECHECK.PY: get_fonbet_info request', 'hide')
    url = "https://23.111.80.222/line/eventView?eventId=" + str(match_id) + "&lang=ru"
    res = requests.get(
        url,
        headers=header,
        timeout=10,
        verify=False
    )
    prnt('FORK_RECHECK.PY: get_fonbet_info response', 'hide')
    # prnt('FORK_RECHECK.PY fonbet: ' + str(res), 'hide')
    resp = res.json()
    if resp.get("result") == "error":
        raise ValueError(resp.get("errorMessage"))

    for event in resp.get("events"):
        if event.get('id') == match_id:
            prnt('fonbet score: ' + event.get('score'))
            for cat in event.get('subcategories'):
                for kof in cat.get('quotes'):
                    if kof.get('factorId') == factor_id:

                        if kof.get('blocked'):
                            raise ValueError('kof is blocked ' + str(kof))

                        if param:
                            if kof.get('pValue') != param:
                                raise ValueError('type kof is change: ' + str(kof))

                        k = kof.get('value')
                        prnt('FORK_RECHECK.PY: get_olimp_info end work', 'hide')
                        return k, round(res.elapsed.total_seconds(), 2)


def get_kof_fonbet(obj, match_id, factor_id, param):
    match_id = int(match_id)
    factor_id = int(factor_id)
    obj['fonbet'] = 0
    obj['fonbet_time_req'] = 0
    if param:
        param = int(param)

    try:
        obj['fonbet'], rime_req = get_fonbet_info(match_id, factor_id, param)
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
    try:
        (r_olimp_coef1, rime_req) = get_olimp_info(olimp_match, olimp_k)
        obj['olimp_time_req'] = rime_req
        obj['olimp'] = r_olimp_coef1
    except Exception as e:
        prnt('FORK_RECHECK.PY - olimp-error: ошибка при повторной проверке коэф-та: ' + str(e))
    if obj['olimp'] is None:
        obj['olimp'] = 0
    return obj


if __name__ == "__main__":
    # print(get_fonbet_info(12264412))
    # print(get_kof_fonbet({}, '12359234', '921', ''))
    print(get_olimp_info(45146516))
