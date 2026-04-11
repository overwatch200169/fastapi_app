from typing import Annotated

from fastapi import Depends

from app.services.ContactServices import ContactService


def get_contact_service():
    return ContactService
ContactServiceDep=Annotated[ContactService,Depends(get_contact_service)]