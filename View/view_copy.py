import streamlit as st
from Model.GoogleAPI import GoogleClass
from Controller.deal_sheet_data import *
from Controller.generate_invoice import *
from datetime import datetime
from Controller.check_info import *
import pandas as pd
from Controller.file_meta import *
from Controller.ali_send_email import *
import time
from Controller.generate_receipt import *
from Model.month_mapper import *
import schedule
import time
import csv
import threading
from pathlib import Path
import logging
from Controller.func import get_counter
import random

logger = logging.getLogger(f"app.{__name__}")



def background_job_send_receipt(google,field_name_1,client_data,select_year,select_templated,today,receipt_csv_path,send_failed,summSheet):
    # schedule.every().day.at("19:00").do(lambda:send_receipt(google,receipt_csv,field_name_1,client_data,select_year,select_templated,today,receipt_csv_path,send_failed))
    # 获取参数
    # google,receipt_csv,field_name_1,client_data,select_year,select_templated,today,receipt_csv_path,send_failed
    # google = st.session_state.get('google','')
    # receipt_csv = st.session_state.get('receipt_csv','')
    # field_name_1 = st.session_state.get('field_name_1','')
    # client_data = st.session_state.get('client_data','')
    # select_year = st.session_state.get('select_year','')
    # select_templated = st.session_state.get('select_templated','')
    # today = st.session_state.get('today','')
    # receipt_csv_path = st.session_state.get('receipt_csv_path','')
    # send_failed = st.session_state.get('send_failed','')
    
    # no = st.session_state.get('no','')
    # print(f'no=={no}')
    # no = 5
    schedule.every().day.at("19:00").do(lambda:send_receipt(google,field_name_1,client_data,select_year,select_templated,today,receipt_csv_path,send_failed,summSheet))
    while True:
        schedule.run_pending()   # 检查是否有任务执行，有就执行
        time.sleep(5)


def background_job_send_invoice(google,summSheet,client_data,select_year,select_templated):
    schedule.every().day.at("19:00").do(lambda:send_invoice(google,summSheet,client_data,select_year,select_templated))
    while True:
        schedule.run_pending()   # 检查是否有任务执行，有就执行
        time.sleep(5)

def test(no):
    print(f'[DEBUG]执行第{no}次[/DEBUG]')
        

