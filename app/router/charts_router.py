import json
from datetime import datetime
from typing import Union

from app.parameter.request.chartsRequest import ChartsDTO
from app.repository import chart_repo as chartRepo
from app.models.charts_model import TbCharts as Charts
from fastapi import APIRouter, Depends, Query, Form
from app.parameter.response import myResponse
import numpy as np
from app.dependencies.db_depend import get_db
from sqlalchemy.orm import Session
from app.config.log_config import logger

router = APIRouter(tags=["charts_router"])

'''
图标保存接口
'''
@router.post("/1.1/charts")
async def postCharts(client: Union[str|None] = Query(), user: Union[str|None] = Query(), name: str = Form(), content: str = Form(), symbol: str = Form(), resolution: str = Form(), Session = Depends(get_db)):
	#校验数据
	if not client:
		return myResponse.resp_400(message="client不能为空")
	if not user:
		return myResponse.resp_400(message="user不能为空")
	if user == 'public_user_id':
		return myResponse.resp_400(message="请先登录")
	#保存用户图表
	print("client===>",client)
	print("user===>",user)
	print("content===>",content)
	print("name===>",name)
	print("symbol===>",symbol)
	print("resolution===>",resolution)
	myChart = Charts(owner_source=client, owner_id=user, name=name, symbol=symbol, resolution=resolution, last_modified=datetime.now(), content=content)
	myChart = chartRepo.save_charts(myChart, Session)
	# chartDTO = ChartsDTO(name=myChart.name, symbol=myChart.symbol, resolution=myChart.resolution, content=myChart.content, lastModified=myChart.last_modified, id=myChart.id)
	return myResponse.resp_tdview_200(message="charts保存成功",data=myChart)