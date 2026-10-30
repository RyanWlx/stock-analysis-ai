#导入models中的Tbdaliy模型，生成数据写入方法
from sqlalchemy import and_
from app.models.models import TbDaliy
from app.models.models import TbMark
from app.models.stock_model import Daliy as daliy
from app.models.stock_model import Secumain as secumain
from app.models.models import TbWeekly
from app.models.models import TbMonthly
from app.models.models import TbStkFactor as tbStkFactor
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import pandas as pd
import app.service.factor_service as fs
from app.config.log_config import logger
import json as json
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
    quotations = db.query(daliy).filter(or_(
	    daliy.ts_code == symbol + '.SZ',
	    daliy.ts_code == symbol + '.SH',
	    daliy.ts_code == symbol + '.BJ',
    )).filter(daliy.trade_date > from_).filter(daliy.trade_date < to).all()

    quotations_all = db.query(daliy).filter(or_(
	    daliy.ts_code == symbol + '.SZ',
	    daliy.ts_code == symbol + '.SH',
	    daliy.ts_code == symbol + '.BJ',
    )).all()
	# 检查symbol是否包含_
    if symbol.find('_') != -1 and quotations_all:
        quotation_list = []
        quotation = {
			"trade_date": "",
			"close": 0,
			"open": 0,
			"high": 0,
			"low": 0,
			"volume": 0,
	        "amount": 0,
	        "ts_code": ""
		}
        for item in quotations:
            quotation["close"] = item.close
            quotation["open"] = item.open
            quotation["high"] = item.high
            quotation["low"] = item.low
            quotation["volume"] = item.vol
            quotation["trade_date"] = item.trade_date
            quotation["amount"] = item.amount
            quotation["ts_code"] = item.ts_code
            quotation_list.append(quotation)
        df = pd.DataFrame(quotation_list)
        xg = fs.strategy_bottom_picking(df)
        logger.info("xg:", xg)
	    #用xg替换quotations中的close的值
        for i in range(len(quotations)):
            quotations_all[i].close = xg[i]
    return quotations

def get_history_from_factor(symbol, from_, to, resolution, db: Session) -> tbStkFactor:
    """
    history
    """

	# print("99999====>",symbol,from_,to)
    quotations = db.query(tbStkFactor).filter(or_(
	    tbStkFactor.ts_code == symbol + '.SZ',
	    tbStkFactor.ts_code == symbol + '.SH',
	    tbStkFactor.ts_code == symbol + '.BJ',
    )).filter(tbStkFactor.trade_date > from_).filter(tbStkFactor.trade_date < to).all()

    quotations_all = db.query(tbStkFactor).filter(or_(
	    tbStkFactor.ts_code == symbol + '.SZ',
	    tbStkFactor.ts_code == symbol + '.SH',
	    tbStkFactor.ts_code == symbol + '.BJ',
    )).all()
	# 检查symbol是否包含_
    if symbol.find('_') != -1 and quotations_all:
        quotation_list = []
        quotation = {
			"trade_date": "",
			"close": 0,
			"open": 0,
			"high": 0,
			"low": 0,
			"volume": 0,
	        "amount": 0,
	        "ts_code": ""
		}
        for item in quotations:
            quotation["close"] = item.close
            quotation["open"] = item.open
            quotation["high"] = item.high
            quotation["low"] = item.low
            quotation["volume"] = item.vol
            quotation["trade_date"] = item.trade_date
            quotation["amount"] = item.amount
            quotation["ts_code"] = item.ts_code
            quotation_list.append(quotation)
        df = pd.DataFrame(quotation_list)
        xg = fs.strategy_bottom_picking(df)
        logger.info("xg:", xg)
	    #用xg替换quotations中的close的值
        for i in range(len(quotations)):
            quotations_all[i].close = xg[i]
    return quotations
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

# 获取股票列表
def get_stock_list_all(db: Session) -> secumain:
    """
    根据股票代码全称查询股票代码列表
    """
    stsm = (select(secumain.full_code).filter(and_(
	               or_(secumain.listed_sector == 1, secumain.listed_sector == 6, secumain.listed_sector == 7, secumain.listed_sector == 8),
                   or_(secumain.listed_state == 1, secumain.listed_state == 3, secumain.listed_state == 9),
                   or_(secumain.secu_category == 1, secumain.secu_category == 3, secumain.secu_category == 51),
                   or_(secumain.suffix == '.BJ', secumain.suffix == '.SZ', secumain.suffix == '.SH'))))
			# filter(or_(secumain.suffix == '.SZ', secumain.suffix == '.SH', secumain.suffix == '.BJ')))

    result = db.execute(stsm)
    return result.all()


def get_marks(symbol, from_, to, resolution, db: Session):
    """
    K线标记（TradingView getMarks）
    """
    return db.query(TbMark).filter(
        or_(
            TbMark.ts_code == symbol + '.SZ',
            TbMark.ts_code == symbol + '.SH',
            TbMark.ts_code == symbol + '.BJ',
        ),
        TbMark.mark_kind == 'bar',
    ).filter(TbMark.mark_time > from_).filter(TbMark.mark_time < to).all()


def get_timescale_marks(symbol, from_, to, resolution, db: Session):
    """
    时间轴标记（TradingView getTimescaleMarks）
    """
    return db.query(TbMark).filter(
        or_(
            TbMark.ts_code == symbol + '.SZ',
            TbMark.ts_code == symbol + '.SH',
            TbMark.ts_code == symbol + '.BJ',
        ),
        TbMark.mark_kind == 'timescale',
    ).filter(TbMark.mark_time > from_).filter(TbMark.mark_time < to).all()


def get_history_weekly(symbol, from_, to, countback, db: Session):
    """
    周线历史（TradingView /history，resolution=W/3W）。
    支持 countback：返回「trade_date <= to」的最近 N 根（升序），优先级高于 from。
    """
    return _get_period_bars(TbWeekly, symbol, from_, to, countback, db)


def get_history_monthly(symbol, from_, to, countback, db: Session):
    """
    月线历史（TradingView /history，resolution=M/6M）。
    支持 countback：返回「trade_date <= to」的最近 N 根（升序），优先级高于 from。
    """
    return _get_period_bars(TbMonthly, symbol, from_, to, countback, db)


def _get_period_bars(model, symbol, from_, to, countback, db: Session):
    """
    按周期表（周线/月线）查询 K 线，字段与日线 /history 对齐（open/high/low/close/vol）。
    countback 存在(>0)时：取 trade_date <= to 的最近 countback 根，倒序取前 N 再反转为升序，忽略 from；
    否则：取 (from, to) 开区间内数据，升序。
    """
    q = db.query(model).filter(or_(
        model.ts_code == symbol + '.SZ',
        model.ts_code == symbol + '.SH',
        model.ts_code == symbol + '.BJ',
    ))
    if countback and countback > 0:
        rows = q.filter(model.trade_date <= to)\
                .order_by(model.trade_date.desc())\
                .limit(countback).all()
        rows = list(reversed(rows))
        return rows
    return q.filter(model.trade_date > from_)\
            .filter(model.trade_date < to)\
            .order_by(model.trade_date.asc()).all()