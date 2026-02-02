from fastapi import APIRouter, HTTPException
from app.dependencies import video_service, audio_results_store, agent_service
import os
import json
import time

router = APIRouter()

RESULTS_DIR = "data/results"
os.makedirs(RESULTS_DIR, exist_ok=True)

@router.get("/final")
def get_final_result():
    video_stats = video_service.get_stats()
    audio_stats = audio_results_store.get("latest", {})
    
    result = agent_service.decide(video_stats, audio_stats)
    
    # Convert Pydantic model to dict
    result_dict = result.dict() if hasattr(result, "dict") else result
    
    # Save combined result to data/results
    timestamp = int(time.time())
    filename = f"{RESULTS_DIR}/result_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(result_dict, f, indent=2)
    
    print(f"[INFO] Final result saved to {filename}")
        
    return result


@router.post("/analyze")
def analyze_session():
    """
    Trigger analysis of the current session.
    Returns the agent's decision based on video and audio data.
    """
    video_stats = video_service.get_stats()
    audio_stats = audio_results_store.get("latest", {})
    
    if not video_stats and not audio_stats:
        raise HTTPException(status_code=400, detail="No session data available for analysis")
    
    result = agent_service.decide(video_stats, audio_stats)
    
    # Convert Pydantic model to dict
    result_dict = result.dict() if hasattr(result, "dict") else result
    
    # Save result
    timestamp = int(time.time())
    filename = f"{RESULTS_DIR}/result_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(result_dict, f, indent=2)
    
    print(f"[INFO] Analysis result saved to {filename}")
    
    return result

