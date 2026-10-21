# -*- coding: utf-8 -*-
"""
补齐 tb_stk_factor 历史数据（Tushare stk_factor 接口已下线）。

数据源：远程同花顺库 thsdb.shsz_stock_daily_quotation（聚源/同花顺托管库）
    host=39.96.14.212 port=53410 user=hsjydb

该表单表即含全部所需字段：
  - 未复权 OHLCV：open_price / high_trans / low_trans / latest_trans
  - pre_close / chg_ratio（涨跌幅）/ trans_vol（股）/ trans_amt_rmb（元）
  - af_alg1（后复权因子）/ af_alg2（前复权因子）

复权价计算（已用 baostock 前复权价交叉验证一致）：
  前复权价(qfq) = 未复权价 × af_alg2 / af_alg2_latest
  后复权价(hfq) = 未复权价 × af_alg1 / af_alg1_latest
  （af_alg1_latest / af_alg2_latest 为该股最新交易日的复权因子值）

技术指标 MACD/KDJ/RSI/BOLL/CCI：本地 app.utils.tdxFunction 计算。

写入目标表：stock_int.tb_stk_factor（35 字段，与 Tushare stk_factor 一一对应）。

特性：
  - 断点续传：已入库 ts_code 自动跳过（--force 覆盖）。
  - 批量 SQL 读取 + 批量写入，速度快。
  - 北交所（exchg='北交所'）同样覆盖。

用法（在项目根目录下执行）：
    python -m app.demo.sync_stk_factor_from_ths --limit 20      # 试点
    python -m app.demo.sync_stk_factor_from_ths                 # 全量
    python -m app.demo.sync_stk_factor_from_ths --codes 000001.SZ,920964.BJ
    python -m app.demo.sync_stk_factor_from_ths --force
    python -m app.demo.sync_stk_factor_from_ths --start 20150101
"""
import sys
import os
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pymysql
import numpy as np
import pandas as pd

from app.utils import tdxFunction as tdx

# ==================== 远程同花顺库 ====================
REMOTE_HOST = '39.96.14.212'
REMOTE_PORT = 53410
REMOTE_USER = 'hsjydb'
REMOTE_PASSWORD = os.getenv('THS_SYNC_DB_PASSWORD', '')

# ==================== 本地数据库 ====================
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = os.getenv('LOCAL_DB_PASSWORD', '')
MYSQL_DB = 'stock_int'

# 交易所 -> 后缀
EXCHG_SUFFIX_MAP = {
    '上交所': '.SH',
    '深交所': '.SZ',
    '北交所': '.BJ',
}


def get_local_db():
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8mb4',
    )


def get_remote_db():
    return pymysql.connect(
        host=REMOTE_HOST, port=REMOTE_PORT, user=REMOTE_USER,
        password=REMOTE_PASSWORD, charset='utf8mb4',
        connect_timeout=10, read_timeout=60,
    )


def get_stock_pool(conn, codes=None, limit=None):
    """从本地 tb_secumain 读股票池，返回 full_code 列表（如 000001.SZ）"""
    sql = "SELECT full_code FROM tb_secumain WHERE full_code IS NOT NULL AND full_code != ''"
    if codes:
        sql += " AND full_code IN ({})".format(','.join(['%s'] * len(codes)))
        params = list(codes)
    else:
        params = []
    sql += " ORDER BY full_code"
    if limit:
        sql += f" LIMIT {limit}"
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    return rows


