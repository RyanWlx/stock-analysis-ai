# -*- coding: utf-8 -*-
"""
从同花顺数据源补齐 stock_basic 表（对标 Tushare stock_basic 接口 doc_id=25）。

数据源说明（均为同花顺体系，tushare 限速不可用）：
  1) 远程同花顺/聚源库 hsjydb（同花顺自有证券主数据，最权威）
       - secumain            : 证券主表 -> symbol/name/fullname/enname/cnspell/market/exchange/list_status/list_date
       - lc_exgindustry      : 行业分类(申万 Standard=38) -> industry
       - lc_instiarchive     : 注册地城市 RegCity -> area(省份)
       - lc_areacode         : 行政区划代码表 -> 城市/省份解析
       - lc_shsccomponent    : 沪股通成分 -> is_hs='H'
       - lc_zhsccomponent    : 深股通成分 -> is_hs='S'
  2) 同花顺网页：industry / area 也可由 akshare 同花顺行业/地域板块补充，
     但 akshare 本环境仅暴露行业名列表、无成分接口，且网页无法提供 cnspell/enname/
     fullname/实控人等字段，故以同花顺自有库为权威主源，保证字段完整。

字段口径对齐 Tushare stock_basic：
  ts_code, symbol, name, area, industry, fullname, enname, cnspell,
  market, exchange, curr_type, list_status, list_date, delist_date,
  is_hs, act_name, act_ent_type

范围：A 股（SecuCategory=1），仅上交所(83)/深交所(90)/北交所(18)，
      上市状态 L(1)/P(3)/D(5)；剔除老三板(81)与未上市/其他(9)。

用法（项目根目录）：
    python -m app.demo.sync_stock_basic_from_ths
    python -m app.demo.sync_stock_basic_from_ths --dry-run   # 只统计不写库
"""
import sys
import os
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pymysql

# ===================== 连接配置 =====================
REMOTE = dict(host='39.96.14.212', port=53410, user='hsjydb', password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
              database='hsjydb', charset='utf8mb4')
LOCAL = dict(host='localhost', port=3306, user='root', password=os.getenv('THS_SYNC_DB_PASSWORD', ''),
             database='stock_int', charset='utf8mb4')

# 交易所 / 后缀映射
EXCHANGE_MAP = {83: ('SSE', '.SH'), 90: ('SZSE', '.SZ'), 18: ('BSE', '.BJ')}
# 上市状态映射 -> tushare list_status (L 上市 / P 暂停 / D 退市)
LIST_STATUS_MAP = {1: 'L', 3: 'P', 5: 'D'}
# 行业优先标准（申万一级）
INDUSTRY_PREFERRED_STANDARD = 38
# 行政区划根节点（lc_areacode.ParentNode == 此值 表示省/直辖市级）
AREA_ROOT = 144000000


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


def board_of(code, exchange):
    """根据代码前缀与交易所推断板块（market 字段）。"""
    if exchange == 'SSE':
        return '科创板' if code[:3] in ('688', '689') else '主板'
    if exchange == 'SZSE':
        return '创业板' if code[:3] in ('300', '301') else '主板'
    if exchange == 'BSE':
        return '北交所'
    return '主板'


def fetch_master(cur):
    """取去重后的证券主表（每只代码取最新一条），过滤 A 股三大交易所 + L/P/D。"""
    sql = """
        SELECT SecuCode, CompanyCode, SecuAbbr, ChiName, EngName, ChiSpelling,
               SecuMarket, ListedSector, ListedState, ListedDate, XGRQ, ID
        FROM secumain
        WHERE SecuCategory = 1 AND SecuMarket IN (83, 90, 18)
    """
    cur.execute(sql)
    rows = cur.fetchall()
    # 按 SecuCode 去重，保留 XGRQ/ID 最大的一条（最新）
    best = {}
    for r in rows:
        code = r[0]
        key = (r[10] or datetime.datetime.min, r[11] or 0)
        if code not in best or key > best[code][0]:
            best[code] = (key, r)
    # 过滤上市状态
    out = []
    for code, (_, r) in best.items():
        state = r[8]
        if state not in LIST_STATUS_MAP:
            continue
        out.append(r)
    return out


