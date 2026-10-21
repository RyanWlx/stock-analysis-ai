# -*- coding: utf-8 -*-
"""
生成 tb_monthly 历史月线（对标 Tushare monthly 接口，doc_id=145，字段与 daily 一致）。

数据来源：本地 tb_daliy（其日线由同花顺/聚源托管库 hsjydb 同步而来）。
    远程同花顺库无原生月线表，月线按业界与 tushare monthly 一致的口径，
    由日线按「自然月」聚合得到：

      trade_date = 当月最后一个交易日
      open       = 当月首个交易日开盘
      high       = 当月最高
      low        = 当月最低
      close      = 当月最后交易日收盘
      vol        = 当月成交量之和（手）
      amount     = 当月成交额之和（千元）
      pre_close  = 上一个月的 close
      change     = close - pre_close
      pct_change = change / pre_close * 100

特性：
    - 幂等：tb_monthly 主键 (ts_code, trade_date)，ON DUPLICATE KEY UPDATE
    - 断点续传：已存在 <=cutoff 月线数据的股票自动跳过（--force 清空重跑）
    - 截止 2026-10-18：最后一个月（2026-10）为「月内累计到 10-16」的部分月（与 tushare 当月口径一致）

用法（项目根目录）：
    python -m app.demo.sync_monthly_from_ths --limit 20
    python -m app.demo.sync_monthly_from_ths
    python -m app.demo.sync_monthly_from_ths --cutoff 20261018
    python -m app.demo.sync_monthly_from_ths --force
"""
import sys
import os
import time
import argparse
import datetime
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pymysql
import numpy as np
import pandas as pd
from sqlalchemy.engine.url import make_url
from concurrent.futures import ThreadPoolExecutor

MONTHLY_SQL = """
    INSERT INTO tb_monthly
    (ts_code, trade_date, open, high, low, close, pre_close, `change`, pct_change, vol, amount)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        open=VALUES(open), high=VALUES(high), low=VALUES(low), close=VALUES(close),
        pre_close=VALUES(pre_close), `change`=VALUES(`change`), pct_change=VALUES(pct_change),
        vol=VALUES(vol), amount=VALUES(amount)
"""


def get_local_params():
    env_host = os.getenv('THS_SYNC_DB_HOST')
    if env_host:
        return dict(
            host=env_host,
            port=int(os.getenv('THS_SYNC_DB_PORT', '3306')),
            user=os.getenv('THS_SYNC_DB_USER', 'root'),
            password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
            database=os.getenv('THS_SYNC_DB_DB', 'stock_int'),
            charset='utf8mb4',
        )
    from app.config.db_config import SQLALCHEMY_DB_URL
    u = make_url(SQLALCHEMY_DB_URL)
    return dict(host=u.host, port=u.port or 3306, user=u.username,
                password=u.password or '', database=u.database, charset='utf8mb4')


