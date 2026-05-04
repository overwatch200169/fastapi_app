from fastapi import APIRouter, HTTPException

from app.dependencies.ester_egg import ester_egg_dep
from app.schemas.ester_egg import EggPublic

router=APIRouter(tags=['egg'])

@router.get('/',response_model=list[EggPublic])
async def egg_list(egg:ester_egg_dep):
    result=egg.get_eggs()
    if result:
        return result
    else:
        raise HTTPException(404,'not found')