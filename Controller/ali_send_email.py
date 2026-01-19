#from log.logging_config import *
from requests_toolbelt import MultipartEncoder
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr,make_msgid
import smtplib
import email
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from jinja2 import Environment,FileSystemLoader



# send_file_content包含  'file_bytes'，['maintype'] ['subtype'] ['filename']
def ali_send_email(email_content:dict,email_subject,files:dict,emailinfo:dict):
    '''
    功能: 发送email
    email_content：Dict   发送email正文相关template
    files：send_file_content   包含  'file_bytes'，['maintype'] ['subtype'] ['filename']
    emailinfo:Dict, 包含to_email:list,bcc_email:list,cc_email:list
    emailinfo = {
    'to_email':[],
    'bcc_email':[],
    'cc_email':[]
    }
    
    '''


    '''smtp认证使用的邮箱账号密码'''
    mail_host = 'smtp.hk.aliyun.com'
    username = 'invoice@oechk.com'     # 更改
    password = 'Fgi_123456'                   # 更改


    '''定义发送邮件的地址'''
    From = 'invoice@oechk.com'   #'no-reply@fgi-capital.cn'         # 更改
    
    
    # 生产环境
    to_email = emailinfo.get('to_email',[])         
    bcc_email = emailinfo.get('bcc_email',[])
    cc_email = emailinfo.get('cc_emial',['fgi.cs@fgi-holdings.com'])
    
    # 测试环境
    # to_email = ['lixin_2@163.com']   #  测试
    # cc_email = []   # 抄送
    # bcc_email  = []   # 密送 测试
    
 
    if bcc_email == ['']:
         bcc_email = []

    '''定义收件对象'''
    to = ','.join(to_email)   
    print(f'to-{to}')
    cc = ','.join(cc_email)  #抄送    # 更改
    bcc = ','.join(bcc_email)  #密送
    print(f'to-{to}')
    receivers = to_email +cc_email + bcc_email
  
    

    
    msg = EmailMessage()
    msg['From'] = From
    msg['To'] = to
    msg['Cc'] = cc
    msg['Bcc'] = bcc
    msg['Message-id'] = email.utils.make_msgid()
    msg['Date'] = email.utils.formatdate()   
                      # 主题

     # 附件部分添加Logo图片
    logo_cid = make_msgid(domain = 'orui.com')[1:-1]
    
    BATH_PATH= Path(__file__).resolve().parent.parent
    LOGO_PATH = Path.joinpath(BATH_PATH,'Static','img','orui_logo.png')
    with open(LOGO_PATH,'rb') as f:
         msg.get_payload()
         msg.add_related(
              f.read(),
              maintype = 'image',
              subtype = 'png',
              cid = logo_cid,
              filename = 'orui_logo.png'
         )
    # 可以将content 定义成HTML generate_html_email_content(template, cus_data)
    # content,email_subject = generate_html_email_content(template=template,cus_data=cus_data)
    
    
    content = email_content.replace("cid:LOGO_CID",f"cid:{logo_cid}")

    msg['Subject'] = email_subject
    # textplain = MIMEText(content, _subtype='plain', _charset='UTF-8')
    # textplain = MIMEText(content, _subtype='html', _charset='UTF-8')
    # msg.attach(textplain)
    #msg.set_content(content,'html','utf-8')
    msg.add_alternative(content,subtype = 'html')
    
    # 封装附件
    for key,value in files.items():
        msg.add_attachment(
			value['file_bytes'],
			maintype = value['maintype'],
			subtype = value['subtype'],
			filename = value['filename']
        )


    '''开始链接验证服务'''
    try:
        client = smtplib.SMTP_SSL(mail_host, 465)
        print('smtp_ssl----连接服务器成功，现在开始检查账号密码')
    except Exception as e1:
        client = smtplib.SMTP(mail_host, 25, timeout=5) 
        print('smtp----连接服务器成功，现在开始检查账号密码')
    except Exception as e2:
        return '抱歉，连接服务超时'
        # exit(1)
		
    try:
        client.login(username, password)
        print('账密验证成功')
    except:
        return '抱歉，账密验证失败'
        # exit(1)

    '''~~~发送邮件并结束任务~~~'''
    try:
        client.sendmail(username, receivers, msg.as_string())
        client.quit()
        print('邮件发送成功')
        return 'Success'
    except smtplib.SMTPConnectError as e:
        return f'邮件发送失败，连接失败:,{e.smtp_code}, {e.smtp_error}'
    except smtplib.SMTPAuthenticationError as e:
        return f'邮件发送失败，认证错误:,{e.smtp_code}, {e.smtp_error}'
    except smtplib.SMTPSenderRefused as e:
        return f'邮件发送失败，发件人被拒绝:, {e.smtp_code}, {e.smtp_error}'
    except smtplib.SMTPRecipientsRefused as e:
        for recipient, (code, message) in e.recipients.items():
            print(f'收件人: {recipient}, 错误码: {code}, 原因: {message.decode() if isinstance(message, bytes) else message}')
        return f'邮件发送失败，收件人被拒绝:, '
    except smtplib.SMTPDataError as e:
        return f'邮件发送失败，数据接收拒绝:, {e.smtp_code}, {e.smtp_error}'
    except smtplib.SMTPException as e:
        return f'邮件发送失败,  {str(e)}'
    except Exception as e:
        return f'邮件发送异常, , {str(e)}'


# 弃用
def ali_email_content(template,cus_data):
		cus_name = cus_data['cus_name']
		email_date = datetime.now().strftime('%Y年%m月%d日')
		email_date_eng = datetime.now().strftime('%d-%m-%Y')
		company_name = 'FGI GROUP HOLDINGS 未來集團控股'
		trf_part = ''
		imi_part = ''
		irs_part = ''
		qbe_part = ''
		condo_part = ''

		if cus_data['is_tax_rep'] and template =='template1':
			trf_part = '''税务代表费（Tax Representative Fee）
   根据葡萄牙法律，黄金签证持有者需指定税务代表以履行税务义务。税务代表将协助处理相关申报事务，确保您的税务合规，避免因违规或延误影响签证续签。
-  Tax Representative Fee
   Under Portuguese law, Golden Visa holders must appoint a tax representative to fulfill their tax obligations. The representative assists in tax filings and ensures your compliance, avoiding penalties or risks that may affect your residence renewal.
'''
			
		if cus_data['is_imi'] and template =='template1':
			imi_part = '''IMI房产持有税（适用于房产持有投资人）
   IMI 是房产持有者每年必须缴纳的市政税，按房产所在地区征收。如未按期缴纳，可能导致罚金、信用受损，甚至影响居留资格。
-  IMI Property Tax (Applicable to property holders)
   IMI is an annual municipal property tax levied on real estate holders in Portugal. Delayed payment may result in penalties, damage to your credit record, and impact your residence status.
'''
			
		if cus_data['is_irs'] and template =='template1':
			irs_part = '''个人收入税（IRS）（如适用，通常在7-8月收到官方通知）
   如您在葡萄牙有收入来源（如租金或工资），需依法申报和缴纳IRS。按时申报是维护良好税务记录的必要条件。
-  Personal Income Tax (IRS) (If applicable – usually notified in July/August)
   If you have any income in Portugal, such as rental or employment income, it is mandatory to declare and pay IRS in accordance with Portuguese tax law. Timely compliance helps maintain a clean tax record and avoid legal risks.
'''
			
		if cus_data['is_qbe'] and template =='template1':
			qbe_part = '''物业保险费（QBE团购保险）（适用于房产持有投资人）
   为保障您的房产，公司组织团购QBE保险，覆盖火灾、地震等主要风险。请务必确保保险持续有效，避免在发生意外时处于无保障状态。
-  Property Insurance Premium (QBE Group Insurance) (Applicable to property holders)
   To safeguard your real estate, our company offers a group insurance plan through QBE at competitive rates. This policy covers key risks such as fire, earthquake, and natural disasters. Please ensure continuous coverage to protect your property and avoid 	uncovered losses.
'''
			
		if cus_data['is_condo'] and template =='template1':
			condo_part = '''物业管理费（Condo Fee）（适用于房产持有投资人）
   用于房产所在小区的公共维护与管理，属于业主的共同责任。请根据物业公司通知及时缴纳，以免产生不必要的法律或邻里纠纷。
-  Condominium Fee (Condo Fee) (Applicable to property holders)
   This fee is used to maintain and manage common areas of your property community. Timely payment is a shared responsibility and helps avoid legal disputes or disruption of services.
'''		
			
		fee_part = [i for i in [trf_part,imi_part,irs_part,qbe_part,condo_part] if i!='']
		# fee_part_eng = [i for i in [trf_part_eng,imi_part_eng,irs_part_eng,qbe_part_eng,condo_part_eng] if i!='']
		i = 0
		fee_parts = []
		# fee_parts_eng = []
		for i in range(len(fee_part)):
			fee_parts.append(str(i+1)+'. '+fee_part[i])
			# fee_parts.append(str(i+1)+'. '+fee_part_eng[i])
			i = i+1
		

		
		fee_content = '\n'.join(fee_parts)
        #fee_content = '<br><br>'.join(f'<pre>{p}</pre>' for p in fee_parts)
		
		email_content = f'''
尊敬的{cus_name}:
Dear {cus_name}:

您好！
Greetings!

感谢您选择{company_name}作为您葡萄牙黄金签证申请及后续服务的合作伙伴。
Thank you for choosing {company_name} as your trusted partner in your Portugal Golden Visa application and ongoing support services.

为确保您的签证申请及后续续签流程顺利进行，并保障您在葡萄牙的合法权益，我们郑重提醒您务必关注并按时缴纳以下费用。这些费用直接关系到您的签证有效性和在葡萄牙的投资稳定性，请务必重视：
To ensure the smooth progress of your application and the continued validity of your residence status in Portugal, we hereby issue this formal reminder regarding the timely payment of the following mandatory fees. Failure to fulfill these obligations may jeopardize your visa status and related rights. Please read carefully:

{fee_content}

* 温馨提醒：
- 请于收到本支付单之日起15个自然日内完成全额支付，及时支付至关重要。
- 所有上述费用均为强制性义务，请务必按照截止时间履行，以确保您的黄金签证及相关权益不受影响。
- 我们将继续通过系统为您发送缴费提醒，但请您主动关注相关费用通知，避免因延误带来不必要的风险。
- 如有任何疑问或需要进一步协助，欢迎随时联系我司客户支持团队。
* Important Reminders:
- Please complete full payment within ​​15 natural days​​ from the date of receiving this payment notice. Timely payment is critical.
- All fees mentioned above are mandatory and time-sensitive. Please fulfill them on or before the respective deadlines to ensure the validity of your Golden Visa and protect your rights in Portugal.
- While our system will continue to send you payment reminders, we strongly recommend that you proactively monitor all notices and plan accordingly.
- If you have any questions or require assistance, please do not hesitate to contact our customer service team.

感谢您的理解与配合，祝您在葡萄牙的生活与投资一切顺利！
Thank you for your attention and cooperation. We wish you continued success in your life and investments in Portugal.

此致
敬礼！

Sincerely,

{company_name}
{company_name}

{email_date}
{email_date_eng}
'''
		print(email_content)
		return email_content



def generate_html_email_content(template, cus_data):
    print(cus_data,'----')
    print(cus_data['cus_name'])
    cus_name = cus_data['cus_name']
    email_date = datetime.now().strftime('%Y年%m月%d日')
    email_date_eng = datetime.now().strftime('%d-%m-%Y')
    if template == 'Receipt_Remind':
         invoice_no = cus_data['receipt_invoice_number']
    else:
         invoice_no = ''
    # company_name = 'FGI GROUP HOLDINGS 未來集團控股'
    trf_part = ''
    imi_part = ''
    irs_part = ''
    qbe_part = ''
    condo_part = ''
    form_part = ''
    data = {
         'is_tax_rep': cus_data.get('is_tax_rep'),
         'is_imi':cus_data.get('is_imi'),
         'is_condo': cus_data.get('is_condo'),
         'is_irs':cus_data.get('is_irs'),
         'is_qbe': cus_data.get('is_qbe'),
         'is_form': cus_data.get('is_form'),
         'form_link': cus_data.get('form_link'),
         
         'is_not_lisbon_lawyer': cus_data.get('is_not_lisbon_lawyer'),
         'is_tax_rep_change':cus_data.get('is_tax_rep_change'),
         'cus_name': cus_name
    }

    # data = {
    #      'is_tax_rep': True,
    #      'is_imi':True,
    #      'is_condo': False,
    #      'is_irs':False,
    #      'is_qbe': False,
    #      'is_form': False,
    #      'form_link': "http://www.oechk.com",
         
    #      'is_not_lisbon_lawyer': False,
    #      'is_tax_rep_change':True,
    #      'cus_name': "需签署协议"
    # }
    return  get_email_html_content(template,data)    # return html_content,subject
    

#     if cus_data.get('is_tax_rep') and template == 'Invoice_Form_202601':
#          trf_part = ''' 
# <span style="font-weight:700;white-space:pre-wrap">税务代表与合规维护费（Tax Representation &amp; Compliance Fee）</span><span style="white-space:pre-wrap"> 根据葡萄牙法律，非欧盟税务居民必须指定税务代表。这不仅是履行法律义务，更是专业团队的全年服务： Under Portuguese law, non-EU tax residents must appoint a tax representative. This requirement is not only a legal obligation but also secures a full year of service from our professional team:</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="text-align:left;padding:0px 20px;font-size:0"><table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-family:Arial, Helvetica, sans-serif"><tbody><tr><td style="width:24px;vertical-align:top;padding-right:8px;text-align:right;white-space:nowrap"><span style="font-size:14.6667px;color:#333333;display:inline-block">•</span></td><td style="font-size:14.6667px;color:#333333;vertical-align:top"><span style="font-weight:700;white-space:pre-wrap">责任与护盾 (Legal Liability &amp; Shield):</span><span style="white-space:pre-wrap"> 为您维持合规的“非税务居民”身份，并实时监控税务局信件及处理官方信函以保持税务身份良好状态</span><span style="white-space:pre-wrap"><br></span></td></tr></tbody></table></td></tr><tr><td dir="ltr" style="text-align:left;padding:0px 20px;font-size:0"><table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-family:Arial, Helvetica, sans-serif"><tbody><tr><td style="width:24px;vertical-align:top;padding-right:8px;text-align:right;white-space:nowrap"><span style="font-size:14.6667px;color:#333333;display:inline-block">•</span></td><td style="font-size:14.6667px;color:#333333;vertical-align:top"><span style="font-weight:700;white-space:pre-wrap">Legal Liability &amp; Shield:</span><span style="white-space:pre-wrap"> We maintain your compliant "Non-Resident" status, monitor the mandatory electronic tax mailbox in real-time, and handle official correspondence to ensure your standing with the Tax Authority remains in good order.</span><span style="white-space:pre-wrap"><br></span></td></tr></tbody></table></td></tr><tr><td dir="ltr" style="text-align:left;padding:0px 20px;font-size:0"><table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-family:Arial, Helvetica, sans-serif"><tbody><tr><td style="width:24px;vertical-align:top;padding-right:8px;text-align:right;white-space:nowrap"><span style="font-size:14.6667px;color:#333333;display:inline-block">•</span></td><td style="font-size:14.6667px;color:#333333;vertical-align:top"><span style="font-weight:700;white-space:pre-wrap">年度税务申报与维护 (Annual Filing &amp; Maintenance):</span><span style="white-space:pre-wrap"> 无论是房产收益申报还是基金投资等税务合规性，财务团队将负责处理年度IRS等基礎层面的合规事宜，确保符合葡国税法要求。 </span><span style="font-weight:700;white-space:pre-wrap">Annual Filing &amp; Maintenance:</span><span style="white-space:pre-wrap"> Whether for property income reporting or </span><span style="font-weight:700;white-space:pre-wrap">fund investment tax compliance</span><span style="white-space:pre-wrap">, our finance team manages the necessary IRS (Personal Income Tax) compliance to ensure your asset returns adhere to Portuguese tax law requirements.</span><span style="white-space:pre-wrap"><br></span></td></tr></tbody></table></td></tr><tr><td dir="ltr" style="text-align:left;padding:0px 20px;font-size:0"><table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-family:Arial, Helvetica, sans-serif"><tbody><tr><td style="width:24px;vertical-align:top;padding-right:8px;text-align:right;white-space:nowrap"><span style="font-size:14.6667px;color:#333333;display:inline-block">•</span></td><td style="font-size:14.6667px;color:#333333;vertical-align:top"><span style="font-weight:700;white-space:pre-wrap">录指纹的关键：无欠税声明 (The Key to Biometrics):</span><span style="white-space:pre-wrap"> </span><span style="font-weight:700;white-space:pre-wrap">这是最重要的一点</span><span style="white-space:pre-wrap">。 只有在税务代表服务生效且费用结清时，我方才能进入系统为您开具AIMA录指纹必须文件之**“无欠税声明”（Declaração de Não Dívida）**。无此文件，您将无法完成黄金居留申请。 </span><span style="font-weight:700;white-space:pre-wrap">The Key to Biometrics:</span><span style="white-space:pre-wrap"> This is the most critical point. Only when the tax representation service is active and paid can we access the system to issue the </span><span style="font-weight:700;white-space:pre-wrap">"Non-Debt Declaration" (Declaração de Não Dívida)</span><span style="white-space:pre-wrap"> required by AIMA for your biometrics. Without this document, you cannot complete your fingerprint collection 安定GV application.</span><span style="white-space:pre-wrap"><br></span></td></tr></tbody></table></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px">
                 
# '''
#     elif cus_data.get('is_tax_rep'):
#         trf_part = '''税务代表费（Tax Representative Fee）
# 根据葡萄牙法律，黄金签证申请者需指定税务代表以履行税务义务。税务代表将协助处理相关申报事务，确保您的税务合规，避免因违规或延误影响签证续签。
# -  Tax Representative Fee
# Under Portuguese law, Golden Visa applicants must appoint a tax representative to fulfill their tax obligations. The representative assists in tax filings and ensures your compliance, avoiding penalties or risks that may affect your residence renewal.
# '''

    

        
    
#     if cus_data['is_imi']:
#         imi_part = '''IMI房产持有税（适用于房产持有投资人）
# IMI 是房产持有者每年必须缴纳的市政税，按房产所在地区征收。如未按期缴纳，可能导致罚金、信用受损，甚至影响居留资格。
# - IMI Property Tax (Applicable to property holders)
# IMI is an annual municipal property tax levied on real estate holders in Portugal. Delayed payment may result in penalties, damage to your credit record, and impact your residence status.

# <strong>⏰ 温馨提醒：IMI政府截止日是今年2025年6月30日，请在此日期前支付</strong>
# '''
# imi
#     if cus_data.get('is_imi') and template == 'Invoice_Form_202601':
#          imi_part = '''<span style="font-weight:700;white-space:pre-wrap">IMI房产持有税（适用于房产持有投资人）</span><span style="white-space:pre-wrap">IMI 是房产持有者每年必须缴纳的市政税，按房产所在地区征收。如未按期缴纳，可能导致罚金、信用受损，甚至影响居留资格。  IMI Property Tax is an annual municipal property tax levied on real estate holders in Portugal. Delayed payment may result in penalties, damage to your credit record, and impact your residence status.</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px">
                 
# '''
#     elif cus_data.get('is_imi') and template == 'Invoice_Remind_202510':
#         imi_part = '''2024年度IMI（房产税）
# 1. 第一分期款项：此前因未按期缴付，葡萄牙税局政府部门已生成相应罚息。为避免产生额外滞纳金，烦请您于2025年10月31日前完成该笔款项（含罚息）的缴付。
# -  First installment: Previously, due to non-payment on time, the Portuguese Tax Authority has generated corresponding interest penalties. To avoid additional late fees, please complete this payment (including interest) by October 31, 2025.

# 2. 第二分期款项：缴费通知已正式发出，您可于2025年11月30日前完成缴付，建议您提前规划以保障流程顺畅。
# -  Second installment: The payment notice has been officially issued, and you may complete the payment by November 30, 2025. We recommend planning in advance to ensure a smooth process.    
# '''
#     elif cus_data.get('is_imi'):
#         imi_part = '''IMI房产持有税（适用于房产持有投资人）
# 特此提醒，根据葡萄牙税务记录其2025年度IMI（Municipal Property Tax）税款未能于法定最终缴纳期限（2025年6月30日）前完成支付。根据葡萄牙税法规定，逾期未缴税款将自动进入宽限期（Grace Period），本次补缴截止日期为 2025年7月31日。若未能在该日期前完成付款，税务局将按日加收滞纳金以及啓动可能相关的法律程序，建议尽快支付。IMI 是房产持有者每年必须缴纳的市政税，按房产所在地区征收。如未按期缴纳，可能导致罚金、信用受损，甚至影响居留资格。
# - IMI Property Tax (Applicable to property holders)
# This is to remind you that, according to the Portuguese tax records, the 2025 IMI (Municipal Property Tax) for your property was not paid by the statutory final deadline of June 30, 2025. In accordance with Portuguese tax law, unpaid taxes automatically enter a grace period, with the new payment deadline set for July 31, 2025. Failure to pay by this date will result in daily interest charges and may trigger relevant legal procedures. We recommend settling the payment as soon as possible. IMI Property Tax is an annual municipal property tax levied on real estate holders in Portugal. Delayed payment may result in penalties, damage to your credit record, and impact your residence status.
     
# <strong>⏰ 温馨提醒：此次提醒之2025年 IMI 缴费稅局截止日为 7月31日，请务必在此之前完成缴纳。
# Reminder: The 2025 IMI tax deadline is July 31 – please ensure payment before this date.</strong>
# '''


#     if cus_data.get('is_irs') and template == 'Invoice_Form_202601':
#          irs_part = '''<span style="font-weight:700;white-space:pre-wrap">个人收入税（IRS）（如适用，通常在9月左右收到官方通知）</span><span style="white-space:pre-wrap"> 如您在葡萄牙有收入来源（如租金或工资），需依法申报和缴纳IRS。按时申报是维护良好税务记录的必要条件。 </span><span style="font-weight:700;white-space:pre-wrap">Personal Income Tax (IRS) (If applicable – usually notified in July/August)</span><span style="white-space:pre-wrap"> If you have any income in Portugal, such as rental or employment income, it is mandatory to declare and pay IRS in accordance with Portuguese tax law. Timely compliance helps maintain a clean tax record and avoid legal risks.</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px">
                 
# '''
    
#     elif cus_data.get('is_irs') and template == 'Invoice_Remind_202510' :
#         irs_part = '''2024年度IRS（个人所得税）
# 根据规定，该笔税款应于2025年8月缴清，目前因逾期已产生罚息。税务部门已为您出具含分期付款计划的账单，首期分期款需在2025年10月31日前缴付，后续分期可按账单提示逐步完成。
# According to regulations, this tax should have been paid by August 2025. Currently, due to overdue payment, interest penalties have accrued. The tax authority has issued a bill including an installment plan for you. The first installment must be paid by October 31, 2025, and subsequent installments can be completed step by step according to the bill instructions.
# '''
#     elif cus_data.get('is_irs') :
#         irs_part = '''个人收入税（IRS）（如适用，通常在7-8月收到官方通知）
# 如您在葡萄牙有收入来源（如租金或工资），需依法申报和缴纳IRS。按时申报是维护良好税务记录的必要条件。
# -  Personal Income Tax (IRS) (If applicable – usually notified in July/August)
# If you have any income in Portugal, such as rental or employment income, it is mandatory to declare and pay IRS in accordance with Portuguese tax law. Timely compliance helps maintain a clean tax record and avoid legal risks.

# <strong>⏰ 温馨提醒：为确认无误，IRS 单据上的付款码仅适用于第一期分期付款金额。如您在 10 月 30 日前完成该笔付款，预计需至 11 月才有机会申请新的付款码，以支付剩余的 IRS 款项。
# Reminder: For clarification, the payment code on the IRS document is only valid for the first installment. Once the payment is made before October 30, a new payment code for the remaining IRS balance can likely be requested in November.</strong>
# '''
        

#     if cus_data.get('is_qbe') and template == 'Invoice_Form_202601':
#          qbe_part = '''<span style="font-weight:700;white-space:pre-wrap">物业保险费（QBE团购保险）（适用于房产持有投资人）</span><span style="white-space:pre-wrap"> 为保障您的房产，公司组织团购QBE保险，覆盖火灾、地震等主要风险。请务必确保保险持续有效，避免在发生意外时处于无保障状态。 </span><span style="font-weight:700;white-space:pre-wrap">Property Insurance Premium (QBE Group Insurance) (Applicable to property holders)</span><span style="white-space:pre-wrap"> To safeguard your real estate, our company offers a group insurance plan through QBE at competitive rates. This policy covers key risks such as fire, earthquake, and natural disasters. Please ensure continuous coverage to protect your property and avoid uncovered losses.</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px">
                 
# '''
#     elif cus_data.get('is_qbe') :
#         qbe_part = '''物业保险费（QBE团购保险）（适用于房产持有投资人）
# 为保障您的房产，公司组织团购QBE保险，覆盖火灾、地震等主要风险。请务必确保保险持续有效，避免在发生意外时处于无保障状态。
# -  Property Insurance Premium (QBE Group Insurance) (Applicable to property holders)
# To safeguard your real estate, our company offers a group insurance plan through QBE at competitive rates. This policy covers key risks such as fire, earthquake, and natural disasters. Please ensure continuous coverage to protect your property and avoid 	uncovered losses.
# '''
    
