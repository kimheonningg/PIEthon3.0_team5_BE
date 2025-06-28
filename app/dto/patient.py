from pydantic import BaseModel, constr, ConfigDict
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from .registerform import Name

class Patient(BaseModel):
    phone_num: constr(strip_whitespace=True, min_length=9, max_length=11)
    patient_mrn: str # 환자 고유 식별 번호
    doctor_id: Optional[List[str]] = None # multiple doctors are allowed, use object id
    name: Name
    medical_notes: Optional[List[str]] = None # only store note object ids
    age: int
    birthdate: datetime
    body_part: Optional[List[str]] = None
    ai_ready: bool = True
    gender: str # only female / male are allowed
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}, 
    )
