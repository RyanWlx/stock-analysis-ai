from app.config.log_config import logger
import app.router.stock_router as stock_router
from app.parameter.request.qutationRequest import QutationDTO

# 输出时间
def data_save():
    logger.info("保存数据至数据库")
    # 调用具体方法执行
    dto = QutationDTO()
    dto.type = 'D'
    dto.ts_code = '600800.SH'
    dto.end_date = '20240101'
    dto.start_date = '20241231'
    stock_router.getStockFactor(dto)

