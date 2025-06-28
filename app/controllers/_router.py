from fastapi import FastAPI, APIRouter
from .auth import router as auth_router
from .patients import router as patients_router
from .notes import router as notes_router
from .appointments import router as appointments_router
from .examinations import router as examinations_router

def init_routers(app_: FastAPI) -> None:
    router = APIRouter()
    
    router.include_router(auth_router, prefix="/auth", tags=["auth"])
    router.include_router(patients_router, prefix="/patients", tags=["patients"])
    router.include_router(notes_router, prefix="/notes", tags=["notes"])
    router.include_router(appointments_router, prefix='/appointments', tags=["appointments"])
    router.include_router(examinations_router, prefix="/examinations", tags=['examinations'])
    
    app_.include_router(router)
    
    @app_.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok"}
    
    @app_.get("/server_on", tags=["health"])
    async def server_on():
        return {"server_on": True}