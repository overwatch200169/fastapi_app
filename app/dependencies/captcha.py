from typing import Annotated

from fastapi import Depends,Request



from app.core.captcha_img import CaptchaManager


# _manager_singleton = None
#
# def get_captcha_manager() -> CaptchaManager:
#     global _manager_singleton
#     if _manager_singleton is None:
#         _manager_singleton = CaptchaManager()
#     return _manager_singleton

def get_captcha_manager(request:Request) -> CaptchaManager:
    return request.app.state.captcha_manager


get_captcha_dep=Annotated[CaptchaManager,Depends(get_captcha_manager)]
#用单例模式因为有状态存储（captcha id)
#不用单例模式改用生命周期，在一个生命周期内只产生一个实例也是单例
