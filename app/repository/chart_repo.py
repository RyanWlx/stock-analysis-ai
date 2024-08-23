from app.models.charts_model import TbCharts as Charts
from sqlalchemy.orm import Session
from sqlalchemy import String, Integer, BigInteger
from sqlalchemy import create_engine, and_, or_


# 保存用户图标信息
def save_charts( chart: Charts,  db: Session) -> Charts:
    """
    保存用户图表信息
    """
    db.add(chart)
    db.commit()
    db.refresh(chart)
    return chart


# 删除用户图标信息
def delete_charts( chart: Charts,  db: Session) -> Charts:
    """
    删除用户图标信息
    """
    db.delete(chart)
    db.commit()
    return chart


# 查询用户图标信息
def get_chart_by_id(id: BigInteger, db: Session) -> Charts:
    """
    根据图标id查询用户信息
    """
    return db.query(Charts).filter(Charts.id == id).first()


# 查询用户图标信息列表
def get_charts_by_user(user: str, db: Session) -> Charts:
    """
    根据用户id查询用户信息列表
    """
    return db.query(Charts).filter(Charts.owner_id == user).all()
# 查询用户指定id的图表
def set_charts_by_user_by_chartid(user: str, chart: str, name: str, content: str, symbol: str, resolution: str, db: Session) -> Charts:
    """
    根据用户id,chartid更新图表
    name，content，symbol，resolution都可能会改变
    """
    print('setcharts===>',user,name)
    myChart = db.query(Charts).filter(
        and_(
            Charts.owner_id == user,
            Charts.id == chart,
        )
    ).update({
        Charts.name: name,
        Charts.content: content,
        Charts.symbol: symbol,
        Charts.resolution: resolution,
    })
    db.commit()
    return myChart;
