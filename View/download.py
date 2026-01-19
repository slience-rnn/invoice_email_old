import pandas as pd
from Model.GoogleAPI import GoogleClass
from io import BytesIO
import os
import pickle
# 如果有excel 那么就退出
def download_doc(google:GoogleClass):
    save_dir = 'temp_file\client_info_1_c'
    content = []
    name_mapper = {}
    folders = google.list_all_folders(google.savecus_personal_data_folder_ID,'Client Info')
    # for folder in folders:
    #     name = folder['name']
    #     n = name.split('.')
    #     if len(n) !=2:
    #         continue
    #     key = n[0].replace(' ','')
    #     value = n[1].replace(' ','').lower()
    #     name_mapper[value] = key
    # # folders = folders[:50]
    # print(name_mapper)
    
    for folder in folders:
        # 进入folder中下载excel 
        parent_id = folder.get('id','')
        shared = True
        filename = 'client' #asset
        save_path = os.path.join(save_dir,folder['name'])
        result_excel = google.search_file_in_folder(parent_id,filename,'Client Info',save_path)
        #excel_id  = google.find_file_by_name(parent_id,shared,filename)
        # if not excel_id:
        #     # 如果没有发现 那么就需要进入客户personal data
        #     folder = 'personal data'
        #     personal_data_id = google.find_shared_folder_id_by_name(folder,parent_id)
        #     if personal_data_id:
        #         excel_id = google.find_file_by_name(personal_data_id,shared,filename)
        # # print(f'excel_id = {excel_id}')
        if result_excel:
            print(f'已经保存{result_excel}')
            continue
        
            # 如果找到了就下载
            # return True
            # file_bytes = google.download_file_from_drive(excel_id[0])
            # content.append(file_bytes)
            # save_file_to_local(save_path,excel_id[0],file_bytes = file_bytes)
            
        # else: # 寻找A1 文档和 employment
        #     # A1
        #     result_a1 = google.search_file_in_folder(parent_id,'a1','Client Info',save_path)
        #     # employment
        #     if result_a1:
        #         print(f'已经保存A1')
        #     result_emp = google.search_file_in_folder(parent_id,'employment','Client Info',save_path)
        #     if result_emp:
        #         print(f'已经保存Employment')
    # 将所有读取的内容保存
    # with open('data.pkl','wb') as f:
    #     pickle.dump(content,f)

        


def save_file_to_local(save_dir,filename,**kwargs):
    # 确保路径存在
    os.makedirs(save_dir,exist_ok=True)
    save_path = os.path.join(save_dir,f'{filename}.xlsx')
    if 'file_bytes' in kwargs:
        file_bytes = kwargs.get('file_bytes')
        with open(save_path,'wb') as f:
            f.write(file_bytes)
        print(f"文件已经保存到{save_path}")



def read_excel_from_bytes(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes),dtype=str)
    df  =df.fillna('')
    return df
        
        
# 下载整份文件夹
def download_folder(google:GoogleClass):
    save_dir = 'temp_file\\client_info_zip'
    folders = google.list_all_folders(google.savecus_personal_data_folder_ID,'Client Info')
    folders = folders[30:]
    print(folders)
    for folder in folders:
        # 进入folder中下载excel 
        parent_id = folder.get('id','')
        folder_name = folder.get('name','')
        folder_id  = google.find_shared_folder_id_by_name('Personal Data',parent_id)
        if folder_id:
            print(f'Personal Data folder_id = {folder_id}')
            new_dir = os.path.join(save_dir,folder_name)
            google.download_folder(folder_id,new_dir,drive_name = 'Client Info')
            print(f'{folder_name} already downloaded!')
    # 将所有读取的内容保存
    # with open('data.pkl','wb') as f:
    #     pickle.dump(content,f)
    
# 下载某个
def find_doc(google:GoogleClass):
    save_dir = 'temp_file\\client_info_1_c'
    folders = google.list_all_folders(google.savecus_personal_data_folder_ID,'Client Info')
    folders = folders[:50]
    for folder in folders:
        parent_id = folder['id']
        shared = True
        filename = '.xlsx'
        excel_id  = google.find_file_by_name(parent_id,shared,filename)
        if excel_id:   # 如果存在
            continue
        else: # 寻找A1 文档和 employment
            path = os.path.join(save_dir,folder['name'])
            google.search_file_in_folder(parent_id,'a1','Client Info',path)
# 读取pickle
# with open('data.pkl','rb') as f:
#     loaded_list = pickle.load(f)
# 50-
# 这些资料是准备移民到葡萄牙的客户的基本信息，从这里面帮我提取客户的英文名称，中文名称，出生日期，教育水平，工作单位，职位，年收入，居住地，总资产，家庭申请情况(一家三口，一家五口等), 孩子数量，婚姻状态，年龄等信息
# 帮我整合在一张表上，输出是csv格式的那种，如果这个客户由配偶的那就是结婚了，如果没有配偶的，就是单身



