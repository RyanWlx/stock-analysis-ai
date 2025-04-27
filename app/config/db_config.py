from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DB_URL = "mysql+pymysql://soosoo_dev:Initial11@rm-bp108x9ex00k889y14o.mysql.rds.aliyuncs.com:3306/stock_int"

engine = create_engine(SQLALCHEMY_DB_URL,pool_size=20, max_overflow=10, pool_recycle=3600)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)


Base = declarative_base()