# coding: utf-8
import pandas as pd
import glob
import sys
import os

if 1 == 1:

    df = pd.read_csv('forks.csv', encoding='utf-8', sep=';')
    df = df.round({'minute': 2})

    idx = df.groupby(
        ['create_fork', 'kof_ol', 'kof_fb', 'name'], sort=False
    )['live_fork'].transform('max') == df['live_fork']

    df = df[idx]

    idx = df.groupby(
        ['create_fork', 'kof_ol', 'kof_fb', 'name'], sort=False
    )['minute'].transform('min') == df['minute']

    df[idx].to_csv('forks_simple.csv', encoding='utf-8', sep=';')
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
