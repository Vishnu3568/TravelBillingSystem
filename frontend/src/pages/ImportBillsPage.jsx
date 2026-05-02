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
                <div className="text-center p-8 bg-white rounded-none shadow-xl border border-slate-100">
                    <AlertTriangle className="mx-auto mb-4 text-amber-500" size={64} />
                    <h2 className="mb-2 text-2xl font-bold text-black">Access Restricted</h2>
                    <p className="text-slate-500 mb-6">Bulk bill import is an administrative feature reserved for owners.</p>
                    <button
                        onClick={() => navigate("/")}
                        className="px-8 py-3 bg-cyan-500 text-black border-2 border-black rounded-none font-bold uppercase tracking-widest text-xs shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:bg-black hover:text-white transition-all active:translate-x-0.5 active:translate-y-0.5 active:shadow-none"
                    >
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
        <div className="p-6 bg-slate-50 min-h-screen text-black">
            <div className="max-w-7xl mx-auto">
                <div className="mb-10">
                    <h1 className="text-4xl font-bold tracking-tight flex items-center gap-3">
                        <Package className="text-cyan-600" size={36} />
                        Bulk Bill Import
                    </h1>
                    <p className="mt-2 text-slate-500">
                        Upload multiple .docx travel bills. The system will automatically extract data,
                        create missing companies/vehicles, and link them to your bill history.
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column: Upload */}
                    <div className="lg:col-span-2 flex flex-col">
                        {/* Drop Zone */}
                        <div
                            className="relative group flex-1 flex flex-col items-center justify-center rounded-none border-2 border-dashed border-slate-300 bg-white p-12 text-center transition-all hover:border-cyan-400 hover:bg-cyan-50/30 shadow-sm min-h-[270px]"
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
                            <div className="bg-cyan-100 text-cyan-600 w-16 h-16 rounded-none flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
                                <UploadCloud size={32} />
                            </div>
                            <h3 className="mb-2 text-xl font-bold text-black">Drop your bills here</h3>
                            <p className="mb-6 text-slate-500">Only .docx files are accepted for bulk processing</p>
                            <span className="inline-block px-8 py-3 bg-cyan-500 text-black border-2 border-black rounded-none font-bold text-xs uppercase tracking-widest shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:bg-black hover:text-white transition-all">
                                Browse Files
                            </span>
                        </div>

                        {/* File List */}
                        {files.length > 0 && (
                            <div className="overflow-hidden rounded-none border border-slate-200 bg-white shadow-xl animate-in fade-in slide-in- duration-300">
                                <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/80 p-5">
                                    <div>
                                        <h3 className="font-bold text-slate-800 flex items-center gap-2">
                                            Files Queued
                                            <span className="px-2 py-0.5 bg-slate-200 text-slate-700 text-xs rounded-none">
                                                {files.length}
                                            </span>
                                        </h3>
                                    </div>
                                    <button
                                        onClick={handleUpload}
                                        disabled={isUploading}
                                        className="flex items-center gap-2 rounded-none bg-black px-6 py-2.5 font-bold text-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:bg-cyan-500 hover:text-black transition-all active:translate-x-0.5 active:translate-y-0.5 active:shadow-none disabled:opacity-50"
                                    >
                                        {isUploading ? <Loader2 className="animate-spin" size={20} /> : <UploadCloud size={20} />}
                                        {isUploading ? "Processing..." : "Upload & Process"}
                                    </button>
                                </div>
                                <ul className="max-h-[500px] divide-y divide-slate-100 overflow-y-auto">
                                    {files.map((f) => (
                                        <li key={f.id} className="group flex items-center justify-between p-5 transition hover:bg-slate-50/50">
                                            <div className="flex items-center gap-4">
                                                <div className="p-3 bg-cyan-50 text-cyan-500 rounded-none">
                                                    <FileText size={24} />
                                                </div>
                                                <div>
                                                    <p className="font-bold text-slate-700">{f.file.name}</p>
                                                    <p className="text-sm text-slate-400">{(f.file.size / 1024).toFixed(1)} KB • Queued</p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => removeFile(f.id)}
                                                className="rounded-none p-2 text-slate-400 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-50 hover:text-red-500"
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
                            <div className="rounded-none border border-slate-200 bg-white p-6 shadow-xl animate-in zoom-in-95 duration-300">
                                <h3 className="mb-6 text-xl font-bold text-black flex items-center gap-2">
                                    Import Summary
                                </h3>

                                <div className="space-y-4">
                                    <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-none border border-emerald-100 text-emerald-800">
                                        <div className="flex items-center gap-3">
                                            <CheckCircle size={20} />
                                            <span className="font-bold">Successful</span>
                                        </div>
                                        <span className="text-xl font-black">{results.successCount || 0}</span>
                                    </div>

                                    <div className="flex items-center justify-between p-4 bg-amber-50 rounded-none border border-amber-100 text-amber-800">
                                        <div className="flex items-center gap-3">
                                            <Info size={20} />
                                            <span className="font-bold">Duplicates</span>
                                        </div>
                                        <span className="text-xl font-black">{results.duplicateCount || 0}</span>
                                    </div>

                                    <div className="flex items-center justify-between p-4 bg-red-50 rounded-none border border-red-100 text-red-800">
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
                                        <ul className="text-sm text-red-600 bg-red-50/50 p-4 rounded-none space-y-1 max-h-40 overflow-y-auto">
                                            {results.errors.map((err, i) => <li key={i}>• {err}</li>)}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Instructions */}
                        <div className="rounded-none bg-black p-8 text-white shadow-2xl border-l-4 border-cyan-500">
                            <h3 className="mb-6 text-xl font-bold flex items-center gap-2 uppercase tracking-widest">
                                <Info className="text-cyan-400" size={24} />
                                Guidelines
                            </h3>
                            <ul className="space-y-5">
                                <li className="relative pl-6 text-sm text-slate-300 leading-relaxed">
                                    <div className="absolute left-0 top-2 w-2 h-2 bg-cyan-500" />
                                    Ensure all files are in <span className="text-cyan-400 font-bold">.docx</span> format.
                                </li>
                                <li className="relative pl-6 text-sm text-slate-300 leading-relaxed">
                                    <div className="absolute left-0 top-2 w-2 h-2 bg-cyan-500" />
                                    Data is extracted from the <span className="text-cyan-400 font-bold">first table</span> in the document.
                                </li>
                                <li className="relative pl-6 text-sm text-slate-300 leading-relaxed">
                                    <div className="absolute left-0 top-2 w-2 h-2 bg-cyan-500" />
                                    System automatically creates new <span className="text-cyan-400 font-bold">Companies</span> and <span className="text-cyan-400 font-bold">Vehicles</span> if they don't exist.
                                </li>
                                <li className="relative pl-6 text-sm text-slate-300 leading-relaxed">
                                    <div className="absolute left-0 top-2 w-2 h-2 bg-cyan-500" />
                                    Duplicates are skipped automatically based on the <span className="text-cyan-400 font-bold">Duty Slip Number</span>.
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
