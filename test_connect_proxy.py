import requests
from requests.auth import HTTPProxyAuth
import urllib3
# disable warning
urllib3.disable_warnings()
import time
from random import choice

avg_t = []
avg_2 = []
cnt_err = 0
for x in range(100):
    url = ['fonbet.ru', 'google.ru']
    url = choice(url)
    proxies = {'https': 'https://a89823703090_gmail_com:I6cm0FkE@37.203.246.194:19990'}
    # proxies = {'https': 'https://a89823703090_gmail_com:I6cm0FkE@37.203.243.230:19994'}
    # proxies = {'https': 'https://shaggy:hzsyk4@85.235.82.32:8771'}
    # proxies = {'https': 'https://e8xkdy32:ouebwvc1@92.255.253.230:17658'}
    ct = time.time()
    try:
        response = requests.get(url='https://' + url, proxies=proxies, timeout=10)
        t = round(response.elapsed.total_seconds(), 2)
        t2 = round(time.time()-ct, 2)
        print('url: ' + url + ', ' + str(t) + '/' + str(t2) + ' time, sec.' )
        avg_t.append(t)
        avg_2.append(t2)
    except Exception as e:
        cnt_err += 1
        print('url: ' + url + ', ' + str(e) + ', 10 sec.' )
avg1 = round(sum(avg_t) / len(avg_t), 2)
avg2 = round(sum(avg_2) / len(avg_2), 2)
print('avg: ' + str(avg1) + ', avg2: ' + str(avg2) + ', connect: ' + str(round(avg2-avg1, 2)) +', err: ' + str(cnt_err))