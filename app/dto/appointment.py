from datetime import datetime
from pydantic import BaseModel, constr, ConfigDict
from typing import List, Optional
from bson import ObjectId

from .registerform import Name

class Appointment(BaseModel):
   # appointment_id: str
   appointment_detail: str
   start_time: datetime
   finish_time: datetime
   patient_mrn: str
   # doctor_id: str