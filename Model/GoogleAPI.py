'''
function:
使用同一个账号
1. 读取sheets中的内容
2. 更改sheets中的内容
3. 向共享drive中新建文件夹
4. 向共享drive中存储pdf文件
5. 需要使用gmail发送邮件
Note:
saveimi_folder_id 需要及时更新
'''

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload,MediaIoBaseUpload,MediaIoBaseDownload
from googleapiclient.errors import HttpError
from email.message import EmailMessage
from google.oauth2 import service_account
import pandas as pd
import os.path
import os
import base64
import io
import re
import configparser
from datetime import datetime
import json


class GoogleClass:

	# 需要初始化
	gmail_service = ''
	sheets_service = ''
	share_drive_service = ''

	# 初始化中需要从配置文件中读取的
	savesheet_folder_ID = ''
	savepdf_folder_ID = ''
	saveimi_folder_ID = ''
	saveimi_bank_proof_folder_ID= ''
	saveirs_bank_proof_folder_ID= ''
	savereceipt_folder_ID = ''
	savecus_personal_data_folder_ID = ''
	# saveirs_payment_proof_folder_ID = ''

	# from_eamil
	from_email =''

	creds = None  # 初始化用户凭证 
	
	


	SCOPES = [ #'https://www.googleapis.com/auth/gmail.readonly', 
			  'https://www.googleapis.com/auth/spreadsheets',    #'https://www.googleapis.com/auth/drive.file', # 写入自己的云盘
			  'https://www.googleapis.com/auth/drive',   
			  'https://www.googleapis.com/auth/gmail.send',  # 发送邮件
			  ]    #访问权限
	
	

	token_path = '.\\config\\token.json'   # 用于访问google.json

	credentials_path = '.\\config\\credentials.json'   # 应用的身份凭证，是OAuth客户端凭据文件，用于发起OAuth2授权流程


	def __init__(self):
		
		config_path = os.path.join('.\\','config','config.ini')
		
		config_path = os.path.abspath(config_path)
		print(config_path)
		print("是否找到文件:",os.path.exists(config_path))
		config = configparser.ConfigParser()
		
		# 读取配置文件
		config.read(config_path)
		print(config.sections())
		self.sheet_id = config['sheet']['sheet_id']
		self.savepdf_folder_ID = config['drive']['savepdf_folder_id']
		self.saveimi_folder_ID = config['drive']['saveimi_folder_id']
	
		self.saveirs_folder_ID = config['drive']['saveirs_folder_id']
		self.savereceipt_folder_ID = config['drive']['savereceipt_folder_id']
		self.from_email = config['email']['from_email']
		self.saveimi_bank_proof_folder_ID = config['drive']['saveimi_bank_proof_folder_id']
		self.saveirs_bank_proof_folder_ID = config['drive']['saveirs_bank_proof_folder_id']
		self.savecus_personal_data_folder_ID = config['drive']['savecus_personal_data_folder_id']
		
		# 第一次授权
		self.auth_user()
		
		# 使用同一个用户的凭证访问gmail，sheets，share_drive，应为这个用户可以同时访问这三个
		self.gmail_service = build('gmail', 'v1', credentials=self.creds)
		self.sheets_service = build('sheets','v4',credentials= self.creds)
		self.share_drive_service = build('drive','v3', credentials= self.creds)

	def auth_user(self):
		# 如果token文件存在，就从token文件中加载用户凭证creds
		if os.path.exists(self.token_path):
			self.creds = Credentials.from_authorized_user_file(self.token_path,self.SCOPES)
			# 使用creds凭证创建一个Gmail API客户端对象，通过service可以调用gmail的功能

		# 如果用户凭证不存在
		if not self.creds or not self.creds.valid:
			if self.creds and self.creds.expired and self.creds.refresh_token:
				self.creds.refresh(Request())
			else:
				#print(self.creds)
				flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path,self.SCOPES)
				#flow = InstalledAppFlow.from_client_secrets_file(...)
				#auth_url,_ = flow.authorization_url(prompt = 'select_account')
				#print(f'授权{auth_url}')
				self.creds = flow.run_local_server(port = 0)
				#self.creds = flow.run_local_server(prompt = 'select_account')

			with open(self.token_path,'w') as f:
				f.write(self.creds.to_json())
		
		# 列出邮件id

	# 邮件元信息
	def get_file_metadata(self,file_id):
		file_metadata = self.share_drive_service.files().get(fileId = file_id,fields = "mimeType,name",supportsAllDrives=True).execute()
		# mime_type = file_metadata['mimeType']
		# filename =file_metadata['name']
		return file_metadata
	
	# 寻找spreadsheet表从中读取信息
	def read_sheet_batchGet(self,sheet_id,range_names = ['Client','SummSheet','TAX REP FEE']):
		try:
			results = self.sheets_service.spreadsheets().values().batchGet(
				spreadsheetId = sheet_id,
				ranges = range_names,
			).execute()
			result = results.get("valueRanges",[])
			return result
		except HttpError as error:
			print(f"An error occurred:{error}")
			return error

	def email_id_list(self,after,before):
		# senders
		s = []
		for sender in self.senders:
			s.append(f'from:{sender}')
		condition = ' OR '.join(s)
		query = f"{condition} has:attachment after:{after} before:{before} "   # 多条件组合不使用and

		# profile = self.gmail_service.users().getProfile(userId='me').execute()
		# print("当前授权账号是：", profile.get('emailAddress'))

		results = self.gmail_service.users().messages().list(userId='me', q = query ).execute()
		#print(results)
		
		messages = results.get('messages',[])
		messages_id = []
		if messages:
			messages_id = [msg.get('id') for msg in messages]
		#print(query)
		#print(messages_id)
		return messages_id

	# 获取邮件附件
	def get_attachments(self,msg_id):
		'''获取邮件的附件'''
		message = self.gmail_service.users().messages().get(userId='me',id=msg_id).execute()
		attachments = []
		parts = message['payload'].get('parts',[])
		for part in parts:
			filename = part.get('filename')
			body = part.get('body')
			attachment_id  = body.get('attachmentId')
			if filename and attachment_id:
				# 获取附件的内容
				attachment = self.gmail_service.users().messages().attachments().get(
					userId = 'me',
					messageId = msg_id,
					id = attachment_id
				).execute()
				data = attachment.get('data','') # gmail使用base64将文件进行了编码
				file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
				attachments.append({
					'filename':filename,
					'data':file_data
				})
		
		return attachments

	# data的结构[[value11,value12,value13],[values21,value22,value23]]
	def write_google_sheets(self,data):
		'''向google sheets追加文件内容'''
		try:
			self.sheets_service.spreadsheets().values().append(
				savesheet_folder_ID = self.savesheet_folder_ID,
				range = '',
				valueInputOption = 'USER_ENTERED',
				insertDataOption = 'INSERT_ROWS',
				body = {'values':data}
			).execute()
		except Exception as e:
			return {'message':'Error writen'}

	
	
	def upload_to_drive(self,attachment,shared:bool = False):
		'''上传文件到drive'''
		#pdf_data = attachment.get('data')
		filename = attachment.get('name')
		parent_id = attachment.get('parents')
		# fh = io.BytesIO(pdf_data)   #用内存创建一个类文件对象

		media = MediaFileUpload(attachment['filepath'],mimetype= 'application/pdf')

		# 找到文件存储的地方
		#parent_id = self.find_first_folder_id_to_save_pdf(address)
		#under Management
		# 找到文件名字
		file_metadata = {
			'name': filename,
			'parents':[parent_id],
		}
		is_save = True
		result = False
		if is_save:
			if shared:    # 共享
				# 按照名字搜索drive中是否有文件存在
				file_id = self.find_file_by_name(parent_id,shared,filename)
				print(f'file_id"{file_id}')
				if not file_id:
					file = self.share_drive_service.files().create(
						body = file_metadata,
						media_body = media,
						fields = 'id',
						supportsAllDrives = True   # 可上传共享网盘
					).execute()
					print(f'{filename}共享文档上传成功{parent_id}')
					if file:
						result = True
				

			if not shared:
				file = self.drive_service.files().create(
					body = file_metadata,
					media_body = media,
					fields = 'id',
					supportsAllDrives = True   # 可上传共享网盘
				).execute()
				if file:
					result = True
		return result
		
	
	def find_file_by_name(self,parents_id,shared,filename,NIF:bool = False):
		'''通过名字进行查找共享文件
		查找方式: 模糊查找，只有传递的filename包含在文件名中即返回
		'''
		#print(f'1. filename = {filename}')
		file_id = []
		q = f"'{parents_id}' in parents and trashed = false"
		if shared:
			try:
				results = self.share_drive_service.files().list(q=q,
												includeItemsFromAllDrives = True,
												supportsAllDrives = True,
												spaces='drive',
												fields = 'files(id,name)',
												pageSize=1000
												).execute()
			except Exception as e:
				return file_id

		else:
			results = self.drive_service.files().list(q=q,spaces='drive',fields = 'files(id,name)').execute()

		# print(f'NIF {NIF}')
		
		for file  in results['files']:
			# print(f'文件的名字是{file['name']}')
			file_name = file['name']
			# print(file_name)
			if NIF:
				match = re.search(r'\d{9,}',file_name)
				
				nif_extract = match.group()
				#print(f'nif_extract = {nif_extract}')
				#file_apredix = file_name.rsplit('.')[1]
				if  nif_extract == str(filename):
					#print(f'nif_extract = {nif_extract} , NIF = {NIF}')
					file_id.append(file.get('id',[]))
			else:
				#print(f'文件的名字是{file['name']}')
				if filename.lower().replace(' ','') in file_name.lower().replace(' ',''):
					# print(f'Find {file_name}')
					file_id.append(file.get('id',[]))
		
		# print(f'执行结束{file_id}')
		return file_id
	

	def download_file_from_drive(self,file_id):
		# file_id 是一个数组
		response = self.share_drive_service.files().get_media(fileId = file_id)
		file_handle = io.BytesIO()     # 在内存中读写二进制数据
		downloader = MediaIoBaseDownload(file_handle,response)
		done = False
		try:
			while not done:
				status,done = downloader.next_chunk()
				#content.append(file_handle.read())     # 返回二进制内容
			file_handle.seek(0)
			print('下载完成')
			return file_handle.read()
		except Exception as e:
			print(e)
		# done = False
		# while not done:
		# 	status,done = downloader.next_chunk()
	
		# contact是文件名称
	
	# 通过名字 寻找共享文件夹，大小写不敏感,空格也不敏感
	def find_shared_folder_id_by_name(self,filename,parent_id,mode=0):
		query = f'''
		mimeType = 'application/vnd.google-apps.folder'
		and '{parent_id}' in parents
		and trashed = false
		'''
		# print('find_shared_folder_id_by_name')
		response = self.share_drive_service.files().list(
			q = query,
			spaces ='drive',
			#corpora = 'drive',
			includeItemsFromAllDrives = True,
			supportsAllDrives = True,
			fields = 'files(id,name)'
		).execute()

		folders = response.get('files',[])

		# 大小写不敏感 精确查找
		if mode == 0:   
			for folder in folders:
				#print(folder['name'])
				if folder['name'].lower() == filename.lower():
					return folder['id']
		# 大小写不敏感，根据关键词 模糊查找
		elif mode == 1:
			for folder in folders:
				if filename.lower().replace(' ','') in folder['name'].lower().replace(' ',''):
					return folder['id'] 
		
		return None
	
	# 通过名字寻找文件夹  大小写不敏感
	def find_folder_by_name_case_insensitive(self,folder_name,parent_folder_id):
		query = "mimeType = 'application/vnd.google-apps.folder' and trashed=false"
		#parent_folder_id = self.shareinvoice_folder_id     # invoice
		if parent_folder_id:
			query += f" and '{parent_folder_id}' in parents"

		response = self.drive_service.files().list(
			q = query,
			spaces = 'drive',
			fields = 'files(id,name)'
		).execute()

		for file in response.get('files',[]):
			if file['name'].lower() == folder_name.lower():
				return file['id']
		# 创建文件夹
		# folder_id = self.create_folder(folder_name,parent_folder_id)
		# # 在这个文件夹下创建年份文件夹
		# year_id = self.create_folder(year,folder_id)
		return None
	
	
	
	def create_folder(self,folder_name,parent_folder_id,shared = False):
		'''创建新的文件夹'''
		file_metadata = {
			'name':folder_name,
			'mimeType': 'application/vnd.google-apps.folder',
		}

		if parent_folder_id:
			file_metadata['parents'] = [parent_folder_id]

		if shared:   #共享
			folder = self.share_drive_service.files().create(
				body = file_metadata,
				supportsAllDrives =True,
				fields= 'id,name'
			).execute()
		if not shared:    # 不共享
			folder = self.drive_service.files().create(
				body = file_metadata,
				supportsAllDrives =True,
				fields= 'id,name'
			).execute()
		return folder['id']

	def add_google_sheet(self,data,filename):
		
		header = ['Date','Apartment','Description','Category','Amount','Notes']
		# 将json转换成字典
		# 20250512
		#save_path = ''
		#filename = os.path.basename(save_path)
		#data = json.loads(data)
		
		street = data['Apartment']['Street']
		number = data['Apartment']['Number']
		floor_location = ''.join([data['Apartment']['Floor'],data['Apartment']['Location']])

		apartment = ' '.join([street,number,floor_location])

		date = data['Date']
		description = data['Description']
		category = data['Category']
		amount = data['Amount']
		deadline = data['Deadline']
		billing_contact = data['Billing contact']
		note = f'Deduct on {deadline}-{billing_contact}'
		# 将信息加入到
		body = {
			'values':[[date,apartment,description,category,amount,note]]
		}
		# 查询data['Date'][:4]文件夹是否存在
		year = data['Date'][:4]
		folder_id = self.find_folder_by_name_case_insensitive(self,year,self.driveID)
		if not folder_id:   # 没有就创建
			folder_id = self.create_folder(year,self.driveID)
		# 表格是否存在
		spreadsheetID= self.find_spreadsheet_by_name(folder_id,filename)
		if not spreadsheetID:
			spreadsheetID = self.create_spreadsheet(filename)
			body_header = {
				'values':[header]
			}
			# 获取工作表
			spreadsheet  =self.sheets_service.spreadsheets().get(spreadsheetId = spreadsheetID).execute()
			sheet_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]

			self.sheets_service.spreadsheets().values().append(
				spreadsheetId = spreadsheetID,
				range = f"'{sheet_names[0]}'!A1",      #并非强制写入A2,从A2开始找空白行
				valueInputOption = 'USER_ENTERED',
				insertDataOption = 'INSERT_ROWS',
				body = body_header
			).execute()
		# 创建成功后就在文件夹中写入header	

		spreadsheet  =self.sheets_service.spreadsheets().get(spreadsheetId = spreadsheetID).execute()
		sheet_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]

		self.sheets_service.spreadsheets().values().append(
				spreadsheetId = spreadsheetID,
				range = f"{sheet_names[0]}!A2",      #并非强制写入A2,从A2开始找空白行
				valueInputOption = 'USER_ENTERED',
				body = body
			).execute()
		return f'Successful write google sheets'

	def find_spreadsheet_by_name(self,folder_id,file_name:str):
		'''检查是否存在表格并创建'''
		# 查询文件是否存在
		query = f"""
			'{folder_id}' in parents
			and name = '{file_name}'
			and mimeType = 'application/vnd.google-apps.spreadsheet'
			and trashed = false
"""
		results = self.drive_service.files().list(q=query,spaces = 'drive',fields = "files(id,name)").execute()
		files = results.get('files',[])
		if files:
			#匹配上了
			return files[0]['id']
		return None
	

	# 创建spreadsheet  
	def create_spreadsheet(self,sheet_name:str):
		file_metadata = {
				'name':sheet_name,
				'mimeType':'application/vnd.google-apps.spreadsheet',
				'parents':[self.savesheet_folder_ID]
		}

		sheet = self.drive_service.files().create(
			body = file_metadata,
			fields= 'id'
		).execute()
		print(f'成功创建{sheet_name},id = {sheet['id']}')
		return sheet['id']
	
	# 发送邮件 template表示选择的是第几个template
	def send_email(self,template,cus_data,send_file_content,subject):
		# 
		# 构建邮箱
		# to_email = cus_data['email']      
		# cc_email = cus_data['qd_email']
		cc_email  = ['lixin_2@163.com']   # 测试
		to_email = [self.from_email]   # 测试

		message = EmailMessage()
		
		message['To'] = ','.join(to_email)
		message['Cc'] = ','.join(cc_email)
		message['From'] = self.from_email     # 更改email
		message['Subject'] = subject #'Tax Service'     
		content = self.email_content(template,cus_data)
		# 正文内容  
		message.set_content(content)
		# 添加invoice附件 invoice 一定是pdf
		# with open(cus_data['filepath'],'rb') as f:     # 以二进制的方式读取
		# 	file_data = f.read()
		# message.add_attachment(file_data,maintype = 'application',subtype = 'pdf',filename = cus_data['filename'])    # 纯文本文件
		# 添加imi附件，imi可能是pdf，png，jpg
		for key,value in send_file_content.items():
			imi_file_bytes = value['file_bytes']
			maintype = value['maintype']
			subtype = value['subtype']
			filename = value['filename']
			message.add_attachment(imi_file_bytes,maintype = maintype,subtype = subtype,filename = filename)    
		
		# 编码并发送   invoice是二进制内容 imi是二进制内容么？
		try:
			encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
			send_message = {'raw':encoded_message}
			draft = None
			draft = self.gmail_service.users().messages().send(userId = 'me',body = send_message).execute()   # 发送文件

		except HttpError as error:
			draft = None
		return draft
	
	

	'''update sheets cell'''
	def update_values(self,data,range_name):
		try:
			result = ''
			values = [
				[data]
			]
			#print(f'range_name的值是{range_name}')
			body = {'values':values}
			result = self.sheets_service.spreadsheets().values().update(
				spreadsheetId = self.sheet_id,
				valueInputOption = 'RAW',
				range = range_name,
				body = body
			).execute()
			return result
		
		except HttpError as error:
			return error


	'''shared drive'''
	def list_all_folders(self,parent_id,drive_name):
		'''
		列出所有文件夹id
		'''
		folders = []
		page_token = None
		print(parent_id)
		drive = self.list_shared_drives(drive_name)
		print(drive)
		while True:
			response = self.share_drive_service.files().list(
				q = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder'",
				spaces = 'drive',
				corpora = 'drive',
				driveId = drive['id'],
				fields = 'nextPageToken,files(id,name)',
				supportsAllDrives =True,  # 是否可以访问共享云盘
				includeItemsFromAllDrives  = True,
				pageToken = page_token
			).execute()
			for file in response.get('files',[]):
				folders.append(file)

			page_token = response.get('nextPageToken',None)
			if page_token is None:
				break
		# print(folders)
		return folders
	
	def list_shared_drives(self,drive_name):
		'''列出所有共享云盘的id'''
		results = self.share_drive_service.drives().list().execute()
		drives = results.get('drives',[])
		for drive in drives:
			if drive.get('name') == drive_name:
				return drive


	def list_files_in_folder(self,folder_id,drive_name):
		'''共享文件夹 ：列出所有文件夹中的文件'''
		query = f"'{folder_id}' in parents and trashed=false"
		files = []
		page_token = None
		drive = self.list_shared_drives(drive_name)
		while True:
			response = self.share_drive_service.files().list(
				q = query,
				spaces = 'drive',
				fields = 'nextPageToken, files(id,name,mimeType)',
				pageToken = page_token,
				driveId = drive['id'],
				corpora = 'drive',
				supportsAllDrives =True,  # 是否可以访问共享云盘
				includeItemsFromAllDrives  = True
			).execute()
			files.extend(response.get('files',[]))
			page_token = response.get('nextPageToken',None)
			if page_token is None:
				break
		return files
	
	def download_folder(self,folder_id,local_path,**kwargs):
		if not os.path.exists(local_path):
			os.makedirs(local_path)
		if 'drive_name' in kwargs:
			drive_name = kwargs.get('drive_name')
			files = self.list_files_in_folder(folder_id,drive_name)
			print(files)
			for file in files:
				if file['mimeType'] == 'application/vnd.google-apps.folder':
					# 递归下载子文件夹
					new_local_path = os.path.join(local_path,file['name'])
					self.download_folder(file['id'],new_local_path)
				else:
					#file_path = os.path.join(local_path,file['name'])
					content = self.download_file_from_drive(file['id'])
					self.save_file_to_local(local_path,file['name'],file_bytes = content)
		
	
	def save_file_to_local(self,save_dir,filename,**kwargs):
    # 确保路径存在
		os.makedirs(save_dir,exist_ok=True)   # 如果当前没有这个路径，就创建它
		save_path = os.path.join(save_dir,f'{filename}')
		
		if 'file_bytes' in kwargs:
			file_bytes = kwargs.get('file_bytes')
			try:
				with open(save_path,'wb') as f:
					f.write(file_bytes)
				result = f'{save_path}'
			except Exception as e:
				print(e)
				result = None
			#print(f"文件已经保存到{save_path}")
			return result


	## shared drive 递归查找函数
	def search_file_in_folder(self,folder_id,filename,drive_name,path):
		files = self.list_files_in_folder(folder_id,drive_name)
		found = False
		for file in files:
			# current_path = f"{path}/{file['name']}"
			if file['mimeType'] == 'application/vnd.google-apps.folder':
				# 如果是文件夹就扫描
				sub_path = os.path.join(path)
				result =self.search_file_in_folder(file['id'],filename,drive_name,sub_path)
				if result:
					return result
			elif filename.lower() in file['name'].lower():
				# 找到了就保存文件
				content = self.download_file_from_drive(file['id'])
				result = self.save_file_to_local(path,file['name'],file_bytes = content)
				found = True
		return found 
	


		