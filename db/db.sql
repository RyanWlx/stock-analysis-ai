-- auto-generated definition
create table tb_charts
(
    id            int auto_increment comment 'id'
        primary key,
    owner_source  varchar(200) null,
    content       json         null comment '昵称',
    name          varchar(200) null,
    symbol        varchar(50)  null,
    resolution    varchar(10)  null comment '创建日期',
    last_modified datetime     null comment '修改日期',
    owner_id      varchar(200) null
)
    comment 'charts' engine = InnoDB;

-- auto-generated definition
create table tb_cyq_chips
(
    ts_code    varchar(90)    null comment '股票代码',
    trade_date datetime       null comment '交易日期',
    price      decimal(24, 6) null comment '成本价格',
    percent    decimal(24, 6) null comment '价格占比（%）',
    constraint idx_ts_date
        unique (ts_code, trade_date)
)
    comment '每日筹码分布' engine = InnoDB;

-- auto-generated definition
create table tb_daliy
(
    ts_code    varchar(90)    not null comment '股票代码',
    trade_date datetime       not null comment '交易日期',
    open       decimal(24, 6) null comment '开盘价',
    high       decimal(24, 6) null comment '最高价',
    low        decimal(24, 6) null comment '最低价',
    close      decimal(24, 6) null comment '收盘价',
    pre_close  decimal(24, 6) null comment '昨收价(前复权)',
    `change`   decimal(24, 6) null comment '涨跌额',
    pct_change decimal(24, 6) null comment '涨跌幅(未复权)',
    vol        decimal(24, 6) null comment '成交量(手)',
    amount     decimal(24, 6) null comment '成交额(千元)',
    primary key (ts_code, trade_date),
    constraint idx_ts_date
        unique (ts_code, trade_date)
)
    comment '日线行情' engine = InnoDB;

-- auto-generated definition
create table tb_exchange
(
    exchange      varchar(90) not null comment '代码',
    cal_date      datetime    not null comment '日历日期',
    is_open       varchar(1)  null comment '是否交易',
    pretrade_date datetime    null comment '上个交易日',
    primary key (exchange, cal_date),
    constraint idx_ex_date
        unique (exchange, cal_date)
)
    comment '交易所' engine = InnoDB;

-- auto-generated definition
create table tb_monthly
(
    ts_code    varchar(90)    not null comment '股票代码',
    trade_date datetime       not null comment '交易日期',
    open       decimal(24, 6) null comment '开盘价',
    high       decimal(24, 6) null comment '最高价',
    low        decimal(24, 6) null comment '最低价',
    close      decimal(24, 6) null comment '收盘价',
    pre_close  decimal(24, 6) null comment '昨收价(前复权)',
    `change`   decimal(24, 6) null comment '涨跌额',
    pct_change decimal(24, 6) null comment '涨跌幅(未复权)',
    vol        decimal(24, 6) null comment '成交量(手)',
    amount     decimal(24, 6) null comment '成交额(千元)',
    primary key (ts_code, trade_date),
    constraint idx_ts_date
        unique (ts_code, trade_date)
)
    comment '月线行情' engine = InnoDB;

-- auto-generated definition
create table tb_order_record
(
    id           varchar(32)    not null comment 'id'
        primary key,
    uid          varchar(32)    null comment '用户id',
    order_uuid   varchar(64)    null comment '支付流水号',
    channel      int            null comment '支付渠道',
    amount       decimal(24, 6) null comment '支付金额',
    order_status int            null comment '支付状态',
    order_time   datetime       null comment '支付时间',
    created_time datetime       null comment '创建时间',
    updated_time datetime       null comment '修改时间'
)
    comment '支付记录' engine = InnoDB;

-- auto-generated definition
create table tb_query_record
(
    id             varchar(32)    not null comment 'id'
        primary key,
    uid            varchar(32)    null comment '用户id',
    content        varchar(900)   null comment '查询内容',
    stock          varchar(255)   null comment '解析股票',
    query_time     datetime       null comment '查询时间',
    execute_status int            null comment '执行状态',
    payment        decimal(24, 6) null comment '消耗积分',
    result         varchar(900)   null comment '查询结果',
    created_time   datetime       null comment '创建时间',
    updated_time   datetime       null comment '修改时间'
)
    comment '查询记录' engine = InnoDB;

