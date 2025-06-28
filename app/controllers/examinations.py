from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.examination import Examination as ExaminationModel
from app.service.postgres.examinationmanage import (
    create_new_examination
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