def compare_teams(team1_bk1, team2_bk1, team1_bk2, team2_bk2, debug=False, need=1.7):
    from difflib import SequenceMatcher
    import sys
    import re
    
    if debug:
        fstr = team1_bk1 + '->{}\n' + team1_bk2 + '->{}\n\n' + team2_bk1 + '->{}\n' + team2_bk2 + '->{}'
    if team1_bk1 and team2_bk1 and team1_bk2 and team2_bk2:
        team1_bk1 = re.sub('[^A-z 0-9]', '', str(team1_bk1).lower()).replace(' ', '')
        team2_bk1 = re.sub('[^A-z 0-9]', '', str(team2_bk1).lower()).replace(' ', '')
        team1_bk2 = re.sub('[^A-z 0-9]', '', str(team1_bk2).lower()).replace(' ', '')
        team2_bk2 = re.sub('[^A-z 0-9]', '', str(team2_bk2).lower()).replace(' ', '')
        if debug:
            fstr = fstr.format(team1_bk1, team1_bk2, team2_bk1, team2_bk2)
            print(fstr)

        r1 = SequenceMatcher(None, team1_bk1, team1_bk2).ratio()
        r2 = SequenceMatcher(None, team2_bk1, team2_bk2).ratio()
        rate = r1 + r2

        if debug:
            print('k1: {}, k2: {}. All: {}, need: {}, res: {}'.format(r1, r2, rate, need, need < rate))
        if need < rate:
            return True

if __name__=='__main__':
    
    # bk1_t1, bk1_t2, bk2_t1, bk2_t2 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    bk1_t1 = input('Fonbet Team 1:')
    bk1_t2 = input('Fonbet Team 2:')
    bk2_t1 = input('Olimp Team 1:')
    bk2_t2 = input('Olimp Team 2:')
    compare_teams(bk1_t1, bk1_t2, bk2_t1, bk2_t2, True)
