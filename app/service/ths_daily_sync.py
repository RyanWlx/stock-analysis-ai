# -*- coding: utf-8 -*-
"""
每日「当天」行情同步服务（同花顺 -> tb_daliy / tb_stk_factor）。

背景：
    原每日同步走 Tushare（job_service.getStockListFromDB），因 Tushare 限速已停用。
    本模块改从「同花顺/聚源托管库」远程库 thsdb.shsz_stock_daily_quotation 抓取
    「当天」全部 A 股行情，写入本地/生产库的两张表：

    - tb_daliy     : 未复权 OHLCV + pre_close + change + pct_change
                     （对标 Tushare daily，10 个业务字段）
    - tb_stk_factor: 35 字段，含前/后复权价、复权因子、MACD/KDJ/RSI/BOLL/CCI
                     （对标 Tushare stk_factor）
    - tb_weekly    : 当周周线（由 tb_daliy 当周数据聚合，对标 Tushare weekly）
    - tb_monthly   : 当月月线（由 tb_daliy 当月数据聚合，对标 Tushare monthly）

口径与历史同步脚本 app/demo/sync_stk_factor_from_ths.py 完全一致：
    * 成交量 股 -> 手 (/100)；成交额 元 -> 千元 (/1000)
    * 前复权价 qfq = 原价 × af_alg2 / af_alg2_latest；当天为最新交易日，故 qfq = 原价
    * 后复权价 hfq = 原价 × af_alg1
    * 技术指标：用「本地 tb_stk_factor 最近若干交易日历史 + 当天 bar」计算，保证连续
    * 涨跌幅缺失时用 (close-pre_close)/pre_close*100 兜底

数据库连接：
    默认复用项目配置 app/config/db_config.py 的 SQLALCHEMY_DB_URL（生产为阿里云 RDS，
    与 FastAPI 的 ORM 使用同一个库）。本地联调可用环境变量覆盖：
        THS_SYNC_DB_HOST / PORT / USER / PASSWORD / DB

用法（项目根目录）：
    python -m app.service.ths_daily_sync               # 同步「今天」
    python -m app.service.ths_daily_sync --date 20261016
    python -m app.service.ths_daily_sync --dry-run     # 只统计不写库
    python -m app.service.ths_daily_sync --limit 20    # 只处理前 20 只（联调）
"""
import os
import sys
import time
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pymysql
from sqlalchemy.engine.url import make_url

from app.utils import tdxFunction as tdx
from app.config.log_config import logger
from app.config.env_config import load_env

load_env()  # 加载项目根目录 .env（本地凭证，勿提交），保证远程同花顺源库密码可用

# ==================== 远程同花顺库 ====================
REMOTE = dict(
    host='39.96.14.212', port=53410, user='hsjydb', password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
    database='hsjydb', charset='utf8mb4', connect_timeout=30, read_timeout=300,
)

# 交易所中文名 <-> 后缀
EXCHG_CN_BY_SUFFIX = {'.SH': '上交所', '.SZ': '深交所', '.BJ': '北交所'}
# 指标历史回看（自然日）。~200 个交易日，足够 MACD/RSI24/BOLL20/CCI14 收敛
INDICATOR_LOOKBACK_DAYS = 300
# 计算指标时本地历史读取的 ts_code 批大小
CODE_BATCH = 400


# ==================== 连接 ====================
def get_local_params():
    """本地/生产库连接参数：默认取项目 db_config 的 SQLALCHEMY_DB_URL，env 可覆盖。"""
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


def get_local_db():
    return pymysql.connect(**get_local_params(), connect_timeout=20)


def get_remote_db():
    return pymysql.connect(**REMOTE)


