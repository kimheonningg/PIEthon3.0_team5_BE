from pydantic import BaseModel, constr
from .registerform import Name

class FindIdForm(BaseModel):
    phone_num: constr(strip_whitespace=True, min_length=9, max_length=11)
    name: Name
