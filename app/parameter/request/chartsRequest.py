# user接口传输对象
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import String, Integer
from typing import Optional


class ChartsDTO():
	name: Optional[str]
	content: Optional[str]
	symbol: Optional[str]
	resolution: str='D'
	id: Optional[int]
	lastModified: datetime

	def __init__(self, name: Optional[str], content: Optional[str], symbol: Optional[str], id: Optional[int], lastModified: datetime, resolution: Optional[str]):
		self.name = name
		self.content = content
		self.symbol = symbol
		self.id = id
		self.lastModified = lastModified
		self.resolution = resolution
