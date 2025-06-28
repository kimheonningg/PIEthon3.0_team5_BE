from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from bson import ObjectId

from app.core.db import User, Patient, Medicalhistory
from app.dto.medicalhistory import Medicalhistory as MedicalhistoryModel

async def create_new_medicalhistory(
    medicalhistory_info: MedicalhistoryModel, 
    db: AsyncSession,
    doctor_info: User
):
    try:
        medicalhistory = Medicalhistory(
            medicalhistory_id=str(ObjectId()),
            medicalhistory_date=medicalhistory_info.medicalhistory_date,
            medicalhistory_title=medicalhistory_info.medicalhistory_title,
            medicalhistory_content=medicalhistory_info.medicalhistory_content,
            tags=medicalhistory_info.tags or [],
            patient_mrn=medicalhistory_info.patient_mrn,
            doctor_id=doctor_info.user_id
        )
        db.add(medicalhistory)
        await db.commit()
        return {"success": True}
    except Exception as e:
        await db.rollback()
        print(f"[create_new_medicalhistory error] {e}")
        return {"success": False, "error": str(e)}
