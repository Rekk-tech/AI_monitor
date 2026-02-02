'use client';

import { useEffect, useState, memo } from 'react';
import { useSessionStore } from '@/store/session.store';

interface ErrorToastProps {
    duration?: number;
}

/**
 * Error toast notification
 * Auto-dismisses after duration
 */
export const ErrorToast = memo(function ErrorToast({
    duration = 5000,
}: ErrorToastProps) {
    const error = useSessionStore((state) => state.error);
    const setError = useSessionStore((state) => state.setError);
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        if (error) {
            setVisible(true);
            const timer = setTimeout(() => {
                setVisible(false);
                setTimeout(() => setError(null), 300); // Wait for fade out
            }, duration);
            return () => clearTimeout(timer);
        }
    }, [error, duration, setError]);

    if (!error) return null;

    return (
        <div
            className={`fixed bottom-4 right-4 z-50 transition-all duration-300 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                }`}
        >
            <div className="bg-red-900/90 border border-red-500/50 rounded-lg p-4 shadow-lg max-w-sm">
                <div className="flex items-start gap-3">
                    <span className="text-red-400 text-xl">⚠️</span>
                    <div className="flex-1">
                        <h4 className="text-red-400 font-medium">Error</h4>
                        <p className="text-red-300/80 text-sm mt-1">{error}</p>
                    </div>
                    <button
                        onClick={() => setError(null)}
                        className="text-red-400/60 hover:text-red-400 transition-colors"
                    >
                        ✕
                    </button>
                </div>
            </div>
        </div>
    );
});

export default ErrorToast;