def fetch_industry(cur, company_codes):
    """返回 {CompanyCode: industry_name}，优先 Standard=38，否则取最新有效记录。"""
    if not company_codes:
        return {}
    placeholders = ','.join(['%s'] * len(company_codes))
    sql = f"""
        SELECT CompanyCode, Standard, FirstIndustryName, InfoPublDate, CancelDate
        FROM lc_exgindustry
        WHERE CompanyCode IN ({placeholders})
    """
    cur.execute(sql, list(company_codes))
    by_company = {}
    for comp, std, fname, pubdate, cancel in cur.fetchall():
        if not fname:
            continue
        item = by_company.setdefault(comp, [])
        item.append((std, fname, pubdate, cancel))
    result = {}
    for comp, items in by_company.items():
        # 优先 Standard=38 且未作废(CancelDate IS NULL)，多条取最新发布日
        pref = [x for x in items if x[0] == INDUSTRY_PREFERRED_STANDARD and x[3] is None]
        pool = pref if pref else [x for x in items if x[3] is None]
        if not pool:
            pool = items  # 全作废也兜底取最新
        pool.sort(key=lambda x: (x[2] or datetime.datetime.min), reverse=True)
        result[comp] = pool[0][1]
    return result


def fetch_regcity(cur, company_codes):
    """返回 {CompanyCode: RegCity(int)}。"""
    if not company_codes:
        return {}
    placeholders = ','.join(['%s'] * len(company_codes))
    sql = f"""
        SELECT CompanyCode, RegCity FROM lc_instiarchive
        WHERE CompanyCode IN ({placeholders}) AND RegCity IS NOT NULL AND RegCity > 0
    """
    cur.execute(sql, list(company_codes))
    return {comp: int(rc) for comp, rc in cur.fetchall()}


def fetch_area_map(cur):
    """返回 {AreaInnerCode: (AreaChiName, ParentNode)} 与 {AreaCode(int): AreaInnerCode}。"""
    cur.execute("SELECT AreaInnerCode, AreaCode, AreaChiName, ParentNode FROM lc_areacode")
    by_inner = {}
    code_to_inner = {}
    for inner, acode, name, parent in cur.fetchall():
        by_inner[inner] = (name, parent)
        try:
            code_to_inner[int(acode)] = inner
        except (ValueError, TypeError):
            pass
    return by_inner, code_to_inner


def resolve_province(regcity, by_inner, code_to_inner):
    """把 RegCity(城市行政代码) 解析为省份/直辖市名称。"""
    if not regcity:
        return None
    inner = code_to_inner.get(regcity)
    if inner is None:
        return None
    name, parent = by_inner.get(inner, (None, None))
    if parent is None or parent == AREA_ROOT:
        return name  # 本身就是省/直辖市
    # 向上找一级父节点（省份）
    pname, _ = by_inner.get(parent, (None, None))
    return pname if pname else name


def fetch_hs(cur):
    """返回 (set(沪股通SecuCode), set(深股通SecuCode))，仅取当前有效(OutDate 为空)。"""
    cur.execute("SELECT DISTINCT SecuCode FROM lc_shsccomponent WHERE OutDate IS NULL OR OutDate > NOW()")
    sh = {r[0] for r in cur.fetchall() if r[0]}
    cur.execute("SELECT DISTINCT SecuCode FROM lc_zhsccomponent WHERE OutDate IS NULL OR OutDate > NOW()")
    sz = {r[0] for r in cur.fetchall() if r[0]}
    return sh, sz


