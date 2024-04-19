from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DB_URL = "mysql://soosoo_dev:Initial11@rm-uf62xspc9k7yy9kw9zo.mysql.rds.aliyuncs.com:3306/stock_int"

engine = create_engine(SQLALCHEMY_DB_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

Base = declarative_base()