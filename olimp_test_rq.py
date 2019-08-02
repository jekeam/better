import requests

with open('olimp.1.proxy', 'r') as f:
    x = f.readlines()
    for p in x:
        url = 'https://olimpkzapi.ru/api/slice/' if 'https' in p else 'http://olimpkzapi.ru/api/slice/'
        try:
            resp = requests.post(
                url,
                headers={'Content-Type': 'application/x-www-form-urlencoded', 'Connection': 'Keep-Alive', 'Accept-Encoding': 'gzip', 'User-Agent': 'okhttp/3.9.1', 'X-TOKEN': '5d237238e0261be09fa4972dab4a6524'},
                data={'live': 1, 'sport_id': 1, 'platforma': 'ANDROID1', 'lang_id': 0, 'time_shift': 0},
                proxies={'http': p.strip(), 'https': p.strip()},
                verify=False,
                timeout=3
            )
            print(p, resp.status_code)
        except:
            print(p, 'err')