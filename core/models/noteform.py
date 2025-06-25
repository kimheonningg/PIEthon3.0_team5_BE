# medical notes

from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal, List
from bson import ObjectId
from datetime import datetime

MedicalNoteType = Literal["consult", "radiology", "surgery", "other"] # TODO

class CreateNoteForm(BaseModel):
    title: str
    content: str
    noteType: MedicalNoteType = "other"

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}, 
    )


class UpdateNoteForm(BaseModel):
    patientId: str
    title: Optional[str] = None
    content: Optional[str] = None
    noteType: Optional[MedicalNoteType] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}, 
    )

class NoteForm(BaseModel):
    patientId: str
    doctorId: List[str] # multiple doctors can add or edit notes
    createdAt: datetime
    lastModified: datetime
    title: str
    content: str
    noteType: MedicalNoteType
    deleted: bool

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}, 
    )

