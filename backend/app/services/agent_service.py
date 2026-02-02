from typing import Dict, List
from app.domain.schemas import SessionResult
from app.domain.enums import SatisfactionState, Sentiment
from app.domain.rules import decide_satisfaction

class AgentService:
    def decide(self, face_summary: Dict, audio_summary: Dict) -> SessionResult:
        """
        Combine Face and Audio summaries to produce final business result.
        """
        # Handle "counts" wrapper if coming from new pipeline structure
        face_stats = face_summary.get("counts", face_summary) if "counts" in face_summary else face_summary

        final_state = decide_satisfaction(face_stats, audio_summary)
        
        # Calculate confidence scores
        conf_image = min(0.95, 0.6 + (face_summary.get("total_frames", 0) / 1000))
        conf_audio = audio_summary.get("confidence", 0.75) if "confidence" in audio_summary else 0.75
        
        # Agent confidence based on agreement between modalities
        audio_negative = audio_summary.get("dissatisfied", 0.0)
        face_negative_ratio = sum(face_stats.get(k, 0) for k in ["angry", "sad", "fear", "disgust"])
        
        # If both agree, confidence is high
        if (audio_negative > 0.5 and face_negative_ratio > 30) or \
           (audio_summary.get("satisfied", 0) > 0.6 and face_stats.get("happy", 0) > 40):
            conf_agent = 0.92
        else:
            conf_agent = 0.68
        
        confidence = {
            "image": round(conf_image, 2),
            "audio": round(conf_audio, 2),
            "agent": round(conf_agent, 2)
        }
        
        # Determine dominant sentiment from audio for summary
        if audio_summary:
            dom_audio = "positive" if audio_summary.get("satisfied", 0) > audio_summary.get("dissatisfied", 0) else "negative"
        else:
            dom_audio = "neutral"
        
        # Determine dominant emotion from face
        dom_face = max(face_stats.items(), key=lambda x: x[1])[0] if face_stats else "neutral"
        
        # Calculate negative ratio for face
        neg_keys = ["angry", "disgust", "fear", "sad"]
        negative_ratio = round(sum(face_stats.get(k, 0) for k in neg_keys), 1)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            final_state, 
            face_stats, 
            audio_summary, 
            negative_ratio
        )

        return SessionResult(
            final_state=final_state,
            confidence=confidence,
            image_summary={
                "dominant_emotion": dom_face,
                "negative_ratio": negative_ratio,
                "emotion_breakdown": face_stats
            },
            audio_summary={
                "dominant_sentiment": dom_audio,
                "satisfied": round(audio_summary.get("satisfied", 0), 2),
                "dissatisfied": round(audio_summary.get("dissatisfied", 0), 2),
                "speech_confidence": round(audio_summary.get("confidence", conf_audio), 2)
            },
            reasoning=reasoning,
            recommendation=self._generate_recommendation(final_state, negative_ratio, audio_summary)
        )
    
    def _generate_reasoning(self, state: SatisfactionState, face: Dict, audio: Dict, neg_ratio: float) -> List[str]:
        """Generate explainable reasoning for the decision"""
        reasons = []
        
        # Audio analysis
        audio_neg = audio.get("dissatisfied", 0)
        audio_pos = audio.get("satisfied", 0)
        
        if audio_neg > 0.6:
            reasons.append(f"Audio analysis indicates potential negative tone (~{audio_neg*100:.0f}% confidence)")
        elif audio_pos > 0.6:
            reasons.append(f"Speech patterns suggest positive sentiment (~{audio_pos*100:.0f}% confidence)")
        
        # Face analysis - use softer language
        if neg_ratio > 30:
            reasons.append(f"Facial indicators suggest potential concern (observed in ~{neg_ratio:.0f}% of analyzed frames)")
        
        face_happy = face.get("happy", 0)
        if face_happy > 40:
            reasons.append(f"Positive facial expressions observed (~{face_happy:.0f}% of session)")
        
        face_angry = face.get("angry", 0)
        if face_angry > 15:
            reasons.append(f"Signs of frustration detected in facial patterns (~{face_angry:.0f}%)")
        
        # Overall - softer conclusions
        if state == SatisfactionState.SATISFIED:
            reasons.append("Combined indicators suggest overall positive experience")
        elif state == SatisfactionState.NOT_SATISFIED:
            reasons.append("Multiple indicators suggest customer dissatisfaction")
        else:
            reasons.append("Mixed signals detected - manual review recommended")
        
        return reasons
    
    def _generate_recommendation(self, state: SatisfactionState, neg_ratio: float, audio: Dict) -> str:
        """Generate actionable recommendation"""
        if state == SatisfactionState.NOT_SATISFIED:
            if audio.get("dissatisfied", 0) > 0.7:
                return "Urgent follow-up call recommended within 24 hours"
            else:
                return "Follow-up call recommended"
        elif state == SatisfactionState.NEUTRAL:
            if neg_ratio > 20:
                return "Monitor customer interaction closely"
            else:
                return "Standard follow-up protocol"
        else:
            return "No immediate action required"
