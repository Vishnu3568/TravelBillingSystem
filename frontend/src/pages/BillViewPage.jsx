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

  // REFINED CALCULATION LOGIC FOR ROW-BY-ROW DISPLAY
  const billRows = useMemo(() => {
    if (!bill) return [];

    const kms = Number(bill.totalKms || 0);
    const hrs = Number(bill.totalHours || 0);
    const vType = (bill.vehicleType || "SEDAN").toUpperCase();
    const isLongTrip = kms > 200;

    const rows = [];

    // 1. BASE TRIP ROW
    if (isLongTrip) {
      const rate = vType.includes("CRYSTA") ? 18 : 14;
      rows.push({
        isFirst: true,
        extraKm: "",
        extraHr: "",
        amt: `${kms}x${rate}`,
        total: kms * rate
      });
    } else {
      rows.push({
        isFirst: true,
        extraKm: "",
        extraHr: "",
        amt: "8/80",
        total: 2800
      });

      // 2. EXTRA KM ROW
      if (kms > 80) {
        const ekm = kms - 80;
        rows.push({
          isFirst: false,
          extraKm: `${ekm}x16`,
          extraHr: "",
          amt: "",
          total: ekm * 16
        });
      }

      // 3. EXTRA HOURS ROW
      if (hrs > 8) {
        const eh = hrs - 8;
        rows.push({
          isFirst: false,
          extraKm: "",
          extraHr: `${eh}x130`,
          amt: "",
          total: eh * 130
        });
      }
    }

    // 4. ADDITIONAL CHARGES
    const additional = (bill.dynamicCharges || []).filter(c => {
      const name = c.name.toLowerCase();
      return !name.includes("base amount") && 
             !name.includes("extra km") && 
             !name.includes("extra hours") && 
             !name.includes("distance charge") &&
             Number(c.amount) > 0;
    });

    additional.forEach(c => {
      rows.push({
        isFirst: false,
        extraKm: "",
        extraHr: "",
        amt: c.name,
        total: c.amount
      });
    });

    return rows;
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

        <div className="bill-paper-wrapper mx-auto w-[21cm] min-h-[29.6cm] bg-white shadow-2xl print:shadow-none print:w-full print:min-h-0 mb-20 print:mb-0 border border-slate-200 overflow-hidden">
          <div className="bill-container p-0 text-black leading-tight border-[4px] border-black h-full min-h-[29.6cm] print:min-h-0" style={{ fontFamily: '"Bookman Old Style", serif' }}>
            <div className="border-[1.5px] border-black p-8 h-full min-h-[29.4cm] print:min-h-0 relative flex flex-col overflow-hidden">
            {/* Header Section */}
            <div className="header-section text-center mb-8">
              <p className="text-[12px] mb-2 font-bold" style={{ fontFamily: '"Imprint MT Shadow", Georgia, serif' }}>Mobile No: 94405 22 814, 99892 08711, 9000 240 410</p>
              <h1 className="header-title text-5xl font-bold mb-1" style={{ fontFamily: '"Imprint MT Shadow", Georgia, serif', letterSpacing: '2px' }}>SRI TULJA BHAVANI TRAVELS</h1>
              <h2 className="header-title text-2xl font-bold text-red-600 mb-2" style={{ fontFamily: '"Imprint MT Shadow", Georgia, serif' }}>RENT-A-CAR</h2>
              <p className="header-address text-[11px] mb-0" style={{ fontFamily: '"Imprint MT Shadow", Georgia, serif' }}>1-11-113/3, P2 Sai Shikara Apartments, Shyamlal Building Begumpet, Hyderabad - 500016</p>
              <p className="header-contact text-[11px] underline" style={{ fontFamily: '"Imprint MT Shadow", Georgia, serif' }}>srituljabhavanitravels.rentacar@gmail.com</p>
            </div>

            <div className="w-full mb-6 px-2">
              <table className="w-full text-[15px]">
                <tbody>
                  <tr className="border-b border-slate-300">
                    <td className="w-1/2 py-2">
                      <p style={{ whiteSpace: 'nowrap' }}>Bill No. <span className="font-bold">{bill.billNumber}</span></p>
                    </td>
                    <td className="w-1/2 text-right py-2">
                      <p style={{ whiteSpace: 'nowrap' }}>Date: <span className="font-bold">{bill.billDate ? format(new Date(bill.billDate), "dd-MM-yyyy") : "-"}</span></p>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 pt-4" colSpan={2}>
                      <p className="text-[14px]">To.</p>
                      <p className="font-bold text-lg">{bill.companyName}</p>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

          {/* Main Table */}
          <div className="w-full mb-6">
            <table className="w-full border-collapse border-2 border-black text-[13px]">
              <thead>
                <tr className="bg-slate-50">
                  <th className="border-2 border-black p-2 text-center font-bold">Duty Slip No</th>
                  <th className="border-2 border-black p-2 text-center font-bold">Date</th>
                  <th className="border-2 border-black p-2 text-center font-bold">Vehicle No</th>
                  <th className="border-2 border-black p-2 text-center font-bold">Total Kms</th>
                  <th className="border-2 border-black p-2 text-center font-bold">Total Hrs</th>
                  <th className="border-2 border-black p-2 text-center font-bold">Extra Kms</th>
                  <th className="border-2 border-black p-2 text-center font-bold">Extra Hrs</th>
                  <th className="border-2 border-black p-2 text-center font-bold">Amt</th>
                  <th className="border-2 border-black p-2 text-center font-bold">Total Amount</th>
                </tr>
              </thead>
              <tbody>
                {billRows.map((row, idx) => (
                  <tr key={idx} className="min-h-[25px]">
                    <td className="border-2 border-black p-2 text-center">{row.isFirst ? (bill.dutySlipNo || "") : ""}</td>
                    <td className="border-2 border-black p-2 text-center whitespace-nowrap">
                      {row.isFirst && bill.tripDate ? format(new Date(bill.tripDate), "dd-MM-yy") : ""}
                    </td>
                    <td className="border-2 border-black p-2 text-left whitespace-nowrap">{row.isFirst ? (bill.vehicleName || "") : ""}</td>
                    <td className="border-2 border-black p-2 text-right">{row.isFirst ? (bill.totalKms || "") : ""}</td>
                    <td className="border-2 border-black p-2 text-right">{row.isFirst ? (bill.totalHours || "") : ""}</td>
                    <td className="border-2 border-black p-2 text-center">{row.extraKm}</td>
                    <td className="border-2 border-black p-2 text-center">{row.extraHr}</td>
                    <td className="border-2 border-black p-2 text-center font-bold">{row.amt}</td>
                    <td className="border-2 border-black p-2 text-right font-bold">
                      {row.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
                
                {/* Empty rows to fill space if needed */}
                {[...Array(Math.max(0, 5 - billRows.length))].map((_, i) => (
                  <tr key={`empty-${i}`} className="h-8">
                    {[...Array(9)].map((_, j) => (
                      <td key={j} className="border-2 border-black"></td>
                    ))}
                  </tr>
                ))}

                {/* Grand Total Row */}
                <tr>
                  <td className="border-none" colSpan={7}></td>
                  <td className="border-2 border-black p-2 text-center font-bold bg-slate-50">Grand Total</td>
                  <td className="border-2 border-black p-2 text-right font-bold text-[15px] bg-slate-50">
                    {bill.grandTotal?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Amount in Words */}
          <div className="mb-8 text-[14px]">
            <p><span className="font-bold">Rupees (in words):</span> <span className="ml-2 font-bold uppercase underline decoration-solid underline-offset-4">{words} ONLY</span></p>
          </div>

          {/* Spacer to push footer to bottom */}
          <div className="flex-grow"></div>

          {/* Footer Section (Signatures) */}
          <div className="footer-section mt-auto">
            <div className="space-y-4 text-[12px]">
              <p className="border-b border-black inline-block min-w-[150px]">For {bill.contactPerson || ""}</p>
              <p>Booked by <span className="font-bold">{bill.companyName}</span></p>
            </div>
            <div className="text-right space-y-12">
              <p className="font-bold text-[13px]">For Sri Tulja Bhavani Travels</p>
              <p className="font-bold mr-12 text-[12px]">Manager</p>
            </div>
          </div>

          <div className="header-contact text-right text-[12px] mt-10 pt-4" style={{ fontFamily: '"Imprint MT Shadow", Georgia, serif', whiteSpace: 'nowrap' }}>
            {/* Empty space for bottom border logic if needed */}
          </div>
        </div> {/* Inner border end */}
        </div> {/* Outer border end */}
        </div> {/* Paper wrapper end */}
        </div> {/* max-w-[21cm] end */}
      
      {/* Print Specific Styles */}
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          @page { size: A4; margin: 0.5cm; }
          body { background: white !important; -webkit-print-color-adjust: exact; margin: 0 !important; }
          .print\\:hidden { display: none !important; }
          .bill-paper-wrapper { width: 100% !important; margin: 0 !important; padding: 0 !important; box-shadow: none !important; min-height: 0 !important; border: none !important; height: auto !important; }
          .bill-container { border: 4px solid black !important; padding: 0 !important; width: 100% !important; min-height: 0 !important; height: auto !important; break-inside: avoid; }
          .bill-container > div { padding: 1cm !important; border: 1.5px solid black !important; min-height: 0 !important; height: auto !important; }
          * { font-family: "Bookman Old Style", serif !important; }
          .header-title, .header-address, .header-contact { font-family: "Imprint MT Shadow", Georgia, serif !important; }
        }
        .bill-paper-wrapper {
          overflow: hidden;
        }
      `}} />
    </div>
  );
}
