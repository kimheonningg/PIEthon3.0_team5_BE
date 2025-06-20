from pydantic import BaseModel

from core.models.medicalnote import MedicalNoteType

class CreateNoteForm(BaseModel):
    title: str
    content: str
    noteType: MedicalNoteType = "other"