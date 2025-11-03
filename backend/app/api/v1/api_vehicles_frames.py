from fastapi import APIRouter
from fastapi.responses import JSONResponse
from api import v1
import asyncio
from services.road_services.AnalyzeOnRoadForMultiProcessing import AnalyzeOnRoadForMultiprocessing
from fastapi.responses import Response
from fastapi import WebSocket, WebSocketDisconnect, status
from utils.jwt_handler import get_current_user, get_user_by_token, get_current_user_flexible, extract_token_from_websocket
from db.base import AsyncSessionLocal
from fastapi import Depends

router = APIRouter()

@router.on_event("startup")
def start_up():
    if v1.state.analyzer is None:
        v1.state.analyzer = AnalyzeOnRoadForMultiprocessing()
        v1.state.analyzer.run_multiprocessing()

@router.get(
    path='/roads_name',
    summary="Lấy danh sách tên đường",
    description="API trả về danh sách tên các tuyến đường đang được giám sát trong hệ thống. Yêu cầu xác thực JWT."
)
async def get_road_names(current_user=Depends(get_current_user)):
    return JSONResponse(content={"road_names": v1.state.analyzer.names})

@router.websocket(
    "/ws/frames/{road_name}",
    name="WebSocket trả về frame hình ảnh tuyến đường",
    )
async def websocket_frames(websocket: WebSocket, road_name: str):
    """
    WebSocket endpoint để stream video frames của tuyến đường theo thời gian thực.
    
    Args:
        road_name: Tên tuyến đường cần xem
        
    Authentication:
        Yêu cầu token qua query params (?token=...), cookie (access_token), hoặc header (Authorization: Bearer ...)
    """
    await websocket.accept()
    token = (
        websocket.query_params.get("token")
        or websocket.cookies.get("access_token")
        or websocket.headers.get("authorization")
    )
    if token and token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]
    if not token:
        await websocket.send_json({"detail": "Unauthorized — missing or invalid token"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    async with AsyncSessionLocal() as db:
        user = await get_user_by_token(token, db)
        if not user:
            await websocket.send_json({"detail": "Unauthorized — missing or invalid token"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    try:
        while True:
            frame_bytes = await asyncio.to_thread(v1.state.analyzer.get_frame_road, road_name)
            await websocket.send_bytes(frame_bytes)
            await asyncio.sleep(1/30)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(e)
        await websocket.close()
        
@router.websocket(
    "/ws/info/{road_name}",
    name="WebSocket trả về thông tin phương tiện tuyến đường",
)
async def websocket_info(websocket: WebSocket, road_name: str):
    """
    WebSocket endpoint để nhận thông tin phương tiện của tuyến đường theo thời gian thực.
    
    Args:
        road_name: Tên tuyến đường cần xem thông tin
        
    Authentication:
        Yêu cầu token qua query params (?token=...), cookie (access_token), hoặc header (Authorization: Bearer ...)
    
    Returns:
        JSON data chứa thông tin phương tiện, cập nhật mỗi 5 giây
    """
    await websocket.accept()
    
    # Lấy token từ WebSocket connection
    token = extract_token_from_websocket(websocket)
    
    if not token:
        await websocket.send_json({"detail": "Unauthorized — missing or invalid token"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Xác thực token
    async with AsyncSessionLocal() as db:
        user = await get_user_by_token(token, db)
        if not user:
            await websocket.send_json({"detail": "Unauthorized — missing or invalid token"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    try:
        while True:
            data = await asyncio.to_thread(v1.state.analyzer.get_info_road, road_name)
            await websocket.send_json(data)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"detail": f"Internal error: {str(e)}"})
        await websocket.close()



@router.get(
    path='/info/{road_name}',
    summary="Lấy thông tin phương tiện trên đường",
    description="API trả về thông tin phương tiện của tuyến đường (số lượng xe, tốc độ trung bình, v.v.). Endpoint này KHÔNG yêu cầu xác thực JWT."
)
async def get_info_road(road_name: str):
    """
    API trả về thông tin phương tiện của tuyến đường road_name (KHÔNG xác thực JWT).
    """
    data = await asyncio.to_thread(v1.state.analyzer.get_info_road, road_name)
    if data is None:
        return JSONResponse(content={
            "Lỗi: Dữ liệu bị lỗi, kiểm tra road_services"
            }, status_code=500)
    return JSONResponse(content=data)


@router.get(
    path='/frames/{road_name}',
    summary="Lấy frame hình ảnh của đường (có xác thực)",
    description="API trả về frame hình ảnh (JPEG) hiện tại của tuyến đường. Yêu cầu xác thực JWT qua Authorization header, cookie, hoặc query parameter (?token=...)."
)
async def get_frame_road(road_name: str, current_user=Depends(get_current_user_flexible)):
    """
    Lấy frame hình ảnh hiện tại của tuyến đường (yêu cầu xác thực).
    
    Args:
        road_name: Tên tuyến đường
        current_user: User đã được xác thực (tự động inject bởi FastAPI)
    
    Authentication:
        Token có thể được gửi qua:
        - Authorization header: Bearer <token>
        - Cookie: access_token
        - Query parameter: ?token=<token>
    
    Returns:
        Response: Image JPEG của frame hiện tại
    """
    frame_bytes = await asyncio.to_thread(v1.state.analyzer.get_frame_road, road_name)
    if frame_bytes is None:
        return JSONResponse(
            content={"error": "Lỗi: Dữ liệu bị lỗi, kiểm tra core"},
            status_code=500
        )
    return Response(content=frame_bytes, media_type="image/jpeg")


@router.get(
    path='/frames_no_auth/{road_name}',
    summary="Lấy frame hình ảnh (không xác thực)",
    description="API trả về frame hình ảnh (JPEG) hiện tại của tuyến đường. Endpoint này KHÔNG yêu cầu xác thực JWT - dùng cho mục đích demo hoặc public."
)   

async def get_frame_road_no_auth(road_name: str):
    frame_bytes = await asyncio.to_thread(v1.state.analyzer.get_frame_road, road_name)
    if frame_bytes is None:
        return JSONResponse(
            content={"error": "Lỗi: Dữ liệu bị lỗi, kiểm tra core"},
            status_code=500
        )
    return Response(content=frame_bytes, media_type="image/jpeg")
