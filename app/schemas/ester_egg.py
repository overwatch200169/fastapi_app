from app.models.base import EsterEggBase


class EggPublic(EsterEggBase):
    egg_id: int
    picture_url: str