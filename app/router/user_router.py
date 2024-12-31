from typing import Any
from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.db_depend import get_db
from app.parameter.request import userApiRequest
from app.parameter.response import myResponse
from app.models.user_model import User
import app.utils.valid as valid
import app.repository.user_repo as userRepo
from typing import Optional

router = APIRouter(tags=["user_router"])

class Item(BaseModel):
    phone: str

@router.post("/user/getUserInfoByPhone")
async def getUserInfo(item: Item, db: Session = Depends(get_db)):
    # 1.2 查询用户是否存在 - 根据手机号查询用户信息
    userInfo = userRepo.get_user_by_mobile(item.phone, db)
    if userInfo is not None:
        return myResponse.resp_200(data = {'username':userInfo.nickname},message="查询成功")
    return myResponse.resp_200(message="用户不存在",data='')

@router.put("/user/")
def register_user(userDto: Optional[userApiRequest.UserDTO] = None, db: Session = Depends(get_db)):
    """
    用户注册
    """
    # 1. 校验输入参数
    if valid.is_valid_string(userDto.mobile) is False:
        return myResponse.resp_400(message= "手机号为空")
    if valid.is_valid_string(userDto.password) is False:
        return myResponse.resp_400(message="密码为空")
    if valid.is_valid_string(userDto.valid_code) is False:
        return myResponse.resp_400(message="验证码为空")
    if valid.is_valid_password(userDto.password) is False:
        return myResponse.resp_400(message="密码格式不正确")
    # 1.1 校验手机号和验证码 - 验证码是否正确

    # 1.2 查询用户是否存在 - 根据手机号查询用户信息
    userInfo = userRepo.get_user_by_mobile(userDto.mobile, db)
    if userInfo is not None:
        return myResponse.resp_400(message="用户已存在")
    # 2. 生成用户信息
    userRepo.save_user(User(mobile=userDto.mobile, nickname=userDto.nickname, password=userDto.password), db)

    # 2.1 生成密码(加密)
    # 3. 保存用户信息

    return myResponse.resp_200(data="注册成功")