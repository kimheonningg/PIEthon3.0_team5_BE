from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.db import ensure_indexes, init_db
from app.controllers._router import init_routers

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

# Initialize all routers
init_routers(app_=app)

if __name__ == "__main__":
    uvicorn.run("server:app", host="localhost", port=8000, reload=True)