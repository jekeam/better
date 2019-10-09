if '__main__'==__name__:
    import time
    from diff_matches import compare_teams
    import re
    
    with open('compare_teams.log', 'r') as f:
        sj = f.readlines()
        sj = list(set(sj))
        add = 0
        add_new = 0
        print('Найдено ситуаций: ' + str(len(sj)))
        for s in sj:
            e = s.strip().split(';')[0]
            if e == 'add':
                add += 1
            
        print('Найдено ситуаций: ' + str(add))
        
        print('Применяем новый коэфициент')
        for s in sj:
            e = s.strip().split(';')
            # print(e)
            # time.sleep(5)
            if compare_teams(e[3], e[4], e[6], e[7], debug=False, need=1.7):
                add_new += 1
                
        print('Найдено ситуаций: ' + str(add_new))