import json
from datetime import datetime
from typing import Union

from app.parameter.request.chartsRequest import ChartsDTO
from app.repository import study_template_repo as studytemplateRepo
from app.models.study_template_model import TbStudyTemplate as TbStudyTemplates
from fastapi import APIRouter, Depends, Query, Form
from app.parameter.response import myResponse
import numpy as np
from app.dependencies.db_depend import get_db
from sqlalchemy.orm import Session
from app.config.log_config import logger

router = APIRouter(tags=["charts_router"])

@router.post("/1.1/study_templates")
async def postStudyTempates(client: Union[str|None] = Query(), user: Union[str|None] = Query(), name: str = Form(), content: str = Form(), Session = Depends(get_db)):
	#校验数据
	if not client:
		return myResponse.resp_400(message="client不能为空")
	if not user:
		return myResponse.resp_400(message="user不能为空")
	# if user == 'public_user_id':
	# 	return myResponse.resp_400(message="请先登录")
	#保存用户图表
	logger.info('content===>%s', content)
	myTemplate = TbStudyTemplates(owner_source=client, owner_id=user, name=name,
						last_modified=datetime.now(), first_modified=datetime.now(), content=content)
	myChart = studytemplateRepo.set_template_by_template(myTemplate, client, user, name, content, Session)
	if myChart is not None:
		return myResponse.resp_tdview_200(message="study_template保存成功", data={'status': 'ok'})
	return myResponse.resp_tdview_200(message="保存用户template失败", data={'status': 'error'})


@router.get("/1.1/study_templates")
async def getStudyTempates(client: Union[str|None] = Query(), user: Union[str|None] = Query(), template: Union[str|None] = Query(default=None), Session = Depends(get_db)):
	#校验数据
	if not client:
		return myResponse.resp_400(message="client不能为空", data=client)
	if not user:
		return myResponse.resp_400(message="user不能为空", data=user)
	# if user == 'public_user_id':
	# 	return myResponse.resp_400(message="请先登录", data=user)
	#获取用户所有研究模板
	if template is None:
		myTemplates = studytemplateRepo.get_templates_by_user(client, user, Session)
		# data: Array
		if(myTemplates is None):
			myTemplates = []
		returnTemplatesData = {
			'data': myTemplates,
			'status': 'ok'
		}
		return myResponse.resp_tdview_200(message="charts查询成功",data=returnTemplatesData)
	#加载研究模板,根据template获取单一研究模板
	else:
		myTemplate = studytemplateRepo.get_template_by_template(client, user, template, Session)
		# data: object
		returnTemplateData = {
			'data': myTemplate,
			'status': 'ok'
		}
		return myResponse.resp_tdview_200(message="charts查询成功",data=returnTemplateData)

@router.delete("/1.1/study_templates")
async def deleteCharts(client: Union[str|None] = Query(), user: Union[str|None] = Query(), template: Union[str|None] = Query(), Session = Depends(get_db)):
	#校验数据
	if not client:
		return myResponse.resp_400(message="client不能为空", data=client)
	if not user:
		return myResponse.resp_400(message="user不能为空", data=user)
	# if user == 'public_user_id':
	# 	return myResponse.resp_400(message="请先登录")
	#删除研究模板
	logger.info('content===>%s',template)
	templateData = studytemplateRepo.get_template_by_template(client, user, template, Session)
	if not templateData:
		return myResponse.resp_400(message="研究模板不存在", data={'status': 'error'})
	else:
		myChart = studytemplateRepo.delete_template(client, user, template, Session)
		returnDeleteData = {
			'status': 'ok'
		}
		return myResponse.resp_tdview_200(message="charts删除成功",data=returnDeleteData)