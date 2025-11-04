from datetime import datetime, timedelta
from jose import jwt
from core.config import settings_server
from fastapi import Depends, HTTPException, status, Request, WebSocket
from fastapi.security import OAuth2PasswordBearer
from models.user import User
from db.base import get_db
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Union

# OAuth2 scheme for form-based login (standard)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def extract_token(source: Union[Request, WebSocket]) -> Optional[str]:
    """
    Extract token từ Request hoặc WebSocket.
    Hỗ trợ: Authorization header, Cookie, Query params
    
    Args:
        source: Request hoặc WebSocket object
        
    Returns:
        Token string nếu tìm thấy, None nếu không
    """
    if not source:
        return None
    
    token = None
    
    # 1. Thử lấy từ Authorization header
    auth_header = source.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    
    # 2. Thử lấy từ cookie
    if not token:
        token = source.cookies.get("access_token")
    
    # 3. Thử lấy từ query params
    if not token:
        token = source.query_params.get("token")
    
    return token

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

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Lấy user hiện tại từ token, hỗ trợ nhiều nguồn:
    - Authorization header: Bearer <token> (OAuth2 standard)
    - Cookie: access_token
    - Query params: token=<token>
    
    Dùng cho cả HTTP và WebSocket endpoints.
    """
    # HTTP endpoints: chỉ dùng OAuth2 Bearer header. Không fallback sang cookie/query.
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc không tồn tại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
            detail="Token không hợp lệ hoặc user không tồn tại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_user_ws(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency cho WebSocket: lấy token linh hoạt từ header/cookie/query params.
    """
    token = extract_token(websocket)
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
            detail="Token không hợp lệ hoặc user không tồn tại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_user_by_token(token: str, db: AsyncSession) -> Optional[User]:
    """Hàm dùng cho websocket hoặc các trường hợp cần truyền token/db trực tiếp

    Args:
        token (str): token JWT cần xác thực
        db (AsyncSession): phiên làm việc với cơ sở dữ liệu

    Returns:
        Optional[User]: người dùng tương ứng với token nếu hợp lệ, ngược lại trả về None
    """
    payload = decode_access_token(token)
    if payload is None:
        return None
    email = payload.get("sub")
    if email is None:
        return None
    result = await db.execute(select(User).where(User.username == email))
    user = result.scalar()
    return user

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
    token = extract_token(request)
    
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
            detail="user không tồn tại."
        )
    return user


async def authenticate_websocket(websocket: WebSocket, db: AsyncSession) -> Optional[User]:
    """
    Xác thực WebSocket connection và trả về User.
    Tự động xử lý lỗi authentication và đóng connection nếu thất bại.
    
    Args:
        websocket: WebSocket connection
        db: Database session
        
    Returns:
        User nếu xác thực thành công, None nếu thất bại (connection đã được đóng)
        
    Usage:
        async with AsyncSessionLocal() as db:
            user = await authenticate_websocket(websocket, db)
            if not user:
                return  # Connection đã được đóng tự động
    """
    token = extract_token(websocket)
    if not token:
        await websocket.send_json({"detail": "Lỗi xác thực: không tìm thấy token"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    
    user = await get_user_by_token(token, db)
    if not user:
        await websocket.send_json({"detail": "Lỗi xác thực: token không hợp lệ hoặc user không tồn tại"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    
    return user
