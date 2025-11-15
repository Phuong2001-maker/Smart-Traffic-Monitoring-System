# Smart Transportation Monitoring System

An intelligent traffic monitoring system that collects traffic flow and metrics including average speed and vehicle counts (motorcycles, cars) for each road. Features real-time data visualization with interactive dashboards and an integrated ReAct-based AI Agent chatbot for querying processed traffic data in real-time.

## Architecture Overview

### Backend Components

- **Video Processing**
  - YOLO model fine-tuned and optimized with INT8 OpenVINO and TensorRT
  - ByteTrack for object tracking
  - Multi-processing implementation for parallel video analysis
- **API Layer**
  - FastAPI for REST endpoints
  - WebSocket support for real-time data streaming
  - Background workers for continuous video analysis
- **AI Assistant**
  - ReAct Agent based on LangGraph
  - Contextual understanding of traffic data
  - Natural language interaction for traffic queries

### Data Flow

1. **Video Processing Pipeline**

   - Each video input runs in a separate subprocess
   - YOLO detection → ByteTrack tracking → Metrics computation
   - Each subprocess stores results in shared memory (main process)

2. **Data Serving**

   - FastAPI serves processed data via REST/WebSocket
   - React frontend consumes and visualizes data in real-time

3. **AI Assistant**
   - Agent processes natural language queries about traffic data
   - Retrieves real-time and historical traffic information
   - Provides insights through conversational interface

## Features

- Real-time traffic monitoring and analytics using AI-powered vehicle detection and tracking
- Multi-camera support with parallel video processing
- Interactive dashboard with real-time metrics and visualizations
- AI chatbot for traffic insights and analysis
- WebSocket integration for live streaming of frames and metrics
- Optimized AI models (INT8 OpenVINO, TensorRT, ...) for efficient inference
- Support for both CPU and GPU deployments

## Short demo

https://github.com/user-attachments/assets/b4a4dabd-2454-4123-ad9d-bd820a96a100

<details>
<summary> <strong>Project Structure</strong></summary>

```
smart-transportation-system
├─ Backend
│  ├─ .dockerignore
│  ├─ .env
│  ├─ app
│  │  ├─ ai_models
│  │  │  ├─ model N
│  │  │  │   └─ bench marks
│  │  │  └─ model S
│  │  │     └─ bench marks
│  │  ├─ api
│  │  │  └─ v1
│  │  │     ├─ api_vehicles_frames.py
│  │  │     └─ state.py
│  │  ├─ core
│  │  │  ├─ config.py
│  │  │  ├─ security.py
│  │  │  └─ __init__.py
│  │  ├─ db
│  │  │  └─ database.py
│  │  ├─ main.py
│  │  ├─ models
│  │  │  └─ user.py
│  │  ├─ schemas
│  │  │  └─ ChatResponse.py
│  │  ├─ services
│  │  │  ├─ chat_services
│  │  │  │  └─ tool_func.py
│  │  │  └─ road_services
│  │  │     ├─ AnalyzeOnRoad.py
│  │  │     ├─ AnalyzeOnRoadBase.py
│  │  │     └─ AnalyzeOnRoadForMultiProcessing.py
│  │  └─ utils
│  │     ├─ jwt_handler.py
│  │     └─ services_utils.py
│  ├─ docker-compose.yml
│  ├─ Dockerfile
│  ├─ requirements_cpu.txt
│  └─ requirements_gpu.txt
├─ docker-compose.yml
├─ Frontend
│  ├─ .dockerignore
│  ├─ components.json
│  ├─ Dockerfile
│  ├─ eslint.config.js
│  ├─ package.json
│  ├─ public
│  │  └─ vite.svg
│  ├─ src
│  │  ├─ App.css
│  │  ├─ App.tsx
│  │  ├─ assets
│  │  │  └─ react.svg
│  │  ├─ components
│  │  │  ├─ ChatInterface.tsx
│  │  │  ├─ LoadingSpinner.tsx
│  │  │  ├─ TrafficAnalytics.tsx
│  │  │  ├─ TrafficDashboard.tsx
│  │  │  ├─ ui
│  │  │  ├─ VideoModal.tsx
│  │  │  └─ VideoMonitor.tsx
│  │  ├─ config.ts
│  │  ├─ hooks
│  │  │  ├─ use-mobile.ts
│  │  │  └─ useWebSocket.ts
│  │  ├─ index.css
│  │  ├─ lib
│  │  │  └─ utils.ts
│  │  ├─ main.tsx
│  │  └─ vite-env.d.ts
│  ├─ tsconfig.app.json
│  ├─ tsconfig.json
│  ├─ tsconfig.node.json
│  └─ vite.config.ts
└─ README1.md

```

</details>

## Requirements

- Python > 3.11
- Node.js 18+
- NVIDIA GPU (optional, for GPU acceleration)
- Backend dependencies: `app/requirements_cpu.txt` or `app/requirements_gpu.txt`
- Frontend dependencies: `package.json`
- Database: Postgresql > 16

## Manual Setup

### Backend Setup

1. From project root, navigate to the app directory:

```bash
cd Backend/app
```

2. Install Python dependencies:

- For CPU-only installation

```bash
pip install -r requirements_cpu.txt
```

- For GPU support

```
pip install -r requirements_gpu.txt
```

- For Linux systems, for OpenCV dependencies:

```bash
sudo apt update
sudo apt install -y libgl1
```

4. Download videos resource:

```bash
gdown --folder https://drive.google.com/drive/folders/1gkac5U5jEs174p7V7VC3rCmgvO_cVwxH
```

5. Configure environment variables:

