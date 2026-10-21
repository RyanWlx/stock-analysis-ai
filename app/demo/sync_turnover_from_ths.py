# -*- coding: utf-8 -*-
"""
为 tb_daliy 补齐 turno_rate / turnover_rate_f（对标 Tushare daily_basic doc_id=328）。

数据来源：同花顺/聚源托管库 hsjydb.thsdb.shsz_stock_daily_quotation.turnover_ratio（换手率）。
注意：远程库只提供【单一】换手率字段 turnover_ratio（按流通股本口径，即 tushare turnover_rate）。
      自由流通股口径的 turnover_rate_f 在源中无独立字段，本脚本用同一数值填充（已在列注释标注），
      如需精确的自由流通口径，需另取自由流通股本后再计算。

实现要点：
  - 仅针对 tb_daliy 中真实存在的 ts_code 集合补数（避免把债券/基金/老三板等海量无关行情拉进来）。
  - 远程按 sec_code 批量拉取历史 turnover_ratio，映射成 ts_code 后写入临时表，
    最后用一条 UPDATE ... JOIN 回填 tb_daliy（幂等，可重跑）。
  - 支持断点续传：已写入临时表的批次会被跳过。

用法（项目根目录，需用已装 pymysql 的 venv python）：
    python -m app.demo.sync_turnover_from_ths            # 执行补录
    python -m app.demo.sync_turnover_from_ths --dry-run  # 只统计不写库
    python -m app.demo.sync_turnover_from_ths --check     # 仅打印补录后的填充率
"""
import os
import sys
import time
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pymysql

# ===================== 连接配置 =====================
REMOTE = dict(
    host='39.96.14.212', port=53410, user='hsjydb', password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
    database='hsjydb', charset='utf8mb4', connect_timeout=30, read_timeout=300,
)
LOCAL = dict(
    host=os.environ.get('THS_SYNC_DB_HOST', 'localhost'),
    port=int(os.environ.get('THS_SYNC_DB_PORT', '3306')),
    user=os.environ.get('THS_SYNC_DB_USER', 'root'),
    password=os.environ.get('THS_SYNC_DB_PASSWORD', 'wlx123'),
    database=os.environ.get('THS_SYNC_DB_DB', 'stock_int'),
    charset='utf8mb4', connect_timeout=20,
)

# 交易所中文名（远程 exchg 字段）-> 后缀
EXCHG_SUFFIX = {'上交所': '.SH', '深交所': '.SZ', '北交所': '.BJ'}

CODE_BATCH = 50          # 每次远程查询的 sec_code 批大小
FLUSH_EVERY = 200_000    # 临时表批量写入阈值
END_DATE = '2026-10-19'  # tb_daliy 最大交易日（含）


def get_local_db():
    return pymysql.connect(**LOCAL)


def get_remote_db():
    return pymysql.connect(**REMOTE)


def add_columns(lconn):
    cur = lconn.cursor()
    cur.execute(
        "SELECT COLUMN_NAME FROM information_schema.columns "
        "WHERE table_schema=DATABASE() AND table_name='tb_daliy' "
        "AND COLUMN_NAME IN ('turnover_rate','turnover_rate_f')"
    )
    existing = {r[0] for r in cur.fetchall()}
    if 'turnover_rate' not in existing:
        print('[schema] 新增列 tb_daliy.turnover_rate')
        cur.execute(
            "ALTER TABLE tb_daliy ADD COLUMN turnover_rate DECIMAL(12,4) DEFAULT NULL "
            "COMMENT '换手率（%），对标tushare daily_basic.turnover_rate（源：同花顺/聚源 turnover_ratio，流通股本口径）'"
        )
    if 'turnover_rate_f' not in existing:
        print('[schema] 新增列 tb_daliy.turnover_rate_f')
        cur.execute(
            "ALTER TABLE tb_daliy ADD COLUMN turnover_rate_f DECIMAL(12,4) DEFAULT NULL "
            "COMMENT '换手率（自由流通股）；源仅提供单一换手率，暂以 turnover_ratio 填充'"
        )
    lconn.commit()
    cur.close()


def ensure_staging(lconn):
    cur = lconn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS tb_daliy_turnover_tmp ("
        "  ts_code VARCHAR(90) NOT NULL,"
        "  trade_date DATETIME NOT NULL,"
        "  turnover_rate DECIMAL(12,4) DEFAULT NULL,"
        "  PRIMARY KEY (ts_code, trade_date)"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    )
    lconn.commit()
    cur.close()


def get_target_codes(lconn):
    """返回 tb_daliy 中真实存在的 ts_code 集合与其 6 位 sec_code 列表。"""
    cur = lconn.cursor()
    cur.execute("SELECT DISTINCT ts_code FROM tb_daliy")
    ts_codes = [r[0] for r in cur.fetchall()]
    cur.close()
    # 过滤出合法的 A 股 ts_code（含 .SH/.SZ/.BJ）
    valid = [c for c in ts_codes if c and '.' in c]
    sec_map = {}  # sec_code(6位) -> ts_code
    for c in valid:
        sec = c.rsplit('.', 1)[0]
        sec_map[sec] = c
    return valid, sec_map


