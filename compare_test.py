if '__main__' == __name__:

    def Diff(li1, li2):
        li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2]
        return li_dif


    import time
    from diff_matches import compare_teams
    import re

    with open('compare_teams.log', 'r') as f:
        sj = f.readlines()
        sj = list(set(sj))

        # sj = list(filter(lambda s: 'Ba;Labasa;' in s and 'Ba FC;Labasa;' in s, sj))
        # for x in sj:
        #     print(x.strip())

        # if '' in add_str:
        #         print(add_str)
        add = []
        add_new = []
        print('Найдено ситуаций: ' + str(len(sj)))
        for s in sj:
            e = s.strip().split(';')
            ed = s.strip().split(';')[0]
            if ed == 'add':
                add_str = e[3] + ' - ' + e[4] + ' | ' + e[6] + ' - ' + e[7]
                add.append(add_str)

        print('Найдено ситуаций: ' + str(len(add)))

        need_new = 1.5
        print('Применяем новый коэфициент: ' + str(need_new))
        for s in sj:
            e = s.strip().split(';')
            # print(e)
            # time.sleep(5)
            if compare_teams(e[3], e[4], e[6], e[7], debug=False, need=need_new):
                add_new_str = e[3] + ' - ' + e[4] + ' | ' + e[6] + ' - ' + e[7]
                add_new.append(add_new_str)

        print('Найдено новых ситуаций: ' + str(len(Diff(add, add_new))))
        for n in add_new:
            if n not in add:
                print(n)
