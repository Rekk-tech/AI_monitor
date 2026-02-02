from enum import Enum

class Emotion(str, Enum):
    ANGRY = "angry"
    DISGUST = "disgust"
    FEAR = "fear"
    HAPPY = "happy"
    NEUTRAL = "neutral"
    SAD = "sad"
    SURPRISE = "surprise"

class Sentiment(str, Enum):
    SATISFIED = "satisfied"
    DISSATISFIED = "dissatisfied"
    NEUTRAL = "neutral"

class SatisfactionState(str, Enum):
    SATISFIED = "Satisfied"
    NOT_SATISFIED = "Not Satisfied"
    NEUTRAL = "Neutral"
