import subprocess

def send_msg(msg:str):
    if msg:
        ar = '/home/bot/send_msg.py --m "' + msg + '"'
        out = subprocess.Popen(
            ['python3.6', ar], 
            # ['python3.6', '/home/ubuntu/environment/bot/bet_fonbet.py'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT
        )
        tdout, stderr = out.communicate()
        # return int(tdout)