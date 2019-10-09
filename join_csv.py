if __name__=='__main__':
    import pandas as pd
    import os
    import datetime
    
    dt = (datetime.datetime.now()-datetime.timedelta(days=1)).strftime("%d_%m_%Y")
    dtt = input('Укажите день выгрузки, по умолчанию, ' + dt + ': ')
    if dtt:
        dt = dtt
    
    li = []
    is_first = True
    for num in range(0, 10000):
        s = './'+ dt + '_{}' + '_statistics.csv'
        f_name = s.format(num)
        # print(f_name)
        if os.path.isfile(f_name):
            
            df = pd.read_csv(f_name, encoding='utf-8', sep=';', index_col=None)#, header=is_first)
            df.insert(0, 'ACC_ID', num)
            if is_first:
                is_first = False
                
            li.append(df)
            
    frame = pd.concat(li, axis=0, ignore_index=True)
    frame.to_csv(dt + '_join_statistics.csv', encoding='utf-8', sep=';', index=False)