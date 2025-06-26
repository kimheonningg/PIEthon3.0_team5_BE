from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.models.registerform import RegisterForm
from core.models.loginform import LoginForm, Token
from core.models.noteform import CreateNoteForm, UpdateNoteForm
from core.models.findidform import FindIdForm
from core.models.changepwform import ChangePwForm
from core.models.patient import Patient
from core.auth import (
    register_user, 
    authenticate_user,
    _create_access_token,
    get_current_user,
    find_user_id,
    change_password
)
from core.db import ensure_indexes, init_db, get_db, User
from core.manage_funcs.notesmanage import (
    add_new_note,
    update_existing_note,
    get_all_notes,
    get_specific_note
)
from core.manage_funcs.patientmanage import (
    create_new_patient,
    assign_patient_to_doctor,
    get_all_assigned_patients,
    get_specific_patient
)
from sqlalchemy.ext.asyncio import AsyncSession

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await ensure_indexes()
    yield

app = FastAPI(
    title="PIEthon3.0", 
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/server_on")
async def server_on():
    return {"server_on": True}

@app.post("/register")
async def register(user_info: RegisterForm, db: AsyncSession = Depends(get_db)):
    new_user_id = await register_user(user_info, db)
    return {"_id": new_user_id, "message": "registered"}
    
@app.post("/login", response_model=Token)
async def login(credentials: LoginForm, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(credentials, db)
    access_token = _create_access_token({"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "Bearer"}

@app.post("/find_id")
async def find_id(user_info: FindIdForm, db: AsyncSession = Depends(get_db)):
    userId = await find_user_id(user_info, db)
    return userId

@app.post("/change_pw")
async def change_pw(user_info: ChangePwForm, db: AsyncSession = Depends(get_db)):
    success = await change_password(user_info, db)
    return success

@app.get("/user_info") # get user info of the specific user
async def get_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user

@app.get("/patients") # get all patients assigned to the current doctor
async def get_patients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await get_all_assigned_patients(current_user, db)
    return result

@app.get("/patient/{patient_id}") # get specific patient with patient id
async def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await get_specific_patient(patient_id, current_user, db)
    return result

@app.post("/patients/create")
async def create_patient(patient_info: Patient, db: AsyncSession = Depends(get_db)):
    success = await create_new_patient(patient_info, db)
    return success

@app.post("/patients/assign/{patientId}")
async def assign_patient(
    patientId: str,
    currentUser: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await assign_patient_to_doctor(patientId, currentUser, db)
    return result

@app.post("/patients/notes/create/{patient_id}")
async def create_note(
    patient_id: str,
    note_in: CreateNoteForm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await add_new_note(patient_id, note_in, current_user, db)
    return result
    
@app.post("/patients/notes/update/{note_id}")
async def update_note(
    note_id: str,
    note_in: UpdateNoteForm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await update_existing_note(note_id, note_in, current_user, db)
    return result

@app.get("/patients/notes/all/{patient_id}") # get all notes for that patient with patient_id
async def get_notes(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await get_all_notes(patient_id, current_user, db)
    return result

@app.get("/patients/note/{note_id}") # get specific note with note_id
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await get_specific_note(note_id, current_user, db)
    return result

if __name__ == "__main__":
    uvicorn.run("server:app", host="localhost", port=8000, reload=True)
