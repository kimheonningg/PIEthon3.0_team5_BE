from typing import Literal, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, constr

Position = Literal["doctor", "patient", "admin", "other"]

class Name(BaseModel):
    firstName: constr(strip_whitespace=True, min_length=1, max_length=40)
    lastName:  constr(strip_whitespace=True, min_length=1, max_length=40)

class RegisterForm(BaseModel):
    email: EmailStr
    phoneNum: constr(strip_whitespace=True, min_length=9, max_length=11)
    name: Name
    userId: constr(pattern=r"^[a-zA-Z0-9_]{1,20}$")
    password: str
    position: Position = "doctor"
    licenceNum: str