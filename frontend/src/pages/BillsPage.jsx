import React, { useEffect, useState, useCallback } from "react";
import {
  Search,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Eye,
  FileDown,
  Calendar,
  Building2,
  FileText,
  Filter,
  Pencil,
  Plus
} from "lucide-react";
import api from "../services/api";
import { format } from "date-fns";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";

export default function BillsPage() {
  const navigate = useNavigate();
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(10);
  const [nlQuery, setNlQuery] = useState("");
  const [isNlSearching, setIsNlSearching] = useState(false);

  const [filters, setFilters] = useState({
    billNumber: "",
    companyName: "",
    fromDate: "",
    toDate: ""
  });

  const fetchBills = useCallback(async (page = 0, currentFilters = null, nlSearchQuery = null) => {
    setLoading(true);
    try {
      let endpoint = "/bills";
      let params = { page, size: pageSize };

      if (nlSearchQuery) {
        endpoint = "/bills/search/nl";
        params.query = nlSearchQuery;
      } else {
        const activeFilters = currentFilters || filters;
        const { billNumber, companyName, fromDate, toDate } = activeFilters;
        const isSearching = billNumber || companyName || fromDate || toDate;
        if (isSearching) {
          endpoint = "/bills/search";
          if (billNumber) params.billNumber = billNumber;
          if (companyName) params.companyName = companyName;
          if (fromDate) params.fromDate = fromDate;
          if (toDate) params.toDate = toDate;
        }
      }

      const response = await api.get(endpoint, { params });
      setBills(response.data.content);
      setTotalPages(response.data.totalPages);
      setCurrentPage(page);
    } catch (error) {
      console.error("Failed to fetch bills:", error);
    } finally {
      setLoading(false);
    }
  }, [filters, pageSize]);

  useEffect(() => {
    fetchBills();
  }, [fetchBills]);

  const handleSearch = (e) => {
    e.preventDefault();
    setIsNlSearching(false);
    setNlQuery("");
    fetchBills(0);
  };

  const handleNLSearch = async (e) => {
    e.preventDefault();
    if (!nlQuery.trim()) return;
    
    try {
      setLoading(true);
      // Get AI interpretation first
      const explainRes = await api.get("/bills/search/nl/explain", {
        params: { query: nlQuery }
      });
      
      const interpretation = explainRes.data;
      
      const result = await Swal.fire({
        title: "AI Search Interpretation",
        html: `
          <div class="text-left p-4 bg-slate-50 border-2 border-black font-bold">
            <p class="text-cyan-600 mb-2">I understood your request as:</p>
            <p class="text-black text-lg">"${interpretation.summary || nlQuery}"</p>
          </div>
        `,
        icon: "info",
        showCancelButton: true,
        confirmButtonText: "Execute Search",
        cancelButtonText: "Refine Query",
        confirmButtonColor: "#0891b2", // cyan-600
        cancelButtonColor: "#000000",
        background: "#ffffff",
        customClass: {
          popup: 'rounded-none border-[3px] border-black shadow-[12px_12px_0px_0px_rgba(0,0,0,1)]',
          title: 'text-2xl font-black uppercase tracking-tight',
          confirmButton: 'rounded-none font-bold uppercase tracking-widest text-xs px-8 py-3',
          cancelButton: 'rounded-none font-bold uppercase tracking-widest text-xs px-8 py-3'
        }
      });

      if (result.isConfirmed) {
        setIsNlSearching(true);
        setFilters({ billNumber: "", companyName: "", fromDate: "", toDate: "" });
        fetchBills(0, null, nlQuery);
      } else {
        setLoading(false);
      }
    } catch (error) {
      console.error("AI Explain Error:", error);
      Swal.fire({
        title: "AI Error",
        text: "Could not understand query. Please refine your search.",
        icon: "error",
        confirmButtonColor: "#000"
      });
      setLoading(false);
    }
  };

  const handleReset = () => {
    const resetFilters = {
      billNumber: "",
      companyName: "",
      fromDate: "",
      toDate: ""
    };
    setFilters(resetFilters);
    setNlQuery("");
    setIsNlSearching(false);
    fetchBills(0, resetFilters);
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 0 && newPage < totalPages) {
      fetchBills(newPage, filters, isNlSearching ? nlQuery : null);
    }
  };

  const handleViewBill = (id) => {
    navigate(`/bill-view/${id}`);
  };

  const handleDownloadPdf = async (id, billNumber) => {
    try {
      const response = await api.get(`/bills/${id}/pdf`, {
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `invoice-${billNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Failed to download PDF:", error);
      alert("Failed to download invoice. Please try again.");
    }
  };

  return (
    <div className="p-6 bg-slate-50 min-h-screen text-black">
      <div className="max-w-7xl mx-auto">
        <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-4xl font-bold tracking-tight flex items-center gap-3">
              <FileText className="text-cyan-600" size={36} />
              Your Bills
            </h1>
            <p className="mt-2 text-slate-500">Search and manage all generated invoices across the system.</p>
          </div>
          
          {/* AI Search Bar */}
          <div className="flex-1 max-w-xl">
            <form onSubmit={handleNLSearch} className="relative group">
              <div className="absolute inset-0 bg-cyan-500 blur-sm opacity-0 group-focus-within:opacity-20 transition-opacity"></div>
              <div className="relative flex items-center">
                <div className="absolute left-4 text-cyan-600 animate-pulse">
                  <Search size={20} strokeWidth={3} />
                </div>
                <input
                  type="text"
                  placeholder="Search using AI (e.g. 'Ashapura bills above 50000 in July')"
                  className="w-full pl-12 pr-28 py-4 bg-white border-2 border-black rounded-none font-bold text-sm focus:ring-0 focus:border-cyan-500 transition-all outline-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] focus:translate-x-0.5 focus:translate-y-0.5 focus:shadow-none"
                  value={nlQuery}
                  onChange={(e) => setNlQuery(e.target.value)}
                />
                <button
                  type="submit"
                  className="absolute right-2 bg-black text-white px-4 py-2 text-[10px] font-black uppercase tracking-widest hover:bg-cyan-500 hover:text-black transition-all"
                >
                  AI Search
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="bg-white border-[3px] border-black p-8 md:p-10 mb-16 shadow-[12px_12px_0px_0px_rgba(0,0,0,1)] flex flex-col md:flex-row md:items-center justify-between gap-8">
          <div>
            <h2 className="text-3xl font-black tracking-tight mb-3">Generate New Bill</h2>
            <p className="text-slate-500 text-sm max-w-xl font-medium leading-relaxed">
              Create a professional bill for your customers in seconds. Our system automatically handles tax calculations, vehicle tracking, and history logging.
            </p>
          </div>
          <button
            onClick={() => navigate("/create-bill")}
            className="flex items-center gap-2 rounded-none bg-cyan-500 px-8 py-4 text-sm font-bold text-black border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:bg-black hover:text-white transition-all active:translate-x-0.5 active:translate-y-0.5 active:shadow-none whitespace-nowrap"
          >
            <Plus size={20} strokeWidth={3} />
            Create New Bill
          </button>
        </div>

        <div className="bg-white rounded-none shadow-sm border border-slate-200 p-4 mb-8">
          <form onSubmit={handleSearch} className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[200px] space-y-1.5">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Bill Number</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="e.g. BILL-2024..."
                  className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-none focus:ring-2 focus:ring-cyan-500 transition-all outline-none text-sm"
                  value={filters.billNumber}
                  onChange={(e) => setFilters({ ...filters, billNumber: e.target.value })}
                />
              </div>
            </div>

            <div className="flex-1 min-w-[200px] space-y-1.5">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Company</label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Company name..."
                  className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-none focus:ring-2 focus:ring-cyan-500 transition-all outline-none text-sm"
                  value={filters.companyName}
                  onChange={(e) => setFilters({ ...filters, companyName: e.target.value })}
                />
              </div>
            </div>

            <div className="w-[160px] space-y-1.5">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">From Date</label>
              <input
                type="date"
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-none focus:ring-2 focus:ring-cyan-500 transition-all outline-none text-sm"
                value={filters.fromDate}
                onChange={(e) => setFilters({ ...filters, fromDate: e.target.value })}
              />
            </div>

            <div className="w-[160px] space-y-1.5">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">To Date</label>
              <input
                type="date"
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-none focus:ring-2 focus:ring-cyan-500 transition-all outline-none text-sm"
                value={filters.toDate}
                onChange={(e) => setFilters({ ...filters, toDate: e.target.value })}
              />
            </div>

            <div className="flex gap-2">
              <button
                type="submit"
                className="bg-black text-white px-6 py-2 font-bold uppercase tracking-widest text-xs hover:bg-cyan-500 hover:text-black transition-all shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none"
              >
                Search
              </button>
              <button
                type="button"
                onClick={handleReset}
                className="p-2 text-slate-400 bg-white hover:text-slate-600 hover:bg-slate-50 rounded-none transition-all border border-slate-200 active:scale-95"
                title="Reset Filters"
              >
                <RotateCcw className="w-5 h-5" />
              </button>
            </div>
          </form>
        </div>

        <div className="bg-white rounded-none shadow-sm border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/50 border-b border-slate-200">
                  <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Bill Number</th>
                  <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Date</th>
                  <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Company</th>
                  <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Vehicle</th>
                  <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Amount</th>
                  <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="animate-pulse">
                      <td colSpan="7" className="px-6 py-4">
                        <div className="h-4 bg-slate-100 rounded-none w-full"></div>
                      </td>
                    </tr>
                  ))
                ) : bills.length > 0 ? (
                  bills.map((bill) => (
                    <tr key={bill.id} className="hover:bg-slate-50 transition-colors group">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-mono text-sm font-semibold text-cyan-600 bg-cyan-50 px-2 py-1 rounded-none">
                          {bill.billNumber}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {bill.billDate ? format(new Date(bill.billDate), "dd MMM yyyy") : "-"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-800">
                        {bill.companyName}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {bill.vehicleName || "-"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm font-bold text-black">
                          ₹{bill.grandTotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                          <span className="text-[10px] font-bold text-slate-400 uppercase leading-none mb-1">Created By</span>
                          <div className="flex items-center gap-2">
                            <div className="w-5 h-5 rounded-none bg-black flex items-center justify-center text-[9px] font-bold text-white uppercase">
                              {bill.createdBy?.substring(0, 2)}
                            </div>
                            <span className="text-xs font-medium text-slate-600">{bill.createdBy}</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={() => handleViewBill(bill.id)}
                            className="p-1.5 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-none transition-all"
                            title="View Details"
                          >
                            <Eye className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDownloadPdf(bill.id, bill.billNumber)}
                            className="p-1.5 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-none transition-all"
                            title="Download PDF"
                          >
                            <FileDown className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => navigate(`/edit-bill/${bill.id}`)}
                            className="p-1.5 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-none transition-all"
                            title="Edit Bill"
                          >
                            <Pencil className="w-5 h-5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center justify-center text-slate-400">
                        <div className="bg-slate-100 p-4 rounded-none mb-4">
                          <Filter className="w-8 h-8" />
                        </div>
                        <p className="text-lg font-medium text-slate-600">No records found</p>
                        <p className="text-sm">Try adjusting your search or filters</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {!loading && totalPages > 1 && (
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
              <div className="text-sm text-slate-500">
                Showing <span className="font-medium">{currentPage * pageSize + 1}</span> to{" "}
                <span className="font-medium">
                  {Math.min((currentPage + 1) * pageSize, bills.length + currentPage * pageSize)}
                </span>{" "}
                results
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 0}
                  className="p-2 border border-slate-200 rounded-none bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                {Array.from({ length: totalPages }).map((_, i) => (
                  <button
                    key={i}
                    onClick={() => handlePageChange(i)}
                    className={`w-10 h-10 rounded-none border font-medium text-sm transition-all ${currentPage === i
                      ? "bg-cyan-600 border-cyan-600 text-white shadow-sm"
                      : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                      }`}
                  >
                    {i + 1}
                  </button>
                ))}
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages - 1}
                  className="p-2 border border-slate-200 rounded-none bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
