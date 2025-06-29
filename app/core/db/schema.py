from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text, Boolean, Integer, ForeignKey, Table, Column, Enum, DECIMAL
from datetime import datetime
from typing import Optional, List
import enum

class ModalityType(enum.Enum):
    XRAY = "x-ray"
    MRI = "mri"

class BodyPartType(enum.Enum):
    CHEST = "chest"
    BRAIN = "brain"

class SequenceType(enum.Enum):
    # MRI sequences
    T1 = "t1"
    T1CE = "t1ce"  # T1 with contrast enhancement
    T2 = "t2"
    FLAIR = "flair"
    DWI = "dwi"
    SEGMENTATION = "seg"  # Ground truth masks
    # X-ray (can be expanded)
    PA = "pa"  # Posterior-anterior
    LATERAL = "lateral"
    AP = "ap"  # Anterior-posterior

class DiseaseClassType(enum.Enum):
    AORTIC_ENLARGEMENT = "Aortic enlargement"
    ATELECTASIS = "Atelectasis"
    CALCIFICATION = "Calcification"
    CARDIOMEGALY = "Cardiomegaly"
    CONSOLIDATION = "Consolidation"
    ILD = "ILD"
    INFILTRATION = "Infiltration"
    LUNG_OPACITY = "Lung Opacity"
    NODULE_MASS = "Nodule/Mass"
    OTHER_LESION = "Other lesion"
    PLEURAL_EFFUSION = "Pleural effusion"
    PLEURAL_THICKENING = "Pleural thickening"
    PNEUMOTHORAX = "Pneumothorax"
    PULMONARY_FIBROSIS = "Pulmonary fibrosis"
    BRAIN_TUMOUR = "brain_tumour"

class ReferenceType(enum.Enum):
    """Reference types for citations."""
    NOTES = "notes"
    APPOINTMENTS = "appointments"
    EXAMINATIONS = "examinations"
    MEDICALHISTORIES = "medicalhistories"
    LABRESULTS = "labresults"
    IMAGING = "imaging"
    EXTERNAL = "external"

class Base(DeclarativeBase):
    pass

# Many-to-many association table for doctors and patients
doctor_patient_association = Table(
    'doctor_patient',
    Base.metadata,
    Column('doctor_id', String(50), ForeignKey('users.user_id'), primary_key=True),
    Column('patient_mrn', String(50), ForeignKey('patients.patient_mrn'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    
    user_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone_num: Mapped[str] = mapped_column(String(11), nullable=False)
    first_name: Mapped[str] = mapped_column(String(40), nullable=False)
    last_name: Mapped[str] = mapped_column(String(40), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(20), default="doctor")
    licence_num: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patients: Mapped[List["Patient"]] = relationship(
        "Patient", 
        secondary=doctor_patient_association, 
        back_populates="doctors"
    )
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="doctor")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="doctor")
    examinations: Mapped[List["Examination"]] = relationship("Examination", back_populates="doctor")
    medicalhistories: Mapped[List["Medicalhistory"]] = relationship("Medicalhistory", back_populates="doctor")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="doctor")

class Patient(Base):
    __tablename__ = 'patients'
    
    patient_mrn: Mapped[str] = mapped_column(String(50), primary_key=True)
    phone_num: Mapped[str] = mapped_column(String(11), nullable=False)
    first_name: Mapped[str] = mapped_column(String(40), nullable=False)
    last_name: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    birthdate: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    body_part: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ai_ready: Mapped[bool] = mapped_column(Boolean, default=True)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships
    doctors: Mapped[List["User"]] = relationship(
        "User", 
        secondary=doctor_patient_association, 
        back_populates="patients"
    )
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="patient")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="patient")
    examinations: Mapped[List["Examination"]] = relationship("Examination", back_populates="patient")
    medicalhistories: Mapped[List["Medicalhistory"]] = relationship("Medicalhistory", back_populates="patient")
    lab_results: Mapped[List["LabResult"]] = relationship("LabResult", back_populates="patient")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="patient")
    imaging_subjects: Mapped[List["ImagingSubject"]] = relationship("ImagingSubject", back_populates="patient")
class Note(Base):
    __tablename__ = 'notes'
    
    note_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(String(20), default="other")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_modified: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Foreign keys - reference string IDs
    patient_mrn: Mapped[str] = mapped_column(String(50), ForeignKey('patients.patient_mrn'), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(50), ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="notes")
    doctor: Mapped["User"] = relationship("User", back_populates="notes")

class Appointment(Base):
    __tablename__ = 'appointments'

    appointment_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    appointment_detail: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Foreign keys
    patient_mrn: Mapped[str] = mapped_column(String(50), ForeignKey('patients.patient_mrn'), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(50), ForeignKey('users.user_id'), nullable=False)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")
    doctor: Mapped["User"] = relationship("User", back_populates="appointments")

class Examination(Base):
    __tablename__ = 'examinations'

    examination_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    examination_title: Mapped[str] = mapped_column(Text, nullable=False)
    examination_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
   
    # Foreign keys
    patient_mrn: Mapped[str] = mapped_column(String(50), ForeignKey('patients.patient_mrn'), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(50), ForeignKey('users.user_id'), nullable=False)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="examinations")
    doctor: Mapped["User"] = relationship("User", back_populates="examinations")

