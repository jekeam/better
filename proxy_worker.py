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

TIME_OUT = 3
CHUNKS = 500

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3163.100 Safari/537.36'


# не подошел для многопоточности
def get_next_proxy(proxi_list):
    for n, i in list(enumerate(proxi_list)):
        # prnts('Get next proxy: ' + i, 'hide')
        prnts('Proxy left: ' + str(len(proxi_list) - n) + '/' + str(len(proxi_list)))
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


def get_random_proxy(proxi_list):
    curr_proxy = choice(proxi_list)
    if curr_proxy.replace(' ', ''):
        return curr_proxy
    else:
        get_random_proxy(proxi_list)
        return False


def check_proxy_olimp(proxies_for_check, valid_proxies):
    from util_olimp import olimp_head, olimp_data, olimp_get_xtoken, olimp_url, olimp_url_https, olimp_secret_key
    global TIME_OUT

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
            http_type = 'https' if 'https' in prx else 'http'
            url = olimp_url_https if 'https' in http_type else olimp_url
            proxies = {http_type: prx}
            resp = requests.post(
                url + '/api/slice/',
                headers=olimp_head_ll,
                data=olimp_data_ll,
                proxies=proxies,
                timeout=TIME_OUT,
                verify=False
            )
            resp.json()
            print('o valid: ' + str(prx), str(resp.status_code))
            x = x + 1
            if prx not in valid_proxies:
                valid_proxies.append(prx)
        except ValueError as e:
            print('o invalid: ' + str(prx), str(e), str(resp.text))
        except Exception as e:
            pass
            print('o invalid: ' + str(prx), str(e))


def check_proxy_fonbet(proxies_for_check, valid_proxies):
    from util_fonbet import url_fonbet_matchs as url_fonbet
    global TIME_OUT

    for prx in proxies_for_check:
        # http_type = 'http' if 'https' in prx else 'http'
        try:
            global url_fonbet
            global UA
            resp = requests.get(
                url_fonbet,
                headers={'User-Agent': UA},
                proxies={'http': prx},
                timeout=TIME_OUT,
                verify=False
            )
            print('f valid: ' + str(prx), str(resp.status_code))
            if prx not in valid_proxies:
                valid_proxies.append(prx)
        except Exception as e:
            pass
            print('f invalid: ' + str(prx), str(e))


def check_proxy(proxies_for_check, valid_proxies, url, headers):
    global TIME_OUT

    for prx in proxies_for_check:
        http_type = 'https' if 'https' in prx else 'http'
        try:
            resp = requests.get(
                http_type + '://' + url,
                headers=headers,
                proxies={http_type: prx},
                timeout=TIME_OUT,
                verify=False
            )
            print('f valid: ' + str(prx), str(resp.status_code))
            if prx not in valid_proxies:
                valid_proxies.append(prx)
        except Exception as e:
            pass
            print('f invalid: ' + str(prx), str(e))


def check_proxies(proxies_list, url, headers):
    mgr = mp.Manager()
    valid_proxies_list = mgr.list()

    n_chunks = CHUNKS
    chunks = [proxies_list[i::n_chunks] for i in range(n_chunks)]

    prcs = []
    for chunk in chunks:
        p = mp.Process(target=check_proxy, args=(chunk, valid_proxies_list, url, headers))
        prcs.append(p)
        p.start()

    for p in prcs:
        p.join()

    return valid_proxies_list


def check_proxies_olimp(proxies_list):
    mgr = mp.Manager()
    valid_proxies_list = mgr.list()

    n_chunks = CHUNKS
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

    n_chunks = CHUNKS
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
    x = 0
    while True:
        proxy = await proxies.get()
        if proxy is None:
            break
        proto = 'https' if 'HTTPS' in proxy.types else 'http'
        row = '%s://%s:%d' % (proto, proxy.host, proxy.port)
        proxy_list.append(row)
        x = x + 1
        prnts(x)


def save_list(proxies, filename=None, clone=1):
    """Save proxies to a file."""
    if not filename:
        global proxy_file_name
        filename = proxy_file_name

    cd()

    with open(filename, 'w') as f:

        if clone > 1:
            proxies = proxies * clone

        for p in proxies:
            f.write(p + '\n')


