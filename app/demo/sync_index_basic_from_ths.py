# -*- coding: utf-8 -*-
"""
从同花顺/聚源数据源补齐 tb_index_basic 表（对标 Tushare index_basic 接口 doc_id=94）。

数据源（均为同花顺/聚源托管库 hsjydb）：
  - secumain           : 证券主表 -> SecuCategory=4 的全部指数
                         SecuCode(代码) / SecuAbbr(简称) / ChiName(全称) / InnerCode
  - lc_indexbasicinfo  : 指数基础信息（按 InnerCode = IndexCode 关联）
                         PubOrgName(发布方) / BaseDate(基期) / BasePoint(基点) /
                         PubDate(发布日期) / EndDate(终止日期) / WAMethod(加权方式代码) /
                         IndexType(指数类别代码) / IndexAbstract(简介) / IndexRemark(编制说明)

字段口径对齐 Tushare index_basic（doc_id=94）：
  ts_code, symbol, name, fullname, market, publisher, index_type, category,
  base_date, base_point, list_date, weight_rule, description, exp_date

关于 market（市场/服务商）的判定：
  聚源库里"上证50"(000016)与"沪深300"(000300)的发布方都写作
  "中证指数有限公司、上海证券交易所"，无法仅凭发布方区分 SSE / CSI。
  故采用【代码前缀 + 发布方】的组合规则（见 derive_market）：
    - 申万发布  -> SW   (.SI)
    - MSCI/摩根 -> MSCI (.MSCI)
    - 代码 93xxxx / 0009xx / 000300 -> CSI (.CSI)
    - 代码 399xxx / 发布方含"深圳" -> SZSE (.SZ)
    - 发布方含"上海" -> SSE (.SH)
    - 发布方含"中证" -> CSI (.CSI)
    - 其余 -> OTH  (.OTH)
  注：沪深300 等少数"中证旗舰"因与上交所联合发布，按上述规则归入 CSI（已显式校正 000300）；
      如要严格对齐 tushare 的 CSI/SSE 标签，可按代码前缀二次校正。

关于 category / weight_rule / index_type：
  - 聚源 IndexType、WAMethod 为数字代码，本环境无法解析其专有字典（ct_systemconst 跨类目代码冲突），
    故 category 存 IndexType 数字串、weight_rule 存 WAMethod 数字串，便于后续映射。
  - index_type（指数风格）聚源无直接对应字段，留 NULL。

范围：secumain(SecuCategory=4) 且与 lc_indexbasicinfo 能关联的指数（约 3.2 万条，含基础信息），
      未关联基础信息的指数（约 1.7 万，多为成分/派生指数）不纳入本表。

用法（项目根目录，需用已装 pymysql 的 venv python 运行）：
    python -m app.demo.sync_index_basic_from_ths
    python -m app.demo.sync_index_basic_from_ths --dry-run   # 只统计不写库
"""
import sys
import os
import re
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pymysql

# ===================== 连接配置 =====================
REMOTE = dict(host='39.96.14.212', port=53410, user='hsjydb', password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
              database='hsjydb', charset='utf8mb4')

# 本地库（优先读环境变量，方便指向生产 RDS）
LOCAL = dict(
    host=os.environ.get('THS_SYNC_DB_HOST', 'localhost'),
    port=int(os.environ.get('THS_SYNC_DB_PORT', '3306')),
    user=os.environ.get('THS_SYNC_DB_USER', 'root'),
    password=os.environ.get('THS_SYNC_DB_PASSWORD', 'wlx123'),
    database=os.environ.get('THS_SYNC_DB_DB', 'stock_int'),
    charset='utf8mb4',
)

# 中证旗舰：聚源与上交所联合发布，需显式校正为 CSI
CSI_OVERRIDE_CODES = {'000300'}


