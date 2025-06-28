from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from config import get_settings
from .schema import (
    Base, User, Patient, Note, Appointment, Examination, Medicalhistory, LabResult, 
    Conversation, Message, Reference, MessageReference, doctor_patient_association
)

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def ensure_indexes():
    pass

# Export models for easy importing
__all__ = [
    'get_db', 
    'init_db', 
    'ensure_indexes', 
    'User', 
    'Patient', 
    'Note', 
    'Assignment', 
    'Examination', 
    'Medicalhistory', 
    'LabResult',
    'doctor_patient_association',
    'Base', 
    'engine', 
    'AsyncSessionLocal'
]