# ==================== 股票池 ====================
def load_universe(lconn):
    """返回 {(symbol, exchg_cn): ts_code}，仅当前上市股票。
    优先用 stock_basic(list_status='L')，不存在时回退 tb_secumain(listed_state=1)。"""
    cur = lconn.cursor()
    rows = []
    try:
        cur.execute("SELECT symbol, ts_code FROM stock_basic WHERE list_status='L'")
        rows = cur.fetchall()
        src = 'stock_basic'
    except Exception:
        rows = []
    if not rows:
        try:
            cur.execute("SELECT secu_code, full_code FROM tb_secumain WHERE full_code IS NOT NULL AND full_code<>'' AND listed_state=1")
            rows = cur.fetchall()
            src = 'tb_secumain'
        except Exception:
            rows = []
            src = 'none'
    cur.close()

    universe = {}
    for symbol, ts_code in rows:
        if not symbol or not ts_code or '.' not in ts_code:
            continue
        suffix = '.' + ts_code.rsplit('.', 1)[1].upper()
        exchg_cn = EXCHG_CN_BY_SUFFIX.get(suffix)
        if exchg_cn:
            universe[(str(symbol).strip(), exchg_cn)] = ts_code.strip()
    logger.info(f'股票池来源 {src}，上市代码 {len(universe)} 只')
    return universe


# ==================== 远程当天行情 ====================
def fetch_remote_day(rconn, trade_date):
    """拉取指定交易日的全部证券行情，返回 {(sec_code, exchg): row_dict}（同键去重保留最后一条）。"""
    cur = rconn.cursor()
    sql = """
        SELECT sec_code, exchg, pre_close, open_price, high_trans, low_trans,
               latest_trans, trans_vol, trans_amt_rmb, af_alg1, af_alg2, chg_ratio,
               turnover_ratio
        FROM thsdb.shsz_stock_daily_quotation
        WHERE td_date = %s AND isvalid = 1
    """
    cur.execute(sql, (trade_date,))
    rows = cur.fetchall()
    cur.close()
    out = {}
    for sec_code, exchg, pre_close, o, h, l, c, vol, amt, af1, af2, chg, tr in rows:
        out[(str(sec_code).strip(), (exchg or '').strip())] = (
            pre_close, o, h, l, c, vol, amt, af1, af2, chg, tr
        )
    return out, len(rows)


# ==================== 指标历史 ====================
def load_history(lconn, ts_codes, before_date, lookback_days):
    """批量读取 <before_date 的最近 lookback_days 自然日内的 high/low/close（升序）。
    返回 {ts_code: [(high, low, close), ...]}"""
    if not ts_codes:
        return {}
    start = before_date - datetime.timedelta(days=lookback_days)
    result = {}
    cur = lconn.cursor()
    codes = list(ts_codes)
    for i in range(0, len(codes), CODE_BATCH):
        chunk = codes[i:i + CODE_BATCH]
        ph = ','.join(['%s'] * len(chunk))
        sql = f"""
            SELECT ts_code, high, low, close
            FROM tb_stk_factor
            WHERE ts_code IN ({ph}) AND trade_date >= %s AND trade_date < %s
            ORDER BY ts_code, trade_date ASC
        """
        cur.execute(sql, chunk + [start, before_date])
        for code, high, low, close in cur.fetchall():
            if high is None or low is None or close is None:
                continue
            result.setdefault(code, []).append((float(high), float(low), float(close)))
    cur.close()
    return result


def _last(a):
    """取序列最后一个值，NaN/异常返回 None。"""
    try:
        v = float(np.asarray(a)[-1])
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    except Exception:
        return None


def compute_indicator_last(hist, today_hlc):
    """用历史 + 当天 bar 计算技术指标，返回最后一根（当天）的值。"""
    highs = [x[0] for x in hist] + [today_hlc[0]]
    lows = [x[1] for x in hist] + [today_hlc[1]]
    closes = [x[2] for x in hist] + [today_hlc[2]]
    close = np.array(closes, dtype=float)
    high = np.array(highs, dtype=float)
    low = np.array(lows, dtype=float)

    dif, dea, macd = tdx.MACD(close)
    k, d, j = tdx.KDJ(close, high, low)
    rsi6 = tdx.RSI(close, 6)
    rsi12 = tdx.RSI(close, 12)
    rsi24 = tdx.RSI(close, 24)
    bu, bm, bl = tdx.BOLL(close)
    cci = tdx.CCI(close, high, low)
    return dict(macd_dif=_last(dif), macd_dea=_last(dea), macd=_last(macd),
                kdj_k=_last(k), kdj_d=_last(d), kdj_j=_last(j),
                rsi_6=_last(rsi6), rsi_12=_last(rsi12), rsi_24=_last(rsi24),
                boll_upper=_last(bu), boll_mid=_last(bm), boll_lower=_last(bl),
                cci=_last(cci))


