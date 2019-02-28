# coding: utf-8
from hashlib import md5

ol_url_api = "https://{}.olimp-proxy.ru/api/{}"

ol_payload = {"time_shift": 0, "lang_id": "0", "platforma": "ANDROID1"}

ol_headers = {
    'Accept-Encoding': 'gzip',
    'Connection': 'Keep-Alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'okhttp/3.9.1'
}


def get_xtoken_bet(payload):
    secret_key = 'b2c59ba4-7702-4b12-bef5-0908391851d9'
    sorted_values = [str(payload[key]) for key in sorted(payload.keys())]
    to_encode = ";".join(sorted_values + [secret_key])
    return {"X-TOKEN": md5(to_encode.encode()).hexdigest()}
