from typing import Any
from fastapi import APIRouter
from app.parameter.request import userApiRequest
from app.models.user_model import User
import app.utils.valid as valid
import app.repository.user_repo as userRepo

router = APIRouter(tags=["user_router"])


@router.put("/user/")
def register_user(session: Any, body: userApiRequest.UserDTO):
    """
    用户注册
    """
    param = userApiRequest.UserDTO(**body)
    # 1. 校验输入参数
    if valid.is_valid_string(param.mobile) is False:
        return {"code": 1009, "msg": "手机号为空"}
    if valid.is_valid_string(param.password) is False:
        return {"code": 1009, "msg": "密码为空"}
    if valid.is_valid_string(param.valid_code) is False:
        return {"code": 1009, "msg": "验证码为空"}
    if valid.is_valid_password(param.password) is False:
        return {"code": 1009, "msg": "密码格式不正确"}
    # 1.1 校验手机号和验证码 - 验证码是否正确

    # 1.2 查询用户是否存在 - 根据手机号查询用户信息
    userInfo = userRepo.get_user_by_mobile(session, param.mobile)
    if userInfo is not None:
        return {"code": 1009, "msg": "用户已存在"}
    # 2. 生成用户信息
    userRepo.save_user(session, User(mobile=param.mobile, nickname=param.nickname, password=param.password))

    # 2.1 生成密码(加密)
    # 3. 保存用户信息

    return {"code": 1008, "msg": "注册成功"}