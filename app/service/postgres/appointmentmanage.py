from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from bson import ObjectId

from app.core.db import User, Patient, Appointment
from app.dto.appointment import Appointment as AppointmentModel

async def create_new_appointment(
    appointment_info: AppointmentModel, 
    db: AsyncSession,
    doctor_info: User
):
    try:
        appointment = Appointment(
            appointment_id=str(ObjectId()),
            appointment_detail=appointment_info.appointment_detail,
            start_time=appointment_info.start_time,
            finish_time=appointment_info.finish_time,
            patient_mrn=appointment_info.patient_mrn,
            doctor_id=doctor_info.user_id
        )
        db.add(appointment)
        await db.commit()
        return {"success": True}
    except Exception as e:
        await db.rollback()
        print(f"[create_new_appointment error] {e}")
        return {"success": False, "error": str(e)}
