import React from 'react';
import StatCard from './StatCard';
import { CheckCircle, XCircle, AlertTriangle, Clock, Activity, FileText, Lock } from 'lucide-react';

const Dashboard = ({ summary }) => {
    if (!summary) return <div className="p-8">Loading data...</div>;

    const pipelineStatus = summary.pipeline_status || 'PENDING';
    const accuracy = summary.accuracy !== undefined ? summary.accuracy : 0;
    const passThreshold = summary.pass_threshold || 0.7;
    const totalSamples = summary.total_samples || 0;
    const integrityHash = summary.integrity_hash;
    const violations = summary.violations || {};

    const getStatusColor = (status) => status === 'PASS' ? 'success' : 'danger';
    const getStatusIcon = (status) => status === 'PASS' ? CheckCircle : XCircle;

    return (
        <div className="space-y-6">
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Pipeline Status"
                    value={pipelineStatus}
                    type={getStatusColor(pipelineStatus)}
                    icon={getStatusIcon(pipelineStatus)}
                />
                <StatCard
                    title="Accuracy"
                    value={`${(accuracy * 100).toFixed(1)}%`}
                    subtext={`Target: ${(passThreshold * 100)}%`}
                    type={accuracy >= passThreshold ? 'success' : 'danger'}
                    icon={Activity}
                />
                <StatCard
                    title="Total Samples"
                    value={totalSamples}
                    type="neutral"
                    icon={FileText}
                    subtext="Processed"
                />
                <StatCard
                    title="Dataset Integrity"
                    value={integrityHash ? "Verified" : "Missing"}
                    type={integrityHash ? "success" : "warning"}
                    icon={Lock}
                />
            </div>

            {/* Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">Violation Breakdown</h3>
                    <div className="space-y-4">
                        {Object.entries(violations).map(([key, count]) => (
                            <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <span className="font-medium text-gray-700">{key}</span>
                                <span className={`px-3 py-1 rounded-full text-sm font-bold ${count > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                                    {count}
                                </span>
                            </div>
                        ))}
                        {Object.keys(violations).length === 0 && <div className="text-gray-500">No data available</div>}
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">Run Metadata</h3>
                    <div className="space-y-3 text-sm">
                        <div className="flex justify-between border-b pb-2">
                            <span className="text-gray-500">Timestamp</span>
                            <span className="font-mono">{summary.timestamp || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between border-b pb-2">
                            <span className="text-gray-500">Dataset Name</span>
                            <span className="font-mono">{summary.dataset || 'Unknown'}</span>
                        </div>
                        <div className="flex justify-between border-b pb-2">
                            <span className="text-gray-500">Hash (SHA256)</span>
                            <span className="font-mono text-xs truncate max-w-[200px]">{integrityHash || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
