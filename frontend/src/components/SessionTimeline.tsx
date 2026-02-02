'use client';

import { memo } from 'react';
import { useSessionStore, TimelineEvent } from '@/store/session.store';

interface SessionTimelineProps {
    className?: string;
    maxEvents?: number;
}

/**
 * Session Timeline - Shows real-time events during session
 */
export const SessionTimeline = memo(function SessionTimeline({
    className = '',
    maxEvents = 10,
}: SessionTimelineProps) {
    const events = useSessionStore((state) => state.events);
    const displayEvents = events.slice(-maxEvents).reverse();

    const getEventConfig = (type: TimelineEvent['type']) => {
        const configs: Record<string, { icon: string; color: string; label: string }> = {
            session_start: { icon: '▶️', color: 'text-green-400', label: 'Session Started' },
            session_stop: { icon: '⏹️', color: 'text-red-400', label: 'Session Stopped' },
            emotion_spike: { icon: '📈', color: 'text-yellow-400', label: 'Emotion Spike' },
            speech_detected: { icon: '🎤', color: 'text-blue-400', label: 'Speech Detected' },
            face_detected: { icon: '👤', color: 'text-purple-400', label: 'Face Detected' },
            result_ready: { icon: '✅', color: 'text-emerald-400', label: 'Result Ready' },
        };
        return configs[type] || { icon: '•', color: 'text-gray-400', label: type };
    };

    const formatTime = (timestamp: number) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    if (displayEvents.length === 0) {
        return (
            <div className={`bg-gray-800 rounded-xl p-5 ${className}`}>
                <h3 className="text-white font-semibold mb-4">Timeline</h3>
                <div className="text-center text-gray-500 py-8">
                    No events yet
                </div>
            </div>
        );
    }

    return (
        <div className={`bg-gray-800 rounded-xl p-5 ${className}`}>
            <h3 className="text-white font-semibold mb-4">Timeline</h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
                {displayEvents.map((event) => {
                    const config = getEventConfig(event.type);
                    return (
                        <div
                            key={event.id}
                            className="flex items-center gap-3 text-sm"
                        >
                            <span className="text-lg">{config.icon}</span>
                            <div className="flex-1">
                                <span className={config.color}>{config.label}</span>
                                {event.data && Object.keys(event.data).length > 0 && (
                                    <span className="text-gray-500 text-xs ml-2">
                                        {JSON.stringify(event.data)}
                                    </span>
                                )}
                            </div>
                            <span className="text-gray-500 text-xs font-mono">
                                {formatTime(event.timestamp)}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
});

export default SessionTimeline;
