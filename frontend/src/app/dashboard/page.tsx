'use client';

import { useState, useEffect } from 'react';
import {
    WebRTCVideoStream,
    AudioWaveform,
    AudioStatusBadge,
    VideoStatsPanel,
    SessionTimeline,
    SessionSummary,
    ConnectionStatus,
    ErrorToast,
    RoleSwitch,
} from '@/components';
import { useSession } from '@/hooks/useSession';
import { useAudioMetrics } from '@/hooks/useAudioMetrics';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useSessionStore } from '@/store/session.store';

export default function Dashboard() {
    const { role, setConnectionState, setVideoState, setAudioMetrics, addEvent } = useSessionStore();
    const {
        session,
        sessionId,
        isActive,
        isProcessing,
        isComplete,
        startSession,
        endSession,
        analyzeSession,
        resetSession,
        isLoading,
    } = useSession();

    const [videoEnabled, setVideoEnabled] = useState(false);
    const [audioEnabled, setAudioEnabled] = useState(false);

    // DEBUG: Log sessionId changes
    useEffect(() => {
        console.log('[Dashboard] sessionId changed to:', sessionId);
    }, [sessionId]);

    // WebSocket connection - ONLY connect when we have a real sessionId
    // Pass sessionId directly (not through intermediate variable) to ensure fresh value
    const { isConnected, isConnecting, reconnectCount, lastMessage } = useWebSocket({
        sessionId: sessionId || '',
        autoConnect: !!sessionId,  // Only connect when sessionId is set
        onConnect: () => {
            console.log('[Dashboard] WebSocket connected to session:', sessionId);
            setConnectionState({ isConnected: true, isConnecting: false, lastError: null });
            // Add timeline event for session start
            addEvent({
                id: `evt_${Date.now()}`,
                type: 'session_start',
                timestamp: Date.now(),
                data: { sessionId }
            });
        },
        onDisconnect: () => {
            console.log('[Dashboard] WebSocket disconnected');
            setConnectionState({ isConnected: false, isConnecting: false });
        },
        onMessage: (event) => {
            console.log('[Dashboard] WS message received:', event.type, event.data);
            
            // Update video state from WS events
            if (event.type === 'video_stats') {
                setVideoState({
                    faceCount: event.data.face_count as number || 0,
                    dominantEmotion: event.data.dominant_emotion as string || 'neutral',
                    confidence: event.data.confidence as number || 0,
                    totalFrames: event.data.total_frames as number || 0,
                    duration: event.data.duration as number || 0,
                    isRecording: true,
                });
            }
            
            // Update audio metrics from WS events
            if (event.type === 'audio_metrics') {
                setAudioMetrics({
                    amplitude: event.data.amplitude as number || 0,
                    is_speech: event.data.is_speech as boolean || false,
                    duration: event.data.duration as number || 0,
                });
            }
        },
    });

    // Sync connection state to store
    useEffect(() => {
        setConnectionState({ isConnected, isConnecting, reconnectCount });
    }, [isConnected, isConnecting, reconnectCount, setConnectionState]);

    // Import video API for backend OpenCV capture
    const videoApi = {
        startSession: async (sessionId: string) => {
            const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            await fetch(`${API_BASE}/video/start?session_id=${sessionId}`, { method: 'POST' });
        },
        stopSession: async () => {
            const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            await fetch(`${API_BASE}/video/stop`, { method: 'POST' });
        }
    };

    const { startRecording, stopRecording } = useAudioMetrics({
        sessionId: sessionId,
        enabled: audioEnabled,
        pollingRate: 20,
    });

    const handleStart = async () => {
        const sid = startSession();
        setVideoEnabled(true);
        setAudioEnabled(true);

        try {
            // Start backend OpenCV capture for AI processing
            await videoApi.startSession(sid);
            // Start audio recording
            await startRecording(sid);
        } catch (err) {
            console.error('Failed to start session:', err);
        }
    };

    const handleStop = async () => {
        setVideoEnabled(false);
        setAudioEnabled(false);
        endSession();

        try {
            await stopRecording();
            // Stop backend OpenCV capture
            await videoApi.stopSession();
        } catch (err) {
            console.error('Failed to stop session:', err);
        }
    };

    const handleAnalyze = async () => {
        await analyzeSession();
    };

    const handleReset = () => {
        setVideoEnabled(false);
        setAudioEnabled(false);
        resetSession();
    };

    return (
        <div className="min-h-screen bg-gray-950">
            {/* Connection Status Banner */}
            <ConnectionStatus className="fixed top-0 left-0 right-0 z-50" />

            {/* Error Toast */}
            <ErrorToast />

            {/* Header */}
            <header className="bg-gray-900/80 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-40">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                                <span className="text-white font-bold text-lg">AI</span>
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-white">AI Monitor</h1>
                                <p className="text-sm text-gray-400">Customer Satisfaction Analysis</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="text-sm text-gray-400">
                                Role: <span className="text-white capitalize">{role}</span>
                            </div>
                            {sessionId && (
                                <div className="text-sm text-gray-500 font-mono">
                                    {sessionId.slice(0, 12)}...
                                </div>
                            )}
                            {isActive && (
                                <div className="flex items-center gap-2 bg-red-600/20 text-red-400 px-3 py-1 rounded-full">
                                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                                    Recording
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column - Video & Audio */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* WebRTC Video Stream - 30 FPS with AI Overlay */}
                        <WebRTCVideoStream 
                            sessionId={sessionId || ''} 
                            enabled={videoEnabled && !!sessionId} 
                            className="w-full"
                            onConnected={() => console.log('[Dashboard] WebRTC connected')}
                            onDisconnected={() => console.log('[Dashboard] WebRTC disconnected')}
                        />

                        {/* Audio Section */}
                        <div className="bg-gray-800 rounded-xl p-5">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-white font-semibold">Audio Monitor</h3>
                                <AudioStatusBadge />
                            </div>
                            <AudioWaveform
                                height={80}
                                barCount={48}
                                color="#10b981"
                            />
                        </div>

                        {/* Control Buttons */}
                        <div className="flex gap-4">
                            {!isActive && !isProcessing && !isComplete && (
                                <button
                                    onClick={handleStart}
                                    disabled={isLoading}
                                    className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all shadow-lg"
                                >
                                    🎬 Start Session
                                </button>
                            )}

                            {isActive && (
                                <button
                                    onClick={handleStop}
                                    disabled={isLoading}
                                    className="flex-1 bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all shadow-lg"
                                >
                                    ⏹️ Stop Recording
                                </button>
                            )}

                            {isProcessing && (
                                <button
                                    onClick={handleAnalyze}
                                    disabled={isLoading}
                                    className="flex-1 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all shadow-lg"
                                >
                                    {isLoading ? '⏳ Analyzing...' : '🔍 Analyze Session'}
                                </button>
                            )}

                            {isComplete && (
                                <button
                                    onClick={handleReset}
                                    className="flex-1 bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white font-semibold py-3 px-6 rounded-lg transition-all shadow-lg"
                                >
                                    🔄 New Session
                                </button>
                            )}
                        </div>

                        {/* Session Summary (shows after analysis) */}
                        {isComplete && <SessionSummary />}
                    </div>

                    {/* Right Column - Stats & Timeline */}
                    <div className="space-y-6">
                        {/* Video Stats Panel */}
                        <VideoStatsPanel />

                        {/* Timeline */}
                        <SessionTimeline maxEvents={8} />

                        {/* Role Switch */}
                        <RoleSwitch />

                    </div>
                </div>
            </main>
        </div>
    );
}
