import api from './api';
import type {
    VideoStartResponse,
    VideoStopResponse,
} from '@/types/api';

/**
 * Video API Service
 * Handles video-related API calls
 * Note: Video streaming now uses WebRTC, this API is for session control only
 */
export const videoApi = {
    /**
     * Start video capture session (legacy - WebRTC auto-starts)
     */
    startSession: async (sessionId?: string): Promise<VideoStartResponse> => {
        const response = await api.post('/video/start', null, {
            params: { session_id: sessionId }
        });
        return response.data;
    },

    /**
     * Stop video capture and get results
     */
    stopSession: async (): Promise<VideoStopResponse> => {
        const response = await api.post('/video/stop');
        return response.data;
    },

    /**
     * Close WebRTC connection
     */
    closeWebRTC: async (sessionId: string): Promise<void> => {
        await api.post('/video/webrtc/close', null, {
            params: { session_id: sessionId }
        });
    },
};

export default videoApi;
