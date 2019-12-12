# coding:utf-8
# import pandas
# import os
import matplotlib.pyplot as plt

val = [2.15, 2.1, 2.02, 2.1, 2.15]
sec = [154, 175, 47, 111, 79]

arr = list(zip(val, sec))

x = []
y = []
n = 1
for p in arr:
    for t in range(1, p[1]):
        x.append(n)
        y.append(p[0])
        n += 1
plt.scatter(x, y, color='blue', marker=',')
plt.show()
if 1 == 2:
    dir_name = '/mnt/278307951A2C09B7/Yandex.Disk/Вилки/dataset'

    listOfFile = os.listdir(dir_name)
    allFiles = list()
    # Iterate over all the entries
    dfs = []
    for file_name in listOfFile:
        if 'lock' not in file_name:
            try:
                fill_path = os.path.join(dir_name, file_name)
                df = pandas.read_csv(fill_path, encoding='utf-8', sep=';')
                idx = df.groupby(['kof_ol', 'kof_fb', 'name'], sort=False)['live_fork_total'].transform('max') == df['live_fork_total']

                df = df[idx]
                # df1 = df[['kof_ol', 'kof_fb', 'name', 'ol_kof_order', 'ol_avg_change']]
                df1 = df[['ol_kof_order', 'ol_avg_change']]
                df1.insert(1, 'system_name', 'o')
                df1 = df1.rename(columns={'ol_kof_order': 'val', 'ol_avg_change': 'sec'})

                # df2 = df[['kof_ol', 'kof_fb', 'name', 'fb_kof_order', 'fb_avg_change']]
                df2 = df[['fb_kof_order', 'fb_avg_change']]
                df2.insert(1, 'system_name', 'f')
                df2 = df2.rename(columns={'fb_kof_order': 'val', 'fb_avg_change': 'sec'})

                dfs.append(df1)
                dfs.append(df2)
                print(file_name + ': ok')
            except Exception as e:
                print(file_name + ': ' + str(e))

    frame = pandas.concat(dfs, axis=0, ignore_index=True, sort=False)
    frame = frame[['system_name', 'val', 'sec']]
    frame.to_csv(os.path.join(dir_name, 'test.csv'), encoding='utf-8', sep=';', index=False)
