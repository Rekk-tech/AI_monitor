import api from './api';
import type {
    AudioStartResponse,
    AudioStopResponse,
    LiveMetrics,
    AudioStatusResponse,
    AudioLatestResult,
} from '@/types/api';

/**
 * Audio API Service
 * Handles all audio-related API calls
 */
export const audioApi = {
    /**
     * Start audio recording
     * Uses force=true to auto-stop any existing recording
     */
    startRecord: async (sessionId: string): Promise<AudioStartResponse> => {
        const response = await api.post('/audio/start-record', null, {
            params: { session_id: sessionId, force: true },
        });
        return response.data;
    },

    /**
     * Stop audio recording
     */
    stopRecord: async (sessionId: string): Promise<AudioStopResponse> => {
        const response = await api.post('/audio/stop-record', null, {
            params: { session_id: sessionId },
        });
        return response.data;
    },

    /**
     * Get live audio metrics
     */
    getLiveMetrics: async (sessionId: string): Promise<LiveMetrics> => {
        const response = await api.get('/audio/live-metrics', {
            params: { session_id: sessionId },
        });
        return response.data;
    },

    /**
     * Get audio processing status
     */
    getStatus: async (sessionId: string): Promise<AudioStatusResponse> => {
        const response = await api.get('/audio/status', {
            params: { session_id: sessionId },
        });
        return response.data;
    },

    /**
     * Get audio processing result
     */
    getLatestResult: async (sessionId: string): Promise<AudioLatestResult> => {
        const response = await api.get('/audio/latest-result', {
            params: { session_id: sessionId },
        });
        return response.data;
    },
};

export default audioApi;
