import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  ArrowLeft, 
  FileDown, 
  Printer, 
  Calendar, 
  Building2, 
  Car, 
  FileText,
  User,
  IndianRupee,
  MapPin,
  Clock
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
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
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
          </div>
        </div>

        {/* Invoice Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden print:shadow-none print:border-none">
          {/* Header */}
          <div className="bg-slate-900 p-8 text-white">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Sri Tulja Bhavani Travels</h1>
                <p className="text-slate-400 mt-1 uppercase tracking-widest text-sm">Professional Travel Solutions</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-mono text-indigo-400">{bill.billNumber}</div>
                <div className="text-slate-400 mt-1">Invoice Number</div>
              </div>
            </div>
          </div>

          <div className="p-8">
            {/* Info Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
              <div className="space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Bill To</h3>
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-indigo-50 rounded-lg">
                    <Building2 className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 text-lg">{bill.companyName}</div>
                    <div className="text-slate-500 text-sm flex items-center gap-1 mt-1">
                      <FileText className="w-4 h-4" />
                      Duty Slip: {bill.dutySlipNo || "-"}
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Travel Details</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    {bill.billDate ? format(new Date(bill.billDate), "dd MMM yyyy") : "-"}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <Car className="w-4 h-4 text-slate-400" />
                    {bill.vehicleName || "-"}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <MapPin className="w-4 h-4 text-slate-400" />
                    {bill.totalKms} KMs
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <Clock className="w-4 h-4 text-slate-400" />
                    {bill.totalHours} Hours
                  </div>
                </div>
              </div>
            </div>

            {/* Charges Table */}
            <div className="border border-slate-200 rounded-xl overflow-hidden mb-8">
              <table className="w-full text-left">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Description</th>
                    <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="px-6 py-4 text-slate-700">Base Amount</td>
                    <td className="px-6 py-4 text-right font-medium">₹{bill.baseAmount.toLocaleString()}</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 text-slate-700">Driver Bata</td>
                    <td className="px-6 py-4 text-right font-medium">₹{bill.driverBata.toLocaleString()}</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 text-slate-700">Parking Charges</td>
                    <td className="px-6 py-4 text-right font-medium">₹{bill.parking.toLocaleString()}</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 text-slate-700">Toll Charges</td>
                    <td className="px-6 py-4 text-right font-medium">₹{bill.toll.toLocaleString()}</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 text-slate-700">Night Charges</td>
                    <td className="px-6 py-4 text-right font-medium">₹{bill.nightCharges.toLocaleString()}</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 text-slate-700">Other Charges</td>
                    <td className="px-6 py-4 text-right font-medium">₹{bill.otherCharges.toLocaleString()}</td>
                  </tr>
                </tbody>
                <tfoot className="bg-slate-50 font-bold">
                  <tr>
                    <td className="px-6 py-6 text-slate-900 text-lg">Grand Total</td>
                    <td className="px-6 py-6 text-right text-2xl text-indigo-600">
                      ₹{bill.grandTotal.toLocaleString()}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Note & Created By */}
            <div className="flex flex-col md:flex-row justify-between items-end gap-8 pt-8 border-t border-slate-100">
              <div className="max-w-md w-full">
                {bill.notes && (
                  <div className="mb-4">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Notes</h4>
                    <p className="text-sm text-slate-600 italic">"{bill.notes}"</p>
                  </div>
                )}
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <User className="w-3 h-3" />
                  Generated by {bill.createdBy} on {format(new Date(bill.createdAt), "dd MMM yyyy, hh:mm a")}
                </div>
              </div>
              
              <div className="text-center md:text-right w-48">
                <div className="h-16 border-b border-slate-300 mb-2"></div>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">Authorized Signature</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
