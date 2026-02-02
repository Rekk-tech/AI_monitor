'use client';

import { useSessionStore } from '@/store/session.store';

interface SessionStatsProps {
    className?: string;
}

export function SessionStats({ className = '' }: SessionStatsProps) {
    const { videoStats, audioMetrics, session, finalResult } = useSessionStore();

    const getStatusColor = () => {
        switch (session.status) {
            case 'recording':
                return 'bg-red-500';
            case 'processing':
                return 'bg-yellow-500';
            case 'complete':
                return 'bg-green-500';
            default:
                return 'bg-gray-500';
        }
    };

    return (
        <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold">Session Stats</h3>
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
                    <span className="text-sm text-gray-300 capitalize">{session.status}</span>
                </div>
            </div>

            {/* Session Info */}
            {session.id && (
                <div className="text-sm text-gray-400 mb-4">
                    ID: <span className="text-white font-mono">{session.id}</span>
                </div>
            )}

            {/* Video Stats */}
            {videoStats && (
                <div className="mb-4">
                    <h4 className="text-gray-400 text-sm mb-2">Video</h4>
                    <div className="grid grid-cols-2 gap-2">
                        <Stat label="Emotion" value={videoStats.current_emotion || '-'} />
                        <Stat label="Confidence" value={`${((videoStats.current_confidence || 0) * 100).toFixed(0)}%`} />
                        <Stat label="Frames" value={videoStats.total_frames.toString()} />
                        <Stat label="Duration" value={`${videoStats.duration_seconds?.toFixed(1)}s`} />
                    </div>
                </div>
            )}

            {/* Audio Stats */}
            {audioMetrics && (
                <div className="mb-4">
                    <h4 className="text-gray-400 text-sm mb-2">Audio</h4>
                    <div className="grid grid-cols-2 gap-2">
                        <Stat label="Amplitude" value={`${(audioMetrics.amplitude * 100).toFixed(0)}%`} />
                        <Stat label="Speech" value={audioMetrics.is_speech ? 'Yes' : 'No'} />
                        <Stat label="Duration" value={`${audioMetrics.duration.toFixed(1)}s`} />
                    </div>
                </div>
            )}

            {/* Final Result */}
            {finalResult && (
                <div className="border-t border-gray-700 pt-4">
                    <h4 className="text-gray-400 text-sm mb-2">Result</h4>
                    <div className={`text-2xl font-bold ${finalResult.final_state === 'SATISFIED' ? 'text-green-500' :
                            finalResult.final_state === 'DISSATISFIED' ? 'text-red-500' :
                                'text-yellow-500'
                        }`}>
                        {finalResult.final_state}
                    </div>
                    <p className="text-sm text-gray-400 mt-1">{finalResult.recommendation}</p>
                </div>
            )}
        </div>
    );
}

function Stat({ label, value }: { label: string; value: string }) {
    return (
        <div className="bg-gray-900 rounded p-2">
            <div className="text-xs text-gray-500">{label}</div>
            <div className="text-white font-medium capitalize">{value}</div>
        </div>
    );
}

export default SessionStats;
