import os

from Controller.deal_sheet_data import *
from datetime import datetime,timedelta
from Controller.func import *
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from Model.GoogleAPI import *

def generate_receipt(meta_data):

    return_file = {}
    env = Environment(loader = FileSystemLoader('./View'))
    template_zfd_layerfee = env.get_template('receipt.html')
    rpt = template_zfd_layerfee.render(meta_data)

    print(f'20250619 \n {meta_data}')

    invoice_no = meta_data['receipt_invoice_number']
    invoice_name = meta_data['cus_name']
    actually_curr = meta_data['actually_curr_paid_eng']
    actually_amount = meta_data['actually_cur_amount']
    receipt_date_filepath = meta_data['receipt_data_filepath'] # 2025年6月3日

    # 将渲染出来的html转为pdf
    file_name = f'RPT_{invoice_no}_{invoice_name}_{receipt_date_filepath}_{actually_curr}{actually_amount}.pdf'
    file_path = os.path.join('temp_file',file_name)
    
    return_file['filename'] = file_name
    return_file['filepath'] = file_path

    
    HTML(string=rpt).write_pdf(file_path)   # 将文件保存到本地
    print('Receipt已经生成')
    
    return return_file
    
