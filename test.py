from subprocess import call
import re
from exceptions import FonbetMatchСompleted


# script = "cat input | python 1.py > outfile"
# call(script, shell=True)

# print(re.match('\([\d|\d\d]:[\d|\d\d]\)', '(0:0)'))
def d():
    raise FonbetMatchСompleted('aaaa')


try:
    d()
except FonbetMatchСompleted as e:
    raise ValueError('a ' + str(e))
except Exception as e:
    print('b ' + str(e))
