
from sqlmodel import Session

from app.core.contact import send_email
from app.models.base import ContactMe
from app.schemas.contact import EmailResponse


class ContactService:
    def __init__(self,session:Session):
        self.session=session
    @staticmethod
    async def send_contact_email(mail:ContactMe)->EmailResponse:
        return await send_email(mail)
