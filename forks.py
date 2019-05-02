# coding: utf-8
import pandas as pd
import glob
import sys
import os
from datetime import datetime

cur_date_str = datetime.now().strftime("%d_%m_%Y")
file_forks_raw = 'forks.csv'

if 1 == 1:

    df = pd.read_csv(file_forks_raw, encoding='utf-8', sep=';')
    df = df.round({'minute': 2})

    idx = df.groupby(
        ['time_create', 'kof_ol', 'kof_fb', 'name'], sort=False
    )['live_fork'].transform('max') == df['live_fork']

    df = df[idx]

    idx = df.groupby(
        ['time_create', 'kof_ol', 'kof_fb', 'name'], sort=False
    )['minute'].transform('min') == df['minute']

    df[idx].to_csv(cur_date_str + '_forks_simple.csv', encoding='utf-8', sep=';')
    os.remove(file_forks_raw)
    
else:
    dir = 'D:\\YandexDisk\\Парсинг\\better\\logs\\*.csv'

    files = glob.glob(dir)

    is_first = True

    for f in files:
        f = f.split('\\')[-1]
        f = 'logs/' + str(f)
        print(f)
        df = pd.read_csv(f, encoding='utf-8', sep=';')
        df = df.round({'minute': 2})

        idx = df.groupby(
            ['match_ol', 'match_fb', 'kof_ol', 'kof_fb', 'name'], sort=False
        )['live_fork'].transform('max') == df['live_fork']

        df = df[idx]

        idx = df.groupby(
            ['match_ol', 'match_fb', 'kof_ol', 'kof_fb', 'name'], sort=False
        )['minute'].transform('min') == df['minute']

        with open('forks_live.csv', 'a') as f:
            df[idx]['live_fork'].to_csv(f, encoding='utf-8', sep=';', header=is_first)
            if is_first:
                is_first = False
