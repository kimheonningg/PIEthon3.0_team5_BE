from pydantic import BaseModel
from core.models.registerform import Name

class ChangePwForm(BaseModel):
    userId: str
    name: Name
    originalPw: str
    newPw: str
