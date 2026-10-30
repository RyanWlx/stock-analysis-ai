-- stock-analysis-ai 本地建库建表脚本（数据库名与 db_config.py 一致，重复执行会先删表重建）
CREATE DATABASE IF NOT EXISTS `stock_int` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `stock_int`;

DROP TABLE IF EXISTS `tb_charts`;
CREATE TABLE `tb_charts` (
    `id`            BIGINT AUTO_INCREMENT COMMENT 'id' PRIMARY KEY,
    `owner_source`  VARCHAR(200) NULL,
    `owner_id`      VARCHAR(200) NULL,
    `name`          VARCHAR(200) NULL,
    `symbol`        VARCHAR(50)  NULL,
    `resolution`    VARCHAR(10)  NULL,
    `last_modified` DATETIME     NULL,
    `content`       JSON         NULL
) COMMENT 'charts' ENGINE = InnoDB;
CREATE INDEX `IX_ownerSource` ON `tb_charts` (`owner_source`, `owner_id`);

DROP TABLE IF EXISTS `tb_cyq_chips`;
CREATE TABLE `tb_cyq_chips` (
    `ts_code`    VARCHAR(90)    NULL,
    `trade_date` DATETIME       NULL,
    `price`      DECIMAL(24, 6) NULL,
    `percent`    DECIMAL(24, 6) NULL,
    CONSTRAINT `idx_ts_date` UNIQUE (`ts_code`, `trade_date`)
) COMMENT '每日筹码分布' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_daliy`;
CREATE TABLE `tb_daliy` (
    `ts_code`    VARCHAR(90)    NOT NULL,
    `trade_date` DATETIME       NOT NULL,
    `open`       DECIMAL(24, 6) NULL,
    `high`       DECIMAL(24, 6) NULL,
    `low`        DECIMAL(24, 6) NULL,
    `close`      DECIMAL(24, 6) NULL,
    `pre_close`  DECIMAL(24, 6) NULL,
    `change`     DECIMAL(24, 6) NULL,
    `pct_change` DECIMAL(24, 6) NULL,
    `vol`        DECIMAL(24, 6) NULL,
    `amount`     DECIMAL(24, 6) NULL,
    PRIMARY KEY (`ts_code`, `trade_date`)
) COMMENT '日线行情' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_exchange`;
CREATE TABLE `tb_exchange` (
    `exchange`      VARCHAR(90) NOT NULL,
    `cal_date`      DATETIME    NOT NULL,
    `is_open`       VARCHAR(1)  NULL,
    `pretrade_date` DATETIME    NULL,
    PRIMARY KEY (`exchange`, `cal_date`)
) COMMENT '交易所' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_monthly`;
CREATE TABLE `tb_monthly` (
    `ts_code`    VARCHAR(90)    NOT NULL,
    `trade_date` DATETIME       NOT NULL,
    `open`       DECIMAL(24, 6) NULL,
    `high`       DECIMAL(24, 6) NULL,
    `low`        DECIMAL(24, 6) NULL,
    `close`      DECIMAL(24, 6) NULL,
    `pre_close`  DECIMAL(24, 6) NULL,
    `change`     DECIMAL(24, 6) NULL,
    `pct_change` DECIMAL(24, 6) NULL,
    `vol`        DECIMAL(24, 6) NULL,
    `amount`     DECIMAL(24, 6) NULL,
    PRIMARY KEY (`ts_code`, `trade_date`)
) COMMENT '月线行情' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_order_record`;
CREATE TABLE `tb_order_record` (
    `id`           VARCHAR(32)    NOT NULL PRIMARY KEY,
    `uid`          VARCHAR(32)    NULL,
    `order_uuid`   VARCHAR(64)    NULL,
    `channel`      INT            NULL,
    `amount`       DECIMAL(24, 6) NULL,
    `order_status` INT            NULL,
    `order_time`   DATETIME       NULL,
    `created_time` DATETIME       NULL,
    `updated_time` DATETIME       NULL
) COMMENT '支付记录' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_query_record`;
CREATE TABLE `tb_query_record` (
    `id`             VARCHAR(32)    NOT NULL PRIMARY KEY,
    `uid`            VARCHAR(32)    NULL,
    `content`        VARCHAR(900)   NULL,
    `stock`          VARCHAR(255)   NULL,
    `query_time`     DATETIME       NULL,
    `execute_status` INT            NULL,
    `payment`        DECIMAL(24, 6) NULL,
    `result`         VARCHAR(900)   NULL,
    `created_time`   DATETIME       NULL,
    `updated_time`   DATETIME       NULL
) COMMENT '查询记录' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_login_record`;
CREATE TABLE `tb_login_record` (
    `id`              VARCHAR(32)  NOT NULL PRIMARY KEY,
    `uid`             VARCHAR(32)  NULL,
    `login_channel`   INT          NULL,
    `login_time`      DATETIME     NULL,
    `valid_code`      VARCHAR(6)   NULL,
    `login_status`    INT          NULL,
    `comments`        VARCHAR(255) NULL,
    `valid_code_time` DATETIME     NULL,
    `created_time`    DATETIME     NULL,
    `updated_time`    DATETIME     NULL
) COMMENT '登录记录' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_secumain`;
CREATE TABLE `tb_secumain` (
    `ID`            BIGINT       NOT NULL AUTO_INCREMENT,
    `full_code`     VARCHAR(30)  NULL COMMENT '证券编码全称',
    `inner_code`    INT          NULL,
    `company_code`  INT          NULL,
    `secu_code`     VARCHAR(30)  NULL,
    `secu_abbr`     VARCHAR(100) NULL,
    `chi_spelling`  VARCHAR(100) NULL,
    `secu_market`   INT          NULL,
    `secu_category` INT          NULL,
    `listed_sector` INT          NULL,
    `listed_date`   DATETIME     NULL,
    `listed_state`  INT          NULL,
    `delisting_date` DATETIME    NULL,
    `JSID`          BIGINT       NULL,
    `sec_id`        VARCHAR(32)  NULL,
    `industry_code` INT          NULL,
    `industry_name` VARCHAR(200) NULL,
    `code_by_agent` VARCHAR(60)  NULL,
    `suffix`        VARCHAR(20)  NULL,
    `created_time`  DATETIME     NULL,
    `update_time`   DATETIME     NULL,
    PRIMARY KEY (`ID`),
    UNIQUE KEY `IX_SecuMain_InnerCode` (`inner_code`),
    KEY `IX_SecuMain_Category` (`secu_category`, `secu_market`, `listed_state`, `listed_sector`),
    KEY `IX_SecuMain_CompanyCode` (`company_code`),
    KEY `IX_SecuMain_JSID` (`JSID`),
    KEY `IX_SecuMain_SecuCode` (`secu_code`),
    KEY `idx_InnerCode_SecuCode_SecuAbbr_Suffix` (`inner_code`, `secu_code`, `secu_abbr`, `suffix`),
    KEY `idx_secid` (`sec_id`)
) COMMENT '证券信息表' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_sms_record`;
CREATE TABLE `tb_sms_record` (
    `id`              VARCHAR(32)  NOT NULL PRIMARY KEY,
    `function_code`   INT          NOT NULL DEFAULT 1,
    `valid_status`    INT          NOT NULL DEFAULT 0,
    `valid_duration`  INT          NOT NULL DEFAULT 600,
    `mobile`          VARCHAR(32)  NULL,
    `valid_code`      VARCHAR(6)   NULL,
    `valid_code_time` DATETIME     NULL,
    `comments`        VARCHAR(255) NULL,
    `created_time`    DATETIME     NULL,
    `updated_time`    DATETIME     NULL
) COMMENT '短信记录' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_stk_factor`;
CREATE TABLE `tb_stk_factor` (
    `ts_code`        VARCHAR(90)    NOT NULL,
    `trade_date`     DATETIME       NOT NULL,
    `open`           DECIMAL(24, 6) NULL,
    `high`           DECIMAL(24, 6) NULL,
    `low`            DECIMAL(24, 6) NULL,
    `close`          DECIMAL(24, 6) NULL,
    `pre_close`      DECIMAL(24, 6) NULL,
    `change`         DECIMAL(24, 6) NULL,
    `pct_change`     DECIMAL(24, 6) NULL,
    `vol`            DECIMAL(24, 6) NULL,
    `amount`         DECIMAL(24, 6) NULL,
    `adj_factor`     DECIMAL(24, 6) NULL,
    `open_hfq`       DECIMAL(24, 6) NULL,
    `open_qfq`       DECIMAL(24, 6) NULL,
    `close_hfq`      DECIMAL(24, 6) NULL,
    `close_qfq`      DECIMAL(24, 6) NULL,
    `high_hfq`       DECIMAL(24, 6) NULL,
    `high_qfq`       DECIMAL(24, 6) NULL,
    `low_hfq`        DECIMAL(24, 6) NULL,
    `low_qfq`        DECIMAL(24, 6) NULL,
    `pre_close_hfq`  DECIMAL(24, 6) NULL,
    `pre_close_qfq`  DECIMAL(24, 6) NULL,
    `macd_dif`       DECIMAL(24, 6) NULL,
    `macd_dea`       DECIMAL(24, 6) NULL,
    `macd`           DECIMAL(24, 6) NULL,
    `kdj_k`          DECIMAL(24, 6) NULL,
    `kdj_d`          DECIMAL(24, 6) NULL,
    `kdj_j`          DECIMAL(24, 6) NULL,
    `rsi_6`          DECIMAL(24, 6) NULL,
    `rsi_12`         DECIMAL(24, 6) NULL,
    `rsi_24`         DECIMAL(24, 6) NULL,
    `boll_upper`     DECIMAL(24, 6) NULL,
    `boll_mid`       DECIMAL(24, 6) NULL,
    `boll_lower`     DECIMAL(24, 6) NULL,
    `cci`            DECIMAL(24, 6) NULL,
    PRIMARY KEY (`ts_code`, `trade_date`)
) COMMENT '股票量化因子' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_study_template`;
CREATE TABLE `tb_study_template` (
    `id`             BIGINT AUTO_INCREMENT COMMENT 'id' PRIMARY KEY,
    `owner_source`   VARCHAR(200) NULL,
    `owner_id`       VARCHAR(200) NULL,
    `name`           VARCHAR(200) NULL,
    `last_modified`  DATETIME     NULL,
    `first_modified` DATETIME     NULL,
    `content`        JSON         NULL
) COMMENT 'study_template' ENGINE = InnoDB;
CREATE INDEX `IX_ownerSource` ON `tb_study_template` (`owner_source`, `owner_id`);

