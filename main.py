import uvicorn
from fastapi import FastAPI
from app.router import RegisterRouterList


# 实例化
app = FastAPI(docs_url="/docs", redoc_url=None)
# 加载路由
for item in RegisterRouterList:
    app.include_router(item.router)

# 启动uvicorn服务，默认端口8000
if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)