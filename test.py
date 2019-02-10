from subprocess import call
script = "cat input | python 1.py > outfile"
call(script, shell=True)