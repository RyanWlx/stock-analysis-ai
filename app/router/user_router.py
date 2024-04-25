from typing import Any
from fastapi import APIRouter
from app.parameter.request import userApiRequest
from app.parameter.response import myResponse
from app.models.user_model import User
import app.utils.valid as valid
import app.repository.user_repo as userRepo

router = APIRouter(tags=["user_router"])
@router.get("/user/getUserInfoByPhone")
async def getUserInfo(mobile: str):
    # 1.2 查询用户是否存在 - 根据手机号查询用户信息
    userInfo = userRepo.get_user_by_mobile( mobile)
    if userInfo is not None:
        return myResponse.resp_400(message="用户已存在")
    return myResponse.resp_200(data = {'username':userInfo.username})

@router.put("/user/")
def register_user(userDto: userApiRequest.UserDTO | None = None):
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
    userInfo = userRepo.get_user_by_mobile( userDto.mobile)
    if userInfo is not None:
        return myResponse.resp_400(message="用户已存在")
    # 2. 生成用户信息
    userRepo.save_user( User(mobile=userDto.mobile, nickname=userDto.nickname, password=userDto.password))

    # 2.1 生成密码(加密)
    # 3. 保存用户信息

    return myResponse.resp_200(data="注册成功")