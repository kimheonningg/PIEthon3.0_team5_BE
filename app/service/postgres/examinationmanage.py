from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from bson import ObjectId
from typing import List

from app.core.db import User, Patient, Examination, doctor_patient_association
from app.dto.examination import Examination as ExaminationModel

async def create_new_examination(
    examination_info: ExaminationModel, 
    db: AsyncSession,
    doctor_info: User
):
    try:
        examination = Examination(
            examination_id=str(ObjectId()),
            examination_title=examination_info.examination_title,
            examination_date=examination_info.examination_date,
            patient_mrn=examination_info.patient_mrn,
            doctor_id=doctor_info.user_id
        )
        db.add(examination)
        await db.commit()
        return {"success": True}
    except Exception as e:
        await db.rollback()
        print(f"[create_new_examination error] {e}")
        return {"success": False, "error": str(e)}

async def get_all_examinations(
    patient_mrn: str,
    db: AsyncSession,
    doctor_info: User
):
    stmt = select(Examination).where(Examination.patient_mrn == patient_mrn).order_by(Examination.examination_date.desc())
    result = await db.execute(stmt)
    examinations = result.scalars().all()

    dto_list = [
        ExaminationModel.model_validate(e, from_attributes=True)
        for e in examinations
    ]
    
    response_data = [dto.model_dump() for dto in dto_list]
    
    return response_data