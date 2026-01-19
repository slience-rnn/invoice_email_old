from Controller.func import *
from Model.GoogleAPI import *
import pandas as pd
def check_info(google:GoogleClass,client_data,summSheet):
    no_email=[]
    no_imi = []
    #print(summSheet)
    for line in range(summSheet.shape[0]): 
        # 检查是否能够找到imi文件，如果需要发送文件，邮件是否存在

        fee_data = summSheet.iloc[line,:]    # <class 'pandas.core.series.Series'>
        
        #print(fee_data)
        cus_no = fee_data.name             # 获取到了客户号
        if not cus_no:
            continue
        cus_data = client_data.loc[cus_no,:]
        
        # tax_data = tax_rep_fee.loc[cus_no,:]
        #print(f'cus_data值是{cus_data}')
        NIF = cus_data['MA NIF']
    
        # 查找是否需要发送emial
        is_email = cus_data['是否發送Email 2025.05.15']
        #print(is_email)
        email = cus_data['Email']
        if is_email == 'Y':
            if not email:
                no_email.append(cus_no)

        # 是否需要imi
        is_imi = current(fee_data['IMI'])
        imi_paid_date= fee_data['IMI Paid Date']
        if is_imi and imi_paid_date in ['',' ','/','?']:
            # print('---------------------------------------')
            # print(NIF)
            # 获取税号 查询是否能够   def find_file_by_name(self,parents_id,shared,filename,NIF:bool = False):
            id = google.find_file_by_name(google.saveimi_folder_ID,True,NIF,True)
            if not id:
                no_imi.append(cus_no)
    return no_imi,no_email
    

            


            