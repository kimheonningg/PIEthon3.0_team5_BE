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

async def get_all_appointments (doctor_info: User, db: AsyncSession): # get all appointments assigned to the doctor
    try:
        result = await db.execute(
            select(Appointment)
            .options(selectinload(Appointment.patient))
            .where(Appointment.doctor_id == doctor_info.user_id)
        )
        appointments = result.scalars().all()

        serialized = []
        for appt in appointments:
            serialized.append({
                "appointment_id": appt.appointment_id,
                "appointment_detail": appt.appointment_detail,
                "start_time": appt.start_time.isoformat(),
                "finish_time": appt.finish_time.isoformat(),
                "patient": {
                    "patient_mrn": appt.patient.patient_mrn,
                    "first_name": appt.patient.first_name,
                    "last_name": appt.patient.last_name,
                    "age": appt.patient.age,
                    "phone_num": appt.patient.phone_num,
                }
            })

        return {"success": True, "appointments": serialized}
    except Exception as e:
        print(f"[get_all_appointments error] {e}")
        return {"success": False, "error": str(e)}

async def get_specific_appointment(
    patient_mrn: str,
    doctor_info: User, 
    db: AsyncSession
):
    try:
        result = await db.execute(
            select(Appointment)
            .options(selectinload(Appointment.patient))
            .where(
                Appointment.doctor_id == doctor_info.user_id,
                Appointment.patient_mrn == patient_mrn
            )
        )
        appointments = result.scalars().all()

        serialized = []
        for appt in appointments:
            serialized.append({
                "appointment_id": appt.appointment_id,
                "appointment_detail": appt.appointment_detail,
                "start_time": appt.start_time.isoformat(),
                "finish_time": appt.finish_time.isoformat(),
                "patient": {
                    "patient_mrn": appt.patient.patient_mrn,
                    "first_name": appt.patient.first_name,
                    "last_name": appt.patient.last_name,
                    "age": appt.patient.age,
                    "phone_num": appt.patient.phone_num,
                }
            })

        return {"success": True, "appointments": serialized}
    except Exception as e:
        print(f"[get_specific_appointment error] {e}")
        return {"success": False, "error": str(e)}

async def get_an_appointment_by_id(
    appointment_id: str,
    doctor_info: User,
    db: AsyncSession
):
    try:
        result = await db.execute(
            select(Appointment)
            .options(selectinload(Appointment.patient))
            .where(
                Appointment.appointment_id == appointment_id,
                Appointment.doctor_id == doctor_info.user_id
            )
        )
        appt = result.scalars().first()

        if not appt:
            return {"success": False, "error": "Appointment not found"}

        return {
            "success": True,
            "appointment": {
                "appointment_id": appt.appointment_id,
                "appointment_detail": appt.appointment_detail,
                "start_time": appt.start_time.isoformat(),
                "finish_time": appt.finish_time.isoformat(),
                "patient": {
                    "patient_mrn": appt.patient.patient_mrn,
                    "first_name": appt.patient.first_name,
                    "last_name": appt.patient.last_name,
                    "age": appt.patient.age,
                    "phone_num": appt.patient.phone_num,
                }
            }
        }

    except Exception as e:
        print(f"[get_an_appointment_by_id error] {e}")
        return {"success": False, "error": str(e)}
