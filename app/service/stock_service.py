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

def get_stk_factor(ts_code: str, start_date: str, end_date: str, offset: int=0, limit: int=1000):

	# 拉取数据
	df = pro.stk_factor(**{
		"ts_code": ts_code,
		"start_date": start_date,
		"end_date": end_date,
		"trade_date": "",
		"limit": limit,
		"offset": offset
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

def save_stk_factor(type: str, data: [], db: Session):
	"""
	保存量化因子信息
	"""
	if len(data) == 0:
		return
	for item in data:
		db_stk_factor = mod.TbStkFactor()
		# 量化因子对象赋值
		db_stk_factor.ts_code = item[0]
		db_stk_factor.trade_date = item[1]
		db_stk_factor.close = item[2]
		db_stk_factor.open = item[3]
		db_stk_factor.high = item[4]
		db_stk_factor.low = item[5]
		db_stk_factor.pre_close = item[6]
		db_stk_factor.change = item[7]
		db_stk_factor.pct_change = item[8]
		db_stk_factor.vol = item[9]
		db_stk_factor.amount = item[10]
		db_stk_factor.adj_factor = item[11]
		db_stk_factor.open_hfq = item[12]
		db_stk_factor.open_qfq = item[13]
		db_stk_factor.close_hfq = item[14]
		db_stk_factor.close_qfq = item[15]
		db_stk_factor.high_hfq = item[16]
		db_stk_factor.high_qfq = item[17]
		db_stk_factor.low_hfq = item[18]
		db_stk_factor.low_qfq = item[19]
		db_stk_factor.pre_close_hfq = item[20]
		db_stk_factor.pre_close_qfq = item[21]
		db_stk_factor.macd_dif = item[22]
		db_stk_factor.macd_dea = item[23]
		db_stk_factor.macd = item[24]
		db_stk_factor.kdj_k = item[25]
		db_stk_factor.kdj_d = item[26]
		db_stk_factor.kdj_j = item[27]
		db_stk_factor.rsi_6 = item[28]
		db_stk_factor.rsi_12 = item[29]
		db_stk_factor.rsi_24 = item[30]
		db_stk_factor.boll_upper = item[31]
		db_stk_factor.boll_mid = item[32]
		db_stk_factor.boll_lower = item[33]
		db_stk_factor.cci = item[34]
		# 保存数据
		db.add(db_stk_factor)
		db.commit()
		db.refresh(db_stk_factor)