def get_done_codes(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT ts_code FROM tb_stk_factor")
    rows = {r[0] for r in cur.fetchall()}
    cur.close()
    return rows


def calc_indicators(df):
    """用 tdxFunction 计算技术指标，输入 df 按日期升序，含 open/high/low/close"""
    close = df['close'].values.astype(float)
    high = df['high'].values.astype(float)
    low = df['low'].values.astype(float)

    dif, dea, macd = tdx.MACD(close)
    k, d, j = tdx.KDJ(close, high, low)
    rsi6 = tdx.RSI(close, 6)
    rsi12 = tdx.RSI(close, 12)
    rsi24 = tdx.RSI(close, 24)
    boll_upper, boll_mid, boll_lower = tdx.BOLL(close)
    cci = tdx.CCI(close, high, low)

    return {
        'macd_dif': dif, 'macd_dea': dea, 'macd': macd,
        'kdj_k': k, 'kdj_d': d, 'kdj_j': j,
        'rsi_6': rsi6, 'rsi_12': rsi12, 'rsi_24': rsi24,
        'boll_upper': boll_upper, 'boll_mid': boll_mid, 'boll_lower': boll_lower,
        'cci': cci,
    }


def fetch_remote_stock(rconn, sec_code, start_date):
    """从远程同花顺库拉取单只股票全部日线，返回 DataFrame（按日期升序）"""
    cur = rconn.cursor()
    sql = """
        SELECT td_date, exchg, pre_close, open_price, high_trans, low_trans,
               latest_trans, trans_vol, trans_amt_rmb, af_alg1, af_alg2, chg_ratio
        FROM thsdb.shsz_stock_daily_quotation
        WHERE sec_code = %s AND td_date >= %s AND isvalid = 1
        ORDER BY td_date ASC
    """
    cur.execute(sql, (sec_code, datetime.datetime.strptime(start_date, '%Y%m%d')))
    rows = cur.fetchall()
    cur.close()
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=[
        'td_date', 'exchg', 'pre_close', 'open', 'high', 'low',
        'close', 'vol', 'amount', 'af_alg1', 'af_alg2', 'pct_change',
    ])
    # 数值列转 float
    for col in ['pre_close', 'open', 'high', 'low', 'close', 'vol', 'amount', 'af_alg1', 'af_alg2', 'pct_change']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['td_date'] = df['td_date'].astype(str).str[:10].str.replace('-', '')
    # 远程库可能存在同一交易日多条记录（历史遗留），按 td_date 去重，保留最后一条
    df = df.drop_duplicates(subset=['td_date'], keep='last').reset_index(drop=True)
    return df


