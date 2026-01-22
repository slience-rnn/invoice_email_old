from datetime import datetime,date
import pandas as pd
from pathlib import Path

def get_counter():
    STATE_FILE = Path(r'config\counter.txt')
    today = date.today().isoformat()
    if STATE_FILE.exists():
        saved_date, value = STATE_FILE.read_text().split(",")
        value = int(value)

        if saved_date != today:
            value = 0
    else:
        value = 0

    code = f"{value:03d}"

    STATE_FILE.write_text(f"{today},{value + 1}")
    return code


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

# def progress_employee_client(employee_csv: pd.DataFrame, client_data: pd.DataFrame, progress_data: pd.DataFrame):
#     """
#     为每个 client 添加对应的 CS_email
#     """
#     client_data['CS_email'] = client_data.apply(lambda x: map_employee(employee_csv, progress_data, x), axis=1)
#     client_data['Sales_email'] = client_data.apply(lambda x: map_employee(employee_csv, progress_data, ))
#     return client_data  # 返回修改后的 DataFrame

def map_employee(employee_csv: pd.DataFrame,
                 progress_data: pd.DataFrame,
                 data: pd.Series):
    """
    根据 progress_data 获取 client 的 CS 文案姓名（可能多个），
    在 employee_csv 中筛选文案类型并返回所有匹配的邮箱列表
    """

    clientno = data.name

    # 1️⃣ 只筛选“文案”
    copy_df = employee_csv[
        employee_csv['Duty'].str.contains('文案', na=False)
    ]

    try:
        cs_name = progress_data.loc[clientno, 'CS文案']
    except KeyError:
        return []

    if pd.isna(cs_name):
        return []

    # 2️⃣ 拆分 Alice/Bob → ['Alice', 'Bob']
    cs_names = [name.strip() for name in str(cs_name).split('/')]

    # 3️⃣ 匹配 Name_
    matched_emails = copy_df[
        copy_df['Name_'].isin(cs_names)
    ]['Email']

    # 4️⃣ 返回邮箱列表
    return matched_emails.tolist()


def match_sales_email(client_data: pd.DataFrame,
                      employee_csv: pd.DataFrame,
                      data: pd.Series):

    clientno = data.name

    try:
        team = client_data.loc[clientno, 'Team']
    except KeyError:
        return []

    if pd.isna(team):
        return []

    # 1️⃣ 拆分 Felix/Ben → ['Felix', 'Ben']
    sales_names = [name.strip() for name in team.split('/')]

    # 2️⃣ 只筛选“销售”
    sales_df = employee_csv[
        employee_csv['Duty'].str.contains('销售', na=False)
    ]

    # 3️⃣ 匹配 Name_
    matched_emails = sales_df[
        sales_df['Name_'].isin(sales_names)
    ]['Email']

    # 4️⃣ 返回所有邮箱
    return matched_emails.tolist()


# 返回的是列表list
def progress_employee_client(employee_csv: pd.DataFrame,
                             client_data: pd.DataFrame,
                             progress_data: pd.DataFrame):
    """
    为每个 client 生成合并后的 Employee_email（文案 + 销售）
    """

    def merge_employee_email(row):
        # 文案邮箱
        cs_emails = map_employee(employee_csv, progress_data, row)

        # 销售邮箱
        sales_emails = match_sales_email(client_data, employee_csv, row)

        # 合并 + 去重 + 过滤空值
        all_emails = list(
            dict.fromkeys(
                [e for e in cs_emails + sales_emails if e]
            )
        )

        return ';'.join(all_emails)

    client_data['Employee_email'] = client_data.apply(
        merge_employee_email,
        axis=1
    )

    return client_data

    


    

    
    
