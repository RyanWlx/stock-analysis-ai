from app.service import stock_service as stockService
from app.service import indicatorData_service as indicatorDataService
from fastapi import APIRouter, Depends
from app.parameter.request.qutationRequest import QutationDTO
from app.parameter.response import myResponse
import numpy as np
from app.dependencies.db_depend import get_db
from sqlalchemy.orm import Session
from app.config.log_config import logger

router = APIRouter(tags=["indicatorData_router"])

@router.post("/stock/getStockCyqChips")
async def getStockFactor(qutationRequeat: QutationDTO, db: Session = Depends(get_db)):
	#获取A股每日的筹码分布情况
	df = indicatorDataService.get_cyq_chips(qutationRequeat.ts_code, qutationRequeat.start_date, qutationRequeat.end_date)
	print(df)
	if df is not None:
		dataArray = np.array(df).tolist()
		indicatorDataService.save_cyq_chips(qutationRequeat.type, dataArray, db)
		return myResponse.resp_200(data = np.array(df).tolist(), message="获取成功")
	return myResponse.resp_200(message="行情数据不存在",data='')