def pull_and_stage(lconn, rconn, valid_codes, sec_map, dry_run):
    cur = lconn.cursor()
    rcur = rconn.cursor(pymysql.cursors.SSCursor)
    total_pulled = 0
    total_staged = 0
    t0 = time.time()

    buffer = []
    n_batches = (len(valid_codes) + CODE_BATCH - 1) // CODE_BATCH

    for bi in range(n_batches):
        batch = valid_codes[bi * CODE_BATCH:(bi + 1) * CODE_BATCH]
        # 断点续传：批次首只代码已写入临时表则跳过
        first = batch[0]
        cur.execute("SELECT 1 FROM tb_daliy_turnover_tmp WHERE ts_code=%s LIMIT 1", (first,))
        if cur.fetchone():
            continue

        sec_codes = [c.rsplit('.', 1)[0] for c in batch]
        ph = ','.join(['%s'] * len(sec_codes))
        sql = (
            f"SELECT sec_code, exchg, td_date, turnover_ratio "
            f"FROM thsdb.shsz_stock_daily_quotation "
            f"WHERE sec_code IN ({ph}) AND td_date <= %s"
        )
        rcur.execute(sql, sec_codes + [END_DATE])
        rows = rcur.fetchall()
        for sec_code, exchg, td_date, tr in rows:
            suf = EXCHG_SUFFIX.get((exchg or '').strip())
            if not suf:
                continue
            ts_code = sec_code + suf
            if ts_code not in sec_map:   # 仅保留 tb_daliy 真实存在的标的（过滤债券/基金等）
                continue
            if td_date is None or tr is None:
                continue
            if isinstance(td_date, datetime.datetime):
                td_dt = td_date
            else:
                td_dt = datetime.datetime(td_date.year, td_date.month, td_date.day)
            buffer.append((ts_code, td_dt, float(tr)))
            total_pulled += 1
            if len(buffer) >= FLUSH_EVERY:
                if not dry_run:
                    cur.executemany(
                        "REPLACE INTO tb_daliy_turnover_tmp (ts_code, trade_date, turnover_rate) "
                        "VALUES (%s,%s,%s)", buffer
                    )
                    lconn.commit()
                total_staged += len(buffer)
                buffer.clear()
                print(f'  [进度] 批次 {bi + 1}/{n_batches}，已拉取 {total_pulled}，已暂存 {total_staged}，'
                      f'耗时 {time.time() - t0:.0f}s')
        if buffer and not dry_run:
            cur.executemany(
                "REPLACE INTO tb_daliy_turnover_tmp (ts_code, trade_date, turnover_rate) "
                "VALUES (%s,%s,%s)", buffer
            )
            lconn.commit()
            total_staged += len(buffer)
            buffer.clear()

    rcur.close()
    cur.close()
    print(f'[拉取完成] 远程命中 {total_pulled} 行，暂存 {total_staged} 行，耗时 {time.time() - t0:.0f}s')
    return total_pulled, total_staged


def update_join(lconn, dry_run):
    cur = lconn.cursor()
    cur.execute("SELECT COUNT(*) FROM tb_daliy_turnover_tmp")
    staged = cur.fetchone()[0]
    print(f'[回填] 临时表 {staged} 行，执行 UPDATE ... JOIN')
    if dry_run:
        cur.close()
        return 0
    t0 = time.time()
    cur.execute(
        "UPDATE tb_daliy t JOIN tb_daliy_turnover_tmp s "
        "ON t.ts_code=s.ts_code AND t.trade_date=s.trade_date "
        "SET t.turnover_rate = s.turnover_rate, t.turnover_rate_f = s.turnover_rate "
        "WHERE s.turnover_rate IS NOT NULL"
    )
    n = cur.rowcount
    lconn.commit()
    cur.close()
    print(f'[回填完成] 更新 {n} 行，耗时 {time.time() - t0:.0f}s')
    return n


def check_fill(lconn):
    cur = lconn.cursor()
    cur.execute("SELECT COUNT(*), "
                "SUM(turnover_rate IS NOT NULL), SUM(turnover_rate_f IS NOT NULL) FROM tb_daliy")
    total, tr, trf = cur.fetchone()
    print(f'[填充率] tb_daliy 总行数 {total}，turnover_rate 非空 {tr}（{100.0 * tr / total:.1f}%），'
          f'turnover_rate_f 非空 {trf}（{100.0 * trf / total:.1f}%）')
    cur.execute("SELECT MIN(trade_date), MAX(trade_date) FROM tb_daliy WHERE turnover_rate IS NOT NULL")
    print('          turnover_rate 日期范围:', cur.fetchone())
    cur.close()


def main():
    ap = argparse.ArgumentParser(description='tb_daliy 换手率补录（同花顺/聚源 -> turnover_ratio）')
    ap.add_argument('--dry-run', action='store_true', help='只统计不写库')
    ap.add_argument('--check', action='store_true', help='仅打印补录后的填充率')
    ap.add_argument('--keep-tmp', action='store_true', help='回填后保留临时表')
    args = ap.parse_args()

    lconn = get_local_db()
    try:
        if args.check:
            check_fill(lconn)
            return
        add_columns(lconn)
        ensure_staging(lconn)
        valid_codes, sec_map = get_target_codes(lconn)
        print(f'[目标] tb_daliy 去重 ts_code {len(valid_codes)} 只，开始从远程拉取换手率'
              f'（END_DATE={END_DATE}）')
        if args.dry_run:
            print('[dry-run] 不写库，仅统计目标规模')
            print(f'  预计处理 {len(valid_codes)} 只标的，远程按 sec_code 分批（每批 {CODE_BATCH}）')
            return

        rconn = get_remote_db()
        try:
            pull_and_stage(lconn, rconn, valid_codes, sec_map, args.dry_run)
        finally:
            rconn.close()

        update_join(lconn, args.dry_run)
        check_fill(lconn)

        if not args.keep_tmp:
            cur = lconn.cursor()
            cur.execute("DROP TABLE IF EXISTS tb_daliy_turnover_tmp")
            lconn.commit()
            cur.close()
            print('[清理] 已删除临时表 tb_daliy_turnover_tmp')
    finally:
        lconn.close()


if __name__ == '__main__':
    main()
