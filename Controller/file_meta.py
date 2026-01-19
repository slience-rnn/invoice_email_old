from Controller.func import *
import pandas as pd
import numpy as np
from datetime import datetime,timedelta
from Controller.func import *
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from Model.GoogleAPI import *
from Model.curr_mapper import curr_mapper
import cn2an
import re
# import csv
# import os

# header_name=['TOTAL AMOUNT EUR__','TOTAL AMOUNT CNY$__','TOTAL AMOUNT HKD$__']
def get_file_meta(fee_data,cus_data,cus_no,year,type:str = 'invoice',num:int=0, header_name=['TOTAL AMOUNT €','TOTAL AMOUNT CNY$','TOTAL AMOUNT HKD$']):
    EUR_FIELD_NAME= header_name[0]
    CNY_FIELD_NAME = header_name[1]
    HKD_FIELD_NAME = header_name[2]
    
    #print(f'Type={type}')
    '''
    year: 表示计算的是第几年的税费
    type: invoice receipt
    num: 表示第几个,只有在生成invoice时才需要传递
    header_name: 主要包含三个名字
    1. 实际应支付的EUR 字段名   header_name[0]
    2. 实际应支付的CNY 字段名  header_name[1]
    3. 实际应支付的HKD 字段名  header_name[2]
    '''
    last_name = fee_data['Last Name (Eng)']   # Last Name
    first_name = fee_data['First Name (Eng)']
    cus_name = ' '.join([last_name,first_name])
    
    #invoice_no_name = (last_name[0] + first_name[:2]).upper()
    # print(fee_data)
    invoice_no = fee_data['Invoice no.']


    file_meta_simple = {
        'cus_name': cus_name,
        'is_tax_rep':False,
        'tax_rep_fee':0,   
        'invoiceno':invoice_no,
        'is_imi':False,
        'imi_fee':0,  
        'is_condo':False,
        'condo_fee':0,  
        'is_qbe':False,
        'qbe_fee':0,   
        'is_irs':False,
        'irs_fee':0,
        'is_other_fee':False,
        'other_fee':0,  
        'email': [],  
        'qb_email':[], 
        'cs_email':[],
        'is_email':False,  
        'NIF': cus_data['MA NIF'],
        'invoice_cus_address' : '',
        'range_' : fee_data['location'],
        'receipt':{},
        'invoice':{},
        'is_form': False,      # 是否发送指模填写模块？
        'is_tax_rep_change':False,    # 是否需要更换税务代表
        'is_not_lisbon_lawyer':False,
        'form_link':'',
    }

    # 判断邮件内容
    file_meta_simple['is_email'],file_meta_simple['email'],file_meta_simple['qb_email'],file_meta_simple['cs_email'] = get_email_info(cus_data)
    # cus_email = cus_data['Email'].replace(' ','')
    # # print(f'---------------------------------------------')
    
    # 判断客户是否需要表单内容
    if cus_data.get('是否发送指模填写模块？',None):
        file_meta_simple['is_form'] = True
        file_meta_simple['form_link'] = cus_data.get('是否发送指模填写模块？')
    
    if cus_data.get('换税务代表FALCON',None):
        file_meta_simple['is_tax_rep_change'] = True
    
    if cus_data.get('非里斯本律师费',None):
        file_meta_simple['is_not_lisbon_lawyer'] = True
        file_meta_simple['is_not_lisbon_lawyer_fee'] = cus_data.get('非里斯本律师费')


    '''
    处理客户的费用
    '''
    # tax_rep_fee_data = fee_data['Tax Rep Fee Paid Date']
    # if tax_rep_fee_data in ['',' ','?'] and fee_data.get('TAX REP FEE','') !='':
    #     tax_rep_fee = current(fee_data['TAX REP FEE'])
    # else:
    #     tax_rep_fee = 0
    
    # if tax_rep_fee != 0:
    #     file_meta_simple['is_tax_rep']  =True
    #     file_meta_simple['tax_rep_fee'] = tax_rep_fee
    invoice_date = ''
    if type=='receipt':
        pattern = r'\w{5}(?P<invoice_date>\d{8})'
        match = re.search(pattern,invoice_no)
        if match:
            invoice_date = match.group('invoice_date')
    file_meta_simple['tax_rep_fee'],file_meta_simple['is_tax_rep'] = judge_fee(fee_data,type,'tax rep fee',invoice_date = invoice_date)
    file_meta_simple['condo_fee'],file_meta_simple['is_condo'] = judge_fee(fee_data,type,'condo fee',invoice_date = invoice_date)
    file_meta_simple['qbe_fee'],file_meta_simple['is_qbe'] = judge_fee(fee_data,type,'qbe',invoice_date = invoice_date)
    file_meta_simple['imi_fee'],file_meta_simple['is_imi'] = judge_fee(fee_data,type,'imi',invoice_date = invoice_date)
    file_meta_simple['irs_fee'],file_meta_simple['is_irs'] = judge_fee(fee_data,type,'irs',invoice_date = invoice_date)
    file_meta_simple['other_fee'],file_meta_simple['is_other'] = judge_fee(fee_data,type,'other fee',invoice_date = invoice_date)
    
    '''
    处理总费用
    '''
    # 对收集到数据进行加和 这是最准确的
    house_amount =  file_meta_simple['irs_fee'] + file_meta_simple['imi_fee'] + file_meta_simple['qbe_fee'] + file_meta_simple['condo_fee']
    amount_eur = house_amount + file_meta_simple['other_fee'] + file_meta_simple['tax_rep_fee']   # 房产费用加上other fee
    file_meta_simple['amount_eur'] = amount_eur    # 系统计算的客户应支付金额
    # print('*****************************')
    #print(file_meta_simple)
    if amount_eur == 0:
        file_meta_simple['is_email']  = False
        return None

    # 计算客户的invoice以及receipt所需要填写的内容
    if house_amount:
        cus_project = fee_data['Project']
        cus_project_address = fee_data['Project Address']
        file_meta_simple['invoice_cus_address'] = ' '.join([cus_project,cus_project_address])

    
    if type in ['invoice','receipt']:
        # 需要生成invocie 自己特有的内容  invoice no,note 
        file_meta_simple['note'] = fee_data['INVOICE ADD-ON REMARKS\n[支付单增加备注]']
        today = datetime.now()
        data_num = today.strftime("%Y%m%d")  # 20250513
        data_str = f'{today.year}年{today.month}月{today.day}日'
        # 发票所需内容
        invoice_no_name = (last_name[0] + first_name[:2]).upper()
        # print(invoice_no_name,data_num,no)
        invoice_no = ''.join(['PT',invoice_no_name,data_num,'-',num_to_3(num)])

        # 计算嵌套数组
        #print(f'year = {year}')
        last_day = datetime(year,12,31)
        #last_day_= datetime.strftime(last_day,'%Y/%m/%d')
        #tax_rep_start_date = ''
        tax_rep_content = []

        # 计算amount
        if fee_data[CNY_FIELD_NAME] not in [' ','']:
        #print(fee_data['TOTAL AMOUNT CNY$'])
            cny_amount = current(fee_data[CNY_FIELD_NAME],1)
            rmb_er = round(cny_amount/amount_eur,4)
        else:
            cny_amount = 0
            rmb_er = 0
        

        if fee_data[HKD_FIELD_NAME] not in [' ','']:
            hkd_amount = current(fee_data[HKD_FIELD_NAME],1)
            hk_er = round(hkd_amount/amount_eur,4)
        else:
            hkd_amount = 0
            hk_er = 0
        if file_meta_simple['is_tax_rep']:
            # 获取tax_rep_fee中的日期
            tax_data = fee_data['Total payment dys'].replace(',','')
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

                start = datetime(start.year,12,31) + timedelta(days = 1)
                # print('*****************************')

        file_meta_simple.update({
            'invoice_number_system_generate':invoice_no,    # 此处的invoice_no 是生成invoice时需要使用到，其他时刻不需要
            'invoice_date_system_generate':data_str,      
            'tax_rep_content':tax_rep_content,   # invoice & receipt 需要使用到tax_rep_content
            'invoice_hkd_amount':hkd_amount,    # invoice
            'invoice_cny_amount':cny_amount,     # invoice
            'invoice_rmb_er':rmb_er,             # invoice
            'invoice_hk_er':hk_er             # invoice
        })
        # return file_meta_simple
    # print('***************************** invoice End')
    if type == 'receipt':
        #print('Enter type == receipt')
        '''
        receipt 中特有的内容 比如客户的invoice_number 需要更新
        '''
        word_special = ''
        # receipt中invoice no file_meta_simple['invoice_no']即可
        # 读取fee_data中的内容
        invoice_no_receipt = fee_data['INVOICE NO. & Date']
        is_gift_pack = False
        spl = '/'
        paid_date = fee_data['Paid_Date'].title()    # 英文符号
        print('**************************')
        print(f'20250627 Paid_Data = {paid_date}')
        # paid_date 可以是日期，也可能是GIFTPACK
        if paid_date == 'Gift Pack' or paid_date == 'Builder Cost':
            paid_date = datetime.strftime(datetime.today(),'%Y/%m/%d')
            is_gift_pack = True
            word_special = fee_data['Paid_Date'].upper()
            #print(f'20250620/gift_pack_date = {paid_date}')

        if '.' in paid_date:   
            spl = '.'
        
        receipt_data_raw = paid_date.split(spl)
        print(receipt_data_raw,cus_no)
        
        

        receipt_data = f'{receipt_data_raw[0]}年{receipt_data_raw[1]}月{receipt_data_raw[2]}日'
        
        # 如果receipt的日期< invoice_date 返回None
        if datetime(int(receipt_data_raw[0]),int(receipt_data_raw[1]),int(receipt_data_raw[2])) < datetime.strptime(invoice_date,'%Y%m%d'):
            return None

        # panduan
        # receipt_data = '2999年12月31日'
        date_eng = str_date_str(paid_date,spl,1)
        hkd_amount = 0
        hk_er = 0
        cny_amount = 0
        rmb_er = 0
        curr_signal = '€'
        exchange_rate = 0
        an_amount = ''

        # 根据Total amount € 与Total Amount CNY计算实际支付汇率
        curr = curr_mapper[curr_signal]     # 实际支付的金额
        if fee_data['TOTAL AMOUNT EUR'] not in [' ','']:    # 实际支付的欧元
            actually_cur_amount = current(fee_data['TOTAL AMOUNT EUR'][1:],1)
            an_amount = cn2an.an2cn(float(actually_cur_amount),'rmb')# 大写的数字
            
        
        if fee_data['TOTAL AMOUNT CNY ¥/HK$/US$/Others'].strip() not in [' ','']:    # 实际支付的是其他货币
            curr_signal = fee_data['TOTAL AMOUNT CNY ¥/HK$/US$/Others'].strip()[0]
            if curr_signal == 'U':
                curr_signal = fee_data['TOTAL AMOUNT CNY ¥/HK$/US$/Others'].strip()[0:3]
                actually_cur_amount = current(fee_data['TOTAL AMOUNT CNY ¥/HK$/US$/Others'][3:],1)
            else:
                actually_cur_amount = current(fee_data['TOTAL AMOUNT CNY ¥/HK$/US$/Others'][1:],1)
            
            curr = curr_mapper[curr_signal]    # ['CNY','人民币']
            an_amount = cn2an.an2cn(float(actually_cur_amount),'rmb')
            exchange_rate = round(actually_cur_amount/amount_eur,4)

        # 计算HKD和CNY的汇率
        paid_cur_amount = actually_cur_amount
        inv_er = exchange_rate
        eur_paid_sheet = current(fee_data[EUR_FIELD_NAME][1:],1)
        if curr[0] == 'HKD':           
            hkd_amount = current(fee_data[HKD_FIELD_NAME],1)
            inv_er= round(hkd_amount/eur_paid_sheet,4)

        elif curr[0] == 'CNY':
            cny_amount = current(fee_data[CNY_FIELD_NAME],1)
            inv_er= round(cny_amount/eur_paid_sheet,4)
        # 若汇率超出了，则修正
        if abs(exchange_rate - inv_er) > 0.0001: 
            exchange_rate = inv_er
            # 计算客户应该 支付给公司的金额   应付金额 
            paid_cur_amount = round(inv_er * amount_eur,2)

        
        
        format_amount = "{:,}".format(actually_cur_amount)

        if not is_gift_pack:
            if curr[0] == 'EUR':
                #receipt_sentence_eng = f"We hereby acknowledge receipt of EUR{format_amount} from client,  {cus_name}. This amount corresponds to the payment of the Consultancy fee for subscription of the Future European Financials Opportunities Fund."
                receipt_sentence_eng = f"We hereby acknowledge receipt of EUR {format_amount} on {date_eng} as payment for the above-mentioned fees."
            else:
                if abs(actually_cur_amount - paid_cur_amount)<0.01:
                #receipt_sentence_eng =f"We hereby acknowledge receipt of {curr[0]}{format_amount} equivalent to EUR{'{:,}'.format(amount_eur)} from client, {cus_name}. This amount corresponds to the payment of the Consultancy fee for subscription of the Future European Financials Opportunities Fund."
                    receipt_sentence_eng = f"We hereby acknowledge receipt of {curr[0]}{format_amount} equivalent to EUR{'{:,}'.format(round(amount_eur,2))} on {date_eng} as payment for the above-mentioned fees."
                else:
                    receipt_sentence_eng = f"We hereby acknowledge receipt of {curr[0]}{format_amount} on {date_eng} as payment for the above-mentioned fees."
        
        else:   # 当其是gift_pack时
            receipt_sentence_eng = f'We hereby confirm that EUR{format_amount} was deducted from the {word_special} as payment for the above-mentioned fees.'
        file_meta_simple.update({
            'receipt_invoice_number':invoice_no_receipt,    # 此处的invoice_no 是生成invoice时需要使用到，其他时刻不需要     
            #'tax_rep_content':tax_rep_content,   # invoice & receipt 需要使用到tax_rep_content
            'receipt_amount_eur':round(amount_eur,2),
            'is_gift_pack':is_gift_pack,
            'word_special':word_special,
            'paid_cur_amount':paid_cur_amount,
            'actually_cur_amount':actually_cur_amount,
            'receipt_data_googlesheet':paid_date,
            'receipt_data_filepath':str_date_str(paid_date),
            'actually_curr_paid_eng': curr[0],
            'receipt_data':receipt_data,
            'receipt_sentence_eng':receipt_sentence_eng,
            'receipt_curr_chi':curr[1],
            'receipt_an_amount':an_amount,         # 客户实际支付的金额
            'receipt_exchange_rate':exchange_rate,
            'receipt_format_amount':format_amount,
        })
            

        # 读取文档中的内容
        # receipt_path = 'doc/receipt.csv'

        # if not os.path.exists(receipt_path): # 如果不存在则创建
        #     header = ['invoice_no','is_gen','is_send']
        #     with open(receipt_path,'w',newline='',encoding='utf-8') as file:
        #         writer = csv.writer(file) 
        #         writer.writerow(header)

        # # 读取文档中的内容
        # receipt_data = pd.read_csv(receipt_path) 

    #print(file_meta_simple)
    return file_meta_simple

        

       
