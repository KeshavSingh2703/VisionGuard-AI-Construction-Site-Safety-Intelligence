import React, { useState, useEffect } from "react";
import { Upload as UploadIcon, FileText, Image as ImageIcon, Video as VideoIcon, ArrowLeft, Loader2, CheckCircle, XCircle } from "lucide-react";
import SafetyAPI from "../api";

const SelectionCard = ({ type, icon, label, desc, limit, onSelect }) => {
    const Icon = icon;
    return (
        <button
            onClick={() => onSelect(type)}
            className="flex flex-col items-center justify-center p-6 bg-white border-2 border-slate-100 rounded-xl hover:border-blue-500 hover:shadow-md transition-all group text-center"
        >
            <div className="p-4 bg-slate-50 rounded-full mb-4 group-hover:bg-blue-50 transition-colors">
                <Icon className="w-8 h-8 text-slate-600 group-hover:text-blue-600" />
            </div>
            <h3 className="font-semibold text-slate-900 mb-1">{label}</h3>
            <p className="text-sm text-slate-500 mb-2">{desc}</p>
            <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-1 rounded">
                Max {limit}
            </span>
        </button>
    );
};

const UploadView = ({ selectedType, status, error, files, handleBack, handleFileSelect, handleUpload, onUploadComplete, uploadId, setStatus }) => {
    const config = {
        image: { accept: "image/*", label: "Upload Image", icon: ImageIcon },
        pdf: { accept: "application/pdf", label: "Upload Site Plan (PDF)", icon: FileText },
        video: { accept: "video/*", label: "Upload Site Video", icon: VideoIcon }
    }[selectedType];

    const isProcessing = status === "UPLOADING" || status === "PROCESSING";
    // Removed unused isCompleted

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center gap-3 bg-slate-50/50">
                <button
                    onClick={handleBack}
                    disabled={isProcessing}
                    className="p-2 hover:bg-slate-200 rounded-full transition-colors disabled:opacity-30"
                >
                    <ArrowLeft className="w-5 h-5 text-slate-600" />
                </button>
                <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                    {config.label}
                </h3>
            </div>

            <div className="p-8">
                {/* Status State Visuals */}
                {status === "PROCESSING" && (
                    <div className="text-center py-8">
                        <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
                        <h4 className="text-lg font-medium text-slate-900">Processing...</h4>
                        <p className="text-slate-500">Analyzing safety violations</p>
                    </div>
                )}

                {status === "COMPLETED" && (
                    <div className="text-center py-8">
                        <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                        <h4 className="text-lg font-medium text-slate-900">Analysis Complete!</h4>
                        <p className="text-slate-500 mb-6">Redirecting to results...</p>
                        <button onClick={() => onUploadComplete(uploadId)} className="text-blue-600 hover:underline">
                            View Results Now
                        </button>
                    </div>
                )}

                {status === "FAILED" && (
                    <div className="text-center py-8">
                        <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                        <h4 className="text-lg font-medium text-slate-900">Analysis Failed</h4>
                        <p className="text-red-500 mb-6">{error || "Unknown error occurred"}</p>
                        <button
                            onClick={() => setStatus("IDLE")}
                            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium transition-colors"
                        >
                            Try Again
                        </button>
                    </div>
                )}

                {/* Input State */}
                {(status === "IDLE" || status === "UPLOADING") && (
                    <div className="space-y-6">
                        <div className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${files.length ? 'border-blue-300 bg-blue-50/30' : 'border-slate-300 hover:border-blue-400'
                            }`}>
                            <input
                                type="file"
                                id="file-upload"
                                className="hidden"
                                accept={config.accept}
                                onChange={handleFileSelect}
                                disabled={status === "UPLOADING"}
                            />
                            <label htmlFor="file-upload" className="cursor-pointer block">
                                <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <config.icon className="w-6 h-6" />
                                </div>
                                {files.length > 0 ? (
                                    <div>
                                        <p className="font-medium text-slate-900">{files[0].name}</p>
                                        <p className="text-sm text-slate-500 mt-1">
                                            {(files[0].size / (1024 * 1024)).toFixed(2)} MB
                                        </p>
                                    </div>
                                ) : (
                                    <div>
                                        <p className="font-medium text-slate-700">Click to select file</p>
                                        <p className="text-sm text-slate-400 mt-1">Supported: {config.accept}</p>
                                    </div>
                                )}
                            </label>
                        </div>

                        {error && (
                            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg flex items-center gap-2">
                                <XCircle className="w-4 h-4" />
                                {error}
                            </div>
                        )}

                        <button
                            onClick={handleUpload}
                            disabled={!files.length || status === "UPLOADING"}
                            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-all flex items-center justify-center gap-2"
                        >
                            {status === "UPLOADING" ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Uploading...
                                </>
                            ) : (
                                <>
                                    <UploadIcon className="w-5 h-5" />
                                    Start Analysis
                                </>
                            )}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default function Upload({ onUploadComplete }) {
    const [selectedType, setSelectedType] = useState(null); // 'image' | 'pdf' | 'video' | null
    const [files, setFiles] = useState([]);
    const [status, setStatus] = useState("IDLE"); // IDLE, UPLOADING, PROCESSING, COMPLETED, FAILED
    const [uploadId, setUploadId] = useState(null);
    const [error, setError] = useState(null);

    // Reset state when switching types
    const handleTypeSelect = (type) => {
        setSelectedType(type);
        setFiles([]);
        setStatus("IDLE");
        setError(null);
        setUploadId(null);
    };

    const handleBack = () => {
        if (status === "UPLOADING" || status === "PROCESSING") return;
        setSelectedType(null);
        setFiles([]);
        setStatus("IDLE");
        setError(null);
        setUploadId(null);
    };

    const validateFiles = (selected, type) => {
        const LIMITS = {
            image: { size: 10, ext: ['jpg', 'jpeg', 'png', 'bmp'], mime: 'image/' },
            pdf: { size: 50, ext: ['pdf'], mime: 'application/pdf' },
            video: { size: 100, ext: ['mp4', 'mov', 'avi', 'mkv'], mime: 'video/' }
        };

        const rule = LIMITS[type];
        if (!rule) return "Unknown type";

        if (selected.length > 1) return "Please select only one file";

        const file = selected[0];

        // Size check
        if (file.size > rule.size * 1024 * 1024) {
            return `File size exceeds ${rule.size}MB limit`;
        }

        // Extension/Type check (Basic)
        // Note: MIME type check can be unreliable cross-browser, but good first line.
        // We rely on backend for strict check, but frontend should give fast feedback.
        if (type === 'pdf' && file.type !== 'application/pdf') return "Invalid PDF file";
        if (type === 'image' && !file.type.startsWith('image/')) return "Invalid image file";
        if (type === 'video' && !file.type.startsWith('video/')) return "Invalid video file";

        return null;
    };

    const handleFileSelect = (e) => {
        const selected = Array.from(e.target.files);
        if (selected.length === 0) return;

        const err = validateFiles(selected, selectedType);
        if (err) {
            setError(err);
            return;
        }
        setError(null);
        setFiles(selected);
    };

    const handleUpload = async () => {
        if (!files.length || !selectedType) return;

        setStatus("UPLOADING");
        setError(null);

        try {
            // Explicitly pass selectedType to API
            const data = await SafetyAPI.upload(files, selectedType);
            setUploadId(data.video_id);
            setStatus("PROCESSING");
        } catch (err) {
            console.error("Upload Error:", err);
            let msg = "Upload failed";
            if (err.response) {
                msg = `Server Error: ${err.response.data.detail || err.response.status}`;
            } else if (err.message) {
                msg = err.message;
            }
            setError(msg);
            setStatus("FAILED");
        }
    };

    // Polling Logic
    useEffect(() => {
        if (!uploadId) return;
        // Don't poll if failed immediately
        if (status === "FAILED") return;

        const interval = setInterval(async () => {
            try {
                const data = await SafetyAPI.getStatus(uploadId);
                const s = data.status.toUpperCase();

                // Only update status if it changed, to avoid flickers/re-renders if needed
                // But for simple string it's fine.
                // Map backend status to UI status
                if (s === "PENDING" || s === "PROCESSING") {
                    setStatus("PROCESSING");
                } else if (s === "COMPLETED") {
                    setStatus("COMPLETED");
                    clearInterval(interval);
                    if (onUploadComplete) onUploadComplete(uploadId);
                } else if (s === "FAILED") {
                    setStatus("FAILED");
                    setError("Processing failed on server.");
                    clearInterval(interval);
                }
            } catch (err) {
                console.error("Polling error", err);
                // Don't fail immediately on one polling error, might be transient network
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [uploadId, status, onUploadComplete]);

    if (selectedType) {
        return (
            <UploadView
                selectedType={selectedType}
                status={status}
                error={error}
                files={files}
                handleBack={handleBack}
                handleFileSelect={handleFileSelect}
                handleUpload={handleUpload}
                onUploadComplete={onUploadComplete}
                uploadId={uploadId}
                setStatus={setStatus}
            />
        );
    }

    return (
        <div className="mb-8">
            <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                <UploadIcon className="w-6 h-6 text-blue-600" />
                New Safety Inspection
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <SelectionCard
                    type="image"
                    icon={ImageIcon}
                    label="Single Image"
                    desc="Instant PPE & Hazard Check"
                    limit="10MB"
                    onSelect={handleTypeSelect}
                />
                <SelectionCard
                    type="pdf"
                    icon={FileText}
                    label="Site Plan PDF"
                    desc="Document Analysis & Rules"
                    limit="50MB"
                    onSelect={handleTypeSelect}
                />
                <SelectionCard
                    type="video"
                    icon={VideoIcon}
                    label="Site Video"
                    desc="Full Temporal Analysis"
                    limit="100MB"
                    onSelect={handleTypeSelect}
                />
            </div>
        </div>
    );
}
