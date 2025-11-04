# WebSocket Authentication Improvements

## Tóm tắt

Đã refactor code WebSocket để sử dụng **FastAPI Dependency Injection** thay vì xác thực thủ công, giúp code gọn gàng, nhất quán và dễ bảo trì hơn.

---

## Backend Changes

### 1. **api_vehicles_frames.py**

#### Trước:

```python
async def websocket_frames(websocket: WebSocket, road_name: str):
    await websocket.accept()

    async with AsyncSessionLocal() as db:
        user = await authenticate_websocket(websocket, db)
        if not user:
            return

    try:
        while True:
            # ... send frames
```

#### Sau:

```python
async def websocket_frames(
    websocket: WebSocket,
    road_name: str,
    current_user = Depends(get_current_user)  # ✅ Dependency Injection
):
    await websocket.accept()

    try:
        while True:
            # ... send frames
```

**Thay đổi:**

- ✅ Thêm `current_user = Depends(get_current_user)`
- ❌ Xóa code xác thực thủ công với `AsyncSessionLocal` và `authenticate_websocket`
- ✅ Import sạch hơn (bỏ `authenticate_websocket`, `AsyncSessionLocal`)

**Endpoints đã cập nhật:**

- `/ws/frames/{road_name}` - Stream video frames
- `/ws/info/{road_name}` - Stream thông tin phương tiện

---

### 2. **api_chatbot.py**

#### Trước:

```python
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    async with AsyncSessionLocal() as db:
        user = await authenticate_websocket(websocket, db)
        if not user:
            return

    try:
        while True:
            # ... handle chat
```

#### Sau:

```python
async def websocket_chat(
    websocket: WebSocket,
    current_user = Depends(get_current_user)  # ✅ Dependency Injection
):
    await websocket.accept()

    try:
        while True:
            # ... handle chat
```

**Endpoints đã cập nhật:**

- `/ws/chat` - Chat với AI Agent

---

## Frontend Changes

### 1. **useWebSocket.ts**

#### Cải tiến:

- ✅ Thêm `authToken` option vào `WebSocketHookOptions`
- ✅ Tự động thêm token vào URL khi kết nối: `?token=...`
- ✅ Hỗ trợ fallback nếu không có token
- ✅ Type safety: thay `any` bằng `unknown`

#### Trước:

```typescript
export const useWebSocket = (
  url: string | null,
  options: WebSocketHookOptions = {}
): WebSocketHook => {
  // ...
  wsRef.current = new WebSocket(url);
```

#### Sau:

```typescript
interface WebSocketHookOptions {
  authToken?: string | null; // ✅ New option
  // ... other options
}

export const useWebSocket = (
  url: string | null,
  options: WebSocketHookOptions = {}
): WebSocketHook => {
  const { authToken, ... } = options;

  // Build WebSocket URL with authentication
  let wsUrl = url;
  if (authToken) {
    const separator = url.includes("?") ? "&" : "?";
    wsUrl = `${url}${separator}token=${encodeURIComponent(authToken)}`;
  }

  wsRef.current = new WebSocket(wsUrl);
```

#### Custom Hooks đã cập nhật:

```typescript
// ✅ useTrafficInfo - tự động lấy token
export const useTrafficInfo = (roadName: string | null) => {
  const token = localStorage.getItem("access_token");
  return useWebSocket(wsUrl, {
    authToken: token, // ✅ Pass token
  });
};

// ✅ useFrameStream - tự động lấy token
export const useFrameStream = (roadName: string | null) => {
  const token = localStorage.getItem("access_token");
  return useWebSocket(wsUrl, {
    authToken: token, // ✅ Pass token
  });
};
```

---

### 2. **ChatInterface.tsx**

#### Trước:

```typescript
const token = localStorage.getItem(authConfig.TOKEN_KEY);
const chatWsUrl = token
  ? `${endpoints.chatWs}?token=${encodeURIComponent(token)}`
  : null;

const { ... } = useWebSocket(chatWsUrl, {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
});
```

#### Sau:

```typescript
const token = localStorage.getItem(authConfig.TOKEN_KEY);
const chatWsUrl = endpoints.chatWs; // ✅ Không thêm token vào URL nữa

const { ... } = useWebSocket(chatWsUrl, {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  authToken: token, // ✅ Pass token qua option
});
```

---

## Lợi ích

### Backend:

1. ✅ **Code gọn gàng hơn** - Không còn code xác thực lặp lại
2. ✅ **Nhất quán** - WebSocket xử lý giống HTTP endpoints
3. ✅ **Dễ bảo trì** - Logic xác thực tập trung ở `jwt_handler.py`
4. ✅ **Best practice** - Sử dụng đúng Dependency Injection của FastAPI (>= 0.103)

### Frontend:

1. ✅ **Tái sử dụng tốt hơn** - Token được quản lý tập trung
2. ✅ **Type safety** - Bỏ `any`, dùng `unknown`
3. ✅ **Flexible** - Dễ dàng thay đổi phương thức authentication
4. ✅ **Clean code** - Không cần concat token vào URL ở nhiều nơi

---

## Authentication Flow

### Backend hỗ trợ 3 phương thức:

1. **Query params** (Frontend đang dùng):

   ```
   ws://localhost:8000/api/v1/ws/chat?token=eyJ...
   ```

2. **Cookie**:

   ```
   Cookie: access_token=eyJ...
   ```

3. **Authorization header** (WebSocket không hỗ trợ trực tiếp, nhưng có thể qua subprotocol)

Frontend hiện tại sử dụng **Query params** vì:

- ✅ Đơn giản nhất cho WebSocket
- ✅ Hoạt động trên mọi browser
- ✅ Không cần config thêm

---

## Testing

### Test WebSocket với token:

```bash
# Test với query params (recommended)
wscat -c "ws://localhost:8000/api/v1/ws/chat?token=YOUR_TOKEN_HERE"

# Test traffic info
wscat -c "ws://localhost:8000/api/v1/ws/info/road1?token=YOUR_TOKEN_HERE"

# Test frames (binary data)
wscat -c "ws://localhost:8000/api/v1/ws/frames/road1?token=YOUR_TOKEN_HERE"
```

### Test từ frontend:

1. Login vào hệ thống
2. Token tự động được lưu vào `localStorage`
3. WebSocket tự động kết nối với token
4. Kiểm tra console log để xem connection status

---

## Notes

- ⚠️ Code cũ trong `jwt_handler.py` (`authenticate_websocket`, `extract_token`, etc.) **KHÔNG bị xóa** - vẫn giữ lại cho tương lai nếu cần
- ✅ Tất cả WebSocket endpoints đều yêu cầu authentication
- ✅ Nếu token không hợp lệ hoặc hết hạn, WebSocket sẽ tự động đóng với error message
- ✅ Frontend có auto-reconnect với exponential backoff

---

## Migration Guide

Nếu bạn có custom WebSocket endpoints khác:

### Backend:

```python
# OLD ❌
@router.websocket("/ws/custom")
async def my_websocket(websocket: WebSocket):
    await websocket.accept()
    async with AsyncSessionLocal() as db:
        user = await authenticate_websocket(websocket, db)
        if not user:
            return
    # ... logic

# NEW ✅
@router.websocket("/ws/custom")
async def my_websocket(
    websocket: WebSocket,
    current_user = Depends(get_current_user)
):
    await websocket.accept()
    # ... logic (có thể dùng current_user.id, current_user.email, etc.)
```

### Frontend:

```typescript
// OLD ❌
const token = localStorage.getItem("access_token");
const wsUrl = token ? `${baseUrl}?token=${token}` : null;
const { ... } = useWebSocket(wsUrl);

// NEW ✅
const token = localStorage.getItem("access_token");
const wsUrl = baseUrl;
const { ... } = useWebSocket(wsUrl, {
  authToken: token
});
```

---

**Date**: November 4, 2025  
**Author**: GitHub Copilot  
**Version**: 1.0
