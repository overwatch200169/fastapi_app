#TODO oss联动，处理图片函数
from fastapi import UploadFile


def upload_file(file:UploadFile):
    # file.read()
    return {'filename':file.filename}

def process_image(image):
    pass