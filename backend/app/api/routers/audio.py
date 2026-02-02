from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from app.dependencies import audio_service, audio_pipeline, audio_results_store, create_audio_session
from app.domain.schemas import (
    StartRecordResponse,
    StopRecordResponse,
    LiveMetricsResponse,
    StatusResponse,
    LatestResultResponse,
    AudioProcessingResult
)
import time
import os

router = APIRouter()


@router.post("/start-record", response_model=StartRecordResponse)
def start_record(
    session_id: str = Query(..., min_length=1, description="Unique session identifier"),
    force: bool = Query(False, description="Force stop existing recording if any")
):
    """
    Start audio recording for a session.
    
    Args:
        session_id: Unique identifier for this recording session
        force: If True, stops any existing recording before starting
        
    Returns:
        StartRecordResponse with status and session_id
        
    Raises:
        HTTPException 400: If already recording (and force=False) or invalid session_id
    """
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id must be a non-empty string")

    if audio_service.is_recording:
        if force:
            # Auto-stop previous recording
            print(f"[INFO] Force-stopping previous recording: {audio_service.session_id}")
            audio_service.stop_recording()
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Recording already in progress for session: {audio_service.session_id}"
            )

    # Start recording
    audio_service.start_recording(session_id)

    # Initialize session in store
    create_audio_session(session_id)

    return StartRecordResponse(
        status="recording_started",
        session_id=session_id
    )


@router.post("/stop-record", response_model=StopRecordResponse)
def stop_record(
    session_id: str = Query(..., min_length=1, description="Session ID to stop"),
    background_tasks: BackgroundTasks = None
):
    """
    Stop audio recording and queue processing.
    
    Args:
        session_id: Session ID that should match the current recording
        background_tasks: FastAPI background tasks
        
    Returns:
        StopRecordResponse with status, session_id, and file path
        
    Raises:
        HTTPException 400: If not recording or session mismatch
        HTTPException 404: If session not found in store
    """
    if not audio_service.is_recording:
        raise HTTPException(status_code=400, detail="No active recording")

    if session_id != audio_service.session_id:
        raise HTTPException(
            status_code=400,
            detail=f"Session mismatch. Expected: {audio_service.session_id}, Got: {session_id}"
        )

    # Stop recording and get file path
    try:
        filepath = audio_service.stop_recording()
    except Exception as e:
        # Update store with error
        if session_id in audio_results_store:
            audio_results_store[session_id]["status"] = "error"
            audio_results_store[session_id]["error"] = f"Recording failed: {str(e)}"
        raise HTTPException(status_code=500, detail=f"Failed to stop recording: {str(e)}")

    # Get session from store
    session = audio_results_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Update store
    session["status"] = "processing"
    session["file"] = filepath

    # Queue background processing
    if background_tasks:
        background_tasks.add_task(process_audio, session_id, filepath)

    return StopRecordResponse(
        status="recording_stopped",
        session_id=session_id,
        file=filepath
    )


def process_audio(session_id: str, filepath: str):
    """
    Background task to process audio file.
    Updates audio_results_store with results or errors.
    
    Args:
        session_id: Session identifier
        filepath: Path to audio file
    """
    try:
        # Validate file exists
        if not filepath or not os.path.exists(filepath):
            raise RuntimeError(f"Audio file not found: {filepath}")

        print(f"[Audio] Start processing session={session_id}, file={filepath}")
        
        # Run audio pipeline
        result = audio_pipeline.run(filepath)

        # Update store with success
        audio_results_store[session_id]["result"] = result
        audio_results_store[session_id]["status"] = "done"
        
        print(f"[Audio] Processing complete session={session_id}")

    except Exception as e:
        # Update store with error
        audio_results_store[session_id]["status"] = "error"
        audio_results_store[session_id]["error"] = str(e)
        print(f"[Audio] Processing ERROR session={session_id}: {e}")


@router.get("/status", response_model=StatusResponse)
def get_audio_status(session_id: str = Query(..., min_length=1, description="Session ID")):
    """
    Get current status of an audio session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        StatusResponse with current status
    """
    session = audio_results_store.get(session_id)
    if not session:
        # Return idle if session doesn't exist
        return StatusResponse(status="idle")

    return StatusResponse(status=session["status"])


@router.get("/live-metrics", response_model=LiveMetricsResponse)
def get_live_metrics(session_id: str = Query(..., min_length=1, description="Session ID")):
    """
    Get real-time recording metrics.
    Returns zeros if not currently recording or session mismatch.
    
    Args:
        session_id: Session identifier
        
    Returns:
        LiveMetricsResponse with amplitude, is_speech, and duration
    """
    # Check if recording and session matches
    if (
        not audio_service.is_recording
        or not audio_service.start_time
        or session_id != audio_service.session_id
    ):
        return LiveMetricsResponse(
            amplitude=0.0,
            is_speech=False,
            duration=0.0
        )

    # Get current metrics with safe attribute access
    amplitude = float(getattr(audio_service, "current_amplitude", 0.0))
    
    # Calculate is_speech based on amplitude threshold
    is_speech = amplitude > 0.05
    
    # Calculate duration
    duration = max(0.0, time.time() - audio_service.start_time)

    return LiveMetricsResponse(
        amplitude=amplitude,
        is_speech=is_speech,
        duration=duration
    )


@router.get("/latest-result", response_model=LatestResultResponse)
def get_latest_audio_result(session_id: str = Query(..., min_length=1, description="Session ID")):
    """
    Get processing result for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        LatestResultResponse with status, result, and error (if any)
        
    Raises:
        HTTPException 404: If session not found
    """
    session = audio_results_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    status = session["status"]
    
    # If not done, return status without result
    if status != "done":
        return LatestResultResponse(
            status=status,
            result=None,
            error=session.get("error")
        )

    # Convert result dict to AudioProcessingResult
    result_data = session.get("result")
    if result_data:
        result = AudioProcessingResult(**result_data)
    else:
        result = None

    return LatestResultResponse(
        status=status,
        result=result,
        error=session.get("error")
    )
