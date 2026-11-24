from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.exceptions import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

# init APIRouter 
router = APIRouter(prefix="/auth", tags=["auth"])

# Declare the endpoint by @router.post or @router.get
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, db: DBSession) -> User:
    """Register a new account"""
    
    email = payload.email.lower()
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="EMAIL_ALREADY_EXISTS",
            message="Email is already registered.",
        )
    
    user = User(email=email, hashed_password=hash_password(payload.password), full_name=payload.full_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, db: DBSession) -> TokenResponse:
    """Login and get access_token"""
    
    email = payload.email.lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_CREDENTIALS",
            message="Incorrect email or password.",
        )
        
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> User:
    """Get information of user."""
    return current_user