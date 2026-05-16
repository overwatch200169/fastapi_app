from fastapi import APIRouter, HTTPException

from app.dependencies.ester_egg import ester_egg_dep
from app.models.base import Page
from app.models.ester_egg import CheckiCount
from app.schemas.ester_egg import EggPublic, CheckiCreate, CheckiUpdate

router=APIRouter(tags=['egg'])

@router.get('/',response_model=list[EggPublic])
async def egg_list(egg:ester_egg_dep):
    result=egg.get_eggs()
    if result:
        return result
    else:
        raise HTTPException(404,'not found')

@router.get('/checki',response_model=list[CheckiCount])
async def checki_list(egg:ester_egg_dep):
    result=egg.get_checki_count_all()
    if result:
        return result
    else:
        raise HTTPException(404,'not found')


@router.get('/checki_pagination',response_model=Page[CheckiCount])
async def checki_pagenation(offset:int,limit:int,egg:ester_egg_dep):
    total,item=egg.get_checki_count_page(offset,limit)
    if total and item:
        return {'total':total, 'items':item}
    else:
        raise HTTPException(404,'not found')

@router.post('/checki',response_model=CheckiCount)
async def create_new_checki(checki:CheckiCreate,egg:ester_egg_dep):
    result=egg.add_checki_count(checki)
    if result:
        return result
    else:
        raise HTTPException(404,'not found')

@router.patch('/checki',response_model=CheckiCount)
async def create_new_checki(id:int,checki:CheckiUpdate,egg:ester_egg_dep):
    result=egg.update_checki_count(id,checki)
    if result:
        return result
    else:
        raise HTTPException(404,'not found')