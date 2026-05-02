import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
    UploadCloud, FileText, X, CheckCircle,
    AlertCircle, Loader2, Info, ChevronRight,
    AlertTriangle, History, Package, Save, Edit2, Trash2
} from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import { toast } from 'sonner';

export default function ImportBillsPage() {
    const { role } = useAuth();
    const navigate = useNavigate();
    const [files, setFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [parsedBills, setParsedBills] = useState([]);
    const [isReviewing, setIsReviewing] = useState(false);
    const [editingIndex, setEditingIndex] = useState(null);
    const [editForm, setEditForm] = useState(null);
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
            (file) => file.name.endsWith(".docx") || file.name.endsWith(".doc")
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

        const formData = new FormData();
        files.forEach((f) => {
            formData.append("files", f.file);
        });

        try {
            const response = await api.post("/import/ai-parse", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            setParsedBills(response.data);
            setIsReviewing(true);
            setFiles([]);
            toast.success(`AI successfully parsed ${response.data.length} bills!`);
        } catch (error) {
            console.error("Upload failed", error);
            toast.error(error.response?.data?.message || "AI parsing failed.");
        } finally {
            setIsUploading(false);
        }
    };

    const handleSaveAll = async () => {
        try {
            await api.post("/bills/bulk", parsedBills);
            toast.success("All bills saved to database successfully!");
            setParsedBills([]);
            setIsReviewing(false);
        } catch (error) {
            toast.error("Failed to save bills to database");
        }
    };

    const startEdit = (index) => {
        setEditingIndex(index);
        setEditForm({ ...parsedBills[index] });
    };

    const saveEdit = () => {
        const updated = [...parsedBills];
        updated[editingIndex] = editForm;
        setParsedBills(updated);
        setEditingIndex(null);
        toast.success("Bill updated locally");
    };

    const deleteBill = (index) => {
        setParsedBills(prev => prev.filter((_, i) => i !== index));
    };

    if (isReviewing) {
        return (
            <div className="min-h-screen bg-slate-50 p-8">
                <div className="mx-auto max-w-7xl">
                    <div className="mb-8 flex items-center justify-between bg-white p-8 border border-slate-200 shadow-sm">
                        <div>
                            <h1 className="text-3xl font-black text-black tracking-tight">Review AI Extraction</h1>
                            <p className="text-slate-500 mt-1">Verify {parsedBills.length} bills before committing to the database</p>
                        </div>
                        <div className="flex gap-4">
                            <button 
                                onClick={() => setIsReviewing(false)}
                                className="px-6 py-3 border border-slate-200 font-bold text-slate-600 hover:bg-slate-50 transition-all"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={handleSaveAll}
                                className="px-8 py-3 bg-black text-white font-bold shadow-xl hover:bg-slate-800 transition-all flex items-center gap-2"
                            >
                                <Save size={18} />
                                Save {parsedBills.length} Bills
                            </button>
                        </div>
                    </div>

                    <div className="bg-white border border-slate-200 shadow-xl overflow-hidden">
                        <table className="w-full text-left">
                            <thead className="bg-slate-900 text-white">
                                <tr>
                                    <th className="p-4 text-xs font-black uppercase tracking-widest">Bill #</th>
                                    <th className="p-4 text-xs font-black uppercase tracking-widest">Date</th>
                                    <th className="p-4 text-xs font-black uppercase tracking-widest">Company</th>
                                    <th className="p-4 text-xs font-black uppercase tracking-widest">Vehicle</th>
                                    <th className="p-4 text-xs font-black uppercase tracking-widest text-right">Amount</th>
                                    <th className="p-4 text-xs font-black uppercase tracking-widest">Issues</th>
                                    <th className="p-4 text-xs font-black uppercase tracking-widest text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {parsedBills.map((bill, index) => (
                                    <tr 
                                        key={index} 
                                        className={`hover:bg-slate-50 transition-colors ${bill.warnings?.length > 0 ? 'bg-amber-50/50' : ''}`}
                                    >
                                        <td className="p-4 font-bold text-slate-900">{bill.billNumber || '---'}</td>
                                        <td className="p-4 text-slate-600 font-medium">{bill.date || '---'}</td>
                                        <td className="p-4 text-slate-600 font-medium">{bill.companyName || '---'}</td>
                                        <td className="p-4 text-slate-500 text-sm">
                                            <span className="font-bold text-slate-700">{bill.vehicleNumber}</span>
                                            <br />
                                            {bill.vehicleType}
                                        </td>
                                        <td className="p-4 text-right font-black text-slate-900">₹{bill.totalAmount?.toLocaleString()}</td>
                                        <td className="p-4">
                                            {bill.warnings?.map((w, i) => (
                                                <div key={i} className="flex items-center gap-1.5 text-amber-700 text-[10px] bg-amber-100 px-2 py-1 mb-1 font-bold last:mb-0">
                                                    <AlertTriangle size={12} />
                                                    {w}
                                                </div>
                                            ))}
                                        </td>
                                        <td className="p-4 text-right">
                                            <div className="flex justify-end gap-2">
                                                <button 
                                                    onClick={() => startEdit(index)}
                                                    className="p-2 text-indigo-600 hover:bg-indigo-50 border border-transparent hover:border-indigo-100 transition-all"
                                                >
                                                    <Edit2 size={16} />
                                                </button>
                                                <button 
                                                    onClick={() => deleteBill(index)}
                                                    className="p-2 text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-100 transition-all"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Edit Modal */}
                {editingIndex !== null && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-white shadow-2xl w-full max-w-2xl animate-in zoom-in-95 duration-200">
                            <div className="px-8 py-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                                <h3 className="text-xl font-black text-black uppercase tracking-tight">Manual Data Correction</h3>
                                <button onClick={() => setEditingIndex(null)} className="text-slate-400 hover:text-black transition-colors"><X size={24} /></button>
                            </div>
                            <div className="p-8 grid grid-cols-2 gap-8">
                                <div className="space-y-2">
                                    <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Bill Number</label>
                                    <input 
                                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 focus:border-black focus:bg-white transition-all outline-none font-bold"
                                        value={editForm.billNumber || ''} 
                                        onChange={e => setEditForm({...editForm, billNumber: e.target.value})} 
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Date</label>
                                    <input 
                                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 focus:border-black focus:bg-white transition-all outline-none font-bold"
                                        value={editForm.date || ''} 
                                        onChange={e => setEditForm({...editForm, date: e.target.value})} 
                                    />
                                </div>
                                <div className="space-y-2 col-span-2">
                                    <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Company Name</label>
                                    <input 
                                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 focus:border-black focus:bg-white transition-all outline-none font-bold"
                                        value={editForm.companyName || ''} 
                                        onChange={e => setEditForm({...editForm, companyName: e.target.value})} 
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Vehicle Number</label>
                                    <input 
                                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 focus:border-black focus:bg-white transition-all outline-none font-bold"
                                        value={editForm.vehicleNumber || ''} 
                                        onChange={e => setEditForm({...editForm, vehicleNumber: e.target.value})} 
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Total Amount</label>
                                    <input 
                                        type="number"
                                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 focus:border-black focus:bg-white transition-all outline-none font-black text-xl"
                                        value={editForm.totalAmount || 0} 
                                        onChange={e => setEditForm({...editForm, totalAmount: parseFloat(e.target.value)})} 
                                    />
                                </div>
                            </div>
                            <div className="px-8 py-6 bg-slate-50 border-t border-slate-100 flex justify-end gap-4">
                                <button onClick={() => setEditingIndex(null)} className="px-6 py-3 border border-slate-200 font-bold hover:bg-white transition-all">Cancel</button>
                                <button onClick={saveEdit} className="px-10 py-3 bg-indigo-600 text-white font-bold hover:bg-indigo-700 shadow-xl shadow-indigo-100 transition-all">Apply Fix</button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    }

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
                                const dropped = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith(".docx") || f.name.endsWith(".doc"));
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
                                        {isUploading ? <Loader2 className="animate-spin" size={20} /> : <CheckCircle size={20} />}
                                        {isUploading ? "AI ANALYZING..." : "START AI PARSING"}
                                    </button>
                                </div>
                                <ul className="divide-y-2 divide-slate-100">
                                    {files.map((f) => (
                                        <li key={f.id} className="group flex items-center justify-between p-6 hover:bg-slate-50 transition-colors">
                                            <div className="flex items-center gap-4">
                                                <div className="p-3 bg-cyan-50 text-cyan-500 rounded-none">
                                                    <FileText size={24} />
                                                </div>
                                                <div>
                                                    <p className="font-black text-slate-800">{f.file.name}</p>
                                                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                                                        {(f.file.size / 1024).toFixed(1)} KB • READY
                                                    </p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => removeFile(f.id)}
                                                className="rounded-none p-2 text-slate-400 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-50 hover:text-red-500"
                                                disabled={isUploading}
                                            >
                                                <X size={24} />
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>

                    {/* Right Column: Instructions */}
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

                        <div className="bg-indigo-600 p-8 text-white">
                            <h4 className="font-black text-xl mb-2 uppercase tracking-widest">Support</h4>
                            <p className="text-indigo-100 text-sm font-medium">
                                Having trouble? Ensure your Word files have clear tables or structured paragraphs. AI works best with standard agency layouts.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
