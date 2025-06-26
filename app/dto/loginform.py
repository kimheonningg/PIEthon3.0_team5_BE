from typing import Optional
from pydantic import BaseModel, constr

class LoginForm(BaseModel):
    phone_num: Optional[constr(strip_whitespace=True, min_length=9, max_length=11)] = None
    user_id: Optional[constr(pattern=r"^[a-zA-Z0-9_]{4,20}$")] = None
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"