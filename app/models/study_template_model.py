from sqlalchemy import BigInteger, Column, DECIMAL, DateTime, Index, Integer, String, Table, text
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR
from sqlalchemy.orm import declarative_base
import uuid
from app.config.db_config import Base

class TbStudyTemplate(Base):
    __tablename__ = 'tb_study_template'
    __table_args__ = (
        Index('IX_ownerSource', 'owner_source', 'owner_id'),
        {'comment': 'study_template'}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='id')
    owner_source = Column(String(200), nullable=True, comment='')
    owner_id = Column(String(200), comment='')
    name = Column(String(200), comment='')
    last_modified = Column(String(200), comment='')
    first_modified = Column(String(200), comment='')
    content = Column(String(200), comment='')

    def __repr__(self):
        return f'<Secumain {self.owner_source, self.owner_id}>'