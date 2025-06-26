from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.registerform import RegisterForm
from app.dto.loginform import LoginForm, Token
from app.dto.findidform import FindIdForm
from app.dto.changepwform import ChangePwForm
from app.core.auth import (
    register_user, 
    authenticate_user,
    _create_access_token,
    find_user_id,
    change_password
)
from app.core.db import get_db, User

router = APIRouter()

@router.post("/register")
async def register(user_info: RegisterForm, db: AsyncSession = Depends(get_db)):
    new_user_id = await register_user(user_info, db)
    return {"_id": new_user_id, "message": "registered"}
    
@router.post("/login", response_model=Token)
async def login(credentials: LoginForm, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(credentials, db)
    access_token = _create_access_token({"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "Bearer"}

@router.post("/find_id")
async def find_id(user_info: FindIdForm, db: AsyncSession = Depends(get_db)):
    user_id = await find_user_id(user_info, db)
    return user_id

@router.post("/change_pw")
async def change_pw(user_info: ChangePwForm, db: AsyncSession = Depends(get_db)):
    success = await change_password(user_info, db)
    return success

@router.get("/user_info") # get user info of the specific user
async def get_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user