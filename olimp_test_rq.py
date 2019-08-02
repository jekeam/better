import requests

resp = requests.post(
    'https://olimpkzapi.ru/api/slice/',
    headers={'Content-Type': 'application/x-www-form-urlencoded', 'Connection': 'Keep-Alive', 'Accept-Encoding': 'gzip', 'User-Agent': 'okhttp/3.9.1'},
    data={'live': 1, 'sport_id': 1, 'platforma': 'ANDROID1', 'lang_id': 0, 'time_shift': 0},
    # proxies={'https': 'https://84.53.243.199:8080'},
    proxies={'https': 'https://suineg:8veh34@185.161.211.100:2974'},
    verify=False
)

print(resp.status_code, resp.text)