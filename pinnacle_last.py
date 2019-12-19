import requests
import multiprocessing as mp
import datetime
import random
import os
import json
import sys
import traceback
import argparse
import urllib3
urllib3.disable_warnings()

WORK_DIR=os.path.dirname(os.path.abspath(__file__))  
# SPORTS={'tennis':33,'soccer':29,'esports':12,'hockey':19,'volleyball':34}
SPORTS={'soccer':29}
SPORT_NAME='soccer'
PROXY_FILE='proxieslist.txt'
PROXY_REQUEST_TIMEOUT=1
PROXY_TO_USE=10
OUTPUT='pinnacle.json'

def log(step, *messages):
    message=str(datetime.datetime.now())+' '+step+' '+' '.join([str(m) for m in messages])
    print(message)
    with open(os.path.join(WORK_DIR,'pinnacle_log.txt'), 'a') as file:
        file.write(message+'\n')
        file.close()
    return step

def american_to_decimal(odd):
    if odd:
        if odd > 0:
            return (odd/100)+1
        elif odd < 0:
            return abs(100/odd)+1
        else:
            return 0
    else:
        return None

def straight_normalize(straight):
    designations={'over':'Б','under':'М', 'home':'1','away':'2','draw':'Н', None:''}
    periods={1:'1', 2:'2', 0:'', None:''}
    types={'team_total':'ИТ','total':'Т','moneyline':'','spread':'Ф', None:''}
    sides={'home':'1','away':'2', None:''}
    
    norm_designations = lambda x: x if x=='Н' else 'П'+x
    norm_periods = lambda x: '' if ~x else x if x != '0' else ''
      
    unit='У' if straight.get('units', '') == 'Corners' else ''
    try:
        if straight.get('type', '') == 'team_total':
            return {norm_periods(straight.get('period'))+unit+types[straight.get('type')]+designations[straight.get('designation')]+sides[straight.get('side')]+'({})'.format(straight.get('points')):straight}
        if straight.get('type', '') == 'total':
            return {norm_periods(straight.get('period'))+unit+types[straight.get('type')]+designations[straight.get('designation')]+'({})'.format(straight.get('points')):straight}
        if straight.get('type', '') == 'moneyline':
            return {unit+norm_designations(designations[straight.get('designation')]):straight}
        if straight.get('type', '') == 'spread':
            return {norm_periods(straight.get('period'))+unit+types[straight.get('type')]+designations[straight.get('designation')]+'({})'.format('+'+str(straight.get('points','')) if straight.get('points') > 0 != '-' else straight.get('points')):straight}
        else:
            return {}
    except Exception as e:
        return {'error':str(e)}
        
def create_session(prxy):
    sess=requests.Session()
    app=proxy_request(sess, requests.Request('GET', 'https://www.pinnacle.com/config/app.json'), prxy)
    
    return sess, app.json()['api']['haywire']['apiKey']

def get_matchups(sess, app_key, sprt_nm, sprt_id, prxy):
    head={
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': 'https://www.pinnacle.com',
        'referer': 'https://www.pinnacle.com',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        'x-api-key': app_key
        }

    live=proxy_request(sess, requests.Request('GET', 'https://guest.api.arcadia.pinnacle.com/0.1/sports/{}/matchups/live'.format(sprt_id), headers=head), prxy).json()

    data={}
    
    for l in filter(lambda x: (
                               x.get('league',{}).get('sport',{}).get('name', '') != 'Hockey' and x.get('liveMode','') == 'live_delay'
                          #and x.get('units','') == 'Regular' #разкомментить для удаления угловых
                          and x.get('parent',{}).get('participants',[{}])[0].get('name','') == x.get('participants',[{}])[0].get('name','')#закомментить для добавления сетов и геймов
                          ) or (
                              x.get('league',{}).get('sport',{}).get('name','') == 'Hockey'
                              )
                    ,live):
        data[l.get('id')]={
            'match_id':l.get('id'),
            'league':l.get('league',{}).get('group') + '-'+ l.get('league',{}).get('name'),
            'team_alignment1':l.get('participants',[{}])[0].get('alignment'),
            'team_name1':l.get('participants',[{}])[0].get('name'),
            'team_alignment2':l.get('participants',[{},{}])[1].get('alignment'),
            'team_name2':l.get('participants',[{},{}])[1].get('name'),
            'name':l.get('participants',[{},{}])[0].get('name')+'-'+l.get('participants',[{},{}])[0].get('name'),
            'score':str(l.get('participants',[{},{}])[0].get('score'))+':'+str(l.get('participants',[{},{}])[0].get('score')),
            'state':l.get('state',{}).get('state'),
            'minute':float(l.get('state',{}).get('minutes',0)),
            'cur_time':int(datetime.datetime.now().timestamp()),
            'sport_id':sprt_id,
            'sport_name':sprt_nm,
            'time_start':int(datetime.datetime.strptime(l.get('startTime'), '%Y-%m-%dT%H:%M:%SZ').timestamp()),
            'units':l.get('units'),
            'liveMode':l.get('liveMode')
            }
    
    return data