-- auto-generated definition
create table tb_secumain
(
    ID             bigint auto_increment
        primary key,
    inner_code      int                          null comment '证券内部编码',
    company_code   int                          null comment '公司代码',
    secu_code      varchar(30)                  null comment '证券代码',
    secu_abbr      varchar(100) charset utf8mb4 null comment '证券简称',
    chi_spelling   varchar(100) charset utf8mb4 null comment '拼音证券简称',
    secu_market    int                          null comment '证券市场，枚举：10-上海期货交易所，13-大连商品交易所，15-郑州商品交易所，17-广州期货交易所，51-中国金融期货交易所，71-柜台交易市场，72-香港联交所，76-美国证券交易所，77-美国纳斯达克证券交易所，78-纽约证券交易所，81-三板市场，83-上海证券交易所，84-其他市场，89-银行间债券市场，90-深圳证券交易所，360-纽交所群岛交易所(NYSE Arca)，460-美国OTC(OTCBB和OtherOTC)， -10:场外基金(自定义类型)参见聚源文档 -20：每市市场(自定义类型) ',
    secu_category  int                          null comment '证券类别，枚举：1-A股，2-B股，3-H股，4-大盘，9-可转换债券，13-投资基金，15-深市代理沪市股票，16-沪市代理深市股票，41-中国存托凭证，51-港股，53-红筹股，62-海外ETF，74-美股普通股，75-美股存托凭证，2001-国债，2003-央行票据，2005-企业债，2008-资产支持证券，2009-买断式回购，2010-质押式回购，2012-短期融资券，2018-公司债，2020-中期票据，2021-地方政府债，2022-集合票据，2023-其它债券，2024-债券借贷，2007001-政策性金融债，2007002-商业银行债，2007003-非银行金融债，2007004-国际机构债，2007005-证券公司债，2010004-新质押式国债回购，2010005-质押式协议回购，2010006-质押式三方回购，2010007-存款类机构质押式回购，2010008-质押式报价回购，7001-商品期货，7002001-外汇期货，7002002-利率期货，7002003-股票指数期货，7002004-债券期货，7002005-股票期货，7002006-商品指数期货',
    listed_sector  int                          null comment '上市板块 1-主板，2-中小企业板，3-三板，4-其他，5-大宗交易系统，6-创业板，7-科创板，8-北交所股票',
    listed_date    datetime                     null comment '上市日期',
    listed_state   int                          null comment '上市状态，枚举：1-上市，2-预上市，3-暂停，4-上市失败，5-终止，9-其他',
    delisting_date datetime                     null comment '退市日期',
    JSID           bigint                       null comment 'jsid',
    sec_id         varchar(32) charset utf8mb4  null comment '同花顺证券id',
    industry_code  int                          null comment '行业代码',
    industry_name  varchar(200)                 null comment '行业名称',
    code_by_agent  varchar(60)                  null comment '转换码',
    suffix         varchar(20)                  null comment '后缀（也可代表上市所在国家）',
    created_time   datetime                     null comment '创建时间',
    update_time    datetime                     null comment '更新时间',
    constraint IX_SecuMain_InnerCode
        unique (inner_coe)
)
    comment '证券信息表' engine = InnoDB
                         collate = utf8mb4_bin;

create index IX_SecuMain_Category
    on tb_secumain (secu_category, secu_market, listed_state, listed_sector);

create index IX_SecuMain_CompanyCode
    on tb_secumain (company_code);

create index IX_SecuMain_JSID
    on tb_secumain (JSID);

create index IX_SecuMain_SecuCode
    on tb_secumain (secu_code);

create index PK_SecuMain
    on tb_secumain (ID);

create index idx_InnerCode_SecuCode_SecuAbbr_Suffix
    on tb_secumain (inner_coe, secu_code, secu_abbr, suffix);

create index idx_secid
    on tb_secumain (sec_id);

-- auto-generated definition
create table tb_sms_record
(
    id              varchar(32)     not null comment 'id'
        primary key,
    mobile          varchar(32)     null comment '用户手机号',
    function_code   int default 1   not null comment '功能码(1-登录 2-重置密码)',
    valid_code      varchar(6)      null comment '短信验证码',
    valid_code_time datetime        null comment '短信验证码发送时间',
    valid_status    int default 0   not null comment '验证码状态(0-失效 1-有效)',
    valid_duration  int default 600 not null comment '有效周期(秒)',
    comments        varchar(255)    null comment '备注',
    created_time    datetime        null comment '创建时间',
    updated_time    datetime        null comment '修改时间'
)
    comment '短信记录' engine = InnoDB;