# ==================== 写库 ====================
DALIY_SQL = """
    INSERT INTO tb_daliy
    (ts_code, trade_date, open, high, low, close, pre_close, `change`, pct_change, vol, amount,
     turnover_rate, turnover_rate_f)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        open=VALUES(open), high=VALUES(high), low=VALUES(low), close=VALUES(close),
        pre_close=VALUES(pre_close), `change`=VALUES(`change`), pct_change=VALUES(pct_change),
        vol=VALUES(vol), amount=VALUES(amount),
        turnover_rate=VALUES(turnover_rate), turnover_rate_f=VALUES(turnover_rate_f)
"""

FACTOR_SQL = """
    INSERT INTO tb_stk_factor
    (ts_code, trade_date, open, high, low, close, pre_close, `change`, pct_change,
     vol, amount, adj_factor,
     open_hfq, open_qfq, close_hfq, close_qfq, high_hfq, high_qfq, low_hfq, low_qfq,
     pre_close_hfq, pre_close_qfq,
     macd_dif, macd_dea, macd, kdj_k, kdj_d, kdj_j, rsi_6, rsi_12, rsi_24,
     boll_upper, boll_mid, boll_lower, cci)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        open=VALUES(open), high=VALUES(high), low=VALUES(low), close=VALUES(close),
        pre_close=VALUES(pre_close), `change`=VALUES(`change`), pct_change=VALUES(pct_change),
        vol=VALUES(vol), amount=VALUES(amount), adj_factor=VALUES(adj_factor),
        open_hfq=VALUES(open_hfq), open_qfq=VALUES(open_qfq),
        close_hfq=VALUES(close_hfq), close_qfq=VALUES(close_qfq),
        high_hfq=VALUES(high_hfq), high_qfq=VALUES(high_qfq),
        low_hfq=VALUES(low_hfq), low_qfq=VALUES(low_qfq),
        macd_dif=VALUES(macd_dif), macd_dea=VALUES(macd_dea), macd=VALUES(macd),
        kdj_k=VALUES(kdj_k), kdj_d=VALUES(kdj_d), kdj_j=VALUES(kdj_j),
        rsi_6=VALUES(rsi_6), rsi_12=VALUES(rsi_12), rsi_24=VALUES(rsi_24),
        boll_upper=VALUES(boll_upper), boll_mid=VALUES(boll_mid), boll_lower=VALUES(boll_lower),
        cci=VALUES(cci)
"""

WEEKLY_SQL = """
    INSERT INTO tb_weekly
    (ts_code, trade_date, open, high, low, close, pre_close, `change`, pct_change, vol, amount)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        open=VALUES(open), high=VALUES(high), low=VALUES(low), close=VALUES(close),
        pre_close=VALUES(pre_close), `change`=VALUES(`change`), pct_change=VALUES(pct_change),
        vol=VALUES(vol), amount=VALUES(amount)
"""