def get_odds(sess, app_key, p_matchups, sprt_id, prxy):
    head={
        'accept': 'application/json',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://www.pinnacle.com',
        'pragma': 'no-cache',
        'referer': 'https://www.pinnacle.com/en/soccer/matchups/live',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        'x-api-key': app_key}

    straight=proxy_request(sess, requests.Request('GET', 'https://guest.api.arcadia.pinnacle.com/0.1/sports/{}/markets/live/straight?primaryOnly=false'.format(sprt_id), headers=head), prxy).json()

    for matchupId in matchups.keys():
        res={}
        for bet in filter(lambda x: x['matchupId'] == matchupId, straight):
            for price in bet.get('prices', []):
                res.update(straight_normalize({
                            'match_id':matchupId, 
                            'type':bet.get('type'), 
                            'side':bet.get('side'), 
                            'period':bet.get('period'), 
                            'designation':price.get('designation'), 
                            'points':price.get('points'), 
                            'price':american_to_decimal(price.get('price')), 
                            'units':matchups[matchupId]['units'],
                            'vector':'UP' if price.get('price') > 0 else 'DOWN'
                            }))
        p_matchups[matchupId]['kofs']=res    

def proxy_request(sess, req, proxy_list, n_proxy_to_use=PROXY_TO_USE, timeout=PROXY_REQUEST_TIMEOUT):
    if proxy_list:
        proxy_gen=iter(proxy_list)
        prepped=req.prepare()
        for i in range(n_proxy_to_use):
            try:
                proxy=next(proxy_gen)
                proxies = {
                     'http': proxy,
                     'https': proxy,
                    }
                return sess.send(prepped, proxies=proxies, timeout=timeout, verify=False)
            except requests.exceptions.ConnectTimeout:
                continue
            except requests.exceptions.ProxyError:
                continue
    else:
        prepped=req.prepare()
        return sess.send(prepped)

def get_proxies():
    if PROXY_FILE != '':
        with open(os.path.join(PROXY_FILE),'r') as file:
            proxylist=file.read().strip().split('\n')
            file.close()
        random.shuffle(proxylist)
        return proxylist
    else:
        None

if __name__ == '__main__':
    try:
        start=datetime.datetime.now()
        step=log('START', start)
        
        step=log('INITIALIZATION')    
    
        parser = argparse.ArgumentParser()
        # parser.add_argument("-n", dest='n', type=str, help="SPORT_NAME", default='soccer')
        parser.add_argument("-pl", dest='pl', type=str, help="PROXY_FILE", default='')
        parser.add_argument("-tm", dest='tm', type=int, help="PROXY_REQUEST_TIMEOUT", default=1)
        parser.add_argument("-pn", dest='pn',type=int, help="PROXY_TO_USE", default=10)
        parser.add_argument("-o", dest='o', type=str, help="OUTPUT", default='pinnacle.json')
        args = parser.parse_args()
        
        step=log('ARGS', args)
        
        # SPORT_NAME=args.n.lower()
        PROXY_FILE=args.pl
        PROXY_REQUEST_TIMEOUT=args.tm
        PROXY_TO_USE=args.pn
        OUTPUT=args.o
        
        step=log('PROXY')
        proxylist=get_proxies()
      
        first_proxies=None
        if proxylist:
            first_proxy=proxylist[-PROXY_TO_USE:-1]
        else:
            first_proxy=None
        
        step=log('CREATE SESSION')
        session, key = create_session(first_proxy)
        step=log('SESSION', key)
        
        sport_id=SPORTS[SPORT_NAME]
    
        for k, val in SPORTS.items():
            step=log('GET MATCHES', k)
            matchups=get_matchups(session, key, k, val, first_proxy)
            step=log('MATCHES', len(matchups))
               
        step=log('COLLECTING DATA')

        if proxylist:
            second_proxy=proxylist[:PROXY_TO_USE]
        else:
            second_proxy=None

        get_odds(session, key, matchups, sport_id, second_proxy)
        
        step=log('WRITING DATA', OUTPUT)
        json.dump(matchups, open(OUTPUT, 'w'))
        
        end=datetime.datetime.now()
        
        step=log('DURATION', end-start)
        step=log('END', end)
        
        session.close()
    except Exception as e:
        ex_type, ex, tb = sys.exc_info()
        log(step, 'ERROR', traceback.print_tb(tb), ex_type, e)