from sqlmodel import SQLModel
class NewPassword(SQLModel):
    token: str
    new_password: str

class Message(SQLModel):
    message: str