/**
 * Session Store - Global Realtime State
 * Single source of truth for WebSocket-driven UI updates.
 * 
 * DESIGN PRINCIPLES:
 * 1. Flat state structure for minimal re-renders
 * 2. Separate selectors for granular subscriptions
 * 3. WS events → store updates → UI reads
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

// =========================
// REALTIME STATE TYPES
// =========================

export interface AudioState {
    amplitude: number;
    isSpeech: boolean;
    duration: number;
    status: 'idle' | 'recording' | 'processing' | 'done' | 'error';
    totalFrames: number;
    speechFrames: number;
    error: string | null;
}

export interface VideoState {
    faceCount: number;
    dominantEmotion: string;
    confidence: number;
    totalFrames: number;
    duration: number;
    emotionCounts: Record<string, number>;
    isRecording: boolean;
}

export interface AgentState {
    finalState: 'SATISFIED' | 'NEUTRAL' | 'DISSATISFIED' | null;
    confidence: Record<string, number>;
    reasoning: string[];
    recommendation: string;
}

export interface SessionMeta {
    id: string;
    startTime: Date | null;
    status: 'idle' | 'recording' | 'processing' | 'complete' | 'error';
    videoActive?: boolean;
    audioActive?: boolean;
}

export interface ConnectionState {
    isConnected: boolean;
    isConnecting: boolean;
    reconnectCount: number;
    lastError: string | null;
}

// =========================
// STORE INTERFACE
// =========================

interface SessionStore {
    // User role
    role: 'supervisor' | 'qa_manager';
    setRole: (role: 'supervisor' | 'qa_manager') => void;

    // Session metadata
    session: SessionMeta;
    setSession: (session: Partial<SessionMeta>) => void;
    resetSession: () => void;

    // Realtime Audio State
    audio: AudioState;
    setAudioState: (state: Partial<AudioState>) => void;
    resetAudio: () => void;

    // Realtime Video State  
    video: VideoState;
    setVideoState: (state: Partial<VideoState>) => void;
    resetVideo: () => void;

    // Agent Decision State
    agent: AgentState;
    setAgentState: (state: Partial<AgentState>) => void;
    resetAgent: () => void;

    // Connection State
    connection: ConnectionState;
    setConnectionState: (state: Partial<ConnectionState>) => void;

    // UI State
    isLoading: boolean;
    setLoading: (loading: boolean) => void;
    error: string | null;
    setError: (error: string | null) => void;

    // Timeline Events
    events: TimelineEvent[];
    addEvent: (event: TimelineEvent) => void;
    clearEvents: () => void;

    // Legacy compatibility (deprecate later)
    videoStats: VideoStats | null;
    setVideoStats: (stats: VideoStats | null) => void;
    audioMetrics: LiveMetrics | null;
    setAudioMetrics: (metrics: LiveMetrics | null) => void;
    finalResult: FinalResult | null;
    setFinalResult: (result: FinalResult | null) => void;
}

// Legacy types for compatibility
interface VideoStats {
    is_recording: boolean;
    total_frames: number;
    duration_seconds: number;
    counts: Record<string, number>;
    current_emotion: string;
    current_confidence: number;
}

interface LiveMetrics {
    amplitude: number;
    is_speech: boolean;
    duration: number;
}

interface FinalResult {
    final_state: string;
    confidence: Record<string, number>;
    reasoning?: string[];
    recommendation?: string;
}

export interface TimelineEvent {
    id: string;
    type: 'session_start' | 'session_stop' | 'emotion_spike' | 'speech_detected' | 'face_detected' | 'result_ready';
    timestamp: number;
    data?: Record<string, unknown>;
}

// =========================
// INITIAL STATE
// =========================

const initialAudio: AudioState = {
    amplitude: 0,
    isSpeech: false,
    duration: 0,
    status: 'idle',
    totalFrames: 0,
    speechFrames: 0,
    error: null,
};

const initialVideo: VideoState = {
    faceCount: 0,
    dominantEmotion: 'neutral',
    confidence: 0,
    totalFrames: 0,
    duration: 0,
    emotionCounts: {},
    isRecording: false,
};

const initialAgent: AgentState = {
    finalState: null,
    confidence: {},
    reasoning: [],
    recommendation: '',
};

const initialSession: SessionMeta = {
    id: '',
    startTime: null,
    status: 'idle',
    videoActive: false,
    audioActive: false,
};

const initialConnection: ConnectionState = {
    isConnected: false,
    isConnecting: false,
    reconnectCount: 0,
    lastError: null,
};

// =========================
// STORE IMPLEMENTATION
// =========================

export const useSessionStore = create<SessionStore>()(
    subscribeWithSelector((set, get) => ({
        // User role
        role: 'supervisor',
        setRole: (role) => set({ role }),

        // Session
        session: initialSession,
        setSession: (session) => set((state) => ({
            session: { ...state.session, ...session },
        })),
        resetSession: () => set({
            session: initialSession,
            audio: initialAudio,
            video: initialVideo,
            agent: initialAgent,
            events: [],
            error: null,
            videoStats: null,
            audioMetrics: null,
            finalResult: null,
        }),

        // Audio
        audio: initialAudio,
        setAudioState: (state) => set((prev) => ({
            audio: { ...prev.audio, ...state },
        })),
        resetAudio: () => set({ audio: initialAudio }),

        // Video
        video: initialVideo,
        setVideoState: (state) => set((prev) => ({
            video: { ...prev.video, ...state },
        })),
        resetVideo: () => set({ video: initialVideo }),

        // Agent
        agent: initialAgent,
        setAgentState: (state) => set((prev) => ({
            agent: { ...prev.agent, ...state },
        })),
        resetAgent: () => set({ agent: initialAgent }),

        // Connection
        connection: initialConnection,
        setConnectionState: (state) => set((prev) => ({
            connection: { ...prev.connection, ...state },
        })),

        // UI
        isLoading: false,
        setLoading: (loading) => set({ isLoading: loading }),
        error: null,
        setError: (error) => set({ error }),

        // Timeline
        events: [],
        addEvent: (event) => set((state) => ({
            events: [...state.events.slice(-49), event], // Keep last 50
        })),
        clearEvents: () => set({ events: [] }),

        // Legacy compatibility
        videoStats: null,
        setVideoStats: (stats) => {
            set({ videoStats: stats });
            // Also update new video state
            if (stats) {
                set((prev) => ({
                    video: {
                        ...prev.video,
                        faceCount: 0,
                        dominantEmotion: stats.current_emotion,
                        confidence: stats.current_confidence,
                        totalFrames: stats.total_frames,
                        duration: stats.duration_seconds,
                        emotionCounts: stats.counts,
                        isRecording: stats.is_recording,
                    },
                }));
            }
        },
        audioMetrics: null,
        setAudioMetrics: (metrics) => {
            set({ audioMetrics: metrics });
            // Also update new audio state
            if (metrics) {
                set((prev) => ({
                    audio: {
                        ...prev.audio,
                        amplitude: metrics.amplitude,
                        isSpeech: metrics.is_speech,
                        duration: metrics.duration,
                        status: 'recording',
                    },
                }));
            }
        },
        finalResult: null,
        setFinalResult: (result) => {
            set({ finalResult: result });
            // Also update new agent state
            if (result) {
                set((prev) => ({
                    agent: {
                        ...prev.agent,
                        finalState: result.final_state as AgentState['finalState'],
                        confidence: result.confidence || {},
                        reasoning: result.reasoning || [],
                        recommendation: result.recommendation || '',
                    },
                }));
            }
        },
    }))
);

// =========================
// SELECTORS (for granular subscriptions)
// =========================

export const selectAudioAmplitude = (state: SessionStore) => state.audio.amplitude;
export const selectAudioStatus = (state: SessionStore) => state.audio.status;
export const selectVideoEmotion = (state: SessionStore) => state.video.dominantEmotion;
export const selectVideoConfidence = (state: SessionStore) => state.video.confidence;
export const selectFaceCount = (state: SessionStore) => state.video.faceCount;
export const selectAgentResult = (state: SessionStore) => state.agent.finalState;
export const selectIsConnected = (state: SessionStore) => state.connection.isConnected;
export const selectSessionStatus = (state: SessionStore) => state.session.status;

export default useSessionStore;
