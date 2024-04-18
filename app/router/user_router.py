from typing import Any
from fastapi import APIRouter
from app.parameter.user_dto import UserDTO
from app.models.user import user
import app.utils.valid as valid

router = APIRouter(tags=["user_router"])


@router.put("/user/")
def register_user(session: Any, body: UserDTO) -> user:
    """
    用户注册
    """
    param = UserDTO(**body)
    # 1. 校验输入参数
    # 1.1 校验手机号和验证码
    # 1.2 查询用户是否存在
    # 1.3 校验密码
    if valid.is_valid_password(param.password) is False:
        return {"code": 1009, "msg": "密码格式不正确"}
    # 2. 生成用户信息
    # 2.1 生成用户ID
    # 2.2 生成密码(加密)
    # 3. 保存用户信息

    return