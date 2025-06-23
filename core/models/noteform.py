from pydantic import BaseModel, ConfigDict
from typing import Optional
from bson import ObjectId

from core.models.medicalnote import MedicalNoteType

class CreateNoteForm(BaseModel):
    title: str
    content: str
    noteType: MedicalNoteType = "other"

class UpdateNoteForm(BaseModel):
    patientId: str
    title: Optional[str] = None
    content: Optional[str] = None
    noteType: Optional[MedicalNoteType] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}, 
    )