#     if cus_data.get('is_condo') and template == 'Invoice_Form_202601':
#          condo_part = '''<span style="font-weight:700;white-space:pre-wrap">物业管理费（Condo Fee）（适用于房产持有投资人）</span><span style="white-space:pre-wrap"> 用于房产所在楼宇的公共维护与管理，属于业主的共同责任。请根据物业公司通知及时缴纳，以免产生不必要的法律或邻里纠纷。 </span><span style="font-weight:700;white-space:pre-wrap">Condominium Fee (Condo Fee) (Applicable to property holders)</span><span style="white-space:pre-wrap"> This fee is used to maintain and manage common areas of your property community. Timely payment is a shared responsibility and helps avoid legal disputes or disruption of services.</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px"><span style="white-space:pre-wrap">⚠️</span><span style="font-weight:700;white-space:pre-wrap"> 温馨提醒与行动指南 | Important Reminders &amp; Action Plan</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="text-align:left;padding:0px 20px;font-size:0"><table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-family:Arial, Helvetica, sans-serif"><tbody><tr><td style="width:24px;vertical-align:top;padding-right:8px;text-align:right;white-space:nowrap"><span style="font-size:14.6667px;color:#333333;display:inline-block">•</span></td><td style="font-size:14.6667px;color:#333333;vertical-align:top"><span style="white-space:pre-wrap">ℹ️</span><span style="font-weight:700;white-space:pre-wrap"> 关于税费周期的特别说明 (Tax Cycle Clarification):</span><span style="white-space:pre-wrap"> 葡萄牙常规税费（如 IMI 地税、IRS 个税）通常分别在 至 </span><span style="font-weight:700;white-space:pre-wrap">5-7月</span><span style="white-space:pre-wrap"> 通知。 </span><span style="font-weight:700;white-space:pre-wrap">本次通知的核心是“税务代表费”及往期未结清项。</span><span style="white-space:pre-wrap"> 这是为了优先确保能为您开具 AIMA 录指纹或续卡必须的**“无欠税声明”**。当后续 IMI 等税单生成时，系统会另行通知，请您留意。 ℹ️</span><span style="font-weight:700;white-space:pre-wrap"> Special Note on Payment Cycles:</span><span style="white-space:pre-wrap"> Standard Portuguese taxes (e.g., IMI, IRS) are typically notified in </span><span style="font-weight:700;white-space:pre-wrap">May - July</span><span style="white-space:pre-wrap">, respectively. </span><span style="font-weight:700;white-space:pre-wrap">This notice specifically targets the "Tax Representation Fee" and outstanding balances.</span><span style="white-space:pre-wrap"> This is to prioritize the issuance of the </span><span style="font-weight:700;white-space:pre-wrap">"Non-Debt Declaration"</span><span style="white-space:pre-wrap"> required for your AIMA biometrics or card renewal. Our system will send separate notifications for future IMI/tax bills when they become due.</span><span style="white-space:pre-wrap"><br></span></td></tr></tbody></table></td></tr><tr><td dir="ltr" style="text-align:left;padding:0px 20px;font-size:0"><table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-family:Arial, Helvetica, sans-serif"><tbody><tr><td style="width:24px;vertical-align:top;padding-right:8px;text-align:right;white-space:nowrap"><span style="font-size:14.6667px;color:#333333;display:inline-block">•</span></td><td style="font-size:14.6667px;color:#333333;vertical-align:top"><span style="font-weight:700;white-space:pre-wrap">付款时效：</span><span style="white-space:pre-wrap"> 请于收到本通知之日起 </span><span style="font-weight:700;white-space:pre-wrap">15 个自然日内</span><span style="white-space:pre-wrap"> 完成全额支付。 </span><span style="font-weight:700;white-space:pre-wrap">Payment Deadline:</span><span style="white-space:pre-wrap"> Full payment is required within </span><span style="font-weight:700;white-space:pre-wrap">15 calendar days</span><span style="white-space:pre-wrap"> from the date of this notice.</span><span style="white-space:pre-wrap"><br></span></td></tr></tbody></table></td></tr><tr><td dir="ltr" style="text-align:left;padding:0px 20px;font-size:0"><table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-family:Arial, Helvetica, sans-serif"><tbody><tr><td style="width:24px;vertical-align:top;padding-right:8px;text-align:right;white-space:nowrap"><span style="font-size:14.6667px;color:#333333;display:inline-block">•</span></td><td style="font-size:14.6667px;color:#333333;vertical-align:top"><span style="font-weight:700;white-space:pre-wrap">合规义务：</span><span style="white-space:pre-wrap"> 所有上述费用均为强制性合规义务，请务必按照截止时间履行，以确保您的黄金签证及相关权益不受影响。 </span><span style="font-weight:700;white-space:pre-wrap">Compliance:</span><span style="white-space:pre-wrap"> All fees mentioned above are mandatory and time-sensitive. Please fulfill them on or before the respective deadlines to ensure the validity of your Golden Visa and protect your rights in Portugal.</span><span style="white-space:pre-wrap"><br></span></td></tr></tbody></table></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td>
#                 </tr>                
# '''
#     if cus_data.get('is_condo'):
#         condo_part = '''物业管理费（Condo Fee）（适用于房产持有投资人）
# 用于房产所在小区的公共维护与管理，属于业主的共同责任。请根据物业公司通知及时缴纳，以免产生不必要的法律或邻里纠纷。
# -  Condominium Fee (Condo Fee) (Applicable to property holders)
# This fee is used to maintain and manage common areas of your property community. Timely payment is a shared responsibility and helps avoid legal disputes or disruption of services.
# '''		

#     if cus_data.get('is_form'):
#          form_part = f'''
# <span style="white-space:pre-wrap"> ✈️</span><span style="font-weight:700;white-space:pre-wrap"> [已获批指模录入客户专属] 赴葡行程登记与接待安排 </span><span style="white-space:pre-wrap">✈️</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px"><span style="white-space:pre-wrap">鉴于我司 2026 年度获批指模录入的客户已突破超 </span><span style="font-weight:700;white-space:pre-wrap">400+ 多组仍会继续增加</span><span style="white-space:pre-wrap">，为确保每一位客户的行程都能得到系统性、高效率的安排，</span><span style="font-weight:700;white-space:pre-wrap">若您已收到 AIMA 的指模录入通知并完成相关费用支付，请务必提前登记您的出行计划。</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;white-space:pre-wrap;text-align:left;padding:0px 20px">您的提前登记将协助我们为您无缝对接律师团队及后续接待事宜。<br></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px"><span style="white-space:pre-wrap">⚠️ </span><span style="font-weight:700;white-space:pre-wrap">至关重要的签证提醒：</span><span style="white-space:pre-wrap"> </span><span style="font-weight:700;white-space:pre-wrap">请务必确保您持有有效的入境签证（如申根签）。</span><span style="white-space:pre-wrap"> 由于签证预约及审批周期较长，我们强烈建议您 </span><span style="font-weight:700;white-space:pre-wrap">提前 3-5 个月</span><span style="white-space:pre-wrap"> 启动签证准备工作。唯有顺利获得签证，方能确保您按时入境葡萄牙完成指模录入。</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="font-size:14.6667px;text-align:left;padding:0px 20px"><span style="color:#333333;white-space:pre-wrap">👉 </span>
# <span style="font-weight:700;color:#333333;white-space:pre-wrap">点击此处填写</span><a href="{cus_data.get('form_link')}" target="_blank" rel="noopener nofollow" ses:no-track="" style="color:inherit;text-decoration:inherit"><span style="font-weight:700;text-decoration:underline;color:#1a62ff;white-space:pre-wrap">《FGI 葡萄牙行程确认表》</span></a><span style="color:#333333;white-space:pre-wrap">  </span><span style="font-style:italic;color:#333333;white-space:pre-wrap">(</span><span style="color:#333333;white-space:pre-wrap">请在出发前</span><span style="font-style:italic;color:#333333;white-space:pre-wrap"> 3 </span><span style="color:#333333;white-space:pre-wrap">个月，或最迟于出发前</span><span style="font-style:italic;color:#333333;white-space:pre-wrap"> 16 </span><span style="color:#333333;white-space:pre-wrap">天完成填写，以便我们为您统筹安排</span><span style="font-style:italic;color:#333333;white-space:pre-wrap">)</span><span style="color:#333333;white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px"><span style="font-weight:700;white-space:pre-wrap">English Translation:</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px"><span style="white-space:pre-wrap">✈️</span><span style="font-weight:700;white-space:pre-wrap"> [Exclusive for Biometric Appointment Clients] Portugal Trip &amp; Reception Arrangement </span><span style="white-space:pre-wrap">✈️</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px"><span style="white-space:pre-wrap">As we are successfully managing </span><span style="font-weight:700;white-space:pre-wrap">over 400+ client groups</span><span style="white-space:pre-wrap"> approved for biometric appointments in 2026, systematic coordination is essential. </span><span style="font-weight:700;white-space:pre-wrap">If you have received your AIMA biometric notification and settled the related fees, we kindly request that you register your travel plans in advance.</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;white-space:pre-wrap;text-align:left;padding:0px 20px">Your early registration allows us to efficiently coordinate with your legal team and arrange the necessary reception services for your visit.<br></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px"><span style="white-space:pre-wrap">⚠️ </span><span style="font-weight:700;white-space:pre-wrap">CRITICAL VISA REMINDER:</span><span style="white-space:pre-wrap"> </span><span style="font-weight:700;white-space:pre-wrap">Please ensure you have a valid visa (e.g., Schengen Visa) for entry.</span><span style="white-space:pre-wrap"> Due to high demand and processing times, we strongly recommend starting your visa application </span><span style="font-weight:700;white-space:pre-wrap">at least 3-5 months in advance</span><span style="white-space:pre-wrap">. A valid visa is a prerequisite for entering Portugal to complete your biometrics.</span><span style="white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="font-size:14.6667px;text-align:left;padding:0px 20px">
# <span style="color:#333333;white-space:pre-wrap">👉</span><a href="{cus_data.get('form_link')}" target="_blank" rel="noopener nofollow" ses:no-track="" style="color:inherit;text-decoration:inherit"><span style="text-decoration:underline;color:#1a62ff;white-space:pre-wrap"> </span><span style="text-decoration:underline;color:#1a62ff;white-space:pre-wrap">Click Here to Complete Your FGI Journey Form</span></a><span style="font-style:italic;color:#333333;white-space:pre-wrap"><br>(Please complete this form 3 months prior to departure, or at least 16 days in advance, to allow us to arrange your reception.)</span><span style="color:#333333;white-space:pre-wrap"><br></span></td></tr><tr><td style="font-size:0;height:16px" height="16">&nbsp;</td></tr><tr><td dir="ltr" style="color:#333333;font-size:14.6667px;text-align:left;padding:0px 20px">
                           
# '''
        
#     fee_part = [i for i in [trf_part,imi_part,irs_part,qbe_part,condo_part] if i!='']
#     # fee_part_eng = [i for i in [trf_part_eng,imi_part_eng,irs_part_eng,qbe_part_eng,condo_part_eng] if i!='']
#     i = 0
#     fee_parts = []
    
#     # fee_parts_eng = []
#     for i in range(len(fee_part)):
#         fee_parts.append(str(i+1)+'. '+fee_part[i])
#         # fee_parts.append(str(i+1)+'. '+fee_part_eng[i])
#         i = i+1

