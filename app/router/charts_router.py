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
	# if user == 'public_user_id':
	# 	return myResponse.resp_400(message="请先登录")
	#保存用户图表
	logger.info('content===>%s',content)
	myChart = Charts(owner_source=client, owner_id=user, name=name, symbol=symbol, resolution=resolution, last_modified=datetime.now(), content=content)
	myChart = chartRepo.save_charts(myChart, Session)
	return myResponse.resp_tdview_200(message="charts保存成功",data=myChart)


'''
图标获取接口
'''
@router.get("/1.1/charts")
async def getCharts(client: Union[str|None] = Query(), user: Union[str|None] = Query(), chart: Union[str|None] = Query(default=None), Session = Depends(get_db)):
	#校验数据
	if not client:
		return myResponse.resp_400(message="client不能为空", data=client)
	if not user:
		return myResponse.resp_400(message="user不能为空", data=user)
	# if user == 'public_user_id':
	# 	return myResponse.resp_400(message="请先登录", data=user)
	#获取用户图表列表
	if chart is None:
		myCharts = chartRepo.get_charts_by_user(user, Session)
		return myResponse.resp_tdview_200(message="charts查询成功",data=myCharts)
	else:
		myChart = chartRepo.get_chart_by_id(chart, Session)
		return myResponse.resp_tdview_200(message="charts查询成功",data=myChart)


'''
图标删除接口
'''
@router.delete("/1.1/charts")
async def deleteCharts(client: Union[str|None] = Query(), user: Union[str|None] = Query(), chart: Union[str|None] = Query(), Session = Depends(get_db)):
	#校验数据
	if not client:
		return myResponse.resp_400(message="client不能为空", data=client)
	if not user:
		return myResponse.resp_400(message="user不能为空", data=user)
	# if user == 'public_user_id':
	# 	return myResponse.resp_400(message="请先登录")
	#删除用户图表
	logger.info('content===>%s',chart)
	chart = chartRepo.get_chart_by_id(chart, Session)
	if not chart:
		return myResponse.resp_400(message="图标id不存在", data=chart)
	else:
		myChart = chartRepo.delete_charts(chart, Session)
		return myResponse.resp_tdview_200(message="charts删除成功",data=myChart)