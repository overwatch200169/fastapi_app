from typing import Literal

from fastapi import APIRouter, UploadFile, Query, File
from app.core.file import upload_file, validate_file_type

router=APIRouter(tags=['file'])

@router.post('/upload')
async def upload_file_router(folder: Literal["articles", "avatars", "system", "general"] = Query(default="general"),file:UploadFile=File(...)):
    file_type=await validate_file_type(file)

    img_url=await upload_file(folder,file,file_type)
    return img_url