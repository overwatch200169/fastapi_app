from captcha.image import ImageCaptcha
from io import BytesIO
import random
import string
from datetime import datetime, timedelta
from typing import Tuple, Optional
import hashlib
import secrets

class CaptchaManager:
    def __init__(self):
        self._storage={}
    def generate_captcha_img(self,length=4,width=200,height=80):
        chars=string.ascii_uppercase.replace('O','').replace('I','')
        chars+=string.digits.replace('1','')

        captcha_code=''.join(random.choices(chars,k=length))

        captcha_img=ImageCaptcha(width,height)
        image_data=captcha_img.generate(captcha_code)


        img_bytes = image_data.getvalue()
        captcha_id=secrets.token_urlsafe(16)
        self._storage[captcha_id]={


            'captcha_code':captcha_code,
            'expires_at': datetime.now() + timedelta(minutes=5),

        }
        return captcha_id,img_bytes,captcha_code


    def verify_captcha(self,input_captcha,captcha_id):
        if captcha_id not in self._storage:
            return False
        data=self._storage[captcha_id]
        print('1',data)
        if datetime.now()>data['expires_at']:
            return False
        if input_captcha.upper() !=data['captcha_code']:
            return False

        del self._storage[captcha_id]
        return True

captcha_manager = CaptchaManager()





