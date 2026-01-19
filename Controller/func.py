from datetime import datetime
import pandas as pd
def num_to_3(num):
    data = str(num)
    if len(data)!=3:
        return '0'*(3-len(data))+data
    else:
        return str(data)

def current(data,type=0):
    # 去掉前后空格
    # print(data)
    if type == 0:
        data = data[1:].strip()    # 1,000.00->
    
    # 去掉逗号
    data = data.replace(',','')
    if data in ['',' ']:
        return 0
    if float(data) == 0.0:
        return 0
    return float(data)

def days_until_year_end(date:datetime):
    given_year = date.year
    end_of_year = datetime(given_year,12,31)
    delta = end_of_year - date
    #start_year_11 = datetime(da,1,1)
    return delta.days

def str_date_str(date:str,spl:str = '/',type:int = 0):
    # 将字符串转成时间
    str2time = datetime.strptime(date,f'%Y{spl}%m{spl}%d')
    if type == 0:
        return datetime.strftime(str2time,'%Y%m%d')
    if type == 1: # May 06，2025
        return datetime.strftime(str2time,'%B %d, %Y')
    # return time2str

def progress_employee_client(employee_csv: pd.DataFrame, client_data: pd.DataFrame, progress_data: pd.DataFrame):
    """
    为每个 client 添加对应的 CS_email
    """
    client_data['CS_email'] = client_data.apply(lambda x: map_employee(employee_csv, progress_data, x), axis=1)
    return client_data  # 返回修改后的 DataFrame

def map_employee(employee_csv: pd.DataFrame, progress_data: pd.DataFrame, data: pd.Series):
    """
    根据 progress_data 获取 client 的 CS name，再在 employee_csv 中查找对应 email
    """
    clientno = data.name  # 注意：确保 client_data 的索引是 clientno
    try:
        cs_name = progress_data.loc[clientno, 'CS文案']
    except KeyError:
        return None

    matched = employee_csv.loc[employee_csv['Name_'] == cs_name, 'Email']
    return matched.iloc[0] if not matched.empty else None


    

    
    
