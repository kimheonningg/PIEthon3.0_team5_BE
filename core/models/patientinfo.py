from typing import List
from pydantic import BaseModel, constr, ConfigDict, Field
from bson import ObjectId

from core.models.medicalnote import MedicalNote
from core.models.registerform import Name

class PatientInfo(BaseModel):
    patientId: str
    patientOid: ObjectId
    name: Name
    phoneNum: constr(strip_whitespace=True, min_length=9, max_length=11)
    medicalNotes: List[MedicalNote] = Field(default_factory=list)
    # TODO image

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )