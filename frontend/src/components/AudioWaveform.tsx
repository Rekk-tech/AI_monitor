'use client';

import { useEffect, useRef, memo } from 'react';
import { useSessionStore, selectAudioAmplitude } from '@/store/session.store';

interface AudioWaveformProps {
    className?: string;
    barCount?: number;
    color?: string;
    height?: number;
}

/**
 * High-performance audio waveform visualizer
 * Uses CSS transforms for 60fps animation without React re-renders
 */
export const AudioWaveform = memo(function AudioWaveform({
    className = '',
    barCount = 32,
    color = '#10b981',
    height = 64,
}: AudioWaveformProps) {
    const barsRef = useRef<HTMLDivElement[]>([]);
    const animationRef = useRef<number | null>(null);
    const amplitudeRef = useRef(0);

    // Subscribe to amplitude changes without re-render
    useEffect(() => {
        const unsubscribe = useSessionStore.subscribe(
            (state) => state.audio.amplitude,
            (amplitude) => {
                amplitudeRef.current = amplitude;
            }
        );
        return () => unsubscribe();
    }, []);

    // Animation loop using requestAnimationFrame
    useEffect(() => {
        const animate = () => {
            const amp = amplitudeRef.current;

            barsRef.current.forEach((bar, i) => {
                if (!bar) return;

                // Create wave effect with phase offset per bar
                const phase = (i / barCount) * Math.PI * 2;
                const time = Date.now() / 200;
                const wave = Math.sin(time + phase);

                // Combine amplitude with wave for natural movement
                const baseHeight = 0.1; // Minimum height
                const ampEffect = amp * 0.9; // Max amplitude contribution
                const waveEffect = 0.1 * Math.abs(wave); // Subtle wave motion

                const scale = baseHeight + ampEffect + (amp > 0.05 ? waveEffect : 0);

                // Use transform for GPU acceleration
                bar.style.transform = `scaleY(${Math.min(scale, 1)})`;
            });

            animationRef.current = requestAnimationFrame(animate);
        };

        animationRef.current = requestAnimationFrame(animate);

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [barCount]);

    return (
        <div
            className={`flex items-end justify-center gap-0.5 ${className}`}
            style={{ height }}
            aria-label="Audio waveform"
            role="img"
        >
            {Array.from({ length: barCount }).map((_, i) => (
                <div
                    key={i}
                    ref={(el) => {
                        if (el) barsRef.current[i] = el;
                    }}
                    className="w-1.5 rounded-full origin-bottom transition-colors"
                    style={{
                        height: '100%',
                        backgroundColor: color,
                        transform: 'scaleY(0.1)',
                        willChange: 'transform',
                    }}
                />
            ))}
        </div>
    );
});

export default AudioWaveform;
