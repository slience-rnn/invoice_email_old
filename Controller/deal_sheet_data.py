'''
function: 处理google sheets中的数据
'''
import pandas as pd
import numpy as np


def deal_sheet_data(raw_data,header,start,name=None):
    first_column_name = ' Client No.'
    engnaem_column_name = 'Last Name (Eng)'
    columns_num = 0
    # 税務代表费用赠送', 'Gift Pack Inclued \nTax Repres.  (Y/N)', 'Property community\n or separation ', 'Signed Date', 'Start Date \n(Info from PTA)', 'Finish Date', 'Start charging from', '2024', '2023/12/31', 'TAX REP FEE ', 'Paid On', '2025', '2025/12/31', 'TAX REP FEE ', 'Tax Rep Fee Paid Date', '2026', '2026/12/31', 'TAX REP FEE ', 'Tax Rep Fee Paid Date', 'FGI REMARKS\n[FGI自行备注]']
    processed_data = [row[:len(header)] + [''] * (len(header) - len(row)) for row in raw_data]   # 自动截断或者补齐
    df_data = pd.DataFrame(data = processed_data,columns = header)
    try:
        #print(f'开始处理原始数据{raw_data}')
        # 将所有的行从3开始加一个数字
        if name == 'summSheet':
            df_data['location'] = ['SummSheet!B'+ str(i+start) for i in df_data.index]
            
        df_data = df_data[~df_data[first_column_name].isin(['',' '])]     # 逐个元素去判断
        df_data = df_data[~df_data['Last Name (Eng)'].isin(['Withdraw','',' '])]
        #print('90%')
        df_data.set_index([first_column_name],inplace=True)
        print(f'处理后\n{df_data}')
        return df_data
    except Exception as e:
        print(e)
        return f'{e}'

# 