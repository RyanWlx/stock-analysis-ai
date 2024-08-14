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

router = APIRouter(tags=["stock_router"])

@router.post("/stock/getStockQuoteByType")
async def getStockQuoteByType(qutationRequeat: QutationDTO, db: Session = Depends(get_db)):
	#获取股票行情数据
	df = stockService.get_qutation(qutationRequeat.type, qutationRequeat.ts_code, qutationRequeat.start_date, qutationRequeat.end_date)
	if df is not None:
		dataArray = np.array(df).tolist()
		logger.info("数据获取成功: {}", dataArray)
		# stockService.save_qutation(qutationRequeat.type, dataArray, db)
		return myResponse.resp_200(data = np.array(df).tolist(), message="获取成功")
	return myResponse.resp_200(message="行情数据不存在",data='')

@router.post("/stock/getStockFactor")
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

@router.get("/history")
async def getStockQuoteHistory(symbol: Union[str, None] = None, from_: str= Query(None, alias="from"), to: Union[str, None] = None, resolution: Union[str, None] = None, db: Session = Depends(get_db)):
	#获取股票行情数据
	from_ = datetime.fromtimestamp(int(from_))
	to = datetime.fromtimestamp(int(to))
	dbData = stockRepo.get_history(symbol, from_, to,resolution, db)
	print("history-dbData====>",dbData)
	print("history-type====>",type(dbData))
	# print("history-value====>", dbData['trade_date'])
	if dbData is not None:
		# dataArray = json.loads(dataArray, cls=DaliyEncoder)
		t = []
		h = []
		c = []
		o = []
		l = []
		v = []

		for element in dbData:
			print(element)
			t.append(int(element.trade_date.timestamp()))
			h.append(element.high)
			c.append(element.close)
			o.append(element.open)
			l.append(element.low)
			v.append(element.vol)

		_data = {
			"t": t,
			"c": c,
			"o": o,
			"h": h,
			"l": l,
			"v": v,
			"s": 'ok'
		}
		print("history-_data====>", h)
		logger.info("数据获取成功: {}", dbData, _data)
		return myResponse.resp_tdview_200(data = _data, message="获取成功")
	return myResponse.resp_tdview_200(message="不存在", data='')

@router.get("/config")
async def getChartConfig():
	#获取图标配置数据
	returnData = {
		"supported_resolutions": ["D","2D","3D","W","3W","M","6M"],
		"supports_group_request": False,
		"supports_marks": True,
		"supports_search": True,
		"supports_time": True,
		"supports_timescale_marks": True,
		"exchanges": [
			{
				"value": "",
				"name": "All Exchanges",
				"desc": ""
			},
			{
				"value": "NasdaqNM",
				"name": "NasdaqNM",
				"desc": "NasdaqNM"
			},
			{
				"value": "NYSE",
				"name": "NYSE",
				"desc": "NYSE"
			},
			{
				"value": "NCM",
				"name": "NCM",
				"desc": "NCM"
			},
			{
				"value": "NGM",
				"name": "NGM",
				"desc": "NGM"
			},
			{
				"value": "SH",
				"name": "上海证券交易所",
				"desc": "SH"
			},
			{
				"value": "SZ",
				"name": "深圳证券交易所",
				"desc": "SZ"
			},
			{
				"value": "BJ",
				"name": "北京证券交易所",
				"desc": "BJ"
			},
		],
		"symbols_types": [
		  {
			"name": "All types",
			"value": ""
		  },
		  {
			"name": "Stock",
			"value": "stock"
		  },
		  {
			"name": "Index",
			"value": "index"
		  }
		]

	}
	logger.info("数据获取成功: {}", returnData)
	return myResponse.resp_tdview_200(message="数据获取成功",data=returnData)

@router.get("/symbols")
async def getChartConfig(symbol: Union[str, None] = None, db: Session = Depends(get_db)):
	#获取图标配置数据
	returnData = {
		"name": "002049",
		"exchange-traded": "SH",
		"exchange-listed": "SH",
		"timezone": "Asia/Shanghai",
		"minmov": 1,
		"minmov2": 0,
		"pointvalue": 1,
		"session": "0930-1630",
		"has_intraday": False,
		"visible_plots_set": "ohlcv",
		"description": "紫光国微",
		"type": "stock",
		"supported_resolutions": ["D", "2D", "3D", "W", "3W", "M", "6M"],
		"pricescale": 100,
		"ticker": "002049",
		"logo_urls": ["https://s3-symbol-logo.tradingview.com/apple.svg"],
		"exchange_logo": "https://s3-symbol-logo.tradingview.com/country/US.svg"
	}
	logger.info("数据获取成功: {}", returnData)
	return myResponse.resp_tdview_200(message="数据获取成功", data=returnData)

@router.get("/symbol_info")
async def getSymbolInfo(symbol: Union[str, None] = None, db: Session = Depends(get_db)):
	#获取图标配置数据
	returnData = {
		"name":"002049",
		"exchange-traded":"SH",
		"exchange-listed":"SH",
		"timezone":"Asia/Shanghai",
		"minmov":1,
		"minmov2":0,
		"pointvalue":1,
		"session":"0930-1630",
		"has_intraday":False,
		"visible_plots_set":"ohlcv",
		"description":"紫光国微",
		"type":"stock",
		"supported_resolutions":["D","2D","3D","W","3W","M","6M"],
		"pricescale":100,
		"ticker":"002049",
		"logo_urls":["https://s3-symbol-logo.tradingview.com/apple.svg"],
		"exchange_logo":"https://s3-symbol-logo.tradingview.com/country/US.svg"
	}
	logger.info("数据获取成功: {}", returnData)
	return myResponse.resp_tdview_200(message="数据获取成功",data=returnData)
@router.get("/time")
async def getStockQuoteHistory():
	return myResponse.resp_200(message="获取成功",data='')



@router.get("/search")
async def search(symbol: Union[str, None] = None, db: Session = Depends(get_db)):
	#获取图标配置数据
	returnData = {
		"supports_search": True,
		"supports_group_request": False,
		"supported_resolutions": ["1D", "1W", "1M"],
		"supports_marks": False,
		"supports_time": True
	}
	logger.info("数据获取成功: {}", returnData)
	return myResponse.resp_200(message="数据获取成功",data=returnData)
