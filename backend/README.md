# Backend - AI Monitor API

FastAPI-based backend for real-time audio and video emotion analysis.

## 📁 Structure

```
backend/
├── app/                    # Application source code
│   ├── main.py            # FastAPI application entry point
│   ├── dependencies.py    # Global dependencies and singletons
│   ├── api/               # API routes
│   ├── domain/            # Domain models and schemas
│   ├── services/          # Business logic services
│   ├── pipelines/         # ML pipelines
│   └── utils/             # Utility functions
│
├── models/                # ML model files
│   └── inference/         # Production models
│
├── data/                  # Runtime data
│   ├── audio/            # Recorded audio files
│   ├── logs/             # Session logs
│   └── results/          # Processing results
│
├── tests/                 # Test files
└── requirements.txt       # Python dependencies
```

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Development Server

```bash
uvicorn app.main:app --reload
```

The API will start on `http://localhost:8000`

### 3. Run Tests

```bash
python tests/test_backend_stability.py
```

## 📡 API Endpoints

### Audio

- `POST /audio/start-record` - Start audio recording
- `POST /audio/stop-record` - Stop recording and process
- `GET /audio/live-metrics` - Get real-time metrics
- `GET /audio/status` - Get session status
- `GET /audio/latest-result` - Get processing results

### Video

- `POST /video/start-session` - Start video capture
- `POST /video/stop-session` - Stop and get results
- `GET /video/stats` - Get current statistics
- `GET /video/frame` - Get latest processed frame

### Results

- `POST /result/analyze` - Analyze session results

### Health

- `GET /health` - Health check

## 🔧 Configuration

Models are loaded from `models/inference/`:
- Speech emotion: `model.safetensors`
- Face detection: `model.pt` (YOLO)
- Face emotion: `face_emotion.onnx`

Data is stored in `data/`:
- Audio files: `data/audio/`
- Session logs: `data/logs/`

## 🧪 Testing

The test suite verifies:
- ✅ API contract compliance
- ✅ Session lifecycle management
- ✅ Error handling
- ✅ Background processing
- ✅ Status transitions

## 📝 Development Notes

- Working directory when running: `backend/`
- All imports use `app.` prefix (e.g., `from app.services import ...`)
- Models and data are outside `app/` for deployment flexibility
