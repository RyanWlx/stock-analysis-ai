from app.dependencies.db_depend import get_db
from app.models.user_model import User as user
from sqlalchemy import String
from sqlalchemy.orm import Session

# 根据手机号查询用户信息
def get_user_by_mobile(mobile: String, db: Session) -> user:
    """
    根据手机号查询用户信息
    """
    return db.query(user).filter(user.mobile == mobile).first()


# 保存用户信息
def save_user( userinfo: user,  db: Session) -> user:
    """
    保存用户信息
    """
    db.add(userinfo)
    db.commit()
    db.refresh(userinfo)
    return userinfo


