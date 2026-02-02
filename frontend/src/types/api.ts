// API Types for AI Monitor Frontend

// =========================
// BASE TYPES
// =========================

export type AudioStatus = 'idle' | 'recording' | 'processing' | 'done' | 'error';
export type SatisfactionState = 'SATISFIED' | 'NEUTRAL' | 'DISSATISFIED';
export type UserRole = 'supervisor' | 'qa_manager';

// =========================
// VIDEO TYPES
// =========================

export interface VideoStartResponse {
    status: 'started';
    session_id: string;
}

export interface EmotionCounts {
    happy: number;
    neutral: number;
    sad: number;
    angry: number;
    [key: string]: number;
}

export interface EmotionRatios {
    happy: number;
    neutral: number;
    sad: number;
    angry: number;
    [key: string]: number;
}

export interface VideoStopResponse {
    status: 'stopped';
    total_frames: number;
    duration_seconds: number;
    counts: EmotionCounts;
    dominant_emotion: string;
    emotion_ratios: EmotionRatios;
}

export interface VideoStats {
    is_recording: boolean;
    total_frames: number;
    duration_seconds: number;
    counts: EmotionCounts;
    current_emotion: string;
    current_confidence: number;
}

// =========================
// AUDIO TYPES
// =========================

export interface AudioStartResponse {
    status: 'recording_started';
    session_id: string;
}

export interface AudioStopResponse {
    status: 'recording_stopped';
    session_id: string;
    file: string;
}

export interface LiveMetrics {
    amplitude: number;
    is_speech: boolean;
    duration: number;
}

export interface AudioStatusResponse {
    status: AudioStatus;
}

export interface AudioProcessingResult {
    satisfied: number;
    dissatisfied: number;
    confidence: number;
    note: string | null;
}

export interface AudioLatestResult {
    status: AudioStatus;
    result: AudioProcessingResult | null;
    error: string | null;
}

// =========================
// RESULT TYPES
// =========================

export interface AudioSummary {
    satisfied: number;
    dissatisfied: number;
    confidence: number;
}

export interface VideoSummary {
    dominant_emotion: string;
    happy_ratio: number;
    neutral_ratio: number;
    negative_ratio: number;
}

export interface FinalResult {
    session_id: string;
    final_state: SatisfactionState;
    confidence: {
        satisfied: number;
        neutral: number;
        dissatisfied: number;
    };
    audio_summary: AudioSummary;
    video_summary: VideoSummary;
    reasoning: string[];
    recommendation: string;
}

// =========================
// SESSION TYPES
// =========================

export interface Session {
    id: string;
    videoActive: boolean;
    audioActive: boolean;
    startTime: Date | null;
    status: 'idle' | 'recording' | 'processing' | 'complete';
}

// =========================
// UI TYPES
// =========================

export interface NavItem {
    label: string;
    href: string;
    icon?: string;
    roles?: UserRole[];
}
