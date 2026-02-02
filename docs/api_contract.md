# API Contract - AI Monitor Backend

> **⚠️ FROZEN API**: This document represents the final API contract. Backend will not change these endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

> **Note**: Authentication not implemented yet (TASK 5). Currently all endpoints are public.

---

## 📹 VIDEO Endpoints

### POST `/video/start-session`

Start video capture and face emotion analysis.

**Request**
```http
POST /video/start-session
Content-Type: application/json
```

**Response** `200 OK`
```json
{
  "status": "started",
  "session_id": "video_session_1"
}
```

**Error** `400 Bad Request`
```json
{
  "detail": "Video session already active"
}
```

---

### POST `/video/stop-session`

Stop video capture and return aggregated results.

**Request**
```http
POST /video/stop-session
```

**Response** `200 OK`
```json
{
  "status": "stopped",
  "total_frames": 450,
  "duration_seconds": 30.0,
  "counts": {
    "happy": 120,
    "neutral": 280,
    "sad": 30,
    "angry": 20
  },
  "dominant_emotion": "neutral",
  "emotion_ratios": {
    "happy": 0.27,
    "neutral": 0.62,
    "sad": 0.07,
    "angry": 0.04
  }
}
```

---

### GET `/video/stats`

Get current video session statistics (real-time).

**Request**
```http
GET /video/stats
```

**Response** `200 OK`
```json
{
  "is_recording": true,
  "total_frames": 150,
  "duration_seconds": 10.0,
  "counts": {
    "happy": 40,
    "neutral": 100,
    "sad": 10
  },
  "current_emotion": "neutral",
  "current_confidence": 0.85
}
```

---

### GET `/video/frame`

Get latest processed video frame as JPEG.

**Request**
```http
GET /video/frame
```

**Response** `200 OK`
- Content-Type: `image/jpeg`
- Body: Binary JPEG image with face detection overlay

**Error** `404 Not Found` (no frame available)

---

## 🎤 AUDIO Endpoints

### POST `/audio/start-record`

Start audio recording for a session.

**Request**
```http
POST /audio/start-record?session_id=SESS_123
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | Unique session identifier |

**Response** `200 OK`
```json
{
  "status": "recording_started",
  "session_id": "SESS_123"
}
```

**Error** `400 Bad Request`
```json
{
  "detail": "Recording already in progress for session: SESS_XXX"
}
```

---

### POST `/audio/stop-record`

Stop audio recording and queue for processing.

**Request**
```http
POST /audio/stop-record?session_id=SESS_123
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | Session ID (must match current recording) |

**Response** `200 OK`
```json
{
  "status": "recording_stopped",
  "session_id": "SESS_123",
  "file": "data/audio/call_SESS_123.wav"
}
```

**Error** `400 Bad Request`
```json
{
  "detail": "No active recording"
}
```

```json
{
  "detail": "Session mismatch. Expected: SESS_XXX, Got: SESS_YYY"
}
```

---

### GET `/audio/live-metrics`

Get real-time audio metrics during recording.

**Request**
```http
GET /audio/live-metrics?session_id=SESS_123
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | Session identifier |

**Response** `200 OK`
```json
{
  "amplitude": 0.42,
  "is_speech": true,
  "duration": 37.2
}
```

> **Note**: Returns zeros if not recording or session mismatch:
```json
{
  "amplitude": 0.0,
  "is_speech": false,
  "duration": 0.0
}
```

---

### GET `/audio/status`

Get audio processing status for a session.

**Request**
```http
GET /audio/status?session_id=SESS_123
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | Session identifier |

**Response** `200 OK`
```json
{
  "status": "recording"
}
```

**Status Values**:
| Status | Description |
|--------|-------------|
| `idle` | Session not found |
| `recording` | Currently recording |
| `processing` | Recording stopped, processing audio |
| `done` | Processing complete, results ready |
| `error` | Processing failed |

---

### GET `/audio/latest-result`

