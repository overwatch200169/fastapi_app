from sqlmodel import Session, select

from app.models.ester_egg import EsterEgg, CheckiCount
from app.schemas.ester_egg import EggPublic, CheckiUpdate, CheckiCreate


class EsterEggService:
    def __init__(self,session:Session):
        self.session=session

    def get_eggs(self):
        eggs=self.session.exec(select(EsterEgg)).all()
        return eggs
    def get_checki_count_all(self):

        checki=self.session.exec(select(CheckiCount)).all()
        return checki
    def get_checki_count(self,id):
        checki=self.session.get(CheckiCount,id)
        return checki

    def add_checki_count(self,cheki_create:CheckiCreate):
        checki_db=CheckiCount.model_validate(cheki_create)

        self.session.add(checki_db)
        self.session.commit()
        self.session.refresh(checki_db)

        return checki_db
    def update_checki_count(self,id,checki:CheckiUpdate):
        checki_db=self.get_checki_count(id)
        checki_count_data=checki.model_dump(exclude_unset=True)
        checki_db.sqlmodel_update(checki_count_data)
        self.session.add(checki_db)
        self.session.commit()
        self.session.refresh(checki_db)


        return checki_db
