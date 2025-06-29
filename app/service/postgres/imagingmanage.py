from typing import Dict, Any, List
from fastapi import HTTPException, status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import logging

from app.core.db.schema import ImagingSubject, ImagingSeries, Disease, Patient, User
from app.utils.utils import to_serializable

logger = logging.getLogger(__name__)


async def create_imaging_subject(
    subject_data: Dict[str, Any], 
    current_user: User, 
    db: AsyncSession
) -> Dict[str, Any]:
    """Create a new imaging subject for a patient."""
    try:
        # Verify patient exists and doctor has access
        patient_query = select(Patient).options(selectinload(Patient.doctors)).where(
            Patient.patient_mrn == subject_data["patient_mrn"]
        )
        result = await db.execute(patient_query)
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if current_user not in patient.doctors:
            raise HTTPException(status_code=403, detail="Not authorized to access this patient")
        
        # Create imaging subject
        imaging_subject = ImagingSubject(
            subject_name=subject_data["subject_name"],
            patient_mrn=subject_data["patient_mrn"],
            modality=subject_data["modality"],
            body_part=subject_data["body_part"],
            study_date=subject_data.get("study_date"),
            study_description=subject_data.get("study_description")
        )
        
        db.add(imaging_subject)
        await db.flush()  # Get the auto-generated subject_id
        
        return {
            "success": True,
            "subject_id": imaging_subject.subject_id,
            "message": "Imaging subject created successfully"
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        return {"success": False, "message": "Operation failed", "error": str(e)}


async def add_imaging_series(
    subject_id: int,
    series_data_list: List[Dict[str, Any]],
    current_user: User,
    db: AsyncSession
) -> Dict[str, Any]:
    """Add multiple imaging series to a subject."""
    try:
        # Verify subject exists and user has access
        subject_query = select(ImagingSubject).options(
            selectinload(ImagingSubject.patient).selectinload(Patient.doctors)
        ).where(ImagingSubject.subject_id == subject_id)
        result = await db.execute(subject_query)
        subject = result.scalar_one_or_none()
        
        if not subject:
            raise HTTPException(status_code=404, detail="Imaging subject not found")
        
        if current_user not in subject.patient.doctors:
            raise HTTPException(status_code=403, detail="Not authorized to access this patient")
        
        series_ids = []
        for series_data in series_data_list:
            series = ImagingSeries(
                subject_id=subject_id,
                sequence_type=series_data["sequence_type"],
                file_uri=series_data["file_uri"],
                slices_dir=series_data.get("slices_dir"),
                slice_idx=series_data.get("slice_idx"),
                image_resolution=series_data.get("image_resolution"),
                series_description=series_data.get("series_description"),
                acquisition_time=series_data.get("acquisition_time")
            )
            db.add(series)
            await db.flush()
            series_ids.append(series.series_id)
        
        return {
            "success": True,
            "series_ids": series_ids,
            "message": f"Added {len(series_ids)} imaging series"
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        return {"success": False, "message": "Operation failed", "error": str(e)}


async def add_disease_annotations(
    series_ids: List[int],
    disease_data_list: List[Dict[str, Any]],
    current_user: User,
    db: AsyncSession
) -> Dict[str, Any]:
    """Add disease annotations to imaging series."""
    try:
        disease_ids = []
        for disease_data in disease_data_list:
            series_index = disease_data["series_index"]
            if series_index >= len(series_ids):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Series index {series_index} out of range"
                )
            
            series_id = series_ids[series_index]
            
            # Verify series exists and user has access
            series_query = select(ImagingSeries).options(
                selectinload(ImagingSeries.subject).selectinload(ImagingSubject.patient).selectinload(Patient.doctors)
            ).where(ImagingSeries.series_id == series_id)
            result = await db.execute(series_query)
            series = result.scalar_one_or_none()
            
            if not series:
                raise HTTPException(status_code=404, detail=f"Imaging series {series_id} not found")
            
            if current_user not in series.subject.patient.doctors:
                raise HTTPException(status_code=403, detail="Not authorized to access this patient")
            
            disease = Disease(
                series_id=series_id,
                bounding_box=disease_data["bounding_box"],
                confidence_score=disease_data.get("confidence_score"),
                class_name=disease_data.get("class_name"),
                disease=disease_data.get("disease")
            )
            db.add(disease)
            await db.flush()
            disease_ids.append(disease.disease_id)
        
        return {
            "success": True,
            "disease_ids": disease_ids,
            "message": f"Added {len(disease_ids)} disease annotations"
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        return {"success": False, "message": "Operation failed", "error": str(e)}


async def get_patient_imaging_studies(
    patient_mrn: str,
    current_user: User,
    db: AsyncSession
) -> Dict[str, Any]:
    """Get all imaging studies for a patient."""
    try:
        # Verify patient exists and user has access
        patient_query = select(Patient).options(selectinload(Patient.doctors)).where(
            Patient.patient_mrn == patient_mrn
        )
        result = await db.execute(patient_query)
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if current_user not in patient.doctors:
            raise HTTPException(status_code=403, detail="Not authorized to access this patient")
        
        # Get all imaging subjects with their series and diseases
        subjects_query = select(ImagingSubject).options(
            selectinload(ImagingSubject.series).selectinload(ImagingSeries.diseases)
        ).where(ImagingSubject.patient_mrn == patient_mrn)
        
        result = await db.execute(subjects_query)
        subjects = result.scalars().all()
        
        studies = []
        for subject in subjects:
            subject_dict = {
                "subject_id": subject.subject_id,
                "subject_name": subject.subject_name,
                "patient_mrn": subject.patient_mrn,
                "modality": subject.modality.value,
                "body_part": subject.body_part.value,
                "study_date": subject.study_date.isoformat() if subject.study_date else None,
                "study_description": subject.study_description,
                "created_at": subject.created_at.isoformat(),
                "series": []
            }
            
            for series in subject.series:
                series_dict = {
                    "series_id": series.series_id,
                    "sequence_type": series.sequence_type.value,
                    "file_uri": series.file_uri,
                    "slices_dir": series.slices_dir,
                    "slice_idx": series.slice_idx,
                    "image_resolution": series.image_resolution,
                    "series_description": series.series_description,
                    "acquisition_time": series.acquisition_time.isoformat() if series.acquisition_time else None,
                    "created_at": series.created_at.isoformat(),
                    "diseases": []
                }
                
                for disease in series.diseases:
                    disease_dict = {
                        "disease_id": disease.disease_id,
                        "bounding_box": disease.bounding_box,
                        "disease": disease.disease,
                        "confidence_score": float(disease.confidence_score) if disease.confidence_score else None,
                        "class_name": disease.class_name.value if disease.class_name else None,
                        "created_at": disease.created_at.isoformat()
                    }
                    series_dict["diseases"].append(disease_dict)
                
                subject_dict["series"].append(series_dict)
            
            studies.append(subject_dict)
        
        return {
            "success": True,
            "patient_mrn": patient_mrn,
            "imaging_studies": studies,
            "total_studies": len(studies)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "message": "Operation failed", "error": str(e)}


async def get_imaging_subject(
    subject_id: int,
    current_user: User,
    db: AsyncSession
) -> Dict[str, Any]:
    """Get a specific imaging subject with all its series and diseases."""
    try:
        # Get subject with all related data
        subject_query = select(ImagingSubject).options(
            selectinload(ImagingSubject.patient).selectinload(Patient.doctors),
            selectinload(ImagingSubject.series).selectinload(ImagingSeries.diseases)
        ).where(ImagingSubject.subject_id == subject_id)
        
        result = await db.execute(subject_query)
        subject = result.scalar_one_or_none()
        
        if not subject:
            raise HTTPException(status_code=404, detail="Imaging subject not found")
        
        if current_user not in subject.patient.doctors:
            raise HTTPException(status_code=403, detail="Not authorized to access this patient")
        
        # Build response similar to get_patient_imaging_studies but for single subject
        subject_dict = {
            "subject_id": subject.subject_id,
            "subject_name": subject.subject_name,
            "patient_mrn": subject.patient_mrn,
            "modality": subject.modality.value,
            "body_part": subject.body_part.value,
            "study_date": subject.study_date.isoformat() if subject.study_date else None,
            "study_description": subject.study_description,
            "created_at": subject.created_at.isoformat(),
            "series": []
        }
        
        for series in subject.series:
            series_dict = {
                "series_id": series.series_id,
                "sequence_type": series.sequence_type.value,
                "file_uri": series.file_uri,
                "slices_dir": series.slices_dir,
                "slice_idx": series.slice_idx,
                "image_resolution": series.image_resolution,
                "series_description": series.series_description,
                "acquisition_time": series.acquisition_time.isoformat() if series.acquisition_time else None,
                "created_at": series.created_at.isoformat(),
                "diseases": []
            }
            
            for disease in series.diseases:
                disease_dict = {
                    "disease_id": disease.disease_id,
                    "bounding_box": disease.bounding_box,
                    "disease": disease.disease,
                    "confidence_score": float(disease.confidence_score) if disease.confidence_score else None,
                    "class_name": disease.class_name.value if disease.class_name else None,
                    "created_at": disease.created_at.isoformat()
                }
                series_dict["diseases"].append(disease_dict)
            
            subject_dict["series"].append(series_dict)
        
        return {
            "success": True,
            "imaging_subject": subject_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "message": "Failed to get imaging subject", "error": str(e)}


async def delete_imaging_subject(
    subject_id: int,
    current_user: User,
    db: AsyncSession
) -> Dict[str, Any]:
    """Delete an imaging subject and all its related data."""
    try:
        # Get subject with patient info for authorization
        subject_query = select(ImagingSubject).options(
            selectinload(ImagingSubject.patient).selectinload(Patient.doctors)
        ).where(ImagingSubject.subject_id == subject_id)
        
        result = await db.execute(subject_query)
        subject = result.scalar_one_or_none()
        
        if not subject:
            raise HTTPException(status_code=404, detail="Imaging subject not found")
        
        if current_user not in subject.patient.doctors:
            raise HTTPException(status_code=403, detail="Not authorized to access this patient")
        
        # Delete cascades should handle series and diseases
        await db.delete(subject)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Imaging subject {subject_id} deleted successfully"
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        return {"success": False, "message": "Failed to delete imaging subject", "error": str(e)}


async def update_disease_annotation(
    disease_id: int,
    update_data: Dict[str, Any],
    current_user: User,
    db: AsyncSession
) -> Dict[str, Any]:
    """Update a disease annotation."""
    try:
        # Get disease with full relationship chain for authorization
        disease_query = select(Disease).options(
            selectinload(Disease.series).selectinload(ImagingSeries.subject).selectinload(ImagingSubject.patient).selectinload(Patient.doctors)
        ).where(Disease.disease_id == disease_id)
        
        result = await db.execute(disease_query)
        disease = result.scalar_one_or_none()
        
        if not disease:
            raise HTTPException(status_code=404, detail="Disease annotation not found")
        
        if current_user not in disease.series.subject.patient.doctors:
            raise HTTPException(status_code=403, detail="Not authorized to access this patient")
        
        # Update fields
        if "bounding_box" in update_data:
            disease.bounding_box = update_data["bounding_box"]
        if "confidence_score" in update_data:
            disease.confidence_score = update_data["confidence_score"]
        if "class_name" in update_data:
            disease.class_name = update_data["class_name"]
        if "disease" in update_data:
            disease.disease = update_data["disease"]
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Disease annotation {disease_id} updated successfully"
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        return {"success": False, "message": "Operation failed", "error": str(e)}


