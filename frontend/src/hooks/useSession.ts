'use client';

import { useState, useCallback } from 'react';
import { useSessionStore } from '@/store/session.store';
import { resultApi } from '@/services/result.api';
import type { FinalResult } from '@/types/api';

export function useSession() {
    const {
        session,
        setSession,
        resetSession,
        finalResult,
        setFinalResult,
        setAgentState,
        isLoading,
        setLoading,
        error,
        setError,
    } = useSessionStore();

    const generateSessionId = useCallback(() => {
        return `SESS_${Date.now()}`;
    }, []);

    const startSession = useCallback(() => {
        const sessionId = generateSessionId();
        setSession({
            id: sessionId,
            startTime: new Date(),
            status: 'recording',
        });
        return sessionId;
    }, [generateSessionId, setSession]);

    const endSession = useCallback(() => {
        setSession({
            status: 'processing',
        });
    }, [setSession]);

    const analyzeSession = useCallback(async () => {
        if (!session.id) {
            setError('No active session');
            return null;
        }

        try {
            setLoading(true);
            setError(null);
            const result = await resultApi.analyze(session.id);
            setFinalResult(result);
            
            // Populate agent state for SessionSummary display
            setAgentState({
                finalState: result.final_state as 'SATISFIED' | 'NEUTRAL' | 'DISSATISFIED',
                confidence: result.confidence,
                reasoning: result.reasoning,
                recommendation: result.recommendation,
            });
            
            setSession({ status: 'complete' });
            return result;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Analysis failed');
            return null;
        } finally {
            setLoading(false);
        }
    }, [session.id, setLoading, setError, setFinalResult, setAgentState, setSession]);

    return {
        session,
        sessionId: session.id,
        isActive: session.status === 'recording',
        isProcessing: session.status === 'processing',
        isComplete: session.status === 'complete',
        finalResult,
        isLoading,
        error,
        startSession,
        endSession,
        analyzeSession,
        resetSession,
    };
}

export default useSession;
