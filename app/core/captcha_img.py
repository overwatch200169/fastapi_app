from captcha.image import ImageCaptcha
from io import BytesIO
import random
import string
from datetime import datetime, timedelta
from typing import Tuple, Optional
import hashlib
import secrets

from app.core.storage import CaptchaStorage


class CaptchaManager:
    def __init__(self,store:CaptchaStorage):
        # self._storage={}
        self._store=store
    async def generate_captcha_img(self,length=4,width=200,height=80):
        chars=string.ascii_uppercase.replace('O','').replace('I','')
        chars+=string.digits.replace('1','')

        captcha_code=''.join(random.choices(chars,k=length))

        captcha_img=ImageCaptcha(width,height)
        image_data=captcha_img.generate(captcha_code)


        img_bytes = image_data.getvalue()
        captcha_id=secrets.token_urlsafe(16)
        await self._store.set(key=captcha_id,code=captcha_code,ttl=120)


        # print(self._store[captcha_id])
        return captcha_id,img_bytes,captcha_code


    async def verify_captcha(self,input_captcha,captcha_id):
        stored_code=await self._store.get(captcha_id)
        if input_captcha != stored_code:
            await self._store.delete(captcha_id)
            return False


        await self._store.delete(captcha_id)
        return True

# captcha_manager = CaptchaManager()





