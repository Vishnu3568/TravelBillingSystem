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

/**
 * BillViewPage - Strict MS Word Replication
 * Optimized for A4 Printing with traditional travel agency aesthetics.
 */
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

  const rate = (n) => Math.floor(n);

  const handlePrint = () => {
    window.print();
  };

  /**
   * Generates rows for the main invoice table.
   * Follows the "Word" requirement of dense, multi-line content.
   */
  const billRows = useMemo(() => {
    if (!bill) return [];

    const kms = Number(bill.totalKms || 0);
    const hrs = Number(bill.totalHours || 0);
    const vType = (bill.vehicleType || "SEDAN").toUpperCase();
    const isLongTrip = kms > 200;

    const rows = [];

    // 1. BASE TRIP ROW
    if (isLongTrip) {
      const tripRate = vType.includes("CRYSTA") ? 18 : 14;
      rows.push({
        type: 'trip',
        dutySlip: bill.dutySlipNo || "",
        date: bill.tripDate ? format(new Date(bill.tripDate), "dd-MM-yy") : "",
        vehicle: `${bill.vehicleName || ""}\n${vType}`,
        kms: rate(kms),
        hrs: rate(hrs),
        extraKm: "",
        extraHr: "",
        amt: `${rate(kms)}x${rate(tripRate)}`,
        total: kms * tripRate
      });
    } else {
      rows.push({
        type: 'trip',
        dutySlip: bill.dutySlipNo || "",
        date: bill.tripDate ? format(new Date(bill.tripDate), "dd-MM-yy") : "",
        vehicle: `${bill.vehicleName || ""}\n${vType}`,
        kms: rate(kms),
        hrs: rate(hrs),
        extraKm: "",
        extraHr: "",
        amt: "8/80",
        total: 2800
      });

      // 2. EXTRA KM ROW
      if (kms > 80) {
        const ekm = kms - 80;
        rows.push({
          type: 'extra',
          dutySlip: "",
          date: "",
          vehicle: "",
          kms: "",
          hrs: "",
          extraKm: `${rate(ekm)}x16`,
          extraHr: "",
          amt: "",
          total: ekm * 16
        });
      }

      // 3. EXTRA HOURS ROW
      if (hrs > 8) {
        const eh = hrs - 8;
        rows.push({
          type: 'extra',
          dutySlip: "",
          date: "",
          vehicle: "",
          kms: "",
          hrs: "",
          extraKm: "",
          extraHr: `${rate(eh)}x130`,
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
        type: 'charge',
        dutySlip: "",
        date: "",
        vehicle: "",
        kms: "",
        hrs: "",
        extraKm: "",
        extraHr: "",
        amt: c.name,
        total: c.amount
      });
    });

    return rows;
  }, [bill]);

  if (loading) return <div className="p-10">Loading...</div>;
  if (!bill) return null;

  const words = numberToWords(bill.grandTotal);

  return (
    <div className="min-h-screen bg-slate-100 p-0 md:p-10 print:p-0">
      {/* UI Navigation - Hidden in Print */}
      <div className="max-w-[21cm] mx-auto mb-6 flex justify-between items-center print:hidden px-4">
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-slate-600 hover:text-black">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <div className="flex gap-4">
          <button onClick={handlePrint} className="flex items-center gap-1 px-4 py-2 bg-white border border-slate-300 rounded hover:bg-slate-50">
            <Printer className="w-4 h-4" /> Print
          </button>
          <button onClick={handleDownloadPdf} className="flex items-center gap-1 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
            <FileDown className="w-4 h-4" /> {downloading ? "..." : "PDF"}
          </button>
          <button onClick={() => navigate(`/edit-bill/${bill.id}`)} className="flex items-center gap-1 px-4 py-2 bg-white border border-slate-300 rounded hover:bg-slate-50">
            <Pencil className="w-4 h-4" /> Edit
          </button>
        </div>
      </div>

      {/* THE WORD DOCUMENT REPLICA */}
      <div
        className="bill-paper bg-white mx-auto shadow-xl print:shadow-none print:m-0"
        style={{
          width: '21cm',
          minHeight: '29.7cm',
          paddingTop: '20px',
          paddingBottom: '20px',
          paddingLeft: '25px',
          paddingRight: '25px',
          fontFamily: '"Bookman Old Style", serif',
          color: 'black',
          lineHeight: '1.2'
        }}
      >
        <div className="w-full h-full flex flex-col">

          {/* Header */}
          <div className="text-center mb-8" style={{ fontFamily: '"Imprint MT Shadow", Georgia, serif' }}>
            <h1 style={{ fontSize: '20px', fontWeight: 'bold', margin: '0', textTransform: 'uppercase' }}>SRI TULJA BHAVANI TRAVELS</h1>
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', color: '#dc2626', margin: '2px 0' }}>RENT-A-CAR</h2>
            <p style={{ fontSize: '12px', margin: '0' }}>1-11-113/3, P2 Sai Shikara Apartments, Shyamlal Building Begumpet, Hyderabad - 500016</p>
            <p style={{ fontSize: '12px', margin: '0', textDecoration: 'underline' }}>srituljabhavanitravels.rentacar@gmail.com</p>
          </div>

          {/* Bill Meta */}
          <div style={{ fontSize: '13px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ textAlign: 'left' }}>
              <p style={{ margin: '0' }}>Bill No. <span style={{ fontWeight: 'bold' }}>{bill.billNumber}</span></p>
              <p style={{ margin: '10px 0 0 0' }}>To.</p>
              <p style={{ margin: '0', fontWeight: 'bold', fontSize: '14px' }}>{bill.companyName}</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p style={{ margin: '0' }}>Date: <span style={{ fontWeight: 'bold' }}>{bill.billDate ? format(new Date(bill.billDate), "dd-MM-yyyy") : ""}</span></p>
            </div>
          </div>

          {/* Main Table */}
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              border: '1px solid black',
              fontSize: '12px',
              marginBottom: '15px'
            }}
          >
            <thead>
              <tr style={{ fontWeight: 'bold' }}>
                <th style={tableHeaderStyle('10%')}>Duty Slip</th>
                <th style={tableHeaderStyle('10%')}>Date</th>
                <th style={tableHeaderStyle('15%')}>Vehicle</th>
                <th style={tableHeaderStyle('10%')}>Total Kms</th>
                <th style={tableHeaderStyle('10%')}>Total Hrs</th>
                <th style={tableHeaderStyle('10%')}>Extra Kms</th>
                <th style={tableHeaderStyle('10%')}>Extra Hrs</th>
                <th style={tableHeaderStyle('10%')}>Amt</th>
                <th style={tableHeaderStyle('15%')}>Total Amount</th>
              </tr>
            </thead>
            <tbody>
              {billRows.map((row, idx) => (
                <tr key={idx}>
                  <td style={tableCellStyle('center')}>{row.dutySlip}</td>
                  <td style={tableCellStyle('center')}>{row.date}</td>
                  <td style={tableCellStyle('left', true)}>{row.vehicle}</td>
                  <td style={tableCellStyle('right')}>{row.kms}</td>
                  <td style={tableCellStyle('right')}>{row.hrs}</td>
                  <td style={tableCellStyle('center')}>{row.extraKm}</td>
                  <td style={tableCellStyle('center')}>{row.extraHr}</td>
                  <td style={tableCellStyle('center', false, true)}>{row.amt}</td>
                  <td style={tableCellStyle('right', false, true)}>
                    {Number(row.total).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}

              {/* Empty padding rows to mimic Word grid */}
              {[...Array(Math.max(0, 4 - billRows.length))].map((_, i) => (
                <tr key={`empty-${i}`} style={{ height: '24px' }}>
                  {[...Array(9)].map((_, j) => <td key={j} style={tableCellStyle()}></td>)}
                </tr>
              ))}

              {/* Grand Total */}
              <tr>
                <td colSpan={7} style={{ border: '1px solid black' }}></td>
                <td style={{ ...tableCellStyle('center'), fontWeight: 'bold' }}>Grand Total</td>
                <td style={{ ...tableCellStyle('right'), fontWeight: 'bold' }}>
                  {bill.grandTotal?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </td>
              </tr>
            </tbody>
          </table>

          {/* Amount in Words */}
          <div style={{ fontSize: '13px', fontStyle: 'italic', marginBottom: '40px' }}>
            <p style={{ margin: '0' }}>Rupees (in words): <span style={{ textTransform: 'capitalize', fontWeight: 'bold' }}>{words} only</span></p>
          </div>

          <div className="flex-grow"></div>

          {/* Footer */}
          <div style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
            <div style={{ textAlign: 'left' }}>
              <p style={{ borderBottom: '1px solid black', display: 'inline-block', minWidth: '150px', marginBottom: '10px' }}>For: {bill.contactPerson || ""}</p>
              <p style={{ margin: '0' }}>Booked by <span style={{ fontWeight: 'bold' }}>{bill.companyName}</span></p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p style={{ margin: '0', fontWeight: 'bold' }}>For Sri Tulja Bhavani Travels</p>
              <p style={{ marginTop: '50px', fontWeight: 'bold', marginRight: '30px' }}>Manager</p>
            </div>
          </div>

          {/* Phone Number at Bottom Right */}
          <div style={{ textAlign: 'right', fontSize: '11px', marginTop: '10px', whiteSpace: 'nowrap' }}>
            <p style={{ margin: '0' }}>Mobile No: 9440522814, 9989208711, 9000240410</p>
          </div>

        </div>
      </div>

      <style dangerouslySetInnerHTML={{
        __html: `
        @media print {
          @page { size: A4; margin: 0; }
          body { background: white !important; margin: 0 !important; }
          .bill-paper { width: 100% !important; height: auto !important; margin: 0 !important; box-shadow: none !important; }
          * { -webkit-print-color-adjust: exact; }
          .print\\:hidden { display: none !important; }
        }
      `}} />
    </div>
  );
}

// Helper styles for Word-like table
const tableHeaderStyle = (width) => ({
  width,
  border: '1px solid black',
  padding: '4px',
  textAlign: 'center',
  backgroundColor: '#f8f9fa'
});

const tableCellStyle = (align = 'left', wrap = false, bold = false) => ({
  border: '1px solid black',
  padding: '4px',
  textAlign: align,
  whiteSpace: wrap ? 'pre-wrap' : 'nowrap',
  fontWeight: bold ? 'bold' : 'normal',
  verticalAlign: 'middle'
});
