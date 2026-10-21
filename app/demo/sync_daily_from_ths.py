# -*- coding: utf-8 -*-
"""
补齐 tb_daliy 历史日线行情（对标 Tushare daily 接口，doc_id=27）。

数据源：远程同花顺/聚源托管库 hsjydb.thsdb.shsz_stock_daily_quotation
    host=39.96.14.212 port=53410 user=hsjydb

背景：
    原 tb_daliy 只由"每日同步"(ths_daily_sync) 写入了最近一天(2026-10-19)。
    本脚本按股票逐只拉取「截至 cutoff(默认 2026-10-18)」的全部历史日线，
    回填到 tb_daliy，使该表与 tb_stk_factor 的历史区间对齐。

字段口径（与 tushare daily / 既有 tb_daliy 完全一致）：
    ts_code, trade_date, open, high, low, close, pre_close,
    `change`, pct_change, vol, amount
    * 成交量 股 -> 手 (/100)；成交额 元 -> 千元 (/1000)
    * 涨跌额 change = close - pre_close
    * 涨跌幅 pct_change 优先用远程 chg_ratio，缺失时用 change/pre_close*100 兜底

特性：
    - 幂等：tb_daliy 主键 (ts_code, trade_date)，ON DUPLICATE KEY UPDATE
    - 断点续传：已存在 <=cutoff 数据的股票自动跳过（--force 强制覆盖整表重跑）
    - 多线程：默认 4 个 worker（每只股票独立建/断远程连接，规避公网长连接中断）
    - 每只股票独立重试 3 次

用法（项目根目录）：
    python -m app.demo.sync_daily_from_ths --limit 20        # 试点
    python -m app.demo.sync_daily_from_ths                   # 全量回填(<=2026-10-18)
    python -m app.demo.sync_daily_from_ths --cutoff 20260101 # 指定截止日
    python -m app.demo.sync_daily_from_ths --workers 6       # 调并发
    python -m app.demo.sync_daily_from_ths --codes 000001.SZ,600000.SH
    python -m app.demo.sync_daily_from_ths --force           # 清空后重跑
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
from sqlalchemy.engine.url import make_url
from concurrent.futures import ThreadPoolExecutor

# ==================== 远程同花顺库 ====================
REMOTE = dict(
    host='39.96.14.212', port=53410, user='hsjydb', password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
    database='hsjydb', charset='utf8mb4', connect_timeout=30, read_timeout=300,
)
# 后缀 -> 远程 exchg 中文名
EXCHG_SUFFIX = {'.SH': '上交所', '.SZ': '深交所', '.BJ': '北交所'}

# ==================== SQL ====================
DALIY_SQL = """
    INSERT INTO tb_daliy
    (ts_code, trade_date, open, high, low, close, pre_close, `change`, pct_change, vol, amount)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        open=VALUES(open), high=VALUES(high), low=VALUES(low), close=VALUES(close),
        pre_close=VALUES(pre_close), `change`=VALUES(`change`), pct_change=VALUES(pct_change),
        vol=VALUES(vol), amount=VALUES(amount)
"""

_remote_sql = """
    SELECT td_date, pre_close, open_price, high_trans, low_trans, latest_trans,
           trans_vol, trans_amt_rmb, chg_ratio
    FROM thsdb.shsz_stock_daily_quotation
    WHERE sec_code = %s AND exchg = %s AND td_date <= %s AND isvalid = 1
    ORDER BY td_date ASC
