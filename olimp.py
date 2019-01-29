# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from hashlib import md5
import datetime
import multiprocessing as mp
import pytz

import csv

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from utils import prnt

OLIMP_DEBUG = False


def get_xtoken(payload, secret_key):
    sorted_values = [str(payload[key]) for key in sorted(payload.keys())]
    to_encode = ";".join(sorted_values + [secret_key])
    return {"X-TOKEN": md5(to_encode.encode()).hexdigest()}


def to_abb(sbet):
    value = re.findall('\((.*)\)', sbet)[0]
    key = re.sub('\((.*)\)', '', sbet)
    abr = ''
    # error to_add("ХунтеларК.(Аякс)(0.5)бол"), value=Аякс)(0.5, key=ХунтеларК.бол
    try:
        abr = abbreviations[key].format(value)
    except:
        # pass
        prnt('error to_add("' + sbet + '"), value=' + value + ', key=' + key)
    return abr


my_list = []


def stake(i, a, shared_list, secret_key, new_url, wager_dict):
    wager = {}
    for b in a.get('it', []):
        bets = {}
        if str(b.get('ms', '1')) == '1' and OLIMP_DEBUG:
            prnt('Олимп (' + b.get('c2', '') + ' vs ' + b.get('c2', '')
                 + '): ставки приостановлены: https://olimp.com/app/event/live/1/index.php?page=line&action=2&live[]='
                 + str(b.get('id', '')), 'hide')
            return False

        if b.get('id') and str(b.get('ms', '1')) != '1':

            data = {
                "live": "1",
                "sport_id": "1",
                "id": b['id'],
                "session": "",
                "platforma": "ANDROID1",
                "lang_id": "0",
                "time_shift": 0
            }
            stake_head.update(get_xtoken(data, secret_key))
            stake_head.pop('Accept-Language', None)

            # prnt('olimp post:' + str(new_url + '/api/stakes/') + str(data))
            res = requests.post(new_url + '/api/stakes/', data=data, headers=stake_head, timeout=10, verify=False)
            stakes = res.json()

            if not stakes.get('error', {}).get('err_code', 0):
                # prnt('STAKE-OK')
                # print(b.get('id', ''))
                bets['ID'] = b.get('id', '')

                # Проверяется выше(так то до сюда не дойдет)
                is_block = ''
                if str(b.get('ms', '')) == '1':
                    is_block = 'BLOCKED'  # 1 - block, 2 - available
                bets['BLOCKED'] = is_block

                bets['max'] = b.get('max', '')
                bets['INFO'] = a.get('cn', '')
                bets['TEAM1'] = b.get('c1', '')
                bets['TEAM2'] = b.get('c2', '')
                bets['START_TIME'] = b.get('dt', '00.00.0000 00:00:00')

                minutes = "-1"
                try:
                    minutes = re.findall('\d{1,2}\"', b.get('scd', ''))[0].replace('"', '')
                except:
                    pass
                bets['MINUTES'] = minutes

                # startTime=datetime.datetime.strptime(b.get('dt',''), "%d.%m.%Y %H:%M:%S")
                # currentTime=datetime.datetime.strptime(datetime.datetime.now(pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
                # timeDif = currentTime-startTime

                # minuts

                bets['SCORE'] = b.get('sc', '0:0')
                # bets['SCORE_DETAIL']=b.get('scd','')
                # prnt(b)
                # prnt(b.get('c1','')+' '+b.get('c2',''))
                for c in stakes.get('data', {}).get('it', []):
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
                                # был кейс когда попались команды:
                                # Сирианска - Арамейска Сирианска(и в тип ставки папало АрамейскаТ1бол)
                                # - надо переписать правильнее|Атыраубол
                                key_r = d.get('n', '').replace(stakes.get('data').get('c1', ''), 'Т1') \
                                    .replace(stakes.get('data').get('c2', ''), 'Т2')
                                bets[key_r] = d.get('v', '')
                                olimp_factor_short = str([
                                                             abbreviations[c.replace(' ', '')]
                                                             if c.replace(' ', '') in abbreviations.keys()
                                                             else c.replace(' ', '')
                                                             if '(' not in c.replace(' ', '')
                                                             else to_abb(c.replace(' ', ''))
                                                             for c in [key_r]
                                                         ][0])
                                key_wager = str(b.get('id', '')) + '-' + olimp_factor_short
                                try:
                                    wager_dict[key_wager]
                                except:
                                    wager_dict[key_wager] = {'apid': str(d.get('apid', ''))}
                shared_list.append(bets)
            else:
                # prnt('STAKE-ERR '+stakes.get('error',{}).get('err_desc',''))
                pass


slice_head = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'okhttp/3.9.1'
}

stake_head = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'okhttp/3.9.1'
}

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
