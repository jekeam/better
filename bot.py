import subprocess
import sys
import utils


def send_msg(msg: str, for_admin: bool = False):
    if msg:
        p = '/home/bot/send_msg.py'
        # p = '/home/ubuntu/environment/bot/bet_fonbet.py'
        out = subprocess.Popen(
            ['python3.6', p, msg, str(for_admin)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True
        )
        stdout, stderr = out.communicate()
        print(stdout, stderr)


if __name__ == '__main__':
    arg = sys.argv
    print(arg)
    send_msg(arg[1], 'False')
