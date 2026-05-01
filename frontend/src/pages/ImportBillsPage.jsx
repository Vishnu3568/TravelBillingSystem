import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { 
    UploadCloud, FileText, X, CheckCircle, 
    AlertCircle, Loader2, Info, ChevronRight,
    AlertTriangle, History, Package
} from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function ImportBillsPage() {
    const { role } = useAuth();
    const navigate = useNavigate();
    const [files, setFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [results, setResults] = useState(null);
    const fileInputRef = useRef(null);

    if (role !== "OWNER") {
        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-50">
                <div className="text-center p-8 bg-white rounded-2xl shadow-xl border border-slate-100">
                    <AlertTriangle className="mx-auto mb-4 text-amber-500" size={64} />
                    <h2 className="mb-2 text-2xl font-bold text-slate-900">Access Restricted</h2>
                    <p className="text-slate-500 mb-6">Bulk bill import is an administrative feature reserved for owners.</p>
                    <button onClick={() => navigate("/")} className="px-6 py-2 bg-slate-900 text-white rounded-lg font-bold transition hover:bg-slate-800">
                        Go Home
                    </button>
                </div>
            </div>
        );
    }

    const handleFileSelect = (e) => {
        const selected = Array.from(e.target.files).filter(
            (file) => file.name.endsWith(".docx")
        );
        const newFiles = selected.map(file => ({
            file,
            id: Math.random().toString(36).substr(2, 9),
            status: 'queued'
        }));
        setFiles((prev) => [...prev, ...newFiles]);
    };

    const removeFile = (id) => {
        setFiles((prev) => prev.filter((f) => f.id !== id));
    };

    const handleUpload = async () => {
        if (files.length === 0) return;
        setIsUploading(true);
        setResults(null);

        const formData = new FormData();
        files.forEach((f) => {
            formData.append("files", f.file);
        });

        try {
            const response = await api.post("/import/bills", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            setResults(response.data);
            setFiles([]);
        } catch (error) {
            console.error("Upload failed", error);
            setResults({ 
                success: false, 
                message: error.response?.data?.message || "Critical failure during import." 
            });
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="mx-auto max-w-5xl">
                {/* Header */}
                <div className="mb-8 flex items-end justify-between">
                    <div>
                        <nav className="flex items-center gap-2 text-sm text-slate-500 mb-2">
                            <span>Admin</span>
                            <ChevronRight size={14} />
                            <span>System</span>
                        </nav>
                        <h1 className="flex items-center gap-3 text-4xl font-extrabold text-slate-900 tracking-tight">
                            <Package className="text-indigo-600" size={40} />
                            Bulk Bill Import
                        </h1>
                        <p className="mt-2 text-slate-500 max-w-xl">
                            Upload multiple .docx travel bills. The system will automatically extract data, 
                            create missing companies/vehicles, and link them to your bill history.
                        </p>
                    </div>
                    <button 
                        onClick={() => navigate("/bills")} 
                        className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-2.5 font-bold text-slate-700 shadow-sm transition hover:bg-slate-50"
                    >
                        <History size={18} />
                        View Bill History
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column: Upload */}
                    <div className="lg:col-span-2 space-y-8">
                        {/* Drop Zone */}
                        <div 
                            className="relative group rounded-3xl border-2 border-dashed border-slate-300 bg-white p-12 text-center transition-all hover:border-indigo-400 hover:bg-indigo-50/30 shadow-sm"
                            onDragOver={(e) => e.preventDefault()}
                            onDrop={(e) => {
                                e.preventDefault();
                                const dropped = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith(".docx"));
                                const newFiles = dropped.map(file => ({
                                    file,
                                    id: Math.random().toString(36).substr(2, 9),
                                    status: 'queued'
                                }));
                                setFiles(prev => [...prev, ...newFiles]);
                            }}
                        >
                            <input 
                                type="file" 
                                multiple 
                                accept=".docx" 
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
                                onChange={handleFileSelect} 
                            />
                            <div className="bg-indigo-100 text-indigo-600 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
                                <UploadCloud size={32} />
                            </div>
                            <h3 className="mb-2 text-xl font-bold text-slate-900">Drop your bills here</h3>
                            <p className="mb-6 text-slate-500">Only .docx files are accepted for bulk processing</p>
                            <span className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold text-sm shadow-md">
                                Browse Files
                            </span>
                        </div>

                        {/* File List */}
                        {files.length > 0 && (
                            <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl animate-in fade-in slide-in-from-bottom-4 duration-300">
                                <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/80 p-5">
                                    <div>
                                        <h3 className="font-bold text-slate-800 flex items-center gap-2">
                                            Files Queued
                                            <span className="px-2 py-0.5 bg-slate-200 text-slate-700 text-xs rounded-full">
                                                {files.length}
                                            </span>
                                        </h3>
                                    </div>
                                    <button 
                                        onClick={handleUpload} 
                                        disabled={isUploading} 
                                        className="flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-2.5 font-bold text-white shadow-lg shadow-emerald-200 transition hover:bg-emerald-700 hover:shadow-emerald-300 disabled:opacity-50 disabled:shadow-none"
                                    >
                                        {isUploading ? <Loader2 className="animate-spin" size={20} /> : <UploadCloud size={20} />}
                                        {isUploading ? "Processing..." : "Upload & Process"}
                                    </button>
                                </div>
                                <ul className="max-h-[500px] divide-y divide-slate-100 overflow-y-auto">
                                    {files.map((f) => (
                                        <li key={f.id} className="group flex items-center justify-between p-5 transition hover:bg-slate-50/50">
                                            <div className="flex items-center gap-4">
                                                <div className="p-3 bg-indigo-50 text-indigo-500 rounded-xl">
                                                    <FileText size={24} />
                                                </div>
                                                <div>
                                                    <p className="font-bold text-slate-700">{f.file.name}</p>
                                                    <p className="text-sm text-slate-400">{(f.file.size / 1024).toFixed(1)} KB • Queued</p>
                                                </div>
                                            </div>
                                            <button 
                                                onClick={() => removeFile(f.id)} 
                                                className="rounded-xl p-2 text-slate-400 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-50 hover:text-red-500" 
                                                disabled={isUploading}
                                            >
                                                <X size={20} />
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>

                    {/* Right Column: Information & Results */}
                    <div className="space-y-8">
                        {/* Results Summary */}
                        {results && (
                            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl animate-in zoom-in-95 duration-300">
                                <h3 className="mb-6 text-xl font-bold text-slate-900 flex items-center gap-2">
                                    Import Summary
                                </h3>
                                
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-2xl border border-emerald-100 text-emerald-800">
                                        <div className="flex items-center gap-3">
                                            <CheckCircle size={20} />
                                            <span className="font-bold">Successful</span>
                                        </div>
                                        <span className="text-xl font-black">{results.successCount || 0}</span>
                                    </div>
                                    
                                    <div className="flex items-center justify-between p-4 bg-amber-50 rounded-2xl border border-amber-100 text-amber-800">
                                        <div className="flex items-center gap-3">
                                            <Info size={20} />
                                            <span className="font-bold">Duplicates</span>
                                        </div>
                                        <span className="text-xl font-black">{results.duplicateCount || 0}</span>
                                    </div>

                                    <div className="flex items-center justify-between p-4 bg-red-50 rounded-2xl border border-red-100 text-red-800">
                                        <div className="flex items-center gap-3">
                                            <AlertCircle size={20} />
                                            <span className="font-bold">Failed</span>
                                        </div>
                                        <span className="text-xl font-black">{results.failureCount || 0}</span>
                                    </div>
                                </div>

                                {results.errors && results.errors.length > 0 && (
                                    <div className="mt-6">
                                        <p className="text-xs font-bold text-slate-400 uppercase mb-3">Error Details</p>
                                        <ul className="text-sm text-red-600 bg-red-50/50 p-4 rounded-2xl space-y-1 max-h-40 overflow-y-auto">
                                            {results.errors.map((err, i) => <li key={i}>• {err}</li>)}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Instructions */}
                        <div className="rounded-3xl bg-slate-900 p-8 text-white shadow-2xl">
                            <h3 className="mb-4 text-xl font-bold flex items-center gap-2">
                                <Info className="text-indigo-400" size={24} />
                                Guidelines
                            </h3>
                            <ul className="space-y-4 text-slate-300 text-sm">
                                <li className="flex gap-3">
                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                                    Ensure all files are in <strong>.docx</strong> format.
                                </li>
                                <li className="flex gap-3">
                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                                    Data is extracted from the <strong>first table</strong> in the document.
                                </li>
                                <li className="flex gap-3">
                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                                    System automatically creates new <strong>Companies</strong> and <strong>Vehicles</strong> if not found.
                                </li>
                                <li className="flex gap-3">
                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                                    Duplicates are skipped based on <strong>Duty Slip Number</strong>.
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
