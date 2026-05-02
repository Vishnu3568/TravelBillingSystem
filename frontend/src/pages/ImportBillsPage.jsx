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
                    <button onClick={() => navigate("/")} className="px-6 py-2 bg-black text-white rounded-none font-bold transition hover:bg-slate-800">
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
                timeout: 600000 // 10 minutes
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
            await api.post("/bills/bulk-ai", parsedBills);
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
                                    <th className="p-4 text-xs font-black uppercase tracking-widest">Duty Slip #</th>
                                    <th className="p-4 text-xs font-black uppercase tracking-widest">Bill Date</th>
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
                                        <td className="p-4 font-bold text-slate-900">{bill.dutySlipNo || '---'}</td>
                                        <td className="p-4 text-slate-600 font-medium">{bill.billDate || '---'}</td>
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
                                    <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Duty Slip Number</label>
                                    <input 
                                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 focus:border-black focus:bg-white transition-all outline-none font-bold"
                                        value={editForm.dutySlipNo || ''} 
                                        onChange={e => setEditForm({...editForm, dutySlipNo: e.target.value})} 
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Bill Date (YYYY-MM-DD)</label>
                                    <input 
                                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 focus:border-black focus:bg-white transition-all outline-none font-bold"
                                        value={editForm.billDate || ''} 
                                        onChange={e => setEditForm({...editForm, billDate: e.target.value})} 
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
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="mx-auto max-w-5xl">
                {/* Header */}
                <div className="mb-8 flex items-end justify-between">
                    <div>
                        <nav className="flex items-center gap-2 text-sm text-slate-500 mb-2 font-medium">
                            <span>Admin</span>
                            <ChevronRight size={14} />
                            <span>AI Services</span>
                        </nav>
                        <h1 className="flex items-center gap-3 text-5xl font-black text-black tracking-tighter">
                            <Package className="text-indigo-600" size={48} />
                            Intelligent Import
                        </h1>
                        <p className="mt-3 text-slate-500 max-w-xl text-lg font-medium">
                            Upload your travel bills in Word format. Gemini AI will automatically 
                            extract data from tables and paragraphs for batch processing.
                        </p>
                    </div>
                    <button 
                        onClick={() => navigate("/bills")} 
                        className="flex items-center gap-2 rounded-none border border-slate-900 bg-white px-6 py-3 font-black text-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none"
                    >
                        <History size={20} />
                        History
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-8">
                        {/* Drop Zone */}
                        <div 
                            className="relative group border-2 border-dashed border-slate-300 bg-white p-16 text-center transition-all hover:border-black hover:bg-slate-50 shadow-sm"
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
                                accept=".docx,.doc" 
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
                                onChange={handleFileSelect} 
                            />
                            <div className="bg-black text-white w-20 h-20 rounded-none flex items-center justify-center mx-auto mb-8 group-hover:rotate-12 transition-transform">
                                <UploadCloud size={40} />
                            </div>
                            <h3 className="mb-2 text-2xl font-black text-black uppercase tracking-tight">Drop Bills Here</h3>
                            <p className="mb-8 text-slate-500 font-medium italic">Supports .doc and .docx formats</p>
                            <span className="inline-block px-8 py-3 bg-black text-white font-black uppercase tracking-widest shadow-xl hover:bg-slate-800 transition-colors">
                                Select Files
                            </span>
                        </div>

                        {/* File List */}
                        {files.length > 0 && (
                            <div className="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] animate-in fade-in slide-in-from-bottom-4 duration-300">
                                <div className="flex items-center justify-between border-b-2 border-black bg-slate-50 p-6">
                                    <h3 className="font-black text-black text-xl uppercase tracking-tighter">
                                        Batch Queue ({files.length})
                                    </h3>
                                    <button 
                                        onClick={handleUpload} 
                                        disabled={isUploading} 
                                        className="flex items-center gap-2 bg-indigo-600 px-8 py-3 font-black text-white shadow-lg hover:bg-indigo-700 disabled:opacity-50 transition-all"
                                    >
                                        {isUploading ? <Loader2 className="animate-spin" size={20} /> : <CheckCircle size={20} />}
                                        {isUploading ? "AI ANALYZING..." : "START AI PARSING"}
                                    </button>
                                </div>
                                <ul className="divide-y-2 divide-slate-100">
                                    {files.map((f) => (
                                        <li key={f.id} className="group flex items-center justify-between p-6 hover:bg-slate-50 transition-colors">
                                            <div className="flex items-center gap-4">
                                                <div className="p-3 bg-slate-900 text-white">
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
                                                className="p-2 text-slate-300 hover:text-rose-600 transition-all" 
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
                        <div className="bg-white border-2 border-black p-8 shadow-[8px_8px_0px_0px_rgba(79,70,229,1)]">
                            <h3 className="mb-6 text-2xl font-black flex items-center gap-2 uppercase tracking-tighter">
                                <Info className="text-indigo-600" size={28} />
                                AI Logic
                            </h3>
                            <ul className="space-y-6">
                                <li className="flex gap-4">
                                    <div className="w-2 h-2 bg-indigo-600 mt-2 shrink-0" />
                                    <p className="text-slate-600 font-medium text-sm leading-relaxed">
                                        <strong>Intelligent Extraction:</strong> Gemini AI reads tables, lists, and paragraphs to find bill data.
                                    </p>
                                </li>
                                <li className="flex gap-4">
                                    <div className="w-2 h-2 bg-indigo-600 mt-2 shrink-0" />
                                    <p className="text-slate-600 font-medium text-sm leading-relaxed">
                                        <strong>Anomaly Detection:</strong> Automatically flags arithmetic errors and duplicate entries.
                                    </p>
                                </li>
                                <li className="flex gap-4">
                                    <div className="w-2 h-2 bg-indigo-600 mt-2 shrink-0" />
                                    <p className="text-slate-600 font-medium text-sm leading-relaxed">
                                        <strong>Auto-Entity Creation:</strong> Creates new Companies/Vehicles if they don't exist in your DB.
                                    </p>
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
