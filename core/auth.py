from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Any, Dict, Optional
from jose import jwt, JWTError

from config import get_settings
from core.models.registerform import RegisterForm
from core.models.loginform import LoginForm
from core.models.findidform import FindIdForm
from core.models.changepwform import ChangePwForm
from core.db import User, get_db

settings = get_settings()
SECRET_KEY: str = settings.secret_key
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_TIME = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)

def _create_access_token(
    data: Dict[str, Any],
    expires_delta: int = ACCESS_TOKEN_EXPIRE_TIME,
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def authenticate_user(payload: LoginForm, db: AsyncSession):
    query = select(User)
    if payload.userId and payload.phoneNum:
        query = query.where(or_(User.user_id == payload.userId, User.phone_num == payload.phoneNum))
    elif payload.userId:
        query = query.where(User.user_id == payload.userId)
    elif payload.phoneNum:
        query = query.where(User.phone_num == payload.phoneNum)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either userId or phoneNum must be provided."
        )
    
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User Id or phone number does not exist or invalid password entered."
        )
    
    if not pwd_context.verify(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User Id or phone number does not exist or invalid password entered."
        )
    
    return user

async def register_user(payload: RegisterForm, db: AsyncSession) -> int:
    user = User(
        user_id=payload.userId,
        email=payload.email,
        phone_num=payload.phoneNum,
        first_name=payload.name.firstName,
        last_name=payload.name.lastName,
        password=hash_password(payload.password),
        position=payload.position,
        licence_num=payload.licenceNum
    )

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user.user_id
    except IntegrityError as e:
        await db.rollback()
        error_str = str(e.orig)
        if "user_id" in error_str:
            detail = "This ID already exists."
        elif "email" in error_str:
            detail = "This email is already registered."
        elif "phone_num" in error_str:
            detail = "This phone number is already registered."
        else:
            detail = "User already registered"

        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
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

    query = select(User).where(User.user_id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_error
    return user

async def find_user_id(payload: FindIdForm, db: AsyncSession):
    query = select(User).where(
        User.first_name == payload.name.firstName,
        User.last_name == payload.name.lastName,
        User.phone_num == payload.phoneNum
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found",
        )

    return {"success": True, "userId": user.user_id}

async def change_password(payload: ChangePwForm, db: AsyncSession):
    if not payload.userId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UserId is required.",
        )
    
    query = select(User).where(User.user_id == payload.userId)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not pwd_context.verify(payload.originalPw, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )

    if pwd_context.verify(payload.newPw, user.password):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="New password must be different from the current password.",
        )
    
    user.password = hash_password(payload.newPw)
    await db.commit()

    return {"success": True}