DROP TABLE IF EXISTS `tb_user`;
CREATE TABLE `tb_user` (
    `id`           VARCHAR(32)    NOT NULL PRIMARY KEY,
    `mobile`       VARCHAR(20)    NULL,
    `nickname`     VARCHAR(50)    NULL,
    `level`        INT            NULL,
    `point`        DECIMAL(24, 6) NULL,
    `reg_date`     DATETIME       NULL,
    `password`     VARCHAR(20)    NOT NULL,
    `pw_status`    TINYINT        NULL,
    `salt`         VARCHAR(255)   NULL,
    `created_time` DATETIME       NULL,
    `updated_time` DATETIME       NULL,
    UNIQUE KEY `uk_mobile` (`mobile`)
) COMMENT '用户' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_weekly`;
CREATE TABLE `tb_weekly` (
    `ts_code`    VARCHAR(90)    NOT NULL,
    `trade_date` DATETIME       NOT NULL,
    `open`       DECIMAL(24, 6) NULL,
    `high`       DECIMAL(24, 6) NULL,
    `low`        DECIMAL(24, 6) NULL,
    `close`      DECIMAL(24, 6) NULL,
    `pre_close`  DECIMAL(24, 6) NULL,
    `change`     DECIMAL(24, 6) NULL,
    `pct_change` DECIMAL(24, 6) NULL,
    `vol`        DECIMAL(24, 6) NULL,
    `amount`     DECIMAL(24, 6) NULL,
    PRIMARY KEY (`ts_code`, `trade_date`)
) COMMENT '周线行情' ENGINE = InnoDB;

DROP TABLE IF EXISTS `tb_marks`;
CREATE TABLE `tb_marks` (
    `id`               BIGINT       NOT NULL AUTO_INCREMENT COMMENT 'id',
    `ts_code`          VARCHAR(90)  NOT NULL COMMENT '股票代码(带后缀，如 600519.SH)',
    `mark_time`        DATETIME     NOT NULL COMMENT '标记时间(对应K线bar时间)',
    `mark_kind`        VARCHAR(20)  NOT NULL DEFAULT 'bar' COMMENT '标记类型: bar=K线标记(getMarks), timescale=时间轴标记(getTimescaleMarks)',
    `mark_type`        VARCHAR(50)  NULL COMMENT '业务类型: dividend/earnings/split/lockup/custom 等',
    `color`            VARCHAR(50)  NULL COMMENT '颜色(red/green/blue/yellow/purple/orange 等)',
    `label`            VARCHAR(10)  NULL COMMENT '标签(bar标记通常单字符，如 E/D/M)',
    `label_font_color` VARCHAR(50)  NULL COMMENT '标签字体颜色',
    `text`             VARCHAR(500) NULL COMMENT '悬浮文本(bar标记 tooltip)',
    `tooltip`          TEXT         NULL COMMENT '时间轴标记多行提示(JSON数组字符串)',
    `min_size`         INT          NULL COMMENT '最小显示尺寸',
    `created_time`     DATETIME     NULL COMMENT '创建时间',
    `updated_time`     DATETIME     NULL COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_marks_code_time` (`ts_code`, `mark_time`),
    KEY `idx_marks_kind` (`mark_kind`)
) COMMENT '图表标记(交易事件/财报/分红/解禁等)' ENGINE = InnoDB;
