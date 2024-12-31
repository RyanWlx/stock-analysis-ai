import uvicorn
from fastapi import FastAPI
from app.router import RegisterRouterList
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.service.job_service import data_save

scheduler = AsyncIOScheduler()

# 输出时间
@scheduler.scheduled_job('interval', seconds=5, id='my_job_id')
def my_job():
    # 执行数据拉取和保存逻辑
    print("start a job")
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

@app.on_event('startup')
async def on_startup():
    print('start event!')
    scheduler.start()

# 启动uvicorn服务，默认端口8000
if __name__ == '__main__':
    uvicorn.run("main:app", port=8000, reload=True)
