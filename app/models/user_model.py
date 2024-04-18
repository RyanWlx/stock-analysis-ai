from sqlalchemy import Column, Integer, String, DateTime, Boolean, UUID, Float
# from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.db_config import Base
import uuid


# 数据表tb_user映射对象
class User(Base):
	__tablename__ = 'tb_user'

	id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
	mobile = Column(String(20), unique=True, index=True)
	nickname = Column(String(50))
	level = Column(Integer, default=0)
	point = Column(Float)
	reg_date = Column(DateTime, default=datetime.now)
	password = Column(String(20), nullable=False)
	pw_status = Column(Integer, default=1)
	salt = Column(String(255))
	created_time = Column(DateTime, default=datetime.now)
	updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

	# 与tb_user_info建立一对一关系
	# user_info = relationship('UserInfo', uselist=False, back_populates='user')

	def __repr__(self):
		return f'<User {self.id, self.mobile}>'


# 数据表tb_sms_record映射对象
class Sms(Base):
	__tablename__ = 'tb_sms_record'

	id = Column(UUID, primary_key=True, index=True)
	mobile = Column(String(50), unique=True, index=True)
	function_code = Column(Integer, default=1)
	valid_code = Column(String(6))
	valid_code_time = Column(DateTime, default=datetime.now)
	valid_status = Column(Boolean, default=True, index=True)
	valid_duration = Column(Integer, default=600)
	comments = Column(String(255))
	created_time = Column(DateTime, default=datetime.now)
	updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

	def __repr__(self):
		return f'<Sms {self.mobile, self.valid_code}>'


# 数据表tb_query_record映射对象
class Query(Base):
	__tablename__ = 'tb_query_record'


# 数据表tb_order_record映射对象
class Order(Base):
	__tablename__ = 'tb_order_record'
