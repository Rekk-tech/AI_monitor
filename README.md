# 🎯 AI Monitor - Customer Satisfaction Analysis

Real-time emotion detection and customer satisfaction monitoring system using AI.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js 16)                       │
│  • Dashboard UI        • Real-time Stats      • WebSocket        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐ │
│  │ Video Pipeline  │  │ Audio Pipeline  │  │  Agent Service   │ │
│  │ (Real-time)     │  │ (Offline)       │  │  (Analysis)      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Backend (Python)

| Component      | Technology            | Purpose                   |
| -------------- | --------------------- | ------------------------- |
| API            | **FastAPI**           | REST API + WebSocket      |
| Face Detection | **YOLO v11**          | Real-time face detection  |
| Emotion Model  | **ONNX Runtime**      | Emotion classification    |
| Audio          | **PyAudio + Whisper** | Recording + Transcription |
| ML Framework   | **PyTorch**           | Model inference           |

### Frontend (TypeScript)

| Component | Technology       | Purpose                 |
| --------- | ---------------- | ----------------------- |
| Framework | **Next.js 16**   | React SSR/SSG           |
| State     | **Zustand**      | Global state management |
| Styling   | **Tailwind CSS** | UI styling              |
| Real-time | **WebSocket**    | Live updates            |

### AI Models

| Model                      | Format | Purpose         |
| -------------------------- | ------ | --------------- |
| `model.pt`                 | YOLO   | Face detection  |
| `emotion_classifier2.onnx` | ONNX   | 7-class emotion |

## 📂 Project Structure

```
AI Monitor/
├── backend/
│   ├── app/
│   │   ├── api/routers/     # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── pipelines/       # Video/Audio processing
│   │   └── domain/          # Enums, schemas
│   ├── models/inference/    # AI models (.pt, .onnx)
│   └── data/                # Audio/Video data (gitignored)
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API clients
│   │   └── store/           # Zustand stores
│   └── public/              # Static assets
│
└── docs/                    # Documentation
```

## 🚀 Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📊 Features

- ✅ Real-time face detection and emotion recognition
- ✅ Audio recording with speech detection
- ✅ Session-based analysis
- ✅ WebSocket live updates
- ✅ Customer satisfaction scoring
- ✅ AI-powered recommendations

## ⚙️ Environment Variables

### Backend (.env)

```
OPENAI_API_KEY=sk-xxx  # For AI reasoning (optional)
```

### Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 📝 License

MIT License

# Link Drive Model Training
https://drive.google.com/drive/folders/1tbwT93VHcCXoH5MZdGvGY27A8EB2Xgrc?usp=sharing
