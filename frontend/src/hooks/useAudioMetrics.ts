'use client';

import { useEffect, useRef, useState } from 'react';
import { audioApi } from '@/services/audio.api';
import { useSessionStore } from '@/store/session.store';
import type { AudioStatus } from '@/types/api';

interface UseAudioMetricsOptions {
    sessionId: string;
    pollingRate?: number; // Hz
    enabled?: boolean;
}

export function useAudioMetrics(options: UseAudioMetricsOptions) {
    const { sessionId, pollingRate = 20, enabled = true } = options;
    const [status, setStatus] = useState<AudioStatus>('idle');
    const [isLoading, setIsLoading] = useState(false);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const { setAudioMetrics } = useSessionStore();

    useEffect(() => {
        if (!enabled || !sessionId) {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
            return;
        }

        const fetchMetrics = async () => {
            try {
                const metrics = await audioApi.getLiveMetrics(sessionId);
                setAudioMetrics(metrics);
            } catch (error) {
                console.error('Failed to fetch audio metrics:', error);
            }
        };

        // Start polling
        fetchMetrics();
        intervalRef.current = setInterval(fetchMetrics, 1000 / pollingRate);

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
        };
    }, [enabled, sessionId, pollingRate, setAudioMetrics]);

    const startRecording = async (overrideSessionId?: string) => {
        const sid = overrideSessionId || sessionId;
        if (!sid) {
            throw new Error('Session ID is required');
        }
        try {
            setIsLoading(true);
            const result = await audioApi.startRecord(sid);
            setStatus('recording');
            return result;
        } finally {
            setIsLoading(false);
        }
    };

    const stopRecording = async () => {
        try {
            setIsLoading(true);
            if (!sessionId) {
                console.warn('[useAudioMetrics] No sessionId, skipping stop');
                setStatus('idle');
                return null;
            }
            const result = await audioApi.stopRecord(sessionId);
            setStatus('processing');
            return result;
        } catch (error: unknown) {
            // Handle 400 errors gracefully (not recording, session mismatch)
            const axiosError = error as { response?: { status?: number } };
            if (axiosError?.response?.status === 400) {
                console.warn('[useAudioMetrics] Stop failed (not recording):', error);
                setStatus('idle');
                return null;
            }
            throw error;
        } finally {
            setIsLoading(false);
        }
    };

    const getResult = async () => {
        try {
            setIsLoading(true);
            const result = await audioApi.getLatestResult(sessionId);
            setStatus(result.status);
            return result;
        } finally {
            setIsLoading(false);
        }
    };

    const pollStatus = async () => {
        try {
            const result = await audioApi.getStatus(sessionId);
            setStatus(result.status);
            return result.status;
        } catch (error) {
            console.error('Failed to get status:', error);
            return 'error' as AudioStatus;
        }
    };

    return {
        status,
        isLoading,
        startRecording,
        stopRecording,
        getResult,
        pollStatus,
    };
}

export default useAudioMetrics;
