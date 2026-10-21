import os
import tushare as ts

# 凭证从环境变量读取，避免明文入库：export TUSHARE_TOKEN=xxxx
# 本项目主要数据源已切换到同花顺/聚源，tushare 仅作备用；
# 未配置 token 时不再抛异常阻塞服务启动，pro 置为 None（调用方需自行判空）。
_TOKEN = os.environ.get('TUSHARE_TOKEN', '')
pro = ts.pro_api(_TOKEN) if _TOKEN else None
