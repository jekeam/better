# coding:utf-8
import pandas as pd

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
