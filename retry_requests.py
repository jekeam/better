# coding:utf-8
import requests
from requests.exceptions import Timeout, ProxyError
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import functools
import time
from utils import prnt

cnt_retry = 0


def requests_retry_session(
        retries=3,
        backoff_factor=0.3,
        status_forcelist=(500, 501, 502, 504),
        session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def retry(exceptions, delay=0, times=2):
    """
    A decorator for retrying a function call with a specified delay in case of a set of exceptions

    Parameter List
    -------------
    :param exceptions:  A tuple of all exceptions that need to be caught for retry
                                        e.g. retry(exception_list = (Timeout, Readtimeout))
    :param delay: Amount of delay (seconds) needed between successive retries.
    :param times: no of times the function should be retried


    """

    def outer_wrapper(function):
        @functools.wraps(function)
        def inner_wrapper(*args, **kwargs):
            final_excep = None
            for counter in range(times):
                if counter > 0:
                    time.sleep(delay)
                final_excep = None
                try:
                    value = function(*args, **kwargs)
                    return value
                except (exceptions) as e:
                    final_excep = e
                    prnt('retry_requests 1: ' + str(final_excep))
                    pass
            if final_excep is not None:
                prnt('retry_requests 2: ' + str(final_excep))
                raise final_excep

        return inner_wrapper

    return outer_wrapper


@retry(exceptions=(Timeout, ProxyError), delay=1, times=4)
def requests_retry_session_post(url: str, headers=None, data=None, json=None, verify=None, timeout=None, proxies=None):
    global cnt_retry
    cnt_retry += 1
    prnt('retry_requests: execute requests_retry_session_post, retry: {}, url:{}'.format(cnt_retry, url))
    resp = requests_retry_session().post(url=url, headers=headers, data=data, json=json, verify=False, timeout=20, proxies=proxies)
    cnt_retry = 0
    return resp