"""


# ==================== 连接 ====================
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
    if v is None:
        return None
    try:
        fv = float(v)
    except (ValueError, TypeError):
        return None
    if np.isnan(fv) or np.isinf(fv):
        return None
    return fv


# ==================== 股票池 ====================
def get_universe(lconn):
    """返回去重后的 [(sec_code, exchg_cn, ts_code), ...]，覆盖全部 A 股（含退市）。
    优先 stock_basic（含 L/P/D），再补 tb_secumain 的 full_code，按后缀推断交易所。"""
    cur = lconn.cursor()
    codes = set()
    try:
        cur.execute("SELECT ts_code FROM stock_basic")
        for (tc,) in cur.fetchall():
            if tc:
                codes.add(tc.strip())
    except Exception:
        pass
    try:
        cur.execute("SELECT full_code FROM tb_secumain WHERE full_code IS NOT NULL AND full_code <> ''")
        for (fc,) in cur.fetchall():
            if fc:
                codes.add(fc.strip())
    except Exception:
        pass
    cur.close()

    universe = []
    for fc in sorted(codes):
        if '.' not in fc:
            continue
        code, suf = fc.rsplit('.', 1)
        suf = '.' + suf.upper()
        exchg = EXCHG_SUFFIX.get(suf)
        if not exchg:
            continue
        universe.append((code, exchg, fc))
    return universe


def get_done(lconn, cutoff):
    """已经存在 <=cutoff 历史数据的 ts_code 集合（用于断点续传）。"""
    cur = lconn.cursor()
    cur.execute("SELECT DISTINCT ts_code FROM tb_daliy WHERE trade_date <= %s", (cutoff,))
    rows = {r[0] for r in cur.fetchall()}
    cur.close()
    return rows


# ==================== 单只处理 ====================
def process_one(sec_code, exchg, ts_code, cutoff, local_params, force=False):
    """拉取单只股票历史并写入 tb_daliy。返回 (写入条数, 状态)。"""
    # 1. 远程拉取（独立连接，最多重试 3 次）
    rows = None
    last_err = None
    for attempt in range(1, 4):
        rconn = None
        try:
            rconn = pymysql.connect(**REMOTE)
            cur = rconn.cursor()
            cur.execute(_remote_sql, (sec_code, exchg, cutoff))
            rows = cur.fetchall()
            cur.close()
            last_err = None
            break
        except Exception as e:
            last_err = e
            if attempt < 3:
                time.sleep(5)
        finally:
            if rconn:
                try:
                    rconn.close()
                except Exception:
                    pass
    if last_err is not None:
        return 0, f'remote_err:{type(last_err).__name__}'
    if not rows:
        return 0, 'remote_empty'

    # 2. 组装
    daliy = []
    for td, pre, o, h, l, c, vol, amt, chg in rows:
        close = _f(c)
        if close is None or _f(h) is None or _f(l) is None:
            continue
        pre_close = _f(pre)
        change = (close - pre_close) if (close is not None and pre_close is not None) else None
        pct = _f(chg)
        if pct is None and change is not None and pre_close not in (None, 0):
            pct = change / pre_close * 100.0
        vol_h = _f(vol) / 100.0 if _f(vol) is not None else None        # 股 -> 手
        amt_k = _f(amt) / 1000.0 if _f(amt) is not None else None        # 元 -> 千元
        td_date = td.date() if isinstance(td, datetime.datetime) else td
        daliy.append((
            ts_code, td_date,
            _f(o), _f(h), _f(l), close, pre_close,
            change, pct, vol_h, amt_k,
        ))
    if not daliy:
        return 0, 'no_rows'

    # 3. 写库（独立本地连接）
    lconn = pymysql.connect(**local_params, connect_timeout=20)
    try:
        cur = lconn.cursor()
        if force:
            cur.execute("DELETE FROM tb_daliy WHERE ts_code = %s AND trade_date <= %s", (ts_code, cutoff))
        cur.executemany(DALIY_SQL, daliy)
        lconn.commit()
        cur.close()
    finally:
        lconn.close()
    return len(daliy), 'ok'


# ==================== 主流程 ====================
def main():
    ap = argparse.ArgumentParser(description='补齐 tb_daliy 历史日线（远程同花顺库）')
    ap.add_argument('--cutoff', type=str, default='20261018', help='截止交易日 YYYYMMDD，默认 20261018（含）')
    ap.add_argument('--workers', type=int, default=4, help='并发 worker 数，默认 4')
    ap.add_argument('--limit', type=int, default=None, help='仅处理前 N 只（试点）')
    ap.add_argument('--codes', type=str, default=None, help='指定 ts_code 列表，逗号分隔')
    ap.add_argument('--force', action='store_true', help='清空 <=cutoff 数据后重跑')
    ap.add_argument('--dry-run', action='store_true', help='只统计不写库')
    args = ap.parse_args()

    cutoff = datetime.datetime.strptime(args.cutoff, '%Y%m%d').date()
    local_params = get_local_params()

    lconn = pymysql.connect(**local_params, connect_timeout=20)
    try:
        if args.codes:
            universe = []
            for fc in [c.strip() for c in args.codes.split(',') if c.strip()]:
                if '.' not in fc:
                    continue
                code, suf = fc.rsplit('.', 1)
                exchg = EXCHG_SUFFIX.get('.' + suf.upper())
                if exchg:
                    universe.append((code, exchg, fc))
        else:
            universe = get_universe(lconn)
        done = get_done(lconn, cutoff) if not args.force else set()
    finally:
        lconn.close()

    if args.limit:
        universe = universe[:args.limit]

    # 过滤已完成
    todo = []
    skipped = 0
    for sec_code, exchg, ts_code in universe:
        if not args.force and ts_code in done:
            skipped += 1
            continue
        todo.append((sec_code, exchg, ts_code))
    total = len(todo)
    print(f'截止 {cutoff}，股票池 {len(universe)} 只，已完成 {skipped} 只，待处理 {total} 只'
          + (' [DRY-RUN]' if args.dry_run else ''))

    if args.dry_run:
        return

    counter = {'ok': 0, 'fail': 0, 'empty': 0, 'rows': 0}
    lock = threading.Lock()

    def worker(item):
        sec_code, exchg, ts_code = item
        try:
            n, status = process_one(sec_code, exchg, ts_code, cutoff, local_params, args.force)
        except Exception as e:
            n, status = 0, f'exc:{type(e).__name__}:{e}'
        with lock:
            if status == 'ok':
                counter['ok'] += 1
                counter['rows'] += n
            elif status == 'remote_empty' or status == 'no_rows':
                counter['empty'] += 1
            else:
                counter['fail'] += 1
            done_n = counter['ok'] + counter['fail'] + counter['empty']
            if done_n % 100 == 0 or status.startswith(('remote_err', 'exc')):
                print(f'--- 进度 {done_n}/{total} | 成功{counter["ok"]} 空{counter["empty"]} '
                      f'失败{counter["fail"]} 累计行{counter["rows"]} --- {ts_code}:{status}')

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(worker, todo))
    print(f'\n完成！待处理 {total}，成功 {counter["ok"]}，空数据 {counter["empty"]}，'
          f'失败 {counter["fail"]}，写入 {counter["rows"]} 行，耗时 {round(time.time() - t0, 1)}s')


if __name__ == '__main__':
    main()
