#导入models中的Tbdaliy模型，生成数据写入方法
from sqlalchemy import and_
from app.models.models import TbDaliy
from app.models.stock_model import Daliy as daliy
from app.models.stock_model import Secumain as secumain
from app.models.models import TbWeekly
from app.models.models import TbMonthly
from sqlalchemy.orm import Session
from sqlalchemy import String
from sqlalchemy import create_engine, and_, or_


def save_daliy(daliyInfo: TbDaliy, db: Session) -> TbDaliy:
	"""
	保存日行情信息
	"""
	db.add(daliyInfo)
	db.commit()
	db.refresh(daliyInfo)
	return daliyInfo

def save_weekly(weeklyInfo: TbWeekly, db: Session) -> TbWeekly:
	"""
	保存周行情信息
	"""
	db.add(weeklyInfo)
	db.commit()
	db.refresh(weeklyInfo)
	return weeklyInfo

def save_weekly(monthly: TbMonthly, db: Session) -> TbMonthly:
	"""
	保存月行情信息
	"""
	db.add(monthly)
	db.commit()
	db.refresh(monthly)
	return monthly

def get_history(symbol, from_, to, resolution, db: Session) -> daliy:
    """
    history
    """

	# print("99999====>",symbol,from_,to)

	# and_(
	# 	Daliy.ts_code == symbol + '.SZ',
	# 	Daliy.trade_date > from_,
	# 	Daliy.trade_date < to,
	# )
    return db.query(daliy).filter(daliy.ts_code == symbol + '.SZ').filter(daliy.trade_date > from_).filter(daliy.trade_date < to).all()

def get_search(query, type, exchange, limit, db: Session) -> secumain:
    """
    search
    """

    return db.query(secumain).filter(
		or_(
			secumain.secu_code.like('%'+query+'%'),
			secumain.secu_abbr.like('%'+query+'%'),
		)
	).limit(limit).all()

def get_symbol(symbol, db: Session) -> secumain:
    """
    search
    """

    return db.query(secumain).filter(
		or_(
			secumain.secu_code == symbol,
			secumain.secu_abbr == symbol,
		)
	).limit(1).all()