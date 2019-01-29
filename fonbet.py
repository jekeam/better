# -*- coding: utf-8 -*-
import requests
import datetime
import pandas as pd
import urllib3
from fake_useragent import UserAgent
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from sys import exit
from utils import prnt

FONBET_DEBUG = False
recheck = None


def getSportNameById(sid, sports):
    """Получим имя событие по его ид"""
    return [sport['name'] for sport in sports if sport['id'] == sid][0]


def getStatusMatch(sid, eventMiscs):
    # prnt('sid ',sid)
    # prnt('eventMiscs ',eventMiscs)
    """Получим инфу по матчу: время, счет, тайм"""
    try:
        d = [
            {'info': event.get('comment'),
             'score1': event['score1'],
             'score2': event['score2'],
             'timerMinutes': round(event.get('timerSeconds', 0) / 60, 0),
             'liveDelay': event.get('liveDelay'),
             'timerUpdateTimestamp': event.get('timerUpdateTimestamp'),
             'timerUpdateTimestampMsec': event.get('timerUpdateTimestampMsec')}

            for event in eventMiscs if event['id'] == sid
        ][0]
    except:
        d = {}
    return d


def checkBlocks(id, f):
    """Проверим коэфицыенты на блокировку, так же может быть залочен весь матч"""
    # prnt('id='+str(id))
    isBlock = {}
    f_e = f.get('eventBlocks', {})
    for x in range(0, len(f_e)):
        if str(f_e[x].get('eventId', '')) == str(id):
            isBlock['state'] = str(f_e[x].get('state', ''))
            # return blocked or partial or blocked or None
            if isBlock.get('state', '') == 'blocked':  # Блокировка всего матча
                pass
            elif isBlock.get('state', '') == 'partial':  # Блокировка только события
                facorts_arr_str = ';'.join(str(e) for e in f_e[x].get('factors')).split(';')
                isBlock['factors'] = facorts_arr_str
    if isBlock and FONBET_DEBUG:
        prnt(str(id) + ' ' + str(isBlock), 'hide')
    return isBlock


def setFactorsByMatch(df, fid, f, event, n):
    global recheck
    wager = {}
    if checkBlocks(str(fid), f).get('state', 'available') != 'blocked':
        # Установим в датасет нужные нам коэфициенты по выбранному матчу
        # Проверим есть ли уже запись по данному матчу

        StatusMatch = getStatusMatch(fid, f['eventMiscs'])
        customFactors = {
            (factor.get('f'), factor.get('e')): {
                'v': factor.get('v'),
                'pt': factor.get('pt', ''),
                'p': factor.get('p'),
            } for factor in f['customFactors']
        }

        df.at[n, 'sportId'] = str(event.get('sportId'))
        df.at[n, 'sport'] = getSportNameById(event.get('sportId'), f['sports'])
        df.at[n, 'idMatch'] = str(fid)
        df.at[n, 'startTime'] = datetime.datetime.fromtimestamp(event['startTime']).strftime('%d.%m.%Y %H:%M:%S')
        df.at[n, 'minuts'] = StatusMatch.get('timerMinutes')
        df.at[n, 'score'] = str(StatusMatch.get('score1')) + ':' + str(StatusMatch.get('score2'))
        df.at[n, 'TeamId1'] = str(event['team1Id'])
        df.at[n, 'TEAM1'] = event.get('team1', '')
        df.at[n, 'TeamId2'] = str(event.get('team2Id', ''))
        df.at[n, 'TEAM2'] = event.get('team2', '')
        # df.at[n, 'isBlock'] = checkBlocks(str(fid), f).get('state','')
        # df.at[n, 'blockFactors'] = checkBlocks(str(fid), f).get('factors','')
        blockFactors = checkBlocks(str(fid), f).get('factors', '')

        for vct in VICTS:
            if str(vct[1]) not in blockFactors:
                cf = customFactors.get((vct[1], fid), {}).get('v')
                p = customFactors.get((vct[1], fid), {}).get('p')
                wager[str(fid) + '-' + str(vct[0])] = {
                    'f': str(vct[1]),
                    'p': str(p),
                    'score': str(StatusMatch.get('score1')) + ':' + str(StatusMatch.get('score2'))
                }
                df.at[n, vct[0]] = cf
            else:
                if FONBET_DEBUG:
                    prnt('https://www.fonbet.com/#!/live/football/'
                         + str(event.get('sportId')) + '/'
                         + str(fid) + ' фонбет: ставки приостановлены ('
                         + event.get('team1')
                         + ' vs '
                         + event.get('team2')
                         + '), фактор блокирован: ' + str(vct[1]) + ' '
                         + str(vct[0].format(customFactors.get((vct[1], fid), {}).get('pt', ''))) + '\n', 'hide')
        for stake in TT:
            if str(stake[1]) not in blockFactors:
                p = customFactors.get((stake[1], fid), {}).get('p')
                coef = str(stake[0].format(customFactors.get((stake[1], fid), {}).get('pt', '')))
                wager[str(fid) + '-' + coef] = {
                    'f': str(stake[1]),
                    'p': str(p),
                    'score': str(StatusMatch.get('score1')) + ':' + str(StatusMatch.get('score2'))
                }
                df.at[n, coef] \
                    = customFactors.get((stake[1], fid), {}).get('v')
            else:
                if FONBET_DEBUG:
                    prnt('https://www.fonbet.com/#!/live/football/'
                         + str(event.get('sportId', '')) + '/'
                         + str(fid) + ' фонбет: ставки приостановлены ('
                         + event.get('team1', '')
                         + ' vs '
                         + event.get('team2', '')
                         + '), фактор блокирован: ' + str(stake[1]) + ' '
                         + str(stake[0].format(customFactors.get((stake[1], fid), {}).get('pt', ''))) + '\n', 'hide')
    else:
        if FONBET_DEBUG:
            prnt('Фонбет: cтавки приостановлены по всему матчу ('
                 + event.get('team1', '')
                 + ' vs '
                 + event.get('team2', '')
                 + '): ' + 'https://www.fonbet.com/#!/live/football/'
                 + str(event.get('sportId', '')) + '/' + str(fid) + '\n', 'hide')
    if not recheck:
        with open('wager_fonbet.json', 'a', encoding='utf8') as f:
            f.write(',')
            f.write(json.dumps(wager, ensure_ascii=False))


