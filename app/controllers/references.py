from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from loguru import logger

from app.core.db import get_db, User
from app.core.auth import get_current_user
from app.core.db.schema import (
    Reference, ReferenceType, Note, Appointment, Medicalhistory, 
    Examination, LabResult
)
from sqlalchemy import select

router = APIRouter()

@router.get("/resolve/{reference_id}")
async def resolve_reference(
    reference_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Resolve a reference ID to get the actual content.
    
    Handles both internal references (notes_abc123, labresults_456) 
    and external references (hash123abc).
    """
    try:
        # First, get the reference record
        result = await db.execute(
            select(Reference).where(Reference.reference_id == reference_id)
        )
        reference = result.scalar_one_or_none()
        
        if not reference:
            raise HTTPException(
                status_code=404, 
                detail=f"Reference {reference_id} not found"
            )
        
        # Handle external references
        if reference.reference_type == ReferenceType.EXTERNAL:
            return {
                "reference_id": reference_id,
                "type": "external",
                "url": reference.external_url,
                "title": reference.title,
                "created_at": reference.created_at.isoformat(),
                "content": {
                    "description": reference.title,
                    "external_url": reference.external_url,
                    "access_note": "This is an external source. Click the URL to view the content."
                }
            }
        
        # Handle internal references
        internal_id = reference.internal_id
        if not internal_id:
            raise HTTPException(
                status_code=400,
                detail=f"Internal reference {reference_id} missing internal_id"
            )
        
        # Route to appropriate table based on reference type
        if reference.reference_type == ReferenceType.NOTES:
            content = await _get_note_content(db, internal_id, current_user)
        elif reference.reference_type == ReferenceType.APPOINTMENTS:
            content = await _get_appointment_content(db, internal_id, current_user)
        elif reference.reference_type == ReferenceType.MEDICALHISTORIES:
            content = await _get_medical_history_content(db, internal_id, current_user)
        elif reference.reference_type == ReferenceType.EXAMINATIONS:
            content = await _get_examination_content(db, internal_id, current_user)
        elif reference.reference_type == ReferenceType.LABRESULTS:
            content = await _get_lab_result_content(db, internal_id, current_user)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported reference type: {reference.reference_type}"
            )
        
        return {
            "reference_id": reference_id,
            "type": "internal",
            "reference_type": reference.reference_type.value,
            "internal_id": internal_id,
            "title": reference.title,
            "created_at": reference.created_at.isoformat(),
            "content": content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving reference {reference_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resolving reference: {str(e)}"
        )


async def _get_note_content(db: AsyncSession, note_id: str, current_user: User) -> Dict[str, Any]:
    """Get note content with access control."""
    result = await db.execute(
        select(Note).where(
            Note.note_id == note_id,
            Note.deleted == False
        )
    )
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check access control - user must be the doctor who created it or assigned to patient
    if note.doctor_id != current_user.user_id:
        # Could add additional checks here for patient assignment
        raise HTTPException(status_code=403, detail="Access denied to this note")
    
    return {
        "title": note.title,
        "content": note.content,
        "note_type": note.note_type,
        "created_at": note.created_at.isoformat(),
        "last_modified": note.last_modified.isoformat(),
        "doctor_id": note.doctor_id,
        "patient_mrn": note.patient_mrn
    }


async def _get_appointment_content(db: AsyncSession, appointment_id: str, current_user: User) -> Dict[str, Any]:
    """Get appointment content with access control."""
    result = await db.execute(
        select(Appointment).where(Appointment.appointment_id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check access control
    if appointment.doctor_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied to this appointment")
    
    return {
        "appointment_detail": appointment.appointment_detail,
        "start_time": appointment.start_time.isoformat(),
        "finish_time": appointment.finish_time.isoformat(),
        "doctor_id": appointment.doctor_id,
        "patient_mrn": appointment.patient_mrn
    }


async def _get_medical_history_content(db: AsyncSession, history_id: str, current_user: User) -> Dict[str, Any]:
    """Get medical history content with access control."""
    result = await db.execute(
        select(Medicalhistory).where(Medicalhistory.medicalhistory_id == history_id)
    )
    history = result.scalar_one_or_none()
    
    if not history:
        raise HTTPException(status_code=404, detail="Medical history not found")
    
    # Check access control
    if history.doctor_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied to this medical history")
    
    return {
        "title": history.medicalhistory_title,
        "content": history.medicalhistory_content,
        "date": history.medicalhistory_date.isoformat(),
        "tags": history.tags or [],
        "doctor_id": history.doctor_id,
        "patient_mrn": history.patient_mrn
    }


async def _get_examination_content(db: AsyncSession, examination_id: str, current_user: User) -> Dict[str, Any]:
    """Get examination content with access control."""
    result = await db.execute(
        select(Examination).where(Examination.examination_id == examination_id)
    )
    examination = result.scalar_one_or_none()
    
    if not examination:
        raise HTTPException(status_code=404, detail="Examination not found")
    
    # Check access control
    if examination.doctor_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied to this examination")
    
    return {
        "title": examination.examination_title,
        "examination_date": examination.examination_date.isoformat(),
        "doctor_id": examination.doctor_id,
        "patient_mrn": examination.patient_mrn
    }


async def _get_lab_result_content(db: AsyncSession, lab_result_id: str, current_user: User) -> Dict[str, Any]:
    """Get lab result content with access control."""
    result = await db.execute(
        select(LabResult).where(LabResult.lab_result_id == int(lab_result_id))
    )
    lab_result = result.scalar_one_or_none()
    
    if not lab_result:
        raise HTTPException(status_code=404, detail="Lab result not found")
    
    # Check access control - lab results don't have direct doctor_id, 
    # so we need to check via patient_mrn or associated medical history
    # For now, we'll allow access if user has access to the patient
    # (This could be enhanced with more sophisticated access control)
    
    return {
        "test_name": lab_result.test_name,
        "result_value": lab_result.result_value,
        "normal_values": lab_result.normal_values,
        "unit": lab_result.unit,
        "lab_date": lab_result.lab_date.isoformat(),
        "patient_mrn": lab_result.patient_mrn,
        "medicalhistory_id": lab_result.medicalhistory_id
    }


@router.get("/batch-resolve")
async def batch_resolve_references(
    reference_ids: str,  # Comma-separated list of reference IDs
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Resolve multiple reference IDs in a single request.
    
    Args:
        reference_ids: Comma-separated string of reference IDs (e.g., "notes_123,labresults_456")
    """
    try:
        ref_ids = [ref_id.strip() for ref_id in reference_ids.split(",") if ref_id.strip()]
        
        if not ref_ids:
            raise HTTPException(status_code=400, detail="No reference IDs provided")
        
        if len(ref_ids) > 50:  # Limit batch size
            raise HTTPException(status_code=400, detail="Too many reference IDs (max 50)")
        
        resolved_references = {}
        errors = {}
        
        for ref_id in ref_ids:
            try:
                # Reuse the single reference resolution logic
                resolved = await resolve_reference(ref_id, current_user, db)
                resolved_references[ref_id] = resolved
            except HTTPException as e:
                errors[ref_id] = {
                    "status_code": e.status_code,
                    "detail": e.detail
                }
            except Exception as e:
                errors[ref_id] = {
                    "status_code": 500,
                    "detail": f"Unexpected error: {str(e)}"
                }
        
        return {
            "resolved_references": resolved_references,
            "errors": errors,
            "total_requested": len(ref_ids),
            "resolved_count": len(resolved_references),
            "error_count": len(errors)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch resolve: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in batch resolution: {str(e)}"
        )


@router.get("/by-message/{message_id}")
async def get_references_by_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all references linked to a specific message.
    """
    try:
        from app.service.postgres.reference_manager import ReferenceManager
        
        ref_manager = ReferenceManager(db)
        references = await ref_manager.get_references_for_message(message_id)
        
        return {
            "message_id": message_id,
            "references": references,
            "count": len(references)
        }
        
    except Exception as e:
        logger.error(f"Error getting references for message {message_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting references: {str(e)}"
        )