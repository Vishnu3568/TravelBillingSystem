import React, { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  ArrowLeft, 
  FileDown, 
  Printer, 
  Pencil
} from "lucide-react";
import api from "../services/api";
import { format } from "date-fns";
import { numberToWords } from "../utils/numberToWords";

export default function BillViewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [bill, setBill] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const fetchBill = async () => {
      try {
        const response = await api.get(`/bills/${id}`);
        setBill(response.data);
      } catch (error) {
        console.error("Failed to fetch bill:", error);
        alert("Bill not found.");
        navigate("/bill-history");
      } finally {
        setLoading(false);
      }
    };
    fetchBill();
  }, [id, navigate]);

  const handleDownloadPdf = async () => {
    setDownloading(true);
    try {
      const response = await api.get(`/bills/${id}/pdf`, {
        responseType: "blob",
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `invoice-${bill?.billNumber || id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Failed to download PDF:", error);
      alert("Failed to download invoice.");
    } finally {
      setDownloading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  // CALCULATION LOGIC FOR DISPLAY
  const tripRowData = useMemo(() => {
    if (!bill) return null;

    const kms = Number(bill.totalKms || 0);
    const hrs = Number(bill.totalHours || 0);
    const vType = (bill.vehicleType || "SEDAN").toUpperCase();
    const isLongTrip = kms > 200;

    let extraKmText = "";
    let extraHrText = "";
    let amtText = "";
    let rowTotal = 0;

    if (isLongTrip) {
      const rate = vType.includes("CRYSTA") ? 18 : 14;
      amtText = `${kms}x${rate}`;
      rowTotal = kms * rate;
    } else {
      amtText = "8/80";
      rowTotal = 2800;

      if (kms > 80) {
        const extraKm = kms - 80;
        extraKmText = `${extraKm}x16`;
        rowTotal += extraKm * 16;
      }

      if (hrs > 8) {
        const extraHr = hrs - 8;
        extraHrText = `${extraHr}x130`;
        rowTotal += extraHr * 130;
      }
    }

    // Filter dynamic charges to exclude the ones we just put in columns
    // We identify system charges by their name
    const additionalCharges = (bill.dynamicCharges || []).filter(c => {
      const name = c.name.toLowerCase();
      if (name.includes("base amount")) return false;
      if (name.includes("extra km")) return false;
      if (name.includes("extra hours")) return false;
      if (name.includes("distance charge")) return false;
      return true;
    });

    return {
      extraKmText,
      extraHrText,
      amtText,
      rowTotal,
      additionalCharges
    };
  }, [bill]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-slate-600 font-medium">Loading bill details...</p>
        </div>
      </div>
    );
  }

  if (!bill) return null;

  const words = numberToWords(bill.grandTotal).toUpperCase();

  return (
    <div className="min-h-screen bg-white p-0 md:p-8 print:p-0">
      <div className="max-w-[21cm] mx-auto">
        {/* Navigation & Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4 print:hidden px-4 md:px-0">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back to History</span>
          </button>
          
          <div className="flex gap-3">
            <button
              onClick={handlePrint}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-50 transition-all font-medium"
            >
              <Printer className="w-4 h-4" />
              Print
            </button>
            <button
              onClick={handleDownloadPdf}
              disabled={downloading}
              className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all font-medium shadow-sm disabled:opacity-70"
            >
              <FileDown className="w-4 h-4" />
              {downloading ? "Downloading..." : "Download PDF"}
            </button>
            <button
              onClick={() => navigate(`/edit-bill/${bill.id}`)}
              className="flex items-center gap-2 px-6 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-all font-medium shadow-sm"
            >
              <Pencil className="w-4 h-4" />
              Edit Bill
            </button>
          </div>
        </div>

        {/* Traditional Bill Format */}
        <div className="bill-container bg-white p-[1cm] md:p-[1.5cm] print:p-0 font-serif text-black leading-tight">
          
          {/* Header */}
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold mb-0" style={{ fontFamily: '"Times New Roman", Times, serif' }}>SRI TULJA BHAVANI TRAVELS</h1>
            <h2 className="text-xl font-bold text-red-600 mb-1">RENT-A-CAR</h2>
            <p className="text-xs mb-0">1-11-113/3, P2 Sai Shikara Apartments, Shyamlal Building Begumpet, Hyderabad - 500016</p>
            <p className="text-xs underline">srituljabhavanitravels.rentacar@gmail.com</p>
          </div>

          <div className="w-full mb-4">
            <table className="w-full text-sm">
              <tbody>
                <tr>
                  <td className="w-1/2 py-1">
                    <p>Bill No. {bill.billNumber}</p>
                    <p className="mt-2">To.</p>
                    <p className="font-bold">{bill.companyName}</p>
                  </td>
                  <td className="w-1/2 text-right align-top py-1">
                    <p>Date: {bill.billDate ? format(new Date(bill.billDate), "dd-MM-yyyy") : "-"}</p>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Main Table */}
          <div className="w-full mb-4">
            <table className="w-full border-collapse border border-black text-[11px]">
              <thead>
                <tr>
                  <th className="border border-black p-1 text-center font-bold">Duty Slip No</th>
                  <th className="border border-black p-1 text-center font-bold">Date</th>
                  <th className="border border-black p-1 text-center font-bold">Vehicle No</th>
                  <th className="border border-black p-1 text-center font-bold">Total Kms</th>
                  <th className="border border-black p-1 text-center font-bold">Total Hrs</th>
                  <th className="border border-black p-1 text-center font-bold">Extra Kms</th>
                  <th className="border border-black p-1 text-center font-bold">Extra Hrs</th>
                  <th className="border border-black p-1 text-center font-bold">Amt</th>
                  <th className="border border-black p-1 text-center font-bold">Total Amount</th>
                </tr>
              </thead>
              <tbody>
                {/* Main Trip Row */}
                <tr>
                  <td className="border border-black p-1 text-center">{bill.dutySlipNo || ""}</td>
                  <td className="border border-black p-1 text-center whitespace-nowrap">
                    {bill.tripDate ? format(new Date(bill.tripDate), "dd-MM-yy") : ""}
                  </td>
                  <td className="border border-black p-1 text-left">{bill.vehicleName || ""}</td>
                  <td className="border border-black p-1 text-right">{bill.totalKms || ""}</td>
                  <td className="border border-black p-1 text-right">{bill.totalHours || ""}</td>
                  <td className="border border-black p-1 text-center">{tripRowData.extraKmText}</td>
                  <td className="border border-black p-1 text-center">{tripRowData.extraHrText}</td>
                  <td className="border border-black p-1 text-center">{tripRowData.amtText}</td>
                  <td className="border border-black p-1 text-right font-bold">
                    {tripRowData.rowTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>

                {/* Additional Charges Rows */}
                {tripRowData.additionalCharges.map((charge, idx) => (
                  <tr key={idx}>
                    <td className="border border-black p-1" colSpan={7}></td>
                    <td className="border border-black p-1 text-center">{charge.name}</td>
                    <td className="border border-black p-1 text-right font-bold">
                      {charge.amount?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}

                {/* Grand Total Row */}
                <tr>
                  <td className="border-none" colSpan={7}></td>
                  <td className="border border-black p-1 text-center font-bold">Grand Total</td>
                  <td className="border border-black p-1 text-right font-bold text-[13px]">
                    {bill.grandTotal?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Amount in Words */}
          <div className="mb-8 text-[12px]">
            <p><span className="font-bold italic">Rupees (in words):</span> <span className="ml-2 font-bold uppercase">{words} ONLY</span></p>
          </div>

          {/* Footer Section */}
          <div className="flex justify-between items-end mt-12">
            <div className="space-y-4 text-[12px]">
              <p className="border-b border-black inline-block min-w-[150px]">For {bill.contactPerson || ""}</p>
              <p>Booked by <span className="font-bold">{bill.companyName}</span></p>
            </div>
            <div className="text-right space-y-12 text-[12px]">
              <p className="font-bold">For Sri Tulja Bhavani Travels</p>
              <p className="font-bold mr-8">Manager</p>
            </div>
          </div>

          <div className="text-right text-[9px] mt-4">
            <p>Mobile: 98480 12345, 98480 67890</p>
          </div>

        </div>
      </div>
      
      {/* Print Specific Styles */}
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          @page { size: A4; margin: 0; }
          body { background: white !important; -webkit-print-color-adjust: exact; }
          .print\\:hidden { display: none !important; }
          .bill-container { padding: 1.5cm !important; width: 100% !important; border: none !important; box-shadow: none !important; }
          * { font-family: "Times New Roman", Times, serif !important; }
        }
        .bill-container {
          box-shadow: none;
        }
      `}} />
    </div>
  );
}
