from subprocess import call
import re
# script = "cat input | python 1.py > outfile"
# call(script, shell=True)

print(re.match('\([\d|\d\d]:[\d|\d\d]\)', '(0:0)'))