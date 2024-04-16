from typing import Any
from app.models import Message, NewPassword
from fastapi import APIRouter

router = APIRouter()
@router.post("/reset-password/")
def reset_password(session: Any, body: NewPassword) -> Message:
    """
    Reset password
    """
    # do something
    return Message(message="Password updated successfully")