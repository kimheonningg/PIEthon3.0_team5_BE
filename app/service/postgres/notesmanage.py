# file for functions that handle medical notes
from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from bson import ObjectId

from app.dto.noteform import CreateNoteForm, UpdateNoteForm
from app.core.db import User, Patient, Note
from app.utils.utils import to_serializable

async def add_new_note(
    patient_mrn: str,
    note_in: CreateNoteForm,
    current_user: User,
    db: AsyncSession,
) -> Dict:
    if current_user.position != "doctor":
        raise HTTPException(403, "Only doctors can create medical notes.")
        
    # Check if patient exists and load with relationships
    query = select(Patient).options(selectinload(Patient.doctors)).where(Patient.patient_mrn == patient_mrn)
    result = await db.execute(query)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient information does not exist. Please register this patient.")

    # Create note with foreign key relationships
    note_id = str(ObjectId())  # Generate unique note ID
    note = Note(
        note_id=note_id,
        patient_mrn=patient.patient_mrn,
        doctor_id=current_user.user_id,
        title=note_in.title,
        content=note_in.content,
        note_type=note_in.note_type
    )

    try:
        db.add(note)
        
        # Add doctor to patient's doctors relationship if not already there
        if current_user not in patient.doctors:
            patient.doctors.append(current_user)
        
        await db.commit()
        await db.refresh(note)
        
        # Convert note to dict for response
        note_dict = {
            "id": note.note_id,
            "patient_mrn": patient_mrn,  # Return the string patient_mrn for API compatibility
            "doctor_id": [current_user.user_id],  # Keep as list for API compatibility
            "title": note.title,
            "content": note.content,
            "note_type": note.note_type,
            "created_at": note.created_at,
            "last_modified": note.last_modified,
            "deleted": note.deleted
        }
        
        return {"success": True, "note": to_serializable(note_dict)}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save note."
        )

async def update_existing_note(
    note_id: str,  # Keep as string
    note_in: UpdateNoteForm,
    current_user: User,
    db: AsyncSession,
) -> Dict:
    if current_user.position != "doctor":
        raise HTTPException(403, "Only doctors can modify this note.")
    
    # Check if patient exists
    query = select(Patient).where(Patient.patient_mrn == note_in.patient_mrn)
    result = await db.execute(query)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient information does not exist. Please register this patient.")
    
    # Get the note with relationships
    note_query = select(Note).options(
        selectinload(Note.doctor),
        selectinload(Note.patient)
    ).where(and_(Note.note_id == note_id, Note.deleted == False))
    note_result = await db.execute(note_query)
    note = note_result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="This note does not exist")
    
    # Check if there's anything to update
    has_updates = False
    if note_in.title is not None:
        note.title = note_in.title
        has_updates = True
    if note_in.content is not None:
        note.content = note_in.content
        has_updates = True
    if note_in.note_type is not None:
        note.note_type = note_in.note_type
        has_updates = True

    if not has_updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is nothing to modify",
        )

    note.last_modified = datetime.utcnow()
    
    await db.commit()

    # Convert note to dict for response
    note_dict = {
        "id": note.note_id,
        "patient_mrn": note.patient.patient_mrn,  # Get patient_mrn from relationship
        "doctor_id": [note.doctor.user_id],  # Get doctor ID from relationship, keep as list for API compatibility
        "title": note.title,
        "content": note.content,
        "note_type": note.note_type,
        "created_at": note.created_at,
        "last_modified": note.last_modified,
        "deleted": note.deleted
    }

    return {"success": True, "note": to_serializable(note_dict)}

async def get_all_notes(
    patient_mrn: str,
    current_user: User,
    db: AsyncSession,
):
    if current_user.position != "doctor":
        raise HTTPException(403, "Only doctors can view medical notes.")

    # Check if patient exists
    query = select(Patient).where(Patient.patient_mrn == patient_mrn)
    result = await db.execute(query)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(404, "Patient information does not exist. Please register this patient.")
    
    # Get all notes for this patient using foreign key relationship
    notes_query = select(Note).options(
        selectinload(Note.doctor),
        selectinload(Note.patient)
    ).where(
        and_(Note.patient_mrn == patient.patient_mrn, Note.deleted == False)
    ).order_by(Note.last_modified.desc())
    
    notes_result = await db.execute(notes_query)
    notes = notes_result.scalars().all()

    # Convert notes to dict format
    note_dicts = []
    for note in notes:
        note_dict = {
            "id": note.note_id,
            "patient_mrn": note.patient.patient_mrn,  # Get string patient_mrn from relationship
            "doctor_id": [note.doctor.user_id],  # Keep as list for API compatibility
            "title": note.title,
            "content": note.content,
            "note_type": note.note_type,
            "created_at": note.created_at,
            "last_modified": note.last_modified,
            "deleted": note.deleted
        }
        note_dicts.append(to_serializable(note_dict))

    return {"success": True, "notes": note_dicts}

async def get_specific_note(
    note_id: str,  # Keep as string
    current_user: User,
    db: AsyncSession,
):
    if current_user.position != "doctor":
        raise HTTPException(403, "Only doctors can view medical notes.")
    
    # Get the note with relationships
    query = select(Note).options(
        selectinload(Note.doctor),
        selectinload(Note.patient)
    ).where(and_(Note.note_id == note_id, Note.deleted == False))
    result = await db.execute(query)
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(404, "This note does not exist.")

    # Convert note to dict for response
    note_dict = {
        "id": note.note_id,
        "patient_mrn": note.patient.patient_mrn,  # Get string patient_mrn from relationship
        "doctor_id": [note.doctor.user_id],  # Keep as list for API compatibility
        "title": note.title,
        "content": note.content,
        "note_type": note.note_type,
        "created_at": note.created_at,
        "last_modified": note.last_modified,
        "deleted": note.deleted
    }

    return {"success": True, "note": to_serializable(note_dict)}