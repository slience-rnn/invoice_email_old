import os

from Controller.deal_sheet_data import *
from datetime import datetime,timedelta
from Controller.func import *
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from Model.GoogleAPI import *


'''
data: 
'''

def template_invoice(fee_data,cus_data,no,year,cus_no,template_name,header_name=['TOTAL AMOUNT €','TOTAL AMOUNT CNY$','TOTAL AMOUNT HKD$']):
    # template_name = IRS_INVOICE.html / zfd_layerfee.html
    # 费用总额
    EUR_FIELD_NAME= header_name[0]
    CNY_FIELD_NAME = header_name[1]
    HKD_FIELD_NAME = header_name[2]

    return_file = None
    return_error_1 = ''
    return_error_2 = ''
    if fee_data[EUR_FIELD_NAME]!='':
        eur_amount = current(fee_data[EUR_FIELD_NAME])
    else:
        eur_amount = 0

    if eur_amount == 0:
        return return_file,return_error_1,return_error_2
    
    # if 
    # print(f'total amount {eur_amount}')

   
    # 从表格中获取数据
    # print('fee_data的值')
    # print(fee_data)
    last_name = fee_data['Last Name (Eng)']   # Last Name
    first_name = fee_data['First Name (Eng)']
    tax_data = 0

    # 客户邮件地址
    email = cus_data['Email']
    # 是否需要发送邮件
    is_email = cus_data['是否發送Email 2025.05.15']     # 有待商榷
    # 客户的税号
    NIF  = cus_data['MA NIF']
    
    # 税务代表费用：
    # tax_rep_fee_data in ['',' ','?'] 表示客戶未查詢到客戶繳納稅款的日期，需要計算客戶的此項費用
    # / 表示忽略此項費用，不將此項費用納入到invoice中
    # 除了'',' ',? 均認爲客戶費用已經繳納，忽略此項費用

    # tax_rep_fee_data = fee_data['Tax Rep Fee Paid Date']
    # if tax_rep_fee_data in ['',' ','?'] and fee_data.get('TAX REP FEE','') !='':      # 
    #     tax_rep_fee = current(fee_data['TAX REP FEE'])
    #     tax_data = fee_data['Total payment dys'].replace(',','')
    # else:
    #     tax_rep_fee = 0

    # 税代费用计算
    # 如果支付日期处匹配的是日期 08/09/2025 表示已经支付 不需要考虑该费用，
    # 如果支付日期处是'',' ','?' 并且费用处不为空，那么考虑该费用，其他情况都需要考虑该费用
    tax_rep_fee_data = fee_data['Tax Rep Fee Paid Date']
    
    if tax_rep_fee_data in ['',' ','?'] and fee_data.get('TAX REP FEE','') !='':      # 
        tax_rep_fee = current(fee_data['TAX REP FEE'])
        tax_data = fee_data['Total payment dys'].replace(',','')
    else:
        tax_rep_fee = 0
    
    # 物业费用管理
    condo_fee_data = fee_data['Condo Fee Paid Date']
    if condo_fee_data in ['',' ','?'] and fee_data.get('CONDO FEE') !='':
        condo_fee = current(fee_data['CONDO FEE'])
    else:
        condo_fee = 0
    
    # 物业保险费用
    qbe_fee_date = fee_data['QBE Paid Date']
    if qbe_fee_date in ['',' ','?'] and fee_data.get('QBE') !='' :
        qbe_fee = current(fee_data['QBE'])
    else:
        qbe_fee = 0
    
    # IMI
    imi_fee_date = fee_data['IMI Paid Date']
    if imi_fee_date in ['',' ','?','by gift pack'] and fee_data.get('IMI')!='':
        imi_fee = current(fee_data['IMI'])
    else:
        imi_fee = 0
    
    # IRS 
    irs_fee_date = fee_data['IRS Paid Date']
    if irs_fee_date in ['',' ','?'] and fee_data.get('IRS') !='':
        irs_fee = current(fee_data['IRS'])
    else:
        irs_fee = 0
    
    # other
    other_fee_date = fee_data['Other Fee Paid Date']
    if other_fee_date in ['',' ','?'] and fee_data.get('OTHER FEE') !='':
        other_fee = current(fee_data['OTHER FEE'])
    else:
        other_fee = 0
    # other_fee = fee_data['OTHER FEE']
    
    
    # 物业地址
    cus_project = cus_data['Project']
    cus_project_address = cus_data['Project Address']
    

    if fee_data[CNY_FIELD_NAME] not in [' ','']:
        #print(fee_data['TOTAL AMOUNT CNY$'])
        cny_amount = current(fee_data[CNY_FIELD_NAME],1)
        rmb_er = round(cny_amount/eur_amount,4)
    else:
        cny_amount = 0
        rmb_er = 0
    

    if fee_data[HKD_FIELD_NAME] not in [' ','']:
        hkd_amount = current(fee_data[HKD_FIELD_NAME],1)
        hk_er = round(hkd_amount/eur_amount,4)
    else:
        hkd_amount = 0
        hk_er = 0
    # 备注
    note = fee_data['INVOICE ADD-ON REMARKS\n[支付单增加备注]']
    # 税费支付开始日期
    



    today = datetime.now()
    data_num = today.strftime("%Y%m%d")  # 20250513
    data_str = f'{today.year}年{today.month}月{today.day}日'
    # 发票所需内容
    invoice_name = ' '.join([last_name,first_name])
    invoice_no_name = (last_name[0] + first_name[:2]).upper()
    print(invoice_no_name,data_num,no)
    invoice_no = ''.join(['PT',invoice_no_name,data_num,'-',num_to_3(no)])

    return_file = {
        'cus_name': invoice_name,
        'filedate':data_num,
        'invoiceno':invoice_no,
        'is_imi':False,
        'range_' : fee_data['location'],
    }
    return_file['is_tax_rep'] = bool(tax_rep_fee)
    if irs_fee or imi_fee or qbe_fee or condo_fee:
        invoice_cus_address = ' '.join([cus_project,cus_project_address])
        return_file['is_imi'] = bool(imi_fee)
        return_file['is_irs'] = bool(irs_fee)
        return_file['is_qbe'] = bool(qbe_fee)
        return_file['is_condo'] = bool(condo_fee)
    else:
        invoice_cus_address = ''
    
    
    last_day = datetime(year,12,31)
    last_day_= datetime.strftime(last_day,'%Y/%m/%d')
    tax_rep_start_date = ''
    tax_rep_content = []
    system_tax_rep_fee = 0
    if tax_rep_fee:
        # 获取tax_rep_fee中的日期
        tax_rep_day = int(tax_data)
        # 计算tax_rep_day 的开始日期
        tax_rep_start = last_day - timedelta(days = tax_rep_day-1 )
        # tax_rep_start_date = f"{tax_rep_start.year}年{tax_rep_start.month}月{tax_rep_start.day}日"
        # tax_rep_start_data_str = datetime.strftime(tax_rep_start_date,'%Y%m%d')
        # 计算其开始日期
        start = tax_rep_start
        tax_rep_year = 1000
        if cus_no in ['2022CS3','2023EV7','2024FU57','2024FU47','2024FU48','2023CS8','2024FU19']:  
            tax_rep_year = 600
        if cus_no in ['2024FU10']:
            tax_rep_year = 990

        while start.year <=  int(year):
            # 将字符串转变成时间
            # start_2_time = datetime.strptime(start,'%Y/%m/%d')
           
            tax_rep_detail = f'由{start.year}年{start.month}月{start.day}日至{start.year}年12月31日'
            tax_rep_days = days_until_year_end(start) + 1
            #计算start这一年的天数
            start_year_11 = datetime(start.year,1,1)
            start_year_days = days_until_year_end(start_year_11) + 1     
            # start_year_days = 365
            tax_rep_amount = round(tax_rep_year/start_year_days * tax_rep_days,2)    
            tax_rep_content.append([tax_rep_detail,tax_rep_amount])
            system_tax_rep_fee = system_tax_rep_fee + tax_rep_amount
            start = datetime(start.year,12,31) + timedelta(days = 1)
    system_amount_fee = system_tax_rep_fee + condo_fee + qbe_fee+ imi_fee + irs_fee + other_fee
    # special ------
    # eur_amount =  round(system_amount_fee,2)
    # hkd_amount =  round(system_amount_fee * 8.993301,2)
    # hk_er = 8.9933
    # -----------
    invoice_data = {
        'customer_name': invoice_name,
        'invoice_number':invoice_no,
        'invoice_date':data_str,
        'tax_rep_content':tax_rep_content,   # 是一个嵌套数组
        'tax_rep_fee':tax_rep_fee,
        'condo_fee':condo_fee,
        'qbe_fee':qbe_fee,
        'imi_fee':imi_fee,
        'irs_fee':irs_fee,
        'other_fee':other_fee,
        'invoice_cus_address':invoice_cus_address,
        'eur_amount':eur_amount,
        'hkd_amount':hkd_amount,
        'cny_amount':cny_amount,
        'rmb_er':rmb_er,
        'hk_er':hk_er,
        'note':note,
    }
    
    env = Environment(loader = FileSystemLoader('./View'))
    template_zfd_layerfee = env.get_template(f'{template_name}')
    zfd = template_zfd_layerfee.render(invoice_data)

    # 将渲染出来的html转为pdf
    file_name = f'{invoice_no}_{invoice_name}_Eur{eur_amount}.pdf'
    file_path = os.path.join('temp_file',file_name)
    return_file['filename'] = file_name
    return_file['filepath'] = file_path
    # 客户邮件地址
    return_file['email'] = cus_data['Email']
    # 是否需要发送邮件
    return_file['is_email'] = cus_data['是否發送Email 2025.05.15']     # 有待商榷
    # 客户的税号
    return_file['NIF']  = cus_data['MA NIF']
    return_file['eur_amount'] = eur_amount
    
    HTML(string=zfd).write_pdf(file_path)   # 将文件保存到本地
    print('invoice已经生成')
    
    
    if system_tax_rep_fee != tax_rep_fee:
        return_error_1 = f'Error:{cus_no},system_tax_rep_fee = EUR{system_tax_rep_fee} / actual_tax_rep_fee = EUR{tax_rep_fee} Please Check it!'
    if system_amount_fee != eur_amount:
        return_error_2 = f'Error:{cus_no},system_amount_fee = EUR{system_amount_fee} / actual_amount = EUR{eur_amount} Please Check it!'
    
    return return_file,return_error_1,return_error_2
    # 将文件上传到google drive

    
    


    
    



    
