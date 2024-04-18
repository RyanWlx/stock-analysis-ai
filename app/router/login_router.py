from typing import Any
from fastapi import APIRouter

router = APIRouter(tags=["login_router"])


@router.post("/user/login/")
def reset_password(session: Any, body: NewPassword) -> Message:
    """
    Reset password
    """
    # do something
    return Message(message="Password updated successfully")