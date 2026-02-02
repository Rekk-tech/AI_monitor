'use client';

import { useEffect, useRef, useState } from 'react';
import { useSessionStore } from '@/store/session.store';

interface WebRTCVideoStreamProps {
    sessionId: string;
    enabled?: boolean;
    className?: string;
    onConnected?: () => void;
    onDisconnected?: () => void;
}

/**
 * Video stream component that polls frames from backend.
 * Backend handles camera capture via OpenCV and AI processing.
 * Frontend displays processed frames via HTTP polling.
 */
export function WebRTCVideoStream({
    sessionId,
    enabled = true,
    className = '',
    onConnected,
    onDisconnected
}: WebRTCVideoStreamProps) {
    const { video } = useSessionStore();
    const [frameUrl, setFrameUrl] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const pollingRef = useRef<NodeJS.Timeout | null>(null);

    // Poll frames from backend
    useEffect(() => {
        if (!enabled || !sessionId) {
            if (pollingRef.current) {
                clearInterval(pollingRef.current);
            }
            setFrameUrl(null);
            return;
        }

        setIsLoading(true);
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        const fetchFrame = () => {
            // Add timestamp to prevent caching
            setFrameUrl(`${API_BASE}/video/frame?t=${Date.now()}`);
        };

        // Start polling at ~10 FPS
        fetchFrame();
        pollingRef.current = setInterval(fetchFrame, 100);
        onConnected?.();
        setIsLoading(false);

        return () => {
            if (pollingRef.current) {
                clearInterval(pollingRef.current);
            }
            onDisconnected?.();
        };
    }, [enabled, sessionId]);

    return (
        <div className={`relative bg-gray-900 rounded-lg overflow-hidden ${className}`}>
            <div className="aspect-video relative">
                {enabled && frameUrl ? (
                    <img
                        src={frameUrl}
                        alt="Video Stream"
                        className="w-full h-full object-cover"
                        onError={() => setError('Camera not available')}
                        onLoad={() => setError(null)}
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gray-800">
                        <div className="text-center text-gray-400">
                            {isLoading ? (
                                <div className="animate-pulse">Connecting camera...</div>
                            ) : error ? (
                                <div className="text-red-400">{error}</div>
                            ) : (
                                <div>Video stream paused</div>
                            )}
                        </div>
                    </div>
                )}

                {/* Recording indicator */}
                {enabled && frameUrl && (
                    <div className="absolute top-3 right-3 flex items-center gap-2 bg-red-600/80 px-3 py-1 rounded-full">
                        <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                        <span className="text-white text-sm font-medium">REC</span>
                    </div>
                )}
            </div>

            {/* Stats Overlay */}
            {video.totalFrames > 0 && (
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                    <div className="flex justify-between items-end text-white text-sm">
                        <div>
                            <div className="text-lg font-semibold capitalize">
                                {video.dominantEmotion || 'Detecting...'}
                            </div>
                            <div className="text-gray-300">
                                Confidence: {(video.confidence * 100).toFixed(0)}%
                            </div>
                        </div>
                        <div className="text-right text-gray-300">
                            <div>Frames: {video.totalFrames}</div>
                            <div>Duration: {video.duration.toFixed(1)}s</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

