import statistics
def find_max_mode(list1):
    list_table = statistics._counts(list1)
    len_table = len(list_table)

    if len_table == 1:
        max_mode = statistics.mode(list1)
    else:
        new_list = []
        for i in range(len_table):
            new_list.append(list_table[i][0])
        max_mode = max(new_list)
    return max_mode

if '__main__' == __name__:
    import sys

    def Diff(li1, li2):
        li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2]
        return li_dif


    import time
    from diff_matches import compare_teams
    import re

    with open('compare_teams.log', 'r') as f:
        sj = f.readlines()
        sj = list(set(sj))

        sj = list(filter(lambda s: 'Universitario' in s, sj))
        for x in sj:
            print(x.strip())

        # if '' in add_str:
        #         print(add_str)
        add = []
        add_new = []
        i = []
        nn = []
        print('Всего ситуаций: ' + str(len(sj)))
        for s in sj:
            e = s.strip().split(';')
            ed = s.strip().split(';')[0]
            if ed == 'add':
                add_str = e[3] + ' - ' + e[4] + ';' + e[6] + ' - ' + e[7]
                add.append(add_str)
        

        print('Найдено ситуаций: ' + str(len(add)))

        try:
            arg = sys.argv[1]
        except:
            arg = None
        if arg:
            need_new = float(arg)
        else:
            need_new = 1.5
        print('Применяем новый коэфициент: ' + str(need_new))
        for s in sj:
            e = s.strip().split(';')
            # print(e)
            # time.sleep(5)
            cur_val = compare_teams(e[3], e[4], e[6], e[7], debug=False, need=need_new)
            nn.append(cur_val)
            if cur_val > need_new:
                add_new_str = e[3] + ' - ' + e[4] + ';' + e[6] + ' - ' + e[7]
                add_new.append(add_new_str)

        print('Найдено новых ситуаций: ' + str(len(Diff(add, add_new))))
        print('Название в БК1;БК2; Верно ли сопоставилось;')
        for n in add_new:
            if n not in add:
                print(n + ';')
        
        # print(list(filter(lambda x: x > 1, nn)))
