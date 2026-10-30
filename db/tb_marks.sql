-- stock-analysis-ai 图表标记表（TradingView Charting Library getMarks / getTimescaleMarks）
-- 数据库：本地 stock_int（重复执行幂等，不会删除已有数据）
USE `stock_int`;

CREATE TABLE IF NOT EXISTS `tb_marks` (
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
) COMMENT '图表标记(交易事件/财报/分红/解禁等)' ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci;
