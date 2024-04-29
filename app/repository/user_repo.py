from app.config.db_config import get_db
from app.models.user_model import User as user
from sqlalchemy import Integer, String, DateTime, Boolean, UUID, Float
from sqlalchemy.orm import Session
from fastapi import Depends


# 根据手机号查询用户信息
def get_user_by_mobile(mobile: String, db: Session = Depends(get_db)) -> user:
    """
    根据手机号查询用户信息
    """
    return db.query(user).filter(user.mobile == mobile).first()


# 保存用户信息
def save_user( userinfo: user,  db: Session = Depends(get_db)) -> user:
    """
    保存用户信息
    """
    db.add(userinfo)
    db.commit()
    db.refresh(userinfo)
    return userinfo


