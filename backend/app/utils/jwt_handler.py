from datetime import datetime, timedelta
from jose import jwt
from core.config import settings_server
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from models.user import User
from db.base import get_db
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def create_access_token(data: dict):
    """ Tạo JWT access token từ dữ liệu đầu vào.

    Args:
        data (dict): Dữ liệu đầu vào để tạo token.

    Returns:
        str: JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings_server.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings_server.JWT_SECRET, algorithm=settings_server.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict|None:
    """Giải mã token JWT.

    Args:
        token (str): token cần giải mã.

    Returns:
        dict|None: thông tin của token nếu hợp lệ, ngược lại trả về None.
    """
    try:
        payload = jwt.decode(token, settings_server.JWT_SECRET, algorithms=[settings_server.JWT_ALGORITHM])
        return payload
    except Exception:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User|None:

    user = await get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ hoặc user không tồn tại.")
    return user


# Hàm dùng cho websocket hoặc các trường hợp cần truyền token/db trực tiếp
async def get_user_by_token(token: str, db: AsyncSession) -> Optional[User]:
    payload = decode_access_token(token)
    if payload is None:
        return None
    username = payload.get("sub")
    if username is None:
        return None
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar()
    return user


# Dependency cho phép đọc token từ nhiều nguồn: header, cookie, query params
async def get_current_user_flexible(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Lấy user hiện tại từ token, hỗ trợ nhiều nguồn:
    - Authorization header: Bearer <token>
    - Cookie: access_token
    - Query params: token=<token>
    """
    token = None
    
    # 1. Thử lấy từ Authorization header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    
    # 2. Thử lấy từ cookie
    if not token:
        token = request.cookies.get("access_token")
    
    # 3. Thử lấy từ query params
    if not token:
        token = request.query_params.get("token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc không tồn tại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc user không tồn tại."
        )
    return user


# Helper function cho WebSocket authentication (không dùng Depends)
def extract_token_from_websocket(websocket) -> Optional[str]:
    """
    Extract token từ WebSocket connection.
    Hỗ trợ: query params, cookie, hoặc authorization header
    
    Returns:
        str: Token nếu tìm thấy, None nếu không
    """
    token = (
        websocket.query_params.get("token")
        or websocket.cookies.get("access_token")
        or websocket.headers.get("authorization")
    )
    
    # Xử lý Bearer token
    if token and token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]
    
    return token