def _f(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return float(v)


def daily_to_monthly(df):
    """日线 DataFrame -> 月线 DataFrame。df 列：trade_date,open,high,low,close,vol,amount。"""
    df = df.sort_values('trade_date').reset_index(drop=True)
    df['month'] = df['trade_date'].dt.to_period('M')  # 自然月
    g = df.groupby('month', sort=True)
    out = pd.DataFrame({
        'trade_date': g['trade_date'].max(),
        'open': g['open'].first(),
        'high': g['high'].max(),
        'low': g['low'].min(),
        'close': g['close'].last(),
        'vol': g['vol'].sum(),
        'amount': g['amount'].sum(),
    }).reset_index(drop=True)
    out['pre_close'] = out['close'].shift(1)
    out['change'] = out['close'] - out['pre_close']
    out['pct_change'] = out['change'] / out['pre_close'] * 100.0
    return out


def process_one(ts_code, cutoff, local_params, force=False):
    """读取单只股票日线 -> 聚合月线 -> 写 tb_monthly。返回 (条数, 状态)。"""
    lconn = pymysql.connect(**local_params, connect_timeout=20)
    try:
        cur = lconn.cursor()
        cur.execute(
            "SELECT trade_date, open, high, low, close, vol, amount "
            "FROM tb_daliy WHERE ts_code=%s AND trade_date<=%s ORDER BY trade_date ASC",
            (ts_code, cutoff),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        lconn.close()
    if not rows:
        return 0, 'no_daily'

    df = pd.DataFrame(rows, columns=['trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount'])
    for c in ['open', 'high', 'low', 'close', 'vol', 'amount']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    if df.empty:
        return 0, 'no_daily'

    m = daily_to_monthly(df)
    data = []
    for _, r in m.iterrows():
        td = r['trade_date']
        if isinstance(td, pd.Timestamp):
            td = td.to_pydatetime()
        data.append((
            ts_code, td,
            _f(r['open']), _f(r['high']), _f(r['low']), _f(r['close']),
            _f(r['pre_close']), _f(r['change']), _f(r['pct_change']),
            _f(r['vol']), _f(r['amount']),
        ))
    if not data:
        return 0, 'no_rows'

    lconn = pymysql.connect(**local_params, connect_timeout=20)
    try:
        cur = lconn.cursor()
        if force:
            cur.execute("DELETE FROM tb_monthly WHERE ts_code=%s AND trade_date<=%s", (ts_code, cutoff))
        cur.executemany(MONTHLY_SQL, data)
        lconn.commit()
        cur.close()
    finally:
        lconn.close()
    return len(data), 'ok'


def main():
    ap = argparse.ArgumentParser(description='生成 tb_monthly 历史月线（聚合 tb_daliy）')
    ap.add_argument('--cutoff', type=str, default='20261018', help='截止交易日 YYYYMMDD，默认 20261018（含）')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--codes', type=str, default=None)
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    cutoff = datetime.datetime.strptime(args.cutoff, '%Y%m%d').date()
    local_params = get_local_params()

    lconn = pymysql.connect(**local_params, connect_timeout=20)
    try:
        cur = lconn.cursor()
        if args.codes:
            codes = [c.strip() for c in args.codes.split(',') if c.strip()]
        else:
            cur.execute("SELECT DISTINCT ts_code FROM tb_daliy WHERE trade_date<=%s", (cutoff,))
            codes = [r[0] for r in cur.fetchall()]
        if not args.force:
            cur.execute("SELECT DISTINCT ts_code FROM tb_monthly WHERE trade_date<=%s", (cutoff,))
            done = {r[0] for r in cur.fetchall()}
        else:
            done = set()
        cur.close()
    finally:
        lconn.close()

    if args.limit:
        codes = codes[:args.limit]

    todo = [c for c in codes if c not in done]
    print(f'截止 {cutoff}，日线股票 {len(codes)} 只，月线已完成 {len(done)} 只，待处理 {len(todo)} 只'
          + (' [DRY-RUN]' if args.dry_run else ''))

    if args.dry_run:
        return

    counter = {'ok': 0, 'empty': 0, 'fail': 0, 'rows': 0}
    lock = threading.Lock()

    def worker(ts_code):
        try:
            n, st = process_one(ts_code, cutoff, local_params, args.force)
        except Exception as e:
            n, st = 0, f'exc:{type(e).__name__}:{e}'
        with lock:
            if st == 'ok':
                counter['ok'] += 1
                counter['rows'] += n
            elif st in ('no_daily', 'no_rows'):
                counter['empty'] += 1
            else:
                counter['fail'] += 1
            d = counter['ok'] + counter['empty'] + counter['fail']
            if d % 200 == 0 or st.startswith('exc'):
                print(f'--- 进度 {d}/{len(todo)} | 成功{counter["ok"]} 空{counter["empty"]} '
                      f'失败{counter["fail"]} 累计月线{counter["rows"]} --- {ts_code}:{st}')

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(worker, todo))
    print(f'\n完成！待处理 {len(todo)}，成功 {counter["ok"]}，空 {counter["empty"]}，'
          f'失败 {counter["fail"]}，写入月线 {counter["rows"]} 行，耗时 {round(time.time() - t0, 1)}s')


if __name__ == '__main__':
    main()