Get audio emotion analysis results.

**Request**
```http
GET /audio/latest-result?session_id=SESS_123
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | Session identifier |

**Response** `200 OK` (processing complete)
```json
{
  "status": "done",
  "result": {
    "satisfied": 0.72,
    "dissatisfied": 0.15,
    "confidence": 0.89,
    "note": null
  },
  "error": null
}
```

**Response** `200 OK` (still processing)
```json
{
  "status": "processing",
  "result": null,
  "error": null
}
```

**Response** `200 OK` (error)
```json
{
  "status": "error",
  "result": null,
  "error": "Audio file not found"
}
```

**Error** `404 Not Found`
```json
{
  "detail": "Session not found: SESS_XXX"
}
```

---

## 📊 RESULT Endpoints

### POST `/result/analyze`

Analyze combined audio and video results for final satisfaction score.

**Request**
```http
POST /result/analyze
Content-Type: application/json
```

```json
{
  "session_id": "SESS_123"
}
```

**Response** `200 OK`
```json
{
  "session_id": "SESS_123",
  "final_state": "SATISFIED",
  "confidence": {
    "satisfied": 0.75,
    "neutral": 0.15,
    "dissatisfied": 0.10
  },
  "audio_summary": {
    "satisfied": 0.72,
    "dissatisfied": 0.15,
    "confidence": 0.89
  },
  "video_summary": {
    "dominant_emotion": "happy",
    "happy_ratio": 0.45,
    "neutral_ratio": 0.40,
    "negative_ratio": 0.15
  },
  "reasoning": [
    "Audio indicates high satisfaction (0.72)",
    "Video shows happy expressions (45%)",
    "Combined confidence is high"
  ],
  "recommendation": "Customer appears satisfied with the call"
}
```

---

## ❤️ HEALTH Endpoints

### GET `/health`

Health check endpoint.

**Request**
```http
GET /health
```

**Response** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T15:30:00Z"
}
```

---

## 🌐 Realtime Strategy

### Video Frame Polling
- **Endpoint**: `GET /video/frame`
- **Polling Rate**: 10-15 FPS (66-100ms interval)
- **Response**: Binary JPEG
- **Frontend**: Use `setInterval` or `requestAnimationFrame`

### Audio Metrics Polling
- **Endpoint**: `GET /audio/live-metrics`
- **Polling Rate**: 20 Hz (50ms interval)
- **Response**: JSON with amplitude, is_speech, duration
- **Frontend**: Use `setInterval`

### Emotion Stats Polling
- **Endpoint**: `GET /video/stats`
- **Polling Rate**: 2-5 Hz (200-500ms interval)
- **Response**: JSON with counts and current emotion
- **Frontend**: Use React Query with refetchInterval

### Future: WebSocket (TASK 4)
- Will provide push-based updates
- Lower latency
- Reduced server load
- Currently: Polling is sufficient

---

## 📝 Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 404 | Not Found (session/resource) |
| 422 | Unprocessable Entity (invalid params) |
| 500 | Internal Server Error |

---

## 🔄 Session Lifecycle

```
1. POST /video/start-session
   └→ Video recording starts

2. POST /audio/start-record?session_id=SESS_123
   └→ Audio recording starts

3. GET /video/stats  (poll)
   GET /video/frame  (poll)
   GET /audio/live-metrics?session_id=SESS_123  (poll)
   └→ Real-time monitoring

4. POST /audio/stop-record?session_id=SESS_123
   └→ Audio stops, processing starts

5. GET /audio/status?session_id=SESS_123  (poll)
   └→ Wait for status: "done"

6. POST /video/stop-session
   └→ Video stops, stats returned

7. GET /audio/latest-result?session_id=SESS_123
   └→ Get audio analysis

8. POST /result/analyze
   └→ Get final combined result
```

---

## 📌 API Version

**Version**: 1.0.0 (Frozen)
**Last Updated**: 2026-01-26
