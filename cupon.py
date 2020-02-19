import subprocess
import utils

def get_id():
    if utils.DEBUG:
        p = '/home/ubuntu/environment/bot/bet_fonbet.py'
    else:
        p = '/home/bot/bet_fonbet.py'
    out = subprocess.Popen(
            ['python3.6', p], 
        # ['python3.6', '/home/ubuntu/environment/bot/bet_fonbet.py'], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT
    )
    tdout, stderr = out.communicate()
    return int(tdout)