import time

from app.config.log_config import logger
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
		ts_code_str0 = []
		ts_code_str1 = []
		ts_code_str2 = []
		ts_code_str3 = []
		ts_code_str4 = []
		ts_code_str5 = []
		ts_code_str6 = []
		print("股票列表长度",len(dataArray))
		for index in range(len(dataArray)):
			if index < 1000:
				# if index == 999 or index == len(dataArray) -1:
				# 	ts_code_str0 = ts_code_str0 + dataArray[index][0]
				# else:
				# 	ts_code_str0 = ts_code_str0 + dataArray[index][0] + ','
				ts_code_str0.append(dataArray[index][0])
			elif 999 < index < 2000:
				# if index == 1999 or index == len(dataArray) -1:
				# 	ts_code_str1 = ts_code_str1 + dataArray[index][0]
				# else:
				# 	ts_code_str1 = ts_code_str1 + dataArray[index][0] + ','
				ts_code_str1.append(dataArray[index][0])
			elif 1999 < index < 3000:
				# if index == 2999 or index == len(dataArray) -1:
				# 	ts_code_str2 = ts_code_str2 + dataArray[index][0]
				# else:
				# 	ts_code_str2 = ts_code_str2 + dataArray[index][0] + ','
				ts_code_str2.append(dataArray[index][0])
			elif 2999 < index < 4000:
				ts_code_str3.append(dataArray[index][0])
				# if index == 3999 or index == len(dataArray) -1:
				# 	ts_code_str3 = ts_code_str3 + dataArray[index][0]
				# else:
				# 	ts_code_str3 = ts_code_str3 + dataArray[index][0] + ','
			elif 3999 < index < 5000:
				ts_code_str4.append(dataArray[index][0])
				# if index == 4999 or index == len(dataArray) -1:
				# 	ts_code_str4 = ts_code_str4 + dataArray[index][0]
				# else:
				# 	ts_code_str4 = ts_code_str4 + dataArray[index][0] + ','
			elif 4999 < index < 6000:
				ts_code_str5.append(dataArray[index][0])
				# if index == 5999 or index == len(dataArray) -1:
				# 	ts_code_str5 = ts_code_str5 + dataArray[index][0]
				# else:
				# 	ts_code_str5 = ts_code_str5 + dataArray[index][0] + ','
		print("6个股票列表长度", len(ts_code_str5),len(ts_code_str4),len(ts_code_str3),len(ts_code_str2),len(ts_code_str1),len(ts_code_str0))
		# 获取当前日期s
		current_date =  (datetime.now() - timedelta(days=2)).date()
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
			dto0.ts_code = ','.join(ts_code_str0)
			dto0.end_date = today_formatted
			dto0.start_date = today_formatted
			getStockFactorFromThreeDB(dto0)
		if ts_code_str1 != '':
			time.sleep(60)
			print('走到了第1秒')
			dto1.ts_code = ','.join(ts_code_str1)
			dto1.end_date = today_formatted
			dto1.start_date = today_formatted
			getStockFactorFromThreeDB(dto1)
		if ts_code_str2 != '':
			time.sleep(120)
			print('走到了第2秒')
			dto2.ts_code = ','.join(ts_code_str2)
			dto2.end_date = today_formatted
			dto2.start_date = today_formatted
			getStockFactorFromThreeDB(dto2)
		if ts_code_str3 != '':
			time.sleep(180)
			print('走到了第3秒')
			dto3.ts_code = ','.join(ts_code_str3)
			dto3.end_date = today_formatted
			dto3.start_date = today_formatted
			getStockFactorFromThreeDB(dto3)
		if ts_code_str4 != '':
			time.sleep(240)
			print('走到了第4秒')
			dto4.ts_code = ','.join(ts_code_str4)
			dto4.end_date = today_formatted
			dto4.start_date = today_formatted
			getStockFactorFromThreeDB(dto4)
		if ts_code_str5 != '':
			time.sleep(300)
			print('走到了第5秒')
			dto5.ts_code = ','.join(ts_code_str5)
			dto5.end_date = today_formatted
			dto5.start_date = today_formatted
			getStockFactorFromThreeDB(dto5)
		return print("getStockListFromDB---success===>")
	print("getStockListFromDB---error===>")

def data_save():
    """每日 17:10 定时任务入口。

    原实现走 Tushare（getStockListFromDB），因 Tushare 限速已停用。
    现改为从同花顺抓取「当天」行情，填充 tb_daliy 与 tb_stk_factor 两张表。
    具体逻辑见 app/service/ths_daily_sync.py（含复权价、技术指标、幂等写入）。
    """
    logger.info("保存数据至数据库（同花顺当天行情 -> tb_daliy / tb_stk_factor）")
    try:
        from app.service.ths_daily_sync import sync_daily
        summary = sync_daily()
        if summary.get('error'):
            logger.error(f"每日行情同步未完成: {summary.get('error')}")
        else:
            logger.info(f"每日行情同步完成: {summary}")
    except Exception as e:
        logger.exception(f"每日行情同步失败: {e}")
    # 旧的 Tushare 方式（已停用）: getStockListFromDB()