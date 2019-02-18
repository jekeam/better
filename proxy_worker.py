# coding: utf-8
import asyncio
from proxybroker import Broker
import requests
import multiprocessing as mp
import os
import time
import urllib3
from random import choice
from utils import prnts, DEBUG
from hashlib import md5
import threading
import platform
from shutil import copyfile
from utils import DEBUG

# disable warning
urllib3.disable_warnings()

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3163.100 Safari/537.36'


# не подошел для многопоточности
def get_next_proxy(proxi_list):
    for i in proxi_list:
        # prnts('Get next proxy: ' + i , 'hide')
        yield i.strip()


class createBatchGenerator:
    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def next(self):
        with self.lock:
            return next(self.it)


''' 
class createBatchGenerator:

    def __init__(self, proxi_list):
        self.proxi_list = proxi_list
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            for i in self.proxi_list:
                prnts('Get next proxy: ' + i)  # , 'hide'
                yield i.strip()
'''


def get_random_proxy(proxi_list):
    curr_proxy = choice(proxi_list)
    if curr_proxy.replace(' ', ''):
        return curr_proxy
    else:
        get_random_proxy(proxi_list)
        return False


def check_proxy_olimp(proxies_for_check, valid_proxies):
    from util_olimp import olimp_head, olimp_data, olimp_get_xtoken, olimp_url, olimp_secret_key

    def olimp_get_xtoken(payload, secret_key):
        sorted_values = [str(payload[key]) for key in sorted(payload.keys())]
        to_encode = ";".join(sorted_values + [secret_key])
        return {"X-TOKEN": md5(to_encode.encode()).hexdigest()}

    olimp_data_ll = olimp_data.copy()
    olimp_head_ll = olimp_head.copy()
    olimp_head_ll.update(olimp_get_xtoken(olimp_data_ll, olimp_secret_key))
    olimp_head_ll.pop('Accept-Language', None)

    for prx in proxies_for_check:
        try:
            x = 0
            resp = requests.post(olimp_url + '/api/slice/', headers=olimp_head_ll, data=olimp_data_ll,
                                 proxies={'http': prx}, timeout=1.51)
            print(
                'o valid: ' + str(prx), str(resp.status_code),
                str(resp.json().get('error', '').get('err_desc', ''))
            )
            x = x + 1
            if prx not in valid_proxies:
                valid_proxies.append(prx)
        except Exception as e:
            pass
            print('o invalid: ' + str(prx), str(e))


def check_proxy_fonbet(proxies_for_check, valid_proxies):
    from util_fonbet import url_fonbet_matchs as url_fonbet
    for prx in proxies_for_check:
        try:
            global url_fonbet
            global UA
            resp = requests.get(
                url_fonbet,
                headers={'User-Agent': UA},
                timeout=1.51,
                verify=False
            )
            print('f valid: ' + str(prx), str(resp.status_code))
            if prx not in valid_proxies:
                valid_proxies.append(prx)
        except Exception as e:
            pass
            print('f invalid: ' + str(prx), str(e))


def check_proxies_olimp(proxies_list):
    mgr = mp.Manager()
    valid_proxies_list = mgr.list()

    n_chunks = 26
    chunks = [proxies_list[i::n_chunks] for i in range(n_chunks)]

    prcs = []
    for chunk in chunks:
        p = mp.Process(target=check_proxy_olimp, args=(chunk, valid_proxies_list))
        prcs.append(p)
        p.start()

    for p in prcs:
        p.join()

    return valid_proxies_list


def check_proxies_fonbet(proxies_list):
    mgr = mp.Manager()
    valid_proxies_list = mgr.list()

    n_chunks = 10
    chunks = [proxies_list[i::n_chunks] for i in range(n_chunks)]

    prcs = []
    for chunk in chunks:
        p = mp.Process(target=check_proxy_fonbet, args=(chunk, valid_proxies_list))
        prcs.append(p)
        p.start()

    for p in prcs:
        p.join()

    return valid_proxies_list


