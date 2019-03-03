pair_mathes = [[3, 4], [1, 2]]

cnt = 0
for pair_match in pair_mathes:
    if '1' in str(pair_match):
        print('Fonbet, pair mathes remove: ' + str(pair_mathes[cnt]))
        pair_mathes.remove(pair_mathes[cnt])
    cnt += 1

print(pair_mathes)
