from datetime import datetime
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError
from core.models.registerform import RegisterForm
from core.db import admin_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)

async def register_user(payload: RegisterForm) -> str:
    user_doc = payload.model_dump()
    user_doc["password"] = hash_password(user_doc["password"])
    user_doc["createdAt"] = datetime.utcnow()
    user_doc.setdefault("notes", [])

    try:
        result = await admin_db.users.insert_one(user_doc)
        return str(result.inserted_id)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already registered",
        )
