import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据读写/推送目标库。
# 默认指向本地 MySQL（原生产为阿里云 RDS，已迁本地；映射 JDBC: mysql://localhost:3306/stock_int）。
# 如需连远程/生产库，设置环境变量 SQLALCHEMY_DB_URL 即可整体覆盖。
SQLALCHEMY_DB_URL = os.getenv(
    'SQLALCHEMY_DB_URL',
    'mysql+pymysql://root:wlx123@localhost:3306/stock_int',
)

engine = create_engine(SQLALCHEMY_DB_URL,pool_size=20, max_overflow=10, pool_recycle=3600)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)


Base = declarative_base()