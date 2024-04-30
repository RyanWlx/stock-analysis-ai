from app.service import stock_service as stockService
from fastapi import APIRouter
from app.parameter.request.qutationRequest import QutationDTO
from app.parameter.response import myResponse
import numpy as np
from app.service import kimi_service as kimiService

router = APIRouter(tags=["stock_router"])

@router.post("/stock/getStockQuoteByType")
async def getStockQuoteByType(qutationRequeat: QutationDTO):
	#获取股票行情数据
    df = stockService.getQutation(qutationRequeat.ts_code, qutationRequeat.start_date, qutationRequeat.end_date)
    if df is not None:
        return myResponse.resp_200(data = np.array(df).tolist(), message="获取成功")
    return myResponse.resp_200(message="用户不存在",data='')


@router.post("/stock/getStockStorageDoc")
def getStockStorageDoc1():
    df = kimiService.getDataSource()
	#获取kimi的回答
    # words = kimiService.getStockStorageDoc()
    # return myResponse.resp_200(data = words.to_dict(), message="获取成功")
