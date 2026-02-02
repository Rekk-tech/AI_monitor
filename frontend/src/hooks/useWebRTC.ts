'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { WebRTCService, createWebRTCService } from '@/services/webrtc.service';

interface UseWebRTCOptions {
    sessionId: string;
    onConnected?: () => void;
    onDisconnected?: () => void;
    onError?: (error: Error) => void;
}

interface UseWebRTCReturn {
    isConnecting: boolean;
    isConnected: boolean;
    localStream: MediaStream | null;
    error: string | null;
    connect: () => Promise<void>;
    disconnect: () => Promise<void>;
    videoRef: React.RefObject<HTMLVideoElement>;
}

export function useWebRTC(options: UseWebRTCOptions): UseWebRTCReturn {
    const [isConnecting, setIsConnecting] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [localStream, setLocalStream] = useState<MediaStream | null>(null);
    const [error, setError] = useState<string | null>(null);
    
    const serviceRef = useRef<WebRTCService | null>(null);
    const videoRef = useRef<HTMLVideoElement>(null);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            serviceRef.current?.disconnect();
        };
    }, []);

    // Attach stream to video element
    useEffect(() => {
        if (localStream && videoRef.current) {
            videoRef.current.srcObject = localStream;
        }
    }, [localStream]);

    const connect = useCallback(async () => {
        if (isConnecting || isConnected) return;

        setIsConnecting(true);
        setError(null);

        try {
            serviceRef.current = createWebRTCService({
                sessionId: options.sessionId,
                onConnected: () => {
                    setIsConnected(true);
                    options.onConnected?.();
                },
                onDisconnected: () => {
                    setIsConnected(false);
                    options.onDisconnected?.();
                },
                onError: (err) => {
                    setError(err.message);
                    options.onError?.(err);
                }
            });

            const stream = await serviceRef.current.connect();
            setLocalStream(stream);
            setIsConnected(true);

        } catch (err) {
            const message = err instanceof Error ? err.message : 'Connection failed';
            setError(message);
            throw err;
        } finally {
            setIsConnecting(false);
        }
    }, [options, isConnecting, isConnected]);

    const disconnect = useCallback(async () => {
        await serviceRef.current?.disconnect();
        serviceRef.current = null;
        setLocalStream(null);
        setIsConnected(false);
    }, []);

    return {
        isConnecting,
        isConnected,
        localStream,
        error,
        connect,
        disconnect,
        videoRef: videoRef as React.RefObject<HTMLVideoElement>
    };
}
