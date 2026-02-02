'use client';

import { memo } from 'react';
import { useSessionStore } from '@/store/session.store';

interface ConnectionStatusProps {
    className?: string;
}

/**
 * Connection status banner
 * Shows WebSocket connection state with reconnecting indicator
 */
export const ConnectionStatus = memo(function ConnectionStatus({
    className = '',
}: ConnectionStatusProps) {
    const connection = useSessionStore((state) => state.connection);

    // Only show when not connected
    if (connection.isConnected) {
        return null;
    }

    if (connection.isConnecting) {
        return (
            <div className={`bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-3 ${className}`}>
                <div className="flex items-center gap-3">
                    <div className="animate-spin h-4 w-4 border-2 border-yellow-500 border-t-transparent rounded-full" />
                    <div>
                        <span className="text-yellow-400 font-medium">Connecting...</span>
                        {connection.reconnectCount > 0 && (
                            <span className="text-yellow-400/70 text-sm ml-2">
                                (Attempt {connection.reconnectCount})
                            </span>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    // Disconnected
    return (
        <div className={`bg-red-500/20 border border-red-500/50 rounded-lg p-3 ${className}`}>
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="h-4 w-4 rounded-full bg-red-500 animate-pulse" />
                    <div>
                        <span className="text-red-400 font-medium">Connection Lost</span>
                        {connection.lastError && (
                            <p className="text-red-400/70 text-sm">{connection.lastError}</p>
                        )}
                    </div>
                </div>
                <button
                    className="px-3 py-1 bg-red-500 hover:bg-red-600 text-white text-sm rounded-lg transition-colors"
                    onClick={() => window.location.reload()}
                >
                    Reload
                </button>
            </div>
        </div>
    );
});

export default ConnectionStatus;
