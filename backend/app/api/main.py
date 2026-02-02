import os
import torch

# --- 1. CPU & Thread Optimization ---
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"

if torch.backends.mps.is_available():
    pass # Mac M1/M2
elif torch.cuda.is_available():
    pass # GPU
else:
    # CPU Optimization for Intel i7-1260P
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import video, audio, result, health

app = FastAPI(title="AI Monitor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(video.router, prefix="/video", tags=["Video"])
app.include_router(audio.router, prefix="/audio", tags=["Audio"])
app.include_router(result.router, prefix="/result", tags=["Result"])

@app.get("/")
def read_root():
    return {"message": "AI Monitor System Ready"}
