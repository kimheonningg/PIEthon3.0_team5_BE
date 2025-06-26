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

class Patient(Base):
    __tablename__ = 'patients'
    
    patient_mrn: Mapped[str] = mapped_column(String(50), primary_key=True)
    phone_num: Mapped[str] = mapped_column(String(11), nullable=False)
    first_name: Mapped[str] = mapped_column(String(40), nullable=False)
    last_name: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    body_part: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ai_ready: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    doctors: Mapped[List["User"]] = relationship(
        "User", 
        secondary=doctor_patient_association, 
        back_populates="patients"
    )
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="patient")

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