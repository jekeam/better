# coding:utf-8
import pandas as pd

df = pd.read_csv('forks.csv', encoding='utf-8', sep=';')

idx = df.groupby(
    ['create_fork', 'kof_ol', 'kof_fb', 'name'], sort=False
)['live_fork'].transform('max') == df['live_fork']

df[idx].to_csv('forks_simple.csv', encoding='utf-8', sep=';')