def view_form(google:GoogleClass):
    st.set_page_config(page_title="TaxPrompt 税务助手", page_icon="📄", layout="centered")

    st.title("📄 TaxPrompt 税务助手")
    st.caption("👨‍💼 技术支持：欧睿 ORUI 跨境数字系统 · 当前版本 V3.0.2")
    regenerate_user = st.text_input("Enter customer IDs to be regenerated, separated by spaces (e.g., 2019IX 2020EX).")  # 需要再次重新生成的客户id
    current_year = datetime.now().year
    years = list(range(current_year,current_year+2))
    return_err1_arr = []
    return_err2_arr = []
    temp = ['Invoice_Form_202601','template1','template2','template3','Receipt_Remind','Receipt_Remind-IRS','Invoice_Remind_202510']
    send_failed = []

    # 让用户选择年份
    select_year = st.selectbox("Please select year",years)
    select_templated  = st.selectbox('please select template',temp)

    # 是否选择发送邮件
    # is_send_email = st.selectbox("Select whether to send the email.",['No Send','Send'])
    if select_templated=='Invoice_Form_202601':
        st.caption('''感谢您选择.... 适用于税务的2026首次税务代表费提醒
        ''')
    elif select_templated == 'template1':
        st.caption('''感谢您选择.... 适用于税务的Invoice首次提醒
        ''')
    elif select_templated == 'template2':
        st.caption('''感谢您选择.... 适用于税务的二次提醒,严肃版本
        ''')
    elif select_templated == 'template3':
        st.caption('''感谢您选择.... 适用于税务的二次提醒
        ''')
    elif select_templated == 'Receipt_Remind':   # Receipt_Remind
        st.caption('''感谢您选择.... 适用于Receipt的发送
        ''')
    elif select_templated == 'Receipt_Remind-IRS':   # Receipt_Remind-IRS
        st.caption('''感谢您选择.... 适用于IRS-Bank Proof的发送
        ''')
    elif select_templated == 'Invoice_Remind_202510':   # 2025年10月 IMI与IRS 的通知
        st.caption('''感谢您选择.... 适用于2025年10月IMI和IRS的通知''')

    if pd.isna(regenerate_user):
        regenerate_ = []
    else:
        regenerate_ = regenerate_user.split(' ')

    start = 3  # 初始值 3
    num = 355  # 最大值355
    tracker_sheet_id = '1aWPRqw02WdZ3C9E9b_v5YEl52EzhjmE_wFNq_oQIOP0'
    client = f'CLIENT!A{str(start-1)}:AG{str(num-1)}' #'CLIENT!A2:AG200'
    summSheet =  f'SummSheet!A{str(start)}:AU{str(num)}' #'SummSheet!A3:AU201'
    mc_pt = f'Progress Tracker(M)!A{str(start)}:F{str(num)}'

    # tax_rep_fee = 'Tax REP FEE!A2:AD21'
    range_name = [client,summSheet]
    file_meta = {}
    
    no_imi = []
    no_email = []
    # 获取client的表头
    client_header = []
    summSheet_header = []
    client_header_region = 'CLIENT!A1:AG1'
    summSheet_header_region = 'SummSheet!A2:AU2'

    # Master_Client_Info 的表头
    mc_sheet_id = '1GoEShJbE9LivPnO5hpxBfwwge7wVHlxHVmHbgv3Wvnw'
    mc_header_region = 'Progress Tracker(M)!A2:G2'
    
    # 读取所有表的表头
    header_region_name = [client_header_region,summSheet_header_region]
    header = google.read_sheet_batchGet(tracker_sheet_id,header_region_name)

    mc_region_name = [mc_header_region]
    mc_header = google.read_sheet_batchGet(mc_sheet_id,mc_region_name)

    
    if header:
        client_header = header[0].get('values')[0]
        summSheet_header = header[1].get('values')[0]

    if mc_header:
        progress_header = mc_header[0].get('values')[0]
   
    
    st.markdown("---")
   
    sheet_data = google.read_sheet_batchGet(tracker_sheet_id,range_name)
    client_data = deal_sheet_data(sheet_data[0].get('values',''),client_header,start = start,name = 'client')
    summSheet = deal_sheet_data(sheet_data[1].get('values',''),summSheet_header,start = start,name = 'summSheet')

    progress_sheet_data = google.read_sheet_batchGet(mc_sheet_id,mc_pt)
    progress_data = deal_sheet_data(progress_sheet_data[0].get('values',''),progress_header,start = start,)

    Base_path = Path(__file__).resolve().parent.parent
    receipt_csv_path = Path.joinpath(Base_path,'doc','receipt_generate_sended.csv')
    employee_csv_path = Path.joinpath(Base_path,'Static','data','CRM_Employee_Table.csv')
    today = datetime.strftime(datetime.today(),'%Y/%m/%d')

    st.info(regenerate_)
    # regenerate_ = ['2020FA1']
    if regenerate_ != ['']:    # 当其不为空
        summSheet = summSheet.loc[regenerate_]

    if not os.path.exists(receipt_csv_path):  # 不存在 则创建
        with open(receipt_csv_path,'w',newline = '',encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['invoice_no','cus_no','generate_date','sended_date'])
                

    # 读取文件：
    receipt_csv = pd.read_csv(receipt_csv_path,header = 0,dtype={'sended_date':str})
    employee_csv = pd.read_csv(employee_csv_path, header = 0)

    client_data= progress_employee_client(employee_csv,client_data,progress_data)
  
    field_name_1 = 'INVOICE NO. & Date'
    field_name_2 = 'Invoice no.'
    field_name_3 = 'Paid_Date'



    # st.session_state['google'] = google
    # st.session_state['receipt_csv'] = receipt_csv
    # st.session_state['field_name_1'] = field_name_1
    # st.session_state['client_data'] = client_data
    # st.session_state['select_year'] = select_year
    # st.session_state['select_templated'] = select_templated
    # st.session_state['today'] = today
    # st.session_state['receipt_csv_path'] = receipt_csv_path
    # st.session_state['send_failed'] = send_failed

    # st.info(f'{st.session_state}')
    if 'thread_started' not in st.session_state:
        # st.info(f'no = {no}')
        # threading.Thread(target = background_job_send_invoice,args = (google,summSheet,client_data,select_year,select_templated),daemon=True).start()
        # threading.Thread(target = background_job_send_receipt,args = (google,field_name_1,client_data,select_year,select_templated,today,receipt_csv_path,send_failed,summSheet), daemon=True).start()
        st.session_state.thread_started = True


    if st.button('🔍 检查客户信息完整性'): # 开始执行 
        st.info('检查客户信息是否完整......')
        
        no_imi,no_email = check_info(google,client_data,summSheet)

        if no_imi:
            st.error(f'未找到客户的房产税文件:{no_imi}\n请及时补充')
        if no_email:
            st.error(f'未找到客户的邮件地址:{no_email}\n请及时补充')
        st.info('检查完成......')
        
    
    # regenerate_uder 默认不填写将执行所有用户的操作
    if st.button('🧾 生成 支付单 Invoice'): # 开始执行 
        # 读取sheet表  
        st.info('Start')
        # sheet_data = google.read_sheet_batchGet(range_name)
        imi_file_bytes = ''
        # print(sheet_data)
        #print(f'原始读取数据的结果\n{sheet_data}')
        '''自动生成invoice''' 
        
        if no_imi == [] and no_email == []:
            st.info('开始执行......')
            logger.info('开始生成客户的支付单Invoice')
            #print(f'summSheet的值是{summSheet}')
            for line in range(summSheet.shape[0]):
                
                
                fee_data = summSheet.iloc[line,:]    # <class 'pandas.core.series.Series'>
                
                cus_no = fee_data.name             # 获取到了客户号
                # 取出Client中的数据，需要提取出非里斯律师费
                # ======================================
                
                #print(regenerate_)
                if regenerate_ != ['']:    # 当其不为空
                    if cus_no not in regenerate_:
                        continue

                #print('continue')
                if not cus_no:
                    continue
                # 通过索引找

                
                logger.info(f'📌 开始准备生成客户 {cus_no} 的支付单Invoice')
                

                cus_data = client_data.loc[cus_no,:]
                #tax_data = tax_rep_fee.loc[cus_no,:]
                template_name = 'zfd_layerfee.html'
                counterstr = get_counter()
                file_meta,return_err1,return_err2 = template_invoice(fee_data,cus_data,line,counterstr,select_year,cus_no,template_name)
                if not file_meta:
                    continue
                if return_err1:

                    st.error(return_err1)
                    logger.info(f"Error:{return_err1}")
                    return_err1_arr.append(return_err1)
                if return_err2:
                    st.error(return_err2)
                    logger.info(f"Error:{return_err2}")
                    return_err2_arr.append(return_err2)

                logger.info(f"invoice 已经准备就绪")

                if file_meta['eur_amount'] == 0:
                    # print(f'eur_amount==0')
                    if os.path.exists(file_meta['filepath']):   # 如果文件存在 则删除
                        os.remove(file_meta['filepath'])
                    continue

                '''save pdf to share drive'''
                logger.info(f"向Google Drive中加载文件")
                parent_id = google.find_shared_folder_id_by_name(file_meta['filedate'],google.savepdf_folder_ID)
                if not parent_id:
                    # 没有 则创建
                    parent_id = google.create_folder(file_meta['filedate'],google.savepdf_folder_ID,shared=True)
                # print(f'pdf保存的文件夹id{parent_id}')
                attachment = {
                    'name': file_meta['filename'],
                    'parents':parent_id,
                    'filepath':file_meta['filepath'],
                }
                google.upload_to_drive(attachment,shared = True)   # 20250812
            

                '''write invoice_no into google sheet'''
                
                result = google.update_values(file_meta['invoiceno'],file_meta['range_'])    # 20250812

                logger.info(f'向Google Sheet中写入完成,{file_meta['invoiceno']}')
                # st.write(result)
            

                '''remonve file'''
                # if os.path.exists(file_meta['filepath']):   # 如果文件存在 则删除
                #     os.remove(file_meta['filepath'])

                '''Done'''
                # logger.info(f'向Google Drive中写入完成,{file_meta['invoiceno']}')
                st.info(f'{cus_no}:{file_meta["cus_name"]} Done')
        
        logger.info(f'🎈 Done')
        st.success('Done')

        print(f'return_err1_arr \n {return_err1_arr}')
        print(f'return_err2_arr \n {return_err2_arr}')


    if st.button('📤 查询 Drive 并发送INV至客户邮箱'):
        # 读取sheet表  
        st.info('Start')
        # sheet_data = google.read_sheet_batchGet(range_name)
        imi_file_bytes = ''
        
        # 处理client_data和cs的数据
        
        
        
        if no_imi == [] and no_email == []:
            st.info('开始执行......')
            send_invoice_form(google,summSheet,client_data,select_year,select_templated)
            
        st.info(f'send failed = {send_failed}')
        st.markdown("---")
        st.success('Done')

    
    if st.button('🧾 生成 收据 Receipt'):
        st.info('Start')
        print('Start')
        print(summSheet)
        # 仅仅只需要summSheet中的表单
        # 需要剔除 无收据号码的
        
        summSheet = summSheet.dropna(subset=[field_name_1])
        print('Enter')
        # 剔除invoice no. 在 receipt_csv中的行
        cond = summSheet[field_name_1].isin(receipt_csv['invoice_no'])
        summSheet = summSheet[~cond]

        print(summSheet)
        for cus_no,fee_data in summSheet.iterrows():
            '''
            num指的是 这行的索引，此处指的是2019AR1,,,
            
            '''
            if 'Builder Cost' in fee_data['Paid_Date'].title():
                 fee_data['Paid_Date'] = 'Builder Cost'
            # print(f'第{cus_no}行的值是:')  
            # 应该使用invoice_no做索引
            receipt_invoice_number = fee_data['INVOICE NO. & Date']
            print('invoice_number',receipt_invoice_number)
            invoice_no= fee_data['Invoice no.']

            if not receipt_invoice_number:
                continue

            if receipt_invoice_number and receipt_invoice_number != invoice_no:
                continue
            if receipt_invoice_number and receipt_invoice_number in receipt_csv.index:   # 已经生成了客户号
                # st.info(f'已于{receipt_csv[receipt_invoice_number]['generate_date']}')
                continue # 不会重新生成receipt
                
            # cus_no = fee_data.name             # 获取到了客户号
                #print(regenerate_)
            # if regenerate_ != ['']:    # 当其不为空
            #     if cus_no not in regenerate_:
            #         continue

            #print('continue')
            if not cus_no: 
                continue
            # 通过索引找

            #print('********************')
            # print(fee_data)
            cus_data = client_data.loc[cus_no,:]

            if pd.isna(fee_data['INVOICE NO. & Date']):   # 如果这里根本没有invocie no 那就是没有支付完成，不需要生成receipt
                continue 
            cus_metadata = get_file_meta(fee_data,cus_data,cus_no,select_year,'receipt',0)
            # 读取Invoice No和INVOICE NO. & Date 如果两者不同，不进行下一步
            
            
            if pd.isna(cus_metadata):
                continue
            #  --------------
            try:
                file_metadata = generate_receipt(cus_metadata)
                # 将文件上传到drive中
                receipt_date = cus_metadata['receipt_data_googlesheet'].split('/')
                folder_year = receipt_date[0]
                print(f'receipt_date = {receipt_date}')
                folder_month = month_mapper[receipt_date[1]]
                parent_id = google.savereceipt_folder_ID
                # 寻找文件夹 folder_year  没有则创建
                first_parent_id = google.find_shared_folder_id_by_name(folder_year,parent_id)
                
                if pd.isna(first_parent_id):
                    first_parent_id = google.create_folder(folder_year,parent_id,shared = True)
                
                # 找到文件夹 folder_month 没有则创建
                second_parent_id = google.find_shared_folder_id_by_name(folder_month,first_parent_id)
                
                if pd.isna(second_parent_id):
                    second_parent_id = google.create_folder(folder_month,first_parent_id,shared = True)

                
                attachment = {
                        'name': file_metadata['filename'],
                        'parents':second_parent_id,
                        'filepath':file_metadata['filepath'],
                    }
                

                is_upload = google.upload_to_drive(attachment,shared = True)
            except Exception as e:
                st.error(f'e')
            # -------------------

            # is_upload  = True
            if is_upload: # 生成了receipt
                # 写入doc中
                with open(receipt_csv_path,'a',newline = '',encoding = 'utf-8') as file:
                    writer = csv.writer(file)
                    value = [cus_metadata['receipt_invoice_number'],cus_no,today,'']
                    writer.writerow(value)
                
                
            

            st.info(f'Success {cus_no}!!!')
        
        # 将receipt更新到csv文件中 
        # receipt_csv.to_csv(receipt_csv_path,index=True,encoding='utf-8-sig')   # 避免中文乱码
        st.info('Success')

    # 从receipt_generate_sended中删除
    # if st.button('🧾 删除 已经生成的Receipt'):
    #     cond = receipt_csv['']

    if st.button('📤 查询Drive 并发送收据RPT给客户'):
        # 读取客户的invoice_number
        st.info('Start')
        # 只提取invoice_number 在 receipt_generate_sended.csv 中的
        # 提取出 csv文件中，已经生成了receipt但是未发送的
        send_receipt(google,field_name_1,client_data,select_year,select_templated,today,receipt_csv_path,send_failed,summSheet)  
        st.success('Done')

    if st.button('仅发送IRS Bank Proof'):
        st.info('Start')
        send_IRS_Bank_Proof(google,client_data,select_year,select_templated,summSheet)
        st.success('Done')


    


