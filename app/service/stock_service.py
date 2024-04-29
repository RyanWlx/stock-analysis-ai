from app.config.tushare_config import pro

def getQutation(ts_code: str, start_date: str, end_date: str, offset: int=0, limit: int=1000):
	"""
	获取行情信息
	"""
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
	return df