# user接口传输对象
from pydantic import BaseModel


class UserDTO(BaseModel):
    mobile: str
    nickname: str
    password: str
    valid_code: str