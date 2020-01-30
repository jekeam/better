import subprocess
out = subprocess.Popen(
    # ['python3.6', '/home/bot/bet_fonbet.py'], 
    ['python3.6', '/home/ubuntu/environment/bot/bet_fonbet.py'], 
    stdout=subprocess.PIPE, 
    stderr=subprocess.STDOUT
)
tdout, stderr = out.communicate()
print(int(tdout))

# import sys

# sys.path.insert(1, '/home/ubuntu/environment/bot')
# import bet_fonbet

# from environment.bot import bet_fonbet

# sys.path.append('../bot')
# from bet_fonbet import get_cupon_id
# print(get_cupon_id())