def setFactorsOth(df, fid, f, event, n):
    global recheck
    wager = {}
    if checkBlocks(str(fid), f).get('state', 'available') != 'blocked':
        """Установим нужные коэфициенты по ребенку матча, например это коэф-ты по первому тайму или угловых"""
        idMatch = event.get('parentId')

        customFactors = {
            (factor.get('f'), factor.get('e')):
                {
                    'v': factor.get('v'),
                    'pt': factor.get('pt', ''),
                    'p': factor.get('p')
                } for factor in f['customFactors']}

        blockFactors = checkBlocks(str(fid), f).get('factors', '')

        try:
            n = df.loc[df['idMatch'] == str(idMatch)].index[0]
        except:
            if FONBET_DEBUG:
                prnt('fonbet.py: pass idMatch ' + str(idMatch), 'hide')  # коэф-ты не найдены
            pass

        if event['name'] == '1st half':
            factorType = '1'
        elif event['name'] == '2nd half':
            factorType = '2'
        elif event['name'] == 'corners':
            factorType = 'УГЛ'
        else:
            return None

        for stake in TT:
            if str(stake[1]) not in blockFactors:
                df.at[n, factorType + stake[0].format(customFactors.get((stake[1], fid), {}).get('pt', ''))] \
                    = customFactors.get((stake[1], fid), {}).get('v')
                p = customFactors.get((stake[1], fid), {}).get('p')
                wager[
                    str(idMatch) + '-' + factorType + stake[0].format(
                        customFactors.get((stake[1], fid), {}).get('pt', ''))] = {
                    'f': str(stake[1]),
                    'p': str(p),
                    'score': str(df.iloc[n]['score'])
                }
                # print(wager)
            else:
                if FONBET_DEBUG:
                    prnt('https://www.fonbet.com/#!/live/football/'
                         + str(event.get('sportId', '')) + '/'
                         + str(fid) + ' фонбет: ставки приостановлены ('
                         + event.get('team1', '')
                         + ' vs '
                         + event.get('team2', '')
                         + '), фактор блокирован: ' + str(stake[1]) + ' '
                         + str(stake[0].format(customFactors.get((stake[1], fid), {}).get('pt', ''))) + '\n', 'hide')

    else:
        if FONBET_DEBUG:
            prnt('https://www.fonbet.com/#!/live/football/'
                 + str(event.get('sportId', '')) + '/'
                 + str(fid) + ' фонбет: cтавки приостановлены по всему матчу ('
                 + event.get('team1', str(event.get('sportId', '')) + '/' + str(event.get('parentId', '')))
                 + ' vs '
                 + event.get('team2', event.get('name', ''))
                 + ')\n', 'hide')
    if not recheck:
        with open('wager_fonbet.json', 'a', encoding='utf8') as f:
            f.write(',')
            f.write(json.dumps(wager, ensure_ascii=False))


