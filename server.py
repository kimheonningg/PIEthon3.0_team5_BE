from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from core.models.registerform import RegisterForm
from core.auth import register_user
from core.db import ensure_indexes, init_db
import uvicorn

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

if __name__ == "__main__":
    uvicorn.run("server:app", host="localhost", port=8000, reload=True)