def process_one_stock(local, full_code, start_date='19900101', force=False):
    """处理单只股票，返回 (写入条数, 状态)。远程连接每次独立创建，避免长连接超时。"""
    code, suffix = full_code.rsplit('.', 1)
    suffix = suffix.upper()

    # 1. 远程拉取（独立连接，用完即关，规避公网长连接中断）
    remote = get_remote_db()
    try:
        df = fetch_remote_stock(remote, code, start_date)
    finally:
        remote.close()
    if df.empty:
        return 0, 'remote_empty'

    # 2. 复权价：
    #    后复权价(hfq) = 未复权价 × af_alg1（af_alg1 从上市首日 1.0 累积，首日价不变）
    #    前复权价(qfq) = 未复权价 × af_alg2 / af_alg2_latest（最新日价不变）
    #    af_alg2_latest 为该股最新交易日的 af_alg2 值
    af1_latest = df['af_alg1'].iloc[-1]
    af2_latest = df['af_alg2'].iloc[-1]

    for col in ['open', 'high', 'low', 'close']:
        df[f'{col}_hfq'] = df[col] * df['af_alg1']
        df[f'{col}_qfq'] = df[col] * df['af_alg2'] / af2_latest if af2_latest else df[col]

    # 3. 涨跌额
    df['change'] = df['close'] - df['pre_close']

    # 涨跌幅兜底：远程 chg_ratio 缺失时，用 change/pre_close 计算
    #（远程库 chg_ratio 字段大面积为空，但有 pre_close 即可反推）
    mask = df['pct_change'].isna() & df['pre_close'].notna() & (df['pre_close'].fillna(0) != 0)
    df.loc[mask, 'pct_change'] = df.loc[mask, 'change'] / df.loc[mask, 'pre_close'] * 100

    # 4. 技术指标
    indicators = calc_indicators(df)

    # 5. 组装写入
    insert_sql = """
        INSERT INTO tb_stk_factor
        (ts_code, trade_date, open, high, low, close, pre_close, `change`, pct_change,
         vol, amount, adj_factor,
         open_hfq, open_qfq, close_hfq, close_qfq, high_hfq, high_qfq, low_hfq, low_qfq,
         pre_close_hfq, pre_close_qfq,
         macd_dif, macd_dea, macd, kdj_k, kdj_d, kdj_j, rsi_6, rsi_12, rsi_24,
         boll_upper, boll_mid, boll_lower, cci)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

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

    rows = []
    for i in range(len(df)):
        r = df.iloc[i]
        dt = datetime.datetime.strptime(str(r['td_date']), '%Y%m%d')

        # 前复权价作为 adj_factor 的补充（af_alg2 即为前复权因子）
        ind = indicators
        row = (
            full_code, dt,
            _f(r['open']), _f(r['high']), _f(r['low']), _f(r['close']),
            _f(r['pre_close']), _f(r['change']), _f(r['pct_change']),
            _f(r['vol']) / 100.0 if _f(r['vol']) is not None else None,        # 股 -> 手
            _f(r['amount']) / 1000.0 if _f(r['amount']) is not None else None, # 元 -> 千元
            _f(r['af_alg2']),  # adj_factor：前复权因子
            _f(r['open_hfq']), _f(r['open_qfq']), _f(r['close_hfq']), _f(r['close_qfq']),
            _f(r['high_hfq']), _f(r['high_qfq']), _f(r['low_hfq']), _f(r['low_qfq']),
            None, None,  # pre_close_hfq / pre_close_qfq 暂留空
            _f(ind['macd_dif'][i]), _f(ind['macd_dea'][i]), _f(ind['macd'][i]),
            _f(ind['kdj_k'][i]), _f(ind['kdj_d'][i]), _f(ind['kdj_j'][i]),
            _f(ind['rsi_6'][i]), _f(ind['rsi_12'][i]), _f(ind['rsi_24'][i]),
            _f(ind['boll_upper'][i]), _f(ind['boll_mid'][i]), _f(ind['boll_lower'][i]),
            _f(ind['cci'][i]),
        )
        rows.append(row)

    if not rows:
        return 0, 'no_rows'

    cur = local.cursor()
    if force:
        cur.execute("DELETE FROM tb_stk_factor WHERE ts_code = %s", (full_code,))
    cur.executemany(insert_sql, rows)
    local.commit()
    cur.close()
    return len(rows), 'ok'


def main():
    parser = argparse.ArgumentParser(description='补齐 tb_stk_factor 历史数据（远程同花顺库）')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--codes', type=str, default=None)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--start', type=str, default='19900101')
    args = parser.parse_args()

    local = get_local_db()

    codes = [c.strip() for c in args.codes.split(',')] if args.codes else None
    pool = get_stock_pool(local, codes=codes, limit=args.limit)
    print(f'股票池共 {len(pool)} 只')

    done = get_done_codes(local) if not args.force else set()
    print(f'已入库 {len(done)} 只（--force 则忽略）')

    total = len(pool)
    success = skipped = failed = 0

    try:
        for idx, full_code in enumerate(pool, 1):
            if not args.force and full_code in done:
                skipped += 1
                continue

            try:
                n, status = process_one_stock(local, full_code, args.start, args.force)
                if status == 'ok':
                    print(f'[{idx}/{total}] {full_code} -> {n} 条')
                    success += 1
                else:
                    print(f'[{idx}/{total}] {full_code} -> {status}')
                    failed += 1
            except Exception as e:
                print(f'[{idx}/{total}] {full_code} 失败: {type(e).__name__}: {e}')
                failed += 1

            if idx % 50 == 0:
                print(f'--- 进度 {idx}/{total} | 成功{success} 跳过{skipped} 失败{failed} ---')
    finally:
        local.close()

    print(f'\n完成！总计 {total}，成功 {success}，跳过 {skipped}，失败 {failed}')


if __name__ == '__main__':
    main()
