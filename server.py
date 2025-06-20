from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Depends
import uvicorn

from core.models.registerform import RegisterForm
from core.models.loginform import LoginForm, Token
from core.models.createnoteform import CreateNoteForm
from core.auth import (
    register_user, 
    authenticate_user,
    _create_access_token,
    get_current_user,
)
from core.db import ensure_indexes, init_db


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

@app.post("/patients/{patient_id}/notes")
async def create_note(
    patient_id: str,
    note_in: CreateNoteForm,
    current_user: dict = Depends(get_current_user),
):
    if current_user["position"] != "doctor":
        raise HTTPException(403, "Only doctors can create medical notes.")

if __name__ == "__main__":
    uvicorn.run("server:app", host="localhost", port=8000, reload=True)
