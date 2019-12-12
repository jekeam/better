import requests
import utils
import proxy_worker
import exceptions

list_matches_head = {
    'accept': 'application/json',
    'content-type': 'application/json',
    'origin': 'https://www.pinnacle.com',
    'referer': 'https://www.pinnacle.com',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'x-api-key': 'app_key'
}
list_matches_url = 'https://guest.api.arcadia.pinnacle.com/0.1/sports/{}/matchups/live'

api_key = requests.get(
    url='https://www.pinnacle.com/config/app.json',
    verify=False,
    timeout=10,
).json()['api']['haywire']['apiKey']

def get_matches(bk_name, proxy, timeout, api_key):
    if bk_name == 'pinnacle':
        head = list_matches_head
        head.update({'x-api-key': api_key})
        url = list_matches_url
    proxies = {'https': proxy}
    try:
        resp = requests.post(
            url,
            headers=head,
            timeout=timeout,
            verify=False,
            proxies=proxies,
        )
        try:
            res = resp.json()
        except Exception as e:
            err_str = bk_name + ' error : ' + str(e)
            utils.prnts(err_str)
            raise ValueError('Exception: ' + str(e))

        if res.status_code == 200:
            return res, resp.elapsed.total_seconds()
        else:
            err_str = res.get("error")
            err_str = bk_name + ' error : ' + str(err_str)
            utils.prnts(err_str)
            raise ValueError(str(err_str))

    except requests.exceptions.Timeout as e:
        err_str = bk_name + ', код ошибки Timeout: ' + str(e)
        utils.prnts(err_str)
        proxies = proxy_worker.del_proxy(proxy, proxies)
        raise exceptions.TimeOut(err_str)
    except requests.exceptions.ConnectionError as e:
        err_str = bk_name + ', код ошибки ConnectionError: ' + str(e)
        utils.prnts(err_str)
        proxies = proxy_worker.del_proxy(proxy, proxies)
        raise ValueError(err_str)
    except requests.exceptions.RequestException as e:
        err_str = bk_name + ', код ошибки RequestException: ' + str(e)
        utils.prnts(err_str)
        proxies = proxy_worker.del_proxy(proxy, proxies)
        raise ValueError(err_str)
    except ValueError as e:
        if str(e) == '404':
            raise exceptions.MatchСompleted(bk_name + ', матч завершен, поток выключен!')

        if resp.text:
            text = resp.text
        err_str = 'Олимп, код ошибки ValueError: ' + str(e) + str(text)
        utils.prnts(err_str)
        proxi_list = proxy_worker.del_proxy(proxy, proxies)
        raise ValueError(err_str)
    except Exception as e:
        err_str = 'Олимп, код ошибки Exception: ' + str(e)
        utils.prnts(err_str)
        proxies = proxy_worker.del_proxy(proxy, proxies)
        raise ValueError(err_str)
