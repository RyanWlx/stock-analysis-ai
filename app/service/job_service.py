import time

from app.config.log_config import logger
import app.router.stock_router as stock_router
from app.service import stock_service as stockService
from app.parameter.request.qutationRequest import QutationDTO,StockClass
from fastapi import APIRouter, Depends, Query
import numpy as np
from app.dependencies.db_depend import get_db
from sqlalchemy.orm import Session
import app.repository.stock_repo as stockRepo
from datetime import datetime, timedelta
import json

# 输出时间
# 从第三方库获取股票行情数据
def getStockFactorFromThreeDB(qutationRequeat: StockClass, db: Session = next(get_db())):
	#获取股票行情数据
	print("qutationRequeat12===>",qutationRequeat.ts_code)
	df = stockService.get_stk_factor(qutationRequeat.ts_code, qutationRequeat.start_date, qutationRequeat.end_date)
	print(df)
	if df is not None:
		dataArray = np.array(df).tolist()
		stockService.save_stk_factor(qutationRequeat.type, dataArray, db)
		print("getStockFactor---success===>")
	print("getStockFactor---error===>")

# 从自有数据库中获取某个股票是否存在，避免重复报错
def getStockFactorFromDB(qutationRequeat: StockClass, db: Session = next(get_db())):
	#获取股票行情数据
	print("qutationRequeat12===>",qutationRequeat.ts_code)
	df = stockService.get_stk_factor(qutationRequeat.ts_code, qutationRequeat.start_date, qutationRequeat.end_date)
	print(df)
	if df is not None:
		dataArray = np.array(df).tolist()
		stockService.save_stk_factor(qutationRequeat.type, dataArray, db)
		print("getStockFactor---success===>")
	print("getStockFactor---error===>")
# 从数据库中获取股票列表
def getStockListFromDB( db: Session = next(get_db())):
	#获取股票行情数据
	print("getStockListFromDB===>")
	df = stockRepo.get_stock_list_all(db)
	print("999",np.array(df))
	if df is not None:
		dataArray = np.array(df).tolist()
		ts_code_str0 = ''
		ts_code_str1 = ''
		ts_code_str2 = ''
		ts_code_str3 = ''
		ts_code_str4 = ''
		ts_code_str5 = ''
		ts_code_str6 = ''

		for index in range(len(dataArray)):
			if index < 1000:
				if index == 999 or index == len(dataArray) -1:
					ts_code_str0 = ts_code_str0 + dataArray[index][0] + ''
				else:
					ts_code_str0 = ts_code_str0 + dataArray[index][0] + ','
			elif 999 < index < 2000:
				if index == 1999 or index == len(dataArray) -1:
					ts_code_str1 = ts_code_str1 + dataArray[index][0] + ''
				else:
					ts_code_str1 = ts_code_str1 + dataArray[index][0] + ','
			elif 1999 < index < 3000:
				if index == 2999 or index == len(dataArray) -1:
					ts_code_str2 = ts_code_str2 + dataArray[index][0] + ''
				else:
					ts_code_str2 = ts_code_str2 + dataArray[index][0] + ','
			elif 2999 < index < 4000:
				if index == 3999 or index == len(dataArray) -1:
					ts_code_str3 = ts_code_str3 + dataArray[index][0] + ''
				else:
					ts_code_str3 = ts_code_str3 + dataArray[index][0] + ','
			elif 3999 < index < 5000:
				if index == 4999 or index == len(dataArray) -1:
					ts_code_str4 = ts_code_str4 + dataArray[index][0] + ''
				else:
					ts_code_str4 = ts_code_str4 + dataArray[index][0] + ','
			elif 4999 < index < 6000:
				if index == 5999 or index == len(dataArray) -1:
					ts_code_str5 = ts_code_str5 + dataArray[index][0] + ''
				else:
					ts_code_str5 = ts_code_str5 + dataArray[index][0] + ','

		# 获取当前日期
		current_date = datetime.now().date()
		# 将日期格式化为YYYYMMDD
		today_formatted = current_date.strftime('%Y%m%d')
		print("today_formatted",today_formatted)
		# 对股票列表进行当天数据的拉取
		# 调用具体方法执行
		dto0 = StockClass()
		dto1 = StockClass()
		dto2 = StockClass()
		dto3 = StockClass()
		dto4 = StockClass()
		dto5 = StockClass()

		if ts_code_str0 != '':
			print('走到了第0秒')
			dto0.ts_code = ts_code_str0
			dto0.end_date = today_formatted
			dto0.start_date = today_formatted
			getStockFactorFromThreeDB(dto0)
		if ts_code_str1 != '':
			time.sleep(1)
			print('走到了第1秒')
			dto1.ts_code = ts_code_str0
			dto1.end_date = today_formatted
			dto1.start_date = today_formatted
			getStockFactorFromThreeDB(dto1)
		if ts_code_str2 != '':
			time.sleep(2)
			print('走到了第2秒')
			dto2.ts_code = ts_code_str0
			dto2.end_date = today_formatted
			dto2.start_date = today_formatted
			getStockFactorFromThreeDB(dto2)
		if ts_code_str3 != '':
			time.sleep(3)
			print('走到了第3秒')
			dto3.ts_code = ts_code_str0
			dto3.end_date = today_formatted
			dto3.start_date = today_formatted
			getStockFactorFromThreeDB(dto3)
		if ts_code_str4 != '':
			time.sleep(4)
			print('走到了第4秒')
			dto4.ts_code = ts_code_str0
			dto4.end_date = today_formatted
			dto4.start_date = today_formatted
			getStockFactorFromThreeDB(dto4)
		if ts_code_str5 != '':
			time.sleep(5)
			print('走到了第5秒')
			dto5.ts_code = ts_code_str0
			dto5.end_date = today_formatted
			dto5.start_date = today_formatted
			getStockFactorFromThreeDB(dto5)
		return print("getStockListFromDB---success===>")
	print("getStockListFromDB---error===>")

def data_save():
    logger.info("保存数据至数据库")
    getStockListFromDB()