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
图表保存接口
1:图表新增：/charts?client=client_id&user=user_id
2:图表编辑保存：/charts?client=client_id&user=user_id&chart=chart_id
'''
@router.post("/1.1/charts")
async def postCharts(client: Union[str|None] = Query(), user: Union[str|None] = Query(), chart: Union[str|None] = Query(), name: str = Form(), content: str = Form(), symbol: str = Form(), resolution: str = Form(), Session = Depends(get_db)):
	#校验数据
	if not client:
		return myResponse.resp_400(message="client不能为空")
	if not user:
		return myResponse.resp_400(message="user不能为空")
	# if user == 'public_user_id':
	# 	return myResponse.resp_400(message="请先登录")
	#保存用户图表
	if chart is not None:
		myChart = chartRepo.set_charts_by_user_by_chartid(user, chart, name, content, symbol, resolution, Session)
		print('postCharts===>',myChart)
		if myChart is not None:
			print('postCharts===>1', myChart)
			return myResponse.resp_tdview_200(message="保存用户图表成功", data={'status': 'ok'})
		else:
			print('postCharts===>2', myChart)
			return myResponse.resp_tdview_200(message="保存用户图表失败", data={'status': 'error'})

	else:
		logger.info('content===>%s', content)
		myChart = Charts(owner_source=client, owner_id=user, name=name, symbol=symbol, resolution=resolution,
						 last_modified=datetime.now(), content=content)
		myChart = chartRepo.save_charts(myChart, Session)
		if myChart is not None:
			return myResponse.resp_tdview_200(message="charts保存成功", data={'status': 'ok', 'id': myChart.id})
		return myResponse.resp_tdview_200(message="保存用户图表失败", data={'status': 'error', 'id': null})



'''
列表图表
charts_storage_url/charts_storage_api_version/charts?client=client_id&user=user_id
ep:https://saveload.tradingview.com/1.1/charts?client=tradingview.com&user=public_user_id
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
		# data: Array
		returnChartsData = {
			'data': myCharts,
			'status': 'ok'
		}
		return myResponse.resp_tdview_200(message="charts查询成功",data=returnChartsData)
	#加载图表,根据chart获取单一图表
	else:
		myChart = chartRepo.get_chart_by_id(chart, Session)
		# data: object
		returnChartData = {
			'data': myChart,
			'status': 'ok'
		}
		return myResponse.resp_tdview_200(message="charts查询成功",data=returnChartData)


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
	chartData = chartRepo.get_chart_by_id(chart, Session)
	if not chartData:
		return myResponse.resp_400(message="图标id不存在", data={'status': 'error'})
	else:
		myChart = chartRepo.delete_charts(chartData, Session)
		returnDeleteData = {
			'status': 'ok'
		}
		return myResponse.resp_tdview_200(message="charts删除成功",data=returnDeleteData)