class Medicalhistory(Base):
    __tablename__ = 'medicalhistories'

    medicalhistory_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    medicalhistory_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    medicalhistory_title = mapped_column(Text, nullable=False)
    medicalhistory_content = mapped_column(Text, nullable=False)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String(30)), nullable=True)

     # Foreign keys
    patient_mrn: Mapped[str] = mapped_column(String(50), ForeignKey('patients.patient_mrn'), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(50), ForeignKey('users.user_id'), nullable=False)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="medicalhistories")
    doctor: Mapped["User"] = relationship("User", back_populates="medicalhistories")
    lab_results: Mapped[List["LabResult"]] = relationship("LabResult", back_populates="medicalhistory")

class LabResult(Base):
    __tablename__ = 'lab_result'

    lab_result_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_name: Mapped[str] = mapped_column(String(100), nullable=False)
    result_value: Mapped[str] = mapped_column(String(100), nullable=False)
    normal_values: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    lab_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Foreign keys
    medicalhistory_id: Mapped[str] = mapped_column(String(50), ForeignKey('medicalhistories.medicalhistory_id'), nullable=True)
    patient_mrn: Mapped[str] = mapped_column(String(50), ForeignKey('patients.patient_mrn'), nullable=True)

    # Relationships
    medicalhistory: Mapped["Medicalhistory"] = relationship("Medicalhistory", back_populates="lab_results")
    patient: Mapped["Patient"] = relationship("Patient", back_populates="lab_results")

class Conversation(Base):
    __tablename__ = 'conversations'
    
    conversation_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    patient_mrn: Mapped[str] = mapped_column(String(50), ForeignKey('patients.patient_mrn'), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(50), ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="conversations")
    doctor: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    
    message_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Store tool calls as JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Foreign key
    conversation_id: Mapped[str] = mapped_column(String(50), ForeignKey('conversations.conversation_id'), nullable=False)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    references: Mapped[List["MessageReference"]] = relationship("MessageReference", back_populates="message", cascade="all, delete-orphan")

class Reference(Base):
    __tablename__ = 'references'
    
    reference_id: Mapped[str] = mapped_column(String(64), primary_key=True)  # Hash for external, ID for internal
    reference_type: Mapped[ReferenceType] = mapped_column(Enum(ReferenceType), nullable=False)
    internal_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Primary key of referenced entity
    external_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # URL for external references
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Title/description of reference
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message_references: Mapped[List["MessageReference"]] = relationship("MessageReference", back_populates="reference")

class MessageReference(Base):
    __tablename__ = 'message_references'
    
    message_id: Mapped[str] = mapped_column(String(50), ForeignKey('messages.message_id'), primary_key=True)
    reference_id: Mapped[str] = mapped_column(String(64), ForeignKey('references.reference_id'), primary_key=True)
    
    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="references")
    reference: Mapped["Reference"] = relationship("Reference", back_populates="message_references")

class ImagingSubject(Base):
    __tablename__ = 'imaging_subjects'
    
    subject_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # UNIQUE DB ID
    subject_name: Mapped[str] = mapped_column(String(100), nullable=False)  # "BraTS2021_00621"
    patient_mrn: Mapped[str] = mapped_column(String(50), ForeignKey('patients.patient_mrn'), nullable=False)
    modality: Mapped[ModalityType] = mapped_column(Enum(ModalityType), nullable=False)
    body_part: Mapped[BodyPartType] = mapped_column(Enum(BodyPartType), nullable=False)
    study_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    study_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="imaging_subjects")
    series: Mapped[List["ImagingSeries"]] = relationship("ImagingSeries", back_populates="subject")

class ImagingSeries(Base):
    __tablename__ = 'imaging_series'
    
    series_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # UNIQUE
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey('imaging_subjects.subject_id'), nullable=False)
    sequence_type: Mapped[SequenceType] = mapped_column(Enum(SequenceType), nullable=False)  # NEW!
    file_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    slices_dir: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    slice_idx: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    image_resolution: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    series_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # NEW!
    acquisition_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # NEW!
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subject: Mapped["ImagingSubject"] = relationship("ImagingSubject", back_populates="series")
    diseases: Mapped[List["Disease"]] = relationship("Disease", back_populates="series")

class Disease(Base):
    __tablename__ = 'diseases'
    
    disease_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # UNIQUE
    series_id: Mapped[int] = mapped_column(Integer, ForeignKey('imaging_series.series_id'), nullable=False)
    bounding_box: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"x1": 45, "y1": 67, "x2": 120, "y2": 145, "z1": 78, "z2": 102}
    disease: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4,3), nullable=True)  # 0.000 to 1.000
    class_name: Mapped[Optional[DiseaseClassType]] = mapped_column(Enum(DiseaseClassType), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    series: Mapped["ImagingSeries"] = relationship("ImagingSeries", back_populates="diseases")
