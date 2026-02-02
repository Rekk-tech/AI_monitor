import api from './api';
import type { FinalResult } from '@/types/api';

/**
 * Result API Service
 * Handles final analysis API calls
 */
export const resultApi = {
    /**
     * Analyze session and get final result
     */
    analyze: async (sessionId: string): Promise<FinalResult> => {
        const response = await api.post('/result/analyze', {
            session_id: sessionId,
        });
        return response.data;
    },
};

export default resultApi;
