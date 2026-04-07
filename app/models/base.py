from sqlmodel import SQLModel

class UserBase(SQLModel):
    username: str
    user_id: int
    email: str


