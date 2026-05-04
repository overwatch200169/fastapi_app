from typing import Annotated

from fastapi import Depends


from app.dependencies.database import SessionDep
from app.services.EsterEggServices import EsterEggService


def get_ester_egg(session:SessionDep):
    return EsterEggService(session)

ester_egg_dep=Annotated[EsterEggService,Depends(get_ester_egg)]