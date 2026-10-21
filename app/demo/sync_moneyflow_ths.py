# -*- coding: utf-8 -*-
"""
同花顺 个股资金流向 -> tb_moneyflow_ths（对标 Tushare moneyflow_ths，doc_id=348）。

数据源：同花顺数据中心 data.10jqka.com.cn 个股资金流向「即时」榜单（免费）。
    URL: /funds/ggzjl/field/zljlr/order/desc/page/{n}/ajax/1/free/1/
    经 akshare.stock_fund_flow_individual(symbol="即时") 抓取（自动分页 + GBK 解码）。

免费同花顺网页口径说明（重要）：
    - 仅提供「当日/最新一期」的【主力资金净额】榜单，字段：代码/名称/最新价/涨跌幅/换手率/流入/流出/净额/成交额。
    - 没有大单/中单/小单净流入分解，也没有历史逐日（带日期参数会被同花顺反爬 401 拦截）。
    因此 tb_moneyflow_ths 中以下字段留空（免费渠道无数据）：
        net_d5_amount / buy_lg_amount(+rate) / buy_md_amount(+rate) / buy_sm_amount(+rate)
    可填充字段：trade_date、ts_code、name、pct_change、latest、net_amount（= 主力净额，换算为万元）。

特性：
    - 建表：CREATE TABLE IF NOT EXISTS（13 字段 + PK (ts_code, trade_date)）
    - 幂等：ON DUPLICATE KEY UPDATE
    - 可每日盘后运行，逐日累积（需每日抓取，无法补历史）

用法（项目根目录）：
    python -m app.demo.sync_moneyflow_ths [--trade-date YYYYMMDD] [--dry-run]
"""
import sys
import os
import time
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pymysql
from sqlalchemy.engine.url import make_url

DDL = """
CREATE TABLE IF NOT EXISTS tb_moneyflow_ths (
    ts_code            varchar(90)  NOT NULL COMMENT '股票代码',
    trade_date         datetime     NOT NULL COMMENT '交易日期',
    name               varchar(60)  DEFAULT NULL COMMENT '股票名称',
    pct_change         decimal(24,6) DEFAULT NULL COMMENT '涨跌幅(%)',
    latest             decimal(24,6) DEFAULT NULL COMMENT '最新价',
    net_amount         decimal(24,6) DEFAULT NULL COMMENT '资金净流入(万元，同花顺口径为主力净额)',
    net_d5_amount      decimal(24,6) DEFAULT NULL COMMENT '5日主力净额(万元)',
    buy_lg_amount      decimal(24,6) DEFAULT NULL COMMENT '今日大单净流入额(万元)',
    buy_lg_amount_rate decimal(24,6) DEFAULT NULL COMMENT '今日大单净流入占比(%)',
    buy_md_amount      decimal(24,6) DEFAULT NULL COMMENT '今日中单净流入额(万元)',
    buy_md_amount_rate decimal(24,6) DEFAULT NULL COMMENT '今日中单净流入占比(%)',
    buy_sm_amount      decimal(24,6) DEFAULT NULL COMMENT '今日小单净流入额(万元)',
    buy_sm_amount_rate decimal(24,6) DEFAULT NULL COMMENT '今日小单净流入占比(%)',
    PRIMARY KEY (ts_code, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='同花顺个股资金流向(即时榜单)'
"""

UPSERT_SQL = """
INSERT INTO tb_moneyflow_ths
(ts_code, trade_date, name, pct_change, latest, net_amount,
 net_d5_amount, buy_lg_amount, buy_lg_amount_rate, buy_md_amount, buy_md_amount_rate,
 buy_sm_amount, buy_sm_amount_rate)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
 name=VALUES(name), pct_change=VALUES(pct_change), latest=VALUES(latest),
 net_amount=VALUES(net_amount), net_d5_amount=VALUES(net_d5_amount),
 buy_lg_amount=VALUES(buy_lg_amount), buy_lg_amount_rate=VALUES(buy_lg_amount_rate),
 buy_md_amount=VALUES(buy_md_amount), buy_md_amount_rate=VALUES(buy_md_amount_rate),
 buy_sm_amount=VALUES(buy_sm_amount), buy_sm_amount_rate=VALUES(buy_sm_amount_rate)
"""


def get_local_params():
    env_host = os.getenv('THS_SYNC_DB_HOST')
    if env_host:
        return dict(
            host=env_host, port=int(os.getenv('THS_SYNC_DB_PORT', '3306')),
            user=os.getenv('THS_SYNC_DB_USER', 'root'),
            password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
            database=os.getenv('THS_SYNC_DB_DB', 'stock_int'), charset='utf8mb4',
        )
    from app.config.db_config import SQLALCHEMY_DB_URL
    u = make_url(SQLALCHEMY_DB_URL)
    return dict(host=u.host, port=u.port or 3306, user=u.username,
                password=u.password or '', database=u.database, charset='utf8mb4')