def send_receipt(google:GoogleClass,field_name_1,client_data,select_year,select_templated,today,receipt_csv_path,send_failed,summSheet):
    # select_templated = 'Receipt_Remind-IRS'
    receipt_csv = pd.read_csv(receipt_csv_path,header = 0,dtype={'sended_date':str})
    no_sended = receipt_csv[pd.isna(receipt_csv['sended_date'])]['invoice_no']

    pre_cond = summSheet[field_name_1].isin(no_sended)
    print(pre_cond)
    summSheet = summSheet[pre_cond]

    ### 发送irs
    # regenerate_ = ''
    # regenerate_ = ['2019PB1','2019TI1','2022CS5','2022CS9','2022CS13','2022CS14','2022CS16','2023CS7','2023CS8','2023CS4']
    # if regenerate_ != ['']:    # 当其不为空
    #     summSheet = summSheet.loc[regenerate_]

    logging.info("发送receipt 📤📤📤📤📤📤📤")
    print(summSheet)
    for cus_no,fee_data in summSheet.iterrows():
        if not cus_no:
            continue
        cus_data = client_data.loc[cus_no,:]
        cus_metadata = get_file_meta(fee_data,cus_data,cus_no,select_year,'receipt',0)

        if not cus_metadata:
            continue
        send_file_content = {}
        receipt_invoice_number = cus_metadata['receipt_invoice_number']
        # 去receipt中去查找
        receipt_date = cus_metadata['receipt_data_googlesheet'].split('/')
        folder_year = receipt_date[0]
        folder_month = month_mapper[receipt_date[1]]
        parent_id = google.savereceipt_folder_ID
        find_receipt = True

        
        print(cus_metadata)
        '''寻找客户的receipt'''
        # 寻找 folder_year
        first_parent_id = google.find_shared_folder_id_by_name(folder_year,parent_id)
        if pd.isna(first_parent_id):
            find_receipt = False
        else: # 只有当first_parent_id 存在时
            second_parent_id = google.find_shared_folder_id_by_name(folder_month,first_parent_id)

            if pd.isna(second_parent_id):
                find_receipt = False
                # 寻找客户的receipt
            else:
                file_ids= google.find_file_by_name(second_parent_id,True,receipt_invoice_number)
                if len(file_ids) == 0:
                    find_receipt = False
        

        if find_receipt:  # 找到了receipt
            # 发送receipt
            for file_id in file_ids:
                send_file_content[file_id] = {}
                send_file_content[file_id]['file_bytes'] = google.download_file_from_drive(file_id)
                file_type = google.get_file_metadata(file_id)
                type = file_type['mimeType'].split('/')
                send_file_content[file_id]['maintype']  = type[0]
                send_file_content[file_id]['subtype']  = type[1]
                send_file_content[file_id]['filename']  =file_type['name']
        '''Find IMI Receipt'''
        if cus_metadata['is_imi']:   # 如果是有imi单子的，就会
            # 查找imi文件夹
            #imi_folder_name = ' '.join(['IMI',current_year.strftime('%Y')])
            imi_proof_parent_id = google.saveimi_bank_proof_folder_ID
            # imi_folder_id = google.find_shared_folder_id_by_name(imi_folder_name,imi_parent_id) 
            cus_NIF = cus_metadata['NIF']   
            # 找到imi_file_id 这是一个数组，一个客户可能包含多个imi_file_id
            # 需要寻找文件夹id
            folder_name = f'{int(select_year)-1} Paid'
            imi_parent_id = google.find_shared_folder_id_by_name(folder_name,imi_proof_parent_id)

            imi_file_id = google.find_file_by_name(imi_parent_id,True,cus_NIF,True)    # 返回文件id
            print(f'imi_file_id = {imi_file_id}')
            if len(imi_file_id) != 0:
                #  下载imi文件
                for file_id in imi_file_id:
                    send_file_content[file_id] = {}
                    send_file_content[file_id]['file_bytes'] = google.download_file_from_drive(file_id)
                    file_type = google.get_file_metadata(file_id)
                    type = file_type['mimeType'].split('/')
                    send_file_content[file_id]['maintype']  = type[0]
                    send_file_content[file_id]['subtype']  = type[1]
                    send_file_content[file_id]['filename']  =file_type['name']
                    
            else:   # 产生了imi但未找到imi 买了房子但是未过户
                # can_send = False
                print(f'No find imi.pdf,税号({cus_NIF}) 仅作为提示，邮件照常发送')


        '''Send Email'''   
        print(f'Sending Email......')
        if cus_metadata['is_email']: 
            result = None
            content,subject = generate_html_email_content(select_templated,cus_metadata)
            email = {
                    'to_email':cus_metadata['email'],
                    'bcc_email':cus_metadata['qb_email']
                }
            result = ali_send_email(content,subject,send_file_content,email)
            st.info(f'{cus_no}_send Email result={result}')
            if result == 'Success':
                cond = receipt_csv['invoice_no'] == receipt_invoice_number
                receipt_csv.loc[cond,'sended_date'] = today
                receipt_csv.to_csv(receipt_csv_path,index=False,encoding = 'utf-8-sig')
            if result!='Success':
                send_failed.append(cus_no)

            if not result:
                print(f'{cus_metadata['invoiceno']}:Send Email Error')  
        else:
            print(f'{cus_no},Is_Emamil = False')
        


