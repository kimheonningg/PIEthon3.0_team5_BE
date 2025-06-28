from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.medicalhistory import Medicalhistory as MedicalhistoryModel
from app.service.postgres.medicalhistorymanage import (
    create_new_medicalhistory,
    get_medications,
    get_procedures
)
from app.core.db import get_db, Medicalhistory, User
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/create")
async def create_medicalhistory(
    medicalhistory_info: MedicalhistoryModel, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await create_new_medicalhistory(
        medicalhistory_info, db, current_user
    )
    return success

@router.get('/medications/{patient_mrn}') # get medical histories with 'medication' tag
async def get_medications_medicalhistory(
    patient_mrn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await get_medications(
        patient_mrn, db, current_user
    )
    return success

@router.get('/procedures/{patient_mrn}') # get medical histories with 'procedure' tag
async def get_procedures_medicalhistory(
    patient_mrn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await get_procedures(
        patient_mrn, db, current_user
    )
    return success