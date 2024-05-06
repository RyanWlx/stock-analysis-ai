from app.config.tushare_config import pro
from app.models import models as mod
from sqlalchemy.orm import Session

def get_qutation(type: str, ts_code: str, start_date: str, end_date: str, offset: int=0, limit: int=1000):
	"""
	获取行情信息
	"""
	if type == 'D':
		df = pro.daily(**{
			"ts_code": ts_code,
			"start_date": start_date,
			"end_date": end_date,
			"offset": offset,
			"limit": limit
		}, fields=[
			"ts_code",
			"trade_date",
			"open",
			"high",
			"low",
			"close",
			"pre_close",
			"change",
			"pct_chg",
			"vol",
			"amount"
		])
	if type == 'W':
		df = pro.weekly(**{
			"ts_code": ts_code,
			"start_date": start_date,
			"end_date": end_date,
			"offset": offset,
			"limit": limit
		}, fields=[
			"ts_code",
			"trade_date",
			"open",
			"high",
			"low",
			"close",
			"pre_close",
			"change",
			"pct_chg",
			"vol",
			"amount"
		])
	if type == 'M':
		df = pro.monthly(**{
			"ts_code": ts_code,
			"start_date": start_date,
			"end_date": end_date,
			"offset": offset,
			"limit": limit
		}, fields=[
			"ts_code",
			"trade_date",
			"open",
			"high",
			"low",
			"close",
			"pre_close",
			"change",
			"pct_chg",
			"vol",
			"amount"
		])
	return df

def get_stk_factor():

	# 拉取数据
	df = pro.stk_factor(**{
		"ts_code": "600600.SH",
		"start_date": 20230101,
		"end_date": 20240506,
		"trade_date": "",
		"limit": 1000,
		"offset": 0
	}, fields=[
		"ts_code",
		"trade_date",
		"close",
		"open",
		"high",
		"low",
		"pre_close",
		"change",
		"pct_change",
		"vol",
		"amount",
		"adj_factor",
		"open_hfq",
		"open_qfq",
		"close_hfq",
		"close_qfq",
		"high_hfq",
		"high_qfq",
		"low_hfq",
		"low_qfq",
		"pre_close_hfq",
		"pre_close_qfq",
		"macd_dif",
		"macd_dea",
		"macd",
		"kdj_k",
		"kdj_d",
		"kdj_j",
		"rsi_6",
		"rsi_12",
		"rsi_24",
		"boll_upper",
		"boll_mid",
		"boll_lower",
		"cci"
	])
	return df

def save_qutation(type: str, data: [], db: Session):
	"""
	保存行情信息
	"""
	if len(data) == 0:
		return
	for item in data:
		if type == 'D':
			# 日线
			db_qutatuion = mod.TbDaliy()
		elif type == 'W':
			# 周线
			db_qutatuion = mod.TbWeekly()
		elif type == 'M':
			# 月线
			db_qutatuion = mod.TbMonthly()
		db_qutatuion.ts_code = item[0]
		db_qutatuion.trade_date = item[1]
		db_qutatuion.open = item[2]
		db_qutatuion.high = item[3]
		db_qutatuion.low = item[4]
		db_qutatuion.close = item[5]
		db_qutatuion.pre_close = item[6]
		db_qutatuion.change = item[7]
		db_qutatuion.pct_change = item[8]
		db_qutatuion.vol = item[9]
		db_qutatuion.amount = item[10]
		db.add(db_qutatuion)
		db.commit()
		db.refresh(db_qutatuion)
