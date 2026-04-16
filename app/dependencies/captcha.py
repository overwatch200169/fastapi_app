from typing import Annotated

from fastapi import Depends



from app.core.captcha_img import CaptchaManager


_manager_singleton = None

def get_captcha_manager() -> CaptchaManager:
    global _manager_singleton
    if _manager_singleton is None:
        _manager_singleton = CaptchaManager()
    return _manager_singleton


get_captcha_dep=Annotated[CaptchaManager,Depends(get_captcha_manager)]
#用单例模式因为有状态存储
