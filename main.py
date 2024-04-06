import uvicorn
from fastapi import FastAPI
from typing import Optional
app = FastAPI()

DemoInfo = {'wlx': '', 'test': 'test'}


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.put('/demo/{demo}')
def result(demo: str):
    return {'demo': demo}
# 启动uvicorn服务，默认端口8000
if __name__ == '__main__':
    uvicorn.run('main:app')