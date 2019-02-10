# coding:utf-8
import requests
from proxy_worker import del_proxy
import time
from exceptions import FonbetMatchСompleted
from utils import prnts

url_fonbet_matchs = "https://line-02.ccf4ab51771cacd46d.com/live/currentLine/en/?2lzf1earo8wjksbh22s"
url_fonbet_match = "https://23.111.80.222/line/eventView?eventId="
UA = 'Mozilla/5.0 (Windows NT 10; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.3163.100 Safari/537.36'
fonbet_header = {
    'User-Agent': 'Fonbet/5.2.2b (Android 21; Phone; com.bkfonbet)',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip'
}


def get_matches_fonbet(proxies, proxy):
    global url_fonbet
    global UA

    try:
        proxy = {'http': proxy}
        # prnts('Fonbet set proxy: ' + proxy.get('http'), 'hide')
    except Exception as e:
        err_str = 'Fonbet error set proxy: ' + str(e)
        prnts(err_str)
        raise ValueError(err_str)

    try:
        resp = requests.get(
            url_fonbet_matchs,
            headers={'User-Agent': UA},
            timeout=5.51,
            verify=False,
            proxies=proxy,
        )
        try:
            res = resp.json()
        except Exception as e:
            err_str = 'Fonbet error : ' + str(e)
            prnts(err_str)
            raise ValueError('Exception: ' + str(e))

        if res.get("result") != "error":
            return res, resp.elapsed.total_seconds()
        else:
            raise ValueError(res.get("errorMessage"))

    except requests.exceptions.ConnectionError as e:
        err_str = 'Фонбет, код ошибки 0: ' + str(e)
        prnts(err_str)
        proxies = del_proxy(proxy.get('http'), proxies)
        raise ValueError(err_str)
    except requests.exceptions.RequestException as e:
        err_str = 'Фонбет, код ошибки 1: ' + str(e)
        prnts(err_str)
        proxies = del_proxy(proxy.get('http'), proxies)
        raise ValueError(err_str)
    except Exception as e:
        err_str = 'Фонбет, код ошибки 2: ' + str(e)
        prnts(err_str)
        # proxi_list = del_proxy(proxy.get('http'), proxies)
        raise ValueError(err_str)


def get_match_fonbet(match_id, proxi_list, proxy):
    global url_fonbet_match
    global fonbet_header

    try:
        proxy = {'http': proxy}
        # prnts('Fonbet: set proxy by ' + str(match_id) + ': ' + str(proxy.get('http')), 'hide')
    except Exception as e:
        err_str = 'Fonbet error set proxy by ' + str(match_id) + ': ' + str(e)
        prnts(err_str)
        raise ValueError(err_str)

    try:
        resp = requests.get(
            url_fonbet_match + str(match_id) + "&lang=en",
            headers=fonbet_header,
            timeout=3.51,
            verify=False,
            proxies=proxy,
        )
        try:
            res = resp.json()
        except Exception as e:
            err_str = 'Fonbet error by ' + str(match_id) + ': ' + str(e)
            prnts(err_str)
            raise ValueError(err_str)

        if res.get("result") != "error":
            return res, resp.elapsed.total_seconds()
        else:
            if 'Event not found' in res.get("errorMessage"):
                raise FonbetMatchСompleted('1 Фонбет, матч ' + str(match_id) + ' завершен, поток выключен!')
            err = res.get("errorMessage")
            prnts(str(err))
            raise ValueError(str(err))

    except requests.exceptions.ConnectionError as e:
        err_str = 'Фонбет ' + str(match_id) + ', код ошибки 0: ' + str(e)
        prnts(err_str)
        proxi_list = del_proxy(proxy.get('http'), proxi_list)
        raise ValueError(err_str)
    except requests.exceptions.RequestException as e:
        err_str = 'Фонбет ' + str(match_id) + ', код ошибки 1: ' + str(e)
        prnts(err_str)
        proxi_list = del_proxy(proxy.get('http'), proxi_list)
        raise ValueError(err_str)
    except FonbetMatchСompleted as e:
        raise FonbetMatchСompleted('2 ' + str(e))
    except Exception as e:
        if 'Event not found' in str(e):
            raise FonbetMatchСompleted('3 Фонбет, матч ' + str(match_id) + ' завершен, поток выключен! ' + str(e))
        err_str = 'Фонбет ' + str(match_id) + ', код ошибки 2: ' + str(e)
        prnts(err_str)
        # proxi_list = del_proxy(proxy.get('http'), proxi_list)
        raise ValueError(err_str)


