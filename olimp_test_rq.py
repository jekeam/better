import requests

resp = requests.post(
    'https://olimpkzapi.ru/api/slice/',
    headers={'Content-Type': 'application/x-www-form-urlencoded', 'Connection': 'Keep-Alive', 'Accept-Encoding': 'gzip', 'User-Agent': 'okhttp/3.9.1', 'X-TOKEN': '5d237238e0261be09fa4972dab4a6524'},
    data={'live': 1, 'sport_id': 1, 'platforma': 'ANDROID1', 'lang_id': 0, 'time_shift': 0},
    proxies={'https': 'https://84.53.243.199:8080'},
    verify=False
)

print(resp.status_code, resp.text)