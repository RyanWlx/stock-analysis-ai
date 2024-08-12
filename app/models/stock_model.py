from sqlalchemy import Boolean, Float
from sqlalchemy import BigInteger, Column, DECIMAL, DateTime, Index, Integer, String, Table, text
from datetime import datetime
from app.config.db_config import Base
import uuid
import json


# 数据表tb_query_record映射对象
class Daliy(Base):
    __tablename__ = 'tb_daliy'

    ts_code = Column(String(90), primary_key=True, nullable=False, comment='股票代码')
    trade_date = Column(DateTime, primary_key=True, nullable=False, comment='交易日期')
    open = Column(DECIMAL(24, 6), comment='开盘价')
    high = Column(DECIMAL(24, 6), comment='最高价')
    low = Column(DECIMAL(24, 6), comment='最低价')
    close = Column(DECIMAL(24, 6), comment='收盘价')
    pre_close = Column(DECIMAL(24, 6), comment='昨收价(前复权)')
    change = Column(DECIMAL(24, 6), comment='涨跌额')
    pct_change = Column(DECIMAL(24, 6), comment='涨跌幅(未复权)')
    vol = Column(DECIMAL(24, 6), comment='成交量(手)')
    amount = Column(DECIMAL(24, 6), comment='成交额(千元)')

    def __repr__(self):
        return f'<Daliy {self.ts_code, self.trade_date}>'

class DaliyEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__

# 数据表tb_order_record映射对象
# class Weekly(Base):
#     __tablename__ = 'tb_weekly'


# 数据表tb_query_record映射对象
# class Monthly(Base):
#     __tablename__ = 'tb_monthly'
#
#
# # 数据表tb_order_record映射对象
# class Exchange(Base):
#     __tablename__ = 'tb_exchange'
#
#
# # 数据表tb_query_record映射对象
# class Secumain(Base):
#     __tablename__ = 'tb_secumain'
#
#
# # 数据表tb_order_record映射对象
# class StkFactor(Base):
#     __tablename__ = 'tb_stk_factor'
