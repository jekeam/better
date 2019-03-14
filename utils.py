# coding:utf-8
from requests import Session
from json import load, dumps
import os
import cfscrape
import requests
import datetime
import statistics

DEBUG = True
# DEBUG = False
MINUTE_COMPLITE = 88

package_dir = os.path.dirname(__file__)
dtOld = datetime.datetime.now()

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
    # '1УГЛТБ': '1УГЛТМ',
    # '1УГЛТМ': '1УГЛТБ',
    # '2УГЛТБ': '2УГЛТМ',
    # '2УГЛТМ': '2УГЛТБ',
    # 'УГЛТБ': 'УГЛТМ',
    # 'УГЛТМ': 'УГЛТБ',
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


def get_vector(bet_type, sc1=None, sc2=None):
    def raise_err(VECT, sc1, sc2):
        if sc1 is None or sc2 is None and VECT != '':
            raise ValueError('ERROR: sc1 or sc2 not defined!')

    D = 'DOWN'
    U = 'UP'
    VECT = ''

    if sc1:
        sc1 = int(sc1)
    if sc2:
        sc2 = int(sc2)

    if [t for t in ['ТБ', 'КЗ', 'ОЗН', 'ННД'] if t in bet_type]:
        return U
    if [t for t in ['ТМ', 'КНЗ', 'ОЗД', 'ННН'] if t in bet_type]:
        return D

    # Или добавлять ретурн в каждую из веток,
    # но те типы что по длинне написания больше,  должны быть выше

    if 'П1Н' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 >= sc2:
            return D
        else:
            return U

    if 'П2Н' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 <= sc2:
            return D
        else:
            return U

    if '12' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 != sc2:
            return D
        else:
            return U

    if 'П1' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 > sc2:
            return D
        else:
            return U

    if 'П2' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 < sc2:
            return D
        else:
            return U

    if 'Н' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 == sc2:
            return D
        else:
            return U

    raise ValueError('Error: vector not defined!')


def find_max_mode(list1):
    list_table = statistics._counts(list1)
    len_table = len(list_table)

    if len_table == 1:
        max_mode = statistics.mode(list1)
    else:
        new_list = []
        for i in range(len_table):
            new_list.append(list_table[i][0])
        max_mode = max(new_list)
    return max_mode


def write_file(filename, s):
    with open(os.path.join(os.path.dirname(__file__), filename), 'w') as file:
        file.write(s)


def read_file(filename):
    try:
        with open(os.path.join(os.path.dirname(__file__), filename), 'r') as file:
            return file.read()
    except:
        pass


def get_account_info(bk, param):
    with open(os.path.join(package_dir, "account.json")) as file:
        json = load(file)
    return json[bk].get(param, None)


def get_account_summ():
    with open(os.path.join(package_dir, "account.json")) as file:
        json = load(file)
    return json.get('summ', None)


def get_param(param):
    with open(os.path.join(package_dir, "account.json")) as file:
        json = load(file)
    return json.get(param)


def rq_log(vstr: str):
    Outfile = open('rq_log/log.txt', "a+", encoding='utf-8')
    Outfile.write(vstr + '\n')
    Outfile.close()


def prnt(vstr=None, hide=None):
    if vstr:
        global dtOld
        if not hide:
            dtDeff = round((datetime.datetime.now() - dtOld).total_seconds())
            strLog = datetime.datetime.now().strftime('%d %H:%M:%S.%f ') + \
                '[' + str(dtDeff).rjust(2, '0') + ']    ' + str(vstr)
            print(strLog)
            dtOld = datetime.datetime.now()
            Outfile = open('client.log', "a+", encoding='utf-8')
            Outfile.write(strLog + '\n')
            Outfile.close()
        else:
            strLog = datetime.datetime.now().strftime('%d %H:%M:%S.%f ') +'    ' + str(vstr)
            Outfile = open('client_hide.log', "a+", encoding='utf-8')
            Outfile.write(strLog + '\n')
            Outfile.close()
            


def prnts(vstr=None, hide=None):
    if vstr:
        global dtOld
        dtDeff = round((datetime.datetime.now() - dtOld).total_seconds())
        strLog = datetime.datetime.now().strftime('%d %H:%M:%S.%f ') + '[' + str(dtDeff).rjust(2, '0') + ']    ' + \
                 str(vstr)
        if not hide:
            dtOld = datetime.datetime.now()
            print(strLog)

        Outfile = open('server.log', "a+", encoding='utf-8')
        Outfile.write(strLog + '\n')
        Outfile.close()


def save_fork(fork_info):
    prnt('SAVE FORK:' + str(fork_info))
    f = open('id_forks.txt', 'a+', encoding='utf-8')
    f.write(dumps(fork_info) + '\n')


class LoadException(Exception):
    pass


def check_status(status_code):
    if status_code != 200:
        raise LoadException("Site is not responding, status code: {}".format(status_code))


def check_status_with_resp(resp, olimp=None):
    if (resp.status_code != 200 and olimp is None) \
            or (olimp is not None and resp.status_code not in (200, 400, 417, 406, 403, 500)):
        raise LoadException("Site is not responding, status code: {}".format(resp.status_code))


def get_session_with_proxy(name):
    with open(os.path.join(package_dir, "proxies.json")) as file:
        proxies = load(file)
    session_proxies = proxies[name]
    session = requests.Session()  # cfscrape.create_scraper(delay=10)  #
    session.proxies = session_proxies

    # scraper = cfscrape.create_scraper(sess=session)

    return session
