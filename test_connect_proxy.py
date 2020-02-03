import requests
from requests.auth import HTTPProxyAuth
import urllib3
# disable warning
urllib3.disable_warnings()
import time
from random import choice

for x in range(10):
    url = ['https://fonbet.ru/', 'https://google.ru/']
    url = choice(url)
    # proxies = {'https': 'https://a89823703090_gmail_com:I6cm0FkE@37.203.246.194:19990'}
    # proxies = {'https': 'https://a89823703090_gmail_com:I6cm0FkE@37.203.243.230:19994'}
    proxies = {'https': 'https://shaggy:hzsyk4@85.235.82.32:8771'}
    ct = time.time()
    try:
        response = requests.get(url=url, proxies=proxies, timeout=10)
        print('url: ' + url + ', ' + str(round(time.time()-ct, 2)) + ' time, sec.' )
    except TimeOut:
        print('url: ' + url + ', timeOut, 10 sec.' )