def parse_amount(s):
    """把同花顺金额字符串('1.77亿'/'94.36万'/'6000.30万')转成 万元(float)。"""
    if s is None:
        return None
    s = str(s).strip().replace(',', '')
    if s in ('', '--', '-', 'None', 'nan'):
        return None
    try:
        if s.endswith('亿'):
            return round(float(s[:-1]) * 10000.0, 4)
        if s.endswith('万'):
            return round(float(s[:-1]), 4)
        return round(float(s), 4)
    except (ValueError, TypeError):
        return None


def parse_pct(s):
    if s is None:
        return None
    s = str(s).strip().replace('%', '').replace(',', '')
    if s in ('', '--', '-', 'None', 'nan'):
        return None
    try:
        return round(float(s), 4)
    except (ValueError, TypeError):
        return None


def build_code_map(lconn):
    """返回 (code_map, name_map)：6位代码->ts_code 与 名称->ts_code。
    优先 stock_basic，回退 tb_secumain。name_map 用于修复同花顺榜单中被截断的代码。"""
    code_map, name_map = {}, {}
    cur = lconn.cursor()
    try:
        cur.execute("SELECT symbol, name, ts_code FROM stock_basic")
        for sym, name, tc in cur.fetchall():
            if tc:
                if sym:
                    code_map.setdefault(str(sym).strip(), tc.strip())
                if name:
                    name_map.setdefault(str(name).strip(), tc.strip())
    except Exception:
        pass
    try:
        cur.execute("SELECT full_code, secu_abbr FROM tb_secumain WHERE full_code IS NOT NULL AND full_code <> ''")
        for fc, abbr in cur.fetchall():
            if '.' in fc:
                code = fc.split('.')[0]
                code_map.setdefault(code, fc)
                if abbr:
                    name_map.setdefault(str(abbr).strip(), fc)
    except Exception:
        pass
    cur.close()
    return code_map, name_map


def suffix_by_code(code):
    code = str(code).strip()
    if code.startswith(('60', '68', '90')):
        return code + '.SH'
    if code.startswith(('00', '30', '20')):
        return code + '.SZ'
    if code.startswith(('4', '8', '92')):
        return code + '.BJ'
    return None


def main():
    ap = argparse.ArgumentParser(description='同花顺个股资金流向(即时榜单) -> tb_moneyflow_ths')
    ap.add_argument('--trade-date', type=str, default=None, help='交易日期 YYYYMMDD，默认今天')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if args.trade_date:
        td = datetime.datetime.strptime(args.trade_date, '%Y%m%d').date()
    else:
        td = datetime.date.today()
    td_dt = datetime.datetime(td.year, td.month, td.day)

    import akshare as ak
    print(f'抓取同花顺即时资金流榜单（trade_date={td}）...')
    t0 = time.time()
    df = ak.stock_fund_flow_individual(symbol="即时")
    print(f'抓取完成：{len(df)} 行，耗时 {round(time.time() - t0, 1)}s')
    if df.empty:
        print('无数据，退出')
        return

    # 建连 + 建表
    lconn = pymysql.connect(**get_local_params(), connect_timeout=20)
    try:
        cur = lconn.cursor()
        cur.execute(DDL)
        code_map, name_map = build_code_map(lconn)
        rows = []
        unmapped = 0
        for _, r in df.iterrows():
            name = str(r['股票简称']).strip() if r['股票简称'] is not None else None
            code = str(r['股票代码']).strip()
            # 同花顺榜单对部分代码做了截断(如 002479->2479、600639->639)，用名称兜底还原
            if len(code) == 6 and code.isdigit():
                ts_code = code_map.get(code) or suffix_by_code(code)
            else:
                ts_code = name_map.get(name)
            if not ts_code:
                unmapped += 1
                continue
            pct = parse_pct(r.get('涨跌幅'))
            latest = parse_amount(str(r.get('最新价'))) if r.get('最新价') is not None else None
            net = parse_amount(r.get('净额'))
            rows.append((ts_code, td_dt, name, pct, latest, net,
                         None, None, None, None, None, None, None))
        print(f'可映射 {len(rows)} 条，无法映射 {unmapped} 条')

        if args.dry_run:
            print('[dry-run] 不写库')
            return
        if rows:
            # 当天快照：先清空该交易日旧数据再插入，自愈且幂等
            cur.execute("DELETE FROM tb_moneyflow_ths WHERE trade_date=%s", (td_dt,))
            cur.executemany(UPSERT_SQL, rows)
            lconn.commit()
        cur.close()
    finally:
        lconn.close()
    print(f'完成：写入 {len(rows)} 条 -> tb_moneyflow_ths')


if __name__ == '__main__':
    main()
