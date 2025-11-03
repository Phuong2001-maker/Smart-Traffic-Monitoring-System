from api.v1 import state
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from schemas.ChatRequest import ChatRequest 
from schemas.ChatResponse import ChatResponse
from services.chat_services.ChatBotAgent import ChatBotAgent
from utils.jwt_handler import get_current_user, get_user_by_token, extract_token_from_websocket
from fastapi import Depends, status
from db.base import AsyncSessionLocal


router = APIRouter()

@router.on_event("startup")
def start_up():
    print("Đã khởi tạo Agent")
    if not hasattr(state, 'agent') or state.agent is None:
        print("Đang khởi tạo Agent...")
        try:
            state.agent = ChatBotAgent()
            print("Khởi tạo Agent thành công")
        except Exception as e:
            print(f"Không thể khởi tạo Agent: {e}")
            state.agent = None


@router.post(
    path='/chat',
    response_model=ChatResponse,
    summary="Chat với AI Assistant",
    description="API gửi tin nhắn tới AI Chatbot và nhận phản hồi. AI có thể trả lời về giao thông, cung cấp hình ảnh và thông tin liên quan. Yêu cầu JWT authentication."
)
async def chat(request: ChatRequest, current_user=Depends(get_current_user)):
    data = await state.agent.get_response(request.message, id= current_user.id)
    return ChatResponse(
        message=data["message"],
        image=data["image"]
    )
    
@router.post(
    path='/chat_no_auth',
    response_model=ChatResponse,
    summary="Chat với AI (không xác thực)",
    description="API gửi tin nhắn tới AI Chatbot KHÔNG yêu cầu authentication. Dùng cho demo hoặc public access. Mặc định sử dụng user_id = 1."
)
async def chat_no_auth(request: ChatRequest):
    data = await state.agent.get_response(request.message, id= 1)
    return ChatResponse(
        message=data["message"],
        image=data["image"]
    )
    
    

@router.websocket(
    "/ws/chat",
    name="WebSocket Chat"
)
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint cho AI ChatBot Agent.
    
    Flow:
    - Client gửi JSON: {"message": "..."}
    - Server trả JSON: {"message": "...", "image": "..."}
    
    Authentication:
        Yêu cầu token qua query params (?token=...), cookie (access_token), hoặc header (Authorization: Bearer ...)
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
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            if not user_message:
                await websocket.send_json({"message": "Bạn chưa nhập tin nhắn.", "image": None})
                continue

            # get_response is async, must be awaited directly
            response = await state.agent.get_response(user_message, id=user.id)
            await websocket.send_json({
                "message": response["message"],
                "image": response["image"]
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "message": f"Lỗi: {str(e)}",
                "image": None
            })
        except:
            pass
        await websocket.close()