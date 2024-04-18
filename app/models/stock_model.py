from sqlalchemy import Column, Integer, String, DateTime, Boolean, UUID, Float
from datetime import datetime
from app.config.db_config import Base
import uuid


# 数据表tb_query_record映射对象
class Daliy(Base):
    __tablename__ = 'tb_daliy'


# 数据表tb_order_record映射对象
class Weekly(Base):
    __tablename__ = 'tb_weekly'


# 数据表tb_query_record映射对象
class Monthly(Base):
    __tablename__ = 'tb_monthly'


# 数据表tb_order_record映射对象
class Exchange(Base):
    __tablename__ = 'tb_exchange'


# 数据表tb_query_record映射对象
class Secumain(Base):
    __tablename__ = 'tb_secumain'


# 数据表tb_order_record映射对象
class StkFactor(Base):
    __tablename__ = 'tb_stk_factor'
