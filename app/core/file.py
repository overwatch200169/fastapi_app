import mimetypes
import time
import uuid
from pathlib import Path
import boto3
import magic
from botocore.config import Config
from fastapi import UploadFile, HTTPException

from app.core.config import settings

# 初始化 S3 客户端
s3_client = boto3.client(
    "s3",
    endpoint_url=settings.R2_ENDPOINT_URL,
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name="auto" # R2 固定写 auto
)

async def upload_file(folder,file_content,file_type):
    file_name=await generate_file_name(folder,file_type)
    try:
        s3_client.upload_fileobj(file_content.file,
        settings.BUCKET_NAME,
        f'{folder}/{file_name}',#不同功能的图片放在不同的文件夹，用前端查询参数进行输入
        ExtraArgs={"ContentType": file_type})
        return {"url": f"{settings.PUBLIC_URL_PREFIX}/{folder}/{file_name}"}
    except Exception as e:
        raise HTTPException(503,detail=str(e))

def process_image(image):
    pass

async def validate_file_type(file:UploadFile):
    header=await file.read(2048)
    mime=magic.Magic(mime=True)
    file_type=mime.from_buffer(header)
    await file.seek(0)

    allowed_types = settings.ALLOWED_FILE_TYPES

    if file_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_type}。请上传图片格式。"
        )

    return file_type


async def generate_file_name(folder,file_type):
    safe_suffix= mimetypes.guess_extension(file_type) or '.bin'
    filename=f'{uuid.uuid4()}-{time.time()}-{folder}{safe_suffix}'
    return filename