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
		ts_code_str = ''
		for index in range(999):
			if index == 998:
				ts_code_str = ts_code_str + dataArray[index][0] + ''
			else:
				ts_code_str = ts_code_str + dataArray[index][0] + ','
		# 对股票列表进行当天数据的拉取
		# 调用具体方法执行
		dto = StockClass()
		# ts_code_str = ','.join(dataArray)
		print('ts_code_str',ts_code_str)
		# dto.type = 'D'
		dto.ts_code = ts_code_str
		# 固定15年1月1日开始
		# 获取当前日期
		current_date = datetime.now().date()
		# 将日期格式化为YYYYMMDD
		today_formatted = current_date.strftime('%Y%m%d')
		print("date_format",today_formatted)
		# 获取今天的日期
		today = datetime.now()
		# 获取昨天的日期
		yesterday = today - timedelta(days=1)
		# 转换为 YYYYMMDD 格式
		yesterday_formatted = yesterday.strftime('%Y%m%d')
		print("yesterday_formatted", yesterday_formatted)
		dto.end_date = today_formatted
		dto.start_date = yesterday_formatted
		getStockFactorFromThreeDB(dto)
		return print("getStockListFromDB---success===>")
	print("getStockListFromDB---error===>")

def data_save():
    logger.info("保存数据至数据库")
    # 调用具体方法执行
    dto = StockClass()
    # dto.type = 'D'
    dto.ts_code = '600800.SH,300757.SZ'
	# 固定15年1月1日开始
    dto.end_date = '20241231'
    dto.start_date = '20150101'
    # getStockFactorFromThreeDB(dto)
    getStockListFromDB()