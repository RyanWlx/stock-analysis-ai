# -*- coding: utf-8 -*-
"""
从新浪财经补齐 tb_moneyflow_ths 的【全部历史】资金流（东方财富/网易/腾讯在本环境均不可达，新浪可达且含全历史）。

数据源：新浪财经 MoneyFlow.ssl_qsfx_zjlrqs（逐股返回全历史，2010 起 / IPO 起）
    字段：opendate, trade(收盘价), changeratio(涨跌幅小数), netamount(主力净流入,元),
          ratioamount(主力占比,小数), r0_net(超大单净流入,元), r0_ratio(超大单占比)

计算（单位对齐 tushare moneyflow_ths：金额=万元、占比=%）：
    net_amount          = netamount / 10000
    net_d5_amount       = 近 5 个交易日 netamount 之和 / 10000（逐日滚动）
    buy_lg_amount       = (netamount - r0_net) / 10000          # 大单 = 主力 - 超大单
    buy_lg_amount_rate  = (ratioamount - r0_ratio) * 100
    pct_change          = changeratio * 100
    latest              = trade
  buy_md_amount/rate、buy_sm_amount/rate（中单/小单）无源，留空。

特性：分批+并发抓取、批量 upsert、断点续传（已有历史(<cutoff)的股票跳过）、幂等。
用法：python -m app.demo.sync_moneyflow_hist_sina [--workers N] [--cutoff YYYYMMDD] [--limit N] [--dry-run]
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
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
           'Referer': 'https://finance.sina.com.cn/'}
NUM = 6000

UPSERT_SQL = """
INSERT INTO tb_moneyflow_ths
(ts_code, trade_date, name, pct_change, latest, net_amount, net_d5_amount,
 buy_lg_amount, buy_lg_amount_rate, buy_md_amount, buy_md_amount_rate,
 buy_sm_amount, buy_sm_amount_rate)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
 name=VALUES(name), pct_change=VALUES(pct_change), latest=VALUES(latest),
 net_amount=VALUES(net_amount), net_d5_amount=VALUES(net_d5_amount),
 buy_lg_amount=VALUES(buy_lg_amount), buy_lg_amount_rate=VALUES(buy_lg_amount_rate)
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


def get_universe(lconn):
    """[(ts_code, name)]，stock_basic 全部 + tb_secumain 兜底。"""
    m = {}
    cur = lconn.cursor()
    try:
        cur.execute("SELECT ts_code, name FROM stock_basic")
        for tc, nm in cur.fetchall():
            if tc and '.' in tc:
                m.setdefault(tc.strip(), nm)
    except Exception:
        pass
    try:
        cur.execute("SELECT full_code, secu_abbr FROM tb_secumain WHERE full_code IS NOT NULL AND full_code <> ''")
        for tc, nm in cur.fetchall():
            if tc and '.' in tc:
                m.setdefault(tc.strip(), nm)
    except Exception:
        pass
    cur.close()
    return list(m.items())


def ts_to_daima(ts_code):
    code, suf = ts_code.rsplit('.', 1)
    return {'SH': 'sh', 'SZ': 'sz', 'BJ': 'bj'}.get(suf.upper(), '') + code


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def fetch_stock(ts_code, name):
    """抓单只股票全历史，返回 rows 列表（按日期升序已计算好）。"""
    daima = ts_to_daima(ts_code)
    try:
        r = requests.get(SINA_URL.format(num=NUM, daima=daima), headers=HEADERS, timeout=30)
        if r.status_code != 200 or not r.text.strip() or r.text.strip() == 'null':
            return []
        arr = r.json()
    except Exception:
        return []
    if not arr:
        return []
    # 升序（新浪默认降序）
    arr = sorted(arr, key=lambda x: x.get('opendate') or '')
    nets = [_num(x.get('netamount')) for x in arr]
    rows = []
    for i, x in enumerate(arr):
        if not x.get('opendate'):
            continue
        trade = _num(x.get('trade'))
        if trade <= 0:
            continue
        main = nets[i]
        r0 = _num(x.get('r0_net'))
        main_ratio = _num(x.get('ratioamount'))
        r0_ratio = _num(x.get('r0_ratio'))
        d5 = sum(nets[max(0, i - 4):i + 1]) / 10000.0
        try:
            td = datetime.datetime.strptime(x['opendate'], '%Y-%m-%d')
        except Exception:
            continue
        rows.append((
            ts_code, td, name,
            round(_num(x.get('changeratio')) * 100.0, 4), round(trade, 4),
            round(main / 10000.0, 4), round(d5, 4),
            round((main - r0) / 10000.0, 4), round((main_ratio - r0_ratio) * 100.0, 4),
            None, None, None, None,
        ))
    return rows


