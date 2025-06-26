# medical notes

from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal, List
from bson import ObjectId
from datetime import datetime

MedicalNoteType = Literal["consult", "radiology", "surgery", "other"] # TODO

class CreateNoteForm(BaseModel):
    title: str
    content: str
    note_type: MedicalNoteType = "other"

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}, 
    )


class UpdateNoteForm(BaseModel):
    patient_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    note_type: Optional[MedicalNoteType] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}, 
    )

class NoteForm(BaseModel):
    patient_id: str
    doctor_id: List[str] # multiple doctors can add or edit notes
    created_at: datetime
    last_modified: datetime
    title: str
    content: str
    note_type: MedicalNoteType
    deleted: bool

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}, 
    )

