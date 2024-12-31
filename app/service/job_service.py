from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from app.router.stock_router import getStockFactor

stockList = ['300757','300170','688668','688313','300444','832978','688639','601127','603897','002313']

# 输出时间
def my_job():
    type = 'D'
    ts_code = stockList[0]
    start_date = '2024-10-30'
    end_date = '2024-01-01'
    getStockFactor(type,ts_code,start_date,end_date)
    pass

def run_job():
    # BlockingScheduler
    print("run_job====>")
    sched = BlockingScheduler()
    sched.add_job(my_job, 'interval', seconds=24*60*60, id='my_job_id')
    sched.start()