def safe(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s not in ('', 'None', 'nan') else None


def to_date(v):
    if v is None:
        return None
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    s = str(v).strip()
    if s in ('', 'None', 'nan'):
        return None
    try:
        return datetime.datetime.strptime(s[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def derive_market(pub, code):
    """返回 (market, suffix)。market 对齐 tushare 枚举 MSCI/CSI/SSE/SZSE/CICC/SW/OTH。"""
    p = pub or ''
    if '申银万国' in p or '申万' in p:
        return 'SW', '.SI'
    if '摩根士丹利' in p or 'MSCI' in p.upper():
        return 'MSCI', '.MSCI'
    if code.startswith('93') or re.match(r'^0009\d\d$', code) or code in CSI_OVERRIDE_CODES:
        return 'CSI', '.CSI'
    if code.startswith('399'):
        return 'SZSE', '.SZ'
    if '深圳' in p:
        return 'SZSE', '.SZ'
    if '中金' in p or '中国国际金融' in p:
        return 'CICC', '.CI'
    if '上海' in p:
        return 'SSE', '.SH'
    if '中证' in p:
        return 'CSI', '.CSI'
    return 'OTH', '.OTH'


def conn_retry(cfg, retries=3):
    for i in range(retries):
        try:
            return pymysql.connect(**cfg, connect_timeout=20, read_timeout=180)
        except Exception as e:
            print(f'  connect retry {i + 1}: {e}')
    raise SystemExit('connect failed')


def fetch_rows(cur):
    """取 secumain(指数) JOIN lc_indexbasicinfo 的全部记录。"""
    sql = """
        SELECT a.SecuCode, a.SecuAbbr, a.ChiName,
               b.PubOrgName, b.BaseDate, b.BasePoint, b.PubDate, b.EndDate,
               b.WAMethod, b.IndexType,
               COALESCE(NULLIF(TRIM(b.IndexAbstract), ''), LEFT(b.IndexRemark, 800)) AS description
        FROM secumain a
        JOIN lc_indexbasicinfo b ON a.InnerCode = b.IndexCode
        WHERE a.SecuCategory = 4
    """
    cur.execute(sql)
    return cur.fetchall()


def ensure_table(conn):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS tb_index_basic")
    cur.execute("""
        CREATE TABLE tb_index_basic (
            id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
            ts_code       VARCHAR(40)  NOT NULL COMMENT 'TS指数代码（带后缀，如 000001.SH）',
            symbol        VARCHAR(30)  DEFAULT NULL COMMENT '指数代码（不带后缀）',
            name          VARCHAR(100) DEFAULT NULL COMMENT '指数简称',
            fullname      VARCHAR(200) DEFAULT NULL COMMENT '指数全称',
            market        VARCHAR(10)  DEFAULT NULL COMMENT '市场/服务商 SSE/SZSE/CSI/SW/MSCI/CICC/OTH',
            publisher     VARCHAR(200) DEFAULT NULL COMMENT '发布方',
            index_type    VARCHAR(50)  DEFAULT NULL COMMENT '指数风格（聚源无直接对应，留空）',
            category      VARCHAR(30)  DEFAULT NULL COMMENT '指数类别（聚源 IndexType 数字代码）',
            base_date     DATE         DEFAULT NULL COMMENT '基期',
            base_point    FLOAT        DEFAULT NULL COMMENT '基点',
            list_date     DATE         DEFAULT NULL COMMENT '发布日期',
            weight_rule   VARCHAR(20)  DEFAULT NULL COMMENT '加权方式（聚源 WAMethod 数字代码）',
            description   VARCHAR(1000) DEFAULT NULL COMMENT '指数简介/编制说明',
            exp_date      DATE         DEFAULT NULL COMMENT '终止日期',
            created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            PRIMARY KEY (id),
            UNIQUE KEY uk_ts_code (ts_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指数列表（对标Tushare index_basic，数据源：同花顺/聚源）'
    """)
    conn.commit()
    cur.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='只统计不写库')
    args = ap.parse_args()

    print('[1] 远程连接并拉取 secumain(指数) + lc_indexbasicinfo ...')
    rconn = conn_retry(REMOTE)
    rcur = rconn.cursor()
    rows = fetch_rows(rcur)
    rcur.close()
    rconn.close()
    print(f'    关联记录数: {len(rows)}')

    print('[2] 组装字段 ...')
    records = []
    stat = {'market': {}, 'null_pub': 0, 'null_base': 0, 'null_point': 0}
    for (secu_code, abbr, fullname, pub, base_date, base_point,
         pub_date, end_date, wa, idx_type, desc) in rows:
        if not secu_code:
            continue
        secu_code = str(secu_code).strip()
        market, suffix = derive_market(pub, secu_code)
        ts_code = f'{secu_code}{suffix}'
        if not pub:
            stat['null_pub'] += 1
        if base_date is None:
            stat['null_base'] += 1
        if base_point is None:
            stat['null_point'] += 1
        stat['market'][market] = stat['market'].get(market, 0) + 1
        records.append((
            ts_code, secu_code, safe(abbr), safe(fullname), market, safe(pub),
            None, (str(idx_type) if idx_type is not None else None),
            to_date(base_date), (float(base_point) if base_point is not None else None),
            to_date(pub_date), (str(wa) if wa is not None else None),
            safe(desc), to_date(end_date),
        ))

    print(f'    待写入: {len(records)} 条')
    print(f'    市场分布: {stat["market"]}')
    print(f'    发布方缺失: {stat["null_pub"]}  基期缺失: {stat["null_base"]}  基点缺失: {stat["null_point"]}')

    if args.dry_run:
        print('[dry-run] 不写库，结束。')
        return

    print('[3] 写入本地库 tb_index_basic ...')
    lconn = conn_retry(LOCAL)
    ensure_table(lconn)
    lcur = lconn.cursor()
    lcur.execute('TRUNCATE TABLE tb_index_basic')
    insert_sql = """
        INSERT INTO tb_index_basic
        (ts_code, symbol, name, fullname, market, publisher, index_type, category,
         base_date, base_point, list_date, weight_rule, description, exp_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
        symbol=VALUES(symbol), name=VALUES(name), fullname=VALUES(fullname),
        market=VALUES(market), publisher=VALUES(publisher), index_type=VALUES(index_type),
        category=VALUES(category), base_date=VALUES(base_date), base_point=VALUES(base_point),
        list_date=VALUES(list_date), weight_rule=VALUES(weight_rule),
        description=VALUES(description), exp_date=VALUES(exp_date)
    """
    batch = 1000
    for i in range(0, len(records), batch):
        lcur.executemany(insert_sql, records[i:i + batch])
        lconn.commit()
        if (i + batch) % 5000 < batch:
            print(f'    已写入 {min(i + batch, len(records))} / {len(records)}')
    lcur.execute('SELECT COUNT(*) FROM tb_index_basic')
    print(f'[4] 完成，tb_index_basic 总记录数: {lcur.fetchone()[0]}')
    lcur.close()
    lconn.close()


if __name__ == '__main__':
    main()
