import requests
import urllib3
import pandas as pd

# disable warning
urllib3.disable_warnings()
url = 'https://line-03.ccf4ab51771cacd46d.com/live/currentLine/ru/?1a4xslry59qk5s4znvy'
UA = 'Mozilla/5.0 (Windows NT 10; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.3163.100 Safari/537.36'

df = pd.read_csv('top.csv', encoding='utf-8', sep=';')
df = df.fillna(0)
df.is_top = df.is_top.astype(int)
liga = list(df['liga_id'])

df_nf = pd.read_csv('liga_not_found.csv', encoding='utf-8', sep=';')
liga_server = list(df['liga_id'])

print('liga: ' + str(liga))

ligas = liga
print('ligas: ' + str(ligas))

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
elif 1 == 0:  # список для разметки

    from utils import sport_list

    print('sport;liga_id;liga_name;flag;')
    # for sport_data in sport_list:
    # for 
    # url = 'https://www.olimp.bet/apiru/prematch/sport/?id=1' + str(sport_data.get('olimp'))
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
        if live:
            c = c.get('champ')
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
elif 1==0:  # Обработанный список
    # POST https://api2.olimp.bet/api/champs HTTP/1.1
    # X-TOKEN: 5a6a276c40bf0b24c639bde74c210b98
    # X-CUPIS: 1
    # Content-Type: application/x-www-form-urlencoded
    # Content-Length: 54
    # Host: api2.olimp.bet
    # Connection: Keep-Alive
    # Accept-Encoding: gzip
    # User-Agent: okhttp/3.12.1
    # live=0&sport_id=1&session=&platforma=CUPISA2&lang_id=2
    url = 'https://api2.olimp.bet/api/champs'
    from util_olimp import head, olimp_data, olimp_secret_key, olimp_get_xtoken

    olimp_data = olimp_data.copy()
    olimp_data.update({'live': '0', 'sport_id': 1, 'lang_id': 2})
    olimp_data.pop('time_shift')
    head = head.copy()
    head.update(olimp_get_xtoken(olimp_data, olimp_secret_key))
    head.pop('Accept-Language', None)
    print(head)
    # print(v_url, olimp_data_ll, proxies)
    # {'id': 1643805, 'cid': 1530550, 'n': 'Switzerland. Super League. Outrights', 'com': '', 'so': 1, 'sn': 'Soccer', 'max': 250000, 'cgi': 10, 'co': 204, 'io': 1, 'is': False, 'top': 0, 'top_b': 0, 'sort': 176}
    resp = requests.post(
        url,
        data=olimp_data,
        headers=head,
        timeout=10,
        verify=False,
    )
    print('liga_name;is_top;')
    for l in resp.json().get('data'):
        # print(l)
        liga_name = l.get('n')
        # if list(df[df['liga_id'] == l.get('id')]):
        #     x = 'id'
        # elif list(df[df['liga_id'] == l.get('cid')]):
        #     x = 'cid'
        if 'statistics' not in liga_name.lower() and 'outrights' not in liga_name.lower()  and 'special offers' not in liga_name.lower():
            x = ''
            if l.get('id') in list(df['liga_id']):
                x = l.get('id')
            elif l.get('cid') in list(df['liga_id']):
                x = l.get('cid')
            # print('{}, {}, {}, {}, {}, {}'.format(x, l.get('id'), l.get('cid'), liga_name, l.get('so'), l.get('sn')))
            # print('{}, {}, {}, {}, {}, {}'.format(x, l.get('id'), l.get('cid'), liga_name, l.get('so'), l.get('sn')))
            print('{};{}'.format(liga_name, df[(df['liga_id'] == x)]['is_top'].values[0]))

if 1 == 1:
    import json
    text = ''
    x = 0
    liga_slices_dot = []
    liga_slices_space = []
    with open('top_by_name.csv', 'r') as file:
        rows = file.readlines()
        for row in rows:
            if x > 0:
                liga_name = row.split(';')[0].strip()
                liga_slice = liga_name.split('. ')
                liga_slices_dot.append(liga_slice[0])
                
                liga_name = liga_name.replace('.', '').replace('  ', ' ')
                liga_slice = liga_name.split(' ')
                for k in liga_slice:
                    liga_slices_space.append(k)
                
                # text = text + 
            x = 1
    liga_slices_arr = {}        
    for i in liga_slices_dot:
        liga_slices_arr.update({i :liga_slices_dot.count(i)})
    print('Предложение;кол-во')
    split_dott = {k: v for k, v in reversed(sorted(liga_slices_arr.items(), key=lambda item: item[1]))}
    for n, c in split_dott.items():
        print(n + ';' + str(c))
    
    liga_slices_arr = {}        
    for i in liga_slices_space:
        liga_slices_arr.update({i :liga_slices_space.count(i)})
    print('Слово;кол-во')
    split_space = {k: v for k, v in reversed(sorted(liga_slices_arr.items(), key=lambda item: item[1]))}
    for n, c in split_space.items():
        print(n + ';' + str(c))