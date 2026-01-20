import React, { useEffect, useState } from "react";
import SafetyAPI from "../api";

export default function Results({ uploadId }) {
    const [summary, setSummary] = useState(null);
    const [violations, setViolations] = useState([]);

    useEffect(() => {
        if (!uploadId) return;

        async function load() {
            try {
                // Using SafetyAPI wrapper methods
                const [s, v] = await Promise.all([
                    SafetyAPI.getSummary(uploadId),
                    SafetyAPI.getViolations(uploadId)
                ]);

                // Note: SafetyAPI.getSummary returns response.data directly (based on src/api.js implementation)
                // Let's verify src/api.js implementation:
                // getSummary: async (uploadId) => { const response = await api.get(...); return response.data; }
                // So 's' IS the data.

                setSummary(s);
                setViolations(v);
            } catch (e) {
                console.error("Failed to load results", e);
            }
        }

        load();
    }, [uploadId]);

    const [selectedImage, setSelectedImage] = useState(null);

    // Helper to construct media URL
    const getMediaUrl = (path) => {
        if (!path) return null;
        // Assuming API_URL is http://localhost:8000/api/v1
        // We want http://localhost:8000/media/{path}
        const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
        const rootUrl = apiBase.replace('/api/v1', '');
        return `${rootUrl}/media/${path}`;
    };

    if (!summary) return null;

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mt-6 space-y-6">
            <div className="flex justify-between items-center border-b pb-4">
                <h2 className="text-xl font-bold text-gray-900">Analysis Results</h2>
                <a
                    href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/results/report?upload_id=${uploadId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                >
                    Download Safety Report
                </a>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Pipeline Status</p>
                    <p className="text-xl font-bold">{summary.pipeline_status || summary.status}</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Compliance Accuracy</p>
                    <p className="text-xl font-bold text-blue-600">{summary.accuracy}%</p>
                </div>
            </div>

            <div>
                <h3 className="font-semibold text-lg mb-4">Detailed Violations</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-gray-100 text-gray-600 uppercase">
                            <tr>
                                <th className="p-3">Evidence</th>
                                <th className="p-3">File</th>
                                <th className="p-3">Type</th>
                                <th className="p-3">Severity</th>
                                <th className="p-3">Detected At</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {violations.map((v, i) => (
                                <tr key={i} className="hover:bg-gray-50">
                                    <td className="p-3">
                                        {v.image_path ? (
                                            <img
                                                src={getMediaUrl(v.image_path)}
                                                alt="Evidence"
                                                className="w-16 h-16 object-cover rounded border cursor-pointer hover:opacity-80"
                                                onClick={() => setSelectedImage(getMediaUrl(v.image_path))}
                                            />
                                        ) : (
                                            <span className="text-gray-400 text-xs text-center block w-16">No Img</span>
                                        )}
                                    </td>
                                    <td className="p-3 font-medium">{v.file_name}</td>
                                    <td className="p-3">{v.violation_type || v.type}</td>
                                    <td className="p-3">
                                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${v.severity === 'HIGH' || v.severity === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                                            v.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
                                            }`}>
                                            {v.severity || v.risk}
                                        </span>
                                    </td>
                                    <td className="p-3 text-gray-500">{new Date(v.detected_at || v.timestamp).toLocaleTimeString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {violations.length === 0 && (
                        <p className="text-center text-gray-500 py-4">No violations detected.</p>
                    )}
                </div>
            </div>

            {/* Image Modal */}
            {selectedImage && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-75" onClick={() => setSelectedImage(null)}>
                    <div className="bg-white p-2 rounded-lg max-w-4xl max-h-[90vh] overflow-auto shadow-2xl relative" onClick={e => e.stopPropagation()}>
                        <button
                            className="absolute top-2 right-2 bg-gray-200 hover:bg-gray-300 rounded-full p-1 w-8 h-8 flex items-center justify-center text-gray-700 font-bold"
                            onClick={() => setSelectedImage(null)}
                        >
                            &times;
                        </button>
                        <img src={selectedImage} alt="Evidence Full" className="max-w-full max-h-[80vh] object-contain block" />
                    </div>
                </div>
            )}
        </div>
    );
}
