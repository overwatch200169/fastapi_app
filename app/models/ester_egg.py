from sqlmodel import Field

from app.models.base import EsterEggBase, CheckiCountBase


class EsterEgg(EsterEggBase,table=True):
    egg_id:int|None = Field(default=None, primary_key=True,sa_column_kwargs={"autoincrement": True})
    picture_url:str

class CheckiCount(CheckiCountBase,table=True):
    id:int|None=Field(default=None, primary_key=True,sa_column_kwargs={"autoincrement": True})