def main():
    ap = argparse.ArgumentParser(description='新浪资金流全量历史 -> tb_moneyflow_ths')
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--chunk', type=int, default=100)
    ap.add_argument('--cutoff', type=str, default=None, help='只回填 < 该日期(YYYYMMDD)，默认今天')
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    cutoff = (datetime.datetime.strptime(args.cutoff, '%Y%m%d').date()
              if args.cutoff else datetime.date.today())
    cutoff_dt = datetime.datetime(cutoff.year, cutoff.month, cutoff.day)

    lconn = pymysql.connect(**get_local_params(), connect_timeout=20)
    try:
        cur = lconn.cursor()
        # 加 trade_date 索引（若缺，便于续传与查询）
        try:
            cur.execute("SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema=DATABASE() "
                        "AND table_name='tb_moneyflow_ths' AND index_name='idx_mf_trade_date'")
            if cur.fetchone()[0] == 0:
                cur.execute("ALTER TABLE tb_moneyflow_ths ADD INDEX idx_mf_trade_date (trade_date)")
                lconn.commit()
        except Exception as e:
            print('建索引跳过:', str(e)[:80])
        universe = get_universe(lconn)
        # 断点续传：<cutoff 已有历史的股票
        cur.execute("SELECT DISTINCT ts_code FROM tb_moneyflow_ths WHERE trade_date < %s", (cutoff_dt,))
        done = {r[0] for r in cur.fetchall()}
    finally:
        lconn.close()

    if args.limit:
        universe = universe[:args.limit]
    todo = [(tc, nm) for tc, nm in universe if tc not in done]
    print(f'股票池 {len(universe)}，已有历史 {len(done)}，待处理 {len(todo)}，cutoff={cutoff}'
          + (' [DRY-RUN]' if args.dry_run else ''))

    n_ok = n_empty = n_fail = 0
    n_rows = 0
    lock = threading.Lock()
    t0 = time.time()

    for ci in range(0, len(todo), args.chunk):
        chunk = todo[ci:ci + args.chunk]
        results = []
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(fetch_stock, tc, nm): tc for tc, nm in chunk}
            for fu in as_completed(futs):
                tc = futs[fu]
                try:
                    rows = fu.result()
                except Exception:
                    rows = None
                with lock:
                    if rows is None:
                        n_fail += 1
                    elif not rows:
                        n_empty += 1
                    else:
                        n_ok += 1
                        results.extend(rows)
        # 过滤 < cutoff（保留历史；默认不含今天之前之外都写，含今天则不过滤）
        results = [r for r in results if r[1] < cutoff_dt] if args.cutoff else results
        n_rows += len(results)
        if results and not args.dry_run:
            lconn = pymysql.connect(**get_local_params(), connect_timeout=20)
            try:
                cur = lconn.cursor()
                cur.executemany(UPSERT_SQL, results)
                lconn.commit()
                cur.close()
            finally:
                lconn.close()
        if (ci // args.chunk) % 10 == 0:
            print(f'--- 进度 {ci+len(chunk)}/{len(todo)} | 成功{n_ok} 空{n_empty} 失败{n_fail} '
                  f'累计{n_rows}行 耗时{round(time.time()-t0,1)}s ---', flush=True)

    print(f'完成！待处理 {len(todo)}，成功 {n_ok}，空 {n_empty}，失败 {n_fail}，写入 {n_rows} 行，'
          f'耗时 {round(time.time()-t0,1)}s')


if __name__ == '__main__':
    main()
