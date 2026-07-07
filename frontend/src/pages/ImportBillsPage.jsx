import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
    UploadCloud, FileText, X, CheckCircle,
    AlertCircle, Loader2, Info, ChevronRight, ChevronLeft,
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
        setResults(null);
        setParsedBills([]);

        const allParsed = [];
        const updatedFiles = [...files];

        for (let i = 0; i < updatedFiles.length; i++) {
            const f = updatedFiles[i];

            // Update status to parsing
            updatedFiles[i] = { ...f, status: 'parsing', progress: 10 };
            setFiles([...updatedFiles]);

            const formData = new FormData();
            formData.append("files", f.file);

            // Simulation of progress while waiting for the AI
            const progressInterval = setInterval(() => {
                setFiles(prev => {
                    const next = [...prev];
                    if (next[i] && next[i].progress < 90) {
                        next[i].progress += 5;
                    }
                    return next;
                });
            }, 1500);

            try {
                const response = await api.post("/import/ai-parse", formData, {
                    headers: { "Content-Type": "multipart/form-data" },
                    timeout: 600000
                });

                clearInterval(progressInterval);
                allParsed.push(...response.data);

                updatedFiles[i] = { ...f, status: 'done', progress: 100 };
                setFiles([...updatedFiles]);

            } catch (error) {
                clearInterval(progressInterval);
                console.error(`Upload failed for ${f.file.name}`, error);
                updatedFiles[i] = { ...f, status: 'error', progress: 0 };
                setFiles([...updatedFiles]);
                toast.error(`${f.file.name}: Parsing failed.`);
            }
        }

        if (allParsed.length > 0) {
            setParsedBills(allParsed);
            setIsReviewing(true);
            setFiles([]);
            toast.success(`AI successfully parsed ${allParsed.length} bills!`);
        }
        setIsUploading(false);
    };

    const handleSaveAll = async () => {
        try {
            await api.post("/bills/bulk-ai", parsedBills);
            toast.success("All bills saved to database successfully!");
            setParsedBills([]);
            setIsReviewing(false);
            setResults({
                successCount: parsedBills.length,
                failureCount: 0,
                duplicateCount: 0,
                errors: []
            });
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

    const getGroupedBills = () => {
        const groups = {};
        parsedBills.forEach((bill, index) => {
            const comp = bill.companyName || "Unknown Company";
            if (!groups[comp]) {
                groups[comp] = [];
            }
            groups[comp].push({ ...bill, originalIndex: index });
        });
        return groups;
    };

    // Side-by-side states and helpers
    const [currentBillIndex, setCurrentBillIndex] = useState(0);

    const stripHtml = (html) => {
        if (!html) return "";
        const doc = new DOMParser().parseFromString(html, 'text/html');
        return doc.body.textContent || "";
    };

    const checkMismatch = (value, originalHtml) => {
        if (!value || String(value).trim() === "" || String(value).trim() === "---") return false;
        const cleanVal = String(value).toLowerCase().replace(/[-\s]/g, "").trim();
        const cleanText = stripHtml(originalHtml).toLowerCase().replace(/[-\s]/g, "").trim();
        
        if (/^\d{4}-\d{2}-\d{2}$/.test(String(value).trim())) {
            const parts = String(value).trim().split("-");
            const alternativeFormat1 = `${parts[2]}-${parts[1]}-${parts[0]}`; 
            const alternativeFormat2 = `${parts[2]}-${parts[1]}-${parts[0].slice(2)}`; 
            if (cleanText.includes(alternativeFormat1.replace(/[-\s]/g, "")) || 
                cleanText.includes(alternativeFormat2.replace(/[-\s]/g, ""))) {
                return false;
            }
        }
        return !cleanText.includes(cleanVal);
    };

    const validateBillFrontend = (bill) => {
        const warnings = [];
        if (!bill.dutySlipNo || bill.dutySlipNo.trim() === "" || bill.dutySlipNo === "---") {
            warnings.push("Missing mandatory field: Duty Slip Number");
        }
        if (!bill.companyName || bill.companyName.trim() === "" || bill.companyName === "---") {
            warnings.push("Missing mandatory field: Company Name");
        }
        if (!bill.vehicleNumber || bill.vehicleNumber.trim() === "" || bill.vehicleNumber === "---") {
            warnings.push("Missing mandatory field: Vehicle Number");
        }
        const amt = parseFloat(bill.totalAmount);
        if (!bill.totalAmount || isNaN(amt) || amt <= 0) {
            warnings.push("Total Amount is missing or zero/negative");
        }
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        if (bill.billDate && !dateRegex.test(bill.billDate)) {
            warnings.push(`Invalid date format: '${bill.billDate}'. Expected YYYY-MM-DD.`);
        }
        if (bill.tripDate && !dateRegex.test(bill.tripDate)) {
            warnings.push(`Invalid date format: '${bill.tripDate}'. Expected YYYY-MM-DD.`);
        }
        return warnings;
    };

    const parseMultiplication = (valStr) => {
        if (!valStr) return null;
        const match = String(valStr).match(/(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)/);
        if (match) {
            const val1 = parseFloat(match[1]);
            const val2 = parseFloat(match[2]);
            return val1 * val2;
        }
        return null;
    };

    const handleFieldChange = (index, field, value) => {
        setParsedBills(prev => {
            const updated = [...prev];
            const currentBill = { ...updated[index] };
            currentBill[field] = value;
            currentBill.warnings = validateBillFrontend(currentBill);
            updated[index] = currentBill;
            return updated;
        });
    };

    const handleDynamicChargeChange = (billIndex, chargeIndex, value) => {
        setParsedBills(prev => {
            const updated = [...prev];
            const currentBill = { ...updated[billIndex] };
            const updatedCharges = [...currentBill.dynamicCharges];
            updatedCharges[chargeIndex] = { ...updatedCharges[chargeIndex], amount: value };
            currentBill.dynamicCharges = updatedCharges;
            currentBill.warnings = validateBillFrontend(currentBill);
            updated[billIndex] = currentBill;
            return updated;
        });
    };

    if (isReviewing) {
        if (parsedBills.length === 0) {
            return (
                <div className="flex min-h-screen items-center justify-center bg-slate-50">
                    <div className="text-center p-8 bg-white border border-slate-200 shadow-sm max-w-md w-full">
                        <CheckCircle className="mx-auto mb-4 text-emerald-500" size={64} />
                        <h2 className="mb-2 text-2xl font-bold text-black">All Done</h2>
                        <p className="text-slate-500 mb-6">No bills remaining to review.</p>
                        <button
                            onClick={() => setIsReviewing(false)}
                            className="px-8 py-3 bg-black text-white border-2 border-black font-bold uppercase tracking-widest text-xs"
                        >
                            Upload More
                        </button>
                    </div>
                </div>
            );
        }

        const bill = parsedBills[currentBillIndex];
        const warnings = validateBillFrontend(bill);
        const hasCriticalErrors = warnings.some(w => w.includes("Missing mandatory field") || w.includes("missing or zero"));

        return (
            <div className="min-h-screen bg-slate-100 flex flex-col">
                {/* Review Header Bar */}
                <div className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between shadow-sm sticky top-0 z-40">
                    <div className="flex items-center gap-6">
                        <div>
                            <h1 className="text-2xl font-black text-black tracking-tight">Verify AI Extraction</h1>
                            <p className="text-xs text-slate-500">Compare parsed fields with the original Word document</p>
                        </div>
                    </div>
                    {/* Pagination Controls */}
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setCurrentBillIndex(prev => Math.max(0, prev - 1))}
                            disabled={currentBillIndex === 0}
                            className="p-2 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40 transition-colors"
                        >
                            <ChevronLeft size={20} />
                        </button>
                        <div className="flex items-center gap-1.5 text-sm font-bold text-slate-700">
                            Page 
                            <input 
                                type="number"
                                className="w-12 text-center border border-slate-300 py-1 font-bold outline-none focus:border-cyan-500"
                                value={currentBillIndex + 1}
                                min={1}
                                max={parsedBills.length}
                                onChange={(e) => {
                                    const val = parseInt(e.target.value);
                                    if (val >= 1 && val <= parsedBills.length) {
                                        setCurrentBillIndex(val - 1);
                                    }
                                }}
                            /> 
                            of {parsedBills.length}
                        </div>
                        <button
                            onClick={() => setCurrentBillIndex(prev => Math.min(parsedBills.length - 1, prev + 1))}
                            disabled={currentBillIndex === parsedBills.length - 1}
                            className="p-2 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40 transition-colors"
                        >
                            <ChevronRight size={20} />
                        </button>
                    </div>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => {
                                setParsedBills(prev => prev.filter((_, i) => i !== currentBillIndex));
                                if (currentBillIndex >= parsedBills.length - 1 && currentBillIndex > 0) {
                                    setCurrentBillIndex(currentBillIndex - 1);
                                }
                            }}
                            className="px-4 py-2 border border-rose-200 text-rose-600 hover:bg-rose-50 font-bold transition-all text-xs uppercase"
                        >
                            Discard
                        </button>
                        <button
                            onClick={() => setIsReviewing(false)}
                            className="px-5 py-2 border border-slate-200 font-bold text-slate-600 hover:bg-slate-50 transition-all text-xs uppercase"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSaveAll}
                            disabled={parsedBills.some(b => validateBillFrontend(b).some(w => w.includes("Missing mandatory field") || w.includes("missing or zero")))}
                            className="px-8 py-2 bg-slate-900 text-white font-bold hover:bg-slate-800 transition-all text-xs uppercase shadow-md disabled:opacity-40"
                        >
                            Save {parsedBills.length} Bills
                        </button>
                    </div>
                </div>

                {/* Validation Warnings Banner */}
                {warnings.length > 0 && (
                    <div className={`px-8 py-3 text-sm font-bold flex items-center justify-between ${hasCriticalErrors ? 'bg-rose-100 text-rose-800 border-b border-rose-200' : 'bg-amber-100 text-amber-800 border-b border-amber-200'}`}>
                        <div className="flex items-center gap-2">
                            <AlertCircle size={18} />
                            <span>{hasCriticalErrors ? "Needs Manual Review: Please correct critical missing fields before saving." : "Warnings Detected: Check highlighted mismatch fields."}</span>
                        </div>
                        <ul className="text-xs list-disc pl-5">
                            {warnings.map((w, i) => <li key={i}>{w}</li>)}
                        </ul>
                    </div>
                )}

                {/* Side-by-Side View Splitter */}
                <div className="flex-1 grid grid-cols-2 overflow-hidden h-[calc(100vh-140px)]">
                    {/* LEFT PANEL: Original Document Preview */}
                    <div className="border-r border-slate-200 bg-slate-50 flex flex-col p-6 overflow-y-auto">
                        <div className="mb-3 flex justify-between items-center text-slate-400 font-bold uppercase tracking-widest text-[10px]">
                            <span className="flex items-center gap-2">
                                Original Document Pages
                                {bill && bill.labeledDocument ? (
                                    <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-800 text-[8px] rounded font-mono font-bold normal-case">Enterprise Labeler</span>
                                ) : (
                                    <span className="px-1.5 py-0.5 bg-slate-200 text-slate-700 text-[8px] rounded font-mono font-bold normal-case">Legacy Parser</span>
                                )}
                            </span>
                            <span>Raw Word Segment Output</span>
                        </div>
                        <div 
                            className="bg-white p-8 border border-slate-200 shadow-sm rounded-none overflow-x-auto min-h-full font-sans text-xs leading-relaxed"
                            dangerouslySetInnerHTML={{ __html: bill.originalDoc || "<p className='text-slate-400'>No HTML preview available.</p>" }}
                        />
                    </div>

                    {/* RIGHT PANEL: Parsed Bill Preview (A4 Invoice Style) */}
                    <div className="bg-slate-200 p-6 overflow-y-auto flex flex-col items-center justify-start gap-4">
                        {bill && bill.validationReport && (
                            <div className="bg-white shadow-md border border-slate-300 w-[780px] p-6 flex items-center justify-between text-xs font-sans">
                                <div className="flex items-center gap-6">
                                    <div>
                                        <span className="font-bold text-slate-500 block uppercase text-[8px] tracking-wider mb-0.5">Quality Score</span>
                                        <span className="text-xl font-black text-slate-800">{Math.round(bill.validationReport.validation_summary.overall_quality_score)}/100</span>
                                    </div>
                                    <div className="h-8 w-px bg-slate-200" />
                                    <div>
                                        <span className="font-bold text-slate-500 block uppercase text-[8px] tracking-wider mb-0.5">Avg Confidence</span>
                                        <span className="text-xl font-black text-slate-800">{Math.round(bill.validationReport.validation_summary.average_confidence * 100)}%</span>
                                    </div>
                                    <div className="h-8 w-px bg-slate-200" />
                                    <div>
                                        <span className="font-bold text-slate-500 block uppercase text-[8px] tracking-wider mb-0.5">Issues Detected</span>
                                        <span className="text-xl font-black text-rose-600">{bill.validationReport.issues.length}</span>
                                    </div>
                                </div>
                                <div>
                                    <span className="font-bold text-slate-500 block uppercase text-[8px] tracking-wider text-right mb-0.5">Recommendation</span>
                                    <span className={`px-2.5 py-1.5 font-bold text-[9px] tracking-wider uppercase border rounded ${
                                        bill.validationReport.validation_summary.recommendation === "PASS" ? "bg-emerald-50 text-emerald-700 border-emerald-300" :
                                        bill.validationReport.validation_summary.recommendation === "PASS_WITH_WARNINGS" ? "bg-amber-50 text-amber-700 border-amber-300" :
                                        "bg-rose-50 text-rose-700 border-rose-300"
                                    }`}>
                                        {bill.validationReport.validation_summary.recommendation.replace(/_/g, " ")}
                                    </span>
                                </div>
                            </div>
                        )}
                        {/* A4 Portrait Paper Layout */}
                        <div className="bg-white shadow-xl p-12 border border-slate-300 w-[780px] min-h-[1050px] flex flex-col justify-between font-serif text-black relative">
                            <div>
                                {/* Header */}
                                <div className="text-center pb-4 mb-6 border-b border-slate-300">
                                    <h2 className="text-xl font-bold uppercase tracking-wider">Sri Tulja Bhavani Travels</h2>
                                    <p className="text-[10px] text-slate-500 font-sans mt-1">1-11-113/3, P2 Sai Shikara Apartments, Shayamlal Building, Begumpet, Hyderabad - 500016</p>
                                    <p className="text-[10px] text-slate-500 font-sans">Email: srituljabhavanitravels.rentacar@gmail.com</p>
                                </div>

                                {/* Bill Title & Number */}
                                <div className="flex justify-between items-start mb-6">
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-1.5">
                                            <span className="font-bold text-slate-500 font-sans uppercase text-[10px] tracking-wide">To,</span>
                                            {checkMismatch(bill.companyName, bill.originalDoc) && <AlertTriangle className="text-amber-500" size={14} />}
                                        </div>
                                        <input
                                            className={`font-black text-sm border-b border-transparent hover:border-slate-300 focus:border-cyan-500 focus:bg-slate-50 outline-none w-72 px-1 py-0.5 ${checkMismatch(bill.companyName, bill.originalDoc) ? 'bg-yellow-100' : 'bg-transparent'}`}
                                            value={bill.companyName || ""}
                                            onChange={(e) => handleFieldChange(currentBillIndex, "companyName", e.target.value)}
                                        />
                                    </div>
                                    <div className="text-right space-y-1 text-xs">
                                        <div className="flex items-center justify-end gap-1.5">
                                            <span className="font-bold text-slate-500 font-sans uppercase text-[10px] tracking-wide">Bill Date:</span>
                                            <input
                                                className={`text-right border-b border-transparent hover:border-slate-300 focus:border-cyan-500 focus:bg-slate-50 outline-none w-24 px-1 py-0.5 ${checkMismatch(bill.billDate, bill.originalDoc) ? 'bg-yellow-100' : 'bg-transparent'}`}
                                                value={bill.billDate || ""}
                                                onChange={(e) => handleFieldChange(currentBillIndex, "billDate", e.target.value)}
                                            />
                                            {checkMismatch(bill.billDate, bill.originalDoc) && <AlertTriangle className="text-amber-500" size={14} />}
                                        </div>
                                        <div className="flex items-center justify-end gap-1.5">
                                            <span className="font-bold text-slate-500 font-sans uppercase text-[10px] tracking-wide">Duty Slip:</span>
                                            <input
                                                className={`text-right border-b border-transparent hover:border-slate-300 focus:border-cyan-500 focus:bg-slate-50 outline-none w-24 px-1 py-0.5 ${checkMismatch(bill.dutySlipNo, bill.originalDoc) ? 'bg-yellow-100' : 'bg-transparent'}`}
                                                value={bill.dutySlipNo || ""}
                                                onChange={(e) => handleFieldChange(currentBillIndex, "dutySlipNo", e.target.value)}
                                            />
                                            {checkMismatch(bill.dutySlipNo, bill.originalDoc) && <AlertTriangle className="text-amber-500" size={14} />}
                                        </div>
                                    </div>
                                </div>

                                {/* Table Structure */}
                                <table className="w-full border-collapse border border-slate-400 text-xs text-left mb-6 font-sans">
                                    <thead>
                                        <tr className="bg-slate-50 text-slate-700 font-bold">
                                            <th className="border border-slate-400 p-2 text-center">Date</th>
                                            <th className="border border-slate-400 p-2">Vehicle No.</th>
                                            <th className="border border-slate-400 p-2 text-center">Total Kms</th>
                                            <th className="border border-slate-400 p-2 text-center">Total Hrs</th>
                                            <th className="border border-slate-400 p-2 text-center">Extra Kms</th>
                                            <th className="border border-slate-400 p-2 text-center">Extra Hrs</th>
                                            <th className="border border-slate-400 p-2 text-center">Amt</th>
                                            <th className="border border-slate-400 p-2 text-right">Total Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {/* Row 1: Base Package Row */}
                                        <tr>
                                            <td className="border border-slate-400 p-2 text-center">
                                                <input
                                                    className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 ${checkMismatch(bill.tripDate, bill.originalDoc) ? 'bg-yellow-100' : ''}`}
                                                    value={bill.tripDate || ""}
                                                    onChange={(e) => handleFieldChange(currentBillIndex, "tripDate", e.target.value)}
                                                />
                                            </td>
                                            <td className="border border-slate-400 p-2">
                                                <input
                                                    className={`w-full bg-transparent border-none outline-none focus:bg-slate-50 font-bold ${checkMismatch(bill.vehicleNumber, bill.originalDoc) ? 'bg-yellow-100' : ''}`}
                                                    value={bill.vehicleNumber || ""}
                                                    onChange={(e) => handleFieldChange(currentBillIndex, "vehicleNumber", e.target.value)}
                                                />
                                            </td>
                                            <td className="border border-slate-400 p-2 text-center">
                                                <input
                                                    className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 ${checkMismatch(bill.totalKms, bill.originalDoc) ? 'bg-yellow-100' : ''}`}
                                                    value={bill.totalKms || ""}
                                                    onChange={(e) => handleFieldChange(currentBillIndex, "totalKms", e.target.value)}
                                                />
                                            </td>
                                            <td className="border border-slate-400 p-2 text-center">
                                                <input
                                                    className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 ${checkMismatch(bill.totalHours, bill.originalDoc) ? 'bg-yellow-100' : ''}`}
                                                    value={bill.totalHours || ""}
                                                    onChange={(e) => handleFieldChange(currentBillIndex, "totalHours", e.target.value)}
                                                />
                                            </td>
                                            <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                            <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                            <td className="border border-slate-400 p-2 text-center">
                                                <input
                                                    className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 ${checkMismatch(bill.baseAmount, bill.originalDoc) ? 'bg-yellow-100' : ''}`}
                                                    value={bill.baseAmount || ""}
                                                    onChange={(e) => handleFieldChange(currentBillIndex, "baseAmount", e.target.value)}
                                                />
                                            </td>
                                            <td className="border border-slate-400 p-2 text-right font-bold">
                                                ₹{parseFloat(bill.baseAmount || 0).toFixed(2)}
                                            </td>
                                        </tr>

                                        {/* Row 2: Extra Kms Row (if any) */}
                                        {bill.extraKms && String(bill.extraKms).trim() !== "" && (
                                            <tr>
                                                <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                <td className="border border-slate-400 p-2 text-slate-400">Extra Kms</td>
                                                <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                <td className="border border-slate-400 p-2 text-center">
                                                    <input
                                                        className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 font-bold ${checkMismatch(bill.extraKms, bill.originalDoc) ? 'bg-yellow-100' : ''}`}
                                                        value={bill.extraKms || ""}
                                                        onChange={(e) => handleFieldChange(currentBillIndex, "extraKms", e.target.value)}
                                                    />
                                                </td>
                                                <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                <td className="border border-slate-400 p-2 text-right font-bold">
                                                    ₹{(bill.dynamicCharges?.find(c => c.name.toLowerCase() === "extra km amount")?.amount 
                                                        ? parseFloat(bill.dynamicCharges.find(c => c.name.toLowerCase() === "extra km amount").amount) 
                                                        : (parseMultiplication(bill.extraKms) || 0.0)).toFixed(2)}
                                                </td>
                                            </tr>
                                        )}

                                        {/* Row 3: Extra Hours Row (if any) */}
                                        {bill.extraHours && String(bill.extraHours).trim() !== "" && (
                                            <tr>
                                                <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                <td className="border border-slate-400 p-2 text-slate-400">Extra Hours</td>
                                                <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                <td className="border border-slate-400 p-2 text-center">
                                                    <input
                                                        className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 font-bold ${checkMismatch(bill.extraHours, bill.originalDoc) ? 'bg-yellow-100' : ''}`}
                                                        value={bill.extraHours || ""}
                                                        onChange={(e) => handleFieldChange(currentBillIndex, "extraHours", e.target.value)}
                                                    />
                                                </td>
                                                <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                <td className="border border-slate-400 p-2 text-right font-bold">
                                                    ₹{(bill.dynamicCharges?.find(c => c.name.toLowerCase() === "extra hour amount")?.amount 
                                                        ? parseFloat(bill.dynamicCharges.find(c => c.name.toLowerCase() === "extra hour amount").amount) 
                                                        : (parseMultiplication(bill.extraHours) || 0.0)).toFixed(2)}
                                                </td>
                                            </tr>
                                        )}

                                        {/* Row 4: Dynamic/Hardcoded Charges Rows */}
                                        {bill.dynamicCharges && bill.dynamicCharges.map((charge, chargeIdx) => {
                                            if (charge.name.toLowerCase().includes("extra km") || charge.name.toLowerCase().includes("extra hour")) {
                                                return null; // Displayed inside the structured rows above
                                            }
                                            return (
                                                <tr key={chargeIdx}>
                                                    <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                    <td className="border border-slate-400 p-2">{charge.name}</td>
                                                    <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                    <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                    <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                    <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                    <td className="border border-slate-400 p-2 text-center text-slate-400">---</td>
                                                    <td className="border border-slate-400 p-2 text-right">
                                                        <input
                                                            type="text"
                                                            className={`w-20 text-right bg-transparent border-none outline-none focus:bg-slate-50 font-bold ${checkMismatch(charge.amount, bill.originalDoc) ? 'bg-yellow-100' : ''}`}
                                                            value={charge.amount || ""}
                                                            onChange={(e) => handleDynamicChargeChange(currentBillIndex, chargeIdx, e.target.value)}
                                                        />
                                                    </td>
                                                </tr>
                                            );
                                        })}

                                        {/* Grand Total Row */}
                                        <tr className="bg-slate-100 font-bold">
                                            <td colSpan={7} className="border border-slate-400 p-2 text-right uppercase tracking-wider text-[10px]">Grand Total</td>
                                            <td className="border border-slate-400 p-2 text-right text-sm">
                                                <span className="mr-1">₹</span>
                                                <input
                                                    type="number"
                                                    className={`w-24 text-right bg-transparent border-none outline-none font-black ${checkMismatch(bill.totalAmount, bill.originalDoc) ? 'bg-yellow-100' : ''}`}
                                                    value={bill.totalAmount || 0}
                                                    onChange={(e) => handleFieldChange(currentBillIndex, "totalAmount", e.target.value)}
                                                />
                                                {checkMismatch(bill.totalAmount, bill.originalDoc) && <AlertTriangle className="inline text-amber-500 ml-1" size={14} />}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>

                                {/* Guest & Booker details */}
                                <div className="grid grid-cols-2 gap-6 text-xs mb-6 font-sans">
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-1.5">
                                            <span className="font-bold text-slate-500 uppercase text-[9px] tracking-wider block">Guest Name:</span>
                                            {checkMismatch(bill.contactPerson, bill.originalDoc) && <AlertTriangle className="text-amber-500" size={14} />}
                                        </div>
                                        <input
                                            className={`font-semibold border-b border-transparent hover:border-slate-300 focus:border-cyan-500 focus:bg-slate-50 outline-none w-full px-1 py-0.5 ${checkMismatch(bill.contactPerson, bill.originalDoc) ? 'bg-yellow-100' : 'bg-transparent'}`}
                                            value={bill.contactPerson || ""}
                                            onChange={(e) => handleFieldChange(currentBillIndex, "contactPerson", e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-1.5">
                                            <span className="font-bold text-slate-500 uppercase text-[9px] tracking-wider block">Booked By:</span>
                                            {checkMismatch(bill.bookedBy, bill.originalDoc) && <AlertTriangle className="text-amber-500" size={14} />}
                                        </div>
                                        <input
                                            className={`font-semibold border-b border-transparent hover:border-slate-300 focus:border-cyan-500 focus:bg-slate-50 outline-none w-full px-1 py-0.5 ${checkMismatch(bill.bookedBy, bill.originalDoc) ? 'bg-yellow-100' : 'bg-transparent'}`}
                                            value={bill.bookedBy || ""}
                                            onChange={(e) => handleFieldChange(currentBillIndex, "bookedBy", e.target.value)}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Signatures & Footer */}
                            <div>
                                <div className="flex justify-between items-end border-t border-slate-300 pt-8 mt-12">
                                    <div className="space-y-4">
                                        <div className="w-32 border-b border-slate-300"></div>
                                        <p className="text-[10px] text-slate-400 font-sans">Guest Signature</p>
                                    </div>
                                    <div className="text-right space-y-4">
                                        <p className="font-bold">For Sri Tulja Bhavani Travels</p>
                                        <div className="w-32 border-b border-slate-300 inline-block"></div>
                                        <p className="text-[10px] text-slate-400 font-sans block mt-1">Authorised Signatory</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
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
                                                    <div className="flex items-center gap-3">
                                                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest whitespace-nowrap">
                                                            {(f.file.size / 1024).toFixed(1)} KB • {f.status}
                                                        </p>
                                                        {f.status === 'parsing' && (
                                                            <div className="w-32 h-1.5 bg-slate-100 rounded-none overflow-hidden border border-slate-200">
                                                                <div
                                                                    className="h-full bg-cyan-500 transition-all duration-500 ease-out"
                                                                    style={{ width: `${f.progress}%` }}
                                                                />
                                                            </div>
                                                        )}
                                                        {f.status === 'done' && (
                                                            <CheckCircle size={14} className="text-emerald-500" />
                                                        )}
                                                        {f.status === 'error' && (
                                                            <AlertCircle size={14} className="text-red-500" />
                                                        )}
                                                    </div>
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
