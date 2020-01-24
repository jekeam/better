import requests
import urllib3
# disable warning
urllib3.disable_warnings()
url = 'https://line-03.ccf4ab51771cacd46d.com/live/currentLine/ru/?1a4xslry59qk5s4znvy'
UA = 'Mozilla/5.0 (Windows NT 10; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.3163.100 Safari/537.36'

if 1==2:
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
            print('{};{};{};{}'.format(sport_name, event.get('id'), event.get('name').replace(sport_name + '. ', ''), event.get('sortOrder') ))
    print(len(arr_fonbet_top_matchs))
else:
    from utils import sport_list

    print('sport;liga_id;liga_name;total;stat;')
    for sport_data in sport_list:
        url = 'https://www.olimp.bet/apiru/prematch/sport/?id=' + str(sport_data.get('olimp'))
        resp = requests.get(
            url,
            headers={'User-Agent': UA},
            timeout=10,
            verify=False,
            # proxies=proxies,
        )
        res = resp.json()
        # arr_fonbet_top_matchs = []
        for c in res.get('champs'):
            if '. Итоги' in c.get('name'):
                pass
            else:
                print('{};{};{};{};{}'.format(res.get('sport').get('name'), c.get('id'), c.get('name'), c.get('total'), c.get('stat')))