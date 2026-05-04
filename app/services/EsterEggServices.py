from sqlmodel import Session, select

from app.models.ester_egg import EsterEgg
from app.schemas.ester_egg import EggPublic


class EsterEggService:
    def __init__(self,session:Session):
        self.session=session

    def get_eggs(self):
        eggs=self.session.exec(select(EsterEgg)).all()
        return eggs
