from retry_requests import requests_retry_session
import time

t0 = time.time()
try:
    response = requests_retry_session().get(
        'http://httpbin.org/delay/99',
        timeout=15
    )
except Exception as x:
    print('It failed :(', x.__class__.__name__)
else:
    print('It eventually worked', response.status_code)
finally:
    t1 = time.time()
    print('Took', t1 - t0, 'seconds')