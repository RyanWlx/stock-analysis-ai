from sqlalchemy import BigInteger, Column, DECIMAL, DateTime, Index, Integer, String, Table, text
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()
metadata = Base.metadata


class TbDaliy(Base):
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


class TbExchange(Base):
    __tablename__ = 'tb_exchange'
    __table_args__ = (
        Index('idx_ex_date', 'exchange', 'cal_date', unique=True),
        {'comment': '交易所'}
    )

    exchange = Column(String(90), primary_key=True, nullable=False, comment='代码')
    cal_date = Column(DateTime, primary_key=True, nullable=False, comment='日历日期')
    is_open = Column(String(1), comment='是否交易')
    pretrade_date = Column(DateTime, comment='上个交易日')


class TbMonthly(Base):
    __tablename__ = 'tb_monthly'
    __table_args__ = (
        Index('idx_ts_date', 'ts_code', 'trade_date', unique=True),
        {'comment': '月线行情'}
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


class TbOrderRecord(Base):
    __tablename__ = 'tb_order_record'
    __table_args__ = {'comment': '支付记录'}

    id = Column(String(32), primary_key=True, comment='id')
    uid = Column(String(32), comment='用户id')
    order_uuid = Column(String(64), comment='支付流水号')
    channel = Column(Integer, comment='支付渠道')
    amount = Column(DECIMAL(24, 6), comment='支付金额')
    order_status = Column(Integer, comment='支付状态')
    order_time = Column(DateTime, comment='支付时间')
    created_time = Column(DateTime, comment='创建时间')
    updated_time = Column(DateTime, comment='修改时间')


class TbQueryRecord(Base):
    __tablename__ = 'tb_query_record'
    __table_args__ = {'comment': '查询记录'}

    id = Column(String(32), primary_key=True, comment='id')
    uid = Column(String(32), comment='用户id')
    content = Column(String(900), comment='查询内容')
    stock = Column(String(255), comment='解析股票')
    query_time = Column(DateTime, comment='查询时间')
    execute_status = Column(Integer, comment='执行状态')
    payment = Column(DECIMAL(24, 6), comment='消耗积分')
    result = Column(String(900), comment='查询结果')
    created_time = Column(DateTime, comment='创建时间')
    updated_time = Column(DateTime, comment='修改时间')


class TbSecumain(Base):
    __tablename__ = 'tb_secumain'
    __table_args__ = (
        Index('IX_SecuMain_Category', 'secu_category', 'secu_market', 'listed_state', 'listed_sector'),
        Index('IX_SecuMain_CompanyCode', 'company_code'),
        Index('IX_SecuMain_InnerCode', 'inner_code', unique=True),
        Index('IX_SecuMain_JSID', 'JSID'),
        Index('IX_SecuMain_SecuCode', 'secu_code'),
        Index('PK_SecuMain', 'ID'),
        Index('idx_InnerCode_SecuCode_SecuAbbr_Suffix', 'inner_code', 'secu_code', 'secu_abbr', 'suffix'),
        Index('idx_secid', 'sec_id'),
        {'comment': '证券信息表'}
    )

    ID = Column(BigInteger, primary_key=True)
    inner_code = Column(Integer, comment='证券内部编码')
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


class TbSmsRecord(Base):
    __tablename__ = 'tb_sms_record'
    __table_args__ = {'comment': '短信记录'}

    id = Column(String(32), primary_key=True, comment='id', default=uuid.uuid4)
    function_code = Column(Integer, nullable=False, server_default=text("'1'"), comment='功能码(1-登录 2-重置密码)')
    valid_status = Column(Integer, nullable=False, server_default=text("'0'"), comment='验证码状态(0-失效 1-有效)')
    valid_duration = Column(Integer, nullable=False, server_default=text("'600'"), comment='有效周期(秒)')
    mobile = Column(String(32), comment='用户手机号')
    valid_code = Column(String(6), comment='短信验证码')
    valid_code_time = Column(DateTime, comment='短信验证码发送时间')
    comments = Column(String(255), comment='备注')
    created_time = Column(DateTime, comment='创建时间')
    updated_time = Column(DateTime, comment='修改时间')


class TbStkFactor(Base):
    __tablename__ = 'tb_stk_factor'
    __table_args__ = (
        {'comment': '股票量化因子'}
    )

    ts_code = Column('ts_code', String(90), primary_key=True, comment='股票代码')
    trade_date = Column('trade_date', DateTime, primary_key=True, comment='交易日期')
    open = Column('open', DECIMAL(24, 6), comment='开盘价')
    high = Column('high', DECIMAL(24, 6), comment='最高价')
    low = Column('low', DECIMAL(24, 6), comment='最低价')
    close = Column('close', DECIMAL(24, 6), comment='收盘价')
    pre_close = Column('pre_close', DECIMAL(24, 6), comment='昨收价')
    change = Column('change', DECIMAL(24, 6), comment='涨跌额')
    pct_change = Column('pct_change', DECIMAL(24, 6), comment='涨跌幅(未复权)')
    vol = Column('vol', DECIMAL(24, 6), comment='成交量(手)')
    amount = Column('amount', DECIMAL(24, 6), comment='成交额(千元)')
    adj_factor = Column('adj_factor', DECIMAL(24, 6), comment='复权因子')
    open_hfq = Column('open_hfq', DECIMAL(24, 6), comment='开盘价后复权')
    open_qfq = Column('open_qfq', DECIMAL(24, 6), comment='开盘价前复权')
    close_hfq = Column('close_hfq', DECIMAL(24, 6), comment='收盘价后复权')
    close_qfq = Column('close_qfq', DECIMAL(24, 6), comment='收盘价前复权')
    high_hfq = Column('high_hfq', DECIMAL(24, 6), comment='最高价后复权')
    high_qfq = Column('high_qfq', DECIMAL(24, 6), comment='最高价前复权')
    low_hfq = Column('low_hfq', DECIMAL(24, 6), comment='最低价后复权')
    low_qfq = Column('low_qfq', DECIMAL(24, 6), comment='最低价前复权')
    pre_close_hfq = Column('pre_close_hfq', DECIMAL(24, 6), comment='昨收价后复权')
    pre_close_qfq = Column('pre_close_qfq', DECIMAL(24, 6), comment='昨收价前复权')
    macd_dif = Column('macd_dif', DECIMAL(24, 6), comment='macd_dif(基于前复权价格计算)')
    macd_dea = Column('macd_dea', DECIMAL(24, 6), comment='macd_dea')
    macd = Column('macd', DECIMAL(24, 6), comment='macd')
    kdj_k = Column('kdj_k', DECIMAL(24, 6), comment='kdj_k')
    kdj_d = Column('kdj_d', DECIMAL(24, 6), comment='kdj_d')
    kdj_j = Column('kdj_j', DECIMAL(24, 6), comment='kdj_j')
    rsi_6 = Column('rsi_6', DECIMAL(24, 6), comment='rsi_6')
    rsi_12 = Column('rsi_12', DECIMAL(24, 6), comment='rsi_12')
    rsi_24 = Column('rsi_24', DECIMAL(24, 6), comment='rsi_24')
    boll_upper = Column('boll_upper', DECIMAL(24, 6), comment='boll_upper')
    boll_mid = Column('boll_mid', DECIMAL(24, 6), comment='boll_mid')
    boll_lower = Column('boll_lower', DECIMAL(24, 6), comment='boll_lower')
    cci = Column('cci', DECIMAL(24, 6), comment='cci')


class TbUser(Base):
    __tablename__ = 'tb_user'
    __table_args__ = {'comment': '用户'}

    id = Column(String(32), primary_key=True, comment='id', default=uuid.uuid4)
    password = Column(String(20), nullable=False, comment='密码')
    mobile = Column(String(20), comment='手机号')
    nickname = Column(String(50), comment='昵称')
    level = Column(Integer, comment='等级')
    point = Column(DECIMAL(24, 6), comment='积分')
    reg_date = Column(DateTime, comment='注册日期')
    pw_status = Column(TINYINT, comment='用户密码(0-失效 1-有效 -1-重置)')
    salt = Column(String(255), comment='加密盐')
    created_time = Column(DateTime, comment='创建日期')
    updated_time = Column(DateTime, comment='修改日期')


class TbWeekly(Base):
    __tablename__ = 'tb_weekly'
    __table_args__ = (
        Index('idx_ts_date', 'ts_code', 'trade_date', unique=True),
        {'comment': '周线行情'}
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
