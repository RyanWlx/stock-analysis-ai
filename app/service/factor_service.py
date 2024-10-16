import decimal
from datetime import datetime
from decimal import Decimal

import app.utils.tdxFunction as tdx
from app.config.log_config import logger
from pandas import DataFrame
import numpy as np
import pandas as pd
from app.models.stock_model import Daliy as daliy

# 指标计算服务
# 定义转换函数
def float_to_decimal(value):
    if value:
        return Decimal(str(value))
    else:
        return Decimal(0)

def strategy_bottom_picking(daliy: DataFrame):
    """
    策略：底部选股
    1. 选股条件：
        1.1 选股时间：每周一
        1.2 选股范围：沪深A股
        1.3 选股指标：市盈率PE < 10
    2. 选股结果：
        2.1 选股时间：每周一
        2.2 选股范围：沪深A股
        2.3 选股指标：市盈率PE < 10
        2.4 选股结果：沪深A股市盈率PE < 10的股票列表
    """
    logger.info("底部选股策略执行开始")
    CLOSE = daliy['close']
    LOW = daliy['low']
    HIGH = daliy['high']
    x_1 = (CLOSE + HIGH + LOW) / 3
    x_1_5 = pd.Series(tdx.MA(x_1, 14))
    x_1_7 = x_1_5.apply(lambda x: Decimal.from_float(x))
    x_1_6 = tdx.AVEDEV(x_1, 14) * 0.015
    x_2 = (x_1-x_1_7) / x_1_6
    x_3 = tdx.CROSS(x_2, -100)
    x_4 = (CLOSE - Decimal.from_float(tdx.LLV(LOW, 9))) / (tdx.HHV(HIGH, 9) - tdx.LLV(LOW, 9)) * 100
    x_5 = tdx.SMA(x_4, 3,1)
    x_6 = tdx.SMA(x_5,3,1)
    x_7 = 3*x_5-2*x_6
    x_8 = tdx.CROSS(x_7,x_6)
    x_9 = tdx.CROSS(x_2,100)
    x_10 = x_8 and x_9
    x_11 = x_8 and x_3
    x_12 = CLOSE / tdx.MA(CLOSE, 40)*100 < 78
    x_13 = CLOSE / tdx.MA(CLOSE, 60)*100 < 74
    x_14 = HIGH > LOW * 1.051
    x_15 = x_14 and tdx.COUNT(x_14,5)>1
    x_16 = tdx.IF(x_15 and (x_12 or x_13),2,0)
    x_17 = CLOSE/tdx.REF(CLOSE, 25) <= 1.1
    x_18 = tdx.SMA(tdx.MAX(CLOSE - tdx.REF(CLOSE, 2),0), 7,1)/tdx.SMA(tdx.ABS(CLOSE-tdx.REF(CLOSE, 2)),7,1)*100 < 15
    x_19 = (CLOSE-tdx.LLV(LOW, 8))/(tdx.HHV(HIGH, 8)-tdx.LLV(LOW, 8))*100
    x_20 = tdx.SMA(x_19, 2,1)
    x_21 = tdx.SMA(x_20, 2,1)
    x_22 = tdx.IF(x_20>tdx.REF(x_20, 1) and tdx.REF(x_20,1)<tdx.REF(x_20,2) and x_20<23,1.5,0)
    x_23 = tdx.LLV(LOW, 9)
    x_24 = tdx.HHV(HIGH, 9)
    x_25 = tdx.EMA((CLOSE - x_23)/(x_24-x_23)*100,3)
    x_26 = tdx.EMA(x_25,3)
    x_27 = tdx.MA(x_26,3)
    x_28 = tdx.CROSS(x_26, x_27)
    xg = x_28 and x_22
    logger.info("底部选股策略执行结束")
    return xg


