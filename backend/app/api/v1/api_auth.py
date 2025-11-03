from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm  
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from schemas.user import UserCreate, UserUpdate, UserOut
from core.security import hash_password, verify_password
from db.base import get_db
from utils.jwt_handler import create_access_token, get_current_user
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/auth")

@router.post(
    "/register",
    summary="Đăng ký tài khoản mới",
    description="API đăng ký user mới với thông tin username, password, email và phone_number. Username, email và số điện thoại phải là duy nhất trong hệ thống.",
    status_code=201
)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(
        username=user.username,
        password=hash_password(user.password),
        email=user.email,
        phone_number=user.phone_number
    )
    db.add(new_user)
    try:
        await db.commit()
        return {"msg": "Register successful"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Username, email hoặc số điện thoại đã tồn tại!")

@router.post(
    "/login",
    summary="Đăng nhập vào hệ thống",
    description="API đăng nhập OAuth2 compatible. Sử dụng email hoặc username cùng với password để lấy access token. Token này dùng để xác thực các request tiếp theo."
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Có thể login bằng:
    - username field: nhập email hoặc username
    - password field: nhập password
    """
    # Thử tìm user bằng email hoặc username
    q = select(User).where(
        (User.email == form_data.username) | (User.username == form_data.username)
    )
    result = await db.execute(q)
    user_db = result.scalar()
    
    if not user_db or not verify_password(form_data.password, user_db.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai thông tin đăng nhập",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token({"sub": user_db.username})
    return {"access_token": token, "token_type": "bearer"}

@router.get(
    "/me",
    response_model=UserOut,
    summary="Lấy thông tin user hiện tại",
    description="API trả về thông tin chi tiết của user đang đăng nhập. Yêu cầu JWT authentication."
)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Lấy thông tin user hiện tại"""
    return current_user

@router.put(
    "/me",
    response_model=UserOut,
    summary="Cập nhật thông tin user",
    description="API cập nhật thông tin cá nhân của user (username, email, phone_number, password). Username, email và số điện thoại phải là duy nhất. Yêu cầu JWT authentication."
)
async def update_user_info(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cập nhật thông tin user"""
    try:
        # Cập nhật các trường được cung cấp
        if user_update.username is not None:
            current_user.username = user_update.username
        if user_update.email is not None:
            current_user.email = user_update.email
        if user_update.phone_number is not None:
            current_user.phone_number = user_update.phone_number
        if user_update.password is not None:
            current_user.password = hash_password(user_update.password)
        
        await db.commit()
        await db.refresh(current_user)
        return current_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Username, email hoặc số điện thoại đã tồn tại!")