def get_bets_fonbet(bets_fonbet, match_id, proxies_fonbet, proxy):
    key_id = str(match_id)
    try:
        resp, time_resp = get_match_fonbet(match_id, proxies_fonbet, proxy)
        # Очистим дстарые данные
        # if bets_fonbet.get(key_id):
        # bets_fonbet[key_id] = dict()
        time_start_proc = time.time()

        # if key_id in (str(12879839), str(12801238), str(12801237), str(12801241)):
        #     f = open('fonbet.txt', 'a+')
        #     f.write(json.dumps(resp, ensure_ascii=False))
        #     f.write('\n')
        #     # prnts('fonbet: '+str(json.dumps(resp, ensure_ascii=False)))

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
                                # prnts('fonbet block: '+str(name), str(kof.get('factorId')))
                            else:
                                value = kof.get('value')
                            # {'event': '12788610', 'factor': '921', 'param': '', 'score': '1:0', 'value': '1.25'}
                            for vct in VICTS:
                                coef = half + str(vct[0])  # + num_team
                                if str(vct[1]) == factorId:
                                    hist5 = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('4',
                                                                                                                  0)
                                    hist4 = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('3',
                                                                                                                  0)
                                    hist3 = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('2',
                                                                                                                  0)
                                    hist2 = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('1',
                                                                                                                  0)
                                    hist1 = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('value', 0)

                                    cof_is_change = True if hist1 != value else False

                                    if cof_is_change and not kof_is_block:
                                        avg_change = \
                                            bets_fonbet[key_id]. \
                                                get('kofs', {}). \
                                                get(coef, {}). \
                                                get('hist', {}). \
                                                get('avg_change', [])
                                        avg_change.append(round(time.time() -
                                                                bets_fonbet[key_id].
                                                                get('kofs', {}).
                                                                get(coef, {}).
                                                                get('hist', {}).
                                                                get('time_change', time.time())))
                                        time_change = round(time.time())
                                    elif not kof_is_block:
                                        avg_change = \
                                            bets_fonbet[key_id]. \
                                                get('kofs', {}). \
                                                get(coef, {}). \
                                                get('hist', {}). \
                                                get('avg_change', [])
                                        time_change = \
                                            bets_fonbet[key_id]. \
                                                get('kofs', {}). \
                                                get(coef, {}). \
                                                get('hist', {}). \
                                                get('time_change', round(time.time()))

                                    if kof_is_block:
                                        avg_change = \
                                            bets_fonbet[key_id]. \
                                                get('kofs', {}). \
                                                get(coef, {}). \
                                                get('hist', {}). \
                                                get('avg_change', [])
                                        time_change = round(time.time())

                                    bets_fonbet[key_id]['kofs'].update(
                                        {
                                            coef:
                                                {
                                                    'time_req': round(time.time()),
                                                    'event': event.get('id'),
                                                    'value': value,
                                                    'param': '',
                                                    'factor': factorId,
                                                    'score': score,
                                                    'hist': {
                                                        'time_change': time_change,
                                                        'avg_change': avg_change,
                                                        '1': hist1,
                                                        '2': hist2,
                                                        '3': hist3,
                                                        '4': hist4,
                                                        '5': hist5
                                                    }
                                                }
                                        }
                                    )

                            for stake in TT:
                                coef = half + str(stake[0].format(p))  # + num_team
                                if str(stake[1]) == factorId:
                                    hist5 = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('4',
                                                                                                                  0)
                                    hist4 = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('3',
                                                                                                                  0)
                                    hist3 = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('2',
                                                                                                                  0)
                                    hist2 = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('hist', {}).get('1',
                                                                                                                  0)
                                    hist1 = bets_fonbet[key_id].get('kofs', {}).get(coef, {}).get('value', 0)

                                    cof_is_change = True if hist1 != value else False

                                    if cof_is_change and not kof_is_block:
                                        avg_change = \
                                            bets_fonbet[key_id]. \
                                                get('kofs', {}). \
                                                get(coef, {}). \
                                                get('hist', {}). \
                                                get('avg_change', [])
                                        avg_change.append(round(time.time() -
                                                                bets_fonbet[key_id].
                                                                get('kofs', {}).
                                                                get(coef, {}).
                                                                get('hist', {}).
                                                                get('time_change', round(time.time()))))
                                        time_change = round(time.time())
                                    elif not kof_is_block:
                                        avg_change = \
                                            bets_fonbet[key_id]. \
                                                get('kofs', {}). \
                                                get(coef, {}). \
                                                get('hist', {}). \
                                                get('avg_change', [])
                                        time_change = \
                                            bets_fonbet[key_id]. \
                                                get('kofs', {}). \
                                                get(coef, {}). \
                                                get('hist', {}). \
                                                get('time_change', round(time.time()))

                                    if kof_is_block:
                                        avg_change = \
                                            bets_fonbet[key_id]. \
                                                get('kofs', {}). \
                                                get(coef, {}). \
                                                get('hist', {}). \
                                                get('avg_change', [])
                                        time_change = round(time.time())

                                    bets_fonbet[key_id]['kofs'].update(
                                        {
                                            coef:
                                                {
                                                    'time_req': round(time.time()),
                                                    'event': event.get('id'),
                                                    'value': value,
                                                    'param': pValue,
                                                    'factor': factorId,
                                                    'score': score,
                                                    'hist': {
                                                        'time_change': time_change,
                                                        'avg_change': avg_change,
                                                        '1': hist1,
                                                        '2': hist2,
                                                        '3': hist3,
                                                        '4': hist4,
                                                        '5': hist5
                                                    }
                                                }}
                                    )

        for val in bets_fonbet.get(key_id, {}).get('kofs', {}).values():
            time_change_kof = val.get('hist', {}).get('time_change')
            time_change_tot = bets_fonbet.get(key_id, {}).get('time_change_total')
            avg_change_total = bets_fonbet.get(key_id, {}).get('avg_change_total', [])
            if round(time_change_tot) < round(time_change_kof):
                avg_change_total.append(round(time_change_kof - time_change_tot))
                bets_fonbet[key_id].update({'time_change_total': time_change_kof})
                bets_fonbet[key_id].update({'avg_change_total': avg_change_total})

        try:
            for i, j in bets_fonbet.get(key_id, {}).get('kofs', {}).copy().items():
                if round(float(time.time() - float(j.get('time_req', 0)))) > 8:
                    try:
                        bets_fonbet[key_id]['kofs'].pop(i)
                        prnts(
                            'Фонбет, данные по котировке из БК не получены более 8 сек., котировка удалена: ' +
                            key_id + ' ' + str(i) + ' ' + str(j), 'hide'
                        )
                    except Exception as e:
                        prnts('Фонбет, ошибка 1 при удалении старой котирофки: ' + str(e))
        except Exception as e:
            prnts('Фонбет, ошибка 2 при удалении старой котирофки: ' + str(e))
            # if key_id == '12907481':
        #     import json
        #     print('--------ф--------')
        #     # print(json.dumps(resp, ensure_ascii=False))
        #     print('')
        #     print('')
        #     print(json.dumps(bets_fonbet.get(str(match_id)), ensure_ascii=False))
        #     print('')
        #     print('')
        #     print('--------ф--------')
        #     time.sleep(5)
        return time_resp + (time.time() - time_start_proc)
    except Exception as e:
        prnts(e)
        if bets_fonbet.get(key_id):
            bets_fonbet.pop(key_id)
        raise ValueError(e)