-- auto-generated definition
create table tb_stk_factor
(
    ts_code       varchar(90)    null comment '股票代码',
    trade_date    datetime       null comment '交易日期',
    open          decimal(24, 6) null comment '开盘价',
    high          decimal(24, 6) null comment '最高价',
    low           decimal(24, 6) null comment '最低价',
    close         decimal(24, 6) null comment '收盘价',
    pre_close     decimal(24, 6) null comment '昨收价',
    `change`      decimal(24, 6) null comment '涨跌额',
    pct_change    decimal(24, 6) null comment '涨跌幅(未复权)',
    vol           decimal(24, 6) null comment '成交量(手)',
    amount        decimal(24, 6) null comment '成交额(千元)',
    adj_factor    decimal(24, 6) null comment '复权因子',
    open_hfq      decimal(24, 6) null comment '开盘价后复权',
    open_qfq      decimal(24, 6) null comment '开盘价前复权',
    close_hfq     decimal(24, 6) null comment '收盘价后复权',
    close_qfq     decimal(24, 6) null comment '收盘价前复权',
    high_hfq      decimal(24, 6) null comment '最高价后复权',
    high_qfq      decimal(24, 6) null comment '最高价前复权',
    low_hfq       decimal(24, 6) null comment '最低价后复权',
    low_qfq       decimal(24, 6) null comment '最低价前复权',
    pre_close_hfq decimal(24, 6) null comment '昨收价后复权',
    pre_close_qfq decimal(24, 6) null comment '昨收价前复权',
    macd_dif      decimal(24, 6) null comment 'macd_dif(基于前复权价格计算)',
    macd_dea      decimal(24, 6) null comment 'macd_dea',
    macd          decimal(24, 6) null comment 'macd',
    kdj_k         decimal(24, 6) null comment 'kdj_k',
    kdj_d         decimal(24, 6) null comment 'kdj_d',
    kdj_j         decimal(24, 6) null comment 'kdj_j',
    rsi_6         decimal(24, 6) null comment 'rsi_6',
    rsi_12        decimal(24, 6) null comment 'rsi_12',
    rsi_24        decimal(24, 6) null comment 'rsi_24',
    boll_upper    decimal(24, 6) null comment 'boll_upper',
    boll_mid      decimal(24, 6) null comment 'boll_mid',
    boll_lower    decimal(24, 6) null comment 'boll_lower',
    cci           decimal(24, 6) null comment 'cci',
    constraint idx_ts_date
        unique (ts_code, trade_date)
)
    comment '量化因子' engine = InnoDB;

-- auto-generated definition
create table tb_user
(
    id           varchar(32)    not null comment 'id'
        primary key,
    mobile       varchar(20)    null comment '手机号',
    nickname     varchar(50)    null comment '昵称',
    level        int            null comment '等级',
    point        decimal(24, 6) null comment '积分',
    reg_date     datetime       null comment '注册日期',
    password     varchar(20)    not null comment '密码',
    pw_status    tinyint        null comment '用户密码(0-失效 1-有效 -1-重置)',
    salt         varchar(255)   null comment '加密盐',
    created_time datetime       null comment '创建日期',
    updated_time datetime       null comment '修改日期'
)
    comment '用户' engine = InnoDB;

-- auto-generated definition
create table tb_weekly
(
    ts_code    varchar(90)    not null comment '股票代码',
    trade_date datetime       not null comment '交易日期',
    open       decimal(24, 6) null comment '开盘价',
    high       decimal(24, 6) null comment '最高价',
    low        decimal(24, 6) null comment '最低价',
    close      decimal(24, 6) null comment '收盘价',
    pre_close  decimal(24, 6) null comment '昨收价(前复权)',
    `change`   decimal(24, 6) null comment '涨跌额',
    pct_change decimal(24, 6) null comment '涨跌幅(未复权)',
    vol        decimal(24, 6) null comment '成交量(手)',
    amount     decimal(24, 6) null comment '成交额(千元)',
    primary key (ts_code, trade_date),
    constraint idx_ts_date
        unique (ts_code, trade_date)
)
    comment '周线行情' engine = InnoDB;

