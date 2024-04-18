from typing import Any
from fastapi import APIRouter
from app.parameter import user_dto
from app.models.user import user

router = APIRouter(tags=["user_router"])


@router.put("/user/")
def register_user(session: Any, body: user_dto) -> user:
    """
    用户注册
    """
    # 1. 校验输入参数
    # 1.1 校验手机号和验证码
    # 1.2 查询用户是否存在
    # 1.3 校验密码
    # 2. 生成用户信息
    # 2.1 生成用户ID
    # 2.2 生成密码(加密)
    # 3. 保存用户信息

    return