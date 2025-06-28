from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Medicalhistory(BaseModel): 
    medicalhistory_title: str
    medicalhistory_content: str
    medicalhistory_date: datetime
    patient_mrn: str
    tags: Optional[List[str]]
