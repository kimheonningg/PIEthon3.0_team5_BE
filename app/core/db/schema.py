from sqlalchemy.dialects.postgresql import ARRAY 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text, Boolean, Integer, ForeignKey, Table, Column
from datetime import datetime
from typing import Optional, List

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
    gender: Mapped[bool] = mapped_column(String(20), nullable=False) # only allow female / male

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
