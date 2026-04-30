import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  ArrowLeft, 
  FileDown, 
  Printer, 
  Pencil
} from "lucide-react";
import api from "../services/api";
import { format } from "date-fns";

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

  return (
    <div className="min-h-screen bg-slate-100 p-4 md:p-8 print:p-0 print:bg-white">
      <div className="max-w-5xl mx-auto">
        {/* Navigation & Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4 print:hidden">
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
        <div className="bg-white p-8 md:p-12 shadow-sm border border-slate-200 print:shadow-none print:border-none print:p-4 font-serif text-slate-900">
          
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold tracking-tight mb-1" style={{ fontFamily: 'serif' }}>SRI TULJA BHAVANI TRAVELS</h1>
            <h2 className="text-2xl font-bold text-red-600 mb-2">RENT-A-CAR</h2>
            <p className="text-sm">1-11-113/3, P2 Sai Shikara Apartments, Shyamlal Building Begumpet, Hyderabad - 500016</p>
            <p className="text-sm underline">srituljabhavanitravels.rentacar@gmail.com</p>
          </div>

          <div className="border-t border-slate-300 pt-6 mb-6">
            <div className="flex justify-between items-start text-lg">
              <div className="space-y-1">
                <p><span className="font-medium">Bill No.</span> {bill.billNumber}</p>
                <p className="mt-4"><span className="font-medium">To.</span></p>
                <p className="font-bold text-xl">{bill.companyName}</p>
              </div>
              <div className="text-right">
                <p><span className="font-medium">Date:</span> {bill.billDate ? format(new Date(bill.billDate), "dd-MM-yyyy") : "-"}</p>
              </div>
            </div>
          </div>

          {/* Main Table */}
          <div className="overflow-x-auto mb-6">
            <table className="w-full border-collapse border border-slate-400 text-sm">
              <thead>
                <tr className="bg-slate-50">
                  <th className="border border-slate-400 p-2 text-center font-bold">Duty Slip No.</th>
                  <th className="border border-slate-400 p-2 text-center font-bold">Date</th>
                  <th className="border border-slate-400 p-2 text-center font-bold">Vehicle No.</th>
                  <th className="border border-slate-400 p-2 text-center font-bold">Total Kms.</th>
                  <th className="border border-slate-400 p-2 text-center font-bold">Total Hrs.</th>
                  <th className="border border-slate-400 p-2 text-center font-bold">Extra Kms.</th>
                  <th className="border border-slate-400 p-2 text-center font-bold">Extra Hrs.</th>
                  <th className="border border-slate-400 p-2 text-center font-bold">Amt</th>
                  <th className="border border-slate-400 p-2 text-center font-bold">Total Amount</th>
                </tr>
              </thead>
              <tbody>
                {/* First Row with trip details */}
                <tr>
                  <td className="border border-slate-400 p-2 text-center">{bill.dutySlipNo || "-"}</td>
                  <td className="border border-slate-400 p-2 text-center">{bill.tripDate ? format(new Date(bill.tripDate), "dd-MM-yy") : "-"}</td>
                  <td className="border border-slate-400 p-2 text-center">
                    {bill.vehicleName} {bill.acNonAc && `(${bill.acNonAc})`}
                  </td>
                  <td className="border border-slate-400 p-2 text-center">{bill.totalKms}</td>
                  <td className="border border-slate-400 p-2 text-center">{bill.totalHours}</td>
                  <td className="border border-slate-400 p-2 text-center">{bill.extraKms || ""}</td>
                  <td className="border border-slate-400 p-2 text-center">{bill.extraHours || ""}</td>
                  
                  {/* Charges Rendered as Rows inside Table */}
                  <td className="border border-slate-400 p-2 text-center align-top" rowSpan={bill.dynamicCharges?.length || 1}>
                    {bill.dynamicCharges?.[0]?.calculation || bill.dynamicCharges?.[0]?.name || ""}
                  </td>
                  <td className="border border-slate-400 p-2 text-right font-bold align-top" rowSpan={bill.dynamicCharges?.length || 1}>
                    {bill.dynamicCharges?.[0]?.amount?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>

                {/* Additional Charge Rows */}
                {bill.dynamicCharges?.slice(1).map((charge, idx) => (
                  <tr key={idx}>
                    <td className="border border-slate-400 p-2" colSpan={7}></td>
                    <td className="border border-slate-400 p-2 text-center">{charge.name}</td>
                    <td className="border border-slate-400 p-2 text-right font-bold">
                      {charge.amount?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}

                {/* Grand Total Row */}
                <tr>
                  <td className="border-none p-2" colSpan={7}></td>
                  <td className="border border-slate-400 p-2 text-center font-bold bg-slate-50">Grand Total</td>
                  <td className="border border-slate-400 p-2 text-right font-bold text-lg bg-slate-50">
                    {bill.grandTotal?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Amount in Words */}
          <div className="mb-12 text-lg">
            <p><span className="font-bold italic">Rupees (in words):</span> <span className="ml-4 font-bold uppercase">{bill.amountInWords || "One Thousand Five Hundred Fifty only"}</span></p>
          </div>

          {/* Footer Section */}
          <div className="flex justify-between items-end mt-12 mb-8">
            <div className="space-y-4">
              <p className="underline underline-offset-4">For {bill.contactPerson || "Mr. Manjunath"}</p>
              <p>Booked by <span className="font-bold">{bill.companyName}</span></p>
            </div>
            <div className="text-right space-y-12">
              <p className="font-bold text-lg">For Sri Tulja Bhavani Travels</p>
              <p className="font-bold mr-8">Manager</p>
            </div>
          </div>

          <div className="text-right text-sm font-medium border-t border-slate-200 pt-4">
            <p>Mobile: 98480 12345, 98480 67890</p>
          </div>

        </div>
      </div>
      
      {/* Print Specific Styles */}
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          @page { size: A4; margin: 1cm; }
          body { background: white !important; }
          .print\\:hidden { display: none !important; }
          .font-serif { font-family: 'Times New Roman', Times, serif !important; }
        }
      `}} />
    </div>
  );
}