MONTHLY_SQL = """
    INSERT INTO tb_monthly
    (ts_code, trade_date, open, high, low, close, pre_close, `change`, pct_change, vol, amount)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        open=VALUES(open), high=VALUES(high), low=VALUES(low), close=VALUES(close),
        pre_close=VALUES(pre_close), `change`=VALUES(`change`), pct_change=VALUES(pct_change),
        vol=VALUES(vol), amount=VALUES(amount)
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


def _agg_period(bars, pre_close):
    """把一段时间内（按日期升序）的日线 bars 聚合为一条周线/月线。
    bars: [(ts_code, trade_date, open, high, low, close, vol, amount), ...]
    返回 (trade_date, open, high, low, close, pre_close, change, pct_change, vol, amount)。
    """
    trade_date = max(b[1] for b in bars)
    o = _f(bars[0][2])                                   # 首日开盘
    highs = [_f(b[3]) for b in bars if b[3] is not None]
    lows = [_f(b[4]) for b in bars if b[4] is not None]
    h = max(highs) if highs else None
    l = min(lows) if lows else None
    c = _f(bars[-1][5])                                  # 末日收盘
    vols = [_f(b[6]) for b in bars if b[6] is not None]
    amts = [_f(b[7]) for b in bars if b[7] is not None]
    vol = sum(vols) if vols else None
    amt = sum(amts) if amts else None
    change = (c - pre_close) if (c is not None and pre_close is not None) else None
    pct = (change / pre_close * 100.0) if (change is not None and pre_close not in (None, 0)) else None
    return trade_date, o, h, l, c, pre_close, change, pct, vol, amt


def update_period_bars(td, codes=None):
    """基于 tb_daliy 重算并覆盖「当周」「当月」的 tb_weekly / tb_monthly 行。

    codes: 本次同步涉及的 ts_code（当天有交易的股票）；None 时从 tb_daliy 取当天全部。
    按 ts_code 分批（走主键 (ts_code,trade_date)，避免 trade_date 全表扫描）：
    每批先删除该批股票当周/当月旧 bar，再插入按日线聚合的新 bar，
    保证「当周/当月」每个周期只有一条记录（trade_date 随最新交易日推进）。
    返回 {'weekly': n, 'monthly': n}。
    """
    # 统一用 datetime（tb_daliy.trade_date 为 datetime 列，避免 date/datetime 比较失败）
    td_dt = datetime.datetime(td.year, td.month, td.day)
    week_start = td_dt - datetime.timedelta(days=td.weekday())      # 周一
    week_end = week_start + datetime.timedelta(days=6)              # 周日
    month_start = datetime.datetime(td.year, td.month, 1)
    next_month = (datetime.datetime(td.year + 1, 1, 1)
                  if td.month == 12 else datetime.datetime(td.year, td.month + 1, 1))
    month_end = next_month - datetime.timedelta(days=1)
    fetch_start = month_start - datetime.timedelta(days=15)         # 覆盖 pre_close 回看

    lconn = get_local_db()
    n_weekly = n_monthly = 0
    try:
        cur = lconn.cursor()
        if not codes:
            cur.execute("SELECT DISTINCT ts_code FROM tb_daliy WHERE trade_date=%s", (td_dt,))
            codes = [r[0] for r in cur.fetchall()]
        codes = list(dict.fromkeys(codes))
        if not codes:
            cur.close()
            return {'weekly': 0, 'monthly': 0}

        for i in range(0, len(codes), 500):
            batch = codes[i:i + 500]
            ph = ','.join(['%s'] * len(batch))
            cur.execute(
                f"SELECT ts_code, trade_date, open, high, low, close, vol, amount "
                f"FROM tb_daliy WHERE ts_code IN ({ph}) AND trade_date >= %s AND trade_date <= %s "
                f"ORDER BY ts_code, trade_date ASC",
                batch + [fetch_start, td_dt],
            )
            by_code, traded = {}, set()
            for r in cur.fetchall():
                by_code.setdefault(r[0], []).append(r)
                if r[1] == td_dt:
                    traded.add(r[0])
            if not traded:
                continue

            wrows, mrows = [], []
            for code in traded:
                bars = by_code.get(code, [])
                if not bars:
                    continue
                mbars = [b for b in bars if month_start <= b[1] <= td_dt]
                if mbars:
                    prev = [b for b in bars if b[1] < month_start]
                    pre = _f(prev[-1][5]) if prev else None
                    mrows.append((code,) + _agg_period(mbars, pre))
                wbars = [b for b in bars if week_start <= b[1] <= td_dt]
                if wbars:
                    prev = [b for b in bars if b[1] < week_start]
                    pre = _f(prev[-1][5]) if prev else None
                    wrows.append((code,) + _agg_period(wbars, pre))

            # 删除该批股票当周/当月旧 bar（按周期全范围，保证一个周期一条）
            cur.execute(
                f"DELETE FROM tb_weekly WHERE ts_code IN ({ph}) AND trade_date>=%s AND trade_date<=%s",
                batch + [week_start, week_end],
            )
            cur.execute(
                f"DELETE FROM tb_monthly WHERE ts_code IN ({ph}) AND trade_date>=%s AND trade_date<=%s",
                batch + [month_start, month_end],
            )
            if wrows:
                cur.executemany(WEEKLY_SQL, wrows)
                n_weekly += len(wrows)
            if mrows:
                cur.executemany(MONTHLY_SQL, mrows)
                n_monthly += len(mrows)
            lconn.commit()
        cur.close()
    finally:
        lconn.close()
    return {'weekly': n_weekly, 'monthly': n_monthly}


def sync_daily(trade_date=None, dry_run=False, limit=None):
    """同步指定交易日（默认今天）的 A 股行情到 tb_daliy / tb_stk_factor。

    参数:
        trade_date: datetime.date 或 'YYYYMMDD' / 'YYYY-MM-DD'，默认今天
        dry_run   : True 只统计不写库
        limit     : 仅处理前 N 只（联调用）
    返回: dict 统计信息
    """
    t0 = time.time()
    # 解析交易日
    if trade_date is None:
        td = datetime.date.today()
    elif isinstance(trade_date, datetime.datetime):
        td = trade_date.date()
    elif isinstance(trade_date, datetime.date):
        td = trade_date
    else:
        s = str(trade_date).replace('-', '')
        td = datetime.datetime.strptime(s, '%Y%m%d').date()

    summary = dict(trade_date=str(td), remote_rows=0, matched=0,
                   daliy_rows=0, factor_rows=0, skipped=0, dry_run=dry_run)

    # 1) 远程当天数据（公网库偶发超时，重试 3 次）
    remote_map, raw_n, last_err = {}, 0, None
    for attempt in range(1, 4):
        try:
            remote = get_remote_db()
            try:
                remote_map, raw_n = fetch_remote_day(remote, td)
            finally:
                remote.close()
            last_err = None
            break
        except Exception as e:
            last_err = e
            logger.warning(f'[{td}] 远程同花顺库连接失败（第 {attempt}/3 次）：{type(e).__name__}: {e}')
            if attempt < 3:
                time.sleep(30)
    if last_err is not None:
        logger.error(f'[{td}] 远程同花顺库多次连接失败，放弃本次同步：{last_err}')
        summary['error'] = f'{type(last_err).__name__}: {last_err}'
        return summary
    summary['remote_rows'] = raw_n
    logger.info(f'[{td}] 远程当天记录 {raw_n} 条（去重后 {len(remote_map)} 个 sec_code+exchg）')
    if not remote_map:
        msg = f'[{td}] 远程无当天数据（非交易日或尚未更新），跳过。'
        logger.warning(msg)
        print(msg)
        return summary

    # 2) 本地股票池 & 匹配
    lconn = get_local_db()
    try:
        universe = load_universe(lconn)

        # 3) 组装当天原始记录
        matched = []  # (ts_code, today_hlc, raw_dict)
        for (sec_code, exchg), vals in remote_map.items():
            ts_code = universe.get((sec_code, exchg))
            if not ts_code:
                continue
            pre_close, o, h, l, c, vol, amt, af1, af2, chg, tr = vals
            if c is None or h is None or l is None:
                summary['skipped'] += 1
                continue
            matched.append((ts_code, (float(h), float(l), float(c)),
                            dict(pre_close=_f(pre_close), open=_f(o), high=_f(h), low=_f(l),
                                 close=_f(c), vol=_f(vol), amount=_f(amt),
                                 af1=_f(af1), af2=_f(af2), chg=_f(chg), turnover=_f(tr))))
            if limit and len(matched) >= limit:
                break
        summary['matched'] = len(matched)
        logger.info(f'[{td}] 匹配到股票池内股票 {len(matched)} 只')

        # 4) 指标历史（< 当天）
        hist = load_history(lconn, [m[0] for m in matched], td, INDICATOR_LOOKBACK_DAYS)
        logger.info(f'[{td}] 加载指标历史股票 {len(hist)} 只')
    finally:
        lconn.close()

    # 5) 计算指标 + 组装两张表
    daliy_rows, factor_rows = [], []
    ind_missing = 0
    for ts_code, (h, l, c), r in matched:
        pre_close = r['pre_close']
        close = r['close']
        change = (close - pre_close) if (close is not None and pre_close is not None) else None
        pct = r['chg']
        if pct is None and change is not None and pre_close not in (None, 0):
            pct = change / pre_close * 100.0
        vol_hand = r['vol'] / 100.0 if r['vol'] is not None else None      # 股->手
        amount_k = r['amount'] / 1000.0 if r['amount'] is not None else None  # 元->千元
        af1, af2 = r['af1'], r['af2']
        turnover = r.get('turnover')                                       # 换手率（%）
        # 当天为最新交易日：qfq=原价；hfq=原价×af_alg1
        o, hi, lo, cl = r['open'], r['high'], r['low'], r['close']

        def hfq(x):
            return x * af1 if (x is not None and af1 is not None) else None

        daliy_rows.append((ts_code, td, o, hi, lo, cl, pre_close, change, pct, vol_hand, amount_k,
                           turnover, turnover))

        ind = compute_indicator_last(hist.get(ts_code, []), (h, l, c))
        if ind.get('macd') is None:
            ind_missing += 1
        factor_rows.append((
            ts_code, td, o, hi, lo, cl, pre_close, change, pct, vol_hand, amount_k,
            af2,
            hfq(o), o, hfq(cl), cl, hfq(hi), hi, hfq(lo), lo,   # open/close/high/low hfq,qfq
            None, None,                                         # pre_close_hfq/qfq
            ind['macd_dif'], ind['macd_dea'], ind['macd'],
            ind['kdj_k'], ind['kdj_d'], ind['kdj_j'],
            ind['rsi_6'], ind['rsi_12'], ind['rsi_24'],
            ind['boll_upper'], ind['boll_mid'], ind['boll_lower'],
            ind['cci'],
        ))

    summary['daliy_rows'] = len(daliy_rows)
    summary['factor_rows'] = len(factor_rows)

    if dry_run:
        print(f'[dry-run] {td} 可写入 tb_daliy {len(daliy_rows)} 行 / tb_stk_factor {len(factor_rows)} 行'
              f'（指标缺失 {ind_missing}）')
        logger.info(f'[dry-run] {summary}')
        return summary

    # 6) 写库
    lconn = get_local_db()
    try:
        cur = lconn.cursor()
        if daliy_rows:
            cur.executemany(DALIY_SQL, daliy_rows)
            lconn.commit()
        if factor_rows:
            cur.executemany(FACTOR_SQL, factor_rows)
            lconn.commit()
        cur.close()
    finally:
        lconn.close()

    # 7) 同步更新「当周」「当月」的 tb_weekly / tb_monthly
    try:
        pb = update_period_bars(td, [m[0] for m in matched])
        summary['weekly_rows'] = pb['weekly']
        summary['monthly_rows'] = pb['monthly']
        logger.info(f'[{td}] 周线 {pb["weekly"]} 行 / 月线 {pb["monthly"]} 行 更新完成')
    except Exception as e:
        summary['period_error'] = f'{type(e).__name__}: {e}'
        logger.warning(f'[{td}] 周线/月线更新失败（不影响日线同步）：{type(e).__name__}: {e}')

    summary['elapsed'] = round(time.time() - t0, 1)
    logger.info(f'[{td}] 同步完成 {summary}')
    print(f"[完成] {td} 写入 tb_daliy {len(daliy_rows)} 行 / tb_stk_factor {len(factor_rows)} 行，"
          f"周线 {summary.get('weekly_rows', 0)} 行 / 月线 {summary.get('monthly_rows', 0)} 行，"
          f"耗时 {summary['elapsed']}s（指标缺失 {ind_missing}）")
    return summary


def main():
    ap = argparse.ArgumentParser(description='同花顺当天行情 -> tb_daliy / tb_stk_factor')
    ap.add_argument('--date', type=str, default=None, help='交易日 YYYYMMDD，默认今天')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=None)
    args = ap.parse_args()
    sync_daily(trade_date=args.date, dry_run=args.dry_run, limit=args.limit)


if __name__ == '__main__':
    main()
