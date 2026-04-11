from fastapi import APIRouter

from app.dependencies.contact import ContactServiceDep
from app.models.base import ContactMe
from app.schemas.contact import EmailResponse


router=APIRouter()

@router.post("/me",response_model=EmailResponse)
#annotated依赖（这是类型）而不是调用类本身
async def contact_us(mail:ContactMe,service:ContactServiceDep):
    result=await service.send_contact_email(mail)


    return result