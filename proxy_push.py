# coding: utf-8
from proxy_worker import proxy_push
from utils import bk_working

for bk_name in bk_working:
    try:
        proxy_push(bk_name)
    except:
        pass
