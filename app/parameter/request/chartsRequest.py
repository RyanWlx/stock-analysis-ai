# user接口传输对象
from pydantic import BaseModel
from sqlalchemy import String, Integer
from typing import Optional


class ChartsDTO(BaseModel):
	name: Optional[str]
	content: Optional[str]
	symbol: Optional[str]
	resolution: str='D'
