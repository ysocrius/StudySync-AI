import { useState } from 'react';
import { Upload, X, Youtube, BookOpen, ArrowRight, Loader } from 'lucide-react';
import api from '../api';

export default function SourceManager({ onComplete }) {
    const [files, setFiles] = useState([]);
    const [urls, setUrls] = useState([]);
    const [urlInput, setUrlInput] = useState("");
    const [status, setStatus] = useState("idle");
    const [error, setError] = useState("");

    const handleFileChange = async (e) => {
        const newFiles = Array.from(e.target.files).filter(f => f.type === 'application/pdf');

        for (const file of newFiles) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                // Using centralized API
                await api.post('/api/upload', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                setFiles(prev => [...prev, file.name]);
            } catch (e) {
                console.error("Upload failed", e);
                // Try to extract server error message
                const msg = e.response?.data?.error || e.message;
                setError(`Failed to upload ${file.name}: ${msg}`);
            }
        }
    };

    const addUrl = () => {
        if (!urlInput.trim()) return;
        setUrls(prev => [...prev, urlInput]);
        setUrlInput("");
    };

    const startProcessing = async () => {
        if (files.length === 0 && urls.length === 0) {
            setError("Please add at least one PDF or Video.");
            return;
        }

        setStatus("processing");
        setError("");

        try {
            // 1. Kick off processing
            const res = await api.post('/api/process-sources', {
                youtube_urls: urls,
                pdf_filenames: files
            });

            if (res.status !== 202) {
                throw new Error("Processing failed");
            }

            // 2. Poll for status
            const poll = setInterval(async () => {
                try {
                    const statusRes = await api.get('/api/status');
                    const statusData = statusRes.data;

                    if (statusData.status === 'complete') {
                        clearInterval(poll);
                        setStatus("success");
                        setTimeout(() => onComplete(), 1000);
                    } else if (statusData.status === 'error') {
                        clearInterval(poll);
                        setStatus("error");
                        setError(statusData.message);
                    } else if (statusData.status === 'idle') {
                        clearInterval(poll);
                        setStatus("error");
                        setError("Server reset. Please try again.");
                    } else if (statusData.status === 'processing' || statusData.status === 'queued') {
                        const el = document.getElementById('processing-text');
                        if (el) el.innerText = statusData.message || "Processing...";
                    }
                } catch (e) {
                    console.error("Polling error", e);
                }
            }, 1000);

        } catch (e) {
            setError(e.message || "Failed to start processing");
            setStatus("error");
        }
    };

    return (
        <div className="max-w-2xl mx-auto mt-20 p-8 glass-card rounded-3xl animate-in fade-in slide-in-from-bottom-8">
            <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-blue-600 mb-2">
                Setup Knowledge Base
            </h2>
            <p className="text-gray-500 mb-8">Upload study materials to train your AI.</p>

            {/* Error Banner */}
            {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm font-medium flex items-center gap-2">
                    <X size={16} /> {error}
                </div>
            )}

            <div className="space-y-6">
                {/* PDF Uploader */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                        <BookOpen size={16} className="text-purple-600" /> Upload Textbooks (PDF)
                    </label>
                    <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 transition hover:border-purple-400 hover:bg-purple-50/50 group text-center cursor-pointer relative">
                        <input
                            type="file"
                            multiple
                            accept=".pdf"
                            onChange={handleFileChange}
                            className="absolute inset-0 opacity-0 cursor-pointer"
                        />
                        <div className="flex flex-col items-center gap-2 text-gray-400 group-hover:text-purple-600 transition">
                            <Upload size={32} />
                            <span className="text-sm font-medium">Drop PDFs here or click to browse</span>
                        </div>
                    </div>
                </div>

                {/* File List */}
                {files.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {files.map((f, i) => (
                            <span key={i} className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-gray-100 text-xs font-medium text-gray-600 border border-gray-200">
                                {f}
                                <button
                                    onClick={() => setFiles(prev => prev.filter((_, idx) => idx !== i))}
                                    className="ml-1 text-gray-400 hover:text-red-500 rounded-full p-0.5"
                                >
                                    <X size={12} />
                                </button>
                            </span>
                        ))}
                    </div>
                )}

                {/* YouTube Linker */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                        <Youtube size={16} className="text-red-500" /> Add Video Sources
                    </label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            placeholder="https://youtube.com/watch?v=..."
                            value={urlInput}
                            onChange={(e) => setUrlInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && addUrl()}
                            className="flex-1 bg-white border border-gray-200 rounded-xl px-4 py-2 focus:ring-2 focus:ring-purple-500 outline-none text-sm transition"
                        />
                        <button
                            onClick={addUrl}
                            className="bg-gray-900 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-gray-800 transition"
                        >
                            Add
                        </button>
                    </div>
                    <p className="text-xs text-gray-400 mt-2 ml-1">Note: Videos MUST have captions enabled.</p>
                </div>

                {/* URL List */}
                {urls.length > 0 && (
                    <div className="space-y-2">
                        {urls.map((u, i) => (
                            <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-xs text-gray-600 border border-gray-100">
                                <span className="truncate flex-1">{u}</span>
                                <button onClick={() => setUrls(prev => prev.filter((_, idx) => idx !== i))} className="text-gray-400 hover:text-red-500">
                                    <X size={14} />
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                <hr className="border-gray-100 my-6" />

                {/* Info Note for HR/Demo */}
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 mb-4 text-xs text-blue-700 flex items-start gap-2">
                    <span className="text-xl">💡</span>
                    <div>
                        <span className="font-semibold">Processing Speed Tip:</span>
                        <ul className="list-disc ml-4 mt-1 space-y-0.5">
                            <li><span className="font-medium">Digital PDFs</span> (Selectable text) are processed <strong>instantly</strong>.</li>
                            <li><span className="font-medium">Scanned/Image PDFs</span> require OCR and may take <strong>1-2 minutes</strong> depending on size.</li>
                        </ul>
                    </div>
                </div>

                {/* Action */}
                <button
                    onClick={startProcessing}
                    disabled={status === 'processing' || (files.length === 0 && urls.length === 0)}
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 rounded-xl font-semibold shadow-lg shadow-purple-500/30 hover:shadow-purple-500/40 hover:scale-[1.02] active:scale-[0.98] transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    {status === 'processing' ? (
                        <>
                            <Loader className="animate-spin" size={20} />
                            <span id="processing-text">Processing...</span>
                        </>
                    ) : (
                        <>
                            Start Studying <ArrowRight size={20} />
                        </>
                    )}
                </button>
            </div>
        </div>
    );
}
