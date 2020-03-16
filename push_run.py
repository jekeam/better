# coding:utf-8
import subprocess
import time

if __name__=='__main__':
    subprocess.call('systemctl stop scan.service', shell=True)
    time.sleep(5)
    subprocess.call('python3.6 forks.py', shell=True, cwd='/home/scan/')
    time.sleep(5)
    subprocess.call('python3.6 proxy_push.py', shell=True, cwd='/home/scan/')
    time.sleep(5)
    subprocess.call('systemctl restart scan.service', shell=True)