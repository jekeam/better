# coding: utf-8
from proxy_worker import proxy_push
from utils import bk_fork_name

for bk_name in bk_fork_name:
    try:
        proxy_push(bk_name)
    except:
        pass