def send_invoice(google:GoogleClass,summSheet,client_data,select_year,select_templated):
    
    # === 定制化内容 ===
    regenerate_ = ['']
    # -----------
    # regenerate_ =['2019PB1', '2019TI1', '2019TI2', '2020OV1', '2022CS5', '2022CS8', '2022CS9', '2022CS13', '2022CS14', '2022CS16', '2022CS17', '2023CS3', '2023CS4', '2023CS5', '2023CS7', '2023CS8', '2023JUN','2022CS6','2023CS6','2023CS9']
    
    # ------------
    # select_templated = 'template1'


    send_failed = []

    if regenerate_ != ['']:    # 当其不为空
        summSheet = summSheet.loc[regenerate_]

    # 当其为空时，扫描各数据将需要发送的invoice进行发送
    for line in range(summSheet.shape[0]):
                # print(f'line = {line}')
                # print(summSheet)
                
        can_send = True
        send_file_content = {}
        
        fee_data = summSheet.iloc[line,:]    # <class 'pandas.core.series.Series'>
        
        cus_no = fee_data.name             # 获取到了客户号
        
        if not cus_no:
            continue

        cus_data = client_data.loc[cus_no,:]
        # tax_data = tax_rep_fee.loc[cus_no,:]

        # 客户的invoice_no
        invoice_no = fee_data['Invoice no.'].replace(' ','')
        if not invoice_no:
            continue
        
        # 获取客户的原数据 get_file_meta(fee_data,cus_data,cus_no,year,type:str = '',num:int=0)
        file_meta_simple = get_file_meta(fee_data,cus_data,cus_no,select_year)
        print(file_meta_simple)
        if pd.isna(file_meta_simple):    # file_meta_simple 的值为None
            continue
        # 不能发送客户的email
        print(f'{file_meta_simple}')
        if not file_meta_simple['is_email']:
            continue
        invoice_data = invoice_no[5:13]
        
        '''find pdf to share drive'''
        # 通过文件名称查找invoice
        # 获取保存pdf的文件夹
        folder_id = google.find_shared_folder_id_by_name(invoice_data,google.savepdf_folder_ID)
        # find_file_by_name(self,parents_id,shared,filename,NIF:bool = False)
        print(f'folder_id = {folder_id}')
        invoice_file_id = google.find_file_by_name(folder_id,True,invoice_no,False)
        print(f'invoice_file_id = {invoice_file_id}')
        # 下载文件
        print(f'Find invoice .......')
        if invoice_file_id:
            for f_id in invoice_file_id: # invoice 只有一个
                invocie_file_bytes = google.download_file_from_drive(f_id)
                send_file_content['invoice'] = {}
                send_file_content['invoice']['file_bytes'] = invocie_file_bytes
                send_file_content['invoice']['maintype']  = 'application'
                send_file_content['invoice']['subtype']  = 'pdf'
                send_file_content['invoice']['filename'] = 'invoice.pdf'
        else:
            can_send = False
            st.error(f'No find invoice:{invoice_no}')
            continue          # 未找到客户的invoice那么就退出此次循环  
    
        '''find imi'''
        print(f'Find imi .......')
        if file_meta_simple['is_imi']:
            # 查找imi文件夹
            #imi_folder_name = ' '.join(['IMI',current_year.strftime('%Y')])
            imi_parent_id = google.saveimi_folder_ID
            # imi_folder_id = google.find_shared_folder_id_by_name(imi_folder_name,imi_parent_id) 
            cus_NIF = file_meta_simple['NIF']   
            # 找到imi_file_id 这是一个数组，一个客户可能包含多个imi_file_id
            imi_file_id = google.find_file_by_name(imi_parent_id,True,cus_NIF,True)    # 返回文件id
            print(f'imi_file_id = {imi_file_id}')
            if imi_file_id:
                #  下载imi文件
                for file_id in imi_file_id:
                    send_file_content[file_id] = {}
                    send_file_content[file_id]['file_bytes'] = google.download_file_from_drive(file_id)
                    file_type = google.get_file_metadata(file_id)
                    type = file_type['mimeType'].split('/')
                    send_file_content[file_id]['maintype']  = type[0]
                    send_file_content[file_id]['subtype']  = type[1]
                    send_file_content[file_id]['filename']  =file_type['name']
                    
            else:   # 产生了imi但未找到imi 买了房子但是未过户
                # can_send = False
                print(f'No find imi.pdf,税号({cus_NIF}) 仅作为提示，邮件照常发送')
                

        '''send email to customer'''
        print(f'{file_meta_simple['is_email']}')
        if file_meta_simple['is_email'] and can_send :
            # 处理send_email 事项
            
            print(f'Sending Email......')
            if file_meta_simple['email']:
                result = None
                
                #subject  ='关于葡萄牙黄金签证相关费用缴纳提醒 Important Notice on Portugal Golden Visa-Related Fee Payments' 
                #ali_send_email(email_content:dict,email_subject,files:dict,email:dict)
                content,subject = generate_html_email_content(select_templated,file_meta_simple)
                email = {
                    'to_email':file_meta_simple['email'],
                    'bcc_email':file_meta_simple['qb_email']
                }
                result = ali_send_email(content,subject,send_file_content,email)
                print(f'{cus_no}_send Email result={result}')
                if result!='Success':
                    send_failed.append(cus_no)
                if not result:
                    print(f'{file_meta_simple['invoiceno']}:Send Email Error')
            else:
                st.error(f'{file_meta_simple['invoiceno']}未提取到有效的邮箱地址，请及时补充')
        time.sleep(20)
    

        '''write invoice_no into google sheet'''
        # result = google.update_values(file_meta_simple['invoiceno'],file_meta_simple['range_'])
        # st.write(result)
    

        '''remonve file'''
        # if os.path.exists(file_meta['filepath']):   # 如果文件存在 则删除
        #     os.remove(file_meta['filepath'])

        '''Done'''
        
        print(f'{cus_no}:{file_meta_simple["cus_name"]} Done')


                    
