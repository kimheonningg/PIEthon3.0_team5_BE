from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.appointment import Appointment as AppointmentModel
from app.service.postgres.appointmentmanage import (
    create_new_appointment,
    get_all_appointments,
    get_specific_appointment
)
from app.core.db import get_db, Appointment, User
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/create") # create an appointment
async def create_appointment(
    appointment_info: AppointmentModel, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await create_new_appointment(
        appointment_info, db, current_user
    )
    return success

@router.get("/") # get all appointments assigned to that doctor
async def get_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await get_all_appointments(current_user, db)
    return success

@router.get("/{patient_mrn}") # get appointments assigned to the patient with patient_mrn
async def get_appointment(
    patient_mrn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await get_specific_appointment(patient_mrn, current_user, db)
    return success