def get_proxies(n):
    global proxy_list, TIME_OUT
    proxies = asyncio.Queue()
    broker = Broker(proxies, timeout=TIME_OUT)
    tasks = asyncio.gather(
        broker.find(types=['HTTP', 'HTTPS'], limit=n),  # , countries=['RU','UA','US','DE']
        save(proxies, proxy_list)
    )
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(tasks)
    except Exception as e:
        print(e)

    return proxy_list


def get_proxy_from_file(filename=None, uniq=True):
    proxys = []
    proxy_uniq = []
    cd()

    if not filename:
        global proxy_file_name
        filename = proxy_file_name

    try:
        with open(filename, 'r') as f:
            proxys = list(f)
            proxys = list(map(str.strip, proxys))
    except:
        pass

    for proxy in proxys:
        if proxy not in proxy_uniq:
            proxy_uniq.append(proxy)

    if uniq:
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
    print('Current number of proxies ' + proxy_file_name + ': ' + str(len(proxy_from_file)))
    proxy_add_uniq(n, proxy_file_name)
    proxy_from_file = get_proxy_from_file(proxy_file_name)
    print('Total number of proxies: ' + proxy_file_name + ': ' + str(len(proxy_from_file)))
    return proxy_from_file


def start_proxy_saver(proxies_olimp, proxies_fonbet, proxy_filename_olimp, proxy_filename_fonbet):  # , gen_proxi_olimp, gen_proxi_fonbet
    while True:
        prnts('Proxies by Olimp: ' + str(len(proxies_olimp)))  # + '/' + str(gen_proxi_olimp.__next__()))  # , 'hide'
        prnts('Proxies by Fonbet: ' + str(len(proxies_fonbet)))  # + '/' + str(gen_proxi_fonbet.__next__()))

        save_list(proxies_olimp, proxy_filename_olimp)
        save_list(proxies_fonbet, proxy_filename_fonbet)
        time.sleep(15)


proxy_file_name = 'proxieslist.txt'


def proxy_push(bk_name):
    bk_name = bk_name.lower()
    copyfile('proxy_by_' + bk_name + '.txt', bk_name + '.proxy')


def cd():
    if platform.system() != 'Windows' and not DEBUG:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))


ol_fl = 'proxy_by_olimp.txt'
fb_fl = 'proxy_by_fonbet.txt'
pn_fl = 'proxy_by_pinnacle.txt'

if __name__ == '__main__':
    prnts('get api_key from pinnacle')
    url_pinnacle = 'www.pinnacle.com'
    app_key = requests.get('https://' + url_pinnacle + '/config/app.json').json()['api']['haywire']['apiKey']
    prnts('pinnacle app_key: ' + app_key)
    headers_pinnacle = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': 'https://' + url_pinnacle,
        'referer': 'https://' + url_pinnacle,
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        'x-api-key': app_key
    }
    # url_pinnacle = 'guest.api.arcadia.pinnacle.com/0.1/sports/29/matchups/live'
    url_pinnacle = 'guest.api.arcadia.pinnacle.com/0.1/sports/29/markets/live/straight?primaryOnly=false'

    prnts('start proxy worker')

    proxy_list = []
    proxy_list_olimp = []
    proxy_list_fonbet = []
    proxy_list = join_proxies_to_file(10000)

    prnts('cnt https: ' + str(len(list(filter(lambda p: 'https' in p, proxy_list)))))
    prnts('cnt http: ' + str(len(list(filter(lambda p: 'http:' in p, proxy_list)))))
    prnts('cnt all: ' + str(len(proxy_list)))
    time.sleep(3)

    # PINNACLE
    # proxy_list_pinnacle = get_proxy_from_file('proxy_by_pinnacle.txt')
    proxy_list_pinnacle = proxy_list
    proxy_list_https = (list(filter(lambda p: 'https' in p, proxy_list_pinnacle)))
    proxy_list_pinnacle = check_proxies(proxy_list_https, url_pinnacle, headers_pinnacle)
    save_list(proxy_list_pinnacle, pn_fl)

    # FB
    proxy_list_fonbet = check_proxies_fonbet(proxy_list)
    save_list(proxy_list_fonbet, fb_fl)

    # OL
    proxy_list = get_proxy_from_file('proxy_for_olimp.txt')
    proxy_list = (list(filter(lambda p: 'https' in p, proxy_list)))
    proxy_list_olimp = check_proxies_olimp(proxy_list)
    save_list(proxy_list_olimp, ol_fl, clone=2000)
