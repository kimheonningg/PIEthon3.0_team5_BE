# for doctors
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from datetime import datetime

from core.db import admin_db
from core.models.patient import Patient
from core.utils import to_serializable

async def _get_patient(patientId: str) -> Optional[Dict[str, Any]]:
    projection = {
        "patientId": 1,
        "name": 1,
        "phoneNum": 1,
        "doctorId": 1,
        "medicalNotes": 1,
        "createdAt": 1
    }
    return await admin_db.patients.find_one(
        {"patientId": patientId}, projection
    )

async def create_new_patient(patientInfo: Patient):
    try:
        doc = patientInfo.model_dump(by_alias=True) 
        doc["createdAt"] = datetime.utcnow()
        if doc.get("doctorId") is None:
            doc["doctorId"] = []
        if doc.get("medicalNotes") is None:
            doc["medicalNotes"] = []
        result = await admin_db.patients.insert_one(doc)
        return {"success": True}
    except:
        return {"success": False}

async def assign_patient_to_doctor(patientId: str, doctorInfo: Dict[str, Any]):
    if doctorInfo.get("position") != "doctor":
        raise HTTPException(status_code=403, detail="의사만 환자를 등록할 수 있습니다.")

    patientDoc = await _get_patient(patientId)
    if not patientDoc:
        raise HTTPException(status_code=404, detail="환자 정보가 없습니다. 환자 정보를 등록해주세요.")

    already_assigned = await admin_db.users.find_one(
        {
            "_id": doctorInfo["_id"],
            "patientList": str(patientDoc["_id"]),
        },
        {"_id": 1},
    )
    if already_assigned:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 이 의사에게 배정된 환자입니다.",
        )

    patientInfo : Patient = {
        "_id": patientDoc["_id"],
        "patientId": patientDoc["patientId"],
        "name": patientDoc.get("name", {}),
        "phoneNum": patientDoc.get("phoneNum", ""),
        "medicalNotes": patientDoc.get("medicalNotes", []),
        "doctorId": patientDoc.get("doctorId", []),
        "createdAt": patientDoc.get("createdAt")
    }
    
    result = await admin_db.users.update_one(
        {"_id": doctorInfo["_id"]}, {"$addToSet": {"patientList": str(patientInfo["_id"])}}
    )

    await admin_db.patients.update_one(
        {"_id": patientDoc["_id"]},
        {"$addToSet": {"doctorId": str(doctorInfo["_id"])}}
    )

    success = result.modified_count == 1
    return {"success": success}

async def get_all_assigned_patients(doctorInfo: Dict[str, Any]):
    if doctorInfo.get("position") != "doctor":
        raise HTTPException(403, "의사만 환자 목록을 조회할 수 있습니다.")

    doctorOid = str(doctorInfo["_id"])
    projection = {
        "patientId": 1,
        "name": 1,
        "phoneNum": 1,
        "medicalNotes": 1,
        "doctorId": 1,
        "createdAt": 1,
    }
    cursor = admin_db.patients.find(
        {"doctorId": doctorOid}, projection
    ).sort("createdAt", -1)

    patients_raw = await cursor.to_list(length=None)
    patients = [to_serializable(p) for p in patients_raw]

    return {"success": True, "patients": patients}

async def get_specific_patient(patientId: str, doctorInfo: Dict[str, Any]):
    if doctorInfo.get("position") != "doctor":
        raise HTTPException(403, "의사만 환자 목록을 조회할 수 있습니다.")
    
    doctorOid = str(doctorInfo["_id"])

    projection = {
        "patientId": 1,
        "name": 1,
        "phoneNum": 1,
        "medicalNotes": 1,
        "doctorId": 1,
        "createdAt": 1,
    }

    patient = await admin_db.patients.find_one(
        {"patientId": patientId, "doctorId": doctorOid}, 
        projection,
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="해당 환자를 찾을 수 없거나 담당 의사가 아닙니다.",
        )

    return {"success": True, "patient": to_serializable(patient)}

