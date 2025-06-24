from pydantic import BaseModel, constr
from typing import List, Optional

from core.models.registerform import Name
from core.models.patient import Patient

class Doctor(BaseModel):
    userId: Optional[str]
    phoneNum: constr(strip_whitespace=True, min_length=9, max_length=11)
    name: Name
    licenceNum: str
    assignedPatients: List[Patient]

