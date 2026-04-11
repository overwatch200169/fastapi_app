from pydantic import BaseModel
from typing import Optional

class EmailResponse(BaseModel):
    success: bool
    message: Optional[str] = None