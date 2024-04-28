from app.config.db_config import SessionLocal
from app.models.user_model import User as user
from sqlalchemy import Integer, String, DateTime, Boolean, UUID, Float


# 根据手机号查询用户信息
def get_user_by_mobile( mobile: String) -> user:
    """
    根据手机号查询用户信息
    """
    Session = SessionLocal()
    return Session.query(user).filter(user.mobile == mobile).first()


# 保存用户信息
def save_user( userinfo: user) -> user:
    """
    保存用户信息
    """
    SessionLocal.add(userinfo)
    SessionLocal.commit()
    SessionLocal.refresh(userinfo)
    return userinfo


