import pandas as pd 
import requests
url = 'https://line-03.ccf4ab51771cacd46d.com/live/currentLine/ru/'
UA = 'Mozilla/5.0 (Windows NT 10; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.3163.100 Safari/537.36'

try:
    df = pd.read_csv('top.csv', encoding='utf-8', sep=';')
    df_all = df[(df['is_top'] != 2)]
    df = df[(df['is_top'] == 2)]
    liga_top = list(df['liga_id'])
    liga_oth = list(df_all['liga_id'])
    print('My liga_top: ' + str(liga_top))
    print('My liga_oth: ' + str(liga_oth))
except Exception as e:
    print('err liga_top: ' + str(e))
    liga_top = []
    liga_oth = []

lags = liga_top + liga_oth
print('lags: ' + str(lags))

resp = requests.get(
    url,
    headers={'User-Agent': UA},
    timeout=10,
    verify=False,
    # proxies=proxies,
)
res = resp.json()
arr_fonbet_top_matchs = []

sport_list = {}
for event in res.get('sports'):
    if event.get('kind') == 'sport':
        sport_list.update({str(event.get('id')): event.get('name')})
print('sport;liga_id;liga_name;by_sort')
for event in res.get('sports'):
    # if 'League VTB' in str(event):
        # print(event)
    if str(event.get('id')) not in arr_fonbet_top_matchs and event.get('kind') == 'segment':
        arr_fonbet_top_matchs.append(str(event.get('id')))
        sport_name = sport_list.get(str(event.get('parentId')), '')
        if sport_name == 'Футбол':
            # print(event)
            print('{};{};{};{}'.format(sport_name, event.get('id'), event.get('name').replace(sport_name + '. ', ''), event.get('sortOrder') ))
            # if event.get('id') in lags:
            #     print('ok')
            # else:
            #     print('err')
print(len(arr_fonbet_top_matchs))