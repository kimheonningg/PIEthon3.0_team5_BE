from pydantic import BaseModel, constr
from typing import List, Optional

from core.models.registerform import Name
from core.models.noteform import NoteForm

class Patient(BaseModel):
    phoneNum: constr(strip_whitespace=True, min_length=9, max_length=11)
    patientId: str # 환자 고유 식별 번호
    doctorLicenceNum: List[str] # multiple doctors are allowed
    name: Name
    medicalNotes: Optional[List[NoteForm]] = None
    
