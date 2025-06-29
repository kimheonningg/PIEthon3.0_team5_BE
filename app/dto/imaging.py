from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.db.schema import ModalityType, BodyPartType, SequenceType, DiseaseClassType


class BoundingBoxData(BaseModel):
    """Bounding box coordinates for disease detection."""
    x1: int = Field(..., description="Left x coordinate")
    y1: int = Field(..., description="Top y coordinate") 
    x2: int = Field(..., description="Right x coordinate")
    y2: int = Field(..., description="Bottom y coordinate")
    z1: Optional[int] = Field(None, description="Start z coordinate (for 3D)")
    z2: Optional[int] = Field(None, description="End z coordinate (for 3D)")


class CreateImagingSubjectRequest(BaseModel):
    """Request to create a new imaging subject."""
    subject_name: str = Field(..., max_length=100, description="Subject identifier")
    patient_mrn: str = Field(..., max_length=50, description="Patient MRN") 
    modality: ModalityType = Field(..., description="Imaging modality")
    body_part: BodyPartType = Field(..., description="Body part being imaged")
    study_date: Optional[datetime] = Field(None, description="Study date and time")
    study_description: Optional[str] = Field(None, max_length=255, description="Study description")


class ImagingSeriesData(BaseModel):
    """Data for a single imaging series."""
    sequence_type: SequenceType = Field(..., description="Sequence type")
    file_uri: str = Field(..., max_length=500, description="File URI") 
    slices_dir: Optional[str] = Field(None, max_length=255, description="Directory for image slices")
    slice_idx: Optional[int] = Field(None, description="Slice index")
    image_resolution: Optional[str] = Field(None, max_length=20, description="Image resolution")
    series_description: Optional[str] = Field(None, max_length=255, description="Series description")
    acquisition_time: Optional[datetime] = Field(None, description="Acquisition time")


class AddImagingSeriesRequest(BaseModel):
    """Request to add imaging series to a subject."""
    subject_id: int = Field(..., description="Subject ID")
    series_data: List[ImagingSeriesData] = Field(..., description="List of imaging series")


class DiseaseAnnotationData(BaseModel):
    """Data for disease annotation."""
    series_index: int = Field(..., description="Index of series in the list")
    bounding_box: BoundingBoxData = Field(..., description="Bounding box coordinates")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    class_name: Optional[DiseaseClassType] = Field(None, description="Disease class")
    disease: Optional[str] = Field(None, max_length=50, description="Disease name")


class AddDiseaseAnnotationsRequest(BaseModel):
    """Request to add disease annotations."""
    series_ids: List[int] = Field(..., description="List of series IDs")
    disease_data: List[DiseaseAnnotationData] = Field(..., description="Disease annotations")


class UpdateDiseaseAnnotationRequest(BaseModel):
    """Request to update disease annotation."""
    bounding_box: Optional[BoundingBoxData] = Field(None, description="Updated bounding box")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Updated confidence score")
    class_name: Optional[DiseaseClassType] = Field(None, description="Updated disease class")
    disease: Optional[str] = Field(None, max_length=50, description="Updated disease name")


class CreateImagingStudyRequest(BaseModel):
    """Complete request to create an imaging study with series and annotations."""
    subject_data: CreateImagingSubjectRequest = Field(..., description="Subject information")
    series_data: List[ImagingSeriesData] = Field(..., description="Series data")
    disease_data: Optional[List[DiseaseAnnotationData]] = Field(None, description="Disease annotations")


# Response models
class DiseaseAnnotationResponse(BaseModel):
    """Response model for disease annotation."""
    disease_id: int
    bounding_box: Optional[Dict[str, Any]]
    disease: Optional[str] 
    confidence_score: Optional[float]
    class_name: Optional[str]
    created_at: str


class ImagingSeriesResponse(BaseModel):
    """Response model for imaging series."""
    series_id: int
    sequence_type: str
    file_uri: str
    slices_dir: Optional[str]
    slice_idx: Optional[int]
    image_resolution: Optional[str]
    series_description: Optional[str]
    acquisition_time: Optional[str]
    created_at: str
    diseases: List[DiseaseAnnotationResponse]


class ImagingSubjectResponse(BaseModel):
    """Response model for imaging subject."""
    subject_id: int
    subject_name: str
    patient_mrn: str
    modality: str
    body_part: str
    study_date: Optional[str]
    study_description: Optional[str]
    created_at: str
    series: List[ImagingSeriesResponse]


class PatientImagingStudiesResponse(BaseModel):
    """Response model for patient's imaging studies."""
    success: bool
    patient_mrn: str
    imaging_studies: List[ImagingSubjectResponse]
    total_studies: int
    message: Optional[str] = None


class ImagingSubjectDetailResponse(BaseModel):
    """Response model for single imaging subject details."""
    success: bool
    imaging_subject: ImagingSubjectResponse
    message: Optional[str] = None


class CreateImagingSubjectResponse(BaseModel):
    """Response model for created imaging subject."""
    success: bool
    subject_id: Optional[int] = None
    message: str
    error: Optional[str] = None


class AddSeriesResponse(BaseModel):
    """Response model for added series."""
    success: bool
    series_ids: Optional[List[int]] = None
    message: str
    error: Optional[str] = None


class AddDiseaseAnnotationsResponse(BaseModel):
    """Response model for added disease annotations."""
    success: bool
    disease_ids: Optional[List[int]] = None
    message: str
    error: Optional[str] = None


class CreateCompleteStudyResponse(BaseModel):
    """Response model for complete study creation."""
    success: bool
    subject_id: Optional[int] = None
    series_ids: Optional[List[int]] = None
    disease_ids: Optional[List[int]] = None
    message: str
    error: Optional[str] = None


class BasicSuccessResponse(BaseModel):
    """Basic success response."""
    success: bool
    message: str
    error: Optional[str] = None


