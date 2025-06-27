from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.appointment import Appointment as AppointmentModel
from app.service.postgres.appointmentmanage import (
    create_new_appointment
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
