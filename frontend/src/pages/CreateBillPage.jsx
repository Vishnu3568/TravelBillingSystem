import { useMemo, useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import api from "../services/api.js";

const today = () => new Date().toISOString().slice(0, 10);

const initialForm = {
  date: today(),
  company: "",
  vehicle: "",
  dutySlipNumber: "",
  totalKms: "",
  totalHours: "",
  baseAmount: "",
  driverBata: "",
  parking: "",
  toll: "",
  nightCharges: "",
  otherCharges: "",
  notes: "",
};

// Companies and vehicles will be loaded from the backend
const chargeFields = [
  ["Base Amount", "baseAmount"],
  ["Driver Bata", "driverBata"],
  ["Parking Charges", "parking"],
  ["Toll Charges", "toll"],
  ["Night Charges", "nightCharges"],
  ["Other Charges", "otherCharges"],
];

const moneyFields = chargeFields.map(([, name]) => name);

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  maximumFractionDigits: 0,
});

function formatMoney(value) {
  return `INR ${currencyFormatter.format(Number(value || 0))}`;
}

function numberValue(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function Field({ label, children, hint }) {
  return (
    <label className="block">
      <span className="text-sm font-semibold text-slate-700">{label}</span>
      <div className="mt-2">{children}</div>
      {hint ? <span className="mt-1 block text-xs text-slate-500">{hint}</span> : null}
    </label>
  );
}

function FormSection({ title, description, children }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-6 border-b border-slate-100 pb-4">
        <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
        <p className="mt-1 text-sm leading-6 text-slate-500">{description}</p>
      </div>
      {children}
    </section>
  );
}

const inputClass =
  "h-12 w-full rounded-lg border border-slate-300 bg-white px-4 text-base text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-cyan-600 focus:ring-4 focus:ring-cyan-100";