#     # fee_content = '<br><br>'.join(f'<pre>{p}</pre>' for p in fee_parts)
#     fee_content = ''.join(fee_parts)

    # return  get_email_html_content(template,cus_name,fee_content,email_date,email_date_eng,form_part, invoice_no)    # return html_content,subject
    

# def get_email_html_content(template,cus_name,fee_content,email_date,email_date_eng,cus_data = None, invoice_no = '',day:int=7):
def get_email_html_content(template,data, invoice_no = '',day:int=7):
    html_content = ''
    subject = ''

    BATH_PATH = Path(__file__).resolve().parent.parent
    env = Environment(loader = FileSystemLoader(Path.joinpath(BATH_PATH,"template")))
    if template == 'template1':
        subject  ='关于葡萄牙黄金签证相关费用缴纳提醒 Important Notice on Portugal Golden Visa-Related Fee Payments'
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', sans-serif; background:#f4f4f4; padding:20px; font-size:14px;}}
            .container {{ background:#fff; padding:30px; max-width:700px; margin:auto; border-radius:10px; box-shadow:0 4px 20px rgba(0,0,0,0.1); }}
            h2 {{ color:#1d3557; }}
            pre {{ background:#f9f9f9; padding:15px; border-left:4px solid #1d3557; border-radius:5px; white-space:pre-wrap; font-size:14px; }}
            .footer {{ margin-top:40px; font-size:12px; color:#666; border-top:1px solid #ddd; padding-top:20px; }}
            .footer_1 {{
      font-size: 0.70em;
      color: #888;
    }}
        </style>
        </head>
        <body>
        <div class="container">
            <h2>尊敬的 {cus_name}:</h2>
            <p>Dear {cus_name},</p>
            
            <p>您好!</p>
            <p>Greetings!</p>
            
            <p>感谢您选择我司作为您葡萄牙黄金签证申请及后续服务的合作伙伴。</p>
            <p>Thank you for selecting our firm as your trusted partner in managing your Portugal Golden Visa application and ongoing support services.</p>

            <p>为确保您的签证申请及后续续签流程顺利进行，并保障您在葡萄牙的合法权益，我司郑重提醒您务必关注并按时缴纳以下费用。这些费用直接关系到您的签证有效性和在葡萄牙的投资稳定性，请务必重视。详细账单信息请参见附件：</p>
            <p>To ensure the smooth processing of your visa application and subsequent renewals, and to safeguard your legal rights in Portugal, we hereby issue this formal reminder to review and settle the following fees in a timely manner. These payments are directly linked to the validity of your residence status and the stability of your investments in Portugal. Please refer to the attached document for the full invoice details:</p>

            
            {fee_content}

        
            <p><strong>⚠️ 温馨提醒 / Important Reminders:</strong></p>
            <ul>
            <li>请于收到本支付单之日起<strong>{day}个自然日内</strong>完成全额支付。</li>
            <li>Full payment is required within {day} calendar days from the date of this notice.</li>
            <li>所有上述费用均为强制性义务，请务必按照截止时间履行，以确保您的黄金签证及相关权益不受影响。</li>
            <li>All fees mentioned above are mandatory and time-sensitive. Please fulfill them on or before the respective deadlines to ensure the validity of your Golden Visa and protect your rights in Portugal.</li>
            <li>我们将继续通过系统为您发送缴费提醒，但请您主动关注相关费用通知，避免因延误带来不必要的风险。</li>
            <li>While our system will continue to send you payment reminders, we strongly recommend that you proactively monitor all notices and plan accordingly</li>
            <li>如有任何疑问或需要进一步协助，欢迎随时联系我司客户支持团队。</li>
            <li>If you have any questions or require assistance, please do not hesitate to contact our customer service team.</li>        
            </ul>

            <p >
            感谢您的理解与配合，祝您在葡萄牙的生活与投资一切顺利！
            </p>
            <p >
            Thank you for your attention and cooperation. We wish you continued success in your life and investments in Portugal.
            </p>

            

            <p>此致<br>敬礼！<br>Sincerely,</p>
            <p>{email_date}<br>{email_date_eng}</p>

            

            <div class="footer">
        <img src="cid:LOGO_CID" alt="ORUI Logo" style="height:80px; margin-bottom:10px; display:block; margin-left:auto; margin-right:auto; " />
        <p><strong>欧睿 O’RUI — 智达欧洲</strong></p>
        <p>📍 Portugal | Hong Kong | Beijing | Shanghai | Shenzhen</p>
        <p>🔗 <a href="http://www.oechk.com/">http://www.oechk.com/</a> | 📩 inquiry@oechk.com</p>
        <hr>
        <p>This message and any attachments are intended solely for the designated recipient(s). Unauthorized use, disclosure, or distribution is prohibited.</p>
        <p class="footer_1">
        免责条款 | Disclaimer <br>
        本邮件及附件所载之信息，仅供参考与客户存档之用。最终支付状态、合规核准、税务解释、申请结果等，
        均以葡萄牙及相关主管机关（包括但不限于银行、基金管理公司、律师事务所、政府机关及税务机关）之官方确认及裁定为准。
        若本邮件与葡萄牙语或英语的正式法律文本存在任何差异或歧义，以葡萄牙语版本为优先解释标准，英语版本次之。
        本邮件以中文提供之内容仅作辅助理解，不具法律效力。我们所提供之资讯基于目前已知情况，若后续有更新或官方调整，我们将尽合理努力及时通知您，
        但不对因延迟、第三方处理或政府政策变动所造成的任何影响承担法律责任。</p>
        <p class="footer_1">
        The information contained in this email and its attachments is provided for reference and record purposes only. 
        The final status of payments, compliance approvals, tax interpretations, and application results shall be subject to the official confirmations and determinations of the relevant Portuguese authorities and institutions (including but not limited to banks, fund managers, law firms, government, and tax authorities).In case of any inconsistency or ambiguity, the official Portuguese version shall prevail, with the English version as secondary. The Chinese content herein is for reference only and does not carry legal effect.Our information is based on the best knowledge available at the time of issuance. Should there be updates or official changes, we will use reasonable efforts to notify you promptly. However, we assume no liability for delays, third-party processing, or changes in governmental policies.</p>
        </p>
        <p>© ORUI. All rights reserved.</p>
        </div>
        </div>
        </body>
        </html>
        """
    elif template == 'template2':
         subject = '[再次提醒]关于葡萄牙黄金签证相关费用缴纳提醒 [Reminder]Important Notice on Portugal Golden Visa-Related Fee Payments'
         html_content = f"""
<!DOCTYPE html>
        <html lang="zh-CN">
        <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', sans-serif; background:#f4f4f4; padding:20px; font-size:14px;}}
            .container {{ background:#fff; padding:30px; max-width:700px; margin:auto; border-radius:10px; box-shadow:0 4px 20px rgba(0,0,0,0.1); }}
            h2 {{ color:#1d3557; }}
            pre {{ background:#f9f9f9; padding:15px; border-left:4px solid #1d3557; border-radius:5px; white-space:pre-wrap; font-size:14px; }}
            .footer {{ margin-top:40px; font-size:12px; color:#666; border-top:1px solid #ddd; padding-top:20px; }}
            .footer_1 {{
      font-size: 0.70em;
      color: #888;
    }}
        </style>
        </head>
        <body>
        <div class="container">
            <h2>尊敬的 {cus_name}:</h2>
            <p>Dear {cus_name},</p>
            
            <p>您好!</p>
            <p>Greetings!</p>
            
            <p>感谢您选择我司作为您葡萄牙黄金签证申请及后续服务的合作伙伴。为确保您的签证申请及续签流程顺利进行，并保障您在葡萄牙的合法权益，我司此前已向您发送关于相关费用缴纳的正式通知。但截至目前，我们尚未收到您的付款记录。为避免影响您的签证有效性及在葡投资的稳定性，我司再次郑重提醒您，请务必关注并按时缴纳以下费用。详细账单信息请参见附件:</p>
            <p>Thank you for selecting our company as your trusted partner in managing your Portugal Golden Visa application and ongoing support services. To ensure the smooth processing of your visa application and renewals, and to safeguard your legal rights in Portugal, we previously issued a formal notice regarding the required fee payments. However, as of today, we have not received confirmation of your payment. In order to avoid any risk to your residence status and the stability of your investments in Portugal, we hereby issue this urgent reminder to review and settle the following fees promptly. Please refer to the attached document for full invoice details.</p>
            
            <h3>📌 重点费用说明| Key Fees:</h3>
            {fee_content}


            <p><strong>⚠️ 温馨提醒 / Important Reminders:</strong></p>
            <ul>
            <li>请于收到本支付单之日起<strong>8个自然日内</strong>完成全额支付。</li>
            <li>Full payment is required within 8 calendar days from the date of this notice.</li>
            <li>所有上述费用均为强制性义务，请务必按照截止时间履行，以确保您的黄金签证及相关权益不受影响。</li>
            <li>All fees mentioned above are mandatory and time-sensitive. Please fulfill them on or before the respective deadlines to ensure the validity of your Golden Visa and protect your rights in Portugal.</li>
            <li>我们将继续通过系统为您发送缴费提醒，但请您主动关注相关费用通知，避免因延误带来不必要的风险。</li>
            <li>While our system will continue to send you payment reminders, we strongly recommend that you proactively monitor all notices and plan accordingly</li>
            <li>如有任何疑问或需要进一步协助，欢迎随时联系我司客户支持团队。</li>
            <li>If you have any questions or require assistance, please do not hesitate to contact our customer service team.</li>        
            </ul>

            <p >
            感谢您的理解与配合，祝您在葡萄牙的生活与投资一切顺利！
            </p>
            <p >
            Thank you for your attention and cooperation. We wish you continued success in your life and investments in Portugal.
            </p>

            <p>如您已完成付款，请忽略此提醒并接受我们的感谢。</p>
            <p>If payment has already been made, please disregard this notice and accept our thanks.</p>

            <p>此致<br>敬礼！<br>Sincerely,</p>
            <p>{email_date}<br>{email_date_eng}</p>

            

            <div class="footer">
        <img src="cid:LOGO_CID" alt="ORUI Logo" style="height:80px; margin-bottom:10px; display:block; margin-left:auto; margin-right:auto; " />
        <p><strong>欧睿 O’RUI — 智达欧洲</strong></p>
        <p>📍 Portugal | Hong Kong | Beijing | Shanghai | Shenzhen</p>
        <p>🔗 <a href="http://www.oechk.com/">http://www.oechk.com/</a> | 📩 inquiry@oechk.com</p>
        <hr>
        <p>This message and any attachments are intended solely for the designated recipient(s). Unauthorized use, disclosure, or distribution is prohibited.</p>
        <p class="footer_1">
        免责条款 | Disclaimer <br>
        本邮件及附件所载之信息，仅供参考与客户存档之用。最终支付状态、合规核准、税务解释、申请结果等，
        均以葡萄牙及相关主管机关（包括但不限于银行、基金管理公司、律师事务所、政府机关及税务机关）之官方确认及裁定为准。
        若本邮件与葡萄牙语或英语的正式法律文本存在任何差异或歧义，以葡萄牙语版本为优先解释标准，英语版本次之。
        本邮件以中文提供之内容仅作辅助理解，不具法律效力。我们所提供之资讯基于目前已知情况，若后续有更新或官方调整，我们将尽合理努力及时通知您，
        但不对因延迟、第三方处理或政府政策变动所造成的任何影响承担法律责任。</p>
        <p class="footer_1">
        The information contained in this email and its attachments is provided for reference and record purposes only. 
        The final status of payments, compliance approvals, tax interpretations, and application results shall be subject to the official confirmations and determinations of the relevant Portuguese authorities and institutions (including but not limited to banks, fund managers, law firms, government, and tax authorities).In case of any inconsistency or ambiguity, the official Portuguese version shall prevail, with the English version as secondary. The Chinese content herein is for reference only and does not carry legal effect.Our information is based on the best knowledge available at the time of issuance. Should there be updates or official changes, we will use reasonable efforts to notify you promptly. However, we assume no liability for delays, third-party processing, or changes in governmental policies.</p>
        </p>
        <p>© ORUI. All rights reserved.</p>
        </div>
        </div>
        </body>
        </html>

"""
    elif template == 'template3':
        subject  ='[再次温馨提醒]关于葡萄牙黄金签证相关费用缴纳提醒 -- IMI税局7月提示 [Reminder]Important Notice on Portugal Golden Visa-Related Fee Payments -- IMI Tax Office July Notice'
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', sans-serif; background:#f4f4f4; padding:20px; font-size:14px;}}
            .container {{ background:#fff; padding:30px; max-width:700px; margin:auto; border-radius:10px; box-shadow:0 4px 20px rgba(0,0,0,0.1); }}
            h2 {{ color:#1d3557; }}
            pre {{ background:#f9f9f9; padding:15px; border-left:4px solid #1d3557; border-radius:5px; white-space:pre-wrap; font-size:14px; }}
            .footer {{ margin-top:40px; font-size:12px; color:#666; border-top:1px solid #ddd; padding-top:20px; }}
        </style>
        </head>
        <body>
        <div class="container">
            <h2>尊敬的 {cus_name}:</h2>
            <p>Dear {cus_name},</p>
            
            <p>您好!</p>
            <p>Greetings!</p>
            
            <p>感谢您选择我司作为您葡萄牙黄金签证申请及后续服务的合作伙伴。</p>
            <p>Thank you for selecting our firm as your trusted partner in managing your Portugal Golden Visa application and ongoing support services.</p>

            <p>为确保您的签证申请及后续续签流程顺利进行，并保障您在葡萄牙的合法权益，我司郑重提醒您务必关注并按时缴纳以下费用。这些费用直接关系到您的签证有效性和在葡萄牙的投资稳定性，请务必重视。详细账单信息请参见附件：</p>
            <p>To ensure the smooth processing of your visa application and subsequent renewals, and to safeguard your legal rights in Portugal, we hereby issue this formal reminder to review and settle the following fees in a timely manner. These payments are directly linked to the validity of your residence status and the stability of your investments in Portugal. Please refer to the attached document for the full invoice details:</p>

            
            {fee_content}

        
            <p><strong>⚠️ 温馨提醒 / Important Reminders:</strong></p>
            <ul>
            <li>请于收到本支付单之日起<strong>8个自然日内</strong>完成全额支付。</li>
            <li>Full payment is required <strong> within 8 calendar days </strong> from the date of this notice.</li>
            <li>所有上述费用均为强制性合规义务，请务必按照截止时间履行，以确保您的黄金签证及相关权益不受影响。</li>
            <li>All fees mentioned above are mandatory and time-sensitive. Please fulfill them on or before the respective deadlines to ensure the validity of your Golden Visa and protect your rights in Portugal.</li>
            <li>我们将继续通过系统为您发送缴费提醒，但请您主动关注相关费用通知，避免因延误带来不必要的风险。</li>
            <li>While our system will continue to send you payment reminders, we strongly recommend that you proactively monitor all notices and plan accordingly</li>
            <li>如有任何疑问或需要进一步协助，欢迎随时联系我司客户支持团队。</li>
            <li>If you have any questions or require assistance, please do not hesitate to contact our customer service team.</li>        
            </ul>

            <p >
            感谢您的理解与配合，祝您在葡萄牙的生活与投资一切顺利！
            </p>
            <p >
            Thank you for your attention and cooperation. We wish you continued success in your life and investments in Portugal.
            </p>

            <p>如您已完成付款，请忽略此提醒并接受我们的感谢。</p>
            <p>If payment has already been made, please disregard this notice and accept our thanks.</p>

            

            <p>此致<br>敬礼！<br>Sincerely,</p>
            <p>{email_date}<br>{email_date_eng}</p>

            

            <div class="footer">
        <img src="cid:LOGO_CID" alt="ORUI Logo" style="height:80px; margin-bottom:10px; display:block; margin-left:auto; margin-right:auto; " />
        <p><strong>欧睿 O’RUI — 智达欧洲</strong></p>
        <p>📍 Portugal | Hong Kong | Beijing | Shanghai | Shenzhen</p>
        <p>🔗 <a href="http://www.oechk.com/">http://www.oechk.com/</a> | 📩 inquiry@oechk.com</p>
        <hr>
        <p>This message and any attachments are intended solely for the designated recipient(s). Unauthorized use, disclosure, or distribution is prohibited.</p>
        <p class="footer_1">
        免责条款 | Disclaimer <br>
        本邮件及附件所载之信息，仅供参考与客户存档之用。最终支付状态、合规核准、税务解释、申请结果等，
        均以葡萄牙及相关主管机关（包括但不限于银行、基金管理公司、律师事务所、政府机关及税务机关）之官方确认及裁定为准。
        若本邮件与葡萄牙语或英语的正式法律文本存在任何差异或歧义，以葡萄牙语版本为优先解释标准，英语版本次之。
        本邮件以中文提供之内容仅作辅助理解，不具法律效力。我们所提供之资讯基于目前已知情况，若后续有更新或官方调整，我们将尽合理努力及时通知您，
        但不对因延迟、第三方处理或政府政策变动所造成的任何影响承担法律责任。</p>
        <p class="footer_1">
        The information contained in this email and its attachments is provided for reference and record purposes only. 
        The final status of payments, compliance approvals, tax interpretations, and application results shall be subject to the official confirmations and determinations of the relevant Portuguese authorities and institutions (including but not limited to banks, fund managers, law firms, government, and tax authorities).In case of any inconsistency or ambiguity, the official Portuguese version shall prevail, with the English version as secondary. The Chinese content herein is for reference only and does not carry legal effect.Our information is based on the best knowledge available at the time of issuance. Should there be updates or official changes, we will use reasonable efforts to notify you promptly. However, we assume no liability for delays, third-party processing, or changes in governmental policies.</p>
        </p>
        <p>© ORUI. All rights reserved.</p>
        </div>
        </div>
        </body>
        </html>
        """
    
    elif template == 'Receipt_Remind':
        subject = f"【O'RUI衷心致谢】葡萄牙黄金签证付款凭证 - [凭证编号:{invoice_no}] O'RUI Sincere Thanks: Portugal Golden Visa Payment Receipt [Ref:{invoice_no}]"
        html_content = f"""
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
      background-color: #f7f7f7;
      font-size:14px;
      padding: 40px 0;
    }}
    .container {{
      max-width: 700px;
      margin: 0 auto;
      background-color: #ffffff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      padding: 40px;
      color: #333;
      line-height: 1.8;
    }}
    h2 {{
      color: #2c3e50;
      margin-top: 0;
    }}
    p {{
      margin: 0.3em 0;
    }}
    .section-title {{
      font-weight: bold;
      color: #0066cc;
      margin-top: 30px;
    }}
    ul {{
      margin: 10px 0 20px 20px;
      padding-left: 0;
    }}
    li {{
      margin-bottom: 8px;
    }}
    .footer {{
      margin-top: 30px;
      font-size: 0.95em;
      color: #888;
    }}
    .footer_1 {{
      font-size: 0.70em;
      color: #888;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h2>尊敬的 {cus_name},<br> Dear {cus_name},</h2>

    <p>您好！<br>Greetings!</p>

    <p>衷心感谢您对我司工作的高度配合与支持！<br>
       Thank you for your valued cooperation and support.</p>

    <p>✅ 我们已确认收到您就相关费用的支付。<br>
       We acknowledge receipt of your payment for the relevant fees.</p>

    <p>请查阅邮件附件获取本次支付的正式收据，供您参考保存。<br>
       Please find the official payment receipts attached to this email for your records.</p>

    <p class="section-title">款项处理状态说明 / Payment Processing Update:</p>
    <ul>
      <li>您的付款已成功到账。<br>Your payment has been successfully received.</li>
      <li>我们将按照标准服务流程，为您处理后续的款项转付及相关信息登记更新。<br>We will now proceed through our standard service workflow to handle the onward processing of these payments and update the relevant records.</li>
      <li>流程我们会跟进协调，确保及时处理。<br>We will monitor the progress throughout this process to ensure timely completion.</li>
    </ul>

    <p>💬 诚挚地感谢您的信任与配合。<br>
       We sincerely appreciate your trust and cooperation.</p>

    <p class="section-title">感恩信任 / For your trust:</p>
    <p>非常感谢您选择我们作为您葡萄牙黄金签证及相关事务的服务伙伴。能为您提供服务是我们的荣幸。<br>
       We are truly grateful that you have chosen our firm as your partner for your Portugal Golden Visa journey and related matters. It is our privilege to serve you.</p>

    <p class="section-title">感恩行动 / For your action:</p>
    <p>非常感谢您对本次费用提醒的迅速响应和及时支付！您的高效配合是确保一切合规义务顺畅履行的关键。<br>
       We deeply appreciate your prompt attention to our reminder and your timely payment! Your efficiency is key to the smooth fulfillment of these important compliance requirements.</p>
    <p>&nbsp;</p>
    <p>再次感谢您一直以来的支持与理解！<br>
       Thank you again for your continued support and understanding.</p>

       <p style="font-size: 12px; color: #000000; line-height: 1.6; margin-top: 20px;">
  <strong>注：</strong>感谢您的配合。我方确认代转款项已收讫，会安排代缴葡萄牙房产税费等年度费用（含 IMI）；IMI 税费政府每年公报有固定缴纳时限（通常年缴两至三期），如逾期支付可能将产生政府滞纳金，我方尽力确保在收到客户代支付的费用时安排代葡萄牙缴纳至税局；若客户本次错过政府规定之支付期限 2025 年 6 月 30 日之前支付 IMI，我方将于下一缴费周期为您补缴，后续如有新账单或政策调整将及时转达，全力协助您税务合规，感谢！
</p>

<p style="font-size: 12px; color: #000000; line-height: 1.6; margin-top: 10px;">
  <strong>Note:</strong> Thank you for your cooperation. We confirm that the entrusted payment has been received and will proceed to pay the annual property-related taxes in Portugal on your behalf (including IMI). The IMI tax is subject to government-mandated deadlines announced each year, typically payable in two to three installments. Late payment may result in government-imposed penalties.<br><br>
  We will do our utmost to ensure timely payment to the Portuguese tax authority once the entrusted payment from the client is received. If the client misses the official deadline of June 30, 2025 for this IMI payment, we will arrange for the payment to be made in the next payment cycle. Any new bills or policy changes will be promptly communicated to you. We are committed to fully assisting you in staying tax compliant. Thank you!
</p>


    

       <p>此致<br>敬礼！<br>Sincerely,</p>
        <p>{email_date}<br>{email_date_eng}</p>

    <div class="footer">
        <img src="cid:LOGO_CID" alt="ORUI Logo" style="height:80px; margin-bottom:10px; display:block; margin-left:auto; margin-right:auto; " />
        <p><strong>欧睿 O’RUI — 智达欧洲</strong></p>
        <p>📍 Portugal | Hong Kong | Beijing | Shanghai | Shenzhen</p>
        <p>🔗 <a href="http://www.oechk.com/">http://www.oechk.com/</a> | 📩 inquiry@oechk.com</p>
        <hr>
        <p>This message and any attachments are intended solely for the designated recipient(s). Unauthorized use, disclosure, or distribution is prohibited.</p>
        <p class="footer_1">
        免责条款 | Disclaimer <br>
        本邮件及附件所载之信息，仅供参考与客户存档之用。最终支付状态、合规核准、税务解释、申请结果等，
        均以葡萄牙及相关主管机关（包括但不限于银行、基金管理公司、律师事务所、政府机关及税务机关）之官方确认及裁定为准。
        若本邮件与葡萄牙语或英语的正式法律文本存在任何差异或歧义，以葡萄牙语版本为优先解释标准，英语版本次之。
        本邮件以中文提供之内容仅作辅助理解，不具法律效力。我们所提供之资讯基于目前已知情况，若后续有更新或官方调整，我们将尽合理努力及时通知您，
        但不对因延迟、第三方处理或政府政策变动所造成的任何影响承担法律责任。</p>
        <p class="footer_1">
        The information contained in this email and its attachments is provided for reference and record purposes only. 
        The final status of payments, compliance approvals, tax interpretations, and application results shall be subject to the official confirmations and determinations of the relevant Portuguese authorities and institutions (including but not limited to banks, fund managers, law firms, government, and tax authorities).In case of any inconsistency or ambiguity, the official Portuguese version shall prevail, with the English version as secondary. The Chinese content herein is for reference only and does not carry legal effect.Our information is based on the best knowledge available at the time of issuance. Should there be updates or official changes, we will use reasonable efforts to notify you promptly. However, we assume no liability for delays, third-party processing, or changes in governmental policies.</p>
        </p>
        
        <p>© ORUI. All rights reserved.</p>
        </div>
  </div>
</body>
</html>


        """

    elif template == 'Receipt_Remind-IRS':
        subject = f"【温馨确认】感谢！葡萄牙相关费用已收到 | Payment Confirmation & Thanks for Your Portugal Fees"
        html_content = f"""
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
      background-color: #f7f7f7;
      font-size:14px;
      padding: 40px 0;
    }}
    .container {{
      max-width: 700px;
      margin: 0 auto;
      background-color: #ffffff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      padding: 40px;
      color: #333;
      line-height: 1.8;
    }}
    p {{
      margin: 0.3em 0;
    }}
    h2 {{
      color: #2c3e50;
      margin-top: 0;
    }}
    .section-title {{
      font-weight: bold;
      color: #0066cc;
      margin-top: 20px;
    }}
    ul {{
      margin: 10px 0 20px 20px;
      padding-left: 0;
    }}
    li {{
      margin-bottom: 8px;
    }}
    .footer {{
      margin-top: 20px;
      font-size: 0.95em;
      color: #888;
    }}
    .footer_1 {{
      font-size: 0.70em;
      color: #888;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h2>尊敬的 {cus_name},<br> Dear {cus_name},</h2>

    <p>您好！<br>Greetings!</p>

    <p>衷心感谢您对我司工作的高度配合与支持！<br>
       Thank you for your valued cooperation and support.</p>

    <p>✅ 我们已确认收到您支付的相关费用，并已按照约定流程安排转付至葡萄牙相关机构/账户。<br>
       We confirm receipt of your payment for the relevant fees, and we have already arranged the onward transfer to the designated institutions/accounts in Portugal as per the agreed procedure.</p>

    <p>请查阅邮件附件，本次我们直接附上由 IRS 银行出具的付款证明 (Proof of Payment)，供您参考与保存。
<br>
Please find attached the Proof of Payment issued by IRS Bank, which serves as the official confirmation of this transaction for your records.
    
    
    <p class="section-title"> 📌 款项处理状态说明 / Payment Processing Update:</p>
    <ul>
      <li>您的付款已成功到账。<br>Your payment has been successfully received.</li>
      <li>我们已代为完成银行转付，并取得 IRS 银行的付款证明。<br>We have completed the onward transfer through IRS Bank and obtained the official Proof of Payment.</li>
      <li>后续流程我们会持续跟进协调，确保一切及时、顺利处理。<br>We will continue to coordinate the follow-up procedures to ensure timely and smooth completion.</li>
    </ul>

    <p>💬 诚挚地感谢您的信任与配合。<br>
       We sincerely appreciate your trust and cooperation.</p>

    <p class="section-title">感恩信任 / For your trust:</p>
    <p>非常感谢您选择我们作为您葡萄牙黄金签证及相关事务的服务伙伴。能为您提供服务是我们的荣幸。<br>
       We are truly grateful that you have chosen our firm as your partner for your Portugal Golden Visa journey and related matters. It is our privilege to serve you.</p>

    <p class="section-title">感恩行动 / For your action:</p>
    <p>非常感谢您对本次费用提醒的迅速响应和及时支付！您的高效配合是确保一切合规义务顺畅履行的关键。<br>
       We deeply appreciate your prompt attention to our reminder and your timely payment! Your efficiency is key to the smooth fulfillment of these important compliance requirements.</p>
    <p>&nbsp;</p>
    <p>再次感谢您一直以来的支持与理解！<br>
       Thank you again for your continued support and understanding.</p>



    
       <p>此致<br>敬礼！<br>Sincerely,</p>
        <p>{email_date}<br>{email_date_eng}</p>

    <div class="footer">
        <img src="cid:LOGO_CID" alt="ORUI Logo" style="height:80px; margin-bottom:10px; display:block; margin-left:auto; margin-right:auto; " />
        <p><strong>欧睿 O’RUI — 智达欧洲</strong></p>
        <p>📍 Portugal | Hong Kong | Beijing | Shanghai | Shenzhen</p>
        <p>🔗 <a href="http://www.oechk.com/">http://www.oechk.com/</a> | 📩 inquiry@oechk.com</p>
        <hr>
        <p>This message and any attachments are intended solely for the designated recipient(s). Unauthorized use, disclosure, or distribution is prohibited.</p>
        <p class="footer_1">
        免责条款 | Disclaimer <br>
        本邮件及附件所载之信息，仅供参考与客户存档之用。最终支付状态、合规核准、税务解释、申请结果等，
        均以葡萄牙及相关主管机关（包括但不限于银行、基金管理公司、律师事务所、政府机关及税务机关）之官方确认及裁定为准。
        若本邮件与葡萄牙语或英语的正式法律文本存在任何差异或歧义，以葡萄牙语版本为优先解释标准，英语版本次之。
        本邮件以中文提供之内容仅作辅助理解，不具法律效力。我们所提供之资讯基于目前已知情况，若后续有更新或官方调整，我们将尽合理努力及时通知您，
        但不对因延迟、第三方处理或政府政策变动所造成的任何影响承担法律责任。</p>
        <p class="footer_1">
        The information contained in this email and its attachments is provided for reference and record purposes only. 
        The final status of payments, compliance approvals, tax interpretations, and application results shall be subject to the official confirmations and determinations of the relevant Portuguese authorities and institutions (including but not limited to banks, fund managers, law firms, government, and tax authorities).In case of any inconsistency or ambiguity, the official Portuguese version shall prevail, with the English version as secondary. The Chinese content herein is for reference only and does not carry legal effect.Our information is based on the best knowledge available at the time of issuance. Should there be updates or official changes, we will use reasonable efforts to notify you promptly. However, we assume no liability for delays, third-party processing, or changes in governmental policies.</p>
        <p>© ORUI. All rights reserved.</p>
        </div>
  </div>
</body>
</html>


        """
    elif template == 'Invoice_Remind_202510':
        subject = f"关于您2024年度IMI（房产税）及IRS（个人所得税）缴付事宜的温馨通知 | Gentle Reminder Regarding Your 2024 IMI (Property Tax) and IRS (Personal Income Tax) Payments"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', sans-serif; background:#f4f4f4; padding:20px; font-size:14px;}}
            .container {{ background:#fff; padding:30px; max-width:700px; margin:auto; border-radius:10px; box-shadow:0 4px 20px rgba(0,0,0,0.1); }}
            h2 {{ color:#1d3557; }}
            pre {{ background:#f9f9f9; padding:15px; border-left:4px solid #1d3557; border-radius:5px; white-space:pre-wrap; font-size:14px; }}
            .footer {{ margin-top:40px; font-size:12px; color:#666; border-top:1px solid #ddd; padding-top:20px; }}
            .footer_1 {{
      font-size: 0.70em;
      color: #888;
    }}
        </style>
        </head>
        <body>
        <div class="container">
            <h2>尊敬的 {cus_name}:</h2>
            <p>Dear {cus_name},</p>

            <p>为协助您持续维护葡萄牙投资房产的良好状态及个人税务记录，现将您2024年度相关葡萄牙政府官方通知税款的缴付整理如下，供您参考安排：</p>
            <p>To assist you in maintaining the good standing of your investment property in Portugal as well as your personal tax records, we have organized the relevant official Portuguese government notices for your 2024 tax payments as follows for your reference and planning:</p>
            
            {fee_content}

            <p>您可通过葡萄牙个人银行账户操作付款，支付后请提供相应凭证我方登记及保留记录：或以代支付服务以人民币支付对应代转款账户，我方将代为完成税款缴付，确保及时结清所有费用，避免影响您的房产权益及税务记录。</p>
            <p>You may make the payment through your Portuguese personal bank account. After payment, please provide the corresponding receipt for our registration and record-keeping; or you may use the proxy payment service to pay the corresponding transfer account in RMB, and we will complete the tax payment on your behalf, ensuring all fees are paid on time and avoiding any impact on your property rights and tax records.</p>

            
            <p>请您告知是否需要我们协助办理代缴事宜，以便我们第一时间为您安排。若您需核对税单细节或有其他疑问，也欢迎随时与我们联系。</p>
            <p>
            Please let us know whether you need our assistance to handle the proxy payment so that we can arrange it for you promptly. If you need to verify tax details or have any other questions, please feel free to contact us at any time.
            </p>


            <p>感谢您的理解与配合，祝您生活顺利！</p>
            <p>
            Thank you for your understanding and cooperation. Wishing you a smooth and pleasant life!
            </p>
            

            <p>此致<br>敬礼！<br>Sincerely,</p>
            <p>{email_date}<br>{email_date_eng}</p>

            <p>
            - 本邮件中提及的税款金额、缴费期限等信息，均基于税务部门当前公示内容及我方获取的最新数据整理，仅供您参考；最终缴费标准及期限请以葡萄牙税务部门出具的官方为准。
            </p>
            <p>
            - The tax amounts, payment deadlines, and other information mentioned in this email are based on the currently published information by the tax authorities and the latest data we have obtained, for your reference only; the final payment standards and deadlines are subject to the official documents issued by the Portuguese tax authorities.
            </p>


            <p>
            - 若您选择由我方代为缴付，需确保所提供的款项金额准确且在约定时间内到账；因款项延迟到账、金额不足或客戶个人信息变更未及时告知导致的逾期、额外费用等问题，请知悉非我方原因以致。
            </p>
            <p>
            - If you choose to have us pay on your behalf, please ensure that the amount provided is accurate and arrives within the agreed time; any delay in arrival, insufficient amount, or failure to promptly notify us of personal information changes resulting in overdue payment or additional costs, please note that this is not caused by us.
            </p>


            <div class="footer">
        <img src="cid:LOGO_CID" alt="ORUI Logo" style="height:80px; margin-bottom:10px; display:block; margin-left:auto; margin-right:auto; " />
        <p><strong>欧睿 O’RUI — 智达欧洲</strong></p>
        <p>📍 Portugal | Hong Kong | Beijing | Shanghai | Shenzhen</p>
        <p>🔗 <a href="http://www.oechk.com/">http://www.oechk.com/</a> | 📩 inquiry@oechk.com</p>
        <hr>
        <p>This message and any attachments are intended solely for the designated recipient(s). Unauthorized use, disclosure, or distribution is prohibited.</p>
        <p class="footer_1">
        免责条款 | Disclaimer <br>
        本邮件及附件所载之信息，仅供参考与客户存档之用。最终支付状态、合规核准、税务解释、申请结果等，
        均以葡萄牙及相关主管机关（包括但不限于银行、基金管理公司、律师事务所、政府机关及税务机关）之官方确认及裁定为准。
        若本邮件与葡萄牙语或英语的正式法律文本存在任何差异或歧义，以葡萄牙语版本为优先解释标准，英语版本次之。
        本邮件以中文提供之内容仅作辅助理解，不具法律效力。我们所提供之资讯基于目前已知情况，若后续有更新或官方调整，我们将尽合理努力及时通知您，
        但不对因延迟、第三方处理或政府政策变动所造成的任何影响承担法律责任。</p>
        <p class="footer_1">
        The information contained in this email and its attachments is provided for reference and record purposes only. 
        The final status of payments, compliance approvals, tax interpretations, and application results shall be subject to the official confirmations and determinations of the relevant Portuguese authorities and institutions (including but not limited to banks, fund managers, law firms, government, and tax authorities).In case of any inconsistency or ambiguity, the official Portuguese version shall prevail, with the English version as secondary. The Chinese content herein is for reference only and does not carry legal effect.Our information is based on the best knowledge available at the time of issuance. Should there be updates or official changes, we will use reasonable efforts to notify you promptly. However, we assume no liability for delays, third-party processing, or changes in governmental policies.</p>
        </p>
        <p>© ORUI. All rights reserved.</p>
        </div>
        </div>
        </body>
        </html>
        """
    
    elif template == 'Invoice_Form_202601':
        
      template_name = '2026_invoice_form_template.html'
      if data.get('is_form',None):
        subject = '【FGI 】黄金签证相关打指模登记及费用缴纳通知 [FGI]  Notice on AIMA Biometrics Trip Registration & Portugal Golden Visa-Related Fee Payments'
      else:
            # 邮件subject
        subject = '【FGI 】葡萄牙黄金签证相关费用缴纳通知  [FGI] Notice on Portugal Golden Visa-Related Fee Payments'

      # 将所有的内容都整合到data中
      # 包括
      
      template_jinja = env.get_template(template_name)
      html_content = template_jinja.render(data)


    return html_content,subject
    # return html_content,subject

    
