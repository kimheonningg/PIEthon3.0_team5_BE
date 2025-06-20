from typing import Optional
from pydantic import BaseModel, constr

class LoginForm(BaseModel):
    phoneNum: Optional[constr(strip_whitespace=True, min_length=9, max_length=11)] = None
    userId: Optional[constr(pattern=r"^[a-zA-Z0-9_]{4,20}$")] = None
    password: str