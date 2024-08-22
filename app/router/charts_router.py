import json
from datetime import datetime
from typing import Union

from app.parameter.request.chartsRequest import ChartsDTO as ChartsDTO
from app.service import stock_service as stockService
from fastapi import APIRouter, Depends, Query, Form
from app.parameter.response import myResponse
import numpy as np
from app.dependencies.db_depend import get_db
from sqlalchemy.orm import Session
from app.config.log_config import logger

router = APIRouter(tags=["charts_router"])
# https://saveload.tradingview.com/1.1/charts?client=tradingview.com&user=public_user_id
@router.post("/1.1/charts")
async def postCharts(client: Union[str|None] = Query(), user: Union[str|None] = Query(), name: str = Form(), content: str = Form(), symbol: str = Form(), resolution: str = Form(), Session = Depends(get_db)):
	#获取股票行情数据
	print("client===>",client)
	print("user===>",user)
	print("content===>",content)
	print("name===>",name)
	print("symbol===>",symbol)
	print("resolution===>",resolution)
	# print("queryparams===>", client,user)
	chartsDTO = ChartsDTO(name=name, content=content, symbol=symbol, resolution=resolution)
	return myResponse.resp_200(message="charts",data=chartsDTO.__dict__)
	# df = stockService.get_stk_factor(qutationRequeat.ts_code+'.SZ', qutationRequeat.start_date, qutationRequeat.end_date)
	print(df)
	if df is not None:
		dataArray = np.array(df).tolist()
		stockService.save_stk_factor(qutationRequeat.type, dataArray, db)
		return myResponse.resp_200(data = np.array(df).tolist(), message="获取成功")
	return myResponse.resp_200(message="行情数据不存在",data='')