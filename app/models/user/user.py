#数据表tb_user映射对象
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.db_config import Base

class User(Base):
	__tablename__ = 'tb_user'

	id = Column(Integer, primary_key=True, index=True)
	mobile = Column(String(50), unique=True, index=True)
	function_code = Column(Integer, default=1)
	valid_code = Column(String(6))
	valid_code_time = Column(DateTime, default=datetime.now)
	valid_status = Column(Boolean, default=True, index=True)
	valid_duration = Column(Integer, default=600)
	comments = Column(String(255))
	created_time = Column(DateTime, default=datetime.now)
	updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

	# 与tb_user_info建立一对一关系
	# user_info = relationship('UserInfo', uselist=False, back_populates='user')

	def __repr__(self):
		return f'<User {self.username}>'