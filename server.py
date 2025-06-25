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
# from core.models.doctor import Doctor
from core.auth import (
    register_user, 
    authenticate_user,
    _create_access_token,
    get_current_user,
    find_user_id,
    change_password
)
from core.db import ensure_indexes, init_db
from core.notes import (
    add_new_note,
    update_existing_note
)
from core.patientmanage import create_new_patient
# from core.doctormanage import create_new_doctor

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
async def register(user_info: RegisterForm):
    new_id = await register_user(user_info)
    return {"_id": new_id, "message": "registered"}
    
@app.post("/login", response_model=Token)
async def login(credentials: LoginForm):
    user = await authenticate_user(credentials)
    access_token = _create_access_token({"sub": str(user["_id"])})
    return {"access_token": access_token, "token_type": "Bearer"}

@app.post("/find_id")
async def find_id(user_info: FindIdForm):
    userId = await find_user_id(user_info)
    return userId

@app.post("/change_pw")
async def change_pw(user_info: ChangePwForm):
    success = await change_password(user_info)
    return success

# @app.post("/doctors/create")
# async def create_doctor(doctor_info: Doctor):
#     success = await create_new_doctor(doctor_info)
#     return success

@app.post("/patients/create")
async def create_patient(patient_info: Patient):
    success = await create_new_patient(patient_info)
    return success

@app.post("/patients/notes/create/{patient_id}")
async def create_note(
    patient_id: str,
    note_in: CreateNoteForm,
    current_user: dict = Depends(get_current_user),
):
    result = await add_new_note(patient_id, note_in, current_user)
    return result
    
@app.post("/patients/notes/update/{note_id}")
async def update_note(
    note_id: str,
    note_in: UpdateNoteForm,
    current_user: dict = Depends(get_current_user),
):
    result = await update_existing_note(note_id, note_in, current_user)
    return result

@app.post("/patients/assign/{patientId}")
async def assign_patient(
    patientId: str,
    currentUser: dict = Depends(get_current_user),
):
    result = await assign_patient_to_doctor(patientId, currentUser)
    return result

if __name__ == "__main__":
    uvicorn.run("server:app", host="localhost", port=8000, reload=True)
