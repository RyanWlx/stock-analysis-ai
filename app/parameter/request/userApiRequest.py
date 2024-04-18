# user接口传输对象
from sqlalchemy import String


class UserDTO:
    mobile: String
    nickname: String
    password: String
    valid_code: String

    def __init__(self, mobile: String, nickname: String, password: String, valid_code: String):
        self.mobile = mobile
        self.nickname = nickname
        self.password = password
        self.valid_code = valid_code