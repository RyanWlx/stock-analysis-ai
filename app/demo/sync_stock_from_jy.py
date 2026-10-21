import os
# -*- coding: utf-8 -*-
"""
从聚源远程库 hsjydb.secumain 同步 A 股股票列表到本地 stock_int.tb_secumain。

数据源：jdbc:mysql://39.96.14.212:53410/hsjydb  表 secumain
目标  ：本地 MySQL stock_int.tb_secumain

过滤规则（对齐 stock_repo.get_stock_list_all 的查询条件）：
  - 只同步 A 股：SecuCategory = 1
  - 只同步上市中：ListedState = 1
  - 只同步三大交易所：
      SecuMarket = 83  -> 上交所  -> suffix .SH
      SecuMarket = 90  -> 深交所  -> suffix .SZ
      SecuMarket = 18 且 ListedSector = 8 -> 北交所 -> suffix .BJ

字段映射（远程 -> 本地）：
  SecuCode + suffix -> full_code,  SecuAbbr -> secu_abbr,  ChiSpelling -> chi_spelling,
  SecuMarket -> secu_market,  SecuCategory -> secu_category,  ListedSector -> listed_sector,
  ListedDate -> listed_date,  ListedState -> listed_state,
  InnerCode/CompanyCode/JSID/sec_id 原样映射；industry_*/delisting_date 留空。
"""
import sys
import datetime

import pymysql

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 远程聚源库
REMOTE = dict(host='39.96.14.212', port=53410, user='hsjydb', password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
              database='hsjydb', charset='utf8mb4')
# 本地库
LOCAL = dict(host='localhost', port=3306, user='root', password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
             database='stock_int', charset='utf8mb4')

SUFFIX_MAP = {83: '.SH', 90: '.SZ', 18: '.BJ'}


def main():
    remote = pymysql.connect(**REMOTE)
    local = pymysql.connect(**LOCAL)
    rcur = remote.cursor()
    lcur = local.cursor()

    sql = """
        SELECT InnerCode, CompanyCode, SecuCode, SecuAbbr, ChiSpelling,
               SecuMarket, SecuCategory, ListedSector, ListedDate, ListedState,
               JSID, sec_id
        FROM secumain
        WHERE SecuCategory = 1
          AND ListedState = 1
          AND (
              SecuMarket IN (83, 90)
              OR (SecuMarket = 18 AND ListedSector = 8)
          )
    """
    rcur.execute(sql)
    rows = rcur.fetchall()
    print(f'[1] fetched A-share listed rows: {len(rows)}')

    if not rows:
        print('no data, abort')
        return

    # 清空本地表（可重复执行）
    lcur.execute('TRUNCATE TABLE tb_secumain')
    print('[2] local tb_secumain truncated')

    now = datetime.datetime.now()
    insert_sql = """
        INSERT INTO tb_secumain
            (full_code, inner_code, company_code, secu_code, secu_abbr, chi_spelling,
             secu_market, secu_category, listed_sector, listed_date, listed_state,
             delisting_date, JSID, sec_id, industry_code, industry_name, code_by_agent,
             suffix, created_time, update_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    data = []
    stat = {}
    skipped = 0
    for r in rows:
        inner, comp, code, abbr, spelling, market, cat, sector, ldate, state, jsid, secid = r
        suffix = SUFFIX_MAP.get(market)
        if not suffix:
            skipped += 1
            continue
        full_code = f'{code}{suffix}'
        stat[suffix] = stat.get(suffix, 0) + 1
        data.append((full_code, inner, comp, code, abbr, spelling,
                     market, cat, sector, ldate, state,
                     None, jsid, secid, None, None, None,
                     suffix, now, now))

    lcur.executemany(insert_sql, data)
    local.commit()
    print(f'[3] inserted: {len(data)}, skipped: {skipped}')
    print(f'[4] by suffix: {stat}')

    rcur.close()
    lcur.close()
    remote.close()
    local.close()
    print('done')


if __name__ == '__main__':
    main()
