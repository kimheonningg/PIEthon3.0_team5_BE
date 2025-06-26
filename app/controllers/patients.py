from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.patient import Patient
from app.service.postgres.patientmanage import (
    create_new_patient,
    assign_patient_to_doctor,
    get_all_assigned_patients,
    get_specific_patient
)
from app.core.auth import get_current_user
from app.core.db import get_db, User

router = APIRouter()

@router.get("/")  # get all patients assigned to the current doctor
async def get_patients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await get_all_assigned_patients(current_user, db)
    return result

@router.get("/{patient_mrn}")  # get specific patient with patient id
async def get_patient(
    patient_mrn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await get_specific_patient(patient_mrn, current_user, db)
    return result

@router.post("/create")
async def create_patient(patient_info: Patient, db: AsyncSession = Depends(get_db)):
    success = await create_new_patient(patient_info, db)
    return success

@router.post("/assign/{patient_mrn}")
async def assign_patient(
    patient_mrn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await assign_patient_to_doctor(patient_mrn, current_user, db)
    return result