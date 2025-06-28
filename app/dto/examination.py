from pydantic import BaseModel
from datetime import datetime

class Examination(BaseModel): 
    # for the 'recent examinations' widget
    examination_title: str
    examination_date: datetime
    patient_mrn: str

    class Config:
        from_attributes = True  
