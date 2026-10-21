# -*- coding: utf-8 -*-
"""
从 Tushare stock_basic 接口拉取公开股票列表，写入本地 MySQL 的 tb_secumain 表。

使用方式（在项目根目录下执行）：
    python -m app.demo.sync_stock_basic

说明：
1. 请在下方"本地数据库连接配置"中填写正确的用户名 / 密码。
2. 默认数据库名为 stock_int（与 app/config/db_config.py 保持一致）。
3. 脚本会先清空 tb_secumain 表再写入，如需保留旧数据请自行调整。
"""
import sys
import os
import time
import datetime

# 保证能 import app 包（将项目根目录加入 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pymysql
import pandas as pd
from app.config.tushare_config import pro

# ================= 本地数据库连接配置（请按实际修改） =================
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = os.getenv('LOCAL_DB_PASSWORD', '')
MYSQL_DB = 'stock_int'
# ======================================================================

# list_status 上市状态映射 -> tb_secumain.listed_state（1-上市 3-暂停 5-终止 9-其他）
LIST_STATUS_MAP = {
    'L': 1,
    'P': 3,
    'D': 5,
    'G': 9,
    'UN': 9,
}

# market 市场类型映射 -> tb_secumain.listed_sector（1-主板 6-创业板 7-科创板 8-北交所）
MARKET_SECTOR_MAP = {
    '主板': 1,
    '创业板': 6,
    '科创板': 7,
    '北交所': 8,
    'CDR': 1,
}

# 只同步这三个交易所（对应后缀 .SH / .SZ / .BJ）
EXCHANGES = ['SSE', 'SZSE', 'BSE']

# exchange 交易所映射 -> 后缀 & 证券市场
EXCHANGE_SUFFIX_MAP = {
    'SSE': '.SH',
    'SZSE': '.SZ',
    'BSE': '.BJ',
}

EXCHANGE_MARKET_MAP = {
    'SSE': 83,    # 上海证券交易所
    'SZSE': 90,   # 深圳证券交易所
    'BSE': 90,    # 北交所（枚举中暂无独立值，暂归 90）
}


def to_date(value):
    """把 YYYYMMDD 字符串转为 datetime.date，空值 / NaN 返回 None"""
    if value is None:
        return None
    s = str(value).strip()
    if s == '' or s == 'nan' or s == 'None':
        return None
    try:
        return datetime.datetime.strptime(s, '%Y%m%d').date()
    except (ValueError, TypeError):
        return None


def safe_str(value):
    """把 NaN / None 清洗为 None，其余转字符串"""
    if value is None:
        return None
    s = str(value).strip()
    if s == '' or s == 'nan' or s == 'None':
        return None
    return s


def main():
    print('开始拉取 Tushare stock_basic 数据 ...')
    fields = 'ts_code,symbol,name,area,industry,cnspell,market,exchange,list_status,list_date,delist_date,is_hs'
    df = None
    for attempt in range(1, 4):
        try:
            df = pro.stock_basic(exchange='', list_status='L', fields=fields)
            break
        except Exception as e:
            print(f'  第 {attempt} 次拉取失败：{e}')
            if attempt < 3:
                print('  等待 60 秒后重试 ...')
                time.sleep(60)
    if df is None or len(df) == 0:
        print('拉取失败，请稍后再试或检查 token 权限')
        return
    # 只保留上交所 / 深交所 / 北交所（对应后缀 .SH / .SZ / .BJ）
    df = df[df['exchange'].isin(EXCHANGES)].reset_index(drop=True)
    print(f'拉取到 {len(df)} 条记录（已过滤为 SSE/SZSE/BSE）')

    # 建立本地数据库连接
    db = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        db=MYSQL_DB,
        charset='utf8mb4',
    )
    cursor = db.cursor()

    # 清空旧数据
    cursor.execute('TRUNCATE TABLE tb_secumain')
    db.commit()
    print('已清空 tb_secumain 表')

    now = datetime.datetime.now()

    insert_sql = """
        INSERT INTO tb_secumain
        (full_code, secu_code, secu_abbr, chi_spelling, secu_market, secu_category,
         listed_sector, listed_date, listed_state, delisting_date, industry_name, suffix,
         created_time, update_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    count = 0
    for _, row in df.iterrows():
        exchange = safe_str(row.get('exchange'))
        list_status = safe_str(row.get('list_status'))
        market = safe_str(row.get('market'))

        suffix = EXCHANGE_SUFFIX_MAP.get(exchange, '')
        secu_market = EXCHANGE_MARKET_MAP.get(exchange, 90)
        listed_state = LIST_STATUS_MAP.get(list_status, 9)
        listed_sector = MARKET_SECTOR_MAP.get(market, 1)

        cursor.execute(insert_sql, (
            safe_str(row.get('ts_code')),     # full_code（如 000001.SZ）
            safe_str(row.get('symbol')),      # secu_code（如 000001）
            safe_str(row.get('name')),        # secu_abbr
            safe_str(row.get('cnspell')),     # chi_spelling
            secu_market,
            1,                                # secu_category：1-A股
            listed_sector,
            to_date(row.get('list_date')),    # listed_date
            listed_state,
            to_date(row.get('delist_date')),  # delisting_date
            safe_str(row.get('industry')),    # industry_name
            suffix,
            now,
            now,
        ))
        count += 1
        if count % 500 == 0:
            db.commit()
            print(f'已写入 {count} 条')

    db.commit()
    cursor.close()
    db.close()
    print(f'全部完成，共写入 {count} 条记录到 tb_secumain')


if __name__ == '__main__':
    main()