# ===============================
# 仅仅发送IRS的Bank_Proof   
# 按照需要发送的客户号进行发送
# 判断发送的邮件信息
# =============================
def send_IRS_Bank_Proof(google:GoogleClass,client_data,select_year,select_templated,summSheet):
    # select_templated = 'Receipt_Remind-IRS'
    can_send  =True     # 默认能够找到irs 
    ### 发送irs
    # regenerate_ = ''
    # regenerate_ = ['2019PB1','2019TI1','2022CS5','2022CS9','2022CS13','2022CS14','2022CS16','2023CS7','2023CS8','2023CS4']
    # if regenerate_ != ['']:    # 当其不为空
    #     summSheet = summSheet.loc[regenerate_]

    print("📤📤📤📤📤📤📤")
    print(summSheet)
    for cus_no,fee_data in summSheet.iterrows():
        if not cus_no:
            continue
        cus_data = client_data.loc[cus_no,:]
        # 仅需要获取 发送邮件的相关信息
        cus_meta_simple = get_cus_info(cus_data)
        
        send_file_content = {}

        
        if not cus_meta_simple.get('is_email'):
            continue

        email = {
            'to_email':cus_meta_simple.get('to_email'),
            'bcc_email':cus_meta_simple.get('bcc_email')
        }
        '''寻找客户的IRS'''

        
        irs_proof_parent_id = google.saveirs_bank_proof_folder_ID 
        cus_NIF = cus_data['MA NIF']  
        # 找到imi_file_id 这是一个数组，一个客户可能包含多个imi_file_id
        # 需要寻找文件夹id
        folder_name = f'{int(select_year)-1} PAID'
        irs_parent_id = google.find_shared_folder_id_by_name(folder_name,irs_proof_parent_id)
        irs_file_id = google.find_file_by_name(irs_parent_id,True,cus_NIF,True)    # 返回文件id
        print(f'irs_file_id = {irs_file_id}')
        if irs_file_id:
            #  下载imi文件
            for file_id in irs_file_id:
                send_file_content[file_id] = {}
                send_file_content[file_id]['file_bytes'] = google.download_file_from_drive(file_id)
                file_type = google.get_file_metadata(file_id)
                type = file_type['mimeType'].split('/')
                send_file_content[file_id]['maintype']  = type[0]
                send_file_content[file_id]['subtype']  = type[1]
                send_file_content[file_id]['filename']  =file_type['name']
        else:   # 未找到irs 则不发送irs
            can_send = False
            print(f'No find irs file,税号({cus_NIF})请检查irs文件夹或客户号是否，默认未找到irs文件时,不发送email')
        
        '''Send Email'''   
        print(f'Sending Email......')
        if can_send:
            result = None
            # get_email_html_content(template,cus_name,fee_content,email_date,email_date_eng,invoice_no = '',day:int=7)
            content,subject = generate_html_email_content(select_templated,cus_meta_simple)

            result = ali_send_email(content,subject,send_file_content,email)
            # result = ali_send_email(select_templated,send_file_content,cus_data)
            st.info(f'{cus_no}_send Email result={result}')
        else:
            print(f'{cus_no},Is_Emamil = False')
            


