'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useSessionStore } from '@/store/session.store';

// WebSocket event types matching backend
export type WSEventType =
    | 'connected'
    | 'disconnected'
    | 'video_stats'
    | 'audio_metrics'
    | 'audio_status'
    | 'session_state'
    | 'session_completed'
    | 'final_result'
    | 'error'
    | 'heartbeat'
    | 'pong';


export interface WSEvent {
    type: WSEventType;
    session_id: string;
    timestamp: string;
    data: Record<string, unknown>;
}

export interface WebSocketConfig {
    sessionId: string;
    autoConnect?: boolean;
    reconnectAttempts?: number;
    reconnectInterval?: number;
    heartbeatInterval?: number;
    onMessage?: (event: WSEvent) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    onError?: (error: Event) => void;
}

export interface WebSocketState {
    isConnected: boolean;
    isConnecting: boolean;
    error: string | null;
    lastMessage: WSEvent | null;
    reconnectCount: number;
    lastHeartbeat: number | null;
    missedPongs: number;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// Heartbeat configuration (match backend)
const PING_INTERVAL = 5000;  // Send ping every 5 seconds
const MAX_MISSED_PONGS = 3;  // Disconnect after 3 missed pongs

export function useWebSocket(config: WebSocketConfig) {
    const {
        sessionId,
        autoConnect = true,
        reconnectAttempts = 5,
        reconnectInterval = 2000,  // Faster reconnect
        onMessage,
        onConnect,
        onDisconnect,
        onError,
    } = config;

    const [state, setState] = useState<WebSocketState>({
        isConnected: false,
        isConnecting: false,
        error: null,
        lastMessage: null,
        reconnectCount: 0,
        lastHeartbeat: null,
        missedPongs: 0,
    });

    const wsRef = useRef<WebSocket | null>(null);
    const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const shouldReconnectRef = useRef(true);
    const missedPongsRef = useRef(0);

    // Store updates
    const setVideoStats = useSessionStore((state) => state.setVideoStats);
    const setAudioMetrics = useSessionStore((state) => state.setAudioMetrics);
    const setFinalResult = useSessionStore((state) => state.setFinalResult);
    const setError = useSessionStore((state) => state.setError);

    // Handle incoming messages
    const handleMessage = useCallback((event: MessageEvent) => {
        try {
            const wsEvent: WSEvent = JSON.parse(event.data);

            setState((prev) => ({ ...prev, lastMessage: wsEvent }));

            // Process event based on type
            switch (wsEvent.type) {
                case 'video_stats':
                    setVideoStats({
                        is_recording: true,
                        total_frames: wsEvent.data.total_frames as number || 0,
                        duration_seconds: wsEvent.data.duration as number || 0,
                        counts: {
                            happy: 0,
                            neutral: 0,
                            sad: 0,
                            angry: 0,
                            ...(wsEvent.data.emotion_counts as Record<string, number> || {}),
                        },
                        current_emotion: wsEvent.data.dominant_emotion as string || 'neutral',
                        current_confidence: wsEvent.data.confidence as number || 0,
                    });
                    break;

                case 'audio_metrics':
                    setAudioMetrics({
                        amplitude: wsEvent.data.amplitude as number || 0,
                        is_speech: wsEvent.data.is_speech as boolean || false,
                        duration: wsEvent.data.duration as number || 0,
                    });
                    break;

                case 'audio_status':
                    console.log('[WS] Audio status:', wsEvent.data.status);
                    break;

                case 'session_completed':
                    console.log('[WS] Session completed for:', wsEvent.session_id);
                    break;

                case 'final_result':
                    if (wsEvent.data) {
                        setFinalResult(wsEvent.data as unknown as import('@/types/api').FinalResult);
                    }
                    break;

                case 'error':
                    setError(wsEvent.data.message as string);
                    break;

                case 'connected':
                    console.log('[WS] Connected to session:', wsEvent.session_id);
                    break;

                case 'heartbeat':
                    // Server heartbeat received - update timestamp
                    setState((prev) => ({ ...prev, lastHeartbeat: Date.now() }));
                    break;

                case 'pong':
                    // Server responded to our ping - reset missed pongs counter
                    missedPongsRef.current = 0;
                    setState((prev) => ({ 
                        ...prev, 
                        lastHeartbeat: Date.now(),
                        missedPongs: 0 
                    }));
                    break;

                default:
                    console.log('[WS] Unhandled event type:', wsEvent.type);
            }

            // Call custom handler if provided
            onMessage?.(wsEvent);
        } catch (err) {
            console.error('[WS] Failed to parse message:', err);
        }
    }, [onMessage, setVideoStats, setAudioMetrics, setFinalResult, setError]);


    // Start ping/pong heartbeat
    const startPing = useCallback(() => {
        if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current);
        }

        missedPongsRef.current = 0;

        pingIntervalRef.current = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                // Increment missed pongs counter (will be reset on pong received)
                missedPongsRef.current += 1;
                
                if (missedPongsRef.current > MAX_MISSED_PONGS) {
                    console.warn('[WS] Too many missed pongs, forcing reconnect...');
                    wsRef.current?.close();
                    return;
                }

                // Send ping
                wsRef.current.send(JSON.stringify({ type: 'ping' }));
                setState((prev) => ({ ...prev, missedPongs: missedPongsRef.current }));
            }
        }, PING_INTERVAL);
    }, []);

    // Stop ping
    const stopPing = useCallback(() => {
        if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current);
            pingIntervalRef.current = null;
        }
        missedPongsRef.current = 0;
    }, []);

    // Connect to WebSocket
    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        setState((prev) => ({ ...prev, isConnecting: true, error: null }));

        const wsUrl = `${WS_BASE_URL}/ws/session/${sessionId}`;
        console.log('[WS] Connecting to:', wsUrl);

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('[WS] Connection established');
            setState((prev) => ({
                ...prev,
                isConnected: true,
                isConnecting: false,
                error: null,
                reconnectCount: 0,
            }));
            startPing();
            onConnect?.();
        };

        ws.onmessage = handleMessage;

        ws.onerror = (error) => {
            console.error('[WS] Error:', error);
            setState((prev) => ({
                ...prev,
                error: 'WebSocket connection error',
                isConnecting: false,
            }));
            onError?.(error);
        };

        ws.onclose = () => {
            console.log('[WS] Connection closed');
            setState((prev) => ({
                ...prev,
                isConnected: false,
                isConnecting: false,
            }));
            stopPing();
            onDisconnect?.();

            // Attempt reconnection if enabled
            if (shouldReconnectRef.current && state.reconnectCount < reconnectAttempts) {
                console.log(`[WS] Attempting reconnect (${state.reconnectCount + 1}/${reconnectAttempts})...`);

                reconnectTimeoutRef.current = setTimeout(() => {
                    setState((prev) => ({
                        ...prev,
                        reconnectCount: prev.reconnectCount + 1,
                    }));
                    connect();
                }, reconnectInterval);
            }
        };
    }, [
        sessionId,
        reconnectAttempts,
        reconnectInterval,
        startPing,
        stopPing,
        handleMessage,
        onConnect,
        onDisconnect,
        onError,
        state.reconnectCount,
    ]);

    // Disconnect from WebSocket
    const disconnect = useCallback(() => {
        shouldReconnectRef.current = false;

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        stopPing();

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }

        setState({
            isConnected: false,
            isConnecting: false,
            error: null,
            lastMessage: null,
            reconnectCount: 0,
            lastHeartbeat: null,
            missedPongs: 0,
        });
    }, [stopPing]);

    // Send message
    const sendMessage = useCallback((message: object) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
            return true;
        }
        console.warn('[WS] Cannot send message: not connected');
        return false;
    }, []);

    // Auto-connect on mount
    useEffect(() => {
        console.log('[useWebSocket] Effect triggered:', { autoConnect, sessionId, shouldConnect: autoConnect && sessionId });
        
        if (autoConnect && sessionId) {
            console.log('[useWebSocket] Connecting to session:', sessionId);
            shouldReconnectRef.current = true;
            connect();
        }

        return () => {
            disconnect();
        };
    }, [autoConnect, sessionId]); // Intentionally not including connect/disconnect to avoid loops

    return {
        ...state,
        connect,
        disconnect,
        sendMessage,
    };
}

export default useWebSocket;
