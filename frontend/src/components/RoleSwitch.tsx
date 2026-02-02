'use client';

import { useSessionStore } from '@/store/session.store';
import type { UserRole } from '@/types/api';

interface RoleSwitchProps {
    className?: string;
}

const ROLES: { value: UserRole; label: string; description: string }[] = [
    {
        value: 'supervisor',
        label: 'Supervisor',
        description: 'Monitor calls in real-time',
    },
];

export function RoleSwitch({ className = '' }: RoleSwitchProps) {
    const { role, setRole } = useSessionStore();

    return (
        <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
            <h3 className="text-white font-semibold mb-3">Select Role</h3>
            <div className="space-y-2">
                {ROLES.map((r) => (
                    <button
                        key={r.value}
                        onClick={() => setRole(r.value)}
                        className={`w-full p-3 rounded-lg text-left transition-all ${role === r.value
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            }`}
                    >
                        <div className="font-medium">{r.label}</div>
                        <div className="text-sm opacity-75">{r.description}</div>
                    </button>
                ))}
            </div>
            <p className="text-xs text-gray-500 mt-3">
                Note: Authentication will be added in a future update
            </p>
        </div>
    );
}

export default RoleSwitch;