def send_invoice_form(google:GoogleClass,summSheet,client_data,select_year,select_templated):
    
    # === 定制化内容 ===
    # regenerate_ = ['']
    # -----------
    # regenerate_ =['2019PB1', '2019TI1', '2019TI2', '2020OV1', '2022CS5', '2022CS8', '2022CS9', '2022CS13', '2022CS14', '2022CS16', '2022CS17', '2023CS3', '2023CS4', '2023CS5', '2023CS7', '2023CS8', '2023JUN','2022CS6','2023CS6','2023CS9']
    
    # ------------
    # select_templated = 'template1'

    logging.info('📌 开始发送invoice')
    send_failed = []

    # if regenerate_ != ['']:    # 当其不为空
    #     summSheet = summSheet.loc[regenerate_]

    # 当其为空时，扫描各数据将需要发送的invoice进行发送
    for line in range(summSheet.shape[0]):
                # print(f'line = {line}')
                # print(summSheet)
                
        can_send = True
        send_file_content = {}
        
        fee_data = summSheet.iloc[line,:]    # <class 'pandas.core.series.Series'>
        
        cus_no = fee_data.name             # 获取到了客户号
        
        if not cus_no:
            continue

        cus_data = client_data.loc[cus_no,:]
        # tax_data = tax_rep_fee.loc[cus_no,:]

        # 客户的invoice_no
        invoice_no = fee_data['Invoice no.'].replace(' ','')
        if not invoice_no:
            continue
        
        # 获取客户的原数据 get_file_meta(fee_data,cus_data,cus_no,year,type:str = '',num:int=0)
        file_meta_simple = get_file_meta(fee_data,cus_data,cus_no,select_year)
        logging.info(file_meta_simple)
        if pd.isna(file_meta_simple):    # file_meta_simple 的值为None
            logging.info('❌ 客户的file_meta_simple为None,继续下一个客户')
            continue
        # 不能发送客户的email
        # print(f'{file_meta_simple}')
        if not file_meta_simple['is_email']:
            logging.info('❌ 不发送邮件,继续下一个客户')
            continue
        invoice_data = invoice_no[5:13]
        
        '''find pdf to share drive'''
        # 通过文件名称查找invoice
        # 获取保存pdf的文件夹
        logging.info('寻找客户invoice文件ing,,,,,,')
        folder_id = google.find_shared_folder_id_by_name(invoice_data,google.savepdf_folder_ID)
        # find_file_by_name(self,parents_id,shared,filename,NIF:bool = False)
        print(f'folder_id = {folder_id}')
        invoice_file_id = google.find_file_by_name(folder_id,True,invoice_no,False)
        print(f'invoice_file_id = {invoice_file_id}')
        # 下载文件
        print(f'Find invoice .......')
        if invoice_file_id:
            for f_id in invoice_file_id: # invoice 只有一个
                invocie_file_bytes = google.download_file_from_drive(f_id)
                send_file_content['invoice'] = {}
                send_file_content['invoice']['file_bytes'] = invocie_file_bytes
                send_file_content['invoice']['maintype']  = 'application'
                send_file_content['invoice']['subtype']  = 'pdf'
                send_file_content['invoice']['filename'] = 'invoice.pdf'
        else:
            can_send = False
            logging.info(f'未发现客户的invocie:{invoice_no},继续下一个客户')
            st.error(f'No find invoice:{invoice_no}')
            continue          # 未找到客户的invoice那么就退出此次循环  
    

        '''find imi'''
        if file_meta_simple['is_imi']:

            logging.info('寻找客户imi文件ing,,,,,,')

            imi_parent_id = google.saveimi_folder_ID
      
            cus_NIF = file_meta_simple['NIF']   
 
            imi_file_id = google.find_file_by_name(imi_parent_id,True,cus_NIF,True)    # 返回文件id

            if imi_file_id:
                #  下载imi文件
                for file_id in imi_file_id:
                    send_file_content[file_id] = {}
                    send_file_content[file_id]['file_bytes'] = google.download_file_from_drive(file_id)
                    file_type = google.get_file_metadata(file_id)
                    type = file_type['mimeType'].split('/')
                    send_file_content[file_id]['maintype']  = type[0]
                    send_file_content[file_id]['subtype']  = type[1]
                    send_file_content[file_id]['filename']  =file_type['name']
                    
            else:   
                logger.info(f'No find imi.pdf,税号({cus_NIF}) 仅作为提示，邮件照常发送')
                
        
        
        logger.info(f'检查是否需要更换税务代表')
        if file_meta_simple['is_tax_rep_change']:
            # 寻找文件
            parent_parent_id = '1khiIAEXoBT7caTXIX5wJlzGDy_FwD6wM'   # 需要更换税务代表
            folder_name = file_meta_simple.get('cus_name').replace(' ','')
            filename = 'Proxy and Appointment of Tax Representative'
            # 找到客户名字的文件夹
            parent_id = google.find_shared_folder_id_by_name(folder_name,parent_parent_id,mode=1)
            # 进入文件夹找到文件
            fileids = google.find_file_by_name(parent_id,True,filename)
            if fileids:
                for fileid in fileids:
                    send_file_content[fileid] = {}
                    send_file_content[fileid]['file_bytes'] = google.download_file_from_drive(fileid)
                    file_type = google.get_file_metadata(fileid)
                    type = file_type['mimeType'].split('/')
                    send_file_content[fileid]['maintype']  = type[0]
                    send_file_content[fileid]['subtype']  = type[1]
                    send_file_content[fileid]['filename']  =file_type['name']
            else:
                logger.info(f"❌ 客户{file_meta_simple.get('cus_name')}需要更换税务代表，未发现需签署文件，请检查，邮件暂不发送")
                st.error(f"❌ 客户{file_meta_simple.get('cus_name')}需要更换税务代表，未发现需签署文件，请检查，邮件暂不发送")
                continue

        '''send email to customer'''
        logger.info(f'准备发送Email，{file_meta_simple['is_email']}')
        if file_meta_simple['is_email'] and can_send :            
            if file_meta_simple['email']:
                result = None
                
                #subject  ='关于葡萄牙黄金签证相关费用缴纳提醒 Important Notice on Portugal Golden Visa-Related Fee Payments' 
                #ali_send_email(email_content:dict,email_subject,files:dict,email:dict)
                content,subject = generate_html_email_content(select_templated,file_meta_simple)
                email = {
                    'to_email':file_meta_simple['email'],
                    'bcc_email':file_meta_simple['qb_email'] + file_meta_simple['cs_email']
                }
                logger.info(f'开始发送Email')
                result = ali_send_email(content,subject,send_file_content,email)
                # print(f'{cus_no}_send Email result={result}')
                logger.info(f'{cus_no}_send Email result={result}')
                if result!='Success':
                    send_failed.append(cus_no)
                if not result:
                    logger.info(f'❌{file_meta_simple['invoiceno']}:Send Email Error：{result}')
                    time.sleep(60)
                    # print(f'{file_meta_simple['invoiceno']}:Send Email Error')
            else:
                logger.info(f'❌{file_meta_simple['invoiceno']}未提取到有效的邮箱地址，请及时补充')
                st.error(f'{file_meta_simple['invoiceno']}未提取到有效的邮箱地址，请及时补充')
        sleep_time = random.uniform(20,40)
        logger.info(f'睡眠{sleep_time}s')
        time.sleep(sleep_time)
    

        '''write invoice_no into google sheet'''
        # result = google.update_values(file_meta_simple['invoiceno'],file_meta_simple['range_'])
        # st.write(result)
    

        '''remonve file'''
        # if os.path.exists(file_meta['filepath']):   # 如果文件存在 则删除
        #     os.remove(file_meta['filepath'])

        '''Done'''
        
        # print(f'{cus_no}:{file_meta_simple["cus_name"]} Done')


                
                
            
