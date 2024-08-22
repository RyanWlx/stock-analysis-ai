from app.models.charts_model import TbCharts as Charts
from sqlalchemy.orm import Session


# 保存用户图标信息
def save_charts( chart: Charts,  db: Session) -> Charts:
    """
    保存用户图标信息
    """
    db.add(chart)
    db.commit()
    db.refresh(chart)
    return chart


