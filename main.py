import uvicorn
from fastapi import FastAPI
from app.router import RegisterRouterList
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.service.job_service import data_save
from app.config.log_config import logger
from datetime import datetime

scheduler = AsyncIOScheduler()

# 定义定时任务执行器
@scheduler.scheduled_job('cron', hour=16, minute=11, id='data_save')
def my_job():
    # 执行数据拉取和保存逻辑
    logger.info("start a job")
    # 周六周天不执行
    today = datetime.today().weekday()
    if today in (5,6):
        print('今天是周六周天，不执行同步数据服务')
    else:
        data_save()

# 实例化
app = FastAPI()

# 跨域配置
origins = {
    "http://47.113.111.219"
}
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","DELETE","HEAD"],
    allow_headers=["*"],
)

# 加载路由
for item in RegisterRouterList:
    app.include_router(item.router)

# 启动时执行任务
@app.on_event('startup')
async def on_startup():
    logger.info('start event!')
    scheduler.start()
    # data_save()

# 启动uvicorn服务，默认端口8000
if __name__ == '__main__':
    uvicorn.run("main:app", port=8000, reload=True)
