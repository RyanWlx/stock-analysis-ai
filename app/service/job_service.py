from app.config.log_config import logger
import app.router.stock_router as stock_router
from app.service import stock_service as stockService
from app.parameter.request.qutationRequest import QutationDTO,StockClass
from fastapi import APIRouter, Depends, Query
import numpy as np
from app.dependencies.db_depend import get_db
from sqlalchemy.orm import Session

# 输出时间
def getStockFactorFromThreeDB(qutationRequeat: StockClass, db: Session = Depends(get_db)):
	#获取股票行情数据
	print("qutationRequeat1===>",qutationRequeat)
	df = stockService.get_stk_factor(qutationRequeat.ts_code, qutationRequeat.start_date, qutationRequeat.end_date)
	print(df)
	if df is not None:
		dataArray = np.array(df).tolist()
		stockService.save_stk_factor(qutationRequeat.type, dataArray, db)
		print("getStockFactor---success===>")
	print("getStockFactor---error===>")

def data_save():
    logger.info("保存数据至数据库")
    # 调用具体方法执行
    dto = StockClass()
    # dto.type = 'D'
    dto.ts_code = '600800.SH'
    dto.end_date = '20240101'
    dto.start_date = '20241231'
    getStockFactorFromThreeDB(dto)

