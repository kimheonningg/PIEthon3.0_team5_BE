from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.dto.imaging import (
    CreateImagingSubjectRequest,
    CreateImagingSubjectResponse,
    AddImagingSeriesRequest,
    AddSeriesResponse,
    AddDiseaseAnnotationsRequest,
    AddDiseaseAnnotationsResponse,
    CreateImagingStudyRequest,
    CreateCompleteStudyResponse,
    UpdateDiseaseAnnotationRequest,
    PatientImagingStudiesResponse,
    ImagingSubjectDetailResponse,
    BasicSuccessResponse
)
from app.service.postgres.imagingmanage import (
    create_imaging_subject,
    add_imaging_series,
    add_disease_annotations,
    get_patient_imaging_studies,
    get_imaging_subject,
    delete_imaging_subject,
    update_disease_annotation
)
from app.core.auth import get_current_user
from app.core.db import get_db, User

router = APIRouter()


@router.post("/subjects", response_model=CreateImagingSubjectResponse)
async def create_subject(
    request: CreateImagingSubjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new imaging subject for a patient."""
    subject_data = request.dict()
    result = await create_imaging_subject(subject_data, current_user, db)
    
    if not result.get("success", False):
        await db.commit()
        return CreateImagingSubjectResponse(**result)
    
    await db.commit()
    return CreateImagingSubjectResponse(**result)


@router.post("/subjects/{subject_id}/series", response_model=AddSeriesResponse)
async def add_series_to_subject(
    subject_id: int,
    request: AddImagingSeriesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add imaging series to an existing subject."""
    series_data_list = [series.dict() for series in request.series_data]
    result = await add_imaging_series(subject_id, series_data_list, current_user, db)
    
    if not result.get("success", False):
        await db.commit()
        return AddSeriesResponse(**result)
    
    await db.commit()
    return AddSeriesResponse(**result)


@router.post("/annotations", response_model=AddDiseaseAnnotationsResponse)
async def add_disease_annotations_to_series(
    request: AddDiseaseAnnotationsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add disease annotations to imaging series."""
    disease_data_list = []
    for disease_data in request.disease_data:
        disease_dict = disease_data.dict()
        # Convert BoundingBoxData to dict for JSON storage
        disease_dict["bounding_box"] = disease_dict["bounding_box"]
        disease_data_list.append(disease_dict)
    
    result = await add_disease_annotations(request.series_ids, disease_data_list, current_user, db)
    
    if not result.get("success", False):
        await db.commit()
        return AddDiseaseAnnotationsResponse(**result)
    
    await db.commit()
    return AddDiseaseAnnotationsResponse(**result)


@router.post("/studies", response_model=CreateCompleteStudyResponse)
async def create_complete_imaging_study(
    request: CreateImagingStudyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a complete imaging study with subject, series, and disease annotations."""
    try:
        # Create subject
        subject_data = request.subject_data.dict()
        subject_result = await create_imaging_subject(subject_data, current_user, db)
        
        if not subject_result.get("success", False):
            await db.rollback()
            return CreateCompleteStudyResponse(**subject_result)
        
        subject_id = subject_result["subject_id"]
        
        # Add series
        series_data_list = [series.dict() for series in request.series_data]
        series_result = await add_imaging_series(subject_id, series_data_list, current_user, db)
        
        if not series_result.get("success", False):
            await db.rollback()
            return CreateCompleteStudyResponse(**series_result)
        
        series_ids = series_result["series_ids"]
        disease_ids = []
        
        # Add disease annotations if provided
        if request.disease_data:
            disease_data_list = []
            for disease_data in request.disease_data:
                disease_dict = disease_data.dict()
                # Convert BoundingBoxData to dict for JSON storage
                disease_dict["bounding_box"] = disease_dict["bounding_box"]
                disease_data_list.append(disease_dict)
            
            disease_result = await add_disease_annotations(series_ids, disease_data_list, current_user, db)
            
            if not disease_result.get("success", False):
                await db.rollback()
                return CreateCompleteStudyResponse(**disease_result)
            
            disease_ids = disease_result["disease_ids"]
        
        await db.commit()
        
        return CreateCompleteStudyResponse(
            success=True,
            subject_id=subject_id,
            series_ids=series_ids,
            disease_ids=disease_ids,
            message=f"Complete imaging study created successfully. Subject: {subject_id}, Series: {len(series_ids)}, Diseases: {len(disease_ids)}"
        )
        
    except Exception as e:
        await db.rollback()
        return CreateCompleteStudyResponse(
            success=False,
            message="Failed to create complete imaging study",
            error=str(e)
        )


@router.get("/patients/{patient_mrn}", response_model=PatientImagingStudiesResponse)
async def get_patient_studies(
    patient_mrn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all imaging studies for a patient."""
    result = await get_patient_imaging_studies(patient_mrn, current_user, db)
    
    if not result.get("success", False):
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return PatientImagingStudiesResponse(
            success=False,
            patient_mrn=patient_mrn,
            imaging_studies=[],
            total_studies=0,
            message=result.get("message", "Failed to retrieve imaging studies")
        )
    
    return PatientImagingStudiesResponse(**result)


@router.get("/subjects/{subject_id}", response_model=ImagingSubjectDetailResponse)
async def get_imaging_subject_detail(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific imaging subject."""
    result = await get_imaging_subject(subject_id, current_user, db)
    
    if not result.get("success", False):
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        raise HTTPException(status_code=404, detail="Imaging subject not found")
    
    return ImagingSubjectDetailResponse(**result)


@router.delete("/subjects/{subject_id}", response_model=BasicSuccessResponse)
async def delete_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an imaging subject and all its related data."""
    result = await delete_imaging_subject(subject_id, current_user, db)
    return BasicSuccessResponse(**result)


@router.put("/annotations/{disease_id}", response_model=BasicSuccessResponse)
async def update_disease_annotation_endpoint(
    disease_id: int,
    request: UpdateDiseaseAnnotationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a disease annotation."""
    # Filter out None values and convert BoundingBoxData to dict if present
    update_data = {}
    for key, value in request.dict(exclude_unset=True).items():
        if value is not None:
            if key == "bounding_box":
                update_data[key] = value  # Already a dict from Pydantic
            else:
                update_data[key] = value
    
    result = await update_disease_annotation(disease_id, update_data, current_user, db)
    return BasicSuccessResponse(**result)


@router.get("/studies/summary/{patient_mrn}")
async def get_patient_imaging_summary(
    patient_mrn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a summary of imaging studies for a patient."""
    result = await get_patient_imaging_studies(patient_mrn, current_user, db)
    
    if not result.get("success", False):
        raise HTTPException(status_code=404, detail="Patient not found or no access")
    
    # Create summary
    studies = result["imaging_studies"]
    summary = {
        "patient_mrn": patient_mrn,
        "total_studies": len(studies),
        "modalities": {},
        "body_parts": {},
        "total_series": 0,
        "total_diseases": 0,
        "recent_study": None
    }
    
    for study in studies:
        # Count modalities
        modality = study["modality"]
        summary["modalities"][modality] = summary["modalities"].get(modality, 0) + 1
        
        # Count body parts
        body_part = study["body_part"]
        summary["body_parts"][body_part] = summary["body_parts"].get(body_part, 0) + 1
        
        # Count series and diseases
        summary["total_series"] += len(study["series"])
        for series in study["series"]:
            summary["total_diseases"] += len(series["diseases"])
        
        # Track most recent study
        if summary["recent_study"] is None or study["created_at"] > summary["recent_study"]["created_at"]:
            summary["recent_study"] = {
                "subject_id": study["subject_id"],
                "subject_name": study["subject_name"],
                "modality": study["modality"],
                "body_part": study["body_part"],
                "created_at": study["created_at"]
            }
    
    return {
        "success": True,
        "summary": summary
    }


