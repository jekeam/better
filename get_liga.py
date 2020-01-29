import requests
import urllib3
import pandas as pd

# disable warning
urllib3.disable_warnings()
url = 'https://line-03.ccf4ab51771cacd46d.com/live/currentLine/ru/?1a4xslry59qk5s4znvy'
UA = 'Mozilla/5.0 (Windows NT 10; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.3163.100 Safari/537.36'


df = pd.read_csv('top.csv', encoding='utf-8', sep=';')
liga = list(df['liga_id'])

df_nf = pd.read_csv('liga_not_found.csv', encoding='utf-8', sep=';')
liga_server = list(df['liga_id'])

print('liga: ' + str(liga))

lags = liga
print('lags: ' + str(lags))

if 1 == 2:
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
            print('{};{};{};{}'.format(sport_name, event.get('id'), event.get('name').replace(sport_name + '. ', ''), event.get('sortOrder')))
    print(len(arr_fonbet_top_matchs))
else:
    from utils import sport_list

    print('sport;liga_id;liga_name;flag;')
    # for sport_data in sport_list:
    # for 
    # url = 'https://www.olimp.bet/apiru/prematch/sport/?id=' + str(sport_data.get('olimp'))
    url = 'https://www.olimp.bet/apiru/prematch/sport/?id=2'
    resp = requests.get(
        url,
        headers={'User-Agent': UA},
        timeout=10,
        verify=False,
        # proxies=proxies,
    )
    res = resp.json()
    # arr_fonbet_top_matchs = []
    x = 0
    for c in res.get('champs'):
        if '. Итоги' in c.get('name'):
            pass
        elif '. Статистика' in c.get('name'):
            pass
        elif '. Специальные предложения' in c.get('name'):
            pass
        else:
            x += 1
            # print(c)
            if c.get('id') in liga:
                pass
                # print('{};{};{};{}'.format(res.get('sport').get('name'), c.get('id'), c.get('name'), 2))
            else:
                print('{};{};{};{}'.format(res.get('sport').get('name'), c.get('id'), c.get('name'), ''))
    # for s in liga_server:
    #     if s not in liga_top and s not in liga_oth:
    #         print(s)
    # print(x)
