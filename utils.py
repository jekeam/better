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

file_session_ol = 'olimp.session'
file_session_fb = 'fonbet.session'

package_dir = os.path.dirname(__file__)
dtOld = datetime.datetime.now()


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


def rq_log(vstr: str):
    Outfile = open('rq_log/log.txt', "a+", encoding='utf-8')
    Outfile.write(vstr + '\n')
    Outfile.close()


def prnt(vstr=None, hide=None):
    if vstr:
        global dtOld
        dtDeff = round((datetime.datetime.now() - dtOld).total_seconds())
        strLog = datetime.datetime.now().strftime('%d %H:%M:%S.%f ') + '[' + str(dtDeff).rjust(2, '0') + ']    ' + \
                 str(vstr)
        if not hide:
            dtOld = datetime.datetime.now()
            print(strLog)

        Outfile = open('client.log', "a+", encoding='utf-8')
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
        prnt(resp.text)
        raise LoadException("Site is not responding, status code: {}".format(resp.status_code))


def get_session_with_proxy(name):
    with open(os.path.join(package_dir, "proxies.json")) as file:
        proxies = load(file)
    session_proxies = proxies[name]
    session = requests.Session()  # cfscrape.create_scraper(delay=10)  #
    session.proxies = session_proxies

    # scraper = cfscrape.create_scraper(sess=session)

    return session