url = "https://line-02.ccf4ab51771cacd46d.com/live/currentLine/en/?2lzf1earo8wjksbh22s"

# VICTORIES
VICTS = [['П1', 921], ['Н', 922], ['П2', 923], ['П1Н', 924], ['12', 1571], ['П2Н', 925],
         ['ОЗД', 4241], ['ОЗН', 4242], ['КЗ1', 4235], ['КНЗ1', 4236], ['КЗ2', 4238], ['КНЗ2', 4239]]
# Обе забьют:да/Обе забьют:нет/Команда 1 забьет/Команда 1 не забьет/Команда 2 забьет/Команда 2 не забьет
# TOTALS
TTO = [['ТБ({})', 930], ['ТБ({})', 1696], ['ТБ({})', 1727], ['ТБ({})', 1730], ['ТБ({})', 1733]]
TTU = [['ТМ({})', 931], ['ТМ({})', 1697], ['ТМ({})', 1728], ['ТМ({})', 1731], ['ТМ({})', 1734]]
# TEAM TOTALS-1
TT1O = [['ТБ1({})', 1809], ['ТБ1({})', 1812], ['ТБ1({})', 1815]]
TT1U = [['ТМ1({})', 1810], ['ТМ1({})', 1813], ['ТМ1({})', 1816]]
# TEAM TOTALS-2
TT2O = [['ТБ2({})', 1854], ['ТБ2({})', 1873], ['ТБ2({})', 1880]]
TT2U = [['ТМ2({})', 1871], ['ТМ2({})', 1874], ['ТМ2({})', 1881]]

TT = []
for bet in [TTO, TTU, TT1O, TT1U, TT2O, TT2U]:
    TT.extend(bet)


# %%
def get_bets(is_recheck=None):
    global recheck
    if is_recheck:
        recheck = is_recheck
    if recheck: prnt('FONBET.PY: get_bets start')
    wagers = dict()
    fonbet_bets = pd.DataFrame()
    UA = UserAgent().chrome
    # prnt('fonbet post:' + str(url))
    if recheck: prnt('FONBET.PY: get_bets request')
    r = requests.get(url, headers={'User-Agent': UA}, timeout=10, verify=False)
    if recheck: prnt('FONBET.PY: get_bets get response')
    # prnt('get success json')

    f = r.json()
    # file = open('fonbet.json', 'w', encoding="UTF-8")
    # for cf in f['customFactors']:
    #     if cf['e'] == 12264423:
    #         print(cf)
    # file.write(json.dumps(f, indent=4, ensure_ascii=False))
    # file.write(r.text)

    # runTime = datetime.datetime.now()
    # prnt('runTime'+str(runTime))

    # получим все события по футболу
    events = [[sport['name'], sport['id']] for sport in f['sports'] if 'Football' in sport['name'] and sport['id'] != 1]
    idEvents = [e[1] for e in events]

    # получим список ид всех матчей по событиям
    if idEvents:
        idMatches = [event['id'] for event in f['events'] if event.get('sportId') in idEvents]

    # полчим все инфу по ид матча
    if idEvents and idMatches:
        for mid in idMatches:
            for event in f['events']:
                if event['id'] == mid and event['kind'] == 1:
                    setFactorsByMatch(fonbet_bets, mid, f, event, fonbet_bets.shape[0])
        for mid in idMatches:
            for event in f['events']:
                if event['id'] == mid and event['kind'] > 1 and event['name'] in ['1st half', '2nd half', 'corners']:
                    setFactorsOth(fonbet_bets, mid, f, event, fonbet_bets.shape[0])

    fonbet_bets = fonbet_bets.astype(str)
    fonbet_bets.columns = [c.replace('()', '') for c in fonbet_bets.columns]
    fonbet_bets = fonbet_bets.replace({'nan': ''})
    if recheck: prnt('FONBET.PY: get_bets end work')
    return fonbet_bets
