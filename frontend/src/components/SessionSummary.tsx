'use client';

import { memo } from 'react';
import { useSessionStore } from '@/store/session.store';

interface SessionSummaryProps {
    className?: string;
}

/**
 * Session Summary Cards - Shows final results from audio, video, and agent analysis
 */
export const SessionSummary = memo(function SessionSummary({
    className = '',
}: SessionSummaryProps) {
    const agent = useSessionStore((state) => state.agent);
    const video = useSessionStore((state) => state.video);
    const audio = useSessionStore((state) => state.audio);

    const getFinalStateConfig = (state: string | null) => {
        switch (state) {
            case 'SATISFIED':
                return { color: 'from-green-500 to-emerald-600', icon: '😊', text: 'Satisfied' };
            case 'DISSATISFIED':
                return { color: 'from-red-500 to-rose-600', icon: '😞', text: 'Dissatisfied' };
            case 'NEUTRAL':
                return { color: 'from-yellow-500 to-amber-600', icon: '😐', text: 'Neutral' };
            default:
                return { color: 'from-gray-500 to-gray-600', icon: '❓', text: 'Pending' };
        }
    };

    const stateConfig = getFinalStateConfig(agent.finalState);

    return (
        <div className={`space-y-4 ${className}`}>
            {/* Final Result Card */}
            <div className={`bg-gradient-to-r ${stateConfig.color} rounded-xl p-6 text-white`}>
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold opacity-90">Final Result</h3>
                        <div className="text-3xl font-bold mt-1">{stateConfig.text}</div>
                    </div>
                    <div className="text-5xl">{stateConfig.icon}</div>
                </div>

                {/* Only show recommendation when analysis complete (finalState is not null) */}
                {agent.finalState && agent.recommendation && (
                    <p className="mt-4 text-sm opacity-90 bg-black/20 rounded-lg p-3">
                        {agent.recommendation}
                    </p>
                )}

                {/* Only show confidence bars when analysis complete */}
                {agent.finalState && Object.keys(agent.confidence).length > 0 && (
                    <div className="mt-4 space-y-2">
                        {Object.entries(agent.confidence).map(([key, value]) => (
                            <div key={key} className="flex items-center gap-2">
                                <span className="text-xs w-24 capitalize opacity-75">{key}</span>
                                <div className="flex-1 h-1.5 bg-black/30 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-white/80"
                                        style={{ width: `${(value as number) * 100}%` }}
                                    />
                                </div>
                                <span className="text-xs w-10 text-right">
                                    {((value as number) * 100).toFixed(0)}%
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Summary Cards Grid */}
            <div className="grid grid-cols-2 gap-4">
                {/* Video Summary */}
                <div className="bg-gray-800 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <span className="text-xl">🎥</span>
                        <h4 className="text-white font-medium">Video</h4>
                    </div>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-400">Dominant</span>
                            <span className="text-white capitalize">{video.dominantEmotion}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-400">Confidence</span>
                            <span className="text-white">{(video.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-400">Frames</span>
                            <span className="text-white">{video.totalFrames}</span>
                        </div>
                    </div>
                </div>

                {/* Audio Summary */}
                <div className="bg-gray-800 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <span className="text-xl">🎤</span>
                        <h4 className="text-white font-medium">Audio</h4>
                    </div>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-400">Duration</span>
                            <span className="text-white">{audio.duration.toFixed(1)}s</span>
                        </div>
                        
                        {/* Show analysis results when available, otherwise show recording metrics */}
                        {agent.finalState ? (
                            <>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Sentiment</span>
                                    <span className={`font-medium ${
                                        agent.confidence.audio > 0.6 ? 'text-green-400' : 
                                        agent.confidence.audio < 0.4 ? 'text-red-400' : 'text-yellow-400'
                                    }`}>
                                        {agent.confidence.audio > 0.6 ? 'Positive' : 
                                         agent.confidence.audio < 0.4 ? 'Negative' : 'Neutral'}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Confidence</span>
                                    <span className="text-white">
                                        {(agent.confidence.audio * 100).toFixed(0)}%
                                    </span>
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Speech</span>
                                    <span className="text-white">
                                        {audio.totalFrames > 0
                                            ? ((audio.speechFrames / audio.totalFrames) * 100).toFixed(0)
                                            : 0}%
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Status</span>
                                    <span className="text-white capitalize">{audio.status}</span>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* Reasoning - only show when analysis complete */}
            {agent.finalState && agent.reasoning.length > 0 && (
                <div className="bg-gray-800 rounded-xl p-4">
                    <h4 className="text-white font-medium mb-3">Analysis Reasoning</h4>
                    <ul className="space-y-2">
                        {agent.reasoning.map((reason, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                                <span className="text-gray-500">•</span>
                                <span className="text-gray-300">{reason}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
});

export default SessionSummary;
