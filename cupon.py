import subprocess

def get_id():
    out = subprocess.Popen(
        ['python3.6', '/home/bot/bet_fonbet.py'], 
        # ['python3.6', '/home/ubuntu/environment/bot/bet_fonbet.py'], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT
    )
    tdout, stderr = out.communicate()
    return int(tdout)