import { useMemo, useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import api from "../services/api.js";
import { numberToWords } from "../utils/numberToWords.js";
import { calculateCharges } from "../utils/pricingUtils.js";
import { toast } from "sonner";

const today = () => new Date().toISOString().slice(0, 10);

const initialForm = {
  date: today(),
  company: "",
  vehicle: "",
  dutySlipNumber: "",
  tripDate: today(),
  vehicleType: "SEDAN",
  acNonAc: "Non-AC",
  totalKms: "",
  totalHours: "",
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

export default function CreateBillPage() {
  const navigate = useNavigate();
  const { username, logout } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [manualCharges, setManualCharges] = useState([
    { name: "Driver Bata", calculation: "", amount: "", isSystem: false },
    { name: "Toll", calculation: "", amount: "", isSystem: false },
    { name: "Parking", calculation: "", amount: "", isSystem: false },
  ]);
  const [companies, setCompanies] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [companiesRes, vehiclesRes] = await Promise.all([
          api.get("/companies"),
          api.get("/vehicles")
        ]);
        setCompanies(companiesRes.data);
        setVehicles(vehiclesRes.data);
      } catch (err) {
        console.error("Error fetching master data:", err);
      }
    };
    fetchData();
  }, []);

  // AUTO-CALCULATION ENGINE
  useEffect(() => {
    const result = calculateCharges(form.totalKms, form.totalHours, form.vehicleType);
    setForm(prev => ({
      ...prev,
      pricingType: result.pricingType,
      dynamicCharges: result.charges
    }));
  }, [form.totalKms, form.totalHours, form.vehicleType]);

  const allDisplayCharges = useMemo(() => {
    return [...form.dynamicCharges, ...manualCharges];
  }, [form.dynamicCharges, manualCharges]);

  const grandTotal = useMemo(() => {
    return allDisplayCharges.reduce((sum, item) => sum + Number(item.amount || 0), 0);
  }, [allDisplayCharges]);

  const amountInWords = useMemo(() => numberToWords(grandTotal), [grandTotal]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleManualChargeChange = (index, field, value) => {
    const newCharges = [...manualCharges];
    newCharges[index][field] = value;
    setManualCharges(newCharges);
  };

  const addManualRow = () => {
    setManualCharges(prev => [...prev, { name: "", calculation: "", amount: "", isSystem: false }]);
  };

  const removeManualRow = (index) => {
    const newCharges = manualCharges.filter((_, i) => i !== index);
    setManualCharges(newCharges.length > 0 ? newCharges : [{ name: "", calculation: "", amount: "", isSystem: false }]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.company || !form.vehicle || !form.dutySlipNumber) {
      toast.error("Please fill required fields (Company, Vehicle, Duty Slip No)");
      return;
    }

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

      const response = await api.post("/bills", payload);
      toast.success("Bill created successfully");
      navigate(`/bill-view/${response.data.id}`);
    } catch (err) {
      console.error("Save error:", err);
      toast.error(err.response?.data?.message || "Failed to create bill");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-cyan-600">Transport Billing</p>
            <h1 className="text-xl font-bold text-black">New Customer Bill</h1>
          </div>
          <div className="flex gap-3">
            <Link to="/owner-dashboard" className="rounded-none border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Dashboard</Link>
            <button onClick={handleSubmit} disabled={isSaving} className="rounded-none bg-black px-6 py-2 text-sm font-semibold text-white shadow-md hover:bg-slate-800 disabled:opacity-50">
              {isSaving ? "Saving..." : "Save and View"}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto mt-8 max-w-5xl px-6">
        <form onSubmit={handleSubmit} className="space-y-8 rounded-none border border-slate-200 bg-white p-8 shadow-sm">
          
          <section>
            <h2 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-400">1. Basic Information</h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Bill Date</label>
                <input type="date" name="date" value={form.date} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Customer *</label>
                <select name="company" value={form.company} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500">
                  <option value="">Select Company</option>
                  {companies.map(c => <option key={c.id} value={c.name}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Duty Slip No *</label>
                <input type="text" name="dutySlipNumber" value={form.dutySlipNumber} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Vehicle No *</label>
                <select name="vehicle" value={form.vehicle} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500">
                  <option value="">Select Vehicle</option>
                  {vehicles.map(v => <option key={v.id} value={v.registrationNumber}>{v.registrationNumber} ({v.type})</option>)}
                </select>
              </div>
            </div>
          </section>

          <section className="rounded-none bg-slate-50 p-6 border border-cyan-100">
            <h2 className="mb-4 text-xs font-bold uppercase tracking-wider text-cyan-600">2. Trip Usage (Automatic Pricing)</h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div>
                <label className="mb-1 block text-sm font-bold text-slate-700">Total Kms</label>
                <input type="number" name="totalKms" value={form.totalKms} onChange={handleChange} placeholder="e.g. 95" className="w-full rounded-none border-2 border-cyan-200 px-3 py-2 text-sm outline-none focus:border-cyan-600 bg-white" />
                <span className="text-[10px] text-slate-400 mt-1 block">Package: 8/80 | Extra: ₹16/km | Long: 200km+</span>
              </div>
              <div>
                <label className="mb-1 block text-sm font-bold text-slate-700">Total Hours</label>
                <input type="number" name="totalHours" value={form.totalHours} onChange={handleChange} placeholder="e.g. 10" className="w-full rounded-none border-2 border-cyan-200 px-3 py-2 text-sm outline-none focus:border-cyan-600 bg-white" />
                <span className="text-[10px] text-slate-400 mt-1 block">Extra: ₹130/hr after 8 hrs</span>
              </div>
              <div>
                <label className="mb-1 block text-sm font-bold text-slate-700">Vehicle Category (for long trips)</label>
                <select name="vehicleType" value={form.vehicleType} onChange={handleChange} className="w-full rounded-none border-2 border-cyan-200 px-3 py-2 text-sm outline-none focus:border-cyan-600 bg-white">
                  <option value="SEDAN">SEDAN (₹14/km)</option>
                  <option value="CRYSTA">CRYSTA (₹18/km)</option>
                </select>
              </div>
            </div>
          </section>

          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">3. Bill Particulars</h2>
              <button type="button" onClick={addManualRow} className="text-xs font-bold text-cyan-600 hover:text-cyan-700">+ Add Others</button>
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
                    <tr key={`sys-${index}`} className="bg-slate-50/80 italic">
                      <td className="border-t border-slate-300 py-2 text-center text-[10px] text-cyan-600 font-black">AUTO</td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input type="text" readOnly value={charge.name} className={`${inputClass} font-bold text-slate-600`} />
                      </td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input type="text" readOnly value={charge.calculation} className={inputClass} />
                      </td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input type="text" readOnly value={charge.amount} className={`${inputClass} text-right font-black text-cyan-700`} />
                      </td>
                      <td className="border-t border-l border-slate-300"></td>
                    </tr>
                  ))}
                  {manualCharges.map((charge, index) => (
                    <tr key={`man-${index}`} className="group hover:bg-cyan-50/30 transition-colors">
                      <td className="border-t border-slate-300 py-2 text-center text-xs text-slate-400 font-medium">{index + 1}</td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input type="text" value={charge.name} placeholder="Charge name..." onChange={(e) => handleManualChargeChange(index, "name", e.target.value)} className={inputClass} />
                      </td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input type="text" value={charge.calculation} placeholder="Calculation..." onChange={(e) => handleManualChargeChange(index, "calculation", e.target.value)} className={inputClass} />
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

          <section className="rounded-none border border-dashed border-slate-200 p-6 bg-slate-50/30">
            <h2 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-400">4. Office Details (Optional)</h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Customer Person</label>
                <input type="text" name="contactPerson" value={form.contactPerson} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 bg-white" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Booked By</label>
                <input type="text" name="bookedBy" value={form.bookedBy} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 bg-white" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Manager Signature</label>
                <input type="text" name="managerName" value={form.managerName} onChange={handleChange} className="w-full rounded-none border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 bg-white" />
              </div>
            </div>
          </section>
        </form>
      </main>
    </div>
  );
}
