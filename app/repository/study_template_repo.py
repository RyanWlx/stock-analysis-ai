from app.models.study_template_model import TbStudyTemplate as StudyTemplate
from sqlalchemy.orm import Session
from sqlalchemy import String, Integer, BigInteger
from sqlalchemy import create_engine, and_, or_


def get_templates_by_user(client: String, user: String, db: Session) -> StudyTemplate:
    """
    根据client,user获取name
    """
    return db.query(StudyTemplate).filter(
        and_(
            StudyTemplate.owner_id == user,
            StudyTemplate.owner_source == client,
        )
    ).all()

def get_template_by_template(client: String, user: String, template: String, db: Session) -> StudyTemplate:
    """
    根据client,user,template获取content
    """
    return db.query(StudyTemplate).filter(
        and_(
            StudyTemplate.owner_id == user,
            StudyTemplate.owner_source == client,
            StudyTemplate.name == template,
        )
    ).first()

def set_template_by_template(stemplate: StudyTemplate, client: String, user: String, name: String, content: String, db: Session) -> StudyTemplate:
    """
    根据client,user,template获取content
    """
    result = db.query(StudyTemplate).filter(
        and_(
            StudyTemplate.owner_id == user,
            StudyTemplate.owner_source == client,
            StudyTemplate.name == name,
        )
    ).first()
    if(result is None):
        db.add(stemplate)
        db.commit()
        db.refresh(stemplate)
        return stemplate
    else:
        mytemplate = db.query(stemplate).filter(
            and_(
                StudyTemplate.owner_id == user,
                StudyTemplate.owner_source == client,
                StudyTemplate.name == name,
            )
        ).update({
            stemplate.content: content,
        })
        db.commit()
        return mytemplate

def delete_template( client: String, user: String, template: String, db: Session) -> StudyTemplate:
    """
    删除用户图标信息
    """
    templateData = db.query(StudyTemplate).filter(
        and_(
            StudyTemplate.owner_id == user,
            StudyTemplate.owner_source == client,
            StudyTemplate.name == template,
        )
    ).first()
    db.delete(templateData)
    db.commit()
    return templateData