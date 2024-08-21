import json
from datetime import datetime
from typing import Union

from app.models.stock_model import DaliyEncoder
from app.service import stock_service as stockService
from fastapi import APIRouter, Depends, Query
from app.parameter.request.qutationRequest import QutationDTO
from app.parameter.response import myResponse
import numpy as np
from app.dependencies.db_depend import get_db
from sqlalchemy.orm import Session
from app.config.log_config import logger
import app.repository.stock_repo as stockRepo

router = APIRouter(tags=["charts_router"])
# https://saveload.tradingview.com/1.1/charts?client=tradingview.com&user=public_user_id
@router.post("/1.1/charts")
async def getStockFactor(qutationRequeat: QutationDTO, db: Session = Depends(get_db)):
	#获取股票行情数据
	print("qutationRequeat===>",qutationRequeat)
	df = stockService.get_stk_factor(qutationRequeat.ts_code+'.SZ', qutationRequeat.start_date, qutationRequeat.end_date)
	print(df)
	if df is not None:
		dataArray = np.array(df).tolist()
		stockService.save_stk_factor(qutationRequeat.type, dataArray, db)
		return myResponse.resp_200(data = np.array(df).tolist(), message="获取成功")
	return myResponse.resp_200(message="行情数据不存在",data='')