async def save(proxies, proxy_list):
    while True:
        proxy = await proxies.get()
        if proxy is None:
            break
        proto = 'https' if 'HTTPS' in proxy.types else 'http'
        row = '%s://%s:%d' % (proto, proxy.host, proxy.port)
        proxy_list.append(row)


def save_list(proxies, filename=None):
    """Save proxies to a file."""
    if not filename:
        global proxy_file_name
        filename = proxy_file_name

    with open(filename, 'w') as f:
        for p in proxies:
            f.write(p + '\n')


def get_proxies(n):
    global proxy_list
    proxies = asyncio.Queue()
    broker = Broker(proxies, timeout=1.51)
    tasks = asyncio.gather(
        broker.find(types=['HTTP'], limit=n),  # , countries=['RU','UA','US','DE']
        save(proxies, proxy_list)
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tasks)

    return proxy_list


def get_proxy_from_file(filename=None):
    proxys = []
    proxy_uniq = []

    if not filename:
        global proxy_file_name
        filename = proxy_file_name

    if platform.system() != 'Windows' and not DEBUG:
        os.chdir('/home/autobro/')

    try:
        with open(os.path.join(os.getcwd(), filename), 'r') as f:
            proxys = list(f)
            proxys = list(map(str.strip, proxys))
    except:
        pass

    for proxy in proxys:
        if proxy not in proxy_uniq:
            proxy_uniq.append(proxy)
    proxys = proxy_uniq

    return proxys


def proxy_add_uniq(n, filename):
    pl = get_proxies(n)
    with open(filename, 'a') as f:
        for p in pl:
            if p not in filename:
                f.write(p + '\n')


def del_proxy(proxy, shared_proxies):
    if proxy in shared_proxies:
        shared_proxies.remove(proxy)
        if DEBUG:
            prnts('del_proxy, proxy deleted: ' + str(proxy))
        else:
            prnts('del_proxy, proxy deleted: ' + str(proxy), 'hide')
        return shared_proxies
    else:
        pass
        prnts('del_proxy, proxy is not found: ' + str(proxy), 'hide')
        return shared_proxies


def join_proxies_to_file(n=50):
    global proxy_file_name
    proxy_from_file = get_proxy_from_file(proxy_file_name)
    # print('Current number of proxies: ' + str(len(proxy_from_file)))
    proxy_add_uniq(n, proxy_file_name)
    proxy_from_file = get_proxy_from_file(proxy_file_name)
    # print('Total number of proxies: ' + str(len(proxy_from_file)))
    return proxy_from_file


def start_proxy_saver(proxies_olimp, proxies_fonbet, proxy_filename_olimp, proxy_filename_fonbet):
    while True:
        prnts('Proxies by Olimp: ' + str(len(proxies_olimp)))  # , 'hide'
        prnts('Proxies by Fonbet: ' + str(len(proxies_fonbet)))

        save_list(proxies_olimp, proxy_filename_olimp)
        save_list(proxies_fonbet, proxy_filename_fonbet)
        time.sleep(15)


proxy_file_name = os.path.join(os.getcwd(), 'proxieslist.txt')


def get_proxys(ol_fl, fb_fl):
    print('start proxy worker')
    proxy_list = []
    proxy_list_olimp = []
    proxy_list_fonbet = []
    proxy_list = join_proxies_to_file(1000)
    proxy_list_olimp = check_proxies_olimp(proxy_list)
    proxy_list_fonbet = check_proxies_fonbet(proxy_list)
    save_list(proxy_list_olimp, ol_fl)
    save_list(proxy_list_fonbet, fb_fl)


def proxy_push(ol_fl, fb_fl):
    copyfile(ol_fl, 'olimp.proxy')
    copyfile(fb_fl, 'fonbet.proxy')


if __name__ == '__main__':
    ol_fl = 'proxy_by_olimp.txt'
    fb_fl = 'proxy_by_fonbet.txt'
    get_proxys(ol_fl, fb_fl)
    # proxy_push(ol_fl, fb_fl)
