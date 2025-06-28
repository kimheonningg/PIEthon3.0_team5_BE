from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.examination import Examination as ExaminationModel
from app.service.postgres.examinationmanage import (
    create_new_examination,
    get_all_examinations
)
from app.core.db import get_db, Examination, User
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/create")
async def create_examination(
    examination_info: ExaminationModel, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await create_new_examination(
        examination_info, db, current_user
    )
    return success

@router.get("/{patient_mrn}") # get examinations of specific patient with patient_mrn
async def get_examination(
    patient_mrn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await get_all_examinations(
        patient_mrn, db, current_user
    )

    return success