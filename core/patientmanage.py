# for doctors
from typing import Dict, Any, Optional
from fastapi import HTTPException

from core.db import admin_db
from core.models.patientinfo import PatientInfo

async def _get_patient(patient_id: str) -> Optional[Dict[str, Any]]:
    projection = {
        "patientId": 1,
        "name": 1,
        "phoneNum": 1,
        "medicalNotes": 1,
    }
    return await admin_db.users.find_one(
        {"patientId": patient_id, "position": "patient"}, projection
    )

async def assign_patient_to_doctor(patientId: str, doctorInfo: Dict[str, Any]):
    if doctorInfo.get("position") != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can assign patients")

    patientDoc = await _get_patient(patientId)
    if not patientDoc:
        raise HTTPException(status_code=404, detail="Patient not found")

    patientInfo : PatientInfo = {
        "patientId": patientDoc["patientId"],
        "patientOid": patientDoc["_id"],
        "name": patientDoc.get("name", {}),
        "phoneNum": patientDoc.get("phoneNum", ""),
        "medicalNotes": patientDoc.get("medicalNotes", []),
    }
    
    result = await admin_db.users.update_one(
        {"_id": doctorInfo["_id"]}, {"$addToSet": {"patientList": patientInfo}}
    )

    success = result.modified_count == 1
    return {"success": success}