from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Literal
from bson import ObjectId

MedicalNoteType = Literal["consult", "radiology", "surgery"] # TODO

class MedicalNote(BaseModel):
    doctorId: str
    patientId: ObjectId
    createdAt: datetime
    lastModified: datetime
    title: str
    content: str
    noteType: MedicalNoteType
    deleted: bool
    # TODO: image

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )