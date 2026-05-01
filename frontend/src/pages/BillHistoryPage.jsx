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
  Pencil
} from "lucide-react";
import api from "../services/api";
import { format } from "date-fns";
import { useNavigate } from "react-router-dom";

export default function BillHistoryPage() {
  const navigate = useNavigate();
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(10);
  
  const [filters, setFilters] = useState({
    billNumber: "",
    companyName: "",
    fromDate: "",
    toDate: ""
  });

  const fetchBills = useCallback(async (page = 0, currentFilters = filters) => {
    setLoading(true);
    try {
      const { billNumber, companyName, fromDate, toDate } = currentFilters;
      const isSearching = billNumber || companyName || fromDate || toDate;
      
      const endpoint = isSearching ? "/bills/search" : "/bills";
      const params = {
        page,
        size: pageSize,
        ...(billNumber && { billNumber }),
        ...(companyName && { companyName }),
        ...(fromDate && { fromDate }),
        ...(toDate && { toDate })
      };

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
    fetchBills(0);
  };

  const handleReset = () => {
    const resetFilters = {
      billNumber: "",
      companyName: "",
      fromDate: "",
      toDate: ""
    };
    setFilters(resetFilters);
    fetchBills(0, resetFilters);
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 0 && newPage < totalPages) {
      fetchBills(newPage);
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
    <div className="bg-slate-50 min-h-full">
      <div className="mx-auto">
        <div className="mb-8">
            <div className="flex items-center gap-2 mb-1">
                <FileText className="w-5 h-5 text-indigo-600" />
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Financial Records</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Bill History</h1>
            <p className="text-sm text-slate-500">Search and manage all generated invoices across the system.</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 mb-8">
          <form onSubmit={handleSearch} className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[200px] space-y-1.5">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Bill Number</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="e.g. BILL-2024..."
                  className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none text-sm"
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
                  className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none text-sm"
                  value={filters.companyName}
                  onChange={(e) => setFilters({ ...filters, companyName: e.target.value })}
                />
              </div>
            </div>

            <div className="w-[160px] space-y-1.5">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">From Date</label>
              <input
                type="date"
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none text-sm"
                value={filters.fromDate}
                onChange={(e) => setFilters({ ...filters, fromDate: e.target.value })}
              />
            </div>

            <div className="w-[160px] space-y-1.5">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">To Date</label>
              <input
                type="date"
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none text-sm"
                value={filters.toDate}
                onChange={(e) => setFilters({ ...filters, toDate: e.target.value })}
              />
            </div>

            <div className="flex gap-2">
              <button
                type="submit"
                className="bg-slate-950 hover:bg-slate-800 text-white font-bold py-2 px-6 rounded-xl transition-all shadow-lg shadow-slate-200 flex items-center gap-2 text-sm active:scale-95"
              >
                Search
              </button>
              <button
                type="button"
                onClick={handleReset}
                className="p-2 text-slate-400 bg-white hover:text-slate-600 hover:bg-slate-50 rounded-xl transition-all border border-slate-200 active:scale-95"
                title="Reset Filters"
              >
                <RotateCcw className="w-5 h-5" />
              </button>
            </div>
          </form>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
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
                        <div className="h-4 bg-slate-100 rounded w-full"></div>
                      </td>
                    </tr>
                  ))
                ) : bills.length > 0 ? (
                  bills.map((bill) => (
                    <tr key={bill.id} className="hover:bg-slate-50 transition-colors group">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-mono text-sm font-semibold text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
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
                        <span className="text-sm font-bold text-slate-900">
                          ₹{bill.grandTotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                            <span className="text-[10px] font-bold text-slate-400 uppercase leading-none mb-1">Created By</span>
                            <div className="flex items-center gap-2">
                                <div className="w-5 h-5 rounded-md bg-slate-950 flex items-center justify-center text-[9px] font-bold text-white uppercase">
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
                            className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
                            title="View Details"
                          >
                            <Eye className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDownloadPdf(bill.id, bill.billNumber)}
                            className="p-1.5 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-all"
                            title="Download PDF"
                          >
                            <FileDown className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => navigate(`/edit-bill/${bill.id}`)}
                            className="p-1.5 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-lg transition-all"
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
                        <div className="bg-slate-100 p-4 rounded-full mb-4">
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
                  className="p-2 border border-slate-200 rounded-lg bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                {Array.from({ length: totalPages }).map((_, i) => (
                  <button
                    key={i}
                    onClick={() => handlePageChange(i)}
                    className={`w-10 h-10 rounded-lg border font-medium text-sm transition-all ${
                      currentPage === i
                        ? "bg-indigo-600 border-indigo-600 text-white shadow-sm"
                        : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    {i + 1}
                  </button>
                ))}
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages - 1}
                  className="p-2 border border-slate-200 rounded-lg bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
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
