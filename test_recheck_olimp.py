import time
from hashlib import md5
import requests

olimp_secret_key = 'b2c59ba4-7702-4b12-bef5-0908391851d9'

olimp_head = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'User-Agent': 'okhttp/3.9.1'
}

olimp_data = {
    "live": 1,
    # "sport_id": 1,
    "sport_id": 1,
    "platforma": "ANDROID1",
    "lang_id": 0,
    "time_shift": 0
}


def olimp_get_xtoken(payload, secret_key):
    sorted_values = [str(payload[key]) for key in sorted(payload.keys())]
    to_encode = ";".join(sorted_values + [secret_key])
    return {"X-TOKEN": md5(to_encode.encode()).hexdigest()}


olimp_url = 'http://176.223.130.230:10600'  # http://olimp.com

proxy = {'http': 'http://85.11.124.195:80'}

olimp_data_ll = olimp_data.copy()
olimp_data_ll.update({'lang_id': 2})

olimp_head_ll = olimp_head
olimp_head_ll.update(olimp_get_xtoken(olimp_data_ll, olimp_secret_key))

olimp_head_ll.pop('Accept-Language', None)
while True:
    resp = requests.post(
        olimp_url + '/api/slice/',
        data=olimp_data_ll,
        headers=olimp_head_ll,
        timeout=5.51,
        verify=False,
        proxies=proxy,
    )
    print(resp)
    #time.sleep(1)
