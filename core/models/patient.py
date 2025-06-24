from pydantic import BaseModel, constr
from core.models.registerform import Name
from core.models.noteform import NoteForm

class Patient(BaseModel):
    phoneNum: constr(strip_whitespace=True, min_length=9, max_length=11)
    patientId: str
    doctorLicenceNum: List[str] # multiple doctors are allowed
    name: Name
    medicalNotes: List[NoteForm] = []
    