Create .env file for ChatBot configuration (Optional)

```bash
echo "GOOGLE_API_KEY=your_google_api_key_here" > .env
```

### Frontend Setup

1. From project root, navigate to the Frontend directory and install Node.js dependencies:

```bash
npm install pnpm
```

```bash
pnpm install
```

## Running the Application

1. From app directory, start the backend server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> Server will be available at http://localhost:8000

2. From Frontend directory, start the frontend development server:

```bash
pnpm run dev
```

> Vite dev server will be available at http://localhost:5173

## Configuration

### Frontend Configuration

Base URLs and API endpoints are configured in `src/config.ts` and can be customized using Vite environment variables.

### Backend Configuration

Configured in `core/config.py` and can be customized environment variables.

<details>
<summary> <strong> Docker Deployment  </strong></summary>

## Quick Start with Docker Compose

1. Download test videos (if not already downloaded):

Navigate to Backend/app directory where `videos_test` will be stored

```bash
cd app
```

Install gdown tool for downloading from Google Drive

```bash
pip install gdown
```

Download test videos

```bash
gdown --folder https://drive.google.com/drive/folders/1gkac5U5jEs174p7V7VC3rCmgvO_cVwxH
```

Return to root directory for docker-compose:

```bash
cd ..
```

thêm một lần nữa để trở lại root

```bash
cd ..
```

2. Run with Docker Compose:

Build and start all services

```bash
docker compose up --build
```

Or run in background

```bash
docker compose up --build -d
```

Build services individually

```bash
docker compose build fastapi
docker compose build frontend
```

Start services without rebuilding

```bash
docker compose up
```

Check logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f fastapi
docker compose logs -f frontend
```

Stop services

```bash
docker compose down
```

Stop and remove volumes

```bash
docker compose down -v
```

This will start:

- Backend API: http://localhost:8000
- Frontend: http://localhost:5173

### Docker Configuration

The `docker-compose.yml` provides:

- FastAPI backend with CPU/GPU support
- React development server
- Volume mounting for video files (`./app/video_test`)
- Custom network for service communication

### GPU Support

To enable GPU acceleration:

1. Prerequisites:

   - NVIDIA Docker runtime installed
   - NVIDIA drivers on host system

2. Enable GPU support:
   ```bash
   docker compose up --build --build-arg DEVICE=gpu
   ```

### Troubleshooting Docker

- **Port conflicts**: Verify ports 8000 and 5173 are available
- **Video files**: Ensure test videos are in `app/video_test/`
- **Build issues**: Try rebuilding without cache:

  ```bash
  docker compose build --no-cache
  ```

- **Debugging**: Check service logs:
  ```bash
  docker compose logs [service_name]
  ```
  </details>

---

## API Documentation

### Available Endpoints Overview

**Authentication:**

- `POST /auth/register` - User registration _(no auth)_
- `POST /auth/login` - User login _(no auth)_
- `GET /auth/me` - Get current user info _(requires JWT)_
- `PUT /user/password` - Update password _(requires JWT)_

**Traffic Monitoring:**

- `GET /roads_name` - List of monitored roads _(no auth)_
- `GET /info/{road_name}` - Traffic metrics (cars, motorcycles, speed, density status) _(requires JWT)_
- `GET /frames/{road_name}` - Current road frame (JPEG) _(requires JWT)_
- `WS /ws/frames/{road_name}` - Stream video frames (~30 FPS) _(requires JWT)_
- `WS /ws/info/{road_name}` - Stream traffic metrics (~50 FPS) _(requires JWT)_

**AI Chat:**

- `POST /chat` - Send message to AI Assistant _(requires JWT)_
- `WS /ws/chat` - Real-time chat WebSocket _(requires JWT)_

**Admin (System Monitoring):**

- `GET /admin/resources` - Get system metrics (CPU, RAM, Disk, Network) _(requires JWT + Admin role)_
- `WS /admin/ws/resources` - Stream system metrics in real-time (2s interval) _(requires JWT + Admin role)_

### Authentication

The API uses **JWT (JSON Web Tokens)** for authentication:

- **REST endpoints**: Add `Authorization: Bearer <JWT_TOKEN>` header
- **WebSocket**: Pass token via query parameter `?token=<JWT_TOKEN>` or cookie
- Endpoints marked _(requires JWT)_ need authentication, others are public

### Quick Start

```bash
# 1. Login to get JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "your_password"}'

# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# 2. Use the token for authenticated requests
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is traffic like?"}'
```

---

## Testing the API

For detailed API testing and exploration, visit the interactive Swagger documentation at:

**`http://localhost:8000/docs`**

The Swagger UI provides:

- Complete list of all endpoints with request/response schemas
- Interactive "Try it out" functionality for each endpoint
- Authentication support (use the "Authorize" button after login)
- Real-time testing of REST and WebSocket connections

## 🔍 Chat System Features

### Current Implementation (localStorage)

- ✅ User-specific chat storage based on JWT token
- ✅ Automatic message reload on account switch
- ✅ Multi-tab support (1s sync interval)
- ✅ Logout clears user data
- ✅ Debug function: `debugChatStorage()` in DevTools console

### Quick Test

```javascript
// In DevTools Console (F12)
debugChatStorage(); // Shows: token, storage keys, message counts
```

<!--
### Database Backend (Optional)

Backend APIs ready but not integrated yet:

- `POST /api/v1/chat/messages` - Save message
- `GET /api/v1/chat/messages` - Get history
- `DELETE /api/v1/chat/messages` - Clear history

See `backend/CHAT_DATABASE_GUIDE.md` for integration steps. -->
