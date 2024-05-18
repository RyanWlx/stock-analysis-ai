from app.config.tushare_config import pro
from app.models import models as mod
from sqlalchemy.orm import Session

def get_cyq_chips(ts_code: str, start_date: str, end_date: str, offset: int=0, limit: int=1000):

	# 拉取数据
	df = pro.cyq_chips(**{
		"ts_code": ts_code,
		"start_date": start_date,
		"end_date": end_date,
		"trade_date": "",
		"limit": limit,
		"offset": offset
	}, fields=[
		"ts_code",
		"trade_date",
		"price",
		"percent",
	])
	return df

def save_cyq_chips(type: str, data: [], db: Session):
	"""
	保存每日的筹码分布情况
	"""
	if len(data) == 0:
		return
	for item in data:
		db_cyq_chips = mod.TbCyqChips()
		# 量化因子对象赋值
		db_cyq_chips.ts_code = item[0]
		db_cyq_chips.trade_date = item[1]
		db_cyq_chips.price = item[2]
		db_cyq_chips.percent = item[3]
		# 保存数据
		db.add(db_cyq_chips)
		db.commit()
		db.refresh(db_cyq_chips)
