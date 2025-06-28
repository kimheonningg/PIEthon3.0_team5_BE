from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LabResult(BaseModel):
    lab_result_id: Optional[int] = None
    test_name: str
    result_value: str
    normal_values: str
    unit: str
    lab_date: datetime
    medicalhistory_id: Optional[str] = None
    patient_mrn: Optional[str] = None
