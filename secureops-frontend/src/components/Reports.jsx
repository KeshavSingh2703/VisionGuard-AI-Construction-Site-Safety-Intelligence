import React, { useState } from 'react';
import { FileText, Download, Loader } from 'lucide-react';
import SafetyAPI from '../api';

const Reports = ({ summary, uploadId }) => {
    const [downloading, setDownloading] = useState(false);

    const handleDownload = async () => {
        if (!uploadId) {
            alert("No upload ID found. Cannot download report.");
            return;
        }

        setDownloading(true);
        try {
            const blob = await SafetyAPI.downloadReport(uploadId);
            // Create Blob URL
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `safety_report_${uploadId}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Download failed", err);
            alert("Failed to download report. Please check if the report exists.");
        } finally {
            setDownloading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="bg-white p-8 rounded-xl border border-gray-200 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
                    <FileText className="w-8 h-8 text-blue-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Safety Compliance Report</h2>
                <p className="text-gray-500 mb-6">Generated on {summary?.timestamp ? new Date(summary.timestamp).toLocaleString() : 'Processing...'}</p>

                <p className="text-sm text-gray-500 mb-4">
                    Download restricted to authorized personnel. ID: {uploadId || "Waiting for upload..."}
                </p>

                <button
                    onClick={handleDownload}
                    disabled={downloading || !uploadId}
                    className={`inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 
                        ${downloading || !uploadId ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
                >
                    {downloading ? (
                        <>
                            <Loader className="w-5 h-5 mr-2 animate-spin" />
                            Downloading...
                        </>
                    ) : (
                        <>
                            <Download className="w-5 h-5 mr-2" />
                            Download PDF Report
                        </>
                    )}
                </button>

                <p className="mt-4 text-xs text-gray-400">
                    MD5 Verification: {summary?.integrity_hash || 'Pending'}
                </p>
            </div>
        </div>
    );
};

export default Reports;
