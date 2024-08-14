from sqlalchemy import Boolean, Float
from sqlalchemy import BigInteger, Column, DECIMAL, DateTime, Index, Integer, String, Table, text
from datetime import datetime
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR
from app.config.db_config import Base
import uuid
import json


# 数据表tb_query_record映射对象

class Secumain(Base):
    __tablename__ = 'tb_secumain'
    __table_args__ = (
        Index('IX_SecuMain_Category', 'secu_category', 'secu_market', 'listed_state', 'listed_sector'),
        Index('IX_SecuMain_CompanyCode', 'company_code'),
        Index('IX_SecuMain_InnerCode', 'inner_coe', unique=True),
        Index('IX_SecuMain_JSID', 'JSID'),
        Index('IX_SecuMain_SecuCode', 'secu_code'),
        Index('PK_SecuMain', 'ID'),
        Index('idx_InnerCode_SecuCode_SecuAbbr_Suffix', 'inner_coe', 'secu_code', 'secu_abbr', 'suffix'),
        Index('idx_secid', 'sec_id'),
        {'comment': '证券信息表'}
    )

    ID = Column(BigInteger, primary_key=True)
    inner_coe = Column(Integer, comment='证券内部编码')
    company_code = Column(Integer, comment='公司代码')
    secu_code = Column(VARCHAR(30), comment='证券代码')
    secu_abbr = Column(VARCHAR(100), comment='证券简称')
    chi_spelling = Column(VARCHAR(100), comment='拼音证券简称')
    secu_market = Column(Integer, comment='证券市场，枚举：10-上海期货交易所，13-大连商品交易所，15-郑州商品交易所，17-广州期货交易所，51-中国金融期货交易所，71-柜台交易市场，72-香港联交所，76-美国证券交易所，77-美国纳斯达克证券交易所，78-纽约证券交易所，81-三板市场，83-上海证券交易所，84-其他市场，89-银行间债券市场，90-深圳证券交易所，360-纽交所群岛交易所(NYSE Arca)，460-美国OTC(OTCBB和OtherOTC)， -10:场外基金(自定义类型)参见聚源文档 -20：每市市场(自定义类型) ')
    secu_category = Column(Integer, comment='证券类别，枚举：1-A股，2-B股，3-H股，4-大盘，9-可转换债券，13-投资基金，15-深市代理沪市股票，16-沪市代理深市股票，41-中国存托凭证，51-港股，53-红筹股，62-海外ETF，74-美股普通股，75-美股存托凭证，2001-国债，2003-央行票据，2005-企业债，2008-资产支持证券，2009-买断式回购，2010-质押式回购，2012-短期融资券，2018-公司债，2020-中期票据，2021-地方政府债，2022-集合票据，2023-其它债券，2024-债券借贷，2007001-政策性金融债，2007002-商业银行债，2007003-非银行金融债，2007004-国际机构债，2007005-证券公司债，2010004-新质押式国债回购，2010005-质押式协议回购，2010006-质押式三方回购，2010007-存款类机构质押式回购，2010008-质押式报价回购，7001-商品期货，7002001-外汇期货，7002002-利率期货，7002003-股票指数期货，7002004-债券期货，7002005-股票期货，7002006-商品指数期货')
    listed_sector = Column(Integer, comment='上市板块 1-主板，2-中小企业板，3-三板，4-其他，5-大宗交易系统，6-创业板，7-科创板，8-北交所股票')
    listed_date = Column(DateTime, comment='上市日期')
    listed_state = Column(Integer, comment='上市状态，枚举：1-上市，2-预上市，3-暂停，4-上市失败，5-终止，9-其他')
    delisting_date = Column(DateTime, comment='退市日期')
    JSID = Column(BigInteger, comment='jsid')
    sec_id = Column(VARCHAR(32), comment='同花顺证券id')
    industry_code = Column(Integer, comment='行业代码')
    industry_name = Column(VARCHAR(200), comment='行业名称')
    code_by_agent = Column(VARCHAR(60), comment='转换码')
    suffix = Column(VARCHAR(20), comment='后缀（也可代表上市所在国家）')
    created_time = Column(DateTime, comment='创建时间')
    update_time = Column(DateTime, comment='更新时间')

    def __repr__(self):
        return f'<Secumain {self.secu_code, self.secu_market, self.secu_abbr}>'

class Daliy(Base):
    __tablename__ = 'tb_daliy'
    __table_args__ = (
        Index('idx_ts_date', 'ts_code', 'trade_date', unique=True),
        {'comment': '日线行情'}
    )
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

class DaliyDTO():
    ts_code: str
    trade_dat: str
    open: DECIMAL(24, 6)
    high: DECIMAL(24, 6)
    low: DECIMAL(24, 6)
    close: DECIMAL(24, 6)
    pre_close: DECIMAL(24, 6)
    change: DECIMAL(24, 6)
    pct_change: DECIMAL(24, 6)
    vol: DECIMAL(24, 6)
    amount: DECIMAL(24, 6)

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
