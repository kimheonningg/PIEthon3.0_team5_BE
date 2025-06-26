from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.noteform import CreateNoteForm, UpdateNoteForm
from app.service.postgres.notesmanage import (
    add_new_note,
    update_existing_note,
    get_all_notes,
    get_specific_note
)
from app.core.auth import get_current_user
from app.core.db import get_db, User

router = APIRouter()

@router.post("/create/{patient_id}")
async def create_note(
    patient_id: str,
    note_in: CreateNoteForm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await add_new_note(patient_id, note_in, current_user, db)
    return result
    
@router.post("/update/{note_id}")
async def update_note(
    note_id: str,
    note_in: UpdateNoteForm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await update_existing_note(note_id, note_in, current_user, db)
    return result

@router.get("/all/{patient_id}")  # get all notes for that patient with patient_id
async def get_notes(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await get_all_notes(patient_id, current_user, db)
    return result

@router.get("/{note_id}")  # get specific note with note_id
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await get_specific_note(note_id, current_user, db)
    return result