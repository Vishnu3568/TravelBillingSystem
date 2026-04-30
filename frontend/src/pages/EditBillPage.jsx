import { useMemo, useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import api from "../services/api.js";
import { numberToWords } from "../utils/numberToWords.js";
import { toast } from "sonner";

const today = () => new Date().toISOString().slice(0, 10);

const initialForm = {
  billNumber: "",
  date: today(),
  company: "",
  vehicle: "",
  dutySlipNumber: "",
  tripDate: today(),
  vehicleType: "",
  acNonAc: "Non-AC",
  totalKms: "",
  totalHours: "",
  extraKms: "",
  extraHours: "",
  tripType: "Local",
  notes: "",
  contactPerson: "",
  bookedBy: "",
  managerName: "Sri Tulja Bhavani Travels",
  dynamicCharges: [
    { name: "Base Amount", calculation: "", amount: "" },
    { name: "Driver Bata", calculation: "", amount: "" },
    { name: "Parking", calculation: "", amount: "" },
    { name: "Toll", calculation: "", amount: "" },
    { name: "", calculation: "", amount: "" },
    { name: "", calculation: "", amount: "" },
    { name: "", calculation: "", amount: "" },
    { name: "", calculation: "", amount: "" },
    { name: "", calculation: "", amount: "" },
    { name: "", calculation: "", amount: "" },
  ],
};

const inputClass = "w-full border-none bg-transparent px-2 py-1 text-slate-900 focus:ring-0 outline-none";
const cellClass = "border border-slate-300 p-0 focus-within:bg-cyan-50 transition-colors";

export default function EditBillPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [form, setForm] = useState(initialForm);
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
        
        // Map backend response to form state
        // Ensure at least 10 rows in dynamicCharges
        let charges = bill.dynamicCharges || [];
        while (charges.length < 10) {
          charges.push({ name: "", calculation: "", amount: "" });
        }

        setForm({
          billNumber: bill.billNumber,
          date: bill.billDate || today(),
          company: bill.companyName,
          vehicle: bill.vehicleName,
          dutySlipNumber: bill.dutySlipNo,
          tripDate: bill.tripDate || today(),
          vehicleType: bill.vehicleType || "",
          acNonAc: bill.acNonAc || "Non-AC",
          totalKms: bill.totalKms || "",
          totalHours: bill.totalHours || "",
          extraKms: bill.extraKms || "",
          extraHours: bill.extraHours || "",
          tripType: bill.tripType || "Local",
          notes: bill.notes || "",
          contactPerson: bill.contactPerson || "",
          bookedBy: bill.bookedBy || "",
          managerName: bill.managerName || "Sri Tulja Bhavani Travels",
          dynamicCharges: charges.map(c => ({
            name: c.name || "",
            calculation: c.calculation || "",
            amount: c.amount || ""
          }))
        });
        
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

  const grandTotal = useMemo(() => {
    return form.dynamicCharges.reduce((sum, item) => sum + Number(item.amount || 0), 0);
  }, [form.dynamicCharges]);

  const amountInWords = useMemo(() => numberToWords(grandTotal), [grandTotal]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleChargeChange = (index, field, value) => {
    const newCharges = [...form.dynamicCharges];
    newCharges[index][field] = value;
    setForm(prev => ({ ...prev, dynamicCharges: newCharges }));
  };

  const addChargeRow = () => {
    setForm(prev => ({
      ...prev,
      dynamicCharges: [...prev.dynamicCharges, { name: "", calculation: "", amount: "" }]
    }));
  };

  const removeChargeRow = (index) => {
    if (form.dynamicCharges.length <= 1) return;
    const newCharges = form.dynamicCharges.filter((_, i) => i !== index);
    setForm(prev => ({ ...prev, dynamicCharges: newCharges }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
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
        notes: form.notes,
        contactPerson: form.contactPerson,
        bookedBy: form.bookedBy,
        managerName: form.managerName,
        dynamicCharges: form.dynamicCharges.filter(c => c.name.trim() !== "" || c.amount !== "").map(c => ({
          name: c.name,
          calculation: c.calculation,
          amount: Number(c.amount) || 0
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
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-cyan-600 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-slate-600 font-medium">Loading bill details...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Edit Bill</h1>
            <p className="text-sm text-slate-500">Bill Number: {form.billNumber}</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate(-1)}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSaving}
              className="rounded-lg bg-cyan-600 px-6 py-2 text-sm font-semibold text-white shadow-md hover:bg-cyan-700 disabled:opacity-50"
            >
              {isSaving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto mt-8 max-w-5xl px-6">
        <form onSubmit={handleSubmit} className="space-y-8 rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          
          {/* SECTION 1: BASIC INFO */}
          <section>
            <h2 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-400">1. Basic Information</h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Bill No</label>
                <input
                  type="text"
                  readOnly
                  value={form.billNumber}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-500 outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Bill Date</label>
                <input
                  type="date"
                  name="date"
                  value={form.date}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>
              <div className="md:col-span-1">
                <label className="mb-1 block text-sm font-medium text-slate-700">Customer</label>
                <select
                  name="company"
                  value={form.company}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                >
                  <option value="">Select Company</option>
                  {companies.map(c => <option key={c.id} value={c.name}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Duty Slip No</label>
                <input
                  type="text"
                  name="dutySlipNumber"
                  value={form.dutySlipNumber}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>
            </div>
          </section>

          {/* SECTION 2: TRIP DETAILS */}
          <section className="rounded-lg bg-slate-50 p-6">
            <h2 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-400">2. Trip Details</h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Trip Date</label>
                <input
                  type="date"
                  name="tripDate"
                  value={form.tripDate}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Vehicle Type</label>
                <select
                  name="vehicleType"
                  value={form.vehicleType}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                >
                  <option value="">Select Type</option>
                  <option value="Swift Dzire">Swift Dzire</option>
                  <option value="Ertiga">Ertiga</option>
                  <option value="Innova">Innova</option>
                  <option value="Innova Crysta">Innova Crysta</option>
                  <option value="Tempo Traveller">Tempo Traveller</option>
                  <option value="Bus">Bus</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">AC / Non-AC</label>
                <select
                  name="acNonAc"
                  value={form.acNonAc}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                >
                  <option value="AC">AC</option>
                  <option value="Non-AC">Non-AC</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Vehicle Number</label>
                <select
                  name="vehicle"
                  value={form.vehicle}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                >
                  <option value="">Select Vehicle</option>
                  {vehicles.map(v => <option key={v.id} value={v.registrationNumber}>{v.registrationNumber}</option>)}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Total Kms</label>
                <input
                  type="number"
                  name="totalKms"
                  value={form.totalKms}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Total Hours</label>
                <input
                  type="number"
                  name="totalHours"
                  value={form.totalHours}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Extra Kms</label>
                <input
                  type="number"
                  name="extraKms"
                  value={form.extraKms}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Extra Hours</label>
                <input
                  type="number"
                  name="extraHours"
                  value={form.extraHours}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>

              <div className="md:col-span-2">
                <label className="mb-1 block text-sm font-medium text-slate-700">Trip Type</label>
                <select
                  name="tripType"
                  value={form.tripType}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                >
                  <option value="Local">Local Trip</option>
                  <option value="Outstation">Outstation Trip</option>
                  <option value="Full Day">Full Day</option>
                  <option value="Pickup/Drop">Pickup / Drop</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="mb-1 block text-sm font-medium text-slate-700">Notes / Remarks</label>
                <input
                  type="text"
                  name="notes"
                  placeholder="Additional trip info..."
                  value={form.notes}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>
            </div>
          </section>

          {/* SECTION 3: DYNAMIC CHARGES TABLE */}
          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">3. Charges & Particulars</h2>
              <button
                type="button"
                onClick={addChargeRow}
                className="text-xs font-bold text-cyan-600 hover:text-cyan-700"
              >
                + Add Row
              </button>
            </div>
            <div className="overflow-hidden rounded-lg border border-slate-300 shadow-sm">
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
                    <tr key={index} className="group hover:bg-slate-50 transition-colors">
                      <td className="border-t border-slate-300 py-2 text-center text-xs text-slate-400 font-medium">
                        {index + 1}
                      </td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input
                          type="text"
                          value={charge.name}
                          placeholder="e.g. Driver Bata"
                          onChange={(e) => handleChargeChange(index, "name", e.target.value)}
                          className={inputClass}
                        />
                      </td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input
                          type="text"
                          value={charge.calculation}
                          placeholder="e.g. 400 x 2"
                          onChange={(e) => handleChargeChange(index, "calculation", e.target.value)}
                          className={inputClass}
                        />
                      </td>
                      <td className={`${cellClass} border-t border-l`}>
                        <input
                          type="number"
                          value={charge.amount}
                          placeholder="0.00"
                          onChange={(e) => handleChargeChange(index, "amount", e.target.value)}
                          className={`${inputClass} text-right font-semibold`}
                        />
                      </td>
                      <td className="border-t border-l border-slate-300 text-center">
                        <button
                          type="button"
                          onClick={() => removeChargeRow(index)}
                          className="text-slate-300 hover:text-red-500 group-hover:opacity-100 opacity-0 transition-all"
                        >
                          ×
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* SECTION 4: TOTAL SECTION */}
          <section className="border-t border-slate-100 pt-6">
            <div className="flex flex-col items-end gap-2">
              <div className="flex items-baseline gap-8">
                <span className="text-sm font-bold text-slate-500 uppercase">Grand Total:</span>
                <span className="text-3xl font-black text-slate-900">₹ {grandTotal.toLocaleString("en-IN")}</span>
              </div>
              <p className="text-sm font-medium italic text-slate-500">
                Rupees {amountInWords}
              </p>
            </div>
          </section>

          {/* SECTION 5: FOOTER SECTION */}
          <section className="rounded-lg border border-dashed border-slate-200 p-6">
            <h2 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-400">4. Office & Footer Details</h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Customer Contact Person</label>
                <input
                  type="text"
                  name="contactPerson"
                  value={form.contactPerson}
                  onChange={handleChange}
                  placeholder="Name of person who hired"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Booked By</label>
                <input
                  type="text"
                  name="bookedBy"
                  value={form.bookedBy}
                  onChange={handleChange}
                  placeholder="Agent / Employee name"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Manager Signature Name</label>
                <input
                  type="text"
                  name="managerName"
                  value={form.managerName}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                />
              </div>
            </div>
            
            <div className="mt-6 flex flex-wrap gap-x-8 gap-y-2 text-xs text-slate-400 font-medium">
              <span>Mobile: 9876543210, 8877665544</span>
              <span>Address: 123, Travel Plaza, Main Road, City - 400001</span>
            </div>
          </section>

        </form>
      </main>
    </div>
  );
}
