x = {'team1': '1', 'team2': None} 

if [x for x in x.values() if x is not None]:
    print(x)