def get_email_info(cus_data):
    '''
    返回值：
    is_email:bool   
    cus_email_processed:list 需要to的邮箱
    qd_email_processed:list 需要bcc 的邮箱
    '''
    cus_email = cus_data['Email'].replace(' ','')
    # print(f'---------------------------------------------')
    
    '''
    处理邮箱
    '''
    cus_email_processed = cus_email
    if ';' in cus_email:
        cus_email_processed = cus_email.split(';')
    elif '；' in cus_email:
        cus_email_processed = cus_email.split('；')
    elif '/' in cus_email:
        cus_email_processed = cus_email.split('/')
    if '>' in cus_email:
        cus_email_processed = cus_email.split('>')
    else:
        cus_email_processed = [cus_email]
    
    if cus_email_processed == ['']:
        cus_email_processed = []

    

    qd_email = cus_data['渠道邮箱'].replace(' ','')
    qd_email_processed = qd_email
    if ';' in qd_email:    # 英文的分号
        qd_email_processed = qd_email.split(';')
    elif '；' in cus_data['渠道邮箱']:    # 中文的分号
        qd_email_processed = qd_email.split('；')
    elif '/' in cus_data['渠道邮箱']:
        qd_email_processed = qd_email.split('/')
    else:
        qd_email_processed = [qd_email]

    if qd_email_processed == ['']:
        qd_email_processed = []


    if cus_data['是否發送Email 2025.05.15'].strip() == 'Y':    # 表示发送客户以及密送渠道
        is_email = True
    
    elif cus_data['是否發送Email 2025.05.15'].strip() == 'Q':    # 表示发送渠道
        is_email = True
        cus_email_processed = []                        # 发送渠道不发送给客户，客户邮箱置空
    else:
        is_email = False
        return is_email,cus_email_processed,qd_email_processed

    # 如果客户邮箱不存在，渠道邮箱存在，默认发送给渠道
    if len(cus_email_processed)==0 and len(qd_email_processed)!=0:
        cus_email_processed = qd_email_processed
        qd_email_processed = []

    # 如果客户邮箱存在，渠道邮箱不存在，默认只发送给客户

    #print(f'2.cus_email:{cus_email}')
    # 客户和渠道邮箱都不存在，默认不发送邮件
    if len(cus_email_processed)==0 and len(qd_email_processed)==0:
        is_email = False
    
    cs_email = [cus_data['CS_email']]

    #print(f'3.cus_email:{cus_email}')
    print(is_email)
    return is_email,cus_email_processed,qd_email_processed,cs_email
  

