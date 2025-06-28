from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from bson import ObjectId

from app.core.db import User, Patient, Examination
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
