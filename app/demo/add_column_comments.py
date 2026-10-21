# -*- coding: utf-8 -*-
"""
给本地库 stock_int 的表添加字段注释（COMMENT）。

注释来源：
- tb_stk_factor : 对齐 tushare stk_factor 接口官方字段说明（doc_id=296）
- tb_secumain   : 使用项目 ORM 模型 app/models/stock_model.py 已有注释（聚源口径，
                  与 tushare stock_basic 字段体系不同，故以项目内模型为准）

实现要点：
- 通过 information_schema 读取每列完整定义（类型/NULL/默认值/auto_increment），
  仅追加 COMMENT，保证其它属性零丢失。
- 大表 tb_stk_factor（1700万+行）用 ALGORITHM=INSTANT 改注释，秒级完成、不重建表。
- 可重复执行（幂等），重复跑只会覆盖注释，无副作用。

用法：
    python -m app.demo.add_column_comments
"""
import os
import pymysql

DB = dict(host='localhost', port=3306, user='root', password=os.getenv('LOCAL_DB_PASSWORD', ''),
          database='stock_int', charset='utf8mb4')

# ---------- tb_stk_factor 字段注释（tushare stk_factor 官方，doc_id=296） ----------
STK_FACTOR_COMMENTS = {
    'ts_code': '股票代码',
    'trade_date': '交易日期',
    'open': '开盘价',
    'high': '最高价',
    'low': '最低价',
    'close': '收盘价',
    'pre_close': '昨收价',
    'change': '涨跌额',
    'pct_change': '涨跌幅',
    'vol': '成交量(手)',
    'amount': '成交额(千元)',
    'adj_factor': '复权因子',
    'open_hfq': '开盘价后复权',
    'open_qfq': '开盘价前复权',
    'close_hfq': '收盘价后复权',
    'close_qfq': '收盘价前复权',
    'high_hfq': '最高价后复权',
    'high_qfq': '最高价前复权',
    'low_hfq': '最低价后复权',
    'low_qfq': '最低价前复权',
    'pre_close_hfq': '昨收价后复权',
    'pre_close_qfq': '昨收价前复权',
    'macd_dif': 'MACD_DIF(基于前复权价格计算)',
    'macd_dea': 'MACD_DEA(基于前复权价格计算)',
    'macd': 'MACD(基于前复权价格计算)',
    'kdj_k': 'KDJ_K(基于前复权价格计算)',
    'kdj_d': 'KDJ_D(基于前复权价格计算)',
    'kdj_j': 'KDJ_J(基于前复权价格计算)',
    'rsi_6': 'RSI_6(基于前复权价格计算)',
    'rsi_12': 'RSI_12(基于前复权价格计算)',
    'rsi_24': 'RSI_24(基于前复权价格计算)',
    'boll_upper': 'BOLL_UPPER(基于前复权价格计算)',
    'boll_mid': 'BOLL_MID(基于前复权价格计算)',
    'boll_lower': 'BOLL_LOWER(基于前复权价格计算)',
    'cci': 'CCI(基于前复权价格计算)',
}

