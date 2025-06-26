# for doctors
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db import User, Patient
from app.dto.patient import Patient as PatientModel
from app.utils.utils import to_serializable

async def _get_patient(patient_mrn: str, db: AsyncSession) -> Optional[Patient]:
    query = select(Patient).where(Patient.patient_mrn == patient_mrn)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_new_patient(patient_info: PatientModel, db: AsyncSession):
    try:
        patient = Patient(
            patient_mrn=patient_info.patient_mrn,
            phone_num=patient_info.phone_num,
            first_name=patient_info.name.first_name,
            last_name=patient_info.name.last_name,
            age=patient_info.age,
            body_part=", ".join(patient_info.body_part) if patient_info.body_part else None,
            ai_ready=patient_info.ai_ready
        )
        db.add(patient)
        await db.commit()
        return {"success": True}
    except Exception as e:
        await db.rollback()
        print(f"[create_new_patient error] {e}")
        return {"success": False, "error": str(e)}

async def assign_patient_to_doctor(patient_mrn: str, current_user: User, db: AsyncSession):
    if current_user.position != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can assign patients.")

    patient = await _get_patient(patient_mrn, db)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient information does not exist. Please register this patient.")

    # Load current_user with patients relationship 
    query = select(User).options(selectinload(User.patients)).where(User.user_id == current_user.user_id)
    result = await db.execute(query)
    user_with_patients = result.scalar_one_or_none()
    
    if not user_with_patients:
        raise HTTPException(status_code=404, detail="Cannot find user.")

    # Check if already assigned using relationship
    if patient in user_with_patients.patients:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This patient is already assigned to this doctor.",
        )

    # Add patient to doctor's patient list using relationship
    user_with_patients.patients.append(patient)
    
    await db.commit()
    return {"success": True}

async def get_all_assigned_patients(current_user: User, db: AsyncSession):
    if current_user.position != "doctor":
        raise HTTPException(403, "Only doctors can view patient information.")

    # Load user with patients relationship and nested doctors relationship
    query = select(User).options(
        selectinload(User.patients).selectinload(Patient.doctors)
    ).where(User.user_id == current_user.user_id)
    result = await db.execute(query)
    user_with_patients = result.scalar_one_or_none()
    
    if not user_with_patients or not user_with_patients.patients:
        return {"success": True, "patients": []}

    patient_dicts = []
    for patient in user_with_patients.patients:
        # Get doctor IDs from the relationship
        doctor_ids = [doctor.user_id for doctor in patient.doctors]

        # Get doctor full names from the relationship
        doctor_names = [
            f"{doctor.last_name} {doctor.first_name}" for doctor in patient.doctors
        ]
        
        patient_dict = {
            "patient_mrn": patient.patient_mrn,
            "phone_num": patient.phone_num,
            "name": {
                "first_name": patient.first_name,
                "last_name": patient.last_name
            },
            "doctor_id": doctor_ids,
            "doctor_name": doctor_names,
            "medical_notes": [],  # Will be populated from notes relationship if needed
            "created_at": patient.created_at,
            "age": patient.age,
            "body_part": patient.body_part,
            "ai_ready": patient.ai_ready
        }
        patient_dicts.append(to_serializable(patient_dict))

    return {"success": True, "patients": patient_dicts}

async def get_specific_patient(patient_mrn: str, current_user: User, db: AsyncSession):
    if current_user.position != "doctor":
        raise HTTPException(403, "Only doctors can view patient information.")
    
    # Get patient with doctors relationship loaded
    query = select(Patient).options(selectinload(Patient.doctors)).where(Patient.patient_mrn == patient_mrn)
    result = await db.execute(query)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Cannot find this patient.",
        )
    
    # Check if doctor is assigned to this patient using relationship
    if current_user not in patient.doctors:
        raise HTTPException(
            status_code=404,
            detail="You are not the assigned doctor to this patient.",
        )

    # Get doctor IDs from the relationship
    doctor_ids = [doctor.user_id for doctor in patient.doctors]

    # Get doctor full names from the relationship
    doctor_names = [
        f"{doctor.last_name} {doctor.first_name}" for doctor in patient.doctors
    ]

    patient_dict = {
        "patient_mrn": patient.patient_mrn,
        "phone_num": patient.phone_num,
        "name": {
            "first_name": patient.first_name,
            "last_name": patient.last_name
        },
        "doctor_id": doctor_ids,
        "doctor_name": doctor_names,
        "medical_notes": [],  # Will be populated from notes relationship if needed
        "created_at": patient.created_at,
        "age": patient.age,
        "body_part": patient.body_part,
        "ai_ready": patient.ai_ready
    }

    return {"success": True, "patient": to_serializable(patient_dict)}