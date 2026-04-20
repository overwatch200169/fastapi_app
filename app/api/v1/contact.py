from fastapi import APIRouter, HTTPException

from app.dependencies.captcha import get_captcha_dep
from app.dependencies.contact import ContactServiceDep
from app.models.base import ContactMe
from app.schemas.contact import EmailResponse


router=APIRouter(tags=['Contact me'])

@router.post("/me",response_model=EmailResponse)
#annotated依赖（这是类型）而不是调用类本身
async def contact_us_with_captcha(mail:ContactMe,service:ContactServiceDep,verify:get_captcha_dep):
    if not verify.verify_captcha(input_captcha=mail.captcha_code,captcha_id=mail.captcha_id):
        raise HTTPException(400, "验证码不可用")

    result=await service.send_contact_email(mail)


    return result