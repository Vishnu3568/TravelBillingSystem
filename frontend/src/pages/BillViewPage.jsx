import React, { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  FileDown,
  Printer,
  Pencil,
  FileText,
  AlertTriangle,
  CheckCircle,
  Eye
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
  const [activeTab, setActiveTab] = useState("parsed"); // "parsed" | "original"

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

  // Helper to extract rawValues JSON
  const rawData = useMemo(() => {
    if (!bill?.rawValues) return null;
    try {
      return typeof bill.rawValues === "string" ? JSON.parse(bill.rawValues) : bill.rawValues;
    } catch (e) {
      console.error("Failed to parse rawValues:", e);
      return null;
    }
  }, [bill]);

  // Check if a parsed value is absent in the original document text
  const checkMismatch = (parsedValue) => {
    if (!parsedValue || !bill?.originalDoc) return false;
    
    // Strip HTML to get clean text for matching
    const cleanText = bill.originalDoc.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").toLowerCase();
    const cleanVal = String(parsedValue).trim().toLowerCase();
    
    if (cleanVal === "" || cleanVal === "null" || cleanVal === "0" || cleanVal === "0.0") return false;
    
    // Check if value exists in original text
    const found = cleanText.includes(cleanVal);
    return !found;
  };

  // Check all fields for warnings
  const mismatches = useMemo(() => {
    if (!bill) return [];
    const fieldsToCheck = [
      { name: "Bill Number", value: bill.billNumber },
      { name: "Company Name", value: bill.companyName },
      { name: "Vehicle Number", value: bill.vehicleName },
      { name: "Duty Slip No", value: bill.dutySlipNo },
      { name: "Total Kms", value: rawData?.totalKms || bill.totalKms },
      { name: "Total Hours", value: rawData?.totalHours || bill.totalHours },
      { name: "Extra Kms", value: rawData?.extraKms || bill.extraKms },
      { name: "Extra Hours", value: rawData?.extraHours || bill.extraHours },
      { name: "Base Amount", value: rawData?.baseAmount || bill.baseAmount },
      { name: "Driver Bata", value: rawData?.driverBata || bill.driverBata },
      { name: "Parking", value: rawData?.parking || bill.parking },
      { name: "Toll", value: rawData?.toll || bill.toll },
      { name: "Night Charges", value: rawData?.nightCharges || bill.nightCharges },
      { name: "Grand Total", value: rawData?.totalAmount || bill.grandTotal }
    ];

    return fieldsToCheck.filter(f => checkMismatch(f.value));
  }, [bill, rawData]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-900 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400"></div>
        <p className="mt-4 text-slate-400 font-medium">Loading Bill details...</p>
      </div>
    );
  }

  if (!bill) return null;

  const words = numberToWords(bill.grandTotal || 0);

  // Field rendering helper that highlights mismatches
  const renderFieldWithHighlight = (value, fallback, label) => {
    const displayVal = value !== undefined && value !== null ? value : fallback;
    const hasMismatch = checkMismatch(displayVal);
    
    return (
      <span 
        className={`px-1 rounded ${hasMismatch ? "bg-red-100 text-red-700 font-semibold border border-red-300 animate-pulse" : ""}`}
        title={hasMismatch ? `${label || "Value"} does not match original document text!` : ""}
      >
        {displayVal || "---"}
        {hasMismatch && <AlertTriangle className="inline w-3 h-3 ml-1 text-red-500" />}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8 print:p-0 text-slate-100">
      
      {/* Dynamic Header / Navigation Controls */}
      <div className="max-w-[21cm] mx-auto mb-6 flex flex-col md:flex-row justify-between items-center gap-4 print:hidden">
        <button 
          onClick={() => navigate(-1)} 
          className="flex items-center gap-2 text-slate-400 hover:text-cyan-400 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to History
        </button>

        {/* Tab Controls (Premium Glassmorphism Style) */}
        <div className="flex bg-slate-900/80 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab("parsed")}
            className={`flex items-center gap-2 px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
              activeTab === "parsed"
                ? "bg-cyan-500 text-slate-950 shadow-md"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Eye className="w-4 h-4" /> Parsed Invoice Layout
          </button>
          <button
            onClick={() => setActiveTab("original")}
            className={`flex items-center gap-2 px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
              activeTab === "original"
                ? "bg-cyan-500 text-slate-950 shadow-md"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <FileText className="w-4 h-4" /> Original Word Document
          </button>
        </div>

        <div className="flex gap-2">
          <button 
            onClick={handlePrint} 
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-white rounded transition-colors"
          >
            <Printer className="w-4 h-4" /> Print
          </button>
          <button 
            onClick={handleDownloadPdf} 
            className="flex items-center gap-1.5 px-4 py-2 bg-cyan-600 text-slate-950 font-bold hover:bg-cyan-500 rounded transition-colors"
          >
            <FileDown className="w-4 h-4" /> {downloading ? "Downloading..." : "PDF"}
          </button>
          <button 
            onClick={() => navigate(`/edit-bill/${bill.id}`)} 
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-white rounded transition-colors"
          >
            <Pencil className="w-4 h-4" /> Edit
          </button>
        </div>
      </div>

      {/* Warning Notification Banner for Mismatched Data */}
      {mismatches.length > 0 && activeTab === "parsed" && (
        <div className="max-w-[21cm] mx-auto mb-6 bg-red-950/80 border border-red-800 text-red-200 px-4 py-3 rounded-lg flex items-start gap-3 animate-fade-in print:hidden">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-red-400">Parsing Mismatch Detected</h4>
            <p className="text-sm mt-0.5 text-red-300">
              The following fields do not match the exact text found in the original document:{" "}
              <span className="font-semibold">{mismatches.map(m => m.name).join(", ")}</span>. 
              Please verify with the "Original Word Document" tab.
            </p>
          </div>
        </div>
      )}

      {/* Success/Verified Banner */}
      {mismatches.length === 0 && activeTab === "parsed" && bill.originalDoc && (
        <div className="max-w-[21cm] mx-auto mb-6 bg-emerald-950/80 border border-emerald-800 text-emerald-200 px-4 py-3 rounded-lg flex items-center gap-3 print:hidden">
          <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />
          <p className="text-sm font-medium text-emerald-300">
            High Precision: All parsed billing values successfully verified against the original document text.
          </p>
        </div>
      )}

      {/* TAB 1: PARSED BILL IN TRUE INVOICE REPLICA LAYOUT */}
      {activeTab === "parsed" && (
        <div
          className="bill-paper bg-white mx-auto shadow-2xl print:shadow-none print:m-0"
          style={{
            width: "21cm",
            minHeight: "29.7cm",
            paddingTop: "40px",
            paddingBottom: "40px",
            paddingLeft: "45px",
            paddingRight: "45px",
            fontFamily: '"Bookman Old Style", serif',
            color: "black",
            lineHeight: "1.3"
          }}
        >
          <div className="w-full h-full flex flex-col">
            {/* Sri Tulja Bhavani Header Replica */}
            <div className="text-center mb-8 pb-4 border-b border-black">
              <h1 className="font-extrabold tracking-wider" style={{ fontSize: "24px", margin: "0", textTransform: "uppercase", fontFamily: '"Georgia", serif' }}>
                SRI TULJA BHAVANI TRAVELS
              </h1>
              <h2 className="font-bold tracking-widest text-red-600" style={{ fontSize: "16px", margin: "4px 0 2px 0" }}>
                RENT-A-CAR
              </h2>
              <p style={{ fontSize: "11px", margin: "0" }}>
                1-11-113/3, P2 Sai Shikara Apartments, Shyamlal Building Begumpet, Hyderabad - 500016
              </p>
              <p style={{ fontSize: "11px", margin: "0", textDecoration: "underline" }}>
                srituljabhavanitravels.rentacar@gmail.com
              </p>
            </div>

            {/* Bill Details Metadata */}
            <div className="mb-6 flex justify-between text-sm">
              <div className="text-left flex flex-col gap-1">
                <div>Bill No: <strong>{renderFieldWithHighlight(bill.billNumber, bill.billNumber, "Bill Number")}</strong></div>
                <div className="mt-2">To,</div>
                <div className="font-bold text-base uppercase tracking-tight">
                  {renderFieldWithHighlight(bill.companyName, bill.companyName, "Company Name")}
                </div>
              </div>
              <div className="text-right">
                <div>Date: <strong>{renderFieldWithHighlight(bill.billDate ? format(new Date(bill.billDate), "dd-MM-yyyy") : "", "", "Bill Date")}</strong></div>
              </div>
            </div>

            {/* Duty Slip Replica Table */}
            <table className="w-full border-collapse border border-black text-sm mb-6">
              <thead>
                <tr className="bg-slate-100 font-bold">
                  <th style={tableHeaderStyle("12%")}>Duty Slip</th>
                  <th style={tableHeaderStyle("12%")}>Date</th>
                  <th style={tableHeaderStyle("20%")}>Vehicle</th>
                  <th style={tableHeaderStyle("11%")}>Total Kms</th>
                  <th style={tableHeaderStyle("11%")}>Total Hrs</th>
                  <th style={tableHeaderStyle("11%")}>Extra Kms</th>
                  <th style={tableHeaderStyle("11%")}>Extra Hrs</th>
                  <th style={tableHeaderStyle("12%")}>Amt</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={tableCellStyle("center")}>
                    {renderFieldWithHighlight(rawData?.dutySlipNo, bill.dutySlipNo, "Duty Slip No")}
                  </td>
                  <td style={tableCellStyle("center")}>
                    {bill.tripDate ? format(new Date(bill.tripDate), "dd-MM-yy") : "---"}
                  </td>
                  <td style={tableCellStyle("left", true)}>
                    {renderFieldWithHighlight(bill.vehicleName, bill.vehicleName, "Vehicle Number")}
                    <div className="text-xs text-slate-500 uppercase">{bill.vehicleType || ""}</div>
                  </td>
                  <td style={tableCellStyle("right")}>
                    {renderFieldWithHighlight(rawData?.totalKms, bill.totalKms, "Total Kms")}
                  </td>
                  <td style={tableCellStyle("right")}>
                    {renderFieldWithHighlight(rawData?.totalHours, bill.totalHours, "Total Hours")}
                  </td>
                  <td style={tableCellStyle("center")}>
                    {renderFieldWithHighlight(rawData?.extraKms, bill.extraKms, "Extra Kms")}
                  </td>
                  <td style={tableCellStyle("center")}>
                    {renderFieldWithHighlight(rawData?.extraHours, bill.extraHours, "Extra Hours")}
                  </td>
                  <td style={tableCellStyle("right", false, true)}>
                    {renderFieldWithHighlight(rawData?.baseAmount, bill.baseAmount, "Base Amount")}
                  </td>
                </tr>

                {/* Additional parsed charges */}
                {(rawData?.driverBata || bill.driverBata) && (
                  <tr>
                    <td colSpan={7} className="border border-black px-3 py-1.5 text-right font-semibold">Driver Bata:</td>
                    <td style={tableCellStyle("right", false, true)}>
                      {renderFieldWithHighlight(rawData?.driverBata, bill.driverBata, "Driver Bata")}
                    </td>
                  </tr>
                )}
                {(rawData?.parking || bill.parking) && (
                  <tr>
                    <td colSpan={7} className="border border-black px-3 py-1.5 text-right font-semibold">Parking:</td>
                    <td style={tableCellStyle("right", false, true)}>
                      {renderFieldWithHighlight(rawData?.parking, bill.parking, "Parking")}
                    </td>
                  </tr>
                )}
                {(rawData?.toll || bill.toll) && (
                  <tr>
                    <td colSpan={7} className="border border-black px-3 py-1.5 text-right font-semibold">Toll:</td>
                    <td style={tableCellStyle("right", false, true)}>
                      {renderFieldWithHighlight(rawData?.toll, bill.toll, "Toll")}
                    </td>
                  </tr>
                )}
                {(rawData?.nightCharges || bill.nightCharges) && (
                  <tr>
                    <td colSpan={7} className="border border-black px-3 py-1.5 text-right font-semibold">Night Charges:</td>
                    <td style={tableCellStyle("right", false, true)}>
                      {renderFieldWithHighlight(rawData?.nightCharges, bill.nightCharges, "Night Charges")}
                    </td>
                  </tr>
                )}
                {(rawData?.otherCharges || bill.otherCharges) && (
                  <tr>
                    <td colSpan={7} className="border border-black px-3 py-1.5 text-right font-semibold">Other Charges:</td>
                    <td style={tableCellStyle("right", false, true)}>
                      {renderFieldWithHighlight(rawData?.otherCharges, bill.otherCharges, "Other Charges")}
                    </td>
                  </tr>
                )}

                {/* Grand Total Row */}
                <tr className="bg-slate-50 font-bold border-t-2 border-black">
                  <td colSpan={6} className="border border-black"></td>
                  <td className="border border-black px-3 py-2 text-right">Grand Total:</td>
                  <td className="border border-black px-3 py-2 text-right text-base text-red-700">
                    {renderFieldWithHighlight(rawData?.totalAmount, bill.grandTotal, "Grand Total")}
                  </td>
                </tr>
              </tbody>
            </table>

            {/* Words representation */}
            <div className="text-sm italic mb-10">
              Rupees (in words): <span className="capitalize font-bold underline">{words} Only</span>
            </div>

            <div className="flex-grow"></div>

            {/* Bottom Signature Area */}
            <div className="flex justify-between items-end text-sm mt-8 border-t border-slate-200 pt-6">
              <div>
                <p className="border-b border-black pb-1 min-w-[200px]">For: {bill.contactPerson || "---"}</p>
                <p className="text-xs text-slate-500 mt-1">Booked by {bill.companyName}</p>
              </div>
              <div className="text-right">
                <p className="font-bold">For Sri Tulja Bhavani Travels</p>
                <p className="mt-12 font-bold pr-4 text-xs uppercase tracking-wider">Manager Signature</p>
              </div>
            </div>

            {/* Phone contact numbers */}
            <div className="text-right text-[10px] text-slate-400 mt-4 border-t border-slate-100 pt-2">
              Mobile: 9440522814, 9989208711, 9000240410
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ORIGINAL DOCUMENT PREVIEW CHUNK */}
      {activeTab === "original" && (
        <div className="max-w-[21cm] mx-auto bg-slate-900/60 p-6 rounded-xl border border-slate-800 shadow-xl">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-bold text-cyan-400 flex items-center gap-2">
              <FileText className="w-5 h-5" /> Document Segment Preview (HTML)
            </h3>
            <span className="text-xs bg-slate-800 text-slate-400 px-3 py-1 rounded-full">
              Page {bill.id} chunk
            </span>
          </div>

          {bill.originalDoc ? (
            <div 
              className="original-doc-container bg-white text-slate-950 p-8 rounded-lg shadow-inner overflow-x-auto min-h-[600px] border border-slate-300"
              style={{
                fontFamily: '"Courier New", Courier, monospace',
                fontSize: "14px",
                lineHeight: "1.5"
              }}
              dangerouslySetInnerHTML={{ __html: bill.originalDoc }}
            />
          ) : (
            <div className="text-center py-20 text-slate-400">
              <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
              <p className="text-base font-semibold">No original document content stored for this bill.</p>
              <p className="text-sm mt-1 text-slate-500">Only bills uploaded after this update contain HTML segment previews.</p>
            </div>
          )}
        </div>
      )}

      {/* Global Invoice Print Styles */}
      <style dangerouslySetInnerHTML={{
        __html: `
        @media print {
          @page { size: A4; margin: 0; }
          body { background: white !important; color: black !important; }
          .bill-paper { width: 100% !important; height: auto !important; margin: 0 !important; box-shadow: none !important; padding: 20px !important; }
          .print\\:hidden { display: none !important; }
          .original-doc-container { border: none !important; box-shadow: none !important; }
        }
      `}} />
    </div>
  );
}

// Inline styles helpers
const tableHeaderStyle = (width) => ({
  width,
  border: "1px solid black",
  padding: "6px",
  textAlign: "center",
  fontSize: "12px",
  backgroundColor: "#f1f5f9"
});

const tableCellStyle = (align = "left", wrap = false, bold = false) => ({
  border: "1px solid black",
  padding: "6px",
  textAlign: align,
  whiteSpace: wrap ? "pre-wrap" : "nowrap",
  fontWeight: bold ? "bold" : "normal",
  verticalAlign: "middle",
  fontSize: "12px"
});