export default function CreateBillPage() {
  const navigate = useNavigate();
  const { username, logout } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [status, setStatus] = useState("");
  const [generatedBillNumber, setGeneratedBillNumber] = useState("");
  const [errors, setErrors] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isSessionExpired, setIsSessionExpired] = useState(false);
  const [companies, setCompanies] = useState([]);
  const [vehicles, setVehicles] = useState([]);

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

  const grandTotal = useMemo(
    () => moneyFields.reduce((total, field) => total + numberValue(form[field]), 0),
    [form],
  );

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setStatus("");
    setGeneratedBillNumber("");
    setErrors([]);
  };

  const handleReset = () => {
    setForm({ ...initialForm, date: today() });
    setStatus("");
    setGeneratedBillNumber("");
    setErrors([]);
    setIsSessionExpired(false);
  };

  const validateForm = () => {
    const validationErrors = [];
    if (!form.date) validationErrors.push("Bill Date is required.");
    if (!form.company) validationErrors.push("Customer Company is required.");
    if (!form.vehicle) validationErrors.push("Vehicle is required.");
    if (!form.dutySlipNumber.trim()) validationErrors.push("Duty Slip Number is required.");

    [...moneyFields, "totalKms", "totalHours"].forEach((field) => {
      if (Number(form[field] || 0) < 0) {
        validationErrors.push(`${field.replace(/([A-Z])/g, " $1")} cannot be negative.`);
      }
    });

    return validationErrors;
  };

  const buildPayload = () => ({
    billDate: form.date,
    companyName: form.company,
    vehicleName: form.vehicle,
    dutySlipNo: form.dutySlipNumber,
    totalKms: numberValue(form.totalKms),
    totalHours: numberValue(form.totalHours),
    baseAmount: numberValue(form.baseAmount),
    driverBata: numberValue(form.driverBata),
    parking: numberValue(form.parking),
    toll: numberValue(form.toll),
    nightCharges: numberValue(form.nightCharges),
    otherCharges: numberValue(form.otherCharges),
    notes: form.notes,
  });

  const handleSignInAgain = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus("");
    setGeneratedBillNumber("");
    setIsSessionExpired(false);

    const validationErrors = validateForm();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    try {
      setErrors([]);
      setIsSaving(true);
      const response = await api.post("/bills", buildPayload());
      setGeneratedBillNumber(response.data.billNumber);
      setStatus(`Bill saved successfully. Generated bill number: ${response.data.billNumber}`);
      setForm({ ...initialForm, date: today() });
    } catch (requestError) {
      const statusCode = requestError.response?.status;
      if (statusCode === 401 || statusCode === 403) {
        setIsSessionExpired(true);
        setErrors([]);
        return;
      }

      const responseData = requestError.response?.data;
      if (responseData?.message) {
        setErrors([responseData.message]);
      } else if (responseData?.errors) {
        setErrors(Object.values(responseData.errors).flat());
      } else {
        setErrors(["Unable to save bill. Please check the form and try again."]);
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">
              Travel Billing System
            </p>
            <h1 className="text-2xl font-semibold">Create Bill</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              to="/owner-dashboard"
            >
              Dashboard
            </Link>
            <button
              className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              type="button"
              onClick={logout}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-5 py-8">
        <div className="mb-7 overflow-hidden rounded-lg bg-slate-950 shadow-panel">
          <div className="grid gap-6 p-6 text-white lg:grid-cols-[1fr_340px] lg:p-8">
            <div>
              <p className="text-sm font-semibold uppercase tracking-widest text-cyan-200">Billing module</p>
              <h2 className="mt-3 text-4xl font-semibold tracking-tight">New customer bill</h2>
              <p className="mt-3 max-w-2xl text-base leading-7 text-slate-300">
                Prepare a clean customer invoice from duty slip details, trip usage, and charge heads. The total updates instantly as amounts change.
              </p>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/10 p-5">
              <p className="text-xs font-semibold uppercase tracking-widest text-slate-300">Prepared by</p>
              <p className="mt-2 text-xl font-semibold">{username}</p>
              <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-md bg-white/10 p-3">
                  <p className="text-slate-300">Bill No.</p>
                  <p className="mt-1 font-semibold">{generatedBillNumber || "AUTO-GENERATED"}</p>
                </div>
                <div className="rounded-md bg-white/10 p-3">
                  <p className="text-slate-300">Grand Total</p>
                  <p className="mt-1 font-semibold">{formatMoney(grandTotal)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <form className="grid gap-7 xl:grid-cols-[minmax(0,1fr)_390px]" onSubmit={handleSubmit}>
          <div className="space-y-7">
            {isSessionExpired ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-5 shadow-sm">
                <p className="text-lg font-semibold text-amber-900">Session expired</p>
                <p className="mt-2 text-sm leading-6 text-amber-800">
                  Your login token is expired or invalid. Sign in again before saving this bill.
                </p>
                <button
                  className="mt-4 rounded-md bg-amber-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-800"
                  type="button"
                  onClick={handleSignInAgain}
                >
                  Back to sign in
                </button>
              </div>
            ) : null}

            {errors.length ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-5 shadow-sm">
                <p className="text-sm font-semibold text-red-800">Please fix the following:</p>
                <ul className="mt-3 space-y-1 text-sm text-red-700">
                  {errors.map((error) => (
                    <li key={error}>{error}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <FormSection
              title="Bill Details"
              description="Select the customer account and vehicle for this billing entry."
            >
              <div className="grid gap-5 md:grid-cols-2">
                <Field label="Bill Number" hint="Final number will be assigned after save.">
                  <input
                    className={`${inputClass} bg-slate-50 font-semibold text-slate-500`}
                    readOnly
                    value="AUTO-GENERATED"
                  />
                </Field>

                <Field label="Bill Date">
                  <input className={inputClass} name="date" type="date" value={form.date} onChange={handleChange} />
                </Field>

                <Field label="Customer Company">
                  <select className={inputClass} name="company" value={form.company} onChange={handleChange}>
                    <option value="">Select company</option>
                    {companies.map((c) => (
                      <option key={c.id} value={c.name}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </Field>

                <Field label="Vehicle">
                  <select className={inputClass} name="vehicle" value={form.vehicle} onChange={handleChange}>
                    <option value="">Select vehicle</option>
                    {vehicles.map((v) => (
                      <option key={v.id} value={`${v.registrationNumber} - ${v.type}`}>
                        {v.registrationNumber} ({v.type})
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
            </FormSection>

            <FormSection
              title="Trip Details"
              description="Capture operational details from the duty slip for later audit and reporting."
            >
              <div className="grid gap-5 md:grid-cols-3">
                <div className="md:col-span-1">
                  <Field label="Duty Slip Number">
                    <input
                      className={inputClass}
                      name="dutySlipNumber"
                      placeholder="DS-2026-001"
                      value={form.dutySlipNumber}
                      onChange={handleChange}
                    />
                  </Field>
                </div>

                <Field label="Total KMs">
                  <input
                    className={inputClass}
                    min="0"
                    name="totalKms"
                    placeholder="0"
                    type="number"
                    value={form.totalKms}
                    onChange={handleChange}
                  />
                </Field>

                <Field label="Total Hours">
                  <input
                    className={inputClass}
                    min="0"
                    name="totalHours"
                    placeholder="0"
                    type="number"
                    value={form.totalHours}
                    onChange={handleChange}
                  />
                </Field>
              </div>
            </FormSection>

            <FormSection
              title="Charges"
              description="Enter all charge heads. Grand total is calculated automatically from these values."
            >
              <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                {chargeFields.map(([label, name]) => (
                  <Field key={name} label={label}>
                    <input
                      className={inputClass}
                      min="0"
                      name={name}
                      placeholder="0"
                      type="number"
                      value={form[name]}
                      onChange={handleChange}
                    />
                  </Field>
                ))}
              </div>
            </FormSection>

            <FormSection title="Notes" description="Optional internal notes, trip remarks, or billing instructions.">
              <textarea
                className={`${inputClass} min-h-36 resize-y py-3 leading-6`}
                name="notes"
                placeholder="Add billing instructions, trip remarks, or payment notes"
                value={form.notes}
                onChange={handleChange}
              />
            </FormSection>
          </div>

          <aside className="space-y-6 xl:sticky xl:top-6 xl:self-start">
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
              <p className="text-sm font-semibold uppercase tracking-widest text-slate-500">Invoice Summary</p>
              <p className="mt-4 text-sm text-slate-500">Grand Total</p>
              <p className="mt-1 text-4xl font-semibold tracking-tight text-slate-950">{formatMoney(grandTotal)}</p>

              <div className="mt-6 rounded-lg bg-slate-50 p-4">
                <div className="space-y-3 text-sm">
                  {chargeFields.map(([label, field]) => (
                    <div className="flex justify-between gap-4" key={field}>
                      <span className="text-slate-500">{label}</span>
                      <span className="font-semibold text-slate-800">{formatMoney(form[field])}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {status ? (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold leading-6 text-emerald-800">
                <p>{status}</p>
                {generatedBillNumber ? <p className="mt-1">Bill Number: {generatedBillNumber}</p> : null}
              </div>
            ) : null}

            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <button
                className="flex h-12 w-full items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 focus:outline-none focus:ring-4 focus:ring-slate-300 disabled:cursor-not-allowed disabled:bg-slate-400"
                type="submit"
                disabled={isSaving}
              >
                {isSaving ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                    Saving Bill...
                  </>
                ) : (
                  "Save Bill"
                )}
              </button>
              <button
                className="mt-3 h-12 w-full rounded-lg border border-slate-300 px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-200"
                type="button"
                onClick={handleReset}
                disabled={isSaving}
              >
                Reset Form
              </button>
              <button
                className="mt-3 h-12 w-full rounded-lg px-4 text-sm font-semibold text-slate-500 transition hover:bg-slate-50"
                type="button"
                onClick={() => navigate("/owner-dashboard")}
              >
                Cancel and return
              </button>
            </div>
          </aside>
        </form>
      </section>
    </main>
  );
}