def ensure_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_basic (
            id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
            ts_code       VARCHAR(15)  NOT NULL COMMENT 'TS代码（带交易所后缀，如 000001.SZ）',
            symbol        VARCHAR(10)  DEFAULT NULL COMMENT '股票代码（不带后缀）',
            name          VARCHAR(50)  DEFAULT NULL COMMENT '股票名称',
            area          VARCHAR(20)  DEFAULT NULL COMMENT '所在地域（省份）',
            industry      VARCHAR(50)  DEFAULT NULL COMMENT '所属行业（申万一级）',
            fullname      VARCHAR(120) DEFAULT NULL COMMENT '股票全称',
            enname        VARCHAR(120) DEFAULT NULL COMMENT '英文全称',
            cnspell       VARCHAR(50)  DEFAULT NULL COMMENT '拼音缩写',
            market        VARCHAR(20)  DEFAULT NULL COMMENT '市场类型（主板/创业板/科创板/北交所）',
            exchange      VARCHAR(10)  DEFAULT NULL COMMENT '交易所（SSE/SZSE/BSE）',
            curr_type     VARCHAR(10)  DEFAULT NULL COMMENT '交易货币（CNY）',
            list_status   CHAR(1)      DEFAULT NULL COMMENT '上市状态 L-上市 P-暂停 D-退市',
            list_date     DATE         DEFAULT NULL COMMENT '上市日期',
            delist_date   DATE         DEFAULT NULL COMMENT '退市日期',
            is_hs         CHAR(1)      DEFAULT NULL COMMENT '是否沪深港通标的 N-否 H-沪 S-深',
            act_name      VARCHAR(100) DEFAULT NULL COMMENT '实际控制人',
            act_ent_type  VARCHAR(50)  DEFAULT NULL COMMENT '实际控制人性质',
            created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            PRIMARY KEY (id),
            UNIQUE KEY uk_ts_code (ts_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票列表（对标Tushare stock_basic，数据源：同花顺）'
    """)
    conn.commit()
    cur.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='只统计不写库')
    args = ap.parse_args()

    rconn = pymysql.connect(**REMOTE, connect_timeout=20, read_timeout=120)
    rcur = rconn.cursor()

    print('[1] 拉取证券主表（去重 + 过滤 A 股三大交易所 / L,P,D）...')
    master = fetch_master(rcur)
    print(f'    主表记录数: {len(master)}')

    company_codes = [r[1] for r in master]
    print('[2] 拉取行业 / 注册地 / 沪深港通 ...')
    industry = fetch_industry(rcur, company_codes)
    regcity = fetch_regcity(rcur, company_codes)
    by_inner, code_to_inner = fetch_area_map(rcur)
    sh_hs, sz_hs = fetch_hs(rcur)
    print(f'    行业覆盖: {len(industry)} / {len(company_codes)}  注册地覆盖: {len(regcity)}  沪股通: {len(sh_hs)} 深股通: {len(sz_hs)}')

    rcur.close()
    rconn.close()

    # 组装
    records = []
    stat = {'market': {}, 'exchange': {}, 'list_status': {}, 'area_null': 0,
            'industry_null': 0, 'hs': 0}
    for r in master:
        (secu_code, company_code, abbr, fullname, enname, cnspell,
         secu_market, listed_sector, listed_state, listed_date, _, _) = r
        exchange, suffix = EXCHANGE_MAP.get(secu_market, ('', ''))
        if not exchange:
            continue
        ts_code = f'{secu_code}{suffix}'
        market = board_of(secu_code, exchange)
        list_status = LIST_STATUS_MAP.get(listed_state)
        area = resolve_province(regcity.get(company_code), by_inner, code_to_inner)
        ind = industry.get(company_code)
        is_hs = 'N'
        if secu_code in sh_hs:
            is_hs = 'H'
        elif secu_code in sz_hs:
            is_hs = 'S'
        if is_hs != 'N':
            stat['hs'] += 1
        if area is None:
            stat['area_null'] += 1
        if ind is None:
            stat['industry_null'] += 1
        stat['market'][market] = stat['market'].get(market, 0) + 1
        stat['exchange'][exchange] = stat['exchange'].get(exchange, 0) + 1
        stat['list_status'][list_status] = stat['list_status'].get(list_status, 0) + 1
        records.append((
            ts_code, secu_code, safe(abbr), safe(area), safe(ind), safe(fullname),
            safe(enname), safe(cnspell), market, exchange, 'CNY', list_status,
            to_date(listed_date), None, is_hs, None, None,
        ))

    print(f'[3] 组装完成，待写入: {len(records)} 条')
    print(f'    板块分布: {stat["market"]}')
    print(f'    交易所分布: {stat["exchange"]}')
    print(f'    上市状态: {stat["list_status"]}')
    print(f'    沪深港通标的数: {stat["hs"]}  地区缺失: {stat["area_null"]}  行业缺失: {stat["industry_null"]}')

    if args.dry_run:
        print('[dry-run] 不写库，结束。')
        return

    lconn = pymysql.connect(**LOCAL, connect_timeout=20)
    ensure_table(lconn)
    lcur = lconn.cursor()
    lcur.execute('TRUNCATE TABLE stock_basic')
    insert_sql = """
        INSERT INTO stock_basic
        (ts_code, symbol, name, area, industry, fullname, enname, cnspell,
         market, exchange, curr_type, list_status, list_date, delist_date,
         is_hs, act_name, act_ent_type)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    batch = 500
    for i in range(0, len(records), batch):
        lcur.executemany(insert_sql, records[i:i + batch])
        lconn.commit()
        if (i + batch) % 2000 < batch:
            print(f'    已写入 {min(i + batch, len(records))} / {len(records)}')
    lcur.execute('SELECT COUNT(*) FROM stock_basic')
    print(f'[4] 完成，stock_basic 总记录数: {lcur.fetchone()[0]}')
    lcur.close()
    lconn.close()


if __name__ == '__main__':
    main()
