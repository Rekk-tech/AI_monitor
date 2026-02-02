from .enums import SatisfactionState
from typing import Dict

def decide_satisfaction(face_stats: Dict[str, float], audio_result: Dict[str, float]) -> SatisfactionState:
    # "face": { "happy": 42.5, "angry": 12.1 } (percentages)
    # "audio": { "satisfied": 0.68, "dissatisfied": 0.32 } (scores)
    
    audio_dissatisfied = audio_result.get("dissatisfied", 0.0)
    audio_satisfied = audio_result.get("satisfied", 0.0)
    
    face_angry = face_stats.get("angry", 0.0)
    face_sad = face_stats.get("sad", 0.0)
    face_happy = face_stats.get("happy", 0.0)

    if audio_dissatisfied > 0.6:
        return SatisfactionState.NOT_SATISFIED
    elif (face_angry + face_sad) > 30:
        return SatisfactionState.NOT_SATISFIED
    elif audio_satisfied > 0.6 and face_happy > 40:
        return SatisfactionState.SATISFIED
    else:
        return SatisfactionState.NEUTRAL
