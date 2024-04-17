from typing import Any
from app.models.models import Message, NewPassword
from fastapi import APIRouter

router = APIRouter(tags=["stock_router"])


@router.post("/stock/")
def reset_password(session: Any, body: NewPassword) -> Message:
    """
    Reset password
    """
    # do something
    return Message(message="Password updated successfully")