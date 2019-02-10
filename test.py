from subprocess import call
import re

# script = "cat input | python 1.py > outfile"
# call(script, shell=True)

# print(re.match('\([\d|\d\d]:[\d|\d\d]\)', '(0:0)'))

try:
    1 / 0
except ZeroDivisionError:
    raise ValueError('sdafs')
except Exception as e:
    print(e)
