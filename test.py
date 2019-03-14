import re

under_list = [
    'Fighting Maroons-stud. – Growling Tigers-stud.'
]    
    
#for u in lower_list:
for u in under_list:
    if re.search('(u\d{2}|\(w\)|\(r\)|\(res\)|\(Reserves\)|-stud\.)', u.lower()):
        print('del: ' + u)
    else:
        print('add: ' + u)