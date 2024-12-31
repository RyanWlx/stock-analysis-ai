import uvicorn
from fastapi import FastAPI, BackgroundTasks
from app.router import RegisterRouterList
from fastapi.middleware.cors import CORSMiddleware
from app.service.job_service import run_job

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

# 启动uvicorn服务，默认端口8000
if __name__ == '__main__':
    backgroud = BackgroundTasks()
    backgroud.add_task(run_job)
    print("run_job====>2")
    uvicorn.run("main:app", port=8000, reload=True)
