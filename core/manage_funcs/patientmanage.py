# for doctors
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.db import User, Patient
from core.models.patient import Patient as PatientModel
from core.utils import to_serializable

async def _get_patient(patient_id: str, db: AsyncSession) -> Optional[Patient]:
    query = select(Patient).where(Patient.patient_id == patient_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_new_patient(patient_info: PatientModel, db: AsyncSession):
    try:
        patient = Patient(
            patient_id=patient_info.patientId,
            phone_num=patient_info.phoneNum,
            first_name=patient_info.name.firstName,
            last_name=patient_info.name.lastName
        )
        db.add(patient)
        await db.commit()
        return {"success": True}
    except Exception:
        await db.rollback()
        return {"success": False}

async def assign_patient_to_doctor(patient_id: str, current_user: User, db: AsyncSession):
    if current_user.position != "doctor":
        raise HTTPException(status_code=403, detail="의사만 환자를 등록할 수 있습니다.")

    patient = await _get_patient(patient_id, db)
    if not patient:
        raise HTTPException(status_code=404, detail="환자 정보가 없습니다. 환자 정보를 등록해주세요.")

    # Load current_user with patients relationship 
    query = select(User).options(selectinload(User.patients)).where(User.user_id == current_user.user_id)
    result = await db.execute(query)
    user_with_patients = result.scalar_one_or_none()
    
    if not user_with_patients:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # Check if already assigned using relationship
    if patient in user_with_patients.patients:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 이 의사에게 배정된 환자입니다.",
        )

    # Add patient to doctor's patient list using relationship
    user_with_patients.patients.append(patient)
    
    await db.commit()
    return {"success": True}

async def get_all_assigned_patients(current_user: User, db: AsyncSession):
    if current_user.position != "doctor":
        raise HTTPException(403, "의사만 환자 목록을 조회할 수 있습니다.")

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
        
        patient_dict = {
            "patientId": patient.patient_id,
            "phoneNum": patient.phone_num,
            "name": {
                "firstName": patient.first_name,
                "lastName": patient.last_name
            },
            "doctorId": doctor_ids,
            "medicalNotes": [],  # Will be populated from notes relationship if needed
            "createdAt": patient.created_at
        }
        patient_dicts.append(to_serializable(patient_dict))

    return {"success": True, "patients": patient_dicts}

async def get_specific_patient(patient_id: str, current_user: User, db: AsyncSession):
    if current_user.position != "doctor":
        raise HTTPException(403, "의사만 환자 목록을 조회할 수 있습니다.")
    
    # Get patient with doctors relationship loaded
    query = select(Patient).options(selectinload(Patient.doctors)).where(Patient.patient_id == patient_id)
    result = await db.execute(query)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="해당 환자를 찾을 수 없습니다.",
        )
    
    # Check if doctor is assigned to this patient using relationship
    if current_user not in patient.doctors:
        raise HTTPException(
            status_code=404,
            detail="해당 환자의 담당 의사가 아닙니다.",
        )

    # Get doctor IDs from the relationship
    doctor_ids = [doctor.user_id for doctor in patient.doctors]

    patient_dict = {
        "patientId": patient.patient_id,
        "phoneNum": patient.phone_num,
        "name": {
            "firstName": patient.first_name,
            "lastName": patient.last_name
        },
        "doctorId": doctor_ids,
        "medicalNotes": [],  # Will be populated from notes relationship if needed
        "createdAt": patient.created_at
    }

    return {"success": True, "patient": to_serializable(patient_dict)}