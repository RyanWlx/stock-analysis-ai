DROP TABLE IF EXISTS tb_user;
CREATE TABLE tb_user(
    `id` VARCHAR(32) NOT NULL   COMMENT 'id' ,
    `mobile` VARCHAR(20)    COMMENT '手机号' ,
    `nickname` VARCHAR(50)    COMMENT '昵称' ,
    `level` INT(1)    COMMENT '等级' ,
    `point` DECIMAL(24,6)    COMMENT '积分' ,
    `reg_date` DATETIME    COMMENT '注册日期' ,
    `created_time` DATETIME    COMMENT '创建日期' ,
    `updated_time` DATETIME    COMMENT '修改日期' ,
    PRIMARY KEY (id)
)  COMMENT = '用户';

DROP TABLE IF EXISTS tb_order_record;
CREATE TABLE tb_order_record(
    `id` VARCHAR(32) NOT NULL   COMMENT 'id' ,
    `uid` VARCHAR(32)    COMMENT '用户id' ,
    `order_uuid` VARCHAR(64)    COMMENT '支付流水号' ,
    `channel` INT    COMMENT '支付渠道' ,
    `amount` DECIMAL(24,6)    COMMENT '支付金额' ,
    `order_status` INT(1)    COMMENT '支付状态' ,
    `order_time` DATETIME    COMMENT '支付时间' ,
    `created_time` DATETIME   COMMENT '创建时间' ,
    `updated_time` DATETIME    COMMENT '修改时间' ,
    PRIMARY KEY (id)
)  COMMENT = '支付记录';

DROP TABLE IF EXISTS tb_query_record;
CREATE TABLE tb_query_record(
    `id` VARCHAR(32) NOT NULL   COMMENT 'id' ,
    `uid` VARCHAR(32)    COMMENT '用户id' ,
    `content` VARCHAR(900)    COMMENT '查询内容' ,
    `stock` VARCHAR(255)    COMMENT '解析股票' ,
    `query_time` DATETIME    COMMENT '查询时间' ,
    `execute_status` INT(1)    COMMENT '执行状态' ,
    `payment` DECIMAL(24,6)    COMMENT '消耗积分' ,
    `result` VARCHAR(900)    COMMENT '查询结果' ,
    `created_time` DATETIME    COMMENT '创建时间' ,
    `updated_time` DATETIME    COMMENT '修改时间' ,
    PRIMARY KEY (id)
)  COMMENT = '查询记录';

DROP TABLE IF EXISTS tb_login_record;
CREATE TABLE tb_login_record(
    `id` VARCHAR(32) NOT NULL   COMMENT 'id' ,
    `uid` VARCHAR(32)    COMMENT '用户id' ,
    `login_channel` INT(1)    COMMENT '登录方式' ,
    `login_time` DATETIME    COMMENT '登录时间' ,
    `valid_code` VARCHAR(6)    COMMENT '短信验证码' ,
    `login_status` INT(1)    COMMENT '执行状态' ,
    `comments` VARCHAR(255)    COMMENT '备注' ,
    `valid_code_time` DATETIME    COMMENT '短信验证码发送时间' ,
    `created_time` DATETIME    COMMENT '创建时间' ,
    `updated_time` DATETIME    COMMENT '修改时间' ,
    PRIMARY KEY (id)
)  COMMENT = '登录记录';
