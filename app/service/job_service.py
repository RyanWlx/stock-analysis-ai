from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler


# 输出时间
def my_job():
    pass

def run_job():
    # BlockingScheduler
    sched = BlockingScheduler()
    sched.add_job(my_job, 'interval', seconds=24*60*60, id='my_job_id')
    sched.start()

