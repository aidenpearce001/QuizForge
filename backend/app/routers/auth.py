from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse
from app.services.auth import (
    get_user_by_username, create_student, verify_password, create_token, get_current_user
)
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_username(db, body.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    user = await create_student(db, body.full_name, body.username, body.password)
    token = create_token(str(user.id), user.role)
    response.set_cookie("token", token, httponly=True, samesite="lax", max_age=86400)
    return AuthResponse(token=token, user=UserResponse.from_user(user))

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(db, body.username)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(str(user.id), user.role)
    response.set_cookie("token", token, httponly=True, samesite="lax", max_age=86400)
    return AuthResponse(token=token, user=UserResponse.from_user(user))

@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse.from_user(user)

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("token")
    return {"ok": True}
