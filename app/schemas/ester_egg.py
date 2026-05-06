from pydantic import BaseModel

from app.models.base import EsterEggBase, CheckiCountBase
from app.models.ester_egg import CheckiCount


class EggPublic(EsterEggBase):
    egg_id: int
    picture_url: str

class CheckiCreate(CheckiCountBase):
    pass
class CheckiUpdate(BaseModel):
    cheki_count:int|None