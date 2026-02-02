'use client';

import { memo } from 'react';
import { useSessionStore } from '@/store/session.store';

interface VideoStatsPanelProps {
    className?: string;
    showEmotionBreakdown?: boolean;
}

/**
 * Real-time video stats panel
 * Shows face count, dominant emotion, confidence, and emotion breakdown
 */
export const VideoStatsPanel = memo(function VideoStatsPanel({
    className = '',
    showEmotionBreakdown = true,
}: VideoStatsPanelProps) {
    const video = useSessionStore((state) => state.video);

    const getEmotionColor = (emotion: string) => {
        const colors: Record<string, string> = {
            happy: 'text-green-400',
            sad: 'text-blue-400',
            angry: 'text-red-400',
            fear: 'text-purple-400',
            surprise: 'text-yellow-400',
            disgust: 'text-orange-400',
            neutral: 'text-gray-400',
        };
        return colors[emotion.toLowerCase()] || 'text-gray-400';
    };

    const getEmotionBgColor = (emotion: string) => {
        const colors: Record<string, string> = {
            happy: 'bg-green-500/20',
            sad: 'bg-blue-500/20',
            angry: 'bg-red-500/20',
            fear: 'bg-purple-500/20',
            surprise: 'bg-yellow-500/20',
            disgust: 'bg-orange-500/20',
            neutral: 'bg-gray-500/20',
        };
        return colors[emotion.toLowerCase()] || 'bg-gray-500/20';
    };

    const getEmotionIcon = (emotion: string) => {
        const icons: Record<string, string> = {
            happy: '😊',
            sad: '😢',
            angry: '😠',
            fear: '😨',
            surprise: '😲',
            disgust: '🤢',
            neutral: '😐',
        };
        return icons[emotion.toLowerCase()] || '😐';
    };

    // Sort emotions by count descending
    const sortedEmotions = Object.entries(video.emotionCounts)
        .sort(([, a], [, b]) => (b as number) - (a as number))
        .slice(0, 5);

    const totalCounts = Object.values(video.emotionCounts).reduce((a, b) => a + b, 0);

    return (
        <div className={`bg-gray-800 rounded-xl p-5 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold">Video Analysis</h3>
                <div className={`flex items-center gap-2 px-2 py-1 rounded-full ${video.isRecording ? 'bg-red-500/20' : 'bg-gray-700'
                    }`}>
                    <div className={`w-2 h-2 rounded-full ${video.isRecording ? 'bg-red-500 animate-pulse' : 'bg-gray-500'
                        }`} />
                    <span className="text-xs text-gray-400">
                        {video.isRecording ? 'Live' : 'Idle'}
                    </span>
                </div>
            </div>

            {/* Main Stats Grid */}
            <div className="grid grid-cols-3 gap-3 mb-4">
                {/* Face Count */}
                <div className="bg-gray-900 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-white">
                        {video.faceCount}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Faces</div>
                </div>

                {/* Dominant Emotion */}
                <div className={`rounded-lg p-3 text-center ${getEmotionBgColor(video.dominantEmotion)}`}>
                    <div className="text-2xl">
                        {getEmotionIcon(video.dominantEmotion)}
                    </div>
                    <div className={`text-xs mt-1 capitalize ${getEmotionColor(video.dominantEmotion)}`}>
                        {video.dominantEmotion}
                    </div>
                </div>

                {/* Confidence */}
                <div className="bg-gray-900 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-white">
                        {(video.confidence * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Confidence</div>
                </div>
            </div>

            {/* Stats Row */}
            <div className="flex justify-between text-sm text-gray-400 mb-4 px-1">
                <span>Frames: {video.totalFrames}</span>
                <span>Duration: {video.duration.toFixed(1)}s</span>
            </div>

            {/* Emotion Breakdown */}
            {showEmotionBreakdown && sortedEmotions.length > 0 && (
                <div className="border-t border-gray-700 pt-4">
                    <h4 className="text-sm text-gray-400 mb-3">Emotion Distribution</h4>
                    <div className="space-y-2">
                        {sortedEmotions.map(([emotion, count]) => {
                            const percentage = totalCounts > 0 ? ((count as number) / totalCounts) * 100 : 0;
                            return (
                                <div key={emotion} className="flex items-center gap-2">
                                    <span className="text-xs w-16 capitalize text-gray-400">{emotion}</span>
                                    <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full transition-all duration-300 ${emotion.toLowerCase() === video.dominantEmotion.toLowerCase()
                                                    ? 'bg-emerald-500'
                                                    : 'bg-gray-500'
                                                }`}
                                            style={{ width: `${percentage}%` }}
                                        />
                                    </div>
                                    <span className="text-xs text-gray-500 w-10 text-right">
                                        {percentage.toFixed(0)}%
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
});

export default VideoStatsPanel;
