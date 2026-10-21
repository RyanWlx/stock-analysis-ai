# -*- coding: utf-8 -*-
"""
用新浪财经资金流补齐 tb_moneyflow_ths 缺失字段（东方财富数据 API 在本环境网络不可达）。

数据源：新浪财经 MoneyFlow.ssl_qsfx_zjlrqs（逐股，近 N 日）
    https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_qsfx_zjlrqs
    返回：netamount(主力净流入,元) / ratioamount(主力占比,小数) / r0_net(超大单净流入,元) / r0_ratio(超大单占比)

补齐字段（单位对齐 tushare moneyflow_ths，金额=万元、占比=%）：
    net_d5_amount       = 近 5 个交易日 主力净额之和 / 10000
    buy_lg_amount       = (主力 netamount - 超大单 r0_net) / 10000   # 大单 = 主力 - 超大单
    buy_lg_amount_rate  = (主力占比 - 超大单占比) * 100
无法补齐（免费可达源均无中单/小单分解，东方财富被阻断）：
    buy_md_amount / buy_md_amount_rate / buy_sm_amount / buy_sm_amount_rate  -> 留空

用法：python -m app.demo.sync_moneyflow_sina [--trade-date YYYYMMDD] [--workers N] [--dry-run]
"""
import sys
import os
import time
import argparse
import datetime
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
import pymysql
from sqlalchemy.engine.url import make_url
from concurrent.futures import ThreadPoolExecutor, as_completed

SINA_URL = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            "MoneyFlow.ssl_qsfx_zjlrqs?page=1&num={num}&sort=opendate&asc=0&daima={daima}")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://finance.sina.com.cn/',
}

UPDATE_SQL = """
    UPDATE tb_moneyflow_ths
    SET net_d5_amount=%s, buy_lg_amount=%s, buy_lg_amount_rate=%s
    WHERE ts_code=%s AND trade_date=%s
"""


def get_local_params():
    env_host = os.getenv('THS_SYNC_DB_HOST')
    if env_host:
        return dict(host=env_host, port=int(os.getenv('THS_SYNC_DB_PORT', '3306')),
                    user=os.getenv('THS_SYNC_DB_USER', 'root'),
                    password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
                    database=os.getenv('THS_SYNC_DB_DB', 'stock_int'), charset='utf8mb4')
    from app.config.db_config import SQLALCHEMY_DB_URL
    u = make_url(SQLALCHEMY_DB_URL)
    return dict(host=u.host, port=u.port or 3306, user=u.username,
                password=u.password or '', database=u.database, charset='utf8mb4')


def ts_to_daima(ts_code):
    code, suf = ts_code.rsplit('.', 1)
    suf = suf.upper()
    return {'SH': 'sh', 'SZ': 'sz', 'BJ': 'bj'}.get(suf, '') + code


def fetch_one(ts_code, num=5):
    """返回 (net_d5_wan, buy_lg_wan, buy_lg_rate) 或 None。"""
    daima = ts_to_daima(ts_code)
    url = SINA_URL.format(num=num, daima=daima)
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200 or not r.text.strip() or r.text.strip() == 'null':
            return None
        arr = r.json()
        if not arr:
            return None
        # 近 N 日主力净额之和(元)
        d5 = sum(float(x.get('netamount') or 0) for x in arr) / 10000.0
        # 今日(第一条，降序) 大单 = 主力 - 超大单
        today = arr[0]
        main = float(today.get('netamount') or 0)
        r0 = float(today.get('r0_net') or 0)
        lg = (main - r0) / 10000.0
        main_ratio = float(today.get('ratioamount') or 0)
        r0_ratio = float(today.get('r0_ratio') or 0)
        lg_rate = (main_ratio - r0_ratio) * 100.0
        return round(d5, 4), round(lg, 4), round(lg_rate, 4)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description='新浪资金流补齐 tb_moneyflow_ths')
    ap.add_argument('--trade-date', type=str, default=None)
    ap.add_argument('--workers', type=int, default=10)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    td = (datetime.datetime.strptime(args.trade_date, '%Y%m%d').date()
          if args.trade_date else datetime.date.today())
    td_dt = datetime.datetime(td.year, td.month, td.day)

    lconn = pymysql.connect(**get_local_params(), connect_timeout=20)
    try:
        cur = lconn.cursor()
        cur.execute("SELECT ts_code FROM tb_moneyflow_ths WHERE trade_date=%s", (td_dt,))
        codes = [r[0] for r in cur.fetchall()]
    finally:
        lconn.close()
    print(f'待补齐 {len(codes)} 只（新浪）')

    results = []
    done = 0
    lock = threading.Lock()
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_one, c): c for c in codes}
        for fu in as_completed(futs):
            c = futs[fu]
            try:
                v = fu.result()
            except Exception:
                v = None
            with lock:
                done += 1
                if v:
                    results.append((v[0], v[1], v[2], c, td_dt))
                if done % 500 == 0:
                    print(f'--- 进度 {done}/{len(codes)} 命中 {len(results)} 耗时 {round(time.time()-t0,1)}s')

    print(f'命中 {len(results)} 只，未命中 {len(codes)-len(results)} 只，耗时 {round(time.time()-t0,1)}s')
    if args.dry_run:
        print('[dry-run] 不写库')
        return

    lconn = pymysql.connect(**get_local_params(), connect_timeout=20)
    try:
        cur = lconn.cursor()
        cur.executemany(UPDATE_SQL, results)
        lconn.commit()
        cur.close()
    finally:
        lconn.close()
    print(f'完成：更新 {len(results)} 条')


if __name__ == '__main__':
    main()
