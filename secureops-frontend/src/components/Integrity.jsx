import React, { useEffect, useState } from 'react';
import { ShieldCheck, Server, Database, Lock, Clock, AlertCircle } from 'lucide-react';
import SafetyAPI from '../api';

const Integrity = () => {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const health = await SafetyAPI.getHealth();
                setStatus(health);
                setError(null);
            } catch (err) {
                console.error("Health check failed", err);
                setError("System unreachable");
            } finally {
                setLoading(false);
            }
        };

        fetchHealth();
        // Poll every 30 seconds
        const interval = setInterval(fetchHealth, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="p-8 text-gray-500">Checking system integrity...</div>;

    const StatusRow = ({ label, value, icon }) => {
        const Icon = icon;
        return (
            <div className="flex items-center justify-between p-4 bg-white border border-gray-100 rounded-lg mb-3 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-full ${value === 'ok' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                        <Icon size={20} />
                    </div>
                    <span className="font-medium text-gray-700">{label}</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${value === 'ok' ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`}></span>
                    <span className={`text-sm font-semibold capitalize ${value === 'ok' ? 'text-green-700' : 'text-red-700'}`}>
                        {value === 'ok' ? 'Operational' : 'Critical'}
                    </span>
                </div>
            </div>
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <ShieldCheck className="text-blue-600" /> System Integrity Status
                </h2>
                {status?.timestamp && (
                    <span className="text-sm text-gray-500 flex items-center gap-1">
                        <Clock size={14} /> Last updated: {new Date(status.timestamp).toLocaleTimeString()}
                    </span>
                )}
            </div>

            {error ? (
                <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg flex items-center gap-2">
                    <AlertCircle size={20} />
                    <strong>Error:</strong> {error}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div className="bg-gray-50 p-6 rounded-xl border border-gray-200">
                        <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Core Components</h3>
                        <StatusRow label="API Gateway" value={status.api} icon={Server} />
                        <StatusRow label="Primary Database" value={status.database} icon={Database} />
                        <StatusRow label="Identity Provider" value={status.auth} icon={Lock} />
                    </div>
                </div>
            )}
        </div>
    );
};

export default Integrity;