# ---------- tb_secumain 字段注释（项目 ORM 模型，聚源口径） ----------
SECUMAIN_COMMENTS = {
    'ID': '主键ID',
    'full_code': '证券编码全称',
    'inner_code': '证券内部编码',
    'company_code': '公司代码',
    'secu_code': '证券代码',
    'secu_abbr': '证券简称',
    'chi_spelling': '拼音证券简称',
    'secu_market': '证券市场，枚举：10-上海期货交易所，13-大连商品交易所，15-郑州商品交易所，17-广州期货交易所，51-中国金融期货交易所，71-柜台交易市场，72-香港联交所，76-美国证券交易所，77-美国纳斯达克证券交易所，78-纽约证券交易所，81-三板市场，83-上海证券交易所，84-其他市场，89-银行间债券市场，90-深圳证券交易所，360-纽交所群岛交易所(NYSE Arca)，460-美国OTC(OTCBB和OtherOTC)，-10:场外基金(自定义类型)，-20:每市市场(自定义类型)',
    'secu_category': '证券类别，枚举：1-A股，2-B股，3-H股，4-大盘，9-可转换债券，13-投资基金，15-深市代理沪市股票，16-沪市代理深市股票，41-中国存托凭证，51-港股，53-红筹股，62-海外ETF，74-美股普通股，75-美股存托凭证，2001-国债，2003-央行票据，2005-企业债，2008-资产支持证券，2009-买断式回购，2010-质押式回购，2012-短期融资券，2018-公司债，2020-中期票据，2021-地方政府债，2022-集合票据，2023-其它债券，2024-债券借贷，2007001-政策性金融债，2007002-商业银行债，2007003-非银行金融债，2007004-国际机构债，2007005-证券公司债，2010004-新质押式国债回购，2010005-质押式协议回购，2010006-质押式三方回购，2010007-存款类机构质押式回购，2010008-质押式报价回购，7001-商品期货，7002001-外汇期货，7002002-利率期货，7002003-股票指数期货，7002004-债券期货，7002005-股票期货，7002006-商品指数期货',
    'listed_sector': '上市板块 1-主板，2-中小企业板，3-三板，4-其他，5-大宗交易系统，6-创业板，7-科创板，8-北交所股票',
    'listed_date': '上市日期',
    'listed_state': '上市状态，枚举：1-上市，2-预上市，3-暂停，4-上市失败，5-终止，9-其他',
    'delisting_date': '退市日期',
    'JSID': 'jsid',
    'sec_id': '同花顺证券id',
    'industry_code': '行业代码',
    'industry_name': '行业名称',
    'code_by_agent': '转换码',
    'suffix': '后缀（也可代表上市所在国家）',
    'created_time': '创建时间',
    'update_time': '更新时间',
}


def build_modify_sql(table, col, coltype, nullable, extra, comment):
    """构造只改注释的 MODIFY COLUMN 语句，保留原类型/NULL/auto_increment 属性。"""
    comment = comment.replace("'", "''")  # 转义单引号
    clause = f"MODIFY COLUMN `{col}` {coltype} "
    if extra == 'auto_increment':
        clause += "NOT NULL AUTO_INCREMENT "
    elif nullable == 'NO':
        clause += "NOT NULL "
    else:
        clause += "DEFAULT NULL "
    clause += f"COMMENT '{comment}'"
    return f"ALTER TABLE `{table}` {clause}"


def main():
    conn = pymysql.connect(**DB)
    cur = conn.cursor()

    for table, comments in [('tb_stk_factor', STK_FACTOR_COMMENTS),
                            ('tb_secumain', SECUMAIN_COMMENTS)]:
        cur.execute(
            "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, EXTRA "
            "FROM information_schema.columns "
            "WHERE table_schema=%s AND table_name=%s ORDER BY ORDINAL_POSITION",
            (DB['database'], table),
        )
        cols = cur.fetchall()
        done = 0
        print(f"=== 表 {table}（共 {len(cols)} 列） ===")
        for name, coltype, nullable, extra in cols:
            if name not in comments:
                print(f"  [跳过] {name} 无注释定义")
                continue
            sql = build_modify_sql(table, name, coltype, nullable, extra, comments[name])
            # 先尝试 INSTANT（不重建表），失败则回退普通 MODIFY
            try:
                cur.execute(sql + ", ALGORITHM=INSTANT")
            except Exception:
                try:
                    cur.execute(sql)
                except Exception as e:
                    print(f"  [失败] {name}: {e}")
                    conn.rollback()
                    continue
            done += 1
        conn.commit()
        print(f"  -> 已添加 {done}/{len(cols)} 列注释\n")

    conn.close()
    print("全部完成。")


if __name__ == '__main__':
    main()
