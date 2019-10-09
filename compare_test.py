if '__main__'==__name__:
    import time
    from diff_matches import compare_teams
    import re
    
    with open('compare_teams.log', 'r') as f:
        sj = f.readlines()
        sj = list(set(sj))
        add = []
        add_new = []
        print('Найдено ситуаций: ' + str(len(sj)))
        for s in sj:
            e = s.strip().split(';')
            ed = s.strip().split(';')[0]
            if ed == 'add':
                add.append(e[3] + ' - ' + e[4] + ' | ' + e[6] + ' - ' + e[7])
            
        print('Найдено ситуаций: ' + str(len(add)))
        
        print('Применяем новый коэфициент')
        for s in sj:
            e = s.strip().split(';')
            # print(e)
            # time.sleep(5)
            if compare_teams(e[3], e[4], e[6], e[7], debug=False, need=1.5):
                add_new.append(e[3] + ' - ' + e[4] + ' | ' + e[6] + ' - ' + e[7])
                
        print('Найдено ситуаций: ' + str(len(add_new)) + '\n')
        for n in add_new:
            if n not in add:
                print(n)