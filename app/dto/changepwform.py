from pydantic import BaseModel
from .registerform import Name

class ChangePwForm(BaseModel):
    user_id: str
    name: Name
    original_pw: str
    new_pw: str
