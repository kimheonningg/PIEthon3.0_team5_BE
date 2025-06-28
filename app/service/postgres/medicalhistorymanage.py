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
        medicalhistory_id = str(ObjectId())
        medicalhistory = Medicalhistory(
            medicalhistory_id=medicalhistory_id,
            medicalhistory_date=medicalhistory_info.medicalhistory_date,
            medicalhistory_title=medicalhistory_info.medicalhistory_title,
            medicalhistory_content=medicalhistory_info.medicalhistory_content,
            tags=medicalhistory_info.tags or [],
            patient_mrn=medicalhistory_info.patient_mrn,
            doctor_id=doctor_info.user_id
        )
        db.add(medicalhistory)
        await db.commit()
        return {"success": True, "medicalhistory_id": medicalhistory_id}
    except Exception as e:
        await db.rollback()
        print(f"[create_new_medicalhistory error] {e}")
        return {"success": False, "error": str(e)}

# get medical histories with 'medication' tag
async def get_medications(
    patient_mrn: str,
    db: AsyncSession,
    doctor_info: User
):
    try:
        stmt = (
            select(Medicalhistory)
            .options(selectinload(Medicalhistory.patient))
            .where(
                Medicalhistory.doctor_id == doctor_info.user_id,
                Medicalhistory.patient_mrn == patient_mrn,
                Medicalhistory.tags.any('medication')
            )
            .order_by(Medicalhistory.medicalhistory_date.desc())
        )
        result = await db.execute(stmt)
        histories = result.scalars().all()

        return {
            "success": True,
            "medical_histories": [
                {
                    "medicalhistory_id": h.medicalhistory_id,
                    "medicalhistory_title": h.medicalhistory_title,
                    "medicalhistory_content": h.medicalhistory_content,
                    "medicalhistory_date": h.medicalhistory_date.isoformat(),
                    "tags": h.tags
                }
                for h in histories
            ]
        }
    except Exception as e:
        print(f"[get_medications error] {e}")
        return {"success": False, "error": str(e)}

# get medical histories with 'procedure' tag
async def get_procedures(
    patient_mrn: str,
    db: AsyncSession,
    doctor_info: User
):
    try:
        stmt = (
            select(Medicalhistory)
            .options(selectinload(Medicalhistory.patient))
            .where(
                Medicalhistory.doctor_id == doctor_info.user_id,
                Medicalhistory.patient_mrn == patient_mrn,
                Medicalhistory.tags.any('procedure')
            )
            .order_by(Medicalhistory.medicalhistory_date.desc())
        )
        result = await db.execute(stmt)
        histories = result.scalars().all()

        return {
            "success": True,
            "medical_histories": [
                {
                    "medicalhistory_id": h.medicalhistory_id,
                    "medicalhistory_title": h.medicalhistory_title,
                    "medicalhistory_content": h.medicalhistory_content,
                    "medicalhistory_date": h.medicalhistory_date.isoformat(),
                    "tags": h.tags
                }
                for h in histories
            ]
        }
    except Exception as e:
        print(f"[get_procedures error] {e}")
        return {"success": False, "error": str(e)}