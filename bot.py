import subprocess
import sys
import utils

def send_msg(msg:str):
    if not utils.DEBUG:
        if msg:
            if utils.DEBUG:
                p = '/home/bot/send_msg.py'
            else:
                p = '/home/ubuntu/environment/bot/bet_fonbet.py'
            out = subprocess.Popen(
                ['python3.6', p, msg], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT
            )
            stdout, stderr = out.communicate()
            print(stdout, stderr)
if __name__=='__main__':
    arg = sys.argv
    print(arg)
    send_msg(arg[1])