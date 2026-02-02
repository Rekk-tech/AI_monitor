'use client';

import { memo } from 'react';
import { useSessionStore } from '@/store/session.store';

interface AudioStatusBadgeProps {
    className?: string;
    showDuration?: boolean;
}

/**
 * Audio status badge with recording indicator
 * - Shows current status (idle/recording/processing/done/error)
 * - Optional duration display
 * - Pulsing animation when recording
 */
export const AudioStatusBadge = memo(function AudioStatusBadge({
    className = '',
    showDuration = true,
}: AudioStatusBadgeProps) {
    const status = useSessionStore((state) => state.audio.status);
    const duration = useSessionStore((state) => state.audio.duration);
    const isSpeech = useSessionStore((state) => state.audio.isSpeech);
    
    const getStatusConfig = () => {
        switch (status) {
            case 'recording':
                return {
                    bgColor: 'bg-red-500/20',
                    dotColor: 'bg-red-500',
                    textColor: 'text-red-400',
                    label: 'Recording',
                    pulse: true,
                };
            case 'processing':
                return {
                    bgColor: 'bg-yellow-500/20',
                    dotColor: 'bg-yellow-500',
                    textColor: 'text-yellow-400',
                    label: 'Processing',
                    pulse: false,
                };
            case 'done':
                return {
                    bgColor: 'bg-green-500/20',
                    dotColor: 'bg-green-500',
                    textColor: 'text-green-400',
                    label: 'Done',
                    pulse: false,
                };
            case 'error':
                return {
                    bgColor: 'bg-red-500/20',
                    dotColor: 'bg-red-600',
                    textColor: 'text-red-400',
                    label: 'Error',
                    pulse: false,
                };
            default:
                return {
                    bgColor: 'bg-gray-500/20',
                    dotColor: 'bg-gray-500',
                    textColor: 'text-gray-400',
                    label: 'Idle',
                    pulse: false,
                };
        }
    };

    const config = getStatusConfig();

    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className={`flex items-center gap-3 ${className}`}>
            {/* Status Badge */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bgColor}`}>
                <div className="relative">
                    <div className={`w-2 h-2 rounded-full ${config.dotColor}`} />
                    {config.pulse && (
                        <div className={`absolute inset-0 w-2 h-2 rounded-full ${config.dotColor} animate-ping`} />
                    )}
                </div>
                <span className={`text-sm font-medium ${config.textColor}`}>
                    {config.label}
                </span>
            </div>

            {/* Duration */}
            {showDuration && status === 'recording' && (
                <span className="text-sm text-gray-400 font-mono">
                    {formatDuration(duration)}
                </span>
            )}

            {/* Speech indicator */}
            {status === 'recording' && (
                <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full transition-colors ${isSpeech ? 'bg-blue-500/20' : 'bg-gray-700/50'
                    }`}>
                    <div className={`w-1.5 h-1.5 rounded-full transition-colors ${isSpeech ? 'bg-blue-400' : 'bg-gray-500'
                        }`} />
                    <span className={`text-xs transition-colors ${isSpeech ? 'text-blue-400' : 'text-gray-500'
                        }`}>
                        {isSpeech ? 'Speech' : 'Silence'}
                    </span>
                </div>
            )}
        </div>
    );
});

export default AudioStatusBadge;