def get_cus_info(cus_data)-> dict:
    # 获取客户最基础的信息
    # 包括email，以及cus_name
    is_email,cus_email,qd_email = get_email_info(cus_data)
    last_name = cus_data['Last Name (Eng)']   # Last Name
    first_name = cus_data['First Name (Eng)']
    cus_name = ' '.join([last_name,first_name])
    results = {
        'is_email':is_email,
        'to_email':cus_email,
        'bcc_email':qd_email,
        'cus_name':cus_name
    }
    return results
    
    
                     
    

def judge_fee(data,condition:str,field:str,**kwargs):
    '''
    判断是否需要费用
    data: fee_data   客户在SummSheet中的记录
    condition:str  'invoice'/'receipt'
    field:str 字段，提取的费用字段 例如
    [kwargs]
    invoice_date: '20250601'  发票日期，发票日期之前支付的不可以出具receipt
    '''

    field = field.lower()    # 小写的
    field_name= field.upper()    # 大写的在summSheet中的位置
    
    fee = 0
    is_fee  =False
    
    # 获取date 首先获取 field_name所在的索引列
    field_row = data.index.get_loc(field_name)
    if field == 'tax rep fee':
        data_row = field_row + 2
    else:
        data_row = field_row + 1
    date = data.iloc[data_row]
    #print(f'20250619 \n field = {field} field_name = {field_name} field_row = {field_row}  \n data_row = {data_row}--date = {date} ')
    conditions = False
    # date = data['Other Fee Paid Date']    # 支付时间
    # conditions 表示是否考虑该费用
    # 判断date是否为时间
    pattern = r'^\d{4}/\d{1,2}/\d{1,2}$'

    cond = bool(re.match(pattern, date))   # 是否为时间

    if condition == 'invoice':     
        # condition   没有支付时间，并且fee_data 不为空 表示需要考虑该费用
        conditions = (not cond) and data.get(field_name).split() !=''
        # 如果该时间为2099/12/31  因为invoice总是在receipt前面，所以不需要考虑这个 
        # 比如: 当出具invoice时，data是2099/12/31，cond为True，Not cond=False   此时conditions是False  表示不考虑这个
    elif condition == 'receipt':
        # condition 当cond为true时，也就是有支付时间，并且fee_data不为空的时候，需要考虑该费用
        conditions = cond and data.get(field_name).split() !=''
        invoice_date = kwargs.get('invoice_date')
        # 当cond为true，但是cond==2099/12/31，那么也是不应该考虑的 因为此时我们在出具receipt
        if cond and date == '2099/12/31':
            conditions = False
        date_array = date.split('/')
        print('--------',date_array)
        if cond and datetime(int(date_array[0]),int(date_array[1]),int(date_array[2])) < datetime.strptime(invoice_date,'%Y%m%d'):
            conditions = False
        


    if conditions:  
        fee = current(data[field_name])
    else:
        fee = 0
    # 因为有时候if下面计算的fee也是0 所以需要更正
    if fee != 0:
        is_fee  =True

    return fee,is_fee
        


    
