import subprocess
import sys

def send_msg(msg:str):
    if msg:
        out = subprocess.Popen(
            ['python3.6', '/home/bot/send_msg.py', msg], 
            # ['python3.6', '/home/ubuntu/environment/bot/bet_fonbet.py'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT
        )
        stdout, stderr = out.communicate()
        print(stdout, stderr)
if __name__=='__main__':
    arg = sys.argv
    print(arg)
    send_msg(arg[1])
