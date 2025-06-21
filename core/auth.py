from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pymongo.errors import DuplicateKeyError
from typing import Any, Dict
from jose import jwt, JWTError
from bson import ObjectId

from config import get_settings
from core.models.registerform import RegisterForm
from core.models.loginform import LoginForm
from core.db import admin_db

settings = get_settings()
SECRET_KEY: str = settings.secret_key
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_TIME = 30 # expires in 30 mins

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)

def _create_access_token(
    data: Dict[str, Any],
    expires_delta: int = ACCESS_TOKEN_EXPIRE_TIME,
) -> str:
    # JWT access token
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def authenticate_user(payload: LoginForm):
    or_filters = []
    if payload.userId:
        or_filters.append({"userId": payload.userId})
    if payload.phoneNum:
        or_filters.append({"phoneNum": payload.phoneNum})

    if not or_filters:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either userId or phoneNum must be provided."
        )
    
    user = await admin_db.users.find_one({"$or": or_filters})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User Id or phone number does not exist or invalid password entered."
        )
    
    if not pwd_context.verify(payload.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User Id or phone number does not exist or invalid password entered."
        )
    
    return user

async def register_user(payload: RegisterForm) -> str:
    user_doc = payload.model_dump()
    user_doc["password"] = hash_password(user_doc["password"])
    user_doc["createdAt"] = datetime.utcnow()
    if payload.position == 'patient':
        user_doc.setdefault("medicalNotes", [])
    elif payload.position == 'doctor':
        user_doc.setdefault("patientList", [])

    try:
        result = await admin_db.users.insert_one(user_doc)
        return str(result.inserted_id)
    except DuplicateKeyError as e:
        detail = "Duplicate key: "
        kp = (e.details or {}).get("keyPattern")
        if kp:
            if "userId" in kp:
                detail = "This ID already exists."
            elif "email" in kp:
                detail = "This email is already registered."
            elif "phoneNum" in kp:
                detail = "This phone number is already registered."
            else:
                detail = "User already registered"
        else:
            detail = "User already registered"

        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = await admin_db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_error
    return user