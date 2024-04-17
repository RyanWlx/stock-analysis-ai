from typing import Any
from app.models.models import Message, NewPassword
from fastapi import APIRouter

router = APIRouter(tags=["login_router"])


@router.post("/login/reset-password/")
def reset_password(session: Any, body: NewPassword) -> Message:
    """
    Reset password
    """
    # do something
    return Message(message="Password updated successfully")