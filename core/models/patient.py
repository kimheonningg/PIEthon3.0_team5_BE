from pydantic import BaseModel, constr, ConfigDict
from typing import List, Optional
from bson import ObjectId

from core.models.registerform import Name

class Patient(BaseModel):
    phoneNum: constr(strip_whitespace=True, min_length=9, max_length=11)
    patientId: str # 환자 고유 식별 번호
    doctorId: Optional[List[str]] = None # multiple doctors are allowed, use object id
    name: Name
    medicalNotes: Optional[List[str]] = None # only store note object ids
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}, 
    )
