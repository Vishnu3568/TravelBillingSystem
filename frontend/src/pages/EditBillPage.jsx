import { useMemo, useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import api from "../services/api.js";
import { numberToWords } from "../utils/numberToWords.js";
import { calculateCharges } from "../utils/pricingUtils.js";
import { toast } from "sonner";
import { Undo2, Redo2, RotateCcw } from "lucide-react";
import AiSuggestions from "../ui/AiSuggestions.jsx";

const today = () => new Date().toISOString().slice(0, 10);

const initialForm = {
  billNumber: "",
  date: today(),
  company: "",
  vehicle: "",
  dutySlipNumber: "",
  tripDate: today(),
  vehicleType: "SEDAN",
  acNonAc: "Non-AC",
  totalKms: "",
  totalHours: "",
  extraKms: "",
  extraHours: "",
  tripType: "Local",
  pricingType: "BASE",
  notes: "",
  contactPerson: "",
  bookedBy: "",
  managerName: "Sri Tulja Bhavani Travels",
  dynamicCharges: [],
};

const inputClass = "w-full border-none bg-transparent px-2 py-1 text-black focus:ring-0 outline-none";
const cellClass = "border border-slate-300 p-0 focus-within:bg-cyan-50 transition-colors";

export default function EditBillPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [manualCharges, setManualCharges] = useState([]);
  
  const [history, setHistory] = useState({
    past: [],
    future: []
  });

  const [companies, setCompanies] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [billRes, companiesRes, vehiclesRes] = await Promise.all([
          api.get(`/bills/${id}`),
          api.get("/companies"),
          api.get("/vehicles")
        ]);
        
        const bill = billRes.data;
        const allCharges = bill.dynamicCharges || [];
        const system = allCharges.filter(c => c.isSystem);
        const manual = allCharges.filter(c => !c.isSystem);

        const initialFormData = {
          billNumber: bill.billNumber,
          date: bill.billDate || today(),
          company: bill.companyName,
          vehicle: bill.vehicleName,
          dutySlipNumber: bill.dutySlipNo,
          tripDate: bill.tripDate || today(),
          vehicleType: bill.vehicleType || "SEDAN",
          acNonAc: bill.acNonAc || "Non-AC",
          totalKms: bill.totalKms || "",
          totalHours: bill.totalHours || "",
          extraKms: bill.extraKms || "",
          extraHours: bill.extraHours || "",
          tripType: bill.tripType || "Local",
          pricingType: bill.pricingType || "BASE",
          notes: bill.notes || "",
          contactPerson: bill.contactPerson || "",
          bookedBy: bill.bookedBy || "",
          managerName: bill.managerName || "Sri Tulja Bhavani Travels",
          dynamicCharges: system
        };

        const initialManual = manual.length > 0 ? manual : [{ name: "", calculation: "", amount: "", isSystem: false }];

        setForm(initialFormData);
        setManualCharges(initialManual);
        setHistory({ past: [], future: [] });
        setCompanies(companiesRes.data);
        setVehicles(vehiclesRes.data);
      } catch (err) {
        console.error("Error fetching data:", err);
        toast.error("Failed to load bill details");
        navigate("/bill-history");
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [id, navigate]);

  useEffect(() => {
    if (isLoading) return;
    const result = calculateCharges(form.totalKms, form.totalHours, form.vehicleType);
    setForm(prev => ({
      ...prev,
      pricingType: result.pricingType,
      dynamicCharges: result.charges
    }));
  }, [form.totalKms, form.totalHours, form.vehicleType, isLoading]);

  const allDisplayCharges = useMemo(() => {
    return [...form.dynamicCharges, ...manualCharges];
  }, [form.dynamicCharges, manualCharges]);

  const grandTotal = useMemo(() => {
    return allDisplayCharges.reduce((sum, item) => sum + Number(item.amount || 0), 0);
  }, [allDisplayCharges]);

  const amountInWords = useMemo(() => numberToWords(grandTotal), [grandTotal]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    saveToHistory();
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleManualChargeChange = (index, field, value) => {
    saveToHistory();
    const newCharges = [...manualCharges];
    newCharges[index][field] = value;
    setManualCharges(newCharges);
  };

  const addManualRow = () => {
    saveToHistory();
    setManualCharges(prev => [...prev, { name: "", calculation: "", amount: "", isSystem: false }]);
  };

  const removeManualRow = (index) => {
    saveToHistory();
    const newCharges = manualCharges.filter((_, i) => i !== index);
    setManualCharges(newCharges.length > 0 ? newCharges : [{ name: "", calculation: "", amount: "", isSystem: false }]);
  };

  const handleApplySuggestion = (field, value) => {
    saveToHistory();
    const fieldMap = {
      'driverBata': 'Driver Bata',
      'toll': 'Toll',
      'parking': 'Parking'
    };
    const targetName = fieldMap[field] || field;
    const index = manualCharges.findIndex(c => c.name.toLowerCase() === targetName.toLowerCase());
    
    if (index !== -1) {
      handleManualChargeChange(index, "amount", value);
      toast.info(`Applied suggestion for ${targetName}`);
    } else {
      setManualCharges(prev => [...prev, { name: targetName, calculation: "AI Suggested", amount: value, isSystem: false }]);
      toast.info(`Added suggestion for ${targetName}`);
    }
  };

  const saveToHistory = () => {
    setHistory(prev => ({
      past: [...prev.past.slice(-49), { form: JSON.parse(JSON.stringify(form)), manualCharges: JSON.parse(JSON.stringify(manualCharges)) }],
      future: []
    }));
  };

  const undo = () => {
    if (history.past.length === 0) return;
    const previous = history.past[history.past.length - 1];
    const newPast = history.past.slice(0, history.past.length - 1);
    setHistory({
      past: newPast,
      future: [{ form: JSON.parse(JSON.stringify(form)), manualCharges: JSON.parse(JSON.stringify(manualCharges)) }, ...history.future]
    });
    setForm(previous.form);
    setManualCharges(previous.manualCharges);
  };

  const redo = () => {
    if (history.future.length === 0) return;
    const next = history.future[0];
    const newFuture = history.future.slice(1);
    setHistory({
      past: [...history.past, { form: JSON.parse(JSON.stringify(form)), manualCharges: JSON.parse(JSON.stringify(manualCharges)) }],
      future: newFuture
    });
    setForm(next.form);
    setManualCharges(next.manualCharges);
  };

  const resetToOriginal = () => {
    if (window.confirm("This will clear ALL your current changes. Are you sure?")) {
      window.location.reload();
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setIsSaving(true);
    try {
      const payload = {
        billDate: form.date,
        companyName: form.company,
        vehicleName: form.vehicle,
        dutySlipNo: form.dutySlipNumber,
        tripDate: form.tripDate,
        vehicleType: form.vehicleType,
        acNonAc: form.acNonAc,
        totalKms: Number(form.totalKms) || 0,
        totalHours: Number(form.totalHours) || 0,
        extraKms: Number(form.extraKms) || 0,
        extraHours: Number(form.extraHours) || 0,
        tripType: form.tripType,
        pricingType: form.pricingType,
        notes: form.notes,
        contactPerson: form.contactPerson,
        bookedBy: form.bookedBy,
        managerName: form.managerName,
        dynamicCharges: allDisplayCharges.filter(c => c.name.trim() !== "" || c.amount !== "").map(c => ({
          name: c.name,
          calculation: c.calculation,
          amount: Number(c.amount) || 0,
          isSystem: c.isSystem || false
        }))
      };
      await api.put(`/bills/${id}`, payload);
      toast.success("Bill updated successfully");
      navigate(`/bill-view/${id}`);
    } catch (err) {
      console.error("Save error:", err);
      toast.error(err.response?.data?.message || "Failed to save bill");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="h-12 w-12 animate-spin rounded-none border-4 border-cyan-600 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-slate-600 font-medium">Loading bill details...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-bold text-black">Edit Bill (Auto-Calculation Active)</h1>
            <p className="text-sm text-slate-500">Bill Number: {form.billNumber}</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 border-r border-slate-200 pr-3 mr-1">
              <button type="button" onClick={undo} disabled={history.past.length === 0} title="Undo (Ctrl+Z)" className="p-1.5 rounded-none hover:bg-slate-100 text-slate-600 disabled:opacity-30 transition-colors">
                <Undo2 className="w-4 h-4" />
              </button>
              <button type="button" onClick={redo} disabled={history.future.length === 0} title="Redo (Ctrl+Y)" className="p-1.5 rounded-none hover:bg-slate-100 text-slate-600 disabled:opacity-30 transition-colors">
                <Redo2 className="w-4 h-4" />
              </button>
              <button type="button" onClick={resetToOriginal} title="Reset to Original" className="p-1.5 rounded-none hover:bg-slate-100 text-slate-600 transition-colors">
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
            <button onClick={() => navigate(-1)} className="rounded-none border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</button>
            <button onClick={handleSubmit} disabled={isSaving} className="rounded-none bg-cyan-600 px-6 py-2 text-sm font-semibold text-white shadow-md hover:bg-cyan-700 disabled:opacity-50">
              {isSaving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto mt-8 max-w-7xl px-6 grid grid-cols-1 lg:grid-cols-4 gap-8">
        <form onSubmit={handleSubmit} className="lg:col-span-3 space-y-8 rounded-none border border-slate-200 bg-white p-8 shadow-sm">
          <section>
            <h2 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-400">1. Basic Information</h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Bill Date</label>
                <input type="date" name="date" value={form.date} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Customer</label>
                <select name="company" value={form.company} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500">
                  <option value="">Select Company</option>
                  {companies.map(c => <option key={c.id} value={c.name}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Duty Slip No</label>
                <input type="text" name="dutySlipNumber" value={form.dutySlipNumber} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Pricing Mode</label>
                <div className="mt-2 text-sm font-bold text-cyan-600">{form.pricingType === "PER_KM" ? "LONG TRIP (>200KM)" : "LOCAL PACKAGE (8/80)"}</div>
              </div>
            </div>
          </section>

          <section className="rounded-none bg-slate-50 p-6">
            <h2 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-400">2. Trip Data (Triggers Auto-Calc)</h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700 text-cyan-700 font-bold">Total Kms *</label>
                <input type="number" name="totalKms" value={form.totalKms} onChange={handleChange} className="w-full rounded-none border-2 border-cyan-300 px-3 py-2 text-sm outline-none focus:border-cyan-600 bg-white" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700 text-cyan-700 font-bold">Total Hours *</label>
                <input type="number" name="totalHours" value={form.totalHours} onChange={handleChange} className="w-full rounded-none border-2 border-cyan-300 px-3 py-2 text-sm outline-none focus:border-cyan-600 bg-white" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Vehicle Type</label>
                <select name="vehicleType" value={form.vehicleType} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 bg-white">
                  <option value="SEDAN">SEDAN (₹14/km)</option>
                  <option value="CRYSTA">CRYSTA (₹18/km)</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Vehicle No</label>
                <select name="vehicle" value={form.vehicle} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 bg-white">
                  <option value="">Select Vehicle</option>
                  {vehicles.map(v => <option key={v.id} value={v.registrationNumber}>{v.registrationNumber}</option>)}
                </select>
              </div>
            </div>
          </section>

          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">3. Charges Table</h2>
              <button type="button" onClick={addManualRow} className="text-xs font-bold text-cyan-600 hover:text-cyan-700">+ Add Extra Charge</button>
            </div>
            <div className="overflow-hidden rounded-none border border-slate-300 shadow-sm">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-slate-100">
                    <th className="w-12 border-b border-slate-300 py-2 text-center text-xs font-bold text-slate-500 uppercase">#</th>
                    <th className="border-b border-l border-slate-300 py-2 text-left px-4 text-xs font-bold text-slate-500 uppercase">Charge Name</th>
                    <th className="border-b border-l border-slate-300 py-2 text-left px-4 text-xs font-bold text-slate-500 uppercase">Calculation</th>
                    <th className="w-40 border-b border-l border-slate-300 py-2 text-right px-4 text-xs font-bold text-slate-500 uppercase">Amount (₹)</th>
                    <th className="w-12 border-b border-l border-slate-300 py-2 text-center"></th>
                  </tr>
                </thead>
                <tbody>
                  {form.dynamicCharges.map((charge, index) => (
                    <tr key={`sys-${index}`} className="bg-slate-50 italic">
                      <td className="border-t border-slate-300 py-2 text-center text-xs text-slate-400 font-medium">SYS</td>
                      <td className={`${cellClass} border-t border-l bg-slate-50/50`}>
                        <input type="text" readOnly value={charge.name} className={`${inputClass} text-slate-500 font-bold`} />
                      </td>
                      <td className={`${cellClass} border-t border-l bg-slate-50/50`}>
                        <input type="text" readOnly value={charge.calculation} className={`${inputClass} text-slate-500`} />
                      </td>
                      <td className={`${cellClass} border-t border-l bg-slate-50/50`}>
                        <input type="text" readOnly value={charge.amount} className={`${inputClass} text-right font-bold text-cyan-700`} />
                      </td>
                      <td className="border-t border-l border-slate-300 text-center"><span className="text-[10px] font-bold text-slate-300 uppercase">Auto</span></td>
                    </tr>
                  ))}
                  {manualCharges.map((charge, index) => (
                    <tr key={`man-${index}`} className="group hover:bg-cyan-50/30 transition-colors">
                      <td className="border-t border-slate-300 py-2 text-center text-xs text-slate-400 font-medium">{index + 1}</td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input type="text" value={charge.name} placeholder="Extra charge name..." onChange={(e) => handleManualChargeChange(index, "name", e.target.value)} className={inputClass} />
                      </td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input type="text" value={charge.calculation} placeholder="Optional calc..." onChange={(e) => handleManualChargeChange(index, "calculation", e.target.value)} className={inputClass} />
                      </td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input type="number" value={charge.amount} placeholder="0" onChange={(e) => handleManualChargeChange(index, "amount", e.target.value)} className={`${inputClass} text-right font-semibold`} />
                      </td>
                      <td className="border-t border-l border-slate-300 text-center">
                        <button type="button" onClick={() => removeManualRow(index)} className="text-slate-300 hover:text-red-500 group-hover:opacity-100 opacity-0 transition-all">×</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="flex flex-col items-end gap-2 border-t border-slate-100 pt-6">
            <div className="flex items-baseline gap-8">
              <span className="text-sm font-bold text-slate-500 uppercase">Grand Total:</span>
              <span className="text-3xl font-black text-black">₹ {grandTotal.toLocaleString("en-IN")}</span>
            </div>
            <p className="text-sm font-medium italic text-slate-500 uppercase">Rupees {amountInWords}</p>
          </section>
        </form>

        <aside className="lg:col-span-1 space-y-6">
           <AiSuggestions 
             currentBill={{ companyName: form.company, vehicleType: form.vehicleType, totalKms: form.totalKms, totalHours: form.totalHours }} 
             onApply={handleApplySuggestion}
           />
        </aside>
      </main>
    </div>
  );
}
