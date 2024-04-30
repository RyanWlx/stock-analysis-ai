# user接口传输对象
from pydantic import BaseModel
from sqlalchemy import String, Integer


class QutationDTO(BaseModel):
	type: str='D'  # D 日线 W 周线 M 月线
	ts_code: str
	trade_date: str
	start_date: str
	end_date: str
	offset: int=0
	limit: int=1000
