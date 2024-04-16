DROP TABLE IF EXISTS TB_EXCHANGE;
CREATE TABLE TB_EXCHANGE(
    `exchange` VARCHAR(90) NOT NULL   COMMENT '代码' ,
    `cal_date` DATETIME NOT NULL   COMMENT '日历日期' ,
    `is_open` VARCHAR(1)    COMMENT '是否交易' ,
    `pretrade_date` DATETIME    COMMENT '上个交易日' ,
    PRIMARY KEY (exchange,cal_date)
)  COMMENT = '交易所';
CREATE UNIQUE INDEX idx_ex_date ON TB_EXCHANGE(exchange,cal_date);

DROP TABLE IF EXISTS TB_DALIY;
CREATE TABLE TB_DALIY(
    `ts_code` VARCHAR(90) NOT NULL   COMMENT '股票代码' ,
    `trade_date` DATETIME NOT NULL   COMMENT '交易日期' ,
    `open` DECIMAL(24,6)    COMMENT '开盘价' ,
    `high` DECIMAL(24,6)    COMMENT '最高价' ,
    `low` DECIMAL(24,6)    COMMENT '最低价' ,
    `close` DECIMAL(24,6)    COMMENT '收盘价' ,
    `pre_close` DECIMAL(24,6)    COMMENT '昨收价(前复权)' ,
    `change` DECIMAL(24,6)    COMMENT '涨跌额' ,
    `pct_change` DECIMAL(24,6)    COMMENT '涨跌幅(未复权)' ,
    `vol` DECIMAL(24,6)    COMMENT '成交量(手)' ,
    `amount` DECIMAL(24,6)    COMMENT '成交额(千元)' ,
    PRIMARY KEY (ts_code,trade_date)
)  COMMENT = '日线行情';
CREATE UNIQUE INDEX idx_ts_date ON TB_DALIY(ts_code,trade_date);

DROP TABLE IF EXISTS TB_WEEKLY;
CREATE TABLE TB_WEEKLY(
    `ts_code` VARCHAR(90) NOT NULL   COMMENT '股票代码' ,
    `trade_date` DATETIME NOT NULL   COMMENT '交易日期' ,
    `open` DECIMAL(24,6)    COMMENT '开盘价' ,
    `high` DECIMAL(24,6)    COMMENT '最高价' ,
    `low` DECIMAL(24,6)    COMMENT '最低价' ,
    `close` DECIMAL(24,6)    COMMENT '收盘价' ,
    `pre_close` DECIMAL(24,6)    COMMENT '昨收价(前复权)' ,
    `change` DECIMAL(24,6)    COMMENT '涨跌额' ,
    `pct_change` DECIMAL(24,6)    COMMENT '涨跌幅(未复权)' ,
    `vol` DECIMAL(24,6)    COMMENT '成交量(手)' ,
    `amount` DECIMAL(24,6)    COMMENT '成交额(千元)' ,
    PRIMARY KEY (ts_code,trade_date)
)  COMMENT = '周线行情';
CREATE UNIQUE INDEX idx_ts_date ON TB_WEEKLY(ts_code,trade_date);

DROP TABLE IF EXISTS TB_MONTHLY;
CREATE TABLE TB_MONTHLY(
    `ts_code` VARCHAR(90) NOT NULL   COMMENT '股票代码' ,
    `trade_date` DATETIME NOT NULL   COMMENT '交易日期' ,
    `open` DECIMAL(24,6)    COMMENT '开盘价' ,
    `high` DECIMAL(24,6)    COMMENT '最高价' ,
    `low` DECIMAL(24,6)    COMMENT '最低价' ,
    `close` DECIMAL(24,6)    COMMENT '收盘价' ,
    `pre_close` DECIMAL(24,6)    COMMENT '昨收价(前复权)' ,
    `change` DECIMAL(24,6)    COMMENT '涨跌额' ,
    `pct_change` DECIMAL(24,6)    COMMENT '涨跌幅(未复权)' ,
    `vol` DECIMAL(24,6)    COMMENT '成交量(手)' ,
    `amount` DECIMAL(24,6)    COMMENT '成交额(千元)' ,
    PRIMARY KEY (ts_code,trade_date)
)  COMMENT = '月线行情';
CREATE UNIQUE INDEX idx_ts_date ON TB_MONTHLY(ts_code,trade_date);

DROP TABLE IF EXISTS TB_STK_FACTOR;
CREATE TABLE TB_STK_FACTOR(
    `ts_code` VARCHAR(90)    COMMENT '股票代码' ,
    `trade_date` DATETIME    COMMENT '交易日期' ,
    `open` DECIMAL(24,6)    COMMENT '开盘价' ,
    `high` DECIMAL(24,6)    COMMENT '最高价' ,
    `low` DECIMAL(24,6)    COMMENT '最低价' ,
    `close` DECIMAL(24,6)    COMMENT '收盘价' ,
    `pre_close` DECIMAL(24,6)    COMMENT '昨收价' ,
    `change` DECIMAL(24,6)    COMMENT '涨跌额' ,
    `pct_change` DECIMAL(24,6)    COMMENT '涨跌幅(未复权)' ,
    `vol` DECIMAL(24,6)    COMMENT '成交量(手)' ,
    `amount` DECIMAL(24,6)    COMMENT '成交额(千元)' ,
    `adj_factor` DECIMAL(24,6)    COMMENT '复权因子' ,
    `open_hfq` DECIMAL(24,6)    COMMENT '开盘价后复权' ,
    `open_qfq` DECIMAL(24,6)    COMMENT '开盘价前复权' ,
    `close_hfq` DECIMAL(24,6)    COMMENT '收盘价后复权' ,
    `close_qfq` DECIMAL(24,6)    COMMENT '收盘价前复权' ,
    `high_hfq` DECIMAL(24,6)    COMMENT '最高价后复权' ,
    `high_qfq` DECIMAL(24,6)    COMMENT '最高价前复权' ,
    `low_hfq` DECIMAL(24,6)    COMMENT '最低价后复权' ,
    `low_qfq` DECIMAL(24,6)    COMMENT '最低价前复权' ,
    `pre_close_hfq` DECIMAL(24,6)    COMMENT '昨收价后复权' ,
    `pre_close_qfq` DECIMAL(24,6)    COMMENT '昨收价前复权' ,
    `macd_dif` DECIMAL(24,6)    COMMENT 'macd_dif(基于前复权价格计算)' ,
    `macd_dea` DECIMAL(24,6)    COMMENT 'macd_dea' ,
    `macd` DECIMAL(24,6)    COMMENT 'macd' ,
    `kdj_k` DECIMAL(24,6)    COMMENT 'kdj_k' ,
    `kdj_d` DECIMAL(24,6)    COMMENT 'kdj_d' ,
    `kdj_j` DECIMAL(24,6)    COMMENT 'kdj_j' ,
    `rsi_6` DECIMAL(24,6)    COMMENT 'rsi_6' ,
    `rsi_12` DECIMAL(24,6)    COMMENT 'rsi_12' ,
    `rsi_24` DECIMAL(24,6)    COMMENT 'rsi_24' ,
    `boll_upper` DECIMAL(24,6)    COMMENT 'boll_upper' ,
    `boll_mid` DECIMAL(24,6)    COMMENT 'boll_mid' ,
    `boll_lower` DECIMAL(24,6)    COMMENT 'boll_lower' ,
    `cci` DECIMAL(24,6)    COMMENT 'cci'
)  COMMENT = '量化因子';
CREATE UNIQUE INDEX idx_ts_date ON TB_STK_FACTOR(ts_code,trade_date);



