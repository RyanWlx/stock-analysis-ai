from fastapi import APIRouter
from typing import Any
from pymysql import connect
from pydantic import BaseModel

router = APIRouter(tags=["demo_router"])


@router.get('/demo/{demo}')
def result(demo: str):
    return {'demo': demo}


def connectdb(sql):
    # 建立Mysql数据库连接
    db = connect(
        host='rm-uf62xspc9k7yy9kw9zo.mysql.rds.aliyuncs.com',  # 数据库地址 可远程，可本地
        port=3306,  # 数据库端口号
        user='soosoo_dev',  # 用户名
        passwd='Initial11',  # 密码
        db='stock_int',  # 需要连接的数据库
        charset='utf8mb4'  # 配置编码
    )
    cursor = db.cursor()
    sqls = sql  # 查询历史数据
    cursor.execute(sqls)  # 执行sql
    results = cursor.fetchall()  # 获取sql的每条数据
    db.commit()
    cursor.close()  # 关闭游标
    db.close()  # 关闭数据库连接
    return results


def login():
    userName = 'test'
    password = '123456'
    sql = 'select name,password from users where name = "{}"'.format(userName)
    up = connectdb(sql)
    if len(up) != 0:
        user_name = up[0][0]
        user_pwd = up[0][1]
    else:
        print('暂无该用户,请前往注册')
        return
    if userName == user_name and password == user_pwd:
        data = {
            'code': 200,
            'msg': '登录成功！'
        }
        print('登录成功')
        return data
    elif userName != user_name and password == user_pwd:
        data = {
            'code': 403,
            'msg': '用户名不正确,请重新输入!'
        }
        print('用户名不正确')
        return data
    elif userName == user_name and password != user_pwd:
        data = {
            'code': 403,
            'msg': '密码不正确,请重新输入!'
        }
        print('密码不正确')
        return data
    else:
        data = {
            'code': 404,
            'msg': '用户名和密码不正确,请重新输入!'
        }
        print('用户名和密码不正确,请重新输入!')
        return data


DemoInfo = {'wlx': '', 'test': 'test'}


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: list[str] = []


@router.get("/demo/")
async def read_root():
    """
    项目信息
    :return:
    """
    return login()
    # return {"Hello": "World"}


@router.post("/items/", response_model=Item)
async def create_item(item: Item) -> Any:
    return item
