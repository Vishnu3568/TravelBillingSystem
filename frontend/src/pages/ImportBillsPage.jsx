import React, { useState, useRef, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
    UploadCloud, FileText, X, CheckCircle,
    AlertCircle, Loader2, Info, ChevronRight, ChevronLeft,
    AlertTriangle, History, Package, Save, Edit2, Trash2,
    ZoomIn, ZoomOut, Maximize2, Search, RotateCcw,
    Check, Filter, Undo, Redo, ShieldAlert, BadgeCheck
} from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import { toast } from 'sonner';

export default function ImportBillsPage() {
    const { role, username } = useAuth();
    const navigate = useNavigate();
    const [files, setFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [parsedBills, setParsedBills] = useState([]);
    const [originalBills, setOriginalBills] = useState([]);
    const [isReviewing, setIsReviewing] = useState(false);
    const [editingIndex, setEditingIndex] = useState(null);
    const [editForm, setEditForm] = useState(null);
    const [results, setResults] = useState(null);
    const fileInputRef = useRef(null);

    // Review Workspace States
    const [selectedField, setSelectedField] = useState(null);
    const [zoom, setZoom] = useState(1.0);
    const [docSearchQuery, setDocSearchQuery] = useState("");
    const [undoStack, setUndoStack] = useState([]);
    const [redoStack, setRedoStack] = useState([]);
    const [rightTab, setRightTab] = useState("fields"); // "fields", "history", "validation"
    const [filterType, setFilterType] = useState("all"); // "all", "errors", "warnings", "lowConfidence", "edited", "required"
    const [changeHistory, setChangeHistory] = useState({}); // { [billIndex]: [ { field, oldValue, newValue, timestamp, user, reason } ] }
    const [reviewStatuses, setReviewStatuses] = useState({}); // { [billIndex]: { status: "Draft", reviewer: "owner", time: null } }

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
            setOriginalBills(JSON.parse(JSON.stringify(allParsed)));
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

    // Mapped friendly names for 26 fields
    const FIELD_NAMES = {
        companyName: "Company Name",
        billNumber: "Bill Number",
        billDate: "Bill Date",
        dutySlipNo: "Duty Slip No",
        tripDate: "Trip Date",
        vehicleNumber: "Vehicle Number",
        vehicleType: "Vehicle Type",
        acNonAc: "AC / Non-AC",
        totalKms: "Total KMs",
        totalHours: "Total Hours",
        extraKms: "Extra KMs",
        extraHours: "Extra Hours",
        tripType: "Trip Type",
        pricingType: "Pricing Type",
        baseAmount: "Base Amount",
        driverBata: "Driver Bata",
        parking: "Parking Charges",
        toll: "Toll Charges",
        nightCharges: "Night Charges",
        otherCharges: "Other Charges",
        notes: "Notes / Details",
        contactPerson: "Guest Name",
        bookedBy: "Booked By",
        managerName: "Manager Name",
        totalAmount: "Grand Total"
    };

    const FIELD_TO_LABEL_MAP = {
        companyName: "HEADER_COMPANY",
        billNumber: "HEADER_BILL_NUMBER",
        billDate: "HEADER_DATE",
        dutySlipNo: "HEADER_DUTY_SLIP",
        tripDate: "TRIP_DATE",
        vehicleNumber: "VEHICLE_NUMBER",
        vehicleType: "VEHICLE_TYPE",
        acNonAc: "AC_NON_AC",
        totalKms: "TOTAL_KMS",
        totalHours: "TOTAL_HOURS",
        extraKms: "EXTRA_KM_FORMULA",
        extraHours: "EXTRA_HOUR_FORMULA",
        tripType: "TRIP_TYPE",
        pricingType: "PRICING_TYPE",
        baseAmount: "BASE_PACKAGE",
        driverBata: "DRIVER_BATA",
        parking: "PARKING",
        toll: "TOLL",
        nightCharges: "NIGHT_CHARGES",
        otherCharges: "OTHER_CHARGE",
        notes: "NOTES",
        contactPerson: "GUEST_NAME",
        bookedBy: "BOOKED_BY",
        managerName: "MANAGER_NAME",
        totalAmount: "TOTAL_AMOUNT"
    };

    // Helper to evaluate multiplications
    const _evalMultiplication = (text) => {
        if (!text) return null;
        const match = String(text).match(/(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)/);
        if (match) {
            return parseFloat(match[1]) * parseFloat(match[2]);
        }
        return null;
    };

    // Workspace change triggers
    const updateBillField = (field, newValue, reason = "Manual correction") => {
        // Push state to undo stack
        setUndoStack(prev => [...prev, JSON.stringify(parsedBills)]);
        setRedoStack([]);

        const oldVal = parsedBills[currentBillIndex][field];

        setParsedBills(prev => {
            const updated = [...prev];
            const currentBill = { ...updated[currentBillIndex] };
            currentBill[field] = newValue;
            updated[currentBillIndex] = currentBill;
            return updated;
        });

        setChangeHistory(prev => {
            const billHist = prev[currentBillIndex] || [];
            const updatedHist = [
                ...billHist,
                {
                    field,
                    oldValue: oldVal ?? "None",
                    newValue: newValue ?? "None",
                    timestamp: new Date().toLocaleTimeString(),
                    user: username || "Reviewer",
                    reason
                }
            ];
            return { ...prev, [currentBillIndex]: updatedHist };
        });

        updateReviewStatus("Reviewed");
    };

    const updateDynamicChargeField = (chargeIdx, newValue, reason = "Manual correction") => {
        setUndoStack(prev => [...prev, JSON.stringify(parsedBills)]);
        setRedoStack([]);

        const oldVal = parsedBills[currentBillIndex].dynamicCharges[chargeIdx].amount;
        const name = parsedBills[currentBillIndex].dynamicCharges[chargeIdx].name;

        setParsedBills(prev => {
            const updated = [...prev];
            const currentBill = { ...updated[currentBillIndex] };
            const updatedCharges = [...currentBill.dynamicCharges];
            updatedCharges[chargeIdx] = { ...updatedCharges[chargeIdx], amount: newValue };
            currentBill.dynamicCharges = updatedCharges;
            updated[currentBillIndex] = currentBill;
            return updated;
        });

        setChangeHistory(prev => {
            const billHist = prev[currentBillIndex] || [];
            const updatedHist = [
                ...billHist,
                {
                    field: `Charge: ${name}`,
                    oldValue: oldVal ?? "None",
                    newValue: newValue ?? "None",
                    timestamp: new Date().toLocaleTimeString(),
                    user: username || "Reviewer",
                    reason
                }
            ];
            return { ...prev, [currentBillIndex]: updatedHist };
        });

        updateReviewStatus("Reviewed");
    };

    const triggerUndo = () => {
        if (undoStack.length === 0) return;
        const nextUndo = [...undoStack];
        const prevState = nextUndo.pop();

        setRedoStack(prev => [...prev, JSON.stringify(parsedBills)]);
        setParsedBills(JSON.parse(prevState));
        setUndoStack(nextUndo);
        toast.info("Undo applied");
    };

    const triggerRedo = () => {
        if (redoStack.length === 0) return;
        const nextRedo = [...redoStack];
        const nextState = nextRedo.pop();

        setUndoStack(prev => [...prev, JSON.stringify(parsedBills)]);
        setParsedBills(JSON.parse(nextState));
        setRedoStack(nextRedo);
        toast.info("Redo applied");
    };

    const triggerReset = () => {
        if (window.confirm("Reset this bill to original AI-extracted values?")) {
            setUndoStack(prev => [...prev, JSON.stringify(parsedBills)]);
            setRedoStack([]);
            setParsedBills(prev => {
                const updated = [...prev];
                updated[currentBillIndex] = { ...originalBills[currentBillIndex] };
                return updated;
            });
            setChangeHistory(prev => ({ ...prev, [currentBillIndex]: [] }));
            updateReviewStatus("Draft");
            toast.info("Bill reset to original values");
        }
    };

    const updateReviewStatus = (status) => {
        setReviewStatuses(prev => ({
            ...prev,
            [currentBillIndex]: {
                status,
                reviewer: username || "Reviewer",
                time: new Date().toLocaleTimeString()
            }
        }));
    };

    // Left Panel document click sync
    const handleDocClick = (e) => {
        const cell = e.target.closest('td');
        if (cell) {
            const row = cell.closest('tr');
            const table = cell.closest('table');
            if (row && table) {
                const trs = Array.from(table.querySelectorAll('tr'));
                const rowIndex = trs.indexOf(row);

                const tds = Array.from(row.querySelectorAll('td'));
                const colIndex = tds.indexOf(cell);

                const tables = Array.from(e.currentTarget.querySelectorAll('table'));
                const tableIndex = tables.indexOf(table) + 1;

                const matchedEl = parsedBills[currentBillIndex]?.labeledDocument?.elements.find(el => {
                    const coords = el.coordinates || {};
                    return coords.table_number === tableIndex &&
                           coords.row_index === rowIndex &&
                           coords.column_index === colIndex;
                });

                if (matchedEl) {
                    const field = Object.keys(FIELD_TO_LABEL_MAP).find(k => FIELD_TO_LABEL_MAP[k] === matchedEl.label);
                    if (field) {
                        setSelectedField(field);
                        toast.success(`Focused field: ${FIELD_NAMES[field]}`);
                        const inpEl = document.getElementById(`input-${field}`);
                        if (inpEl) inpEl.focus();
                    }
                }
            }
        }
    };

    // Sync highlights on left panel HTML DOM
    useEffect(() => {
        if (!isReviewing || parsedBills.length === 0) return;
        const viewer = document.getElementById("docx-viewer-content");
        if (!viewer) return;

        // Clear previous outlines
        viewer.querySelectorAll(".workspace-highlight").forEach(el => {
            el.style.outline = "none";
            el.style.backgroundColor = "transparent";
            el.classList.remove("workspace-highlight");
        });

        if (!selectedField) return;
        const label = FIELD_TO_LABEL_MAP[selectedField];
        if (!label) return;

        const currentBill = parsedBills[currentBillIndex];
        const matchedEl = currentBill?.labeledDocument?.elements.find(el => el.label === label);
        if (matchedEl && matchedEl.coordinates) {
            const coords = matchedEl.coordinates;
            if (coords.table_number !== undefined) {
                const tables = viewer.querySelectorAll("table");
                const table = tables[coords.table_number - 1];
                if (table) {
                    const rows = table.querySelectorAll("tr");
                    const row = rows[coords.row_index];
                    if (row) {
                        const cells = row.querySelectorAll("td");
                        const cell = cells[coords.column_index];
                        if (cell) {
                            const isError = currentBill.validationReport?.issues.some(iss => iss.field === label && iss.severity === "ERROR");
                            cell.style.outline = isError ? "3px solid #ef4444" : "3px solid #06b6d4";
                            cell.style.backgroundColor = isError ? "rgba(239, 68, 68, 0.15)" : "rgba(6, 182, 212, 0.15)";
                            cell.classList.add("workspace-highlight");
                            cell.scrollIntoView({ behavior: "smooth", block: "center" });
                        }
                    }
                }
            }
        }
    }, [selectedField, currentBillIndex, isReviewing, parsedBills]);

    // Search highlights
    const getSearchedHtml = () => {
        let html = parsedBills[currentBillIndex]?.originalDoc || "";
        if (!docSearchQuery.trim()) return html;
        try {
            const escaped = docSearchQuery.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
            const regex = new RegExp(`(${escaped})`, 'gi');
            return html.replace(/(>[^<]+<)/g, (match) => {
                return match.replace(regex, '<mark class="bg-yellow-300 text-black">$1</mark>');
            });
        } catch (e) {
            return html;
        }
    };

    // Keyboard Shortcuts
    useEffect(() => {
        if (!isReviewing) return;
        const handleKeyDown = (e) => {
            // Undo: Ctrl + Z
            if (e.ctrlKey && e.key === "z") {
                e.preventDefault();
                triggerUndo();
            }
            // Redo: Ctrl + Y
            if (e.ctrlKey && e.key === "y") {
                e.preventDefault();
                triggerRedo();
            }
            // Save: Ctrl + S
            if (e.ctrlKey && e.key === "s") {
                e.preventDefault();
                toast.success("Draft saved successfully");
            }
            // Zoom In: Ctrl + Plus
            if (e.ctrlKey && e.key === "=") {
                e.preventDefault();
                setZoom(prev => Math.min(1.8, prev + 0.1));
            }
            // Zoom Out: Ctrl + Minus
            if (e.ctrlKey && e.key === "-") {
                e.preventDefault();
                setZoom(prev => Math.max(0.5, prev - 0.1));
            }
            // Next Error: Alt + N
            if (e.altKey && e.key === "n") {
                e.preventDefault();
                focusNextIssue();
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isReviewing, parsedBills, currentBillIndex, undoStack, redoStack]);

    const focusNextIssue = () => {
        const report = parsedBills[currentBillIndex]?.validationReport;
        if (!report || !report.issues.length) return;
        const errorFields = report.issues.map(iss => {
            return Object.keys(FIELD_TO_LABEL_MAP).find(k => FIELD_TO_LABEL_MAP[k] === iss.field);
        }).filter(Boolean);
        if (errorFields.length) {
            const nextIdx = (errorFields.indexOf(selectedField) + 1) % errorFields.length;
            const nextField = errorFields[nextIdx];
            setSelectedField(nextField);
            const inpEl = document.getElementById(`input-${nextField}`);
            if (inpEl) inpEl.focus();
            toast.info(`Focused issue: ${FIELD_NAMES[nextField]}`);
        }
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
        const statusMeta = reviewStatuses[currentBillIndex] || { status: "Draft", reviewer: "None", time: "N/A" };
        const warnings = validateBillFrontend(bill);
        const hasCriticalErrors = warnings.some(w => w.includes("Missing mandatory field") || w.includes("missing or zero"));

        return (
            <div className="min-h-screen bg-slate-100 flex flex-col font-sans text-black">
                {/* 1. Header Bar */}
                <div className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between shadow-sm sticky top-0 z-40">
                    <div className="flex items-center gap-6">
                        <div>
                            <h1 className="text-2xl font-black text-black tracking-tight flex items-center gap-2">
                                <BadgeCheck className="text-cyan-600 animate-pulse" size={24} />
                                Enterprise Review Workspace
                            </h1>
                            <p className="text-xs text-slate-500">Cross-examine layout formats, labels, calculations, and validation rules</p>
                        </div>
                    </div>

                    {/* Pagination */}
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => {
                                setCurrentBillIndex(prev => Math.max(0, prev - 1));
                                setSelectedField(null);
                            }}
                            disabled={currentBillIndex === 0}
                            className="p-1.5 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40 transition-colors cursor-pointer"
                        >
                            <ChevronLeft size={16} />
                        </button>
                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                            Invoice 
                            <input 
                                type="number"
                                className="w-10 text-center border border-slate-300 py-0.5 font-bold outline-none focus:border-cyan-500"
                                value={currentBillIndex + 1}
                                min={1}
                                max={parsedBills.length}
                                onChange={(e) => {
                                    const val = parseInt(e.target.value);
                                    if (val >= 1 && val <= parsedBills.length) {
                                        setCurrentBillIndex(val - 1);
                                        setSelectedField(null);
                                    }
                                }}
                            /> 
                            of {parsedBills.length}
                        </div>
                        <button
                            onClick={() => {
                                setCurrentBillIndex(prev => Math.min(parsedBills.length - 1, prev + 1));
                                setSelectedField(null);
                            }}
                            disabled={currentBillIndex === parsedBills.length - 1}
                            className="p-1.5 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40 transition-colors cursor-pointer"
                        >
                            <ChevronRight size={16} />
                        </button>
                    </div>

                    {/* Workflow status and actions */}
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1.5 bg-slate-100 px-3 py-1 text-xs border border-slate-200">
                            <span className="font-bold text-slate-500">Status:</span>
                            <select
                                className="bg-transparent font-black uppercase text-[10px] outline-none text-slate-800"
                                value={statusMeta.status}
                                onChange={(e) => updateReviewStatus(e.target.value)}
                            >
                                <option value="Draft">Draft</option>
                                <option value="Reviewed">Reviewed</option>
                                <option value="Approved">Approved</option>
                                <option value="Rejected">Rejected</option>
                            </select>
                        </div>

                        <button
                            onClick={triggerReset}
                            className="px-3.5 py-1.5 border border-slate-300 font-bold hover:bg-slate-50 transition-all text-[10px] uppercase flex items-center gap-1"
                        >
                            <RotateCcw size={12} />
                            Reset
                        </button>

                        <button
                            onClick={() => {
                                setParsedBills(prev => prev.filter((_, i) => i !== currentBillIndex));
                                if (currentBillIndex >= parsedBills.length - 1 && currentBillIndex > 0) {
                                    setCurrentBillIndex(currentBillIndex - 1);
                                }
                                setSelectedField(null);
                            }}
                            className="px-3.5 py-1.5 border border-rose-200 text-rose-600 hover:bg-rose-50 font-bold transition-all text-[10px] uppercase flex items-center gap-1"
                        >
                            <Trash2 size={12} />
                            Discard
                        </button>

                        <button
                            onClick={handleSaveAll}
                            disabled={parsedBills.some(b => validateBillFrontend(b).some(w => w.includes("Missing mandatory field") || w.includes("missing or zero")))}
                            className="px-6 py-2 bg-slate-900 text-white font-bold hover:bg-cyan-500 hover:text-black transition-all text-xs uppercase shadow-md disabled:opacity-40 flex items-center gap-1.5"
                        >
                            <Save size={14} />
                            Save {parsedBills.length} Bills
                        </button>
                    </div>
                </div>

                {/* 2. Three-Panel Layout */}
                <div className="flex-1 grid grid-cols-3 overflow-hidden h-[calc(100vh-73px)]">
                    
                    {/* LEFT PANEL: Original Word Document Viewer */}
                    <div className="border-r border-slate-200 bg-slate-50 flex flex-col overflow-hidden">
                        <div className="px-5 py-3.5 border-b border-slate-200 bg-white flex items-center justify-between">
                            <span className="font-bold text-slate-500 uppercase text-[10px] tracking-wider">Left Panel: Document Viewer</span>
                            {/* Zoom & Search Controls */}
                            <div className="flex items-center gap-2">
                                <button onClick={() => setZoom(prev => Math.max(0.5, prev - 0.1))} className="p-1 border border-slate-200 hover:bg-slate-50"><ZoomOut size={14} /></button>
                                <span className="text-[10px] font-bold text-slate-600">{Math.round(zoom * 100)}%</span>
                                <button onClick={() => setZoom(prev => Math.min(1.8, prev + 0.1))} className="p-1 border border-slate-200 hover:bg-slate-50"><ZoomIn size={14} /></button>
                                <button onClick={() => setZoom(1.0)} className="p-1 border border-slate-200 hover:bg-slate-50 text-[9px] font-bold uppercase px-1.5">Fit</button>
                            </div>
                        </div>

                        {/* Search in Left Document */}
                        <div className="px-4 py-2 border-b border-slate-100 bg-slate-100/50 relative flex items-center">
                            <Search className="absolute left-7 text-slate-400" size={14} />
                            <input
                                type="text"
                                placeholder="Search document text..."
                                className="w-full pl-9 pr-4 py-1 text-xs border border-slate-200 bg-white outline-none focus:border-cyan-500"
                                value={docSearchQuery}
                                onChange={(e) => setDocSearchQuery(e.target.value)}
                            />
                        </div>

                        {/* Document Content Wrapper */}
                        <div className="flex-1 overflow-auto p-6" onClick={handleDocClick}>
                            <div 
                                id="docx-viewer-content"
                                className="bg-white p-8 border border-slate-200 shadow-sm font-sans text-xs leading-relaxed transition-all duration-300"
                                style={{ transform: `scale(${zoom})`, transformOrigin: 'top left', width: `${100 / zoom}%` }}
                                dangerouslySetInnerHTML={{ __html: getSearchedHtml() }}
                            />
                        </div>
                    </div>

                    {/* CENTER PANEL: A4 Portrait Bill Preview */}
                    <div className="border-r border-slate-200 bg-slate-200 flex flex-col overflow-hidden items-center">
                        <div className="w-full px-5 py-3.5 border-b border-slate-200 bg-white flex items-center justify-between">
                            <span className="font-bold text-slate-500 uppercase text-[10px] tracking-wider">Center Panel: A4 Invoice Layout</span>
                            {/* Undo / Redo */}
                            <div className="flex items-center gap-1">
                                <button 
                                    onClick={triggerUndo} 
                                    disabled={undoStack.length === 0}
                                    className="p-1 border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
                                    title="Undo (Ctrl+Z)"
                                >
                                    <Undo size={14} />
                                </button>
                                <button 
                                    onClick={triggerRedo} 
                                    disabled={redoStack.length === 0}
                                    className="p-1 border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
                                    title="Redo (Ctrl+Y)"
                                >
                                    <Redo size={14} />
                                </button>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto w-full p-6 flex flex-col items-center justify-start gap-4">
                            {/* A4 sheet */}
                            <div className="bg-white shadow-xl p-10 border border-slate-300 w-[640px] min-h-[850px] flex flex-col justify-between font-serif text-black relative scale-95 origin-top">
                                <div>
                                    {/* Company header */}
                                    <div className="text-center pb-4 mb-4 border-b border-slate-200">
                                        <h2 className="text-lg font-black uppercase tracking-wider">Sri Tulja Bhavani Travels</h2>
                                        <p className="text-[9px] text-slate-500 font-sans mt-0.5">1-11-113/3, P2 Sai Shikara Apartments, Shayamlal Building, Begumpet, Hyderabad - 500016</p>
                                    </div>

                                    {/* Bill info */}
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="space-y-1">
                                            <span className="font-bold text-slate-500 font-sans uppercase text-[9px] tracking-wide block">To,</span>
                                            <input
                                                id="input-companyName"
                                                className={`font-black text-xs border-b border-transparent hover:border-slate-300 focus:border-cyan-500 focus:bg-slate-50 outline-none w-56 px-1 py-0.5 ${selectedField === "companyName" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : 'bg-transparent'}`}
                                                value={bill.companyName || ""}
                                                onFocus={() => setSelectedField("companyName")}
                                                onChange={(e) => updateBillField("companyName", e.target.value)}
                                            />
                                        </div>
                                        <div className="text-right space-y-0.5 text-[10px]">
                                            <div className="flex items-center justify-end gap-1">
                                                <span className="font-bold text-slate-500 font-sans uppercase text-[9px] tracking-wide">Bill Date:</span>
                                                <input
                                                    id="input-billDate"
                                                    className={`text-right border-b border-transparent hover:border-slate-300 focus:border-cyan-500 focus:bg-slate-50 outline-none w-20 px-1 py-0.5 ${selectedField === "billDate" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : 'bg-transparent'}`}
                                                    value={bill.billDate || ""}
                                                    onFocus={() => setSelectedField("billDate")}
                                                    onChange={(e) => updateBillField("billDate", e.target.value)}
                                                />
                                            </div>
                                            <div className="flex items-center justify-end gap-1">
                                                <span className="font-bold text-slate-500 font-sans uppercase text-[9px] tracking-wide">Duty Slip:</span>
                                                <input
                                                    id="input-dutySlipNo"
                                                    className={`text-right border-b border-transparent hover:border-slate-300 focus:border-cyan-500 focus:bg-slate-50 outline-none w-20 px-1 py-0.5 ${selectedField === "dutySlipNo" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : 'bg-transparent'}`}
                                                    value={bill.dutySlipNo || ""}
                                                    onFocus={() => setSelectedField("dutySlipNo")}
                                                    onChange={(e) => updateBillField("dutySlipNo", e.target.value)}
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Table grid */}
                                    <table className="w-full border-collapse border border-slate-300 text-[10px] text-left mb-4 font-sans">
                                        <thead>
                                            <tr className="bg-slate-50 text-slate-700 font-bold border-b border-slate-300">
                                                <th className="border-r border-slate-300 p-1.5 text-center">Date</th>
                                                <th className="border-r border-slate-300 p-1.5">Vehicle No.</th>
                                                <th className="border-r border-slate-300 p-1.5 text-center">Total Kms</th>
                                                <th className="border-r border-slate-300 p-1.5 text-center">Total Hrs</th>
                                                <th className="border-r border-slate-300 p-1.5 text-center">Extra Kms</th>
                                                <th className="border-r border-slate-300 p-1.5 text-center">Extra Hrs</th>
                                                <th className="border-r border-slate-300 p-1.5 text-center">Amt</th>
                                                <th className="p-1.5 text-right">Total Amount</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {/* Row 1: Base Package Row */}
                                            <tr className="border-b border-slate-300">
                                                <td className="border-r border-slate-300 p-1.5 text-center">
                                                    <input
                                                        id="input-tripDate"
                                                        className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 ${selectedField === "tripDate" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : ''}`}
                                                        value={bill.tripDate || ""}
                                                        onFocus={() => setSelectedField("tripDate")}
                                                        onChange={(e) => updateBillField("tripDate", e.target.value)}
                                                    />
                                                </td>
                                                <td className="border-r border-slate-300 p-1.5">
                                                    <input
                                                        id="input-vehicleNumber"
                                                        className={`w-full bg-transparent border-none outline-none focus:bg-slate-50 font-bold ${selectedField === "vehicleNumber" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : ''}`}
                                                        value={bill.vehicleNumber || ""}
                                                        onFocus={() => setSelectedField("vehicleNumber")}
                                                        onChange={(e) => updateBillField("vehicleNumber", e.target.value)}
                                                    />
                                                </td>
                                                <td className="border-r border-slate-300 p-1.5 text-center">
                                                    <input
                                                        id="input-totalKms"
                                                        className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 ${selectedField === "totalKms" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : ''}`}
                                                        value={bill.totalKms || ""}
                                                        onFocus={() => setSelectedField("totalKms")}
                                                        onChange={(e) => updateBillField("totalKms", e.target.value)}
                                                    />
                                                </td>
                                                <td className="border-r border-slate-300 p-1.5 text-center">
                                                    <input
                                                        id="input-totalHours"
                                                        className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 ${selectedField === "totalHours" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : ''}`}
                                                        value={bill.totalHours || ""}
                                                        onFocus={() => setSelectedField("totalHours")}
                                                        onChange={(e) => updateBillField("totalHours", e.target.value)}
                                                    />
                                                </td>
                                                <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                <td className="border-r border-slate-300 p-1.5 text-center">
                                                    <input
                                                        id="input-baseAmount"
                                                        className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 ${selectedField === "baseAmount" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : ''}`}
                                                        value={bill.baseAmount || ""}
                                                        onFocus={() => setSelectedField("baseAmount")}
                                                        onChange={(e) => updateBillField("baseAmount", e.target.value)}
                                                    />
                                                </td>
                                                <td className="p-1.5 text-right font-bold">
                                                    ₹{parseFloat(bill.baseAmount || 0).toFixed(2)}
                                                </td>
                                            </tr>

                                            {/* Row 2: Extra Kms Row (if any) */}
                                            {bill.extraKms && String(bill.extraKms).trim() !== "" && (
                                                <tr className="border-b border-slate-300">
                                                    <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                    <td className="border-r border-slate-300 p-1.5 text-slate-400">Extra Kms</td>
                                                    <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                    <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                    <td className="border-r border-slate-300 p-1.5 text-center">
                                                        <input
                                                            id="input-extraKms"
                                                            className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 font-bold ${selectedField === "extraKms" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : ''}`}
                                                            value={bill.extraKms || ""}
                                                            onFocus={() => setSelectedField("extraKms")}
                                                            onChange={(e) => updateBillField("extraKms", e.target.value)}
                                                        />
                                                    </td>
                                                    <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                    <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                    <td className="p-1.5 text-right font-bold">
                                                        ₹{(bill.dynamicCharges?.find(c => c.name.toLowerCase() === "extra km amount")?.amount 
                                                            ? parseFloat(bill.dynamicCharges.find(c => c.name.toLowerCase() === "extra km amount").amount) 
                                                            : (_evalMultiplication(bill.extraKms) || 0.0)).toFixed(2)}
                                                    </td>
                                                </tr>
                                            )}

                                            {/* Row 3: Extra Hours Row (if any) */}
                                            {bill.extraHours && String(bill.extraHours).trim() !== "" && (
                                                <tr className="border-b border-slate-300">
                                                    <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                    <td className="border-r border-slate-300 p-1.5 text-slate-400">Extra Hours</td>
                                                    <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                    <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                    <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                    <td className="border-r border-slate-300 p-1.5 text-center">
                                                        <input
                                                            id="input-extraHours"
                                                            className={`w-full text-center bg-transparent border-none outline-none focus:bg-slate-50 font-bold ${selectedField === "extraHours" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : ''}`}
                                                            value={bill.extraHours || ""}
                                                            onFocus={() => setSelectedField("extraHours")}
                                                            onChange={(e) => updateBillField("extraHours", e.target.value)}
                                                        />
                                                    </td>
                                                    <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                    <td className="p-1.5 text-right font-bold">
                                                        ₹{(bill.dynamicCharges?.find(c => c.name.toLowerCase() === "extra hour amount")?.amount 
                                                            ? parseFloat(bill.dynamicCharges.find(c => c.name.toLowerCase() === "extra hour amount").amount) 
                                                            : (_evalMultiplication(bill.extraHours) || 0.0)).toFixed(2)}
                                                    </td>
                                                </tr>
                                            )}

                                            {/* Dynamic/Additional Charges */}
                                            {bill.dynamicCharges && bill.dynamicCharges.map((charge, chargeIdx) => {
                                                if (charge.name.toLowerCase().includes("extra km") || charge.name.toLowerCase().includes("extra hour")) {
                                                    return null;
                                                }
                                                return (
                                                    <tr key={chargeIdx} className="border-b border-slate-300">
                                                        <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                        <td className="border-r border-slate-300 p-1.5">{charge.name}</td>
                                                        <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                        <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                        <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                        <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                        <td className="border-r border-slate-300 p-1.5 text-center text-slate-400">---</td>
                                                        <td className="p-1.5 text-right">
                                                            <input
                                                                type="text"
                                                                className={`w-20 text-right bg-transparent border-none outline-none focus:bg-slate-50 font-bold ${selectedField === `Charge: ${charge.name}` ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : ''}`}
                                                                value={charge.amount || ""}
                                                                onFocus={() => setSelectedField(`Charge: ${charge.name}`)}
                                                                onChange={(e) => updateDynamicChargeField(chargeIdx, e.target.value)}
                                                            />
                                                        </td>
                                                    </tr>
                                                );
                                            })}

                                            {/* Grand Total */}
                                            <tr className="bg-slate-50 font-bold">
                                                <td colSpan={7} className="border-r border-slate-300 p-1.5 text-right uppercase tracking-wider text-[9px]">Grand Total</td>
                                                <td className="p-1.5 text-right text-xs">
                                                    <span className="mr-0.5">₹</span>
                                                    <input
                                                        id="input-totalAmount"
                                                        type="number"
                                                        className={`w-20 text-right bg-transparent border-none outline-none font-black ${selectedField === "totalAmount" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : ''}`}
                                                        value={bill.totalAmount || 0}
                                                        onFocus={() => setSelectedField("totalAmount")}
                                                        onChange={(e) => updateBillField("totalAmount", e.target.value)}
                                                    />
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    {/* Passenger details */}
                                    <div className="grid grid-cols-2 gap-4 text-[10px] mb-4 font-sans">
                                        <div className="space-y-0.5">
                                            <span className="font-bold text-slate-500 uppercase text-[8px] tracking-wider block">Guest Name:</span>
                                            <input
                                                id="input-contactPerson"
                                                className={`font-semibold border-b border-transparent hover:border-slate-300 focus:border-cyan-500 focus:bg-slate-50 outline-none w-full px-1 py-0.5 ${selectedField === "contactPerson" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : 'bg-transparent'}`}
                                                value={bill.contactPerson || ""}
                                                onFocus={() => setSelectedField("contactPerson")}
                                                onChange={(e) => updateBillField("contactPerson", e.target.value)}
                                            />
                                        </div>
                                        <div className="space-y-0.5">
                                            <span className="font-bold text-slate-500 uppercase text-[8px] tracking-wider block">Booked By:</span>
                                            <input
                                                id="input-bookedBy"
                                                className={`font-semibold border-b border-transparent hover:border-slate-300 focus:border-cyan-500 focus:bg-slate-50 outline-none w-full px-1 py-0.5 ${selectedField === "bookedBy" ? 'ring-2 ring-cyan-500 bg-cyan-50/50' : 'bg-transparent'}`}
                                                value={bill.bookedBy || ""}
                                                onFocus={() => setSelectedField("bookedBy")}
                                                onChange={(e) => updateBillField("bookedBy", e.target.value)}
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* A4 Footer */}
                                <div>
                                    <div className="flex justify-between items-end border-t border-slate-200 pt-4 mt-6">
                                        <div className="space-y-2">
                                            <div className="w-24 border-b border-slate-300"></div>
                                            <p className="text-[9px] text-slate-400 font-sans">Guest Signature</p>
                                        </div>
                                        <div className="text-right space-y-2">
                                            <p className="font-bold text-[9px]">For Sri Tulja Bhavani Travels</p>
                                            <div className="w-24 border-b border-slate-300 inline-block"></div>
                                            <p className="text-[9px] text-slate-400 font-sans block mt-0.5">Authorised Signatory</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* RIGHT PANEL: AI Inspector & Validation Centre */}
                    <div className="bg-white flex flex-col overflow-hidden border-l border-slate-200">
                        {/* Tab header */}
                        <div className="border-b border-slate-200 bg-slate-50 p-2 flex gap-1">
                            <button
                                onClick={() => setRightTab("fields")}
                                className={`flex-1 py-1.5 text-[10px] font-black uppercase tracking-wider transition-all border ${rightTab === "fields" ? "bg-white text-cyan-600 border-slate-200" : "text-slate-500 border-transparent hover:bg-slate-100"}`}
                            >
                                AI Fields
                            </button>
                            <button
                                onClick={() => setRightTab("validation")}
                                className={`flex-1 py-1.5 text-[10px] font-black uppercase tracking-wider transition-all border relative ${rightTab === "validation" ? "bg-white text-cyan-600 border-slate-200" : "text-slate-500 border-transparent hover:bg-slate-100"}`}
                            >
                                Validation
                                {bill.validationReport?.issues.length > 0 && (
                                    <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-rose-500 text-white rounded-full flex items-center justify-center text-[8px] font-black">{bill.validationReport.issues.length}</span>
                                )}
                            </button>
                            <button
                                onClick={() => setRightTab("history")}
                                className={`flex-1 py-1.5 text-[10px] font-black uppercase tracking-wider transition-all border ${rightTab === "history" ? "bg-white text-cyan-600 border-slate-200" : "text-slate-500 border-transparent hover:bg-slate-100"}`}
                            >
                                History
                                {(changeHistory[currentBillIndex] || []).length > 0 && (
                                    <span className="ml-1 px-1 bg-slate-200 text-slate-700 text-[8px] rounded-full">{(changeHistory[currentBillIndex] || []).length}</span>
                                )}
                            </button>
                        </div>

                        {/* Tab contents */}
                        <div className="flex-1 overflow-y-auto p-4">
                            
                            {/* TAB 1: Fields Inspector */}
                            {rightTab === "fields" && (
                                <div className="space-y-3">
                                    {/* Smart Filter Header */}
                                    <div className="bg-slate-50 p-3.5 border border-slate-200 rounded-none mb-2">
                                        <span className="font-bold text-slate-400 uppercase text-[8px] block mb-2 tracking-wider">Smart Filters</span>
                                        <div className="flex flex-wrap gap-1">
                                            {["all", "errors", "warnings", "lowConfidence", "edited", "required"].map(f => (
                                                <button
                                                    key={f}
                                                    onClick={() => setFilterType(f)}
                                                    className={`px-2 py-1 text-[9px] font-bold uppercase border tracking-tight ${filterType === f ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"}`}
                                                >
                                                    {f.replace(/([A-Z])/g, ' $1')}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Fields List */}
                                    {Object.keys(FIELD_NAMES).map(fieldName => {
                                        const label = FIELD_TO_LABEL_MAP[fieldName];
                                        const matchedEl = bill.labeledDocument?.elements.find(el => el.label === label);
                                        const confidence = matchedEl?.confidence ?? 1.0;
                                        const coords = matchedEl?.coordinates ?? {};

                                        // Apply smart filter check
                                        const isEdited = originalBills[currentBillIndex]?.[fieldName] !== bill[fieldName];
                                        const issues = bill.validationReport?.issues.filter(iss => iss.field === label) || [];
                                        const isError = issues.some(i => i.severity === "ERROR");
                                        const isWarning = issues.some(i => i.severity === "WARNING");
                                        const isRequired = ["billNumber", "billDate", "companyName", "vehicleNumber", "dutySlipNo", "totalAmount"].includes(fieldName);

                                        if (filterType === "errors" && !isError) return null;
                                        if (filterType === "warnings" && !isWarning) return null;
                                        if (filterType === "lowConfidence" && confidence >= 0.98) return null;
                                        if (filterType === "edited" && !isEdited) return null;
                                        if (filterType === "required" && !isRequired) return null;

                                        return (
                                            <div
                                                key={fieldName}
                                                onClick={() => {
                                                    setSelectedField(fieldName);
                                                    const inpEl = document.getElementById(`input-${fieldName}`);
                                                    if (inpEl) inpEl.focus();
                                                }}
                                                className={`p-3 border transition-all cursor-pointer text-xs ${
                                                    selectedField === fieldName ? "bg-cyan-50/50 border-cyan-400 shadow-sm" : "bg-white border-slate-200 hover:border-slate-300"
                                                }`}
                                            >
                                                <div className="flex justify-between items-center mb-1">
                                                    <span className="font-bold text-slate-800">{FIELD_NAMES[fieldName]}</span>
                                                    {isRequired && (
                                                        <span className="text-[8px] font-bold text-slate-400 border border-slate-200 px-1 py-0.2 rounded font-sans uppercase">Required</span>
                                                    )}
                                                </div>
                                                <div className="flex justify-between items-center mb-1.5 text-slate-500 font-mono text-[10px]">
                                                    <span>Extracted: "{bill[fieldName] || "None"}"</span>
                                                    <span className={`px-1.5 py-0.5 text-[9px] font-bold ${
                                                        confidence >= 0.98 ? "text-emerald-700 bg-emerald-50" :
                                                        confidence >= 0.95 ? "text-amber-700 bg-amber-50" : "text-rose-700 bg-rose-50"
                                                    }`}>
                                                        {Math.round(confidence * 100)}%
                                                    </span>
                                                </div>

                                                {/* Coords & Validation Status */}
                                                <div className="flex justify-between items-center text-[9px]">
                                                    <span className="text-slate-400 font-mono">
                                                        {coords.table_number !== undefined 
                                                            ? `P${coords.page_number} T${coords.table_number} R${coords.row_index} C${coords.column_index}` 
                                                            : coords.page_number ? `P${coords.page_number} Line` : "N/A"
                                                        }
                                                    </span>
                                                    <span className={`font-black text-[8px] uppercase tracking-wider ${
                                                        isError ? "text-rose-600" : isWarning ? "text-amber-600" : "text-emerald-600"
                                                    }`}>
                                                        {isError ? "FAIL" : isWarning ? "WARNING" : "PASS"}
                                                    </span>
                                                </div>

                                                {/* Print issues if any */}
                                                {issues.length > 0 && (
                                                    <div className="mt-2 text-[9px] text-rose-700 bg-rose-50 p-2 border-l-2 border-rose-500">
                                                        {issues.map((iss, issIdx) => <p key={issIdx}>{iss.message}</p>)}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {/* TAB 2: Validation Issues Aggregator */}
                            {rightTab === "validation" && (
                                <div className="space-y-4">
                                    {/* Validation Report card */}
                                    {bill.validationReport && bill.validationReport.validation_summary && (
                                        <div className="p-4 border border-slate-200 bg-slate-50 rounded-none text-xs">
                                            <h3 className="font-bold text-slate-800 uppercase text-[9px] tracking-wider mb-3">Validation Summary</h3>
                                            <div className="grid grid-cols-2 gap-4 mb-4">
                                                <div>
                                                    <span className="text-slate-400 font-bold uppercase text-[8px] block">Overall Score</span>
                                                    <span className="text-2xl font-black text-slate-800">{Math.round(bill.validationReport.validation_summary.overall_quality_score || 0)}/100</span>
                                                </div>
                                                <div>
                                                    <span className="text-slate-400 font-bold uppercase text-[8px] block">Avg Confidence</span>
                                                    <span className="text-2xl font-black text-slate-800">{Math.round((bill.validationReport.validation_summary.average_confidence || 0) * 100)}%</span>
                                                </div>
                                            </div>
                                            <div className="text-center py-2.5 border-t border-slate-200 mt-2">
                                                <span className={`px-3 py-1.5 font-bold uppercase text-[9px] tracking-wider border rounded ${
                                                    bill.validationReport.validation_summary.recommendation === "PASS" ? "bg-emerald-50 text-emerald-700 border-emerald-300" :
                                                    bill.validationReport.validation_summary.recommendation === "PASS_WITH_WARNINGS" ? "bg-amber-50 text-amber-700 border-amber-300" :
                                                    "bg-rose-50 text-rose-700 border-rose-300"
                                                }`}>
                                                    {(bill.validationReport.validation_summary.recommendation || "MANUAL_REVIEW").replace(/_/g, " ")}
                                                </span>
                                            </div>
                                        </div>
                                    )}

                                    {/* Issues list grouped */}
                                    <div className="space-y-3 text-xs">
                                        <span className="font-bold text-slate-500 uppercase text-[9px] tracking-wider block">Issues Detected</span>
                                        {bill.validationReport?.issues.length > 0 ? (
                                            bill.validationReport.issues.map((iss, issIdx) => {
                                                const field = Object.keys(FIELD_TO_LABEL_MAP).find(k => FIELD_TO_LABEL_MAP[k] === iss.field);
                                                return (
                                                    <div 
                                                        key={issIdx} 
                                                        onClick={() => {
                                                            if (field) {
                                                                setSelectedField(field);
                                                                const inpEl = document.getElementById(`input-${field}`);
                                                                if (inpEl) inpEl.focus();
                                                            }
                                                        }}
                                                        className={`p-3 border-l-4 rounded bg-white shadow-xs border cursor-pointer hover:border-slate-300 ${
                                                            iss.severity === "ERROR" ? "border-rose-500 text-rose-800" : "border-amber-500 text-amber-800"
                                                        }`}
                                                    >
                                                        <div className="flex justify-between items-center mb-1 font-bold">
                                                            <span className="uppercase text-[8px] tracking-wider">{iss.severity}</span>
                                                            <span className="text-[9px] text-slate-400">{iss.rule_violated}</span>
                                                        </div>
                                                        <p className="text-xs mb-1.5 font-medium leading-normal">{iss.message}</p>
                                                        {iss.suggested_correction && (
                                                            <p className="text-[10px] text-slate-500 italic">Correction: {iss.suggested_correction}</p>
                                                        )}
                                                    </div>
                                                );
                                            })
                                        ) : (
                                            <div className="text-center py-8 text-slate-400 border border-dashed border-slate-200">
                                                <BadgeCheck className="mx-auto mb-2 text-emerald-500" size={32} />
                                                <p className="font-semibold text-xs text-slate-600">All checks passed successfully</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* TAB 3: Change Log / History timeline */}
                            {rightTab === "history" && (
                                <div className="space-y-4">
                                    <span className="font-bold text-slate-500 uppercase text-[9px] tracking-wider block">Change Timeline</span>
                                    {(changeHistory[currentBillIndex] || []).length > 0 ? (
                                        <div className="border-l border-slate-200 ml-2 pl-4 space-y-4 relative text-xs">
                                            {(changeHistory[currentBillIndex] || []).map((log, logIdx) => (
                                                <div key={logIdx} className="relative group">
                                                    {/* Timeline node */}
                                                    <div className="absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full bg-cyan-500 border border-white" />
                                                    <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
                                                        <span className="font-bold text-slate-600">{log.user}</span>
                                                        <span>{log.timestamp}</span>
                                                    </div>
                                                    <p className="font-bold text-slate-800 text-[11px] mb-0.5">Changed: {FIELD_NAMES[log.field] || log.field}</p>
                                                    <p className="text-slate-500 font-mono text-[10px]">"{log.oldValue}" &rarr; "{log.newValue}"</p>
                                                    
                                                    {/* Restore value button */}
                                                    <button
                                                        onClick={() => {
                                                            updateBillField(log.field, log.oldValue, `Reverted changes to values`);
                                                            toast.success("Restored previous value!");
                                                        }}
                                                        className="mt-1 text-[9px] font-black text-cyan-600 hover:text-cyan-800 uppercase"
                                                    >
                                                        Restore Value
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="text-center py-8 text-slate-400 border border-dashed border-slate-200">
                                            <History className="mx-auto mb-2 text-slate-300" size={32} />
                                            <p className="text-xs text-slate-500 font-medium">No modifications logged yet</p>
                                        </div>
                                    )}
                                </div>
                            )}
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
