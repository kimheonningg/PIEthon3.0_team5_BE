from pydantic import BaseModel, constr
from core.models.registerform import Name

class FindIdForm(BaseModel):
    phoneNum: constr(strip_whitespace=True, min_length=9, max_length=11)
    name: Name
