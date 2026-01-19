# from View.view import *
from Model.GoogleAPI import GoogleClass
from View.download import *
from View.view_copy import *

from logs.setup_logging import setup_logging
import logging

google = GoogleClass()

setup_logging()
logger = logging.getLogger('app')    # 获取logger
logger.info('log应用启动成功')        # 使用logger

if __name__ == "__main__":
    # view(google)
    view_form(google)
    #download_excel(google)
    # download_doc(google)


