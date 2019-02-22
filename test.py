from run import opposition, get_vector
import re

o = opposition

for x in o:
    try:
        print(x+';'+ get_vector(x, 1, 0))
    except Exception as e:
        print(x+';'+str(e))